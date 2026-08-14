from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

import pytest


REPOSITORY = Path(__file__).resolve().parents[3]
GIT_EXECUTABLE = Path(shutil.which("git") or "git").resolve()
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

    artifact_root = tmp_path / "backend"
    check_temp_root = (
        Path(tmp_path.anchor)
        / "lao-pfb"
        / tmp_path.name[-12:]
    )
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
    assert 1 <= runtimes[0].turn_count <= 10
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
    observed_task_keys = {item["task_external_key"] for item in check_records}
    assert "R01" in observed_task_keys
    assert observed_task_keys <= {
        f"R{ordinal:02d}" for ordinal in range(1, 9)
    }
    assert not (artifact_root / plan.cells[2].cell_id).exists()
    shutil.rmtree(check_temp_root)
    assert not check_temp_root.exists()
