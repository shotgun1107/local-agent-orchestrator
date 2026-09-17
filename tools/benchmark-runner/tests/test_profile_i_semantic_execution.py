"""Wiring tests with inspected Git inputs and in-memory Docker results only."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace as NS

import pytest

from benchmark_runner import profile_i_semantic_execution as se

REPO = Path(__file__).resolve().parents[3]
GIT = Path(shutil.which("git")).resolve()


def git(repo, *args):
    return subprocess.run([str(GIT), *args], cwd=repo, capture_output=True, check=True).stdout


@pytest.fixture(scope="module")
def source(tmp_path_factory):
    parent = tmp_path_factory.mktemp("semantic-source")
    repo = parent / "repo"
    repo.mkdir()
    names = list(se.SOURCE_FILES.values())
    names += git(REPO, "ls-files", se.FIXTURE).decode().splitlines()
    for name in names:
        dest = repo / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((REPO / name).read_bytes())
    git(repo, "init", "-q", "-b", "codex/phase-d-artifacts")
    git(repo, "config", "core.autocrlf", "false")
    git(repo, "config", "core.longpaths", "true")
    git(repo, "config", "user.name", "Synthetic F14")
    git(repo, "config", "user.email", "f14@example.invalid")
    git(repo, "remote", "add", "origin", "https://example.invalid/reviewed-source.git")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "reviewed synthetic source")
    docker = parent / "never-executed.exe"
    docker.write_bytes(b"synthetic Docker identity - never executable")
    return repo, git(repo, "rev-parse", "HEAD").strip().decode(), docker


@pytest.fixture(scope="module")
def prepared(source):
    repo, commit, docker = source
    root = repo.parent / "evidence" / "prepared"
    plan = se.prepare(repo, root, git_executable=GIT, docker_executable=docker,
                      source_commit=commit, diagnostic_id="f14-reviewed-reference")
    return root / "plan.json", plan


def environment(plan):
    return {"SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"), "PATH": "synthetic"}


def observed_environment(*_args, **_kwargs):
    return {"failures": [], "identity_sha256": "a" * 64, "image_id": "sha256:" + "b" * 64, "server_version": "29.6.2"}


def observation(plan, *, failed=None):
    statuses, rows = {}, []
    for requirement in se.selected_properties(plan["contract"], plan["task_id"]):
        key = requirement["property_id"]
        blocked = any(statuses[p] != "pass" for p in requirement["prerequisite_ids"])
        cases = [] if blocked else [{"case_id": case, "passed": key != failed} for case in requirement["case_ids"]]
        status = "blocked_by_prerequisite" if blocked else "fail" if key == failed else "pass"
        rows.append({"property_id": key, "status": status, "cases": cases})
        statuses[key] = status
    hashes = {r["path"]: r["sha256"] for r in plan["judge_files"]}
    passed = all(r["status"] == "pass" for r in rows)
    case_map = {r["property_id"]: r["case_ids"] for r in plan["contract"]["properties"] if r["property_id"] != se.CLAIM}
    return dict(schema_version=2, kind="profile_i_behavior_observation", scope="synthetic_behavior_only",
        properties=rows, behavior_passed=passed, os_enforcement_verified=False, challenge_ready=False, model_turns=0,
        experiment_id="profile-i-semantic-diagnostic", cell_id=plan["diagnostic_id"], checker_run_status="completed",
        aggregate_status="pass" if passed else "fail", checker_sha256=hashes["checker/check_properties.py"],
        oracle_sha256=hashes["checker/test_behavior.py"], contract_sha256=plan["contract_sha256"],
        case_set_sha256=se.digest(json.dumps(case_map, sort_keys=True).encode()),
        workspace_before_sha256=plan["worker_sha256"], workspace_after_sha256=plan["worker_sha256"], workspace_mutated=False,
        invocation_sha256=plan["invocation_sha256"], task_id=plan["task_id"], oracle_isolation=se.ISOLATION, comparison_authorized=False)


def raw(data, *, exit_code=0, started=True, timed_out=False):
    return NS(stdout=data, stdout_total=len(data), stdout_sha256=se.digest(data), stderr_sha256=se.digest(b""),
              exit_code=exit_code, started=started, timed_out=timed_out, cleanup_succeeded=None)


def encode(value):
    return (se.MARKER + json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def test_preparation_is_bound_nonexecuting_and_reference_is_not_mounted(prepared):
    path, plan = prepared
    assert se.verify_plan(path, plan["plan_sha256"]) == plan
    assert plan["comparison_authorized"] is False and plan["model_turns"] == plan["phase_f_claims"] == 0
    assert not (path.parent / "dispatch.json").exists()
    assert (path.parent / "bundle/reference.patch").is_file()
    assert not (path.parent / "judge/reference.patch").exists()
    assert plan["command"][plan["command"].index("--network") + 1] == "none"
    assert plan["command"][plan["command"].index("--user") + 1] == "65532:65532"
    assert "--read-only" in plan["command"] and "ALL" in plan["command"]
    assert plan["image_reference"] in plan["command"]
    assert plan["noop_command"][:plan["noop_command"].index(se.DOCKER_JUDGE_IMAGE) + 1] == plan["command"][:plan["command"].index(se.DOCKER_JUDGE_IMAGE) + 1]


@pytest.mark.parametrize("task_id", [None, *[f"I{i:02d}" for i in range(1, 9)]])
def test_checker_case_contract_and_consumer_agree_without_importing_worker(prepared, tmp_path, task_id):
    import importlib.util
    path, original = prepared
    plan = copy.deepcopy(original)
    plan["task_id"] = task_id
    checker_path = REPO / se.ROOT / "check_properties.py"
    spec = importlib.util.spec_from_file_location("reviewed_contract_test_checker", checker_path)
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    checker.validate_case_contract(plan["contract"])
    assert checker._workspace_hash(path.parent / "worker") == plan["worker_sha256"]
    # Known synthetic functions, not the prepared Worker/runtime or real SDK.
    oracle = NS(**{name: (lambda: None) for cases in checker.PROPERTIES.values() for name in cases})
    evaluated = checker.evaluate_loaded_oracle(oracle, tmp_path, task_id=task_id, workspace=path.parent / "worker")
    value = observation(plan)
    value.update(evaluated)
    value["aggregate_status"] = "pass" if value["behavior_passed"] else "fail"
    assert se.verify_observation(plan, encode(value), exit_code=0 if value["behavior_passed"] else 1) == value


@pytest.mark.parametrize("failed", [None, "I-P03-ELEVATED-IDENTITY", "I-P10-EVIDENCE-CLAIM-ALIGNMENT"])
def test_valid_observations_preserve_case_results_and_diagnostic_only_scope(prepared, failed):
    _, plan = prepared
    value = observation(plan, failed=failed)
    assert se.verify_observation(plan, encode(value), exit_code=0 if failed is None else 1) == value


@pytest.mark.parametrize("field,bad", [
    ("schema_version", True), ("schema_version", 1), ("challenge_ready", True), ("model_turns", False),
    ("model_turns", 1), ("comparison_authorized", True), ("os_enforcement_verified", True),
    ("invocation_sha256", "f"*64), ("checker_sha256", "f"*64), ("oracle_sha256", "f"*64),
    ("contract_sha256", "f"*64), ("case_set_sha256", "f"*64), ("cell_id", "other"),
    ("workspace_after_sha256", "f"*64), ("workspace_mutated", True), ("task_id", "I01"),
    ("scope", "production"), ("oracle_isolation", "safe"), ("behavior_passed", 1),
    ("aggregate_status", "fail"), ("properties", []),
])
def test_wrong_identity_or_unearned_scope_is_rejected(prepared, field, bad):
    _, plan = prepared
    value = observation(plan)
    value[field] = bad
    with pytest.raises(se.SemanticExecutionError):
        se.verify_observation(plan, encode(value), exit_code=0)


@pytest.mark.parametrize("attack", ["missing_case", "duplicate_case", "wrong_case", "false_case", "integer_bool", "duplicate_property", "unblocked_dependent", "extra_field"])
def test_case_coverage_and_aggregates_are_recomputed(prepared, attack):
    _, plan = prepared
    value = observation(plan)
    row = value["properties"][0]
    if attack == "missing_case": row["cases"].pop()
    elif attack == "duplicate_case": row["cases"].append(row["cases"][0])
    elif attack == "wrong_case": row["cases"][0]["case_id"] = "fake"
    elif attack == "false_case": row["cases"][0]["passed"] = False
    elif attack == "integer_bool": row["cases"][0]["passed"] = 1
    elif attack == "duplicate_property": value["properties"].append(row)
    elif attack == "extra_field": value["untrusted_extra"] = True
    elif attack == "unblocked_dependent":
        value = observation(plan, failed="I-P03-ELEVATED-IDENTITY")
        value["properties"][3]["status"] = "pass"
    with pytest.raises(se.SemanticExecutionError):
        se.verify_observation(plan, encode(value), exit_code=0)


@pytest.mark.parametrize("attack", ["no_marker", "two_markers", "duplicate_json_key", "too_large", "wrong_exit"])
def test_result_framing_is_strict(prepared, attack):
    _, plan = prepared
    data = encode(observation(plan))
    if attack == "no_marker": data = b'{}'
    elif attack == "two_markers": data += data
    elif attack == "duplicate_json_key": data = data.replace(b'{', b'{"schema_version":2,', 1)
    elif attack == "too_large": data = b"x" * (plan["limits"]["stdout_limit_bytes"] + 1)
    with pytest.raises(se.SemanticExecutionError):
        se.verify_observation(plan, data, exit_code=1 if attack == "wrong_exit" else 0)


def test_metadata_unavailable_never_dispatches_noop(prepared):
    path, plan = prepared
    backend = NS(execute=lambda *_a, **_k: pytest.fail("Docker must not run"))
    result = se.preflight(path, plan["plan_sha256"], rehearse=True, backend=backend,
        inspector=lambda *_a, **_k: {"failures": ["SERVER_UNAVAILABLE"]})
    assert result["verdict"] == "NO-GO"
    assert result["judge_workloads"] == result["model_turns"] == 0


def test_read_only_inspection_fails_when_daemon_is_off(prepared):
    _, plan = prepared
    calls = []
    def runner(argv, **kwargs):
        calls.append(argv)
        return NS(returncode=1, stdout=b"", stderr=b"synthetic daemon unavailable")
    result = se.inspect_environment(plan, source_environment=environment(plan), runner=runner)
    assert result["failures"] and result["image_id"] is None
    assert all("run" not in command for command in calls)


@pytest.mark.parametrize("name", ["OPENAI_API_KEY", "CODEX_API_KEY", "DOCKER_HOST", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH"])
def test_unbound_environment_fails_before_docker_read(prepared, name):
    _, plan = prepared
    from benchmark_runner.realistic_docker_judge import DockerJudgeError
    with pytest.raises((se.SemanticExecutionError, DockerJudgeError)):
        se.inspect_environment(plan, source_environment={**environment(plan), name: "synthetic-not-a-secret"},
                               runner=lambda *_a, **_k: pytest.fail("No invocation"))


def noop_raw(plan):
    hashes = {r["path"]: r["sha256"] for r in plan["judge_files"]}
    return raw(json.dumps(dict(python=[3,12,10], packages={"pytest":"8.4.2","pydantic":"2.13.4"},
        checker_sha256=hashes["checker/check_properties.py"], oracle_sha256=hashes["checker/test_behavior.py"],
        contract_sha256=hashes["checker/semantic-contract.json"], workspace_exists=True, output_io=True)).encode())


def test_noop_and_dispatch_are_separate_and_one_shot(source):
    repo, commit, docker = source
    root = repo.parent / "evidence" / "one-shot"
    plan = se.prepare(repo, root, git_executable=GIT, docker_executable=docker, source_commit=commit, diagnostic_id="f14-one-shot")
    path = root / "plan.json"
    calls = []
    def execute(command, **kwargs):
        calls.append(command)
        return noop_raw(plan) if command == plan["noop_command"] else raw(encode(observation(plan)))
    backend = NS(execute=execute)
    closure = se.preflight(path, plan["plan_sha256"], rehearse=True, backend=backend,
                           source_environment=environment(plan), inspector=observed_environment)
    assert closure["verdict"] == "GO" and calls == [plan["noop_command"]]
    assert not (root / "dispatch.json").exists()
    result = se.dispatch_diagnostic(path, approved_plan_sha256=plan["plan_sha256"], closure=closure,
        expected_closure_sha256=closure["receipt_sha256"], backend=backend,
        source_environment=environment(plan), inspector=observed_environment)
    assert result["diagnostic_passed"] is True and result["challenge_ready"] is False
    assert calls == [plan["noop_command"], plan["command"]]
    with pytest.raises(FileExistsError):
        se.dispatch_diagnostic(path, approved_plan_sha256=plan["plan_sha256"], closure=closure,
            expected_closure_sha256=closure["receipt_sha256"], backend=backend,
            source_environment=environment(plan), inspector=observed_environment)
    assert len(calls) == 2


def test_changed_input_fails_before_execution(prepared):
    path, plan = prepared
    target = path.parent / "judge/checker/semantic-contract.json"
    before = target.read_bytes()
    try:
        target.write_bytes(before + b"\n")
        with pytest.raises(se.SemanticExecutionError, match="INPUT_TREE_CHANGED"):
            se.verify_plan(path, plan["plan_sha256"])
    finally:
        target.write_bytes(before)


def test_existing_destination_is_preserved(prepared, source):
    path, plan = prepared
    repo, commit, docker = source
    before = path.read_bytes()
    with pytest.raises(se.SemanticExecutionError, match="FRESH"):
        se.prepare(repo, path.parent, git_executable=GIT, docker_executable=docker, source_commit=commit, diagnostic_id="f14-reuse")
    assert path.read_bytes() == before


def test_cli_does_not_expose_an_execution_command():
    with pytest.raises(SystemExit):
        se.main(["run"])


@pytest.mark.parametrize("attack", [None, "context", "image", "server", "residue"])
def test_inspection_binds_context_image_platform_and_no_residue(prepared, attack):
    _, plan = prepared
    responses = {
        "context": [{"Name": plan["docker_context"]}],
        "image": [{"Id": "sha256:" + "b" * 64, "RepoDigests": [plan["image_reference"]], "Os": "linux", "Architecture": "amd64"}],
        "version": {"Os": "linux", "Arch": "amd64", "Version": "synthetic"},
    }
    if attack == "context": responses["context"][0]["Name"] = "unbound"
    elif attack == "image": responses["image"][0]["RepoDigests"] = []
    elif attack == "server": responses["version"]["Arch"] = "arm64"
    def runner(argv, **_kwargs):
        data = (b'"f14-residue"\n' if attack == "residue" else b'') if argv[1] == "container" else json.dumps(responses[argv[1]]).encode()
        return NS(returncode=0, stdout=data, stderr=b'')
    result = se.inspect_environment(plan, source_environment=environment(plan), runner=runner)
    assert bool(result["failures"]) == (attack is not None)


@pytest.mark.parametrize("field", ["branch", "origin"])
def test_changed_source_binding_is_rejected(prepared, source, field):
    path, plan = prepared
    repo, _, _ = source
    try:
        if field == "branch": git(repo, "branch", "-m", "synthetic-changed")
        else: git(repo, "remote", "set-url", "origin", "https://example.invalid/changed.git")
        with pytest.raises(se.SemanticExecutionError, match="SOURCE_BRANCH_OR_ORIGIN_CHANGED"):
            se.verify_plan(path, plan["plan_sha256"])
    finally:
        if field == "branch": git(repo, "branch", "-m", plan["source_branch"])
        else: git(repo, "remote", "set-url", "origin", plan["source_origin"])


@pytest.mark.parametrize("attack", ["scope", "automatic", "limit", "source_tree", "command", "noop", "extra_reference_mount"])
def test_even_rehashed_plan_cannot_change_fixed_execution_contract(prepared, attack):
    path, original = prepared
    before = path.read_bytes()
    changed = copy.deepcopy(original)
    if attack == "scope": changed["purpose"] = "untrusted_worker_evaluation"
    elif attack == "automatic": changed["automatic_continuation"] = True
    elif attack == "limit": changed["limits"]["pids_limit"] = 512
    elif attack == "source_tree": changed["source_tree"] = "f" * 40
    elif attack == "command": changed["command"][changed["command"].index("none")] = "host"
    elif attack == "noop": changed["noop_command"][-1] = "import forbidden_worker"
    elif attack == "extra_reference_mount": changed["command"].extend(["--mount", "/private"])
    changed["plan_sha256"] = se.digest(se.canonical({k:v for k,v in changed.items() if k != "plan_sha256"}))
    try:
        path.write_bytes(se.canonical(changed))
        with pytest.raises(se.SemanticExecutionError):
            se.verify_plan(path, changed["plan_sha256"])
    finally:
        path.write_bytes(before)


@pytest.mark.parametrize("attack", ["no_go", "stale", "different_plan", "missing_noop", "changed_environment", "bad_external_hash", "fake_noop", "comparison", "bad_time"])
def test_dispatch_requires_fresh_specific_closure(prepared, attack):
    path, plan = prepared
    closure = dict(kind="profile_i_semantic_preflight", plan_sha256=plan["plan_sha256"], verdict="GO", failures=[],
                   purpose=se.PURPOSE, comparison_authorized=False, judge_workloads=0, model_turns=0, phase_f_claims=0,
                   noop=json.loads(noop_raw(plan).stdout), environment=observed_environment(), created_unix=int(se.time.time()))
    if attack == "no_go": closure["verdict"] = "NO-GO"
    elif attack == "stale": closure["created_unix"] -= 1000
    elif attack == "different_plan": closure["plan_sha256"] = "f" * 64
    elif attack == "missing_noop": closure["noop"] = None
    elif attack == "fake_noop": closure["noop"] = {"synthetic":True}
    elif attack == "comparison": closure["comparison_authorized"] = True
    elif attack == "bad_time": closure["created_unix"] = "wrong"
    closure["receipt_sha256"] = se.digest(se.canonical(closure))
    inspector = (lambda *_a, **_k: {"changed": True}) if attack == "changed_environment" else observed_environment
    backend = NS(execute=lambda *_a, **_k: pytest.fail("No workload permitted"))
    with pytest.raises(se.SemanticExecutionError):
        se.dispatch_diagnostic(path, approved_plan_sha256=plan["plan_sha256"], closure=closure,
            expected_closure_sha256="f" * 64 if attack == "bad_external_hash" else closure["receipt_sha256"],
            backend=backend, source_environment=environment(plan), inspector=inspector)
    assert not (path.parent / "dispatch.json").exists()


@pytest.mark.parametrize("attack", ["bad_package", "bad_hash", "wrong_image", "invalid_json", "not_object", "wrong_python_type", "cleanup_failed"])
def test_noop_must_prove_exact_required_environment(prepared, attack):
    path, plan = prepared
    data = noop_raw(plan).stdout
    if attack == "invalid_json": data = b"not json"
    else:
        value = json.loads(data)
        if attack == "bad_package": value["packages"]["pytest"] = "0.0.0"
        elif attack == "bad_hash": value["checker_sha256"] = "f" * 64
        elif attack == "not_object": value = []
        elif attack == "wrong_python_type": value["python"] = 312
        data = json.dumps(value).encode()
    inspector = (lambda *_a, **_k: {"failures":["IMAGE_IDENTITY_MISMATCH"]}) if attack == "wrong_image" else observed_environment
    record = raw(data)
    if attack == "cleanup_failed": record.cleanup_succeeded = False
    result = se.preflight(path, plan["plan_sha256"], rehearse=True, backend=NS(execute=lambda *_a, **_k: record),
                          source_environment=environment(plan), inspector=inspector)
    assert result["verdict"] == "NO-GO" and result["comparison_authorized"] is False
