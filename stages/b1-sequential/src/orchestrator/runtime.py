"""Runtime boundary for deterministic fake execution and Codex SDK 0.144.4."""

from __future__ import annotations

import json
import os
import queue
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Protocol

from .contract import (
    FailureKind,
    InterruptOutcome,
    InterruptState,
    RuntimeCapabilities,
    RuntimeFailure,
    RuntimeOutcome,
    RuntimeProfile,
    SandboxMode,
    ResultEnvelope,
    TaskEnvelope,
    TerminalStatus,
    TokenCounts,
    UsageSnapshot,
    UsageStatus,
)
from .worker import render_worker_prompt

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
]
API_KEY_ENV_NAMES = ("OPENAI_API_KEY", "CODEX_API_KEY")


def present_api_key_environment_names(
    environ: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    source = os.environ if environ is None else environ
    return tuple(name for name in API_KEY_ENV_NAMES if name in source)


class RuntimeBoundaryError(RuntimeError):
    pass


class DispatchUncertain(RuntimeBoundaryError):
    """A runtime may have started, but its durable identifier was not received."""


def redact(value: object) -> str:
    text = str(value)
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text[:2000]


@dataclass(slots=True)
class SessionHandle:
    id: str
    raw: Any
    envelope: TaskEnvelope
    runtime_profile: Any
    initial_feedback: dict[str, Any] | None = None


@dataclass(slots=True)
class TurnHandle:
    id: str
    session: SessionHandle
    raw: Any
    turn_no: int
    interrupted: threading.Event = field(default_factory=threading.Event)


class RuntimePort(Protocol):
    def capabilities(self) -> RuntimeCapabilities: ...
    def start_session(self, task_envelope: TaskEnvelope, runtime_profile: Any) -> SessionHandle: ...
    def start_turn(self, session_handle: SessionHandle, task_envelope: TaskEnvelope) -> TurnHandle: ...
    def await_terminal(self, turn_handle: TurnHandle, monotonic_deadline: float) -> RuntimeOutcome: ...
    def resume_session(self, session_handle: SessionHandle, feedback_envelope: dict[str, Any]) -> TurnHandle: ...
    def interrupt(self, turn_handle: TurnHandle) -> InterruptOutcome: ...
    def close(self) -> None: ...


def _default_result() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status_claim": "completed",
        "summary": "fake runtime completed",
        "artifacts": [],
        "changed_paths": [],
        "checks_run_by_worker": [],
        "assumptions": [],
        "warnings": [],
        "requested_followup": None,
    }


class FakeRuntime:
    """Deterministic RuntimePort with the same blocking boundary as CodexRuntime."""

    def __init__(
        self,
        scenario: str = "complete",
        *,
        workspace: Path | None = None,
        fixture: dict[str, Any] | None = None,
        interrupt_grace_seconds: float = 0.05,
    ) -> None:
        self.scenario = scenario
        self.workspace = Path(workspace or Path.cwd()).resolve()
        self.fixture = fixture or {}
        self.interrupt_grace_seconds = interrupt_grace_seconds
        self.session_count = 0
        self.turn_count = 0
        self.initial_feedbacks: list[dict[str, Any] | None] = []
        self._outcomes: dict[str, RuntimeOutcome] = {}
        self._done: dict[str, threading.Event] = {}
        self._handles: dict[str, TurnHandle] = {}

    @classmethod
    def from_file(cls, path: Path, *, workspace: Path) -> "FakeRuntime":
        with path.open("r", encoding="utf-8") as handle:
            fixture = json.load(handle)
        return cls(str(fixture.get("scenario", "complete")), workspace=workspace, fixture=fixture)

    def capabilities(self) -> RuntimeCapabilities:
        interrupt = self.scenario != "timeout_interrupt_unsupported"
        return RuntimeCapabilities(
            runtime_name="fake",
            runtime_version="1",
            supports_interrupt=interrupt,
            supports_usage=True,
            supports_resume=True,
            supports_output_schema=True,
        )

    def start_session(self, task_envelope: TaskEnvelope, runtime_profile: Any) -> SessionHandle:
        self.session_count += 1
        return SessionHandle(
            id=f"fake-session-{self.session_count}",
            raw=None,
            envelope=task_envelope,
            runtime_profile=runtime_profile,
        )

    def start_turn(self, session_handle: SessionHandle, task_envelope: TaskEnvelope) -> TurnHandle:
        if self.scenario == "dispatch_uncertain":
            raise DispatchUncertain("fake runtime receipt deliberately lost")
        self.initial_feedbacks.append(session_handle.initial_feedback)
        self.turn_count += 1
        handle = TurnHandle(
            id=f"fake-turn-{self.turn_count}",
            session=session_handle,
            raw=None,
            turn_no=self.turn_count,
        )
        self._handles[handle.id] = handle
        return handle

    def resume_session(self, session_handle: SessionHandle, feedback_envelope: dict[str, Any]) -> TurnHandle:
        self.turn_count += 1
        handle = TurnHandle(
            id=f"fake-turn-{self.turn_count}",
            session=session_handle,
            raw={"feedback": feedback_envelope},
            turn_no=self.turn_count,
        )
        self._handles[handle.id] = handle
        return handle

    def _apply_effects(self, effects: list[dict[str, Any]]) -> None:
        for effect in effects:
            relative = str(effect.get("path", ""))
            destination = (self.workspace / relative).resolve()
            if self.workspace not in destination.parents and destination != self.workspace:
                raise RuntimeBoundaryError("FakeRuntime effect escaped workspace")
            kind = effect.get("type")
            if kind in {"write_file", "mutate_input"}:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(
                    str(effect.get("content", "")),
                    encoding="utf-8",
                    newline="\n",
                )
            elif kind == "delete_file" and destination.exists():
                destination.unlink()
            else:
                raise RuntimeBoundaryError(f"unknown FakeRuntime effect: {kind}")

    def _produce(self, handle: TurnHandle) -> RuntimeOutcome:
        scenario = self.scenario
        fixture = self.fixture
        scripted_turns = fixture.get("turns")
        if isinstance(scripted_turns, list) and handle.turn_no <= len(scripted_turns):
            scripted = scripted_turns[handle.turn_no - 1]
            if not isinstance(scripted, dict):
                raise RuntimeBoundaryError("FakeRuntime turn script must be an object")
            fixture = {**fixture, **scripted}
        delay_ms = int(fixture.get("delay_ms", 5))
        if scenario.startswith("timeout_"):
            delay_ms = int(fixture.get("delay_ms", 60_000))
        deadline = time.monotonic() + delay_ms / 1000
        while time.monotonic() < deadline:
            if handle.interrupted.is_set() and self.capabilities().supports_interrupt:
                return RuntimeOutcome(
                    terminal_status=TerminalStatus.CANCELLED,
                    terminal_evidence={"notification": "turn_completed", "reason": "interrupted"},
                    usage_snapshot=UsageSnapshot(status=UsageStatus.UNKNOWN),
                )
            time.sleep(min(0.005, max(0.0, deadline - time.monotonic())))

        if scenario == "transient_failure" and self.session_count == 1:
            return RuntimeOutcome(
                terminal_status=TerminalStatus.FAILED,
                terminal_evidence={"notification": "turn_completed", "status": "failed"},
                failure=RuntimeFailure(
                    kind=FailureKind.TRANSIENT_RUNTIME,
                    retryable=True,
                    redacted_message="deterministic transient failure",
                    source_exception_type="FakeTransientFailure",
                ),
                usage_snapshot=UsageSnapshot(status=UsageStatus.UNKNOWN),
            )
        if scenario == "terminal_unknown":
            return RuntimeOutcome(
                terminal_status=TerminalStatus.UNKNOWN,
                terminal_evidence={"notification": "missing"},
                failure=RuntimeFailure(
                    kind=FailureKind.TERMINAL_UNKNOWN,
                    retryable=False,
                    redacted_message="terminal evidence unavailable",
                    source_exception_type="FakeTerminalUnknown",
                ),
                usage_snapshot=UsageSnapshot(status=UsageStatus.UNKNOWN),
            )

        effects = list(fixture.get("effects", []))
        result: Any = fixture.get("result", _default_result())
        if scenario == "malformed_result" and handle.turn_no == 1:
            result = {"schema_version": 1, "status_claim": "completed"}
        elif scenario == "out_of_scope_write":
            effects = effects or [{"type": "write_file", "path": "outside-scope.txt", "content": "violation\n"}]
            result = {**_default_result(), "changed_paths": ["outside-scope.txt"]}
        elif scenario == "stale_input":
            path = fixture.get("stale_path", "input.txt")
            effects = effects or [{"type": "mutate_input", "path": path, "content": "changed while running\n"}]
        self._apply_effects(effects)
        external_changed_paths = [
            str(effect["path"]) for effect in effects if effect.get("type") == "mutate_input" and effect.get("path")
        ]
        usage_raw = fixture.get(
            "usage",
            {
                "status": "measured",
                "scope": "thread_cumulative",
                "total": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
            },
        )
        return RuntimeOutcome(
            terminal_status=TerminalStatus.COMPLETED,
            terminal_evidence={
                "notification": "turn_completed",
                "runtime_turn_id": handle.id,
                "duplicate_delivery": scenario in {"duplicate_same_result", "duplicate_conflicting_result"},
                "conflicting_duplicate": scenario == "duplicate_conflicting_result",
                "external_changed_paths": external_changed_paths,
                "corrupt_result_artifact": scenario == "artifact_corrupt",
            },
            raw_result=result,
            usage_snapshot=UsageSnapshot.model_validate(usage_raw),
        )

    def await_terminal(self, turn_handle: TurnHandle, monotonic_deadline: float) -> RuntimeOutcome:
        completed = threading.Event()
        self._done[turn_handle.id] = completed

        def consume() -> None:
            try:
                self._outcomes[turn_handle.id] = self._produce(turn_handle)
            except Exception as exc:  # runtime boundary must normalize every exception
                self._outcomes[turn_handle.id] = RuntimeOutcome(
                    terminal_status=TerminalStatus.FAILED,
                    terminal_evidence={"consumer": "failed"},
                    failure=normalize_exception(exc),
                    usage_snapshot=UsageSnapshot(status=UsageStatus.UNKNOWN),
                )
            finally:
                completed.set()

        threading.Thread(target=consume, name=f"fake-runtime-{turn_handle.id}", daemon=True).start()
        remaining = max(0.0, monotonic_deadline - time.monotonic())
        if completed.wait(remaining):
            return self._outcomes[turn_handle.id]
        interrupt = self.interrupt(turn_handle)
        if interrupt.state == InterruptState.CONFIRMED and completed.wait(self.interrupt_grace_seconds):
            return self._outcomes[turn_handle.id]
        return RuntimeOutcome(
            terminal_status=TerminalStatus.UNKNOWN,
            terminal_evidence={"deadline_exceeded": True, "interrupt_state": interrupt.state},
            failure=RuntimeFailure(
                kind=FailureKind.TERMINAL_UNKNOWN,
                retryable=False,
                redacted_message="terminal could not be proven before interrupt grace expired",
                source_exception_type="RuntimeDeadlineExceeded",
            ),
            usage_snapshot=UsageSnapshot(status=UsageStatus.UNKNOWN),
        )

    def interrupt(self, turn_handle: TurnHandle) -> InterruptOutcome:
        if not self.capabilities().supports_interrupt:
            return InterruptOutcome(state=InterruptState.UNSUPPORTED)
        turn_handle.interrupted.set()
        return InterruptOutcome(state=InterruptState.CONFIRMED, terminal_evidence={"requested": True})

    def close(self) -> None:
        return None


def normalize_exception(exc: BaseException) -> RuntimeFailure:
    retryable_types = {"ServerBusyError", "TransportClosedError", "RetryLimitExceededError"}
    retryable = type(exc).__name__ in retryable_types
    return RuntimeFailure(
        kind=FailureKind.TRANSIENT_RUNTIME if retryable else FailureKind.RUNTIME_UNKNOWN,
        retryable=retryable,
        redacted_message=redact(exc),
        source_exception_type=type(exc).__name__,
    )


class CodexRuntime:
    """Pinned openai-codex 0.144.4 adapter with fail-closed approvals."""

    def __init__(self, *, workspace: Path, interrupt_grace_seconds: float = 15.0) -> None:
        present_keys = present_api_key_environment_names()
        if present_keys:
            raise RuntimeBoundaryError(
                f"API key environment is present ({', '.join(present_keys)}); "
                "B1 ChatGPT-auth mode fails closed"
            )
        try:
            import openai_codex
            from openai_codex import ApprovalMode, Codex, Sandbox
        except ImportError as exc:
            raise RuntimeBoundaryError("install the 'codex' extra to use CodexRuntime") from exc
        if getattr(openai_codex, "__version__", None) != "0.144.4":
            raise RuntimeBoundaryError("CodexRuntime requires openai-codex==0.144.4")
        self._ApprovalMode = ApprovalMode
        self._Sandbox = Sandbox
        self._client_context = Codex()
        self._client = self._client_context.__enter__()
        try:
            account_response = self._client.account(refresh_token=False)
            account_root = getattr(getattr(account_response, "account", None), "root", None)
            account_type = getattr(account_root, "type", None)
        except Exception as exc:
            self._client_context.__exit__(type(exc), exc, exc.__traceback__)
            raise RuntimeBoundaryError(f"could not verify Codex authentication: {type(exc).__name__}") from exc
        if account_type != "chatgpt":
            self._client_context.__exit__(None, None, None)
            raise RuntimeBoundaryError(f"B1 requires ChatGPT authentication; active account type is {account_type or 'none'}")
        self.workspace = Path(workspace).resolve()
        self.interrupt_grace_seconds = interrupt_grace_seconds

    def capabilities(self) -> RuntimeCapabilities:
        return RuntimeCapabilities(
            runtime_name="codex",
            runtime_version="0.144.4",
            supports_interrupt=True,
            supports_usage=True,
            supports_resume=True,
            supports_output_schema=True,
        )

    def _sandbox(self, envelope: TaskEnvelope) -> Any:
        return (
            self._Sandbox.read_only
            if envelope.workspace_mode == "read_only"
            else self._Sandbox.workspace_write
        )

    def start_session(self, task_envelope: TaskEnvelope, runtime_profile: RuntimeProfile) -> SessionHandle:
        sandbox = self._sandbox(task_envelope)
        thread = self._client.thread_start(
            approval_mode=self._ApprovalMode.deny_all,
            cwd=str(self.workspace),
            ephemeral=False,
            model=runtime_profile.model,
            sandbox=sandbox,
        )
        return SessionHandle(
            id=thread.id,
            raw=thread,
            envelope=task_envelope,
            runtime_profile=runtime_profile,
        )

    def start_turn(self, session_handle: SessionHandle, task_envelope: TaskEnvelope) -> TurnHandle:
        raw = session_handle.raw.turn(
            render_worker_prompt(task_envelope, session_handle.initial_feedback),
            approval_mode=self._ApprovalMode.deny_all,
            cwd=str(self.workspace),
            effort=session_handle.runtime_profile.reasoning_effort,
            model=session_handle.runtime_profile.model,
            output_schema=ResultEnvelope.model_json_schema(),
            sandbox=self._sandbox(task_envelope),
        )
        return TurnHandle(id=raw.id, session=session_handle, raw=raw, turn_no=1)

    def resume_session(self, session_handle: SessionHandle, feedback_envelope: dict[str, Any]) -> TurnHandle:
        raw = session_handle.raw.turn(
            render_worker_prompt(session_handle.envelope, feedback_envelope),
            approval_mode=self._ApprovalMode.deny_all,
            cwd=str(self.workspace),
            effort=session_handle.runtime_profile.reasoning_effort,
            model=session_handle.runtime_profile.model,
            output_schema=ResultEnvelope.model_json_schema(),
            sandbox=self._sandbox(session_handle.envelope),
        )
        return TurnHandle(id=raw.id, session=session_handle, raw=raw, turn_no=2)

    def _collect(self, turn_handle: TurnHandle, destination: queue.Queue[RuntimeOutcome]) -> None:
        try:
            result = turn_handle.raw.run()
            status = getattr(result.status, "value", str(result.status))
            usage = _usage_from_codex(result.usage)
            evidence = {
                "runtime_turn_id": result.id,
                "status": status,
                "started_at": result.started_at,
                "completed_at": result.completed_at,
                "duration_ms": result.duration_ms,
            }
            if status == "completed":
                try:
                    raw_result = json.loads(result.final_response or "")
                except json.JSONDecodeError:
                    raw_result = result.final_response
                destination.put(RuntimeOutcome(
                    terminal_status=TerminalStatus.COMPLETED,
                    terminal_evidence=evidence,
                    raw_result=raw_result,
                    usage_snapshot=usage,
                ))
            elif status == "interrupted":
                destination.put(RuntimeOutcome(
                    terminal_status=TerminalStatus.CANCELLED,
                    terminal_evidence=evidence,
                    usage_snapshot=usage,
                ))
            else:
                failure = _failure_from_turn_error(result.error)
                destination.put(RuntimeOutcome(
                    terminal_status=TerminalStatus.FAILED,
                    terminal_evidence=evidence,
                    failure=failure,
                    usage_snapshot=usage,
                ))
        except Exception as exc:
            destination.put(RuntimeOutcome(
                terminal_status=TerminalStatus.FAILED,
                terminal_evidence={"consumer": "failed"},
                failure=normalize_exception(exc),
                usage_snapshot=UsageSnapshot(status=UsageStatus.UNKNOWN),
            ))

    def await_terminal(self, turn_handle: TurnHandle, monotonic_deadline: float) -> RuntimeOutcome:
        destination: queue.Queue[RuntimeOutcome] = queue.Queue(maxsize=1)
        threading.Thread(
            target=self._collect,
            args=(turn_handle, destination),
            name=f"codex-consumer-{turn_handle.id}",
            daemon=True,
        ).start()
        remaining = max(0.0, monotonic_deadline - time.monotonic())
        try:
            return destination.get(timeout=remaining)
        except queue.Empty:
            interrupt = self.interrupt(turn_handle)
            if interrupt.state == InterruptState.CONFIRMED:
                try:
                    return destination.get(timeout=self.interrupt_grace_seconds)
                except queue.Empty:
                    pass
            return RuntimeOutcome(
                terminal_status=TerminalStatus.UNKNOWN,
                terminal_evidence={"deadline_exceeded": True, "interrupt_state": interrupt.state},
                failure=RuntimeFailure(
                    kind=FailureKind.TERMINAL_UNKNOWN,
                    retryable=False,
                    redacted_message="Codex terminal not proven before interrupt grace expired",
                    source_exception_type="RuntimeDeadlineExceeded",
                ),
                usage_snapshot=UsageSnapshot(status=UsageStatus.UNKNOWN),
            )

    def interrupt(self, turn_handle: TurnHandle) -> InterruptOutcome:
        try:
            turn_handle.raw.interrupt()
            turn_handle.interrupted.set()
            return InterruptOutcome(state=InterruptState.CONFIRMED, terminal_evidence={"requested": True})
        except Exception as exc:
            return InterruptOutcome(
                state=InterruptState.FAILED,
                terminal_evidence={"error_type": type(exc).__name__, "message": redact(exc)},
            )

    def close(self) -> None:
        self._client_context.__exit__(None, None, None)


def _usage_from_codex(usage: Any) -> UsageSnapshot:
    if usage is None:
        return UsageSnapshot(status=UsageStatus.UNKNOWN)
    total = usage.total
    return UsageSnapshot(
        status=UsageStatus.MEASURED,
        scope="thread_cumulative",
        total=TokenCounts(
            input_tokens=int(total.input_tokens),
            output_tokens=int(total.output_tokens),
            total_tokens=int(total.total_tokens),
        ),
    )


def _failure_from_turn_error(error: Any) -> RuntimeFailure:
    if error is None:
        return RuntimeFailure(
            kind=FailureKind.RUNTIME_UNKNOWN,
            retryable=False,
            redacted_message="Codex turn failed without structured error",
            source_exception_type="TurnErrorMissing",
        )
    info = getattr(error, "codex_error_info", None)
    root = getattr(info, "root", None)
    value = getattr(root, "value", None)
    retryable_values = {"serverOverloaded", "internalServerError"}
    retryable_types = {
        "HttpConnectionFailedCodexErrorInfo",
        "ResponseStreamConnectionFailedCodexErrorInfo",
        "ResponseStreamDisconnectedCodexErrorInfo",
        "ResponseTooManyFailedAttemptsCodexErrorInfo",
    }
    retryable = value in retryable_values or type(root).__name__ in retryable_types
    return RuntimeFailure(
        kind=FailureKind.TRANSIENT_RUNTIME if retryable else FailureKind.RUNTIME_UNKNOWN,
        retryable=retryable,
        redacted_message=redact(getattr(error, "message", "Codex turn failed")),
        source_exception_type=type(root).__name__ if root is not None else type(error).__name__,
    )
