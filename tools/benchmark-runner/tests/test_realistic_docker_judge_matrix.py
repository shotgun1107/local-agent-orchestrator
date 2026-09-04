from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import pytest

from benchmark_runner.realistic_docker_judge import DockerJudgeManifest, DockerJudgeResult
from benchmark_runner.realistic_docker_judge_matrix import (
    EQUIVALENT_TARGETS,
    MUTATION_TARGETS,
    GitPatchBackend,
    MatrixVariantPlan,
    PropertyExpectation,
    compare_variant_result,
)
from benchmark_runner.runner import sha256_bytes, sha256_file


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
JUDGE_ROOT = (
    REPOSITORY_ROOT
    / "benchmarks"
    / "judge-source"
    / "sdk-routing-realistic-high-difficulty-v1"
    / "realistic-compat-migration-001"
)


def _payload(relative: str) -> dict[str, object]:
    return json.loads((JUDGE_ROOT / relative).read_text(encoding="utf-8"))


def _plan(variant_id: str) -> tuple[MatrixVariantPlan, dict[str, object]]:
    if variant_id == "reference":
        kind = "reference"
        target = None
        patches = ["reference.patch"]
        evidence = "evidence/reference.json"
        ordinal = 1
    elif variant_id in dict(EQUIVALENT_TARGETS):
        targets = dict(EQUIVALENT_TARGETS)
        kind = "positive_equivalent"
        target = targets[variant_id]
        patches = [
            "reference.patch",
            f"equivalent-implementations/{variant_id}.patch",
        ]
        evidence = f"evidence/equivalents/{variant_id}.json"
        ordinal = [item[0] for item in EQUIVALENT_TARGETS].index(variant_id) + 2
    else:
        targets = dict(MUTATION_TARGETS)
        kind = "negative_mutation"
        target = targets[variant_id]
        patches = ["reference.patch", f"negative-mutations/{variant_id}.patch"]
        evidence = f"evidence/mutations/{variant_id}.json"
        ordinal = [item[0] for item in MUTATION_TARGETS].index(variant_id) + 2
    payload = _payload(evidence)
    plan = MatrixVariantPlan(
        ordinal=ordinal,
        variant_id=variant_id,
        kind=kind,
        target_property_id=target,
        patch_paths=patches,
        patch_sha256=[sha256_file(JUDGE_ROOT / path) for path in patches],
        expected_evidence_path=evidence,
        expected_evidence_sha256=sha256_file(JUDGE_ROOT / evidence),
        expected_aggregate_status=payload["aggregate_status"],
        expected_workspace_sha256=payload["workspace_after_sha256"],
        expected_catalog_sha256=payload["catalog_sha256"],
        expected_prerequisite_dag_sha256=payload["prerequisite_dag_sha256"],
        expected_checker_sha256=payload["checker_sha256"],
        expected_properties=[
            PropertyExpectation(property_id=item["property_id"], status=item["status"])
            for item in payload["properties"]
        ],
        run_id=f"profile-r-judge-test-{variant_id}",
    )
    return plan, payload


def _docker_objects(
    plan: MatrixVariantPlan,
    payload: dict[str, object],
) -> tuple[DockerJudgeManifest, DockerJudgeResult]:
    manifest = DockerJudgeManifest.model_construct(
        run_id=plan.run_id,
        command=["test"],
        command_sha256=sha256_bytes(b"test"),
    )
    result = DockerJudgeResult.model_construct(
        run_id=plan.run_id,
        status=(
            "CHECKS_FAILED"
            if plan.kind == "negative_mutation"
            else "CHECKS_PASSED"
        ),
        checker_payload=payload,
        result_sha256="a" * 64,
    )
    return manifest, result


def test_registered_reference_and_mutation_expectations_are_strict() -> None:
    assert len(MUTATION_TARGETS) == 13
    reference, _ = _plan("reference")
    assert {item.status for item in reference.expected_properties} == {"pass"}
    for variant_id, target in MUTATION_TARGETS:
        plan, _ = _plan(variant_id)
        statuses = {item.property_id: item.status for item in plan.expected_properties}
        assert plan.target_property_id == target
        assert statuses[target] == "fail"
        assert "blocked_by_prerequisite" not in statuses.values()
        assert set(statuses.values()) <= {"pass", "fail"}


def test_registered_public_equivalents_are_all_pass() -> None:
    assert len(EQUIVALENT_TARGETS) == 2
    for variant_id, target in EQUIVALENT_TARGETS:
        plan, _ = _plan(variant_id)
        assert plan.kind == "positive_equivalent"
        assert plan.target_property_id == target
        assert plan.expected_aggregate_status == "pass"
        assert {item.status for item in plan.expected_properties} == {"pass"}


def test_variant_plan_records_independent_cofailures() -> None:
    plan, _ = _plan("r-p05-manifest-binding")
    properties = [item.model_copy() for item in plan.expected_properties]
    unrelated_index = next(
        index
        for index, item in enumerate(properties)
        if item.property_id != plan.target_property_id
    )
    properties[unrelated_index] = properties[unrelated_index].model_copy(update={"status": "fail"})
    changed = MatrixVariantPlan(
        **plan.model_dump(exclude={"expected_properties"}),
        expected_properties=properties,
    )
    assert sum(item.status == "fail" for item in changed.expected_properties) >= 2


@pytest.mark.parametrize(
    "variant_id",
    [
        "reference",
        "r11-equivalent-write-effects",
        "r-p01-source-boundary",
    ],
)
def test_comparator_accepts_exact_registered_result(variant_id: str) -> None:
    plan, payload = _plan(variant_id)
    manifest, result = _docker_objects(plan, payload)
    cell = compare_variant_result(plan, manifest, result)
    assert cell.matched_expectation is True
    assert cell.mismatch_codes == []


def test_comparator_rejects_property_and_provenance_drift() -> None:
    plan, payload = _plan("reference")
    changed = copy.deepcopy(payload)
    changed["catalog_sha256"] = "0" * 64
    changed["properties"][0]["status"] = "fail"
    manifest, result = _docker_objects(plan, changed)
    cell = compare_variant_result(plan, manifest, result)
    assert cell.matched_expectation is False
    assert cell.mismatch_codes == ["CATALOG_SHA256_MISMATCH", "PROPERTY_STATUS_MISMATCH"]


def test_git_patch_backend_applies_without_git_metadata(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "value.txt").write_bytes(b"before\n")
    patch = (
        b"diff --git a/value.txt b/value.txt\n"
        b"--- a/value.txt\n"
        b"+++ b/value.txt\n"
        b"@@ -1 +1 @@\n"
        b"-before\n"
        b"+after\n"
    )
    environment = {
        name: os.environ[name]
        for name in ("PATH", "SYSTEMROOT", "WINDIR", "COMSPEC")
        if name in os.environ
    }
    GitPatchBackend().apply(workspace, patch, environment=environment)
    assert (workspace / "value.txt").read_bytes() == b"after\n"
    assert not (workspace / ".git").exists()
