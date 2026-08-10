from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


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
    assert intake["status"] == "SOURCE_VERIFIED_COMPOSITION_PENDING"


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
