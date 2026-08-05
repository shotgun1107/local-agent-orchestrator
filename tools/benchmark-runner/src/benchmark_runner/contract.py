from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator, model_validator

PRODUCER = "lao-bench/0.1.0"
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def validate_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return value


def validate_relative_path(value: str) -> str:
    if not value or "\\" in value:
        raise ValueError("path must be a non-empty POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or str(path) != value:
        raise ValueError("path must be normalized and stay below its root")
    return value


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PublicEnvelope(StrictModel):
    schema_version: Literal[1] = 1
    kind: str
    created_at: datetime
    producer: Literal[PRODUCER] = PRODUCER

    @field_validator("created_at")
    @classmethod
    def timestamp_has_timezone(cls, value: datetime) -> datetime:
        return validate_timestamp(value)


class SourceManifest(StrictModel):
    path: str
    sha256: Sha256

    _path_is_relative = field_validator("path")(validate_relative_path)


class ArtifactIdentity(StrictModel):
    artifact_id: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9._-]*$")
    version: str = Field(min_length=1)
    sha256: Sha256


class FixtureIdentity(StrictModel):
    fixture_id: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9._-]*$")
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    git_tree: str = Field(pattern=r"^[0-9a-f]{40}$")


class PlannedCell(StrictModel):
    cell_id: str = Field(pattern=r"^cell_[a-z0-9._-]+$")
    block_id: str = Field(pattern=r"^block_[a-z0-9._-]+$")
    fixture_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    repetition: int = Field(ge=1)
    variant_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    execution_ordinal: int = Field(ge=1)


class PlanSupplement(StrictModel):
    field: str = Field(min_length=1)
    value: JsonValue
    source: str = Field(min_length=1)


class ExecutionPlan(PublicEnvelope):
    kind: Literal["execution_plan"] = "execution_plan"
    experiment_id: str = Field(pattern=r"^exp_[0-9]{8}_[0-9a-f]{8}_[1-9][0-9]*$")
    plan_fingerprint: Sha256
    revision: int = Field(ge=1)
    source_manifest: SourceManifest
    runner: ArtifactIdentity
    variants: list[ArtifactIdentity] = Field(min_length=1)
    fixtures: list[FixtureIdentity] = Field(min_length=1)
    cells: list[PlannedCell] = Field(min_length=1)
    seed: int
    baseline_variant: str = Field(min_length=1)
    candidate_variants: list[str]
    primary_metrics: list[str] = Field(min_length=1)
    decision_policy: dict[str, JsonValue]
    reasoning_control: str = Field(min_length=1)
    plan_supplemented: list[PlanSupplement]
    environment_fingerprint: dict[str, str]

    @model_validator(mode="after")
    def ids_are_unique(self) -> ExecutionPlan:
        fixture_ids = [fixture.fixture_id for fixture in self.fixtures]
        variant_ids = [variant.artifact_id for variant in self.variants]
        cell_ids = [cell.cell_id for cell in self.cells]
        ordinals = [cell.execution_ordinal for cell in self.cells]
        if len(fixture_ids) != len(set(fixture_ids)):
            raise ValueError("fixture_id values must be unique")
        if len(variant_ids) != len(set(variant_ids)):
            raise ValueError("variant artifact_id values must be unique")
        if len(cell_ids) != len(set(cell_ids)):
            raise ValueError("cell_id values must be unique")
        if sorted(ordinals) != list(range(1, len(ordinals) + 1)):
            raise ValueError("execution ordinals must be contiguous from one")
        if self.baseline_variant not in variant_ids:
            raise ValueError("baseline_variant must reference a declared variant")
        if len(self.candidate_variants) != len(set(self.candidate_variants)):
            raise ValueError("candidate_variants must be unique")
        if self.baseline_variant in self.candidate_variants:
            raise ValueError("baseline_variant cannot also be a candidate")
        unknown_candidates = set(self.candidate_variants) - set(variant_ids)
        if unknown_candidates:
            raise ValueError("candidate_variants must reference declared variants")
        unknown_cell_fixtures = {cell.fixture_id for cell in self.cells} - set(fixture_ids)
        if unknown_cell_fixtures:
            raise ValueError("every Cell fixture_id must reference a declared fixture")
        unknown_cell_variants = {cell.variant_id for cell in self.cells} - set(variant_ids)
        if unknown_cell_variants:
            raise ValueError("every Cell variant_id must reference a declared variant")
        return self


class MetricStatus(StrEnum):
    MEASURED = "measured"
    DERIVED = "derived"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class MetricValue(StrictModel):
    status: MetricStatus
    value: JsonValue | None = None
    unit: str = Field(min_length=1)
    source: str | None = None
    evidence_ref: str | None = None

    @field_validator("evidence_ref")
    @classmethod
    def evidence_path_is_safe(cls, value: str | None) -> str | None:
        return validate_relative_path(value) if value is not None else None

    @model_validator(mode="after")
    def status_matches_value(self) -> MetricValue:
        has_value = self.value is not None
        if self.status in {MetricStatus.MEASURED, MetricStatus.DERIVED} and not has_value:
            raise ValueError("measured and derived metrics require a value")
        if self.status in {MetricStatus.UNKNOWN, MetricStatus.NOT_APPLICABLE} and has_value:
            raise ValueError("unknown and not_applicable metrics cannot have a value")
        return self


class MeasurementIdentity(StrictModel):
    experiment_id: str
    block_id: str
    cell_id: str
    fixture_id: str
    repetition: int = Field(ge=1)
    variant_id: str
    execution_ordinal: int = Field(ge=1)


class MeasurementProvenance(StrictModel):
    manifest_sha256: Sha256
    fixture_source_commit: str
    fixture_tree_before: str
    fixture_tree_after: str
    runner_commit: str
    variant_version: str
    variant_artifact_sha256: Sha256


class MeasurementEnvironment(StrictModel):
    os: str
    python_version: str
    model: str
    auth_method: str
    reasoning_effort: str
    surface_kind: str
    approval_mode: str
    model_control: str
    reasoning_control: str
    treatment_control: Literal["full", "partial", "not_applicable"]


OutcomeState = Literal[
    "completed",
    "failed",
    "blocked",
    "interrupted",
    "timed_out",
    "infrastructure_error",
]


class MeasurementOutcome(StrictModel):
    state: OutcomeState
    failure_kind: str | None = None
    check_success: bool


class MeasurementEffort(StrictModel):
    variant_execution_seconds: MetricValue
    judge_seconds: MetricValue
    total_wall_clock_seconds: MetricValue
    startup_action_count: MetricValue
    manual_copy_or_relay_count_excluding_start: MetricValue
    manual_copy_or_relay_count_including_start: MetricValue
    manual_recovery_count: MetricValue
    manual_recovery_seconds: MetricValue


class MeasurementResource(StrictModel):
    session_count: MetricValue
    turn_count: MetricValue
    attempt_count: MetricValue
    token_usage: MetricValue


class MeasurementQuality(StrictModel):
    errors_found_by_automatic_checks: MetricValue
    human_errors_after_pass: MetricValue


class MeasurementIntegrity(StrictModel):
    scope_ok: bool
    evidence_hashes_ok: bool
    secret_findings: list[str]


class EvidenceRef(StrictModel):
    path: str
    size: int = Field(ge=0)
    sha256: Sha256

    _path_is_relative = field_validator("path")(validate_relative_path)


class VariantMetrics(StrictModel):
    schema_id: str
    values: dict[str, JsonValue]


class Measurement(PublicEnvelope):
    kind: Literal["measurement"] = "measurement"
    identity: MeasurementIdentity
    provenance: MeasurementProvenance
    environment: MeasurementEnvironment
    outcome: MeasurementOutcome
    effort: MeasurementEffort
    resource: MeasurementResource
    quality: MeasurementQuality
    integrity: MeasurementIntegrity
    evidence: list[EvidenceRef]
    variant_metrics: VariantMetrics

    @model_validator(mode="after")
    def evidence_is_unique_and_sorted(self) -> Measurement:
        paths = [item.path for item in self.evidence]
        if paths != sorted(paths) or len(paths) != len(set(paths)):
            raise ValueError("evidence paths must be unique and sorted")
        return self


InterventionKind = Literal[
    "initial_prompt_copy",
    "b1_start",
    "additional_prompt",
    "correction",
    "manual_retry",
    "recovery_start",
    "recovery_end",
    "session_replacement",
    "status_observation",
    "abort",
]


class InterventionEvent(PublicEnvelope):
    kind: Literal["intervention_event"] = "intervention_event"
    event_id: str = Field(pattern=r"^evt_[a-z0-9._-]+$")
    cell_id: str = Field(pattern=r"^cell_[a-z0-9._-]+$")
    timestamp: datetime
    monotonic_offset_seconds: float = Field(ge=0)
    intervention_kind: InterventionKind
    actor: Literal["user", "runner"]
    duration_seconds: float | None = Field(default=None, ge=0)
    note: str | None = None

    _timestamp_has_timezone = field_validator("timestamp")(validate_timestamp)


class B0Attestation(StrictModel):
    """Internal B0 Evidence; deliberately not a fourth public input Schema."""

    status: Literal["confirmed", "refused"]
    confirmed_at: datetime
    timeline_complete: bool
    model: str | None = None
    reasoning_effort: str | None = None
    surface_kind: str | None = None

    _confirmed_at_has_timezone = field_validator("confirmed_at")(validate_timestamp)

    @model_validator(mode="after")
    def confirmation_is_complete(self) -> B0Attestation:
        if self.status == "confirmed":
            if not self.timeline_complete:
                raise ValueError("confirmed attestation requires a complete timeline")
            if not self.model or not self.reasoning_effort or not self.surface_kind:
                raise ValueError("confirmed attestation requires B0 control values")
        elif self.timeline_complete:
            raise ValueError("refused attestation cannot claim a complete timeline")
        return self


class B0ManualSubmission(StrictModel):
    outcome_state: Literal["completed", "failed", "blocked", "interrupted"]
    attestation: B0Attestation | None = None
    note: str | None = None


class CellLifecycleState(StrEnum):
    PLANNED = "PLANNED"
    PREPARED = "PREPARED"
    ACTIVE = "ACTIVE"
    CAPTURED = "CAPTURED"
    JUDGING = "JUDGING"
    STOPPED = "STOPPED"
    SEALED = "SEALED"


class LifecycleEntry(StrictModel):
    state: CellLifecycleState
    at: datetime


class CellStateRecord(StrictModel):
    cell_id: str
    state: CellLifecycleState
    history: list[LifecycleEntry]
    outcome_state: OutcomeState | None = None
    sealed_measurement_sha256: Sha256 | None = None


PUBLIC_SCHEMAS: dict[str, type[BaseModel]] = {
    "execution-plan.schema.json": ExecutionPlan,
    "measurement.schema.json": Measurement,
    "intervention-event.schema.json": InterventionEvent,
}


def export_public_schemas(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, model in PUBLIC_SCHEMAS.items():
        schema = model.model_json_schema()
        data = json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        (output_dir / filename).write_text(data, encoding="utf-8", newline="\n")
