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
    PhaseFBackendResult,
    PhaseFCellLifecycle,
    PhaseFDispatchRequest,
    PhaseFRuntimeMode,
    _request_for,
    initialize_phase_f_execution,
    load_verified_phase_f_candidate,
    phase_f_model_turn_receipt,
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
    _verify_adapter_turn_evidence,
    verify_phase_f_cell_finalization,
)
from benchmark_runner.realistic_phase_f_docker import PhaseFDockerJudgePort
from benchmark_runner.realistic_phase_f_ss1 import (
    PROFILE_R_EXPECTED_TASK_IDS,
    ModelFreeClearBoundaryTelemetry,
    ProfileRPhaseFSS1Backend,
)
from benchmark_runner.realistic_routing import canonical_json_bytes, canonical_sha256
from benchmark_runner.sdk_common import FakeSdkRuntime, FakeTurnScript
from benchmark_runner.runner import sha256_bytes, sha256_file


REPOSITORY = Path(__file__).resolve().parents[3]
CANDIDATE_ROOT = (
    REPOSITORY
    / "benchmarks"
    / "artifacts"
    / "sdk-routing-realistic-high-difficulty-phase-e-v17"
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
        ),
        "R03": (
            (
                "benchmarks/fixtures/routing-v1/intermediate/three-stage-config-migration/benchmark-run.yaml",
                "schema_version: 1\ntasks: []\n",
            ),
        ),
        "R04": (
            (
                "benchmarks/fixtures/routing-v1/intermediate/three-stage-incident-analysis/benchmark-run.yaml",
                "schema_version: 1\ntasks: []\n",
            ),
        ),
        "R05": (
            (
                "benchmarks/manifests/sdk-routing-s2-intermediate.yaml",
                "schema_version: 1\nstatus: fake\n",
            ),
        ),
        "R07": (
            (
                "tools/benchmark-runner/src/benchmark_runner/s2_policy.py",
                '"""Model-free fake S2 policy."""\n',
            ),
        ),
        "R09": (
            (
                "tools/benchmark-runner/src/benchmark_runner/s2_posthoc.py",
                '"""Model-free fake S2 posthoc."""\n',
            ),
        ),
        "R11": (
            (
                "tools/benchmark-runner/tests/test_routing_s2.py",
                "def test_model_free_placeholder():\n    assert True\n",
            ),
        ),
        "R12": (
            (
                "tools/benchmark-runner/tests/test_routing_suite.py",
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
    assert measurement.resource.turn_count.value == 13
    assert measurement.resource.session_count.value == 1
    assert measurement.variant_metrics.values["actual_model_turns"] == 0
    assert measurement.variant_metrics.values["failure_classification"] is None
    assert measurement.variant_metrics.values["comparison_valid"] is True
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


def test_judge_product_failure_is_structured_and_comparison_remains_valid(
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
    backend = _backend(tmp_path, [], FakePhaseFJudgePort(check_success=False))

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
    measurement = verify_phase_f_cell_finalization(
        cell_root,
        expected_seal_file_sha256=sha256_file(seal_path),
    )

    assert measurement.outcome.state == "failed"
    assert measurement.outcome.failure_kind == "independent_judge_failed"
    assert measurement.variant_metrics.values["failure_classification"] == (
        "PRODUCT_ASSERTION"
    )
    assert measurement.variant_metrics.values["comparison_valid"] is True
    assert measurement.variant_metrics.values["product_failure_present"] is True
    assert measurement.variant_metrics.values["environment_failure_present"] is False


def test_worker_environment_and_judge_product_failures_are_preserved_as_mixed(
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

    def broken_runtime(workspace: Path) -> FakeSdkRuntime:
        return FakeSdkRuntime(
            workspace,
            {
                "R01": FakeTurnScript(
                    effects=(),
                    result=_completed_result("R01"),
                    terminal_status="failed",
                    error_kind="SyntheticRuntimeFailure",
                )
            },
        )

    worker = ProfileRPhaseFSS1Backend(
        repository=REPOSITORY,
        artifact_root=tmp_path / "backend",
        runtime_mode=PhaseFRuntimeMode.MODEL_FREE_FAKE,
        runtime_factory=broken_runtime,
        telemetry=ModelFreeClearBoundaryTelemetry(),
        environ={},
    )
    backend = ProfileRPhaseFCellFinalizerBackend(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        worker_backend=worker,
        judge=FakePhaseFJudgePort(check_success=False),
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

    assert measurement.outcome.state == "infrastructure_error"
    assert measurement.outcome.failure_kind == "mixed_product_and_environment"
    diagnostic = measurement.variant_metrics.values["failure_diagnostic"]
    assert diagnostic["classification"] == "MIXED_PRODUCT_AND_ENVIRONMENT"
    assert diagnostic["comparison_valid"] is False
    assert diagnostic["product_failure_present"] is True
    assert diagnostic["environment_failure_present"] is True
    assert [node["classification"] for node in diagnostic["nodes"]] == [
        "ENVIRONMENT",
        "PRODUCT_ASSERTION",
    ]


def test_over_budget_worker_result_is_rejected_before_judge(
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

    class OverBudgetWorker:
        runtime_mode = PhaseFRuntimeMode.LIVE_CHATGPT
        artifact_root = tmp_path / "backend"
        evidence_filename = "unused-adapter-evidence.json"

        @staticmethod
        def run_one_cell(request):
            return PhaseFBackendResult(
                experiment_id=request.experiment_id,
                plan_fingerprint=request.plan_fingerprint,
                candidate_seal_sha256=request.candidate_seal_sha256,
                candidate_snapshot_sha256=request.candidate_snapshot_sha256,
                model_turn_ceiling=request.model_turn_ceiling,
                execution_ordinal=request.execution_ordinal,
                cell_id=request.cell_id,
                fixture_id=request.fixture_id,
                variant_id=request.variant_id,
                runtime_mode=PhaseFRuntimeMode.LIVE_CHATGPT,
                request_sha256=request.request_sha256,
                outcome_state="completed",
                actual_model_turns=16,
                sealed_artifact_sha256=sha256_bytes(b"unused"),
                public_summary={},
            )

    judge = FakePhaseFJudgePort(check_success=True)
    backend = ProfileRPhaseFCellFinalizerBackend(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        worker_backend=OverBudgetWorker(),
        judge=judge,
    )

    with pytest.raises(
        PhaseFFinalizationError,
        match="model turns 16 exceed candidate Cell ceiling 15 before Judge",
    ):
        run_next_phase_f_cell(
            repository=REPOSITORY,
            candidate_root=CANDIDATE_ROOT,
            experiment_dir=experiment_dir,
            backend=backend,
            expected_execution_ordinal=1,
            confirm_cell_dispatch=True,
            confirm_model_usage=True,
        )

    assert judge.calls == []
    status = phase_f_status(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        experiment_dir=experiment_dir,
    )
    assert status["stopped"] is True
    assert status["cells"][0]["lifecycle"] == PhaseFCellLifecycle.FAILED.value
    assert status["cells"][0]["failure_type"] == "PhaseFFinalizationError"


def test_evidence_sixteen_result_fifteen_is_rejected_before_judge(
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

    class MismatchedCountWorker:
        runtime_mode = PhaseFRuntimeMode.LIVE_CHATGPT
        artifact_root = tmp_path / "backend"
        evidence_filename = "mismatched-adapter-evidence.json"

        def run_one_cell(self, request):
            cell_root = self.artifact_root / request.cell_id
            (cell_root / "workspace").mkdir(parents=True)
            receipts = [
                phase_f_model_turn_receipt(
                    ordinal=ordinal,
                    task_id=f"R{min(ordinal, 13):02d}",
                    status="accepted",
                    turn_id=f"turn-{ordinal}",
                ).model_dump(mode="json")
                for ordinal in range(1, 17)
            ]
            payload = {
                "schema_version": 1,
                "kind": "phase_f_profile_r_ss1_adapter_evidence",
                "experiment_id": request.experiment_id,
                "cell_id": request.cell_id,
                "request_sha256": request.request_sha256,
                "fixture_id": request.fixture_id,
                "variant_id": request.variant_id,
                "runtime_mode": request.runtime_mode.value,
                "worker_tree_final_sha256": "a" * 64,
                "actual_model_turns": 16,
                "model_turn_accounting": {
                    "schema_version": 1,
                    "basis": "turn_start_requests_issued",
                    "runtime_mode": request.runtime_mode.value,
                    "model_turn_ceiling": request.model_turn_ceiling,
                    "turn_start_attempts": 16,
                    "actual_model_turns": 16,
                    "runtime_reported_model_turns": 16,
                    "receipts": receipts,
                },
                "adapter_outcome_state": "completed",
                "adapter_failure_kind": None,
                "adapter_attempt_count": 1,
                "adapter_raw_payload": {
                    "actual_model_turns": 16,
                    "turns": [{} for _ in range(16)],
                    "boundary_records": [{} for _ in range(16)],
                },
                "adapter_normalized_metrics": {
                    "turn_count": 16,
                    "session_count": 1,
                },
            }
            evidence_bytes = canonical_json_bytes(payload)
            (cell_root / self.evidence_filename).write_bytes(evidence_bytes)
            return PhaseFBackendResult(
                experiment_id=request.experiment_id,
                plan_fingerprint=request.plan_fingerprint,
                candidate_seal_sha256=request.candidate_seal_sha256,
                candidate_snapshot_sha256=request.candidate_snapshot_sha256,
                model_turn_ceiling=request.model_turn_ceiling,
                execution_ordinal=request.execution_ordinal,
                cell_id=request.cell_id,
                fixture_id=request.fixture_id,
                variant_id=request.variant_id,
                runtime_mode=request.runtime_mode,
                request_sha256=request.request_sha256,
                outcome_state="completed",
                actual_model_turns=15,
                sealed_artifact_sha256=sha256_bytes(evidence_bytes),
                public_summary={},
            )

    judge = FakePhaseFJudgePort(check_success=True)
    backend = ProfileRPhaseFCellFinalizerBackend(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        worker_backend=MismatchedCountWorker(),
        judge=judge,
    )

    with pytest.raises(PhaseFFinalizationError, match="turn accounting is invalid"):
        run_next_phase_f_cell(
            repository=REPOSITORY,
            candidate_root=CANDIDATE_ROOT,
            experiment_dir=experiment_dir,
            backend=backend,
            expected_execution_ordinal=1,
            confirm_cell_dispatch=True,
            confirm_model_usage=True,
        )

    assert judge.calls == []


def test_worker_identity_mismatch_is_rejected_before_judge(tmp_path: Path) -> None:
    snapshot = load_verified_phase_f_candidate(REPOSITORY, CANDIDATE_ROOT)
    planned = next(item for item in snapshot.plan.cells if item.execution_ordinal == 1)
    request = _request_for(
        plan=snapshot.plan,
        snapshot=snapshot,
        cell=planned,
        runtime_mode=PhaseFRuntimeMode.LIVE_CHATGPT,
    )

    class WrongIdentityWorker:
        runtime_mode = PhaseFRuntimeMode.LIVE_CHATGPT
        artifact_root = tmp_path / "backend"
        evidence_filename = "unused.json"

        @staticmethod
        def run_one_cell(value):
            return PhaseFBackendResult(
                experiment_id=value.experiment_id,
                plan_fingerprint=value.plan_fingerprint,
                candidate_seal_sha256=value.candidate_seal_sha256,
                candidate_snapshot_sha256=value.candidate_snapshot_sha256,
                model_turn_ceiling=value.model_turn_ceiling,
                execution_ordinal=value.execution_ordinal,
                cell_id=value.cell_id,
                fixture_id="wrong-fixture",
                variant_id=value.variant_id,
                runtime_mode=value.runtime_mode,
                request_sha256=value.request_sha256,
                outcome_state="completed",
                actual_model_turns=1,
                sealed_artifact_sha256="0" * 64,
                public_summary={},
            )

    judge = FakePhaseFJudgePort(check_success=True)
    backend = ProfileRPhaseFCellFinalizerBackend(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        worker_backend=WrongIdentityWorker(),
        judge=judge,
    )

    with pytest.raises(PhaseFFinalizationError, match="identity differs before Judge"):
        backend.run_one_cell(request)

    assert judge.calls == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("top_actual", 2),
        ("raw_actual", 2),
        ("normalized_turns", 2),
        ("turn_record_count", 2),
        ("boundary_record_count", 0),
        ("runtime_reported", 0),
    ],
)
def test_turn_count_mismatch_matrix_is_rejected_before_judge_boundary(
    field: str,
    value: int,
) -> None:
    request_values = {
        "schema_version": 1,
        "kind": "realistic_phase_f_cell_dispatch",
        "experiment_id": "exp_turn_matrix",
        "plan_fingerprint": "1" * 64,
        "candidate_seal_sha256": "2" * 64,
        "candidate_snapshot_sha256": "3" * 64,
        "model_turn_ceiling": 15,
        "execution_ordinal": 1,
        "cell_id": "cell-turn-matrix",
        "fixture_id": "realistic-compat-migration-001",
        "variant_id": "ss1",
        "runtime_mode": "live_chatgpt",
        "automatic_continuation": False,
    }
    request = PhaseFDispatchRequest(
        **request_values,
        request_sha256=canonical_sha256(request_values),
    )
    receipt = phase_f_model_turn_receipt(
        ordinal=1,
        task_id="R01",
        status="accepted",
        turn_id="turn-1",
    ).model_dump(mode="json")
    payload = {
        "experiment_id": request.experiment_id,
        "cell_id": request.cell_id,
        "request_sha256": request.request_sha256,
        "fixture_id": request.fixture_id,
        "variant_id": request.variant_id,
        "runtime_mode": request.runtime_mode.value,
        "actual_model_turns": 1,
        "model_turn_accounting": {
            "schema_version": 1,
            "basis": "turn_start_requests_issued",
            "runtime_mode": request.runtime_mode.value,
            "model_turn_ceiling": request.model_turn_ceiling,
            "turn_start_attempts": 1,
            "actual_model_turns": 1,
            "runtime_reported_model_turns": 1,
            "receipts": [receipt],
        },
        "adapter_raw_payload": {
            "actual_model_turns": 1,
            "turns": [{}],
            "boundary_records": [{}],
        },
        "adapter_normalized_metrics": {"turn_count": 1},
    }
    if field == "top_actual":
        payload["actual_model_turns"] = value
    elif field == "raw_actual":
        payload["adapter_raw_payload"]["actual_model_turns"] = value
    elif field == "normalized_turns":
        payload["adapter_normalized_metrics"]["turn_count"] = value
    elif field == "turn_record_count":
        payload["adapter_raw_payload"]["turns"] = [{} for _ in range(value)]
    elif field == "boundary_record_count":
        payload["adapter_raw_payload"]["boundary_records"] = [
            {} for _ in range(value)
        ]
    else:
        payload["model_turn_accounting"]["runtime_reported_model_turns"] = value

    with pytest.raises(PhaseFFinalizationError):
        _verify_adapter_turn_evidence(
            request=request,
            expected_actual_model_turns=1,
            adapter_payload=payload,
        )


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
    assert measurement.outcome.state == "failed"
    assert measurement.outcome.check_success is False
    assert measurement.outcome.failure_kind == "independent_judge_failed"
    assert measurement.variant_metrics.values["failure_classification"] == (
        "PRODUCT_ASSERTION"
    )
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
