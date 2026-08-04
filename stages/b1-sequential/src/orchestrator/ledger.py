"""SQLite ledger and the only state-transition implementation for B1."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .contract import (
    AttemptState,
    CheckState,
    RunState,
    SessionState,
    TaskState,
    canonical_json,
    new_id,
    utc_now,
)


class LedgerError(RuntimeError):
    pass


class StateConflict(LedgerError):
    pass


class IntegrityViolation(LedgerError):
    pass


RUN_TRANSITIONS = {
    RunState.DRAFT: {RunState.READY, RunState.CANCELLED},
    RunState.READY: {RunState.RUNNING, RunState.CANCELLED, RunState.BLOCKED},
    RunState.RUNNING: {RunState.VERIFYING, RunState.CANCELLED, RunState.BLOCKED, RunState.FAILED},
    RunState.VERIFYING: {RunState.COMPLETED, RunState.BLOCKED, RunState.FAILED},
    RunState.BLOCKED: {RunState.READY, RunState.RUNNING},
}
TASK_TRANSITIONS = {
    TaskState.PENDING: {TaskState.READY, TaskState.SUPERSEDED, TaskState.CANCELLED},
    TaskState.READY: {TaskState.RUNNING, TaskState.SUPERSEDED, TaskState.CANCELLED},
    TaskState.RUNNING: {
        TaskState.REPORTED,
        TaskState.RETRYABLE_FAILED,
        TaskState.BLOCKED,
        TaskState.FAILED,
        TaskState.CANCELLED,
    },
    TaskState.REPORTED: {TaskState.VERIFYING, TaskState.BLOCKED, TaskState.FAILED},
    TaskState.VERIFYING: {
        TaskState.SUCCEEDED,
        TaskState.RETRYABLE_FAILED,
        TaskState.BLOCKED,
        TaskState.FAILED,
    },
    TaskState.RETRYABLE_FAILED: {TaskState.READY},
}
ATTEMPT_TRANSITIONS = {
    AttemptState.CREATED: {AttemptState.DISPATCHING},
    AttemptState.DISPATCHING: {AttemptState.RUNNING, AttemptState.DISPATCH_UNCERTAIN},
    AttemptState.RUNNING: {
        AttemptState.REPORTED,
        AttemptState.RETRYABLE_FAILED,
        AttemptState.FAILED,
        AttemptState.BLOCKED,
        AttemptState.CANCELLED,
        AttemptState.QUARANTINED,
    },
    AttemptState.REPORTED: {AttemptState.VERIFYING, AttemptState.BLOCKED, AttemptState.FAILED},
    AttemptState.VERIFYING: {
        AttemptState.SUCCEEDED,
        AttemptState.RETRYABLE_FAILED,
        AttemptState.FAILED,
        AttemptState.BLOCKED,
    },
}
SESSION_TRANSITIONS = {
    SessionState.STARTING: {SessionState.RUNNING, SessionState.UNKNOWN, SessionState.QUARANTINED},
    SessionState.RUNNING: {
        SessionState.COMPLETED,
        SessionState.FAILED,
        SessionState.TIMED_OUT,
        SessionState.CANCELLED,
        SessionState.UNKNOWN,
        SessionState.QUARANTINED,
        SessionState.INTERRUPTING,
    },
    SessionState.INTERRUPTING: {
        SessionState.CANCELLED,
        SessionState.UNKNOWN,
        SessionState.QUARANTINED,
    },
}
CHECK_TRANSITIONS = {
    CheckState.PENDING: {CheckState.RUNNING},
    CheckState.RUNNING: {CheckState.PASSED, CheckState.FAILED, CheckState.ERROR, CheckState.SKIPPED},
}

TRANSITIONS: dict[str, Mapping[Any, set[Any]]] = {
    "run": RUN_TRANSITIONS,
    "task": TASK_TRANSITIONS,
    "attempt": ATTEMPT_TRANSITIONS,
    "session": SESSION_TRANSITIONS,
    "check": CHECK_TRANSITIONS,
}
TABLES = {
    "run": ("runs", "run_id"),
    "task": ("tasks", "task_id"),
    "attempt": ("attempts", "attempt_id"),
    "session": ("sessions", "session_id"),
    "check": ("checks", "check_id"),
}

MIGRATION_1_UP = """
CREATE TABLE schema_migrations (
  version INTEGER PRIMARY KEY,
  applied_at TEXT NOT NULL,
  checksum TEXT NOT NULL
);
CREATE TABLE runs (
  run_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  request_text TEXT NOT NULL,
  request_source TEXT NOT NULL,
  received_at TEXT NOT NULL,
  requirements_version INTEGER NOT NULL CHECK (requirements_version >= 1),
  completion_criteria_json TEXT NOT NULL,
  constraints_json TEXT NOT NULL,
  assumptions_json TEXT NOT NULL,
  unresolved_json TEXT NOT NULL,
  auth_method TEXT NOT NULL CHECK(auth_method IN ('none', 'chatgpt')),
  policy_name TEXT NOT NULL,
  project_pack_version INTEGER NOT NULL,
  project_pack_sha256 TEXT NOT NULL,
  core_version TEXT NOT NULL,
  state TEXT NOT NULL,
  max_turns INTEGER NOT NULL,
  turns_used INTEGER NOT NULL DEFAULT 0,
  timeout_seconds INTEGER NOT NULL,
  started_at TEXT,
  ended_at TEXT,
  version INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE tasks (
  task_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES runs(run_id),
  external_key TEXT NOT NULL,
  ordinal INTEGER NOT NULL,
  goal TEXT NOT NULL,
  completion_criteria_json TEXT NOT NULL,
  read_scope_json TEXT NOT NULL,
  write_scope_json TEXT NOT NULL,
  capability_profile TEXT NOT NULL,
  workspace_mode TEXT NOT NULL CHECK(workspace_mode IN ('read_only', 'shared_serial_write')),
  check_names_json TEXT NOT NULL,
  approval TEXT NOT NULL CHECK(approval = 'none'),
  requirements_version INTEGER NOT NULL,
  state TEXT NOT NULL,
  active_attempt_id TEXT REFERENCES attempts(attempt_id),
  version INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(run_id, external_key),
  UNIQUE(run_id, ordinal)
);
CREATE TABLE task_dependencies (
  task_id TEXT NOT NULL REFERENCES tasks(task_id),
  depends_on_task_id TEXT NOT NULL REFERENCES tasks(task_id),
  PRIMARY KEY(task_id, depends_on_task_id),
  CHECK(task_id <> depends_on_task_id)
);
CREATE TABLE attempts (
  attempt_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL REFERENCES tasks(task_id),
  attempt_no INTEGER NOT NULL CHECK (attempt_no >= 1),
  start_reason TEXT NOT NULL CHECK(start_reason IN (
    'initial', 'retry_transient', 'retry_stale', 'retry_check', 'manual_recovery'
  )),
  dispatch_token TEXT NOT NULL UNIQUE,
  task_contract_json TEXT NOT NULL,
  input_fingerprint TEXT NOT NULL,
  baseline_artifact_id TEXT REFERENCES artifacts(artifact_id),
  session_id TEXT REFERENCES sessions(session_id),
  state TEXT NOT NULL,
  result_claim TEXT,
  failure_kind TEXT CHECK(failure_kind IS NULL OR failure_kind IN (
    'transient_runtime', 'runtime_unknown', 'malformed_result', 'check_failed',
    'stale_input', 'scope_violation', 'timeout', 'dispatch_uncertain',
    'terminal_unknown', 'artifact_corrupt', 'internal'
  )),
  resume_count INTEGER NOT NULL DEFAULT 0,
  started_at TEXT,
  ended_at TEXT,
  version INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(task_id, attempt_no)
);
CREATE TABLE sessions (
  session_id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL UNIQUE REFERENCES attempts(attempt_id),
  runtime_name TEXT NOT NULL,
  runtime_version TEXT NOT NULL,
  runtime_session_id TEXT UNIQUE,
  active_runtime_turn_id TEXT UNIQUE,
  runtime_profile TEXT NOT NULL,
  cwd TEXT NOT NULL,
  sandbox TEXT NOT NULL CHECK(sandbox IN ('read_only', 'workspace_write')),
  capabilities_json TEXT NOT NULL,
  state TEXT NOT NULL,
  interrupt_state TEXT NOT NULL CHECK(interrupt_state IN (
    'not_requested', 'requested', 'confirmed', 'failed', 'unsupported'
  )),
  last_runtime_event_at TEXT,
  usage_status TEXT NOT NULL CHECK(usage_status IN ('measured', 'unknown', 'unsupported')),
  usage_json TEXT,
  terminal_evidence_json TEXT,
  started_at TEXT,
  ended_at TEXT,
  version INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE artifacts (
  artifact_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES runs(run_id),
  task_id TEXT REFERENCES tasks(task_id),
  attempt_id TEXT REFERENCES attempts(attempt_id),
  kind TEXT NOT NULL CHECK(kind IN (
    'request', 'run_spec', 'task_envelope', 'fingerprint', 'workspace_baseline',
    'result_envelope', 'runtime_observation', 'terminal_evidence', 'check_stdout',
    'check_stderr', 'check_result', 'report', 'project_file', 'late_result'
  )),
  relative_path TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  size_bytes INTEGER NOT NULL CHECK(size_bytes >= 0),
  media_type TEXT,
  sensitivity TEXT NOT NULL CHECK(sensitivity IN ('public', 'project_local', 'sensitive_redacted')),
  retention TEXT NOT NULL CHECK(retention IN ('run', 'benchmark', 'manual')),
  producer TEXT NOT NULL CHECK(producer IN ('user', 'controller', 'runtime', 'verifier')),
  created_at TEXT NOT NULL,
  UNIQUE(run_id, relative_path)
);
CREATE TABLE checks (
  check_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL REFERENCES tasks(task_id),
  attempt_id TEXT NOT NULL REFERENCES attempts(attempt_id),
  requirements_version INTEGER NOT NULL,
  check_name TEXT NOT NULL,
  check_kind TEXT NOT NULL CHECK(check_kind = 'command'),
  command_argv_json TEXT,
  state TEXT NOT NULL,
  exit_code INTEGER,
  stdout_artifact_id TEXT REFERENCES artifacts(artifact_id),
  stderr_artifact_id TEXT REFERENCES artifacts(artifact_id),
  started_at TEXT,
  ended_at TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(attempt_id, check_name)
);
CREATE TABLE decisions (
  decision_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES runs(run_id),
  task_id TEXT REFERENCES tasks(task_id),
  attempt_id TEXT REFERENCES attempts(attempt_id),
  kind TEXT NOT NULL CHECK(kind IN ('unblock', 'recovery', 'budget_change', 'cancel')),
  actor TEXT NOT NULL CHECK(actor IN ('user', 'controller')),
  outcome TEXT NOT NULL CHECK(outcome IN ('approved', 'rejected', 'recorded')),
  scope_json TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE events (
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT NOT NULL UNIQUE,
  aggregate_type TEXT NOT NULL CHECK(aggregate_type IN ('run', 'task', 'attempt', 'session', 'check')),
  aggregate_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  schema_version INTEGER NOT NULL,
  payload_json TEXT NOT NULL,
  causation_id TEXT,
  idempotency_key TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_tasks_run_state ON tasks(run_id, state, ordinal);
CREATE INDEX idx_attempts_task ON attempts(task_id, attempt_no);
CREATE INDEX idx_artifacts_attempt ON artifacts(attempt_id, kind);
CREATE INDEX idx_checks_attempt ON checks(attempt_id, state);
CREATE INDEX idx_events_aggregate ON events(aggregate_type, aggregate_id, seq);
""".strip()
MIGRATION_1_CHECKSUM = hashlib.sha256(MIGRATION_1_UP.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def _split_sql(script: str) -> Iterable[str]:
    for statement in script.split(";"):
        statement = statement.strip()
        if statement:
            yield statement


class Ledger:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, isolation_level=None, timeout=5)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute("PRAGMA synchronous = FULL")
        self.connection.execute("PRAGMA busy_timeout = 5000")

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "Ledger":
        self.apply_migrations()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _begin(self) -> None:
        self.connection.execute("BEGIN IMMEDIATE")

    def apply_migrations(self) -> None:
        table = self.connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
        ).fetchone()
        if table is None:
            self._begin()
            try:
                for statement in _split_sql(MIGRATION_1_UP):
                    self.connection.execute(statement)
                self.connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at, checksum) VALUES(1, ?, ?)",
                    (utc_now(), MIGRATION_1_CHECKSUM),
                )
                self.connection.commit()
            except Exception:
                self.connection.rollback()
                raise
        self.verify_migrations()

    def verify_migrations(self) -> None:
        rows = self.connection.execute(
            "SELECT version, checksum FROM schema_migrations ORDER BY version"
        ).fetchall()
        if [(row["version"], row["checksum"]) for row in rows] != [(1, MIGRATION_1_CHECKSUM)]:
            raise IntegrityViolation("migration history or checksum does not match schema version 1")

    def foreign_key_violations(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.connection.execute("PRAGMA foreign_key_check").fetchall()]

    def quick_check(self) -> str:
        return str(self.connection.execute("PRAGMA quick_check").fetchone()[0])

    def _insert_event(
        self,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: Mapping[str, Any],
        idempotency_key: str,
        causation_id: str | None = None,
    ) -> str:
        payload_json = canonical_json(payload)
        existing = self.connection.execute(
            "SELECT event_id, payload_json FROM events WHERE idempotency_key=?", (idempotency_key,)
        ).fetchone()
        if existing:
            if existing["payload_json"] != payload_json:
                raise IntegrityViolation(f"conflicting idempotency key: {idempotency_key}")
            return str(existing["event_id"])
        event_id = new_id("event")
        self.connection.execute(
            """INSERT INTO events(
                event_id, aggregate_type, aggregate_id, event_type, schema_version,
                payload_json, causation_id, idempotency_key, created_at
            ) VALUES(?, ?, ?, ?, 1, ?, ?, ?, ?)""",
            (
                event_id,
                aggregate_type,
                aggregate_id,
                event_type,
                payload_json,
                causation_id,
                idempotency_key,
                utc_now(),
            ),
        )
        return event_id

    def create_run(self, values: Mapping[str, Any]) -> dict[str, Any]:
        run_id = str(values.get("run_id") or new_id("run"))
        now = utc_now()
        self._begin()
        try:
            self.connection.execute(
                """INSERT INTO runs(
                    run_id, project_id, request_text, request_source, received_at,
                    requirements_version, completion_criteria_json, constraints_json,
                    assumptions_json, unresolved_json, auth_method, policy_name,
                    project_pack_version, project_pack_sha256, core_version, state,
                    max_turns, timeout_seconds, created_at, updated_at
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id,
                    values["project_id"],
                    values["request_text"],
                    values["request_source"],
                    now,
                    values.get("requirements_version", 1),
                    canonical_json(values["completion_criteria"]),
                    canonical_json(values.get("constraints", [])),
                    canonical_json(values.get("assumptions", [])),
                    canonical_json(values.get("unresolved", [])),
                    values["auth_method"],
                    values["policy_name"],
                    values.get("project_pack_version", 1),
                    values["project_pack_sha256"],
                    values["core_version"],
                    RunState.DRAFT,
                    values["max_turns"],
                    values["timeout_seconds"],
                    now,
                    now,
                ),
            )
            self._insert_event("run", run_id, "run_created", {"state": RunState.DRAFT}, f"create:run:{run_id}")
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        return self.get("run", run_id)

    def create_tasks(self, run_id: str, task_specs: Iterable[Any]) -> list[dict[str, Any]]:
        specs = list(task_specs)
        ids = {task.key: new_id("task") for task in specs}
        now = utc_now()
        self._begin()
        try:
            for ordinal, task in enumerate(specs):
                task_id = ids[task.key]
                self.connection.execute(
                    """INSERT INTO tasks(
                        task_id, run_id, external_key, ordinal, goal, completion_criteria_json,
                        read_scope_json, write_scope_json, capability_profile, workspace_mode,
                        check_names_json, approval, requirements_version, state, created_at, updated_at
                    ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)""",
                    (
                        task_id,
                        run_id,
                        task.key,
                        ordinal,
                        task.goal,
                        canonical_json(task.completion_criteria),
                        canonical_json(task.read_scope),
                        canonical_json(task.write_scope),
                        task.capability_profile,
                        str(task.workspace_mode),
                        canonical_json(task.check_names),
                        task.approval,
                        TaskState.PENDING,
                        now,
                        now,
                    ),
                )
                self._insert_event(
                    "task", task_id, "task_created", {"state": TaskState.PENDING, "key": task.key}, f"create:task:{task_id}"
                )
            for task in specs:
                for dependency in task.depends_on:
                    self.connection.execute(
                        "INSERT INTO task_dependencies(task_id, depends_on_task_id) VALUES(?, ?)",
                        (ids[task.key], ids[dependency]),
                    )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        return [self.get("task", ids[task.key]) for task in specs]

    def get(self, entity_type: str, entity_id: str) -> dict[str, Any]:
        table, id_column = TABLES[entity_type]
        row = self.connection.execute(
            f"SELECT * FROM {table} WHERE {id_column}=?", (entity_id,)
        ).fetchone()
        if row is None:
            raise LedgerError(f"{entity_type} not found: {entity_id}")
        return dict(row)

    def transition(
        self,
        entity_type: str,
        entity_id: str,
        expected_version: int,
        target_state: str,
        event_type: str,
        payload: Mapping[str, Any] | None = None,
        *,
        decision_id: str | None = None,
    ) -> dict[str, Any]:
        table, id_column = TABLES[entity_type]
        payload = dict(payload or {})
        self._begin()
        try:
            row = self.connection.execute(
                f"SELECT * FROM {table} WHERE {id_column}=?", (entity_id,)
            ).fetchone()
            if row is None:
                raise LedgerError(f"{entity_type} not found: {entity_id}")
            current = row["state"]
            current_version = int(row["version"])
            if current == target_state and current_version == expected_version + 1:
                key_pattern = f"transition:{entity_type}:{entity_id}:%:{target_state}:{expected_version}"
                existing = self.connection.execute(
                    "SELECT payload_json FROM events WHERE idempotency_key LIKE ?", (key_pattern,)
                ).fetchone()
                if existing and existing["payload_json"] == canonical_json(payload):
                    self.connection.commit()
                    return dict(row)
            if current_version != expected_version:
                raise StateConflict(f"version conflict for {entity_type} {entity_id}")
            allowed = TRANSITIONS[entity_type].get(current, set())
            if target_state not in {str(value) for value in allowed}:
                raise StateConflict(f"forbidden transition {entity_type} {current} -> {target_state}")
            if current == RunState.BLOCKED and target_state in {RunState.READY, RunState.RUNNING} and not decision_id:
                raise StateConflict("BLOCKED Run requires an explicit Decision")
            now = utc_now()
            terminal_states = {
                "run": {"COMPLETED", "FAILED", "CANCELLED"},
                "task": {"SUCCEEDED", "FAILED", "CANCELLED", "SUPERSEDED", "BLOCKED"},
                "attempt": {
                    "SUCCEEDED", "RETRYABLE_FAILED", "FAILED", "BLOCKED", "CANCELLED",
                    "QUARANTINED", "DISPATCH_UNCERTAIN",
                },
                "session": {"COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED", "UNKNOWN", "QUARANTINED"},
                "check": {"PASSED", "FAILED", "ERROR", "SKIPPED"},
            }
            ended = now if target_state in terminal_states[entity_type] else None
            started = now if target_state == "RUNNING" and "started_at" in row.keys() and row["started_at"] is None else row["started_at"] if "started_at" in row.keys() else None
            assignments = ["state=?", "version=version+1", "updated_at=?"]
            parameters: list[Any] = [target_state, now]
            if "started_at" in row.keys() and started is not None:
                assignments.append("started_at=COALESCE(started_at, ?)")
                parameters.append(started)
            if "ended_at" in row.keys() and ended is not None:
                assignments.append("ended_at=?")
                parameters.append(ended)
            parameters.extend([entity_id, expected_version])
            cursor = self.connection.execute(
                f"UPDATE {table} SET {', '.join(assignments)} WHERE {id_column}=? AND version=?",
                parameters,
            )
            if cursor.rowcount != 1:
                raise StateConflict(f"concurrent transition for {entity_type} {entity_id}")
            key = f"transition:{entity_type}:{entity_id}:{current}:{target_state}:{expected_version}"
            self._insert_event(entity_type, entity_id, event_type, payload, key, decision_id)
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        return self.get(entity_type, entity_id)

    def begin_attempt(
        self,
        task_id: str,
        attempt_no: int,
        start_reason: str,
        task_contract_json: str,
        input_fingerprint: str,
        attempt_id: str | None = None,
    ) -> dict[str, Any]:
        attempt_id = attempt_id or new_id("attempt")
        dispatch_token = f"{attempt_id}:1"
        now = utc_now()
        self._begin()
        try:
            task = self.connection.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if task is None or task["state"] != TaskState.READY or task["active_attempt_id"] is not None:
                raise StateConflict("Task is not ready for a new Attempt")
            active = self.connection.execute(
                "SELECT COUNT(*) FROM tasks WHERE active_attempt_id IS NOT NULL"
            ).fetchone()[0]
            if active:
                raise StateConflict("B1 permits only one active Attempt")
            self.connection.execute(
                """INSERT INTO attempts(
                    attempt_id, task_id, attempt_no, start_reason, dispatch_token,
                    task_contract_json, input_fingerprint, state, started_at, created_at, updated_at
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    attempt_id, task_id, attempt_no, start_reason, dispatch_token,
                    task_contract_json, input_fingerprint, AttemptState.CREATED, now, now, now,
                ),
            )
            self._insert_event(
                "attempt", attempt_id, "attempt_created", {"state": AttemptState.CREATED}, f"create:attempt:{attempt_id}"
            )
            self.connection.execute(
                "UPDATE tasks SET active_attempt_id=?, state=?, version=version+1, updated_at=? WHERE task_id=? AND version=?",
                (attempt_id, TaskState.RUNNING, now, task_id, task["version"]),
            )
            self._insert_event(
                "task",
                task_id,
                "task_started",
                {"attempt_id": attempt_id},
                f"transition:task:{task_id}:{TaskState.READY}:{TaskState.RUNNING}:{task['version']}",
            )
            self.connection.execute(
                "UPDATE attempts SET state=?, version=1, updated_at=? WHERE attempt_id=? AND version=0",
                (AttemptState.DISPATCHING, now, attempt_id),
            )
            self._insert_event(
                "attempt",
                attempt_id,
                "attempt_dispatching",
                {"dispatch_token": dispatch_token},
                f"transition:attempt:{attempt_id}:{AttemptState.CREATED}:{AttemptState.DISPATCHING}:0",
            )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        return self.get("attempt", attempt_id)

    def create_session(
        self,
        attempt_id: str,
        runtime_name: str,
        runtime_version: str,
        runtime_session_id: str,
        runtime_profile: str,
        cwd: str,
        sandbox: str,
        capabilities: Mapping[str, Any],
        usage_status: str,
    ) -> dict[str, Any]:
        session_id = new_id("session")
        now = utc_now()
        self._begin()
        try:
            attempt = self.connection.execute("SELECT * FROM attempts WHERE attempt_id=?", (attempt_id,)).fetchone()
            if attempt is None or attempt["session_id"] is not None:
                raise StateConflict("Attempt cannot accept a Session")
            self.connection.execute(
                """INSERT INTO sessions(
                    session_id, attempt_id, runtime_name, runtime_version, runtime_session_id,
                    runtime_profile, cwd, sandbox, capabilities_json, state, interrupt_state,
                    usage_status, started_at, created_at, updated_at
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'not_requested', ?, ?, ?, ?)""",
                (
                    session_id, attempt_id, runtime_name, runtime_version, runtime_session_id,
                    runtime_profile, cwd, sandbox, canonical_json(capabilities), SessionState.STARTING,
                    usage_status, now, now, now,
                ),
            )
            self.connection.execute(
                "UPDATE attempts SET session_id=?, updated_at=? WHERE attempt_id=?",
                (session_id, now, attempt_id),
            )
            self._insert_event(
                "session", session_id, "session_created", {"state": SessionState.STARTING}, f"create:session:{session_id}"
            )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        return self.get("session", session_id)

    def mark_dispatched(self, attempt_id: str, session_id: str, runtime_turn_id: str) -> None:
        now = utc_now()
        self._begin()
        try:
            attempt = self.connection.execute("SELECT * FROM attempts WHERE attempt_id=?", (attempt_id,)).fetchone()
            session = self.connection.execute("SELECT * FROM sessions WHERE session_id=?", (session_id,)).fetchone()
            if attempt is None or session is None:
                raise LedgerError("Attempt or Session not found")
            if attempt["state"] != AttemptState.DISPATCHING or session["state"] != SessionState.STARTING:
                raise StateConflict("dispatch records are not in STARTING states")
            self.connection.execute(
                "UPDATE sessions SET active_runtime_turn_id=?, state=?, version=version+1, updated_at=? WHERE session_id=? AND version=?",
                (runtime_turn_id, SessionState.RUNNING, now, session_id, session["version"]),
            )
            self.connection.execute(
                "UPDATE attempts SET state=?, version=version+1, updated_at=? WHERE attempt_id=? AND version=?",
                (AttemptState.RUNNING, now, attempt_id, attempt["version"]),
            )
            self._insert_event(
                "session", session_id, "session_running", {"runtime_turn_id": runtime_turn_id},
                f"transition:session:{session_id}:{SessionState.STARTING}:{SessionState.RUNNING}:{session['version']}",
            )
            self._insert_event(
                "attempt", attempt_id, "attempt_running", {"runtime_turn_id": runtime_turn_id},
                f"transition:attempt:{attempt_id}:{AttemptState.DISPATCHING}:{AttemptState.RUNNING}:{attempt['version']}",
            )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def set_active_turn(self, session_id: str, runtime_turn_id: str) -> dict[str, Any]:
        now = utc_now()
        self._begin()
        try:
            session = self.connection.execute("SELECT * FROM sessions WHERE session_id=?", (session_id,)).fetchone()
            if session is None or session["state"] != SessionState.RUNNING:
                raise StateConflict("Session is not RUNNING")
            self.connection.execute(
                "UPDATE sessions SET active_runtime_turn_id=?, version=version+1, updated_at=? WHERE session_id=? AND version=?",
                (runtime_turn_id, now, session_id, session["version"]),
            )
            self._insert_event(
                "session", session_id, "session_resumed", {"runtime_turn_id": runtime_turn_id},
                f"resume:session:{session_id}:{runtime_turn_id}",
            )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        return self.get("session", session_id)

    def increment_resume(self, attempt_id: str, maximum: int) -> int:
        self._begin()
        try:
            row = self.connection.execute(
                "SELECT resume_count FROM attempts WHERE attempt_id=?", (attempt_id,)
            ).fetchone()
            if row is None or int(row["resume_count"]) >= maximum:
                raise StateConflict("Attempt resume budget exhausted")
            count = int(row["resume_count"]) + 1
            self.connection.execute(
                "UPDATE attempts SET resume_count=?, updated_at=? WHERE attempt_id=?", (count, utc_now(), attempt_id)
            )
            self._insert_event(
                "attempt", attempt_id, "attempt_resumed", {"resume_count": count}, f"resume:attempt:{attempt_id}:{count}"
            )
            self.connection.commit()
            return count
        except Exception:
            self.connection.rollback()
            raise

    def set_baseline_artifact(self, attempt_id: str, artifact_id: str) -> None:
        self.connection.execute(
            "UPDATE attempts SET baseline_artifact_id=?, updated_at=? WHERE attempt_id=?",
            (artifact_id, utc_now(), attempt_id),
        )

    def append_usage_snapshot(self, session_id: str, runtime_turn_id: str, snapshot: Mapping[str, Any] | None) -> None:
        session = self.get("session", session_id)
        existing = json.loads(session["usage_json"]) if session["usage_json"] else {
            "scope": "thread_cumulative",
            "snapshots": [],
        }
        if not snapshot or snapshot.get("status") != "measured" or not snapshot.get("total"):
            self.connection.execute(
                "UPDATE sessions SET usage_status=?, updated_at=? WHERE session_id=?",
                (snapshot.get("status", "unknown") if snapshot else "unknown", utc_now(), session_id),
            )
            return
        total = snapshot["total"]
        previous = existing["snapshots"][-1]["total"] if existing["snapshots"] else None
        delta: dict[str, int] | str
        if previous is None:
            delta = dict(total)
        else:
            keys = {"input_tokens", "output_tokens", "total_tokens"}
            if not keys.issubset(total) or not keys.issubset(previous):
                delta = "unknown"
            else:
                calculated = {key: int(total[key]) - int(previous[key]) for key in keys}
                delta = calculated if all(value >= 0 for value in calculated.values()) else "unknown"
        existing["snapshots"].append({
            "runtime_turn_id": runtime_turn_id,
            "last": dict(total),
            "total": dict(total),
            "delta": delta,
        })
        self.connection.execute(
            "UPDATE sessions SET usage_status='measured', usage_json=?, updated_at=? WHERE session_id=?",
            (canonical_json(existing), utc_now(), session_id),
        )

    def finish_attempt(
        self,
        attempt_id: str,
        attempt_target: str,
        task_target: str,
        failure_kind: str | None,
        payload: Mapping[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        payload = dict(payload or {})
        now = utc_now()
        self._begin()
        try:
            attempt = self.connection.execute("SELECT * FROM attempts WHERE attempt_id=?", (attempt_id,)).fetchone()
            if attempt is None:
                raise LedgerError(f"Attempt not found: {attempt_id}")
            task = self.connection.execute("SELECT * FROM tasks WHERE task_id=?", (attempt["task_id"],)).fetchone()
            if task is None or task["active_attempt_id"] != attempt_id:
                raise StateConflict("Task does not own this active Attempt")
            if attempt_target not in {str(value) for value in ATTEMPT_TRANSITIONS.get(attempt["state"], set())}:
                raise StateConflict(f"forbidden Attempt terminal transition {attempt['state']} -> {attempt_target}")
            if task_target not in {str(value) for value in TASK_TRANSITIONS.get(task["state"], set())}:
                raise StateConflict(f"forbidden Task terminal transition {task['state']} -> {task_target}")
            self.connection.execute(
                """UPDATE attempts SET state=?, failure_kind=?, ended_at=?, version=version+1,
                    updated_at=? WHERE attempt_id=? AND version=?""",
                (attempt_target, failure_kind, now, now, attempt_id, attempt["version"]),
            )
            self.connection.execute(
                """UPDATE tasks SET state=?, active_attempt_id=NULL,
                    version=version+1, updated_at=? WHERE task_id=? AND version=?""",
                (task_target, now, task["task_id"], task["version"]),
            )
            self._insert_event(
                "attempt", attempt_id, "attempt_finished", {**payload, "state": attempt_target, "failure_kind": failure_kind},
                f"transition:attempt:{attempt_id}:{attempt['state']}:{attempt_target}:{attempt['version']}",
            )
            self._insert_event(
                "task", task["task_id"], "task_attempt_finished", {**payload, "state": task_target, "attempt_id": attempt_id},
                f"transition:task:{task['task_id']}:{task['state']}:{task_target}:{task['version']}",
            )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        return self.get("attempt", attempt_id), self.get("task", task["task_id"])

    def set_result_claim(self, attempt_id: str, claim: str) -> None:
        self.connection.execute(
            "UPDATE attempts SET result_claim=?, updated_at=? WHERE attempt_id=?", (claim, utc_now(), attempt_id)
        )

    def update_session_terminal(
        self,
        session_id: str,
        target_state: str,
        evidence: Mapping[str, Any],
        usage_status: str,
        usage: Mapping[str, Any] | None,
        interrupt_state: str | None = None,
    ) -> dict[str, Any]:
        row = self.get("session", session_id)
        updated = self.transition(
            "session",
            session_id,
            row["version"],
            target_state,
            "session_terminal",
            evidence,
        )
        assignments = ["terminal_evidence_json=?", "usage_status=?", "last_runtime_event_at=?"]
        values: list[Any] = [canonical_json(evidence), usage_status, utc_now()]
        if usage is not None:
            assignments.append("usage_json=?")
            values.append(canonical_json(usage))
        if interrupt_state:
            assignments.append("interrupt_state=?")
            values.append(interrupt_state)
        values.append(session_id)
        self.connection.execute(f"UPDATE sessions SET {', '.join(assignments)} WHERE session_id=?", values)
        return self.get("session", session_id)

    def increment_turns(self, run_id: str) -> None:
        cursor = self.connection.execute(
            "UPDATE runs SET turns_used=turns_used+1, updated_at=? WHERE run_id=? AND turns_used < max_turns",
            (utc_now(), run_id),
        )
        if cursor.rowcount != 1:
            raise StateConflict("Run turn budget exhausted")

    def register_artifact(self, metadata: Mapping[str, Any]) -> dict[str, Any]:
        artifact_id = str(metadata.get("artifact_id") or new_id("artifact"))
        try:
            self.connection.execute(
                """INSERT INTO artifacts(
                    artifact_id, run_id, task_id, attempt_id, kind, relative_path, sha256,
                    size_bytes, media_type, sensitivity, retention, producer, created_at
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    artifact_id, metadata["run_id"], metadata.get("task_id"), metadata.get("attempt_id"),
                    metadata["kind"], metadata["relative_path"], metadata["sha256"], metadata["size_bytes"],
                    metadata.get("media_type"), metadata.get("sensitivity", "project_local"),
                    metadata.get("retention", "run"), metadata.get("producer", "controller"), utc_now(),
                ),
            )
        except sqlite3.IntegrityError as exc:
            existing = self.connection.execute(
                "SELECT * FROM artifacts WHERE run_id=? AND relative_path=?",
                (metadata["run_id"], metadata["relative_path"]),
            ).fetchone()
            if existing and existing["sha256"] == metadata["sha256"]:
                return dict(existing)
            if existing and existing["kind"] == "report" and metadata["kind"] == "report":
                self.connection.execute(
                    "UPDATE artifacts SET sha256=?, size_bytes=?, media_type=?, created_at=? WHERE artifact_id=?",
                    (metadata["sha256"], metadata["size_bytes"], metadata.get("media_type"), utc_now(), existing["artifact_id"]),
                )
                return dict(self.connection.execute(
                    "SELECT * FROM artifacts WHERE artifact_id=?", (existing["artifact_id"],)
                ).fetchone())
            raise IntegrityViolation("conflicting Artifact path or hash") from exc
        return dict(self.connection.execute("SELECT * FROM artifacts WHERE artifact_id=?", (artifact_id,)).fetchone())

    def record_result_event(self, runtime_name: str, runtime_turn_id: str, result_sha256: str, attempt_id: str) -> str:
        key = f"result:{runtime_name}:{runtime_turn_id}:{result_sha256}"
        self._begin()
        try:
            existing_turn = self.connection.execute(
                "SELECT idempotency_key, payload_json FROM events WHERE event_type='runtime_result' AND idempotency_key LIKE ?",
                (f"result:{runtime_name}:{runtime_turn_id}:%",),
            ).fetchone()
            payload = {"runtime_turn_id": runtime_turn_id, "result_sha256": result_sha256}
            if existing_turn and existing_turn["idempotency_key"] != key:
                raise IntegrityViolation("same runtime turn produced conflicting result hashes")
            event_id = self._insert_event("attempt", attempt_id, "runtime_result", payload, key)
            self.connection.commit()
            return event_id
        except Exception:
            self.connection.rollback()
            raise

    def create_check(self, values: Mapping[str, Any]) -> dict[str, Any]:
        check_id = str(values.get("check_id") or new_id("check"))
        now = utc_now()
        self._begin()
        try:
            self.connection.execute(
                """INSERT INTO checks(
                    check_id, task_id, attempt_id, requirements_version, check_name, check_kind,
                    command_argv_json, state, exit_code, stdout_artifact_id, stderr_artifact_id,
                    started_at, ended_at, created_at
                ) VALUES(?, ?, ?, ?, ?, 'command', ?, ?, NULL, NULL, NULL, NULL, NULL, ?)""",
                (
                    check_id, values["task_id"], values["attempt_id"], values.get("requirements_version", 1),
                    values["check_name"], canonical_json(values["argv"]), CheckState.PENDING, now,
                ),
            )
            self._insert_event(
                "check", check_id, "check_created", {"state": CheckState.PENDING}, f"create:check:{check_id}"
            )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        return self.get("check", check_id)

    def start_check(self, check_id: str) -> dict[str, Any]:
        self._begin()
        try:
            row = self.connection.execute("SELECT * FROM checks WHERE check_id=?", (check_id,)).fetchone()
            if row is None or row["state"] != CheckState.PENDING:
                raise StateConflict("Check is not PENDING")
            now = utc_now()
            self.connection.execute(
                "UPDATE checks SET state=?, started_at=? WHERE check_id=? AND state=?",
                (CheckState.RUNNING, now, check_id, CheckState.PENDING),
            )
            self._insert_event(
                "check", check_id, "check_running", {"state": CheckState.RUNNING},
                f"transition:check:{check_id}:{CheckState.PENDING}:{CheckState.RUNNING}",
            )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        return self.get("check", check_id)

    def finish_check(self, check_id: str, values: Mapping[str, Any]) -> dict[str, Any]:
        target = str(values["state"])
        if target not in {str(value) for value in CHECK_TRANSITIONS[CheckState.RUNNING]}:
            raise StateConflict(f"invalid Check terminal state: {target}")
        self._begin()
        try:
            row = self.connection.execute("SELECT * FROM checks WHERE check_id=?", (check_id,)).fetchone()
            if row is None or row["state"] != CheckState.RUNNING:
                raise StateConflict("Check is not RUNNING")
            self.connection.execute(
                """UPDATE checks SET state=?, exit_code=?, stdout_artifact_id=?, stderr_artifact_id=?,
                    ended_at=? WHERE check_id=? AND state=?""",
                (
                    target, values.get("exit_code"), values.get("stdout_artifact_id"),
                    values.get("stderr_artifact_id"), values.get("ended_at", utc_now()),
                    check_id, CheckState.RUNNING,
                ),
            )
            key = f"check:{values['attempt_id']}:{values['check_name']}:{values['input_fingerprint']}"
            self._insert_event(
                "check", check_id, "check_finished", {"state": target, "exit_code": values.get("exit_code")}, key
            )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        return self.get("check", check_id)

    def record_check(self, values: Mapping[str, Any]) -> dict[str, Any]:
        check = self.create_check(values)
        self.start_check(check["check_id"])
        return self.finish_check(check["check_id"], values)

    def record_decision(self, values: Mapping[str, Any]) -> dict[str, Any]:
        decision_id = str(values.get("decision_id") or new_id("decision"))
        self.connection.execute(
            """INSERT INTO decisions(
                decision_id, run_id, task_id, attempt_id, kind, actor, outcome,
                scope_json, evidence_json, created_at
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                decision_id, values["run_id"], values.get("task_id"), values.get("attempt_id"), values["kind"],
                values.get("actor", "user"), values.get("outcome", "recorded"), canonical_json(values.get("scope", {})),
                canonical_json(values.get("evidence", {})), utc_now(),
            ),
        )
        return dict(self.connection.execute("SELECT * FROM decisions WHERE decision_id=?", (decision_id,)).fetchone())

    def task_by_key(self, run_id: str, key: str) -> dict[str, Any]:
        row = self.connection.execute(
            "SELECT * FROM tasks WHERE run_id=? AND external_key=?", (run_id, key)
        ).fetchone()
        if row is None:
            raise LedgerError(f"Task not found: {key}")
        return dict(row)

    def list_tasks(self, run_id: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self.connection.execute(
            "SELECT * FROM tasks WHERE run_id=? ORDER BY ordinal", (run_id,)
        ).fetchall()]

    def list_attempts(self, task_id: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self.connection.execute(
            "SELECT * FROM attempts WHERE task_id=? ORDER BY attempt_no", (task_id,)
        ).fetchall()]

    def dependencies_succeeded(self, task_id: str) -> bool:
        row = self.connection.execute(
            """SELECT COUNT(*) FROM task_dependencies d JOIN tasks t ON t.task_id=d.depends_on_task_id
               WHERE d.task_id=? AND t.state<>?""",
            (task_id, TaskState.SUCCEEDED),
        ).fetchone()
        return int(row[0]) == 0

    def any_active_attempt(self) -> bool:
        return bool(self.connection.execute(
            "SELECT 1 FROM tasks WHERE active_attempt_id IS NOT NULL LIMIT 1"
        ).fetchone())

    def nonterminal_attempts(self, run_id: str) -> list[dict[str, Any]]:
        terminal = tuple(str(value) for value in {
            AttemptState.SUCCEEDED, AttemptState.RETRYABLE_FAILED, AttemptState.FAILED,
            AttemptState.BLOCKED, AttemptState.CANCELLED, AttemptState.QUARANTINED,
            AttemptState.DISPATCH_UNCERTAIN,
        })
        placeholders = ",".join("?" for _ in terminal)
        return [dict(row) for row in self.connection.execute(
            f"""SELECT a.* FROM attempts a JOIN tasks t ON t.task_id=a.task_id
                WHERE t.run_id=? AND a.state NOT IN ({placeholders})""",
            (run_id, *terminal),
        ).fetchall()]

    def load_run_snapshot(self, run_id: str) -> dict[str, Any]:
        run = self.get("run", run_id)
        tasks = self.list_tasks(run_id)
        for task in tasks:
            task["attempts"] = self.list_attempts(task["task_id"])
        checks = [dict(row) for row in self.connection.execute(
            "SELECT c.* FROM checks c JOIN tasks t ON t.task_id=c.task_id WHERE t.run_id=? ORDER BY c.created_at", (run_id,)
        ).fetchall()]
        sessions = [dict(row) for row in self.connection.execute(
            """SELECT s.* FROM sessions s JOIN attempts a ON a.attempt_id=s.attempt_id
                JOIN tasks t ON t.task_id=a.task_id WHERE t.run_id=? ORDER BY s.created_at""", (run_id,)
        ).fetchall()]
        decisions = [dict(row) for row in self.connection.execute(
            "SELECT * FROM decisions WHERE run_id=? ORDER BY created_at", (run_id,)
        ).fetchall()]
        artifacts = [dict(row) for row in self.connection.execute(
            "SELECT * FROM artifacts WHERE run_id=? ORDER BY relative_path", (run_id,)
        ).fetchall()]
        aggregate_ids = {run_id}
        aggregate_ids.update(task["task_id"] for task in tasks)
        aggregate_ids.update(attempt["attempt_id"] for task in tasks for attempt in task["attempts"])
        aggregate_ids.update(session["session_id"] for session in sessions)
        aggregate_ids.update(check["check_id"] for check in checks)
        placeholders = ",".join("?" for _ in aggregate_ids)
        events = [dict(row) for row in self.connection.execute(
            f"SELECT * FROM events WHERE aggregate_id IN ({placeholders}) ORDER BY seq", tuple(sorted(aggregate_ids))
        ).fetchall()]
        return {
            "run": run,
            "tasks": tasks,
            "checks": checks,
            "sessions": sessions,
            "decisions": decisions,
            "artifacts": artifacts,
            "events": events,
        }

    def find_run(self, run_id: str) -> bool:
        return self.connection.execute("SELECT 1 FROM runs WHERE run_id=?", (run_id,)).fetchone() is not None

    def sqlite_backup(self, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        target = sqlite3.connect(destination)
        try:
            self.connection.backup(target)
        finally:
            target.close()
