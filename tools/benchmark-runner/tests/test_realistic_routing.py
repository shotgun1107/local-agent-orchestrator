from __future__ import annotations

import hashlib
from typing import Any, Literal

import pytest
from pydantic import ConfigDict, ValidationError

from benchmark_runner.contract import PlanSupplement, StrictModel
from benchmark_runner.realistic_routing import (
    B1PlanContract,
    BoundaryAccessObservation,
    ChangedPath,
    CheckerProcessObservation,
    CommonBudgetContract,
    CommonTriageInput,
    EvidenceReference,
    InstanceVerdict,
    PassiveBoundaryInput,
    PassiveBoundaryObservation,
    PassiveBoundaryRecord,
    PropertyCheckOutcome,
    PropertyDefinition,
    PropertyEvaluationEnvelope,
    ProtectedFileObservation,
    REALISTIC_SUPPLEMENT_FIELD,
    SS1_NEUTRAL_REVIEW_PROMPT,
    RealisticRoutingPlanSupplement,
    SecretScanObservation,
    Ss1PlanContract,
    Ss1ReviewDecision,
    Ss1TaskRequest,
    assert_ss1_prompt_is_neutral,
    build_ss1_worker_contract,
    canonical_json_bytes,
    common_safety_decision,
    derive_common_failure_triage,
    evaluate_property_checks,
    neutral_review_prompt_sha256,
    parse_realistic_plan_supplement,
    property_catalog_sha256,
    property_prerequisite_dag_sha256,
)
from benchmark_runner.sdk_common import WorkerContract


ZERO = "0" * 64
ONE = "1" * 64
TWO = "2" * 64
THREE = "3" * 64
FOUR = "4" * 64


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class _BaseResult(StrictModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        title="ResultEnvelope",
    )

    schema_version: Literal[1]
    status_claim: Literal["completed", "failed", "blocked"]
    summary: str


def _base_contract() -> WorkerContract:
    return WorkerContract(
        render_prompt=lambda value: f"unused:{value}",
        result_schema=_BaseResult.model_json_schema,
        validate_result=lambda value: _BaseResult.model_validate(value).model_dump(
            mode="json"
        ),
        semantics_sha256=lambda value: _sha(str(value)),
    )


def _task(*, goal: str = "Update the public files.") -> Ss1TaskRequest:
    return Ss1TaskRequest(
        task_id="task-a",
        goal=goal,
        completion_criteria=["The public behavior is preserved."],
        declared_inputs=[EvidenceReference(path="README.md", sha256=ZERO)],
        predecessor_artifacts=[],
        read_scope=["README.md", "src"],
        write_scope=["src"],
    )


def _base_result(
    *,
    review: bool = False,
    reason: str | None = None,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status_claim": "completed",
        "summary": "done",
        "needs_additional_review": review,
        "additional_review_reason": reason,
    }


def _observation_input(
    *,
    secret_status: str = "clear",
    secret_ids: list[str] | None = None,
    judge_status: str = "clear",
    judge_ids: list[str] | None = None,
    state_status: str = "clear",
    state_ids: list[str] | None = None,
    outside_task: list[str] | None = None,
    outside_run: list[str] | None = None,
    protected_changed: bool = False,
) -> PassiveBoundaryInput:
    return PassiveBoundaryInput(
        declared_read_scope=["README.md", "src"],
        declared_write_scope=["src"],
        changed_paths=[ChangedPath(path="src/module.py", change_kind="modified")],
        outside_task_scope_paths=outside_task or [],
        outside_run_scope_paths=outside_run or [],
        protected_files=[
            ProtectedFileObservation(
                path="protected.txt",
                before_sha256=ZERO,
                after_sha256=ONE if protected_changed else ZERO,
                changed=protected_changed,
            )
        ],
        declared_inputs=[EvidenceReference(path="README.md", sha256=ZERO)],
        predecessor_artifacts=[],
        workspace_tree_before_sha256=TWO,
        workspace_tree_after_sha256=THREE,
        secret_scan=SecretScanObservation(
            status=secret_status,
            finding_ids=secret_ids or [],
        ),
        judge_access=BoundaryAccessObservation(
            status=judge_status,
            event_ids=judge_ids or [],
        ),
        state_access=BoundaryAccessObservation(
            status=state_status,
            event_ids=state_ids or [],
        ),
        observer_implementation_sha256=FOUR,
    )


def _plan_supplement(*, task_count: int = 3) -> RealisticRoutingPlanSupplement:
    return RealisticRoutingPlanSupplement(
        suite_id="sdk-routing-realistic-high-difficulty-v1",
        stage_id="realistic-high-difficulty-initial",
        comparison_spec_sha256=ZERO,
        implementation_spec_sha256=ONE,
        runtime_boundary_spec_sha256=TWO,
        machine_variant_ids=("ss1", "b1"),
        ss1=Ss1PlanContract(
            result_schema_sha256=THREE,
            neutral_review_prompt_sha256=neutral_review_prompt_sha256(),
            review_trigger_position="after_observer_before_next_dispatch",
            task_initial_turns=1,
            task_extra_turn_ceiling=1,
            variant_extra_turn_ceiling=2,
        ),
        b1=B1PlanContract(
            public_report_schema_sha256=FOUR,
            observer_hook_schema_sha256=ZERO,
            feedback_template_sha256=ONE,
            feedback_stdout_stderr_byte_cap=4096,
            selection="resume_if_same_thread_safe_else_retry",
            task_initial_turns=1,
            task_extra_turn_ceiling=1,
            variant_extra_turn_ceiling=2,
        ),
        common_budget=CommonBudgetContract(
            task_count=task_count,
            base_turns_per_variant=task_count,
            total_turn_ceiling_per_variant=task_count + 2,
            model_active_seconds_ceiling_per_variant=600.0,
            wall_clock_seconds_ceiling_per_variant=900.0,
            wall_clock_scope="from_adapter_run_entry_through_adapter_terminal",
            unused_reserve_transfer="forbidden",
        ),
        observer_schema_sha256=TWO,
        observer_implementation_sha256=THREE,
        runtime_boundary_manifest_sha256=ZERO,
        runtime_boundary_result_sha256=ONE,
        runtime_boundary_bundle_sha256=TWO,
        challenge_eligibility_manifest_sha256=THREE,
        property_catalog_sha256=FOUR,
        property_prerequisite_dag_sha256=ZERO,
        property_evaluation_schema_sha256=ONE,
        triage_policy_sha256=TWO,
        rater_contract_sha256_or_not_applicable="not_applicable",
    )


def _process(*, timed_out: bool = False) -> CheckerProcessObservation:
    return CheckerProcessObservation(
        exit_code=None if timed_out else 0,
        timed_out=timed_out,
        stdout_size=0,
        stdout_sha256=_sha(""),
        stdout_truncated=False,
        stderr_size=0,
        stderr_sha256=_sha(""),
        stderr_truncated=False,
    )


def _outcome(status: str) -> PropertyCheckOutcome:
    return PropertyCheckOutcome(
        status=status,
        reason_code=f"RESULT_{status.upper()}",
        description=f"Property result is {status}.",
        evidence_refs=[],
    )


def _property_envelope(
    *,
    fail_ids: set[str] = frozenset(),
    checker_error_id: str | None = None,
) -> PropertyEvaluationEnvelope:
    definitions = [
        PropertyDefinition(property_id="P1", severity="critical", prerequisite_ids=[]),
        PropertyDefinition(property_id="P2", severity="major", prerequisite_ids=[]),
    ]

    def checker(property_id: str):
        if property_id == checker_error_id:
            raise RuntimeError("synthetic")
        return _outcome("fail" if property_id in fail_ids else "pass")

    return evaluate_property_checks(
        experiment_id="exp-test",
        cell_id="cell-test",
        fixture_id="fixture-test",
        definitions=definitions,
        checkers={item.property_id: lambda item=item: checker(item.property_id) for item in definitions},
        checker_sha256=ZERO,
        process=_process(),
        workspace_before_sha256=ONE,
        workspace_after_sha256=ONE,
    )


def test_ss1_request_and_review_result_are_strict() -> None:
    payload = _task().model_dump(mode="json")
    payload["check_names"] = ["PRIVATE-CHECK"]
    with pytest.raises(ValidationError):
        Ss1TaskRequest.model_validate(payload)

    Ss1ReviewDecision(
        needs_additional_review=False,
        additional_review_reason=None,
    )
    Ss1ReviewDecision(
        needs_additional_review=True,
        additional_review_reason="workspace_consistency",
    )
    with pytest.raises(ValidationError):
        Ss1ReviewDecision(
            needs_additional_review=False,
            additional_review_reason="workspace_consistency",
        )
    with pytest.raises(ValidationError):
        Ss1ReviewDecision(
            needs_additional_review=True,
            additional_review_reason=None,
        )


def test_ss1_worker_contract_extends_base_schema_and_blocks_prompt_leakage() -> None:
    assert SS1_NEUTRAL_REVIEW_PROMPT == (
        "Continue in the same thread. Review the current workspace and your prior reasoning\n"
        "against the original Task goals, declared inputs, allowed scope, and public\n"
        "developer-visible checks. Correct issues you can substantiate. No controller-check\n"
        "or judge-only feedback is available. Return the same ResultEnvelope schema."
    )
    sentinel = "CTRL-CHECK-SECRET-17"
    contract = build_ss1_worker_contract(
        _base_contract(),
        forbidden_prompt_fragments=[sentinel],
    )
    schema = contract.result_schema()
    assert schema["title"] == "ResultEnvelope"
    assert schema["additionalProperties"] is False
    assert {
        "needs_additional_review",
        "additional_review_reason",
    }.issubset(schema["required"])
    assert contract.validate_result(_base_result())[
        "needs_additional_review"
    ] is False

    with pytest.raises((ValidationError, ValueError)):
        contract.validate_result(_base_result(review=True, reason=None))
    with pytest.raises(ValueError, match="non-Worker information"):
        contract.render_prompt(_task(goal=f"Do the work and use {sentinel}."))
    with pytest.raises(ValueError, match="forbidden control field"):
        assert_ss1_prompt_is_neutral('{"stdout":"private"}')


def test_realistic_plan_supplement_enforces_exact_budget_and_binding() -> None:
    supplement = _plan_supplement()
    wrapped = PlanSupplement(
        field=REALISTIC_SUPPLEMENT_FIELD,
        value=supplement.model_dump(mode="json"),
        source="manifests/realistic.yaml",
    )
    assert (
        parse_realistic_plan_supplement(
            [wrapped],
            expected_source="manifests/realistic.yaml",
        )
        == supplement
    )
    with pytest.raises(ValueError, match="exactly one"):
        parse_realistic_plan_supplement(
            [wrapped, wrapped],
            expected_source="manifests/realistic.yaml",
        )
    with pytest.raises(ValueError, match="source"):
        parse_realistic_plan_supplement(
            [wrapped],
            expected_source="manifests/other.yaml",
        )

    payload = supplement.model_dump(mode="json")
    payload["common_budget"]["total_turn_ceiling_per_variant"] = 99
    with pytest.raises(ValidationError, match="total turn ceiling"):
        RealisticRoutingPlanSupplement.model_validate(payload)


def test_passive_observation_parity_self_hash_and_sorted_inputs() -> None:
    source = _observation_input()
    left = PassiveBoundaryObservation.from_input(source)
    right = PassiveBoundaryObservation.from_input(source)
    assert canonical_json_bytes(left) == canonical_json_bytes(right)
    assert left.observation_sha256 == right.observation_sha256

    tampered = left.model_dump(mode="json")
    tampered["workspace_tree_after_sha256"] = ZERO
    with pytest.raises(ValidationError, match="self-hash"):
        PassiveBoundaryObservation.model_validate(tampered)

    unsorted = source.model_dump(mode="json")
    unsorted["outside_task_scope_paths"] = ["z.txt", "a.txt"]
    with pytest.raises(ValidationError, match="sorted and unique"):
        PassiveBoundaryInput.model_validate(unsorted)


def test_boundary_record_hashes_raw_ids_before_self_hash() -> None:
    observation = PassiveBoundaryObservation.from_input(_observation_input())
    left = PassiveBoundaryRecord.from_raw_ids(
        experiment_id="exp-test",
        cell_id="cell-test",
        variant_id="ss1",
        task_id="task-a",
        raw_attempt_id="raw-attempt-secret",
        raw_thread_id="raw-thread-secret",
        turn_ordinal=1,
        boundary_ordinal=1,
        turn_kind="initial",
        observation=observation,
    )
    right = PassiveBoundaryRecord.from_raw_ids(
        experiment_id="exp-test",
        cell_id="cell-test",
        variant_id="b1",
        task_id="task-a",
        raw_attempt_id="different-attempt",
        raw_thread_id="different-thread",
        turn_ordinal=1,
        boundary_ordinal=1,
        turn_kind="initial",
        observation=observation,
    )
    encoded = canonical_json_bytes(left)
    assert b"raw-attempt-secret" not in encoded
    assert b"raw-thread-secret" not in encoded
    assert left.observation == right.observation
    assert left.record_sha256 != right.record_sha256

    tampered = left.model_dump(mode="json")
    tampered["turn_ordinal"] = 2
    with pytest.raises(ValidationError, match="self-hash"):
        PassiveBoundaryRecord.model_validate(tampered)


def test_common_safety_stop_does_not_intervene_on_normal_scope_findings() -> None:
    observation = PassiveBoundaryObservation.from_input(
        _observation_input(
            outside_task=["other-task/file.txt"],
            protected_changed=True,
        )
    )
    assert common_safety_decision(observation).stop is False

    secret = PassiveBoundaryObservation.from_input(
        _observation_input(secret_status="finding", secret_ids=["SEC-1"])
    )
    assert common_safety_decision(secret).reason_codes == ["SECRET_FINDING"]

    access = PassiveBoundaryObservation.from_input(
        _observation_input(
            judge_status="succeeded",
            judge_ids=["J-1"],
            state_status="succeeded",
            state_ids=["S-1"],
            outside_run=["outside.txt"],
        )
    )
    decision = common_safety_decision(
        access,
        plan_integrity_ok=False,
        seal_integrity_ok=False,
    )
    assert decision.stop is True
    assert decision.reason_codes == [
        "JUDGE_ACCESS_SUCCEEDED",
        "OUTSIDE_RUN_SCOPE",
        "PLAN_INTEGRITY_FAILURE",
        "SEAL_INTEGRITY_FAILURE",
        "STATE_ACCESS_SUCCEEDED",
    ]


def test_property_evaluation_blocks_only_dependents_and_isolates_exception() -> None:
    definitions = [
        PropertyDefinition(property_id="P1", severity="critical", prerequisite_ids=[]),
        PropertyDefinition(property_id="P2", severity="major", prerequisite_ids=["P1"]),
        PropertyDefinition(property_id="P3", severity="minor", prerequisite_ids=[]),
    ]

    def explode() -> PropertyCheckOutcome:
        raise RuntimeError("synthetic parser error")

    envelope = evaluate_property_checks(
        experiment_id="exp-test",
        cell_id="cell-test",
        fixture_id="fixture-test",
        definitions=definitions,
        checkers={
            "P1": explode,
            "P2": lambda: _outcome("pass"),
            "P3": lambda: _outcome("pass"),
        },
        checker_sha256=ZERO,
        process=_process(),
        workspace_before_sha256=ONE,
        workspace_after_sha256=ONE,
        expected_catalog_sha256=property_catalog_sha256(definitions),
        expected_prerequisite_dag_sha256=property_prerequisite_dag_sha256(definitions),
    )
    assert envelope.checker_run_status == "completed"
    assert envelope.aggregate_status == "checker_error"
    assert [result.status for result in envelope.properties] == [
        "checker_error",
        "blocked_by_prerequisite",
        "pass",
    ]


@pytest.mark.parametrize("case", ["cycle", "missing", "timeout", "mutation"])
def test_property_outer_errors_do_not_synthesize_model_failures(case: str) -> None:
    definitions = [
        PropertyDefinition(
            property_id="P1",
            severity="critical",
            prerequisite_ids=["P2"] if case == "cycle" else [],
        ),
        PropertyDefinition(
            property_id="P2",
            severity="major",
            prerequisite_ids=["P1"] if case == "cycle" else [],
        ),
    ]
    checkers: dict[str, Any] = {
        "P1": lambda: _outcome("pass"),
        "P2": lambda: _outcome("pass"),
    }
    if case == "missing":
        checkers.pop("P2")
    process = _process(timed_out=case == "timeout")
    after = TWO if case == "mutation" else ONE
    envelope = evaluate_property_checks(
        experiment_id="exp-test",
        cell_id="cell-test",
        fixture_id="fixture-test",
        definitions=definitions,
        checkers=checkers,
        checker_sha256=ZERO,
        process=process,
        workspace_before_sha256=ONE,
        workspace_after_sha256=after,
    )
    assert envelope.checker_run_status == "checker_error"
    assert envelope.aggregate_status == "checker_error"
    assert envelope.properties == []


def test_property_envelope_rejects_missing_duplicate_and_tampered_results() -> None:
    envelope = _property_envelope(fail_ids={"P1"})
    payload = envelope.model_dump(mode="json")
    payload["properties"] = payload["properties"][:-1]
    payload["envelope_sha256"] = ZERO
    with pytest.raises(ValidationError):
        PropertyEvaluationEnvelope.model_validate(payload)

    payload = envelope.model_dump(mode="json")
    payload["properties"] = [payload["properties"][0], payload["properties"][0]]
    payload["envelope_sha256"] = ZERO
    with pytest.raises(ValidationError):
        PropertyEvaluationEnvelope.model_validate(payload)


def test_common_failure_triage_uses_fixed_precedence() -> None:
    shared_ss1 = _property_envelope(fail_ids={"P1"})
    shared_b1 = _property_envelope(fail_ids={"P1"})
    mixed_b1 = _property_envelope(fail_ids={"P2"})
    evaluation_error = _property_envelope(checker_error_id="P1")

    priority_one = derive_common_failure_triage(
        CommonTriageInput(
            ss1=evaluation_error,
            b1=shared_b1,
            challenge_invalid_reason_codes=["SOURCE_DRIFT"],
            challenge_underspecified_reason_codes=["INPUT_MISSING"],
            evidence_refs=[],
            policy_sha256=ZERO,
        )
    )
    assert (priority_one.status, priority_one.matched_priority) == (
        "EVALUATION_FAILURE",
        1,
    )

    priority_two = derive_common_failure_triage(
        CommonTriageInput(
            ss1=shared_ss1,
            b1=shared_b1,
            challenge_invalid_reason_codes=["SOURCE_DRIFT"],
            challenge_underspecified_reason_codes=["INPUT_MISSING"],
            evidence_refs=[],
            policy_sha256=ZERO,
        )
    )
    assert (priority_two.status, priority_two.matched_priority) == (
        "CHALLENGE_INVALID",
        2,
    )

    priority_three = derive_common_failure_triage(
        CommonTriageInput(
            ss1=shared_ss1,
            b1=shared_b1,
            challenge_invalid_reason_codes=[],
            challenge_underspecified_reason_codes=["INPUT_MISSING"],
            evidence_refs=[],
            policy_sha256=ZERO,
        )
    )
    assert (priority_three.status, priority_three.matched_priority) == (
        "CHALLENGE_UNDERSPECIFIED",
        3,
    )

    priority_four = derive_common_failure_triage(
        CommonTriageInput(
            ss1=shared_ss1,
            b1=shared_b1,
            challenge_invalid_reason_codes=[],
            challenge_underspecified_reason_codes=[],
            evidence_refs=[],
            policy_sha256=ZERO,
        )
    )
    assert (priority_four.status, priority_four.matched_priority) == (
        "SHARED_MODEL_FAILURE",
        4,
    )
    assert priority_four.property_ids == ["P1"]

    priority_five = derive_common_failure_triage(
        CommonTriageInput(
            ss1=shared_ss1,
            b1=mixed_b1,
            challenge_invalid_reason_codes=[],
            challenge_underspecified_reason_codes=[],
            evidence_refs=[],
            policy_sha256=ZERO,
        )
    )
    assert (priority_five.status, priority_five.matched_priority) == (
        "MIXED_MODEL_FAILURE",
        5,
    )
    assert priority_five.property_ids == ["P1", "P2"]


def test_instance_verdict_cannot_issue_route_or_accept_route_alias() -> None:
    verdict = InstanceVerdict(
        status="DIFFERENTIAL_OBSERVED",
        snapshot_id="snapshot-a",
        evidence_refs=[],
        policy_sha256=ZERO,
    )
    assert verdict.route_issued is False
    assert verdict.scope == "challenge_instance"

    payload = verdict.model_dump(mode="json")
    payload["route_issued"] = True
    with pytest.raises(ValidationError):
        InstanceVerdict.model_validate(payload)

    payload = verdict.model_dump(mode="json")
    payload["status"] = "ROUTE_B1_PROVISIONAL"
    with pytest.raises(ValidationError):
        InstanceVerdict.model_validate(payload)
