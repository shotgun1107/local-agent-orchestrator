from __future__ import annotations

import json
import importlib.metadata
from pathlib import Path

import pytest
from pydantic import ValidationError

from orchestrator.contract import (
    ResultEnvelope,
    RunReportEnvelope,
    RunSpec,
    RunStatusEnvelope,
    TaskEnvelope,
)


def test_checked_in_schemas_match_public_contracts() -> None:
    root = Path(__file__).resolve().parents[2] / "schemas" / "v1"
    models = {
        "run-spec.schema.json": RunSpec,
        "task-envelope.schema.json": TaskEnvelope,
        "result-envelope.schema.json": ResultEnvelope,
        "run-status.schema.json": RunStatusEnvelope,
        "run-report.schema.json": RunReportEnvelope,
    }
    for filename, model in models.items():
        expected = model.model_json_schema()
        expected["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        assert json.loads((root / filename).read_text(encoding="utf-8")) == expected


def test_dependency_lock_matches_test_environment() -> None:
    root = Path(__file__).resolve().parents[2]
    locked = {}
    for line in (root / "requirements.lock").read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        name, version = line.split("==", 1)
        locked[name] = version
    assert locked
    for name, expected in locked.items():
        assert importlib.metadata.version(name) == expected


def test_status_and_report_contracts_reject_unknown_fields() -> None:
    status = {
        "schema_version": 1,
        "run_id": "run_example",
        "state": "COMPLETED",
        "turns_used": 0,
        "tasks": [],
        "session_usage_statuses": [],
        "unexpected": True,
    }
    with pytest.raises(ValidationError, match="unexpected"):
        RunStatusEnvelope.model_validate(status)

    report = {
        "schema_version": 1,
        "run_id": "run_example",
        "state": "COMPLETED",
        "project_id": "example",
        "request": "example",
        "metrics": {
            "turns": 0,
            "sessions": 0,
            "tasks": 0,
            "attempts": 0,
            "checks_passed": 0,
            "checks_failed": 0,
            "wall_clock_seconds": 0,
            "usage_status": "partial_or_unknown",
            "token_usage": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
            },
            "decisions": 0,
            "manual_copy_or_relay_count": None,
            "manual_recovery_seconds": None,
            "unexpected": True,
        },
        "tasks": [],
    }
    with pytest.raises(ValidationError, match="unexpected"):
        RunReportEnvelope.model_validate(report)
