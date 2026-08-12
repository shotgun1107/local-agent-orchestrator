"""SDK baseline adapters, including the model-free SS1 Phase C candidate."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable, Literal

from pydantic import JsonValue, ValidationError

from benchmark_runner.adapter import (
    CellContext,
    PreflightResult,
    VariantCapabilities,
    VariantEvidence,
)
from benchmark_runner.sdk_common import SdkRuntime, SdkThread, SdkUsage, WorkerContract
from benchmark_runner.realistic_routing import (
    SS1_NEUTRAL_REVIEW_PROMPT,
    PassiveBoundaryObservation,
    PassiveBoundaryRecord,
    Ss1TaskRequest,
    assert_ss1_prompt_is_neutral,
    canonical_sha256,
    common_safety_decision,
)


SdkVariantId = Literal["c0", "c1", "c2"]


@dataclass(frozen=True)
class SdkBaselineConfig:
    variant_id: SdkVariantId
    tasks: tuple[Any, ...]
    contract: WorkerContract
    runtime: SdkRuntime


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class SdkBaselineAdapter:
    def __init__(self, config: SdkBaselineConfig) -> None:
        self.config = config

    def id(self) -> str:
        return self.config.variant_id

    def capabilities(self) -> VariantCapabilities:
        return VariantCapabilities(
            automated_launch=True,
            supports_usage=True,
            supports_attempt_count=True,
        )

    def preflight(self, context: CellContext) -> PreflightResult:
        if not self.config.tasks:
            return PreflightResult(False, "SDK baseline has no Tasks")
        if self.id() == "c0" and len(self.config.tasks) != 1:
            return PreflightResult(False, "C0 requires exactly one synthetic Task")
        task_ids = [str(task.task_id) for task in self.config.tasks]
        if len(task_ids) != len(set(task_ids)):
            return PreflightResult(False, "SDK baseline Task IDs must be unique")
        try:
            self.config.runtime.preflight()
            schema = self.config.contract.result_schema()
            if schema.get("title") != "ResultEnvelope":
                raise ValueError("unexpected worker result schema")
        except (OSError, RuntimeError, ValueError) as exc:
            self.config.runtime.close()
            return PreflightResult(False, f"SDK baseline preflight failed: {type(exc).__name__}")
        return PreflightResult(True, f"{self.id()} preflight passed for {context.cell_id}")

    def _failure(
        self,
        *,
        failure_kind: str,
        turns: list[dict[str, JsonValue]],
        thread_ids: list[str],
        total_usage: SdkUsage,
        usage_status: str,
        model_active_seconds: float,
    ) -> VariantEvidence:
        metrics: dict[str, JsonValue] = {
            "session_count": len(thread_ids),
            "turn_count": len(turns),
            "attempt_count": 1,
            "token_usage_status": usage_status,
            "model_active_seconds": model_active_seconds,
        }
        if usage_status == "measured":
            metrics["token_usage"] = total_usage.public_payload()
        return VariantEvidence(
            outcome_state="failed",
            failure_kind=failure_kind,
            attempt_count=1,
            raw_payload={
                "adapter_id": self.id(),
                "thread_ids": thread_ids,
                "turns": turns,
            },
            normalized_metrics=metrics,
        )

    def run(self, context: CellContext) -> VariantEvidence:
        try:
            return self._run(context)
        finally:
            self.config.runtime.close()

    def _run(self, context: CellContext) -> VariantEvidence:
        del context
        contract = self.config.contract
        output_schema = contract.result_schema()
        schema_sha256 = _canonical_sha256(output_schema)
        shared_thread: SdkThread | None = None
        thread_ids: list[str] = []
        previous_usage: dict[str, SdkUsage] = {}
        total_usage = SdkUsage(0, 0, 0)
        usage_status = "measured"
        turns: list[dict[str, JsonValue]] = []
        model_active_seconds = 0.0

        for task in self.config.tasks:
            if self.id() == "c1":
                if shared_thread is None:
                    shared_thread = self.config.runtime.start_thread()
                    thread_ids.append(shared_thread.id)
                thread = shared_thread
            else:
                thread = self.config.runtime.start_thread()
                thread_ids.append(thread.id)

            prompt = contract.render_prompt(task)
            prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
            semantics_sha256 = contract.semantics_sha256(task)
            result = self.config.runtime.run_turn(
                thread,
                task_id=str(task.task_id),
                prompt=prompt,
                output_schema=output_schema,
            )
            if turns:
                turns[-1]["downstream_dispatched"] = True
            turn_payload: dict[str, JsonValue] = {
                "task_id": str(task.task_id),
                "thread_id": thread.id,
                "terminal_status": result.terminal_status,
                "prompt_sha256": prompt_sha256,
                "output_schema_sha256": schema_sha256,
                "task_semantics_sha256": semantics_sha256,
                "duration_seconds": result.duration_seconds,
                "downstream_dispatched": False,
            }
            if result.error_kind is not None:
                turn_payload["error_kind"] = result.error_kind
            turns.append(turn_payload)
            model_active_seconds += result.duration_seconds

            current = result.cumulative_usage
            if current is None:
                usage_status = "unknown"
            else:
                previous = previous_usage.get(thread.id, SdkUsage(0, 0, 0))
                try:
                    delta = current.subtract(previous)
                except ValueError:
                    usage_status = "unknown"
                else:
                    previous_usage[thread.id] = current
                    turn_payload["usage_cumulative"] = current.public_payload()
                    total_usage = SdkUsage(
                        total_usage.input_tokens + delta.input_tokens,
                        total_usage.output_tokens + delta.output_tokens,
                        total_usage.total_tokens + delta.total_tokens,
                    )
                    turn_payload["usage_delta"] = delta.public_payload()

            if result.terminal_status != "completed":
                return self._failure(
                    failure_kind="sdk_terminal_failed",
                    turns=turns,
                    thread_ids=thread_ids,
                    total_usage=total_usage,
                    usage_status=usage_status,
                    model_active_seconds=model_active_seconds,
                )
            try:
                validated = contract.validate_result(result.raw_result)
            except (ValidationError, ValueError, TypeError):
                return self._failure(
                    failure_kind="result_schema_invalid",
                    turns=turns,
                    thread_ids=thread_ids,
                    total_usage=total_usage,
                    usage_status=usage_status,
                    model_active_seconds=model_active_seconds,
                )
            turn_payload["status_claim"] = str(validated["status_claim"])
            turn_payload["result_envelope"] = validated
            if validated["status_claim"] != "completed":
                return self._failure(
                    failure_kind=f"worker_{validated['status_claim']}",
                    turns=turns,
                    thread_ids=thread_ids,
                    total_usage=total_usage,
                    usage_status=usage_status,
                    model_active_seconds=model_active_seconds,
                )

        metrics: dict[str, JsonValue] = {
            "session_count": len(thread_ids),
            "turn_count": len(turns),
            "attempt_count": 1,
            "token_usage_status": usage_status,
            "model_active_seconds": model_active_seconds,
        }
        if usage_status == "measured":
            metrics["token_usage"] = total_usage.public_payload()
        return VariantEvidence(
            outcome_state="completed",
            failure_kind=None,
            attempt_count=1,
            raw_payload={
                "adapter_id": self.id(),
                "thread_ids": thread_ids,
                "turns": turns,
            },
            normalized_metrics=metrics,
        )


@dataclass(frozen=True)
class SS1ObserverContext:
    """Controller-private identity for one post-terminal passive observation."""

    experiment_id: str
    cell_id: str
    task: Ss1TaskRequest
    raw_attempt_id: str
    raw_thread_id: str
    turn_ordinal: int
    task_turn_ordinal: int
    boundary_ordinal: int
    turn_kind: Literal["initial", "ss1_self_review"]
    terminal_status: str
    error_kind: str | None


SS1Observer = Callable[[SS1ObserverContext], PassiveBoundaryObservation]
SS1TaskResolver = Callable[[Ss1TaskRequest], Ss1TaskRequest]


@dataclass(frozen=True)
class SS1PersistentConfig:
    tasks: tuple[Ss1TaskRequest, ...]
    contract: WorkerContract
    runtime: SdkRuntime
    observer: SS1Observer
    task_resolver: SS1TaskResolver | None = None
    forbidden_prompt_fragments: tuple[str, ...] = ()
    task_extra_turn_ceiling: Literal[1] = 1
    variant_extra_turn_ceiling: Literal[2] = 2

    def __post_init__(self) -> None:
        if self.task_extra_turn_ceiling != 1:
            raise ValueError("SS1 Task extra-turn ceiling must be exactly 1")
        if self.variant_extra_turn_ceiling != 2:
            raise ValueError("SS1 Variant extra-turn ceiling must be exactly 2")
        if any(type(task) is not Ss1TaskRequest for task in self.tasks):
            raise TypeError("SS1 tasks must use the exact Ss1TaskRequest type")
        if any(not fragment for fragment in self.forbidden_prompt_fragments):
            raise ValueError("SS1 forbidden prompt fragments must not be empty")


class SS1PersistentAdapter:
    """Persistent-thread SS1 adapter with bounded, self-requested neutral review."""

    def __init__(self, config: SS1PersistentConfig) -> None:
        if type(config) is not SS1PersistentConfig:
            raise TypeError("SS1 requires the exact SS1PersistentConfig type")
        self.config = config

    def id(self) -> str:
        return "ss1"

    def capabilities(self) -> VariantCapabilities:
        return VariantCapabilities(
            automated_launch=True,
            supports_usage=True,
            supports_attempt_count=True,
        )

    @staticmethod
    def _assert_extended_schema(schema: dict[str, Any]) -> None:
        if (
            schema.get("title") != "ResultEnvelope"
            or schema.get("type") != "object"
            or schema.get("additionalProperties") is not False
        ):
            raise ValueError("SS1 requires the strict extended ResultEnvelope schema")
        properties = schema.get("properties")
        required = schema.get("required")
        if not isinstance(properties, dict) or not isinstance(required, list):
            raise ValueError("SS1 ResultEnvelope schema is incomplete")
        if properties.get("needs_additional_review") != {"type": "boolean"}:
            raise ValueError("SS1 ResultEnvelope review flag differs")
        reason = properties.get("additional_review_reason")
        if not isinstance(reason, dict) or "anyOf" not in reason:
            raise ValueError("SS1 ResultEnvelope review reason differs")
        if not {
            "needs_additional_review",
            "additional_review_reason",
        }.issubset(required):
            raise ValueError("SS1 ResultEnvelope review fields are not required")

    def preflight(self, context: CellContext) -> PreflightResult:
        if not self.config.tasks:
            return PreflightResult(False, "SS1 has no Tasks")
        task_ids = [task.task_id for task in self.config.tasks]
        if len(task_ids) != len(set(task_ids)):
            return PreflightResult(False, "SS1 Task IDs must be unique")
        try:
            self.config.runtime.preflight()
            schema = self.config.contract.result_schema()
            self._assert_extended_schema(schema)
            assert_ss1_prompt_is_neutral(
                SS1_NEUTRAL_REVIEW_PROMPT,
                forbidden_fragments=self.config.forbidden_prompt_fragments,
            )
            for task in self.config.tasks:
                prompt = self.config.contract.render_prompt(task)
                assert_ss1_prompt_is_neutral(
                    prompt,
                    forbidden_fragments=self.config.forbidden_prompt_fragments,
                )
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            self.config.runtime.close()
            return PreflightResult(False, f"SS1 preflight failed: {type(exc).__name__}")
        return PreflightResult(True, f"SS1 preflight passed for {context.cell_id}")

    @staticmethod
    def _runtime_model_turns(runtime: SdkRuntime) -> int | None:
        value = getattr(runtime, "actual_model_turns", None)
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    def _metrics(
        self,
        *,
        turns: list[dict[str, JsonValue]],
        total_usage: SdkUsage,
        usage_status: str,
        model_active_seconds: float,
        extra_turns_used: int,
        ceiling_denials: list[dict[str, JsonValue]],
        session_count: int,
    ) -> dict[str, JsonValue]:
        metrics: dict[str, JsonValue] = {
            "session_count": session_count,
            "turn_count": len(turns),
            "attempt_count": 1,
            "token_usage_status": usage_status,
            "model_active_seconds": model_active_seconds,
            "ss1_self_review_count": extra_turns_used,
            "ss1_task_extra_turn_ceiling": self.config.task_extra_turn_ceiling,
            "ss1_variant_extra_turn_ceiling": self.config.variant_extra_turn_ceiling,
            "ss1_ceiling_denial_count": len(ceiling_denials),
            "resource_ceiling_reached": bool(ceiling_denials),
        }
        if usage_status == "measured":
            metrics["token_usage"] = total_usage.public_payload()
        return metrics

    def _evidence(
        self,
        *,
        context: CellContext,
        outcome_state: Literal["completed", "failed", "infrastructure_error"],
        failure_kind: str | None,
        turns: list[dict[str, JsonValue]],
        boundary_records: list[PassiveBoundaryRecord],
        ceiling_denials: list[dict[str, JsonValue]],
        total_usage: SdkUsage,
        usage_status: str,
        model_active_seconds: float,
        extra_turns_used: int,
        session_count: int,
        error_kind: str | None = None,
        stop_reason_codes: list[str] | None = None,
    ) -> VariantEvidence:
        public_thread_ids = sorted(
            {record.public_thread_id for record in boundary_records}
        )
        raw_payload: dict[str, JsonValue] = {
            "adapter_id": self.id(),
            "cell_id": context.cell_id,
            "actual_model_turns": self._runtime_model_turns(self.config.runtime),
            "public_thread_ids": public_thread_ids,
            "turns": turns,
            "boundary_records": [
                record.model_dump(mode="json") for record in boundary_records
            ],
            "ceiling_denials": ceiling_denials,
            "stop_required": outcome_state != "completed",
            "stop_reason": failure_kind,
            "stop_reason_codes": stop_reason_codes or [],
        }
        if error_kind is not None:
            raw_payload["error_kind"] = error_kind
        return VariantEvidence(
            outcome_state=outcome_state,
            failure_kind=failure_kind,
            attempt_count=1,
            raw_payload=raw_payload,
            normalized_metrics=self._metrics(
                turns=turns,
                total_usage=total_usage,
                usage_status=usage_status,
                model_active_seconds=model_active_seconds,
                extra_turns_used=extra_turns_used,
                ceiling_denials=ceiling_denials,
                session_count=session_count,
            ),
        )

    def run(self, context: CellContext) -> VariantEvidence:
        try:
            return self._run(context)
        finally:
            self.config.runtime.close()

    def _run(self, context: CellContext) -> VariantEvidence:
        turns: list[dict[str, JsonValue]] = []
        boundary_records: list[PassiveBoundaryRecord] = []
        ceiling_denials: list[dict[str, JsonValue]] = []
        total_usage = SdkUsage(0, 0, 0)
        previous_usage: SdkUsage | None = None
        usage_status = "measured"
        model_active_seconds = 0.0
        variant_extra_turns_used = 0
        session_count = 0

        try:
            output_schema = self.config.contract.result_schema()
            self._assert_extended_schema(output_schema)
            output_schema_sha256 = canonical_sha256(output_schema)
            assert_ss1_prompt_is_neutral(
                SS1_NEUTRAL_REVIEW_PROMPT,
                forbidden_fragments=self.config.forbidden_prompt_fragments,
            )
            self.config.runtime.preflight()
            thread = self.config.runtime.start_thread()
            session_count = 1
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            return self._evidence(
                context=context,
                outcome_state="infrastructure_error",
                failure_kind="ss1_setup_failed",
                turns=turns,
                boundary_records=boundary_records,
                ceiling_denials=ceiling_denials,
                total_usage=total_usage,
                usage_status=usage_status,
                model_active_seconds=model_active_seconds,
                extra_turns_used=variant_extra_turns_used,
                session_count=session_count,
                error_kind=type(exc).__name__,
            )

        expected_thread_id = thread.id
        raw_attempt_id = (
            f"ss1-attempt:{context.experiment_id}:{context.cell_id}:1"
        )
        global_turn_ordinal = 0
        boundary_ordinal = 0

        for frozen_task in self.config.tasks:
            try:
                task = (
                    frozen_task
                    if self.config.task_resolver is None
                    else self.config.task_resolver(frozen_task)
                )
                if type(task) is not Ss1TaskRequest or task.task_id != frozen_task.task_id:
                    raise TypeError("SS1 Task resolver changed the Task identity")
            except Exception as exc:
                return self._evidence(
                    context=context,
                    outcome_state="infrastructure_error",
                    failure_kind="ss1_task_resolution_failed",
                    turns=turns,
                    boundary_records=boundary_records,
                    ceiling_denials=ceiling_denials,
                    total_usage=total_usage,
                    usage_status=usage_status,
                    model_active_seconds=model_active_seconds,
                    extra_turns_used=variant_extra_turns_used,
                    session_count=session_count,
                    error_kind=type(exc).__name__,
                )
            task_turn_ordinal = 0
            next_kind: Literal["initial", "ss1_self_review"] = "initial"
            while True:
                global_turn_ordinal += 1
                task_turn_ordinal += 1
                prompt: str
                try:
                    prompt = (
                        self.config.contract.render_prompt(task)
                        if next_kind == "initial"
                        else SS1_NEUTRAL_REVIEW_PROMPT
                    )
                    assert_ss1_prompt_is_neutral(
                        prompt,
                        forbidden_fragments=self.config.forbidden_prompt_fragments,
                    )
                except (TypeError, ValueError) as exc:
                    return self._evidence(
                        context=context,
                        outcome_state="infrastructure_error",
                        failure_kind="ss1_prompt_information_leak",
                        turns=turns,
                        boundary_records=boundary_records,
                        ceiling_denials=ceiling_denials,
                        total_usage=total_usage,
                        usage_status=usage_status,
                        model_active_seconds=model_active_seconds,
                        extra_turns_used=variant_extra_turns_used,
                        session_count=session_count,
                        error_kind=type(exc).__name__,
                    )

                turn_payload: dict[str, JsonValue] = {
                    "task_id": task.task_id,
                    "turn_kind": next_kind,
                    "turn_ordinal": global_turn_ordinal,
                    "task_turn_ordinal": task_turn_ordinal,
                    "prompt_sha256": hashlib.sha256(
                        prompt.encode("utf-8")
                    ).hexdigest(),
                    "output_schema_sha256": output_schema_sha256,
                    "task_semantics_sha256": self.config.contract.semantics_sha256(
                        task
                    ),
                    "downstream_dispatched": False,
                }
                if turns:
                    turns[-1]["downstream_dispatched"] = True
                try:
                    result = self.config.runtime.run_turn(
                        thread,
                        task_id=task.task_id,
                        prompt=prompt,
                        output_schema=output_schema,
                    )
                except Exception as exc:
                    turn_payload["terminal_status"] = "not_observed"
                    turn_payload["error_kind"] = type(exc).__name__
                    turns.append(turn_payload)
                    return self._evidence(
                        context=context,
                        outcome_state="infrastructure_error",
                        failure_kind="ss1_runtime_dispatch_failed",
                        turns=turns,
                        boundary_records=boundary_records,
                        ceiling_denials=ceiling_denials,
                        total_usage=total_usage,
                        usage_status=usage_status,
                        model_active_seconds=model_active_seconds,
                        extra_turns_used=variant_extra_turns_used,
                        session_count=session_count,
                        error_kind=type(exc).__name__,
                    )

                boundary_ordinal += 1
                turn_payload["terminal_status"] = result.terminal_status
                turn_payload["duration_seconds"] = result.duration_seconds
                if result.error_kind is not None:
                    turn_payload["error_kind"] = result.error_kind
                turns.append(turn_payload)
                model_active_seconds += result.duration_seconds

                current_usage = result.cumulative_usage
                if current_usage is None:
                    usage_status = "unknown"
                else:
                    previous = previous_usage or SdkUsage(0, 0, 0)
                    try:
                        delta = current_usage.subtract(previous)
                    except ValueError:
                        usage_status = "unknown"
                    else:
                        previous_usage = current_usage
                        turn_payload["usage_cumulative"] = current_usage.public_payload()
                        turn_payload["usage_delta"] = delta.public_payload()
                        total_usage = SdkUsage(
                            total_usage.input_tokens + delta.input_tokens,
                            total_usage.output_tokens + delta.output_tokens,
                            total_usage.total_tokens + delta.total_tokens,
                        )

                observer_context = SS1ObserverContext(
                    experiment_id=context.experiment_id,
                    cell_id=context.cell_id,
                    task=task,
                    raw_attempt_id=raw_attempt_id,
                    raw_thread_id=thread.id,
                    turn_ordinal=global_turn_ordinal,
                    task_turn_ordinal=task_turn_ordinal,
                    boundary_ordinal=boundary_ordinal,
                    turn_kind=next_kind,
                    terminal_status=result.terminal_status,
                    error_kind=result.error_kind,
                )
                try:
                    observation = self.config.observer(observer_context)
                    if type(observation) is not PassiveBoundaryObservation:
                        raise TypeError(
                            "SS1 observer must return PassiveBoundaryObservation"
                        )
                    record = PassiveBoundaryRecord.from_raw_ids(
                        experiment_id=context.experiment_id,
                        cell_id=context.cell_id,
                        variant_id="ss1",
                        task_id=task.task_id,
                        raw_attempt_id=raw_attempt_id,
                        raw_thread_id=thread.id,
                        turn_ordinal=global_turn_ordinal,
                        boundary_ordinal=boundary_ordinal,
                        turn_kind=next_kind,
                        observation=observation,
                    )
                except Exception as exc:
                    return self._evidence(
                        context=context,
                        outcome_state="infrastructure_error",
                        failure_kind="ss1_observer_failed",
                        turns=turns,
                        boundary_records=boundary_records,
                        ceiling_denials=ceiling_denials,
                        total_usage=total_usage,
                        usage_status=usage_status,
                        model_active_seconds=model_active_seconds,
                        extra_turns_used=variant_extra_turns_used,
                        session_count=session_count,
                        error_kind=type(exc).__name__,
                    )
                boundary_records.append(record)
                turn_payload["public_thread_id"] = record.public_thread_id
                turn_payload["boundary_record_sha256"] = record.record_sha256
                turn_payload["observation_sha256"] = observation.observation_sha256

                if thread.id != expected_thread_id:
                    return self._evidence(
                        context=context,
                        outcome_state="infrastructure_error",
                        failure_kind="ss1_thread_drift",
                        turns=turns,
                        boundary_records=boundary_records,
                        ceiling_denials=ceiling_denials,
                        total_usage=total_usage,
                        usage_status=usage_status,
                        model_active_seconds=model_active_seconds,
                        extra_turns_used=variant_extra_turns_used,
                        session_count=session_count,
                    )

                safety = common_safety_decision(observation)
                if safety.stop:
                    return self._evidence(
                        context=context,
                        outcome_state="infrastructure_error",
                        failure_kind="ss1_common_safety_stop",
                        turns=turns,
                        boundary_records=boundary_records,
                        ceiling_denials=ceiling_denials,
                        total_usage=total_usage,
                        usage_status=usage_status,
                        model_active_seconds=model_active_seconds,
                        extra_turns_used=variant_extra_turns_used,
                        session_count=session_count,
                        stop_reason_codes=safety.reason_codes,
                    )
                if result.terminal_status != "completed":
                    return self._evidence(
                        context=context,
                        outcome_state="failed",
                        failure_kind="sdk_terminal_failed",
                        turns=turns,
                        boundary_records=boundary_records,
                        ceiling_denials=ceiling_denials,
                        total_usage=total_usage,
                        usage_status=usage_status,
                        model_active_seconds=model_active_seconds,
                        extra_turns_used=variant_extra_turns_used,
                        session_count=session_count,
                        error_kind=result.error_kind,
                    )
                try:
                    validated = self.config.contract.validate_result(result.raw_result)
                    status_claim = str(validated["status_claim"])
                    needs_review = validated["needs_additional_review"]
                    if type(needs_review) is not bool:
                        raise TypeError("SS1 review flag must be boolean")
                except (KeyError, ValidationError, ValueError, TypeError) as exc:
                    return self._evidence(
                        context=context,
                        outcome_state="failed",
                        failure_kind="result_schema_invalid",
                        turns=turns,
                        boundary_records=boundary_records,
                        ceiling_denials=ceiling_denials,
                        total_usage=total_usage,
                        usage_status=usage_status,
                        model_active_seconds=model_active_seconds,
                        extra_turns_used=variant_extra_turns_used,
                        session_count=session_count,
                        error_kind=type(exc).__name__,
                    )
                turn_payload["status_claim"] = status_claim
                turn_payload["result_envelope"] = validated
                if status_claim != "completed":
                    return self._evidence(
                        context=context,
                        outcome_state="failed",
                        failure_kind=f"worker_{status_claim}",
                        turns=turns,
                        boundary_records=boundary_records,
                        ceiling_denials=ceiling_denials,
                        total_usage=total_usage,
                        usage_status=usage_status,
                        model_active_seconds=model_active_seconds,
                        extra_turns_used=variant_extra_turns_used,
                        session_count=session_count,
                    )

                if not needs_review:
                    break
                if next_kind == "ss1_self_review":
                    ceiling_denials.append(
                        {
                            "task_id": task.task_id,
                            "requested_after_turn_ordinal": global_turn_ordinal,
                            "reason_code": "SS1_TASK_EXTRA_TURN_CEILING",
                        }
                    )
                    break
                if (
                    variant_extra_turns_used
                    >= self.config.variant_extra_turn_ceiling
                ):
                    ceiling_denials.append(
                        {
                            "task_id": task.task_id,
                            "requested_after_turn_ordinal": global_turn_ordinal,
                            "reason_code": "SS1_VARIANT_EXTRA_TURN_CEILING",
                        }
                    )
                    break
                variant_extra_turns_used += 1
                next_kind = "ss1_self_review"

        return self._evidence(
            context=context,
            outcome_state="completed",
            failure_kind=None,
            turns=turns,
            boundary_records=boundary_records,
            ceiling_denials=ceiling_denials,
            total_usage=total_usage,
            usage_status=usage_status,
            model_active_seconds=model_active_seconds,
            extra_turns_used=variant_extra_turns_used,
            session_count=session_count,
        )
