"""Failure provenance survives adapter -> Measurement; no SDK or Docker."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmark_runner import realistic_phase_f_b1 as b1
from benchmark_runner import realistic_phase_f_finalize as final
from benchmark_runner.plan import ExecutionPlan
from benchmark_runner.realistic_phase_f import PhaseFBackendResult, PhaseFDispatchRequest
from benchmark_runner.realistic_routing import canonical_sha256


@pytest.mark.parametrize("kind,claim,expected,product,environment", [
    ("runtime_unknown", None, "UNKNOWN", False, False),
    ("terminal_unknown", None, "UNKNOWN", False, False),
    ("check_unknown", None, "UNKNOWN", False, False),
    ("check_mixed", None, "MIXED_PRODUCT_AND_ENVIRONMENT", True, True),
    ("check_environment", None, "ENVIRONMENT", False, True),
    ("dispatch_uncertain", None, "ENVIRONMENT", False, True),
    ("runtime_unknown", "blocked", "PRODUCT_ASSERTION", True, False),
    ("check_failed", None, "PRODUCT_ASSERTION", True, False),
    (None, None, None, False, False),
])
@pytest.mark.parametrize("judge_status", ["CHECKS_PASSED", "CHECKS_FAILED", "JUDGE_RUNTIME_ERROR"])
def test_failure_classification_matrix(kind, claim, expected, product, environment, judge_status, monkeypatch):
    root = Path(__file__).resolve().parents[3]
    plan = ExecutionPlan.model_validate_json((root / "benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v1/execution-plan.json").read_bytes())
    cell = plan.cells[1]
    values = dict(schema_version=1, kind="realistic_phase_f_cell_dispatch", experiment_id=plan.experiment_id,
        plan_fingerprint=plan.plan_fingerprint, candidate_seal_sha256="a"*64, candidate_snapshot_sha256="b"*64,
        model_turn_ceiling=15, execution_ordinal=cell.execution_ordinal, cell_id=cell.cell_id,
        fixture_id=cell.fixture_id, variant_id=cell.variant_id, runtime_mode="model_free_fake", automatic_continuation=False)
    request = PhaseFDispatchRequest(**values, request_sha256=canonical_sha256(values))
    state = "COMPLETED" if kind is None else "FAILED"
    report = {"state": state, "tasks": [{"key": "R01", "attempts": [{"attempt_no": 1, "state": state,
        "failure_kind": kind, "result_claim": claim}]}]}
    outcome, failure = b1._b1_adapter_outcome(state, report)
    worker = PhaseFBackendResult(**request.model_dump(mode="json", exclude={"kind", "automatic_continuation"}),
        outcome_state=outcome, actual_model_turns=0, sealed_artifact_sha256="c"*64, public_summary={})
    payload = {"adapter_raw_payload": {"boundary_records": [], "report": report, "check_records": []},
        "adapter_normalized_metrics": {"session_count": 1, "turn_count": 1},
        "worker_tree_final_sha256": "e"*64, "adapter_failure_kind": failure, "adapter_attempt_count": 1}
    if hasattr(b1, "b1_failure_diagnostic"):
        payload["adapter_failure_diagnostic"] = b1.b1_failure_diagnostic(state, report, [])
    jvalues = dict(schema_version=1, kind="phase_f_realistic_judge_observation", status=judge_status,
        judge_kind="model_free_fake", docker_executed=False, actual_model_turns=0,
        check_success=judge_status == "CHECKS_PASSED", failed_property_ids=["R-P01"] if judge_status == "CHECKS_FAILED" else [],
        duration_seconds=1.0, raw_manifest_sha256=None, raw_result_sha256=None,
        files=[{"path": "result.json", "size": 2, "sha256": "d"*64}])
    judge = final.PhaseFJudgeObservation(**jvalues, observation_sha256=canonical_sha256(jvalues))
    monkeypatch.setattr(final.platform, "system", lambda: "Windows")
    measurement = final._measurement(plan=plan, request=request, worker=worker, adapter_payload=payload,
        judge=judge, evidence=[], adapter_evidence_filename="synthetic.json", worker_seconds=1, total_seconds=2)
    product = product or judge_status == "CHECKS_FAILED"
    environment = environment or judge_status == "JUDGE_RUNTIME_ERROR"
    if expected != "UNKNOWN":
        expected = "MIXED_PRODUCT_AND_ENVIRONMENT" if product and environment else "PRODUCT_ASSERTION" if product else "ENVIRONMENT" if environment else None
    metrics = measurement.variant_metrics.values
    assert metrics["failure_classification"] == expected
    assert metrics["product_failure_present"] is product
    assert metrics["environment_failure_present"] is environment
    assert metrics["comparison_valid"] is (not environment and expected != "UNKNOWN")


def test_frozen_ledger_mixed_stage_and_distinct_check_nodes_are_preserved():
    report = {"state": "FAILED", "tasks": [{"attempts": [{"failure_kind": "check_unknown", "failure_stage": "check_mixed"}]}]}
    checks = [{"state": "FAILED", "failure_classification": "MIXED_PRODUCT_AND_ENVIRONMENT", "diagnostic_result": {
        "nodes": [{"node_id": "assertion", "passed": False, "classification": "PRODUCT_ASSERTION", "reason_code": "ASSERTION_FAILED"},
                  {"node_id": "transport", "passed": False, "classification": "ENVIRONMENT", "reason_code": "ENVIRONMENT_FAILED"}]}}]
    diagnostic = b1.b1_failure_diagnostic("FAILED", report, checks)
    assert diagnostic["classification"] == "MIXED_PRODUCT_AND_ENVIRONMENT"
    assert not diagnostic["comparison_valid"] and not diagnostic["unknown_failure_present"]
    assert len(diagnostic["nodes"]) == 4
    assert b1._b1_adapter_outcome("FAILED", report) == ("infrastructure_error", "check_mixed")


def test_recovered_product_failure_is_not_a_final_failure():
    report = {"tasks": [{"attempts": [{"failure_kind": "check_failed"}, {"failure_kind": None}]}]}
    diagnostic = b1.b1_failure_diagnostic("COMPLETED", report, [])
    assert diagnostic["classification"] is None and diagnostic["comparison_valid"]
    assert diagnostic["nodes"][0]["recovered"] is True
