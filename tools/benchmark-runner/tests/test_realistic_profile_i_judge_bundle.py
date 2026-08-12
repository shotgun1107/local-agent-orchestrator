from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from benchmark_runner.realistic_profile_i_docker_matrix import (
    MUTATION_TARGETS,
    ORDERED_VARIANTS,
    PreparedVariant,
    _cell_result,
)
from benchmark_runner.realistic_docker_judge import DockerJudgeManifest, DockerJudgeResult


REPOSITORY = Path(__file__).resolve().parents[3]
PROFILE_ROOT = REPOSITORY / "benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-incident-repair-001"
JUDGE_ROOT = REPOSITORY / "benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-incident-repair-001"


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_profile_i_bundle_manifest_and_evidence_are_closed() -> None:
    manifest = _load(JUDGE_ROOT / "bundle-manifest.json")
    eligibility = _load(JUDGE_ROOT / "challenge-eligibility.json")
    assert manifest["status"] == "PROFILE_I_SOURCE_BUNDLE_VERIFIED"
    assert eligibility["source_bundle_verified"] is True
    assert eligibility["judge_runtime_boundary_verified"] is False
    assert eligibility["challenge_ready"] is False
    records = manifest["files"]
    assert manifest["file_count_excluding_manifest"] == len(records) == 37
    for record in records:
        payload = (JUDGE_ROOT / record["path"]).read_bytes()
        assert len(payload) == record["size"]
        assert hashlib.sha256(payload).hexdigest() == record["sha256"]

    reference = _load(JUDGE_ROOT / "evidence/reference.json")
    pristine = _load(JUDGE_ROOT / "evidence/pristine.json")
    assert reference["aggregate_status"] == "pass"
    assert len(reference["properties"]) == 10
    assert {row["status"] for row in reference["properties"]} == {"pass"}
    assert pristine["aggregate_status"] == "fail"


def test_profile_i_mutations_fail_only_target_or_block_dependents() -> None:
    evidence_root, patch_root = JUDGE_ROOT / "evidence/mutations", JUDGE_ROOT / "negative-mutations"
    expected = dict(MUTATION_TARGETS)
    assert {path.stem for path in evidence_root.glob("*.json")} == set(expected)
    assert {path.stem for path in patch_root.glob("*.patch")} == set(expected)
    for mutation_id, target in expected.items():
        assert (patch_root / f"{mutation_id}.patch").stat().st_size > 0
        result = _load(evidence_root / f"{mutation_id}.json")
        statuses = {row["property_id"]: row["status"] for row in result["properties"]}
        assert statuses[target] == "fail"
        assert all(status in {"pass", "blocked_by_prerequisite"} for key, status in statuses.items() if key != target)


def test_profile_i_reference_checker_recomputes_without_mutating_workspace() -> None:
    checker_path = JUDGE_ROOT / "checker/check_properties.py"
    spec = importlib.util.spec_from_file_location("profile_i_checker_test", checker_path)
    assert spec is not None and spec.loader is not None
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    recorded = _load(JUDGE_ROOT / "evidence/pristine.json")
    actual = checker.evaluate_workspace(PROFILE_ROOT / "workspace", experiment_id="phase-d-profile-i", cell_id="pristine")
    assert actual["aggregate_status"] == recorded["aggregate_status"] == "fail"
    assert actual["workspace_mutated"] is False
    assert [row["status"] for row in actual["properties"]] == [row["status"] for row in recorded["properties"]]


def test_profile_i_docker_variant_order_and_exact_comparison() -> None:
    assert len(ORDERED_VARIANTS) == 11
    expected = _load(JUDGE_ROOT / "evidence/reference.json")
    variant = PreparedVariant(1, "reference", None, None, "profile-i-test-reference", expected, ("reference.patch",), ("a" * 64,))
    manifest = DockerJudgeManifest.model_construct(run_id=variant.run_id)
    result = DockerJudgeResult.model_construct(run_id=variant.run_id, status="CHECKS_PASSED", checker_payload=expected, result_sha256="b" * 64)
    cell = _cell_result(variant, manifest, result)
    assert cell["matched_expectation"] is True
    assert cell["mismatch_codes"] == []


def test_profile_i_docker_comparison_rejects_property_drift() -> None:
    expected = _load(JUDGE_ROOT / "evidence/reference.json")
    changed = json.loads(json.dumps(expected))
    changed["properties"][0]["status"] = "fail"
    changed["aggregate_status"] = "fail"
    variant = PreparedVariant(1, "reference", None, None, "profile-i-test-reference", expected, ("reference.patch",), ("a" * 64,))
    manifest = DockerJudgeManifest.model_construct(run_id=variant.run_id)
    result = DockerJudgeResult.model_construct(run_id=variant.run_id, status="CHECKS_FAILED", checker_payload=changed, result_sha256="b" * 64)
    cell = _cell_result(variant, manifest, result)
    assert cell["matched_expectation"] is False
    assert cell["mismatch_codes"] == ["AGGREGATE_STATUS_MISMATCH", "PROPERTY_STATUS_MISMATCH", "REFERENCE_NOT_ALL_PASS"]


def test_profile_i_versioned_qualification_is_exact_eleven_cell_projection() -> None:
    path = REPOSITORY / "benchmarks/artifacts/profile-i-docker-judge-qualification-v1/qualification.json"
    if not path.is_file():
        return
    payload = _load(path)
    assert payload["status"] == "CHALLENGE_READY"
    assert payload["challenge_ready"] is True
    assert payload["model_turns"] == 0
    assert [row["variant_id"] for row in payload["cells"]] == list(ORDERED_VARIANTS)
    assert all(row["matched_expectation"] is True for row in payload["cells"])
