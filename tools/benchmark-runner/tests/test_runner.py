from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

import benchmark_runner.runner as runner_module
from benchmark_runner.contract import CellLifecycleState, CellStateRecord, Measurement
from benchmark_runner.runner import (
    WINDOWS_ATOMIC_REPLACE_ATTEMPTS,
    IntegrityError,
    atomic_write,
    run_r0_fake_cell,
    verify_sealed_cell,
)

FROZEN_TIME = datetime(2026, 8, 5, tzinfo=timezone.utc)


def _cell_dir(measurement_path: str) -> Path:
    return Path(measurement_path).parents[1]


def test_atomic_write_retries_transient_windows_permission_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "state.json"
    original_replace = runner_module.os.replace
    attempts = 0
    delays: list[float] = []

    def transient_replace(source: Path, destination: Path) -> None:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise PermissionError(5, "transient Windows sharing lock")
        original_replace(source, destination)

    monkeypatch.setattr(runner_module.os, "name", "nt")
    monkeypatch.setattr(runner_module.os, "replace", transient_replace)
    monkeypatch.setattr(runner_module.time, "sleep", delays.append)

    atomic_write(target, b'{"state":"SEALED"}')

    assert attempts == 3
    assert delays == [0.01, 0.01]
    assert target.read_bytes() == b'{"state":"SEALED"}'
    assert list(tmp_path.glob(".*.tmp")) == []


def test_atomic_write_preserves_failure_after_windows_retry_budget(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "state.json"
    target.write_bytes(b"original")
    attempts = 0
    delays: list[float] = []

    def persistent_replace(_source: Path, _destination: Path) -> None:
        nonlocal attempts
        attempts += 1
        raise PermissionError(5, "persistent Windows access denial")

    monkeypatch.setattr(runner_module.os, "name", "nt")
    monkeypatch.setattr(runner_module.os, "replace", persistent_replace)
    monkeypatch.setattr(runner_module.time, "sleep", delays.append)

    with pytest.raises(PermissionError, match="persistent Windows access denial"):
        atomic_write(target, b"replacement")

    assert attempts == WINDOWS_ATOMIC_REPLACE_ATTEMPTS
    assert delays == [0.01] * (WINDOWS_ATOMIC_REPLACE_ATTEMPTS - 1)
    assert target.read_bytes() == b"original"
    assert list(tmp_path.glob(".*.tmp")) == []


def test_completed_fake_cell_reaches_sealed_with_valid_hashes(tmp_path: Path) -> None:
    result = run_r0_fake_cell(tmp_path, "completed", FROZEN_TIME)
    cell_dir = _cell_dir(result.measurement_path)
    state = CellStateRecord.model_validate_json((cell_dir / "cell-state.json").read_bytes())
    measurement = verify_sealed_cell(cell_dir)

    assert result.model_turns == 0
    assert state.state is CellLifecycleState.SEALED
    assert [entry.state for entry in state.history] == [
        CellLifecycleState.PLANNED,
        CellLifecycleState.PREPARED,
        CellLifecycleState.ACTIVE,
        CellLifecycleState.CAPTURED,
        CellLifecycleState.JUDGING,
        CellLifecycleState.SEALED,
    ]
    assert measurement.outcome.state == "completed"
    assert measurement.outcome.check_success is True
    assert measurement.integrity.evidence_hashes_ok is True
    assert not (cell_dir / "workspace").exists()


def test_failed_fake_cell_is_sealed_but_not_successful(tmp_path: Path) -> None:
    result = run_r0_fake_cell(tmp_path, "failed", FROZEN_TIME)
    cell_dir = _cell_dir(result.measurement_path)
    state = CellStateRecord.model_validate_json((cell_dir / "cell-state.json").read_bytes())
    measurement = Measurement.model_validate_json(Path(result.measurement_path).read_bytes())

    assert state.state is CellLifecycleState.SEALED
    assert state.outcome_state == "failed"
    assert measurement.outcome.state == "failed"
    assert measurement.outcome.check_success is False
    assert measurement.quality.errors_found_by_automatic_checks.value == 1
    verify_sealed_cell(cell_dir)


def test_evidence_tampering_is_detected(tmp_path: Path) -> None:
    result = run_r0_fake_cell(tmp_path, "completed", FROZEN_TIME)
    cell_dir = _cell_dir(result.measurement_path)
    with (cell_dir / "raw" / "fake-result.json").open("ab") as handle:
        handle.write(b" ")
    with pytest.raises(IntegrityError, match="Evidence hash mismatch"):
        verify_sealed_cell(cell_dir)


def test_measurement_tampering_is_detected(tmp_path: Path) -> None:
    result = run_r0_fake_cell(tmp_path, "completed", FROZEN_TIME)
    cell_dir = _cell_dir(result.measurement_path)
    with Path(result.measurement_path).open("ab") as handle:
        handle.write(b" ")
    with pytest.raises(IntegrityError, match="Measurement hash"):
        verify_sealed_cell(cell_dir)


def test_execution_plan_tampering_is_detected(tmp_path: Path) -> None:
    result = run_r0_fake_cell(tmp_path, "completed", FROZEN_TIME)
    cell_dir = _cell_dir(result.measurement_path)
    plan_path = cell_dir.parents[1] / "execution-plan.json"
    plan = plan_path.read_text(encoding="utf-8")
    tampered = plan.replace('"r0_only":true', '"r0_only":false')
    assert tampered != plan
    plan_path.write_text(tampered, encoding="utf-8")
    with pytest.raises(IntegrityError, match="Execution Plan"):
        verify_sealed_cell(cell_dir)


def test_existing_experiment_is_not_overwritten(tmp_path: Path) -> None:
    run_r0_fake_cell(tmp_path, "completed", FROZEN_TIME)
    with pytest.raises(FileExistsError):
        run_r0_fake_cell(tmp_path, "completed", FROZEN_TIME)
