from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable


SNAPSHOT_ID = "realistic-incident-repair-001"
BASE_COMMIT = "5fe78aa5c6a357c08682684a258b41e7d84c4dbc"
REFERENCE_COMMIT = "9b29e781136e13b43b1e18f3fe1823bf496bef5c"
PROFILE_ROOT = Path("benchmarks/fixtures/routing-realistic-high-difficulty-v1") / SNAPSHOT_ID
JUDGE_ROOT = Path("benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1") / SNAPSHOT_ID
CHECKER_RELATIVE = Path("checker/check_properties.py")
RUNTIME = "tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py"
REFERENCE_PATHS = (
    "docs/design/sdk-routing-realistic-high-difficulty-implementation-candidate-spec.md",
    "docs/design/sdk-routing-realistic-high-difficulty-runtime-boundary-spec.md",
    "tools/benchmark-runner/scripts/probe_runtime_boundary.py",
    "tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py",
    "tools/benchmark-runner/tests/test_runtime_boundary.py",
)


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def pretty_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object: {path}")
    return value


def git(repository: Path, *arguments: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(["git", *arguments], cwd=repository, input=input_bytes, check=True, capture_output=True).stdout


def git_blob(repository: Path, commit: str, path: str) -> bytes:
    return git(repository, "cat-file", "blob", f"{commit}:{path}")


def write_bytes(root: Path, relative: str, payload: bytes) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def copy_tree(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".git"))


def apply_mapping(path: str, payload: bytes, mapping: dict[str, Any]) -> bytes:
    result = payload
    for replacement in mapping["replacements"]:
        result = result.replace(str(replacement["source_utf8"]).encode(), str(replacement["replacement_utf8"]).encode())
    if path.startswith("docs/") or path.endswith("/README.md"):
        text = result.decode("utf-8")
        result = re.sub(r"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])", "0" * 40, text).encode("utf-8")
    return result


def initialize_repo(path: Path) -> None:
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "core.autocrlf", "false")
    git(path, "config", "core.longpaths", "true")
    git(path, "config", "user.name", "profile-i-builder")
    git(path, "config", "user.email", "profile-i@fixture.invalid")
    git(path, "add", "-A")
    environment = os.environ.copy()
    environment.update({"GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z"})
    subprocess.run(["git", "commit", "-q", "-m", "baseline"], cwd=path, env=environment, check=True)


def patch_bytes(baseline: Path, target: Path) -> bytes:
    with tempfile.TemporaryDirectory(prefix="profile-i-diff-") as raw:
        repository = Path(raw) / "repository"
        copy_tree(baseline, repository)
        initialize_repo(repository)
        for child in list(repository.iterdir()):
            if child.name == ".git":
                continue
            shutil.rmtree(child) if child.is_dir() else child.unlink()
        for source in target.iterdir():
            destination = repository / source.name
            shutil.copytree(source, destination) if source.is_dir() else shutil.copy2(source, destination)
        git(repository, "add", "-N", ".")
        return git(repository, "diff", "--binary", "--full-index", "--no-renames", "HEAD", "--", ".")


def reference_work_payloads(solution: Path) -> None:
    observations = load_json(solution / "profile-i/evidence/public-observations.json")["records"]
    by_id = {record["observation_id"]: record["observation_sha256"] for record in observations}
    ledger = {
        "schema_version": 1,
        "records": [
            {
                "observation_id": oid,
                "status": "confirmed",
                "reason_code": "PUBLIC_OBSERVATION_RECORDED",
                "observation_sha256s": [by_id[oid]],
                "contradiction_ids": [],
            }
            for oid in sorted(by_id)
        ],
    }
    claim_groups = (
        ("C01-PROFILE", ["O001", "O010"]),
        ("C02-POLICY", ["O002", "O003", "O004", "O005"]),
        ("C03-WORKSPACE", ["O006", "O007", "O008"]),
        ("C04-CONTROLLER-ROOTS", ["O009", "O011", "O012"]),
        ("C05-LINK-CLEANUP", ["O013"]),
        ("C06-STATE", ["O014"]),
    )
    claims = {
        "schema_version": 1,
        "claims": [
            {
                "claim_id": claim_id,
                "status": "confirmed",
                "reason_code": "PUBLIC_FACT_SET_CLASSIFIED",
                "evidence_ids": evidence_ids,
                "observation_sha256s": sorted(by_id[oid] for oid in evidence_ids),
                "contradiction_ids": [],
            }
            for claim_id, evidence_ids in claim_groups
        ],
    }
    common_runtime = "tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py"
    common_tests = "tools/benchmark-runner/tests/test_runtime_boundary.py"
    tasks = {
        "I02": (["O001", "O010"], [common_runtime, common_tests], ["derive_sdk_profile_provenance", "verify_sdk_profile_provenance"], ["test_complete_zero_turn_transcript_is_recomputed", "test_collector_uses_named_profile_and_guaranteed_thread_started"]),
        "I03": (["O002", "O003", "O004", "O005", "O010"], ["docs/design/sdk-routing-realistic-high-difficulty-implementation-candidate-spec.md", "docs/design/sdk-routing-realistic-high-difficulty-runtime-boundary-spec.md", "tools/benchmark-runner/scripts/probe_runtime_boundary.py", common_runtime, common_tests], ["_runtime_boundary_config_overrides", "derive_windows_sandbox_kind"], ["test_configuration_rejects_weakened_runtime_boundary_profile", "test_profile_failure_is_written_beside_uncreated_bundle"]),
        "I04": (["O006", "O007", "O008"], [common_runtime, common_tests], ["verify_workspace_acl_transition", "_parse_workspace_acl_ace"], ["test_workspace_acl_transition_is_bound_to_exact_p01_restricted_sid", "test_workspace_acl_transition_rejects_an_extra_ace"]),
        "I05": (["O009", "O011", "O012"], [common_runtime, common_tests], ["_harden_controller_only_directory", "verify_root_identity_contract"], ["test_controller_only_directory_hardening_is_exact", "test_manifest_rejects_profile_not_bound_to_controller_roots"]),
        "I06": (["O013"], ["tools/benchmark-runner/scripts/probe_runtime_boundary.py", common_runtime, common_tests], ["_path_entry_exists", "_link_attempt"], ["test_p05_command_identity_does_not_follow_created_junction", "test_p05_junction_cleanup_does_not_depend_on_target_readability"]),
        "I07": (["O014"], [common_runtime, common_tests], ["recompute_probe_pass", "result_with_recomputed_verdict"], ["test_p08_requires_worker_metadata_nondisclosure_and_controller_invariants", "test_candidate_result_and_exact_four_file_bundle"]),
        "I08": (["O014"], ["docs/design/sdk-routing-realistic-high-difficulty-implementation-candidate-spec.md", "docs/design/sdk-routing-realistic-high-difficulty-runtime-boundary-spec.md", "profile-i/work/evidence-ledger.json", "profile-i/work/incident-claims.json", common_runtime, common_tests], ["verify_runtime_boundary_result", "verify_runtime_boundary_bundle", "result_with_recomputed_verdict"], ["test_candidate_result_and_exact_four_file_bundle", "test_complete_zero_turn_transcript_is_recomputed", "test_p08_requires_worker_metadata_nondisclosure_and_controller_invariants"]),
    }
    task_payload = {
        "schema_version": 1,
        "tasks": {
            task_id: {"completed": True, "evidence_ids": evidence_ids, "changed_paths": ["profile-i/work/task-contracts.json", *paths], "implementation_symbols": symbols, "test_names": tests}
            for task_id, (evidence_ids, paths, symbols, tests) in tasks.items()
        },
    }
    # Avoid duplicate declarations while preserving deterministic order.
    for record in task_payload["tasks"].values():
        record["changed_paths"] = list(dict.fromkeys(record["changed_paths"]))
    write_bytes(solution, "profile-i/work/evidence-ledger.json", pretty_json(ledger))
    write_bytes(solution, "profile-i/work/incident-claims.json", pretty_json(claims))
    write_bytes(solution, "profile-i/work/task-contracts.json", pretty_json(task_payload))


def project_reference(repository: Path, pristine: Path, solution: Path, mapping: dict[str, Any]) -> None:
    copy_tree(pristine, solution)
    for relative in REFERENCE_PATHS:
        write_bytes(solution, relative, apply_mapping(relative, git_blob(repository, REFERENCE_COMMIT, relative), mapping))
    reference_work_payloads(solution)


def replace_once(path: Path, before: bytes, after: bytes) -> None:
    payload = path.read_bytes()
    if payload.count(before) != 1:
        raise RuntimeError(f"mutation anchor is not unique: {path} ({payload.count(before)})")
    path.write_bytes(payload.replace(before, after, 1))


def mutate_active_profile(root: Path) -> None:
    replace_once(root / "tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py", b'PERMISSION_PROFILE_LIST_METHOD = "permissionProfile/list"', b'PERMISSION_PROFILE_LIST_METHOD = "permissionProfile/list-mutated"')


def mutate_legacy_sandbox(root: Path) -> None:
    replace_once(root / TESTS_PATH, b"test_manifest_builds_exact_profile_commands_without_legacy_sandbox", b"test_manifest_builds_profile_commands_mutated")


def mutate_elevated(root: Path) -> None:
    replace_once(
        root / "tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py",
        b"def _runtime_boundary_config_overrides(\n",
        b"def _runtime_boundary_config_overrides_mutated(\n",
    )


def mutate_workspace_acl(root: Path) -> None:
    path = root / "tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py"
    path.write_bytes(path.read_bytes().replace(b"WorkspaceAclTransitionObservation", b"WorkspaceAclTransitionObservationMutated"))


def mutate_controller_roots(root: Path) -> None:
    replace_once(root / "tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py", b"(A;OICI;FA;;;SY)", b"(A;OICI;FA;;;SYY)")


def mutate_link_cleanup(root: Path) -> None:
    replace_once(
        root / "tools/benchmark-runner/scripts/probe_runtime_boundary.py",
        b"        os.lstat(path)",
        b"        path.exists()",
    )


def mutate_child_boundary(root: Path) -> None:
    path = root / "tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py"
    path.write_bytes(path.read_bytes().replace(b"P07InputScanResult", b"P07InputScanResultMutated"))


def mutate_state(root: Path) -> None:
    replace_once(
        root / "tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py",
        b"probe.S_sentinel_sha256_before == manifest.S_sentinel.sha256",
        b"probe.S_sentinel_sha256_before != manifest.S_sentinel.sha256",
    )


def mutate_bundle(root: Path) -> None:
    replace_once(
        root / "tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py",
        b"def verify_runtime_boundary_bundle(\n",
        b"def verify_runtime_boundary_bundle_mutated(\n",
    )


def mutate_claims(root: Path) -> None:
    path = root / "profile-i/work/incident-claims.json"
    payload = load_json(path)
    payload["claims"][0]["observation_sha256s"][0] = "0" * 64
    path.write_bytes(pretty_json(payload))


TESTS_PATH = "tools/benchmark-runner/tests/test_runtime_boundary.py"
MUTATIONS: tuple[tuple[str, str, Callable[[Path], None]], ...] = (
    ("i-p01-active-profile", "I-P01-ACTIVE-PROFILE", mutate_active_profile),
    ("i-p02-no-legacy-sandbox", "I-P02-NO-LEGACY-SANDBOX", mutate_legacy_sandbox),
    ("i-p03-elevated-identity", "I-P03-ELEVATED-IDENTITY", mutate_elevated),
    ("i-p04-w-acl-boundary", "I-P04-W-ACL-BOUNDARY", mutate_workspace_acl),
    ("i-p05-js-controller-only", "I-P05-JS-CONTROLLER-ONLY", mutate_controller_roots),
    ("i-p06-link-cleanup", "I-P06-LINK-ESCAPE-CLEANUP", mutate_link_cleanup),
    ("i-p07-child-secret", "I-P07-CHILD-SECRET-BOUNDARY", mutate_child_boundary),
    ("i-p08-state-nondisclosure", "I-P08-STATE-NONDISCLOSURE", mutate_state),
    ("i-p09-bundle-recalculation", "I-P09-BUNDLE-RECALCULATION", mutate_bundle),
    ("i-p10-evidence-claims", "I-P10-EVIDENCE-CLAIM-ALIGNMENT", mutate_claims),
)


def load_checker(path: Path):
    spec = importlib.util.spec_from_file_location("profile_i_check_properties", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Profile I checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def file_manifest(root: Path, *, exclude: set[str]) -> list[dict[str, object]]:
    records = []
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.relative_to(root).as_posix().encode("utf-8")):
        relative = path.relative_to(root).as_posix()
        if relative in exclude or "__pycache__" in path.parts:
            continue
        payload = path.read_bytes()
        records.append({"path": relative, "size": len(payload), "sha256": sha256(payload)})
    return records


def build(repository: Path) -> dict[str, object]:
    profile_root, judge_root = repository / PROFILE_ROOT, repository / JUDGE_ROOT
    pristine, checker_path = profile_root / "workspace", judge_root / CHECKER_RELATIVE
    if not pristine.is_dir() or not checker_path.is_file():
        raise RuntimeError("Profile I Worker snapshot or checker is missing")
    generated = {"bundle-manifest.json", "challenge-eligibility.json", "r-change-composition.json", "property-catalog.json", "prerequisite-dag.json", "information-dependency-map.json", "operator-contract.json", "incident-claims.json", "reference.patch"}
    for path in list(judge_root.rglob("*")):
        if path.is_file() and (path.relative_to(judge_root).as_posix() in generated or path.relative_to(judge_root).as_posix().startswith(("negative-mutations/", "evidence/"))):
            path.unlink()
    properties = [
        {"property_id": "I-P01-ACTIVE-PROFILE", "severity": "critical", "prerequisite_ids": []},
        {"property_id": "I-P02-NO-LEGACY-SANDBOX", "severity": "critical", "prerequisite_ids": []},
        {"property_id": "I-P03-ELEVATED-IDENTITY", "severity": "major", "prerequisite_ids": []},
        {"property_id": "I-P04-W-ACL-BOUNDARY", "severity": "critical", "prerequisite_ids": ["I-P03-ELEVATED-IDENTITY"]},
        {"property_id": "I-P05-JS-CONTROLLER-ONLY", "severity": "critical", "prerequisite_ids": ["I-P03-ELEVATED-IDENTITY"]},
        {"property_id": "I-P06-LINK-ESCAPE-CLEANUP", "severity": "critical", "prerequisite_ids": ["I-P04-W-ACL-BOUNDARY", "I-P05-JS-CONTROLLER-ONLY"]},
        {"property_id": "I-P07-CHILD-SECRET-BOUNDARY", "severity": "safety", "prerequisite_ids": ["I-P04-W-ACL-BOUNDARY", "I-P05-JS-CONTROLLER-ONLY"]},
        {"property_id": "I-P08-STATE-NONDISCLOSURE", "severity": "critical", "prerequisite_ids": ["I-P05-JS-CONTROLLER-ONLY"]},
        {"property_id": "I-P09-BUNDLE-RECALCULATION", "severity": "integrity", "prerequisite_ids": [f"I-P{i:02d}-{name}" for i, name in ((1,"ACTIVE-PROFILE"),(2,"NO-LEGACY-SANDBOX"),(3,"ELEVATED-IDENTITY"),(4,"W-ACL-BOUNDARY"),(5,"JS-CONTROLLER-ONLY"),(6,"LINK-ESCAPE-CLEANUP"),(7,"CHILD-SECRET-BOUNDARY"),(8,"STATE-NONDISCLOSURE"))]},
        {"property_id": "I-P10-EVIDENCE-CLAIM-ALIGNMENT", "severity": "major", "prerequisite_ids": []},
    ]
    write_bytes(judge_root, "property-catalog.json", pretty_json({"schema_version": 1, "profile": "I", "properties": properties}))
    write_bytes(judge_root, "prerequisite-dag.json", pretty_json({"schema_version": 1, "properties": [{"property_id": row["property_id"], "prerequisite_ids": row["prerequisite_ids"]} for row in properties]}))
    write_bytes(judge_root, "r-change-composition.json", pretty_json({"schema_version": 1, "profile": "I", "base_commit": BASE_COMMIT, "reference_commit": REFERENCE_COMMIT, "changed_paths": list(REFERENCE_PATHS)}))
    write_bytes(judge_root, "operator-contract.json", pretty_json({"schema_version": 1, "profile": "I", "checker_argv": ["python", "checker/check_properties.py", "--workspace", "<W>"], "success_exit_codes": [0], "contract_failure_exit_codes": [1], "network_required": False, "model_turns": 0}))
    write_bytes(judge_root, "incident-claims.json", pretty_json({"schema_version": 1, "profile": "I", "authority": "structured Worker incident-claims.json only"}))
    write_bytes(judge_root, "information-dependency-map.json", pretty_json({"schema_version": 1, "properties": [{"property_id": row["property_id"], "task_ids": ["I01" if row["property_id"] == "I-P10-EVIDENCE-CLAIM-ALIGNMENT" else f"I{min(int(row['property_id'][3:5]) + 1, 8):02d}"], "worker_readable_paths": ["profile-i/requirements/boundary-contract.md", RUNTIME], "source_evidence_sha256": sha256(canonical_json(row))} for row in properties]}))
    write_bytes(judge_root, "challenge-eligibility.json", pretty_json({"schema_version": 1, "snapshot_id": SNAPSHOT_ID, "profile": "I", "status": "REFERENCE_VALIDATION_PENDING", "challenge_ready": False}))

    mapping = load_json(judge_root / "anonymization-map.json")
    checker = load_checker(checker_path)
    with tempfile.TemporaryDirectory(prefix="profile-i-reference-") as raw:
        temporary, solution = Path(raw), Path(raw) / "solution"
        project_reference(repository, pristine, solution, mapping)
        reference_patch = patch_bytes(pristine, solution)
        write_bytes(judge_root, "reference.patch", reference_patch)
        pristine_result = checker.evaluate_workspace(pristine, experiment_id="phase-d-profile-i", cell_id="pristine")
        reference_result = checker.evaluate_workspace(solution, experiment_id="phase-d-profile-i", cell_id="reference")
        write_bytes(judge_root, "evidence/pristine.json", pretty_json(pristine_result))
        write_bytes(judge_root, "evidence/reference.json", pretty_json(reference_result))
        mutation_summaries = []
        for mutation_id, target, mutate in MUTATIONS:
            mutated = temporary / mutation_id
            copy_tree(solution, mutated)
            mutate(mutated)
            mutation_patch = patch_bytes(solution, mutated)
            result = checker.evaluate_workspace(mutated, experiment_id="phase-d-profile-i", cell_id=mutation_id)
            write_bytes(judge_root, f"negative-mutations/{mutation_id}.patch", mutation_patch)
            write_bytes(judge_root, f"evidence/mutations/{mutation_id}.json", pretty_json(result))
            statuses = {item["property_id"]: item["status"] for item in result["properties"]}
            mutation_summaries.append({"mutation_id": mutation_id, "target_property_id": target, "statuses": statuses})
        reference_ok = reference_result["aggregate_status"] == "pass"
        pristine_failed = pristine_result["aggregate_status"] == "fail"
        mutation_ok = all(row["statuses"].get(row["target_property_id"]) == "fail" and all(status in {"pass", "blocked_by_prerequisite"} for key, status in row["statuses"].items() if key != row["target_property_id"]) for row in mutation_summaries)
        review = f"# Profile I anonymization review\n\n- Worker file count: {sum(1 for p in pristine.rglob('*') if p.is_file())}\n- Reference aggregate: {reference_result['aggregate_status']}\n- Pristine aggregate: {pristine_result['aggregate_status']}\n- Negative mutation contracts: {'pass' if mutation_ok else 'fail'}\n- The checker reads only W and committed Judge metadata; it does not read Phase B raw evidence.\n- Model, SDK, Codex, app-server, sandbox, and network calls: 0.\n"
        write_bytes(judge_root, "evidence/anonymization-review.md", review.encode())
        eligible = reference_ok and pristine_failed and mutation_ok
        write_bytes(judge_root, "challenge-eligibility.json", pretty_json({"schema_version": 1, "snapshot_id": SNAPSHOT_ID, "profile": "I", "status": "PROFILE_I_SOURCE_BUNDLE_VERIFIED" if eligible else "CHALLENGE_NOT_READY", "challenge_ready": False, "source_bundle_verified": eligible, "judge_runtime_boundary_verified": False, "reference_aggregate_status": reference_result["aggregate_status"], "pristine_aggregate_status": pristine_result["aggregate_status"], "negative_mutation_count": len(mutation_summaries)}))

    records = file_manifest(judge_root, exclude={"bundle-manifest.json"})
    manifest = {"schema_version": 1, "snapshot_id": SNAPSHOT_ID, "profile": "I", "status": load_json(judge_root / "challenge-eligibility.json")["status"], "source_commit": BASE_COMMIT, "reference_commit": REFERENCE_COMMIT, "file_count_excluding_manifest": len(records), "files": records, "payload_aggregate_sha256": sha256(canonical_json(records))}
    write_bytes(judge_root, "bundle-manifest.json", pretty_json(manifest))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and model-free validate the Profile I Judge source bundle.")
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    manifest = build(args.repository.resolve(strict=True))
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
