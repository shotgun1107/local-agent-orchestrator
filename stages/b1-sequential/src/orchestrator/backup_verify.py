"""Read-only verification of a closed, schema-1, single-Run backup bundle.

Only trusted program SQL runs, against a bounded in-memory copy of the hashed
DB. This checks internal consistency, not publisher authenticity or Live safety.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import time
from typing import Any

from .contract import AttemptState, CheckState, CORE_VERSION, RunState, SessionState, TaskState, sha256_bytes
from .ledger import MIGRATION_1_CHECKSUM, MIGRATION_1_UP

MAX_FILES = 50_000
MAX_MANIFEST_BYTES = 8 * 1024 * 1024
MAX_DB_BYTES = 256 * 1024 * 1024
MAX_FILE_BYTES = 512 * 1024 * 1024
MAX_TOTAL_BYTES = 2 * 1024 * 1024 * 1024
MAX_SQL_SECONDS = 10.0


class BackupVerificationError(ValueError):
    """Messages are fixed reason codes, never untrusted DB/manifest contents."""


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise BackupVerificationError(reason)


def validate_backup_relative_path(value: Any) -> str:
    _require(isinstance(value, str) and 0 < len(value) <= 1024, "unsafe_path")
    _require(not any(c in value for c in '\\:\x00<>"|?*') and not any(ord(c) < 32 or ord(c) == 127 for c in value), "unsafe_path")
    parts = value.split("/")
    _require(len(parts) <= 64, "path_depth_limit")
    for part in parts:
        _require(part not in {"", ".", ".."} and not part.endswith((" ", ".")), "unsafe_path")
        _require(re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", part) is None, "unsafe_path")
    return value


def _stamp(info: os.stat_result) -> tuple[int, ...]:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _no_link(info: os.stat_result) -> None:
    _require(not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400, "link_or_reparse")


def checked_backup_directory(path: Path) -> Path:
    root = Path(os.path.abspath(path))
    for ancestor in (root, *root.parents):
        info = ancestor.lstat()
        _no_link(info)
        _require(stat.S_ISDIR(info.st_mode), "not_directory")
    return root


def _tree(root: Path) -> dict[str, tuple[int, ...]]:
    root = checked_backup_directory(root)
    found = {"": _stamp(root.lstat())}
    aliases: set[str] = set()
    pending = [(root, "")]
    total = 0
    while pending:
        directory, prefix = pending.pop()
        _no_link(directory.lstat())
        with os.scandir(directory) as entries:
            for entry in entries:
                relative = validate_backup_relative_path(prefix + entry.name)
                _require(relative.casefold() not in aliases, "path_alias")
                aliases.add(relative.casefold())
                # DirEntry.stat caches zero inode/dev/link counts on Windows;
                # use path lstat consistently for identity and hard-link checks.
                info = Path(entry.path).lstat()
                _no_link(info)
                _require(stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode), "not_regular_file")
                _require(stat.S_ISDIR(info.st_mode) or info.st_nlink == 1, "hard_link")
                _require(info.st_size <= MAX_FILE_BYTES, "file_size_limit")
                found[relative] = _stamp(info)
                _require(len(found) <= MAX_FILES, "file_count_limit")
                if stat.S_ISDIR(info.st_mode):
                    pending.append((Path(entry.path), relative + "/"))
                else:
                    total += info.st_size
                    _require(total <= MAX_TOTAL_BYTES, "bundle_size_limit")
    return found


def _read(root: Path, relative: str, tree: dict, *, capture: bool = False, limit: int = MAX_FILE_BYTES) -> tuple[str, bytes]:
    validate_backup_relative_path(relative)
    _require(relative in tree and stat.S_ISREG(tree[relative][2]), "missing_file")
    expected = tree[relative]
    _require(expected[3] <= limit, "file_size_limit")
    path = root.joinpath(*relative.split("/"))
    for parent in (path, *path.parents):
        info = parent.lstat()
        _no_link(info)
        if parent == root:
            break
    _require(_stamp(path.lstat()) == expected, "bundle_changed")
    digest = hashlib.sha256()
    chunks = []
    size = 0
    with path.open("rb") as handle:
        opened = _stamp(os.fstat(handle.fileno()))
        # Windows 3.12 lstat/fstat can disagree on ctime; compare it only within
        # the same API, while binding the handle through all other fields.
        _require(opened[:-1] == expected[:-1], "bundle_changed")
        while chunk := handle.read(256 * 1024):
            size += len(chunk)
            _require(size <= limit, "file_size_limit")
            digest.update(chunk)
            if capture:
                chunks.append(chunk)
        _require(_stamp(os.fstat(handle.fileno())) == opened, "bundle_changed")
    _require(size == expected[3] and _stamp(path.lstat()) == expected, "bundle_changed")
    return digest.hexdigest(), b"".join(chunks)


def _pairs(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        _require(key not in result, "duplicate_json_key")
        result[key] = value
    return result


def _manifest(data: bytes, expected_run_id: str | None) -> dict:
    def reject_constant(value: str) -> None:
        raise BackupVerificationError("nonfinite_json")
    value = json.loads(data.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=reject_constant)
    _require(type(value) is dict and set(value) == {"schema_version", "run_id", "core_version", "created_at", "files"}, "manifest_fields")
    _require(type(value["schema_version"]) is int and value["schema_version"] == 1, "manifest_version")
    _require(value["core_version"] == CORE_VERSION, "core_version")
    run_id = value["run_id"]
    _require(isinstance(run_id, str) and 0 < len(run_id) <= 200 and not any(ord(c) < 32 for c in run_id), "run_identity")
    _require(expected_run_id is None or expected_run_id == run_id, "unexpected_run")
    _require(isinstance(value["created_at"], str), "manifest_timestamp")
    _require(datetime.fromisoformat(value["created_at"].replace("Z", "+00:00")).utcoffset() is not None, "manifest_timestamp")
    files = value["files"]
    _require(type(files) is list and 0 < len(files) <= MAX_FILES, "manifest_files")
    names: set[str] = set()
    for item in files:
        _require(type(item) is dict and set(item) == {"path", "sha256"}, "manifest_file_fields")
        name = validate_backup_relative_path(item["path"])
        _require(name.casefold() not in names, "duplicate_path")
        names.add(name.casefold())
        _require(isinstance(item["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is not None, "invalid_hash")
    _require(any(item["path"] == "ledger.sqlite" for item in files), "missing_database")
    return value


def _schema(connection: sqlite3.Connection) -> list:
    return [(kind, name, table, sql.replace("\r\n", "\n").strip() if sql else sql)
            for kind, name, table, sql in connection.execute("SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name")]


def _database(data: bytes, run_id: str, core_version: str) -> tuple[list[tuple], bool]:
    _require(len(data) >= 100 and data.startswith(b"SQLite format 3\0"), "invalid_database")
    _require(data[18:20] in {b"\x01\x01", b"\x02\x02"}, "database_format")
    # SQLite's documented deserialize workaround for a complete online backup
    # with a WAL header. Only this RAM copy is adjusted, NEVER the hashed file.
    ram_image = data[:18] + b"\x01\x01" + data[20:]
    connection = sqlite3.connect(":memory:")
    reference = sqlite3.connect(":memory:")
    try:
        _require(hasattr(connection, "deserialize") and hasattr(sqlite3, "SQLITE_DBCONFIG_DEFENSIVE"), "sqlite_capability")
        connection.setconfig(sqlite3.SQLITE_DBCONFIG_DEFENSIVE, True)
        connection.setlimit(sqlite3.SQLITE_LIMIT_ATTACHED, 0)
        connection.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, MAX_DB_BYTES)
        connection.deserialize(ram_image)
        connection.execute("PRAGMA trusted_schema=OFF")
        connection.execute("PRAGMA query_only=ON")
        connection.execute("PRAGMA temp_store=MEMORY")
        deadline = time.monotonic() + MAX_SQL_SECONDS
        connection.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
        # Executed SQL is this repository's frozen schema, never SQL from input.
        reference.executescript(MIGRATION_1_UP)
        _require(_schema(connection) == _schema(reference), "database_schema")
        _require(connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)], "database_integrity")
        _require(not connection.execute("PRAGMA foreign_key_check").fetchall(), "database_foreign_keys")
        _require(connection.execute("SELECT version,checksum FROM schema_migrations ORDER BY version").fetchall() == [(1, MIGRATION_1_CHECKSUM)], "database_migration")
        _require(connection.execute("SELECT core_version FROM runs WHERE run_id=?", (run_id,)).fetchall() == [(core_version,)], "database_run")
        for table, states in (("runs", RunState), ("tasks", TaskState), ("attempts", AttemptState),
                              ("sessions", SessionState), ("checks", CheckState)):
            allowed = {value.value for value in states}
            _require(all(state in allowed for (state,) in connection.execute(f"SELECT DISTINCT state FROM {table}")), "database_state")
        # FKs prove existence, but not that ownership stays in the same Run/Task.
        violations = [
            "SELECT 1 FROM artifacts a JOIN tasks t ON t.task_id=a.task_id WHERE a.run_id<>t.run_id",
            "SELECT 1 FROM artifacts a JOIN attempts p ON p.attempt_id=a.attempt_id JOIN tasks t ON t.task_id=p.task_id WHERE a.run_id<>t.run_id OR a.task_id IS NULL OR a.task_id<>p.task_id",
            "SELECT 1 FROM checks c JOIN attempts a ON a.attempt_id=c.attempt_id WHERE c.task_id<>a.task_id",
            "SELECT 1 FROM tasks t JOIN attempts a ON a.attempt_id=t.active_attempt_id WHERE t.task_id<>a.task_id",
            "SELECT 1 FROM attempts a JOIN sessions s ON s.session_id=a.session_id WHERE s.attempt_id<>a.attempt_id",
            "SELECT 1 FROM sessions s JOIN attempts a ON a.attempt_id=s.attempt_id WHERE a.session_id IS NULL OR a.session_id<>s.session_id",
            "SELECT 1 FROM task_dependencies d JOIN tasks t ON t.task_id=d.task_id JOIN tasks p ON p.task_id=d.depends_on_task_id WHERE t.run_id<>p.run_id",
            "SELECT 1 FROM attempts p JOIN artifacts a ON a.artifact_id=p.baseline_artifact_id WHERE a.attempt_id IS NULL OR a.attempt_id<>p.attempt_id OR a.kind<>'workspace_baseline'",
            "SELECT 1 FROM decisions d JOIN tasks t ON t.task_id=d.task_id WHERE d.run_id<>t.run_id",
            "SELECT 1 FROM decisions d JOIN attempts a ON a.attempt_id=d.attempt_id JOIN tasks t ON t.task_id=a.task_id WHERE d.run_id<>t.run_id OR (d.task_id IS NOT NULL AND d.task_id<>a.task_id)",
        ]
        for query in violations:
            _require(connection.execute(query + " LIMIT 1").fetchone() is None, "database_ownership")
        for kind, table, key in (("run", "runs", "run_id"), ("task", "tasks", "task_id"),
                                 ("attempt", "attempts", "attempt_id"), ("session", "sessions", "session_id"),
                                 ("check", "checks", "check_id")):
            _require(connection.execute(
                f"SELECT 1 FROM events e LEFT JOIN {table} t ON t.{key}=e.aggregate_id WHERE e.aggregate_type=? AND t.{key} IS NULL LIMIT 1", (kind,),
            ).fetchone() is None, "database_event_reference")
        for column, kind in (("stdout_artifact_id", "check_stdout"), ("stderr_artifact_id", "check_stderr")):
            _require(connection.execute(
                f"SELECT 1 FROM checks c JOIN artifacts a ON a.artifact_id=c.{column} WHERE a.attempt_id IS NULL OR a.attempt_id<>c.attempt_id OR a.kind<>? LIMIT 1", (kind,),
            ).fetchone() is None, "database_ownership")
        artifacts = connection.execute("SELECT relative_path,sha256,size_bytes FROM artifacts WHERE run_id=? ORDER BY relative_path", (run_id,)).fetchall()
        cancel_id = "cancel_" + sha256_bytes(run_id.encode())[:32]
        cancellation = connection.execute("SELECT 1 FROM decisions WHERE decision_id=? AND run_id=? AND kind='cancel'", (cancel_id, run_id)).fetchone() is not None
        return artifacts, cancellation
    finally:
        connection.close()
        reference.close()


def verify_backup(path: Path, *, expected_run_id: str | None = None) -> dict[str, Any]:
    """No source writes/migrations/reconcile. Failure never echoes untrusted data."""
    try:
        root = Path(os.path.abspath(path))
        before = _tree(root)
        _, raw_manifest = _read(root, "manifest.json", before, capture=True, limit=MAX_MANIFEST_BYTES)
        manifest = _manifest(raw_manifest, expected_run_id)
        listed = {item["path"]: item["sha256"] for item in manifest["files"]}
        actual = {name for name, info in before.items() if stat.S_ISREG(info[2])}
        _require(actual == set(listed) | {"manifest.json"}, "bundle_file_set")
        directories = {""}
        for name in listed:
            directories.update("/".join(name.split("/")[:i]) for i in range(1, len(name.split("/"))))
        _require({name for name, info in before.items() if stat.S_ISDIR(info[2])} == directories, "bundle_directory_set")
        digests = {}
        database = b""
        for relative, expected in listed.items():
            digest, payload = _read(root, relative, before, capture=relative == "ledger.sqlite",
                                    limit=MAX_DB_BYTES if relative == "ledger.sqlite" else MAX_FILE_BYTES)
            _require(digest == expected, "file_hash_mismatch")
            digests[relative] = digest
            if relative == "ledger.sqlite":
                database = payload
        artifacts, cancellation = _database(database, manifest["run_id"], manifest["core_version"])
        required = {"ledger.sqlite"}
        for relative, digest, size in artifacts:
            name = "artifacts/" + validate_backup_relative_path(relative)
            _require(name not in required, "artifact_path_collision")
            required.add(name)
            _require(name in digests and digests[name] == digest and type(size) is int and before[name][3] == size, "artifact_binding")
        marker = "cancel-requests/" + sha256_bytes(manifest["run_id"].encode()) + ".request"
        if cancellation or marker in listed:
            _require(marker in digests and digests[marker] == sha256_bytes(b"") and before[marker][3] == 0, "cancel_intent")
            required.add(marker)
        _require(set(listed) == required, "run_artifact_set")
        _require(_tree(root) == before, "bundle_changed")
        for relative, digest in {**digests, "manifest.json": sha256_bytes(raw_manifest)}.items():
            _require(_read(root, relative, before)[0] == digest, "bundle_changed")
        _require(_tree(root) == before, "bundle_changed")
        return {"ok": True, "mismatches": [], "manifest": manifest, "scope": "selected_run", "verified_files": len(listed)}
    except BackupVerificationError as exc:
        reason = str(exc)
    except (OSError, ValueError, TypeError, KeyError, sqlite3.Error, MemoryError, OverflowError, RecursionError):
        reason = "unreadable_or_invalid_bundle"
    return {"ok": False, "mismatches": [reason], "manifest": None, "scope": "selected_run"}
