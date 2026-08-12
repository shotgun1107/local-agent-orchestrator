"""Model-free Docker Judge qualification matrix for the Profile I fixture."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Protocol

from .runner import atomic_write, canonical_json_bytes, sha256_bytes, sha256_file
from .realistic_docker_judge import (
    DockerJudgeManifest,
    DockerJudgeResult,
    build_docker_controller_environment,
    execute_docker_judge,
    verify_docker_judge_result,
)
from .realistic_judge import PreparedJudgeRoots, prepare_realistic_judge_roots
from .realistic_docker_judge_matrix import GitPatchBackend, PatchBackend


SNAPSHOT_ID = "realistic-incident-repair-001"
PROFILE_ROOT = f"benchmarks/fixtures/routing-realistic-high-difficulty-v1/{SNAPSHOT_ID}/workspace"
JUDGE_ROOT = f"benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/{SNAPSHOT_ID}"
MUTATION_TARGETS: tuple[tuple[str, str], ...] = (
    ("i-p01-active-profile", "I-P01-ACTIVE-PROFILE"),
    ("i-p02-no-legacy-sandbox", "I-P02-NO-LEGACY-SANDBOX"),
    ("i-p03-elevated-identity", "I-P03-ELEVATED-IDENTITY"),
    ("i-p04-w-acl-boundary", "I-P04-W-ACL-BOUNDARY"),
    ("i-p05-js-controller-only", "I-P05-JS-CONTROLLER-ONLY"),
    ("i-p06-link-cleanup", "I-P06-LINK-ESCAPE-CLEANUP"),
    ("i-p07-child-secret", "I-P07-CHILD-SECRET-BOUNDARY"),
    ("i-p08-state-nondisclosure", "I-P08-STATE-NONDISCLOSURE"),
    ("i-p09-bundle-recalculation", "I-P09-BUNDLE-RECALCULATION"),
    ("i-p10-evidence-claims", "I-P10-EVIDENCE-CLAIM-ALIGNMENT"),
)
ORDERED_VARIANTS = ("reference", *(item[0] for item in MUTATION_TARGETS))
EVIDENCE_FILES = (
    "docker-judge-manifest.json",
    "docker-judge-process.json",
    "docker-judge-result.json",
    "docker-judge.stdout.bin",
    "docker-judge.stderr.bin",
)


class ProfileIDockerMatrixError(RuntimeError):
    pass


@dataclass(frozen=True)
class PreparedVariant:
    ordinal: int
    variant_id: str
    target_property_id: str | None
    roots: PreparedJudgeRoots | None
    run_id: str
    expected: dict[str, Any]
    patch_paths: tuple[str, ...]
    patch_sha256s: tuple[str, ...]


@dataclass(frozen=True)
class ProfileIDockerMatrixExecution:
    root: Path
    manifest: dict[str, Any]
    result: dict[str, Any]
    seal: dict[str, Any]


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ProfileIDockerMatrixError(f"expected object: {path.name}")
    return value


def _relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ProfileIDockerMatrixError("unsafe matrix path")
    return path


def _patch_spec(variant_id: str) -> tuple[str | None, tuple[str, ...], str]:
    if variant_id == "reference":
        return None, ("reference.patch",), "evidence/reference.json"
    target = dict(MUTATION_TARGETS).get(variant_id)
    if target is None:
        raise ProfileIDockerMatrixError("unknown Profile I variant")
    return target, ("reference.patch", f"negative-mutations/{variant_id}.patch"), f"evidence/mutations/{variant_id}.json"


def _prepare_variant(
    *,
    repository: Path,
    cells_root: Path,
    source_commit: str,
    run_token: str,
    ordinal: int,
    variant_id: str,
    patch_backend: PatchBackend,
    environment: Mapping[str, str],
) -> PreparedVariant:
    roots = prepare_realistic_judge_roots(
        repository=repository,
        base_root=cells_root,
        source_commit=source_commit,
        run_token=f"{run_token}-{ordinal:02d}-{variant_id}",
        worker_prefix=PROFILE_ROOT,
        judge_source_prefix=JUDGE_ROOT,
        run_label="profile-i-judge",
    )
    target, patch_paths, evidence_path = _patch_spec(variant_id)
    hashes: list[str] = []
    for relative in patch_paths:
        patch = roots.J.joinpath(*_relative(relative).parts).read_bytes()
        if not patch:
            raise ProfileIDockerMatrixError("matrix patch is empty")
        hashes.append(sha256_bytes(patch))
        patch_backend.apply(roots.W, patch, environment=environment)
    if (roots.W / ".git").exists():
        raise ProfileIDockerMatrixError("patch application created Git metadata")
    expected = _load(roots.J.joinpath(*_relative(evidence_path).parts))
    return PreparedVariant(ordinal, variant_id, target, roots, roots.run_root.name, expected, patch_paths, tuple(hashes))


def _property_statuses(payload: Mapping[str, Any] | None) -> dict[str, str]:
    if payload is None or not isinstance(payload.get("properties"), list):
        return {}
    return {
        str(item["property_id"]): str(item["status"])
        for item in payload["properties"]
        if isinstance(item, dict) and "property_id" in item and "status" in item
    }


def _cell_result(variant: PreparedVariant, manifest: DockerJudgeManifest, result: DockerJudgeResult) -> dict[str, Any]:
    expected_statuses = _property_statuses(variant.expected)
    actual_statuses = _property_statuses(result.checker_payload)
    mismatches: list[str] = []
    if result.status not in {"CHECKS_PASSED", "CHECKS_FAILED"}:
        mismatches.append("DOCKER_STATUS_NOT_CHECK_RESULT")
    if result.checker_payload is None or result.checker_payload.get("aggregate_status") != variant.expected.get("aggregate_status"):
        mismatches.append("AGGREGATE_STATUS_MISMATCH")
    if actual_statuses != expected_statuses:
        mismatches.append("PROPERTY_STATUS_MISMATCH")
    if len(actual_statuses) != 10:
        mismatches.append("PROPERTY_COUNT_MISMATCH")
    if variant.target_property_id is not None and actual_statuses.get(variant.target_property_id) != "fail":
        mismatches.append("TARGET_PROPERTY_NOT_FAILED")
    if variant.target_property_id is None and any(value != "pass" for value in actual_statuses.values()):
        mismatches.append("REFERENCE_NOT_ALL_PASS")
    return {
        "ordinal": variant.ordinal,
        "variant_id": variant.variant_id,
        "target_property_id": variant.target_property_id,
        "run_id": variant.run_id,
        "patch_paths": list(variant.patch_paths),
        "patch_sha256s": list(variant.patch_sha256s),
        "docker_manifest_sha256": sha256_bytes(canonical_json_bytes(manifest)),
        "docker_result_sha256": result.result_sha256,
        "docker_status": result.status,
        "aggregate_status": None if result.checker_payload is None else result.checker_payload.get("aggregate_status"),
        "properties": [{"property_id": key, "status": actual_statuses[key]} for key in sorted(actual_statuses)],
        "mismatch_codes": sorted(set(mismatches)),
        "matched_expectation": not mismatches,
    }


def _payload_records(root: Path) -> list[dict[str, Any]]:
    records = []
    paths = [root / "batch-manifest.json", root / "batch-result.json"]
    for run_root in sorted((root / "cells").iterdir(), key=lambda item: item.name.encode("utf-8")):
        paths.extend(run_root / relative for relative in EVIDENCE_FILES)
    for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix().encode("utf-8")):
        if not path.is_file():
            raise ProfileIDockerMatrixError("matrix evidence file is missing")
        relative = path.relative_to(root).as_posix()
        records.append({"path": relative, "size": path.stat().st_size, "sha256": sha256_file(path)})
    return records


def _seal(root: Path, manifest: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    records = _payload_records(root)
    files = b"".join(f"{row['sha256']}  {row['path']}\n".encode() for row in records)
    atomic_write(root / "files.sha256", files)
    values = {
        "schema_version": 1,
        "batch_id": manifest["batch_id"],
        "file_count": len(records),
        "files_sha256": sha256_bytes(files),
        "payload_aggregate_sha256": sha256_bytes(canonical_json_bytes(records)),
        "manifest_sha256": manifest["manifest_sha256"],
        "result_sha256": result["result_sha256"],
    }
    seal = {**values, "seal_sha256": sha256_bytes(canonical_json_bytes(values))}
    atomic_write(root / "batch-seal.json", canonical_json_bytes(seal))
    return seal


def execute_profile_i_docker_matrix(
    *,
    repository: Path,
    base_root: Path,
    source_commit: str,
    docker_executable: Path,
    run_token: str,
    source_environment: Mapping[str, str] | None = None,
    patch_backend: PatchBackend | None = None,
) -> ProfileIDockerMatrixExecution:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,47}", run_token):
        raise ProfileIDockerMatrixError("matrix run token is not canonical")
    repository, parent, docker = Path(repository).resolve(strict=True), Path(base_root).resolve(strict=True), Path(docker_executable).resolve(strict=True)
    environment = build_docker_controller_environment(source_environment)
    batch_id = f"profile-i-docker-matrix-{run_token}"
    root = parent / batch_id
    if root.exists():
        raise ProfileIDockerMatrixError("matrix root already exists")
    root.mkdir()
    cells = root / "cells"
    cells.mkdir()
    backend = patch_backend or GitPatchBackend()
    variants = [
        _prepare_variant(repository=repository, cells_root=cells, source_commit=source_commit, run_token=run_token, ordinal=ordinal, variant_id=variant_id, patch_backend=backend, environment=environment)
        for ordinal, variant_id in enumerate(ORDERED_VARIANTS, 1)
    ]
    manifest_values = {
        "schema_version": 1,
        "profile": "I",
        "snapshot_id": SNAPSHOT_ID,
        "batch_id": batch_id,
        "source_commit": source_commit,
        "docker_executable_sha256": sha256_file(docker),
        "model_turns": 0,
        "variants": [
            {"ordinal": row.ordinal, "variant_id": row.variant_id, "target_property_id": row.target_property_id, "run_id": row.run_id, "patch_paths": list(row.patch_paths), "patch_sha256s": list(row.patch_sha256s), "expected_evidence_sha256": sha256_bytes(canonical_json_bytes(row.expected))}
            for row in variants
        ],
    }
    manifest = {**manifest_values, "manifest_sha256": sha256_bytes(canonical_json_bytes(manifest_values))}
    atomic_write(root / "batch-manifest.json", canonical_json_bytes(manifest))
    results = []
    for variant in variants:
        if variant.roots is None:
            raise ProfileIDockerMatrixError("prepared variant roots are missing")
        docker_manifest, docker_result = execute_docker_judge(variant.roots, docker_executable=docker, source_environment=environment, cell_id=variant.variant_id)
        results.append(_cell_result(variant, docker_manifest, docker_result))
    result_values = {"schema_version": 1, "profile": "I", "batch_id": batch_id, "manifest_sha256": manifest["manifest_sha256"], "model_turns": 0, "status": "CHALLENGE_READY" if all(row["matched_expectation"] for row in results) else "CHALLENGE_NOT_READY", "challenge_ready": all(row["matched_expectation"] for row in results), "cells": results}
    result = {**result_values, "result_sha256": sha256_bytes(canonical_json_bytes(result_values))}
    atomic_write(root / "batch-result.json", canonical_json_bytes(result))
    seal = _seal(root, manifest, result)
    verify_profile_i_docker_matrix(root)
    return ProfileIDockerMatrixExecution(root, manifest, result, seal)


def verify_profile_i_docker_matrix(root: Path) -> dict[str, Any]:
    root = Path(root).resolve(strict=True)
    manifest, stored, seal = _load(root / "batch-manifest.json"), _load(root / "batch-result.json"), _load(root / "batch-seal.json")
    manifest_payload = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if manifest.get("manifest_sha256") != sha256_bytes(canonical_json_bytes(manifest_payload)):
        raise ProfileIDockerMatrixError("manifest hash mismatch")
    if [row.get("variant_id") for row in manifest.get("variants", [])] != list(ORDERED_VARIANTS):
        raise ProfileIDockerMatrixError("variant order mismatch")
    cells = []
    for plan in manifest["variants"]:
        run_root = root / "cells" / plan["run_id"]
        docker_manifest = DockerJudgeManifest.model_validate_json((run_root / "docker-judge-manifest.json").read_bytes())
        docker_result = DockerJudgeResult.model_validate_json((run_root / "docker-judge-result.json").read_bytes())
        verify_docker_judge_result(docker_manifest, docker_result)
        judge_roots = list(run_root.glob(".judge-private-*/runtime"))
        if len(judge_roots) != 1:
            raise ProfileIDockerMatrixError("cell does not contain exactly one protected runtime J")
        expected = _load(judge_roots[0] / ("evidence/reference.json" if plan["variant_id"] == "reference" else f"evidence/mutations/{plan['variant_id']}.json"))
        variant = PreparedVariant(plan["ordinal"], plan["variant_id"], plan["target_property_id"], None, plan["run_id"], expected, tuple(plan["patch_paths"]), tuple(plan["patch_sha256s"]))
        cells.append(_cell_result(variant, docker_manifest, docker_result))
    result_values = {key: value for key, value in stored.items() if key != "result_sha256"}
    recomputed_values = {**result_values, "cells": cells, "status": "CHALLENGE_READY" if all(row["matched_expectation"] for row in cells) else "CHALLENGE_NOT_READY", "challenge_ready": all(row["matched_expectation"] for row in cells)}
    if stored.get("result_sha256") != sha256_bytes(canonical_json_bytes(result_values)) or result_values != recomputed_values:
        raise ProfileIDockerMatrixError("stored matrix result differs from recomputation")
    records = _payload_records(root)
    files = b"".join(f"{row['sha256']}  {row['path']}\n".encode() for row in records)
    expected_values = {"schema_version": 1, "batch_id": manifest["batch_id"], "file_count": len(records), "files_sha256": sha256_bytes(files), "payload_aggregate_sha256": sha256_bytes(canonical_json_bytes(records)), "manifest_sha256": manifest["manifest_sha256"], "result_sha256": stored["result_sha256"]}
    expected_seal = {**expected_values, "seal_sha256": sha256_bytes(canonical_json_bytes(expected_values))}
    if (root / "files.sha256").read_bytes() != files or seal != expected_seal:
        raise ProfileIDockerMatrixError("matrix seal mismatch")
    return stored


def qualification_projection(execution: ProfileIDockerMatrixExecution) -> dict[str, Any]:
    return {"schema_version": 1, "profile": "I", "snapshot_id": SNAPSHOT_ID, "source_commit": execution.manifest["source_commit"], "batch_id": execution.manifest["batch_id"], "manifest_sha256": execution.manifest["manifest_sha256"], "result_sha256": execution.result["result_sha256"], "seal_sha256": execution.seal["seal_sha256"], "status": execution.result["status"], "challenge_ready": execution.result["challenge_ready"], "model_turns": 0, "cells": [{key: row[key] for key in ("ordinal", "variant_id", "docker_status", "aggregate_status", "matched_expectation", "docker_result_sha256", "properties")} for row in execution.result["cells"]]}
