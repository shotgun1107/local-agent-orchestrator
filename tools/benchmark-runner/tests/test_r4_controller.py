from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from benchmark_runner.adapter import VariantCapabilities
from benchmark_runner.contract import (
    ArtifactIdentity,
    CellLifecycleState,
    CellStateRecord,
    ControllerLockRecord,
    ExperimentControl,
    ExperimentDisplayState,
    FixtureIdentity,
    utc_now,
)
from benchmark_runner.plan import build_r4_plan
from benchmark_runner.runner import (
    R4CapturedCell,
    R4CellDriver,
    R4ControllerError,
    R4ControllerLockedError,
    R4ExperimentController,
    R4InjectedCrash,
    R4SealedCell,
    _ControllerLock,
    canonical_json_bytes,
    create_r4_experiment_from_manifest,
    initialize_r4_experiment,
)

REPOSITORY_ROOT = Path(__file__).parents[3]
MANIFEST_PATH = REPOSITORY_ROOT / "benchmarks" / "manifests" / "b0-b1-frozen.yaml"
FROZEN_TIME = datetime(2026, 8, 5, tzinfo=timezone.utc)
RUNNER_SHA = "a" * 64
VARIANT_SHA = {"b0": "b" * 64, "b1": "c" * 64}


def _git() -> Path:
    executable = shutil.which("git")
    assert executable is not None
    return Path(executable)


class FakeR4Driver(R4CellDriver):
    def __init__(self, variant_id: str, *, stop_reason: str | None = None) -> None:
        self.variant_id = variant_id
        self.stop_reason = stop_reason
        self.prepare_calls = 0
        self.invoke_calls = 0
        self.validate_capture_calls = 0
        self.recover_active_calls = 0
        self.recover_judging_calls = 0
        self.judge_calls = 0
        self.deadlines: list[float] = []

    def id(self) -> str:
        return self.variant_id

    def capabilities(self) -> VariantCapabilities:
        return VariantCapabilities(
            automated_launch=self.variant_id == "b1",
            supports_usage=self.variant_id == "b1",
            supports_attempt_count=True,
        )

    def prepare(self, plan, cell, cell_dir: Path) -> None:
        self.prepare_calls += 1
        (cell_dir / "workspace").mkdir(parents=True, exist_ok=True)

    def invoke(
        self,
        plan,
        cell,
        cell_dir: Path,
        *,
        deadline_seconds: float,
    ) -> R4CapturedCell:
        self.invoke_calls += 1
        self.deadlines.append(deadline_seconds)
        captured = R4CapturedCell(outcome_state="completed")
        path = cell_dir / "raw" / "driver-capture.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical_json_bytes(captured))
        return captured

    def validate_captured(self, plan, cell, cell_dir: Path) -> R4CapturedCell:
        self.validate_capture_calls += 1
        path = cell_dir / "raw" / "driver-capture.json"
        if not path.is_file():
            raise R4ControllerError("driver has no terminal capture")
        return R4CapturedCell.model_validate_json(path.read_bytes())

    def recover_active(self, cell_dir: Path) -> None:
        self.recover_active_calls += 1

    def recover_judging(self, cell_dir: Path) -> None:
        self.recover_judging_calls += 1

    def judge_and_seal(self, plan, cell, cell_dir: Path, captured: R4CapturedCell) -> R4SealedCell:
        self.judge_calls += 1
        payload = {
            "cell_id": cell.cell_id,
            "outcome_state": captured.outcome_state,
            "r4_fake": True,
        }
        data = canonical_json_bytes(payload)
        path = cell_dir / "sealed" / "measurement.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return R4SealedCell(
            outcome_state=captured.outcome_state,
            sealed_measurement_sha256=hashlib.sha256(data).hexdigest(),
            stop_reason=self.stop_reason,
        )


def _plan():
    manifest_sha = hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()
    return build_r4_plan(
        source_manifest_path=MANIFEST_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
        source_manifest_sha256=manifest_sha,
        fixtures=[
            FixtureIdentity(
                fixture_id="code-change",
                source_commit="e915914c0494cd21969de5bc60f81ad74ec1b037",
                git_tree="65dee05f3922b421140950b8297f0df2fa602b30",
            ),
            FixtureIdentity(
                fixture_id="document-read",
                source_commit="e915914c0494cd21969de5bc60f81ad74ec1b037",
                git_tree="2198d58636119afac24887cffa082e6db658efc1",
            ),
        ],
        repetitions=3,
        runner=ArtifactIdentity(
            artifact_id="benchmark-runner",
            version="0.1.0-r4-test",
            sha256=RUNNER_SHA,
        ),
        variants=[
            ArtifactIdentity(artifact_id="b0", version="r3-test", sha256=VARIANT_SHA["b0"]),
            ArtifactIdentity(artifact_id="b1", version="r2-test", sha256=VARIANT_SHA["b1"]),
        ],
        baseline_variant="b0",
        candidate_variant="b1",
        seed=20260805,
        primary_metrics=["check_success", "manual_copy_or_relay_count_excluding_start"],
        decision_policy={"quality_noninferiority": True},
        reasoning_control="not_applicable_fake",
        environment_fingerprint={
            "model": "fake",
            "reasoning_effort": "not_applicable",
            "surface_kind": "r4_fake",
        },
        created_at=FROZEN_TIME,
    )


def _setup(
    tmp_path: Path,
    *,
    fault_hook=None,
    stop_reason: str | None = None,
    runner_sha: str = RUNNER_SHA,
):
    plan = _plan()
    created = initialize_r4_experiment(tmp_path / "state", plan)
    drivers = {
        "b0": FakeR4Driver("b0", stop_reason=stop_reason),
        "b1": FakeR4Driver("b1", stop_reason=stop_reason),
    }
    controller = R4ExperimentController(
        experiment_dir=Path(created.experiment_dir),
        source_repository=REPOSITORY_ROOT,
        manifest_path=MANIFEST_PATH,
        benchmark_python=Path(sys.executable),
        git_executable=_git(),
        current_runner_sha256=runner_sha,
        current_variant_sha256=VARIANT_SHA,
        drivers=drivers,
        preflight_environment={
            "model": "fake",
            "auth_method": "none",
            "reasoning_effort": "not_applicable",
            "surface_kind": "r4_fake",
            "validated_without_model_turn": True,
        },
        fault_hook=fault_hook,
    )
    return controller, drivers, plan


@pytest.fixture(autouse=True)
def _without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CODEX_API_KEY", raising=False)


def test_preflight_is_required_before_any_cell_side_effect(tmp_path: Path) -> None:
    controller, drivers, plan = _setup(tmp_path)

    with pytest.raises(R4ControllerError, match="preflight"):
        controller.run_next()

    assert controller.status().display_state is ExperimentDisplayState.CREATED
    assert sum(driver.prepare_calls for driver in drivers.values()) == 0
    assert all(
        controller._cell_state(cell).state is CellLifecycleState.PLANNED
        for cell in plan.cells
    )


@pytest.mark.parametrize("variable", ["OPENAI_API_KEY", "CODEX_API_KEY"])
def test_preflight_fails_closed_for_api_key_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, variable: str
) -> None:
    controller, drivers, plan = _setup(tmp_path)
    monkeypatch.setenv(variable, "not-read-or-logged")

    with pytest.raises(R4ControllerError, match="API key environment is present") as exc_info:
        controller.preflight()

    assert "not-read-or-logged" not in str(exc_info.value)
    assert sum(driver.prepare_calls for driver in drivers.values()) == 0
    assert all(
        controller._cell_state(cell).state is CellLifecycleState.PLANNED
        for cell in plan.cells
    )


def test_manifest_factory_creates_full_plan_without_copying_fixture_workspaces(
    tmp_path: Path,
) -> None:
    created = create_r4_experiment_from_manifest(
        state_root=tmp_path / "state",
        source_repository=REPOSITORY_ROOT,
        manifest_path=MANIFEST_PATH,
        runner_artifact=ArtifactIdentity(
            artifact_id="benchmark-runner",
            version="r4-test",
            sha256=RUNNER_SHA,
        ),
        variant_artifacts=[
            ArtifactIdentity(artifact_id="b0", version="r3", sha256=VARIANT_SHA["b0"]),
            ArtifactIdentity(artifact_id="b1", version="r2", sha256=VARIANT_SHA["b1"]),
        ],
        baseline_variant="b0",
        candidate_variant="b1",
        seed=20260805,
        primary_metrics=["check_success", "manual_copy_or_relay_count_excluding_start"],
        decision_policy={"quality_noninferiority": True},
        reasoning_control="not_established_test",
        environment_fingerprint={
            "model": "gpt-5.6-terra",
            "auth_method": "chatgpt",
            "reasoning_effort": "not_established",
            "surface_kind": "mixed_b0_b1",
        },
        created_at=FROZEN_TIME,
    )

    experiment_dir = Path(created.experiment_dir)
    assert created.planned_cells == 12
    assert len(list((experiment_dir / "cells").iterdir())) == 12
    assert not list(experiment_dir.glob("cells/*/workspace"))


def test_preflight_seals_evidence_without_model_turn(tmp_path: Path) -> None:
    controller, _, _ = _setup(tmp_path)
    record = controller.preflight()
    evidence = json.loads(
        (controller.experiment_dir / record.evidence_path).read_text(encoding="utf-8")
    )

    assert controller.status().display_state is ExperimentDisplayState.PREFLIGHTED
    assert evidence["actual_model_turns"] == 0
    assert evidence["task_deadline_seconds"] == 900.0
    assert evidence["fixture_trees"] == {
        "code-change": "65dee05f3922b421140950b8297f0df2fa602b30",
        "document-read": "2198d58636119afac24887cffa082e6db658efc1",
    }


def test_tampered_preflight_evidence_blocks_before_prepare(tmp_path: Path) -> None:
    controller, drivers, _ = _setup(tmp_path)
    record = controller.preflight()
    (controller.experiment_dir / record.evidence_path).write_text(
        "{}",
        encoding="utf-8",
    )

    with pytest.raises(R4ControllerError, match="preflight"):
        controller.run_next()
    assert sum(driver.prepare_calls for driver in drivers.values()) == 0


def test_run_next_seals_exactly_one_cell_per_command(tmp_path: Path) -> None:
    controller, drivers, _ = _setup(tmp_path)
    controller.preflight()

    first = controller.run_next()
    assert first.action == "sealed"
    assert controller.status().sealed_cells == 1
    assert sum(driver.invoke_calls for driver in drivers.values()) == 1
    assert [
        deadline for driver in drivers.values() for deadline in driver.deadlines
    ] == [900.0]

    second = controller.run_next()
    assert second.action == "sealed"
    assert controller.status().sealed_cells == 2
    assert sum(driver.invoke_calls for driver in drivers.values()) == 2


@pytest.mark.parametrize(
    ("fault_point", "expected_state"),
    [
        ("before_state:PREPARED", CellLifecycleState.PLANNED),
        ("after_state:PREPARED", CellLifecycleState.PREPARED),
        ("before_state:ACTIVE", CellLifecycleState.PREPARED),
        ("after_state:ACTIVE", CellLifecycleState.ACTIVE),
        ("before_state:CAPTURED", CellLifecycleState.ACTIVE),
        ("after_state:CAPTURED", CellLifecycleState.CAPTURED),
        ("before_state:JUDGING", CellLifecycleState.CAPTURED),
        ("after_state:JUDGING", CellLifecycleState.JUDGING),
        ("before_state:SEALED", CellLifecycleState.JUDGING),
        ("after_state:SEALED", CellLifecycleState.SEALED),
    ],
)
def test_every_state_write_boundary_is_crash_injected(
    tmp_path: Path,
    fault_point: str,
    expected_state: CellLifecycleState,
) -> None:
    fired = False

    def fault(point: str, cell) -> None:
        nonlocal fired
        if not fired and point == fault_point:
            fired = True
            raise R4InjectedCrash(point)

    controller, _, plan = _setup(tmp_path, fault_hook=fault)
    controller.preflight()
    with pytest.raises(R4InjectedCrash):
        controller.run_next()

    assert fired is True
    assert controller._cell_state(plan.cells[0]).state is expected_state


def test_active_crash_never_reinvokes_variant_automatically(tmp_path: Path) -> None:
    def crash_after_active(point: str, cell) -> None:
        if point == "after_state:ACTIVE":
            raise R4InjectedCrash(point)

    controller, drivers, plan = _setup(tmp_path, fault_hook=crash_after_active)
    controller.preflight()
    with pytest.raises(R4InjectedCrash):
        controller.run_next()
    assert sum(driver.invoke_calls for driver in drivers.values()) == 0

    recovered = _controller_without_fault(controller, drivers)
    result = recovered.run_next()
    assert result.action == "stopped_active_crash"
    assert sum(driver.invoke_calls for driver in drivers.values()) == 0
    assert sum(driver.recover_active_calls for driver in drivers.values()) == 1
    assert recovered._cell_state(plan.cells[0]).state is CellLifecycleState.STOPPED
    with pytest.raises(R4ControllerError, match="no terminal capture"):
        recovered.accept_stopped_capture(
            plan.cells[0].cell_id,
            decided_by="test",
            evidence="no invocation occurred",
        )


def test_prepared_crash_resumes_same_cell_safely(tmp_path: Path) -> None:
    def crash_after_prepared(point: str, cell) -> None:
        if point == "after_state:PREPARED":
            raise R4InjectedCrash(point)

    controller, drivers, plan = _setup(tmp_path, fault_hook=crash_after_prepared)
    controller.preflight()
    with pytest.raises(R4InjectedCrash):
        controller.run_next()

    recovered = _controller_without_fault(controller, drivers)
    result = recovered.run_next()
    assert result.cell_id == plan.cells[0].cell_id
    assert result.action == "sealed"
    assert sum(driver.invoke_calls for driver in drivers.values()) == 1


def test_active_crash_after_capture_can_judge_without_reinvoke(tmp_path: Path) -> None:
    def crash_before_captured(point: str, cell) -> None:
        if point == "before_state:CAPTURED":
            raise R4InjectedCrash(point)

    controller, drivers, plan = _setup(tmp_path, fault_hook=crash_before_captured)
    controller.preflight()
    with pytest.raises(R4InjectedCrash):
        controller.run_next()
    assert sum(driver.invoke_calls for driver in drivers.values()) == 1

    recovered = _controller_without_fault(controller, drivers)
    assert recovered.run_next().action == "stopped_active_crash"
    assert sum(driver.recover_active_calls for driver in drivers.values()) == 1
    recovered.accept_stopped_capture(
        plan.cells[0].cell_id,
        decided_by="test",
        evidence="driver capture hash inspected",
    )
    recovered.resume(
        decided_by="test",
        decision="resume_judge_only",
        evidence="captured Evidence accepted",
    )
    assert recovered.run_next().action == "sealed"
    assert sum(driver.invoke_calls for driver in drivers.values()) == 1


def test_captured_and_judging_resume_never_invoke_variant(tmp_path: Path) -> None:
    for fault_point, expected_recovery_calls in (
        ("after_state:CAPTURED", 0),
        ("after_state:JUDGING", 1),
    ):
        case_root = tmp_path / fault_point.replace(":", "-")

        def fault(point: str, cell, target=fault_point) -> None:
            if point == target:
                raise R4InjectedCrash(point)

        controller, drivers, _ = _setup(case_root, fault_hook=fault)
        controller.preflight()
        with pytest.raises(R4InjectedCrash):
            controller.run_next()
        recovered = _controller_without_fault(controller, drivers)
        assert recovered.run_next().action == "sealed"
        assert sum(driver.invoke_calls for driver in drivers.values()) == 1
        assert sum(driver.recover_judging_calls for driver in drivers.values()) == expected_recovery_calls


def test_stop_resume_preserves_history_and_does_not_skip_order(tmp_path: Path) -> None:
    controller, _, plan = _setup(tmp_path, stop_reason="manual_review_required")
    controller.preflight()
    result = controller.run_next()

    assert result.stop_reason == "manual_review_required"
    assert controller.status().display_state is ExperimentDisplayState.STOPPED
    with pytest.raises(R4ControllerError, match="stopped"):
        controller.run_next()
    controller.resume(
        decided_by="user",
        decision="continue_after_review",
        evidence="sealed Cell reviewed",
    )
    control = ExperimentControl.model_validate_json(controller.control_path.read_bytes())
    assert control.stop_reason is None
    assert control.stop_history[0].reason == "manual_review_required"
    assert controller.status().next_cell_id == plan.cells[1].cell_id


def test_artifact_change_stops_before_workspace_preparation(tmp_path: Path) -> None:
    controller, drivers, _ = _setup(tmp_path)
    controller.preflight()
    changed = R4ExperimentController(
        experiment_dir=controller.experiment_dir,
        source_repository=REPOSITORY_ROOT,
        manifest_path=MANIFEST_PATH,
        benchmark_python=Path(sys.executable),
        git_executable=_git(),
        current_runner_sha256="d" * 64,
        current_variant_sha256=VARIANT_SHA,
        drivers=drivers,
        preflight_environment=controller.preflight_environment,
    )

    with pytest.raises(R4ControllerError, match="new revision"):
        changed.run_next()
    assert sum(driver.prepare_calls for driver in drivers.values()) == 0
    assert changed.status().stop_reason == "artifact_fingerprint_changed"


def test_live_lock_rejected_and_stale_lock_requires_explicit_confirmation(
    tmp_path: Path,
) -> None:
    controller, _, plan = _setup(tmp_path)
    live = _ControllerLock.acquire(controller.experiment_dir, plan.experiment_id)
    try:
        with pytest.raises(R4ControllerLockedError):
            controller.preflight()
        with pytest.raises(R4ControllerLockedError, match="still alive"):
            R4ExperimentController.recover_unlock(
                controller.experiment_dir,
                confirm_no_controller=True,
            )
    finally:
        live.release()

    dead_lock = ControllerLockRecord(
        controller_id="ctl_" + "1" * 32,
        pid=999999,
        hostname=__import__("socket").gethostname(),
        process_start_identity="dead-test-process",
        acquired_at=utc_now(),
        runner_version="test",
        experiment_id=plan.experiment_id,
    )
    (controller.experiment_dir / "lock.json").write_bytes(canonical_json_bytes(dead_lock))
    with pytest.raises(R4ControllerLockedError, match="Explicit"):
        R4ExperimentController.recover_unlock(
            controller.experiment_dir,
            confirm_no_controller=False,
        )
    removed = R4ExperimentController.recover_unlock(
        controller.experiment_dir,
        confirm_no_controller=True,
    )
    assert removed.controller_id == dead_lock.controller_id
    assert not (controller.experiment_dir / "lock.json").exists()


def test_superseded_experiment_cannot_resume_or_run(tmp_path: Path) -> None:
    controller, _, _ = _setup(tmp_path)
    controller.preflight()
    controller._record_stop("implementation_changed")
    controller.supersede(
        "exp_20260805_12345678_2",
        decided_by="user",
        evidence="new Runner revision",
    )

    assert controller.status().display_state is ExperimentDisplayState.SUPERSEDED
    with pytest.raises(R4ControllerError, match="Superseded"):
        controller.resume(decided_by="user", decision="resume", evidence="invalid")
    with pytest.raises(R4ControllerError, match="superseded"):
        controller.run_next()


def _controller_without_fault(
    controller: R4ExperimentController,
    drivers: dict[str, FakeR4Driver],
) -> R4ExperimentController:
    return R4ExperimentController(
        experiment_dir=controller.experiment_dir,
        source_repository=REPOSITORY_ROOT,
        manifest_path=MANIFEST_PATH,
        benchmark_python=Path(sys.executable),
        git_executable=_git(),
        current_runner_sha256=RUNNER_SHA,
        current_variant_sha256=VARIANT_SHA,
        drivers=drivers,
        preflight_environment=controller.preflight_environment,
    )
