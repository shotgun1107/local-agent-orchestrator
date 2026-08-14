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
from pathlib import Path, PurePosixPath
from typing import Any, Callable


SNAPSHOT_ID = "realistic-compat-migration-001"
BASE_COMMIT = "dbd84422a315b8bc34d0fc2583862f5add8c7c44"
REFERENCE_COMMIT = "56c91334fb32c4699d11ef80769831f14a0431d6"
PROFILE_ROOT = Path("benchmarks/fixtures/routing-realistic-high-difficulty-v1") / SNAPSHOT_ID
JUDGE_ROOT = Path("benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1") / SNAPSHOT_ID
CHECKER_RELATIVE = Path("checker/check_properties.py")
PROBE_SOURCE_RELATIVE = Path("tools/benchmark-runner/scripts/probe_runtime_boundary.py")
PROBE_RELATIVE = Path("checker/probe_runtime_boundary.py")


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def pretty_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def git(repository: Path, *arguments: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        input=input_bytes,
        check=True,
        capture_output=True,
    ).stdout


def git_blob(repository: Path, commit: str, path: str) -> bytes:
    return git(repository, "show", f"{commit}:{path}")


def apply_mapping(payload: bytes, mapping: dict[str, Any]) -> bytes:
    value = payload
    for item in mapping["replacements"]:
        value = value.replace(
            str(item["source_utf8"]).encode("utf-8"),
            str(item["replacement_utf8"]).encode("utf-8"),
        )
    return value


def copy_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        raise RuntimeError(f"destination already exists: {destination}")
    shutil.copytree(source, destination)


def write_bytes(root: Path, relative: str, payload: bytes) -> None:
    path = PurePosixPath(relative)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise RuntimeError(f"unsafe path: {relative}")
    destination = root.joinpath(*path.parts)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)


def adapt_public_s2_test(payload: bytes) -> bytes:
    text = payload.decode("utf-8")
    old_root = '''GOLDEN_ROOT = (
    REPOSITORY_ROOT / "benchmarks" / "posthoc-checks" / "sdk-routing-v1" / "s2" / "golden"
)'''
    if old_root not in text:
        raise RuntimeError("historical S2 golden root contract changed")
    text = text.replace(old_root, "SOLUTION_ROOT = FIXTURE_ROOT", 1)
    old_copy = '''    if golden:
        shutil.copytree(GOLDEN_ROOT / fixture_id, workspace, dirs_exist_ok=True)
    return workspace'''
    if old_copy not in text:
        raise RuntimeError("historical S2 fixture copy contract changed")
    text = text.replace(
        old_copy,
        '''    # Phase D keeps reference outputs outside W.  The public regression
    # validates only the outputs currently present in the fixture tree.
    _ = golden
    return workspace''',
        1,
    )
    text = text.replace("GOLDEN_ROOT / fixture_id / relative", "SOLUTION_ROOT / fixture_id / relative")
    old_name = "test_s2_posthoc_pristine_golden_and_label_parity"
    if old_name not in text:
        raise RuntimeError("historical S2 posthoc test name changed")
    text = text.replace(old_name, "test_s2_posthoc_fixture_outputs_and_label_parity", 1)
    old_assertions = '''    assert evaluate_posthoc(fixture_id, pristine)["property_status"] == "fail"

    workspace = _copy_fixture(tmp_path / "golden", fixture_id, golden=True)
    c2_result = evaluate_posthoc(fixture_id, workspace)
    b1_result = evaluate_posthoc(fixture_id, workspace)
    assert c2_result == b1_result
    assert c2_result["property_status"] == "pass"'''
    if old_assertions not in text:
        raise RuntimeError("historical S2 pristine/golden assertion contract changed")
    text = text.replace(
        old_assertions,
        '''    c2_result = evaluate_posthoc(fixture_id, pristine)
    b1_result = evaluate_posthoc(fixture_id, pristine)
    assert c2_result == b1_result
    assert c2_result["property_status"] == "pass"''',
        1,
    )
    if "GOLDEN_ROOT" in text or "benchmarks/posthoc-checks" in text:
        raise RuntimeError("public S2 test still names a hidden golden path")
    return text.encode("utf-8")


def operator_contract() -> dict[str, object]:
    schema = "tools/benchmark-runner/schemas/v1/execution-plan.schema.json"
    common = {
        "success_exit_codes": [0],
        "failure_map": {"1": "contract_or_state_failure", "2": "usage_error"},
        "public_schema": schema,
    }
    rows = [
        ("create", ["python", "-m", "benchmark_runner", "routing", "create"], "frozen source and empty state root", ["not_created"], ["ready"], True, "routing_suite:initialize_routing_s2_experiment"),
        ("status", ["python", "-m", "benchmark_runner", "routing", "status"], "existing experiment", ["ready", "running", "terminal"], ["ready", "running", "terminal"], False, "routing_suite:routing_s2_nonlive_status"),
        ("run-next", ["python", "-m", "benchmark_runner", "routing", "run-next"], "ready experiment with no stop condition", ["ready", "running"], ["ready", "running", "terminal"], True, "routing_suite:run_next_routing_s2_nonlive_cell"),
        ("export", ["python", "-m", "benchmark_runner", "routing", "export"], "terminal sealed experiment", ["terminal"], ["exported"], True, "routing_suite:export_routing_s2_nonlive"),
        ("verify", ["python", "-m", "benchmark_runner", "routing", "verify"], "sealed export", ["exported"], ["verified"], True, "routing_suite:verify_routing_s2_nonlive_export"),
    ]
    return {
        "schema_version": 1,
        "commands": [
            {
                "command_id": command_id,
                "argv": argv,
                "precondition": precondition,
                "allowed_source_states": source_states,
                "allowed_terminal_states": terminal_states,
                "stop_before_next_dispatch": stop,
                "implementation_symbol": symbol,
                **common,
            }
            for command_id, argv, precondition, source_states, terminal_states, stop, symbol in rows
        ],
    }


def migration_work_payloads(workspace: Path) -> tuple[dict[str, object], dict[str, object]]:
    surface = load_json(workspace / "profile-r/requirements/change-surface.json")
    entries: list[dict[str, object]] = []
    for task in surface["tasks"]:
        for relative in task["write_paths"]:
            entries.append(
                {
                    "path": relative,
                    "kind": "tree" if relative.endswith("/**") else "file",
                    "migration_action": "extend" if (workspace / relative.removesuffix("/**")).exists() else "add",
                    "owner_task": task["task_id"],
                }
            )
    entries.sort(key=lambda item: str(item["path"]).encode("utf-8"))
    inventory = {"schema_version": 1, "entries": entries}
    evidence = {
        "legacy-stage-bytes": ["benchmarks/suites/sdk-routing-v1/stages/s1-baseline.yaml"],
        "stage-discriminator": ["benchmarks/suites/sdk-routing-v1/stage.schema.json"],
        "plan-source-binding": ["tools/benchmark-runner/src/benchmark_runner/routing_suite.py"],
        "reserve-isolation": ["tools/benchmark-runner/src/benchmark_runner/s2_policy.py"],
        "lifecycle-reuse": ["tools/benchmark-runner/src/benchmark_runner/routing_live.py"],
        "export-roundtrip": ["tools/benchmark-runner/src/benchmark_runner/routing_suite.py"],
        "cross-checkout-repro": ["benchmarks/suites/sdk-routing-v1/stage.schema.json"],
        "operator-contract": ["profile-r/work/operator-contract.json"],
    }
    statuses = {
        "legacy-stage-bytes": "preserve",
        "stage-discriminator": "extend",
        "plan-source-binding": "extend",
        "reserve-isolation": "extend",
        "lifecycle-reuse": "preserve",
        "export-roundtrip": "extend",
        "cross-checkout-repro": "preserve",
        "operator-contract": "extend",
    }
    ledger = {
        "schema_version": 1,
        "invariants": [
            {"id": key, "status": statuses[key], "evidence_paths": evidence[key]}
            for key in statuses
        ],
    }
    return ledger, inventory


def append_operator_readme(workspace: Path, contract: dict[str, object]) -> None:
    path = workspace / "tools/benchmark-runner/README.md"
    text = path.read_text(encoding="utf-8").rstrip() + "\n\n"
    text += "<!-- profile-r-operator-contract:start -->\n"
    text += "## Profile R operator contract\n\n"
    for command in contract["commands"]:
        text += f"- `{command['command_id']}`: `{command['implementation_symbol']}`; stop-before-next-dispatch=`{str(command['stop_before_next_dispatch']).lower()}`\n"
    text += "<!-- profile-r-operator-contract:end -->\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def project_reference(repository: Path, pristine: Path, solution: Path, mapping: dict[str, Any], composition: dict[str, Any]) -> None:
    copy_tree(pristine, solution)
    for record in composition["records"]:
        category = record["category"]
        relative = str(record["path"])
        if category in {"historical_result_or_evidence", "golden_or_export_mirror"}:
            continue
        if relative.startswith("benchmarks/posthoc-checks/sdk-routing-v1/s2/golden/"):
            continue
        payload = apply_mapping(git_blob(repository, REFERENCE_COMMIT, relative), mapping)
        if relative == "tools/benchmark-runner/tests/test_routing_s2.py":
            payload = adapt_public_s2_test(payload)
        write_bytes(solution, relative, payload)
    for record in composition["records"]:
        if record["category"] != "golden_or_export_mirror":
            continue
        source = apply_mapping(git_blob(repository, REFERENCE_COMMIT, str(record["path"])), mapping)
        targets = record["canonical_source_paths"]
        if len(targets) != 1:
            raise RuntimeError("golden mirror must have exactly one Worker target")
        write_bytes(solution, str(targets[0]), source)
    ledger, inventory = migration_work_payloads(solution)
    write_bytes(solution, "profile-r/work/migration-ledger.json", canonical_json(ledger))
    write_bytes(solution, "profile-r/work/source-inventory.json", canonical_json(inventory))
    contract = operator_contract()
    write_bytes(solution, "profile-r/work/operator-contract.json", canonical_json(contract))
    append_operator_readme(solution, contract)


def initialize_repo(path: Path) -> None:
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "core.autocrlf", "false")
    git(path, "config", "core.longpaths", "true")
    git(path, "config", "user.name", "profile-r-builder")
    git(path, "config", "user.email", "profile-r@fixture.invalid")
    git(path, "add", "-A")
    environment = os.environ.copy()
    environment.update({"GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z"})
    subprocess.run(["git", "commit", "-q", "-m", "baseline"], cwd=path, env=environment, check=True)


def patch_bytes(baseline: Path, target: Path) -> bytes:
    with tempfile.TemporaryDirectory(prefix="profile-r-diff-") as raw:
        repo = Path(raw) / "repository"
        copy_tree(baseline, repo)
        initialize_repo(repo)
        for child in list(repo.iterdir()):
            if child.name == ".git":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        for source in target.iterdir():
            destination = repo / source.name
            if source.is_dir():
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)
        git(repo, "add", "-N", ".")
        return git(repo, "diff", "--binary", "--full-index", "--no-renames", "HEAD", "--", ".")


def replace_once(path: Path, before: bytes, after: bytes) -> None:
    payload = path.read_bytes()
    if payload.count(before) != 1:
        raise RuntimeError(f"mutation anchor is not unique: {path}")
    path.write_bytes(payload.replace(before, after, 1))


def mutate_legacy_bytes(root: Path) -> None:
    path = root / "tools/benchmark-runner/schemas/v1/measurement.schema.json"
    path.write_bytes(path.read_bytes() + b"\n")


def mutate_stage_discriminator(root: Path) -> None:
    replace_once(
        root / "tools/benchmark-runner/src/benchmark_runner/routing_suite.py",
        b'    stage_id: Literal["s2-intermediate"]',
        b'    stage_id: Literal["s1-baseline"]',
    )


def mutate_plan_order(root: Path) -> None:
    path = root / "benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml"
    replace_once(path, b"cell_s2_a_1_c2", b"cell_s2_a_1_b1_mutated")


def mutate_reserve(root: Path) -> None:
    path = root / "tools/benchmark-runner/src/benchmark_runner/s2_policy.py"
    replace_once(
        path,
        b"return min(project_policy_turn_cap, task_count + remaining)",
        b"return min(project_policy_turn_cap, task_count + remaining + 1)",
    )


def mutate_lifecycle(root: Path) -> None:
    write_bytes(root, "tools/benchmark-runner/src/benchmark_runner/routing_s2_live.py", b'"""Forbidden duplicate S2 lifecycle."""\n')


def mutate_export(root: Path) -> None:
    path = root / "tools/benchmark-runner/src/benchmark_runner/routing_suite.py"
    before = b'''def verify_routing_s2_nonlive_export(export_root: Path) -> dict[str, Any]:\n    return _verify_routing_nonlive_export(\n        export_root,\n        expected_stage_id="s2-intermediate",\n    )'''
    after = before.replace(b'expected_stage_id="s2-intermediate"', b'expected_stage_id="s1-baseline"')
    replace_once(path, before, after)


def mutate_checkout(root: Path) -> None:
    path = root / ".gitattributes"
    replace_once(path, b"* text=auto eol=lf", b"* text=auto")


def mutate_operator(root: Path) -> None:
    path = root / "profile-r/work/operator-contract.json"
    value = load_json(path)
    value["commands"][2]["stop_before_next_dispatch"] = False
    path.write_bytes(canonical_json(value))


MUTATIONS: tuple[tuple[str, str, Callable[[Path], None]], ...] = (
    ("r-p01-legacy-bytes", "R-P01-LEGACY-BYTES", mutate_legacy_bytes),
    ("r-p02-stage-discriminator", "R-P02-STAGE-DISCRIMINATOR", mutate_stage_discriminator),
    ("r-p03-plan-binding", "R-P03-PLAN-BINDING", mutate_plan_order),
    ("r-p04-reserve-isolation", "R-P04-RESERVE-ISOLATION", mutate_reserve),
    ("r-p05-lifecycle-reuse", "R-P05-LIFECYCLE-REUSE", mutate_lifecycle),
    ("r-p06-export-roundtrip", "R-P06-EXPORT-ROUNDTRIP", mutate_export),
    ("r-p07-cross-checkout", "R-P07-CROSS-CHECKOUT-REPRO", mutate_checkout),
    ("r-p08-operator-contract", "R-P08-OPERATOR-CONTRACT", mutate_operator),
)


def load_checker(checker_path: Path):
    spec = importlib.util.spec_from_file_location("profile_r_check_properties", checker_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Profile R checker")
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
    profile_root = repository / PROFILE_ROOT
    judge_root = repository / JUDGE_ROOT
    pristine = profile_root / "workspace"
    checker_path = judge_root / CHECKER_RELATIVE
    if not pristine.is_dir() or not checker_path.is_file():
        raise RuntimeError("Profile R Worker snapshot or checker is missing")
    generated = {
        "challenge-eligibility.json", "r-change-composition.json", "property-catalog.json",
        "prerequisite-dag.json", "information-dependency-map.json", "worker-information-boundary.json",
        "solution-leakage-catalog.json", "operator-contract.json", "incident-claims.json",
        "reference.patch", "bundle-manifest.json", PROBE_RELATIVE.as_posix(),
    }
    generated_prefixes = ("negative-mutations/", "evidence/")
    for path in list(judge_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(judge_root).as_posix()
        if relative in generated or relative.startswith(generated_prefixes):
            path.unlink()
    for directory in sorted((item for item in judge_root.rglob("*") if item.is_dir()), reverse=True):
        if directory != judge_root and not any(directory.iterdir()):
            directory.rmdir()

    write_bytes(
        judge_root,
        PROBE_RELATIVE.as_posix(),
        (repository / PROBE_SOURCE_RELATIVE).read_bytes(),
    )

    mapping = load_json(judge_root / "anonymization-map.json")
    composition = load_json(profile_root / "r-change-composition.json")
    legacy_paths = (
        "tools/benchmark-runner/schemas/v1/execution-plan.schema.json",
        "tools/benchmark-runner/schemas/v1/intervention-event.schema.json",
        "tools/benchmark-runner/schemas/v1/measurement.schema.json",
        "benchmarks/suites/sdk-routing-v1/stages/s1-baseline.yaml",
    )
    properties = [
        {"property_id": "R-P01-LEGACY-BYTES", "severity": "critical", "prerequisite_ids": []},
        {"property_id": "R-P02-STAGE-DISCRIMINATOR", "severity": "critical", "prerequisite_ids": []},
        {"property_id": "R-P03-PLAN-BINDING", "severity": "critical", "prerequisite_ids": ["R-P02-STAGE-DISCRIMINATOR"]},
        {"property_id": "R-P04-RESERVE-ISOLATION", "severity": "major", "prerequisite_ids": ["R-P03-PLAN-BINDING"]},
        {"property_id": "R-P05-LIFECYCLE-REUSE", "severity": "major", "prerequisite_ids": []},
        {"property_id": "R-P06-EXPORT-ROUNDTRIP", "severity": "critical", "prerequisite_ids": ["R-P02-STAGE-DISCRIMINATOR", "R-P03-PLAN-BINDING"]},
        {"property_id": "R-P07-CROSS-CHECKOUT-REPRO", "severity": "major", "prerequisite_ids": ["R-P06-EXPORT-ROUNDTRIP"]},
        {"property_id": "R-P08-OPERATOR-CONTRACT", "severity": "major", "prerequisite_ids": ["R-P03-PLAN-BINDING", "R-P06-EXPORT-ROUNDTRIP"]},
    ]
    catalog = {
        "schema_version": 1,
        "profile": "R",
        "properties": properties,
        "legacy_byte_contract": {path: sha256((pristine / path).read_bytes()) for path in legacy_paths},
    }
    dag = {"schema_version": 1, "properties": [{"property_id": item["property_id"], "prerequisite_ids": item["prerequisite_ids"]} for item in properties]}
    write_bytes(judge_root, "property-catalog.json", pretty_json(catalog))
    write_bytes(judge_root, "prerequisite-dag.json", pretty_json(dag))
    write_bytes(judge_root, "r-change-composition.json", pretty_json(composition))
    contract = operator_contract()
    write_bytes(judge_root, "operator-contract.json", pretty_json(contract))
    write_bytes(judge_root, "incident-claims.json", pretty_json({"schema_version": 1, "profile": "R", "not_applicable": True, "claims": []}))

    information = {
        "schema_version": 1,
        "properties": [
            {
                "property_id": item["property_id"],
                "worker_readable_paths": sorted({entry["path"] for entry in profile_root.joinpath("worker-snapshot-manifest.json") and load_json(profile_root / "worker-snapshot-manifest.json")["files"] if isinstance(entry, dict) and isinstance(entry.get("path"), str) and not str(entry["path"]).startswith(("benchmark_checks/", ".orchestrator/"))})[:1],
                "task_ids": [f"R{index:02d}"],
                "required_fact_description": "The public migration contract and declared source surface needed for this property.",
                "goal_alignment": "Directly checks one frozen Profile R migration invariant.",
                "source_evidence_sha256": sha256(canonical_json(item)),
            }
            for index, item in enumerate(properties, 1)
        ],
    }
    task_paths = {
        "R-P01-LEGACY-BYTES": ["profile-r/requirements/migration-contract.md", "tools/benchmark-runner/schemas/v1/measurement.schema.json"],
        "R-P02-STAGE-DISCRIMINATOR": ["profile-r/requirements/migration-contract.md", "benchmarks/suites/sdk-routing-v1/stage.schema.json"],
        "R-P03-PLAN-BINDING": ["profile-r/requirements/migration-contract.md", "benchmarks/suites/sdk-routing-v1/stages/s1-baseline.yaml"],
        "R-P04-RESERVE-ISOLATION": ["profile-r/requirements/migration-contract.md", "tools/benchmark-runner/src/benchmark_runner/routing_suite.py"],
        "R-P05-LIFECYCLE-REUSE": ["profile-r/requirements/migration-contract.md", "tools/benchmark-runner/src/benchmark_runner/routing_live.py"],
        "R-P06-EXPORT-ROUNDTRIP": ["profile-r/requirements/migration-contract.md", "tools/benchmark-runner/src/benchmark_runner/routing_suite.py"],
        "R-P07-CROSS-CHECKOUT-REPRO": ["profile-r/requirements/migration-contract.md", "tools/benchmark-runner/tests/test_routing_suite.py"],
        "R-P08-OPERATOR-CONTRACT": ["profile-r/requirements/operator-contract-schema.json", "tools/benchmark-runner/README.md"],
    }
    for record in information["properties"]:
        record["worker_readable_paths"] = task_paths[record["property_id"]]
    write_bytes(judge_root, "information-dependency-map.json", pretty_json(information))
    write_bytes(judge_root, "worker-information-boundary.json", pretty_json({
        "schema_version": 1,
        "worker_root": "workspace",
        "allowed_information": ["public requirements", "public developer checks", "base implementation", "declared Task graph"],
        "forbidden_information": ["reference.patch", "negative-mutations/**", "checker/**", "evidence/**", "historical reference commit explanation", "golden solution tree"],
    }))
    write_bytes(judge_root, "solution-leakage-catalog.json", pretty_json({
        "schema_version": 1,
        "forbidden_worker_literals": ["reference.patch", "negative-mutations/", "check_properties.py", REFERENCE_COMMIT],
        "forbidden_worker_paths": ["benchmarks/judge-source/**", "benchmarks/posthoc-checks/sdk-routing-v1/s2/golden/**"],
    }))
    write_bytes(judge_root, "challenge-eligibility.json", pretty_json({
        "schema_version": 1,
        "snapshot_id": SNAPSHOT_ID,
        "profile": "R",
        "status": "REFERENCE_VALIDATION_PENDING",
        "challenge_ready": False,
        "profile_i_status": "not_applicable",
    }))

    checker = load_checker(checker_path)
    with tempfile.TemporaryDirectory(prefix="profile-r-reference-") as raw:
        temporary = Path(raw)
        solution = temporary / "solution"
        project_reference(repository, pristine, solution, mapping, composition)
        reference_patch = patch_bytes(pristine, solution)
        write_bytes(judge_root, "reference.patch", reference_patch)
        pristine_eval = temporary / "eval-pristine"
        copy_tree(pristine, pristine_eval)
        initialize_repo(pristine_eval)
        reference_eval = temporary / "eval-reference"
        copy_tree(pristine, reference_eval)
        initialize_repo(reference_eval)
        git(reference_eval, "apply", "-", input_bytes=reference_patch)
        pristine_result = checker.evaluate_workspace(pristine_eval, experiment_id="phase-d-profile-r", cell_id="pristine")
        reference_result = checker.evaluate_workspace(reference_eval, experiment_id="phase-d-profile-r", cell_id="reference")
        write_bytes(judge_root, "evidence/pristine.json", pretty_json(pristine_result))
        write_bytes(judge_root, "evidence/reference.json", pretty_json(reference_result))

        mutation_summaries = []
        for mutation_id, target_property, mutate in MUTATIONS:
            mutated = temporary / f"mutation-{mutation_id}"
            copy_tree(solution, mutated)
            mutate(mutated)
            mutation_patch = patch_bytes(solution, mutated)
            mutation_eval = temporary / f"eval-{mutation_id}"
            copy_tree(pristine, mutation_eval)
            initialize_repo(mutation_eval)
            git(mutation_eval, "apply", "-", input_bytes=reference_patch)
            git(mutation_eval, "apply", "-", input_bytes=mutation_patch)
            result = checker.evaluate_workspace(mutation_eval, experiment_id="phase-d-profile-r", cell_id=mutation_id)
            write_bytes(judge_root, f"negative-mutations/{mutation_id}.patch", mutation_patch)
            write_bytes(judge_root, f"evidence/mutations/{mutation_id}.json", pretty_json(result))
            statuses = {item["property_id"]: item["status"] for item in result["properties"]}
            mutation_summaries.append({"mutation_id": mutation_id, "target_property_id": target_property, "statuses": statuses})

        reference_ok = reference_result["aggregate_status"] == "pass"
        pristine_failed = pristine_result["aggregate_status"] == "fail"
        mutation_ok = all(
            item["statuses"].get(item["target_property_id"]) == "fail"
            and all(
                status in {"pass", "blocked_by_prerequisite"}
                for property_id, status in item["statuses"].items()
                if property_id != item["target_property_id"]
            )
            for item in mutation_summaries
        )
        forbidden = load_json(judge_root / "solution-leakage-catalog.json")
        worker_files = [path for path in pristine.rglob("*") if path.is_file()]
        leakage_hits = []
        for path in worker_files:
            payload = path.read_bytes()
            for literal in forbidden["forbidden_worker_literals"]:
                if str(literal).encode("utf-8") in payload:
                    leakage_hits.append({"path": path.relative_to(pristine).as_posix(), "literal": literal})
        review = (
            "# Profile R anonymization and solution-leakage review\n\n"
            f"- Worker file count: {len(worker_files)}\n"
            f"- Reference aggregate: {reference_result['aggregate_status']}\n"
            f"- Pristine aggregate: {pristine_result['aggregate_status']}\n"
            f"- Negative mutation contracts: {'pass' if mutation_ok else 'fail'}\n"
            f"- Forbidden Worker literal hits: {len(leakage_hits)}\n"
            "- The public S2 regression consumes current fixture outputs and never reads the hidden golden tree.\n"
            "- This source bundle does not claim the protected Judge runtime filesystem/no-network boundary.\n"
        )
        write_bytes(judge_root, "evidence/anonymization-review.md", review.encode("utf-8"))
        eligible = reference_ok and pristine_failed and mutation_ok and not leakage_hits
        eligibility = load_json(judge_root / "challenge-eligibility.json")
        eligibility.update({
            "status": "PROFILE_R_SOURCE_BUNDLE_VERIFIED" if eligible else "CHALLENGE_NOT_READY",
            "challenge_ready": False,
            "source_bundle_verified": eligible,
            "judge_runtime_boundary_verified": False,
            "reference_aggregate_status": reference_result["aggregate_status"],
            "pristine_aggregate_status": pristine_result["aggregate_status"],
            "negative_mutation_count": len(mutation_summaries),
        })
        write_bytes(judge_root, "challenge-eligibility.json", pretty_json(eligibility))

    records = file_manifest(judge_root, exclude={"bundle-manifest.json"})
    manifest = {
        "schema_version": 1,
        "snapshot_id": SNAPSHOT_ID,
        "profile": "R",
        "status": load_json(judge_root / "challenge-eligibility.json")["status"],
        "source_commit": BASE_COMMIT,
        "reference_commit": REFERENCE_COMMIT,
        "file_count_excluding_manifest": len(records),
        "files": records,
        "payload_aggregate_sha256": sha256(canonical_json(records)),
    }
    write_bytes(judge_root, "bundle-manifest.json", pretty_json(manifest))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and model-free validate the Profile R Judge source bundle.")
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    repository = args.repository.resolve(strict=True)
    controller_source = str(repository / "tools/benchmark-runner/src")
    sys.path.insert(0, controller_source)
    try:
        manifest = build(repository)
    finally:
        sys.path.remove(controller_source)
    print(canonical_json({"status": manifest["status"], "file_count": manifest["file_count_excluding_manifest"], "payload_aggregate_sha256": manifest["payload_aggregate_sha256"]}).decode("utf-8"), end="")
    return 0 if manifest["status"] == "PROFILE_R_SOURCE_BUNDLE_VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
