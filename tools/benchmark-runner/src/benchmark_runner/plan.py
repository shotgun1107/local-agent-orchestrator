from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from benchmark_runner.contract import (
    PRODUCER,
    ArtifactIdentity,
    ExecutionPlan,
    FixtureIdentity,
    PlanSupplement,
    PlannedCell,
    SourceManifest,
    utc_now,
)

ZERO_SHA256 = "0" * 64
ZERO_GIT_ID = "0" * 40


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def recompute_plan_fingerprint(plan: ExecutionPlan) -> str:
    payload = plan.model_dump(
        mode="json",
        exclude={"experiment_id", "plan_fingerprint", "created_at"},
    )
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def assert_plan_integrity(plan: ExecutionPlan) -> None:
    fingerprint = recompute_plan_fingerprint(plan)
    if fingerprint != plan.plan_fingerprint:
        raise ValueError("Execution Plan fingerprint does not match its canonical payload")
    _, experiment_date, short_fingerprint, revision = plan.experiment_id.split("_")
    expected_date = plan.created_at.astimezone(timezone.utc).strftime("%Y%m%d")
    if (
        experiment_date != expected_date
        or short_fingerprint != fingerprint[:8]
        or int(revision) != plan.revision
    ):
        raise ValueError("Experiment ID does not match the Execution Plan fingerprint")


def build_r0_plan(created_at: datetime | None = None) -> ExecutionPlan:
    created = created_at or utc_now()
    if created.tzinfo is None or created.utcoffset() is None:
        raise ValueError("created_at must include a timezone")
    date = created.astimezone(timezone.utc).strftime("%Y%m%d")
    placeholder = ExecutionPlan(
        created_at=created,
        producer=PRODUCER,
        experiment_id=f"exp_{date}_00000000_1",
        plan_fingerprint=ZERO_SHA256,
        revision=1,
        source_manifest=SourceManifest(
            path="r0/fake-manifest.json",
            sha256=ZERO_SHA256,
        ),
        runner=ArtifactIdentity(
            artifact_id="benchmark-runner",
            version="0.1.0",
            sha256=ZERO_SHA256,
        ),
        variants=[
            ArtifactIdentity(
                artifact_id="fake",
                version="0.1.0",
                sha256=ZERO_SHA256,
            )
        ],
        fixtures=[
            FixtureIdentity(
                fixture_id="r0-read-only",
                source_commit=ZERO_GIT_ID,
                git_tree=ZERO_GIT_ID,
            )
        ],
        cells=[
            PlannedCell(
                cell_id="cell_r0-read-only_1_fake",
                block_id="block_r0-read-only_1",
                fixture_id="r0-read-only",
                repetition=1,
                variant_id="fake",
                execution_ordinal=1,
            )
        ],
        seed=0,
        baseline_variant="fake",
        candidate_variants=[],
        primary_metrics=["check_success"],
        decision_policy={"r0_only": True},
        reasoning_control="not_applicable",
        plan_supplemented=[
            PlanSupplement(field="mode", value="r0_fake", source="runner_constant")
        ],
        environment_fingerprint={"surface_kind": "fake", "model_turns": "0"},
    )
    fingerprint = recompute_plan_fingerprint(placeholder)
    plan = placeholder.model_copy(
        update={
            "plan_fingerprint": fingerprint,
            "experiment_id": f"exp_{date}_{fingerprint[:8]}_1",
        }
    )
    assert_plan_integrity(plan)
    return plan


def build_r2_plan(
    *,
    source_manifest_path: str,
    source_manifest_sha256: str,
    fixture_id: str,
    fixture_source_commit: str,
    fixture_git_tree: str,
    runner_sha256: str,
    b1_sha256: str,
    created_at: datetime | None = None,
) -> ExecutionPlan:
    created = created_at or utc_now()
    if created.tzinfo is None or created.utcoffset() is None:
        raise ValueError("created_at must include a timezone")
    date = created.astimezone(timezone.utc).strftime("%Y%m%d")
    placeholder = ExecutionPlan(
        created_at=created,
        producer=PRODUCER,
        experiment_id=f"exp_{date}_00000000_1",
        plan_fingerprint=ZERO_SHA256,
        revision=1,
        source_manifest=SourceManifest(
            path=source_manifest_path,
            sha256=source_manifest_sha256,
        ),
        runner=ArtifactIdentity(
            artifact_id="benchmark-runner",
            version="0.1.0-r2",
            sha256=runner_sha256,
        ),
        variants=[
            ArtifactIdentity(
                artifact_id="b1",
                version="0.1.0-source",
                sha256=b1_sha256,
            )
        ],
        fixtures=[
            FixtureIdentity(
                fixture_id=fixture_id,
                source_commit=fixture_source_commit,
                git_tree=fixture_git_tree,
            )
        ],
        cells=[
            PlannedCell(
                cell_id=f"cell_{fixture_id}_1_b1",
                block_id=f"block_{fixture_id}_1",
                fixture_id=fixture_id,
                repetition=1,
                variant_id="b1",
                execution_ordinal=1,
            )
        ],
        seed=0,
        baseline_variant="b1",
        candidate_variants=[],
        primary_metrics=["check_success"],
        decision_policy={"r2_fake_vertical_slice": True},
        reasoning_control="not_applicable_fake_runtime",
        plan_supplemented=[
            PlanSupplement(
                field="runtime",
                value="fake",
                source="r2_test_control",
            )
        ],
        environment_fingerprint={
            "surface_kind": "b1_cli_fake_runtime",
            "actual_model_turns": "0",
        },
    )
    fingerprint = recompute_plan_fingerprint(placeholder)
    plan = placeholder.model_copy(
        update={
            "plan_fingerprint": fingerprint,
            "experiment_id": f"exp_{date}_{fingerprint[:8]}_1",
        }
    )
    assert_plan_integrity(plan)
    return plan
