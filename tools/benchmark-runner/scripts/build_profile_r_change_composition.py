from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path


SNAPSHOT_ID = "realistic-compat-migration-001"
PROFILE_R_ROOT = Path(
    "benchmarks/fixtures/routing-realistic-high-difficulty-v1"
) / SNAPSHOT_ID
GOLDEN_PREFIX = "benchmarks/posthoc-checks/sdk-routing-v1/s2/golden/"
FIXTURE_PREFIX = "benchmarks/fixtures/routing-v1/intermediate/"
ROUTING_SUITE_SOURCE = "tools/benchmark-runner/src/benchmark_runner/routing_suite.py"
GENERATED_SCHEMAS = {
    "benchmarks/suites/sdk-routing-v1/stage.schema.json",
    "benchmarks/suites/sdk-routing-v1/suite.schema.json",
}
HISTORICAL_PATHS = {
    "docs/operations/codex-revision-log.md",
    "docs/operations/home-codex-handoff.md",
    "docs/operations/implementation-incidents/index.md",
}


def _git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout


def _classify(path: str) -> tuple[str, str | None, str, bool]:
    if path.startswith(GOLDEN_PREFIX):
        canonical = FIXTURE_PREFIX + path.removeprefix(GOLDEN_PREFIX)
        return (
            "golden_or_export_mirror",
            canonical,
            "byte_mirror_of_reference_fixture",
            False,
        )
    if path in GENERATED_SCHEMAS:
        return (
            "generated_schema_or_manifest",
            ROUTING_SUITE_SOURCE,
            "generated_from_routing_suite_models",
            False,
        )
    if (
        path.startswith("docs/reviews/")
        or path in HISTORICAL_PATHS
        or path.startswith("docs/operations/implementation-incidents/entries/")
    ):
        return (
            "historical_result_or_evidence",
            None,
            "historical_record_excluded_from_structure",
            False,
        )
    if "/benchmark_checks/" in path or path.startswith(
        "tools/benchmark-runner/tests/"
    ):
        return "authored_test", path, "authored_at_reference_commit", True
    if path.endswith(".py") and path.startswith(
        (
            "benchmarks/fixtures/",
            "benchmarks/posthoc-checks/",
            "tools/benchmark-runner/scripts/",
            "tools/benchmark-runner/src/",
        )
    ):
        return "authored_source", path, "authored_at_reference_commit", True
    return (
        "authored_spec_or_operator_contract",
        path,
        "authored_at_reference_commit",
        True,
    )


def build_composition(repository: Path) -> dict[str, object]:
    intake_path = repository / PROFILE_R_ROOT / "source-intake.json"
    intake = json.loads(intake_path.read_text(encoding="utf-8"))
    base = intake["base_commit"]
    reference = intake["reference_commit"]
    records: list[dict[str, object]] = []
    for line in _git(repository, "diff", "--name-status", base, reference).splitlines():
        git_status, path = line.split("\t", 1)
        category, canonical, producer, counted = _classify(path)
        semantic_source = canonical if canonical is not None else path
        records.append(
            {
                "path": path,
                "git_status": git_status,
                "category": category,
                "semantic_group_id": (
                    ("content:" if canonical is not None else "history:")
                    + semantic_source
                ),
                "canonical_source_paths": [] if canonical is None else [canonical],
                "producer_or_derivation": producer,
                "counted_for_structure": counted,
            }
        )

    records.sort(key=lambda item: str(item["path"]).encode("utf-8"))
    changed_paths = {str(item["path"]) for item in records}
    for record in records:
        if record["category"] == "golden_or_export_mirror":
            canonical = str(record["canonical_source_paths"][0])
            if canonical not in changed_paths:
                raise RuntimeError(f"golden mirror lacks changed source: {canonical}")
    counted_groups = [
        str(item["semantic_group_id"])
        for item in records
        if item["counted_for_structure"]
    ]
    duplicates = [
        group for group, count in Counter(counted_groups).items() if count != 1
    ]
    if duplicates:
        raise RuntimeError("counted semantic group is duplicated")
    if len(records) != intake["changed_path_count"]:
        raise RuntimeError("composition path count differs from source intake")

    category_counts = Counter(str(item["category"]) for item in records)
    return {
        "schema_version": 1,
        "snapshot_id": SNAPSHOT_ID,
        "profile": "R",
        "status": "COMPOSITION_CANDIDATE",
        "base_commit": base,
        "reference_commit": reference,
        "classification_revision": "profile-r-composition-r1",
        "raw_changed_path_count": len(records),
        "counted_semantic_group_count": len(counted_groups),
        "category_counts": dict(sorted(category_counts.items())),
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Profile R change composition.")
    parser.add_argument(
        "--repository",
        type=Path,
        default=Path(__file__).resolve().parents[3],
    )
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    repository = arguments.repository.resolve(strict=True)
    output = arguments.output or repository / PROFILE_R_ROOT / "r-change-composition.json"
    payload = build_composition(repository)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
