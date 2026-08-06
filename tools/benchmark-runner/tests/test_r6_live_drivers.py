import json
import shutil
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from benchmark_runner.contract import (
    ArtifactIdentity,
    B0Attestation,
    CellLifecycleState,
    FixtureIdentity,
    Measurement,
)
from benchmark_runner.plan import build_r4_plan
from benchmark_runner.runner import (
    R4ControllerError,
    R4ExperimentController,
    R6B0ManualDriver,
    R6B1SequentialDriver,
    R6ScriptedB0Config,
    analyze_r5_experiment,
    create_r6_b0_task_prompt_plan,
    enqueue_r6_b0_control_command,
    export_r5_experiment,
    frozen_b0_b1_decision_policy,
    initialize_r4_experiment,
    sha256_file,
    verify_r5_export,
    verify_sealed_cell,
)
from benchmark_runner.r6 import _assert_b0_task_prompt_evidence

REPOSITORY_ROOT = Path(__file__).parents[3]
MANIFEST_PATH = REPOSITORY_ROOT / "benchmarks" / "manifests" / "b0-b1-frozen.yaml"
B1_ROOT = REPOSITORY_ROOT / "stages" / "b1-sequential"
FROZEN_TIME = datetime(2026, 8, 5, tzinfo=timezone.utc)
RUNNER_SHA = "8" * 64
VARIANT_SHA = {"b0": "9" * 64, "b1": "a" * 64}

SOLUTIONS = {
    "code-change": {
        "path": "src/config.py",
        "content": (
            'ALLOWED_KEYS = {"name"}\n\n\n'
            "def parse_config(value: dict[str, object]) -> dict[str, object]:\n"
            "    unknown_keys = set(value) - ALLOWED_KEYS\n"
            "    if unknown_keys:\n"
            '        raise ValueError(f"unknown top-level keys: {sorted(unknown_keys)}")\n'
            "    return dict(value)\n"
        ),
    },
    "document-read": {
        "path": "report.md",
        "content": (
            "# 상태 보고서\n\n"
            "## 확인된 사실\n\n"
            "- 작업 A는 완료됐다.\n"
            "- 작업 B는 아직 실행되지 않았다.\n\n"
            "## 미확인\n\n"
            "- 외부 배포 여부는 확인하지 못했다.\n"
        ),
    },
}


def _git() -> Path:
    executable = shutil.which("git")
    assert executable is not None
    return Path(executable)


def _plan(seed: int = 20260805):
    return build_r4_plan(
        source_manifest_path=MANIFEST_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
        source_manifest_sha256=sha256_file(MANIFEST_PATH),
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
            version="r6-nonlive-test",
            sha256=RUNNER_SHA,
        ),
        variants=[
            ArtifactIdentity(artifact_id="b0", version="manual-r6", sha256=VARIANT_SHA["b0"]),
            ArtifactIdentity(artifact_id="b1", version="b1-r6", sha256=VARIANT_SHA["b1"]),
        ],
        baseline_variant="b0",
        candidate_variant="b1",
        seed=seed,
        primary_metrics=[
            "check_success",
            "manual_copy_or_relay_count_excluding_start",
        ],
        decision_policy=frozen_b0_b1_decision_policy(),
        reasoning_control="not_applicable_fake",
        environment_fingerprint={
            "model": "fake",
            "auth_method": "none",
            "reasoning_effort": "not_applicable",
            "surface_kind": "r6_nonlive",
        },
        created_at=FROZEN_TIME,
    )


def _fake_fixture(path: Path, fixture_id: str) -> Path:
    solution = SOLUTIONS[fixture_id]
    value = {
        "scenario": "complete",
        "effects": [{"type": "write_file", **solution}],
        "result": {
            "schema_version": 1,
            "status_claim": "completed",
            "summary": "R6 full-driver non-live solution",
            "artifacts": [],
            "changed_paths": [solution["path"]],
            "checks_run_by_worker": [],
            "assumptions": [],
            "warnings": [],
            "requested_followup": None,
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return path


def _drivers(tmp_path: Path):
    common = {
        "source_repository": REPOSITORY_ROOT,
        "manifest_path": MANIFEST_PATH,
        "benchmark_python": Path(sys.executable),
        "git_executable": _git(),
        "runner_python": Path(sys.executable),
        "model": "fake",
        "reasoning_effort": "not_applicable",
        "auth_method": "none",
        "model_control": "not_applicable",
        "reasoning_control": "not_applicable",
        "treatment_control": "not_applicable",
    }
    b0_scripts = {
        fixture_id: R6ScriptedB0Config(
            writes={solution["path"]: solution["content"]},
            interventions=["initial_prompt_copy", "additional_prompt"],
        )
        for fixture_id, solution in SOLUTIONS.items()
    }
    fake_fixtures = {
        fixture_id: _fake_fixture(tmp_path / "fake" / f"{fixture_id}.json", fixture_id)
        for fixture_id in SOLUTIONS
    }
    return {
        "b0": R6B0ManualDriver(
            **common,
            surface_kind="r6_b0_scripted",
            approval_mode="not_applicable",
            scripted_by_fixture=b0_scripts,
        ),
        "b1": R6B1SequentialDriver(
            **common,
            surface_kind="r6_b1_fake_runtime",
            approval_mode="deny_all",
            command_prefix=(sys.executable, "-m", "orchestrator"),
            schema_root=B1_ROOT / "schemas" / "v1",
            runtime="fake",
            fake_fixture_by_fixture=fake_fixtures,
            b1_pythonpath=B1_ROOT / "src",
        ),
    }


@pytest.fixture(autouse=True)
def _without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CODEX_API_KEY", raising=False)


def test_r6_real_driver_boundary_runs_all_12_nonlive_cells(tmp_path: Path) -> None:
    plan = _plan()
    created = initialize_r4_experiment(tmp_path / "state", plan)
    drivers = _drivers(tmp_path)
    controller = R4ExperimentController(
        experiment_dir=Path(created.experiment_dir),
        source_repository=REPOSITORY_ROOT,
        manifest_path=MANIFEST_PATH,
        benchmark_python=Path(sys.executable),
        git_executable=_git(),
        current_runner_sha256=RUNNER_SHA,
        current_variant_sha256=VARIANT_SHA,
        drivers=drivers,
        preflight_environment={
            "model": "fake",
            "auth_method": "none",
            "reasoning_effort": "not_applicable",
            "surface_kind": "r6_nonlive",
            "validated_without_model_turn": True,
        },
    )

    preflight = controller.preflight()
    results = [controller.run_next() for _ in plan.cells]

    assert preflight.plan_fingerprint == plan.plan_fingerprint
    assert all(result.action == "sealed" for result in results)
    status = controller.status()
    assert status.sealed_cells == 12
    assert status.next_cell_id is None
    assert all(state is CellLifecycleState.SEALED for state in status.cell_states.values())
    measurements = [
        verify_sealed_cell(Path(created.experiment_dir) / "cells" / cell.cell_id)
        for cell in plan.cells
    ]
    assert all(measurement.outcome.check_success for measurement in measurements)
    assert all(
        measurement.variant_metrics.values.get("actual_model_turns") == 0
        for measurement in measurements
        if measurement.identity.variant_id == "b1"
    )
    assert all(
        "<WORKSPACE>" not in json.dumps(measurement.model_dump(mode="json"))
        for measurement in measurements
    )

    analysis = analyze_r5_experiment(Path(created.experiment_dir))
    export = export_r5_experiment(Path(created.experiment_dir), tmp_path / "results")
    verified = verify_r5_export(tmp_path / "results", plan.experiment_id)

    assert analysis.verdicts == {"b1": "ADOPT_B1"}
    assert export.export_sha256 == verified.export_sha256
    assert verified.cell_count == 12


def test_r6_prepare_is_idempotent_before_cell_activation(tmp_path: Path) -> None:
    plan = _plan()
    created = initialize_r4_experiment(tmp_path / "state", plan)
    drivers = _drivers(tmp_path)
    cell = next(item for item in plan.cells if item.variant_id == "b0")
    cell_dir = Path(created.experiment_dir) / "cells" / cell.cell_id

    drivers["b0"].prepare(plan, cell, cell_dir)
    first = (cell_dir / "raw" / "prepared-fixture.json").read_bytes()
    drivers["b0"].prepare(plan, cell, cell_dir)

    assert (cell_dir / "raw" / "prepared-fixture.json").read_bytes() == first


def test_r6_prepare_next_does_not_start_b0_deadline(tmp_path: Path) -> None:
    plan = _plan(seed=0)
    created = initialize_r4_experiment(tmp_path / "state", plan)
    drivers = _drivers(tmp_path)
    controller = R4ExperimentController(
        experiment_dir=Path(created.experiment_dir),
        source_repository=REPOSITORY_ROOT,
        manifest_path=MANIFEST_PATH,
        benchmark_python=Path(sys.executable),
        git_executable=_git(),
        current_runner_sha256=RUNNER_SHA,
        current_variant_sha256=VARIANT_SHA,
        drivers=drivers,
        preflight_environment={
            "model": "fake",
            "auth_method": "none",
            "reasoning_effort": "not_applicable",
            "surface_kind": "r6_nonlive",
            "validated_without_model_turn": True,
        },
    )
    controller.preflight()

    prepared = controller.prepare_next()
    time.sleep(0.25)
    status = controller.status()
    cell_dir = Path(created.experiment_dir) / "cells" / prepared.cell_id

    assert prepared.variant_id == "b0"
    assert status.cell_states[prepared.cell_id] is CellLifecycleState.PREPARED
    assert not (cell_dir / "variant-state" / "sidecar-process" / "active-process.json").exists()
    assert not (cell_dir / "variant-state" / "adapter-result.json").exists()


def test_r6_b0_control_queue_rejects_out_of_order_and_duplicate_commands(
    tmp_path: Path,
) -> None:
    control_dir = tmp_path / "control"
    with pytest.raises(R4ControllerError, match="initial prompt"):
        enqueue_r6_b0_control_command(
            control_dir,
            cell_id="cell_test",
            kind="additional_prompt",
        )
    first = enqueue_r6_b0_control_command(
        control_dir,
        cell_id="cell_test",
        kind="initial_prompt_copy",
    )
    with pytest.raises(R4ControllerError, match="first and only"):
        enqueue_r6_b0_control_command(
            control_dir,
            cell_id="cell_test",
            kind="initial_prompt_copy",
        )
    with pytest.raises(R4ControllerError, match="matching recovery_start"):
        enqueue_r6_b0_control_command(
            control_dir,
            cell_id="cell_test",
            kind="recovery_end",
        )
    with pytest.raises(R4ControllerError, match="attestation"):
        enqueue_r6_b0_control_command(
            control_dir,
            cell_id="cell_test",
            kind="complete",
        )
    terminal = enqueue_r6_b0_control_command(
        control_dir,
        cell_id="cell_test",
        kind="complete",
        attestation=B0Attestation(
            status="confirmed",
            confirmed_at=datetime.now(timezone.utc),
            timeline_complete=True,
            model="fake",
            reasoning_effort="low",
            surface_kind="codex_app_task",
        ),
    )
    with pytest.raises(R4ControllerError, match="already terminal"):
        enqueue_r6_b0_control_command(
            control_dir,
            cell_id="cell_test",
            kind="status_observation",
        )
    assert first.sequence == 1
    assert terminal.sequence == 2


def test_r6_b0_sequential_prompt_plan_is_hashed_and_required_in_order(
    tmp_path: Path,
) -> None:
    experiment_dir = tmp_path / "experiment"
    cell_dir = experiment_dir / "cells" / "cell_test"
    workspace = tmp_path / "workspace"
    shutil.copytree(
        REPOSITORY_ROOT / "benchmarks" / "fixtures" / "sequential-code-change",
        workspace,
    )
    plan = create_r6_b0_task_prompt_plan(
        workspace=workspace,
        cell_dir=cell_dir,
        codex_project_root=None,
    )

    assert [(item.task_key, item.event_kind) for item in plan.prompts] == [
        ("T1", "initial_prompt_copy"),
        ("T2", "additional_prompt"),
    ]
    for item in plan.prompts:
        assert sha256_file(cell_dir / item.relative_path) == item.sha256

    control_dir = cell_dir / "variant-state" / "b0-control"
    first, second = plan.prompts
    enqueue_r6_b0_control_command(
        control_dir,
        cell_id="cell_test",
        kind=first.event_kind,
        task_key=first.task_key,
        prompt_sha256=first.sha256,
    )
    with pytest.raises(R4ControllerError, match="every planned Task prompt"):
        _assert_b0_task_prompt_evidence(experiment_dir, "cell_test")
    enqueue_r6_b0_control_command(
        control_dir,
        cell_id="cell_test",
        kind=second.event_kind,
        task_key=second.task_key,
        prompt_sha256=second.sha256,
    )
    _assert_b0_task_prompt_evidence(experiment_dir, "cell_test")

    (cell_dir / second.relative_path).write_text("changed\n", encoding="utf-8")
    with pytest.raises(R4ControllerError, match="missing or changed"):
        _assert_b0_task_prompt_evidence(experiment_dir, "cell_test")


def test_r6_b0_file_control_runs_active_cell_to_sealed(tmp_path: Path) -> None:
    plan = _plan(seed=0)
    created = initialize_r4_experiment(tmp_path / "state", plan)
    drivers = _drivers(tmp_path)
    common = {
        "source_repository": REPOSITORY_ROOT,
        "manifest_path": MANIFEST_PATH,
        "benchmark_python": Path(sys.executable),
        "git_executable": _git(),
        "runner_python": Path(sys.executable),
        "model": "fake",
        "reasoning_effort": "not_applicable",
        "surface_kind": "r6_b0_file_control",
        "auth_method": "none",
        "approval_mode": "not_applicable",
        "model_control": "not_applicable",
        "reasoning_control": "not_applicable",
        "treatment_control": "not_applicable",
    }
    codex_project_root = tmp_path / "AI 오케스트레이터 실험실"
    drivers["b0"] = R6B0ManualDriver(
        **common,
        codex_project_root=codex_project_root,
    )
    controller = R4ExperimentController(
        experiment_dir=Path(created.experiment_dir),
        source_repository=REPOSITORY_ROOT,
        manifest_path=MANIFEST_PATH,
        benchmark_python=Path(sys.executable),
        git_executable=_git(),
        current_runner_sha256=RUNNER_SHA,
        current_variant_sha256=VARIANT_SHA,
        drivers=drivers,
        preflight_environment={
            "model": "fake",
            "auth_method": "none",
            "reasoning_effort": "not_applicable",
            "surface_kind": "r6_nonlive",
            "validated_without_model_turn": True,
        },
    )
    controller.preflight()
    prepared = controller.prepare_next()
    assert prepared.variant_id == "b0"
    cell_dir = Path(created.experiment_dir) / "cells" / prepared.cell_id
    active_workspace = codex_project_root / "active-workspace"
    owner_path = codex_project_root.parent / (
        f".{codex_project_root.name}.active-workspace.owner.json"
    )
    assert active_workspace.is_dir()
    assert owner_path.is_file()
    assert not (cell_dir / "workspace").exists()
    other_b0 = next(
        cell
        for cell in plan.cells
        if cell.variant_id == "b0" and cell.cell_id != prepared.cell_id
    )
    with pytest.raises(R4ControllerError, match="owned by another Cell"):
        drivers["b0"]._claim_workspace(  # type: ignore[attr-defined]
            plan,
            other_b0,
            Path(created.experiment_dir) / "cells" / other_b0.cell_id,
        )
    results: list[object] = []
    failures: list[BaseException] = []

    def run_cell() -> None:
        try:
            results.append(controller.run_next())
        except BaseException as exc:  # pragma: no cover - asserted below
            failures.append(exc)

    thread = threading.Thread(target=run_cell, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while controller.status().cell_states[prepared.cell_id] is not CellLifecycleState.ACTIVE:
        if time.monotonic() >= deadline:
            pytest.fail("B0 Cell did not become ACTIVE")
        time.sleep(0.02)
    control_dir = cell_dir / "variant-state" / "b0-control"
    enqueue_r6_b0_control_command(
        control_dir,
        cell_id=prepared.cell_id,
        kind="initial_prompt_copy",
    )
    solution = SOLUTIONS["code-change"]
    (active_workspace / solution["path"]).write_text(
        solution["content"],
        encoding="utf-8",
        newline="\n",
    )
    enqueue_r6_b0_control_command(
        control_dir,
        cell_id=prepared.cell_id,
        kind="complete",
        attestation=B0Attestation(
            status="confirmed",
            confirmed_at=datetime.now(timezone.utc),
            timeline_complete=True,
            model="fake",
            reasoning_effort="not_applicable",
            surface_kind="r6_b0_file_control",
        ),
    )
    thread.join(timeout=15)

    assert not thread.is_alive()
    assert failures == []
    assert results and results[0].action == "sealed"
    assert not active_workspace.exists()
    assert not owner_path.exists()
    assert (cell_dir / "workspace" / solution["path"]).is_file()
    measurement = verify_sealed_cell(cell_dir)
    assert measurement.outcome.check_success is True
    assert measurement.variant_metrics.values["measurement_trusted"] is True
    assert measurement.effort.startup_action_count.value == 1


def test_r6_sidecar_deadline_seals_timeout_without_model_call(tmp_path: Path) -> None:
    plan = _plan()
    created = initialize_r4_experiment(tmp_path / "state", plan)
    solution = SOLUTIONS["code-change"]
    common = {
        "source_repository": REPOSITORY_ROOT,
        "manifest_path": MANIFEST_PATH,
        "benchmark_python": Path(sys.executable),
        "git_executable": _git(),
        "runner_python": Path(sys.executable),
        "model": "fake",
        "reasoning_effort": "not_applicable",
        "surface_kind": "r6_timeout_test",
        "auth_method": "none",
        "approval_mode": "not_applicable",
        "model_control": "not_applicable",
        "reasoning_control": "not_applicable",
        "treatment_control": "not_applicable",
    }
    driver = R6B0ManualDriver(
        **common,
        scripted_by_fixture={
            "code-change": R6ScriptedB0Config(
                writes={solution["path"]: solution["content"]},
                interventions=["initial_prompt_copy"],
                delay_seconds=5.0,
            )
        },
    )
    cell = next(
        item
        for item in plan.cells
        if item.fixture_id == "code-change" and item.variant_id == "b0"
    )
    cell_dir = Path(created.experiment_dir) / "cells" / cell.cell_id
    driver.prepare(plan, cell, cell_dir)

    captured = driver.invoke(plan, cell, cell_dir, deadline_seconds=0.2)

    assert captured.outcome_state == "timed_out"
    assert captured.stop_reason == "b0_deadline_exceeded"
    record = json.loads(
        (cell_dir / "variant-state" / "sidecar-process" / "active-process.json").read_text(
            encoding="utf-8"
        )
    )
    assert record["status"] == "recovered_terminated"


def test_r6_measurement_uses_plan_artifact_identity(tmp_path: Path) -> None:
    plan = _plan()
    created = initialize_r4_experiment(tmp_path / "state", plan)
    drivers = _drivers(tmp_path)
    cell = plan.cells[0]
    cell_dir = Path(created.experiment_dir) / "cells" / cell.cell_id
    driver = drivers[cell.variant_id]
    driver.prepare(plan, cell, cell_dir)
    captured = driver.invoke(plan, cell, cell_dir, deadline_seconds=30)
    sealed = driver.judge_and_seal(plan, cell, cell_dir, captured)
    measurement = Measurement.model_validate_json(
        (cell_dir / "sealed" / "measurement.json").read_bytes()
    )
    artifact = next(item for item in plan.variants if item.artifact_id == cell.variant_id)

    assert measurement.provenance.variant_artifact_sha256 == artifact.sha256
    assert measurement.provenance.variant_version == artifact.version
    assert sealed.sealed_measurement_sha256 == sha256_file(
        cell_dir / "sealed" / "measurement.json"
    )
