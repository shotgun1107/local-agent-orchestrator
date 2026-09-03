"""Shared worker contract for B1 and SDK-controlled comparison variants."""

from __future__ import annotations

from typing import Any

from .contract import (
    ResultEnvelope,
    RunSpec,
    TaskEnvelope,
    TaskLimits,
    TaskSpec,
    WorkspaceMode,
    canonical_json,
    sha256_bytes,
)


TASK_IDENTITY_FIELDS = frozenset({"run_id", "task_id", "attempt_id", "dispatch_token"})


def build_task_envelope(
    task: TaskSpec,
    *,
    run_id: str,
    task_id: str,
    attempt_id: str,
    requirements_version: int,
    timeout_seconds: int,
    remaining_attempts: int | None,
) -> TaskEnvelope:
    """Compile one TaskSpec into the worker-facing envelope used by every variant."""

    return TaskEnvelope(
        schema_version=1,
        run_id=run_id,
        task_id=task_id,
        attempt_id=attempt_id,
        requirements_version=requirements_version,
        dispatch_token=f"{attempt_id}:1",
        goal=task.goal,
        completion_criteria=[criterion.text for criterion in task.completion_criteria],
        inputs=task.inputs,
        read_scope=task.read_scope,
        write_scope=task.write_scope,
        workspace_mode=task.workspace_mode,
        check_names=task.check_names,
        limits=TaskLimits(
            timeout_seconds=timeout_seconds,
            remaining_attempts=remaining_attempts,
        ),
        result_schema_path="schemas/v1/result-envelope.schema.json",
    )


def task_semantics_payload(envelope: TaskEnvelope) -> dict[str, Any]:
    payload = envelope.model_dump(mode="json")
    for field in TASK_IDENTITY_FIELDS:
        payload.pop(field)
    return payload


def task_semantics_sha256(envelope: TaskEnvelope) -> str:
    return sha256_bytes(canonical_json(task_semantics_payload(envelope)).encode("utf-8"))


def render_worker_prompt(
    envelope: TaskEnvelope,
    feedback: dict[str, Any] | None = None,
) -> str:
    payload = envelope.model_dump(mode="json")
    instructions = (
        "Execute only the TaskEnvelope below. Respect read_scope and write_scope. "
        "Do not perform external actions. Return only JSON matching the supplied ResultEnvelope schema. "
        "Every artifacts.path must name one existing regular file; directory paths and glob patterns "
        "are invalid, so represent a directory output with a concrete manifest or index file. "
        "Your completed claim is evidence only; the controller will independently verify it."
    )
    if feedback:
        instructions += (
            " The resume_feedback contains only Controller-approved public Check diagnostics. "
            "Use the reported traceback and assertion details, rerun the named public Check, "
            "and correct only that failure without broadening scope. Do not claim success merely "
            "because a local command was not independently verified."
        )
        payload["resume_feedback"] = feedback
    return f"{instructions}\n\n{canonical_json(payload)}"


def result_schema() -> dict[str, Any]:
    return ResultEnvelope.model_json_schema()


def validate_result(value: Any) -> ResultEnvelope:
    return ResultEnvelope.model_validate(value)


def _stable_dependency_order(spec: RunSpec) -> list[TaskSpec]:
    by_key = {task.key: task for task in spec.tasks}
    ordered: list[TaskSpec] = []
    visited: set[str] = set()

    def visit(task: TaskSpec) -> None:
        if task.key in visited:
            return
        for dependency in task.depends_on:
            visit(by_key[dependency])
        visited.add(task.key)
        ordered.append(task)

    for task in spec.tasks:
        visit(task)
    return ordered


def build_oneshot_envelope(
    spec: RunSpec,
    *,
    run_id: str,
    task_id: str,
    attempt_id: str,
    requirements_version: int,
    timeout_seconds: int,
    remaining_attempts: int | None,
) -> TaskEnvelope:
    """Compile C0's information-equivalent synthetic TaskEnvelope."""

    ordered = _stable_dependency_order(spec)
    goals = [f"{task.goal}" for task in ordered]
    task_criteria = [
        criterion.text
        for task in ordered
        for criterion in task.completion_criteria
    ]
    run_criteria = [criterion.text for criterion in spec.completion_criteria]

    def unique(values: list[str]) -> list[str]:
        return list(dict.fromkeys(values))

    write_scope = unique([scope for task in ordered for scope in task.write_scope])
    inputs = []
    seen_inputs: set[str] = set()
    for task in ordered:
        for item in task.inputs:
            key = canonical_json(item)
            if key not in seen_inputs:
                seen_inputs.add(key)
                inputs.append(item)
    return TaskEnvelope(
        schema_version=1,
        run_id=run_id,
        task_id=task_id,
        attempt_id=attempt_id,
        requirements_version=requirements_version,
        dispatch_token=f"{attempt_id}:1",
        goal="\n\n".join([spec.request.text, *goals]),
        completion_criteria=[*run_criteria, *task_criteria],
        inputs=inputs,
        read_scope=unique([scope for task in ordered for scope in task.read_scope]),
        write_scope=write_scope,
        workspace_mode=(
            WorkspaceMode.SHARED_SERIAL_WRITE if write_scope else WorkspaceMode.READ_ONLY
        ),
        check_names=unique([name for task in ordered for name in task.check_names]),
        limits=TaskLimits(
            timeout_seconds=timeout_seconds,
            remaining_attempts=remaining_attempts,
        ),
        result_schema_path="schemas/v1/result-envelope.schema.json",
    )
