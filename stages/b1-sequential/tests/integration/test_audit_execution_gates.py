"""F8/F9/F3 regressions with local fixtures and in-memory runtime/Check ports only."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from orchestrator.contract import CheckResult, InputRef, RuntimeProfile, sha256_bytes, utc_now
from orchestrator.ledger import Ledger
from orchestrator.runtime import FakeRuntime
from orchestrator.schedule import ConfigurationError, Orchestrator, load_project, validate_run_against_project
import orchestrator.schedule as schedule_module
import orchestrator.verify as verify_module
from orchestrator.verify import VerificationError
from tests.conftest import make_spec


class CapturingRuntime(FakeRuntime):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.profiles = []

    def start_session(self, envelope, profile):
        self.profiles.append(profile)
        return super().start_session(envelope, profile)


@pytest.fixture
def no_external_ports(monkeypatch):
    monkeypatch.setattr(schedule_module, "preflight_check_environment", lambda *args, **kwargs: None)
    calls = []

    def check(name, definition, workspace, **kwargs):
        calls.append(name)
        return CheckResult(check_name=name, state="PASSED", argv=definition.argv,
                           exit_code=0, stdout="ok", stderr="", started_at=utc_now(), ended_at=utc_now(),
                           failure_classification_source="passed", temp_root=str(kwargs["temp_root"]),
                           temp_allocation_id="a" * 32)

    monkeypatch.setattr(schedule_module, "run_command_check", check)
    return calls


def snapshot(state, run_id=None):
    with Ledger(state / "ledger.sqlite") as ledger:
        if run_id is None:
            run_id = ledger.connection.execute("SELECT run_id FROM runs").fetchone()[0]
        return ledger.load_run_snapshot(run_id)


def test_f8_each_task_uses_its_named_profile(tmp_path, project_factory, monkeypatch, no_external_ports):
    loaded = load_project(project_factory())
    capability = loaded.pack.capabilities.profiles["document_read"]
    loaded.pack.capabilities.profiles["special_read"] = capability.model_copy(update={"runtime_profile": "special"})
    spec = make_spec(tasks=2)
    spec.tasks[1] = spec.tasks[1].model_copy(update={"capability_profile": "special_read"})
    profiles = {
        "local_default": RuntimeProfile(runtime="codex", model="default-model", auth_method="chatgpt", reasoning_effort="low"),
        "special": RuntimeProfile(runtime="codex", model="special-model", auth_method="chatgpt", reasoning_effort="high"),
    }
    monkeypatch.setattr(schedule_module, "load_runtime_profile", lambda name, path: profiles[name])
    monkeypatch.setattr(schedule_module, "CodexRuntime", CapturingRuntime)
    state = tmp_path / "state"
    app = Orchestrator(loaded, state_root=state, check_temp_root=tmp_path / "checks", runtime_kind="codex")
    try:
        run_id = app.start(spec)
        assert [p.model for p in app.runtime.profiles] == ["default-model", "special-model"]
        assert [p.reasoning_effort for p in app.runtime.profiles] == ["low", "high"]
    finally:
        app.close()
    data = snapshot(state, run_id)
    assert data["run"]["state"] == "COMPLETED"
    assert [s["runtime_profile"] for s in data["sessions"]] == ["local_default", "special"]
    assert all(s["sandbox"] == "read_only" for s in data["sessions"])


@pytest.mark.parametrize("workspace_mode,sandbox", [("read_only", "workspace_write"), ("shared_serial_write", "read_only")])
def test_f8_contradictory_sandbox_is_rejected(project_factory, workspace_mode, sandbox):
    loaded = load_project(project_factory())
    spec = make_spec(workspace_mode=workspace_mode, write_scope=[] if workspace_mode == "read_only" else ["src/**"])
    name = spec.tasks[0].capability_profile
    loaded.pack.capabilities.profiles[name] = loaded.pack.capabilities.profiles[name].model_copy(update={"sandbox": sandbox})
    with pytest.raises(ConfigurationError, match="sandbox"):
        validate_run_against_project(spec, loaded)


def test_f8_single_injected_profile_cannot_silently_cover_another_name(tmp_path, project_factory, no_external_ports):
    loaded = load_project(project_factory())
    loaded.pack.capabilities.profiles["document_read"] = loaded.pack.capabilities.profiles["document_read"].model_copy(update={"runtime_profile": "other"})
    runtime = CapturingRuntime()
    app = Orchestrator(loaded, state_root=tmp_path / "state", check_temp_root=tmp_path / "checks",
                       runtime_port=runtime, runtime_profile_override={"runtime": "fake"}, auth_method_override="none")
    try:
        with pytest.raises(ConfigurationError, match="profile"):
            app.start(make_spec())
        assert runtime.session_count == 0
    finally:
        app.close()


@pytest.mark.parametrize("case", ["missing", "wrong-hash", "malformed-hash", "directory", "missing-artifact"])
def test_f9_invalid_input_never_creates_an_attempt_or_session(tmp_path, project_factory, no_external_ports, case):
    root = project_factory()
    spec = make_spec()
    item = {"path": "README.md"}
    if case == "missing":
        item["path"] = "missing.txt"
    elif case == "wrong-hash":
        item["sha256"] = "0" * 64
    elif case == "malformed-hash":
        item["sha256"] = "not-a-sha256"
    elif case == "directory":
        item["path"] = "src"
    else:
        item["artifact_id"] = "artifact_missing"
    spec.tasks[0] = spec.tasks[0].model_copy(update={"inputs": [InputRef(**item)]})
    state = tmp_path / "state"
    app = Orchestrator(load_project(root), state_root=state, check_temp_root=tmp_path / "checks")
    try:
        run_id = app.start(spec)
        assert app.runtime.session_count == 0
        assert app.runtime.turn_count == 0
    finally:
        app.close()
    data = snapshot(state, run_id)
    assert data["run"]["state"] == "BLOCKED"
    assert data["tasks"][0]["attempts"] == []
    assert no_external_ports == []
    with Ledger(state / "ledger.sqlite") as ledger:
        event = ledger.connection.execute(
            "SELECT payload_json FROM events WHERE event_type='run_verification_boundary_failed'"
        ).fetchone()
        assert json.loads(event[0])["stage"] == "required_inputs"


@pytest.mark.parametrize("with_hash", [False, True])
def test_f9_regular_input_with_optional_matching_hash_is_accepted(tmp_path, project_factory, no_external_ports, with_hash):
    root = project_factory()
    spec = make_spec()
    spec.tasks[0] = spec.tasks[0].model_copy(update={"inputs": [InputRef(path="README.md", sha256=sha256_bytes((root / "README.md").read_bytes()) if with_hash else None)]})
    state = tmp_path / "state"
    app = Orchestrator(load_project(root), state_root=state, check_temp_root=tmp_path / "checks")
    try:
        run_id = app.start(spec)
    finally:
        app.close()
    assert snapshot(state, run_id)["run"]["state"] == "COMPLETED"


@pytest.mark.parametrize("drift", [
    "none", "modify", "delete", "legacy", "add", "task",
    "snapshot-corrupt", "snapshot-missing", "event-payload", "event-binding", "declared-artifact",
])
def test_f3_passed_check_is_bound_to_workspace_at_check_time(tmp_path, project_factory, monkeypatch, no_external_ports, drift):
    root = project_factory()
    state = tmp_path / "state"
    spec = make_spec(workspace_mode="shared_serial_write", write_scope=["src/**"])
    fixture = None
    if drift == "declared-artifact":
        (root / ".git/info/exclude").write_text("src/ignored-output.txt\n", encoding="utf-8")
        (root / "src/ignored-output.txt").write_text("GOOD", encoding="utf-8")
        fixture = {"result": {
            "schema_version": 1, "status_claim": "completed", "summary": "fixture",
            "artifacts": [{"path": "src/ignored-output.txt", "kind": "file", "description": "declared output"}],
            "changed_paths": [], "checks_run_by_worker": [], "assumptions": [], "warnings": [],
            "requested_followup": None,
        }}
    original_finish = Ledger.finish_check

    def crash_after_pass(ledger, check_id, values):
        if drift == "legacy":
            values = {key: value for key, value in values.items() if key != "verification_snapshot"}
        result = original_finish(ledger, check_id, values)
        if result["state"] == "PASSED":
            raise RuntimeError("simulated crash immediately after Check commit")
        return result

    monkeypatch.setattr(Ledger, "finish_check", crash_after_pass)
    first = Orchestrator(load_project(root), state_root=state, check_temp_root=tmp_path / "checks", fake_fixture=fixture)
    try:
        with pytest.raises(RuntimeError, match="simulated crash"):
            first.start(spec)
    finally:
        first.close()
    before = snapshot(state)
    run_id = before["run"]["run_id"]
    assert before["checks"][0]["state"] == "PASSED"
    assert before["tasks"][0]["state"] == "VERIFYING"
    monkeypatch.setattr(Ledger, "finish_check", original_finish)
    if drift == "modify":
        (root / "src/existing.txt").write_text("BAD\n", encoding="utf-8")
    elif drift == "delete":
        (root / "src/existing.txt").unlink()
    elif drift == "add":
        (root / "src/new.txt").write_text("new", encoding="utf-8")
    elif drift == "task":
        spec.tasks[0] = spec.tasks[0].model_copy(update={"goal": "a different goal"})
    elif drift == "declared-artifact":
        (root / "src/ignored-output.txt").write_text("BAD", encoding="utf-8")
    elif drift in {"snapshot-corrupt", "snapshot-missing"}:
        artifact = next(a for a in before["artifacts"] if a["relative_path"].endswith("/verification-snapshot.json"))
        path = state / artifact["relative_path"]
        if drift == "snapshot-missing":
            path.unlink()
        else:
            path.write_text("{}", encoding="utf-8")
    elif drift in {"event-payload", "event-binding"}:
        # Corrupt only this synthetic fixture, never a historical Run.
        payload = [] if drift == "event-payload" else {"verification_snapshot": {"artifact_id": {}, "sha256": []}}
        with Ledger(state / "ledger.sqlite") as ledger:
            ledger.connection.execute("UPDATE events SET payload_json=? WHERE event_type='check_finished'", (json.dumps(payload),))
            ledger.connection.commit()
    second = Orchestrator(load_project(root), state_root=state, check_temp_root=tmp_path / "checks")
    try:
        second.resume(run_id, spec)
        assert second.runtime.session_count == 0
    finally:
        second.close()
    after = snapshot(state, run_id)
    assert after["run"]["state"] == ("COMPLETED" if drift == "none" else "BLOCKED")
    assert after["checks"][0] == before["checks"][0]
    assert no_external_ports == ["test_check"]
    assert len(after["sessions"]) == 1


def test_f8_missing_second_profile_rejected_before_first_session(tmp_path, project_factory, monkeypatch, no_external_ports):
    loaded = load_project(project_factory())
    loaded.pack.capabilities.profiles["special_read"] = loaded.pack.capabilities.profiles["document_read"].model_copy(
        update={"runtime_profile": "absent"})
    spec = make_spec(tasks=2)
    spec.tasks[1] = spec.tasks[1].model_copy(update={"capability_profile": "special_read"})
    profile_file = tmp_path / "profiles.yaml"
    profile_file.write_text("schema_version: 1\nprofiles:\n  local_default:\n    runtime: codex\n    model: test-model\n    auth_method: chatgpt\n    reasoning_effort: low\n", encoding="utf-8")
    monkeypatch.setattr(schedule_module, "CodexRuntime", CapturingRuntime)
    state = tmp_path / "state"
    app = Orchestrator(loaded, state_root=state, check_temp_root=tmp_path / "checks",
                       runtime_kind="codex", runtime_profiles_path=profile_file)
    try:
        with pytest.raises(ConfigurationError, match="profile not found"):
            app.start(spec)
        assert app.runtime.session_count == 0
        assert not (state / "ledger.sqlite").exists()
    finally:
        app.close()


def test_f9_ignored_explicit_file_is_present_in_fingerprint(tmp_path, project_factory, no_external_ports):
    root = project_factory()
    (root / ".git/info/exclude").write_text("ignored-input.txt\n", encoding="utf-8")
    (root / "ignored-input.txt").write_text("required", encoding="utf-8")
    spec = make_spec()
    spec.tasks[0] = spec.tasks[0].model_copy(update={"inputs": [InputRef(path="ignored-input.txt")]})
    state = tmp_path / "state"
    app = Orchestrator(load_project(root), state_root=state, check_temp_root=tmp_path / "checks")
    try:
        run_id = app.start(spec)
    finally:
        app.close()
    data = snapshot(state, run_id)
    assert data["run"]["state"] == "COMPLETED"
    artifact = next(a for a in data["artifacts"] if a["kind"] == "fingerprint")
    fingerprint = json.loads((state / artifact["relative_path"]).read_text(encoding="utf-8"))
    assert any(entry["path"] == "ignored-input.txt" for entry in fingerprint["manifest"])


def test_f9_reparse_input_is_rejected_without_dispatch(tmp_path, project_factory, monkeypatch, no_external_ports):
    root = project_factory()
    spec = make_spec()
    spec.tasks[0] = spec.tasks[0].model_copy(update={"inputs": [InputRef(path="README.md")]})
    real_probe = verify_module._is_reparse_point
    monkeypatch.setattr(verify_module, "_is_reparse_point", lambda path: path == root / "README.md" or real_probe(path))
    state = tmp_path / "state"
    app = Orchestrator(load_project(root), state_root=state, check_temp_root=tmp_path / "checks")
    try:
        run_id = app.start(spec)
        assert app.runtime.session_count == 0
    finally:
        app.close()
    assert snapshot(state, run_id)["run"]["state"] == "BLOCKED"


def test_f9_input_change_between_gate_and_fingerprint_blocks_dispatch(tmp_path, project_factory, monkeypatch, no_external_ports):
    root = project_factory()
    spec = make_spec()
    spec.tasks[0] = spec.tasks[0].model_copy(update={"inputs": [InputRef(path="README.md")]})
    state = tmp_path / "state"
    app = Orchestrator(load_project(root), state_root=state, check_temp_root=tmp_path / "checks")
    original = app.workspace.fingerprint_inputs

    def change_then_fingerprint(task):
        (root / "README.md").write_text("changed after the input gate", encoding="utf-8")
        return original(task)

    monkeypatch.setattr(app.workspace, "fingerprint_inputs", change_then_fingerprint)
    try:
        run_id = app.start(spec)
        assert app.runtime.session_count == 0
    finally:
        app.close()
    data = snapshot(state, run_id)
    assert data["run"]["state"] == "BLOCKED"
    assert data["tasks"][0]["attempts"] == []


@pytest.mark.parametrize("case", [
    "dependency", "user", "other-run", "unrelated-task", "wrong-attempt",
    "wrong-bytes", "wrong-size", "corrupt-store", "missing-store", "wrong-kind", "no-owner",
])
def test_f9_artifact_bytes_and_run_task_provenance(tmp_path, project_factory, no_external_ports, case):
    root = project_factory()
    spec = make_spec(tasks=2)
    state = tmp_path / "state"
    app = Orchestrator(load_project(root), state_root=state, check_temp_root=tmp_path / "checks")
    try:
        run_id = app.start(spec)
        with Ledger(state / "ledger.sqlite") as ledger:
            tasks = ledger.list_tasks(run_id)
            owner, consumer = tasks
            task_spec = spec.tasks[1]
            owner_attempt = ledger.list_attempts(owner["task_id"])[0]["attempt_id"]
            copied = app.store.write_bytes("inputs/readme.txt", (root / "README.md").read_bytes())
            metadata = {**copied, "run_id": run_id, "task_id": owner["task_id"],
                        "attempt_id": owner_attempt, "kind": "project_file", "producer": "runtime",
                        "sensitivity": "project_local", "retention": "run"}
            if case == "other-run":
                other = ledger.create_run({
                    "project_id": "other", "request_text": "test", "request_source": "test",
                    "completion_criteria": [{"id": "R"}], "auth_method": "none", "policy_name": "test",
                    "project_pack_sha256": "a" * 64, "core_version": "0.1.0", "max_turns": 1, "timeout_seconds": 1,
                })
                metadata["run_id"] = other["run_id"]
            elif case == "unrelated-task":
                consumer, task_spec = owner, spec.tasks[0]
            elif case == "wrong-attempt":
                metadata["attempt_id"] = ledger.list_attempts(consumer["task_id"])[0]["attempt_id"]
            elif case == "wrong-bytes":
                metadata["sha256"] = "0" * 64
            elif case == "wrong-size":
                metadata["size_bytes"] += 1
            elif case == "wrong-kind":
                metadata["kind"] = "result_envelope"
            elif case in {"user", "no-owner"}:
                metadata.update(task_id=None, attempt_id=None, producer="user" if case == "user" else "controller")
            artifact = ledger.register_artifact(metadata)
            if case == "corrupt-store":
                app.store.resolve(copied["relative_path"]).write_text("corrupt", encoding="utf-8")
            elif case == "missing-store":
                app.store.resolve(copied["relative_path"]).unlink()
            task_spec = task_spec.model_copy(update={"inputs": [InputRef(path="README.md", artifact_id=artifact["artifact_id"])]})
            if case in {"dependency", "user"}:
                assert "README.md" in app._validate_task_inputs(ledger, run_id, consumer, task_spec)
            else:
                with pytest.raises(VerificationError) as error:
                    app._validate_task_inputs(ledger, run_id, consumer, task_spec)
                assert error.value.stage == "required_inputs"
    finally:
        app.close()


def test_f3_check_cannot_mutate_candidate_and_then_claim_success(tmp_path, project_factory, monkeypatch, no_external_ports):
    root = project_factory()
    original_check = schedule_module.run_command_check

    def mutating_check(name, definition, workspace, **kwargs):
        (workspace.root / "src/existing.txt").write_text("changed by Check", encoding="utf-8")
        return original_check(name, definition, workspace, **kwargs)

    monkeypatch.setattr(schedule_module, "run_command_check", mutating_check)
    state = tmp_path / "state"
    app = Orchestrator(load_project(root), state_root=state, check_temp_root=tmp_path / "checks")
    try:
        run_id = app.start(make_spec(workspace_mode="shared_serial_write", write_scope=["src/**"]))
    finally:
        app.close()
    data = snapshot(state, run_id)
    assert data["run"]["state"] == "BLOCKED"
    assert data["checks"][0]["state"] == "PASSED"  # Command exit evidence is preserved.
    assert data["tasks"][0]["attempts"][0]["failure_kind"] == "artifact_corrupt"
