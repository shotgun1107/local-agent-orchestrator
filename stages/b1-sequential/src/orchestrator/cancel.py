"""Durable cancellation intent; only the controller holding the lock writes Ledger."""
from __future__ import annotations

import os
from pathlib import Path
import queue
import stat
import threading
import time
from typing import Callable

from .contract import (
    AttemptState, FailureKind, InterruptOutcome, InterruptState, RunState,
    RuntimeFailure, RuntimeOutcome, SessionState, TaskState, TerminalStatus,
    UsageSnapshot, UsageStatus, sha256_bytes,
)
from .ledger import Ledger
from .runtime import RuntimePort, TurnHandle

TERMINAL_RUNS = {RunState.COMPLETED, RunState.FAILED, RunState.CANCELLED}
POLL_SECONDS = 0.05


def _request_path(root: Path, run_id: str) -> Path:
    # Never interpret an identifier as a filesystem path or a command.
    path = Path(os.path.abspath(root)) / "cancel-requests" / (sha256_bytes(run_id.encode()) + ".request")
    for part in reversed((path, *path.parents)):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("cancellation request path cannot contain links/reparse points")
        if part == path and (not stat.S_ISREG(info.st_mode) or info.st_size != 0):
            raise ValueError("cancellation intent must be an empty regular file")
    return path


def cancel_requested(root: Path, run_id: str) -> bool:
    return _request_path(root, run_id).is_file()


def request_cancel(root: Path, run_id: str) -> Path:
    """Publish an idempotent, payload-free marker. Never remove/overwrite old intent."""
    path = _request_path(root, run_id)
    path.parent.mkdir(exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        _request_path(root, run_id)
    return path


def await_cancellable_terminal(
    runtime: RuntimePort, turn: TurnHandle, deadline: float,
    requested: Callable[[], bool], grace_seconds: float,
) -> RuntimeOutcome:
    """Bound cancellation even if an adapter's wait or interrupt call gets stuck.

    Background calls never receive a Ledger. UNKNOWN is not proof that the
    runtime stopped; its Attempt must be quarantined and never auto-retried.
    """
    results: queue.Queue[RuntimeOutcome | Exception] = queue.Queue(maxsize=1)
    interrupts: queue.Queue[InterruptOutcome] = queue.Queue(maxsize=1)

    def wait() -> None:
        try:
            results.put(runtime.await_terminal(turn, deadline))
        except Exception as exc:
            results.put(exc)

    def interrupt() -> None:
        try:
            interrupts.put(runtime.interrupt(turn))
        except Exception:
            interrupts.put(InterruptOutcome(state=InterruptState.FAILED))

    def unknown(evidence: dict) -> RuntimeOutcome:
        return RuntimeOutcome(
            terminal_status=TerminalStatus.UNKNOWN,
            terminal_evidence={"cancel_requested": True, **evidence},
            failure=RuntimeFailure(
                kind=FailureKind.TERMINAL_UNKNOWN, retryable=False,
                redacted_message="terminal not proven within user cancellation grace",
                source_exception_type="CancellationTerminalUnknown",
            ),
            usage_snapshot=UsageSnapshot(status=UsageStatus.UNKNOWN),
        )

    threading.Thread(target=wait, name="lao-terminal-wait", daemon=True).start()
    cancel_deadline = None
    while True:
        if cancel_deadline is None and requested():
            cancel_deadline = time.monotonic() + grace_seconds
            threading.Thread(target=interrupt, name="lao-cancel-interrupt", daemon=True).start()
        try:
            outcome = results.get(timeout=(
                POLL_SECONDS if cancel_deadline is None
                else min(POLL_SECONDS, max(0.0, cancel_deadline - time.monotonic()))
            ))
        except queue.Empty:
            if cancel_deadline is None or time.monotonic() < cancel_deadline:
                continue
            try:
                interrupt_state = interrupts.get_nowait().state
            except queue.Empty:
                interrupt_state = InterruptState.REQUESTED
            return unknown({"interrupt_state": interrupt_state})
        if isinstance(outcome, Exception):
            if cancel_deadline is not None or requested():
                return unknown({"wait_error_type": type(outcome).__name__})
            raise outcome
        return outcome


def apply_cancel(ledger: Ledger, run_id: str) -> dict:
    """Caller MUST own ControllerLock. No runtime reattachment or invented terminal."""
    run = ledger.get("run", run_id)
    if run["state"] in TERMINAL_RUNS:
        return {"run_id": run_id, "state": run["state"], "changed": False, "cancel_requested": False}
    decision_id = "cancel_" + sha256_bytes(run_id.encode())[:32]
    recorded = ledger.connection.execute(
        "SELECT 1 FROM decisions WHERE decision_id=?", (decision_id,),
    ).fetchone() is not None
    unconfirmed_check = False
    for attempt in ledger.nonterminal_attempts(run_id):
        session = ledger.get("session", attempt["session_id"]) if attempt["session_id"] else None
        if session and session["state"] in {SessionState.STARTING, SessionState.RUNNING, SessionState.INTERRUPTING}:
            session = ledger.update_session_terminal(
                session["session_id"], SessionState.QUARANTINED,
                {"cancel_requested": True, "terminal_unconfirmed": True}, "unknown", None,
            )
        if attempt["state"] == AttemptState.DISPATCHING:
            ledger.finish_attempt(
                attempt["attempt_id"], AttemptState.DISPATCH_UNCERTAIN, TaskState.BLOCKED,
                FailureKind.DISPATCH_UNCERTAIN, {"cancel_requested": True},
            )
        elif attempt["state"] == AttemptState.RUNNING:
            proven = session is not None and session["state"] in {
                SessionState.COMPLETED, SessionState.CANCELLED, SessionState.FAILED, SessionState.TIMED_OUT,
            }
            ledger.finish_attempt(
                attempt["attempt_id"], AttemptState.CANCELLED if proven else AttemptState.QUARANTINED,
                TaskState.CANCELLED if proven else TaskState.BLOCKED,
                None if proven else FailureKind.TERMINAL_UNKNOWN, {"cancel_requested": True},
            )
        elif attempt["state"] in {AttemptState.REPORTED, AttemptState.VERIFYING}:
            for check in ledger.connection.execute(
                "SELECT * FROM checks WHERE attempt_id=? AND state IN ('PENDING','RUNNING')",
                (attempt["attempt_id"],),
            ).fetchall():
                unconfirmed_check = True
                if check["state"] == "PENDING":
                    ledger.start_check(check["check_id"])
                ledger.finish_check(check["check_id"], {
                    "state": "ERROR", "exit_code": None, "attempt_id": attempt["attempt_id"],
                    "check_name": check["check_name"], "input_fingerprint": attempt["input_fingerprint"],
                })
            ledger.finish_attempt(
                attempt["attempt_id"], AttemptState.BLOCKED, TaskState.BLOCKED, None,
                {"cancelled_during_verification": True},
            )
    for task in ledger.list_tasks(run_id):
        if task["state"] in {TaskState.PENDING, TaskState.READY}:
            ledger.transition("task", task["task_id"], task["version"], TaskState.CANCELLED, "task_cancelled", {})
    uncertain = unconfirmed_check or ledger.connection.execute(
        """SELECT 1 FROM attempts a JOIN tasks t ON t.task_id=a.task_id
           WHERE t.run_id=? AND a.state IN ('QUARANTINED','DISPATCH_UNCERTAIN') LIMIT 1""", (run_id,),
    ).fetchone() is not None
    uncertain = uncertain or ledger.connection.execute(
        """SELECT 1 FROM checks c JOIN attempts a ON a.attempt_id=c.attempt_id
           JOIN tasks t ON t.task_id=a.task_id
           WHERE t.run_id=? AND a.state='BLOCKED' AND c.state='ERROR' LIMIT 1""", (run_id,),
    ).fetchone() is not None
    # The frozen state machine deliberately has no BLOCKED/VERIFYING -> CANCELLED.
    # Do not resurrect a blocked Run just to force it through that transition.
    target = RunState.BLOCKED if uncertain or run["state"] in {RunState.BLOCKED, RunState.VERIFYING} else RunState.CANCELLED
    if not recorded:
        ledger.record_decision({
            "decision_id": decision_id, "run_id": run_id, "kind": "cancel", "actor": "user",
            "outcome": "recorded", "evidence": {"terminal_unconfirmed": uncertain},
        })
    if run["state"] != target:
        ledger.transition("run", run_id, run["version"], target, "run_cancelled" if target == RunState.CANCELLED else "run_cancel_blocked", {})
    return {"run_id": run_id, "state": target, "changed": not recorded or run["state"] != target, "cancel_requested": True}
