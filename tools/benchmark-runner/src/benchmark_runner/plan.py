from __future__ import annotations

import hashlib
import json
import random
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


def build_r3_plan(
    *,
    source_manifest_path: str,
    source_manifest_sha256: str,
    fixture_id: str,
    fixture_source_commit: str,
    fixture_git_tree: str,
    runner_sha256: str,
    b0_sha256: str,
    model: str,
    reasoning_effort: str,
    surface_kind: str,
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
            version="0.1.0-r3",
            sha256=runner_sha256,
        ),
        variants=[
            ArtifactIdentity(
                artifact_id="b0",
                version="0.1.0-r3-manual",
                sha256=b0_sha256,
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
                cell_id=f"cell_{fixture_id}_1_b0",
                block_id=f"block_{fixture_id}_1",
                fixture_id=fixture_id,
                repetition=1,
                variant_id="b0",
                execution_ordinal=1,
            )
        ],
        seed=0,
        baseline_variant="b0",
        candidate_variants=[],
        primary_metrics=[
            "check_success",
            "manual_copy_or_relay_count_excluding_start",
        ],
        decision_policy={
            "r3_manual_vertical_slice": True,
            "primary_intervention_metric_excludes_start": True,
        },
        reasoning_control=reasoning_effort,
        plan_supplemented=[
            PlanSupplement(
                field="b0_measurement_authority",
                value="runner_intervention_events_plus_user_attestation",
                source="frozen_design_r3",
            )
        ],
        environment_fingerprint={
            "model": model,
            "reasoning_effort": reasoning_effort,
            "surface_kind": surface_kind,
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


def build_r4_plan(
    *,
    source_manifest_path: str,
    source_manifest_sha256: str,
    fixtures: list[FixtureIdentity],
    repetitions: int,
    runner: ArtifactIdentity,
    variants: list[ArtifactIdentity],
    baseline_variant: str,
    candidate_variant: str,
    seed: int,
    primary_metrics: list[str],
    decision_policy: dict[str, object],
    reasoning_control: str,
    environment_fingerprint: dict[str, str],
    created_at: datetime | None = None,
    revision: int = 1,
) -> ExecutionPlan:
    """Build the full balanced B0/B1 plan; all experiment choices are explicit inputs."""

    if repetitions < 1:
        raise ValueError("repetitions must be positive")
    if revision < 1:
        raise ValueError("revision must be positive")
    variant_ids = [variant.artifact_id for variant in variants]
    if len(variant_ids) != len(set(variant_ids)):
        raise ValueError("R4 variant artifact IDs must be unique")
    if baseline_variant not in variant_ids or candidate_variant not in variant_ids:
        raise ValueError("R4 baseline and candidate must have artifact identities")
    if baseline_variant == candidate_variant:
        raise ValueError("R4 baseline and candidate must differ")
    if not fixtures:
        raise ValueError("R4 requires at least one fixture")
    block_inputs = [
        (fixture, repetition)
        for repetition in range(1, repetitions + 1)
        for fixture in fixtures
    ]
    block_count = len(block_inputs)
    if block_count % 2:
        raise ValueError("balanced order requires an even number of Blocks")
    randomizer = random.Random(seed)
    baseline_first = set(randomizer.sample(range(block_count), block_count // 2))
    cells: list[PlannedCell] = []
    ordinal = 1
    for block_index, (fixture, repetition) in enumerate(block_inputs):
        ordered_variants = (
            (baseline_variant, candidate_variant)
            if block_index in baseline_first
            else (candidate_variant, baseline_variant)
        )
        block_id = f"block_{fixture.fixture_id}_{repetition}"
        for variant_id in ordered_variants:
            cells.append(
                PlannedCell(
                    cell_id=f"cell_{fixture.fixture_id}_{repetition}_{variant_id}",
                    block_id=block_id,
                    fixture_id=fixture.fixture_id,
                    repetition=repetition,
                    variant_id=variant_id,
                    execution_ordinal=ordinal,
                )
            )
            ordinal += 1

    created = created_at or utc_now()
    if created.tzinfo is None or created.utcoffset() is None:
        raise ValueError("created_at must include a timezone")
    date = created.astimezone(timezone.utc).strftime("%Y%m%d")
    placeholder = ExecutionPlan(
        created_at=created,
        producer=PRODUCER,
        experiment_id=f"exp_{date}_00000000_{revision}",
        plan_fingerprint=ZERO_SHA256,
        revision=revision,
        source_manifest=SourceManifest(
            path=source_manifest_path,
            sha256=source_manifest_sha256,
        ),
        runner=runner,
        variants=variants,
        fixtures=fixtures,
        cells=cells,
        seed=seed,
        baseline_variant=baseline_variant,
        candidate_variants=[candidate_variant],
        primary_metrics=primary_metrics,
        decision_policy=decision_policy,
        reasoning_control=reasoning_control,
        plan_supplemented=[
            PlanSupplement(
                field="baseline_variant",
                value=baseline_variant,
                source="user_before_first_cell",
            ),
            PlanSupplement(
                field="candidate_variants",
                value=[candidate_variant],
                source="user_before_first_cell",
            ),
            PlanSupplement(
                field="seed",
                value=seed,
                source="user_before_first_cell",
            ),
            PlanSupplement(
                field="decision_policy",
                value=decision_policy,
                source="user_before_first_cell",
            ),
            PlanSupplement(
                field="reasoning_control",
                value=reasoning_control,
                source="user_before_first_cell",
            ),
            PlanSupplement(
                field="wall_clock_seconds",
                value={
                    "primary": "variant_execution_seconds",
                    "operational": "total_wall_clock_seconds",
                },
                source="frozen_design_section_16_4",
            ),
        ],
        environment_fingerprint=environment_fingerprint,
    )
    fingerprint = recompute_plan_fingerprint(placeholder)
    plan = placeholder.model_copy(
        update={
            "plan_fingerprint": fingerprint,
            "experiment_id": f"exp_{date}_{fingerprint[:8]}_{revision}",
        }
    )
    assert_plan_integrity(plan)
    baseline_first_count = sum(
        1
        for index in range(0, len(plan.cells), 2)
        if plan.cells[index].variant_id == baseline_variant
    )
    if baseline_first_count * 2 != block_count:
        raise AssertionError("R4 block order is not balanced")
    return plan


def build_sdk_controlled_plan(
    *,
    source_manifest_path: str,
    source_manifest_sha256: str,
    fixtures: list[FixtureIdentity],
    runner: ArtifactIdentity,
    variants: list[ArtifactIdentity],
    cells: list[PlannedCell],
    baseline_variant: str,
    candidate_variants: list[str],
    decision_policy: dict[str, object],
    environment_fingerprint: dict[str, str],
    created_at: datetime | None = None,
    revision: int = 1,
    seed: int = 0,
) -> ExecutionPlan:
    """Build an explicit C0/C1/C2/B1 plan without inventing Cell order."""

    if revision < 1:
        raise ValueError("SDK-controlled Plan revision must be positive")
    if not fixtures:
        raise ValueError("SDK-controlled Plan requires at least one fixture")
    if not variants:
        raise ValueError("SDK-controlled Plan requires at least one variant")
    if not cells:
        raise ValueError("SDK-controlled Plan requires at least one Cell")
    created = created_at or utc_now()
    if created.tzinfo is None or created.utcoffset() is None:
        raise ValueError("created_at must include a timezone")
    date = created.astimezone(timezone.utc).strftime("%Y%m%d")
    placeholder = ExecutionPlan(
        created_at=created,
        producer=PRODUCER,
        experiment_id=f"exp_{date}_00000000_{revision}",
        plan_fingerprint=ZERO_SHA256,
        revision=revision,
        source_manifest=SourceManifest(
            path=source_manifest_path,
            sha256=source_manifest_sha256,
        ),
        runner=runner,
        variants=variants,
        fixtures=fixtures,
        cells=cells,
        seed=seed,
        baseline_variant=baseline_variant,
        candidate_variants=candidate_variants,
        primary_metrics=[
            "check_success",
            "turn_count",
            "token_usage",
            "total_wall_clock_seconds",
        ],
        decision_policy=decision_policy,
        reasoning_control="low_explicit_each_turn",
        plan_supplemented=[
            PlanSupplement(
                field="track",
                value="sdk_controlled_nonlive_gate",
                source="frozen_design_section_17",
            ),
            PlanSupplement(
                field="cell_order",
                value=[cell.cell_id for cell in cells],
                source="explicit_builder_input",
            ),
            PlanSupplement(
                field="actual_model_turns",
                value=0,
                source="nonlive_runtime_guard",
            ),
        ],
        environment_fingerprint=environment_fingerprint,
    )
    fingerprint = recompute_plan_fingerprint(placeholder)
    plan = placeholder.model_copy(
        update={
            "plan_fingerprint": fingerprint,
            "experiment_id": f"exp_{date}_{fingerprint[:8]}_{revision}",
        }
    )
    assert_plan_integrity(plan)
    return plan
