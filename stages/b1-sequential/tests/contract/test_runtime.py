from __future__ import annotations

import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestrator.contract import RuntimeProfile, TaskEnvelope, TaskLimits
from orchestrator.runtime import CodexRuntime, FakeRuntime, normalize_exception


def envelope(mode: str = "read_only") -> TaskEnvelope:
    return TaskEnvelope(
        schema_version=1,
        run_id="run_" + "1" * 32,
        task_id="task_" + "2" * 32,
        attempt_id="attempt_" + "3" * 32,
        requirements_version=1,
        dispatch_token="attempt_" + "3" * 32 + ":1",
        goal="test",
        completion_criteria=["done"],
        inputs=[],
        read_scope=["README.md"],
        write_scope=[] if mode == "read_only" else ["src/**"],
        workspace_mode=mode,
        check_names=["unit"],
        limits=TaskLimits(timeout_seconds=5, remaining_attempts=0),
        result_schema_path="schemas/v1/result-envelope.schema.json",
    )


def test_fake_runtime_complete_uses_blocking_contract(tmp_path: Path) -> None:
    runtime = FakeRuntime(workspace=tmp_path)
    session = runtime.start_session(envelope(), {"runtime": "fake"})
    turn = runtime.start_turn(session, envelope())
    result = runtime.await_terminal(turn, time.monotonic() + 1)
    assert result.terminal_status == "completed"
    assert result.raw_result["status_claim"] == "completed"


def test_fake_timeout_does_not_block_main_thread(tmp_path: Path) -> None:
    runtime = FakeRuntime(
        "timeout_interrupt_unsupported", workspace=tmp_path,
        fixture={"delay_ms": 10_000}, interrupt_grace_seconds=0.01,
    )
    session = runtime.start_session(envelope(), None)
    turn = runtime.start_turn(session, envelope())
    started = time.monotonic()
    result = runtime.await_terminal(turn, time.monotonic() + 0.03)
    assert time.monotonic() - started < 0.3
    assert result.terminal_status == "unknown"


def test_unknown_exception_is_not_retryable() -> None:
    failure = normalize_exception(RuntimeError("unknown failure"))
    assert failure.retryable is False
    assert failure.kind == "runtime_unknown"


def test_codex_adapter_sets_deny_all_on_thread_and_turn(monkeypatch, tmp_path: Path) -> None:
    import openai_codex

    calls = {}

    class FakeTurn:
        id = "codex-turn"

    class FakeThread:
        id = "codex-thread"

        def turn(self, prompt, **kwargs):
            calls["turn"] = kwargs
            return FakeTurn()

    class FakeClient:
        def account(self, *, refresh_token=False):
            return SimpleNamespace(account=SimpleNamespace(root=SimpleNamespace(type="chatgpt")))

        def thread_start(self, **kwargs):
            calls["thread_start"] = kwargs
            return FakeThread()

    class FakeContext:
        def __enter__(self):
            return FakeClient()

        def __exit__(self, *args):
            return None

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(openai_codex, "Codex", FakeContext)
    runtime = CodexRuntime(workspace=tmp_path)
    profile = RuntimeProfile(runtime="codex", model="gpt-test", auth_method="chatgpt", reasoning_effort="low")
    session = runtime.start_session(envelope(), profile)
    runtime.start_turn(session, envelope())
    assert calls["thread_start"]["approval_mode"] == openai_codex.ApprovalMode.deny_all
    assert calls["turn"]["approval_mode"] == openai_codex.ApprovalMode.deny_all
    assert calls["thread_start"]["ephemeral"] is False
    assert calls["turn"]["output_schema"]["title"] == "ResultEnvelope"


def test_codex_adapter_fails_closed_when_api_key_is_present(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "not-read-or-logged")
    with pytest.raises(Exception, match="fails closed"):
        CodexRuntime(workspace=tmp_path)


def test_codex_adapter_fails_closed_when_sdk_account_is_not_chatgpt(monkeypatch, tmp_path: Path) -> None:
    import openai_codex

    class FakeClient:
        def account(self, *, refresh_token=False):
            return SimpleNamespace(account=SimpleNamespace(root=SimpleNamespace(type="apiKey")))

    class FakeContext:
        def __enter__(self):
            return FakeClient()

        def __exit__(self, *args):
            return None

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(openai_codex, "Codex", FakeContext)
    with pytest.raises(Exception, match="requires ChatGPT authentication"):
        CodexRuntime(workspace=tmp_path)


def test_all_required_fake_fixtures_exist_and_load(tmp_path: Path) -> None:
    fixture_root = Path(__file__).parents[1] / "fixtures" / "fake-runtime"
    required = {
        "complete", "malformed_result", "transient_failure", "timeout_interrupt_supported",
        "timeout_interrupt_unsupported", "dispatch_uncertain", "duplicate_same_result",
        "duplicate_conflicting_result", "out_of_scope_write", "stale_input", "terminal_unknown",
        "artifact_corrupt",
    }
    assert {path.stem for path in fixture_root.glob("*.json")} == required
    for path in fixture_root.glob("*.json"):
        runtime = FakeRuntime.from_file(path, workspace=tmp_path)
        assert runtime.scenario == path.stem
