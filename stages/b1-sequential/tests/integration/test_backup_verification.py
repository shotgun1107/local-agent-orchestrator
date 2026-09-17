"""F12: untrusted backup bundles, tested only in disposable local fixtures."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import subprocess

import pytest

from orchestrator.contract import CORE_VERSION, sha256_bytes, utc_now
from orchestrator.cancel import request_cancel
from orchestrator.cli import main
from orchestrator.ledger import Ledger
from orchestrator.recover import ControllerLock, backup_run, verify_backup
from orchestrator.verify import ArtifactStore
import orchestrator.backup_verify as verifier
import orchestrator.cli as cli_module
from tests.unit.test_ledger import create_run


@pytest.mark.parametrize("kind", ["empty", "text_database"])
def test_incomplete_bundle_is_not_a_verified_backup(tmp_path, kind):
    files = []
    if kind == "text_database":
        payload = b"this is not SQLite"
        (tmp_path / "ledger.sqlite").write_bytes(payload)
        files.append({"path": "ledger.sqlite", "sha256": sha256_bytes(payload)})
    manifest = {"schema_version": 1, "run_id": "run_" + "1" * 32,
                "core_version": CORE_VERSION, "created_at": utc_now(), "files": files}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert verify_backup(tmp_path)["ok"] is False


@pytest.fixture
def bundle(tmp_path):
    state = tmp_path / "source"
    with ControllerLock(state), Ledger(state / "ledger.sqlite") as ledger:
        first, task = create_run(ledger)
        other, other_task = create_run(ledger)
        store = ArtifactStore(state)
        for run, name in ((first, "selected.txt"), (other, "other.txt")):
            metadata = store.write_text(name, "fixture " + name)
            ledger.register_artifact({**metadata, "run_id": run["run_id"], "kind": "project_file", "producer": "user"})
        backup = backup_run(ledger, state, first["run_id"])
    return backup, first["run_id"], other["run_id"], task["task_id"], other_task["task_id"]


def read_manifest(root):
    return json.loads((root / "manifest.json").read_text(encoding="utf-8"))


def write_manifest(root, value):
    (root / "manifest.json").write_text(json.dumps(value), encoding="utf-8")


def rehash_db(root):
    value = read_manifest(root)
    for entry in value["files"]:
        if entry["path"] == "ledger.sqlite":
            entry["sha256"] = sha256_bytes((root / "ledger.sqlite").read_bytes())
    write_manifest(root, value)


def edit_database(root, query, parameters=()):
    # Intentional corruption of THIS synthetic copy only; production verifier never does this.
    connection = sqlite3.connect(root / "ledger.sqlite")
    try:
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.execute(query, parameters)
        connection.commit()
    finally:
        connection.close()
    rehash_db(root)


def file_snapshot(root):
    return {path.relative_to(root).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
            for path in root.rglob("*") if path.is_file()}


def test_valid_selected_run_is_read_only_and_never_opens_sqlite_on_disk(bundle, monkeypatch):
    root, run_id, *_ = bundle
    before = file_snapshot(root)
    connect = sqlite3.connect
    connections = []
    def memory_only(database, *args, **kwargs):
        assert database == ":memory:", "verifier opened a disk database"
        result = connect(database, *args, **kwargs)
        connections.append(result)
        return result
    monkeypatch.setattr(sqlite3, "connect", memory_only)
    result = verify_backup(root, expected_run_id=run_id)
    assert result["ok"] and result["scope"] == "selected_run"
    assert result["verified_files"] == 2
    assert len(connections) == 2
    assert file_snapshot(root) == before
    assert not (root / "ledger.sqlite-wal").exists()
    assert not (root / "ledger.sqlite-shm").exists()
    assert not (root / "artifacts/other.txt").exists()  # DB contains other Runs; payload scope does not.


@pytest.mark.parametrize("case", ["version", "boolean_version", "core", "run", "timestamp", "unknown_field", "missing_field", "files_type", "duplicate", "alias", "hash", "file_field", "missing_database", "omitted_artifact", "extra_listed", "wrong_hash"])
def test_manifest_corruption_is_rejected(bundle, case):
    root, run_id, other_id, *_ = bundle
    value = read_manifest(root)
    if case == "version": value["schema_version"] = 2
    elif case == "boolean_version": value["schema_version"] = True
    elif case == "core": value["core_version"] = "unsupported"
    elif case == "run": value["run_id"] = other_id
    elif case == "timestamp": value["created_at"] = "2026-09-17"
    elif case == "unknown_field": value["untrusted"] = "not-a-setting"
    elif case == "missing_field": del value["core_version"]
    elif case == "files_type": value["files"] = {}
    elif case == "duplicate": value["files"].append(dict(value["files"][0]))
    elif case == "alias": value["files"].append({**value["files"][0], "path": "LEDGER.SQLITE"})
    elif case == "hash": value["files"][0]["sha256"] = "not-a-hash"
    elif case == "file_field": value["files"][0]["extra"] = True
    elif case == "missing_database": value["files"] = value["files"][1:]
    elif case == "omitted_artifact":
        value["files"] = [entry for entry in value["files"] if entry["path"] == "ledger.sqlite"]
        (root / "artifacts/selected.txt").unlink()
        (root / "artifacts").rmdir()
    elif case == "extra_listed":
        (root / "extra.txt").write_bytes(b"extra")
        value["files"].append({"path": "extra.txt", "sha256": sha256_bytes(b"extra")})
    else: value["files"][0]["sha256"] = "0" * 64
    write_manifest(root, value)
    result = verify_backup(root)
    assert result["ok"] is False, case
    assert result["manifest"] is None


@pytest.mark.parametrize("path", ["../sentinel.txt", "/sentinel.txt", "C:/sentinel.txt", "C:sentinel.txt", "\\\\server\\share\\file", "artifacts/../sentinel.txt", "artifacts//selected.txt", "artifacts/./selected.txt", "artifacts/selected.txt:stream", "artifacts/selected.txt.", "artifacts/selected.txt ", "artifacts/NUL", "artifacts/COM1.txt", "artifacts/line\nname"])
def test_unsafe_manifest_path_is_never_opened(bundle, monkeypatch, path):
    root, *_ = bundle
    value = read_manifest(root)
    value["files"][1]["path"] = path
    write_manifest(root, value)
    original = Path.open
    opened = []
    def checked(self, *args, **kwargs):
        opened.append(self)
        assert self == root / "manifest.json", "payload was opened before all manifest paths were checked"
        return original(self, *args, **kwargs)
    monkeypatch.setattr(Path, "open", checked)
    assert verify_backup(root)["ok"] is False
    assert opened == [root / "manifest.json"]


@pytest.mark.parametrize("payload", ['{"schema_version":1,"schema_version":1}', '{"files":NaN}', '{', '[]', '[' * 2000 + '0' + ']' * 2000], ids=["duplicate_keys", "nonfinite", "truncated", "wrong_root", "deeply_nested"])
def test_invalid_json_is_rejected_without_traceback(bundle, payload):
    root, *_ = bundle
    (root / "manifest.json").write_text(payload, encoding="utf-8")
    assert verify_backup(root)["ok"] is False


@pytest.mark.parametrize("case", ["migration", "schema_missing", "schema_extra", "schema_view", "schema_trigger", "foreign_key", "run_core", "run_state", "artifact_size", "artifact_hash", "artifact_path", "cross_run_artifact", "event_reference"])
def test_database_must_match_frozen_schema_run_and_artifacts(bundle, case):
    root, run_id, other_id, task_id, other_task_id = bundle
    statements = {
        "migration": ("UPDATE schema_migrations SET checksum=?", ("0" * 64,)),
        "schema_missing": ("DROP TABLE decisions", ()),
        "schema_extra": ("CREATE TABLE extra(value TEXT)", ()),
        "schema_view": ("CREATE VIEW extra AS SELECT 1 AS value", ()),
        "schema_trigger": ("CREATE TRIGGER extra AFTER INSERT ON runs BEGIN SELECT 1; END", ()),
        "foreign_key": ("UPDATE artifacts SET run_id='missing' WHERE run_id=?", (run_id,)),
        "run_core": ("UPDATE runs SET core_version='different' WHERE run_id=?", (run_id,)),
        "run_state": ("UPDATE runs SET state='NOT_A_STATE' WHERE run_id=?", (run_id,)),
        "artifact_size": ("UPDATE artifacts SET size_bytes=size_bytes+1 WHERE run_id=?", (run_id,)),
        "artifact_hash": ("UPDATE artifacts SET sha256=? WHERE run_id=?", ("0" * 64, run_id)),
        "artifact_path": ("UPDATE artifacts SET relative_path='../escape' WHERE run_id=?", (run_id,)),
        "cross_run_artifact": ("UPDATE artifacts SET task_id=? WHERE run_id=?", (other_task_id, run_id)),
        "event_reference": ("UPDATE events SET aggregate_id='missing' WHERE aggregate_type='run'", ()),
    }
    edit_database(root, *statements[case])
    assert verify_backup(root)["ok"] is False, case


@pytest.mark.parametrize("case", ["missing", "modified", "extra", "wal", "directory", "manifest_missing", "truncated_db"])
def test_physical_bundle_corruption_is_rejected(bundle, case):
    root, *_ = bundle
    if case == "missing": (root / "artifacts/selected.txt").unlink()
    elif case == "modified": (root / "artifacts/selected.txt").write_bytes(b"changed")
    elif case == "extra": (root / "unlisted.txt").write_bytes(b"extra")
    elif case == "wal": (root / "ledger.sqlite-wal").write_bytes(b"")
    elif case == "directory": (root / "unlisted").mkdir()
    elif case == "manifest_missing": (root / "manifest.json").unlink()
    else:
        (root / "ledger.sqlite").write_bytes((root / "ledger.sqlite").read_bytes()[:100])
        rehash_db(root)
    assert verify_backup(root)["ok"] is False


def test_external_run_pin_and_cli_exit_codes(bundle, capsys):
    root, run_id, other_id, *_ = bundle
    assert main(["recover", "verify-backup", str(root), "--expected-run-id", run_id]) == 0
    assert json.loads(capsys.readouterr().out)["ok"]
    assert main(["recover", "verify-backup", str(root), "--expected-run-id", other_id]) == 5
    assert json.loads(capsys.readouterr().out)["mismatches"] == ["unexpected_run"]
    (root / "manifest.json").write_text('{"untrusted":"must-not-be-echoed"}', encoding="utf-8")
    assert main(["recover", "verify-backup", str(root)]) == 5
    output = capsys.readouterr()
    assert "must-not-be-echoed" not in output.out + output.err


def test_backup_cli_returns_failure_if_published_bundle_no_longer_verifies(bundle, monkeypatch, capsys):
    root, run_id, *_ = bundle
    state = root.parent.parent
    (root / "artifacts/selected.txt").write_bytes(b"changed after publication")
    monkeypatch.setattr(cli_module, "find_state_root", lambda target: state)
    monkeypatch.setattr(cli_module, "backup_run", lambda *args: root)
    assert main(["recover", "backup", run_id]) == 5
    assert json.loads(capsys.readouterr().out)["verified"] is False


@pytest.mark.parametrize("boundary", ["permission", "replacement", "late_extra"])
def test_read_failure_or_mid_verification_change_is_not_accepted(bundle, monkeypatch, boundary):
    root, *_ = bundle
    original = verifier._read
    count = 0
    def read(*args, **kwargs):
        nonlocal count
        relative = args[1]
        if boundary == "permission" and relative == "ledger.sqlite":
            raise PermissionError("fixture denial must not be echoed")
        result = original(*args, **kwargs)
        if relative == "ledger.sqlite":
            count += 1
            if count == 1 and boundary == "replacement":
                (root / "artifacts/selected.txt").write_bytes(b"replaced")
            if count == 2 and boundary == "late_extra":
                (root / "late.txt").write_bytes(b"late")
        return result
    monkeypatch.setattr(verifier, "_read", read)
    assert verify_backup(root)["ok"] is False


@pytest.mark.parametrize("limit", ["MAX_DB_BYTES", "MAX_MANIFEST_BYTES", "MAX_FILES", "MAX_TOTAL_BYTES"])
def test_resource_limits_fail_closed(bundle, monkeypatch, limit):
    root, *_ = bundle
    monkeypatch.setattr(verifier, limit, 1)
    assert verify_backup(root)["ok"] is False


def test_hard_link_is_rejected(bundle, tmp_path):
    root, *_ = bundle
    original = tmp_path / "external-fixture.txt"
    original.write_bytes(b"fixture selected.txt")
    target = root / "artifacts/selected.txt"
    target.unlink()
    os.link(original, target)
    assert verify_backup(root)["mismatches"] == ["hard_link"]


@pytest.mark.skipif(os.name != "nt", reason="Windows junction boundary")
def test_junction_is_rejected_without_reading_target(bundle, tmp_path, monkeypatch):
    root, *_ = bundle
    external = tmp_path / "external-fixture"
    external.mkdir()
    original = external / "selected.txt"
    original.write_bytes(b"fixture selected.txt")
    (root / "artifacts/selected.txt").unlink()
    (root / "artifacts").rmdir()
    result = subprocess.run(["powershell", "-NoProfile", "-Command",
        "$ErrorActionPreference='Stop'; New-Item -ItemType Junction -Path $env:LAO_TEST_LINK_PATH -Target $env:LAO_TEST_LINK_TARGET | Out-Null"],
        env={**os.environ, "LAO_TEST_LINK_PATH": str(root / "artifacts"), "LAO_TEST_LINK_TARGET": str(external)},
        capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    read = Path.open
    def checked(self, *args, **kwargs):
        assert self != original and self != root / "artifacts/selected.txt"
        return read(self, *args, **kwargs)
    monkeypatch.setattr(Path, "open", checked)
    assert verify_backup(root)["mismatches"] == ["link_or_reparse"]


@pytest.mark.parametrize("cancelled", [False, True])
def test_legacy_and_cancel_intent_bundles_are_compatible(tmp_path, cancelled):
    state = tmp_path / "state"
    with ControllerLock(state), Ledger(state / "ledger.sqlite") as ledger:
        run, _ = create_run(ledger)
        if cancelled:
            request_cancel(state, run["run_id"])
            from orchestrator.cancel import apply_cancel
            apply_cancel(ledger, run["run_id"])
        root = backup_run(ledger, state, run["run_id"])
    assert verify_backup(root)["ok"]
    if cancelled:
        value = read_manifest(root)
        marker = next(entry["path"] for entry in value["files"] if entry["path"].endswith(".request"))
        (root / marker).unlink()
        (root / "cancel-requests").rmdir()
        value["files"] = [entry for entry in value["files"] if entry["path"] != marker]
        write_manifest(root, value)
        assert verify_backup(root)["mismatches"] == ["cancel_intent"]


@pytest.mark.parametrize("run_id", ["../outside", "/outside", "C:/outside", "run/nested", "run:stream"])
def test_generator_rejects_unsafe_run_name_before_allocating_temp(tmp_path, monkeypatch, run_id):
    state = tmp_path / "state"
    state.mkdir()
    import orchestrator.recover as recovery
    def forbidden(*args, **kwargs):
        raise AssertionError("unsafe Run reached temporary directory allocation")
    monkeypatch.setattr(recovery.tempfile, "mkdtemp", forbidden)
    with pytest.raises((ValueError, recovery.IntegrityViolation)):
        backup_run(None, state, run_id)
    assert list(state.iterdir()) == []
