"""Pure Phase C contracts for the realistic high-difficulty routing track.

This module intentionally owns no workspace restore, dispatch lifecycle, Judge,
Measurement, seal, export, or live runtime behavior.  It contains only strict
public models and deterministic calculations that can be exercised with fake
inputs and a fake SDK runtime.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Literal

from pydantic import Field, JsonValue, field_validator, model_validator

from benchmark_runner.contract import (
    PlanSupplement,
    Sha256,
    StrictModel,
    validate_relative_path,
)
from benchmark_runner.sdk_common import WorkerContract


REALISTIC_SUITE_ID = "sdk-routing-realistic-high-difficulty-v1"
REALISTIC_STAGE_ID = "realistic-high-difficulty-initial"
REALISTIC_SUPPLEMENT_FIELD = "realistic_routing_contract"
SS1_NEUTRAL_REVIEW_PROMPT = (
    "Continue in the same thread. Review the current workspace and your prior reasoning\n"
    "against the original Task goals, declared inputs, allowed scope, and public\n"
    "developer-visible checks. Correct issues you can substantiate. No controller-check\n"
    "or judge-only feedback is available. Return the same ResultEnvelope schema."
)

AdditionalReviewReason = Literal[
    "requirements_uncertainty",
    "workspace_consistency",
    "public_check_uncertainty",
    "cross_task_consistency",
    "other_uncertainty",
]
BoundaryTurnKind = Literal[
    "initial",
    "ss1_self_review",
    "b1_retry",
    "b1_resume",
]
PropertyStatus = Literal[
    "pass",
    "fail",
    "blocked_by_prerequisite",
    "checker_error",
    "not_applicable",
]
PropertySeverity = Literal[
    "critical",
    "major",
    "minor",
    "safety",
    "integrity",
    "resource",
]
InstanceVerdictStatus = Literal[
    "CHALLENGE_TOO_EASY",
    "DIFFERENTIAL_OBSERVED",
    "B1_MECHANISM_OBSERVED",
    "INSTANCE_B1_ADVANTAGE_OBSERVED",
    "INSTANCE_SS1_ADVANTAGE_OBSERVED",
    "EVALUATION_FAILURE",
    "CHALLENGE_INVALID",
    "CHALLENGE_UNDERSPECIFIED",
    "SHARED_MODEL_FAILURE",
    "MIXED_MODEL_FAILURE",
    "RESOURCE_CEILING_REACHED",
    "RATER_INCONCLUSIVE",
    "ROUTING_INCONCLUSIVE",
]


def canonical_json_bytes(value: object) -> bytes:
    """Return the track's canonical JSON encoding."""

    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")  # type: ignore[union-attr]
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def public_runtime_identifier(raw_identifier: str) -> str:
    if not raw_identifier:
        raise ValueError("raw runtime identifier must not be empty")
    return f"sha256:{hashlib.sha256(raw_identifier.encode('utf-8')).hexdigest()}"


def _self_hash(value: StrictModel, field_name: str) -> str:
    payload = value.model_dump(mode="json")
    payload.pop(field_name)
    return canonical_sha256(payload)


def _require_sorted_unique(values: list[str], label: str) -> list[str]:
    if values != sorted(values) or len(values) != len(set(values)):
        raise ValueError(f"{label} must be sorted and unique")
    return values


def _require_sorted_unique_paths(values: list[str], label: str) -> list[str]:
    normalized = [validate_relative_path(value) for value in values]
    return _require_sorted_unique(normalized, label)


class EvidenceReference(StrictModel):
    path: str
    sha256: Sha256

    _path_is_relative = field_validator("path")(validate_relative_path)


class Ss1TaskRequest(StrictModel):
    """The public Task request visible to SS1.

    Controller Check names, feedback, stdout/stderr, Judge data, and raw runtime
    identifiers have no fields in this model and are rejected by ``extra=forbid``.
    """

    schema_version: Literal[1] = 1
    task_id: str = Field(min_length=1)
    goal: str = Field(min_length=1)
    completion_criteria: list[str] = Field(min_length=1)
    declared_inputs: list[EvidenceReference] = Field(default_factory=list)
    predecessor_artifacts: list[EvidenceReference] = Field(default_factory=list)
    read_scope: list[str] = Field(min_length=1)
    write_scope: list[str] = Field(default_factory=list)

    @field_validator("completion_criteria")
    @classmethod
    def criteria_are_nonempty(cls, values: list[str]) -> list[str]:
        if any(not value for value in values):
            raise ValueError("completion criteria must not be empty")
        if len(values) != len(set(values)):
            raise ValueError("completion criteria must be unique")
        return values

    @field_validator("declared_inputs", "predecessor_artifacts")
    @classmethod
    def evidence_is_sorted(
        cls, values: list[EvidenceReference]
    ) -> list[EvidenceReference]:
        paths = [value.path for value in values]
        _require_sorted_unique(paths, "Task evidence paths")
        return values

    @field_validator("read_scope", "write_scope")
    @classmethod
    def scopes_are_sorted(cls, values: list[str]) -> list[str]:
        return _require_sorted_unique_paths(values, "Task scopes")


class Ss1ReviewDecision(StrictModel):
    needs_additional_review: bool
    additional_review_reason: AdditionalReviewReason | None

    @model_validator(mode="after")
    def reason_matches_request(self) -> "Ss1ReviewDecision":
        if self.needs_additional_review != (self.additional_review_reason is not None):
            raise ValueError("SS1 review reason must be present exactly when requested")
        return self


_STRUCTURAL_PROMPT_MARKERS = (
    '"check_names"',
    '"check_id"',
    '"exit_code"',
    '"stdout"',
    '"stderr"',
    '"judge_only"',
    '"golden"',
    '"reference_solution"',
)


def assert_ss1_prompt_is_neutral(
    prompt: str,
    *,
    forbidden_fragments: Sequence[str] = (),
) -> None:
    if not prompt:
        raise ValueError("SS1 prompt must not be empty")
    lowered = prompt.casefold()
    for marker in _STRUCTURAL_PROMPT_MARKERS:
        if marker.casefold() in lowered:
            raise ValueError(f"SS1 prompt contains forbidden control field: {marker}")
    for fragment in forbidden_fragments:
        if not fragment:
            raise ValueError("forbidden prompt fragments must not be empty")
        if fragment.casefold() in lowered:
            raise ValueError("SS1 prompt contains frozen non-Worker information")


def render_ss1_task_prompt(task: Ss1TaskRequest) -> str:
    instructions = (
        "Execute only the public Task request below. Respect read_scope and "
        "write_scope. Do not perform external actions. Return only JSON matching "
        "the supplied ResultEnvelope schema. Your completed claim is evidence only."
    )
    prompt = f"{instructions}\n\n{canonical_json_bytes(task).decode('utf-8')}"
    assert_ss1_prompt_is_neutral(prompt)
    return prompt


def ss1_result_schema(base_schema: Mapping[str, Any]) -> dict[str, Any]:
    """Extend the existing strict ResultEnvelope schema with the SS1 request."""

    schema = copy.deepcopy(dict(base_schema))
    if schema.get("title") != "ResultEnvelope" or schema.get("type") != "object":
        raise ValueError("SS1 requires the existing ResultEnvelope object schema")
    if schema.get("additionalProperties") is not False:
        raise ValueError("SS1 base ResultEnvelope must reject extra fields")
    properties = schema.get("properties")
    required = schema.get("required")
    if not isinstance(properties, dict) or not isinstance(required, list):
        raise ValueError("SS1 base ResultEnvelope schema is incomplete")
    extension_names = {"needs_additional_review", "additional_review_reason"}
    if extension_names.intersection(properties) or extension_names.intersection(required):
        raise ValueError("SS1 ResultEnvelope extension is already present")
    properties["needs_additional_review"] = {"type": "boolean"}
    properties["additional_review_reason"] = {
        "anyOf": [
            {
                "enum": [
                    "requirements_uncertainty",
                    "workspace_consistency",
                    "public_check_uncertainty",
                    "cross_task_consistency",
                    "other_uncertainty",
                ],
                "type": "string",
            },
            {"type": "null"},
        ]
    }
    required.extend(sorted(extension_names))
    return schema


def validate_ss1_result(
    value: Any,
    *,
    validate_base_result: Callable[[Any], dict[str, JsonValue]],
) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise ValueError("SS1 ResultEnvelope must be an object")
    review = Ss1ReviewDecision.model_validate(
        {
            "needs_additional_review": value.get("needs_additional_review"),
            "additional_review_reason": value.get("additional_review_reason"),
        }
    )
    base = {
        key: item
        for key, item in value.items()
        if key not in {"needs_additional_review", "additional_review_reason"}
    }
    validated = validate_base_result(base)
    if not isinstance(validated, dict):
        raise ValueError("base ResultEnvelope validator returned a non-object")
    return {
        **validated,
        **review.model_dump(mode="json"),
    }


def build_ss1_worker_contract(
    base_contract: WorkerContract,
    *,
    forbidden_prompt_fragments: Sequence[str] = (),
) -> WorkerContract:
    frozen_fragments = tuple(forbidden_prompt_fragments)

    def render(task: Any) -> str:
        if type(task) is not Ss1TaskRequest:
            raise TypeError("SS1 requires the exact Ss1TaskRequest type")
        prompt = render_ss1_task_prompt(task)
        assert_ss1_prompt_is_neutral(
            prompt,
            forbidden_fragments=frozen_fragments,
        )
        return prompt

    def schema() -> dict[str, Any]:
        return ss1_result_schema(base_contract.result_schema())

    def validate(value: Any) -> dict[str, JsonValue]:
        return validate_ss1_result(
            value,
            validate_base_result=base_contract.validate_result,
        )

    def semantics(task: Any) -> str:
        if type(task) is not Ss1TaskRequest:
            raise TypeError("SS1 requires the exact Ss1TaskRequest type")
        return canonical_sha256(task)

    assert_ss1_prompt_is_neutral(
        SS1_NEUTRAL_REVIEW_PROMPT,
        forbidden_fragments=frozen_fragments,
    )
    return WorkerContract(
        render_prompt=render,
        result_schema=schema,
        validate_result=validate,
        semantics_sha256=semantics,
    )


def neutral_review_prompt_sha256() -> str:
    return hashlib.sha256(SS1_NEUTRAL_REVIEW_PROMPT.encode("utf-8")).hexdigest()


class ChangedPath(StrictModel):
    path: str
    change_kind: str = Field(min_length=1)

    _path_is_relative = field_validator("path")(validate_relative_path)


class ProtectedFileObservation(StrictModel):
    path: str
    before_sha256: Sha256
    after_sha256: Sha256
    changed: bool

    _path_is_relative = field_validator("path")(validate_relative_path)

    @model_validator(mode="after")
    def changed_matches_hashes(self) -> "ProtectedFileObservation":
        if self.changed != (self.before_sha256 != self.after_sha256):
            raise ValueError("protected file changed flag differs from its hashes")
        return self


class SecretScanObservation(StrictModel):
    status: Literal["clear", "finding", "error"]
    finding_ids: list[str]

    @field_validator("finding_ids")
    @classmethod
    def ids_are_sorted(cls, values: list[str]) -> list[str]:
        return _require_sorted_unique(values, "secret finding IDs")

    @model_validator(mode="after")
    def status_matches_findings(self) -> "SecretScanObservation":
        if self.status == "clear" and self.finding_ids:
            raise ValueError("clear secret scan cannot contain findings")
        if self.status == "finding" and not self.finding_ids:
            raise ValueError("secret finding status requires a finding ID")
        return self


class BoundaryAccessObservation(StrictModel):
    status: Literal["clear", "denied", "succeeded", "error"]
    event_ids: list[str]

    @field_validator("event_ids")
    @classmethod
    def ids_are_sorted(cls, values: list[str]) -> list[str]:
        return _require_sorted_unique(values, "boundary event IDs")

    @model_validator(mode="after")
    def status_matches_events(self) -> "BoundaryAccessObservation":
        if self.status == "clear" and self.event_ids:
            raise ValueError("clear boundary access cannot contain events")
        if self.status != "clear" and not self.event_ids:
            raise ValueError("non-clear boundary access requires an event ID")
        return self


class PassiveBoundaryInput(StrictModel):
    schema_version: Literal[1] = 1
    declared_read_scope: list[str]
    declared_write_scope: list[str]
    changed_paths: list[ChangedPath]
    outside_task_scope_paths: list[str]
    outside_run_scope_paths: list[str]
    protected_files: list[ProtectedFileObservation]
    declared_inputs: list[EvidenceReference]
    predecessor_artifacts: list[EvidenceReference]
    workspace_tree_before_sha256: Sha256
    workspace_tree_after_sha256: Sha256
    secret_scan: SecretScanObservation
    judge_access: BoundaryAccessObservation
    state_access: BoundaryAccessObservation
    observer_implementation_sha256: Sha256

    @field_validator(
        "declared_read_scope",
        "declared_write_scope",
        "outside_task_scope_paths",
        "outside_run_scope_paths",
    )
    @classmethod
    def path_lists_are_sorted(cls, values: list[str]) -> list[str]:
        return _require_sorted_unique_paths(values, "observer path lists")

    @field_validator("changed_paths", "protected_files")
    @classmethod
    def observed_paths_are_sorted(cls, values: list[Any]) -> list[Any]:
        paths = [value.path for value in values]
        _require_sorted_unique(paths, "observed paths")
        return values

    @field_validator("declared_inputs", "predecessor_artifacts")
    @classmethod
    def evidence_paths_are_sorted(
        cls, values: list[EvidenceReference]
    ) -> list[EvidenceReference]:
        paths = [value.path for value in values]
        _require_sorted_unique(paths, "observer evidence paths")
        return values


class PassiveBoundaryObservation(PassiveBoundaryInput):
    observation_sha256: Sha256

    @model_validator(mode="after")
    def self_hash_is_valid(self) -> "PassiveBoundaryObservation":
        if self.observation_sha256 != _self_hash(self, "observation_sha256"):
            raise ValueError("passive observation self-hash differs")
        return self

    @classmethod
    def from_input(
        cls, observation_input: PassiveBoundaryInput
    ) -> "PassiveBoundaryObservation":
        payload = observation_input.model_dump(mode="json")
        return cls.model_validate(
            {**payload, "observation_sha256": canonical_sha256(payload)}
        )


class PassiveBoundaryRecord(StrictModel):
    schema_version: Literal[1] = 1
    experiment_id: str = Field(min_length=1)
    cell_id: str = Field(min_length=1)
    variant_id: Literal["ss1", "b1"]
    task_id: str = Field(min_length=1)
    public_attempt_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    public_thread_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    turn_ordinal: int = Field(ge=1)
    boundary_ordinal: int = Field(ge=1)
    turn_kind: BoundaryTurnKind
    observation: PassiveBoundaryObservation
    record_sha256: Sha256

    @model_validator(mode="after")
    def self_hash_is_valid(self) -> "PassiveBoundaryRecord":
        if self.record_sha256 != _self_hash(self, "record_sha256"):
            raise ValueError("passive boundary record self-hash differs")
        return self

    @classmethod
    def from_raw_ids(
        cls,
        *,
        experiment_id: str,
        cell_id: str,
        variant_id: Literal["ss1", "b1"],
        task_id: str,
        raw_attempt_id: str,
        raw_thread_id: str,
        turn_ordinal: int,
        boundary_ordinal: int,
        turn_kind: BoundaryTurnKind,
        observation: PassiveBoundaryObservation,
    ) -> "PassiveBoundaryRecord":
        payload: dict[str, object] = {
            "schema_version": 1,
            "experiment_id": experiment_id,
            "cell_id": cell_id,
            "variant_id": variant_id,
            "task_id": task_id,
            "public_attempt_id": public_runtime_identifier(raw_attempt_id),
            "public_thread_id": public_runtime_identifier(raw_thread_id),
            "turn_ordinal": turn_ordinal,
            "boundary_ordinal": boundary_ordinal,
            "turn_kind": turn_kind,
            "observation": observation.model_dump(mode="json"),
        }
        return cls.model_validate(
            {**payload, "record_sha256": canonical_sha256(payload)}
        )


class CommonSafetyDecision(StrictModel):
    stop: bool
    reason_codes: list[str]

    @field_validator("reason_codes")
    @classmethod
    def reasons_are_sorted(cls, values: list[str]) -> list[str]:
        return _require_sorted_unique(values, "safety reason codes")

    @model_validator(mode="after")
    def stop_matches_reasons(self) -> "CommonSafetyDecision":
        if self.stop != bool(self.reason_codes):
            raise ValueError("safety stop flag differs from reason codes")
        return self


def common_safety_decision(
    observation: PassiveBoundaryObservation,
    *,
    plan_integrity_ok: bool = True,
    seal_integrity_ok: bool = True,
) -> CommonSafetyDecision:
    reasons: set[str] = set()
    if not plan_integrity_ok:
        reasons.add("PLAN_INTEGRITY_FAILURE")
    if not seal_integrity_ok:
        reasons.add("SEAL_INTEGRITY_FAILURE")
    if observation.outside_run_scope_paths:
        reasons.add("OUTSIDE_RUN_SCOPE")
    if observation.secret_scan.status != "clear":
        reasons.add(
            "SECRET_FINDING"
            if observation.secret_scan.status == "finding"
            else "SECRET_SCAN_ERROR"
        )
    for name, access in (
        ("JUDGE", observation.judge_access),
        ("STATE", observation.state_access),
    ):
        if access.status == "succeeded":
            reasons.add(f"{name}_ACCESS_SUCCEEDED")
        elif access.status == "error":
            reasons.add(f"{name}_ACCESS_OBSERVER_ERROR")
    return CommonSafetyDecision(stop=bool(reasons), reason_codes=sorted(reasons))


class Ss1PlanContract(StrictModel):
    result_schema_sha256: Sha256
    neutral_review_prompt_sha256: Sha256
    review_trigger_position: Literal["after_observer_before_next_dispatch"]
    task_initial_turns: Literal[1]
    task_extra_turn_ceiling: Literal[1]
    variant_extra_turn_ceiling: Literal[2]


class B1PlanContract(StrictModel):
    public_report_schema_sha256: Sha256
    observer_hook_schema_sha256: Sha256
    feedback_template_sha256: Sha256
    feedback_stdout_stderr_byte_cap: int = Field(gt=0)
    selection: Literal["resume_if_same_thread_safe_else_retry"]
    task_initial_turns: Literal[1]
    task_extra_turn_ceiling: Literal[1]
    variant_extra_turn_ceiling: Literal[2]


class CommonBudgetContract(StrictModel):
    task_count: int = Field(gt=0)
    base_turns_per_variant: int = Field(gt=0)
    total_turn_ceiling_per_variant: int = Field(gt=0)
    model_active_seconds_ceiling_per_variant: float = Field(gt=0)
    wall_clock_seconds_ceiling_per_variant: float = Field(gt=0)
    wall_clock_scope: Literal["from_adapter_run_entry_through_adapter_terminal"]
    unused_reserve_transfer: Literal["forbidden"]


class RealisticRoutingPlanSupplement(StrictModel):
    schema_version: Literal[1] = 1
    suite_id: Literal["sdk-routing-realistic-high-difficulty-v1"]
    stage_id: Literal["realistic-high-difficulty-initial"]
    comparison_spec_sha256: Sha256
    implementation_spec_sha256: Sha256
    runtime_boundary_spec_sha256: Sha256
    machine_variant_ids: tuple[Literal["ss1"], Literal["b1"]]
    ss1: Ss1PlanContract
    b1: B1PlanContract
    common_budget: CommonBudgetContract
    observer_schema_sha256: Sha256
    observer_implementation_sha256: Sha256
    runtime_boundary_manifest_sha256: Sha256
    runtime_boundary_result_sha256: Sha256
    runtime_boundary_bundle_sha256: Sha256
    challenge_eligibility_manifest_sha256: Sha256
    property_catalog_sha256: Sha256
    property_prerequisite_dag_sha256: Sha256
    property_evaluation_schema_sha256: Sha256
    triage_policy_sha256: Sha256
    rater_contract_sha256_or_not_applicable: Sha256 | Literal["not_applicable"]

    @model_validator(mode="after")
    def budgets_are_symmetric(self) -> "RealisticRoutingPlanSupplement":
        if self.ss1.task_initial_turns != self.b1.task_initial_turns:
            raise ValueError("Variant initial-turn budgets differ")
        if self.ss1.task_extra_turn_ceiling != self.b1.task_extra_turn_ceiling:
            raise ValueError("Variant Task reserve budgets differ")
        if self.ss1.variant_extra_turn_ceiling != self.b1.variant_extra_turn_ceiling:
            raise ValueError("Variant reserve budgets differ")
        if self.common_budget.base_turns_per_variant != self.common_budget.task_count:
            raise ValueError("base turns must equal Task count")
        if self.common_budget.total_turn_ceiling_per_variant != (
            self.common_budget.task_count + self.ss1.variant_extra_turn_ceiling
        ):
            raise ValueError("total turn ceiling must equal Task count plus reserve")
        return self


def parse_realistic_plan_supplement(
    supplements: Sequence[PlanSupplement],
    *,
    expected_source: str,
) -> RealisticRoutingPlanSupplement:
    matches = [
        item for item in supplements if item.field == REALISTIC_SUPPLEMENT_FIELD
    ]
    if len(matches) != 1:
        raise ValueError("Plan requires exactly one realistic routing supplement")
    item = matches[0]
    if item.source != expected_source:
        raise ValueError("realistic routing supplement source differs")
    return RealisticRoutingPlanSupplement.model_validate(item.value)


class PropertyDefinition(StrictModel):
    property_id: str = Field(min_length=1, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    severity: PropertySeverity
    prerequisite_ids: list[str]

    @field_validator("prerequisite_ids")
    @classmethod
    def prerequisites_are_sorted(cls, values: list[str]) -> list[str]:
        return _require_sorted_unique(values, "property prerequisites")

    @model_validator(mode="after")
    def cannot_depend_on_self(self) -> "PropertyDefinition":
        if self.property_id in self.prerequisite_ids:
            raise ValueError("property cannot depend on itself")
        return self


class PropertyCheckOutcome(StrictModel):
    status: Literal["pass", "fail", "not_applicable"]
    reason_code: str = Field(min_length=1)
    description: str = Field(min_length=1)
    evidence_refs: list[EvidenceReference]

    @field_validator("evidence_refs")
    @classmethod
    def evidence_is_sorted(
        cls, values: list[EvidenceReference]
    ) -> list[EvidenceReference]:
        paths = [value.path for value in values]
        _require_sorted_unique(paths, "property evidence")
        return values


class PropertyResult(StrictModel):
    property_id: str = Field(min_length=1)
    status: PropertyStatus
    severity: PropertySeverity
    reason_code: str = Field(min_length=1)
    description: str = Field(min_length=1)
    evidence_refs: list[EvidenceReference]
    prerequisite_ids: list[str]
    checker_sha256: Sha256

    @field_validator("evidence_refs")
    @classmethod
    def evidence_is_sorted(
        cls, values: list[EvidenceReference]
    ) -> list[EvidenceReference]:
        paths = [value.path for value in values]
        _require_sorted_unique(paths, "property evidence")
        return values

    @field_validator("prerequisite_ids")
    @classmethod
    def prerequisites_are_sorted(cls, values: list[str]) -> list[str]:
        return _require_sorted_unique(values, "property prerequisites")


class CheckerProcessObservation(StrictModel):
    exit_code: int | None
    timed_out: bool
    stdout_size: int = Field(ge=0)
    stdout_sha256: Sha256
    stdout_truncated: bool
    stderr_size: int = Field(ge=0)
    stderr_sha256: Sha256
    stderr_truncated: bool

    def has_outer_error(self) -> bool:
        return (
            self.exit_code != 0
            or self.timed_out
            or self.stdout_truncated
            or self.stderr_truncated
        )


class PropertyEvaluationEnvelope(StrictModel):
    schema_version: Literal[1] = 1
    experiment_id: str = Field(min_length=1)
    cell_id: str = Field(min_length=1)
    fixture_id: str = Field(min_length=1)
    catalog_sha256: Sha256
    prerequisite_dag_sha256: Sha256
    checker_sha256: Sha256
    ordered_property_ids: list[str]
    checker_run_status: Literal["completed", "checker_error"]
    aggregate_status: Literal["pass", "fail", "checker_error"]
    process: CheckerProcessObservation
    workspace_before_sha256: Sha256
    workspace_after_sha256: Sha256
    workspace_mutated: bool
    properties: list[PropertyResult]
    envelope_sha256: Sha256

    @field_validator("ordered_property_ids")
    @classmethod
    def property_ids_are_sorted(cls, values: list[str]) -> list[str]:
        return _require_sorted_unique(values, "ordered property IDs")

    @model_validator(mode="after")
    def envelope_is_complete(self) -> "PropertyEvaluationEnvelope":
        if self.workspace_mutated != (
            self.workspace_before_sha256 != self.workspace_after_sha256
        ):
            raise ValueError("workspace mutation flag differs from workspace hashes")
        outer_error = self.process.has_outer_error() or self.workspace_mutated
        if self.checker_run_status == "checker_error":
            if self.aggregate_status != "checker_error" or self.properties:
                raise ValueError("outer checker errors cannot synthesize property results")
        else:
            if outer_error:
                raise ValueError("completed checker run contains an outer error")
            result_ids = [result.property_id for result in self.properties]
            if result_ids != self.ordered_property_ids:
                raise ValueError("completed property result set/order differs from catalog")
            if len(result_ids) != len(set(result_ids)):
                raise ValueError("property results must occur exactly once")
            if any(result.checker_sha256 != self.checker_sha256 for result in self.properties):
                raise ValueError("property result checker identity differs")
            statuses = {result.status for result in self.properties}
            expected = (
                "checker_error"
                if "checker_error" in statuses
                else "fail"
                if statuses.intersection({"fail", "blocked_by_prerequisite"})
                else "pass"
            )
            if self.aggregate_status != expected:
                raise ValueError("property aggregate status differs from results")
        if self.envelope_sha256 != _self_hash(self, "envelope_sha256"):
            raise ValueError("property evaluation self-hash differs")
        return self

    @classmethod
    def build(cls, payload: Mapping[str, object]) -> "PropertyEvaluationEnvelope":
        value = dict(payload)
        return cls.model_validate(
            {**value, "envelope_sha256": canonical_sha256(value)}
        )


def _definition_payload(definitions: Sequence[PropertyDefinition]) -> list[dict[str, JsonValue]]:
    return [definition.model_dump(mode="json") for definition in definitions]


def property_catalog_sha256(definitions: Sequence[PropertyDefinition]) -> str:
    return canonical_sha256(
        [
            {
                "property_id": definition.property_id,
                "severity": definition.severity,
            }
            for definition in definitions
        ]
    )


def property_prerequisite_dag_sha256(
    definitions: Sequence[PropertyDefinition],
) -> str:
    return canonical_sha256(
        [
            {
                "property_id": definition.property_id,
                "prerequisite_ids": definition.prerequisite_ids,
            }
            for definition in definitions
        ]
    )


def _catalog_error(definitions: Sequence[PropertyDefinition]) -> str | None:
    ids = [definition.property_id for definition in definitions]
    if ids != sorted(ids) or len(ids) != len(set(ids)):
        return "PROPERTY_CATALOG_ORDER_OR_DUPLICATE"
    known = set(ids)
    if any(set(definition.prerequisite_ids) - known for definition in definitions):
        return "PROPERTY_DAG_UNKNOWN_ID"
    by_id = {definition.property_id: definition for definition in definitions}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(property_id: str) -> bool:
        if property_id in visiting:
            return False
        if property_id in visited:
            return True
        visiting.add(property_id)
        if not all(visit(item) for item in by_id[property_id].prerequisite_ids):
            return False
        visiting.remove(property_id)
        visited.add(property_id)
        return True

    if not all(visit(property_id) for property_id in ids):
        return "PROPERTY_DAG_CYCLE"
    return None


PropertyChecker = Callable[[], PropertyCheckOutcome | Mapping[str, object]]


def evaluate_property_checks(
    *,
    experiment_id: str,
    cell_id: str,
    fixture_id: str,
    definitions: Sequence[PropertyDefinition],
    checkers: Mapping[str, PropertyChecker],
    checker_sha256: str,
    process: CheckerProcessObservation,
    workspace_before_sha256: str,
    workspace_after_sha256: str,
    expected_catalog_sha256: str | None = None,
    expected_prerequisite_dag_sha256: str | None = None,
) -> PropertyEvaluationEnvelope:
    definitions = tuple(definitions)
    ordered_ids = sorted({definition.property_id for definition in definitions})
    computed_catalog = property_catalog_sha256(definitions)
    computed_dag = property_prerequisite_dag_sha256(definitions)
    catalog_identity = expected_catalog_sha256 or computed_catalog
    dag_identity = expected_prerequisite_dag_sha256 or computed_dag
    workspace_mutated = workspace_before_sha256 != workspace_after_sha256
    outer_error = _catalog_error(definitions)
    if set(checkers) != set(ordered_ids):
        outer_error = outer_error or "PROPERTY_CHECKER_SET_DIFFERS"
    if expected_catalog_sha256 is not None and expected_catalog_sha256 != computed_catalog:
        outer_error = outer_error or "PROPERTY_CATALOG_IDENTITY_DRIFT"
    if (
        expected_prerequisite_dag_sha256 is not None
        and expected_prerequisite_dag_sha256 != computed_dag
    ):
        outer_error = outer_error or "PROPERTY_DAG_IDENTITY_DRIFT"
    if process.has_outer_error():
        outer_error = outer_error or "CHECKER_PROCESS_ERROR"
    if workspace_mutated:
        outer_error = outer_error or "CHECKER_WORKSPACE_MUTATION"

    base_payload: dict[str, object] = {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "cell_id": cell_id,
        "fixture_id": fixture_id,
        "catalog_sha256": catalog_identity,
        "prerequisite_dag_sha256": dag_identity,
        "checker_sha256": checker_sha256,
        "ordered_property_ids": ordered_ids,
        "process": process.model_dump(mode="json"),
        "workspace_before_sha256": workspace_before_sha256,
        "workspace_after_sha256": workspace_after_sha256,
        "workspace_mutated": workspace_mutated,
    }
    if outer_error is not None:
        return PropertyEvaluationEnvelope.build(
            {
                **base_payload,
                "checker_run_status": "checker_error",
                "aggregate_status": "checker_error",
                "properties": [],
            }
        )

    by_id = {definition.property_id: definition for definition in definitions}
    results: dict[str, PropertyResult] = {}

    def evaluate(property_id: str) -> PropertyResult:
        if property_id in results:
            return results[property_id]
        definition = by_id[property_id]
        prerequisite_results = [evaluate(item) for item in definition.prerequisite_ids]
        if any(result.status != "pass" for result in prerequisite_results):
            result = PropertyResult(
                property_id=property_id,
                status="blocked_by_prerequisite",
                severity=definition.severity,
                reason_code="PREREQUISITE_NOT_PASSED",
                description="A prerequisite property did not pass.",
                evidence_refs=[],
                prerequisite_ids=definition.prerequisite_ids,
                checker_sha256=checker_sha256,
            )
        else:
            try:
                outcome = PropertyCheckOutcome.model_validate(checkers[property_id]())
            except Exception:
                result = PropertyResult(
                    property_id=property_id,
                    status="checker_error",
                    severity=definition.severity,
                    reason_code="CHECKER_EXCEPTION",
                    description="The property checker raised an exception.",
                    evidence_refs=[],
                    prerequisite_ids=definition.prerequisite_ids,
                    checker_sha256=checker_sha256,
                )
            else:
                result = PropertyResult(
                    property_id=property_id,
                    status=outcome.status,
                    severity=definition.severity,
                    reason_code=outcome.reason_code,
                    description=outcome.description,
                    evidence_refs=outcome.evidence_refs,
                    prerequisite_ids=definition.prerequisite_ids,
                    checker_sha256=checker_sha256,
                )
        results[property_id] = result
        return result

    ordered_results = [evaluate(property_id) for property_id in ordered_ids]
    statuses = {result.status for result in ordered_results}
    aggregate = (
        "checker_error"
        if "checker_error" in statuses
        else "fail"
        if statuses.intersection({"fail", "blocked_by_prerequisite"})
        else "pass"
    )
    return PropertyEvaluationEnvelope.build(
        {
            **base_payload,
            "checker_run_status": "completed",
            "aggregate_status": aggregate,
            "properties": [result.model_dump(mode="json") for result in ordered_results],
        }
    )


class CommonTriageInput(StrictModel):
    ss1: PropertyEvaluationEnvelope
    b1: PropertyEvaluationEnvelope
    challenge_invalid_reason_codes: list[str]
    challenge_underspecified_reason_codes: list[str]
    rater_integrity_failed: bool = False
    evidence_refs: list[EvidenceReference]
    policy_sha256: Sha256

    @field_validator(
        "challenge_invalid_reason_codes",
        "challenge_underspecified_reason_codes",
    )
    @classmethod
    def reasons_are_sorted(cls, values: list[str]) -> list[str]:
        return _require_sorted_unique(values, "triage reason codes")

    @field_validator("evidence_refs")
    @classmethod
    def evidence_is_sorted(
        cls, values: list[EvidenceReference]
    ) -> list[EvidenceReference]:
        paths = [value.path for value in values]
        _require_sorted_unique(paths, "triage evidence")
        return values


class CommonFailureTriage(StrictModel):
    status: Literal[
        "EVALUATION_FAILURE",
        "CHALLENGE_INVALID",
        "CHALLENGE_UNDERSPECIFIED",
        "SHARED_MODEL_FAILURE",
        "MIXED_MODEL_FAILURE",
    ]
    matched_priority: Literal[1, 2, 3, 4, 5]
    reason_codes: list[str]
    property_ids: list[str]
    evidence_refs: list[EvidenceReference]
    policy_sha256: Sha256

    @field_validator("reason_codes", "property_ids")
    @classmethod
    def strings_are_sorted(cls, values: list[str]) -> list[str]:
        return _require_sorted_unique(values, "triage values")

    @field_validator("evidence_refs")
    @classmethod
    def evidence_is_sorted(
        cls, values: list[EvidenceReference]
    ) -> list[EvidenceReference]:
        paths = [value.path for value in values]
        _require_sorted_unique(paths, "triage evidence")
        return values

    @model_validator(mode="after")
    def priority_matches_status(self) -> "CommonFailureTriage":
        expected = {
            "EVALUATION_FAILURE": 1,
            "CHALLENGE_INVALID": 2,
            "CHALLENGE_UNDERSPECIFIED": 3,
            "SHARED_MODEL_FAILURE": 4,
            "MIXED_MODEL_FAILURE": 5,
        }[self.status]
        if self.matched_priority != expected:
            raise ValueError("triage priority differs from status")
        return self


def _semantic_failures(envelope: PropertyEvaluationEnvelope) -> set[str]:
    return {
        result.property_id
        for result in envelope.properties
        if result.status == "fail" and result.severity in {"critical", "major"}
    }


def derive_common_failure_triage(value: CommonTriageInput) -> CommonFailureTriage:
    evaluation_reasons: set[str] = set()
    if value.ss1.aggregate_status == "checker_error":
        evaluation_reasons.add("SS1_EVALUATION_FAILURE")
    if value.b1.aggregate_status == "checker_error":
        evaluation_reasons.add("B1_EVALUATION_FAILURE")
    if value.rater_integrity_failed:
        evaluation_reasons.add("RATER_INTEGRITY_FAILURE")
    if evaluation_reasons:
        status = "EVALUATION_FAILURE"
        priority = 1
        reasons = sorted(evaluation_reasons)
        properties: list[str] = []
    elif value.challenge_invalid_reason_codes:
        status = "CHALLENGE_INVALID"
        priority = 2
        reasons = value.challenge_invalid_reason_codes
        properties = []
    elif value.challenge_underspecified_reason_codes:
        status = "CHALLENGE_UNDERSPECIFIED"
        priority = 3
        reasons = value.challenge_underspecified_reason_codes
        properties = []
    else:
        ss1_failures = _semantic_failures(value.ss1)
        b1_failures = _semantic_failures(value.b1)
        shared = ss1_failures.intersection(b1_failures)
        if shared:
            status = "SHARED_MODEL_FAILURE"
            priority = 4
            reasons = ["SAME_SEMANTIC_PROPERTY_FAILED"]
            properties = sorted(shared)
        elif ss1_failures and b1_failures:
            status = "MIXED_MODEL_FAILURE"
            priority = 5
            reasons = ["DIFFERENT_SEMANTIC_PROPERTIES_FAILED"]
            properties = sorted(ss1_failures.union(b1_failures))
        else:
            raise ValueError("common failure triage requires both Variants to fail")
    return CommonFailureTriage(
        status=status,
        matched_priority=priority,
        reason_codes=reasons,
        property_ids=properties,
        evidence_refs=value.evidence_refs,
        policy_sha256=value.policy_sha256,
    )


class InstanceVerdict(StrictModel):
    status: InstanceVerdictStatus
    scope: Literal["challenge_instance"] = "challenge_instance"
    route_issued: Literal[False] = False
    snapshot_id: str = Field(min_length=1)
    evidence_refs: list[EvidenceReference]
    policy_sha256: Sha256

    @field_validator("evidence_refs")
    @classmethod
    def evidence_is_sorted(
        cls, values: list[EvidenceReference]
    ) -> list[EvidenceReference]:
        paths = [value.path for value in values]
        _require_sorted_unique(paths, "verdict evidence")
        return values
