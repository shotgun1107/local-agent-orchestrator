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

    consumed = 0
    for measurement in sealed_measurements:
        if measurement.identity.variant_id != "b1":
            continue
        values = measurement.variant_metrics.values
        consumed += _nonnegative_int(values.get("b1_retry_count", 0), "b1_retry_count")
        consumed += _nonnegative_int(values.get("b1_resume_count", 0), "b1_resume_count")
    return max(0, reserve_turns - consumed)


def s2_b1_turn_cap(
    sealed_measurements: Sequence[Measurement],
    *,
    task_count: int = 3,
    project_policy_turn_cap: int = 8,
    reserve_turns: int = 3,
) -> int:
    remaining = remaining_b1_retry_resume_reserve(
        sealed_measurements,
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
    maximum_turns = 3 if identity.variant_id == "c2" else 6
    maximum_model_active = (
        2_700
        if identity.variant_id == "c2"
        else min(2_700 + 900 * max(0, actual_turns - 3), 3_300)
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
        or not 0 <= wall <= 3300
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
    if identity.variant_id == "b1" and actual_turns > 3 + _nonnegative_int(
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
