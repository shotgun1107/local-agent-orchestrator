from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from benchmark_runner.contract import ArtifactIdentity, ExecutionPlan, FixtureIdentity
from benchmark_runner.plan import (
    assert_plan_integrity,
    build_r0_plan,
    build_r4_plan,
    recompute_plan_fingerprint,
)


def _r4_plan(seed: int = 20990805) -> ExecutionPlan:
    return build_r4_plan(
        source_manifest_path="benchmarks/manifests/b0-b1-frozen.yaml",
        source_manifest_sha256="1" * 64,
        fixtures=[
            FixtureIdentity(fixture_id="code-change", source_commit="2" * 40, git_tree="3" * 40),
            FixtureIdentity(fixture_id="document-read", source_commit="4" * 40, git_tree="5" * 40),
        ],
        repetitions=3,
        runner=ArtifactIdentity(artifact_id="benchmark-runner", version="r4", sha256="6" * 64),
        variants=[
            ArtifactIdentity(artifact_id="b0", version="r3", sha256="7" * 64),
            ArtifactIdentity(artifact_id="b1", version="r2", sha256="8" * 64),
        ],
        baseline_variant="b0",
        candidate_variant="b1",
        seed=seed,
        primary_metrics=["check_success", "manual_copy_or_relay_count_excluding_start"],
        decision_policy={"quality_noninferiority": True},
        reasoning_control="not_applicable_fake",
        environment_fingerprint={
            "model": "fake",
            "reasoning_effort": "not_applicable",
            "surface_kind": "r4_fake",
        },
        created_at=datetime(2099, 8, 5, tzinfo=timezone.utc),
    )


def test_r0_plan_fingerprint_is_reproducible_and_excludes_created_at() -> None:
    first = build_r0_plan(datetime(2099, 8, 5, 1, tzinfo=timezone.utc))
    later = build_r0_plan(datetime(2099, 8, 5, 2, tzinfo=timezone.utc))
    assert first.plan_fingerprint == later.plan_fingerprint
    assert first.experiment_id == later.experiment_id
    assert recompute_plan_fingerprint(first) == first.plan_fingerprint


def test_experiment_date_does_not_change_plan_fingerprint() -> None:
    first = build_r0_plan(datetime(2099, 8, 5, tzinfo=timezone.utc))
    tomorrow = build_r0_plan(datetime(2099, 8, 5, tzinfo=timezone.utc) + timedelta(days=1))
    assert first.plan_fingerprint == tomorrow.plan_fingerprint
    assert first.experiment_id != tomorrow.experiment_id


def test_r4_plan_expands_exactly_twelve_cells_in_balanced_blocks() -> None:
    plan = _r4_plan()

    assert len(plan.cells) == 12
    assert [cell.execution_ordinal for cell in plan.cells] == list(range(1, 13))
    blocks: dict[str, list[str]] = {}
    for cell in plan.cells:
        blocks.setdefault(cell.block_id, []).append(cell.variant_id)
    assert len(blocks) == 6
    assert all(set(order) == {"b0", "b1"} for order in blocks.values())
    assert sum(order[0] == "b0" for order in blocks.values()) == 3
    assert sum(order[0] == "b1" for order in blocks.values()) == 3


def test_r4_seed_is_deterministic_and_part_of_plan_identity() -> None:
    first = _r4_plan(20990805)
    same = _r4_plan(20990805)
    changed = _r4_plan(20990806)

    assert first.cells == same.cells
    assert first.plan_fingerprint == same.plan_fingerprint
    assert changed.plan_fingerprint != first.plan_fingerprint


def test_decision_policy_change_changes_fingerprint() -> None:
    plan = build_r0_plan(datetime(2099, 8, 5, tzinfo=timezone.utc))
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
    plan = build_r0_plan(datetime(2099, 8, 5, tzinfo=timezone.utc))
    payload = plan.model_dump(mode="json")
    payload["cells"][0][field] = value
    with pytest.raises(ValidationError):
        ExecutionPlan.model_validate(payload)


def test_plan_integrity_rejects_nested_payload_mutation() -> None:
    plan = build_r0_plan(datetime(2099, 8, 5, tzinfo=timezone.utc))
    plan.decision_policy["r0_only"] = False
    with pytest.raises(ValueError, match="fingerprint"):
        assert_plan_integrity(plan)


def test_plan_integrity_rejects_experiment_revision_mismatch() -> None:
    plan = build_r0_plan(datetime(2099, 8, 5, tzinfo=timezone.utc))
    changed = plan.model_copy(update={"experiment_id": plan.experiment_id[:-1] + "2"})
    with pytest.raises(ValueError, match="Experiment ID"):
        assert_plan_integrity(changed)
