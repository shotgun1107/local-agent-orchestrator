"""Sealed Profile R reference and negative-mutation Docker Judge matrix.

The matrix materializes nine fresh workspaces from one exact Git commit:
one reference solution and eight pre-registered negative mutations.  It never
calls Codex or a model.  Expected property outcomes and patch bytes are read
only from the protected Judge source extracted from that same commit.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Literal, Mapping, Protocol, Sequence

from pydantic import Field, model_validator

from benchmark_runner.contract import Sha256, StrictModel, utc_now, validate_timestamp
from benchmark_runner.realistic_docker_judge import (
    DOCKER_JUDGE_DOCKERFILE_SHA256,
    DOCKER_JUDGE_IMAGE,
    DOCKER_JUDGE_REQUIREMENTS_SHA256,
    DockerJudgeManifest,
    DockerJudgeResult,
    build_docker_controller_environment,
    execute_docker_judge,
    verify_docker_judge_result,
)
from benchmark_runner.realistic_judge import PreparedJudgeRoots, prepare_realistic_judge_roots
from benchmark_runner.runner import atomic_write, canonical_json_bytes, sha256_bytes, sha256_file


REFERENCE_VARIANT = "reference"
MUTATION_TARGETS: tuple[tuple[str, str], ...] = (
    ("r-p01-legacy-bytes", "R-P01-LEGACY-BYTES"),
    ("r-p02-stage-discriminator", "R-P02-STAGE-DISCRIMINATOR"),
    ("r-p03-plan-binding", "R-P03-PLAN-BINDING"),
    ("r-p04-reserve-isolation", "R-P04-RESERVE-ISOLATION"),
    ("r-p05-lifecycle-reuse", "R-P05-LIFECYCLE-REUSE"),
    ("r-p06-export-roundtrip", "R-P06-EXPORT-ROUNDTRIP"),
    ("r-p07-cross-checkout", "R-P07-CROSS-CHECKOUT-REPRO"),
    ("r-p08-operator-contract", "R-P08-OPERATOR-CONTRACT"),
)
ORDERED_VARIANTS = (REFERENCE_VARIANT, *(item[0] for item in MUTATION_TARGETS))
EVIDENCE_FILES = (
    "docker-judge-manifest.json",
    "docker-judge-process.json",
    "docker-judge-result.json",
    "docker-judge.stdout.bin",
    "docker-judge.stderr.bin",
)


class DockerJudgeMatrixError(RuntimeError):
    """Raised when a matrix cannot be constructed or independently verified."""


class PropertyExpectation(StrictModel):
    property_id: str = Field(pattern=r"^R-P[0-9]{2}-[A-Z0-9-]+$")
    status: Literal["pass", "fail", "blocked_by_prerequisite"]


class MatrixVariantPlan(StrictModel):
    ordinal: int = Field(ge=1, le=9)
    variant_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,63}$")
    kind: Literal["reference", "negative_mutation"]
    target_property_id: str | None
    patch_paths: list[str] = Field(min_length=1, max_length=2)
    patch_sha256: list[Sha256] = Field(min_length=1, max_length=2)
    expected_evidence_path: str
    expected_evidence_sha256: Sha256
    expected_aggregate_status: Literal["pass", "fail"]
    expected_workspace_sha256: Sha256
    expected_catalog_sha256: Sha256
    expected_prerequisite_dag_sha256: Sha256
    expected_checker_sha256: Sha256
    expected_properties: list[PropertyExpectation] = Field(min_length=8, max_length=8)
    run_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,119}$")

    @model_validator(mode="after")
    def variant_is_coherent(self) -> "MatrixVariantPlan":
        if len(self.patch_paths) != len(self.patch_sha256):
            raise ValueError("matrix patch path/hash count mismatch")
        if self.kind == "reference":
            if self.variant_id != REFERENCE_VARIANT or self.target_property_id is not None:
                raise ValueError("reference variant identity is invalid")
            if self.expected_aggregate_status != "pass" or any(
                item.status != "pass" for item in self.expected_properties
            ):
                raise ValueError("reference expectation is not an all-pass result")
        else:
            statuses = {item.property_id: item.status for item in self.expected_properties}
            if self.target_property_id is None or statuses.get(self.target_property_id) != "fail":
                raise ValueError("negative mutation target is not expected to fail")
            if self.expected_aggregate_status != "fail":
                raise ValueError("negative mutation must expect an aggregate failure")
            if any(
                status not in {"pass", "blocked_by_prerequisite"}
                for property_id, status in statuses.items()
                if property_id != self.target_property_id
            ):
                raise ValueError("negative mutation expectation has an unrelated failure")
        return self


class DockerJudgeMatrixManifest(StrictModel):
    schema_version: Literal[1] = 1
    batch_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,119}$")
    created_at: datetime
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    image_reference: Literal[DOCKER_JUDGE_IMAGE] = DOCKER_JUDGE_IMAGE
    image_dockerfile_sha256: Literal[DOCKER_JUDGE_DOCKERFILE_SHA256] = DOCKER_JUDGE_DOCKERFILE_SHA256
    image_requirements_sha256: Literal[DOCKER_JUDGE_REQUIREMENTS_SHA256] = DOCKER_JUDGE_REQUIREMENTS_SHA256
    docker_executable_sha256: Sha256
    model_turns: Literal[0] = 0
    variants: list[MatrixVariantPlan] = Field(min_length=9, max_length=9)
    manifest_sha256: Sha256

    @model_validator(mode="after")
    def manifest_is_canonical(self) -> "DockerJudgeMatrixManifest":
        validate_timestamp(self.created_at)
        if [item.ordinal for item in self.variants] != list(range(1, 10)):
            raise ValueError("matrix ordinals are not exact 1..9")
        if tuple(item.variant_id for item in self.variants) != ORDERED_VARIANTS:
            raise ValueError("matrix variant order differs from the frozen order")
        payload = self.model_dump(mode="json", exclude={"manifest_sha256"})
        if self.manifest_sha256 != sha256_bytes(canonical_json_bytes(payload)):
            raise ValueError("matrix manifest SHA-256 mismatch")
        return self


class MatrixCellResult(StrictModel):
    ordinal: int = Field(ge=1, le=9)
    variant_id: str
    run_id: str
    docker_manifest_sha256: Sha256
    docker_result_sha256: Sha256
    docker_status: str
    aggregate_status: str | None
    properties: list[PropertyExpectation]
    mismatch_codes: list[str]
    matched_expectation: bool

    @model_validator(mode="after")
    def cell_is_canonical(self) -> "MatrixCellResult":
        if self.mismatch_codes != sorted(set(self.mismatch_codes)):
            raise ValueError("matrix mismatch codes must be sorted and unique")
        if self.matched_expectation != (not self.mismatch_codes):
            raise ValueError("matrix match flag differs from mismatch codes")
        return self


MatrixStatus = Literal["CHALLENGE_READY", "CHALLENGE_NOT_READY", "CHALLENGE_INVALID"]


class DockerJudgeMatrixResult(StrictModel):
    schema_version: Literal[1] = 1
    batch_id: str
    completed_at: datetime
    status: MatrixStatus
    challenge_ready: bool
    model_turns: Literal[0] = 0
    manifest_sha256: Sha256
    cells: list[MatrixCellResult] = Field(min_length=9, max_length=9)
    result_sha256: Sha256

    @model_validator(mode="after")
    def result_is_canonical(self) -> "DockerJudgeMatrixResult":
        validate_timestamp(self.completed_at)
        if [item.ordinal for item in self.cells] != list(range(1, 10)):
            raise ValueError("matrix result ordinals are not exact 1..9")
        expected_ready = all(item.matched_expectation for item in self.cells)
        if self.challenge_ready != expected_ready:
            raise ValueError("matrix challenge-ready flag differs from its cells")
        if self.status == "CHALLENGE_READY" and not expected_ready:
            raise ValueError("non-matching matrix cannot be challenge ready")
        if self.status != "CHALLENGE_READY" and expected_ready:
            raise ValueError("matching matrix must be challenge ready")
        payload = self.model_dump(mode="json", exclude={"result_sha256"})
        if self.result_sha256 != sha256_bytes(canonical_json_bytes(payload)):
            raise ValueError("matrix result SHA-256 mismatch")
        return self


class MatrixFileRecord(StrictModel):
    path: str
    size: int = Field(ge=0)
    sha256: Sha256


class DockerJudgeMatrixSeal(StrictModel):
    schema_version: Literal[1] = 1
    batch_id: str
    file_count: int = Field(ge=1)
    files_sha256: Sha256
    payload_aggregate_sha256: Sha256
    manifest_sha256: Sha256
    result_sha256: Sha256
    seal_sha256: Sha256

    @model_validator(mode="after")
    def seal_is_canonical(self) -> "DockerJudgeMatrixSeal":
        payload = self.model_dump(mode="json", exclude={"seal_sha256"})
        if self.seal_sha256 != sha256_bytes(canonical_json_bytes(payload)):
            raise ValueError("matrix seal SHA-256 mismatch")
        return self


class PatchBackend(Protocol):
    def apply(self, workspace: Path, patch: bytes, *, environment: Mapping[str, str]) -> None: ...


class GitPatchBackend:
    """Apply already hash-bound patches without creating a repository in W."""

    def apply(self, workspace: Path, patch: bytes, *, environment: Mapping[str, str]) -> None:
        command = [
            "git",
            "-c",
            "core.autocrlf=false",
            "-c",
            "core.safecrlf=false",
            "apply",
            "--no-index",
            "--whitespace=nowarn",
            "-",
        ]
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        check = subprocess.run(
            [*command[:6], "--check", *command[6:]],
            cwd=workspace,
            env=dict(environment),
            input=patch,
            capture_output=True,
            creationflags=creationflags,
        )
        if check.returncode != 0:
            raise DockerJudgeMatrixError("frozen patch precheck failed")
        applied = subprocess.run(
            command,
            cwd=workspace,
            env=dict(environment),
            input=patch,
            capture_output=True,
            creationflags=creationflags,
        )
        if applied.returncode != 0:
            raise DockerJudgeMatrixError("frozen patch application failed")


@dataclass(frozen=True)
class PreparedVariant:
    plan: MatrixVariantPlan
    roots: PreparedJudgeRoots


@dataclass(frozen=True)
class DockerJudgeMatrixExecution:
    root: Path
    manifest: DockerJudgeMatrixManifest
    result: DockerJudgeMatrixResult
    seal: DockerJudgeMatrixSeal


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise DockerJudgeMatrixError(f"expected an object in {path.name}")
    return value


def _safe_relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise DockerJudgeMatrixError("matrix contains an unsafe relative path")
    return path


def _expectations(payload: Mapping[str, Any]) -> list[PropertyExpectation]:
    raw = payload.get("properties")
    if not isinstance(raw, list):
        raise DockerJudgeMatrixError("expected evidence lacks properties")
    return [
        PropertyExpectation(property_id=str(item["property_id"]), status=str(item["status"]))
        for item in raw
        if isinstance(item, dict)
    ]


def _variant_source(variant_id: str) -> tuple[Literal["reference", "negative_mutation"], str | None, list[str], str]:
    if variant_id == REFERENCE_VARIANT:
        return "reference", None, ["reference.patch"], "evidence/reference.json"
    targets = dict(MUTATION_TARGETS)
    if variant_id not in targets:
        raise DockerJudgeMatrixError("unknown Profile R matrix variant")
    return (
        "negative_mutation",
        targets[variant_id],
        ["reference.patch", f"negative-mutations/{variant_id}.patch"],
        f"evidence/mutations/{variant_id}.json",
    )


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
    token = f"{run_token}-{ordinal:02d}-{variant_id}"
    roots = prepare_realistic_judge_roots(
        repository=repository,
        base_root=cells_root,
        source_commit=source_commit,
        run_token=token,
    )
    kind, target, patch_paths, evidence_path = _variant_source(variant_id)
    patch_hashes: list[str] = []
    for relative in patch_paths:
        pure = _safe_relative(relative)
        patch_path = roots.J.joinpath(*pure.parts)
        patch = patch_path.read_bytes()
        if not patch:
            raise DockerJudgeMatrixError("matrix patch is empty")
        patch_hashes.append(sha256_bytes(patch))
        patch_backend.apply(roots.W, patch, environment=environment)
    if (roots.W / ".git").exists():
        raise DockerJudgeMatrixError("patch backend created repository metadata in W")
    evidence_file = roots.J.joinpath(*_safe_relative(evidence_path).parts)
    expected = _load_json(evidence_file)
    properties = _expectations(expected)
    if len(properties) != 8:
        raise DockerJudgeMatrixError("expected evidence property count is not eight")
    plan = MatrixVariantPlan(
        ordinal=ordinal,
        variant_id=variant_id,
        kind=kind,
        target_property_id=target,
        patch_paths=patch_paths,
        patch_sha256=patch_hashes,
        expected_evidence_path=evidence_path,
        expected_evidence_sha256=sha256_file(evidence_file),
        expected_aggregate_status=str(expected["aggregate_status"]),
        expected_workspace_sha256=str(expected["workspace_after_sha256"]),
        expected_catalog_sha256=str(expected["catalog_sha256"]),
        expected_prerequisite_dag_sha256=str(expected["prerequisite_dag_sha256"]),
        expected_checker_sha256=str(expected["checker_sha256"]),
        expected_properties=properties,
        run_id=roots.run_root.name,
    )
    return PreparedVariant(plan=plan, roots=roots)


def _manifest(
    *,
    batch_id: str,
    source_commit: str,
    docker_executable: Path,
    variants: Sequence[PreparedVariant],
) -> DockerJudgeMatrixManifest:
    values = {
        "batch_id": batch_id,
        "created_at": utc_now(),
        "source_commit": source_commit,
        "docker_executable_sha256": sha256_file(docker_executable),
        "variants": [item.plan for item in variants],
    }
    draft = DockerJudgeMatrixManifest.model_construct(**values, manifest_sha256="0" * 64)
    return DockerJudgeMatrixManifest(
        **values,
        manifest_sha256=sha256_bytes(
            canonical_json_bytes(draft.model_dump(mode="json", exclude={"manifest_sha256"}))
        ),
    )


def _actual_properties(payload: Mapping[str, Any] | None) -> list[PropertyExpectation]:
    if payload is None:
        return []
    try:
        return _expectations(payload)
    except (DockerJudgeMatrixError, KeyError, ValueError):
        return []


def compare_variant_result(
    plan: MatrixVariantPlan,
    docker_manifest: DockerJudgeManifest,
    docker_result: DockerJudgeResult,
) -> MatrixCellResult:
    codes: list[str] = []
    expected_docker_status = "CHECKS_PASSED" if plan.kind == "reference" else "CHECKS_FAILED"
    if docker_result.status != expected_docker_status:
        codes.append("DOCKER_STATUS_MISMATCH")
    payload = docker_result.checker_payload
    properties = _actual_properties(payload)
    if payload is None:
        codes.append("CHECKER_PAYLOAD_MISSING")
        aggregate = None
    else:
        aggregate = str(payload.get("aggregate_status"))
        checks = {
            "CHECKER_RUN_STATUS_MISMATCH": payload.get("checker_run_status") == "completed",
            "AGGREGATE_STATUS_MISMATCH": aggregate == plan.expected_aggregate_status,
            "WORKSPACE_BEFORE_MISMATCH": payload.get("workspace_before_sha256") == plan.expected_workspace_sha256,
            "WORKSPACE_AFTER_MISMATCH": payload.get("workspace_after_sha256") == plan.expected_workspace_sha256,
            "WORKSPACE_MUTATED": payload.get("workspace_mutated") is False,
            "CATALOG_SHA256_MISMATCH": payload.get("catalog_sha256") == plan.expected_catalog_sha256,
            "DAG_SHA256_MISMATCH": payload.get("prerequisite_dag_sha256") == plan.expected_prerequisite_dag_sha256,
            "CHECKER_SHA256_MISMATCH": payload.get("checker_sha256") == plan.expected_checker_sha256,
        }
        codes.extend(code for code, passed in checks.items() if not passed)
        if properties != plan.expected_properties:
            codes.append("PROPERTY_STATUS_MISMATCH")
    return MatrixCellResult(
        ordinal=plan.ordinal,
        variant_id=plan.variant_id,
        run_id=plan.run_id,
        docker_manifest_sha256=sha256_bytes(canonical_json_bytes(docker_manifest)),
        docker_result_sha256=docker_result.result_sha256,
        docker_status=docker_result.status,
        aggregate_status=aggregate,
        properties=properties,
        mismatch_codes=sorted(set(codes)),
        matched_expectation=not codes,
    )


def _matrix_status(cells: Sequence[MatrixCellResult]) -> MatrixStatus:
    if all(item.matched_expectation for item in cells):
        return "CHALLENGE_READY"
    if any(item.docker_status == "CHALLENGE_INVALID" for item in cells):
        return "CHALLENGE_INVALID"
    return "CHALLENGE_NOT_READY"


def _result(manifest: DockerJudgeMatrixManifest, cells: list[MatrixCellResult]) -> DockerJudgeMatrixResult:
    status = _matrix_status(cells)
    values = {
        "batch_id": manifest.batch_id,
        "completed_at": utc_now(),
        "status": status,
        "challenge_ready": status == "CHALLENGE_READY",
        "manifest_sha256": manifest.manifest_sha256,
        "cells": cells,
    }
    draft = DockerJudgeMatrixResult.model_construct(**values, result_sha256="0" * 64)
    return DockerJudgeMatrixResult(
        **values,
        result_sha256=sha256_bytes(
            canonical_json_bytes(draft.model_dump(mode="json", exclude={"result_sha256"}))
        ),
    )


def _payload_records(root: Path, result: DockerJudgeMatrixResult) -> list[MatrixFileRecord]:
    paths = ["batch-manifest.json", "batch-result.json"]
    for cell in result.cells:
        paths.extend(f"cells/{cell.run_id}/{name}" for name in EVIDENCE_FILES)
    records: list[MatrixFileRecord] = []
    for relative in sorted(paths, key=lambda value: value.encode("utf-8")):
        path = root.joinpath(*PurePosixPath(relative).parts)
        payload = path.read_bytes()
        records.append(MatrixFileRecord(path=relative, size=len(payload), sha256=sha256_bytes(payload)))
    return records


def _write_seal(
    root: Path,
    manifest: DockerJudgeMatrixManifest,
    result: DockerJudgeMatrixResult,
) -> DockerJudgeMatrixSeal:
    records = _payload_records(root, result)
    files_bytes = b"".join(
        f"{item.sha256}  {item.path}\n".encode("utf-8") for item in records
    )
    atomic_write(root / "files.sha256", files_bytes)
    values = {
        "batch_id": manifest.batch_id,
        "file_count": len(records),
        "files_sha256": sha256_bytes(files_bytes),
        "payload_aggregate_sha256": sha256_bytes(
            canonical_json_bytes([item.model_dump(mode="json") for item in records])
        ),
        "manifest_sha256": manifest.manifest_sha256,
        "result_sha256": result.result_sha256,
    }
    draft = DockerJudgeMatrixSeal.model_construct(**values, seal_sha256="0" * 64)
    seal = DockerJudgeMatrixSeal(
        **values,
        seal_sha256=sha256_bytes(
            canonical_json_bytes(draft.model_dump(mode="json", exclude={"seal_sha256"}))
        ),
    )
    atomic_write(root / "batch-seal.json", canonical_json_bytes(seal))
    return seal


def execute_profile_r_docker_matrix(
    *,
    repository: Path,
    base_root: Path,
    source_commit: str,
    docker_executable: Path,
    run_token: str,
    source_environment: Mapping[str, str] | None = None,
    patch_backend: PatchBackend | None = None,
) -> DockerJudgeMatrixExecution:
    """Prepare, execute, classify, and seal the exact nine-cell matrix."""

    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,47}", run_token):
        raise DockerJudgeMatrixError("matrix run token is not canonical")
    repository = Path(repository).resolve(strict=True)
    parent = Path(base_root).resolve(strict=True)
    docker = Path(docker_executable).resolve(strict=True)
    environment = build_docker_controller_environment(source_environment)
    batch_id = f"profile-r-docker-matrix-{run_token}"
    root = parent / batch_id
    if root.exists():
        raise DockerJudgeMatrixError("matrix root already exists")
    root.mkdir()
    cells_root = root / "cells"
    cells_root.mkdir()
    backend = patch_backend or GitPatchBackend()
    variants = [
        _prepare_variant(
            repository=repository,
            cells_root=cells_root,
            source_commit=source_commit,
            run_token=run_token,
            ordinal=ordinal,
            variant_id=variant_id,
            patch_backend=backend,
            environment=environment,
        )
        for ordinal, variant_id in enumerate(ORDERED_VARIANTS, start=1)
    ]
    manifest = _manifest(
        batch_id=batch_id,
        source_commit=source_commit,
        docker_executable=docker,
        variants=variants,
    )
    atomic_write(root / "batch-manifest.json", canonical_json_bytes(manifest))
    cells: list[MatrixCellResult] = []
    for item in variants:
        docker_manifest, docker_result = execute_docker_judge(
            item.roots,
            docker_executable=docker,
            source_environment=environment,
            cell_id=item.plan.variant_id,
        )
        cells.append(compare_variant_result(item.plan, docker_manifest, docker_result))
    result = _result(manifest, cells)
    atomic_write(root / "batch-result.json", canonical_json_bytes(result))
    seal = _write_seal(root, manifest, result)
    verify_profile_r_docker_matrix(root)
    return DockerJudgeMatrixExecution(root=root, manifest=manifest, result=result, seal=seal)


def verify_profile_r_docker_matrix(root: Path) -> DockerJudgeMatrixResult:
    """Independently recompute every cell, batch result, and bundle seal."""

    root = Path(root).resolve(strict=True)
    manifest = DockerJudgeMatrixManifest.model_validate_json((root / "batch-manifest.json").read_bytes())
    stored_result = DockerJudgeMatrixResult.model_validate_json((root / "batch-result.json").read_bytes())
    stored_seal = DockerJudgeMatrixSeal.model_validate_json((root / "batch-seal.json").read_bytes())
    if stored_result.manifest_sha256 != manifest.manifest_sha256:
        raise DockerJudgeMatrixError("matrix result does not bind the manifest")
    cells: list[MatrixCellResult] = []
    for plan in manifest.variants:
        run_root = root / "cells" / plan.run_id
        docker_manifest = DockerJudgeManifest.model_validate_json(
            (run_root / "docker-judge-manifest.json").read_bytes()
        )
        docker_result = DockerJudgeResult.model_validate_json(
            (run_root / "docker-judge-result.json").read_bytes()
        )
        if verify_docker_judge_result(docker_manifest, docker_result) != docker_result.status:
            raise DockerJudgeMatrixError("Docker Judge cell verification failed")
        cells.append(compare_variant_result(plan, docker_manifest, docker_result))
    recomputed = _result(manifest, cells)
    stable_stored = stored_result.model_copy(update={"completed_at": recomputed.completed_at})
    if stable_stored.model_dump(mode="json", exclude={"completed_at", "result_sha256"}) != recomputed.model_dump(
        mode="json", exclude={"completed_at", "result_sha256"}
    ):
        raise DockerJudgeMatrixError("stored matrix result differs from recomputation")
    records = _payload_records(root, stored_result)
    files_bytes = b"".join(f"{item.sha256}  {item.path}\n".encode("utf-8") for item in records)
    if (root / "files.sha256").read_bytes() != files_bytes:
        raise DockerJudgeMatrixError("matrix files manifest differs from payload bytes")
    expected_values = {
        "batch_id": manifest.batch_id,
        "file_count": len(records),
        "files_sha256": sha256_bytes(files_bytes),
        "payload_aggregate_sha256": sha256_bytes(
            canonical_json_bytes([item.model_dump(mode="json") for item in records])
        ),
        "manifest_sha256": manifest.manifest_sha256,
        "result_sha256": stored_result.result_sha256,
    }
    expected_draft = DockerJudgeMatrixSeal.model_construct(**expected_values, seal_sha256="0" * 64)
    expected = DockerJudgeMatrixSeal(
        **expected_values,
        seal_sha256=sha256_bytes(
            canonical_json_bytes(expected_draft.model_dump(mode="json", exclude={"seal_sha256"}))
        ),
    )
    if expected != stored_seal:
        raise DockerJudgeMatrixError("matrix seal differs from recomputation")
    return stored_result


def qualification_projection(execution: DockerJudgeMatrixExecution) -> dict[str, Any]:
    """Return a path-free versioned summary of one verified matrix."""

    return {
        "schema_version": 1,
        "profile": "R",
        "snapshot_id": "realistic-compat-migration-001",
        "source_commit": execution.manifest.source_commit,
        "batch_id": execution.manifest.batch_id,
        "image_reference": execution.manifest.image_reference,
        "manifest_sha256": execution.manifest.manifest_sha256,
        "result_sha256": execution.result.result_sha256,
        "seal_sha256": execution.seal.seal_sha256,
        "status": execution.result.status,
        "challenge_ready": execution.result.challenge_ready,
        "model_turns": 0,
        "cells": [
            {
                "ordinal": item.ordinal,
                "variant_id": item.variant_id,
                "docker_status": item.docker_status,
                "aggregate_status": item.aggregate_status,
                "matched_expectation": item.matched_expectation,
                "docker_result_sha256": item.docker_result_sha256,
                "properties": [value.model_dump(mode="json") for value in item.properties],
            }
            for item in execution.result.cells
        ],
    }
