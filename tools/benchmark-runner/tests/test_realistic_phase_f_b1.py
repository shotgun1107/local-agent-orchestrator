from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


REPOSITORY = Path(__file__).resolve().parents[3]
B1_SOURCE = REPOSITORY / "stages" / "b1-sequential" / "src"
if str(B1_SOURCE) not in sys.path:
    sys.path.insert(0, str(B1_SOURCE))

from orchestrator.runtime import FakeRuntime

from benchmark_runner.contract import ExecutionPlan
from benchmark_runner.realistic_phase_e import verify_phase_e_candidate
from benchmark_runner.realistic_phase_f import (
    PHASE_F_PLAN_FILENAME,
    PhaseFRuntimeMode,
    _request_for,
)
from benchmark_runner.realistic_phase_f_b1 import (
    PHASE_F_B1_EVIDENCE_FILENAME,
    ProfileRPhaseFB1Backend,
)
from benchmark_runner.realistic_phase_f_finalize import (
    FakePhaseFJudgePort,
    ProfileRPhaseFCellFinalizerBackend,
)
from benchmark_runner.realistic_phase_f_ss1 import (
    ModelFreeClearBoundaryTelemetry,
)


CANDIDATE_ROOT = (
    REPOSITORY
    / "benchmarks"
    / "artifacts"
    / "sdk-routing-realistic-high-difficulty-phase-e-v1"
)


def test_model_free_b1_cell_uses_scheduler_and_variant_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    plan = ExecutionPlan.model_validate_json(
        (CANDIDATE_ROOT / PHASE_F_PLAN_FILENAME).read_bytes()
    )
    candidate_seal = verify_phase_e_candidate(REPOSITORY, CANDIDATE_ROOT)
    planned = next(item for item in plan.cells if item.execution_ordinal == 2)
    request = _request_for(
        plan=plan,
        seal=candidate_seal,
        cell=planned,
        runtime_mode=PhaseFRuntimeMode.MODEL_FREE_FAKE,
    )
    runtimes: list[FakeRuntime] = []

    def runtime_factory(workspace: Path) -> FakeRuntime:
        runtime = FakeRuntime("complete", workspace=workspace)
        runtimes.append(runtime)
        return runtime

    worker = ProfileRPhaseFB1Backend(
        repository=REPOSITORY,
        artifact_root=tmp_path / "backend",
        runtime_mode=PhaseFRuntimeMode.MODEL_FREE_FAKE,
        runtime_factory=runtime_factory,
        telemetry=ModelFreeClearBoundaryTelemetry(),
        check_temp_root=tmp_path / "check-temp",
        environ={},
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
    assert 1 <= runtimes[0].turn_count <= 10
    cell_root = tmp_path / "backend" / request.cell_id
    evidence_path = cell_root / PHASE_F_B1_EVIDENCE_FILENAME
    assert evidence_path.is_file()
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    first_attempt = evidence["adapter_raw_payload"]["report"]["tasks"][0][
        "attempts"
    ][0]
    assert first_attempt["state"] != "RUNNING"
    assert evidence["adapter_raw_payload"]["boundary_records"]
    assert not (tmp_path / "backend" / plan.cells[2].cell_id).exists()
