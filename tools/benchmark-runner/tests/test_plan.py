from __future__ import annotations

from datetime import datetime, timedelta, timezone

from benchmark_runner.plan import build_r0_plan, recompute_plan_fingerprint


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
