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
                artifact_id="r0-fake",
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
    return placeholder.model_copy(
        update={
            "plan_fingerprint": fingerprint,
            "experiment_id": f"exp_{date}_{fingerprint[:8]}_1",
        }
    )
