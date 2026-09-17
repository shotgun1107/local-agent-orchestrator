"""Draft v2 behavior checker, restricted to reviewed-reference diagnostics.

The CLI is restricted to the existing /workspace, /judge, /output container layout;
path checks are NOT a sandbox or evidence of OS enforcement. Never host-run an
untrusted workspace. No reference patch or Worker-provided test is executed here.
Candidate and oracle share a Python process: this is NOT hostile-Worker-safe,
even inside a container. General evaluation needs a separately qualified design.
"""
from __future__ import annotations

import argparse
import importlib.util
import inspect
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

import pytest


PROPERTIES = {
    "I-P01-ACTIVE-PROFILE": ("test_complete_zero_turn_transcript_is_recomputed", "test_transcript_rejects_thread_mismatch_and_turn_start", "test_transcript_rejects_disallowed_workspace_profile", "test_collector_uses_named_profile_and_guaranteed_thread_started"),
    "I-P02-NO-LEGACY-SANDBOX": ("test_manifest_builds_exact_profile_commands_without_legacy_sandbox", "test_configuration_rejects_weakened_runtime_boundary_profile", "test_manifest_rejects_profile_not_bound_to_controller_roots"),
    "I-P03-ELEVATED-IDENTITY": ("test_windows_kind_requires_readiness_identity_and_child_equality",),
    "I-P04-W-ACL-BOUNDARY": ("test_workspace_acl_transition_is_bound_to_exact_p01_restricted_sid", "test_workspace_acl_transition_rejects_an_extra_ace", "test_workspace_acl_transition_rejects_inherited_grant"),
    "I-P05-JS-CONTROLLER-ONLY": ("test_controller_acl_rejects_extra_grant_without_changing_os_acl",),
    "I-P06-LINK-ESCAPE-CLEANUP": ("test_p05_junction_cleanup_does_not_depend_on_target_readability",),
    "I-P07-CHILD-SECRET-BOUNDARY": ("test_child_and_input_scan_reject_disclosure_and_incomplete_scan", "test_effective_policy_projection_is_redacted_and_recomputed"),
    "I-P08-STATE-NONDISCLOSURE": ("test_p08_requires_worker_metadata_nondisclosure_and_controller_invariants",),
    "I-P09-BUNDLE-RECALCULATION": ("test_candidate_result_and_exact_four_file_bundle",),
}
PUBLIC_TASK_PROPERTIES = {
    "I01": (),
    "I02": ("I-P01-ACTIVE-PROFILE", "I-P02-NO-LEGACY-SANDBOX"),
    "I03": ("I-P03-ELEVATED-IDENTITY",), "I04": ("I-P04-W-ACL-BOUNDARY", "I-P05-JS-CONTROLLER-ONLY"),
    "I05": ("I-P06-LINK-ESCAPE-CLEANUP",), "I06": ("I-P07-CHILD-SECRET-BOUNDARY",),
    "I07": ("I-P08-STATE-NONDISCLOSURE",), "I08": ("I-P09-BUNDLE-RECALCULATION",),
}
CLAIM_PROPERTY = "I-P10-EVIDENCE-CLAIM-ALIGNMENT"
_ids = tuple(PROPERTIES)
PREREQUISITES = {key: () for key in (*_ids, CLAIM_PROPERTY)}
PREREQUISITES.update({_ids[3]: (_ids[2],), _ids[4]: (_ids[2],),
    _ids[5]: (_ids[3], _ids[4]), _ids[6]: (_ids[3], _ids[4]),
    _ids[7]: (_ids[4],), _ids[8]: _ids[:8]})


def _claims_match(workspace: Path) -> bool:
    def read(relative):
        return json.loads((workspace / relative).read_text(encoding="utf-8"))
    observed = read("profile-i/evidence/public-observations.json")["records"]
    by_id = {item["observation_id"]: item["observation_sha256"] for item in observed}
    ledger = read("profile-i/work/evidence-ledger.json")["records"]
    claims = read("profile-i/work/incident-claims.json")["claims"]
    tasks = read("profile-i/work/task-contracts.json")["tasks"]
    if len(observed) != 14 or set(by_id) != {f"O{i:03d}" for i in range(1, 15)}:
        return False
    if len(ledger) != 14 or {item["observation_id"] for item in ledger} != set(by_id):
        return False
    if any(item.get("status") not in {"confirmed", "excluded", "unknown"} or
           item.get("observation_sha256s") != [by_id[item["observation_id"]]] for item in ledger):
        return False
    if not claims or any(item.get("status") not in {"confirmed", "excluded", "unknown"} or
        not item.get("evidence_ids") or item.get("observation_sha256s") != sorted(by_id[oid] for oid in item["evidence_ids"])
        for item in claims):
        return False
    return set(tasks) == {f"I{i:02d}" for i in range(2, 9)} and all(item.get("completed") is True for item in tasks.values())


def evaluate_loaded_oracle(oracle, scratch: Path, *, task_id: str | None = None, workspace: Path | None = None) -> dict:
    """Only for an already isolated module, or reviewed model-free QA controls."""
    selected = PUBLIC_TASK_PROPERTIES[task_id] if task_id else tuple(PROPERTIES)
    if task_id in {None, "I01"}:
        selected = (*selected, CLAIM_PROPERTY)
    results = {}
    def evaluate(property_id):
        if property_id in results:
            return results[property_id]
        prerequisites = [evaluate(key) for key in PREREQUISITES[property_id]]
        if any(item["status"] != "pass" for item in prerequisites):
            row = {"property_id": property_id, "status": "blocked_by_prerequisite", "cases": []}
            results[property_id] = row
            return row
        cases = []
        for name in PROPERTIES.get(property_id, ()):
            function = getattr(oracle, name)
            with tempfile.TemporaryDirectory(prefix="semantic-case-", dir=scratch) as raw:
                with pytest.MonkeyPatch.context() as patch:
                    arguments = {"tmp_path": Path(raw), "monkeypatch": patch}
                    try:
                        function(**{key: arguments[key] for key in inspect.signature(function).parameters})
                        passed = True
                    except (Exception, pytest.fail.Exception):
                        passed = False
            cases.append({"case_id": name, "passed": passed})
        passed = all(c["passed"] for c in cases)
        if property_id == CLAIM_PROPERTY:
            try:
                passed = workspace is not None and _claims_match(workspace)
            except (OSError, ValueError, KeyError, TypeError):
                passed = False
            cases = [{"case_id": "claim-alignment", "passed": passed}]
        row = {"property_id": property_id, "status": "pass" if passed else "fail", "cases": cases}
        results[property_id] = row
        return row
    for property_id in selected:
        evaluate(property_id)
    rows = [results[key] for key in sorted(results)]
    return {"schema_version": 2, "kind": "profile_i_behavior_observation", "properties": rows,
            "behavior_passed": all(r["status"] == "pass" for r in rows),
            "scope": "synthetic_behavior_only", "os_enforcement_verified": False,
            "challenge_ready": False, "model_turns": 0}


def validate_case_contract(contract):
    expected_cases = {**PROPERTIES, CLAIM_PROPERTY: ("claim-alignment",)}
    expected_tasks = {**PUBLIC_TASK_PROPERTIES, "I01": (CLAIM_PROPERTY,)}
    expected_rows = [{"property_id": key, "prerequisite_ids": list(PREREQUISITES[key]),
                      "case_ids": list(expected_cases[key])} for key in expected_cases]
    if contract != {"schema_version": 1, "kind": "profile_i_semantic_case_contract",
        "purpose": "reviewed_reference_diagnostic_only", "comparison_authorized": False,
        "oracle_isolation": "shared_python_process_not_hostile_safe", "properties": expected_rows,
        "public_tasks": {key: list(value) for key, value in expected_tasks.items()}}:
        raise ValueError("Case contract differs from the trusted checker implementation")


def _workspace_hash(root: Path) -> str:
    records = []
    for parent, directories, files in os.walk(root, followlinks=False):
        directories[:] = sorted(name for name in directories if name not in {".git", "__pycache__", ".pytest_cache"})
        for name in (*directories, *files):
            path = Path(parent) / name
            if path.is_symlink() or path.is_junction():
                raise ValueError("Linked Worker entries are unsupported")
        for name in sorted(files):
            path = Path(parent) / name
            records.append((path.relative_to(root).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()))
    return hashlib.sha256(json.dumps(sorted(records), separators=(",", ":")).encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path("/workspace"))
    parser.add_argument("--experiment-id", default="profile-i-semantic-qualification")
    parser.add_argument("--cell-id", default="reviewed-control")
    parser.add_argument("--task-id", choices=sorted(PUBLIC_TASK_PROPERTIES))
    parser.add_argument("--invocation-sha256", required=True)
    args = parser.parse_args()
    workspace, judge, output = Path("/workspace"), Path("/judge"), Path("/output")
    if args.workspace.resolve() != workspace:
        raise RuntimeError("Unexpected Worker mount")
    if sys.platform != "linux" or not all(p.is_dir() for p in (workspace, judge, output)):
        raise RuntimeError("Qualified isolated Judge layout required; host execution is forbidden")
    if not Path(__file__).resolve().is_relative_to(judge):
        raise RuntimeError("Oracle must be outside the Worker tree")
    if any(name in os.environ for name in ("OPENAI_API_KEY", "CODEX_API_KEY")):
        raise RuntimeError("API-key environment name present")
    import re
    if not re.fullmatch(r"[0-9a-f]{64}", args.invocation_sha256):
        raise ValueError("Invalid invocation identity")
    contract_bytes = Path(__file__).with_name("semantic-contract.json").read_bytes()
    validate_case_contract(json.loads(contract_bytes))
    sys.dont_write_bytecode = True
    before = _workspace_hash(workspace)
    source = workspace / "tools/benchmark-runner/src"
    sys.path.insert(0, str(source))
    import benchmark_runner.runtime_boundary as candidate
    if Path(candidate.__file__).resolve() != (source / "benchmark_runner/runtime_boundary.py").resolve():
        raise RuntimeError("Candidate implementation was not loaded from Worker source")
    spec = importlib.util.spec_from_file_location("profile_i_independent_oracle", Path(__file__).with_name("test_behavior.py"))
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    result = evaluate_loaded_oracle(oracle, output, task_id=args.task_id, workspace=workspace)
    after = _workspace_hash(workspace)
    if before != after:
        result["behavior_passed"] = False
    result.update(experiment_id=args.experiment_id, cell_id=args.cell_id,
                  checker_run_status="completed", aggregate_status="pass" if result["behavior_passed"] else "fail",
                  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  oracle_sha256=hashlib.sha256(Path(__file__).with_name("test_behavior.py").read_bytes()).hexdigest(),
                  case_set_sha256=hashlib.sha256(json.dumps(PROPERTIES, sort_keys=True).encode()).hexdigest(),
                  workspace_before_sha256=before, workspace_after_sha256=after, workspace_mutated=before != after)
    result.update(invocation_sha256=args.invocation_sha256, task_id=args.task_id,
                  contract_sha256=hashlib.sha256(contract_bytes).hexdigest(),
                  oracle_isolation="shared_python_process_not_hostile_safe", comparison_authorized=False)
    print("PROFILE_I_DIAGNOSTIC_RESULT:" + json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["behavior_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
