"""Synthetic archived fixtures test verification only; never native evidence."""
import copy
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from benchmark_runner import profile_i_qualification as q
from test_profile_i_isolated_execution import (
    source, probe, observations, prepare, fake_backend, environment, env,
    execution, binding, oracle, GIT,
)


def write(path, value):
    path.write_bytes(binding.canonical(value))


def reseal(path, field, value):
    sealed = execution.seal({k:v for k,v in value.items() if k != field}, field)
    write(path, sealed)
    return sealed


@pytest.fixture(scope="module")
def saved(source, observations):
    path, plan = prepare(source, "archive-fixture")
    backend = fake_backend(plan, observations)
    closure = execution.preflight(path, plan["plan_sha256"], rehearse=True, backend=backend, inspector=environment, source_environment=env())
    result = execution.dispatch(path, approved_plan_sha256=plan["plan_sha256"], closure=closure, expected_closure_sha256=closure["receipt_sha256"],
        backend=backend, inspector=environment, source_environment=env())
    with pytest.raises(ValueError, match="NATIVE_RESULT_CONTRACT"):
        q.verify_run(path.parent, plan["plan_sha256"], result["result_sha256"])
    # Fabricated archive metadata exercises the reader, NOT native dispatch.
    # This remains under pytest tmp and is never a qualification artifact.
    closure["rehearsal_backend"] = "native_docker"
    closure = reseal(path.parent / "preflight.json", "receipt_sha256", closure)
    marker = binding.parse((path.parent / "dispatch.json").read_bytes())
    marker["closure_sha256"] = closure["receipt_sha256"]
    write(path.parent / "dispatch.json", marker)
    result["execution_backend"] = "native_docker"
    result = reseal(path.parent / "result.json", "result_sha256", result)
    return path.parent, plan, result


def test_saved_evidence_is_independently_recomputed(saved):
    root, plan, result = saved
    checked = q.verify_run(root, plan["plan_sha256"], result["result_sha256"])
    assert checked["matched_expectation"] and checked["process_count"] == 11


@pytest.mark.parametrize("attack", ["stdout", "stderr", "verdict", "counter", "prefix", "scope", "failure", "environment", "injected", "extra-stream"])
def test_saved_evidence_tampering_is_rejected(saved, attack):
    root, plan, original = saved
    result = copy.deepcopy(original)
    target = root / "result.json"
    before = target.read_bytes()
    changed = None
    if attack in {"stdout", "stderr"}:
        changed = root / ("streams/profile." + attack)
    elif attack == "extra-stream": changed = root / "streams/extra.stdout"
    previous = changed.read_bytes() if changed and changed.exists() else None
    try:
        if changed: changed.write_bytes(b"tampered")
        if attack == "verdict": result["properties"][0]["status"] = "fail"
        elif attack == "counter": result["processes"][0]["stdout_total"] += 1
        elif attack == "prefix": result["processes"][0]["stdout_prefix_sha256"] = "f"*64
        elif attack == "scope": result["model_turns"] = False
        elif attack == "failure": result["failure"] = "EXECUTION_INCOMPLETE"
        elif attack == "environment": result["final_environment"]["identity_sha256"] = "f"*64
        elif attack == "injected": result["execution_backend"] = "injected_test_backend"
        result = reseal(target, "result_sha256", result)
        with pytest.raises(ValueError): q.verify_run(root, plan["plan_sha256"], result["result_sha256"])
    finally:
        target.write_bytes(before)
        if changed:
            if previous is None: changed.unlink()
            else: changed.write_bytes(previous)


@pytest.fixture
def matrix(tmp_path):
    value = execution.seal({"version":1, "kind":"f14_fixed_preparation_matrix", "source_commit":"a"*40,
        "verifier_sha256":binding.digest(Path(q.__file__).read_bytes().replace(b"\r\n", b"\n")),
        "variants":[{"variant":v,"plan_sha256":"b"*64} for v in q.VARIANTS],
        "scope":"fixed_synthetic_qualification_only", "comparison_authorized":False, "model_turns":0, "phase_f_claims":0}, "manifest_sha256")
    write(tmp_path / "matrix.json", value)
    return tmp_path, value


@pytest.mark.parametrize("failure", ["preflight", "exception", "unexpected"])
def test_matrix_stops_and_preserves_summary_without_retry(matrix, monkeypatch, failure):
    root, value = matrix
    (root / "reference").mkdir()
    calls = []
    def preflight(*args, **kwargs):
        calls.append("preflight")
        if failure == "exception": raise ValueError("not exported")
        return {"verdict":"NO-GO" if failure == "preflight" else "GO", "receipt_sha256":"c"*64}
    monkeypatch.setattr(execution, "preflight", preflight)
    monkeypatch.setattr(execution, "dispatch", lambda *a,**k: {"result_sha256":"d"*64})
    monkeypatch.setattr(q, "verify_run", lambda *a,**k: {"matched_expectation":False})
    result = q.run_approved(root, value["manifest_sha256"], authorization_note="Unit test only")
    assert result["qualification_passed"] is False and result["failure"] and calls == ["preflight"]
    assert (root / "matrix-result.json").exists()
    with pytest.raises(FileExistsError): q.run_approved(root, value["manifest_sha256"], authorization_note="Unit test only")
    assert calls == ["preflight"]


@pytest.mark.parametrize("variants", [["../outside"], ["equivalent"], ["reference", "reference"], list(q.VARIANTS)+["reference"]])
def test_summary_variants_cannot_direct_paths(matrix, monkeypatch, variants):
    root, value = matrix
    summary = execution.seal({"version":1,"manifest_sha256":value["manifest_sha256"],"scope":value["scope"],
        "comparison_authorized":False,"challenge_ready":False,"model_turns":0,"phase_f_claims":0,
        "rows":[{"variant":v,"result_sha256":"c"*64} for v in variants]}, "summary_sha256")
    write(root / "matrix-result.json", summary)
    monkeypatch.setattr(q, "verify_run", lambda *a,**k: pytest.fail("Must reject before path access"))
    with pytest.raises(ValueError, match="SUMMARY_VARIANT_SEQUENCE"):
        q.verify_matrix(root, value["manifest_sha256"], summary["summary_sha256"])


def test_matrix_prepare_binds_all_variants_without_execution(source):
    repo, commit, docker = source
    root = repo.parent / "evidence/fixed-matrix"
    value = q.prepare(repo, root, source_commit=commit, git_executable=GIT, docker_executable=docker, token="synthetic")
    assert q.manifest(root, value["manifest_sha256"]) == value
    assert [r["variant"] for r in value["variants"]] == list(q.VARIANTS)
    assert not list(root.rglob("dispatch.json"))


def test_timeout_and_flood_need_specific_evidence():
    cases = {"claims":{"passed":True}}
    result = {"behavior_passed":False,"failure":"EXECUTION_INCOMPLETE", "processes":[
        {"timed_out":True,"exit_code":None,"cleanup_succeeded":False}]}
    assert not q.matches("timeout", result, cases, {})
    result["processes"][0]["cleanup_succeeded"] = True
    assert q.matches("timeout", result, cases, {})
    result["processes"][0].update(stdout_total=q.LIMIT+1, stdout_size=q.LIMIT)
    assert not q.matches("output-flood", result, cases, {"profile.stdout":b"y"*q.LIMIT})
    assert q.matches("output-flood", result, cases, {"profile.stdout":b"x"*q.LIMIT})
