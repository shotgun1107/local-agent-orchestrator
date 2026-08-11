"""Model-free Docker execution backend for the Profile R property Judge.

The Controller prepares frozen W/J/O/S roots with :mod:`realistic_judge`.
This module exposes only W and J read-only, exposes O read/write, never mounts
S, disables container networking, and classifies the checker outcome without
turning an expected property failure into an infrastructure failure.
"""

from __future__ import annotations

import hashlib
import json
import os
import queue
import re
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Mapping, NoReturn, Protocol, Sequence

from pydantic import Field, model_validator

from benchmark_runner.contract import Sha256, StrictModel, utc_now, validate_timestamp
from benchmark_runner.realistic_judge import (
    API_KEY_ENVIRONMENT_NAMES,
    CHECKER_RELATIVE_PATH,
    SNAPSHOT_ID,
    PreparedJudgeRoots,
    StreamRecord,
    TreeFingerprint,
    fingerprint_tree,
)
from benchmark_runner.runner import atomic_write, canonical_json_bytes, sha256_bytes, sha256_file


DOCKER_JUDGE_IMAGE = (
    "local-agent-orchestrator/profile-r-judge@sha256:"
    "fc6b0d42a14a88ccc23d9d5787913915feae988027a1c36926dfdf78493fbf98"
)
DOCKER_JUDGE_DOCKERFILE_SHA256 = "e923029fe5f20c3e01f4d1da27d5cbfc40f0899658251455274c85b8b6e3b1c1"
DOCKER_JUDGE_REQUIREMENTS_SHA256 = "0fe996a5674c46d85b217d8579c10d4b1d24a801de01b11d9814cf095b7dc07b"
DOCKER_CONTROLLER_ENVIRONMENT_ALLOWLIST = frozenset(
    {
        "APPDATA",
        "COMSPEC",
        "DOCKER_CONFIG",
        "DOCKER_CONTEXT",
        "DOCKER_HOST",
        "LOCALAPPDATA",
        "PATH",
        "PATHEXT",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "USERPROFILE",
        "WINDIR",
    }
)
CONTAINER_CHECKER_PATH = "/judge/checker/check_properties.py"
CONTAINER_W = "/workspace"
CONTAINER_J = "/judge"
CONTAINER_O = "/output"


class DockerJudgeError(RuntimeError):
    """Raised when a Docker Judge invocation cannot be constructed safely."""


class DockerJudgeLimits(StrictModel):
    timeout_seconds: int = Field(default=180, ge=1, le=600)
    cleanup_timeout_seconds: int = Field(default=15, ge=1, le=60)
    stdout_limit_bytes: int = Field(default=1_048_576, ge=1024, le=1_048_576)
    memory_megabytes: int = Field(default=512, ge=128, le=4096)
    cpus: int = Field(default=1, ge=1, le=8)
    pids_limit: int = Field(default=64, ge=16, le=512)
    tmpfs_megabytes: int = Field(default=32, ge=8, le=256)


class DockerJudgeMount(StrictModel):
    role: Literal["W", "J", "O"]
    host_path: str = Field(min_length=3)
    container_path: Literal["/workspace", "/judge", "/output"]
    read_only: bool

    @model_validator(mode="after")
    def mount_is_canonical(self) -> "DockerJudgeMount":
        expected = {
            "W": (CONTAINER_W, True),
            "J": (CONTAINER_J, True),
            "O": (CONTAINER_O, False),
        }[self.role]
        if (self.container_path, self.read_only) != expected:
            raise ValueError("Docker Judge mount role does not match its frozen access")
        path = Path(self.host_path)
        if not path.is_absolute() or "," in self.host_path:
            raise ValueError("Docker Judge host mount path is unsafe")
        return self


class DockerJudgeManifest(StrictModel):
    schema_version: Literal[1] = 1
    snapshot_id: Literal[SNAPSHOT_ID] = SNAPSHOT_ID
    run_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,119}$")
    created_at: datetime
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    docker_executable: str = Field(min_length=3)
    docker_executable_sha256: Sha256
    image_reference: Literal[DOCKER_JUDGE_IMAGE] = DOCKER_JUDGE_IMAGE
    image_dockerfile_sha256: Literal[DOCKER_JUDGE_DOCKERFILE_SHA256] = DOCKER_JUDGE_DOCKERFILE_SHA256
    image_requirements_sha256: Literal[DOCKER_JUDGE_REQUIREMENTS_SHA256] = DOCKER_JUDGE_REQUIREMENTS_SHA256
    container_name: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,119}$")
    network_mode: Literal["none"] = "none"
    root_filesystem_read_only: Literal[True] = True
    all_capabilities_dropped: Literal[True] = True
    no_new_privileges: Literal[True] = True
    non_root_user: Literal["65532:65532"] = "65532:65532"
    S_mounted: Literal[False] = False
    mounts: list[DockerJudgeMount] = Field(min_length=3, max_length=3)
    checker_relative_path: Literal[CHECKER_RELATIVE_PATH] = CHECKER_RELATIVE_PATH
    checker_sha256: Sha256
    environment_name_allowlist: list[str]
    api_key_environment_names_present: list[str] = Field(max_length=0)
    limits: DockerJudgeLimits
    W_before: TreeFingerprint
    J_before: TreeFingerprint
    O_before: TreeFingerprint
    command: list[str] = Field(min_length=1)
    command_sha256: Sha256

    @model_validator(mode="after")
    def manifest_is_canonical(self) -> "DockerJudgeManifest":
        validate_timestamp(self.created_at)
        roles = [mount.role for mount in self.mounts]
        if roles != ["W", "J", "O"]:
            raise ValueError("Docker Judge mounts must be ordered W, J, O")
        if self.O_before.file_count != 0:
            raise ValueError("Docker Judge output root must start empty")
        if self.environment_name_allowlist != sorted(set(self.environment_name_allowlist)):
            raise ValueError("Docker environment allowlist must be sorted and unique")
        if self.command_sha256 != sha256_bytes(canonical_json_bytes(self.command)):
            raise ValueError("Docker Judge command SHA-256 mismatch")
        required_pairs = (
            ("--pull", "never"),
            ("--network", "none"),
            ("--user", "65532:65532"),
        )
        for flag, value in required_pairs:
            if flag not in self.command or self.command[self.command.index(flag) + 1] != value:
                raise ValueError(f"Docker Judge command is missing {flag} {value}")
        for flag in ("--read-only", "--cap-drop", "--security-opt"):
            if flag not in self.command:
                raise ValueError(f"Docker Judge command is missing {flag}")
        if "/state" in self.command or any("/state" in value for value in self.command):
            raise ValueError("Docker Judge command exposes S")
        if self.command[-9:-1] != [
            "python",
            "-P",
            CONTAINER_CHECKER_PATH,
            "--workspace",
            CONTAINER_W,
            "--experiment-id",
            "phase-d-profile-r-docker",
            "--cell-id",
        ] or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,119}", self.command[-1]):
            # The final cell ID is run-specific, while every preceding checker
            # argument is frozen.  A clearer exact reconstruction is performed
            # by verify_docker_judge_manifest below.
            raise ValueError("Docker Judge checker command suffix is invalid")
        return self


class DockerProcessRecord(StrictModel):
    started: bool
    exit_code: int | None
    timed_out: bool
    start_error_kind: str | None
    cleanup_attempted: bool
    cleanup_succeeded: bool | None
    stream: StreamRecord

    @model_validator(mode="after")
    def process_state_is_coherent(self) -> "DockerProcessRecord":
        if not self.started:
            if self.exit_code is not None or self.timed_out or self.start_error_kind is None:
                raise ValueError("Docker start failure record is incoherent")
        elif self.start_error_kind is not None:
            raise ValueError("started Docker process cannot have a start error")
        if self.timed_out and not self.cleanup_attempted:
            raise ValueError("timed-out Docker process must attempt cleanup")
        if self.cleanup_attempted != (self.cleanup_succeeded is not None):
            raise ValueError("Docker cleanup result presence mismatch")
        return self


DockerJudgeStatus = Literal[
    "CHECKS_PASSED",
    "CHECKS_FAILED",
    "JUDGE_TIMED_OUT",
    "JUDGE_RUNTIME_ERROR",
    "CHALLENGE_INVALID",
]


class DockerJudgeResult(StrictModel):
    schema_version: Literal[1] = 1
    snapshot_id: Literal[SNAPSHOT_ID] = SNAPSHOT_ID
    run_id: str = Field(min_length=1)
    completed_at: datetime
    status: DockerJudgeStatus
    manifest_sha256: Sha256
    process: DockerProcessRecord
    checker_payload: dict[str, Any] | None
    W_after: TreeFingerprint
    J_after: TreeFingerprint
    O_after: TreeFingerprint
    reason_codes: list[str]
    result_sha256: Sha256

    @model_validator(mode="after")
    def result_is_canonical(self) -> "DockerJudgeResult":
        validate_timestamp(self.completed_at)
        if self.reason_codes != sorted(set(self.reason_codes)):
            raise ValueError("Docker Judge reason codes must be sorted and unique")
        payload = self.model_dump(mode="json", exclude={"result_sha256"})
        if self.result_sha256 != sha256_bytes(canonical_json_bytes(payload)):
            raise ValueError("Docker Judge result SHA-256 mismatch")
        return self


@dataclass(frozen=True)
class DockerRawExecution:
    started: bool
    exit_code: int | None
    stdout: bytes
    stdout_total: int
    stdout_sha256: str
    stderr: bytes
    stderr_total: int
    stderr_sha256: str
    duration_ms: int
    timed_out: bool = False
    start_error_kind: str | None = None
    cleanup_attempted: bool = False
    cleanup_succeeded: bool | None = None


class DockerExecutionBackend(Protocol):
    def execute(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        environment: Mapping[str, str],
        timeout_seconds: int,
        cleanup_timeout_seconds: int,
        limit: int,
        container_name: str,
    ) -> DockerRawExecution: ...


def _drain_stream(
    stream: Any,
    *,
    limit: int,
    destination: queue.Queue[tuple[bytes, int, str]],
) -> NoReturn:
    captured = bytearray()
    total = 0
    digest = hashlib.sha256()
    try:
        while True:
            chunk = stream.read(8192)
            if not chunk:
                break
            total += len(chunk)
            digest.update(chunk)
            if len(captured) < limit + 1:
                captured.extend(chunk[: limit + 1 - len(captured)])
    finally:
        destination.put((bytes(captured), total, digest.hexdigest()))


class SubprocessDockerExecutionBackend:
    """Concrete Docker CLI backend with bounded streams and timeout cleanup."""

    def execute(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        environment: Mapping[str, str],
        timeout_seconds: int,
        cleanup_timeout_seconds: int,
        limit: int,
        container_name: str,
    ) -> DockerRawExecution:
        started_at = time.monotonic()
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        try:
            process = subprocess.Popen(
                list(command),
                cwd=cwd,
                env=dict(environment),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creationflags,
            )
        except OSError as exc:
            empty_hash = sha256_bytes(b"")
            return DockerRawExecution(
                started=False,
                exit_code=None,
                stdout=b"",
                stdout_total=0,
                stdout_sha256=empty_hash,
                stderr=b"",
                stderr_total=0,
                stderr_sha256=empty_hash,
                duration_ms=int((time.monotonic() - started_at) * 1000),
                start_error_kind=type(exc).__name__,
            )
        if process.stdout is None or process.stderr is None:
            process.kill()
            raise DockerJudgeError("Docker process streams were not created")
        stdout_queue: queue.Queue[tuple[bytes, int, str]] = queue.Queue(maxsize=1)
        stderr_queue: queue.Queue[tuple[bytes, int, str]] = queue.Queue(maxsize=1)
        stdout_thread = threading.Thread(
            target=_drain_stream,
            kwargs={"stream": process.stdout, "limit": limit, "destination": stdout_queue},
            daemon=True,
        )
        stderr_thread = threading.Thread(
            target=_drain_stream,
            kwargs={"stream": process.stderr, "limit": limit, "destination": stderr_queue},
            daemon=True,
        )
        stdout_thread.start()
        stderr_thread.start()
        timed_out = False
        cleanup_attempted = False
        cleanup_succeeded: bool | None = None
        try:
            exit_code = process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass
            cleanup_attempted = True
            try:
                cleanup = subprocess.run(
                    [command[0], "rm", "--force", "--volumes", container_name],
                    cwd=cwd,
                    env=dict(environment),
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    timeout=cleanup_timeout_seconds,
                    creationflags=creationflags,
                )
                cleanup_succeeded = cleanup.returncode == 0 or b"No such container" in cleanup.stderr
            except (OSError, subprocess.TimeoutExpired):
                cleanup_succeeded = False
            exit_code = None
        stdout_thread.join(timeout=2)
        stderr_thread.join(timeout=2)
        if stdout_thread.is_alive() or stderr_thread.is_alive():
            raise DockerJudgeError("Docker stream collector did not stop")
        stdout, stdout_total, stdout_hash = stdout_queue.get_nowait()
        stderr, stderr_total, stderr_hash = stderr_queue.get_nowait()
        return DockerRawExecution(
            started=True,
            exit_code=exit_code,
            stdout=stdout,
            stdout_total=stdout_total,
            stdout_sha256=stdout_hash,
            stderr=stderr,
            stderr_total=stderr_total,
            stderr_sha256=stderr_hash,
            duration_ms=int((time.monotonic() - started_at) * 1000),
            timed_out=timed_out,
            cleanup_attempted=cleanup_attempted,
            cleanup_succeeded=cleanup_succeeded,
        )


def build_docker_controller_environment(
    source: Mapping[str, str] | None = None,
) -> dict[str, str]:
    values = os.environ if source is None else source
    names = {str(name).upper() for name in values.keys()}
    present = sorted(names.intersection(API_KEY_ENVIRONMENT_NAMES))
    if present:
        raise DockerJudgeError(
            "Docker Judge Controller environment contains an API-key name: "
            + ",".join(present)
        )
    environment = {
        name: values[name]
        for name in sorted(DOCKER_CONTROLLER_ENVIRONMENT_ALLOWLIST)
        if name in values
    }
    if os.name == "nt" and "SYSTEMROOT" not in environment:
        raise DockerJudgeError("Docker Judge Controller environment lacks SYSTEMROOT")
    return environment


def _mount_argument(mount: DockerJudgeMount) -> str:
    value = (
        f"type=bind,source={mount.host_path},target={mount.container_path}"
    )
    return value + (",readonly" if mount.read_only else "")


def build_docker_judge_command(
    *,
    docker_executable: Path,
    container_name: str,
    mounts: Sequence[DockerJudgeMount],
    limits: DockerJudgeLimits,
    cell_id: str,
) -> list[str]:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,119}", container_name):
        raise DockerJudgeError("Docker container name is not canonical")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,119}", cell_id):
        raise DockerJudgeError("Docker Judge cell ID is not canonical")
    command = [
        str(Path(docker_executable).resolve(strict=True)),
        "run",
        "--rm",
        "--pull",
        "never",
        "--name",
        container_name,
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        str(limits.pids_limit),
        "--memory",
        f"{limits.memory_megabytes}m",
        "--cpus",
        str(limits.cpus),
        "--user",
        "65532:65532",
    ]
    for mount in mounts:
        command.extend(["--mount", _mount_argument(mount)])
    command.extend(
        [
            "--tmpfs",
            f"/tmp:rw,noexec,nosuid,size={limits.tmpfs_megabytes}m",
            "--workdir",
            CONTAINER_O,
            "--env",
            "PYTHONDONTWRITEBYTECODE=1",
            "--env",
            "PYTHONIOENCODING=utf-8",
            "--env",
            "PYTHONUTF8=1",
            DOCKER_JUDGE_IMAGE,
            "python",
            "-P",
            CONTAINER_CHECKER_PATH,
            "--workspace",
            CONTAINER_W,
            "--experiment-id",
            "phase-d-profile-r-docker",
            "--cell-id",
            cell_id,
        ]
    )
    return command


def create_docker_judge_manifest(
    prepared: PreparedJudgeRoots,
    *,
    docker_executable: Path,
    limits: DockerJudgeLimits | None = None,
    cell_id: str | None = None,
) -> DockerJudgeManifest:
    limits = limits or DockerJudgeLimits()
    executable = Path(docker_executable).resolve(strict=True)
    checker = prepared.J / CHECKER_RELATIVE_PATH
    if not checker.is_file():
        raise DockerJudgeError("runtime J is missing the Profile R checker")
    if any("," in str(path.resolve()) for path in (prepared.W, prepared.J, prepared.O)):
        raise DockerJudgeError("Docker Judge mount path contains a comma")
    mounts = [
        DockerJudgeMount(role="W", host_path=str(prepared.W.resolve()), container_path=CONTAINER_W, read_only=True),
        DockerJudgeMount(role="J", host_path=str(prepared.J.resolve()), container_path=CONTAINER_J, read_only=True),
        DockerJudgeMount(role="O", host_path=str(prepared.O.resolve()), container_path=CONTAINER_O, read_only=False),
    ]
    container_name = f"lao-{prepared.run_root.name}"
    cell_id = cell_id or f"pristine-{prepared.run_root.name[-24:]}"
    command = build_docker_judge_command(
        docker_executable=executable,
        container_name=container_name,
        mounts=mounts,
        limits=limits,
        cell_id=cell_id,
    )
    return DockerJudgeManifest(
        run_id=prepared.run_root.name,
        created_at=utc_now(),
        source_commit=prepared.source_commit,
        docker_executable=str(executable),
        docker_executable_sha256=sha256_file(executable),
        container_name=container_name,
        mounts=mounts,
        checker_sha256=sha256_file(checker),
        environment_name_allowlist=sorted(DOCKER_CONTROLLER_ENVIRONMENT_ALLOWLIST),
        api_key_environment_names_present=[],
        limits=limits,
        W_before=fingerprint_tree(prepared.W),
        J_before=fingerprint_tree(prepared.J),
        O_before=fingerprint_tree(prepared.O),
        command=command,
        command_sha256=sha256_bytes(canonical_json_bytes(command)),
    )


def verify_docker_judge_manifest(manifest: DockerJudgeManifest) -> None:
    expected = build_docker_judge_command(
        docker_executable=Path(manifest.docker_executable),
        container_name=manifest.container_name,
        mounts=manifest.mounts,
        limits=manifest.limits,
        cell_id=manifest.command[-1],
    )
    if manifest.command != expected:
        raise DockerJudgeError("Docker Judge command differs from its frozen fields")
    if sha256_file(Path(manifest.docker_executable)) != manifest.docker_executable_sha256:
        raise DockerJudgeError("Docker executable bytes drifted")


def _stream_record(raw: DockerRawExecution, limit: int) -> StreamRecord:
    return StreamRecord(
        exit_code=raw.exit_code if raw.exit_code is not None else -1,
        stdout_size=raw.stdout_total,
        stdout_sha256=raw.stdout_sha256,
        stdout_truncated=raw.stdout_total > limit,
        stderr_size=raw.stderr_total,
        stderr_sha256=raw.stderr_sha256,
        stderr_truncated=raw.stderr_total > limit,
        duration_ms=raw.duration_ms,
    )


def _process_record(raw: DockerRawExecution, limit: int) -> DockerProcessRecord:
    return DockerProcessRecord(
        started=raw.started,
        exit_code=raw.exit_code,
        timed_out=raw.timed_out,
        start_error_kind=raw.start_error_kind,
        cleanup_attempted=raw.cleanup_attempted,
        cleanup_succeeded=raw.cleanup_succeeded,
        stream=_stream_record(raw, limit),
    )


def _decode_checker_payload(raw: DockerRawExecution, limit: int) -> dict[str, Any] | None:
    if raw.stdout_total > limit:
        return None
    try:
        value = json.loads(raw.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _derive_result(
    manifest: DockerJudgeManifest,
    *,
    process: DockerProcessRecord,
    checker_payload: dict[str, Any] | None,
    W_after: TreeFingerprint,
    J_after: TreeFingerprint,
    O_after: TreeFingerprint,
) -> tuple[DockerJudgeStatus, list[str]]:
    codes: list[str] = []
    if W_after != manifest.W_before:
        codes.append("W_MUTATED")
    if J_after != manifest.J_before:
        codes.append("J_MUTATED")
    if O_after.file_count != 0:
        codes.append("O_UNEXPECTED_OUTPUT")
    if not process.started:
        codes.append("DOCKER_START_FAILED")
    if process.timed_out:
        codes.append("DOCKER_TIMEOUT")
    if process.started and not process.timed_out and process.exit_code not in {0, 1}:
        codes.append("DOCKER_EXIT_UNEXPECTED")
    if process.cleanup_attempted and process.cleanup_succeeded is not True:
        codes.append("DOCKER_CLEANUP_FAILED")
    if process.stream.stdout_truncated:
        codes.append("CHECKER_STDOUT_LIMIT_EXCEEDED")
    if process.stream.stderr_truncated:
        codes.append("CHECKER_STDERR_LIMIT_EXCEEDED")

    typed_outcome: Literal["pass", "fail"] | None = None
    if process.started and not process.timed_out and not process.stream.stdout_truncated:
        if checker_payload is None:
            codes.append("CHECKER_RESULT_INVALID")
        else:
            if checker_payload.get("checker_run_status") != "completed":
                codes.append("CHECKER_RUN_STATUS_INVALID")
            if checker_payload.get("workspace_mutated") is not False:
                codes.append("CHECKER_REPORTED_WORKSPACE_MUTATION")
            aggregate = checker_payload.get("aggregate_status")
            if aggregate in {"pass", "fail"}:
                typed_outcome = aggregate
            else:
                codes.append("CHECKER_AGGREGATE_STATUS_INVALID")
            expected_exit = {"pass": 0, "fail": 1}.get(typed_outcome)
            if expected_exit is None or process.exit_code != expected_exit:
                codes.append("CHECKER_EXIT_STATUS_MISMATCH")

    codes = sorted(set(codes))
    if any(code in codes for code in ("W_MUTATED", "J_MUTATED", "O_UNEXPECTED_OUTPUT", "CHECKER_REPORTED_WORKSPACE_MUTATION")):
        return "CHALLENGE_INVALID", codes
    if "DOCKER_CLEANUP_FAILED" in codes:
        return "JUDGE_RUNTIME_ERROR", codes
    if process.timed_out:
        return "JUDGE_TIMED_OUT", codes
    if codes:
        return "JUDGE_RUNTIME_ERROR", codes
    return ("CHECKS_PASSED", []) if typed_outcome == "pass" else ("CHECKS_FAILED", ["CHECKS_FAILED"])


def execute_docker_judge(
    prepared: PreparedJudgeRoots,
    *,
    docker_executable: Path,
    backend: DockerExecutionBackend | None = None,
    source_environment: Mapping[str, str] | None = None,
    limits: DockerJudgeLimits | None = None,
    cell_id: str | None = None,
) -> tuple[DockerJudgeManifest, DockerJudgeResult]:
    """Run one frozen Docker Judge invocation and always persist typed evidence."""

    manifest = create_docker_judge_manifest(
        prepared,
        docker_executable=docker_executable,
        limits=limits,
        cell_id=cell_id,
    )
    verify_docker_judge_manifest(manifest)
    environment = build_docker_controller_environment(source_environment)
    manifest_sha = sha256_bytes(canonical_json_bytes(manifest))
    atomic_write(
        prepared.run_root / "docker-judge-manifest.json",
        canonical_json_bytes(manifest),
    )
    executor = backend or SubprocessDockerExecutionBackend()
    raw = executor.execute(
        manifest.command,
        cwd=prepared.O,
        environment=environment,
        timeout_seconds=manifest.limits.timeout_seconds,
        cleanup_timeout_seconds=manifest.limits.cleanup_timeout_seconds,
        limit=manifest.limits.stdout_limit_bytes,
        container_name=manifest.container_name,
    )
    atomic_write(prepared.run_root / "docker-judge.stdout.bin", raw.stdout)
    atomic_write(prepared.run_root / "docker-judge.stderr.bin", raw.stderr)
    process = _process_record(raw, manifest.limits.stdout_limit_bytes)
    atomic_write(
        prepared.run_root / "docker-judge-process.json",
        canonical_json_bytes(process),
    )
    checker_payload = _decode_checker_payload(raw, manifest.limits.stdout_limit_bytes)
    W_after = fingerprint_tree(prepared.W)
    J_after = fingerprint_tree(prepared.J)
    O_after = fingerprint_tree(prepared.O)
    status, codes = _derive_result(
        manifest,
        process=process,
        checker_payload=checker_payload,
        W_after=W_after,
        J_after=J_after,
        O_after=O_after,
    )
    values = {
        "run_id": manifest.run_id,
        "completed_at": utc_now(),
        "status": status,
        "manifest_sha256": manifest_sha,
        "process": process,
        "checker_payload": checker_payload,
        "W_after": W_after,
        "J_after": J_after,
        "O_after": O_after,
        "reason_codes": codes,
    }
    draft = DockerJudgeResult.model_construct(**values, result_sha256="0" * 64)
    result = DockerJudgeResult(
        **values,
        result_sha256=sha256_bytes(
            canonical_json_bytes(draft.model_dump(mode="json", exclude={"result_sha256"}))
        ),
    )
    atomic_write(
        prepared.run_root / "docker-judge-result.json",
        canonical_json_bytes(result),
    )
    return manifest, result


def verify_docker_judge_result(
    manifest: DockerJudgeManifest,
    result: DockerJudgeResult,
) -> DockerJudgeStatus:
    verify_docker_judge_manifest(manifest)
    if result.run_id != manifest.run_id:
        raise DockerJudgeError("Docker Judge manifest/result run ID mismatch")
    if result.manifest_sha256 != sha256_bytes(canonical_json_bytes(manifest)):
        raise DockerJudgeError("Docker Judge result does not bind its manifest")
    if result.result_sha256 != sha256_bytes(
        canonical_json_bytes(result.model_dump(mode="json", exclude={"result_sha256"}))
    ):
        raise DockerJudgeError("Docker Judge result self-hash mismatch")
    expected_status, expected_codes = _derive_result(
        manifest,
        process=result.process,
        checker_payload=result.checker_payload,
        W_after=result.W_after,
        J_after=result.J_after,
        O_after=result.O_after,
    )
    if result.status != expected_status or result.reason_codes != expected_codes:
        raise DockerJudgeError("Docker Judge stored classification is not reproducible")
    return result.status
