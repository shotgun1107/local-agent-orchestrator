from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from benchmark_runner.contract import ExecutionPlan
from benchmark_runner.plan import (
    assert_plan_integrity,
    build_r0_plan,
    recompute_plan_fingerprint,
)


def test_r0_plan_fingerprint_is_reproducible_and_excludes_created_at() -> None:
    first = build_r0_plan(datetime(2026, 8, 5, 1, tzinfo=timezone.utc))
    later = build_r0_plan(datetime(2026, 8, 5, 2, tzinfo=timezone.utc))
    assert first.plan_fingerprint == later.plan_fingerprint
    assert first.experiment_id == later.experiment_id
    assert recompute_plan_fingerprint(first) == first.plan_fingerprint


def test_experiment_date_does_not_change_plan_fingerprint() -> None:
    first = build_r0_plan(datetime(2026, 8, 5, tzinfo=timezone.utc))
    tomorrow = build_r0_plan(datetime(2026, 8, 5, tzinfo=timezone.utc) + timedelta(days=1))
    assert first.plan_fingerprint == tomorrow.plan_fingerprint
    assert first.experiment_id != tomorrow.experiment_id


def test_decision_policy_change_changes_fingerprint() -> None:
    plan = build_r0_plan(datetime(2026, 8, 5, tzinfo=timezone.utc))
    changed = plan.model_copy(update={"decision_policy": {"r0_only": False}})
    assert recompute_plan_fingerprint(changed) != plan.plan_fingerprint


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("fixture_id", "missing-fixture"),
        ("variant_id", "missing-variant"),
    ],
)
def test_plan_rejects_cells_that_reference_undeclared_inputs(
    field: str,
    value: str,
) -> None:
    plan = build_r0_plan(datetime(2026, 8, 5, tzinfo=timezone.utc))
    payload = plan.model_dump(mode="json")
    payload["cells"][0][field] = value
    with pytest.raises(ValidationError):
        ExecutionPlan.model_validate(payload)


def test_plan_integrity_rejects_nested_payload_mutation() -> None:
    plan = build_r0_plan(datetime(2026, 8, 5, tzinfo=timezone.utc))
    plan.decision_policy["r0_only"] = False
    with pytest.raises(ValueError, match="fingerprint"):
        assert_plan_integrity(plan)


def test_plan_integrity_rejects_experiment_revision_mismatch() -> None:
    plan = build_r0_plan(datetime(2026, 8, 5, tzinfo=timezone.utc))
    changed = plan.model_copy(update={"experiment_id": plan.experiment_id[:-1] + "2"})
    with pytest.raises(ValueError, match="Experiment ID"):
        assert_plan_integrity(changed)
