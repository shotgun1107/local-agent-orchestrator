from __future__ import annotations

from pathlib import Path

import pytest
import benchmark_runner.realistic_phase_f as phase_f_module

from benchmark_runner.realistic_phase_f import (
    PHASE_F_CELLS_DIRECTORY,
    PHASE_F_CLAIM_FILENAME,
    PhaseFBackendResult,
    PhaseFCellLifecycle,
    PhaseFControllerError,
    PhaseFDispatchRequest,
    PhaseFRuntimeMode,
    initialize_phase_f_execution,
    phase_f_status,
    run_next_phase_f_cell,
)
from benchmark_runner.runner import sha256_bytes


REPOSITORY = Path(__file__).resolve().parents[3]
CANDIDATE_ROOT = (
    REPOSITORY
    / "benchmarks"
    / "artifacts"
    / "sdk-routing-realistic-high-difficulty-phase-e-v1"
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
