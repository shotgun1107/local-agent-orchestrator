"""Deterministic SDK routing S2 reserve and profile-policy derivation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from benchmark_runner.contract import ExecutionPlan, Measurement, MetricStatus, PlannedCell


S2_POLICY_VERSION = "sdk-routing-s2-policy-v1"
S2_INITIAL_CELL_IDS = {
    "three-stage-config-migration": {
        "c2": "cell_s2_a_1_c2",
        "b1": "cell_s2_a_1_b1",
    },
    "three-stage-incident-analysis": {
        "c2": "cell_s2_b_1_c2",
        "b1": "cell_s2_b_1_b1",
    },
}
S2_REVERSE_CELL_IDS = {
    "three-stage-config-migration": {
        "c2": "cell_s2_a_2_c2",
        "b1": "cell_s2_a_2_b1",
    },
    "three-stage-incident-analysis": {
        "c2": "cell_s2_b_2_c2",
        "b1": "cell_s2_b_2_b1",
    },
}
S3_POLICY_VERSION = "sdk-routing-s3-policy-v1"
S3_INITIAL_CELL_IDS = {
    "four-stage-compatibility-refactor": {
        "c2": "cell_s3_a_1_c2",
        "b1": "cell_s3_a_1_b1",
    },
    "four-stage-conflicting-incident-report": {
        "c2": "cell_s3_b_1_c2",
        "b1": "cell_s3_b_1_b1",
    },
}
S3_REVERSE_CELL_IDS = {
    "four-stage-compatibility-refactor": {
        "c2": "cell_s3_a_2_c2",
        "b1": "cell_s3_a_2_b1",
    },
    "four-stage-conflicting-incident-report": {
        "c2": "cell_s3_b_2_c2",
        "b1": "cell_s3_b_2_b1",
    },
}
S3_TASK_CHECKS = {
    "four-stage-compatibility-refactor": {
        "A1": ("schema_contract", frozenset({"HCR-P1"})),
        "A2": ("migration_contract", frozenset({"HCR-P2", "HCR-P5a"})),
        "A3": ("integration_contract", frozenset({"HCR-P3", "HCR-P5b"})),
        "A4": ("backward_compatibility", frozenset({"HCR-P4", "HCR-P5b"})),
    },
    "four-stage-conflicting-incident-report": {
        "I1": ("evidence_contract", frozenset({"HCI-P1", "HCI-P2"})),
        "I2": ("conflict_contract", frozenset({"HCI-P2", "HCI-P3"})),
        "I3": ("alternative_contract", frozenset({"HCI-P3", "HCI-P4"})),
        "I4": ("report_contract", frozenset({"HCI-P4", "HCI-P5", "HCI-P6"})),
    },
}
_S3_SAFETY_PROPERTIES = frozenset({"HCR-P6"})
_INFRASTRUCTURE_FAILURES = {
    "infrastructure_error",
    "transient_runtime",
    "runtime_dispatch_failed",
    "runtime_timeout",
    "timeout",
    "timed_out",
    "checker_error",
}


class S2PolicyError(RuntimeError):
    pass


def _nonnegative_int(value: object, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise S2PolicyError(f"{field} must be a nonnegative integer")
    return value


def remaining_b1_retry_resume_reserve(
    sealed_measurements: Sequence[Measurement],
    *,
    reserve_turns: int = 3,
) -> int:
    """Return the independent reserve after prior sealed B1 retry/resume use."""

    reserve_turns = _nonnegative_int(reserve_turns, "reserve_turns")
    consumed = 0
    for measurement in sealed_measurements:
        values = measurement.variant_metrics.values
        if measurement.identity.variant_id != "b1":
            for field in ("b1_retry_count", "b1_resume_count"):
                if field in values and _nonnegative_int(values[field], field) != 0:
                    raise S2PolicyError(
                        "non-B1 Measurements cannot consume the B1 reserve"
                    )
            continue
        consumed += _nonnegative_int(values.get("b1_retry_count", 0), "b1_retry_count")
        consumed += _nonnegative_int(values.get("b1_resume_count", 0), "b1_resume_count")
        if consumed > reserve_turns:
            raise S2PolicyError("B1 retry/resume history exceeds the supplied reserve")
    return reserve_turns - consumed


def s2_b1_turn_cap(
    sealed_measurements: Sequence[Measurement],
    *,
    task_count: int = 3,
    project_policy_turn_cap: int = 8,
    reserve_turns: int = 3,
) -> int:
    task_count = _nonnegative_int(task_count, "task_count")
    project_policy_turn_cap = _nonnegative_int(
        project_policy_turn_cap, "project_policy_turn_cap"
    )
    reserve_turns = _nonnegative_int(reserve_turns, "reserve_turns")
    if task_count < 1 or project_policy_turn_cap < task_count:
        raise S2PolicyError("S2 turn cap inputs cannot represent one Task sequence")
    remaining = remaining_b1_retry_resume_reserve(
        sealed_measurements,
        reserve_turns=reserve_turns,
    )
    return min(project_policy_turn_cap, task_count + remaining)


def remaining_s3_b1_retry_resume_reserve(
    sealed_measurements: Sequence[Measurement],
    *,
    fixture_id: str,
    reserve_turns: int = 2,
) -> int:
    """Return one S3 profile's reserve without borrowing from another profile."""

    if fixture_id not in S3_INITIAL_CELL_IDS:
        raise S2PolicyError(f"unsupported S3 fixture: {fixture_id}")
    consumed = 0
    for measurement in sealed_measurements:
        if (
            measurement.identity.variant_id != "b1"
            or measurement.identity.fixture_id != fixture_id
        ):
            continue
        values = measurement.variant_metrics.values
        consumed += _nonnegative_int(values.get("b1_retry_count", 0), "b1_retry_count")
        consumed += _nonnegative_int(values.get("b1_resume_count", 0), "b1_resume_count")
    return max(0, reserve_turns - consumed)


def s3_b1_turn_cap(
    sealed_measurements: Sequence[Measurement],
    *,
    fixture_id: str,
    task_count: int = 4,
    project_policy_turn_cap: int = 6,
    reserve_turns: int = 2,
) -> int:
    remaining = remaining_s3_b1_retry_resume_reserve(
        sealed_measurements,
        fixture_id=fixture_id,
        reserve_turns=reserve_turns,
    )
    return min(project_policy_turn_cap, task_count + remaining)


def _metric_number(metric: object) -> float | None:
    status = getattr(metric, "status", None)
    value = getattr(metric, "value", None)
    if status not in {MetricStatus.MEASURED, MetricStatus.DERIVED}:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    return float(value)


def _checker_contract(plan: ExecutionPlan, fixture_id: str) -> dict[str, Any]:
    checks = plan.decision_policy.get("posthoc_checks")
    if not isinstance(checks, dict):
        raise S2PolicyError("S2 Plan omitted posthoc_checks")
    value = checks.get(fixture_id)
    if not isinstance(value, dict):
        raise S2PolicyError(f"S2 Plan omitted checker identity for {fixture_id}")
    return value


def _cell_validity(
    *,
    planned_cells: Mapping[str, tuple[ExecutionPlan, PlannedCell]],
    measurement: Measurement,
    sealed_cell_ids: set[str],
    posthoc_results: Mapping[str, Mapping[str, object]],
    task_count: int = 3,
    b1_maximum_turns: int = 6,
    c2_model_active_limit: int = 2_700,
    b1_model_active_ceiling: int = 3_300,
    wall_clock_limit: int = 3_300,
) -> tuple[bool, str | None, frozenset[str]]:
    identity = measurement.identity
    binding = planned_cells.get(identity.cell_id)
    if binding is None:
        return False, "cell_not_in_plan", frozenset()
    plan, planned = binding
    if (
        identity.cell_id not in sealed_cell_ids
        or identity.experiment_id != plan.experiment_id
        or identity.block_id != planned.block_id
        or identity.fixture_id != planned.fixture_id
        or identity.variant_id != planned.variant_id
        or identity.repetition != planned.repetition
        or identity.execution_ordinal != planned.execution_ordinal
    ):
        return False, "identity_or_seal", frozenset()
    fixture = next(
        item for item in plan.fixtures if item.fixture_id == planned.fixture_id
    )
    variant = next(
        item for item in plan.variants if item.artifact_id == planned.variant_id
    )
    provenance = measurement.provenance
    if (
        provenance.manifest_sha256 != plan.source_manifest.sha256
        or provenance.fixture_source_commit != fixture.source_commit
        or provenance.fixture_tree_before != fixture.git_tree
        or provenance.runner_commit != plan.runner.version
        or provenance.variant_version != variant.version
        or provenance.variant_artifact_sha256 != variant.sha256
    ):
        return False, "source_identity", frozenset()
    values = measurement.variant_metrics.values
    posthoc = posthoc_results.get(identity.cell_id)
    checker = _checker_contract(plan, identity.fixture_id)
    if not isinstance(posthoc, Mapping):
        return False, "checker_result_missing", frozenset()
    properties = posthoc.get("properties")
    failed_properties = (
        frozenset(
            item["property_id"]
            for item in properties
            if isinstance(item, dict)
            and item.get("status") == "fail"
            and isinstance(item.get("property_id"), str)
        )
        if isinstance(properties, list)
        else frozenset()
    )
    if (
        posthoc.get("property_status") == "checker_error"
        or values.get("property_status") == "checker_error"
    ):
        return False, "checker_error", failed_properties
    if (
        posthoc.get("checker_sha256") != checker.get("checker_sha256")
        or values.get("checker_sha256") != checker.get("checker_sha256")
        or posthoc.get("property_status") != values.get("property_status")
    ):
        return False, "checker_identity", failed_properties
    actual_turns = values.get("actual_model_turns")
    turn_count = _metric_number(measurement.resource.turn_count)
    model_active = values.get("model_active_seconds")
    wall = _metric_number(measurement.effort.total_wall_clock_seconds)
    maximum_turns = task_count if identity.variant_id == "c2" else b1_maximum_turns
    maximum_model_active = (
        c2_model_active_limit
        if identity.variant_id == "c2"
        else min(
            c2_model_active_limit + 900 * max(0, actual_turns - task_count),
            b1_model_active_ceiling,
        )
        if isinstance(actual_turns, int) and not isinstance(actual_turns, bool)
        else -1
    )
    if (
        not isinstance(actual_turns, int)
        or isinstance(actual_turns, bool)
        or not 1 <= actual_turns <= maximum_turns
        or turn_count != actual_turns
        or not isinstance(model_active, (int, float))
        or isinstance(model_active, bool)
        or not 0 <= float(model_active) <= maximum_model_active
        or wall is None
        or not 0 <= wall <= wall_clock_limit
    ):
        return False, "resource_limit", failed_properties
    if measurement.resource.token_usage.status not in {
        MetricStatus.MEASURED,
        MetricStatus.UNKNOWN,
    }:
        return False, "usage_contract", failed_properties
    if (
        not measurement.integrity.scope_ok
        or not measurement.integrity.evidence_hashes_ok
        or measurement.integrity.secret_findings
        or values.get("protected_files_ok") is not True
    ):
        return False, "integrity", failed_properties
    if identity.variant_id == "b1" and actual_turns > task_count + _nonnegative_int(
        values.get("b1_retry_count", 0), "b1_retry_count"
    ) + _nonnegative_int(values.get("b1_resume_count", 0), "b1_resume_count"):
        return False, "b1_turn_attribution", failed_properties
    if (
        measurement.outcome.state == "infrastructure_error"
        or measurement.outcome.failure_kind in _INFRASTRUCTURE_FAILURES
    ):
        return False, "infrastructure_failure", failed_properties
    return True, None, failed_properties


def _b1_control_effect(measurement: Measurement) -> bool:
    values = measurement.variant_metrics.values
    return any(
        (
            values.get("b1_intermediate_check_changed_result") is True,
            values.get("b1_intermediate_check_changed_dispatch") is True,
            _nonnegative_int(values.get("b1_retry_count", 0), "b1_retry_count") > 0,
            _nonnegative_int(values.get("b1_resume_count", 0), "b1_resume_count") > 0,
        )
    )


def _profile_success(measurement: Measurement, valid: bool) -> bool:
    return bool(
        valid
        and measurement.outcome.state == "completed"
        and measurement.outcome.check_success is True
        and measurement.variant_metrics.values.get("property_status") == "pass"
    )


def _metric_summary(metric: object) -> dict[str, object]:
    status = getattr(metric, "status", None)
    return {
        "status": getattr(status, "value", status),
        "value": getattr(metric, "value", None),
    }


def b1_dual_outcome_contract_valid(measurement: Measurement) -> bool:
    values = measurement.variant_metrics.values
    extra_turns = _nonnegative_int(
        values.get("b1_retry_count", 0), "b1_retry_count"
    ) + _nonnegative_int(values.get("b1_resume_count", 0), "b1_resume_count")
    if values.get("attempt_level_cost") != "not_available":
        return False
    status = values.get("dual_outcome_status")
    first = values.get("first_attempt_outcome")
    full = values.get("full_orchestrated_outcome")
    if extra_turns == 0:
        return status == "not_applicable" and first is None and full is None
    if status != "reported" or not isinstance(first, list) or not first:
        return False
    if any(
        not isinstance(item, dict)
        or set(item) != {"task_key", "state", "failure_kind"}
        or not isinstance(item.get("task_key"), str)
        or not item["task_key"]
        or not isinstance(item.get("state"), str)
        or (
            item.get("failure_kind") is not None
            and not isinstance(item.get("failure_kind"), str)
        )
        for item in first
    ):
        return False
    if not isinstance(full, dict) or set(full) != {
        "state",
        "failure_kind",
        "check_success",
        "turn_count",
        "token_usage_status",
        "token_usage",
    }:
        return False
    token_status = getattr(
        measurement.resource.token_usage.status,
        "value",
        measurement.resource.token_usage.status,
    )
    return bool(
        full.get("state") == measurement.outcome.state
        and full.get("failure_kind") == measurement.outcome.failure_kind
        and full.get("check_success") == measurement.outcome.check_success
        and full.get("turn_count") == measurement.resource.turn_count.value
        and full.get("token_usage_status") == token_status
        and full.get("token_usage") == measurement.resource.token_usage.value
    )


def derive_s2_routing_policy(
    *,
    plan: ExecutionPlan,
    measurements: Sequence[Measurement],
    sealed_cell_ids: set[str],
    posthoc_results: Mapping[str, Mapping[str, object]],
    additional_plans: Sequence[ExecutionPlan] = (),
) -> dict[str, Any]:
    """Derive S2 profile observations/routes from sealed machine-readable fields only."""

    if plan.decision_policy.get("stage_id") != "s2-intermediate":
        raise S2PolicyError("routing policy requires an S2 Plan")
    plans = (plan, *additional_plans)
    if any(
        item.decision_policy.get("stage_id") != "s2-intermediate"
        for item in plans
    ):
        raise S2PolicyError("all routing policy Plans must be S2 Plans")
    planned_cells = {
        cell.cell_id: (item, cell)
        for item in plans
        for cell in item.cells
    }
    if sum(len(item.cells) for item in plans) != len(planned_cells):
        raise S2PolicyError("duplicate Cell ID across S2 Plans")
    by_cell = {item.identity.cell_id: item for item in measurements}
    if len(by_cell) != len(measurements):
        raise S2PolicyError("duplicate S2 Measurement Cell ID")
    profile_results: dict[str, dict[str, object]] = {}
    any_expansion = False
    any_not_ready = False
    all_initial_terminal = True
    any_reverse = False
    all_reverse_terminal = True

    for fixture_id, initial_ids in S2_INITIAL_CELL_IDS.items():
        reverse_ids = S2_REVERSE_CELL_IDS[fixture_id]
        initial = {variant: by_cell.get(cell_id) for variant, cell_id in initial_ids.items()}
        reverse = {variant: by_cell.get(cell_id) for variant, cell_id in reverse_ids.items()}
        initial_complete = all(value is not None for value in initial.values())
        reverse_present = any(value is not None for value in reverse.values())
        reverse_complete = all(value is not None for value in reverse.values())
        all_initial_terminal = all_initial_terminal and initial_complete
        any_reverse = any_reverse or reverse_present
        all_reverse_terminal = all_reverse_terminal and (not reverse_present or reverse_complete)
        cell_summaries: dict[str, dict[str, object]] = {}
        failures: dict[str, frozenset[str]] = {}
        valid: dict[str, bool] = {}
        success: dict[str, bool] = {}
        control: dict[str, bool] = {}
        not_ready = False
        for order, cells in (("initial", initial), ("reverse", reverse)):
            for variant, measurement in cells.items():
                if measurement is None:
                    continue
                input_valid, reason, failed = _cell_validity(
                    planned_cells=planned_cells,
                    measurement=measurement,
                    sealed_cell_ids=sealed_cell_ids,
                    posthoc_results=posthoc_results,
                )
                key = f"{order}_{variant}"
                if (
                    input_valid
                    and variant == "b1"
                    and not b1_dual_outcome_contract_valid(measurement)
                ):
                    input_valid = False
                    reason = "b1_dual_outcome_contract"
                valid_cell = input_valid and measurement.outcome.state == "completed"
                valid[key] = valid_cell
                failures[key] = failed
                success[key] = _profile_success(measurement, input_valid)
                control[key] = variant == "b1" and _b1_control_effect(measurement)
                not_ready = not_ready or not input_valid
                values = measurement.variant_metrics.values
                cell_summaries[key] = {
                    "cell_id": measurement.identity.cell_id,
                    "order": order,
                    "variant_id": variant,
                    "sealed": measurement.identity.cell_id in sealed_cell_ids,
                    "measurement_ref": (
                        f"cells/{measurement.identity.cell_id}/measurement.json"
                    ),
                    "seal_ref": f"cells/{measurement.identity.cell_id}/seal.json",
                    "policy_input_valid": input_valid,
                    "valid_cell": valid_cell,
                    "invalid_reason": reason,
                    "profile_success": success[key],
                    "judge": {
                        "outcome_state": measurement.outcome.state,
                        "failure_kind": measurement.outcome.failure_kind,
                        "check_success": measurement.outcome.check_success,
                    },
                    "property": {
                        "status": values.get("property_status"),
                        "checker_sha256": values.get("checker_sha256"),
                        "failed_property_ids": sorted(failed),
                    },
                    "resource": {
                        "actual_model_turns": values.get("actual_model_turns"),
                        "turn_count": _metric_summary(measurement.resource.turn_count),
                        "token_usage": _metric_summary(
                            measurement.resource.token_usage
                        ),
                        "model_active_seconds": values.get(
                            "model_active_seconds"
                        ),
                        "total_wall_clock_seconds": _metric_summary(
                            measurement.effort.total_wall_clock_seconds
                        ),
                    },
                    "failed_property_ids": sorted(failed),
                    "failure_kind": measurement.outcome.failure_kind,
                    "b1_control_effect": control[key],
                    "b1_control": (
                        {
                            "intermediate_check_changed_result": values.get(
                                "b1_intermediate_check_changed_result"
                            ),
                            "intermediate_check_changed_dispatch": values.get(
                                "b1_intermediate_check_changed_dispatch"
                            ),
                            "retry_count": values.get("b1_retry_count"),
                            "resume_count": values.get("b1_resume_count"),
                            "repeatable_quality_regression": values.get(
                                "b1_repeatable_quality_regression"
                            ),
                            "dual_outcome_status": values.get(
                                "dual_outcome_status"
                            ),
                            "first_attempt_outcome": values.get(
                                "first_attempt_outcome"
                            ),
                            "full_orchestrated_outcome": values.get(
                                "full_orchestrated_outcome"
                            ),
                            "attempt_level_cost": values.get(
                                "attempt_level_cost"
                            ),
                        }
                        if variant == "b1"
                        else None
                    ),
                }

        state = "ROUTING_INCONCLUSIVE"
        route_issued = False
        expansion_required = False
        if not initial_complete:
            state = "NOT_READY"
        elif not_ready:
            state = "NOT_READY"
        elif not reverse_present:
            b1_effect = control.get("initial_b1", False)
            if success.get("initial_c2") and success.get("initial_b1") and not b1_effect:
                state = "C2_SUFFICIENT_OBSERVED_SINGLE_PAIR"
            elif success.get("initial_c2") != success.get("initial_b1") or b1_effect:
                state = "EXPANSION_REQUIRED"
                expansion_required = True
        elif not reverse_complete:
            state = "NOT_READY"
        else:
            b1_both = success.get("initial_b1") and success.get("reverse_b1")
            c2_both = success.get("initial_c2") and success.get("reverse_c2")
            b1_effect_both = control.get("initial_b1") and control.get("reverse_b1")
            c2_initial = initial["c2"]
            c2_reverse = reverse["c2"]
            b1_initial = initial["b1"]
            b1_reverse = reverse["b1"]
            assert c2_initial and c2_reverse and b1_initial and b1_reverse
            c2_same_quality_failure = (
                not c2_both
                and c2_initial.outcome.failure_kind == c2_reverse.outcome.failure_kind
                and c2_initial.outcome.failure_kind not in _INFRASTRUCTURE_FAILURES
                and failures.get("initial_c2") == failures.get("reverse_c2")
            )
            b1_same_quality_failure = (
                not b1_both
                and b1_initial.outcome.failure_kind == b1_reverse.outcome.failure_kind
                and b1_initial.outcome.failure_kind not in _INFRASTRUCTURE_FAILURES
                and failures.get("initial_b1") == failures.get("reverse_b1")
            )
            b1_regression_both = all(
                item.variant_metrics.values.get("b1_repeatable_quality_regression") is True
                for item in (b1_initial, b1_reverse)
            )
            if b1_both and c2_same_quality_failure and b1_effect_both:
                state = "ROUTE_B1_PROVISIONAL"
                route_issued = True
            elif c2_both and b1_same_quality_failure and b1_regression_both:
                state = "REJECT_B1_PROFILE"
                route_issued = True

        any_expansion = any_expansion or expansion_required
        any_not_ready = any_not_ready or state == "NOT_READY"
        profile_results[fixture_id] = {
            "state": state,
            "route_issued": route_issued,
            "expansion_required": expansion_required,
            "reverse_executed": reverse_present,
            "cells": cell_summaries,
            "complexity": plan.decision_policy.get("profiles", {}).get(fixture_id),
            "residual_uncertainty": (
                "S2 uses one initial synthetic pair and at most one reverse pair."
            ),
        }

    if any_not_ready:
        stage_state = "S2_STOP" if all_initial_terminal else "S2_INCOMPLETE"
    elif not all_initial_terminal:
        stage_state = "S2_INCOMPLETE"
    elif any_reverse and not all_reverse_terminal:
        stage_state = "S2_INCOMPLETE"
    elif any_expansion:
        stage_state = "S2_EXPANSION_REQUIRED"
    elif any_reverse and all_reverse_terminal:
        stage_state = "S2_POLICY_READY"
    elif all(
        value["state"] == "C2_SUFFICIENT_OBSERVED_SINGLE_PAIR"
        for value in profile_results.values()
    ):
        stage_state = "S2_OBSERVATION_READY"
    else:
        stage_state = "S2_INCONCLUSIVE"

    return {
        "schema_version": 1,
        "kind": "sdk_routing_policy_v1",
        "decision_function_version": S2_POLICY_VERSION,
        "suite_id": plan.decision_policy.get("suite_id"),
        "stage_id": "s2-intermediate",
        "plan_fingerprint": plan.plan_fingerprint,
        "plan_fingerprints": [item.plan_fingerprint for item in plans],
        "experiment_id": plan.experiment_id,
        "source_identity": [
            {
                "plan_fingerprint": item.plan_fingerprint,
                "source_manifest": item.source_manifest.model_dump(mode="json"),
                "fixtures": [
                    fixture.model_dump(mode="json") for fixture in item.fixtures
                ],
            }
            for item in plans
        ],
        "runner_identity": plan.runner.model_dump(mode="json"),
        "variant_identities": [
            item.model_dump(mode="json") for item in plan.variants
        ],
        "checker_identities": plan.decision_policy.get("posthoc_checks"),
        "stage_state": stage_state,
        "profiles": profile_results,
        "unclassified_low_risk": {
            "value": "c2",
            "origin": "suite_v1_inherited_default",
            "measured_in_s2": False,
        },
        "unclassified_high_risk": {
            "value": "user_decision",
            "origin": "suite_v1_inherited_default",
            "measured_in_s2": False,
        },
        "global_b1_default_issued": False,
    }


def _s3_b1_control_effect(
    measurement: Measurement,
    *,
    policy_input_valid: bool,
) -> dict[str, object]:
    values = measurement.variant_metrics.values
    fixture_id = measurement.identity.fixture_id
    task_checks = S3_TASK_CHECKS[fixture_id]
    first = values.get("first_attempt_outcome")
    failed_task_keys = sorted(
        item["task_key"]
        for item in first
        if isinstance(item, dict)
        and item.get("failure_kind") == "check_failed"
        and item.get("task_key") in task_checks
    ) if isinstance(first, list) else []
    check_ids = sorted({task_checks[key][0] for key in failed_task_keys})
    mapped_properties = sorted(
        set().union(*(task_checks[key][1] for key in failed_task_keys))
        if failed_task_keys
        else set()
    )
    evidence = {item.path: item.sha256 for item in measurement.evidence}
    raw_sha256 = evidence.get("raw/adapter-result.json")
    judge_sha256 = evidence.get("judge/result.json")
    extra_turns = _nonnegative_int(
        values.get("b1_retry_count", 0), "b1_retry_count"
    ) + _nonnegative_int(values.get("b1_resume_count", 0), "b1_resume_count")
    b1_success = _profile_success(measurement, policy_input_valid)
    effect = bool(
        policy_input_valid
        and b1_success
        and failed_task_keys
        and values.get("b1_intermediate_check_changed_result") is True
        and values.get("b1_intermediate_check_changed_dispatch") is True
        and extra_turns > 0
        and values.get("dual_outcome_status") == "reported"
        and isinstance(values.get("full_orchestrated_outcome"), dict)
        and isinstance(raw_sha256, str)
        and isinstance(judge_sha256, str)
    )
    return {
        "b1_control_effect": effect,
        "failed_task_keys": failed_task_keys,
        "check_ids": check_ids,
        "mapped_property_ids": mapped_properties,
        "retry_resume_reserve_turns_used": extra_turns,
        "first_attempt_evidence_sha256": raw_sha256,
        "full_outcome_evidence_sha256": judge_sha256,
    }


def _s3_quality_signatures(
    measurement: Measurement,
    failed_properties: frozenset[str],
) -> frozenset[str]:
    """Return only Check/property pairs with an observed failed B1 Task Check."""

    values = measurement.variant_metrics.values
    first = values.get("first_attempt_outcome")
    if not isinstance(first, list):
        return frozenset()
    task_checks = S3_TASK_CHECKS[measurement.identity.fixture_id]
    signatures: set[str] = set()
    for item in first:
        if not isinstance(item, dict) or item.get("failure_kind") != "check_failed":
            continue
        contract = task_checks.get(item.get("task_key"))
        if contract is None:
            continue
        check_id, mapped = contract
        for property_id in failed_properties & mapped:
            if property_id not in _S3_SAFETY_PROPERTIES:
                signatures.add(f"{check_id}:{property_id}")
    return frozenset(signatures)


def derive_s3_routing_policy(
    *,
    plan: ExecutionPlan,
    measurements: Sequence[Measurement],
    sealed_cell_ids: set[str],
    posthoc_results: Mapping[str, Mapping[str, object]],
    additional_plans: Sequence[ExecutionPlan] = (),
) -> dict[str, Any]:
    """Derive frozen S3 initial/reverse policy without score or timing heuristics."""

    if plan.decision_policy.get("stage_id") != "s3-complex-high-risk":
        raise S2PolicyError("routing policy requires an S3 Plan")
    plans = (plan, *additional_plans)
    if any(
        item.decision_policy.get("stage_id") != "s3-complex-high-risk"
        for item in plans
    ):
        raise S2PolicyError("all routing policy Plans must be S3 Plans")
    planned_cells = {
        cell.cell_id: (item, cell)
        for item in plans
        for cell in item.cells
    }
    if sum(len(item.cells) for item in plans) != len(planned_cells):
        raise S2PolicyError("duplicate Cell ID across S3 Plans")
    by_cell = {item.identity.cell_id: item for item in measurements}
    if len(by_cell) != len(measurements):
        raise S2PolicyError("duplicate S3 Measurement Cell ID")

    profile_results: dict[str, dict[str, object]] = {}
    all_initial_terminal = True
    all_reverse_terminal = True
    any_reverse = False
    any_not_ready = False
    any_replication = False
    any_route = False

    for fixture_id, initial_ids in S3_INITIAL_CELL_IDS.items():
        reverse_ids = S3_REVERSE_CELL_IDS[fixture_id]
        initial = {variant: by_cell.get(cell_id) for variant, cell_id in initial_ids.items()}
        reverse = {variant: by_cell.get(cell_id) for variant, cell_id in reverse_ids.items()}
        initial_complete = all(item is not None for item in initial.values())
        reverse_present = any(item is not None for item in reverse.values())
        reverse_complete = all(item is not None for item in reverse.values())
        all_initial_terminal = all_initial_terminal and initial_complete
        any_reverse = any_reverse or reverse_present
        all_reverse_terminal = all_reverse_terminal and (
            not reverse_present or reverse_complete
        )

        success: dict[str, bool] = {}
        failed: dict[str, frozenset[str]] = {}
        controls: dict[str, dict[str, object]] = {}
        signatures: dict[str, frozenset[str]] = {}
        summaries: dict[str, dict[str, object]] = {}
        not_ready = False

        for order, cells in (("initial", initial), ("reverse", reverse)):
            for variant, measurement in cells.items():
                if measurement is None:
                    continue
                input_valid, reason, failed_properties = _cell_validity(
                    planned_cells=planned_cells,
                    measurement=measurement,
                    sealed_cell_ids=sealed_cell_ids,
                    posthoc_results=posthoc_results,
                    task_count=4,
                    b1_maximum_turns=6,
                    c2_model_active_limit=3_600,
                    b1_model_active_ceiling=5_400,
                    wall_clock_limit=5_700,
                )
                if input_valid and failed_properties & _S3_SAFETY_PROPERTIES:
                    input_valid = False
                    reason = "safety_property"
                if (
                    input_valid
                    and variant == "b1"
                    and not b1_dual_outcome_contract_valid(measurement)
                ):
                    input_valid = False
                    reason = "b1_dual_outcome_contract"
                key = f"{order}_{variant}"
                success[key] = _profile_success(measurement, input_valid)
                failed[key] = failed_properties - _S3_SAFETY_PROPERTIES
                control = (
                    _s3_b1_control_effect(
                        measurement,
                        policy_input_valid=input_valid,
                    )
                    if variant == "b1"
                    else {
                        "b1_control_effect": False,
                        "failed_task_keys": [],
                        "check_ids": [],
                        "mapped_property_ids": [],
                        "retry_resume_reserve_turns_used": 0,
                        "first_attempt_evidence_sha256": None,
                        "full_outcome_evidence_sha256": None,
                    }
                )
                controls[key] = control
                signatures[key] = (
                    _s3_quality_signatures(measurement, failed[key])
                    if variant == "b1"
                    else frozenset()
                )
                not_ready = not_ready or not input_valid
                values = measurement.variant_metrics.values
                summaries[key] = {
                    "cell_id": measurement.identity.cell_id,
                    "order": order,
                    "variant_id": variant,
                    "sealed": measurement.identity.cell_id in sealed_cell_ids,
                    "measurement_ref": f"cells/{measurement.identity.cell_id}/measurement.json",
                    "seal_ref": f"cells/{measurement.identity.cell_id}/seal.json",
                    "policy_input_valid": input_valid,
                    "invalid_reason": reason,
                    "profile_success": success[key],
                    "judge": {
                        "outcome_state": measurement.outcome.state,
                        "failure_kind": measurement.outcome.failure_kind,
                        "check_success": measurement.outcome.check_success,
                    },
                    "property": {
                        "status": values.get("property_status"),
                        "checker_sha256": values.get("checker_sha256"),
                        "failed_property_ids": sorted(failed[key]),
                    },
                    "resource": {
                        "actual_model_turns": values.get("actual_model_turns"),
                        "turn_count": _metric_summary(measurement.resource.turn_count),
                        "token_usage": _metric_summary(measurement.resource.token_usage),
                        "model_active_seconds": values.get("model_active_seconds"),
                        "total_wall_clock_seconds": _metric_summary(
                            measurement.effort.total_wall_clock_seconds
                        ),
                    },
                    "quality_signatures": sorted(signatures[key]),
                    "b1_control": control if variant == "b1" else None,
                }

        state = "ROUTING_INCONCLUSIVE"
        route_issued = False
        replication_required = False
        attributable: dict[str, bool] = {}
        for order in ("initial", "reverse"):
            control = controls.get(f"{order}_b1", {})
            c2_failed = failed.get(f"{order}_c2", frozenset())
            attributable[order] = bool(
                control.get("b1_control_effect") is True
                and c2_failed
                & frozenset(control.get("mapped_property_ids", []))
            )

        initial_b1_quality_failure = bool(
            initial_complete
            and success.get("initial_c2")
            and not success.get("initial_b1")
            and failed.get("initial_b1")
        )
        repeatable_signatures = signatures.get(
            "initial_b1", frozenset()
        ) & signatures.get("reverse_b1", frozenset())

        if not initial_complete:
            state = "NOT_READY"
        elif not_ready:
            state = "NOT_READY"
        elif not reverse_present:
            if success.get("initial_c2") and success.get("initial_b1"):
                state = (
                    "B1_CONTROL_OBSERVED_NO_ROUTE"
                    if controls.get("initial_b1", {}).get("b1_control_effect") is True
                    else "C2_SUFFICIENT_OBSERVED_SINGLE_PAIR"
                )
            elif success.get("initial_b1") and attributable.get("initial"):
                state = "S3_REPLICATION_REQUIRED"
                replication_required = True
            elif initial_b1_quality_failure:
                state = "S3_REPLICATION_REQUIRED"
                replication_required = True
        elif not reverse_complete:
            state = "NOT_READY"
        else:
            c2_both_success = success.get("initial_c2") and success.get("reverse_c2")
            b1_both_success = success.get("initial_b1") and success.get("reverse_b1")
            c2_same_failure = (
                bool(failed.get("initial_c2"))
                and failed.get("initial_c2") == failed.get("reverse_c2")
            )
            if (
                b1_both_success
                and c2_same_failure
                and attributable.get("initial")
                and attributable.get("reverse")
            ):
                state = "RETAIN_B1_HIGH_RISK"
                route_issued = True
            elif (
                c2_both_success
                and not success.get("initial_b1")
                and not success.get("reverse_b1")
                and bool(repeatable_signatures)
            ):
                state = "REJECT_B1_PROFILE"
                route_issued = True

        any_not_ready = any_not_ready or state == "NOT_READY"
        any_replication = any_replication or replication_required
        any_route = any_route or route_issued
        profile_results[fixture_id] = {
            "state": state,
            "route_issued": route_issued,
            "replication_required": replication_required,
            "reverse_executed": reverse_present,
            "single_order_b1_quality_failure": initial_b1_quality_failure,
            "repeatable_quality_regression": bool(repeatable_signatures),
            "repeatable_quality_signatures": sorted(repeatable_signatures),
            "attributable_control_effect": attributable,
            "cells": summaries,
            "complexity": plan.decision_policy.get("profiles", {}).get(fixture_id),
            "residual_uncertainty": (
                "S3 uses one initial synthetic pair and, only after a frozen predicate, "
                "one reverse pair; absence of a route is not a general B1 ranking."
            ),
        }

    if any_not_ready:
        stage_state = "S3_STOP" if all_initial_terminal else "S3_INCOMPLETE"
    elif not all_initial_terminal:
        stage_state = "S3_INCOMPLETE"
    elif any_reverse and not all_reverse_terminal:
        stage_state = "S3_INCOMPLETE"
    elif any_replication:
        stage_state = "S3_REPLICATION_REQUIRED"
    elif any_route:
        stage_state = "S3_POLICY_READY"
    elif all(
        value["state"]
        in {
            "C2_SUFFICIENT_OBSERVED_SINGLE_PAIR",
            "B1_CONTROL_OBSERVED_NO_ROUTE",
        }
        for value in profile_results.values()
    ):
        stage_state = "S3_OBSERVATION_READY"
    else:
        stage_state = "S3_INCONCLUSIVE"

    return {
        "schema_version": 1,
        "kind": "sdk_routing_policy_v1",
        "decision_function_version": S3_POLICY_VERSION,
        "suite_id": plan.decision_policy.get("suite_id"),
        "stage_id": "s3-complex-high-risk",
        "plan_fingerprint": plan.plan_fingerprint,
        "plan_fingerprints": [item.plan_fingerprint for item in plans],
        "experiment_id": plan.experiment_id,
        "source_identity": [
            {
                "plan_fingerprint": item.plan_fingerprint,
                "source_manifest": item.source_manifest.model_dump(mode="json"),
                "fixtures": [fixture.model_dump(mode="json") for fixture in item.fixtures],
            }
            for item in plans
        ],
        "runner_identity": plan.runner.model_dump(mode="json"),
        "variant_identities": [item.model_dump(mode="json") for item in plan.variants],
        "checker_identities": plan.decision_policy.get("posthoc_checks"),
        "stage_state": stage_state,
        "profiles": profile_results,
        "unclassified_low_risk": {
            "value": "c2",
            "origin": "suite_v1_inherited_default",
            "measured_in_s3": False,
        },
        "unclassified_high_risk": {
            "value": "user_decision",
            "origin": "suite_v1_inherited_default",
            "measured_in_s3": False,
        },
        "global_b1_default_issued": False,
    }
