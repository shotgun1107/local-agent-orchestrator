from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from orchestrator.contract import AttemptState, CheckState, RunState, SessionState, TaskState, canonical_json
from orchestrator.ledger import (
    ATTEMPT_TRANSITIONS,
    CHECK_TRANSITIONS,
    MIGRATION_1_CHECKSUM,
    RUN_TRANSITIONS,
    SESSION_TRANSITIONS,
    TASK_TRANSITIONS,
    IntegrityViolation,
    Ledger,
    StateConflict,
)
from tests.conftest import make_spec


def create_run(ledger: Ledger):
    run = ledger.create_run({
        "project_id": "ledger-test",
        "request_text": "test",
        "request_source": "test",
        "completion_criteria": [{"id": "RC1"}],
        "auth_method": "none",
        "policy_name": "b1_safe",
        "project_pack_sha256": "a" * 64,
        "core_version": "0.1.0",
        "max_turns": 8,
        "timeout_seconds": 60,
    })
    tasks = ledger.create_tasks(run["run_id"], make_spec().tasks)
    return run, tasks[0]


def test_schema_is_reproducible_and_has_ten_tables(tmp_path: Path) -> None:
    with Ledger(tmp_path / "ledger.sqlite") as ledger:
        tables = {row[0] for row in ledger.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        expected = {"schema_migrations", "runs", "tasks", "task_dependencies", "attempts", "sessions", "artifacts", "checks", "decisions", "events"}
        assert expected.issubset(tables)
        assert ledger.connection.execute("SELECT checksum FROM schema_migrations WHERE version=1").fetchone()[0] == MIGRATION_1_CHECKSUM
        assert ledger.foreign_key_violations() == []


def test_state_machine_tables_match_frozen_contract() -> None:
    assert RUN_TRANSITIONS == {
        RunState.DRAFT: {RunState.READY, RunState.CANCELLED},
        RunState.READY: {RunState.RUNNING, RunState.CANCELLED, RunState.BLOCKED},
        RunState.RUNNING: {RunState.VERIFYING, RunState.CANCELLED, RunState.BLOCKED, RunState.FAILED},
        RunState.VERIFYING: {RunState.COMPLETED, RunState.BLOCKED, RunState.FAILED},
        RunState.BLOCKED: {RunState.READY, RunState.RUNNING},
    }
    assert TASK_TRANSITIONS == {
        TaskState.PENDING: {TaskState.READY, TaskState.SUPERSEDED, TaskState.CANCELLED},
        TaskState.READY: {TaskState.RUNNING, TaskState.SUPERSEDED, TaskState.CANCELLED},
        TaskState.RUNNING: {TaskState.REPORTED, TaskState.RETRYABLE_FAILED, TaskState.BLOCKED, TaskState.FAILED, TaskState.CANCELLED},
        TaskState.REPORTED: {TaskState.VERIFYING, TaskState.BLOCKED, TaskState.FAILED},
        TaskState.VERIFYING: {TaskState.SUCCEEDED, TaskState.RETRYABLE_FAILED, TaskState.BLOCKED, TaskState.FAILED},
        TaskState.RETRYABLE_FAILED: {TaskState.READY},
    }
    assert ATTEMPT_TRANSITIONS == {
        AttemptState.CREATED: {AttemptState.DISPATCHING},
        AttemptState.DISPATCHING: {AttemptState.RUNNING, AttemptState.DISPATCH_UNCERTAIN},
        AttemptState.RUNNING: {AttemptState.REPORTED, AttemptState.RETRYABLE_FAILED, AttemptState.FAILED, AttemptState.BLOCKED, AttemptState.CANCELLED, AttemptState.QUARANTINED},
        AttemptState.REPORTED: {AttemptState.VERIFYING, AttemptState.BLOCKED, AttemptState.FAILED},
        AttemptState.VERIFYING: {AttemptState.SUCCEEDED, AttemptState.RETRYABLE_FAILED, AttemptState.FAILED, AttemptState.BLOCKED},
    }
    assert SESSION_TRANSITIONS == {
        SessionState.STARTING: {SessionState.RUNNING, SessionState.UNKNOWN, SessionState.QUARANTINED},
        SessionState.RUNNING: {SessionState.COMPLETED, SessionState.FAILED, SessionState.TIMED_OUT, SessionState.CANCELLED, SessionState.UNKNOWN, SessionState.QUARANTINED, SessionState.INTERRUPTING},
        SessionState.INTERRUPTING: {SessionState.CANCELLED, SessionState.UNKNOWN, SessionState.QUARANTINED},
    }
    assert CHECK_TRANSITIONS == {
        CheckState.PENDING: {CheckState.RUNNING},
        CheckState.RUNNING: {CheckState.PASSED, CheckState.FAILED, CheckState.ERROR, CheckState.SKIPPED},
    }


def test_transition_updates_state_and_event_atomically(tmp_path: Path) -> None:
    with Ledger(tmp_path / "ledger.sqlite") as ledger:
        run, _ = create_run(ledger)
        updated = ledger.transition("run", run["run_id"], 0, RunState.READY, "ready", {"why": "valid"})
        assert updated["state"] == "READY"
        assert updated["version"] == 1
        event = ledger.connection.execute("SELECT * FROM events WHERE event_type='ready'").fetchone()
        assert event is not None
        with pytest.raises(StateConflict):
            ledger.transition("run", run["run_id"], 0, RunState.RUNNING, "stale", {})
        assert ledger.get("run", run["run_id"])["state"] == "READY"


def test_attempt_terminal_clears_active_attempt_in_same_transaction(tmp_path: Path) -> None:
    with Ledger(tmp_path / "ledger.sqlite") as ledger:
        _, task = create_run(ledger)
        task = ledger.transition("task", task["task_id"], 0, TaskState.READY, "ready", {})
        attempt = ledger.begin_attempt(task["task_id"], 1, "initial", "{}", "f" * 64)
        assert ledger.get("task", task["task_id"])["active_attempt_id"] == attempt["attempt_id"]
        ledger.finish_attempt(
            attempt["attempt_id"], AttemptState.DISPATCH_UNCERTAIN, TaskState.BLOCKED,
            "dispatch_uncertain", {},
        )
        task = ledger.get("task", task["task_id"])
        assert task["active_attempt_id"] is None
        assert task["state"] == "BLOCKED"
        assert ledger.foreign_key_violations() == []


def test_only_one_active_attempt_is_permitted(tmp_path: Path) -> None:
    spec = make_spec(tasks=2)
    with Ledger(tmp_path / "ledger.sqlite") as ledger:
        run = ledger.create_run({
            "project_id": "ledger-test", "request_text": "test", "request_source": "test",
            "completion_criteria": [{"id": "RC1"}], "auth_method": "none", "policy_name": "b1_safe",
            "project_pack_sha256": "a" * 64, "core_version": "0.1.0", "max_turns": 8, "timeout_seconds": 60,
        })
        first, second = ledger.create_tasks(run["run_id"], spec.tasks)
        first = ledger.transition("task", first["task_id"], 0, TaskState.READY, "ready1", {})
        second = ledger.transition("task", second["task_id"], 0, TaskState.READY, "ready2", {})
        ledger.begin_attempt(first["task_id"], 1, "initial", "{}", "a" * 64)
        with pytest.raises(StateConflict, match="only one active"):
            ledger.begin_attempt(second["task_id"], 1, "initial", "{}", "b" * 64)


def test_result_idempotency_accepts_same_and_rejects_conflict(tmp_path: Path) -> None:
    with Ledger(tmp_path / "ledger.sqlite") as ledger:
        _, task = create_run(ledger)
        task = ledger.transition("task", task["task_id"], 0, TaskState.READY, "ready", {})
        attempt = ledger.begin_attempt(task["task_id"], 1, "initial", "{}", "a" * 64)
        first = ledger.record_result_event("fake", "turn-1", "1" * 64, attempt["attempt_id"])
        assert ledger.record_result_event("fake", "turn-1", "1" * 64, attempt["attempt_id"]) == first
        with pytest.raises(IntegrityViolation):
            ledger.record_result_event("fake", "turn-1", "2" * 64, attempt["attempt_id"])


def test_migration_checksum_mismatch_stops_startup(tmp_path: Path) -> None:
    database = tmp_path / "ledger.sqlite"
    with Ledger(database) as ledger:
        ledger.connection.execute("UPDATE schema_migrations SET checksum='bad' WHERE version=1")
    ledger = Ledger(database)
    with pytest.raises(IntegrityViolation):
        ledger.apply_migrations()
    ledger.close()


def test_future_schema_stops_startup(tmp_path: Path) -> None:
    database = tmp_path / "ledger.sqlite"
    with Ledger(database) as ledger:
        ledger.connection.execute(
            "INSERT INTO schema_migrations(version, applied_at, checksum) VALUES(2, 'now', 'future')"
        )
    ledger = Ledger(database)
    with pytest.raises(IntegrityViolation):
        ledger.apply_migrations()
    ledger.close()


def test_failed_migration_rolls_back_ddl_and_history(tmp_path: Path, monkeypatch) -> None:
    import hashlib
    import orchestrator.ledger as ledger_module

    broken = "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT, checksum TEXT); CREATE TABLE partial(value TEXT); THIS IS INVALID"
    monkeypatch.setattr(ledger_module, "MIGRATION_1_UP", broken)
    monkeypatch.setattr(ledger_module, "MIGRATION_1_CHECKSUM", hashlib.sha256(broken.encode("utf-8")).hexdigest())
    ledger = Ledger(tmp_path / "ledger.sqlite")
    with pytest.raises(sqlite3.Error):
        ledger.apply_migrations()
    tables = {row[0] for row in ledger.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "partial" not in tables
    assert "schema_migrations" not in tables
    ledger.close()


def test_usage_delta_decrease_becomes_unknown(tmp_path: Path) -> None:
    with Ledger(tmp_path / "ledger.sqlite") as ledger:
        _, task = create_run(ledger)
        task = ledger.transition("task", task["task_id"], 0, TaskState.READY, "ready", {})
        attempt = ledger.begin_attempt(task["task_id"], 1, "initial", "{}", "a" * 64)
        session = ledger.create_session(attempt["attempt_id"], "fake", "1", "s1", "fake", ".", "read_only", {}, "unknown")
        ledger.append_usage_snapshot(session["session_id"], "turn1", {"status": "measured", "total": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}})
        ledger.append_usage_snapshot(session["session_id"], "turn2", {"status": "measured", "total": {"input_tokens": 9, "output_tokens": 6, "total_tokens": 15}})
        usage = __import__("json").loads(ledger.get("session", session["session_id"])["usage_json"])
        assert usage["snapshots"][1]["delta"] == "unknown"


def test_check_state_changes_each_have_an_event(tmp_path: Path) -> None:
    with Ledger(tmp_path / "ledger.sqlite") as ledger:
        _, task = create_run(ledger)
        task = ledger.transition("task", task["task_id"], 0, TaskState.READY, "ready", {})
        attempt = ledger.begin_attempt(task["task_id"], 1, "initial", "{}", "a" * 64)
        check = ledger.create_check({
            "task_id": task["task_id"], "attempt_id": attempt["attempt_id"],
            "check_name": "unit", "argv": ["python", "-m", "pytest"],
        })
        assert check["state"] == "PENDING"
        assert ledger.start_check(check["check_id"])["state"] == "RUNNING"
        finished = ledger.finish_check(check["check_id"], {
            "attempt_id": attempt["attempt_id"], "check_name": "unit",
            "input_fingerprint": "a" * 64, "state": "PASSED", "exit_code": 0,
        })
        assert finished["state"] == "PASSED"
        events = ledger.connection.execute(
            "SELECT event_type FROM events WHERE aggregate_id=? ORDER BY seq", (check["check_id"],)
        ).fetchall()
        assert [row[0] for row in events] == ["check_created", "check_running", "check_finished"]
