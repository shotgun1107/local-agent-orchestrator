"""Model-free controls only; real Docker qualification is a separate user turn."""
from __future__ import annotations

import copy
import base64
import ast
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace as NS

import pytest

from benchmark_runner import profile_i_isolated_execution as execution
from benchmark_runner import profile_i_isolated_oracle as oracle
from benchmark_runner import profile_i_semantic_execution as binding
from benchmark_runner import profile_i_qualification as qualification

REPO = Path(__file__).resolve().parents[3]
GIT = Path(shutil.which("git")).resolve()


def git(repo, *args):
    return subprocess.run([str(GIT), *args], cwd=repo, capture_output=True, check=True).stdout


@pytest.fixture(scope="module")
def probe():
    spec = importlib.util.spec_from_file_location("reviewed_v3_probe", REPO / execution.ROOT / "probe.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def observations(probe, tmp_path_factory):
    rows = {}
    for case in oracle.CASES:
        rows[case] = probe.observe(case, "a" * 32, tmp_path_factory.mktemp("observed-" + case))
    return rows


def request(case):
    return {"version": 3, "case": case, "nonce": "a" * 32}


def wire(req, value):
    return binding.canonical({**req, "observations": value})


@pytest.mark.parametrize("case", oracle.CASES)
def test_reviewed_implementation_observations_satisfy_external_oracle(observations, case):
    assert oracle.grade(request(case), wire(request(case), observations[case]), exit_code=0)["passed"] is True


@pytest.mark.parametrize("case", oracle.CASES)
@pytest.mark.parametrize("value", [None, True, {"passed": True}, {"behavior_passed": True, "challenge_ready": True}])
def test_noop_or_self_awarded_verdict_cannot_pass(case, value):
    assert oracle.grade(request(case), wire(request(case), value), exit_code=0)["passed"] is False


@pytest.mark.parametrize("attack", ["wrong_count", "bool_count", "extra_method", "frame_hash", "notification_id"])
def test_profile_method_ledger_is_not_a_self_asserted_pass(observations, attack):
    value = copy.deepcopy(observations["profile"])
    counts = value["good"]["method_ledger"]["client_request_method_counts"]
    if attack == "wrong_count": counts["initialize"] = 2
    elif attack == "bool_count": counts["initialize"] = True
    elif attack == "extra_method": counts["turn/start"] = 1
    elif attack == "frame_hash": value["good"]["transcript"][0]["message"]["sha256"] = "f" * 64
    else: value["good"]["thread_started_notification_thread_id_sha256"] = "f" * 64
    assert not oracle.grade(request("profile"), wire(request("profile"), value), exit_code=0)["passed"]


@pytest.mark.parametrize("attack", ["duplicate", "nan", "overflow_float", "trailing", "too_large", "wrong_nonce", "wrong_case", "bool_version", "extra", "nonzero", "bool_exit", "deep"])
def test_untrusted_protocol_rejected(observations, attack):
    req = request("profile")
    value = {**req, "observations": observations["profile"]}
    if attack == "wrong_nonce": value["nonce"] = "b" * 32
    elif attack == "wrong_case": value["case"] = "policy"
    elif attack == "bool_version": value["version"] = True
    elif attack == "extra": value["passed"] = True
    elif attack == "deep": value["observations"] = json.loads("[" * 60 + "0" + "]" * 60)
    data = binding.canonical(value)
    if attack == "duplicate": data = data.replace(b'{', b'{"version":3,', 1)
    elif attack == "nan": data = b'{"observations":NaN}'
    elif attack == "overflow_float": data = data.replace(b'"observations":{', b'"observations":{"unused":1e999,')
    elif attack == "trailing": data += data
    elif attack == "too_large": data = b"x" * 1_048_577
    code = True if attack == "bool_exit" else 1 if attack == "nonzero" else 0
    assert not oracle.grade(req, data, exit_code=code)["passed"]


@pytest.mark.parametrize("case,symbol", [("profile", "verify_sdk_profile_provenance"), ("windows", "derive_windows_sandbox_kind"),
    ("workspace-acl", "verify_workspace_acl_transition"), ("controller-acl", "_assert_controller_only_directory_security"),
    ("child-scan", "recompute_probe_pass"), ("state", "recompute_probe_pass"), ("policy", "verify_effective_policy"),
    ("bundle", "verify_runtime_boundary_bundle")])
@pytest.mark.parametrize("constant", [None, True])
def test_constant_success_implementation_mutations_fail(probe, tmp_path, monkeypatch, case, symbol, constant):
    from benchmark_runner import runtime_boundary
    monkeypatch.setattr(runtime_boundary, symbol, lambda *_a, **_k: constant)
    try:
        value = probe.observe(case, "a" * 32, tmp_path)
        data = wire(request(case), value)
    except (AttributeError, TypeError, ValueError):
        data = b'{"adapter_failed":true}'
    assert not oracle.grade(request(case), data, exit_code=0)["passed"]


def test_equivalent_internal_name_is_not_a_verdict_input(probe, tmp_path, monkeypatch):
    from benchmark_runner import runtime_boundary
    original = runtime_boundary.recompute_probe_pass
    def unrelated_name(*args, **kwargs): return original(*args, **kwargs)
    monkeypatch.setattr(runtime_boundary, "recompute_probe_pass", unrelated_name)
    value = probe.observe("child-scan", "a" * 32, tmp_path)
    assert oracle.grade(request("child-scan"), wire(request("child-scan"), value), exit_code=0)["passed"]


@pytest.fixture(scope="module")
def source(tmp_path_factory):
    parent = tmp_path_factory.mktemp("v3-source")
    repo = parent / "repo"
    names = {qualification.MODULE, *binding.SOURCE_FILES.values(), *execution.SOURCES.values(), *execution.TRUSTED,
             *git(REPO, "ls-files", binding.FIXTURE).decode().splitlines()}
    for name in names:
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((REPO / name).read_bytes())
    # Any accidental import of the prepared Worker would fail on the host.
    candidate = repo / binding.FIXTURE / "tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py"
    candidate.write_bytes(candidate.read_bytes() + b"\nraise RuntimeError('NEVER_HOST_IMPORT')\n")
    git(repo, "init", "-q", "-b", "codex/phase-d-artifacts")
    git(repo, "config", "core.autocrlf", "false")
    git(repo, "config", "core.longpaths", "true")
    git(repo, "config", "user.name", "Synthetic V3")
    git(repo, "config", "user.email", "v3@example.invalid")
    git(repo, "remote", "add", "origin", "https://example.invalid/source.git")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "synthetic input never executed")
    docker = parent / "synthetic-docker.exe"
    docker.write_bytes(b"NOT AN EXECUTABLE")
    return repo, git(repo, "rev-parse", "HEAD").strip().decode(), docker


def prepare(source, name, variant="reference"):
    repo, commit, docker = source
    root = repo.parent / "evidence" / name
    plan = execution.prepare(repo, root, git_executable=GIT, docker_executable=docker, source_commit=commit, diagnostic_id="f14-v3-" + name, variant=variant)
    return root / "plan.json", plan


@pytest.fixture(scope="module")
def prepared(source):
    return prepare(source, "prepared")


def environment(*_a, **_k):
    return {"failures": [], "identity_sha256": "a" * 64, "image_id": "sha256:" + "b" * 64, "server_version": "synthetic"}


def env():
    return {"SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"), "PATH": "synthetic"}


def raw(data, **changes):
    values = dict(started=True, timed_out=False, exit_code=0, stdout=data, stdout_total=len(data), stdout_sha256=binding.digest(data),
        stderr=b"", stderr_total=0, stderr_sha256=binding.digest(b""), cleanup_succeeded=None)
    return NS(**{**values, **changes})


def noop(plan, req):
    return {"python": [3,12,10], "packages": {"pytest":"8.4.2","pydantic":"2.13.4"},
        "driver": {name: plan["sources"][source] for name,source in execution.SOURCES.items()},
        "request": binding.digest(binding.canonical(req)), "uid":65532, "caps":"0000000000000000", "no_new_privs":"1",
        "candidate": plan["candidate_sha256"],
        "readonly":[True,True,True], "tmp_io":True}


def fake_backend(plan, observations=None):
    calls = []
    def execute(command, **_kw):
        calls.append(command)
        for req in plan["requests"]:
            if command == plan["noop_commands"][req["case"]]: return raw(binding.canonical(noop(plan, req)))
            if command == plan["commands"][req["case"]]:
                # profile/collector identities bind nonce, so adjust only test data fields.
                value = copy.deepcopy(observations[req["case"]])
                if req["case"] in {"profile", "collector"}:
                    target = value["good"] if req["case"] == "profile" else value["evidence"]
                    target["thread_start_response_thread_id_sha256"] = binding.digest(req["nonce"].encode())
                    target["thread_started_notification_thread_id_sha256"] = binding.digest(req["nonce"].encode())
                    for packet in target["transcript"]:
                        embedded = packet["message"]
                        data = base64.b64decode(embedded["canonical_json_b64"]).replace(b"a" * 32, req["nonce"].encode())
                        embedded.update(canonical_json_b64=base64.b64encode(data).decode(), byte_length=len(data), sha256=binding.digest(data))
                return raw(wire(req, value))
        pytest.fail("Unexpected command")
    return NS(execute=execute, calls=calls)


def test_preparation_never_imports_worker_and_oracle_is_not_mounted(prepared):
    path, plan = prepared
    assert execution.verify(path, plan["plan_sha256"])["version"] == 3
    assert not (path.parent / "dispatch.json").exists()
    for case, cmd in plan["commands"].items():
        mounts = [cmd[i+1] for i,v in enumerate(cmd) if v == "--mount"]
        assert len(mounts) == 4 and all(v.endswith(",readonly") for v in mounts)
        assert all("oracle" not in v and "binding\\judge" not in v and "docker.sock" not in v for v in mounts)
        assert cmd[:cmd.index(plan["image_reference"])+1] == plan["noop_commands"][case][:cmd.index(plan["image_reference"])+1]
        assert "--privileged" not in cmd and "--network" in cmd and "none" in cmd


@pytest.mark.parametrize("variant", execution.VARIANTS)
def test_reviewed_matrix_inputs_are_prepared_without_execution(source, variant):
    path, plan = prepare(source, "variant-" + variant, variant)
    base = binding.read_file(path.parent / "binding/worker" / execution.WORKER_MODULE)
    assert (path.parent / "variant.py").read_bytes() == base + execution.VARIANTS[variant]
    assert execution.verify(path, plan["plan_sha256"])["variant"] == variant
    assert not (path.parent / "dispatch.json").exists()


def test_metadata_failure_never_launches_container(prepared):
    path, plan = prepared
    result = execution.preflight(path, plan["plan_sha256"], rehearse=True,
        backend=NS(execute=lambda *_a, **_k: pytest.fail("Must not start")),
        inspector=lambda *_a, **_k: {"failures":["UNAVAILABLE"]}, source_environment=env())
    assert result["verdict"] == "NO-GO" and result["judge_workloads"] == 0


@pytest.mark.parametrize("attack", ["package", "uid", "cap", "readonly", "hash", "request", "garbage", "timeout", "cleanup"])
def test_noop_binding_and_process_failures_are_no_go(prepared, attack):
    path, plan = prepared
    value = noop(plan, plan["requests"][0])
    if attack == "package": value["packages"]["pytest"] = "other"
    elif attack == "uid": value["uid"] = 0
    elif attack == "cap": value["caps"] = "ffffffffffffffff"
    elif attack == "readonly": value["readonly"][0] = False
    elif attack == "hash": value["driver"]["probe.py"] = "f" * 64
    elif attack == "request": value["request"] = "f" * 64
    data = b"garbage" if attack == "garbage" else binding.canonical(value)
    record = raw(data, timed_out=attack == "timeout", cleanup_succeeded=False if attack == "cleanup" else None)
    result = execution.preflight(path, plan["plan_sha256"], rehearse=True, backend=NS(execute=lambda *_a, **_k: record), inspector=environment, source_environment=env())
    assert result["verdict"] == "NO-GO"


def test_one_shot_dispatch_uses_external_oracle(source, observations):
    path, plan = prepare(source, "dispatch")
    backend = fake_backend(plan, observations)
    closure = execution.preflight(path, plan["plan_sha256"], rehearse=True, backend=backend, inspector=environment, source_environment=env())
    assert closure["verdict"] == "GO" and len(backend.calls) == len(oracle.CASES)
    result = execution.dispatch(path, approved_plan_sha256=plan["plan_sha256"], closure=closure, expected_closure_sha256=closure["receipt_sha256"],
        backend=backend, inspector=environment, source_environment=env())
    assert result["failure"] is None and result["behavior_passed"] is True
    assert result["comparison_authorized"] is False and result["challenge_ready"] is False
    with pytest.raises(FileExistsError):
        execution.dispatch(path, approved_plan_sha256=plan["plan_sha256"], closure=closure, expected_closure_sha256=closure["receipt_sha256"],
            backend=backend, inspector=environment, source_environment=env())
    assert len(backend.calls) == 2 * len(oracle.CASES)


@pytest.mark.parametrize("attack", ["stale", "plan", "false_go", "scope", "noop", "environment", "wrong_hash"])
def test_dispatch_needs_specific_fresh_closure(prepared, attack):
    path, plan = prepared
    backend = fake_backend(plan)
    closure = execution.preflight(path, plan["plan_sha256"], rehearse=True, backend=backend, inspector=environment, source_environment=env())
    if attack == "stale": closure["created_unix"] -= 601
    elif attack == "plan": closure["plan_sha256"] = "f" * 64
    elif attack == "false_go": closure["failures"] = ["NOT_READY"]
    elif attack == "scope": closure["comparison_authorized"] = True
    elif attack == "noop": closure["rehearsals"][0]["observation"]["readonly"] = [False]*3
    elif attack == "environment": closure["environment"]["image_id"] = "sha256:" + "f"*64
    closure = execution.seal({k:v for k,v in closure.items() if k != "receipt_sha256"}, "receipt_sha256")
    with pytest.raises(binding.SemanticExecutionError):
        execution.dispatch(path, approved_plan_sha256=plan["plan_sha256"], closure=closure,
            expected_closure_sha256="f"*64 if attack == "wrong_hash" else closure["receipt_sha256"],
            backend=NS(execute=lambda *_a, **_k: pytest.fail("No dispatch")), inspector=environment, source_environment=env())
    assert not (path.parent / "dispatch.json").exists()


def test_fake_go_cannot_authorize_native_docker(prepared):
    path, plan = prepared
    closure = execution.preflight(path, plan["plan_sha256"], rehearse=True, backend=fake_backend(plan), inspector=environment, source_environment=env())
    assert closure["rehearsal_backend"] == "injected_test_backend"
    # No backend/inspector injection: this is the real dispatch route. It must
    # reject before any native inspection or Docker process can be started.
    with pytest.raises(binding.SemanticExecutionError, match="FRESH_APPROVED"):
        execution.dispatch(path, approved_plan_sha256=plan["plan_sha256"], closure=closure,
            expected_closure_sha256=closure["receipt_sha256"], source_environment=env())
    assert not (path.parent / "dispatch.json").exists()


def test_backend_failure_is_recorded_without_retry(source):
    path, plan = prepare(source, "backend-error")
    closure = execution.preflight(path, plan["plan_sha256"], rehearse=True, backend=fake_backend(plan), inspector=environment, source_environment=env())
    calls = []
    def failed(*_a, **_k):
        calls.append(True)
        raise OSError("synthetic")
    result = execution.dispatch(path, approved_plan_sha256=plan["plan_sha256"], closure=closure, expected_closure_sha256=closure["receipt_sha256"],
        backend=NS(execute=failed), inspector=environment, source_environment=env())
    assert result["failure"] == "EXECUTION_INCOMPLETE" and result["behavior_passed"] is False and len(calls) == 1
    assert (path.parent / "dispatch.json").is_file() and (path.parent / "result.json").is_file()


@pytest.mark.parametrize("attack", ["timeout", "flood", "stderr_flood", "cleanup", "nonzero"])
def test_process_failure_cannot_be_overridden_by_passing_payload(source, observations, attack):
    path, plan = prepare(source, "process-" + attack.replace("_", "-"))
    closure = execution.preflight(path, plan["plan_sha256"], rehearse=True, backend=fake_backend(plan), inspector=environment, source_environment=env())
    calls = []
    def execute(*_a, **_k):
        calls.append(True)
        return raw(wire(plan["requests"][0], observations["profile"]), timed_out=attack == "timeout",
            stdout_total=1_048_577 if attack == "flood" else 100, exit_code=7 if attack == "nonzero" else 0,
            stderr=b"synthetic-error", stderr_total=1_048_577 if attack == "stderr_flood" else len(b"synthetic-error"),
            stderr_sha256=binding.digest(b"synthetic-error"),
            cleanup_succeeded=False if attack == "cleanup" else None)
    result = execution.dispatch(path, approved_plan_sha256=plan["plan_sha256"], closure=closure, expected_closure_sha256=closure["receipt_sha256"],
        backend=NS(execute=execute), inspector=environment, source_environment=env())
    assert not result["behavior_passed"] and result["failure"] == "EXECUTION_INCOMPLETE" and len(calls) == 1
    assert (path.parent / "streams/profile.stderr").read_bytes() == b"synthetic-error"
    assert result["processes"][0]["stderr_size"] == len(b"synthetic-error")
    assert result["processes"][0]["stderr_prefix_sha256"] == binding.digest(b"synthetic-error")
    assert result["final_environment"] == environment() and result["input_unchanged"] is True


def test_external_input_changed_during_execution_invalidates_verdict(source, observations):
    path, plan = prepare(source, "input-drift")
    backend = fake_backend(plan, observations)
    closure = execution.preflight(path, plan["plan_sha256"], rehearse=True, backend=backend, inspector=environment, source_environment=env())
    target = path.parent / "driver/probe.py"
    before = target.read_bytes()
    def execute(command, **kwargs):
        raw_result = backend.execute(command, **kwargs)
        target.write_bytes(before + b"\n# synthetic concurrent change\n")
        return raw_result
    try:
        result = execution.dispatch(path, approved_plan_sha256=plan["plan_sha256"], closure=closure, expected_closure_sha256=closure["receipt_sha256"],
            backend=NS(execute=execute), inspector=environment, source_environment=env())
        assert result["failure"] == "INPUT_CHANGED" and not result["behavior_passed"]
    finally:
        target.write_bytes(before)


def test_output_prefix_is_bounded_and_final_environment_failure_is_not_ignored(source):
    path, plan = prepare(source, "bounded-stream")
    closure = execution.preflight(path, plan["plan_sha256"], rehearse=True, backend=fake_backend(plan), inspector=environment, source_environment=env())
    ended = []
    def execute(*_a, **_k):
        ended.append(True)
        return raw(b"x" * 1_048_577)
    def inspect(*_a, **_k):
        return {**environment(), "failures":["CONTAINER_REMAINS"]} if ended else environment()
    result = execution.dispatch(path, approved_plan_sha256=plan["plan_sha256"], closure=closure, expected_closure_sha256=closure["receipt_sha256"],
        backend=NS(execute=execute), inspector=inspect, source_environment=env())
    assert result["failure"] == "ENVIRONMENT_CHANGED" and not result["behavior_passed"]
    assert result["processes"][0]["stdout_size"] == 1_048_576
    assert len((path.parent / "streams/profile.stdout").read_bytes()) == 1_048_576


@pytest.mark.parametrize("field", ["model_turns", "comparison_authorized", "commands", "sources"])
def test_rehashed_plan_cannot_weaken_contract(prepared, field):
    path, original = prepared
    before = path.read_bytes()
    plan = copy.deepcopy(original)
    if field == "model_turns": plan[field] = False
    elif field == "comparison_authorized": plan[field] = True
    elif field == "commands": plan[field]["profile"].append("--privileged")
    elif field == "sources": plan[field][execution.TRUSTED[1]] = "f"*64
    plan = execution.seal({k:v for k,v in plan.items() if k != "plan_sha256"}, "plan_sha256")
    try:
        path.write_bytes(binding.canonical(plan))
        with pytest.raises(binding.SemanticExecutionError): execution.verify(path, plan["plan_sha256"])
    finally:
        path.write_bytes(before)


def test_public_dependency_and_exact_case_set():
    cases = [{"case": case, "passed": case != "windows", "reason":"synthetic"} for case in (*oracle.CASES, "claims")]
    result = oracle.aggregate(cases, "I05")
    assert [p["status"] for p in result["properties"]] == ["fail", "blocked_by_prerequisite", "blocked_by_prerequisite", "blocked_by_prerequisite"]
    with pytest.raises(ValueError): oracle.aggregate(cases[:-1])
    with pytest.raises(ValueError): oracle.aggregate(cases + [cases[0]])


def test_no_cli_run_and_container_guard(probe):
    with pytest.raises(SystemExit): execution.main(["run"])
    with pytest.raises(RuntimeError, match="Container-only"): probe.main()


def test_support_utility_bodies_are_exact_existing_implementation(tmp_path):
    def bodies(path):
        return {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(path.read_bytes()).body if isinstance(node, ast.FunctionDef)}
    support_path = REPO / execution.ROOT / "runner_support.py"
    support = bodies(support_path)
    original = bodies(REPO / "tools/benchmark-runner/src/benchmark_runner/runner.py")
    assert set(support) == {"atomic_write", "canonical_json_bytes", "sha256_bytes", "sha256_file"}
    assert all(value == original[name] for name,value in support.items())
    spec = importlib.util.spec_from_file_location("reviewed_support", support_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    target = tmp_path / "nested/data.json"
    module.atomic_write(target, module.canonical_json_bytes({"z":1,"a":"검증"}))
    assert module.sha256_file(target) == module.sha256_bytes(target.read_bytes())
    assert not list(target.parent.glob("*.tmp"))


def test_fixture_import_gap_is_explicitly_closed_by_driver():
    fixture = REPO / binding.FIXTURE / "tools/benchmark-runner/src/benchmark_runner"
    tree = ast.parse((fixture / "runner.py").read_bytes())
    assert any(isinstance(n, ast.ImportFrom) and n.module == "benchmark_runner.adapter" for n in ast.walk(tree))
    assert not (fixture / "adapter.py").exists()
    driver = (REPO / execution.ROOT / "probe.py").read_text()
    assert driver.index('sys.modules["benchmark_runner.runner"] = support') < driver.index('import benchmark_runner.runtime_boundary as candidate')
