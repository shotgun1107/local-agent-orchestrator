from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import benchmark_runner.realistic_phase_f as phase_f_module

from benchmark_runner.realistic_phase_f import (
    PHASE_F_CELLS_DIRECTORY,
    PHASE_F_BACKEND_RESULT_FILENAME,
    PHASE_F_CLAIM_FILENAME,
    PHASE_F_STATE_FILENAME,
    PhaseFBackendResult,
    PhaseFCellLifecycle,
    PhaseFControllerError,
    PhaseFDispatchRequest,
    PhaseFRuntimeMode,
    initialize_phase_f_execution,
    phase_f_status,
    run_next_phase_f_cell,
)
from benchmark_runner.realistic_routing import canonical_json_bytes, canonical_sha256
from benchmark_runner.runner import sha256_bytes


REPOSITORY = Path(__file__).resolve().parents[3]
CANDIDATE_ROOT = (
    REPOSITORY
    / "benchmarks"
    / "artifacts"
    / "sdk-routing-realistic-high-difficulty-phase-e-v1"
)
CANDIDATE_V17_ROOT = (
    REPOSITORY
    / "benchmarks"
    / "artifacts"
    / "sdk-routing-realistic-high-difficulty-phase-e-v17"
)


class FakePhaseFBackend:
    runtime_mode = PhaseFRuntimeMode.MODEL_FREE_FAKE

    def __init__(self) -> None:
        self.calls: list[PhaseFDispatchRequest] = []

    def run_one_cell(self, request: PhaseFDispatchRequest) -> PhaseFBackendResult:
        self.calls.append(request)
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
            runtime_mode=self.runtime_mode,
            request_sha256=request.request_sha256,
            outcome_state="fake_completed",
            actual_model_turns=0,
            sealed_artifact_sha256=sha256_bytes(
                f"fake:{request.request_sha256}".encode("utf-8")
            ),
            public_summary={"fake": True},
        )


class LiveTripwireBackend(FakePhaseFBackend):
    runtime_mode = PhaseFRuntimeMode.LIVE_CHATGPT

    def run_one_cell(self, request: PhaseFDispatchRequest) -> PhaseFBackendResult:
        raise AssertionError("live tripwire backend must not be called")


class RaisingFakeBackend(FakePhaseFBackend):
    def run_one_cell(self, request: PhaseFDispatchRequest) -> PhaseFBackendResult:
        self.calls.append(request)
        raise RuntimeError("model-free backend failure")


class FixedLiveTurnsBackend:
    runtime_mode = PhaseFRuntimeMode.LIVE_CHATGPT

    def __init__(self, actual_model_turns: int) -> None:
        self.actual_model_turns = actual_model_turns
        self.calls: list[PhaseFDispatchRequest] = []

    def run_one_cell(self, request: PhaseFDispatchRequest) -> PhaseFBackendResult:
        self.calls.append(request)
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
            runtime_mode=self.runtime_mode,
            request_sha256=request.request_sha256,
            outcome_state="completed",
            actual_model_turns=self.actual_model_turns,
            sealed_artifact_sha256=sha256_bytes(
                f"live:{request.request_sha256}".encode("utf-8")
            ),
            public_summary={"fake_live_result": True},
        )


def _initialize(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    return initialize_phase_f_execution(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        state_root=tmp_path / "state",
    )


def test_fake_run_dispatches_only_cell_one_and_never_auto_starts_cell_two(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    experiment_dir = _initialize(tmp_path, monkeypatch)
    backend = FakePhaseFBackend()

    result = run_next_phase_f_cell(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        experiment_dir=experiment_dir,
        backend=backend,
        expected_execution_ordinal=1,
        confirm_cell_dispatch=True,
        confirm_model_usage=False,
    )

    assert len(backend.calls) == 1
    assert backend.calls[0].execution_ordinal == 1
    assert backend.calls[0].fixture_id == "realistic-compat-migration-001"
    assert backend.calls[0].variant_id == "ss1"
    assert result.executed_ordinal == 1
    assert result.actual_model_turns == 0
    assert result.next_execution_ordinal == 2
    assert result.automatic_continuation is False

    status = phase_f_status(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        experiment_dir=experiment_dir,
    )
    assert status["sealed_cells"] == 1
    assert status["next_execution_ordinal"] == 2
    assert [item["lifecycle"] for item in status["cells"]] == [
        PhaseFCellLifecycle.SEALED.value,
        PhaseFCellLifecycle.PLANNED.value,
        PhaseFCellLifecycle.PLANNED.value,
        PhaseFCellLifecycle.PLANNED.value,
    ]
    cell_two = status["cells"][1]
    assert not (
        experiment_dir
        / PHASE_F_CELLS_DIRECTORY
        / cell_two["cell_id"]
        / PHASE_F_CLAIM_FILENAME
    ).exists()


def test_redesigned_profile_r_accepts_candidate_ceiling_fifteen(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    experiment_dir = initialize_phase_f_execution(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_V17_ROOT,
        state_root=tmp_path / "state",
    )
    backend = FixedLiveTurnsBackend(15)

    result = run_next_phase_f_cell(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_V17_ROOT,
        experiment_dir=experiment_dir,
        backend=backend,
        expected_execution_ordinal=1,
        confirm_cell_dispatch=True,
        confirm_model_usage=True,
    )

    assert result.actual_model_turns == 15
    status = phase_f_status(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_V17_ROOT,
        experiment_dir=experiment_dir,
    )
    assert status["cells"][0]["lifecycle"] == PhaseFCellLifecycle.SEALED.value
    assert status["cells"][0]["actual_model_turns"] == 15
    assert status["cells"][1]["lifecycle"] == PhaseFCellLifecycle.PLANNED.value
    assert status["automatic_continuation"] is False


def test_result_and_state_rehash_cannot_bypass_external_cell_anchor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    experiment_dir = _initialize(tmp_path, monkeypatch)
    backend = FakePhaseFBackend()
    run_next_phase_f_cell(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        experiment_dir=experiment_dir,
        backend=backend,
        expected_execution_ordinal=1,
        confirm_cell_dispatch=True,
        confirm_model_usage=False,
    )

    result_path = next(
        experiment_dir.joinpath(PHASE_F_CELLS_DIRECTORY).glob(
            f"*/{PHASE_F_BACKEND_RESULT_FILENAME}"
        )
    )
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    result_payload["outcome_state"] = "tampered_but_rehashed"
    result_bytes = canonical_json_bytes(result_payload)
    result_path.write_bytes(result_bytes)

    state_path = experiment_dir / PHASE_F_STATE_FILENAME
    state_payload = json.loads(state_path.read_text(encoding="utf-8"))
    state_payload["cells"][0]["backend_result_sha256"] = sha256_bytes(result_bytes)
    state_values = {
        key: value for key, value in state_payload.items() if key != "state_sha256"
    }
    state_payload["state_sha256"] = canonical_sha256(state_values)
    state_path.write_bytes(canonical_json_bytes(state_payload))

    with pytest.raises(PhaseFControllerError, match="Cell anchor differs"):
        phase_f_status(
            repository=REPOSITORY,
            candidate_root=CANDIDATE_ROOT,
            experiment_dir=experiment_dir,
        )


def test_redesigned_profile_r_rejects_turn_sixteen_and_stops(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    experiment_dir = initialize_phase_f_execution(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_V17_ROOT,
        state_root=tmp_path / "state",
    )
    backend = FixedLiveTurnsBackend(16)

    with pytest.raises(
        PhaseFControllerError,
        match="model turns 16 exceed candidate Cell ceiling 15",
    ):
        run_next_phase_f_cell(
            repository=REPOSITORY,
            candidate_root=CANDIDATE_V17_ROOT,
            experiment_dir=experiment_dir,
            backend=backend,
            expected_execution_ordinal=1,
            confirm_cell_dispatch=True,
            confirm_model_usage=True,
        )

    status = phase_f_status(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_V17_ROOT,
        experiment_dir=experiment_dir,
    )
    assert status["stopped"] is True
    assert status["sealed_cells"] == 0
    assert status["cells"][0]["lifecycle"] == PhaseFCellLifecycle.FAILED.value
    assert status["cells"][0]["failure_type"] == "ModelTurnCeilingExceeded"
    assert status["cells"][1]["lifecycle"] == PhaseFCellLifecycle.PLANNED.value
    assert not any(
        experiment_dir.joinpath(PHASE_F_CELLS_DIRECTORY).glob(
            f"*/{phase_f_module.PHASE_F_BACKEND_RESULT_FILENAME}"
        )
    )


def test_legacy_profile_r_still_rejects_turn_eleven(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    experiment_dir = _initialize(tmp_path, monkeypatch)
    backend = FixedLiveTurnsBackend(11)

    with pytest.raises(
        PhaseFControllerError,
        match="model turns 11 exceed candidate Cell ceiling 10",
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


def test_verified_candidate_snapshot_is_used_after_candidate_path_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = tmp_path / "candidate"
    shutil.copytree(CANDIDATE_V17_ROOT, candidate)
    original_verify = phase_f_module.verify_phase_e_candidate_snapshot
    captured = []

    def verify_then_mutate(repository: Path, candidate_root: Path):
        snapshot = original_verify(repository, candidate_root)
        captured.append(snapshot)
        stage_path = candidate_root / "stage-manifest.json"
        stage_path.write_bytes(b"invalid after verified snapshot")
        return snapshot

    monkeypatch.setattr(
        phase_f_module,
        "verify_phase_e_candidate_snapshot",
        verify_then_mutate,
    )
    loaded = phase_f_module.load_verified_phase_f_candidate(REPOSITORY, candidate)

    assert loaded is captured[0]
    assert loaded.stage.budget.total_turn_ceiling_per_variant == 15
    assert loaded.file_bytes("stage-manifest.json") != b"invalid after verified snapshot"


def test_wrong_expected_ordinal_is_rejected_before_fake_backend(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    experiment_dir = _initialize(tmp_path, monkeypatch)
    backend = FakePhaseFBackend()

    with pytest.raises(PhaseFControllerError, match="next Cell is ordinal 1"):
        run_next_phase_f_cell(
            repository=REPOSITORY,
            candidate_root=CANDIDATE_ROOT,
            experiment_dir=experiment_dir,
            backend=backend,
            expected_execution_ordinal=2,
            confirm_cell_dispatch=True,
            confirm_model_usage=False,
        )

    assert backend.calls == []


def test_explicit_dispatch_confirmation_is_required(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    experiment_dir = _initialize(tmp_path, monkeypatch)
    backend = FakePhaseFBackend()

    with pytest.raises(PhaseFControllerError, match="dispatch confirmation"):
        run_next_phase_f_cell(
            repository=REPOSITORY,
            candidate_root=CANDIDATE_ROOT,
            experiment_dir=experiment_dir,
            backend=backend,
            expected_execution_ordinal=1,
            confirm_cell_dispatch=False,
            confirm_model_usage=False,
        )

    assert backend.calls == []


def test_live_mode_requires_separate_model_confirmation_before_backend(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    experiment_dir = _initialize(tmp_path, monkeypatch)
    backend = LiveTripwireBackend()

    with pytest.raises(PhaseFControllerError, match="model-usage confirmation"):
        run_next_phase_f_cell(
            repository=REPOSITORY,
            candidate_root=CANDIDATE_ROOT,
            experiment_dir=experiment_dir,
            backend=backend,
            expected_execution_ordinal=1,
            confirm_cell_dispatch=True,
            confirm_model_usage=False,
        )

    assert backend.calls == []


def test_controller_source_has_no_concrete_sdk_or_process_backend() -> None:
    source = (
        REPOSITORY
        / "tools"
        / "benchmark-runner"
        / "src"
        / "benchmark_runner"
        / "realistic_phase_f.py"
    ).read_text(encoding="utf-8")
    for forbidden in ("openai_codex", "subprocess", "CodexSdkRuntime", "turn/start"):
        assert forbidden not in source


def test_claim_written_then_state_write_failure_blocks_every_future_dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    experiment_dir = _initialize(tmp_path, monkeypatch)
    backend = FakePhaseFBackend()
    monkeypatch.setattr(
        phase_f_module,
        "atomic_write",
        lambda path, data: (_ for _ in ()).throw(OSError("state write failed")),
    )

    with pytest.raises(OSError, match="state write failed"):
        run_next_phase_f_cell(
            repository=REPOSITORY,
            candidate_root=CANDIDATE_ROOT,
            experiment_dir=experiment_dir,
            backend=backend,
            expected_execution_ordinal=1,
            confirm_cell_dispatch=True,
            confirm_model_usage=False,
        )
    assert backend.calls == []

    with pytest.raises(PhaseFControllerError, match="planned Phase F Cell has dispatch artifacts"):
        run_next_phase_f_cell(
            repository=REPOSITORY,
            candidate_root=CANDIDATE_ROOT,
            experiment_dir=experiment_dir,
            backend=backend,
            expected_execution_ordinal=1,
            confirm_cell_dispatch=True,
            confirm_model_usage=False,
        )
    assert backend.calls == []


def test_backend_exception_marks_failed_and_blocks_every_future_dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    experiment_dir = _initialize(tmp_path, monkeypatch)
    backend = RaisingFakeBackend()

    with pytest.raises(RuntimeError, match="model-free backend failure"):
        run_next_phase_f_cell(
            repository=REPOSITORY,
            candidate_root=CANDIDATE_ROOT,
            experiment_dir=experiment_dir,
            backend=backend,
            expected_execution_ordinal=1,
            confirm_cell_dispatch=True,
            confirm_model_usage=False,
        )
    assert len(backend.calls) == 1

    with pytest.raises(PhaseFControllerError, match="execution is stopped"):
        run_next_phase_f_cell(
            repository=REPOSITORY,
            candidate_root=CANDIDATE_ROOT,
            experiment_dir=experiment_dir,
            backend=backend,
            expected_execution_ordinal=2,
            confirm_cell_dispatch=True,
            confirm_model_usage=False,
        )
    assert len(backend.calls) == 1


def test_result_written_then_sealed_state_failure_blocks_every_future_dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    experiment_dir = _initialize(tmp_path, monkeypatch)
    backend = FakePhaseFBackend()
    original_atomic_write = phase_f_module.atomic_write

    def fail_after_backend_result(path: Path, data: bytes) -> None:
        result_exists = any(
            experiment_dir.joinpath(PHASE_F_CELLS_DIRECTORY).glob(
                f"*/{phase_f_module.PHASE_F_BACKEND_RESULT_FILENAME}"
            )
        )
        if result_exists:
            raise OSError("sealed state write failed")
        original_atomic_write(path, data)

    monkeypatch.setattr(phase_f_module, "atomic_write", fail_after_backend_result)

    with pytest.raises(OSError, match="sealed state write failed"):
        run_next_phase_f_cell(
            repository=REPOSITORY,
            candidate_root=CANDIDATE_ROOT,
            experiment_dir=experiment_dir,
            backend=backend,
            expected_execution_ordinal=1,
            confirm_cell_dispatch=True,
            confirm_model_usage=False,
        )
    assert len(backend.calls) == 1

    with pytest.raises(PhaseFControllerError, match="unsealed Phase F Cell has a backend result"):
        run_next_phase_f_cell(
            repository=REPOSITORY,
            candidate_root=CANDIDATE_ROOT,
            experiment_dir=experiment_dir,
            backend=backend,
            expected_execution_ordinal=2,
            confirm_cell_dispatch=True,
            confirm_model_usage=False,
        )
    assert len(backend.calls) == 1
