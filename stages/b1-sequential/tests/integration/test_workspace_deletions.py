"""F11 workspace deletion/rename regressions using disposable Git/Fake fixtures."""
from __future__ import annotations

from pathlib import Path
import errno
import json
import os
import subprocess
from types import SimpleNamespace

import pytest
import yaml

from orchestrator.contract import InputRef
from orchestrator.ledger import Ledger
from orchestrator.schedule import ConfigurationError, Orchestrator, load_project
import orchestrator.schedule as schedule_module
import orchestrator.verify as verify_module
from orchestrator.verify import GitWorkspace, VerificationError
from tests.conftest import git, make_spec


def test_deleted_index_entry_is_a_change_not_a_read_error(project_factory):
    root = project_factory()
    workspace = GitWorkspace(root)
    baseline = workspace.capture_baseline()
    target = root / "src/existing.txt"
    assert root.resolve() in target.resolve().parents
    target.unlink()
    assert workspace.changed_paths(baseline) == ["src/existing.txt"]
    assert "src/existing.txt" not in workspace.list_files()
    assert workspace.status()["clean"] is False


def test_allowed_deletion_completes_without_restoring_file(tmp_path, project_factory):
    root = project_factory()
    state = tmp_path / "state"
    app = Orchestrator(load_project(root), state_root=state, check_temp_root=tmp_path / "checks",
        fake_fixture={"effects": [{"type": "delete_file", "path": "src/existing.txt"}]})
    try:
        run_id = app.start(make_spec(workspace_mode="shared_serial_write", write_scope=["src/**"]))
    finally:
        app.close()
    with Ledger(state / "ledger.sqlite") as ledger:
        assert ledger.get("run", run_id)["state"] == "COMPLETED"
    assert not (root / "src/existing.txt").exists()


def snapshot(state, run_id=None):
    with Ledger(state / "ledger.sqlite") as ledger:
        if run_id is None:
            run_id = ledger.connection.execute("SELECT run_id FROM runs").fetchone()[0]
        return ledger.load_run_snapshot(run_id)


@pytest.fixture
def no_preflight(monkeypatch):
    monkeypatch.setattr(schedule_module, "preflight_check_environment", lambda *a, **kw: None)


@pytest.mark.parametrize("staged", [False, True])
@pytest.mark.parametrize("change", ["delete", "rename"])
def test_delete_and_rename_include_both_sides(project_factory, staged, change):
    root = project_factory()
    original = root / "src/existing.txt"
    renamed = root / "src/이름 변경.txt"
    assert root.resolve() in original.resolve().parents and root.resolve() in renamed.resolve().parents
    workspace = GitWorkspace(root)
    before = workspace.capture_baseline()
    original.rename(renamed) if change == "rename" else original.unlink()
    if staged:
        git(root, "add", "-A", "--", "src")
    expected = ["src/existing.txt", "src/이름 변경.txt"] if change == "rename" else ["src/existing.txt"]
    assert workspace.changed_paths(before) == sorted(expected)
    assert workspace.status()["clean"] is False
    assert "src/existing.txt" not in workspace.list_files()
    assert "src/existing.txt" not in {e.path for e in workspace.fingerprint_inputs(make_spec().tasks[0]).manifest}


@pytest.mark.parametrize("case", ["read_only", "out_of_scope", "required_input", "declared_artifact", "rename_allowed", "rename_outside"])
def test_deletion_policy_gates(tmp_path, project_factory, no_preflight, case):
    root = project_factory()
    state = tmp_path / "state"
    spec = make_spec(workspace_mode="read_only" if case == "read_only" else "shared_serial_write",
                     write_scope=[] if case == "read_only" else ["other/**"] if case == "out_of_scope" else ["src/**"])
    if case == "required_input":
        spec.tasks[0] = spec.tasks[0].model_copy(update={"inputs": [InputRef(path="src/existing.txt")]})
    effects = [{"type": "delete_file", "path": "src/existing.txt"}]
    if case.startswith("rename_"):
        effects.append({"type": "write_file", "path": "src/renamed.txt" if case == "rename_allowed" else "outside.txt", "content": "original\n"})
    fixture = {"effects": effects}
    if case == "declared_artifact":
        fixture["result"] = {"schema_version": 1, "status_claim": "completed", "summary": "fixture",
            "artifacts": [{"path": "src/existing.txt", "kind": "file", "description": "must exist"}],
            "changed_paths": [], "checks_run_by_worker": [], "assumptions": [], "warnings": [], "requested_followup": None}
    app = Orchestrator(load_project(root), state_root=state, check_temp_root=tmp_path / "checks", fake_fixture=fixture)
    try:
        run_id = app.start(spec)
        assert app.runtime.session_count == app.runtime.turn_count == 1
    finally:
        app.close()
    data = snapshot(state, run_id)
    allowed = case == "rename_allowed"
    assert data["run"]["state"] == ("COMPLETED" if allowed else "BLOCKED")
    attempt = data["tasks"][0]["attempts"][0]
    assert attempt["state"] == ("SUCCEEDED" if allowed else "BLOCKED")
    assert data["tasks"][0]["active_attempt_id"] is None
    if not allowed:
        assert attempt["failure_kind"] == ("artifact_corrupt" if case in {"required_input", "declared_artifact"} else "scope_violation")
        assert data["checks"] == []
    assert not (root / "src/existing.txt").exists()


@pytest.mark.parametrize("require_clean", [True, False])
def test_existing_deletion_respects_clean_worktree_policy(tmp_path, project_factory, no_preflight, require_clean):
    root = project_factory()
    if not require_clean:
        policy_path = root / ".orchestrator/policies.yaml"
        config = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
        config["policies"]["b1_safe"]["require_clean_worktree"] = False
        policy_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
        git(root, "add", ".orchestrator/policies.yaml")
        git(root, "commit", "-m", "allow preexisting fixture changes")
    (root / "src/existing.txt").unlink()
    state = tmp_path / "state"
    app = Orchestrator(load_project(root), state_root=state, check_temp_root=tmp_path / "checks")
    try:
        if require_clean:
            with pytest.raises(ConfigurationError, match="must be clean"):
                app.start(make_spec())
            assert app.runtime.session_count == 0
            assert not (state / "ledger.sqlite").exists()
        else:
            run_id = app.start(make_spec())
            assert snapshot(state, run_id)["run"]["state"] == "COMPLETED"
    finally:
        app.close()
    assert not (root / "src/existing.txt").exists()


@pytest.mark.parametrize("restore", [False, True])
def test_recovered_passed_check_binds_file_absence(tmp_path, project_factory, monkeypatch, no_preflight, restore):
    root = project_factory()
    state = tmp_path / "state"
    spec = make_spec(workspace_mode="shared_serial_write", write_scope=["src/**"])
    finish = Ledger.finish_check
    def crash(ledger, check_id, values):
        result = finish(ledger, check_id, values)
        raise RuntimeError("fixture crash after Check")
    monkeypatch.setattr(Ledger, "finish_check", crash)
    first = Orchestrator(load_project(root), state_root=state, check_temp_root=tmp_path / "checks",
        fake_fixture={"effects": [{"type": "delete_file", "path": "src/existing.txt"}]})
    try:
        with pytest.raises(RuntimeError, match="fixture crash"):
            first.start(spec)
    finally:
        first.close()
    before = snapshot(state)
    run_id = before["run"]["run_id"]
    artifact = next(a for a in before["artifacts"] if a["relative_path"].endswith("verification-snapshot.json"))
    evidence_path = state / artifact["relative_path"]
    evidence_bytes = evidence_path.read_bytes()
    assert "src/existing.txt" not in {item["path"] for item in json.loads(evidence_bytes)["before"]["files"]}
    if restore:
        (root / "src/existing.txt").write_text("original\n", encoding="utf-8")
    monkeypatch.setattr(Ledger, "finish_check", finish)
    second = Orchestrator(load_project(root), state_root=state, check_temp_root=tmp_path / "checks")
    try:
        second.resume(run_id, spec)
        assert second.runtime.session_count == second.runtime.turn_count == 0
    finally:
        second.close()
    after = snapshot(state, run_id)
    assert after["run"]["state"] == ("BLOCKED" if restore else "COMPLETED")
    assert after["checks"] == before["checks"]
    assert evidence_path.read_bytes() == evidence_bytes


@pytest.mark.parametrize("operation", ["delete", "restore"])
def test_check_cannot_change_presence_then_claim_pass(tmp_path, project_factory, monkeypatch, no_preflight, operation):
    root = project_factory()
    state = tmp_path / "state"
    run_check = schedule_module.run_command_check
    def changing_check(*args, **kwargs):
        result = run_check(*args, **kwargs)
        path = root / "src/existing.txt"
        path.unlink() if operation == "delete" else path.write_text("original\n", encoding="utf-8")
        return result
    monkeypatch.setattr(schedule_module, "run_command_check", changing_check)
    app = Orchestrator(load_project(root), state_root=state, check_temp_root=tmp_path / "checks",
        fake_fixture={"effects": [{"type": "delete_file", "path": "src/existing.txt"}]} if operation == "restore" else None)
    try:
        run_id = app.start(make_spec(workspace_mode="shared_serial_write", write_scope=["src/**"]))
    finally:
        app.close()
    data = snapshot(state, run_id)
    assert data["run"]["state"] == "BLOCKED"
    assert data["checks"][0]["state"] == "PASSED"
    assert data["tasks"][0]["attempts"][0]["failure_kind"] == "artifact_corrupt"


@pytest.mark.parametrize("phase", ["stat", "open"])
@pytest.mark.parametrize("error", ["permission", "io", "missing"])
def test_io_failure_is_not_silently_a_deletion(project_factory, monkeypatch, phase, error):
    root = project_factory()
    path = root / "src/existing.txt"
    workspace = GitWorkspace(root)
    baseline = workspace.capture_baseline()
    method_name = "lstat" if phase == "stat" else "open"
    original = getattr(Path, method_name)
    exception = PermissionError("fixture denial") if error == "permission" else OSError(errno.EIO, "fixture IO failure") if error == "io" else FileNotFoundError("fixture vanished")
    def denied(self, *args, **kwargs):
        if self == path:
            raise exception
        return original(self, *args, **kwargs)
    monkeypatch.setattr(Path, method_name, denied)
    if phase == "stat" and error == "missing":
        # Stable ENOENT at inventory time is the permitted deletion observation.
        assert workspace.changed_paths(baseline) == ["src/existing.txt"]
    else:
        with pytest.raises(VerificationError) as caught:
            workspace.changed_paths(baseline)
        assert caught.value.stage == "workspace_inventory"
        assert caught.value.retryable is False


@pytest.mark.parametrize("race", ["vanish_before_read", "replace_before_read", "mutate_after_read", "restore_absent", "add_untracked"])
def test_inventory_detects_observed_races(project_factory, monkeypatch, race):
    root = project_factory()
    path = root / "src/existing.txt"
    workspace = GitWorkspace(root)
    if race == "restore_absent":
        path.unlink()
    original = verify_module._file_entry
    fired = False
    def racing_entry(base, relative, expected=None):
        nonlocal fired
        trigger = relative == ("README.md" if race in {"restore_absent", "add_untracked"} else "src/existing.txt")
        if trigger and not fired:
            fired = True
            if race == "vanish_before_read":
                path.unlink()
            elif race == "replace_before_read":
                replacement = root / "src/replacement.txt"
                replacement.write_bytes(path.read_bytes())
                assert root.resolve() in replacement.resolve().parents and root.resolve() in path.resolve().parents
                replacement.replace(path)
            elif race == "restore_absent":
                path.write_text("restored", encoding="utf-8")
            elif race == "add_untracked":
                (root / "new.txt").write_text("new", encoding="utf-8")
        result = original(base, relative, expected)
        if trigger and race == "mutate_after_read":
            path.write_text("a different length", encoding="utf-8")
        return result
    monkeypatch.setattr(verify_module, "_file_entry", racing_entry)
    with pytest.raises(VerificationError) as caught:
        workspace.capture_baseline()
    assert caught.value.stage == "workspace_inventory"
    assert fired


@pytest.mark.parametrize("drift", [False, True])
def test_handle_ctime_is_compared_only_with_same_api(project_factory, monkeypatch, drift):
    root = project_factory()
    original = os.fstat
    calls = 0
    def stat_with_different_ctime(fd):
        nonlocal calls
        calls += 1
        observed = original(fd)
        fields = {key: getattr(observed, key) for key in ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns")}
        fields["st_ctime_ns"] = 1000 + (calls if drift else 0)
        return SimpleNamespace(**fields)
    monkeypatch.setattr(os, "fstat", stat_with_different_ctime)
    if drift:
        with pytest.raises(VerificationError):
            verify_module._file_entry(root, "README.md")
    else:
        assert verify_module._file_entry(root, "README.md").size == len((root / "README.md").read_bytes())


@pytest.mark.parametrize("unsafe", ["directory", "reparse_parent"])
def test_nonregular_paths_are_not_treated_as_absence(project_factory, monkeypatch, unsafe):
    root = project_factory()
    if unsafe == "directory":
        path = root / "src/existing.txt"
        path.unlink()
        path.mkdir()
    else:
        original = Path.lstat
        def reparse(self, *args, **kwargs):
            result = original(self, *args, **kwargs)
            if self == root / "src":
                return SimpleNamespace(st_mode=result.st_mode, st_file_attributes=0x400)
            return result
        monkeypatch.setattr(Path, "lstat", reparse)
    with pytest.raises(VerificationError) as caught:
        GitWorkspace(root).capture_baseline()
    assert caught.value.stage == "workspace_inventory"


@pytest.mark.parametrize("when", ["before_dispatch", "after_runtime"])
def test_inventory_error_blocks_without_retry_or_dangling_attempt(tmp_path, project_factory, monkeypatch, no_preflight, when):
    root = project_factory()
    state = tmp_path / "state"
    app = Orchestrator(load_project(root), state_root=state, check_temp_root=tmp_path / "checks")
    path_open = Path.open
    def denied(path, *args, **kwargs):
        if path == root / "src/existing.txt":
            raise PermissionError("fixture read denied")
        return path_open(path, *args, **kwargs)
    if when == "before_dispatch":
        monkeypatch.setattr(Path, "open", denied)
    else:
        app.turn_boundary_observer = lambda context: monkeypatch.setattr(Path, "open", denied)
    try:
        run_id = app.start(make_spec())
        assert app.runtime.session_count == (0 if when == "before_dispatch" else 1)
    finally:
        app.close()
    data = snapshot(state, run_id)
    assert data["run"]["state"] == "BLOCKED"
    assert data["tasks"][0]["active_attempt_id"] is None
    if when == "after_runtime":
        assert data["tasks"][0]["attempts"][0]["state"] == "BLOCKED"
        assert data["tasks"][0]["attempts"][0]["failure_kind"] == "internal"
    else:
        assert data["tasks"][0]["attempts"] == []


def test_git_failure_is_not_an_empty_inventory(project_factory, monkeypatch):
    workspace = GitWorkspace(project_factory())
    def failed(*args, **kwargs):
        raise subprocess.CalledProcessError(128, ["git", "ls-files"])
    monkeypatch.setattr(workspace, "_git_file_candidates", failed)
    with pytest.raises(VerificationError, match="Git file inventory is unavailable"):
        workspace.capture_baseline()


def test_removed_parent_directory_is_a_stable_deletion(project_factory):
    root = project_factory()
    workspace = GitWorkspace(root)
    baseline = workspace.capture_baseline()
    (root / "src/existing.txt").unlink()
    (root / "src").rmdir()  # Empty disposable fixture directory; never recursive.
    assert workspace.changed_paths(baseline) == ["src/existing.txt"]


def test_delete_then_restore_same_bytes_is_net_unchanged(project_factory):
    root = project_factory()
    workspace = GitWorkspace(root)
    baseline = workspace.capture_baseline()
    path = root / "src/existing.txt"
    original = path.read_bytes()
    path.unlink()
    path.write_bytes(original)
    assert workspace.changed_paths(baseline) == []
