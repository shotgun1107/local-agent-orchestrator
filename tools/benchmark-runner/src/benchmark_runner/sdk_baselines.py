"""Thin C0, C1, and C2 adapters for the SDK-controlled comparison."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import JsonValue, ValidationError

from benchmark_runner.adapter import (
    CellContext,
    PreflightResult,
    VariantCapabilities,
    VariantEvidence,
)
from benchmark_runner.sdk_common import SdkRuntime, SdkThread, SdkUsage, WorkerContract


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
        except (OSError, ValueError) as exc:
            return PreflightResult(False, f"SDK baseline preflight failed: {type(exc).__name__}")
        return PreflightResult(True, f"{self.id()} preflight passed for {context.cell_id}")

    def _failure(
        self,
        *,
        failure_kind: str,
        turns: list[dict[str, JsonValue]],
        thread_ids: list[str],
    ) -> VariantEvidence:
        return VariantEvidence(
            outcome_state="failed",
            failure_kind=failure_kind,
            attempt_count=1,
            raw_payload={
                "adapter_id": self.id(),
                "model_turns": 0,
                "thread_ids": thread_ids,
                "turns": turns,
            },
            normalized_metrics={
                "session_count": len(thread_ids),
                "turn_count": len(turns),
                "attempt_count": 1,
                "token_usage_status": "unknown",
            },
        )

    def run(self, context: CellContext) -> VariantEvidence:
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
            if turns:
                turns[-1]["downstream_dispatched"] = True
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
            turns.append(turn_payload)
            model_active_seconds += result.duration_seconds
            if result.terminal_status != "completed":
                return self._failure(
                    failure_kind="sdk_terminal_failed",
                    turns=turns,
                    thread_ids=thread_ids,
                )
            try:
                validated = contract.validate_result(result.raw_result)
            except (ValidationError, ValueError, TypeError):
                return self._failure(
                    failure_kind="result_schema_invalid",
                    turns=turns,
                    thread_ids=thread_ids,
                )
            turn_payload["status_claim"] = str(validated["status_claim"])
            turn_payload["result_envelope"] = validated
            if validated["status_claim"] != "completed":
                return self._failure(
                    failure_kind=f"worker_{validated['status_claim']}",
                    turns=turns,
                    thread_ids=thread_ids,
                )

            current = result.cumulative_usage
            if current is None:
                usage_status = "unknown"
                continue
            previous = previous_usage.get(thread.id, SdkUsage(0, 0, 0))
            try:
                delta = current.subtract(previous)
            except ValueError:
                usage_status = "unknown"
                continue
            previous_usage[thread.id] = current
            turn_payload["usage_cumulative"] = current.public_payload()
            total_usage = SdkUsage(
                total_usage.input_tokens + delta.input_tokens,
                total_usage.output_tokens + delta.output_tokens,
                total_usage.total_tokens + delta.total_tokens,
            )
            turn_payload["usage_delta"] = delta.public_payload()

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
                "model_turns": 0,
                "thread_ids": thread_ids,
                "turns": turns,
            },
            normalized_metrics=metrics,
        )
