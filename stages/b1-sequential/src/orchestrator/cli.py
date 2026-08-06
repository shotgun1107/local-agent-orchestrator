"""`lao` command-line interface for the B1 reference implementation."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .contract import (
    AttemptState,
    RunState,
    RunStatusEnvelope,
    SessionState,
    TaskState,
    canonical_json,
)
from .ledger import IntegrityViolation, Ledger, LedgerError, StateConflict
from .recover import (
    ControllerLock,
    ControllerLockError,
    backup_run,
    check_integrity,
    force_unlock,
    verify_backup,
)
from .runtime import RuntimeBoundaryError, present_api_key_environment_names
from .schemas import export_public_schemas
from .schedule import (
    ConfigurationError,
    Orchestrator,
    default_runtime_profiles_path,
    load_project,
    load_run_spec,
    read_project_root_from_state,
    read_run_spec_from_state,
    state_root_for,
    validate_run_against_project,
)

EXIT_OK = 0
EXIT_INPUT = 2
EXIT_BLOCKED = 3
EXIT_TASK_FAILED = 4
EXIT_INTEGRITY = 5
EXIT_LOCKED = 6
EXIT_RUNTIME = 7


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lao", description="B1 sequential local-agent orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)

    project = sub.add_parser("project")
    project_sub = project.add_subparsers(dest="project_command", required=True)
    init = project_sub.add_parser("init")
    init.add_argument("path", type=Path)
    init.add_argument("--project-id")

    doctor = sub.add_parser("doctor")
    doctor.add_argument("--project", type=Path, required=True)
    doctor.add_argument("--json", action="store_true")

    run = sub.add_parser("run")
    run_sub = run.add_subparsers(dest="run_command", required=True)
    validate = run_sub.add_parser("validate")
    validate.add_argument("--project", type=Path, required=True)
    validate.add_argument("--spec", type=Path, required=True)
    start = run_sub.add_parser("start")
    start.add_argument("--project", type=Path, required=True)
    start.add_argument("--spec", type=Path, required=True)
    start.add_argument("--runtime", choices=["fake", "codex"], required=True)
    start.add_argument("--fake-scenario", default="complete")
    start.add_argument("--fake-fixture", type=Path)
    resume = run_sub.add_parser("resume")
    resume.add_argument("run_id")
    status = run_sub.add_parser("status")
    status.add_argument("run_id")
    status.add_argument("--json", action="store_true")
    cancel = run_sub.add_parser("cancel")
    cancel.add_argument("run_id")

    decision = sub.add_parser("decision")
    decision_sub = decision.add_subparsers(dest="decision_command", required=True)
    record = decision_sub.add_parser("record")
    record.add_argument("run_id")
    record.add_argument("--file", type=Path, required=True)

    report = sub.add_parser("report")
    report.add_argument("run_id")
    report.add_argument("--format", choices=["json", "md"], required=True)

    schema = sub.add_parser("schema")
    schema_sub = schema.add_subparsers(dest="schema_command", required=True)
    schema_export = schema_sub.add_parser("export")
    schema_export.add_argument("--output", type=Path, required=True)

    recover = sub.add_parser("recover")
    recover_sub = recover.add_subparsers(dest="recover_command", required=True)
    check = recover_sub.add_parser("check")
    check.add_argument("run_id")
    backup = recover_sub.add_parser("backup")
    backup.add_argument("run_id")
    unlock = recover_sub.add_parser("unlock")
    unlock.add_argument("--state-root", type=Path, required=True)
    unlock.add_argument("--confirm-no-controller", action="store_true")
    verify = recover_sub.add_parser("verify-backup")
    verify.add_argument("path", type=Path)
    return parser


def _template_root() -> Path:
    packaged = Path(__file__).resolve().parent / "_project_pack"
    if packaged.is_dir():
        return packaged
    return Path(__file__).resolve().parents[2] / "templates" / "project-pack" / ".orchestrator"


def _project_init(path: Path, project_id: str | None) -> dict[str, Any]:
    path = path.resolve()
    if not path.exists():
        path.mkdir(parents=True)
    pack = path / ".orchestrator"
    if pack.exists():
        raise ConfigurationError(f"Project Pack already exists: {pack}")
    source = _template_root()
    if not source.is_dir():
        raise ConfigurationError(f"bundled Project Pack template missing: {source}")
    shutil.copytree(source, pack)
    if project_id:
        project_file = pack / "project.yaml"
        raw = yaml.safe_load(project_file.read_text(encoding="utf-8"))
        raw["project_id"] = project_id
        project_file.write_text(yaml.safe_dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return {"project_pack": str(pack), "created": True}


def _doctor(project_path: Path) -> dict[str, Any]:
    loaded = load_project(project_path)
    from .verify import GitWorkspace

    workspace = GitWorkspace(loaded.project_root)
    sdk: dict[str, Any]
    try:
        import openai_codex

        sdk = {"installed": True, "version": getattr(openai_codex, "__version__", "unknown"), "pinned": getattr(openai_codex, "__version__", None) == "0.144.4"}
    except ImportError:
        sdk = {"installed": False, "version": None, "pinned": False}
    login: dict[str, Any] = {"checked": False, "authenticated": False, "method": "unknown"}
    present_api_keys = present_api_key_environment_names()
    if sdk["pinned"] and not present_api_keys:
        try:
            from openai_codex import Codex

            with Codex() as codex:
                account_response = codex.account(refresh_token=False)
            account_root = getattr(getattr(account_response, "account", None), "root", None)
            account_type = getattr(account_root, "type", None)
            login = {
                "checked": True,
                "authenticated": account_type is not None,
                "method": account_type or "unknown",
            }
        except Exception as exc:
            login = {
                "checked": True,
                "authenticated": False,
                "method": "unknown",
                "error_kind": type(exc).__name__,
            }
    return {
        "project_id": loaded.pack.project.project_id,
        "project_pack_sha256": loaded.pack.sha256,
        "workspace": workspace.doctor(),
        "worktree": workspace.status(),
        "state_root": str(state_root_for(loaded.pack.project.project_id)),
        "runtime_profiles_path": str(default_runtime_profiles_path()),
        "api_key_present": bool(present_api_keys),
        "codex_sdk": sdk,
        "codex_login": login,
    }


def _candidate_state_roots() -> list[Path]:
    explicit = os.environ.get("LAO_STATE_ROOT")
    if explicit:
        return [Path(explicit).resolve()]
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    projects = base / "local-agent-orchestrator" / "projects"
    return [path.parent for path in projects.glob("*/ledger.sqlite")]


def find_state_root(run_id: str) -> Path:
    for root in _candidate_state_roots():
        database = root / "ledger.sqlite"
        if not database.is_file():
            continue
        connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
        try:
            exists = connection.execute("SELECT 1 FROM runs WHERE run_id=?", (run_id,)).fetchone()
        except sqlite3.Error:
            exists = None
        finally:
            connection.close()
        if exists:
            return root
    raise ConfigurationError(f"Run not found: {run_id}; set LAO_STATE_ROOT when using a custom state root")


def _status(run_id: str) -> dict[str, Any]:
    root = find_state_root(run_id)
    with Ledger(root / "ledger.sqlite") as ledger:
        snapshot = ledger.load_run_snapshot(run_id)
    return RunStatusEnvelope(
        schema_version=1,
        run_id=run_id,
        state=snapshot["run"]["state"],
        turns_used=snapshot["run"]["turns_used"],
        tasks=[
            {
                "key": task["external_key"],
                "state": task["state"],
                "attempts": len(task["attempts"]),
                "active_attempt_id": task["active_attempt_id"],
            }
            for task in snapshot["tasks"]
        ],
        session_usage_statuses=[
            session["usage_status"] for session in snapshot["sessions"]
        ],
    ).model_dump(mode="json")


def _resume(run_id: str) -> dict[str, Any]:
    root = find_state_root(run_id)
    project_root = read_project_root_from_state(root, run_id)
    spec = read_run_spec_from_state(root, run_id)
    with Ledger(root / "ledger.sqlite") as ledger:
        run = ledger.get("run", run_id)
    runtime_kind = "codex" if run["auth_method"] == "chatgpt" else "fake"
    orchestrator = Orchestrator(load_project(project_root), state_root=root, runtime_kind=runtime_kind)
    try:
        orchestrator.resume(run_id, spec)
    finally:
        orchestrator.close()
    return _status(run_id)


def _cancel(run_id: str) -> dict[str, Any]:
    root = find_state_root(run_id)
    with ControllerLock(root):
        with Ledger(root / "ledger.sqlite") as ledger:
            run = ledger.get("run", run_id)
            if run["state"] in {RunState.COMPLETED, RunState.FAILED, RunState.CANCELLED}:
                return {"run_id": run_id, "state": run["state"], "changed": False}
            for attempt in ledger.nonterminal_attempts(run_id):
                task = ledger.get("task", attempt["task_id"])
                if attempt["session_id"]:
                    session = ledger.get("session", attempt["session_id"])
                    if session["state"] == SessionState.RUNNING:
                        ledger.update_session_terminal(
                            session["session_id"], SessionState.UNKNOWN,
                            {"cancel": "runtime could not be reattached safely"}, "unknown", None,
                        )
                if attempt["state"] == AttemptState.DISPATCHING:
                    ledger.finish_attempt(
                        attempt["attempt_id"], AttemptState.DISPATCH_UNCERTAIN, TaskState.CANCELLED,
                        "dispatch_uncertain", {"cancelled": True},
                    )
                elif attempt["state"] == AttemptState.RUNNING:
                    ledger.finish_attempt(
                        attempt["attempt_id"], AttemptState.CANCELLED, TaskState.CANCELLED,
                        None, {"cancelled": True},
                    )
                elif attempt["state"] in {AttemptState.REPORTED, AttemptState.VERIFYING}:
                    ledger.finish_attempt(
                        attempt["attempt_id"], AttemptState.BLOCKED, TaskState.BLOCKED,
                        None, {"cancelled_during_verification": True},
                    )
            for task in ledger.list_tasks(run_id):
                if task["state"] in {TaskState.PENDING, TaskState.READY}:
                    ledger.transition("task", task["task_id"], task["version"], TaskState.CANCELLED, "task_cancelled", {})
            run = ledger.get("run", run_id)
            ledger.record_decision({"run_id": run_id, "kind": "cancel", "actor": "user", "outcome": "recorded"})
            ledger.transition("run", run_id, run["version"], RunState.CANCELLED, "run_cancelled", {})
    return {"run_id": run_id, "state": "CANCELLED", "changed": True}


def _record_decision(run_id: str, path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("kind") not in {"unblock", "recovery", "budget_change", "cancel"}:
        raise ConfigurationError("Decision file requires a supported kind")
    root = find_state_root(run_id)
    with ControllerLock(root):
        with Ledger(root / "ledger.sqlite") as ledger:
            decision = ledger.record_decision({
                "run_id": run_id,
                "task_id": raw.get("task_id"),
                "attempt_id": raw.get("attempt_id"),
                "kind": raw["kind"],
                "actor": "user",
                "outcome": raw.get("outcome", "recorded"),
                "scope": raw.get("scope", {}),
                "evidence": raw.get("evidence", {}),
            })
            run = ledger.get("run", run_id)
            if raw["kind"] == "unblock" and raw.get("outcome") == "approved" and run["state"] == RunState.BLOCKED:
                ledger.transition(
                    "run", run_id, run["version"], RunState.RUNNING, "run_unblocked", {},
                    decision_id=decision["decision_id"],
                )
            return decision


def _print(value: Any, *, as_json: bool = True) -> None:
    if as_json:
        print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))
    else:
        print(value)


def _exit_for_state(state: str) -> int:
    if state == RunState.BLOCKED:
        return EXIT_BLOCKED
    if state == RunState.FAILED:
        return EXIT_TASK_FAILED
    return EXIT_OK


def dispatch(args: argparse.Namespace) -> int:
    if args.command == "project" and args.project_command == "init":
        _print(_project_init(args.path, args.project_id))
        return EXIT_OK
    if args.command == "doctor":
        result = _doctor(args.project)
        _print(result)
        healthy = (
            result["workspace"].get("healthy")
            and result["codex_sdk"]["pinned"]
            and not result["api_key_present"]
            and result["codex_login"]["checked"]
            and result["codex_login"]["authenticated"]
            and result["codex_login"]["method"] == "chatgpt"
        )
        return EXIT_OK if healthy else EXIT_RUNTIME
    if args.command == "run" and args.run_command == "validate":
        loaded = load_project(args.project)
        spec = load_run_spec(args.spec)
        validate_run_against_project(spec, loaded)
        _print({"valid": True, "tasks": len(spec.tasks), "project_pack_sha256": loaded.pack.sha256})
        return EXIT_OK
    if args.command == "run" and args.run_command == "start":
        loaded = load_project(args.project)
        original = args.spec.read_text(encoding="utf-8")
        spec = load_run_spec(args.spec)
        fixture = None
        if args.fake_fixture:
            fixture = json.loads(args.fake_fixture.read_text(encoding="utf-8"))
        orchestrator = Orchestrator(
            loaded,
            runtime_kind=args.runtime,
            fake_scenario=args.fake_scenario,
            fake_fixture=fixture,
        )
        try:
            run_id = orchestrator.start(spec, original_spec=original)
        finally:
            orchestrator.close()
        result = _status(run_id)
        _print(result)
        return _exit_for_state(result["state"])
    if args.command == "run" and args.run_command == "resume":
        result = _resume(args.run_id)
        _print(result)
        return _exit_for_state(result["state"])
    if args.command == "run" and args.run_command == "status":
        result = _status(args.run_id)
        if args.json:
            _print(result)
        else:
            print(f"{result['run_id']} {result['state']} turns={result['turns_used']}")
            for task in result["tasks"]:
                print(f"  {task['key']}: {task['state']} attempts={task['attempts']}")
        return _exit_for_state(result["state"])
    if args.command == "run" and args.run_command == "cancel":
        _print(_cancel(args.run_id))
        return EXIT_OK
    if args.command == "decision" and args.decision_command == "record":
        _print(_record_decision(args.run_id, args.file))
        return EXIT_OK
    if args.command == "report":
        root = find_state_root(args.run_id)
        path = root / "runs" / args.run_id / "report" / f"summary.{args.format}"
        if not path.is_file():
            raise IntegrityViolation(f"report Artifact missing: {path}")
        print(path.read_text(encoding="utf-8"), end="")
        return EXIT_OK
    if args.command == "schema" and args.schema_command == "export":
        _print(export_public_schemas(args.output))
        return EXIT_OK
    if args.command == "recover" and args.recover_command == "unlock":
        force_unlock(args.state_root, confirmed=args.confirm_no_controller)
        _print({"unlocked": True, "state_root": str(args.state_root.resolve())})
        return EXIT_OK
    if args.command == "recover" and args.recover_command == "verify-backup":
        result = verify_backup(args.path)
        _print(result)
        return EXIT_OK if result["ok"] else EXIT_INTEGRITY
    if args.command == "recover" and args.recover_command in {"check", "backup"}:
        root = find_state_root(args.run_id)
        with ControllerLock(root):
            with Ledger(root / "ledger.sqlite") as ledger:
                if args.recover_command == "check":
                    result = check_integrity(ledger, root, args.run_id)
                    _print(result)
                    return EXIT_OK if result["ok"] else EXIT_INTEGRITY
                destination = backup_run(ledger, root, args.run_id)
                _print({"backup": str(destination), "verified": verify_backup(destination)["ok"]})
                return EXIT_OK
    raise ConfigurationError("unhandled command")


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    try:
        return dispatch(parser.parse_args(argv))
    except ControllerLockError as exc:
        print(f"controller lock: {exc}", file=sys.stderr)
        return EXIT_LOCKED
    except (ConfigurationError, ValidationError, yaml.YAMLError, FileNotFoundError, ValueError) as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return EXIT_INPUT
    except RuntimeBoundaryError as exc:
        print(f"runtime error: {exc}", file=sys.stderr)
        return EXIT_RUNTIME
    except (IntegrityViolation, LedgerError, sqlite3.Error) as exc:
        print(f"integrity error: {exc}", file=sys.stderr)
        return EXIT_INTEGRITY
    except KeyboardInterrupt:
        print("cancelled by user", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
