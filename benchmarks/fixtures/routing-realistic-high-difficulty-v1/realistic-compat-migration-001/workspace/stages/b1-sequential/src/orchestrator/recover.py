"""Single-controller locking, startup reconciliation, integrity checks, and backup."""

from __future__ import annotations

import json
import os
import shutil
import socket
import tempfile
from pathlib import Path
from typing import Any

from .contract import AttemptState, CORE_VERSION, RunState, SessionState, TaskState, canonical_json, sha256_bytes, utc_now
from .ledger import Ledger
from .verify import ArtifactStore, scan_state_for_secrets


class ControllerLockError(RuntimeError):
    pass


class ControllerLock:
    def __init__(self, state_root: Path):
        self.path = Path(state_root) / "controller.lock"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle: Any = None

    def acquire(self) -> "ControllerLock":
        self._handle = self.path.open("a+b")
        if self.path.stat().st_size == 0:
            self._handle.write(b"\0")
            self._handle.flush()
        self._handle.seek(0)
        try:
            owner = self._handle.read().decode("utf-8", errors="replace").strip("\0")
        except OSError:
            owner = ""
        self._handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self._handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self._handle.close()
            self._handle = None
            raise ControllerLockError(owner or "another controller owns the lock") from exc
        metadata = canonical_json({
            "pid": os.getpid(),
            "hostname": socket.gethostname(),
            "started_at": utc_now(),
            "core_version": CORE_VERSION,
        }).encode("utf-8")
        self._handle.seek(0)
        self._handle.truncate()
        self._handle.write(metadata)
        self._handle.flush()
        os.fsync(self._handle.fileno())
        self._handle.seek(0)
        return self

    def release(self) -> None:
        if self._handle is None:
            return
        self._handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        self._handle.close()
        self._handle = None

    def __enter__(self) -> "ControllerLock":
        return self.acquire()

    def __exit__(self, *_: object) -> None:
        self.release()


def force_unlock(state_root: Path, *, confirmed: bool) -> None:
    if not confirmed:
        raise ControllerLockError("--confirm-no-controller is required")
    lock = ControllerLock(state_root)
    lock.acquire()
    try:
        lock._handle.seek(0)
        lock._handle.truncate()
        lock._handle.write(b"\0")
        lock._handle.flush()
    finally:
        lock.release()


def reconcile(ledger: Ledger, run_id: str, store: ArtifactStore) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    run = ledger.get("run", run_id)
    for attempt in ledger.nonterminal_attempts(run_id):
        task = ledger.get("task", attempt["task_id"])
        session = ledger.get("session", attempt["session_id"]) if attempt["session_id"] else None
        if attempt["state"] == AttemptState.DISPATCHING and session is None:
            ledger.finish_attempt(
                attempt["attempt_id"], AttemptState.DISPATCH_UNCERTAIN, TaskState.BLOCKED,
                "dispatch_uncertain", {"reconcile": "runtime identifier missing"},
            )
            actions.append({"attempt_id": attempt["attempt_id"], "action": "dispatch_uncertain"})
        elif attempt["state"] == AttemptState.RUNNING:
            if session is not None:
                ledger.update_session_terminal(
                    session["session_id"], SessionState.UNKNOWN,
                    {"reconcile": "live runtime cannot be proven after controller restart"},
                    "unknown", None,
                )
            ledger.finish_attempt(
                attempt["attempt_id"], AttemptState.QUARANTINED, TaskState.BLOCKED,
                "terminal_unknown", {"reconcile": "runtime state unknown"},
            )
            actions.append({"attempt_id": attempt["attempt_id"], "action": "quarantined"})
        elif attempt["state"] in {AttemptState.REPORTED, AttemptState.VERIFYING}:
            artifacts = ledger.connection.execute(
                "SELECT relative_path, sha256 FROM artifacts WHERE attempt_id=?",
                (attempt["attempt_id"],),
            ).fetchall()
            corrupt = [row["relative_path"] for row in artifacts if not store.verify(row["relative_path"], row["sha256"])]
            if corrupt:
                target = TaskState.BLOCKED
                attempt_target = AttemptState.BLOCKED
                ledger.finish_attempt(
                    attempt["attempt_id"], attempt_target, target, "artifact_corrupt",
                    {"corrupt_artifacts": corrupt},
                )
                actions.append({"attempt_id": attempt["attempt_id"], "action": "blocked_artifact_corrupt"})
            else:
                actions.append({"attempt_id": attempt["attempt_id"], "action": "verification_pending"})
        else:
            actions.append({"attempt_id": attempt["attempt_id"], "action": "manual_review"})
    if any(action["action"] in {"dispatch_uncertain", "quarantined", "blocked_artifact_corrupt"} for action in actions):
        run = ledger.get("run", run_id)
        if run["state"] in {RunState.READY, RunState.RUNNING, RunState.VERIFYING}:
            ledger.transition("run", run_id, run["version"], RunState.BLOCKED, "run_blocked_by_reconcile", {"actions": actions})
    return actions


def check_integrity(ledger: Ledger, state_root: Path, run_id: str | None = None) -> dict[str, Any]:
    ledger.verify_migrations()
    foreign_keys = ledger.foreign_key_violations()
    quick_check = ledger.quick_check()
    parameters: tuple[Any, ...] = ()
    where = ""
    if run_id:
        where = " WHERE run_id=?"
        parameters = (run_id,)
    artifacts = ledger.connection.execute(
        "SELECT relative_path, sha256 FROM artifacts" + where, parameters
    ).fetchall()
    store = ArtifactStore(state_root)
    corrupt = [row["relative_path"] for row in artifacts if not store.verify(row["relative_path"], row["sha256"])]
    secrets = scan_state_for_secrets(state_root)
    return {
        "ok": quick_check == "ok" and not foreign_keys and not corrupt and not secrets,
        "quick_check": quick_check,
        "foreign_key_violations": foreign_keys,
        "corrupt_artifacts": corrupt,
        "secret_findings": secrets,
    }


def backup_run(ledger: Ledger, state_root: Path, run_id: str) -> Path:
    state_root = Path(state_root).resolve()
    ledger.get("run", run_id)
    backup_root = state_root / "backups"
    backup_root.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{run_id}-", dir=backup_root))
    destination = backup_root / f"{run_id}-{utc_now().replace(':', '').replace('-', '')}"
    try:
        database = temporary / "ledger.sqlite"
        ledger.sqlite_backup(database)
        copied: list[dict[str, Any]] = []
        for row in ledger.connection.execute(
            "SELECT relative_path, sha256 FROM artifacts WHERE run_id=? ORDER BY relative_path", (run_id,)
        ).fetchall():
            source = (state_root / PurePath(row["relative_path"])).resolve()
            if state_root not in source.parents or not source.is_file():
                raise RuntimeError(f"missing or unsafe Artifact during backup: {row['relative_path']}")
            target = temporary / "artifacts" / PurePath(row["relative_path"])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            actual = sha256_bytes(target.read_bytes())
            if actual != row["sha256"]:
                raise RuntimeError(f"Artifact hash mismatch during backup: {row['relative_path']}")
            copied.append({"path": f"artifacts/{row['relative_path']}", "sha256": actual})
        files = [{"path": "ledger.sqlite", "sha256": sha256_bytes(database.read_bytes())}, *copied]
        manifest = {
            "schema_version": 1,
            "run_id": run_id,
            "core_version": CORE_VERSION,
            "created_at": utc_now(),
            "files": files,
        }
        (temporary / "manifest.json").write_text(canonical_json(manifest) + "\n", encoding="utf-8")
        os.replace(temporary, destination)
        return destination
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def verify_backup(path: Path) -> dict[str, Any]:
    path = Path(path)
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    mismatches = []
    for item in manifest["files"]:
        target = path / item["path"]
        if not target.is_file() or sha256_bytes(target.read_bytes()) != item["sha256"]:
            mismatches.append(item["path"])
    return {"ok": not mismatches, "mismatches": mismatches, "manifest": manifest}


def PurePath(value: str) -> Path:
    parts = value.replace("\\", "/").split("/")
    if ".." in parts or any(not part for part in parts):
        raise RuntimeError("unsafe Artifact path")
    return Path(*parts)
