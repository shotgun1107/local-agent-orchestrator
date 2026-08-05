from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from benchmark_runner.adapter import B0ManualSession
from benchmark_runner.contract import (
    B0Attestation,
    B0ManualSubmission,
    CellLifecycleState,
    CellStateRecord,
    MetricStatus,
)
from benchmark_runner.runner import run_r3_b0_manual_cell, verify_sealed_cell

REPOSITORY_ROOT = Path(__file__).parents[3]
MANIFEST_PATH = REPOSITORY_ROOT / "benchmarks" / "manifests" / "b0-b1-frozen.yaml"
FROZEN_TIME = datetime(2026, 8, 5, tzinfo=timezone.utc)

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
            "## 미확인\n"
            "- 외부 배포 여부는 확인하지 못했다.\n"
        ),
    },
}


def _git() -> Path:
    executable = shutil.which("git")
    assert executable is not None
    return Path(executable)


def _attestation(*, confirmed: bool = True) -> B0Attestation:
    return B0Attestation(
        status="confirmed" if confirmed else "refused",
        confirmed_at=FROZEN_TIME,
        timeline_complete=confirmed,
        model="fake-b0" if confirmed else None,
        reasoning_effort="not_applicable" if confirmed else None,
        surface_kind="scripted_manual_test" if confirmed else None,
    )


class SuccessfulProvider:
    def __init__(self, fixture_id: str) -> None:
        self.fixture_id = fixture_id

    def collect(self, session: B0ManualSession) -> B0ManualSubmission:
        solution = SOLUTIONS[self.fixture_id]
        target = session.workspace / str(solution["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(solution["content"]), encoding="utf-8", newline="\n")
        session.recorder.record("initial_prompt_copy")
        session.recorder.record("additional_prompt")
        session.recorder.record("correction")
        session.recorder.record("manual_retry")
        session.recorder.record("recovery_start")
        session.recorder.record("recovery_end")
        session.recorder.record("session_replacement")
        session.recorder.record("status_observation")
        return B0ManualSubmission(
            outcome_state="completed",
            attestation=_attestation(),
            note="deterministic fake user completed the fixture",
        )


class MissingAttestationProvider:
    def collect(self, session: B0ManualSession) -> B0ManualSubmission:
        session.recorder.record("initial_prompt_copy")
        return B0ManualSubmission(outcome_state="completed", attestation=None)


class RefusedAttestationProvider:
    def collect(self, session: B0ManualSession) -> B0ManualSubmission:
        session.recorder.record("initial_prompt_copy")
        return B0ManualSubmission(
            outcome_state="completed",
            attestation=_attestation(confirmed=False),
        )


class InvalidB1EventProvider:
    def collect(self, session: B0ManualSession) -> B0ManualSubmission:
        session.recorder.record("initial_prompt_copy")
        session.recorder.record("b1_start")
        return B0ManualSubmission(outcome_state="completed", attestation=_attestation())


class IncompleteRecoveryProvider:
    def collect(self, session: B0ManualSession) -> B0ManualSubmission:
        session.recorder.record("initial_prompt_copy")
        session.recorder.record("recovery_start")
        return B0ManualSubmission(outcome_state="completed", attestation=_attestation())


class CompletedWithoutSolutionProvider:
    def collect(self, session: B0ManualSession) -> B0ManualSubmission:
        session.recorder.record("initial_prompt_copy")
        return B0ManualSubmission(outcome_state="completed", attestation=_attestation())


def _run(tmp_path: Path, provider: object, fixture_id: str = "code-change"):
    return run_r3_b0_manual_cell(
        state_root=tmp_path / "state",
        source_repository=REPOSITORY_ROOT,
        manifest_path=MANIFEST_PATH,
        fixture_id=fixture_id,
        input_provider=provider,  # type: ignore[arg-type]
        benchmark_python=Path(sys.executable),
        git_executable=_git(),
        model="fake-b0",
        reasoning_effort="not_applicable",
        surface_kind="scripted_manual_test",
        auth_method="none",
        approval_mode="none",
        created_at=FROZEN_TIME,
    )


@pytest.mark.parametrize("fixture_id", ["code-change", "document-read"])
def test_r3_b0_fake_user_reaches_independently_judged_seal(
    tmp_path: Path,
    fixture_id: str,
) -> None:
    result = _run(tmp_path, SuccessfulProvider(fixture_id), fixture_id)
    cell_dir = Path(result.measurement_path).parents[1]
    measurement = verify_sealed_cell(cell_dir)
    state = CellStateRecord.model_validate_json(
        (cell_dir / "cell-state.json").read_bytes()
    )

    assert result.runner_model_turns == 0
    assert result.check_success is True
    assert result.outcome_state == "completed"
    assert result.stop_required is False
    assert result.stop_reason is None
    assert state.state is CellLifecycleState.SEALED
    assert measurement.effort.startup_action_count.value == 1
    assert measurement.effort.manual_copy_or_relay_count_excluding_start.value == 3
    assert measurement.effort.manual_copy_or_relay_count_including_start.value == 4
    assert measurement.effort.manual_recovery_count.value == 1
    assert measurement.effort.manual_recovery_seconds.value >= 0
    assert measurement.resource.turn_count.value == 4
    assert measurement.resource.session_count.value == 2
    assert measurement.resource.attempt_count.value == 2
    assert measurement.resource.token_usage.status is MetricStatus.UNKNOWN
    assert measurement.variant_metrics.values["runner_model_turns"] == 0
    assert measurement.variant_metrics.values["measurement_trusted"] is True
    assert measurement.variant_metrics.values["attestation_status"] == "confirmed"
    evidence_paths = {item.path for item in measurement.evidence}
    assert "events/interventions.jsonl" in evidence_paths
    assert "raw/attestation.json" in evidence_paths
    assert "raw/b0-fixed-prompt.md" in evidence_paths
    assert "judge/result.json" in evidence_paths


@pytest.mark.parametrize(
    ("provider", "failure_kind"),
    [
        (MissingAttestationProvider(), "measurement_attestation_missing"),
        (RefusedAttestationProvider(), "measurement_attestation_missing"),
        (InvalidB1EventProvider(), "measurement_event_invalid"),
        (IncompleteRecoveryProvider(), "measurement_event_invalid"),
    ],
)
def test_r3_measurement_failures_are_sealed_and_stop_experiment(
    tmp_path: Path,
    provider: object,
    failure_kind: str,
) -> None:
    result = _run(tmp_path, provider)
    cell_dir = Path(result.measurement_path).parents[1]
    experiment_dir = cell_dir.parents[1]
    measurement = verify_sealed_cell(cell_dir)
    stop = json.loads((experiment_dir / "experiment-stop.json").read_text(encoding="utf-8"))

    assert result.outcome_state == "infrastructure_error"
    assert result.stop_required is True
    assert result.stop_reason == failure_kind
    assert measurement.outcome.failure_kind == failure_kind
    assert measurement.effort.startup_action_count.status is MetricStatus.UNKNOWN
    assert measurement.resource.turn_count.status is MetricStatus.UNKNOWN
    assert measurement.variant_metrics.values["measurement_trusted"] is False
    assert stop["cell_id"] == result.cell_id
    assert stop["stop_reason"] == failure_kind


def test_r3_judge_rejects_worker_completion_claim_and_stops_experiment(
    tmp_path: Path,
) -> None:
    result = _run(tmp_path, CompletedWithoutSolutionProvider())
    measurement = verify_sealed_cell(Path(result.measurement_path).parents[1])

    assert result.outcome_state == "completed"
    assert result.check_success is False
    assert result.stop_required is True
    assert result.stop_reason == "independent_judge_failed"
    assert measurement.outcome.failure_kind == "independent_judge_failed"
    assert measurement.effort.startup_action_count.value == 1
