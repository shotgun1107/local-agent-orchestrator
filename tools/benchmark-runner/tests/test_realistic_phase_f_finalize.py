from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

from benchmark_runner.realistic_docker_judge import (
    SubprocessDockerExecutionBackend,
)
from benchmark_runner.realistic_phase_f import (
    PHASE_F_CELLS_DIRECTORY,
    PHASE_F_CLAIM_FILENAME,
    PhaseFCellLifecycle,
    PhaseFRuntimeMode,
    initialize_phase_f_execution,
    phase_f_status,
    run_next_phase_f_cell,
)
from benchmark_runner.realistic_phase_f_finalize import (
    PHASE_F_CELL_SEAL_FILENAME,
    PHASE_F_FINAL_DIRECTORY,
    PHASE_F_JUDGE_DIRECTORY,
    PHASE_F_MEASUREMENT_FILENAME,
    PHASE_F_SEALED_DIRECTORY,
    FakePhaseFJudgePort,
    PhaseFFinalizationError,
    ProfileRPhaseFCellFinalizerBackend,
    verify_phase_f_cell_finalization,
)
from benchmark_runner.realistic_phase_f_docker import PhaseFDockerJudgePort
from benchmark_runner.realistic_phase_f_ss1 import (
    PROFILE_R_EXPECTED_TASK_IDS,
    ModelFreeClearBoundaryTelemetry,
    ProfileRPhaseFSS1Backend,
)
from benchmark_runner.sdk_common import FakeSdkRuntime, FakeTurnScript
from benchmark_runner.runner import sha256_file


REPOSITORY = Path(__file__).resolve().parents[3]
CANDIDATE_ROOT = (
    REPOSITORY
    / "benchmarks"
    / "artifacts"
    / "sdk-routing-realistic-high-difficulty-phase-e-v1"
)


def _completed_result(task_id: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status_claim": "completed",
        "summary": f"model-free completion for {task_id}",
        "artifacts": [],
        "changed_paths": [],
        "checks_run_by_worker": [],
        "assumptions": [],
        "warnings": [],
        "requested_followup": None,
        "needs_additional_review": False,
        "additional_review_reason": None,
    }


def _runtime_factory(captured: list[FakeSdkRuntime]):
    effects = {
        "R02": (
            (
                "benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml",
                "schema_version: 1\nstage_id: s2-intermediate\n",
            ),
            (
                "benchmarks/manifests/sdk-routing-s2-intermediate.yaml",
                "schema_version: 1\nstatus: fake\n",
            ),
        ),
        "R05": (
            (
                "tools/benchmark-runner/src/benchmark_runner/s2_policy.py",
                '"""Model-free fake S2 policy."""\n',
            ),
        ),
        "R06": (
            (
                "tools/benchmark-runner/src/benchmark_runner/s2_posthoc.py",
                '"""Model-free fake S2 posthoc."""\n',
            ),
        ),
        "R07": (
            (
                "tools/benchmark-runner/tests/test_routing_s2.py",
                "def test_model_free_placeholder():\n    assert True\n",
            ),
        ),
    }

    def create(workspace: Path) -> FakeSdkRuntime:
        runtime = FakeSdkRuntime(
            workspace,
            {
                task_id: FakeTurnScript(
                    effects=effects.get(task_id, ()),
                    result=_completed_result(task_id),
                )
                for task_id in PROFILE_R_EXPECTED_TASK_IDS
            },
        )
        captured.append(runtime)
        return runtime

    return create


def _backend(
    tmp_path: Path,
    runtimes: list[FakeSdkRuntime],
    judge: FakePhaseFJudgePort,
) -> ProfileRPhaseFCellFinalizerBackend:
    worker = ProfileRPhaseFSS1Backend(
        repository=REPOSITORY,
        artifact_root=tmp_path / "backend",
        runtime_mode=PhaseFRuntimeMode.MODEL_FREE_FAKE,
        runtime_factory=_runtime_factory(runtimes),
        telemetry=ModelFreeClearBoundaryTelemetry(),
        environ={},
    )
    return ProfileRPhaseFCellFinalizerBackend(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        worker_backend=worker,
        judge=judge,
    )


def test_fake_ss1_judge_measurement_and_seal_complete_only_cell_one(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    experiment_dir = initialize_phase_f_execution(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        state_root=tmp_path / "state",
    )
    runtimes: list[FakeSdkRuntime] = []
    judge = FakePhaseFJudgePort(check_success=True)
    backend = _backend(tmp_path, runtimes, judge)

    result = run_next_phase_f_cell(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        experiment_dir=experiment_dir,
        backend=backend,
        expected_execution_ordinal=1,
        confirm_cell_dispatch=True,
        confirm_model_usage=False,
    )

    assert result.executed_ordinal == 1
    assert result.actual_model_turns == 0
    assert result.next_execution_ordinal == 2
    assert result.automatic_continuation is False
    assert judge.calls == [result.executed_cell_id]
    assert len(runtimes) == 1
    assert runtimes[0].actual_model_turns == 0

    cell_root = tmp_path / "backend" / result.executed_cell_id
    sealed_root = cell_root / PHASE_F_FINAL_DIRECTORY / PHASE_F_SEALED_DIRECTORY
    seal_path = sealed_root / PHASE_F_CELL_SEAL_FILENAME
    measurement = verify_phase_f_cell_finalization(
        cell_root,
        expected_seal_file_sha256=sha256_file(seal_path),
    )
    assert measurement.outcome.state == "completed"
    assert measurement.outcome.check_success is True
    assert measurement.resource.turn_count.value == 8
    assert measurement.resource.session_count.value == 1
    assert measurement.variant_metrics.values["actual_model_turns"] == 0
    assert measurement.variant_metrics.values["automatic_continuation"] is False
    assert (
        cell_root
        / PHASE_F_FINAL_DIRECTORY
        / PHASE_F_JUDGE_DIRECTORY
        / "result.json"
    ).is_file()
    assert (sealed_root / PHASE_F_MEASUREMENT_FILENAME).is_file()

    status = phase_f_status(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        experiment_dir=experiment_dir,
    )
    assert [item["lifecycle"] for item in status["cells"]] == [
        PhaseFCellLifecycle.SEALED.value,
        PhaseFCellLifecycle.PLANNED.value,
        PhaseFCellLifecycle.PLANNED.value,
        PhaseFCellLifecycle.PLANNED.value,
    ]
    second = status["cells"][1]
    assert not (
        experiment_dir
        / PHASE_F_CELLS_DIRECTORY
        / second["cell_id"]
        / PHASE_F_CLAIM_FILENAME
    ).exists()


def test_final_seal_verifier_rejects_judge_file_tamper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    experiment_dir = initialize_phase_f_execution(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        state_root=tmp_path / "state",
    )
    backend = _backend(tmp_path, [], FakePhaseFJudgePort(check_success=True))
    result = run_next_phase_f_cell(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        experiment_dir=experiment_dir,
        backend=backend,
        expected_execution_ordinal=1,
        confirm_cell_dispatch=True,
        confirm_model_usage=False,
    )
    cell_root = tmp_path / "backend" / result.executed_cell_id
    seal_path = (
        cell_root
        / PHASE_F_FINAL_DIRECTORY
        / PHASE_F_SEALED_DIRECTORY
        / PHASE_F_CELL_SEAL_FILENAME
    )
    expected = sha256_file(seal_path)
    judge_result = (
        cell_root
        / PHASE_F_FINAL_DIRECTORY
        / PHASE_F_JUDGE_DIRECTORY
        / "result.json"
    )
    payload = json.loads(judge_result.read_text(encoding="utf-8"))
    payload["status"] = "CHECKS_FAILED"
    judge_result.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(PhaseFFinalizationError, match="Evidence bytes differ"):
        verify_phase_f_cell_finalization(
            cell_root,
            expected_seal_file_sha256=expected,
        )


@pytest.mark.skipif(
    os.environ.get("LAO_PHASE_F_FULL_DRY_RUN") != "1",
    reason="explicit model-free full Docker dry-run opt-in required",
)
def test_fake_ss1_real_docker_measurement_seals_only_cell_one(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    docker = shutil.which("docker")
    if docker is None:
        pytest.fail("Docker executable is unavailable")
    plan = json.loads((CANDIDATE_ROOT / "execution-plan.json").read_text(encoding="utf-8"))
    source_commit = plan["environment_fingerprint"]["source_commit"]
    experiment_dir = initialize_phase_f_execution(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        state_root=tmp_path / "state",
    )
    runtimes: list[FakeSdkRuntime] = []
    worker = ProfileRPhaseFSS1Backend(
        repository=REPOSITORY,
        artifact_root=tmp_path / "backend",
        runtime_mode=PhaseFRuntimeMode.MODEL_FREE_FAKE,
        runtime_factory=_runtime_factory(runtimes),
        telemetry=ModelFreeClearBoundaryTelemetry(),
        environ={},
    )
    judge = PhaseFDockerJudgePort(
        repository=REPOSITORY,
        raw_root=tmp_path / "docker-raw",
        source_commit=source_commit,
        docker_executable=Path(docker),
        execution_backend=SubprocessDockerExecutionBackend(),
        source_environment=os.environ,
    )
    backend = ProfileRPhaseFCellFinalizerBackend(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        worker_backend=worker,
        judge=judge,
    )

    result = run_next_phase_f_cell(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        experiment_dir=experiment_dir,
        backend=backend,
        expected_execution_ordinal=1,
        confirm_cell_dispatch=True,
        confirm_model_usage=False,
    )

    assert result.executed_ordinal == 1
    assert result.actual_model_turns == 0
    assert result.automatic_continuation is False
    assert result.next_execution_ordinal == 2
    assert len(runtimes) == 1
    assert runtimes[0].actual_model_turns == 0
    cell_root = tmp_path / "backend" / result.executed_cell_id
    seal_path = (
        cell_root
        / PHASE_F_FINAL_DIRECTORY
        / PHASE_F_SEALED_DIRECTORY
        / PHASE_F_CELL_SEAL_FILENAME
    )
    measurement = verify_phase_f_cell_finalization(
        cell_root,
        expected_seal_file_sha256=sha256_file(seal_path),
    )
    assert measurement.outcome.state == "completed"
    assert measurement.outcome.check_success is False
    assert measurement.outcome.failure_kind == "independent_judge_failed"
    assert measurement.variant_metrics.values["judge_kind"] == "docker_property"
    assert measurement.variant_metrics.values["judge_docker_executed"] is True
    assert measurement.variant_metrics.values["judge_model_turns"] == 0
    assert measurement.variant_metrics.values["actual_model_turns"] == 0
    assert measurement.variant_metrics.values["automatic_continuation"] is False
    status = phase_f_status(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        experiment_dir=experiment_dir,
    )
    assert [item["lifecycle"] for item in status["cells"]] == [
        PhaseFCellLifecycle.SEALED.value,
        PhaseFCellLifecycle.PLANNED.value,
        PhaseFCellLifecycle.PLANNED.value,
        PhaseFCellLifecycle.PLANNED.value,
    ]
    second = status["cells"][1]
    assert not (
        experiment_dir
        / PHASE_F_CELLS_DIRECTORY
        / second["cell_id"]
        / PHASE_F_CLAIM_FILENAME
    ).exists()
