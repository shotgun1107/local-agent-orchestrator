"""Deterministic judge-only property checker for Profile I.

The checker receives only the frozen Worker tree.  It never reads Phase B raw
evidence, the reference patch, mutation patches, or live Codex state.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from typing import Any, Callable


BUNDLE_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = BUNDLE_ROOT / "property-catalog.json"
DAG_PATH = BUNDLE_ROOT / "prerequisite-dag.json"
RUNTIME = "tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py"
PROBE = "tools/benchmark-runner/scripts/probe_runtime_boundary.py"
TESTS = "tools/benchmark-runner/tests/test_runtime_boundary.py"
LEDGER = "profile-i/work/evidence-ledger.json"
CLAIMS = "profile-i/work/incident-claims.json"
TASKS = "profile-i/work/task-contracts.json"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_sha256(value: object) -> str:
    return _sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def _tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(
        (
            path for path in root.rglob("*")
            if path.is_file() and not {".git", "__pycache__", ".pytest_cache"}.intersection(path.relative_to(root).parts)
        ),
        key=lambda path: path.relative_to(root).as_posix().encode("utf-8"),
    )
    for path in files:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        payload = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _definitions(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _evidence(root: Path, *paths: str) -> list[dict[str, str]]:
    result = []
    for relative in sorted(set(paths)):
        path = root / relative
        if path.is_file():
            result.append({"path": relative, "sha256": _sha256(path.read_bytes())})
    return result


def _outcome(
    root: Path,
    passed: bool,
    *,
    pass_code: str,
    fail_code: str,
    description: str,
    evidence: tuple[str, ...],
) -> dict[str, object]:
    return {
        "status": "pass" if passed else "fail",
        "reason_code": pass_code if passed else fail_code,
        "description": description,
        "evidence_refs": _evidence(root, *evidence),
    }


def _source(root: Path) -> tuple[str, str, str, set[str], set[str], set[str]]:
    runtime_path, probe_path, test_path = root / RUNTIME, root / PROBE, root / TESTS
    return (
        runtime_path.read_text(encoding="utf-8"),
        probe_path.read_text(encoding="utf-8"),
        test_path.read_text(encoding="utf-8"),
        _definitions(runtime_path),
        _definitions(probe_path),
        _definitions(test_path),
    )


def _active_profile(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    runtime, _probe, tests, definitions, _pdefs, test_defs = _source(root)
    passed = (
        'PERMISSION_PROFILE_ID = "runtime-boundary-worker"' in runtime
        and 'PERMISSION_PROFILE_LIST_METHOD = "permissionProfile/list"' in runtime
        and 'THREAD_STARTED_NOTIFICATION_METHOD = "thread/started"' in runtime
        and {"derive_sdk_profile_provenance", "verify_sdk_profile_provenance"} <= definitions
        and {"test_complete_zero_turn_transcript_is_recomputed", "test_collector_uses_named_profile_and_guaranteed_thread_started"} <= test_defs
        and "turn/start" in runtime
    )
    return _outcome(root, passed, pass_code="ACTIVE_PROFILE_RECOMPUTED", fail_code="ACTIVE_PROFILE_NOT_PROVEN", description="Direction-aware SDK frames bind the selected permission profile and zero-turn contract.", evidence=(RUNTIME, TESTS))


def _no_legacy_sandbox(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    runtime, _probe, _tests, definitions, _pdefs, test_defs = _source(root)
    passed = (
        "sandbox=Sandbox" not in runtime
        and "sandbox=\"workspace-write\"" not in runtime
        and "test_manifest_builds_exact_profile_commands_without_legacy_sandbox" in test_defs
    )
    return _outcome(root, passed, pass_code="LEGACY_SANDBOX_ABSENT", fail_code="LEGACY_SANDBOX_PRESENT_OR_UNCHECKED", description="The named profile is used without a legacy sandbox argument.", evidence=(RUNTIME, TESTS))


def _elevated_identity(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    runtime, _probe, _tests, definitions, _pdefs, test_defs = _source(root)
    passed = (
        'windows.sandbox="elevated"' in runtime
        and {"_runtime_boundary_config_overrides", "derive_windows_sandbox_kind", "verify_windows_sandbox_provenance", "observe_controller_process_identity"} <= definitions
        and "test_configuration_rejects_weakened_runtime_boundary_profile" in test_defs
    )
    return _outcome(root, passed, pass_code="ELEVATED_IDENTITY_RECOMPUTED", fail_code="ELEVATED_IDENTITY_UNBOUND", description="Effective configuration, readiness, and process identity jointly establish the sandbox kind.", evidence=(RUNTIME, TESTS))


def _workspace_acl(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    runtime, _probe, _tests, definitions, _pdefs, test_defs = _source(root)
    passed = (
        {"WorkspaceAclTransitionObservation", "verify_workspace_acl_transition", "_parse_workspace_acl_ace"} <= definitions
        and "P01_restricted_contains_added_ace_sid" in runtime
        and "test_workspace_acl_transition_is_bound_to_exact_p01_restricted_sid" in test_defs
        and "test_workspace_acl_transition_rejects_an_extra_ace" in test_defs
    )
    return _outcome(root, passed, pass_code="WORKSPACE_ACL_IDENTITY_BOUND", fail_code="WORKSPACE_ACL_IDENTITY_UNBOUND", description="The one-ACE workspace transition is bound to the executing restricted SID.", evidence=(RUNTIME, TESTS))


def _controller_only_roots(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    runtime, _probe, _tests, definitions, _pdefs, test_defs = _source(root)
    passed = (
        {"_assert_controller_only_directory_security", "_harden_controller_only_directory", "verify_root_identity_contract"} <= definitions
        and "(A;OICI;FA;;;SY)" in runtime
        and "(A;OICI;FA;;;BA)" in runtime
        and "test_controller_only_directory_hardening_is_exact" in test_defs
    )
    return _outcome(root, passed, pass_code="CONTROLLER_ROOTS_PROTECTED", fail_code="CONTROLLER_ROOTS_NOT_PROTECTED", description="J and S are hardened to exact Controller-only ACLs and rechecked by identity.", evidence=(RUNTIME, TESTS))


def _link_cleanup(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    _runtime, probe, _tests, _defs, probe_defs, test_defs = _source(root)
    passed = (
        {"_path_entry_exists", "_link_attempt"} <= probe_defs
        and "os.lstat(path)" in probe
        and "test_p05_command_identity_does_not_follow_created_junction" in test_defs
        and "test_p05_junction_cleanup_does_not_depend_on_target_readability" in test_defs
    )
    return _outcome(root, passed, pass_code="LINK_ESCAPE_CLEANED", fail_code="LINK_ESCAPE_OR_CLEANUP_DRIFT", description="Link existence and cleanup do not follow a protected target and command identity stays frozen.", evidence=(PROBE, TESTS))


def _child_secret_boundary(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    runtime, probe, _tests, definitions, _pdefs, test_defs = _source(root)
    passed = (
        {"P06ChildResult", "P07InputScanResult", "redact_sensitive_json"} <= definitions
        and "environment_names_scanned" in runtime
        and "argument_values_scanned" in runtime
        and "test_p08_requires_worker_metadata_nondisclosure_and_controller_invariants" in test_defs
    )
    return _outcome(root, passed, pass_code="CHILD_SECRET_BOUNDARY_PRESERVED", fail_code="CHILD_SECRET_BOUNDARY_UNPROVEN", description="Child access and output surfaces preserve the protected-content boundary.", evidence=(RUNTIME, PROBE, TESTS))


def _state_nondisclosure(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    runtime, _probe, _tests, definitions, _pdefs, test_defs = _source(root)
    passed = (
        {"P08StateResult", "recompute_probe_pass", "result_with_recomputed_verdict"} <= definitions
        and "probe.S_sentinel_sha256_before == manifest.S_sentinel.sha256" in runtime
        and "probe.S_sentinel_sha256_after == manifest.S_sentinel.sha256" in runtime
        and "test_p08_requires_worker_metadata_nondisclosure_and_controller_invariants" in test_defs
    )
    return _outcome(root, passed, pass_code="STATE_NONDISCLOSURE_RECOMPUTED", fail_code="STATE_NONDISCLOSURE_TRUSTED_OR_EXPOSED", description="P08 is recalculated from public typed results and Controller invariants without protected metadata.", evidence=(RUNTIME, TESTS))


def _bundle_recalculation(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    runtime, _probe, _tests, definitions, _pdefs, test_defs = _source(root)
    passed = (
        {"write_runtime_boundary_bundle", "verify_runtime_boundary_bundle", "_files_manifest_bytes"} <= definitions
        and "bundle-seal.json" in runtime
        and "files.sha256" in runtime
        and "test_candidate_result_and_exact_four_file_bundle" in test_defs
    )
    return _outcome(root, passed, pass_code="BUNDLE_IDENTITY_RECALCULATED", fail_code="BUNDLE_IDENTITY_NOT_RECALCULATED", description="The candidate verdict and exact four-file bundle are independently recomputed.", evidence=(RUNTIME, TESTS))


def _claims(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    observations = _load(root / "profile-i/evidence/public-observations.json")
    by_id = {record["observation_id"]: record for record in observations.get("records", []) if isinstance(record, dict)}
    ledger = _load(root / LEDGER).get("records")
    claims = _load(root / CLAIMS).get("claims")
    tasks = _load(root / TASKS).get("tasks")
    passed = isinstance(ledger, list) and isinstance(claims, list) and isinstance(tasks, dict)
    if passed:
        passed = len(ledger) == 14 and set(by_id) == {f"O{i:03d}" for i in range(1, 15)}
    if passed:
        for record in ledger:
            oid = record.get("observation_id")
            expected = by_id.get(oid, {}).get("observation_sha256")
            if record.get("status") not in {"confirmed", "excluded", "unknown"} or record.get("observation_sha256s") != [expected]:
                passed = False
                break
    if passed:
        passed = bool(claims) and all(
            isinstance(claim, dict)
            and claim.get("status") in {"confirmed", "excluded", "unknown"}
            and isinstance(claim.get("evidence_ids"), list)
            and claim["evidence_ids"]
            and claim.get("observation_sha256s") == sorted(by_id[oid]["observation_sha256"] for oid in claim["evidence_ids"])
            for claim in claims
        )
    if passed:
        passed = set(tasks) == {f"I{i:02d}" for i in range(2, 9)} and all(item.get("completed") is True for item in tasks.values())
    return _outcome(root, passed, pass_code="EVIDENCE_CLAIMS_ALIGNED", fail_code="EVIDENCE_CLAIMS_MISALIGNED", description="Structured claims and task declarations remain bound to the fourteen public observations.", evidence=(LEDGER, CLAIMS, TASKS, "profile-i/evidence/public-observations.json"))


CHECKERS: dict[str, Callable[[Path, dict[str, Any]], dict[str, object]]] = {
    "I-P01-ACTIVE-PROFILE": _active_profile,
    "I-P02-NO-LEGACY-SANDBOX": _no_legacy_sandbox,
    "I-P03-ELEVATED-IDENTITY": _elevated_identity,
    "I-P04-W-ACL-BOUNDARY": _workspace_acl,
    "I-P05-JS-CONTROLLER-ONLY": _controller_only_roots,
    "I-P06-LINK-ESCAPE-CLEANUP": _link_cleanup,
    "I-P07-CHILD-SECRET-BOUNDARY": _child_secret_boundary,
    "I-P08-STATE-NONDISCLOSURE": _state_nondisclosure,
    "I-P09-BUNDLE-RECALCULATION": _bundle_recalculation,
    "I-P10-EVIDENCE-CLAIM-ALIGNMENT": _claims,
}


def evaluate_workspace(workspace: Path, *, experiment_id: str, cell_id: str) -> dict[str, object]:
    workspace = workspace.resolve(strict=True)
    catalog, dag = _load(CATALOG_PATH), _load(DAG_PATH)
    definitions, dag_entries = catalog.get("properties"), dag.get("properties")
    if not isinstance(definitions, list) or not isinstance(dag_entries, list):
        raise ValueError("invalid catalog or DAG")
    expected_dag = [{"property_id": row["property_id"], "prerequisite_ids": row["prerequisite_ids"]} for row in definitions]
    if dag_entries != expected_dag or [row["property_id"] for row in definitions] != sorted(CHECKERS):
        raise ValueError("catalog, DAG, or checker set differs")
    before = _tree_sha256(workspace)
    checker_hash = _sha256(Path(__file__).read_bytes())
    by_id = {row["property_id"]: row for row in definitions}
    results: dict[str, dict[str, object]] = {}

    def evaluate(property_id: str) -> dict[str, object]:
        if property_id in results:
            return results[property_id]
        definition = by_id[property_id]
        prerequisites = list(definition["prerequisite_ids"])
        prerequisite_results = [evaluate(item) for item in prerequisites]
        if any(item["status"] != "pass" for item in prerequisite_results):
            outcome = {"status": "blocked_by_prerequisite", "reason_code": "PREREQUISITE_NOT_PASSED", "description": "A prerequisite property did not pass.", "evidence_refs": []}
        else:
            try:
                outcome = CHECKERS[property_id](workspace, catalog)
            except Exception:
                outcome = {"status": "checker_error", "reason_code": "CHECKER_EXCEPTION", "description": "The checker raised an exception.", "evidence_refs": []}
        result = {"property_id": property_id, "severity": definition["severity"], "prerequisite_ids": prerequisites, "checker_sha256": checker_hash, **outcome}
        results[property_id] = result
        return result

    ordered = [evaluate(row["property_id"]) for row in definitions]
    statuses = {row["status"] for row in ordered}
    aggregate = "checker_error" if "checker_error" in statuses else "fail" if statuses - {"pass"} else "pass"
    after = _tree_sha256(workspace)
    payload: dict[str, object] = {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "cell_id": cell_id,
        "fixture_id": "realistic-incident-repair-001",
        "catalog_sha256": _canonical_sha256([{"property_id": row["property_id"], "severity": row["severity"]} for row in definitions]),
        "prerequisite_dag_sha256": _canonical_sha256(expected_dag),
        "checker_sha256": checker_hash,
        "ordered_property_ids": [row["property_id"] for row in definitions],
        "checker_run_status": "completed",
        "aggregate_status": aggregate,
        "process": {"exit_code": 0, "timed_out": False, "stdout_size": 0, "stdout_sha256": _sha256(b""), "stdout_truncated": False, "stderr_size": 0, "stderr_sha256": _sha256(b""), "stderr_truncated": False},
        "workspace_before_sha256": before,
        "workspace_after_sha256": after,
        "workspace_mutated": before != after,
        "properties": ordered,
    }
    payload["envelope_sha256"] = _canonical_sha256(payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--experiment-id", default="phase-d-profile-i")
    parser.add_argument("--cell-id", default="reference")
    args = parser.parse_args(argv)
    result = evaluate_workspace(args.workspace, experiment_id=args.experiment_id, cell_id=args.cell_id)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["aggregate_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
