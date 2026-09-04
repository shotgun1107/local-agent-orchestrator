from __future__ import annotations

import json
import time
from typing import Literal

import pytest
from pydantic import ConfigDict

from benchmark_runner.adapter import CellContext
from benchmark_runner.contract import StrictModel
from benchmark_runner.realistic_routing import (
    SS1_NEUTRAL_REVIEW_PROMPT,
    BoundaryAccessObservation,
    ChangedPath,
    EvidenceReference,
    PassiveBoundaryInput,
    PassiveBoundaryObservation,
    ProtectedFileObservation,
    SecretScanObservation,
    Ss1TaskRequest,
    build_ss1_worker_contract,
    canonical_sha256,
)
from benchmark_runner.sdk_baselines import (
    SS1ObserverContext,
    SS1PersistentAdapter,
    SS1PersistentConfig,
)
from benchmark_runner.sdk_common import (
    FakeSdkRuntime,
    FakeTurnScript,
    SdkThread,
    WorkerContract,
)


ZERO = "0" * 64
ONE = "1" * 64
TWO = "2" * 64
THREE = "3" * 64
FOUR = "4" * 64
CONTEXT = CellContext(experiment_id="exp-ss1", cell_id="cell-ss1")


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
        semantics_sha256=canonical_sha256,
    )


def _contract(*, forbidden: tuple[str, ...] = ()) -> WorkerContract:
    return build_ss1_worker_contract(
        _base_contract(),
        forbidden_prompt_fragments=forbidden,
    )


def _task(task_id: str, *, goal: str | None = None) -> Ss1TaskRequest:
    return Ss1TaskRequest(
        task_id=task_id,
        goal=goal or f"Complete public Task {task_id}.",
        completion_criteria=["The requested public behavior is complete."],
        declared_inputs=[EvidenceReference(path="README.md", sha256=ZERO)],
        predecessor_artifacts=[],
        read_scope=["README.md", "src"],
        write_scope=["src"],
    )


def _result(
    *,
    review: bool = False,
    reason: str | None = None,
    status: str = "completed",
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status_claim": status,
        "summary": "model-free scripted result",
        "needs_additional_review": review,
        "additional_review_reason": reason,
    }


def _observation(
    context: SS1ObserverContext,
    *,
    outside_task: bool = False,
    protected_changed: bool = False,
    secret_status: Literal["clear", "finding", "error"] = "clear",
    judge_status: Literal["clear", "denied", "succeeded", "error"] = "clear",
    state_status: Literal["clear", "denied", "succeeded", "error"] = "clear",
) -> PassiveBoundaryObservation:
    return PassiveBoundaryObservation.from_input(
        PassiveBoundaryInput(
            declared_read_scope=context.task.read_scope,
            declared_write_scope=context.task.write_scope,
            changed_paths=[ChangedPath(path="src/module.py", change_kind="modified")],
            outside_task_scope_paths=["other/public.txt"] if outside_task else [],
            outside_run_scope_paths=[],
            protected_files=[
                ProtectedFileObservation(
                    path="protected.txt",
                    before_sha256=ZERO,
                    after_sha256=ONE if protected_changed else ZERO,
                    changed=protected_changed,
                )
            ],
            declared_inputs=context.task.declared_inputs,
            predecessor_artifacts=context.task.predecessor_artifacts,
            workspace_tree_before_sha256=TWO,
            workspace_tree_after_sha256=THREE,
            secret_scan=SecretScanObservation(
                status=secret_status,
                finding_ids=[] if secret_status == "clear" else ["SECRET-001"],
            ),
            judge_access=BoundaryAccessObservation(
                status=judge_status,
                event_ids=[] if judge_status == "clear" else ["J-001"],
            ),
            state_access=BoundaryAccessObservation(
                status=state_status,
                event_ids=[] if state_status == "clear" else ["S-001"],
            ),
            observer_implementation_sha256=FOUR,
        )
    )


def _adapter(
    tmp_path,
    *,
    tasks: tuple[Ss1TaskRequest, ...],
    scripts: dict[str, FakeTurnScript | tuple[FakeTurnScript, ...]],
    observer=None,
    forbidden: tuple[str, ...] = (),
    runtime: FakeSdkRuntime | None = None,
) -> tuple[SS1PersistentAdapter, FakeSdkRuntime]:
    selected_runtime = runtime or FakeSdkRuntime(tmp_path, scripts)
    adapter = SS1PersistentAdapter(
        SS1PersistentConfig(
            tasks=tasks,
            contract=_contract(forbidden=forbidden),
            runtime=selected_runtime,
            observer=observer or _observation,
            forbidden_prompt_fragments=forbidden,
        )
    )
    return adapter, selected_runtime


def test_fake_runtime_sequences_per_task_and_preserves_single_repeat(tmp_path) -> None:
    runtime = FakeSdkRuntime(
        tmp_path,
        {
            "sequence": (
                FakeTurnScript(effects=(), result={"value": "first"}),
                FakeTurnScript(effects=(), result={"value": "second"}),
            ),
            "repeat": FakeTurnScript(effects=(), result={"value": "same"}),
        },
    )
    runtime.preflight()
    thread = runtime.start_thread()
    schema = {"title": "ResultEnvelope"}

    assert runtime.run_turn(
        thread, task_id="sequence", prompt="one", output_schema=schema
    ).raw_result == {"value": "first"}
    assert runtime.run_turn(
        thread, task_id="sequence", prompt="two", output_schema=schema
    ).raw_result == {"value": "second"}
    with pytest.raises(ValueError, match="sequence exhausted"):
        runtime.run_turn(
            thread, task_id="sequence", prompt="three", output_schema=schema
        )
    runtime.run_turn(thread, task_id="repeat", prompt="one", output_schema=schema)
    runtime.run_turn(thread, task_id="repeat", prompt="two", output_schema=schema)

    assert [turn["task_turn_ordinal"] for turn in runtime.turns] == [1, 2, 1, 2]
    assert runtime.actual_model_turns == 0


def test_multiple_tasks_and_review_use_one_thread_and_record_every_boundary(
    tmp_path,
) -> None:
    first = _task("task-a")
    second = _task("task-b")
    observed: list[SS1ObserverContext] = []

    def observer(context: SS1ObserverContext) -> PassiveBoundaryObservation:
        observed.append(context)
        return _observation(context)

    adapter, runtime = _adapter(
        tmp_path,
        tasks=(first, second),
        scripts={
            first.task_id: FakeTurnScript(effects=(), result=_result()),
            second.task_id: (
                FakeTurnScript(
                    effects=(),
                    result=_result(
                        review=True,
                        reason="workspace_consistency",
                    ),
                ),
                FakeTurnScript(effects=(), result=_result()),
            ),
        },
        observer=observer,
    )

    assert adapter.preflight(CONTEXT).ok is True
    evidence = adapter.run(CONTEXT)

    assert evidence.outcome_state == "completed"
    assert runtime.started_threads == ["fake-sdk-thread-1"]
    assert {turn["thread_id"] for turn in runtime.turns} == {
        "fake-sdk-thread-1"
    }
    assert [turn["task_id"] for turn in runtime.turns] == [
        "task-a",
        "task-b",
        "task-b",
    ]
    assert [turn["task_turn_ordinal"] for turn in runtime.turns] == [1, 1, 2]
    assert runtime.turns[-1]["prompt"] == SS1_NEUTRAL_REVIEW_PROMPT
    assert [item.turn_kind for item in observed] == [
        "initial",
        "initial",
        "ss1_self_review",
    ]
    assert len(evidence.raw_payload["boundary_records"]) == 3
    assert evidence.raw_payload["actual_model_turns"] == 0
    assert evidence.normalized_metrics["turn_count"] == 3
    assert evidence.normalized_metrics["ss1_self_review_count"] == 1


def test_second_review_request_hits_task_cap_without_third_turn(tmp_path) -> None:
    task = _task("task-cap")
    adapter, runtime = _adapter(
        tmp_path,
        tasks=(task,),
        scripts={
            task.task_id: (
                FakeTurnScript(
                    effects=(),
                    result=_result(review=True, reason="other_uncertainty"),
                ),
                FakeTurnScript(
                    effects=(),
                    result=_result(review=True, reason="other_uncertainty"),
                ),
                FakeTurnScript(effects=(), result=_result()),
            )
        },
    )

    evidence = adapter.run(CONTEXT)

    assert evidence.outcome_state == "completed"
    assert len(runtime.turns) == 2
    assert evidence.raw_payload["ceiling_denials"] == [
        {
            "task_id": "task-cap",
            "requested_after_turn_ordinal": 2,
            "reason_code": "SS1_TASK_EXTRA_TURN_CEILING",
        }
    ]
    assert evidence.normalized_metrics["resource_ceiling_reached"] is True


def test_completion_deadline_mode_stops_repeated_review_without_workspace_progress(
    tmp_path,
) -> None:
    task = _task("task-stalled-review")
    runtime = FakeSdkRuntime(
        tmp_path,
        {
            task.task_id: (
                FakeTurnScript(
                    effects=(),
                    result=_result(review=True, reason="public_check_uncertainty"),
                ),
                FakeTurnScript(
                    effects=(),
                    result=_result(review=True, reason="public_check_uncertainty"),
                ),
                FakeTurnScript(effects=(), result=_result()),
            )
        },
    )
    adapter = SS1PersistentAdapter(
        SS1PersistentConfig(
            tasks=(task,),
            contract=_contract(),
            runtime=runtime,
            observer=_observation,
            task_extra_turn_ceiling=None,
            variant_extra_turn_ceiling=None,
            completion_deadline_monotonic=time.monotonic() + 60,
        )
    )

    evidence = adapter.run(CONTEXT)

    assert evidence.outcome_state == "failed"
    assert evidence.failure_kind == "ss1_review_no_progress"
    assert len(runtime.turns) == 2
    assert evidence.raw_payload["turns"][-1]["review_progress"] == "stalled"
    assert evidence.raw_payload["ceiling_denials"] == []


def test_variant_cap_denies_third_task_review_without_transferring_reserve(
    tmp_path,
) -> None:
    tasks = tuple(_task(f"task-{index}") for index in range(1, 4))
    scripts = {
        task.task_id: (
            FakeTurnScript(
                effects=(),
                result=_result(review=True, reason="requirements_uncertainty"),
            ),
            FakeTurnScript(effects=(), result=_result()),
        )
        for task in tasks
    }
    adapter, runtime = _adapter(tmp_path, tasks=tasks, scripts=scripts)

    evidence = adapter.run(CONTEXT)

    assert evidence.outcome_state == "completed"
    assert [turn["task_id"] for turn in runtime.turns] == [
        "task-1",
        "task-1",
        "task-2",
        "task-2",
        "task-3",
    ]
    assert evidence.normalized_metrics["ss1_self_review_count"] == 2
    assert evidence.raw_payload["ceiling_denials"][0]["reason_code"] == (
        "SS1_VARIANT_EXTRA_TURN_CEILING"
    )


@pytest.mark.parametrize(
    ("script", "expected_kind"),
    [
        (
            FakeTurnScript(
                effects=(),
                result={
                    "schema_version": 1,
                    "status_claim": "completed",
                    "summary": "missing SS1 fields",
                },
            ),
            "result_schema_invalid",
        ),
        (
            FakeTurnScript(
                effects=(),
                result=_result(status="failed"),
            ),
            "worker_failed",
        ),
        (
            FakeTurnScript(
                effects=(),
                result=_result(),
                terminal_status="failed",
                error_kind="SyntheticTerminalFailure",
            ),
            "sdk_terminal_failed",
        ),
    ],
)
def test_schema_status_and_terminal_failures_stop_after_observation(
    tmp_path,
    script: FakeTurnScript,
    expected_kind: str,
) -> None:
    task = _task("task-failure")
    observed: list[SS1ObserverContext] = []

    def observer(context: SS1ObserverContext) -> PassiveBoundaryObservation:
        observed.append(context)
        return _observation(context)

    adapter, runtime = _adapter(
        tmp_path,
        tasks=(task,),
        scripts={task.task_id: script},
        observer=observer,
    )

    evidence = adapter.run(CONTEXT)

    assert evidence.outcome_state == "failed"
    assert evidence.failure_kind == expected_kind
    assert len(runtime.turns) == 1
    assert len(observed) == 1
    assert len(evidence.raw_payload["boundary_records"]) == 1


@pytest.mark.parametrize(
    "sentinel",
    [
        "PRIVATE-CHECK-ID",
        "PRIVATE-STDOUT-SENTINEL",
        "PRIVATE-STDERR-SENTINEL",
        "PRIVATE-JUDGE-SENTINEL",
    ],
)
def test_forbidden_controller_fragments_fail_before_dispatch(
    tmp_path,
    sentinel: str,
) -> None:
    task = _task("task-leak", goal=f"Do the work using {sentinel}.")
    adapter, runtime = _adapter(
        tmp_path,
        tasks=(task,),
        scripts={task.task_id: FakeTurnScript(effects=(), result=_result())},
        forbidden=(sentinel,),
    )

    evidence = adapter.run(CONTEXT)

    assert evidence.outcome_state == "infrastructure_error"
    assert evidence.failure_kind == "ss1_prompt_information_leak"
    assert runtime.turns == []


def test_review_prompt_is_exact_and_does_not_relay_controller_sentinels(
    tmp_path,
) -> None:
    sentinels = (
        "PRIVATE-CHECK-ID",
        "PRIVATE-STDOUT",
        "PRIVATE-STDERR",
        "PRIVATE-JUDGE",
    )
    task = _task("task-neutral-review")
    adapter, runtime = _adapter(
        tmp_path,
        tasks=(task,),
        scripts={
            task.task_id: (
                FakeTurnScript(
                    effects=(),
                    result=_result(review=True, reason="public_check_uncertainty"),
                ),
                FakeTurnScript(effects=(), result=_result()),
            )
        },
        forbidden=sentinels,
    )

    evidence = adapter.run(CONTEXT)

    assert evidence.outcome_state == "completed"
    assert runtime.turns[1]["prompt"] == SS1_NEUTRAL_REVIEW_PROMPT
    prompts = "\n".join(str(turn["prompt"]) for turn in runtime.turns)
    assert all(sentinel not in prompts for sentinel in sentinels)


def test_general_task_scope_and_protected_findings_are_passive(tmp_path) -> None:
    tasks = (_task("task-a"), _task("task-b"))

    def observer(context: SS1ObserverContext) -> PassiveBoundaryObservation:
        return _observation(
            context,
            outside_task=True,
            protected_changed=True,
        )

    adapter, runtime = _adapter(
        tmp_path,
        tasks=tasks,
        scripts={
            task.task_id: FakeTurnScript(effects=(), result=_result())
            for task in tasks
        },
        observer=observer,
    )

    evidence = adapter.run(CONTEXT)

    assert evidence.outcome_state == "completed"
    assert len(runtime.turns) == 2
    assert evidence.raw_payload["stop_required"] is False


@pytest.mark.parametrize(
    "finding",
    ["secret", "judge", "state"],
)
def test_secret_judge_and_state_findings_stop_before_review(
    tmp_path,
    finding: str,
) -> None:
    task = _task(f"task-{finding}")

    def observer(context: SS1ObserverContext) -> PassiveBoundaryObservation:
        return _observation(
            context,
            secret_status="finding" if finding == "secret" else "clear",
            judge_status="succeeded" if finding == "judge" else "clear",
            state_status="succeeded" if finding == "state" else "clear",
        )

    adapter, runtime = _adapter(
        tmp_path,
        tasks=(task,),
        scripts={
            task.task_id: (
                FakeTurnScript(
                    effects=(),
                    result=_result(review=True, reason="other_uncertainty"),
                ),
                FakeTurnScript(effects=(), result=_result()),
            )
        },
        observer=observer,
    )

    evidence = adapter.run(CONTEXT)

    assert evidence.outcome_state == "infrastructure_error"
    assert evidence.failure_kind == "ss1_common_safety_stop"
    assert len(runtime.turns) == 1
    assert evidence.raw_payload["stop_reason_codes"]


def test_observer_exception_fails_closed_without_next_dispatch(tmp_path) -> None:
    task = _task("task-observer")

    def observer(context: SS1ObserverContext) -> PassiveBoundaryObservation:
        del context
        raise RuntimeError("synthetic observer failure")

    adapter, runtime = _adapter(
        tmp_path,
        tasks=(task,),
        scripts={
            task.task_id: FakeTurnScript(
                effects=(),
                result=_result(review=True, reason="other_uncertainty"),
            )
        },
        observer=observer,
    )

    evidence = adapter.run(CONTEXT)

    assert evidence.outcome_state == "infrastructure_error"
    assert evidence.failure_kind == "ss1_observer_failed"
    assert len(runtime.turns) == 1
    assert evidence.raw_payload["boundary_records"] == []


class _DriftingRuntime(FakeSdkRuntime):
    def run_turn(self, thread: SdkThread, **kwargs):
        result = super().run_turn(thread, **kwargs)
        object.__setattr__(thread, "id", "drifted-thread")
        return result


def test_thread_drift_fails_closed_after_boundary_record(tmp_path) -> None:
    task = _task("task-drift")
    runtime = _DriftingRuntime(
        tmp_path,
        {task.task_id: FakeTurnScript(effects=(), result=_result())},
    )
    adapter, runtime = _adapter(
        tmp_path,
        tasks=(task,),
        scripts={},
        runtime=runtime,
    )

    evidence = adapter.run(CONTEXT)

    assert evidence.outcome_state == "infrastructure_error"
    assert evidence.failure_kind == "ss1_thread_drift"
    assert len(runtime.turns) == 1
    assert len(evidence.raw_payload["boundary_records"]) == 1


def test_public_boundary_ids_and_self_hashes_do_not_expose_raw_ids(tmp_path) -> None:
    task = _task("task-public-id")
    adapter, _runtime = _adapter(
        tmp_path,
        tasks=(task,),
        scripts={task.task_id: FakeTurnScript(effects=(), result=_result())},
    )

    evidence = adapter.run(CONTEXT)
    record = evidence.raw_payload["boundary_records"][0]
    encoded = json.dumps(record, sort_keys=True)

    assert "fake-sdk-thread-1" not in encoded
    assert "ss1-attempt:" not in encoded
    assert record["public_thread_id"].startswith("sha256:")
    assert record["public_attempt_id"].startswith("sha256:")
    observation = dict(record["observation"])
    observation_hash = observation.pop("observation_sha256")
    assert observation_hash == canonical_sha256(observation)
    record_payload = dict(record)
    record_hash = record_payload.pop("record_sha256")
    assert record_hash == canonical_sha256(record_payload)
