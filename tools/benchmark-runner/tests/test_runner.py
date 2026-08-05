from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from benchmark_runner.contract import CellLifecycleState, CellStateRecord, Measurement
from benchmark_runner.runner import IntegrityError, run_r0_fake_cell, verify_sealed_cell

FROZEN_TIME = datetime(2026, 8, 5, tzinfo=timezone.utc)


def _cell_dir(measurement_path: str) -> Path:
    return Path(measurement_path).parents[1]


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
