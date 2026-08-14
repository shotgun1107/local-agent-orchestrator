from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

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


def _load_profile_r_public_checker():
    path = WORKER_ROOT / "benchmark_checks" / "check_profile_r.py"
    spec = importlib.util.spec_from_file_location("profile_r_public_checker", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _workspace_files(root: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in root.rglob("*")
            if path.is_file()
            and not {".git", ".pytest_cache", "__pycache__"}.intersection(
                path.relative_to(root).parts
            )
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
    assert manifest["base_file_count"] == allowlist["expected_file_count"] == 115
    assert manifest["public_overlay_file_count"] == len(overlay_files)
    assert manifest["file_count"] == len(files) == allowlist["expected_file_count"] + len(overlay_files)
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
    assert task_ids == [f"R{number:02d}" for number in range(1, 9)]
    assert {task["key"]: task["depends_on"] for task in tasks} == {
        "R01": [],
        "R02": ["R01"],
        "R03": ["R01"],
        "R04": ["R02", "R03"],
        "R05": ["R02", "R04"],
        "R06": ["R04", "R05"],
        "R07": ["R01", "R03", "R06"],
        "R08": ["R02", "R07"],
    }
    assert max(_dependency_depth(tasks, task_id) for task_id in task_ids) == 7
    assert {task_id for task_id, task in zip(task_ids, tasks, strict=True) if len(task["depends_on"]) > 1} == {
        "R04", "R05", "R06", "R07", "R08"
    }
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
        assert task["check_names"] == [f"{task['key'].lower()}_contract", "diff_check"]
        assert protected.isdisjoint(set(task["write_scope"]))

    r07 = next(task for task in tasks if task["key"] == "R07")
    assert "FrozenManifest and FrozenFixtureSpec" in r07["goal"]
    assert "strict models only" in r07["goal"]
    assert "do not forward S2 stage or profile dictionaries" in r07["goal"]
    assert "Preserve Windows long-path support" in r07["goal"]
    assert "GOLDEN_ROOT/_golden_turns" in r07["goal"]
    assert "completed result envelope without file effects is invalid" in r07["goal"]

    checks = yaml.safe_load(
        (WORKER_ROOT / ".orchestrator/checks.yaml").read_text(encoding="utf-8")
    )["checks"]
    assert list(checks) == [
        *(f"r{number:02d}_contract" for number in range(1, 9)),
        "diff_check",
    ]
    for number in range(1, 9):
        check = checks[f"r{number:02d}_contract"]
        assert check["argv"] == [
            "python",
            "benchmark_checks/check_profile_r.py",
            f"R{number:02d}",
        ]
        assert check["timeout_seconds"] == 120


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


def test_profile_r_pristine_task_pack_fails_each_public_completion_check() -> None:
    check_path = WORKER_ROOT / "benchmark_checks/check_profile_r.py"
    for number in range(1, 9):
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
        assert result.stdout.splitlines() == [
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
    assert manifest["file_count_excluding_manifest"] == len(records) == 32
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


def test_profile_r_negative_mutations_fail_only_target_or_block_dependents() -> None:
    target_by_name = {
        "r-p01-legacy-bytes": "R-P01-LEGACY-BYTES",
        "r-p02-stage-discriminator": "R-P02-STAGE-DISCRIMINATOR",
        "r-p03-plan-binding": "R-P03-PLAN-BINDING",
        "r-p04-reserve-isolation": "R-P04-RESERVE-ISOLATION",
        "r-p05-lifecycle-reuse": "R-P05-LIFECYCLE-REUSE",
        "r-p06-export-roundtrip": "R-P06-EXPORT-ROUNDTRIP",
        "r-p07-cross-checkout": "R-P07-CROSS-CHECKOUT-REPRO",
        "r-p08-operator-contract": "R-P08-OPERATOR-CONTRACT",
    }
    evidence_root = JUDGE_SOURCE_ROOT / "evidence" / "mutations"
    patch_root = JUDGE_SOURCE_ROOT / "negative-mutations"
    assert {path.stem for path in evidence_root.glob("*.json")} == set(target_by_name)
    assert {path.stem for path in patch_root.glob("*.patch")} == set(target_by_name)
    for name, target in target_by_name.items():
        result = json.loads((evidence_root / f"{name}.json").read_text(encoding="utf-8"))
        statuses = {item["property_id"]: item["status"] for item in result["properties"]}
        assert statuses[target] == "fail"
        assert all(
            status in {"pass", "blocked_by_prerequisite"}
            for property_id, status in statuses.items()
            if property_id != target
        )
        assert (patch_root / f"{name}.patch").stat().st_size > 0


def test_profile_r_judge_checker_is_model_free_and_worker_has_no_solution_leak() -> None:
    checker = (JUDGE_SOURCE_ROOT / "checker/check_properties.py").read_text(
        encoding="utf-8"
    )
    compile(checker, "check_properties.py", "exec")
    forbidden_runtime = (
        "openai_codex",
        "CodexClient",
        "turn/start",
        "OPENAI_API_KEY",
        "CODEX_API_KEY",
    )
    assert all(value not in checker for value in forbidden_runtime)
    leakage = json.loads(
        (JUDGE_SOURCE_ROOT / "solution-leakage-catalog.json").read_text(
            encoding="utf-8"
        )
    )
    for path in _workspace_files(WORKER_ROOT):
        payload = path.read_bytes()
        for literal in leakage["forbidden_worker_literals"]:
            assert literal.encode("utf-8") not in payload
