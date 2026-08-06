"""SDK-controlled runtime boundary shared by the C0, C1, and C2 baselines."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

from pydantic import JsonValue


@dataclass(frozen=True)
class WorkerContract:
    render_prompt: Callable[[Any], str]
    result_schema: Callable[[], dict[str, Any]]
    validate_result: Callable[[Any], dict[str, JsonValue]]
    semantics_sha256: Callable[[Any], str]


@dataclass(frozen=True)
class SdkThread:
    id: str


@dataclass(frozen=True)
class SdkUsage:
    input_tokens: int
    output_tokens: int
    total_tokens: int

    def __post_init__(self) -> None:
        if min(self.input_tokens, self.output_tokens, self.total_tokens) < 0:
            raise ValueError("SDK usage cannot be negative")
        if self.input_tokens + self.output_tokens != self.total_tokens:
            raise ValueError("SDK usage total must equal input plus output")

    def subtract(self, previous: "SdkUsage") -> "SdkUsage":
        delta = SdkUsage(
            input_tokens=self.input_tokens - previous.input_tokens,
            output_tokens=self.output_tokens - previous.output_tokens,
            total_tokens=self.total_tokens - previous.total_tokens,
        )
        return delta

    def public_payload(self) -> dict[str, JsonValue]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass(frozen=True)
class SdkTurnResult:
    terminal_status: str
    raw_result: Any
    cumulative_usage: SdkUsage | None
    duration_seconds: float


class SdkRuntime(Protocol):
    def preflight(self) -> None: ...

    def start_thread(self) -> SdkThread: ...

    def run_turn(
        self,
        thread: SdkThread,
        *,
        task_id: str,
        prompt: str,
        output_schema: dict[str, Any],
    ) -> SdkTurnResult: ...


@dataclass(frozen=True)
class FakeTurnScript:
    effects: tuple[tuple[str, str], ...]
    result: dict[str, JsonValue]
    usage: SdkUsage = SdkUsage(input_tokens=10, output_tokens=5, total_tokens=15)


class FakeSdkRuntime:
    """Deterministic no-model runtime that records SDK thread and turn boundaries."""

    def __init__(self, workspace: Path, scripts: dict[str, FakeTurnScript]) -> None:
        self.workspace = Path(workspace).resolve()
        self.scripts = dict(scripts)
        self.started_threads: list[str] = []
        self.turns: list[dict[str, JsonValue]] = []
        self._usage_by_thread: dict[str, SdkUsage] = {}

    def preflight(self) -> None:
        if not self.workspace.is_dir():
            raise ValueError("fake SDK workspace does not exist")

    def start_thread(self) -> SdkThread:
        thread_id = f"fake-sdk-thread-{len(self.started_threads) + 1}"
        self.started_threads.append(thread_id)
        self._usage_by_thread[thread_id] = SdkUsage(0, 0, 0)
        return SdkThread(thread_id)

    def run_turn(
        self,
        thread: SdkThread,
        *,
        task_id: str,
        prompt: str,
        output_schema: dict[str, Any],
    ) -> SdkTurnResult:
        if thread.id not in self._usage_by_thread:
            raise ValueError("unknown fake SDK thread")
        try:
            script = self.scripts[task_id]
        except KeyError as exc:
            raise ValueError(f"missing fake SDK script for {task_id}") from exc
        for relative, content in script.effects:
            destination = (self.workspace / relative).resolve()
            if not destination.is_relative_to(self.workspace):
                raise ValueError("fake SDK effect escaped workspace")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8", newline="\n")
        previous = self._usage_by_thread[thread.id]
        cumulative = SdkUsage(
            previous.input_tokens + script.usage.input_tokens,
            previous.output_tokens + script.usage.output_tokens,
            previous.total_tokens + script.usage.total_tokens,
        )
        self._usage_by_thread[thread.id] = cumulative
        self.turns.append(
            {
                "thread_id": thread.id,
                "task_id": task_id,
                "prompt": prompt,
                "output_schema_title": str(output_schema.get("title", "")),
            }
        )
        return SdkTurnResult(
            terminal_status="completed",
            raw_result=script.result,
            cumulative_usage=cumulative,
            duration_seconds=0.001,
        )
