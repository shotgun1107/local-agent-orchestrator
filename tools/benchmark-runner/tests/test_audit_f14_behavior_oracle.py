"""Qualify the independent oracle against reviewed in-memory mutations only."""
import importlib.util
import inspect
from pathlib import Path

import pytest


ORACLE = Path(__file__).resolve().parents[1] / "qualifications/profile-i-semantic-v2/test_behavior.py"


def load_oracle():
    spec = importlib.util.spec_from_file_location("independent_profile_i_oracle", ORACLE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def invoke(function, tmp_path, monkeypatch):
    args = {"tmp_path": tmp_path, "monkeypatch": monkeypatch}
    return function(**{key: args[key] for key in inspect.signature(function).parameters})


@pytest.mark.parametrize("symbol,test", [
    ("verify_sdk_profile_provenance", "test_transcript_rejects_thread_mismatch_and_turn_start"),
    ("derive_sdk_profile_provenance", "test_complete_zero_turn_transcript_is_recomputed"),
    ("verify_workspace_acl_transition", "test_workspace_acl_transition_rejects_an_extra_ace"),
    ("_assert_controller_only_directory_security", "test_controller_acl_rejects_extra_grant_without_changing_os_acl"),
    ("derive_windows_sandbox_kind", "test_windows_kind_requires_readiness_identity_and_child_equality"),
    ("recompute_probe_pass", "test_child_and_input_scan_reject_disclosure_and_incomplete_scan"),
    ("recompute_probe_pass", "test_p08_requires_worker_metadata_nondisclosure_and_controller_invariants"),
    ("verify_runtime_boundary_bundle", "test_candidate_result_and_exact_four_file_bundle"),
])
@pytest.mark.parametrize("return_value", [None, True])
def test_noop_and_constant_success_do_not_satisfy_behavior(symbol, test, return_value, tmp_path, monkeypatch):
    oracle = load_oracle()
    replacement = lambda *_a, **_kw: return_value
    monkeypatch.setattr(oracle.runtime_boundary, symbol, replacement)
    if hasattr(oracle, symbol):
        monkeypatch.setattr(oracle, symbol, replacement)
    # The mutations must make the oracle fail, not silently earn a property pass.
    with pytest.raises((AssertionError, TypeError, AttributeError, ValueError, KeyError, pytest.fail.Exception)):
        invoke(getattr(oracle, test), tmp_path, monkeypatch)


def test_equivalent_api_with_different_internal_function_names_passes(tmp_path, monkeypatch):
    oracle = load_oracle()
    original = oracle.runtime_boundary.recompute_probe_pass
    def equivalent_implementation_with_unrelated_name(*args, **kwargs):
        return original(*args, **kwargs)
    monkeypatch.setattr(oracle.runtime_boundary, "recompute_probe_pass", equivalent_implementation_with_unrelated_name)
    invoke(oracle.test_child_and_input_scan_reject_disclosure_and_incomplete_scan, tmp_path, monkeypatch)


def test_new_bundle_is_closed_nonready_and_preserves_reference(tmp_path):
    import hashlib
    import json
    root = Path(__file__).resolve().parents[3]
    script = root / "tools/benchmark-runner/scripts/build_profile_i_semantic_bundle.py"
    spec = importlib.util.spec_from_file_location("semantic_bundle_builder", script)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    destination = tmp_path / "new-bundle"
    manifest = builder.build(root, destination)
    assert manifest["challenge_ready"] is False and manifest["execution_performed"] is False
    assert manifest["semantic_gate_version"] == 2 and len(manifest["files"]) == 8
    for item in manifest["files"]:
        data = (destination / item["path"]).read_bytes()
        assert len(data) == item["size"] and hashlib.sha256(data).hexdigest() == item["sha256"]
    assert not (destination / "evidence").exists()
    old = root / "benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-incident-repair-001/reference.patch"
    assert (destination / "reference.patch").read_bytes() == old.read_bytes()
    with pytest.raises(ValueError):
        builder.build(root, destination)


def test_legacy_matrix_is_blocked_before_any_files_or_workload(tmp_path):
    from benchmark_runner.realistic_profile_i_docker_matrix import execute_profile_i_docker_matrix, ProfileIDockerMatrixError
    with pytest.raises(ProfileIDockerMatrixError, match="semantic v2"):
        execute_profile_i_docker_matrix(repository=tmp_path, base_root=tmp_path, source_commit="a"*40,
                                       docker_executable=tmp_path / "missing.exe", run_token="test")
    assert not list(tmp_path.iterdir())


def load_checker():
    spec = importlib.util.spec_from_file_location("independent_profile_i_checker", ORACLE.with_name("check_properties.py"))
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    return checker


def test_public_task_checks_behavior_and_blocks_failed_prerequisites(tmp_path):
    from types import SimpleNamespace
    checker = load_checker()
    calls = []
    def failed_identity():
        calls.append("identity")
        raise AssertionError("synthetic")
    oracle = SimpleNamespace(test_windows_kind_requires_readiness_identity_and_child_equality=failed_identity)
    result = checker.evaluate_loaded_oracle(oracle, tmp_path, task_id="I05")
    assert calls == ["identity"] and result["behavior_passed"] is False
    assert [r["status"] for r in result["properties"]] == ["fail", "blocked_by_prerequisite", "blocked_by_prerequisite", "blocked_by_prerequisite"]
    assert result["challenge_ready"] is False


def test_checker_dag_matches_unchanged_property_contract():
    import json
    checker = load_checker()
    root = Path(__file__).resolve().parents[3]
    dag = json.loads((root / "benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-incident-repair-001/prerequisite-dag.json").read_bytes())
    assert {row["property_id"]: tuple(row["prerequisite_ids"]) for row in dag["properties"]} == checker.PREREQUISITES


def test_public_i01_rejects_claim_hash_drift(tmp_path):
    import json
    checker = load_checker()
    records = [{"observation_id": f"O{i:03d}", "observation_sha256": f"{i:064x}"} for i in range(1, 15)]
    files = {"profile-i/evidence/public-observations.json": {"records": records},
        "profile-i/work/evidence-ledger.json": {"records": [{"observation_id": row["observation_id"], "status": "confirmed", "observation_sha256s": [row["observation_sha256"]]} for row in records]},
        "profile-i/work/incident-claims.json": {"claims": [{"status": "confirmed", "evidence_ids": ["O001"], "observation_sha256s": [records[0]["observation_sha256"]]}]},
        "profile-i/work/task-contracts.json": {"tasks": {f"I{i:02d}": {"completed": True} for i in range(2, 9)}}}
    for name, value in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")
    assert checker.evaluate_loaded_oracle(None, tmp_path, task_id="I01", workspace=tmp_path)["behavior_passed"] is True
    path = tmp_path / "profile-i/work/incident-claims.json"
    path.write_text(path.read_text().replace(records[0]["observation_sha256"], "f" * 64), encoding="utf-8")
    assert checker.evaluate_loaded_oracle(None, tmp_path, task_id="I01", workspace=tmp_path)["behavior_passed"] is False
