from __future__ import annotations

import json
import importlib.metadata
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from orchestrator.contract import (
    ResultEnvelope,
    RunReportEnvelope,
    RunSpec,
    RunStatusEnvelope,
    TaskEnvelope,
)
from orchestrator.schemas import export_public_schemas
from orchestrator.worker import build_task_envelope
from tests.conftest import make_spec


PUBLIC_MODELS = {
    "run-spec.schema.json": RunSpec,
    "task-envelope.schema.json": TaskEnvelope,
    "result-envelope.schema.json": ResultEnvelope,
    "run-status.schema.json": RunStatusEnvelope,
    "run-report.schema.json": RunReportEnvelope,
}


@pytest.mark.parametrize("filename,model", PUBLIC_MODELS.items())
def test_checked_in_schemas_match_public_contracts(filename, model) -> None:
    root = Path(__file__).resolve().parents[2] / "schemas" / "v1"
    expected = model.model_json_schema()
    expected["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    actual = json.loads((root / filename).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(actual)
    assert actual == expected


def exported_validator(tmp_path: Path, filename: str) -> Draft202012Validator:
    target = tmp_path / "exported"
    export_public_schemas(target)
    schema = json.loads((target / filename).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.mark.parametrize("own_check", ["omitted", None, "test_check"])
def test_exported_run_spec_accepts_legacy_and_own_check(tmp_path, own_check) -> None:
    raw = make_spec().model_dump(mode="json")
    if own_check == "omitted":
        raw["tasks"][0].pop("own_check")
    else:
        raw["tasks"][0]["own_check"] = own_check
    RunSpec.model_validate(raw)
    exported_validator(tmp_path, "run-spec.schema.json").validate(raw)


def envelope_payload(remaining_attempts):
    return build_task_envelope(
        make_spec().tasks[0], run_id="run_fixture", task_id="task_fixture",
        attempt_id="attempt_fixture", requirements_version=1, timeout_seconds=10,
        remaining_attempts=remaining_attempts,
    ).model_dump(mode="json")


@pytest.mark.parametrize("remaining_attempts", ["omitted", None, 0, 3])
def test_exported_task_envelope_accepts_finite_and_unlimited_attempts(tmp_path, remaining_attempts) -> None:
    raw = envelope_payload(0 if remaining_attempts == "omitted" else remaining_attempts)
    if remaining_attempts == "omitted":
        raw["limits"].pop("remaining_attempts")
    TaskEnvelope.model_validate(raw)
    exported_validator(tmp_path, "task-envelope.schema.json").validate(raw)


@pytest.mark.parametrize("value", ["", 7])
def test_own_check_schema_does_not_accept_invalid_values(tmp_path, value) -> None:
    raw = make_spec().model_dump(mode="json")
    raw["tasks"][0]["own_check"] = value
    with pytest.raises(ValidationError):
        RunSpec.model_validate(raw)
    assert not exported_validator(tmp_path, "run-spec.schema.json").is_valid(raw)


@pytest.mark.parametrize("value", [-1, "unlimited"])
def test_attempt_limit_schema_does_not_accept_invalid_values(tmp_path, value) -> None:
    raw = envelope_payload(0)
    raw["limits"]["remaining_attempts"] = value
    with pytest.raises(ValidationError):
        TaskEnvelope.model_validate(raw)
    assert not exported_validator(tmp_path, "task-envelope.schema.json").is_valid(raw)


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
