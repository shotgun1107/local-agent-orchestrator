from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


REPOSITORY = Path(__file__).resolve().parents[3]
INTAKE_PATH = (
    REPOSITORY
    / "benchmarks"
    / "fixtures"
    / "routing-realistic-high-difficulty-v1"
    / "realistic-compat-migration-001"
    / "source-intake.json"
)
COMPOSITION_PATH = INTAKE_PATH.with_name("r-change-composition.json")
ALLOWLIST_PATH = INTAKE_PATH.with_name("worker-source-allowlist.json")
WORKER_ROOT = INTAKE_PATH.with_name("workspace")
WORKER_MANIFEST_PATH = INTAKE_PATH.with_name("worker-snapshot-manifest.json")
PUBLIC_OVERLAY_ROOT = INTAKE_PATH.with_name("worker-public-overlay")
JUDGE_SOURCE_ROOT = (
    REPOSITORY
    / "benchmarks"
    / "judge-source"
    / "sdk-routing-realistic-high-difficulty-v1"
    / "realistic-compat-migration-001"
)
ANONYMIZATION_MAP_PATH = (
    REPOSITORY
    / "benchmarks"
    / "judge-source"
    / "sdk-routing-realistic-high-difficulty-v1"
    / "realistic-compat-migration-001"
    / "anonymization-map.json"
)
SNAPSHOT_BUILDER_PATH = (
    REPOSITORY
    / "tools"
    / "benchmark-runner"
    / "scripts"
    / "build_profile_r_worker_snapshot.py"
)
JUDGE_BUNDLE_BUILDER_PATH = (
    REPOSITORY
    / "tools"
    / "benchmark-runner"
    / "scripts"
    / "build_profile_r_judge_bundle.py"
)
ALLOWED_COMPOSITION_CATEGORIES = {
    "authored_source",
    "authored_test",
    "authored_spec_or_operator_contract",
    "generated_schema_or_manifest",
    "golden_or_export_mirror",
    "historical_result_or_evidence",
    "out_of_scope",
}


def _git(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=REPOSITORY,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _canonical_lines_sha256(output: str) -> str:
    lines = output.splitlines()
    payload = (("\n".join(lines) + "\n") if lines else "").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def test_profile_r_source_intake_matches_git_objects() -> None:
    intake = json.loads(INTAKE_PATH.read_text(encoding="utf-8"))
    base = intake["base_commit"]
    reference = intake["reference_commit"]

    assert _git("rev-parse", f"{base}^{{tree}}").stdout.strip() == intake["base_tree"]
    assert (
        _git("rev-parse", f"{reference}^{{tree}}").stdout.strip()
        == intake["reference_tree"]
    )
    assert _git("merge-base", "--is-ancestor", base, reference, check=False).returncode == 0

    name_status = _git("diff", "--name-status", base, reference).stdout
    numstat = _git("diff", "--numstat", base, reference).stdout
    assert len(name_status.splitlines()) == intake["changed_path_count"]
    assert _canonical_lines_sha256(name_status) == intake["name_status_sha256"]
    assert _canonical_lines_sha256(numstat) == intake["numstat_sha256"]

    insertions = 0
    deletions = 0
    for line in numstat.splitlines():
        added, removed, _path = line.split("\t", 2)
        insertions += 0 if added == "-" else int(added)
        deletions += 0 if removed == "-" else int(removed)
    assert insertions == intake["insertions"]
    assert deletions == intake["deletions"]


def test_profile_r_source_intake_does_not_claim_challenge_ready() -> None:
    intake = json.loads(INTAKE_PATH.read_text(encoding="utf-8"))

    assert intake["schema_version"] == 1
    assert intake["snapshot_id"] == "realistic-compat-migration-001"
    assert intake["profile"] == "R"
    assert intake["source_authority"] == "git_object_database"
    assert intake["status"] == "SOURCE_VERIFIED_COMPOSITION_CANDIDATE"


def test_profile_r_change_composition_covers_every_changed_path_once() -> None:
    intake = json.loads(INTAKE_PATH.read_text(encoding="utf-8"))
    composition = json.loads(COMPOSITION_PATH.read_text(encoding="utf-8"))
    records = composition["records"]
    record_paths = [record["path"] for record in records]
    diff_paths = [
        line.split("\t", 1)[1]
        for line in _git(
            "diff",
            "--name-status",
            intake["base_commit"],
            intake["reference_commit"],
        ).stdout.splitlines()
    ]

    assert record_paths == sorted(record_paths, key=lambda value: value.encode("utf-8"))
    assert record_paths == sorted(diff_paths, key=lambda value: value.encode("utf-8"))
    assert len(record_paths) == len(set(record_paths)) == intake["changed_path_count"]
    assert composition["raw_changed_path_count"] == intake["changed_path_count"]
    assert {record["category"] for record in records} <= ALLOWED_COMPOSITION_CATEGORIES


def test_profile_r_change_composition_deduplicates_derived_content() -> None:
    composition = json.loads(COMPOSITION_PATH.read_text(encoding="utf-8"))
    records = composition["records"]
    by_path = {record["path"]: record for record in records}
    counted_groups = [
        record["semantic_group_id"]
        for record in records
        if record["counted_for_structure"]
    ]

    assert len(counted_groups) == len(set(counted_groups))
    assert len(counted_groups) == composition["counted_semantic_group_count"] == 64
    for record in records:
        assert set(record) == {
            "path",
            "git_status",
            "category",
            "semantic_group_id",
            "canonical_source_paths",
            "producer_or_derivation",
            "counted_for_structure",
        }
        if record["category"] in {
            "generated_schema_or_manifest",
            "golden_or_export_mirror",
            "historical_result_or_evidence",
        }:
            assert record["counted_for_structure"] is False
        if record["category"] == "golden_or_export_mirror":
            canonical = record["canonical_source_paths"]
            assert len(canonical) == 1
            assert canonical[0] in by_path
            assert record["semantic_group_id"] == by_path[canonical[0]][
                "semantic_group_id"
            ]

    category_counts: dict[str, int] = {}
    for record in records:
        category = record["category"]
        category_counts[category] = category_counts.get(category, 0) + 1
    assert composition["category_counts"] == dict(sorted(category_counts.items()))
    assert composition["status"] == "COMPOSITION_CANDIDATE"


def _load_snapshot_builder():
    spec = importlib.util.spec_from_file_location(
        "profile_r_snapshot_builder", SNAPSHOT_BUILDER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_judge_bundle_builder():
    spec = importlib.util.spec_from_file_location(
        "profile_r_judge_bundle_builder", JUDGE_BUNDLE_BUILDER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def _load_profile_r_public_checker():
    path = WORKER_ROOT / "benchmark_checks" / "check_profile_r.py"
    spec = importlib.util.spec_from_file_location("profile_r_public_checker", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def _workspace_files(root: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in root.rglob("*")
            if path.is_file() and ".git" not in path.relative_to(root).parts
        ),
        key=lambda path: path.relative_to(root).as_posix().encode("utf-8"),
    )


def test_profile_r_worker_snapshot_matches_manifest_and_excludes_sensitive_literals() -> None:
    manifest = json.loads(WORKER_MANIFEST_PATH.read_text(encoding="utf-8"))
    mapping = json.loads(ANONYMIZATION_MAP_PATH.read_text(encoding="utf-8"))
    allowlist = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    files = _workspace_files(WORKER_ROOT)
    relative_paths = [path.relative_to(WORKER_ROOT).as_posix() for path in files]

    assert manifest["status"] == "ANONYMIZED_WORKER_TASK_PACK_CANDIDATE"
    assert manifest["challenge_ready"] is False
    overlay_files = _workspace_files(PUBLIC_OVERLAY_ROOT)
    override_paths = allowlist["overlay_override_paths"]
    assert manifest["base_file_count"] == allowlist["expected_file_count"] == 115
    assert manifest["public_overlay_file_count"] == len(overlay_files)
    assert manifest["public_overlay_override_paths"] == override_paths
    assert manifest["public_overlay_text_normalization"] == "utf8_lf"
    assert manifest["file_count"] == len(files) == (
        allowlist["expected_file_count"] + len(overlay_files) - len(override_paths)
    )
    assert relative_paths == [record["path"] for record in manifest["files"]]
    for path, record in zip(files, manifest["files"], strict=True):
        payload = path.read_bytes()
        assert len(payload) == record["worker_size"]
        assert hashlib.sha256(payload).hexdigest() == record["worker_sha256"]
        assert record["provenance"] in {"base_snapshot", "public_requirement"}
        if record["provenance"] == "public_requirement":
            assert record["source_blob_oid"] is None
            assert record["source_path"].startswith(
                "benchmarks/fixtures/routing-realistic-high-difficulty-v1/"
                "realistic-compat-migration-001/worker-public-overlay/"
            )
        else:
            assert record["source_blob_oid"]
            assert record["source_path"] is None
        for literal in mapping["forbidden_worker_literals"]:
            assert literal.encode("utf-8") not in payload
        for pattern in mapping["forbidden_worker_regexes"]:
            assert re.search(pattern.encode("ascii"), payload) is None
    runner_record = next(
        record
        for record in manifest["files"]
        if record["path"] == "tools/benchmark-runner/src/benchmark_runner/runner.py"
    )
    assert runner_record["provenance"] == "public_requirement"
    assert b"\r" not in (
        WORKER_ROOT / "tools/benchmark-runner/src/benchmark_runner/runner.py"
    ).read_bytes()


def test_profile_r_judge_builder_rejects_extra_worker_cache_before_derivation(
    tmp_path: Path,
) -> None:
    builder = _load_judge_bundle_builder()

    canonical = builder.validate_exact_worker_snapshot(
        WORKER_ROOT,
        WORKER_MANIFEST_PATH,
    )
    assert canonical["file_count"] == len(canonical["files"]) == 130

    profile_root = tmp_path / builder.PROFILE_ROOT
    workspace = profile_root / "workspace"
    workspace.mkdir(parents=True)
    kept_payload = b"sealed worker byte\n"
    (workspace / "kept.txt").write_bytes(kept_payload)
    (profile_root / "worker-snapshot-manifest.json").write_text(
        json.dumps(
            {
                "files": [
                    {
                        "path": "kept.txt",
                        "worker_size": len(kept_payload),
                        "worker_sha256": hashlib.sha256(kept_payload).hexdigest(),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    judge_root = tmp_path / builder.JUDGE_ROOT
    checker = judge_root / builder.CHECKER_RELATIVE
    checker.parent.mkdir(parents=True)
    checker.write_text("# prerequisite marker\n", encoding="utf-8")
    prior_evidence = judge_root / "evidence" / "must-not-be-deleted.json"
    prior_evidence.parent.mkdir(parents=True)
    prior_evidence.write_bytes(b"prior evidence\n")

    cache = workspace / "__pycache__" / "x.pyc"
    cache.parent.mkdir()
    cache.write_bytes(b"unsealed cache byte")

    with pytest.raises(
        RuntimeError,
        match="Worker snapshot exact file set differs from its manifest",
    ):
        builder.build(tmp_path)
    assert prior_evidence.read_bytes() == b"prior evidence\n"


def test_profile_r_judge_builder_uses_declared_regression_outer_timeouts() -> None:
    builder = _load_judge_bundle_builder()
    checks = yaml.safe_load(
        (WORKER_ROOT / ".orchestrator/checks.yaml").read_text(encoding="utf-8")
    )["checks"]

    for check_id in ("r11_contract", "r12_contract"):
        assert checks[check_id]["timeout_seconds"] == 1020
        assert (
            builder.public_check_timeout_seconds(WORKER_ROOT, check_id)
            == checks[check_id]["timeout_seconds"]
        )


def test_profile_r_judge_builder_loads_checker_without_bytecode_cache(
    tmp_path: Path,
) -> None:
    builder = _load_judge_bundle_builder()
    checker = tmp_path / "checker.py"
    checker.write_text("VALUE = 1\n", encoding="utf-8", newline="\n")

    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = False
    try:
        loaded = builder.load_checker(checker)
    finally:
        sys.dont_write_bytecode = previous

    assert loaded.VALUE == 1
    assert not (tmp_path / "__pycache__").exists()


def test_profile_r_public_regression_projection_ignores_transient_absolute_paths() -> None:
    builder = _load_judge_bundle_builder()
    base = {
        "pytest": {
            "tests": 12,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "warnings": 0,
        },
        "growth_margin": 32,
        "growth_probe_path_length": 294,
        "probe_repository_path_length": 58,
        "temp_root": "C:/first/random-root",
        "deepest_path": "C:/first/random-root/random/path",
    }
    alternate = {
        **base,
        "temp_root": "D:/different/random-root",
        "deepest_path": "D:/different/random-root/random/path",
    }

    first = builder.public_regression_evidence_projection(base)
    second = builder.public_regression_evidence_projection(alternate)
    assert first == second
    assert builder.sha256(builder.canonical_json(first)) == builder.sha256(
        builder.canonical_json(second)
    )


def test_profile_r_judge_source_rejects_transient_cache_paths(tmp_path: Path) -> None:
    builder = _load_judge_bundle_builder()
    cache = tmp_path / "checker" / "__pycache__" / "checker.pyc"
    cache.parent.mkdir(parents=True)
    cache.write_bytes(b"transient")

    with pytest.raises(RuntimeError, match="transient cache path"):
        builder.assert_no_transient_cache_files(tmp_path)


def test_profile_r_worker_snapshot_rebuild_is_byte_identical(tmp_path: Path) -> None:
    builder = _load_snapshot_builder()
    output_a = tmp_path / "a" / "workspace"
    manifest_a = tmp_path / "a" / "manifest.json"
    output_b = tmp_path / "b" / "workspace"
    manifest_b = tmp_path / "b" / "manifest.json"

    built_a = builder.build_snapshot(REPOSITORY, output_a, manifest_a)
    built_b = builder.build_snapshot(REPOSITORY, output_b, manifest_b)

    assert manifest_a.read_bytes() == manifest_b.read_bytes() == WORKER_MANIFEST_PATH.read_bytes()
    assert built_a["worker_tree_aggregate_sha256"] == built_b["worker_tree_aggregate_sha256"]
    assert [path.relative_to(output_a).as_posix() for path in _workspace_files(output_a)] == [
        path.relative_to(output_b).as_posix() for path in _workspace_files(output_b)
    ]
    for path_a, path_b in zip(
        _workspace_files(output_a), _workspace_files(output_b), strict=True
    ):
        assert path_a.read_bytes() == path_b.read_bytes()


def _dependency_depth(tasks: list[dict[str, object]], task_id: str) -> int:
    by_id = {str(task["key"]): task for task in tasks}
    dependencies = [str(value) for value in by_id[task_id]["depends_on"]]
    if not dependencies:
        return 1
    return 1 + max(_dependency_depth(tasks, dependency) for dependency in dependencies)


def test_profile_r_public_task_pack_has_exact_graph_and_protected_checks() -> None:
    run = yaml.safe_load((WORKER_ROOT / "benchmark-run.yaml").read_text(encoding="utf-8"))
    tasks = run["tasks"]
    task_ids = [task["key"] for task in tasks]
    assert task_ids == [f"R{number:02d}" for number in range(1, 14)]
    assert {task["key"]: task["depends_on"] for task in tasks} == {
        task_id: ([] if index == 0 else [task_ids[index - 1]])
        for index, task_id in enumerate(task_ids)
    }
    assert max(_dependency_depth(tasks, task_id) for task_id in task_ids) == 13
    protected = {
        "benchmark-run.yaml",
        "README.md",
        "benchmark_checks/**",
        ".orchestrator/**",
        "profile-r/requirements/**",
    }
    for task in tasks:
        assert task["workspace_mode"] == "shared_serial_write"
        assert task["approval"] == "none"
        assert task["own_check"] == f"{task['key'].lower()}_contract"
        assert "check_names" not in task
        assert protected.isdisjoint(set(task["write_scope"]))

    r11 = next(task for task in tasks if task["key"] == "R11")
    r12 = next(task for task in tasks if task["key"] == "R12")
    assert "four-Cell E2E regression" in r11["goal"]
    assert "zero model turns" in " ".join(
        item["text"] for item in r11["completion_criteria"]
    )
    assert "deterministic isolated Git repository" in r12["goal"]
    assert "never read historical Git objects" in r12["goal"]

    checks = yaml.safe_load(
        (WORKER_ROOT / ".orchestrator/checks.yaml").read_text(encoding="utf-8")
    )["checks"]
    assert list(checks) == [
        *(f"r{number:02d}_contract" for number in range(1, 14)),
        "diff_check",
    ]
    for number in range(1, 14):
        check = checks[f"r{number:02d}_contract"]
        assert check["argv"] == [
            "python",
            "benchmark_checks/check_profile_r.py",
            f"R{number:02d}",
        ]
        assert check["timeout_seconds"] == {
            3: 180,
            4: 180,
            6: 240,
            7: 180,
            8: 360,
            9: 360,
            10: 600,
            11: 1020,
            12: 1020,
            13: 240,
        }.get(number, 120)
    policies = yaml.safe_load(
        (WORKER_ROOT / ".orchestrator/policies.yaml").read_text(encoding="utf-8")
    )["policies"]
    assert policies["b1_safe"]["task_timeout_seconds"] == 900
    assert policies["b1_safe"]["check_timeout_seconds"] == 1020


def test_profile_r_regression_outer_timeouts_have_fixed_overhead_margin() -> None:
    checker = _load_profile_r_public_checker()
    checks = yaml.safe_load(
        (WORKER_ROOT / ".orchestrator/checks.yaml").read_text(encoding="utf-8")
    )["checks"]
    policy = yaml.safe_load(
        (WORKER_ROOT / ".orchestrator/policies.yaml").read_text(encoding="utf-8")
    )["policies"]["b1_safe"]

    internal_child_budget = (
        checker.R07_COLLECTION_TIMEOUT_SECONDS
        + checker.R07_EXECUTION_TIMEOUT_SECONDS
        + checker.R07_GIT_COMMAND_COUNT
        * checker.R07_GIT_COMMAND_TIMEOUT_SECONDS
    )
    assert internal_child_budget == checker.R07_INTERNAL_CHILD_BUDGET_SECONDS == 900
    for check_id in ("r11_contract", "r12_contract"):
        assert checks[check_id]["timeout_seconds"] == internal_child_budget + 120
        assert policy["check_timeout_seconds"] == checks[check_id]["timeout_seconds"]
    # task_timeout_seconds is the Worker model-turn deadline, not an outer
    # command-Check deadline.  Only check_timeout_seconds bounds r07_contract.
    assert policy["task_timeout_seconds"] == 900
    assert policy["task_timeout_seconds"] != checks["r11_contract"]["timeout_seconds"]


def test_profile_r_public_check_is_model_free_and_compiles() -> None:
    check_path = WORKER_ROOT / "benchmark_checks/check_profile_r.py"
    source = check_path.read_text(encoding="utf-8")
    forbidden = (
        "openai_codex",
        "CodexClient",
        "turn/start",
        "OPENAI_API_KEY",
        "CODEX_API_KEY",
    )
    assert all(value not in source for value in forbidden)
    compile(source, str(check_path), "exec")


def test_profile_r_r07_exports_bounded_actionable_public_pytest_feedback(
    capsys,
) -> None:
    checker = _load_profile_r_public_checker()
    pytest_result = subprocess.CompletedProcess(
        [sys.executable, "-m", "pytest"],
        1,
        (
            "test_s2_fake_four_cell_plan_judge_property_seal_export\n"
            "FrozenManifest\n"
            "extra_forbidden\n"
        ),
        "",
    )
    feedback = checker._public_pytest_failure_feedback(pytest_result)
    feedback_text = "\n".join(feedback)
    assert "FrozenManifest/FrozenFixtureSpec" in feedback_text
    assert "stage_id, purpose, initial_cell_order" in feedback_text
    assert "extra_forbidden" in feedback_text
    assert len(feedback_text.encode("utf-8")) <= checker.WORKER_FEEDBACK_MAX_BYTES

    project_config_feedback = checker._public_pytest_failure_feedback(
        subprocess.CompletedProcess(
            [sys.executable, "-m", "pytest"],
            1,
            (
                "FAILED tools/benchmark-runner/tests/test_routing_s2.py::"
                "test_s2_fake_four_cell_plan_judge_property_seal_export\n"
                "RuntimeError: b1 preflight failed: B1 run validate failed\n"
            ),
            "",
        )
    )
    project_config_text = "\n".join(project_config_feedback)
    assert "legacy project.yaml fields purpose, requirements, and task_order" in project_config_text
    assert "core_compat, repository_root" in project_config_text
    assert "default_capability_profile, and default_policy" in project_config_text
    assert "RuntimeError: b1 preflight failed" in project_config_text
    assert len(project_config_text.encode("utf-8")) <= checker.WORKER_FEEDBACK_MAX_BYTES

    long_path_feedback = checker._public_pytest_failure_feedback(
        subprocess.CompletedProcess(
            [sys.executable, "-m", "pytest"],
            1,
            "RoutingSuiteError: git show failed: Filename too long\n",
            "",
        )
    )
    long_path_text = "\n".join(long_path_feedback)
    assert "Windows path limit" in long_path_text
    assert "core.longpaths=true" in long_path_text

    missing_effect_feedback = checker._public_pytest_failure_feedback(
        subprocess.CompletedProcess(
            [sys.executable, "-m", "pytest"],
            1,
            (
                "FAILED tools/benchmark-runner/tests/test_routing_s2.py::"
                "test_s2_fake_four_cell_plan_judge_property_seal_export\n"
                "E assert all(result.check_success for result in results)\n"
            ),
            "",
        )
    )
    missing_effect_text = "\n".join(missing_effect_feedback)
    assert "GOLDEN_ROOT/_golden_turns" in missing_effect_text
    assert "write_file effects" in missing_effect_text
    assert "result envelopes alone do not change the workspace" in missing_effect_text

    r9_style_feedback = checker._public_pytest_failure_feedback(
        subprocess.CompletedProcess(
            [sys.executable, "-m", "pytest"],
            1,
            (
                "ERROR tools/benchmark-runner/tests/test_routing_s2.py::"
                "test_s2_b1_preflight_canonicalizes_legacy_project_pack\n"
                "Traceback (most recent call last):\n"
                "  File \"tools/benchmark-runner/tests/test_routing_s2.py\", line 731\n"
                "    prepared = prepare_fixture()\n"
                "ValueError: missing required field core_compat\n"
            ),
            "public stderr detail\n",
        )
    )
    r9_style_text = "\n".join(r9_style_feedback)
    assert "Traceback (most recent call last)" in r9_style_text
    assert "line 731" in r9_style_text
    assert "ValueError: missing required field core_compat" in r9_style_text
    assert "public stderr detail" in r9_style_text

    undecodable_stream_feedback = checker._public_pytest_failure_feedback(
        subprocess.CompletedProcess(
            [sys.executable, "-m", "pytest"],
            1,
            None,
            None,
        )
    )
    assert "public S2 pytest exited 1" in "\n".join(undecodable_stream_feedback)
    source = (
        WORKER_ROOT / "benchmark_checks" / "check_profile_r.py"
    ).read_text(encoding="utf-8")
    assert 'errors="replace"' in source

    def fail_r07() -> None:
        raise checker.PublicContractError("failed", public_feedback=feedback)

    checker.CHECKS["R07"] = fail_r07
    assert checker.main(["check_profile_r.py", "R07"]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "R07_PUBLIC_CONTRACT_FAILED",
        "CHECK_FAILURE_CLASS:PRODUCT_ASSERTION",
        *(f"WORKER_FEEDBACK:{line}" for line in feedback),
    ]


def test_profile_r_public_check_main_separates_structured_failure_diagnostics(
    capsys,
) -> None:
    checker = _load_profile_r_public_checker()
    diagnostic_result = {
        "classification": "PRODUCT_ASSERTION",
        "comparison_valid": False,
        "environment_failure_present": False,
        "nodes": [],
        "product_failure_present": True,
        "schema_version": 1,
        "task_id": "R11",
    }
    environment_diagnostic = checker._default_environment_diagnostic(
        "R11",
        "TEST_ENVIRONMENT_FAILURE",
    )

    def fail_product() -> None:
        raise checker.PublicContractError(
            "product failed",
            diagnostic_result=diagnostic_result,
            public_feedback=["repair the public behavior"],
        )

    checker.CHECKS["R11"] = fail_product
    assert checker.main(["check_profile_r.py", "R11"]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "R11_PUBLIC_CONTRACT_FAILED",
        "CHECK_FAILURE_CLASS:PRODUCT_ASSERTION",
        checker.CHECK_DIAGNOSTIC_RESULT_PREFIX
        + json.dumps(
            diagnostic_result,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ),
        "WORKER_FEEDBACK:repair the public behavior",
    ]

    def fail_environment() -> None:
        raise checker.PublicContractError(
            "environment failed",
            failure_classification="ENVIRONMENT",
            environment_diagnostic=environment_diagnostic,
        )

    checker.CHECKS["R11"] = fail_environment
    assert checker.main(["check_profile_r.py", "R11"]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "R11_PUBLIC_CONTRACT_FAILED",
        "CHECK_FAILURE_CLASS:ENVIRONMENT",
        checker.CHECK_ENVIRONMENT_DIAGNOSTIC_PREFIX
        + json.dumps(
            environment_diagnostic,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ),
    ]

    def fail_mixed() -> None:
        raise checker.PublicContractError(
            "mixed failure",
            failure_classification="MIXED_PRODUCT_AND_ENVIRONMENT",
            environment_diagnostic=environment_diagnostic,
            diagnostic_result=diagnostic_result,
        )

    checker.CHECKS["R11"] = fail_mixed
    assert checker.main(["check_profile_r.py", "R11"]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "R11_PUBLIC_CONTRACT_FAILED",
        "CHECK_FAILURE_CLASS:MIXED_PRODUCT_AND_ENVIRONMENT",
        checker.CHECK_DIAGNOSTIC_RESULT_PREFIX
        + json.dumps(
            diagnostic_result,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ),
        checker.CHECK_ENVIRONMENT_DIAGNOSTIC_PREFIX
        + json.dumps(
            environment_diagnostic,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ),
    ]


def test_profile_r_pristine_task_pack_fails_each_public_completion_check() -> None:
    check_path = WORKER_ROOT / "benchmark_checks/check_profile_r.py"
    for number in range(1, 14):
        task_id = f"R{number:02d}"
        result = subprocess.run(
            [sys.executable, str(check_path), task_id],
            cwd=WORKER_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
        assert result.returncode == 1
        assert result.stdout.splitlines()[:2] == [
            f"{task_id}_PUBLIC_CONTRACT_FAILED",
            "CHECK_FAILURE_CLASS:PRODUCT_ASSERTION",
        ]
        assert result.stderr == ""


def test_profile_r_judge_source_bundle_manifest_and_evidence_are_closed() -> None:
    manifest = json.loads(
        (JUDGE_SOURCE_ROOT / "bundle-manifest.json").read_text(encoding="utf-8")
    )
    eligibility = json.loads(
        (JUDGE_SOURCE_ROOT / "challenge-eligibility.json").read_text(encoding="utf-8")
    )
    assert manifest["status"] == "PROFILE_R_SOURCE_BUNDLE_VERIFIED"
    assert eligibility["status"] == "PROFILE_R_SOURCE_BUNDLE_VERIFIED"
    assert eligibility["source_bundle_verified"] is True
    assert eligibility["judge_runtime_boundary_verified"] is False
    assert eligibility["challenge_ready"] is False
    records = manifest["files"]
    assert eligibility["public_r11_r12_reference_verified"] is True
    assert manifest["file_count_excluding_manifest"] == len(records) == 47
    for record in records:
        payload = (JUDGE_SOURCE_ROOT / record["path"]).read_bytes()
        assert len(payload) == record["size"]
        assert hashlib.sha256(payload).hexdigest() == record["sha256"]

    reference = json.loads(
        (JUDGE_SOURCE_ROOT / "evidence/reference.json").read_text(encoding="utf-8")
    )
    pristine = json.loads(
        (JUDGE_SOURCE_ROOT / "evidence/pristine.json").read_text(encoding="utf-8")
    )
    assert reference["aggregate_status"] == "pass"
    assert {item["status"] for item in reference["properties"]} == {"pass"}
    assert pristine["aggregate_status"] == "fail"

    for task_id, expected_tests in (("r11", 7), ("r12", 5)):
        public = json.loads(
            (JUDGE_SOURCE_ROOT / f"evidence/public-{task_id}-reference.json").read_text(
                encoding="utf-8"
            )
        )
        assert public["passed"] is True
        assert public["return_code"] == 0
        assert public["contract_ok_marker"] is True
        projection = public["evidence_projection"]
        assert projection["pytest"] == {
            "tests": expected_tests,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "warnings": 0,
        }
        assert projection["growth_margin"] >= 32
        assert projection["growth_probe_minimum_path_length"] == 261
        assert projection["growth_probe_minimum_satisfied"] is True
        assert projection["probe_repository_shorter_than_growth_path"] is True
        assert public["evidence_projection_sha256"] == hashlib.sha256(
            (json.dumps(projection, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        ).hexdigest()


def test_profile_r_negative_mutations_fail_only_target_or_block_dependents() -> None:
    target_by_name = {
        "r-p01-source-boundary": "R-P01-SOURCE-BOUNDARY",
        "r-p02-discriminator": "R-P02-DISCRIMINATOR",
        "r-p03-config-fixture": "R-P03-CONFIG-FIXTURE",
        "r-p04-incident-fixture": "R-P04-INCIDENT-FIXTURE",
        "r-p05-manifest-binding": "R-P05-MANIFEST-BINDING",
        "r-p06-plan-binding": "R-P06-PLAN-BINDING",
        "r-p07-routing-policy": "R-P07-ROUTING-POLICY",
        "r-p08-lifecycle-reuse": "R-P08-LIFECYCLE-REUSE",
        "r-p09-status-posthoc": "R-P09-STATUS-POSTHOC",
        "r-p10-export-verify": "R-P10-EXPORT-VERIFY",
        "r-p11-s2-e2e": "R-P11-S2-E2E",
        "r-p12-s1-portability": "R-P12-S1-PORTABILITY",
        "r-p13-operator-semantics": "R-P13-OPERATOR-SEMANTICS",
    }
    evidence_root = JUDGE_SOURCE_ROOT / "evidence" / "mutations"
    patch_root = JUDGE_SOURCE_ROOT / "negative-mutations"
    assert {path.stem for path in evidence_root.glob("*.json")} == set(target_by_name)
    assert {path.stem for path in patch_root.glob("*.patch")} == set(target_by_name)
    for name, target in target_by_name.items():
        result = json.loads((evidence_root / f"{name}.json").read_text(encoding="utf-8"))
        statuses = {item["property_id"]: item["status"] for item in result["properties"]}
        assert statuses[target] == "fail"
        assert "checker_error" not in statuses.values()
        assert result.get("public_contract") is None
        assert (patch_root / f"{name}.patch").stat().st_size > 0

    public_matrix = json.loads(
        (JUDGE_SOURCE_ROOT / "evidence/public-negative-matrix.json").read_text(
            encoding="utf-8"
        )
    )
    assert [item["mutation_id"] for item in public_matrix["cases"]] == list(
        target_by_name
    )
    assert all(
        item["public_contract"]["contract_rejected"] is True
        for item in public_matrix["cases"]
    )


def test_profile_r_judge_checker_is_model_free_and_worker_has_no_solution_leak() -> None:
    checker = (JUDGE_SOURCE_ROOT / "checker/check_properties.py").read_text(
        encoding="utf-8"
    )
    protected = (
        JUDGE_SOURCE_ROOT / "checker/protected_behavior_checks.py"
    ).read_text(encoding="utf-8")
    compile(checker, "check_properties.py", "exec")
    compile(protected, "protected_behavior_checks.py", "exec")
    forbidden_runtime = (
        "openai_codex",
        "CodexClient",
        "turn/start",
        "OPENAI_API_KEY",
        "CODEX_API_KEY",
    )
    assert all(value not in checker + protected for value in forbidden_runtime)
    assert "blocked_by_prerequisite" not in checker
    assert "checker_error" in checker
    leakage = json.loads(
        (JUDGE_SOURCE_ROOT / "solution-leakage-catalog.json").read_text(
            encoding="utf-8"
        )
    )
    for path in _workspace_files(WORKER_ROOT):
        payload = path.read_bytes()
        for literal in leakage["forbidden_worker_literals"]:
            assert literal.encode("utf-8") not in payload


def test_profile_r_protected_judge_rejects_worker_test_oracle_co_mutation() -> None:
    evidence = json.loads(
        (
            JUDGE_SOURCE_ROOT
            / "evidence"
            / "adversarial-worker-test-oracle.json"
        ).read_text(encoding="utf-8")
    )
    cases = {item["case_id"]: item for item in evidence["cases"]}
    assert len(cases) == 7
    for mode in ("noop", "skip", "assert_false"):
        value = cases[f"worker-tests-{mode}"]
        assert value["aggregate_status"] == "fail"
        assert value["statuses"]["R-P11-S2-E2E"] == "fail"
        assert value["statuses"]["R-P12-S1-PORTABILITY"] == "fail"
        assert value["matched_expectation"] is True

    targets = {
        "r-p02-discriminator": "R-P02-DISCRIMINATOR",
        "r-p07-routing-policy": "R-P07-ROUTING-POLICY",
        "r-p10-export-verify": "R-P10-EXPORT-VERIFY",
        "r-p12-s1-portability": "R-P12-S1-PORTABILITY",
    }
    for mutation, target in targets.items():
        value = cases[f"{mutation}-plus-noop"]
        assert value["worker_test_mode"] == "noop"
        assert value["aggregate_status"] == "fail"
        assert value["statuses"][target] == "fail"
        assert value["matched_expectation"] is True

    p07 = cases["r-p07-routing-policy-plus-noop"]
    assert p07["statuses"]["R-P07-ROUTING-POLICY"] == "fail"
    assert p07["statuses"]["R-P10-EXPORT-VERIFY"] == "pass"
