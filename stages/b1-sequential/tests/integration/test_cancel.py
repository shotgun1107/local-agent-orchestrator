"""F10: local controller/CLI cancellation; never constructs a live SDK client."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import threading
import time

import pytest
import yaml

from orchestrator.cancel import cancel_requested, request_cancel
from orchestrator.contract import CheckResult, InterruptOutcome, RuntimeOutcome, TerminalStatus, canonical_json, utc_now
from orchestrator.ledger import Ledger
from orchestrator.recover import ControllerLock, backup_run, verify_backup
from orchestrator.runtime import DispatchUncertain, FakeRuntime
from orchestrator.schedule import Orchestrator, load_project
from orchestrator.worker import build_task_envelope
import orchestrator.schedule as schedule_module
import orchestrator.cli as cli_module
import orchestrator.verify as verify_module
from tests.conftest import git, make_spec
from tests.unit.test_ledger import create_run


def cancel_cli(state: Path, run_id: str):
    return subprocess.run(
        [sys.executable, "-B", "-m", "orchestrator", "run", "cancel", run_id],
        env={**os.environ, "LAO_STATE_ROOT": str(state)},
        capture_output=True, text=True, encoding="utf-8", timeout=10, shell=False,
    )


def test_active_cancel_queues_without_opening_a_writer(tmp_path):
    state = tmp_path / "state"
    with ControllerLock(state):
        with Ledger(state / "ledger.sqlite") as ledger:
            run, _ = create_run(ledger)
            before = ledger.load_run_snapshot(run["run_id"])
            result = cancel_cli(state, run["run_id"])
            assert result.returncode == 0, result.stderr
            reply = json.loads(result.stdout)
            assert reply["cancel_requested"] is True
            assert reply["changed"] is False
            assert reply["state"] == "DRAFT"
            assert ledger.load_run_snapshot(run["run_id"]) == before


def run_id_from(state):
    connection = sqlite3.connect((state / "ledger.sqlite").as_uri() + "?mode=ro", uri=True)
    try:
        return connection.execute("SELECT run_id FROM runs ORDER BY created_at DESC LIMIT 1").fetchone()[0]
    finally:
        connection.close()


def snapshot(state, run_id):
    with Ledger(state / "ledger.sqlite") as ledger:
        return ledger.load_run_snapshot(run_id)


class ControlledRuntime(FakeRuntime):
    def __init__(self, mode, **kwargs):
        super().__init__(fixture={"delay_ms": 6000}, **kwargs)
        self.mode = mode
        self.entered = threading.Event()
        self.release = threading.Event()
        self.interrupt_calls = 0

    def await_terminal(self, turn, deadline):
        self.entered.set()
        if self.mode == "fake":
            return super().await_terminal(turn, deadline)
        self.release.wait(8)
        if self.mode == "await_raises":
            raise RuntimeError("fake terminal consumer failure")
        return RuntimeOutcome(
            terminal_status=TerminalStatus.COMPLETED if self.mode == "completed_race" else TerminalStatus.CANCELLED,
            terminal_evidence={"notification": "turn_completed"},
        )

    def interrupt(self, turn):
        self.interrupt_calls += 1
        if self.mode == "fake":
            return super().interrupt(turn)
        if self.mode in {"confirmed", "completed_race", "await_raises"}:
            self.release.set()
        if self.mode == "raises":
            raise RuntimeError("fake interrupt failure")
        if self.mode == "hangs":
            self.release.wait(8)
        return InterruptOutcome(state=self.mode if self.mode in {"unsupported", "failed"} else "confirmed")


def start_background(app, spec):
    errors = []

    def run():
        try:
            app.start(spec)
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread, errors


@pytest.mark.parametrize("mode", ["fake", "confirmed", "completed_race", "unsupported", "failed", "raises", "hangs", "no_terminal", "await_raises"])
def test_owner_handles_request_and_never_adopts_or_retries(mode, tmp_path, project_factory, monkeypatch):
    root = project_factory(task_timeout=60)
    state = tmp_path / "state"
    port = ControlledRuntime(mode, workspace=root)
    monkeypatch.setattr(schedule_module, "preflight_check_environment", lambda *a, **kw: None)
    app = Orchestrator(load_project(root), state_root=state, check_temp_root=tmp_path / "checks",
                       runtime_port=port, runtime_profile_override={"runtime": "fake"}, auth_method_override="none")
    thread, errors = start_background(app, make_spec(tasks=2))
    try:
        assert port.entered.wait(5), errors
        run_id = run_id_from(state)
        result = cancel_cli(state, run_id)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["cancel_requested"] is True
        thread.join(5)
        assert not thread.is_alive(), "controller did not stop within the bounded cancellation window"
        assert errors == []
        result = snapshot(state, run_id)
        confirmed = mode in {"fake", "confirmed", "completed_race"}
        assert result["run"]["state"] == ("CANCELLED" if confirmed else "BLOCKED")
        assert result["tasks"][0]["attempts"][0]["state"] == ("CANCELLED" if confirmed else "QUARANTINED")
        assert result["sessions"][0]["state"] == ("COMPLETED" if mode == "completed_race" else "CANCELLED" if confirmed else "QUARANTINED")
        assert result["tasks"][1]["state"] == "CANCELLED"
        assert all(task["active_attempt_id"] is None for task in result["tasks"])
        assert result["checks"] == []
        assert port.session_count == port.turn_count == port.interrupt_calls == 1
        assert len(result["decisions"]) == 1
        report = json.loads((state / f"runs/{run_id}/report/summary.json").read_text(encoding="utf-8"))
        assert report["state"] == result["run"]["state"]
        assert report["tasks"][0]["state"] == result["tasks"][0]["state"]
        # Durable intent also prevents a later resume from re-dispatching a quarantined Run.
        app.resume(run_id, make_spec(tasks=2))
        assert port.turn_count == 1
        assert len(snapshot(state, run_id)["decisions"]) == 1
    finally:
        port.release.set()
        thread.join(10)
        app.close()


def seed_attempt(state, stage):
    with ControllerLock(state), Ledger(state / "ledger.sqlite") as ledger:
        run, task = create_run(ledger)
        ledger.transition("run", run["run_id"], 0, "READY", "ready", {})
        ledger.transition("run", run["run_id"], 1, "RUNNING", "running", {})
        task = ledger.transition("task", task["task_id"], 0, "READY", "ready", {})
        attempt_id = "attempt_" + "1" * 32
        envelope = build_task_envelope(make_spec().tasks[0], run_id=run["run_id"], task_id=task["task_id"],
            attempt_id=attempt_id, requirements_version=1, timeout_seconds=60, remaining_attempts=0)
        attempt = ledger.begin_attempt(task["task_id"], 1, "initial", canonical_json(envelope), "a" * 64, attempt_id=attempt_id)
        session = ledger.create_session(attempt["attempt_id"], "fake", "1", "fake-session", "local_default",
                                        str(state), "read_only", {}, "unknown")
        if stage != "DISPATCHING":
            ledger.mark_dispatched(attempt["attempt_id"], session["session_id"], "fake-turn")
        if stage == "VERIFYING":
            ledger.update_session_terminal(session["session_id"], "COMPLETED", {"terminal": True}, "unknown", None)
            for aggregate, identity in [("attempt", attempt["attempt_id"]), ("task", task["task_id"])]:
                current = ledger.get(aggregate, identity)
                current = ledger.transition(aggregate, identity, current["version"], "REPORTED", "reported", {})
                ledger.transition(aggregate, identity, current["version"], "VERIFYING", "verifying", {})
            check = ledger.create_check({"task_id": task["task_id"], "attempt_id": attempt["attempt_id"],
                                         "check_name": "test_check", "argv": ["fake"]})
            ledger.start_check(check["check_id"])
        return run["run_id"]


@pytest.mark.parametrize("stage,expected", [("DISPATCHING", "DISPATCH_UNCERTAIN"), ("RUNNING", "QUARANTINED"), ("VERIFYING", "BLOCKED")])
def test_ownerless_attempt_is_not_falsely_confirmed(stage, expected, tmp_path):
    state = tmp_path / "state"
    run_id = seed_attempt(state, stage)
    result = cancel_cli(state, run_id)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["state"] == "BLOCKED"
    data = snapshot(state, run_id)
    assert data["tasks"][0]["attempts"][0]["state"] == expected
    assert data["tasks"][0]["active_attempt_id"] is None
    report = json.loads((state / f"runs/{run_id}/report/summary.json").read_text(encoding="utf-8"))
    assert report["state"] == "BLOCKED"
    assert report["tasks"][0]["attempts"][0]["state"] == expected
    if stage == "VERIFYING":
        assert data["checks"][0]["state"] == "ERROR"
    assert cancel_cli(state, run_id).returncode == 0
    assert snapshot(state, run_id) == data


@pytest.mark.parametrize("terminal", ["CANCELLED", "COMPLETED", "FAILED"])
def test_terminal_cancel_is_noop_even_when_lock_is_busy(tmp_path, terminal):
    state = tmp_path / "state"
    with ControllerLock(state), Ledger(state / "ledger.sqlite") as ledger:
        run, _ = create_run(ledger)
        steps = ["CANCELLED"] if terminal == "CANCELLED" else ["READY", "RUNNING", "VERIFYING", "COMPLETED"] if terminal == "COMPLETED" else ["READY", "RUNNING", "FAILED"]
        for version, target in enumerate(steps):
            ledger.transition("run", run["run_id"], version, target, "test_transition", {})
        before = ledger.load_run_snapshot(run["run_id"])
        result = cancel_cli(state, run["run_id"])
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout) == {"run_id": run["run_id"], "state": terminal, "changed": False, "cancel_requested": False}
        assert ledger.load_run_snapshot(run["run_id"]) == before
        assert not cancel_requested(state, run["run_id"])


def test_intent_is_idempotent_scoped_and_rejects_corruption(tmp_path):
    request_cancel(tmp_path, "../unsafe/path")
    assert cancel_requested(tmp_path, "../unsafe/path")
    assert not cancel_requested(tmp_path, "another-run")
    request_cancel(tmp_path, "../unsafe/path")
    files = list((tmp_path / "cancel-requests").iterdir())
    assert len(files) == 1
    files[0].write_text("not an intent", encoding="utf-8")
    with pytest.raises(ValueError, match="empty regular"):
        cancel_requested(tmp_path, "../unsafe/path")


def test_cancel_unknown_run_does_not_create_intent(tmp_path):
    result = cancel_cli(tmp_path, "unknown")
    assert result.returncode == 2
    assert list(tmp_path.iterdir()) == []


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object process-tree integration")
def test_cancel_during_real_check_reaps_descendant(tmp_path, project_factory, monkeypatch):
    root = project_factory()
    ready = tmp_path / "check-child.pid"
    child_code = f"import os,time; from pathlib import Path; Path({str(ready)!r}).write_text(str(os.getpid())); time.sleep(60)"
    command = f"import subprocess,sys,time; subprocess.Popen([sys.executable,'-c',{child_code!r}]); print('check-started',flush=True); time.sleep(60)"
    checks_path = root / ".orchestrator/checks.yaml"
    checks = yaml.safe_load(checks_path.read_text(encoding="utf-8"))
    checks["checks"]["test_check"]["argv"] = ["python", "-c", command]
    checks["checks"]["test_check"]["timeout_seconds"] = 30
    checks_path.write_text(yaml.safe_dump(checks, sort_keys=False), encoding="utf-8")
    git(root, "add", ".orchestrator/checks.yaml")
    git(root, "commit", "-m", "cancellable local check fixture")
    state = tmp_path / "state"
    monkeypatch.setattr(schedule_module, "preflight_check_environment", lambda *a, **kw: None)
    app = Orchestrator(load_project(root), state_root=state, check_temp_root=tmp_path / "checks")
    thread, errors = start_background(app, make_spec(tasks=2))
    try:
        deadline = time.monotonic() + 10
        while not ready.exists() and time.monotonic() < deadline and not errors:
            time.sleep(0.02)
        assert ready.exists(), errors
        run_id = run_id_from(state)
        result = cancel_cli(state, run_id)
        assert result.returncode == 0, result.stderr
        thread.join(10)
        assert not thread.is_alive()
        assert errors == []
        data = snapshot(state, run_id)
        assert data["run"]["state"] == "CANCELLED"
        assert data["checks"][0]["state"] == "SKIPPED"
        assert data["tasks"][0]["state"] == "BLOCKED"
        assert data["tasks"][1]["state"] == "CANCELLED"
        assert app.runtime.turn_count == 1
        assert list((tmp_path / "checks").iterdir()) == []
        pid = int(ready.read_text())
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            kernel.OpenProcess.restype = wintypes.HANDLE
            kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
            kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            handle = kernel.OpenProcess(0x1000, False, pid)
            if handle:
                try:
                    code = wintypes.DWORD()
                    assert kernel.GetExitCodeProcess(handle, ctypes.byref(code))
                    assert code.value != 259  # STILL_ACTIVE
                finally:
                    kernel.CloseHandle(handle)
        else:
            with pytest.raises(ProcessLookupError):
                os.kill(pid, 0)
    finally:
        # The controller owns cleanup; no PID-based arbitrary termination.
        if thread.is_alive() and (state / "ledger.sqlite").exists():
            request_cancel(state, run_id_from(state))
        thread.join(35)
        app.close()


def test_active_cli_never_constructs_ledger(tmp_path, monkeypatch):
    state = tmp_path / "state"
    with ControllerLock(state):
        with Ledger(state / "ledger.sqlite") as ledger:
            run, _ = create_run(ledger)
        monkeypatch.setenv("LAO_STATE_ROOT", str(state))
        def forbidden(*a, **kw):
            raise AssertionError("competing CLI opened a Ledger writer")
        monkeypatch.setattr(cli_module, "Ledger", forbidden)
        assert cli_module._cancel(run["run_id"])["cancel_requested"]


def test_pending_intent_survives_owner_exit_and_backup(tmp_path):
    state = tmp_path / "state"
    with ControllerLock(state), Ledger(state / "ledger.sqlite") as ledger:
        run, _ = create_run(ledger)
        run_id = run["run_id"]
        assert cancel_cli(state, run_id).returncode == 0
        backup = backup_run(ledger, state, run_id)
        assert verify_backup(backup)["ok"]
        assert cancel_requested(backup, run_id)
    # Retrying against the original and a restored DB/intent requires no runtime reattachment.
    for target in (state, backup):
        result = cancel_cli(target, run_id)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["state"] == "CANCELLED"
        assert len(snapshot(target, run_id)["decisions"]) == 1


@pytest.mark.parametrize("boundary", ["before_turn", "dispatch_loss", "dispatch_receipt", "after_terminal", "before_resume", "check_error"])
def test_cancellation_boundaries_do_not_dispatch_or_adopt(boundary, tmp_path, project_factory, monkeypatch):
    root = project_factory()
    state = tmp_path / "state"
    app = Orchestrator(load_project(root), state_root=state, check_temp_root=tmp_path / "checks",
                       fake_scenario="malformed_result" if boundary == "before_resume" else "complete")
    monkeypatch.setattr(schedule_module, "preflight_check_environment", lambda *a, **kw: None)
    if boundary == "before_turn":
        original = app.runtime.start_session
        def start(envelope, profile):
            result = original(envelope, profile)
            request_cancel(state, envelope.run_id)
            return result
        monkeypatch.setattr(app.runtime, "start_session", start)
    elif boundary in {"dispatch_loss", "dispatch_receipt"}:
        original = app.runtime.start_turn
        def start_turn(session, envelope):
            result = original(session, envelope)
            request_cancel(state, envelope.run_id)
            if boundary == "dispatch_loss":
                raise DispatchUncertain("fake lost dispatch receipt")
            return result
        monkeypatch.setattr(app.runtime, "start_turn", start_turn)
    elif boundary == "after_terminal":
        app.turn_boundary_observer = lambda context: request_cancel(state, context.run_id).name
    elif boundary == "before_resume":
        original = schedule_module.validate_result_schema
        def validate(value):
            request_cancel(state, run_id_from(state))
            return original(value)
        monkeypatch.setattr(schedule_module, "validate_result_schema", validate)
    else:
        def failed_cleanup(name, definition, workspace, **kwargs):
            request_cancel(state, run_id_from(state))
            return CheckResult(
                check_name=name, state="ERROR", argv=definition.argv, exit_code=None, stdout="",
                stderr="injected cleanup failure", started_at=utc_now(), ended_at=utc_now(),
                failure_classification_source="controller_runtime", temp_root=str(kwargs["temp_root"]),
                temp_allocation_id="a" * 32,
            )
        monkeypatch.setattr(schedule_module, "run_command_check", failed_cleanup)
    try:
        run_id = app.start(make_spec(tasks=2))
        data = snapshot(state, run_id)
        assert data["run"]["state"] == ("BLOCKED" if boundary in {"before_turn", "dispatch_loss", "check_error"} else "CANCELLED")
        assert data["tasks"][1]["state"] == "CANCELLED"
        assert all(task["state"] != "SUCCEEDED" for task in data["tasks"])
        assert app.runtime.turn_count == (0 if boundary == "before_turn" else 1)
        assert len(data["decisions"]) == 1
    finally:
        app.close()


def test_cancel_before_check_launch_spawns_nothing(tmp_path, project_factory, monkeypatch):
    root = project_factory()
    workspace = verify_module.GitWorkspace(root)
    check = load_project(root).pack.checks.checks["test_check"]
    def forbidden(*a, **kw):
        raise AssertionError("cancelled Check was spawned")
    monkeypatch.setattr(verify_module.subprocess, "Popen", forbidden)
    result = verify_module.run_command_check("test_check", check, workspace,
        temp_root=tmp_path / "checks", cancel_requested=lambda: True)
    assert result.state == "SKIPPED"
    assert list((tmp_path / "checks").iterdir()) == []


def test_marker_directory_link_is_rejected(tmp_path):
    external = tmp_path / "external"
    external.mkdir()
    state = tmp_path / "state"
    state.mkdir()
    link = state / "cancel-requests"
    if os.name == "nt":
        # Junction creation is fixture-only; no admin privilege or external path is needed.
        result = subprocess.run(["powershell", "-NoProfile", "-Command",
            "$ErrorActionPreference='Stop'; New-Item -ItemType Junction -Path $env:LAO_TEST_LINK_PATH -Target $env:LAO_TEST_LINK_TARGET | Out-Null"],
            env={**os.environ, "LAO_TEST_LINK_PATH": str(link), "LAO_TEST_LINK_TARGET": str(external)},
            capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, result.stderr
    else:
        link.symlink_to(external, target_is_directory=True)
    with pytest.raises(ValueError, match="links/reparse"):
        request_cancel(state, "test-run")
    assert list(external.iterdir()) == []


def test_other_run_intent_does_not_cancel_current_run(tmp_path, project_factory, monkeypatch):
    state = tmp_path / "state"
    with ControllerLock(state), Ledger(state / "ledger.sqlite") as ledger:
        old, _ = create_run(ledger)
        request_cancel(state, old["run_id"])
    root = project_factory()
    monkeypatch.setattr(schedule_module, "preflight_check_environment", lambda *a, **kw: None)
    app = Orchestrator(load_project(root), state_root=state, check_temp_root=tmp_path / "checks")
    try:
        new_id = app.start(make_spec())
        assert snapshot(state, new_id)["run"]["state"] == "COMPLETED"
        assert snapshot(state, old["run_id"])["run"]["state"] == "DRAFT"
        assert not cancel_requested(state, new_id)
    finally:
        app.close()
