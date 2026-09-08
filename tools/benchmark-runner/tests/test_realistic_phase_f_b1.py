from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest


REPOSITORY = Path(__file__).resolve().parents[3]
GIT_EXECUTABLE = Path(shutil.which("git") or "git").resolve()
B1_SOURCE = REPOSITORY / "stages" / "b1-sequential" / "src"
if str(B1_SOURCE) not in sys.path:
    sys.path.insert(0, str(B1_SOURCE))

from orchestrator.runtime import FakeRuntime

from benchmark_runner.realistic_phase_f import (
    PhaseFRuntimeMode,
    _request_for,
    load_verified_phase_f_candidate,
)
from benchmark_runner.realistic_phase_f_b1 import (
    PHASE_F_B1_EVIDENCE_FILENAME,
    ProfileRPhaseFB1Backend,
    PhaseFB1BackendError,
    _BudgetedB1Runtime,
    _b1_adapter_outcome,
)
from benchmark_runner.realistic_phase_f_finalize import (
    FakePhaseFJudgePort,
    ProfileRPhaseFCellFinalizerBackend,
    verify_phase_f_cell_finalization,
)
from benchmark_runner.realistic_phase_f_sdk import PhaseFConfigurationDriftError
from benchmark_runner.realistic_phase_f_ss1 import (
    ModelFreeClearBoundaryTelemetry,
)


CANDIDATE_ROOT = (
    REPOSITORY
    / "benchmarks"
    / "artifacts"
    / "sdk-routing-realistic-high-difficulty-phase-e-v1"
)


def test_b1_environment_failure_is_not_labeled_as_product_failure() -> None:
    report = {
        "tasks": [
            {
                "attempts": [
                    {"failure_kind": "check_environment", "state": "FAILED"}
                ]
            }
        ]
    }

    assert _b1_adapter_outcome("FAILED", report) == (
        "infrastructure_error",
        "check_environment",
    )
    assert _b1_adapter_outcome(
        "FAILED",
        {"tasks": [{"attempts": [{"failure_kind": "check_failed"}]}]},
    ) == ("failed", "b1_failed")
    assert _b1_adapter_outcome(
        "FAILED",
        {"tasks": [{"attempts": [{"failure_kind": "check_mixed"}]}]},
    ) == ("infrastructure_error", "check_mixed")
    assert _b1_adapter_outcome(
        "FAILED",
        {"tasks": [{"attempts": [{"failure_kind": "check_unknown"}]}]},
    ) == ("infrastructure_error", "check_unknown")
    assert _b1_adapter_outcome(
        "BLOCKED",
        {"tasks": [{"attempts": [{"failure_kind": "dispatch_uncertain"}]}]},
    ) == ("infrastructure_error", "b1_dispatch_uncertain")


@pytest.mark.parametrize("judge_passes", [True, False])
def test_config_dispatch_failure_remains_environment_failure_through_sealing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, judge_passes: bool,
) -> None:
    """Exercise scheduler -> adapter -> finalizer without a real SDK or live state."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    snapshot = load_verified_phase_f_candidate(REPOSITORY, CANDIDATE_ROOT)
    planned = snapshot.plan.cells[1]
    request = _request_for(plan=snapshot.plan, snapshot=snapshot, cell=planned,
                          runtime_mode=PhaseFRuntimeMode.MODEL_FREE_FAKE)

    class ConfigDriftRuntime(FakeRuntime):
        def start_session(self, task_envelope, runtime_profile):
            raise PhaseFConfigurationDriftError("Phase F configuration changed after preflight")

    worker = ProfileRPhaseFB1Backend(
        repository=REPOSITORY, artifact_root=tmp_path / "backend",
        runtime_mode=PhaseFRuntimeMode.MODEL_FREE_FAKE,
        runtime_factory=lambda workspace: ConfigDriftRuntime("complete", workspace=workspace),
        telemetry=ModelFreeClearBoundaryTelemetry(), check_temp_root=tmp_path / "check-temp",
        environ={}, git_executable=GIT_EXECUTABLE, source_environment=os.environ,
    )
    backend = ProfileRPhaseFCellFinalizerBackend(
        repository=REPOSITORY, candidate_root=CANDIDATE_ROOT,
        worker_backend=worker, judge=FakePhaseFJudgePort(check_success=judge_passes),
    )
    result = backend.run_one_cell(request)
    root = tmp_path / "backend" / planned.cell_id
    adapter = json.loads((root / PHASE_F_B1_EVIDENCE_FILENAME).read_bytes())
    assert adapter["adapter_outcome_state"] == "infrastructure_error"
    assert adapter["adapter_failure_kind"] == "b1_dispatch_uncertain"
    metrics = adapter["adapter_normalized_metrics"]
    assert metrics["environment_failure_present"] is True
    assert metrics["comparison_valid"] is False and metrics["b1_invalid_environment"] is True
    assert metrics["b1_retry_count"] == metrics["b1_resume_count"] == 0
    attempts = adapter["adapter_raw_payload"]["report"]["tasks"][0]["attempts"]
    assert len(attempts) == 1 and attempts[0]["failure_kind"] == "dispatch_uncertain"
    assert result.actual_model_turns == adapter["actual_model_turns"] == 0
    measurement = verify_phase_f_cell_finalization(root, expected_seal_file_sha256=result.sealed_artifact_sha256)
    assert measurement.outcome.state == "infrastructure_error"
    assert measurement.variant_metrics.values["failure_classification"] == (
        "ENVIRONMENT" if judge_passes else "MIXED_PRODUCT_AND_ENVIRONMENT")
    assert measurement.variant_metrics.values["comparison_valid"] is False
    assert measurement.variant_metrics.values["environment_failure_present"] is True


def test_model_free_b1_cell_uses_scheduler_and_variant_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    snapshot = load_verified_phase_f_candidate(REPOSITORY, CANDIDATE_ROOT)
    plan = snapshot.plan
    planned = next(item for item in plan.cells if item.execution_ordinal == 2)
    request = _request_for(
        plan=plan,
        snapshot=snapshot,
        cell=planned,
        runtime_mode=PhaseFRuntimeMode.MODEL_FREE_FAKE,
    )
    runtimes: list[FakeRuntime] = []

    def runtime_factory(workspace: Path) -> FakeRuntime:
        runtime = FakeRuntime("complete", workspace=workspace)
        runtimes.append(runtime)
        return runtime

    artifact_root = tmp_path / "backend"
    check_temp_root = Path(tempfile.gettempdir()) / f"pfb{tmp_path.name[-4:]}"
    if check_temp_root.exists():
        shutil.rmtree(check_temp_root)
    worker = ProfileRPhaseFB1Backend(
        repository=REPOSITORY,
        artifact_root=artifact_root,
        runtime_mode=PhaseFRuntimeMode.MODEL_FREE_FAKE,
        runtime_factory=runtime_factory,
        telemetry=ModelFreeClearBoundaryTelemetry(),
        check_temp_root=check_temp_root,
        protected_execution_roots=(CANDIDATE_ROOT, tmp_path / "phase-f-state"),
        environ={},
        git_executable=GIT_EXECUTABLE,
        source_environment={
            "PATH": str(GIT_EXECUTABLE.parent),
            **(
                {"SYSTEMROOT": os.environ["SYSTEMROOT"]}
                if os.name == "nt"
                else {}
            ),
        },
    )
    backend = ProfileRPhaseFCellFinalizerBackend(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        worker_backend=worker,
        judge=FakePhaseFJudgePort(check_success=True),
    )

    result = backend.run_one_cell(request)

    assert result.variant_id == "b1"
    assert result.execution_ordinal == 2
    assert result.actual_model_turns == 0
    assert result.public_summary["automatic_continuation"] is False
    assert result.public_summary["final_cell_sealed"] is True
    assert len(runtimes) == 1
    assert 1 <= runtimes[0].turn_count <= 15
    cell_root = artifact_root / request.cell_id
    evidence_path = cell_root / PHASE_F_B1_EVIDENCE_FILENAME
    assert evidence_path.is_file()
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    first_attempt = evidence["adapter_raw_payload"]["report"]["tasks"][0][
        "attempts"
    ][0]
    assert first_attempt["state"] != "RUNNING"
    assert evidence["adapter_raw_payload"]["boundary_records"]
    assert len(evidence["git_provenance"]["git_executable_sha256"]) == 64
    check_records = evidence["adapter_raw_payload"]["check_records"]
    assert len(check_records) >= 1
    assert all(
        "failure_classification" in item
        and "failure_classification_source" in item
        and "diagnostic_result" in item
        for item in check_records
    )
    observed_task_keys = {item["task_external_key"] for item in check_records}
    assert "R01" in observed_task_keys
    assert observed_task_keys <= {
        f"R{ordinal:02d}" for ordinal in range(1, 14)
    }
    assert not (artifact_root / plan.cells[2].cell_id).exists()
    shutil.rmtree(check_temp_root)
    assert not check_temp_root.exists()


def test_b1_budget_wrapper_blocks_eleventh_turn_before_delegate_call() -> None:
    class CountingRuntime:
        def __init__(self) -> None:
            self.calls = 0

        @property
        def actual_model_turns(self) -> int:
            return self.calls

        def start_turn(self, session_handle, task_envelope):
            self.calls += 1
            from orchestrator.runtime import TurnHandle

            return TurnHandle(
                id=f"turn-{self.calls}",
                session=session_handle,
                raw=None,
                turn_no=self.calls,
            )

    delegate = CountingRuntime()
    runtime = _BudgetedB1Runtime(
        delegate,  # type: ignore[arg-type]
        runtime_mode=PhaseFRuntimeMode.LIVE_CHATGPT,
        model_turn_ceiling=10,
    )
    envelope = SimpleNamespace(task_id="R01")
    session = SimpleNamespace(envelope=envelope)

    for _ in range(10):
        runtime.start_turn(session, envelope)  # type: ignore[arg-type]

    with pytest.raises(PhaseFB1BackendError, match="ceiling reached before dispatch"):
        runtime.start_turn(session, envelope)  # type: ignore[arg-type]

    assert delegate.calls == 10
    accounting = runtime.model_turn_accounting()
    assert accounting.actual_model_turns == 10
    assert accounting.turn_start_attempts == 10
    assert len(accounting.receipts) == 10
