"""Profile R Phase F port for the already-qualified Docker property Judge.

The port snapshots the modified Worker workspace without Git/cache metadata,
prepares a protected historical Judge root, invokes the existing Docker Judge,
and writes only a path-sanitized public projection into the Cell evidence tree.
The Docker execution backend and roots factory are injected so contract tests
do not start Docker or alter protected Windows ACLs.
"""

from __future__ import annotations

import os
import re
from dataclasses import replace
from pathlib import Path
from typing import Mapping, Protocol

from benchmark_runner.realistic_docker_judge import (
    DOCKER_JUDGE_IMAGE,
    DockerExecutionBackend,
    DockerJudgeLimits,
    DockerJudgeResult,
    execute_docker_judge,
    verify_docker_judge_result,
)
from benchmark_runner.realistic_judge import (
    PreparedJudgeRoots,
    TreeFingerprint,
    fingerprint_tree,
    prepare_realistic_judge_roots,
)
from benchmark_runner.realistic_phase_f import PhaseFDispatchRequest
from benchmark_runner.realistic_phase_f_finalize import (
    PhaseFFinalizationError,
    PhaseFJudgeFile,
    PhaseFJudgeObservation,
)
from benchmark_runner.realistic_routing import canonical_json_bytes, canonical_sha256
from benchmark_runner.runner import sha256_bytes, sha256_file


_EXCLUDED_WORKER_PARTS = frozenset({".git", ".pytest_cache", "__pycache__"})


class PhaseFJudgeRootsFactory(Protocol):
    def prepare(
        self,
        *,
        repository: Path,
        base_root: Path,
        source_commit: str,
        request: PhaseFDispatchRequest,
        workspace: Path,
    ) -> PreparedJudgeRoots: ...


def _path_is_reparse(path: Path) -> bool:
    attributes = getattr(path.stat(follow_symlinks=False), "st_file_attributes", 0)
    return bool(attributes & 0x400)


def _write_new(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _copy_worker_snapshot(source: Path, target: Path) -> TreeFingerprint:
    source = source.resolve(strict=True)
    if not source.is_dir() or _path_is_reparse(source) or target.exists():
        raise PhaseFFinalizationError("Phase F Worker snapshot roots are invalid")
    target.mkdir(parents=True, exist_ok=False)
    seen: set[str] = set()
    for path in sorted(
        source.rglob("*"),
        key=lambda item: item.relative_to(source).as_posix().encode("utf-8"),
    ):
        relative = path.relative_to(source)
        if _EXCLUDED_WORKER_PARTS.intersection(relative.parts):
            continue
        if path.is_dir():
            if path.is_symlink() or _path_is_reparse(path):
                raise PhaseFFinalizationError("Worker contains a reparse directory")
            continue
        value = relative.as_posix()
        if (
            not path.is_file()
            or path.is_symlink()
            or _path_is_reparse(path)
            or "\\" in value
            or ":" in value
            or value.casefold() in seen
        ):
            raise PhaseFFinalizationError("Worker contains an unsafe file")
        seen.add(value.casefold())
        _write_new(target / relative, path.read_bytes())
    if not seen:
        raise PhaseFFinalizationError("Worker snapshot is empty")
    return fingerprint_tree(target)


class WindowsPhaseFJudgeRootsFactory:
    """Create protected J/O/S and an exact metadata-free Worker snapshot."""

    def prepare(
        self,
        *,
        repository: Path,
        base_root: Path,
        source_commit: str,
        request: PhaseFDispatchRequest,
        workspace: Path,
    ) -> PreparedJudgeRoots:
        token = f"{request.execution_ordinal:02d}-{request.request_sha256[:12]}"
        prepared = prepare_realistic_judge_roots(
            repository=repository,
            base_root=base_root,
            source_commit=source_commit,
            run_token=token,
            run_label="phase-f-profile-r",
        )
        observed_worker = prepared.run_root / "worker-observed"
        observed = _copy_worker_snapshot(workspace, observed_worker)
        return replace(prepared, W=observed_worker, worker_source=observed)


def _failed_property_ids(result: DockerJudgeResult) -> list[str]:
    payload = result.checker_payload
    if not isinstance(payload, dict):
        return []
    properties = payload.get("properties")
    if not isinstance(properties, list):
        return []
    values: list[str] = []
    for item in properties:
        if not isinstance(item, dict) or item.get("status") != "fail":
            continue
        property_id = item.get("property_id")
        if isinstance(property_id, str) and property_id:
            values.append(property_id)
    return sorted(set(values))


def _public_files(root: Path) -> list[PhaseFJudgeFile]:
    return [
        PhaseFJudgeFile(
            path=path.relative_to(root).as_posix(),
            size=path.stat().st_size,
            sha256=sha256_file(path),
        )
        for path in sorted(
            (item for item in root.rglob("*") if item.is_file()),
            key=lambda item: item.relative_to(root).as_posix().encode("utf-8"),
        )
    ]


class PhaseFDockerJudgePort:
    """Run one Profile R Docker Judge and return a sanitized typed observation."""

    def __init__(
        self,
        *,
        repository: Path,
        raw_root: Path,
        source_commit: str,
        docker_executable: Path,
        execution_backend: DockerExecutionBackend,
        source_environment: Mapping[str, str],
        limits: DockerJudgeLimits | None = None,
        roots_factory: PhaseFJudgeRootsFactory | None = None,
    ) -> None:
        self.repository = repository.resolve(strict=True)
        self.raw_root = raw_root.resolve()
        if self.raw_root == self.repository or self.raw_root.is_relative_to(self.repository):
            raise PhaseFFinalizationError("Docker Judge raw root must be outside Git")
        if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
            raise PhaseFFinalizationError("Docker Judge source commit is invalid")
        self.source_commit = source_commit
        self.docker_executable = docker_executable.resolve(strict=True)
        self.execution_backend = execution_backend
        self.source_environment = source_environment
        self.limits = limits
        self.roots_factory = roots_factory or WindowsPhaseFJudgeRootsFactory()

    def run(
        self,
        *,
        workspace: Path,
        output_root: Path,
        request: PhaseFDispatchRequest,
    ) -> PhaseFJudgeObservation:
        if request.fixture_id != "realistic-compat-migration-001":
            raise PhaseFFinalizationError("Docker Judge port only accepts Profile R")
        if not workspace.resolve(strict=True).is_dir() or output_root.exists():
            raise PhaseFFinalizationError("Docker Judge Cell roots are invalid")
        self.raw_root.mkdir(parents=True, exist_ok=True)
        prepared = self.roots_factory.prepare(
            repository=self.repository,
            base_root=self.raw_root,
            source_commit=self.source_commit,
            request=request,
            workspace=workspace,
        )
        manifest, result = execute_docker_judge(
            prepared,
            docker_executable=self.docker_executable,
            backend=self.execution_backend,
            source_environment=self.source_environment,
            limits=self.limits,
            cell_id=f"phase-f-r-{request.execution_ordinal}-{request.variant_id}",
        )
        status = verify_docker_judge_result(manifest, result)
        failed = _failed_property_ids(result)
        if status == "CHECKS_PASSED":
            public_status = "CHECKS_PASSED"
        elif status == "CHECKS_FAILED":
            public_status = "CHECKS_FAILED"
        elif status == "CHALLENGE_INVALID":
            public_status = "CHALLENGE_INVALID"
        else:
            public_status = "JUDGE_RUNTIME_ERROR"
        if public_status == "CHECKS_FAILED" and not failed:
            raise PhaseFFinalizationError("Docker Judge failure lacks a failed property")

        raw_manifest_sha256 = sha256_bytes(canonical_json_bytes(manifest))
        raw_result_sha256 = result.result_sha256
        output_root.mkdir(parents=True, exist_ok=False)
        public_manifest = {
            "schema_version": 1,
            "kind": "phase_f_docker_judge_public_manifest",
            "cell_id": request.cell_id,
            "source_commit": self.source_commit,
            "image_reference": DOCKER_JUDGE_IMAGE,
            "docker_executable_sha256": manifest.docker_executable_sha256,
            "checker_sha256": manifest.checker_sha256,
            "command_sha256": manifest.command_sha256,
            "network_mode": manifest.network_mode,
            "root_filesystem_read_only": manifest.root_filesystem_read_only,
            "all_capabilities_dropped": manifest.all_capabilities_dropped,
            "S_mounted": manifest.S_mounted,
            "worker_before_sha256": manifest.W_before.aggregate_sha256,
            "judge_before_sha256": manifest.J_before.aggregate_sha256,
            "raw_manifest_sha256": raw_manifest_sha256,
            "model_turns": 0,
        }
        public_result = {
            "schema_version": 1,
            "kind": "phase_f_docker_judge_public_result",
            "cell_id": request.cell_id,
            "status": public_status,
            "check_success": public_status == "CHECKS_PASSED",
            "failed_property_ids": failed,
            "reason_codes": result.reason_codes,
            "process": result.process.model_dump(mode="json"),
            "checker_payload_sha256": (
                sha256_bytes(canonical_json_bytes(result.checker_payload))
                if result.checker_payload is not None
                else None
            ),
            "worker_after_sha256": result.W_after.aggregate_sha256,
            "judge_after_sha256": result.J_after.aggregate_sha256,
            "output_after_sha256": result.O_after.aggregate_sha256,
            "raw_result_sha256": raw_result_sha256,
            "model_turns": 0,
        }
        _write_new(output_root / "manifest.json", canonical_json_bytes(public_manifest))
        _write_new(output_root / "result.json", canonical_json_bytes(public_result))
        files = _public_files(output_root)
        values = {
            "schema_version": 1,
            "kind": "phase_f_realistic_judge_observation",
            "status": public_status,
            "judge_kind": "docker_property",
            "docker_executed": True,
            "actual_model_turns": 0,
            "check_success": public_status == "CHECKS_PASSED",
            "failed_property_ids": failed,
            "duration_seconds": result.process.stream.duration_ms / 1000,
            "raw_manifest_sha256": raw_manifest_sha256,
            "raw_result_sha256": raw_result_sha256,
            "files": [item.model_dump(mode="json") for item in files],
        }
        return PhaseFJudgeObservation(
            **values,
            observation_sha256=canonical_sha256(values),
        )
