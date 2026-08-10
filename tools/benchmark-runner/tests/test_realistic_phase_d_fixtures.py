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
