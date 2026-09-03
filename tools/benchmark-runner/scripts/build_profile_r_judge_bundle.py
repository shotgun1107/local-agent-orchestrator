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

import yaml


SNAPSHOT_ID = "realistic-compat-migration-001"
BASE_COMMIT = "dbd84422a315b8bc34d0fc2583862f5add8c7c44"
REFERENCE_COMMIT = "56c91334fb32c4699d11ef80769831f14a0431d6"
REFERENCE_OVERRIDE_ROOT = (
    Path("benchmarks/reference-source/sdk-routing-realistic-high-difficulty-v1/")
    / "realistic-compat-migration-001/solution-overrides"
)
PROFILE_ROOT = Path("benchmarks/fixtures/routing-realistic-high-difficulty-v1") / SNAPSHOT_ID
JUDGE_ROOT = Path("benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1") / SNAPSHOT_ID
CHECKER_RELATIVE = Path("checker/check_properties.py")
PROBE_SOURCE_RELATIVE = Path("tools/benchmark-runner/scripts/probe_runtime_boundary.py")
PROBE_RELATIVE = Path("checker/probe_runtime_boundary.py")
R07_GROWTH_PATH_MINIMUM = 261


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


def git(
    repository: Path,
    *arguments: str,
    input_bytes: bytes | None = None,
    environment: dict[str, str] | None = None,
) -> bytes:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        input=input_bytes,
        env=environment,
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
    result_anchor = '''    assert len(results) == 4
    assert all(result.check_success for result in results)'''
    result_replacement = '''    assert len(results) == 4
    expected_cells = {
        "cell_s2_a_1_c2": "c2",
        "cell_s2_a_1_b1": "b1",
        "cell_s2_b_1_b1": "b1",
        "cell_s2_b_1_c2": "c2",
    }
    assert {result.cell_id: result.variant_id for result in results} == expected_cells
    for result in results:
        assert result.cell_state == "SEALED"
        assert result.check_success is True
        assert result.measurement_path
        assert len(result.sealed_measurement_sha256) == 64
        assert result.actual_model_turns == 0'''
    if text.count(result_anchor) != 1:
        raise RuntimeError("historical S2 per-Cell result contract changed")
    text = text.replace(result_anchor, result_replacement, 1)
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
    create_anchor = "def _create_s2_source_repository(tmp_path: Path) -> tuple[Path, Path, Path]:"
    if text.count(create_anchor) != 1:
        raise RuntimeError("historical S2 source-repository helper changed")
    legacy_helper = '''def _write_legacy_b1_project(workspace: Path) -> None:
    project_path = workspace / ".orchestrator" / "project.yaml"
    project = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    project_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": project["schema_version"],
                "project_id": project["project_id"],
                "purpose": "legacy S2 model-free fixture",
                "requirements": ["preserve the public S2 contract"],
                "task_order": ["T1", "T2", "T3"],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
        newline="\\n",
    )


'''
    text = text.replace(create_anchor, legacy_helper + create_anchor, 1)
    old_fixture_copy = '''        shutil.copytree(FIXTURE_ROOT / fixture_id, target)
    _git(source, "init", "-q", "-b", "main")'''
    new_fixture_copy = '''        shutil.copytree(FIXTURE_ROOT / fixture_id, target)
        _write_legacy_b1_project(target)
        _canonicalize_prepared_b1_project(target)
    _git(source, "init", "-q", "-b", "main")'''
    if text.count(old_fixture_copy) != 1:
        raise RuntimeError("historical S2 source fixture copy contract changed")
    text = text.replace(old_fixture_copy, new_fixture_copy, 1)
    completed_anchor = "def _completed_result(paths: list[str]) -> dict[str, object]:"
    if text.count(completed_anchor) != 1:
        raise RuntimeError("historical S2 completed-result helper changed")
    canonicalization = '''def _canonicalize_prepared_b1_project(workspace: Path) -> dict[str, object]:
    project_path = workspace / ".orchestrator" / "project.yaml"
    legacy = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    assert set(legacy) == {
        "schema_version",
        "project_id",
        "purpose",
        "requirements",
        "task_order",
    }
    capabilities = yaml.safe_load(
        (workspace / ".orchestrator" / "capabilities.yaml").read_text(encoding="utf-8")
    )["profiles"]
    policies = yaml.safe_load(
        (workspace / ".orchestrator" / "policies.yaml").read_text(encoding="utf-8")
    )["policies"]
    assert len(capabilities) == len(policies) == 1
    canonical = {
        "schema_version": legacy["schema_version"],
        "project_id": legacy["project_id"],
        "core_compat": ">=0.1,<0.2",
        "repository_root": ".",
        "default_capability_profile": next(iter(capabilities)),
        "default_policy": next(iter(policies)),
    }
    project_path.write_text(
        yaml.safe_dump(canonical, sort_keys=False),
        encoding="utf-8",
        newline="\\n",
    )
    return canonical


def test_s2_b1_preflight_canonicalizes_legacy_project_pack(tmp_path: Path) -> None:
    for fixture_id in (CONFIG_FIXTURE_ID, INCIDENT_FIXTURE_ID):
        workspace = tmp_path / fixture_id
        shutil.copytree(FIXTURE_ROOT / fixture_id, workspace)
        _write_legacy_b1_project(workspace)
        legacy = yaml.safe_load(
            (workspace / ".orchestrator" / "project.yaml").read_text(encoding="utf-8")
        )
        assert set(legacy) == {
            "schema_version",
            "project_id",
            "purpose",
            "requirements",
            "task_order",
        }
        canonical = _canonicalize_prepared_b1_project(workspace)
        assert set(canonical) == {
            "schema_version",
            "project_id",
            "core_compat",
            "repository_root",
            "default_capability_profile",
            "default_policy",
        }


'''
    text = text.replace(completed_anchor, canonicalization + completed_anchor, 1)
    if "GOLDEN_ROOT" in text or "benchmarks/posthoc-checks" in text:
        raise RuntimeError("public S2 test still names a hidden golden path")
    return text.encode("utf-8")


def adapt_public_s1_test(payload: bytes) -> bytes:
    """Make the selected legacy S1 regressions hermetic in a one-commit W.

    The historical tests intentionally bind frozen fixtures to commits that are
    not present in a materialized Profile R Worker repository.  Keep the same
    production paths and assertions, but give those tests a local Git source
    whose manifests bind the fixture bytes that are actually under test.
    """

    text = payload.decode("utf-8")
    import_anchor = "import shutil\n"
    if text.count(import_anchor) != 1:
        raise RuntimeError("historical S1 import surface changed")
    text = text.replace(
        import_anchor,
        "import os\n" + import_anchor + "import subprocess\nimport tempfile\n",
        1,
    )
    old_git = '''def _git() -> Path:
    executable = shutil.which("git")
    assert executable is not None
    return Path(executable)
'''
    if old_git not in text:
        raise RuntimeError("historical S1 Git helper contract changed")
    helper = old_git + '''

def _fixture_git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        [
            str(_git()),
            "-c",
            "core.longpaths=true",
            "-C",
            str(repository),
            *arguments,
        ],
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "profile-r-fixture",
            "GIT_AUTHOR_EMAIL": "profile-r@test.invalid",
            "GIT_COMMITTER_NAME": "profile-r-fixture",
            "GIT_COMMITTER_EMAIL": "profile-r@test.invalid",
            "GIT_AUTHOR_DATE": "2026-01-01T00:00:00+00:00",
            "GIT_COMMITTER_DATE": "2026-01-01T00:00:00+00:00",
        },
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def _write_self_contained_manifest(source: Path, relative: str) -> None:
    value = yaml.safe_load((REPOSITORY_ROOT / relative).read_text(encoding="utf-8"))
    commit = _fixture_git(source, "rev-parse", "HEAD")
    for fixture in value["fixtures"]:
        fixture["commit"] = commit
        fixture["git_tree"] = _fixture_git(
            source,
            "rev-parse",
            f"HEAD:{fixture['path']}",
        )
    destination = source / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        yaml.safe_dump(value, sort_keys=False),
        encoding="utf-8",
        newline="\\n",
    )


def _create_self_contained_s1_repository(tmp_path: Path) -> Path:
    _ = tmp_path
    source = Path(tempfile.mkdtemp(prefix="s1-", dir=os.environ["TEMP"]))
    for fixture_id in (
        "code-change",
        "document-read",
        "sequential-code-change",
        "sequential-document",
    ):
        destination = source / "benchmarks" / "fixtures" / fixture_id
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(REPOSITORY_ROOT / "benchmarks" / "fixtures" / fixture_id, destination)
    shutil.copytree(
        SUITE_ROOT,
        source / "benchmarks" / "suites" / "sdk-routing-v1",
    )
    source.mkdir(parents=True, exist_ok=True)
    _fixture_git(source, "init", "-q", "-b", "main")
    _fixture_git(source, "config", "core.autocrlf", "false")
    _fixture_git(source, "config", "core.filemode", "false")
    _fixture_git(source, "config", "core.longpaths", "true")
    _fixture_git(source, "add", "-A")
    _fixture_git(source, "commit", "-q", "-m", "Profile R self-contained S1 fixture")
    for relative in (
        "benchmarks/manifests/b0-b1-frozen.yaml",
        "benchmarks/manifests/b0-b1-sequential-followup.yaml",
    ):
        _write_self_contained_manifest(source, relative)
    return source


@pytest.fixture
def self_contained_s1_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    source = _create_self_contained_s1_repository(tmp_path)
    suite_root = source / "benchmarks" / "suites" / "sdk-routing-v1"
    monkeypatch.setitem(globals(), "REPOSITORY_ROOT", source)
    monkeypatch.setitem(globals(), "SUITE_ROOT", suite_root)
    monkeypatch.setitem(globals(), "SUITE_PATH", suite_root / "suite.yaml")
    monkeypatch.setitem(
        globals(),
        "STAGE_PATH",
        suite_root / "stages" / "s1-baseline.yaml",
    )
    try:
        yield source
    finally:
        shutil.rmtree(source, ignore_errors=True)
'''
    text = text.replace(old_git, helper, 1)
    signature_replacements = {
        '''def test_complexity_profiles_are_recomputed_from_frozen_fixture_trees() -> None:''': '''def test_complexity_profiles_are_recomputed_from_frozen_fixture_trees(
    self_contained_s1_source: Path,
) -> None:''',
        '''def test_s1_plan_has_exact_eight_cell_order_and_calibration_only_policy() -> None:''': '''def test_s1_plan_has_exact_eight_cell_order_and_calibration_only_policy(
    self_contained_s1_source: Path,
) -> None:''',
        '''def test_model_free_runner_executes_exactly_one_next_cell_and_seals(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:''': '''def test_model_free_runner_executes_exactly_one_next_cell_and_seals(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    self_contained_s1_source: Path,
) -> None:''',
        '''def test_model_free_status_and_export_reject_an_incomplete_suite(
    tmp_path: Path,
) -> None:''': '''def test_model_free_status_and_export_reject_an_incomplete_suite(
    tmp_path: Path,
    self_contained_s1_source: Path,
) -> None:''',
        '''def test_all_eight_model_free_cells_seal_export_and_detect_tampering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:''': '''def test_all_eight_model_free_cells_seal_export_and_detect_tampering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    self_contained_s1_source: Path,
) -> None:''',
    }
    for old, new in signature_replacements.items():
        if text.count(old) != 1:
            raise RuntimeError("historical S1 selected regression signature changed")
        text = text.replace(old, new, 1)
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
        "r01-source-boundary": ["profile-r/requirements/change-surface.json"],
        "r02-stage-discriminator": ["benchmarks/suites/sdk-routing-v1/stage.schema.json"],
        "r03-config-fixture": ["benchmarks/fixtures/routing-v1/intermediate/three-stage-config-migration/benchmark-run.yaml"],
        "r04-incident-fixture": ["benchmarks/fixtures/routing-v1/intermediate/three-stage-incident-analysis/benchmark-run.yaml"],
        "r05-manifest-binding": ["benchmarks/manifests/sdk-routing-s2-intermediate.yaml"],
        "r06-plan-binding": ["tools/benchmark-runner/src/benchmark_runner/routing_suite.py"],
        "r07-routing-policy": ["tools/benchmark-runner/src/benchmark_runner/s2_policy.py"],
        "r08-lifecycle-reuse": ["tools/benchmark-runner/src/benchmark_runner/routing_live.py"],
        "r09-status-posthoc": ["tools/benchmark-runner/src/benchmark_runner/s2_posthoc.py"],
        "r10-export-verify": ["tools/benchmark-runner/src/benchmark_runner/routing_suite.py"],
        "r11-s2-e2e": ["tools/benchmark-runner/tests/test_routing_s2.py"],
        "r12-s1-portability": ["tools/benchmark-runner/tests/test_routing_suite.py"],
        "r13-operator-contract": ["profile-r/work/operator-contract.json"],
    }
    statuses = {
        "r01-source-boundary": "preserve",
        "r02-stage-discriminator": "extend",
        "r03-config-fixture": "add",
        "r04-incident-fixture": "add",
        "r05-manifest-binding": "add",
        "r06-plan-binding": "extend",
        "r07-routing-policy": "add",
        "r08-lifecycle-reuse": "preserve",
        "r09-status-posthoc": "extend",
        "r10-export-verify": "extend",
        "r11-s2-e2e": "add",
        "r12-s1-portability": "preserve",
        "r13-operator-contract": "add",
    }
    ledger = {
        "schema_version": 1,
        "invariants": [
            {"id": key, "status": statuses[key], "evidence_paths": evidence[key]}
            for key in statuses
        ],
    }
    return ledger, inventory


def bind_s2_manifest_to_projected_fixtures(solution: Path) -> None:
    manifest_path = solution / "benchmarks/manifests/sdk-routing-s2-intermediate.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_AUTHOR_NAME": "profile-r-reference",
            "GIT_AUTHOR_EMAIL": "profile-r@test.invalid",
            "GIT_COMMITTER_NAME": "profile-r-reference",
            "GIT_COMMITTER_EMAIL": "profile-r@test.invalid",
            "GIT_AUTHOR_DATE": "2026-01-01T00:00:00+00:00",
            "GIT_COMMITTER_DATE": "2026-01-01T00:00:00+00:00",
        }
    )
    with tempfile.TemporaryDirectory(prefix="profile-r-r05-reference-") as raw:
        source = Path(raw) / "source"
        for fixture in manifest["fixtures"]:
            relative = Path(str(fixture["path"]))
            destination = source / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(solution / relative, destination)
        git(source, "init", "-q", "-b", "main", environment=environment)
        git(source, "config", "core.autocrlf", "false", environment=environment)
        git(source, "config", "core.filemode", "false", environment=environment)
        git(source, "config", "core.longpaths", "true", environment=environment)
        git(source, "add", "-A", environment=environment)
        git(
            source,
            "commit",
            "-q",
            "-m",
            "Profile R projected S2 fixtures",
            environment=environment,
        )
        commit = git(source, "rev-parse", "HEAD", environment=environment).decode("ascii").strip()
        for fixture in manifest["fixtures"]:
            fixture["commit"] = commit
            fixture["git_tree"] = git(
                source,
                "rev-parse",
                f"HEAD:{fixture['path']}",
                environment=environment,
            ).decode("ascii").strip()
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False),
        encoding="utf-8",
        newline="\n",
    )


def append_operator_readme(workspace: Path, contract: dict[str, object]) -> None:
    path = workspace / "tools/benchmark-runner/README.md"
    text = path.read_text(encoding="utf-8").rstrip() + "\n\n"
    text += "<!-- profile-r-operator-contract:start -->\n"
    text += "## Profile R operator contract\n\n"
    for command in contract["commands"]:
        text += f"- `{command['command_id']}`: `{command['implementation_symbol']}`; stop-before-next-dispatch=`{str(command['stop_before_next_dispatch']).lower()}`\n"
    text += "<!-- profile-r-operator-contract:end -->\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def _reference_scope_allows(relative: str, scopes: tuple[str, ...]) -> bool:
    return any(
        relative.startswith(scope[:-3].rstrip("/") + "/")
        if scope.endswith("/**")
        else relative == scope
        for scope in scopes
    )


def project_reference(repository: Path, pristine: Path, solution: Path, mapping: dict[str, Any], composition: dict[str, Any]) -> None:
    copy_tree(pristine, solution)
    surface = load_json(
        pristine / "profile-r/requirements/change-surface.json"
    )
    scopes = tuple(
        str(scope)
        for task in surface["tasks"]
        for scope in task["write_paths"]
    )
    for record in composition["records"]:
        category = record["category"]
        relative = str(record["path"])
        if category in {"historical_result_or_evidence", "golden_or_export_mirror"}:
            continue
        if relative.startswith("benchmarks/posthoc-checks/sdk-routing-v1/s2/golden/"):
            continue
        if not _reference_scope_allows(relative, scopes):
            continue
        payload = apply_mapping(git_blob(repository, REFERENCE_COMMIT, relative), mapping)
        if relative == "tools/benchmark-runner/tests/test_routing_s2.py":
            payload = adapt_public_s2_test(payload)
        elif relative == "tools/benchmark-runner/tests/test_routing_suite.py":
            payload = adapt_public_s1_test(payload)
        write_bytes(solution, relative, payload)
    for record in composition["records"]:
        if record["category"] != "golden_or_export_mirror":
            continue
        source = apply_mapping(git_blob(repository, REFERENCE_COMMIT, str(record["path"])), mapping)
        targets = record["canonical_source_paths"]
        if len(targets) != 1:
            raise RuntimeError("golden mirror must have exactly one Worker target")
        target = str(targets[0])
        if not _reference_scope_allows(target, scopes):
            raise RuntimeError("golden mirror target escaped Profile R Task scopes")
        write_bytes(solution, target, source)
    override_root = repository / REFERENCE_OVERRIDE_ROOT
    if not override_root.is_dir():
        raise RuntimeError("Profile R reference override root is unavailable")
    for source in sorted(
        (path for path in override_root.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(override_root).as_posix(),
    ):
        relative = source.relative_to(override_root).as_posix()
        if not _reference_scope_allows(relative, scopes):
            raise RuntimeError(
                f"Profile R reference override escaped Task scopes: {relative}"
            )
        payload = source.read_bytes()
        if b"\x00" in payload or b"\r" in payload:
            raise RuntimeError(
                f"Profile R reference override is not exact UTF-8 LF text: {relative}"
            )
        text = payload.decode("utf-8")
        stripped = text.rstrip("\n")
        payload = ((stripped + "\n") if stripped else "").encode("utf-8")
        write_bytes(solution, relative, payload)
    bind_s2_manifest_to_projected_fixtures(solution)
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


def mutate_source_boundary(root: Path) -> None:
    path = root / "profile-r/requirements/change-surface.json"
    value = load_json(path)
    value["tasks"][0]["write_paths"].append("outside/undeclared.txt")
    path.write_bytes(pretty_json(value))


def mutate_stage_discriminator(root: Path) -> None:
    replace_once(
        root / "tools/benchmark-runner/src/benchmark_runner/routing_suite.py",
        b'    stage_id: Literal["s2-intermediate"]',
        b'    stage_id: Literal["s1-baseline"]',
    )


def mutate_config_fixture(root: Path) -> None:
    path = root / "benchmarks/fixtures/routing-v1/intermediate/three-stage-config-migration/runtime/parser.py"
    replace_once(
        path,
        b"def parse_config(source: str | bytes | bytearray)",
        b"def parse(source: str | bytes | bytearray)",
    )


def mutate_incident_fixture(root: Path) -> None:
    path = root / "benchmarks/fixtures/routing-v1/intermediate/three-stage-incident-analysis/report/claims.json"
    replace_once(
        path,
        b'"evidence_ids":["EV-B1"]',
        b'"evidence_id":"EV-B1"',
    )


def mutate_manifest_binding(root: Path) -> None:
    path = root / "benchmarks/manifests/sdk-routing-s2-intermediate.yaml"
    payload = path.read_bytes()
    marker = b"git_tree: "
    index = payload.find(marker)
    if index < 0:
        raise RuntimeError("manifest tree mutation anchor is absent")
    position = index + len(marker)
    replacement = b"0" if payload[position:position + 1] != b"0" else b"1"
    path.write_bytes(payload[:position] + replacement + payload[position + 1:])


def mutate_plan_order(root: Path) -> None:
    path = root / "benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml"
    replace_once(path, b"cell_s2_a_1_c2", b"cell_s2_a_1_b1_mutated")


def mutate_reserve(root: Path) -> None:
    path = root / "tools/benchmark-runner/src/benchmark_runner/s2_policy.py"
    payload = path.read_bytes()
    anchor = b"return min(project_policy_turn_cap, task_count + remaining)"
    if payload.count(anchor) != 2:
        raise RuntimeError("S2 reserve mutation anchor count differs")
    path.write_bytes(
        payload.replace(
            anchor,
            b"return min(project_policy_turn_cap, task_count + remaining + 1)",
            1,
        )
    )


def mutate_lifecycle(root: Path) -> None:
    write_bytes(root, "tools/benchmark-runner/src/benchmark_runner/routing_s2_live.py", b'"""Forbidden duplicate S2 lifecycle."""\n')


def mutate_export(root: Path) -> None:
    path = root / "tools/benchmark-runner/src/benchmark_runner/routing_suite.py"
    before = b'''def verify_routing_s2_nonlive_export(export_root: Path) -> dict[str, Any]:\n    return _verify_routing_nonlive_export(\n        export_root,\n        expected_stage_id="s2-intermediate",\n    )'''
    after = before.replace(b'expected_stage_id="s2-intermediate"', b'expected_stage_id="s1-baseline"')
    replace_once(path, before, after)


def mutate_status_posthoc(root: Path) -> None:
    path = root / "tools/benchmark-runner/src/benchmark_runner/s2_posthoc.py"
    payload = path.read_bytes()
    if b'"CFG-P1"' not in payload:
        raise RuntimeError("status/posthoc mutation anchor is absent")
    path.write_bytes(payload.replace(b'"CFG-P1"', b'"CFG-BROKEN"', 1))


def mutate_s2_e2e(root: Path) -> None:
    path = root / "tools/benchmark-runner/tests/test_routing_s2.py"
    payload = path.read_bytes()
    if b'"type": "write_file"' not in payload:
        raise RuntimeError("S2 write-effect mutation anchor is absent")
    path.write_bytes(payload.replace(b'"type": "write_file"', b'"type": "missing_effect"'))


def mutate_s1_portability(root: Path) -> None:
    path = root / "tools/benchmark-runner/tests/test_routing_suite.py"
    payload = path.read_bytes()
    marker = b"_create_self_contained_s1_repository"
    if marker not in payload:
        raise RuntimeError("S1 self-contained helper mutation anchor is absent")
    path.write_bytes(
        payload.replace(marker, b"_historical_s1_repository")
        + b'\n# e915914c0494cd21969de5bc60f81ad74ec1b037\n'
    )


def mutate_checkout(root: Path) -> None:
    path = root / ".gitattributes"
    replace_once(path, b"* text=auto eol=lf", b"* text=auto")


def mutate_operator(root: Path) -> None:
    path = root / "profile-r/work/operator-contract.json"
    value = load_json(path)
    value["commands"][2]["stop_before_next_dispatch"] = False
    path.write_bytes(canonical_json(value))


_S2_WORKER_TEST_NAMES = (
    "test_s2_stage_discriminator_rejects_cross_branch_bytes",
    "test_s2_frozen_fixture_manifest_matches_live_model_controls",
    "test_s2_retry_reserve_is_independent_and_never_recycles_early_turns",
    "test_s2_b1_preflight_canonicalizes_legacy_project_pack",
    "test_s2_fake_four_cell_plan_judge_property_seal_export",
    "test_s2_posthoc_fixture_outputs_and_label_parity",
)
_SUITE_WORKER_TEST_NAMES = (
    "test_routing_manifests_and_generated_schemas_match_contracts",
    "test_complexity_profiles_are_recomputed_from_frozen_fixture_trees",
    "test_s1_plan_has_exact_eight_cell_order_and_calibration_only_policy",
    "test_model_free_runner_executes_exactly_one_next_cell_and_seals",
    "test_model_free_status_and_export_reject_an_incomplete_suite",
    "test_all_eight_model_free_cells_seal_export_and_detect_tampering",
)


def replace_worker_test_oracles(root: Path, mode: str) -> None:
    if mode not in {"noop", "skip", "assert_false"}:
        raise ValueError(f"unsupported Worker test-oracle mutation: {mode}")

    def module(names: tuple[str, ...]) -> bytes:
        lines = ['"""Adversarial Worker-owned test replacement."""', ""]
        if mode == "skip":
            lines.extend(("import pytest", ""))
        for name in names:
            if mode == "skip":
                lines.append('@pytest.mark.skip(reason="adversarial Worker skip")')
            lines.append(f"def {name}() -> None:")
            lines.append("    pass" if mode in {"noop", "skip"} else '    assert False, "adversarial Worker assertion"')
            lines.append("")
        return ("\n".join(lines).rstrip() + "\n").encode("utf-8")

    write_bytes(
        root,
        "tools/benchmark-runner/tests/test_routing_s2.py",
        module(_S2_WORKER_TEST_NAMES),
    )
    write_bytes(
        root,
        "tools/benchmark-runner/tests/test_routing_suite.py",
        module(_SUITE_WORKER_TEST_NAMES),
    )


MUTATIONS: tuple[tuple[str, str, Callable[[Path], None]], ...] = (
    ("r-p01-source-boundary", "R-P01-SOURCE-BOUNDARY", mutate_source_boundary),
    ("r-p02-discriminator", "R-P02-DISCRIMINATOR", mutate_stage_discriminator),
    ("r-p03-config-fixture", "R-P03-CONFIG-FIXTURE", mutate_config_fixture),
    ("r-p04-incident-fixture", "R-P04-INCIDENT-FIXTURE", mutate_incident_fixture),
    ("r-p05-manifest-binding", "R-P05-MANIFEST-BINDING", mutate_manifest_binding),
    ("r-p06-plan-binding", "R-P06-PLAN-BINDING", mutate_plan_order),
    ("r-p07-routing-policy", "R-P07-ROUTING-POLICY", mutate_reserve),
    ("r-p08-lifecycle-reuse", "R-P08-LIFECYCLE-REUSE", mutate_lifecycle),
    ("r-p09-status-posthoc", "R-P09-STATUS-POSTHOC", mutate_status_posthoc),
    ("r-p10-export-verify", "R-P10-EXPORT-VERIFY", mutate_export),
    ("r-p11-s2-e2e", "R-P11-S2-E2E", mutate_s2_e2e),
    ("r-p12-s1-portability", "R-P12-S1-PORTABILITY", mutate_s1_portability),
    ("r-p13-operator-semantics", "R-P13-OPERATOR-SEMANTICS", mutate_operator),
)


def load_checker(checker_path: Path):
    spec = importlib.util.spec_from_file_location("profile_r_check_properties", checker_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Profile R checker")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def public_check_timeout_seconds(solution: Path, check_id: str) -> int:
    """Read the public command-Check deadline from the projected Worker pack."""

    value = yaml.safe_load(
        (solution / ".orchestrator" / "checks.yaml").read_text(encoding="utf-8")
    )
    try:
        timeout_seconds = value["checks"][check_id]["timeout_seconds"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError(f"public Check timeout is unavailable: {check_id}") from exc
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int):
        raise RuntimeError(f"public Check timeout is invalid: {check_id}")
    if timeout_seconds <= 0:
        raise RuntimeError(f"public Check timeout must be positive: {check_id}")
    return timeout_seconds


def public_regression_evidence_projection(evidence: dict[str, Any]) -> dict[str, object]:
    """Bind portable regression facts without transient absolute TEMP paths."""

    def exact_int(name: str) -> int:
        value = evidence.get(name)
        if isinstance(value, bool) or not isinstance(value, int):
            raise RuntimeError(f"public R07 Evidence field is not an integer: {name}")
        return value

    pytest_counts = evidence.get("pytest")
    if not isinstance(pytest_counts, dict):
        raise RuntimeError("public R07 pytest Evidence is unavailable")
    growth_path_length = exact_int("growth_probe_path_length")
    probe_repository_length = exact_int("probe_repository_path_length")
    return {
        "schema_version": 1,
        "pytest": pytest_counts,
        "growth_margin": exact_int("growth_margin"),
        "growth_probe_minimum_path_length": R07_GROWTH_PATH_MINIMUM,
        "growth_probe_minimum_satisfied": (
            growth_path_length >= R07_GROWTH_PATH_MINIMUM
        ),
        "probe_repository_shorter_than_growth_path": (
            probe_repository_length < growth_path_length
        ),
    }


def validate_public_regression_reference(
    solution: Path,
    *,
    task_id: str,
    expected_tests: int,
) -> dict[str, object]:
    """Run one exact protected public regression entrypoint against projected W."""

    outer_timeout_seconds = public_check_timeout_seconds(
        solution, f"{task_id.lower()}_contract"
    )
    with tempfile.TemporaryDirectory(prefix=f"profile-r-public-{task_id.lower()}-") as raw:
        temp_root = Path(raw).resolve()
        environment = os.environ.copy()
        environment.update(
            {
                "TEMP": str(temp_root),
                "TMP": str(temp_root),
                "TMPDIR": str(temp_root),
                "PYTHONUTF8": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
            }
        )
        environment.pop("PYTHONPATH", None)
        completed = subprocess.run(
            [
                sys.executable,
                str(solution / "benchmark_checks" / "check_profile_r.py"),
                task_id,
            ],
            cwd=solution,
            env=environment,
            capture_output=True,
            timeout=outer_timeout_seconds,
            check=False,
        )
    stdout = completed.stdout.decode("utf-8", errors="replace")
    stdout_lines = stdout.splitlines()
    evidence_prefix = "CHECK_ENVIRONMENT_EVIDENCE:"
    evidence_lines = [
        line[len(evidence_prefix) :]
        for line in stdout.splitlines()
        if line.startswith(evidence_prefix)
    ]
    evidence: dict[str, Any] = {}
    if len(evidence_lines) == 1:
        try:
            candidate = json.loads(evidence_lines[0])
        except json.JSONDecodeError:
            candidate = None
        if isinstance(candidate, dict):
            evidence = candidate
    projection = public_regression_evidence_projection(evidence)
    pytest_counts = projection["pytest"]
    stdout_contract_ok = (
        len(stdout_lines) == 3
        and stdout_lines[0].startswith("CHECK_DIAGNOSTIC_RESULT:")
        and stdout_lines[1].startswith(evidence_prefix)
        and stdout_lines[2] == f"{task_id}_PUBLIC_CONTRACT_OK"
    )
    passed = (
        completed.returncode == 0
        and completed.stderr == b""
        and stdout_contract_ok
        and pytest_counts
        == {"tests": expected_tests, "failures": 0, "errors": 0, "skipped": 0, "warnings": 0}
        and int(projection["growth_margin"]) >= 32
        and projection["growth_probe_minimum_satisfied"] is True
        and projection["probe_repository_shorter_than_growth_path"] is True
    )
    return {
        "schema_version": 1,
        "entrypoint": f"benchmark_checks/check_profile_r.py {task_id}",
        "outer_timeout_seconds": outer_timeout_seconds,
        "return_code": completed.returncode,
        "stdout_contract": "one diagnostic line, one environment Evidence line, and one Task OK line",
        "evidence_projection": projection,
        "evidence_projection_sha256": sha256(canonical_json(projection)),
        "stderr_sha256": sha256(completed.stderr),
        "contract_ok_marker": stdout_contract_ok,
        "passed": passed,
    }


def validate_public_mutation(
    solution: Path,
    *,
    task_id: str,
) -> dict[str, object]:
    """Require the owning public contract to reject one known-bad solution."""

    timeout_seconds = public_check_timeout_seconds(
        solution, f"{task_id.lower()}_contract"
    )
    with tempfile.TemporaryDirectory(
        prefix=f"profile-r-public-negative-{task_id.lower()}-"
    ) as raw:
        temp_root = Path(raw).resolve()
        environment = os.environ.copy()
        environment.update(
            {
                "TEMP": str(temp_root),
                "TMP": str(temp_root),
                "TMPDIR": str(temp_root),
                "PYTHONUTF8": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
            }
        )
        environment.pop("PYTHONPATH", None)
        completed = subprocess.run(
            [
                sys.executable,
                str(solution / "benchmark_checks" / "check_profile_r.py"),
                task_id,
            ],
            cwd=solution,
            env=environment,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    stdout_lines = completed.stdout.decode(
        "utf-8", errors="replace"
    ).splitlines()
    expected = [
        f"{task_id}_PUBLIC_CONTRACT_FAILED",
        "CHECK_FAILURE_CLASS:PRODUCT_ASSERTION",
    ]
    rejected = completed.returncode == 1 and stdout_lines[:2] == expected
    return {
        "task_id": task_id,
        "return_code": completed.returncode,
        "classification": (
            "PRODUCT_ASSERTION"
            if "CHECK_FAILURE_CLASS:PRODUCT_ASSERTION" in stdout_lines
            else None
        ),
        "contract_rejected": rejected,
        "stdout_sha256": sha256(completed.stdout),
        "stderr_sha256": sha256(completed.stderr),
    }


def file_manifest(root: Path, *, exclude: set[str]) -> list[dict[str, object]]:
    records = []
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.relative_to(root).as_posix().encode("utf-8")):
        relative = path.relative_to(root).as_posix()
        if relative in exclude:
            continue
        payload = path.read_bytes()
        records.append({"path": relative, "size": len(payload), "sha256": sha256(payload)})
    return records


def assert_no_transient_cache_files(root: Path) -> None:
    for path in root.rglob("*"):
        relative_parts = path.relative_to(root).parts
        if "__pycache__" in relative_parts or ".pytest_cache" in relative_parts:
            raise RuntimeError("Judge source contains a transient cache path")


def validate_exact_worker_snapshot(
    workspace: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    """Reject transient or unsealed bytes before deriving protected Evidence."""

    manifest = load_json(manifest_path)
    records = manifest.get("files")
    if not isinstance(records, list) or not records:
        raise RuntimeError("Worker snapshot manifest file records are unavailable")
    expected_paths: list[str] = []
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise RuntimeError("Worker snapshot manifest contains an invalid file record")
        expected_paths.append(str(record["path"]))
    if len(expected_paths) != len(set(expected_paths)):
        raise RuntimeError("Worker snapshot manifest contains duplicate paths")

    actual_files: list[Path] = []
    for path in workspace.rglob("*"):
        is_junction = getattr(path, "is_junction", None)
        if path.is_symlink() or bool(is_junction is not None and is_junction()):
            raise RuntimeError("Worker snapshot contains a link or junction")
        if path.is_file():
            actual_files.append(path)
    actual_files.sort(key=lambda item: item.relative_to(workspace).as_posix().encode("utf-8"))
    actual_paths = [path.relative_to(workspace).as_posix() for path in actual_files]
    if actual_paths != expected_paths:
        raise RuntimeError("Worker snapshot exact file set differs from its manifest")

    for path, record in zip(actual_files, records, strict=True):
        payload = path.read_bytes()
        if (
            isinstance(record.get("worker_size"), bool)
            or not isinstance(record.get("worker_size"), int)
            or record["worker_size"] != len(payload)
            or record.get("worker_sha256") != sha256(payload)
        ):
            raise RuntimeError(
                f"Worker snapshot bytes differ from manifest: {record['path']}"
            )
    return manifest


def build(repository: Path) -> dict[str, object]:
    profile_root = repository / PROFILE_ROOT
    judge_root = repository / JUDGE_ROOT
    pristine = profile_root / "workspace"
    checker_path = judge_root / CHECKER_RELATIVE
    if not pristine.is_dir() or not checker_path.is_file():
        raise RuntimeError("Profile R Worker snapshot or checker is missing")
    assert_no_transient_cache_files(judge_root)
    worker_manifest = validate_exact_worker_snapshot(
        pristine,
        profile_root / "worker-snapshot-manifest.json",
    )
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
        {"property_id": "R-P01-SOURCE-BOUNDARY", "severity": "critical", "prerequisite_ids": []},
        {"property_id": "R-P02-DISCRIMINATOR", "severity": "critical", "prerequisite_ids": []},
        {"property_id": "R-P03-CONFIG-FIXTURE", "severity": "critical", "prerequisite_ids": []},
        {"property_id": "R-P04-INCIDENT-FIXTURE", "severity": "critical", "prerequisite_ids": []},
        {"property_id": "R-P05-MANIFEST-BINDING", "severity": "critical", "prerequisite_ids": []},
        {"property_id": "R-P06-PLAN-BINDING", "severity": "critical", "prerequisite_ids": []},
        {"property_id": "R-P07-ROUTING-POLICY", "severity": "major", "prerequisite_ids": []},
        {"property_id": "R-P08-LIFECYCLE-REUSE", "severity": "major", "prerequisite_ids": []},
        {"property_id": "R-P09-STATUS-POSTHOC", "severity": "major", "prerequisite_ids": []},
        {"property_id": "R-P10-EXPORT-VERIFY", "severity": "critical", "prerequisite_ids": []},
        {"property_id": "R-P11-S2-E2E", "severity": "critical", "prerequisite_ids": []},
        {"property_id": "R-P12-S1-PORTABILITY", "severity": "critical", "prerequisite_ids": []},
        {"property_id": "R-P13-OPERATOR-SEMANTICS", "severity": "major", "prerequisite_ids": []},
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
                "worker_readable_paths": sorted({entry["path"] for entry in worker_manifest["files"] if isinstance(entry, dict) and isinstance(entry.get("path"), str) and not str(entry["path"]).startswith(("benchmark_checks/", ".orchestrator/"))})[:1],
                "task_ids": [f"R{index:02d}"],
                "required_fact_description": "The public migration contract and declared source surface needed for this property.",
                "goal_alignment": "Directly checks one frozen Profile R migration invariant.",
                "source_evidence_sha256": sha256(canonical_json(item)),
            }
            for index, item in enumerate(properties, 1)
        ],
    }
    task_paths = {
        "R-P01-SOURCE-BOUNDARY": ["profile-r/requirements/migration-contract.md", "profile-r/requirements/change-surface.json"],
        "R-P02-DISCRIMINATOR": ["profile-r/requirements/migration-contract.md", "benchmarks/suites/sdk-routing-v1/stage.schema.json"],
        "R-P03-CONFIG-FIXTURE": ["benchmarks/fixtures/routing-v1/intermediate/three-stage-config-migration/benchmark-run.yaml"],
        "R-P04-INCIDENT-FIXTURE": ["benchmarks/fixtures/routing-v1/intermediate/three-stage-incident-analysis/benchmark-run.yaml"],
        "R-P05-MANIFEST-BINDING": ["benchmarks/manifests/sdk-routing-s2-intermediate.yaml"],
        "R-P06-PLAN-BINDING": ["benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml", "tools/benchmark-runner/src/benchmark_runner/routing_suite.py"],
        "R-P07-ROUTING-POLICY": ["tools/benchmark-runner/src/benchmark_runner/s2_policy.py"],
        "R-P08-LIFECYCLE-REUSE": ["tools/benchmark-runner/src/benchmark_runner/routing_live.py", "tools/benchmark-runner/src/benchmark_runner/routing_suite.py"],
        "R-P09-STATUS-POSTHOC": ["tools/benchmark-runner/src/benchmark_runner/s2_posthoc.py"],
        "R-P10-EXPORT-VERIFY": ["tools/benchmark-runner/src/benchmark_runner/routing_live.py", "tools/benchmark-runner/src/benchmark_runner/routing_suite.py"],
        "R-P11-S2-E2E": ["tools/benchmark-runner/tests/test_routing_s2.py"],
        "R-P12-S1-PORTABILITY": ["tools/benchmark-runner/tests/test_routing_suite.py"],
        "R-P13-OPERATOR-SEMANTICS": ["profile-r/requirements/operator-contract-schema.json", "tools/benchmark-runner/README.md"],
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
        public_r11_result = validate_public_regression_reference(
            solution,
            task_id="R11",
            expected_tests=7,
        )
        public_r12_result = validate_public_regression_reference(
            solution,
            task_id="R12",
            expected_tests=5,
        )
        write_bytes(
            judge_root,
            "evidence/public-r11-reference.json",
            pretty_json(public_r11_result),
        )
        write_bytes(
            judge_root,
            "evidence/public-r12-reference.json",
            pretty_json(public_r12_result),
        )
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
        for mutation_index, (mutation_id, target_property, mutate) in enumerate(
            MUTATIONS,
            1,
        ):
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
            public_result = validate_public_mutation(
                mutated,
                task_id=f"R{mutation_index:02d}",
            )
            write_bytes(judge_root, f"negative-mutations/{mutation_id}.patch", mutation_patch)
            write_bytes(judge_root, f"evidence/mutations/{mutation_id}.json", pretty_json(result))
            statuses = {item["property_id"]: item["status"] for item in result["properties"]}
            mutation_summaries.append(
                {
                    "mutation_id": mutation_id,
                    "target_property_id": target_property,
                    "statuses": statuses,
                    "public_contract": public_result,
                    "cofailed_property_ids": sorted(
                        property_id
                        for property_id, status in statuses.items()
                        if property_id != target_property and status == "fail"
                    ),
                }
            )

        write_bytes(
            judge_root,
            "evidence/public-negative-matrix.json",
            pretty_json(
                {
                    "schema_version": 1,
                    "profile": "R",
                    "cases": mutation_summaries,
                }
            ),
        )

        adversarial_summaries = []
        for mode in ("noop", "skip", "assert_false"):
            adversarial = temporary / f"adversarial-worker-tests-{mode}"
            copy_tree(solution, adversarial)
            replace_worker_test_oracles(adversarial, mode)
            result = checker.evaluate_workspace(
                adversarial,
                experiment_id="phase-d-profile-r",
                cell_id=f"worker-tests-{mode}",
            )
            statuses = {
                item["property_id"]: item["status"]
                for item in result["properties"]
            }
            matched = (
                result["aggregate_status"] == "fail"
                and statuses.get("R-P11-S2-E2E") == "fail"
                and statuses.get("R-P12-S1-PORTABILITY") == "fail"
            )
            adversarial_summaries.append(
                {
                    "case_id": f"worker-tests-{mode}",
                    "worker_test_mode": mode,
                    "implementation_mutation": None,
                    "target_property_id": None,
                    "aggregate_status": result["aggregate_status"],
                    "statuses": statuses,
                    "matched_expectation": matched,
                }
            )

        co_mutations = (
            ("r-p02-discriminator", "R-P02-DISCRIMINATOR", mutate_stage_discriminator),
            ("r-p07-routing-policy", "R-P07-ROUTING-POLICY", mutate_reserve),
            ("r-p10-export-verify", "R-P10-EXPORT-VERIFY", mutate_export),
            ("r-p12-s1-portability", "R-P12-S1-PORTABILITY", mutate_s1_portability),
        )
        for mutation_id, target_property, mutate in co_mutations:
            adversarial = temporary / f"adversarial-{mutation_id}-plus-noop"
            copy_tree(solution, adversarial)
            mutate(adversarial)
            replace_worker_test_oracles(adversarial, "noop")
            result = checker.evaluate_workspace(
                adversarial,
                experiment_id="phase-d-profile-r",
                cell_id=f"{mutation_id}-plus-noop",
            )
            statuses = {
                item["property_id"]: item["status"]
                for item in result["properties"]
            }
            matched = (
                result["aggregate_status"] == "fail"
                and statuses.get(target_property) == "fail"
            )
            adversarial_summaries.append(
                {
                    "case_id": f"{mutation_id}-plus-noop",
                    "worker_test_mode": "noop",
                    "implementation_mutation": mutation_id,
                    "target_property_id": target_property,
                    "aggregate_status": result["aggregate_status"],
                    "statuses": statuses,
                    "matched_expectation": matched,
                }
            )
        write_bytes(
            judge_root,
            "evidence/adversarial-worker-test-oracle.json",
            pretty_json(
                {
                    "schema_version": 1,
                    "worker_test_paths": [
                        "tools/benchmark-runner/tests/test_routing_s2.py",
                        "tools/benchmark-runner/tests/test_routing_suite.py",
                    ],
                    "cases": adversarial_summaries,
                }
            ),
        )

        reference_ok = reference_result["aggregate_status"] == "pass"
        pristine_failed = pristine_result["aggregate_status"] == "fail"
        mutation_ok = all(
            item["statuses"].get(item["target_property_id"]) == "fail"
            and item["public_contract"]["contract_rejected"] is True
            and all(
                status in {"pass", "fail"}
                for status in item["statuses"].values()
            )
            for item in mutation_summaries
        )
        adversarial_ok = all(
            item["matched_expectation"] for item in adversarial_summaries
        )
        public_regressions_ok = (
            public_r11_result["passed"] is True
            and public_r12_result["passed"] is True
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
            f"- Adversarial Worker test-oracle contracts: {'pass' if adversarial_ok else 'fail'}\n"
            f"- Exact public R11/R12 projected-reference runs: {'pass' if public_regressions_ok else 'fail'}\n"
            f"- Forbidden Worker literal hits: {len(leakage_hits)}\n"
            "- The public S2 regression consumes current fixture outputs and never reads the hidden golden tree.\n"
            "- This source bundle does not claim the protected Judge runtime filesystem/no-network boundary.\n"
        )
        write_bytes(judge_root, "evidence/anonymization-review.md", review.encode("utf-8"))
        eligible = (
            reference_ok
            and pristine_failed
            and mutation_ok
            and adversarial_ok
            and public_regressions_ok
            and not leakage_hits
        )
        eligibility = load_json(judge_root / "challenge-eligibility.json")
        eligibility.update({
            "status": "PROFILE_R_SOURCE_BUNDLE_VERIFIED" if eligible else "CHALLENGE_NOT_READY",
            "challenge_ready": False,
            "source_bundle_verified": eligible,
            "judge_runtime_boundary_verified": False,
            "reference_aggregate_status": reference_result["aggregate_status"],
            "pristine_aggregate_status": pristine_result["aggregate_status"],
            "negative_mutation_count": len(mutation_summaries),
            "adversarial_worker_test_oracle_count": len(adversarial_summaries),
            "public_r11_r12_reference_verified": public_regressions_ok,
        })
        write_bytes(judge_root, "challenge-eligibility.json", pretty_json(eligibility))

    assert_no_transient_cache_files(judge_root)
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
