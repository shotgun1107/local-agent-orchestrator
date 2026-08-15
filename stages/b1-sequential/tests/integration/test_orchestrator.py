from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pytest
import yaml

from orchestrator.ledger import Ledger
from orchestrator.recover import ControllerLock, ControllerLockError, backup_run, check_integrity, verify_backup
from orchestrator.runtime import FakeRuntime
from orchestrator.schedule import ConfigurationError, Orchestrator, load_project
from tests.conftest import git, make_spec


PROFILE_R_PUBLIC_CHECK = (
    Path(__file__).resolve().parents[4]
    / "benchmarks/fixtures/routing-realistic-high-difficulty-v1/"
    "realistic-compat-migration-001/workspace/benchmark_checks/check_profile_r.py"
)


def execute(root: Path, state: Path, spec, *, scenario="complete", fixture=None):
    orchestrator = Orchestrator(
        load_project(root), state_root=state,
        check_temp_root=state.parent / f"{state.name}-check-temp",
        runtime_kind="fake",
        fake_scenario=scenario, fake_fixture=fixture,
    )
    try:
        run_id = orchestrator.start(spec)
    finally:
        orchestrator.close()
    with Ledger(state / "ledger.sqlite") as ledger:
        snapshot = ledger.load_run_snapshot(run_id)
    return run_id, snapshot


def test_read_only_run_completes_and_report_is_deterministic(tmp_path: Path, project_factory) -> None:
    root = project_factory()
    state = tmp_path / "state"
    run_id, snapshot = execute(root, state, make_spec())
    assert snapshot["run"]["state"] == "COMPLETED"
    assert snapshot["tasks"][0]["state"] == "SUCCEEDED"
    assert snapshot["checks"][0]["state"] == "PASSED"
    report = json.loads((state / "runs" / run_id / "report" / "summary.json").read_text(encoding="utf-8"))
    assert report["state"] == "COMPLETED"
    assert report["metrics"]["attempts"] == 1
    assert report["metrics"]["checks_failed"] == 0
    assert report["metrics"]["checks_passed"] == 1
    assert report["metrics"]["sessions"] == 1
    assert report["metrics"]["token_usage"] == {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}


def test_shared_write_is_verified_and_two_tasks_are_sequential(tmp_path: Path, project_factory) -> None:
    root = project_factory()
    spec = make_spec(workspace_mode="shared_serial_write", write_scope=["src/**"], tasks=2)
    fixture = {
        "effects": [{"type": "write_file", "path": "src/generated.txt", "content": "generated\n"}],
    }
    _, snapshot = execute(root, tmp_path / "state", spec, fixture=fixture)
    assert [task["state"] for task in snapshot["tasks"]] == ["SUCCEEDED", "SUCCEEDED"]
    assert all(task["active_attempt_id"] is None for task in snapshot["tasks"])
    assert (root / "src" / "generated.txt").read_text(encoding="utf-8") == "generated\n"


def test_run_level_turn_override_blocks_before_dispatching_past_budget(
    tmp_path: Path, project_factory
) -> None:
    root = project_factory()
    state = tmp_path / "state"
    orchestrator = Orchestrator(
        load_project(root),
        state_root=state,
        check_temp_root=tmp_path / "check-temp",
        runtime_kind="fake",
        max_turns_override=1,
    )
    try:
        run_id = orchestrator.start(make_spec(tasks=2))
    finally:
        orchestrator.close()
    with Ledger(state / "ledger.sqlite") as ledger:
        snapshot = ledger.load_run_snapshot(run_id)
    assert snapshot["run"]["state"] == "BLOCKED"
    assert snapshot["run"]["turns_used"] == 1
    assert [task["state"] for task in snapshot["tasks"]] == ["SUCCEEDED", "READY"]


def test_worker_completed_claim_cannot_override_failed_check(tmp_path: Path, project_factory) -> None:
    root = project_factory(check_fails=True)
    _, snapshot = execute(root, tmp_path / "state", make_spec())
    assert snapshot["run"]["state"] == "FAILED"
    assert snapshot["tasks"][0]["state"] == "FAILED"
    assert len(snapshot["tasks"][0]["attempts"]) == 1
    assert all(
        attempt["failure_kind"] == "check_unknown"
        for attempt in snapshot["tasks"][0]["attempts"]
    )


def test_retry_prompt_receives_only_explicit_public_check_feedback(
    tmp_path: Path,
    project_factory,
) -> None:
    root = project_factory()
    checks_path = root / ".orchestrator" / "checks.yaml"
    checks = yaml.safe_load(checks_path.read_text(encoding="utf-8"))
    checks["checks"]["test_check"]["argv"] = [
        "python",
        "-c",
        (
            "print('CHECK_FAILURE_CLASS:PRODUCT_ASSERTION'); "
            "print('unmarked private diagnostic'); "
            "print('WORKER_FEEDBACK:rerun the public regression and fix its strict input'); "
            "print('WORKER_FEEDBACK:Traceback (most recent call last):'); "
            "print('WORKER_FEEDBACK:    File public_test.py, line 42'); "
            "print('WORKER_FEEDBACK:ValueError: missing public field'); "
            "raise SystemExit(1)"
        ),
    ]
    checks_path.write_text(
        yaml.safe_dump(checks, sort_keys=False),
        encoding="utf-8",
    )
    git(root, "add", ".orchestrator/checks.yaml")
    git(root, "commit", "-m", "exercise public retry feedback")
    runtime = FakeRuntime()
    orchestrator = Orchestrator(
        load_project(root),
        state_root=tmp_path / "state",
        check_temp_root=tmp_path / "check-temp",
        runtime_port=runtime,
        runtime_profile_override={"runtime": "fake"},
        auth_method_override="none",
    )
    try:
        run_id = orchestrator.start(make_spec())
    finally:
        orchestrator.close()

    assert runtime.initial_feedbacks[0] is None
    assert runtime.initial_feedbacks[1] == {
        "failure": "checks",
        "check_name": "test_check",
        "exit_code": 1,
        "public_feedback": [
            "rerun the public regression and fix its strict input",
            "Traceback (most recent call last):",
            "    File public_test.py, line 42",
            "ValueError: missing public field",
        ],
        "public_feedback_truncated": False,
        "public_feedback_bytes": sum(
            len(message.encode("utf-8"))
            for message in (
                "rerun the public regression and fix its strict input",
                "Traceback (most recent call last):",
                "    File public_test.py, line 42",
                "ValueError: missing public field",
            )
        ),
        "allowed_write_scope": [],
        "remaining_completion_criteria": ["Check passes"],
    }
    assert "private diagnostic" not in json.dumps(
        runtime.initial_feedbacks,
        ensure_ascii=False,
    )
    with Ledger(tmp_path / "state" / "ledger.sqlite") as ledger:
        snapshot = ledger.load_run_snapshot(run_id)
    assert snapshot["run"]["state"] == "FAILED"


def test_check_process_error_is_environment_failure_and_never_retries(
    tmp_path: Path,
    project_factory,
) -> None:
    root = project_factory()
    checks_path = root / ".orchestrator" / "checks.yaml"
    checks = yaml.safe_load(checks_path.read_text(encoding="utf-8"))
    checks["checks"]["test_check"]["argv"] = ["missing-check-command-for-test.exe"]
    checks_path.write_text(
        yaml.safe_dump(checks, sort_keys=False),
        encoding="utf-8",
    )
    git(root, "add", ".orchestrator/checks.yaml")
    git(root, "commit", "-m", "exercise environment failure")

    _, snapshot = execute(root, tmp_path / "state", make_spec())

    attempts = snapshot["tasks"][0]["attempts"]
    assert len(attempts) == 1
    assert attempts[0]["failure_kind"] == "check_environment"
    assert snapshot["checks"][0]["state"] == "ERROR"


def test_environment_diagnostic_is_preserved_as_verifier_evidence(
    tmp_path: Path,
    project_factory,
) -> None:
    root = project_factory()
    checks_path = root / ".orchestrator" / "checks.yaml"
    checks = yaml.safe_load(checks_path.read_text(encoding="utf-8"))
    diagnostic = {
        "command_ordinal": 1,
        "path_lengths": {
            "deepest_observed": 209,
            "git_config": 263,
            "growth_target": 261,
            "probe_file": 261,
            "probe_relative": 204,
            "probe_repository": 251,
            "temp_root": 123,
        },
        "return_code": 128,
        "safe_error_code": "GIT_INIT_FAILED_PATH_LIMIT",
        "schema_version": 1,
        "stage": "r07_path_growth_git",
        "stderr_sha256": "a" * 64,
    }
    encoded = json.dumps(
        diagnostic,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    checks["checks"]["test_check"]["argv"] = [
        sys.executable,
        "-c",
        (
            "print('CHECK_FAILURE_CLASS:ENVIRONMENT'); "
            f"print('CHECK_ENVIRONMENT_DIAGNOSTIC:{encoded}'); "
            "raise SystemExit(1)"
        ),
    ]
    checks_path.write_text(
        yaml.safe_dump(checks, sort_keys=False),
        encoding="utf-8",
    )
    git(root, "add", ".orchestrator/checks.yaml")
    git(root, "commit", "-m", "exercise environment diagnostic evidence")

    state = tmp_path / "state"
    _, snapshot = execute(root, state, make_spec())

    attempts = snapshot["tasks"][0]["attempts"]
    assert len(attempts) == 1
    assert attempts[0]["failure_kind"] == "check_environment"
    artifacts = [
        artifact
        for artifact in snapshot["artifacts"]
        if artifact["kind"] == "check_result"
        and artifact["relative_path"].endswith("/environment-diagnostic.json")
    ]
    assert len(artifacts) == 1
    diagnostic_path = state / artifacts[0]["relative_path"]
    assert json.loads(diagnostic_path.read_text(encoding="utf-8")) == diagnostic


def test_public_checker_permission_error_is_environment_failure_and_never_retries(
    tmp_path: Path,
    project_factory,
) -> None:
    root = project_factory()
    checks_path = root / ".orchestrator" / "checks.yaml"
    checks = yaml.safe_load(checks_path.read_text(encoding="utf-8"))
    injected_check = "\n".join(
        (
            "import importlib.util, pathlib, sys",
            "path = pathlib.Path(sys.argv[1])",
            "spec = importlib.util.spec_from_file_location('profile_r_public_check', path)",
            "module = importlib.util.module_from_spec(spec)",
            "spec.loader.exec_module(module)",
            "original = pathlib.Path.read_text",
            "def denied(self, *args, **kwargs):",
            "    if self.suffix == '.json':",
            "        raise PermissionError('injected public input denial')",
            "    return original(self, *args, **kwargs)",
            "pathlib.Path.read_text = denied",
            "raise SystemExit(module.main(['check_profile_r.py', 'R01']))",
        )
    )
    checks["checks"]["test_check"]["argv"] = [
        sys.executable,
        "-c",
        injected_check,
        str(PROFILE_R_PUBLIC_CHECK),
    ]
    checks_path.write_text(
        yaml.safe_dump(checks, sort_keys=False),
        encoding="utf-8",
    )
    git(root, "add", ".orchestrator/checks.yaml")
    git(root, "commit", "-m", "exercise public input permission failure")

    runtime = FakeRuntime()
    state = tmp_path / "state"
    orchestrator = Orchestrator(
        load_project(root),
        state_root=state,
        check_temp_root=tmp_path / "check-temp",
        runtime_port=runtime,
        runtime_profile_override={"runtime": "fake"},
        auth_method_override="none",
    )
    try:
        run_id = orchestrator.start(make_spec())
    finally:
        orchestrator.close()

    with Ledger(state / "ledger.sqlite") as ledger:
        snapshot = ledger.load_run_snapshot(run_id)
    attempts = snapshot["tasks"][0]["attempts"]
    assert len(attempts) == 1
    assert attempts[0]["failure_kind"] == "check_environment"
    assert len(runtime.initial_feedbacks) == 1
    assert snapshot["checks"][0]["state"] == "FAILED"


def test_public_checker_import_permission_error_stops_before_retry_or_next_task(
    tmp_path: Path,
    project_factory,
) -> None:
    root = project_factory()
    checks_path = root / ".orchestrator" / "checks.yaml"
    checks = yaml.safe_load(checks_path.read_text(encoding="utf-8"))
    injected_check = "\n".join(
        (
            "import importlib.util, pathlib, sys",
            "path = pathlib.Path(sys.argv[1])",
            "spec = importlib.util.spec_from_file_location('profile_r_public_check', path)",
            "module = importlib.util.module_from_spec(spec)",
            "spec.loader.exec_module(module)",
            "original = module.importlib.import_module",
            "def denied(name, *args, **kwargs):",
            "    if name.startswith('benchmark_runner.'):",
            "        raise PermissionError('injected public module import denial')",
            "    return original(name, *args, **kwargs)",
            "module.importlib.import_module = denied",
            "module.CHECKS['R02'] = lambda: module._import_runner_module('routing_suite')",
            "raise SystemExit(module.main(['check_profile_r.py', 'R02']))",
        )
    )
    checks["checks"]["test_check"]["argv"] = [
        sys.executable,
        "-c",
        injected_check,
        str(PROFILE_R_PUBLIC_CHECK),
    ]
    checks_path.write_text(
        yaml.safe_dump(checks, sort_keys=False),
        encoding="utf-8",
    )
    git(root, "add", ".orchestrator/checks.yaml")
    git(root, "commit", "-m", "exercise public module import permission failure")

    runtime = FakeRuntime()
    state = tmp_path / "state"
    orchestrator = Orchestrator(
        load_project(root),
        state_root=state,
        check_temp_root=tmp_path / "check-temp",
        runtime_port=runtime,
        runtime_profile_override={"runtime": "fake"},
        auth_method_override="none",
    )
    try:
        run_id = orchestrator.start(make_spec(tasks=2))
    finally:
        orchestrator.close()

    with Ledger(state / "ledger.sqlite") as ledger:
        snapshot = ledger.load_run_snapshot(run_id)
    first_attempts = snapshot["tasks"][0]["attempts"]
    assert len(first_attempts) == 1
    assert first_attempts[0]["failure_kind"] == "check_environment"
    assert snapshot["checks"][0]["state"] == "FAILED"
    assert snapshot["tasks"][1]["attempts"] == []
    assert runtime.turn_count == 1
    assert len(runtime.initial_feedbacks) == 1


@pytest.mark.parametrize(
    ("detached_output", "leader_exits_early"),
    ((False, True), (True, False)),
    ids=("leader-exits-with-inherited-pipes", "detached-output-holds-temp-lock"),
)
def test_outer_check_timeout_reaps_nested_child_and_never_retries(
    tmp_path: Path,
    project_factory,
    detached_output: bool,
    leader_exits_early: bool,
) -> None:
    root = project_factory()
    child_pid_path = tmp_path / "nested-child.pid"
    child_code = (
        "import os,pathlib,time;"
        f"pathlib.Path({str(child_pid_path)!r}).write_text(str(os.getpid()),encoding='ascii');"
        "lock=pathlib.Path(os.environ['TEMP'])/'nested-child.lock';"
        "handle=lock.open('w');handle.write('held');handle.flush();"
        "time.sleep(60)"
    )
    detached_arguments = (
        ",stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,"
        "stderr=subprocess.DEVNULL,close_fds=True"
        if detached_output
        else ""
    )
    leader_terminal = "raise SystemExit(0)" if leader_exits_early else "time.sleep(60)"
    parent_code = (
        "import pathlib,subprocess,sys,time;"
        f"pid_path=pathlib.Path({str(child_pid_path)!r});"
        f"subprocess.Popen([sys.executable,'-c',{child_code!r}]{detached_arguments});"
        "deadline=time.monotonic()+5;"
        "\nwhile not pid_path.is_file() and time.monotonic()<deadline: time.sleep(0.01)"
        "\nif not pid_path.is_file(): raise RuntimeError('nested child did not start')"
        # The first case exits the leader before timeout; the second keeps the
        # leader alive but detaches all child output while it holds TEMP open.
        f"\n{leader_terminal}"
    )
    checks_path = root / ".orchestrator" / "checks.yaml"
    checks = yaml.safe_load(checks_path.read_text(encoding="utf-8"))
    checks["checks"]["test_check"].update(
        {
            "argv": ["python", "-c", parent_code],
            "timeout_seconds": 1,
        }
    )
    checks_path.write_text(yaml.safe_dump(checks, sort_keys=False), encoding="utf-8")
    git(root, "add", ".orchestrator/checks.yaml")
    git(root, "commit", "-m", "exercise nested Check timeout")

    runtime = FakeRuntime()
    state = tmp_path / "state"
    check_temp_root = tmp_path / "check-temp"
    orchestrator = Orchestrator(
        load_project(root),
        state_root=state,
        check_temp_root=check_temp_root,
        runtime_port=runtime,
        runtime_profile_override={"runtime": "fake"},
        auth_method_override="none",
    )
    try:
        run_id = orchestrator.start(make_spec())
    finally:
        orchestrator.close()

    assert child_pid_path.is_file()
    child_pid = int(child_pid_path.read_text(encoding="ascii"))

    def child_is_running() -> bool:
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.OpenProcess.argtypes = [
                wintypes.DWORD,
                wintypes.BOOL,
                wintypes.DWORD,
            ]
            kernel32.OpenProcess.restype = wintypes.HANDLE
            kernel32.GetExitCodeProcess.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(wintypes.DWORD),
            ]
            kernel32.GetExitCodeProcess.restype = wintypes.BOOL
            kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            kernel32.CloseHandle.restype = wintypes.BOOL
            handle = kernel32.OpenProcess(0x1000, False, child_pid)
            if not handle:
                error = ctypes.get_last_error()
                if error == 87:  # ERROR_INVALID_PARAMETER: PID no longer exists.
                    return False
                raise OSError(error, "OpenProcess failed while checking nested child")
            exit_code = wintypes.DWORD()
            try:
                if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                    raise OSError(
                        ctypes.get_last_error(),
                        "GetExitCodeProcess failed while checking nested child",
                    )
                return exit_code.value == 259
            finally:
                if not kernel32.CloseHandle(handle):
                    raise OSError(
                        ctypes.get_last_error(),
                        "CloseHandle failed while checking nested child",
                    )
        try:
            os.kill(child_pid, 0)
            return True
        except ProcessLookupError:
            return False

    deadline = time.monotonic() + 2
    while child_is_running() and time.monotonic() < deadline:
        time.sleep(0.05)
    assert child_is_running() is False
    assert check_temp_root.is_dir()
    assert list(check_temp_root.iterdir()) == []

    with Ledger(state / "ledger.sqlite") as ledger:
        snapshot = ledger.load_run_snapshot(run_id)
        attempt = snapshot["tasks"][0]["attempts"][0]
        event = ledger.connection.execute(
            """SELECT payload_json FROM events
               WHERE aggregate_id=? AND event_type='attempt_finished'""",
            (attempt["attempt_id"],),
        ).fetchone()
    assert snapshot["run"]["state"] == "FAILED"
    assert len(snapshot["tasks"][0]["attempts"]) == 1
    assert attempt["failure_kind"] == "check_environment"
    assert snapshot["checks"][0]["state"] == "ERROR"
    assert runtime.turn_count == 1
    assert runtime.initial_feedbacks == [None]
    feedback = json.loads(event["payload_json"])["public_check_feedback"]
    assert feedback["messages"] == []
    assert feedback["transmitted_bytes"] == 0

    # The lock file is a durable owner record, so residue means an active lock,
    # not file presence.  A fresh controller must be able to acquire it now.
    with ControllerLock(state):
        pass


def test_transient_failure_creates_new_attempt_with_unique_artifacts(tmp_path: Path, project_factory) -> None:
    root = project_factory()
    _, snapshot = execute(root, tmp_path / "state", make_spec(), scenario="transient_failure")
    attempts = snapshot["tasks"][0]["attempts"]
    assert [attempt["state"] for attempt in attempts] == ["RETRYABLE_FAILED", "SUCCEEDED"]
    paths = [artifact["relative_path"] for artifact in snapshot["artifacts"]]
    assert any("attempts/001/" in path for path in paths)
    assert any("attempts/002/" in path for path in paths)
    assert len(paths) == len(set(paths))


def test_malformed_result_resumes_same_session_once(tmp_path: Path, project_factory) -> None:
    root = project_factory()
    _, snapshot = execute(root, tmp_path / "state", make_spec(), scenario="malformed_result")
    attempt = snapshot["tasks"][0]["attempts"][0]
    assert snapshot["run"]["state"] == "COMPLETED"
    assert attempt["resume_count"] == 1
    assert snapshot["run"]["turns_used"] == 2
    result_paths = [artifact["relative_path"] for artifact in snapshot["artifacts"] if artifact["kind"] == "result_envelope"]
    assert any("turns/001/" in path for path in result_paths)
    assert any("turns/002/" in path for path in result_paths)


def test_directory_artifact_gets_immediate_guidance_then_file_artifact_passes(
    tmp_path: Path, project_factory
) -> None:
    root = project_factory()
    result = {
        "schema_version": 1,
        "status_claim": "completed",
        "summary": "generated artifact",
        "artifacts": [
            {
                "path": "src",
                "kind": "generated_tree",
                "description": "generated directory",
            }
        ],
        "changed_paths": ["src/generated.txt"],
        "checks_run_by_worker": [],
        "assumptions": [],
        "warnings": [],
        "requested_followup": None,
    }
    corrected = {
        **result,
        "artifacts": [
            {
                "path": "src/generated.txt",
                "kind": "generated_file",
                "description": "generated file",
            }
        ],
    }
    runtime = FakeRuntime(
        workspace=root,
        fixture={
            "effects": [
                {
                    "type": "write_file",
                    "path": "src/generated.txt",
                    "content": "generated\n",
                }
            ],
            "turns": [{"result": result}, {"result": corrected}],
        },
    )
    state = tmp_path / "state"
    orchestrator = Orchestrator(
        load_project(root),
        state_root=state,
        check_temp_root=tmp_path / "check-temp",
        runtime_kind="injected_fake",
        runtime_port=runtime,
        runtime_profile_override={"runtime": "fake"},
        auth_method_override="none",
    )
    try:
        run_id = orchestrator.start(
            make_spec(
                workspace_mode="shared_serial_write",
                write_scope=["src/**"],
            )
        )
    finally:
        orchestrator.close()

    with Ledger(state / "ledger.sqlite") as ledger:
        snapshot = ledger.load_run_snapshot(run_id)
    feedback = [
        handle.raw["feedback"]
        for handle in runtime._handles.values()
        if isinstance(handle.raw, dict) and "feedback" in handle.raw
    ]
    assert snapshot["run"]["state"] == "COMPLETED"
    assert snapshot["tasks"][0]["state"] == "SUCCEEDED"
    assert snapshot["tasks"][0]["attempts"][0]["resume_count"] == 1
    assert len(feedback) == 1
    assert feedback[0]["failure"] == "result_schema"
    assert "directory paths are invalid: src" in feedback[0]["message"]


def test_untracked_python_bytecode_is_normalized_before_scope_validation(
    tmp_path: Path, project_factory
) -> None:
    root = project_factory()
    bytecode = "benchmark_checks/__pycache__/check_profile_r.cpython-312.pyc"
    fixture = {
        "effects": [
            {
                "type": "write_file",
                "path": "src/generated.txt",
                "content": "generated\n",
            },
            {
                "type": "write_file",
                "path": bytecode,
                "content": "automatic bytecode byproduct",
            },
        ],
    }

    _, snapshot = execute(
        root,
        tmp_path / "state",
        make_spec(workspace_mode="shared_serial_write", write_scope=["src/**"]),
        fixture=fixture,
    )

    assert snapshot["run"]["state"] == "COMPLETED"
    assert snapshot["tasks"][0]["state"] == "SUCCEEDED"
    assert not (root / bytecode).exists()


def test_non_bytecode_file_inside_pycache_remains_a_scope_violation(
    tmp_path: Path, project_factory
) -> None:
    root = project_factory()
    injected = "benchmark_checks/__pycache__/injected.txt"
    fixture = {
        "effects": [
            {
                "type": "write_file",
                "path": "src/generated.txt",
                "content": "generated\n",
            },
            {
                "type": "write_file",
                "path": injected,
                "content": "must remain visible to scope validation\n",
            },
        ],
    }

    _, snapshot = execute(
        root,
        tmp_path / "state",
        make_spec(workspace_mode="shared_serial_write", write_scope=["src/**"]),
        fixture=fixture,
    )

    attempt = snapshot["tasks"][0]["attempts"][0]
    assert snapshot["run"]["state"] == "BLOCKED"
    assert snapshot["tasks"][0]["state"] == "BLOCKED"
    assert attempt["failure_kind"] == "scope_violation"
    assert (root / injected).is_file()


@pytest.mark.parametrize(
    ("scenario", "expected_run", "expected_failure"),
    [
        ("out_of_scope_write", "BLOCKED", "scope_violation"),
        ("terminal_unknown", "BLOCKED", "terminal_unknown"),
        ("dispatch_uncertain", "BLOCKED", "dispatch_uncertain"),
        ("duplicate_conflicting_result", "BLOCKED", "artifact_corrupt"),
        ("artifact_corrupt", "BLOCKED", "artifact_corrupt"),
    ],
)
def test_unsafe_scenarios_are_never_adopted(
    tmp_path: Path, project_factory, scenario: str, expected_run: str, expected_failure: str
) -> None:
    root = project_factory()
    _, snapshot = execute(root, tmp_path / "state", make_spec(), scenario=scenario)
    attempt = snapshot["tasks"][0]["attempts"][0]
    assert snapshot["run"]["state"] == expected_run
    assert snapshot["tasks"][0]["state"] != "SUCCEEDED"
    assert attempt["failure_kind"] == expected_failure


def test_duplicate_same_result_is_idempotent(tmp_path: Path, project_factory) -> None:
    root = project_factory()
    _, snapshot = execute(root, tmp_path / "state", make_spec(), scenario="duplicate_same_result")
    assert snapshot["run"]["state"] == "COMPLETED"


@pytest.mark.parametrize(
    ("scenario", "task_state", "attempt_state"),
    [
        ("timeout_interrupt_supported", "FAILED", "FAILED"),
        ("timeout_interrupt_unsupported", "BLOCKED", "QUARANTINED"),
    ],
)
def test_timeout_paths_are_bounded_and_never_adopted(
    tmp_path: Path, project_factory, scenario: str, task_state: str, attempt_state: str
) -> None:
    root = project_factory(task_timeout=1)
    started = time.monotonic()
    _, snapshot = execute(
        root, tmp_path / "state", make_spec(), scenario=scenario, fixture={"delay_ms": 10_000}
    )
    assert time.monotonic() - started < 2.0
    assert snapshot["tasks"][0]["state"] == task_state
    assert snapshot["tasks"][0]["attempts"][0]["state"] == attempt_state


def test_stale_input_retries_then_fails_without_adoption(tmp_path: Path, project_factory) -> None:
    root = project_factory()
    spec = make_spec(workspace_mode="shared_serial_write", write_scope=["README.md"])
    fixture = {"stale_path": "README.md"}
    _, snapshot = execute(root, tmp_path / "state", spec, scenario="stale_input", fixture=fixture)
    assert snapshot["run"]["state"] == "FAILED"
    assert len(snapshot["tasks"][0]["attempts"]) == 2
    assert all(attempt["failure_kind"] == "stale_input" for attempt in snapshot["tasks"][0]["attempts"])


def test_artifact_corruption_is_reported_and_backup_verifies(tmp_path: Path, project_factory) -> None:
    root = project_factory()
    state = tmp_path / "state"
    run_id, snapshot = execute(root, state, make_spec())
    with ControllerLock(state):
        with Ledger(state / "ledger.sqlite") as ledger:
            destination = backup_run(ledger, state, run_id)
            assert verify_backup(destination)["ok"] is True
            artifact = next(item for item in snapshot["artifacts"] if item["kind"] == "result_envelope")
            (state / artifact["relative_path"]).write_text("corrupt", encoding="utf-8")
            integrity = check_integrity(ledger, state, run_id)
            assert integrity["ok"] is False
            assert artifact["relative_path"] in integrity["corrupt_artifacts"]


def test_second_controller_is_rejected(tmp_path: Path) -> None:
    state = tmp_path / "state"
    first = ControllerLock(state).acquire()
    try:
        with pytest.raises(ControllerLockError):
            ControllerLock(state).acquire()
    finally:
        first.release()


def test_dirty_worktree_is_rejected_before_run_creation(tmp_path: Path, project_factory) -> None:
    root = project_factory()
    (root / "dirty.txt").write_text("dirty\n", encoding="utf-8")
    state = tmp_path / "state"
    orchestrator = Orchestrator(
        load_project(root),
        state_root=state,
        check_temp_root=tmp_path / "check-temp",
        runtime_kind="fake",
    )
    try:
        with pytest.raises(ConfigurationError, match="clean"):
            orchestrator.start(make_spec())
    finally:
        orchestrator.close()
    assert not (state / "ledger.sqlite").exists()


def test_controller_restart_resumes_from_reported_without_new_session(tmp_path: Path, project_factory) -> None:
    root = project_factory()
    state = tmp_path / "state"

    class CrashAfterReport(Orchestrator):
        def _verify_and_finish(self, *args, **kwargs):
            raise RuntimeError("simulated controller crash after REPORTED")

    first = CrashAfterReport(
        load_project(root),
        state_root=state,
        check_temp_root=tmp_path / "check-temp",
        runtime_kind="fake",
    )
    try:
        with pytest.raises(RuntimeError, match="simulated controller crash"):
            first.start(make_spec())
    finally:
        first.close()
    with Ledger(state / "ledger.sqlite") as ledger:
        run_id = ledger.connection.execute("SELECT run_id FROM runs").fetchone()[0]
        snapshot = ledger.load_run_snapshot(run_id)
        assert snapshot["tasks"][0]["attempts"][0]["state"] == "REPORTED"
        assert len(snapshot["sessions"]) == 1

    second = Orchestrator(
        load_project(root),
        state_root=state,
        check_temp_root=tmp_path / "check-temp",
        runtime_kind="fake",
    )
    try:
        second.resume(run_id, make_spec())
    finally:
        second.close()
    with Ledger(state / "ledger.sqlite") as ledger:
        snapshot = ledger.load_run_snapshot(run_id)
        assert snapshot["run"]["state"] == "COMPLETED"
        assert snapshot["tasks"][0]["state"] == "SUCCEEDED"
        assert len(snapshot["sessions"]) == 1
