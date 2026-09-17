"""Structured comparison failure provenance; unknown is not product evidence."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def classification(product: bool, environment: bool, unknown: bool) -> str | None:
    if unknown:
        return "UNKNOWN"
    if product and environment:
        return "MIXED_PRODUCT_AND_ENVIRONMENT"
    return "PRODUCT_ASSERTION" if product else "ENVIRONMENT" if environment else None


def summarize(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    product = any(n["product_failure_present"] and not n.get("recovered", False) for n in nodes)
    environment = any(n["environment_failure_present"] for n in nodes)
    unknown = any(n["unknown_failure_present"] for n in nodes)
    return {"schema_version": 1, "classification": classification(product, environment, unknown),
            "product_failure_present": product, "environment_failure_present": environment,
            "unknown_failure_present": unknown, "comparison_valid": not (environment or unknown), "nodes": nodes}


def node(node_id: str, reason: str, kind: str | None, *, recovered: bool = False) -> dict[str, Any]:
    return {"node_id": node_id, "reason_code": reason, "passed": kind is None,
            "classification": kind, "recovered": recovered,
            "product_failure_present": kind in {"PRODUCT_ASSERTION", "MIXED_PRODUCT_AND_ENVIRONMENT"},
            "environment_failure_present": kind in {"ENVIRONMENT", "MIXED_PRODUCT_AND_ENVIRONMENT"},
            "unknown_failure_present": kind == "UNKNOWN"}


def b1_failure_diagnostic(state: str, report: Mapping[str, Any], checks=()) -> dict[str, Any]:
    nodes = []
    for ti, task in enumerate(report.get("tasks", [])):
        for ai, attempt in enumerate(task.get("attempts", [])):
            reason = attempt.get("failure_kind")
            if reason is None:
                continue
            kind = {
                "check_failed": "PRODUCT_ASSERTION", "malformed_result": "PRODUCT_ASSERTION",
                "scope_violation": "PRODUCT_ASSERTION", "check_environment": "ENVIRONMENT",
                "dispatch_uncertain": "ENVIRONMENT", "check_mixed": "MIXED_PRODUCT_AND_ENVIRONMENT",
            }.get(reason, "UNKNOWN")
            if reason == "runtime_unknown" and attempt.get("result_claim") in {"failed", "blocked"}:
                kind = "PRODUCT_ASSERTION"
            if reason == "check_unknown" and attempt.get("failure_stage") == "check_mixed":
                kind = "MIXED_PRODUCT_AND_ENVIRONMENT"
            nodes.append(node(f"attempt:{ti}:{ai}", str(reason), kind, recovered=state == "COMPLETED"))
    for ci, check in enumerate(checks):
        if check.get("state") == "PASSED":
            continue
        diagnostic = check.get("diagnostic_result")
        subnodes = diagnostic.get("nodes", []) if isinstance(diagnostic, dict) else []
        # Preserve each public diagnostic node; a summary cannot erase mixed causes.
        for ni, item in enumerate(subnodes):
            if not isinstance(item, dict) or item.get("passed") is True:
                continue
            kind = item.get("classification")
            if kind not in {"PRODUCT_ASSERTION", "ENVIRONMENT", "UNKNOWN", "MIXED_PRODUCT_AND_ENVIRONMENT"}:
                kind = "UNKNOWN"
            nodes.append(node(f"check:{ci}:{ni}", str(item.get("reason_code", "CHECK_FAILED")), kind,
                              recovered=state == "COMPLETED"))
        kind = check.get("failure_classification")
        if kind not in {"PRODUCT_ASSERTION", "ENVIRONMENT", "UNKNOWN", "MIXED_PRODUCT_AND_ENVIRONMENT"}:
            kind = "UNKNOWN"
        nodes.append(node(f"check:{ci}", "CHECK_FAILED", kind, recovered=state == "COMPLETED"))
    if not nodes:
        nodes.append(node("worker", state, None if state == "COMPLETED" else "UNKNOWN"))
    return summarize(nodes)


def worker_failure_diagnostic(outcome: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    explicit = payload.get("adapter_failure_diagnostic")
    if explicit is not None:
        raw = payload.get("adapter_raw_payload", {})
        report = raw.get("report", {})
        expected = b1_failure_diagnostic(str(report.get("state")), report, raw.get("check_records", []))
        if explicit != expected:
            raise ValueError("Adapter failure diagnostic differs from its source evidence")
        return expected
    # Legacy/SS1 producers: only explicit known causes establish product failure.
    reason = payload.get("adapter_failure_kind")
    kind = {
        "check_mixed": "MIXED_PRODUCT_AND_ENVIRONMENT", "check_environment": "ENVIRONMENT",
        "check_unknown": "UNKNOWN", "b1_dispatch_uncertain": "ENVIRONMENT",
        "sdk_terminal_failed": "ENVIRONMENT", "ss1_setup_failed": "ENVIRONMENT",
        "ss1_task_resolution_failed": "ENVIRONMENT", "ss1_runtime_dispatch_failed": "ENVIRONMENT",
        "ss1_observer_failed": "ENVIRONMENT", "ss1_common_safety_stop": "ENVIRONMENT",
        "worker_blocked": "PRODUCT_ASSERTION", "worker_failed": "PRODUCT_ASSERTION",
        "result_schema_invalid": "PRODUCT_ASSERTION", "ss1_review_no_progress": "PRODUCT_ASSERTION",
    }.get(reason, "UNKNOWN")
    if outcome == "completed" and reason is None:
        kind = None
    nodes = [node("worker", str(reason or outcome), kind)]
    metrics = payload.get("adapter_normalized_metrics", {})
    # Earlier structured presence flags are additive, never erased by a summary.
    for key, value in (("product_failure_present", "PRODUCT_ASSERTION"), ("environment_failure_present", "ENVIRONMENT")):
        if metrics.get(key) is True:
            nodes.append(node("worker:" + key, key, value))
    return summarize(nodes)
