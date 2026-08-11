from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from benchmark_runner.contract import (
    CellLifecycleState,
    CellStateRecord,
    ExecutionPlan,
    MetricStatus,
)
from benchmark_runner.runner import run_r2_b1_fake_cell, verify_sealed_cell

REPOSITORY_ROOT = Path(__file__).parents[3]
MANIFEST_PATH = REPOSITORY_ROOT / "benchmarks" / "manifests" / "b0-b1-frozen.yaml"
B1_ROOT = REPOSITORY_ROOT / "stages" / "b1-sequential"
FROZEN_TIME = datetime(2099, 8, 5, tzinfo=timezone.utc)

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


def _fake_fixture(fixture_id: str) -> dict[str, object]:
    solution = SOLUTIONS[fixture_id]
    return {
        "scenario": "complete",
        "effects": [{"type": "write_file", **solution}],
        "result": {
            "schema_version": 1,
            "status_claim": "completed",
            "summary": "deterministic R2 sealed vertical slice",
            "artifacts": [],
            "changed_paths": [solution["path"]],
            "checks_run_by_worker": [],
            "assumptions": [],
            "warnings": [],
            "requested_followup": None,
        },
    }


@pytest.mark.parametrize("fixture_id", ["code-change", "document-read"])
def test_r2_b1_fake_cell_reaches_independently_judged_seal(
    tmp_path: Path,
    fixture_id: str,
) -> None:
    result = run_r2_b1_fake_cell(
        state_root=tmp_path / "state",
        source_repository=REPOSITORY_ROOT,
        manifest_path=MANIFEST_PATH,
        fixture_id=fixture_id,
        b1_command_prefix=(sys.executable, "-m", "orchestrator"),
        b1_project_root=B1_ROOT,
        b1_schema_root=B1_ROOT / "schemas" / "v1",
        fake_fixture=_fake_fixture(fixture_id),
        benchmark_python=Path(sys.executable),
        git_executable=_git(),
        created_at=FROZEN_TIME,
    )
    cell_dir = Path(result.measurement_path).parents[1]
    state = CellStateRecord.model_validate_json(
        (cell_dir / "cell-state.json").read_bytes()
    )
    measurement = verify_sealed_cell(cell_dir)
    plan = ExecutionPlan.model_validate_json(Path(result.plan_path).read_bytes())

    assert result.actual_model_turns == 0
    assert result.check_success is True
    assert result.outcome_state == "completed"
    assert result.b1_run_id.startswith("run_")
    assert state.state is CellLifecycleState.SEALED
    assert [entry.state for entry in state.history] == [
        CellLifecycleState.PLANNED,
        CellLifecycleState.PREPARED,
        CellLifecycleState.ACTIVE,
        CellLifecycleState.CAPTURED,
        CellLifecycleState.JUDGING,
        CellLifecycleState.SEALED,
    ]
    assert measurement.outcome.check_success is True
    b1_artifact = next(item for item in plan.variants if item.artifact_id == "b1")
    assert b1_artifact.sha256 != "0" * 64
    assert b1_artifact.sha256 == measurement.provenance.variant_artifact_sha256
    assert measurement.resource.turn_count.value == 1
    assert measurement.resource.session_count.value == 1
    assert measurement.resource.attempt_count.value == 1
    assert measurement.resource.token_usage.status is MetricStatus.MEASURED
    assert measurement.resource.token_usage.value == {
        "input_tokens": 10,
        "output_tokens": 5,
        "total_tokens": 15,
    }
    assert measurement.variant_metrics.values["actual_model_turns"] == 0
    assert measurement.variant_metrics.values["b1_session_usage_statuses"] == [
        "measured"
    ]
    assert measurement.effort.startup_action_count.value == 1
    assert measurement.effort.manual_copy_or_relay_count_excluding_start.value == 0
    assert measurement.effort.manual_copy_or_relay_count_including_start.value == 1
    evidence_paths = {item.path for item in measurement.evidence}
    assert "events/interventions.jsonl" in evidence_paths
    assert "raw/adapter-result.json" in evidence_paths
    assert "raw/fake-runtime-input.json" in evidence_paths
    assert "judge/result.json" in evidence_paths
    assert "judge/final.diff" in evidence_paths
    assert all(not path.startswith("variant-state/") for path in evidence_paths)


def test_r2_partial_usage_subtotal_is_sealed_as_unknown(tmp_path: Path) -> None:
    fake_fixture = _fake_fixture("code-change")
    fake_fixture["usage"] = {"status": "unknown"}
    result = run_r2_b1_fake_cell(
        state_root=tmp_path / "state",
        source_repository=REPOSITORY_ROOT,
        manifest_path=MANIFEST_PATH,
        fixture_id="code-change",
        b1_command_prefix=(sys.executable, "-m", "orchestrator"),
        b1_project_root=B1_ROOT,
        b1_schema_root=B1_ROOT / "schemas" / "v1",
        fake_fixture=fake_fixture,
        benchmark_python=Path(sys.executable),
        git_executable=_git(),
        created_at=FROZEN_TIME,
    )
    measurement = verify_sealed_cell(Path(result.measurement_path).parents[1])

    assert measurement.outcome.check_success is True
    assert measurement.resource.token_usage.status is MetricStatus.UNKNOWN
    assert measurement.resource.token_usage.value is None
    assert measurement.variant_metrics.values["b1_report_usage_status"] == (
        "partial_or_unknown"
    )
    assert measurement.variant_metrics.values["b1_token_usage_raw"] == {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
    }
    assert measurement.variant_metrics.values["b1_session_usage_statuses"] == [
        "unknown"
    ]
