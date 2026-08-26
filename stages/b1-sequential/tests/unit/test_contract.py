from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from orchestrator.contract import ResultEnvelope, RunSpec, canonical_json, new_id
from tests.conftest import make_spec


def test_ids_and_canonical_json_are_stable() -> None:
    assert new_id("run").startswith("run_")
    assert canonical_json({"b": 1, "a": "한글"}) == '{"a":"한글","b":1}'
    with pytest.raises(ValueError):
        new_id("unknown")


@pytest.mark.parametrize("bad_scope", ["../secret", "/absolute", "src\\file.py", ".git/**", ".orchestrator/**"])
def test_write_scope_rejects_unsafe_paths(bad_scope: str) -> None:
    raw = make_spec(workspace_mode="shared_serial_write", write_scope=["src/**"]).model_dump(mode="json")
    raw["tasks"][0]["write_scope"] = [bad_scope]
    with pytest.raises(ValidationError):
        RunSpec.model_validate(raw)


def test_read_only_rejects_write_scope() -> None:
    raw = make_spec().model_dump(mode="json")
    raw["tasks"][0]["write_scope"] = ["src/**"]
    with pytest.raises(ValidationError):
        RunSpec.model_validate(raw)


def test_dependency_cycle_and_unknown_dependency_are_rejected() -> None:
    raw = make_spec(tasks=2).model_dump(mode="json")
    raw["tasks"][0]["depends_on"] = ["T2"]
    with pytest.raises(ValidationError, match="cycle"):
        RunSpec.model_validate(raw)
    raw = make_spec().model_dump(mode="json")
    raw["tasks"][0]["depends_on"] = ["MISSING"]
    with pytest.raises(ValidationError, match="missing dependencies"):
        RunSpec.model_validate(raw)


def test_unknown_fields_and_unproven_criteria_are_rejected() -> None:
    raw = make_spec().model_dump(mode="json")
    raw["surprise"] = True
    with pytest.raises(ValidationError):
        RunSpec.model_validate(raw)
    raw = make_spec().model_dump(mode="json")
    raw["tasks"][0]["completion_criteria"][0]["check_names"] = ["not_assigned"]
    with pytest.raises(ValidationError):
        RunSpec.model_validate(raw)


def test_own_checks_derive_exact_cumulative_check_prefixes() -> None:
    raw = make_spec(tasks=2).model_dump(mode="json")
    for index, task in enumerate(raw["tasks"], 1):
        own_check = f"t{index}_contract"
        task["own_check"] = own_check
        task.pop("check_names")
        task["completion_criteria"][0]["check_names"] = [own_check]
    spec = RunSpec.model_validate(raw)
    assert spec.tasks[0].check_names == ["t1_contract", "diff_check"]
    assert spec.tasks[1].check_names == [
        "t1_contract",
        "t2_contract",
        "diff_check",
    ]

    raw["tasks"][1].pop("own_check")
    with pytest.raises(ValidationError, match="all-or-none"):
        RunSpec.model_validate(raw)


def test_result_envelope_is_strict() -> None:
    valid = {
        "schema_version": 1,
        "status_claim": "completed",
        "summary": "done",
        "artifacts": [],
        "changed_paths": [],
        "checks_run_by_worker": [],
        "assumptions": [],
        "warnings": [],
        "requested_followup": None,
    }
    assert ResultEnvelope.model_validate(valid).status_claim == "completed"
    with pytest.raises(ValidationError):
        ResultEnvelope.model_validate({**valid, "extra": 1})
    with pytest.raises(ValidationError):
        ResultEnvelope.model_validate({**valid, "changed_paths": ["../escape"]})
