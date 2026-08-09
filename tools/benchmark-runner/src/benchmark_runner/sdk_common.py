"""SDK-controlled runtime boundary shared by the C0, C1, and C2 baselines."""

from __future__ import annotations

import json
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

from pydantic import JsonValue

from benchmark_runner.contract import present_api_key_environment_names


PINNED_SDK_VERSION = "0.144.4"
PINNED_MODEL = "gpt-5.6-terra"
PINNED_REASONING_EFFORT = "low"
PINNED_SANDBOX = "workspace_write"
PINNED_APPROVAL_MODE = "deny_all"


@dataclass(frozen=True)
class WorkerContract:
    render_prompt: Callable[[Any], str]
    result_schema: Callable[[], dict[str, Any]]
    validate_result: Callable[[Any], dict[str, JsonValue]]
    semantics_sha256: Callable[[Any], str]


@dataclass(frozen=True)
class SdkLiveControlSettings:
    sdk_version: str
    account_type: str
    model: str
    reasoning_effort: str
    thread_sandbox: str
    turn_sandbox: str
    thread_approval_mode: str
    turn_approval_mode: str
    cwd: Path
    ephemeral: bool
    output_schema_title: str
    validated_without_model_turn: bool
    actual_model_turns: int


def validate_sdk_live_controls(
    settings: SdkLiveControlSettings,
    *,
    environ: Mapping[str, str] | None = None,
) -> dict[str, JsonValue]:
    """Validate the frozen live controls without starting an SDK model turn."""

    present_keys = present_api_key_environment_names(environ)
    if present_keys:
        raise RuntimeError(
            f"API key environment is present ({', '.join(present_keys)}); "
            "ChatGPT-auth mode fails closed"
        )
    expected = {
        "sdk_version": PINNED_SDK_VERSION,
        "account_type": "chatgpt",
        "model": PINNED_MODEL,
        "reasoning_effort": PINNED_REASONING_EFFORT,
        "thread_sandbox": PINNED_SANDBOX,
        "turn_sandbox": PINNED_SANDBOX,
        "thread_approval_mode": PINNED_APPROVAL_MODE,
        "turn_approval_mode": PINNED_APPROVAL_MODE,
        "output_schema_title": "ResultEnvelope",
        "validated_without_model_turn": True,
        "actual_model_turns": 0,
    }
    for field, expected_value in expected.items():
        if getattr(settings, field) != expected_value:
            raise RuntimeError(f"SDK live control mismatch: {field}")
    cwd = Path(settings.cwd)
    if not cwd.is_absolute() or not cwd.resolve().is_dir():
        raise RuntimeError("SDK live control cwd must be an existing absolute directory")
    if settings.ephemeral is not False:
        raise RuntimeError("SDK live control mismatch: ephemeral")
    return {
        **expected,
        "cwd": str(cwd.resolve()),
        "ephemeral": False,
        "service_tier": "unspecified",
        "summary": "unspecified",
        "api_key_environment_names_present": [],
    }


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
    error_kind: str | None = None


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

    def close(self) -> None: ...


@dataclass(frozen=True)
class CodexSdkBindings:
    """Small injectable surface around openai-codex for no-model contract tests."""

    sdk_version: str
    codex_factory: Callable[[], Any]
    approval_deny_all: Any
    sandbox_workspace_write: Any


def default_codex_sdk_bindings() -> CodexSdkBindings:
    try:
        import openai_codex
        from openai_codex import ApprovalMode, Codex, Sandbox
    except ImportError as exc:
        raise RuntimeError(
            "install the Benchmark Runner 'codex' extra to use CodexSdkRuntime"
        ) from exc
    return CodexSdkBindings(
        sdk_version=str(getattr(openai_codex, "__version__", "unknown")),
        codex_factory=Codex,
        approval_deny_all=ApprovalMode.deny_all,
        sandbox_workspace_write=Sandbox.workspace_write,
    )


class CodexSdkRuntime:
    """Pinned ChatGPT-auth Codex SDK runtime for C0, C1, and C2.

    Construction and preflight do not start a model turn. The SDK boundary is
    injectable so its exact thread/turn options can be tested without opening
    the app-server or consuming usage.
    """

    def __init__(
        self,
        workspace: Path,
        *,
        bindings: CodexSdkBindings | None = None,
        environ: Mapping[str, str] | None = None,
        timeout_seconds: float = 900.0,
        interrupt_grace_seconds: float = 15.0,
    ) -> None:
        if timeout_seconds <= 0 or interrupt_grace_seconds < 0:
            raise ValueError(
                "SDK timeout must be positive and interrupt grace must be non-negative"
            )
        self.workspace = Path(workspace).resolve()
        self._bindings = bindings
        self._environ = environ
        self.timeout_seconds = timeout_seconds
        self.interrupt_grace_seconds = interrupt_grace_seconds
        self._context: Any | None = None
        self._client: Any | None = None
        self._threads: dict[str, Any] = {}
        self._actual_model_turns = 0
        self._preflight_evidence: dict[str, JsonValue] | None = None

    @property
    def actual_model_turns(self) -> int:
        return self._actual_model_turns

    @property
    def preflight_evidence(self) -> dict[str, JsonValue] | None:
        return dict(self._preflight_evidence) if self._preflight_evidence else None

    def _assert_chatgpt_environment(self) -> None:
        present_keys = present_api_key_environment_names(self._environ)
        if present_keys:
            raise RuntimeError(
                f"API key environment is present ({', '.join(present_keys)}); "
                "ChatGPT-auth mode fails closed"
            )

    def _load_bindings(self) -> CodexSdkBindings:
        if self._bindings is None:
            self._bindings = default_codex_sdk_bindings()
        if self._bindings.sdk_version != PINNED_SDK_VERSION:
            raise RuntimeError(
                f"CodexSdkRuntime requires openai-codex=={PINNED_SDK_VERSION}"
            )
        return self._bindings

    @staticmethod
    def _account_type(response: Any) -> str:
        account = getattr(response, "account", None)
        root = getattr(account, "root", None)
        value = getattr(root, "type", None)
        return str(getattr(value, "value", value) or "none")

    def preflight(self) -> None:
        self._assert_chatgpt_environment()
        if not self.workspace.is_absolute() or not self.workspace.is_dir():
            raise RuntimeError("SDK workspace must be an existing absolute directory")
        bindings = self._load_bindings()
        if self._client is not None:
            return
        context = bindings.codex_factory()
        try:
            client = context.__enter__()
            account_type = self._account_type(client.account(refresh_token=False))
            if account_type != "chatgpt":
                raise RuntimeError(
                    f"CodexSdkRuntime requires ChatGPT authentication; got {account_type}"
                )
            self._preflight_evidence = validate_sdk_live_controls(
                SdkLiveControlSettings(
                    sdk_version=bindings.sdk_version,
                    account_type=account_type,
                    model=PINNED_MODEL,
                    reasoning_effort=PINNED_REASONING_EFFORT,
                    thread_sandbox=PINNED_SANDBOX,
                    turn_sandbox=PINNED_SANDBOX,
                    thread_approval_mode=PINNED_APPROVAL_MODE,
                    turn_approval_mode=PINNED_APPROVAL_MODE,
                    cwd=self.workspace,
                    ephemeral=False,
                    output_schema_title="ResultEnvelope",
                    validated_without_model_turn=True,
                    actual_model_turns=0,
                ),
                environ=self._environ,
            )
        except Exception:
            context.__exit__(*sys.exc_info())
            raise
        self._context = context
        self._client = client

    def start_thread(self) -> SdkThread:
        self._assert_chatgpt_environment()
        if self._client is None:
            raise RuntimeError("CodexSdkRuntime preflight must succeed before dispatch")
        bindings = self._load_bindings()
        thread = self._client.thread_start(
            approval_mode=bindings.approval_deny_all,
            cwd=str(self.workspace),
            ephemeral=False,
            model=PINNED_MODEL,
            sandbox=bindings.sandbox_workspace_write,
        )
        thread_id = str(getattr(thread, "id", ""))
        if not thread_id or thread_id in self._threads:
            raise RuntimeError("Codex SDK returned an empty or duplicate thread ID")
        self._threads[thread_id] = thread
        return SdkThread(thread_id)

    @staticmethod
    def _usage(result: Any) -> SdkUsage | None:
        usage = getattr(result, "usage", None)
        total = getattr(usage, "total", None)
        if total is None:
            return None
        try:
            return SdkUsage(
                input_tokens=int(total.input_tokens),
                output_tokens=int(total.output_tokens),
                total_tokens=int(total.total_tokens),
            )
        except (AttributeError, TypeError, ValueError):
            return None

    @staticmethod
    def _terminal_status(result: Any) -> str:
        status = getattr(result, "status", "unknown")
        return str(getattr(status, "value", status))

    @staticmethod
    def _raw_result(result: Any) -> Any:
        response = getattr(result, "final_response", None)
        if not isinstance(response, str):
            return response
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return response

    def run_turn(
        self,
        thread: SdkThread,
        *,
        task_id: str,
        prompt: str,
        output_schema: dict[str, Any],
    ) -> SdkTurnResult:
        del task_id
        self._assert_chatgpt_environment()
        if self._client is None:
            raise RuntimeError("CodexSdkRuntime preflight must succeed before dispatch")
        raw_thread = self._threads.get(thread.id)
        if raw_thread is None:
            raise ValueError("unknown Codex SDK thread")
        if output_schema.get("title") != "ResultEnvelope":
            raise ValueError("Codex SDK turn requires the ResultEnvelope schema")
        bindings = self._load_bindings()
        result_box: list[Any] = []
        error_box: list[BaseException] = []
        handle_box: list[Any] = []
        finished = threading.Event()
        cancel_requested = threading.Event()
        started = time.monotonic()

        def consume() -> None:
            try:
                handle = raw_thread.turn(
                    prompt,
                    approval_mode=bindings.approval_deny_all,
                    cwd=str(self.workspace),
                    effort=PINNED_REASONING_EFFORT,
                    model=PINNED_MODEL,
                    output_schema=output_schema,
                    sandbox=bindings.sandbox_workspace_write,
                )
                handle_box.append(handle)
                self._actual_model_turns += 1
                if cancel_requested.is_set():
                    handle.interrupt()
                result_box.append(handle.run())
            except Exception as exc:
                error_box.append(exc)
            finally:
                finished.set()

        threading.Thread(
            target=consume,
            name=f"codex-sdk-{thread.id}",
            daemon=True,
        ).start()
        if not finished.wait(self.timeout_seconds):
            cancel_requested.set()
            if handle_box:
                try:
                    handle_box[0].interrupt()
                except Exception:
                    pass
            if not finished.wait(self.interrupt_grace_seconds):
                return SdkTurnResult(
                    terminal_status="unknown",
                    raw_result=None,
                    cumulative_usage=None,
                    duration_seconds=time.monotonic() - started,
                    error_kind="SdkTurnTimeout",
                )
        if error_box:
            return SdkTurnResult(
                terminal_status="unknown",
                raw_result={"error_kind": type(error_box[0]).__name__},
                cumulative_usage=None,
                duration_seconds=time.monotonic() - started,
                error_kind=type(error_box[0]).__name__,
            )
        if not result_box:
            return SdkTurnResult(
                terminal_status="unknown",
                raw_result=None,
                cumulative_usage=None,
                duration_seconds=time.monotonic() - started,
                error_kind="SdkTurnResultMissing",
            )
        result = result_box[0]
        duration_ms = getattr(result, "duration_ms", None)
        return SdkTurnResult(
            terminal_status=self._terminal_status(result),
            raw_result=self._raw_result(result),
            cumulative_usage=self._usage(result),
            duration_seconds=(
                float(duration_ms) / 1000.0
                if isinstance(duration_ms, (int, float)) and duration_ms >= 0
                else time.monotonic() - started
            ),
        )

    def close(self) -> None:
        context = self._context
        self._context = None
        self._client = None
        self._threads.clear()
        if context is not None:
            context.__exit__(None, None, None)


@dataclass(frozen=True)
class FakeTurnScript:
    effects: tuple[tuple[str, str], ...]
    result: dict[str, JsonValue]
    usage: SdkUsage = SdkUsage(input_tokens=10, output_tokens=5, total_tokens=15)
    terminal_status: str = "completed"
    error_kind: str | None = None


class FakeSdkRuntime:
    """Deterministic no-model runtime that records SDK thread and turn boundaries."""

    def __init__(
        self,
        workspace: Path,
        scripts: dict[str, FakeTurnScript | tuple[FakeTurnScript, ...]],
    ) -> None:
        self.workspace = Path(workspace).resolve()
        self.scripts = dict(scripts)
        self.started_threads: list[str] = []
        self.turns: list[dict[str, JsonValue]] = []
        self._usage_by_thread: dict[str, SdkUsage] = {}
        self._task_turn_ordinals: dict[str, int] = {}

    @property
    def actual_model_turns(self) -> int:
        """Fake turns exercise contracts only and never consume model usage."""

        return 0

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
            configured = self.scripts[task_id]
        except KeyError as exc:
            raise ValueError(f"missing fake SDK script for {task_id}") from exc
        task_turn_ordinal = self._task_turn_ordinals.get(task_id, 0) + 1
        if isinstance(configured, tuple):
            if task_turn_ordinal > len(configured):
                raise ValueError(
                    f"fake SDK script sequence exhausted for {task_id} "
                    f"at turn {task_turn_ordinal}"
                )
            script = configured[task_turn_ordinal - 1]
        else:
            script = configured
        self._task_turn_ordinals[task_id] = task_turn_ordinal
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
                "task_turn_ordinal": task_turn_ordinal,
                "prompt": prompt,
                "output_schema_title": str(output_schema.get("title", "")),
            }
        )
        return SdkTurnResult(
            terminal_status=script.terminal_status,
            raw_result=script.result,
            cumulative_usage=cumulative,
            duration_seconds=0.001,
            error_kind=script.error_kind,
        )

    def close(self) -> None:
        return None
