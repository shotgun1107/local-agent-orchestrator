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
FIXTURE_ROOT = (
    REPOSITORY
    / "benchmarks"
    / "fixtures"
    / "routing-realistic-high-difficulty-v1"
    / "realistic-incident-repair-001"
)
JUDGE_ROOT = (
    REPOSITORY
    / "benchmarks"
    / "judge-source"
    / "sdk-routing-realistic-high-difficulty-v1"
    / "realistic-incident-repair-001"
)
WORKER_ROOT = FIXTURE_ROOT / "workspace"
MANIFEST_PATH = FIXTURE_ROOT / "worker-snapshot-manifest.json"
ALLOWLIST_PATH = FIXTURE_ROOT / "worker-source-allowlist.json"
BOUNDARY_PATH = JUDGE_ROOT / "worker-information-boundary.json"
LEAKAGE_PATH = JUDGE_ROOT / "solution-leakage-catalog.json"
LINEAGE_PATH = JUDGE_ROOT / "failure-lineage.json"
BUILDER_PATH = (
    REPOSITORY
    / "tools"
    / "benchmark-runner"
    / "scripts"
    / "build_profile_i_worker_snapshot.py"
)


def _load_builder():
    spec = importlib.util.spec_from_file_location(
        "profile_i_worker_snapshot_builder", BUILDER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _pretty_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _workspace_files(root: Path) -> list[Path]:
    return sorted(
        (path for path in root.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(root).as_posix().encode("utf-8"),
    )


def test_profile_i_worker_snapshot_is_bound_to_base_git_objects() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    allowlist = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    files = _workspace_files(WORKER_ROOT)
    by_path = {record["path"]: record for record in manifest["files"]}

    assert manifest["status"] == "ANONYMIZED_WORKER_TASK_PACK_CANDIDATE"
    assert manifest["challenge_ready"] is False
    assert manifest["base_file_count"] == allowlist["expected_file_count"] == 10
    assert manifest["public_observation_file_count"] == 1
    assert manifest["file_count"] == len(files) == len(by_path) == 20
    for path in files:
        relative = path.relative_to(WORKER_ROOT).as_posix()
        record = by_path[relative]
        payload = path.read_bytes()
        assert len(payload) == record["worker_size"]
        assert hashlib.sha256(payload).hexdigest() == record["worker_sha256"]
        assert record["provenance"] in {
            "base_snapshot",
            "public_observation",
            "public_requirement",
        }


def test_profile_i_public_observations_are_hash_bound_without_final_candidate() -> None:
    observations = json.loads(
        (WORKER_ROOT / "profile-i/evidence/public-observations.json").read_text(
            encoding="utf-8"
        )
    )["records"]
    lineage = json.loads(LINEAGE_PATH.read_text(encoding="utf-8"))["records"]
    by_ordinal = {record["ordinal"]: record for record in lineage}

    assert [record["observation_id"] for record in observations] == [
        f"O{number:03d}" for number in range(1, 15)
    ]
    assert len({record["observation_sha256"] for record in observations}) == 14
    for number, record in enumerate(observations, start=1):
        payload = dict(record)
        stored = payload.pop("observation_sha256")
        canonical = (
            json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        assert hashlib.sha256(canonical).hexdigest() == stored
        source = by_ordinal[f"P{number:03d}"]
        assert record["raw_ordinal_aggregate_sha256"] == source[
            "raw_ordinal_aggregate_sha256"
        ]
        assert record["revision_evidence_sha256"] == source[
            "revision_evidence_sha256"
        ]

    serialized = json.dumps(observations, sort_keys=True).casefold()
    assert "p015" not in serialized
    assert "runtime_boundary_candidate" not in serialized


def test_profile_i_task_graph_is_exact_and_protected_paths_are_not_writable() -> None:
    run = yaml.safe_load((WORKER_ROOT / "benchmark-run.yaml").read_text(encoding="utf-8"))
    tasks = run["tasks"]
    assert [task["key"] for task in tasks] == [f"I{number:02d}" for number in range(1, 9)]
    assert {task["key"]: task["depends_on"] for task in tasks} == {
        "I01": [],
        "I02": ["I01"],
        "I03": ["I01", "I02"],
        "I04": ["I01", "I03"],
        "I05": ["I01", "I04"],
        "I06": ["I03", "I05"],
        "I07": ["I02", "I05"],
        "I08": ["I01", "I06", "I07"],
    }
    protected = {
        "README.md",
        "benchmark-run.yaml",
        "benchmark_checks/**",
        ".orchestrator/**",
        "profile-i/evidence/**",
        "profile-i/requirements/**",
    }
    for task in tasks:
        assert task["workspace_mode"] == "shared_serial_write"
        assert task["approval"] == "none"
        assert protected.isdisjoint(set(task["write_scope"]))
        assert task["check_names"] == [f"{task['key'].lower()}_contract", "diff_check"]


def test_profile_i_information_boundary_covers_every_worker_file() -> None:
    boundary = json.loads(BOUNDARY_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert boundary["status"] == "WORKER_INFORMATION_BOUNDARY_VERIFIED"
    assert boundary["challenge_ready"] is False
    assert boundary["file_count"] == manifest["file_count"] == 20
    assert boundary["worker_tree_aggregate_sha256"] == manifest[
        "worker_tree_aggregate_sha256"
    ]
    assert [record["path"] for record in boundary["files"]] == [
        record["path"] for record in manifest["files"]
    ]
    assert set(boundary["allowed_provenance"]) == {
        "base_snapshot",
        "public_observation",
        "public_requirement",
    }
    assert [task["task_id"] for task in boundary["tasks"]] == [
        f"I{number:02d}" for number in range(1, 9)
    ]
    assert len(boundary["checks"]) == 9
    assert {check["check_id"] for check in boundary["checks"]} == {
        *(f"i{number:02d}_contract" for number in range(1, 9)),
        "diff_check",
    }
    assert boundary["b1_feedback_contract"]["per_stream_maximum_bytes"] == 2048
    assert boundary["b1_feedback_contract"]["combined_maximum_bytes"] == 4096
    by_path = {record["path"]: record for record in manifest["files"]}
    assert boundary["task_manifest_sha256"] == by_path["benchmark-run.yaml"][
        "worker_sha256"
    ]
    assert boundary["checks_manifest_sha256"] == by_path[
        ".orchestrator/checks.yaml"
    ]["worker_sha256"]


def test_profile_i_worker_surface_has_no_solution_or_raw_identifier_leak() -> None:
    leakage = json.loads(LEAKAGE_PATH.read_text(encoding="utf-8"))
    lineage = json.loads(LINEAGE_PATH.read_text(encoding="utf-8"))["records"]
    final_record = lineage[-1]
    forbidden_hashes = {
        final_record["source_commit"],
        final_record["raw_ordinal_aggregate_sha256"],
        *(binding["sha256"] for binding in final_record["artifact_bindings"]),
    }
    overlay_paths = {
        path.relative_to(WORKER_ROOT).as_posix()
        for path in _workspace_files(WORKER_ROOT)
        if path.relative_to(WORKER_ROOT).as_posix()
        in {
            record["path"]
            for record in json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))["files"]
            if record["provenance"] != "base_snapshot"
        }
    }
    forbidden_literals = {
        literal
        for fact in leakage["facts"]
        for literal in fact["forbidden_normalized_literals"]
    }
    expected_reference_hashes = {
        final_record["source_commit"],
        final_record["raw_ordinal_aggregate_sha256"],
        *(binding["sha256"] for binding in final_record["artifact_bindings"]),
    }
    for fact in leakage["facts"]:
        assert set(fact) == {
            "fact_id",
            "forbidden_normalized_literals",
            "forbidden_structured_keys",
            "reference_only_hashes",
            "source_evidence_sha256",
            "task_ids",
        }
        assert set(fact["reference_only_hashes"]) == expected_reference_hashes
        assert re.fullmatch(r"[0-9a-f]{64}", fact["source_evidence_sha256"])
    for path in _workspace_files(WORKER_ROOT):
        payload = path.read_bytes()
        assert all(value.encode("ascii") not in payload for value in forbidden_hashes)
        relative = path.relative_to(WORKER_ROOT).as_posix()
        if relative in overlay_paths:
            text = payload.decode("utf-8").casefold().replace("\\", "/")
            assert all(literal not in text for literal in forbidden_literals)
            assert re.search(r"C:[\\/]Users[\\/]", text, re.IGNORECASE) is None
            assert re.search(r"S-1-[0-9-]{8,}", text) is None
            assert re.search(
                r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text
            ) is None


def test_profile_i_public_check_is_model_free_and_compiles() -> None:
    check_path = WORKER_ROOT / "benchmark_checks/check_profile_i.py"
    source = check_path.read_text(encoding="utf-8")
    compile(source, str(check_path), "exec")
    forbidden = (
        "openai_codex",
        "CodexClient",
        "turn/start",
        "OPENAI_API_KEY",
        "CODEX_API_KEY",
    )
    assert all(value not in source for value in forbidden)


def test_profile_i_pristine_worker_fails_all_public_task_contracts() -> None:
    check_path = WORKER_ROOT / "benchmark_checks/check_profile_i.py"
    for number in range(1, 9):
        task_id = f"I{number:02d}"
        completed = subprocess.run(
            [sys.executable, str(check_path), task_id],
            cwd=WORKER_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
        assert completed.returncode == 1
        result = json.loads(completed.stdout)
        assert result["task_id"] == task_id
        assert result["passed"] is False
        assert result["reason_codes"]
        assert completed.stderr == ""


def test_profile_i_worker_snapshot_rebuild_is_byte_identical(tmp_path: Path) -> None:
    builder = _load_builder()
    output_a = tmp_path / "a" / "workspace"
    manifest_a = tmp_path / "a" / "manifest.json"
    boundary_a = tmp_path / "a" / "boundary.json"
    output_b = tmp_path / "b" / "workspace"
    manifest_b = tmp_path / "b" / "manifest.json"
    boundary_b = tmp_path / "b" / "boundary.json"

    built_a, info_a = builder.build_snapshot(
        REPOSITORY, output_a, manifest_a, boundary_a
    )
    built_b, info_b = builder.build_snapshot(
        REPOSITORY, output_b, manifest_b, boundary_b
    )

    assert manifest_a.read_bytes() == manifest_b.read_bytes() == MANIFEST_PATH.read_bytes()
    assert boundary_a.read_bytes() == boundary_b.read_bytes() == BOUNDARY_PATH.read_bytes()
    assert built_a["worker_tree_aggregate_sha256"] == built_b[
        "worker_tree_aggregate_sha256"
    ]
    assert info_a == info_b
    files_a = _workspace_files(output_a)
    files_b = _workspace_files(output_b)
    assert [path.relative_to(output_a).as_posix() for path in files_a] == [
        path.relative_to(output_b).as_posix() for path in files_b
    ]
    for path_a, path_b in zip(files_a, files_b, strict=True):
        assert path_a.read_bytes() == path_b.read_bytes()
