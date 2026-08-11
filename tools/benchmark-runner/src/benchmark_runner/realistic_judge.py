"""Profile R protected Judge boundary preparation and model-free verification.

This module never dispatches a model turn.  It extracts W and the versioned J
source from frozen Git objects, creates fresh W/J/O/S runtime roots, invokes the
existing runtime-boundary probe through ``codex sandbox``, and independently
recomputes the filesystem/no-network result.
"""

from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Literal, Mapping, Sequence

from pydantic import Field, model_validator

from benchmark_runner.contract import Sha256, StrictModel, utc_now, validate_timestamp
from benchmark_runner.runner import atomic_write, canonical_json_bytes, sha256_bytes, sha256_file
from benchmark_runner.runtime_boundary import (
    DEFAULT_ENVIRONMENT_NAME_ALLOWLIST,
    RootIdentity,
    RuntimeBoundaryError,
    RuntimeIdentity,
    _harden_controller_only_directory,
    _run_command_capped,
    _toml_basic_string,
    build_sanitized_environment,
    capture_windows_root_identity,
    resolve_pinned_runtime_identity,
    verify_pinned_runtime_identity,
)


SNAPSHOT_ID = "realistic-compat-migration-001"
PROFILE_ID = "realistic-property-judge-v1"
WORKER_PREFIX = (
    "benchmarks/fixtures/routing-realistic-high-difficulty-v1/"
    f"{SNAPSHOT_ID}/workspace"
)
JUDGE_SOURCE_PREFIX = (
    "benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/"
    f"{SNAPSHOT_ID}"
)
PROBE_RELATIVE_PATH = "checker/probe_runtime_boundary.py"
CHECKER_RELATIVE_PATH = "checker/check_properties.py"
API_KEY_ENVIRONMENT_NAMES = frozenset({"OPENAI_API_KEY", "CODEX_API_KEY"})


class RealisticJudgeError(RuntimeError):
    """Raised when the protected Judge boundary cannot be proven."""


class TreeFileRecord(StrictModel):
    path: str = Field(min_length=1)
    size: int = Field(ge=0)
    sha256: Sha256
    git_blob_oid: str | None = Field(default=None, pattern=r"^[0-9a-f]{40}$")


class TreeFingerprint(StrictModel):
    file_count: int = Field(ge=0)
    files: list[TreeFileRecord]
    aggregate_sha256: Sha256

    @model_validator(mode="after")
    def fingerprint_is_canonical(self) -> "TreeFingerprint":
        paths = [item.path for item in self.files]
        if paths != sorted(set(paths), key=lambda value: value.encode("utf-8")):
            raise ValueError("tree paths must be byte-sorted and unique")
        if self.file_count != len(self.files):
            raise ValueError("tree file count mismatch")
        expected = sha256_bytes(
            canonical_json_bytes([item.model_dump(mode="json") for item in self.files])
        )
        if self.aggregate_sha256 != expected:
            raise ValueError("tree aggregate SHA-256 mismatch")
        return self


class SourceRuntimeBinding(StrictModel):
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    source_tree_oid: str = Field(pattern=r"^[0-9a-f]{40}$")
    source: TreeFingerprint
    runtime: TreeFingerprint
    source_runtime_relative_paths_equal: Literal[True]
    source_runtime_bytes_equal: Literal[True]
    runtime_root_identity_sha256: Sha256
    runtime_parent_identity_sha256: Sha256
    binding_sha256: Sha256

    @model_validator(mode="after")
    def binding_is_canonical(self) -> "SourceRuntimeBinding":
        if self.source != self.runtime:
            raise ValueError("J source and runtime fingerprints differ")
        payload = self.model_dump(mode="json", exclude={"binding_sha256"})
        if self.binding_sha256 != sha256_bytes(canonical_json_bytes(payload)):
            raise ValueError("J source/runtime binding SHA-256 mismatch")
        return self


class JudgeBoundaryManifest(StrictModel):
    schema_version: Literal[1] = 1
    snapshot_id: Literal[SNAPSHOT_ID] = SNAPSHOT_ID
    run_id: str = Field(min_length=1)
    created_at: datetime
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    runtime: RuntimeIdentity
    permission_profile_id: Literal[PROFILE_ID] = PROFILE_ID
    config_overrides: list[str]
    environment_name_allowlist: list[str]
    api_key_environment_names_present: list[str] = Field(max_length=0)
    python_executable: str = Field(min_length=1)
    python_executable_sha256: Sha256
    probe_relative_path: Literal[PROBE_RELATIVE_PATH] = PROBE_RELATIVE_PATH
    probe_sha256: Sha256
    checker_relative_path: Literal[CHECKER_RELATIVE_PATH] = CHECKER_RELATIVE_PATH
    checker_sha256: Sha256
    W: RootIdentity
    J: RootIdentity
    O: RootIdentity
    S: RootIdentity
    W_before: TreeFingerprint
    J_before: TreeFingerprint
    O_before: TreeFingerprint
    S_before: TreeFingerprint
    worker_source_tree_oid: str = Field(pattern=r"^[0-9a-f]{40}$")
    worker_source: TreeFingerprint
    j_source_runtime_binding: SourceRuntimeBinding
    command: list[str] = Field(min_length=1)
    command_sha256: Sha256
    timeout_seconds: int = Field(ge=1, le=600)
    stdout_limit_bytes: int = Field(ge=1024, le=1_048_576)

    @model_validator(mode="after")
    def manifest_is_canonical(self) -> "JudgeBoundaryManifest":
        validate_timestamp(self.created_at)
        if self.environment_name_allowlist != sorted(
            set(self.environment_name_allowlist)
        ):
            raise ValueError("environment allowlist must be sorted and unique")
        if self.command_sha256 != sha256_bytes(canonical_json_bytes(self.command)):
            raise ValueError("Judge probe command SHA-256 mismatch")
        if self.W_before != self.worker_source:
            raise ValueError("runtime W differs from frozen Worker source")
        roots = [
            Path(value.resolved_absolute_path).resolve()
            for value in (self.W, self.J, self.O, self.S)
        ]
        for index, left in enumerate(roots):
            for right in roots[index + 1 :]:
                if left == right or left in right.parents or right in left.parents:
                    raise ValueError("Judge logical roots overlap")
        return self


class StreamRecord(StrictModel):
    exit_code: int
    stdout_size: int = Field(ge=0)
    stdout_sha256: Sha256
    stdout_truncated: bool
    stderr_size: int = Field(ge=0)
    stderr_sha256: Sha256
    stderr_truncated: bool
    duration_ms: int = Field(ge=0)


class JudgeBoundaryResult(StrictModel):
    schema_version: Literal[1] = 1
    snapshot_id: Literal[SNAPSHOT_ID] = SNAPSHOT_ID
    run_id: str = Field(min_length=1)
    completed_at: datetime
    status: Literal[
        "JUDGE_RUNTIME_BOUNDARY_CANDIDATE",
        "CHALLENGE_NOT_READY",
        "CHALLENGE_INVALID",
    ]
    manifest_sha256: Sha256
    probe_process: StreamRecord
    checker_process: StreamRecord
    probe_payload: dict[str, Any]
    checker_payload: dict[str, Any] | None
    listener_ready: bool
    listener_accepted_connection_count: int = Field(ge=0)
    W_after: TreeFingerprint
    J_after: TreeFingerprint
    O_after: TreeFingerprint
    S_after: TreeFingerprint
    verification_codes: list[str]
    result_sha256: Sha256

    @model_validator(mode="after")
    def result_is_canonical(self) -> "JudgeBoundaryResult":
        validate_timestamp(self.completed_at)
        if self.verification_codes != sorted(set(self.verification_codes)):
            raise ValueError("verification codes must be sorted and unique")
        payload = self.model_dump(mode="json", exclude={"result_sha256"})
        if self.result_sha256 != sha256_bytes(canonical_json_bytes(payload)):
            raise ValueError("Judge boundary result SHA-256 mismatch")
        return self


@dataclass(frozen=True)
class PreparedJudgeRoots:
    run_root: Path
    W: Path
    J_parent: Path
    J: Path
    O: Path
    S_parent: Path
    S: Path
    source_commit: str
    worker_source_tree_oid: str
    worker_source: TreeFingerprint
    j_binding: SourceRuntimeBinding


def _sha_file(path: Path) -> str:
    return sha256_file(path)


def _path_is_reparse(path: Path) -> bool:
    attributes = getattr(path.stat(follow_symlinks=False), "st_file_attributes", 0)
    return bool(attributes & 0x400)


def fingerprint_tree(root: Path, *, include_git_oids: Mapping[str, str] | None = None) -> TreeFingerprint:
    resolved = Path(root).resolve(strict=True)
    if not resolved.is_dir() or _path_is_reparse(resolved):
        raise RealisticJudgeError("tree root must be a non-reparse directory")
    records: list[TreeFileRecord] = []
    casefold_paths: set[str] = set()
    for path in sorted(
        resolved.rglob("*"),
        key=lambda value: value.relative_to(resolved).as_posix().encode("utf-8"),
    ):
        if path.is_dir():
            if path.is_symlink() or _path_is_reparse(path):
                raise RealisticJudgeError("tree contains a reparse directory")
            continue
        if not path.is_file() or path.is_symlink() or _path_is_reparse(path):
            raise RealisticJudgeError("tree contains a non-regular file")
        relative = path.relative_to(resolved).as_posix()
        folded = relative.casefold()
        if folded in casefold_paths or ":" in relative or "\\" in relative:
            raise RealisticJudgeError("tree contains an unsafe or colliding path")
        casefold_paths.add(folded)
        payload = path.read_bytes()
        records.append(
            TreeFileRecord(
                path=relative,
                size=len(payload),
                sha256=sha256_bytes(payload),
                git_blob_oid=(include_git_oids or {}).get(relative),
            )
        )
    return TreeFingerprint(
        file_count=len(records),
        files=records,
        aggregate_sha256=sha256_bytes(
            canonical_json_bytes([item.model_dump(mode="json") for item in records])
        ),
    )


def _git(repository: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        stdin=subprocess.DEVNULL,
        capture_output=True,
    ).stdout


def _git_prefix_records(repository: Path, commit: str, prefix: str) -> tuple[str, list[tuple[str, str, bytes]]]:
    commit_id = _git(repository, "rev-parse", f"{commit}^{{commit}}").decode("ascii").strip()
    if commit_id != commit:
        raise RealisticJudgeError("source commit must be an exact full commit ID")
    tree_oid = _git(repository, "rev-parse", f"{commit}:{prefix}").decode("ascii").strip()
    raw = _git(repository, "ls-tree", "-r", "-z", "--full-tree", commit, "--", prefix)
    records: list[tuple[str, str, bytes]] = []
    prefix_slash = prefix.rstrip("/") + "/"
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        mode, kind, raw_oid = metadata.decode("ascii").split(" ")
        path = raw_path.decode("utf-8")
        if kind != "blob" or mode not in {"100644", "100755"} or not path.startswith(prefix_slash):
            raise RealisticJudgeError("source prefix contains a non-regular Git entry")
        relative = path[len(prefix_slash) :]
        pure = PurePosixPath(relative)
        if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
            raise RealisticJudgeError("source prefix contains an unsafe path")
        payload = _git(repository, "cat-file", "blob", raw_oid)
        records.append((relative, raw_oid, payload))
    if not records:
        raise RealisticJudgeError("source prefix is empty")
    return tree_oid, records


def _extract_git_prefix(repository: Path, commit: str, prefix: str, destination: Path) -> tuple[str, TreeFingerprint]:
    if destination.exists():
        raise RealisticJudgeError("Git extraction destination already exists")
    tree_oid, records = _git_prefix_records(repository, commit, prefix)
    destination.mkdir(parents=True)
    casefold_paths: set[str] = set()
    oid_by_path: dict[str, str] = {}
    for relative, oid, payload in records:
        folded = relative.casefold()
        if folded in casefold_paths or ":" in relative or "\\" in relative:
            raise RealisticJudgeError("Git source contains an unsafe or colliding path")
        casefold_paths.add(folded)
        pure = PurePosixPath(relative)
        target = destination.joinpath(*pure.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise RealisticJudgeError("Git extraction would overwrite a path")
        atomic_write(target, payload)
        oid_by_path[relative] = oid
    return tree_oid, fingerprint_tree(destination, include_git_oids=oid_by_path)


def _judge_config_overrides(*, W: Path, J: Path, O: Path, S: Path) -> tuple[str, ...]:
    roots = [Path(value).resolve() for value in (W, J, O, S)]
    common_parent = Path(os.path.commonpath(roots)).resolve()
    filesystem_entries = {
        ":minimal": "read",
        ":root": "deny",
        str(common_parent): "deny",
        str(roots[0]): "read",
        str(roots[1]): "read",
        str(roots[2]): "write",
        str(roots[3]): "deny",
    }
    filesystem_value = "{" + ",".join(
        f"{_toml_basic_string(path)}={_toml_basic_string(access)}"
        for path, access in sorted(filesystem_entries.items())
    ) + "}"
    return tuple(
        sorted(
            (
                f'default_permissions="{PROFILE_ID}"',
                f'permissions.{PROFILE_ID}.extends=":workspace"',
                f"permissions.{PROFILE_ID}.filesystem={filesystem_value}",
                f"permissions.{PROFILE_ID}.network.enabled=false",
                'windows.sandbox="elevated"',
            )
        )
    )


def _binding(
    *,
    source_commit: str,
    source_tree_oid: str,
    source: TreeFingerprint,
    runtime: TreeFingerprint,
    runtime_root: RootIdentity,
    runtime_parent: RootIdentity,
) -> SourceRuntimeBinding:
    runtime_root_hash = sha256_bytes(canonical_json_bytes(runtime_root))
    runtime_parent_hash = sha256_bytes(canonical_json_bytes(runtime_parent))
    values = {
        "source_commit": source_commit,
        "source_tree_oid": source_tree_oid,
        "source": source.model_dump(mode="json"),
        "runtime": runtime.model_dump(mode="json"),
        "source_runtime_relative_paths_equal": True,
        "source_runtime_bytes_equal": True,
        "runtime_root_identity_sha256": runtime_root_hash,
        "runtime_parent_identity_sha256": runtime_parent_hash,
    }
    return SourceRuntimeBinding(
        **values,
        binding_sha256=sha256_bytes(canonical_json_bytes(values)),
    )


def prepare_realistic_judge_roots(
    *,
    repository: Path,
    base_root: Path,
    source_commit: str,
    run_token: str | None = None,
) -> PreparedJudgeRoots:
    """Extract frozen W/J and create fresh O/S roots without running Codex."""

    if os.name != "nt":
        raise RealisticJudgeError("Profile R Judge boundary is Windows-only")
    repository = Path(repository).resolve(strict=True)
    parent = Path(base_root).resolve(strict=True)
    token = run_token or uuid.uuid4().hex[:12]
    if not token or any(value not in "abcdefghijklmnopqrstuvwxyz0123456789-" for value in token):
        raise RealisticJudgeError("run token is not path-safe")
    run_root = parent / f"profile-r-judge-{token}"
    if run_root.exists():
        raise RealisticJudgeError("Judge run root already exists")
    run_root.mkdir()
    W = run_root / "worker"
    O = run_root / "output"
    J_parent = run_root / f".judge-private-{uuid.uuid4().hex}"
    J = J_parent / "runtime"
    S_parent = run_root / f".state-private-{uuid.uuid4().hex}"
    S = S_parent / "state"
    worker_tree_oid, worker_source = _extract_git_prefix(
        repository, source_commit, WORKER_PREFIX, W
    )
    j_tree_oid, j_source = _extract_git_prefix(
        repository, source_commit, JUDGE_SOURCE_PREFIX, J
    )
    O.mkdir()
    if not J.exists():
        raise RealisticJudgeError("runtime J extraction failed")
    S_parent.mkdir()
    S.mkdir()
    state_payload = os.urandom(64)
    state_sentinel = S / "state-sentinel.bin"
    atomic_write(state_sentinel, state_payload)
    with open(str(state_sentinel) + ":judge-boundary", "wb") as stream:
        stream.write(os.urandom(64))
    J_parent_identity = _harden_controller_only_directory(J_parent)
    J_identity = _harden_controller_only_directory(J)
    S_parent_identity = _harden_controller_only_directory(S_parent)
    _harden_controller_only_directory(S)
    runtime_J = fingerprint_tree(J, include_git_oids={item.path: item.git_blob_oid for item in j_source.files if item.git_blob_oid})
    binding = _binding(
        source_commit=source_commit,
        source_tree_oid=j_tree_oid,
        source=j_source,
        runtime=runtime_J,
        runtime_root=J_identity,
        runtime_parent=J_parent_identity,
    )
    # Capture S parent now so an ACL drift cannot be hidden by a later lookup.
    _ = S_parent_identity
    return PreparedJudgeRoots(
        run_root=run_root,
        W=W,
        J_parent=J_parent,
        J=J,
        O=O,
        S_parent=S_parent,
        S=S,
        source_commit=source_commit,
        worker_source_tree_oid=worker_tree_oid,
        worker_source=worker_source,
        j_binding=binding,
    )


class _LoopbackListener:
    def __init__(self) -> None:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind(("127.0.0.1", 0))
        self._socket.listen(4)
        self._socket.settimeout(0.2)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self.accepted = 0

    @property
    def host(self) -> str:
        return str(self._socket.getsockname()[0])

    @property
    def port(self) -> int:
        return int(self._socket.getsockname()[1])

    def _serve(self) -> None:
        while not self._stop.is_set():
            try:
                connection, _ = self._socket.accept()
            except TimeoutError:
                continue
            except OSError:
                break
            self.accepted += 1
            connection.close()

    def __enter__(self) -> "_LoopbackListener":
        self._thread.start()
        return self

    def __exit__(self, *_args: object) -> None:
        self._stop.set()
        self._socket.close()
        self._thread.join(timeout=2)


def _sandbox_prefix(
    runtime: RuntimeIdentity,
    *,
    cwd: Path,
    overrides: Sequence[str],
) -> list[str]:
    values = [
        runtime.probe_resolved_executable,
        "sandbox",
        "--cd",
        str(cwd.resolve()),
        "--permission-profile",
        PROFILE_ID,
        "--include-managed-config",
    ]
    for override in overrides:
        values.extend(["--config", override])
    values.append("--")
    return values


def _manifest(
    prepared: PreparedJudgeRoots,
    *,
    runtime: RuntimeIdentity,
    python: Path,
    host: str,
    port: int,
    environment_allowlist: Sequence[str],
    timeout_seconds: int,
    stdout_limit_bytes: int,
) -> JudgeBoundaryManifest:
    W_identity = capture_windows_root_identity(prepared.W, redacted_path_id="W")
    J_identity = capture_windows_root_identity(prepared.J, redacted_path_id="J-runtime")
    O_identity = capture_windows_root_identity(prepared.O, redacted_path_id="O")
    S_identity = capture_windows_root_identity(prepared.S, redacted_path_id="S")
    overrides = _judge_config_overrides(W=prepared.W, J=prepared.J, O=prepared.O, S=prepared.S)
    probe = prepared.J / PROBE_RELATIVE_PATH
    checker = prepared.J / CHECKER_RELATIVE_PATH
    if not probe.is_file() or not checker.is_file():
        raise RealisticJudgeError("runtime J is missing its checker or probe")
    W_sentinel = prepared.W / "README.md"
    J_sentinel = prepared.J / "property-catalog.json"
    S_sentinel = prepared.S / "state-sentinel.bin"
    command = [
        *_sandbox_prefix(runtime, cwd=prepared.O, overrides=overrides),
        str(python),
        "-P",
        str(probe),
        "judge-boundary",
        "--python",
        str(python),
        "--w-root",
        str(prepared.W),
        "--j-root",
        str(prepared.J),
        "--o-root",
        str(prepared.O),
        "--s-root",
        str(prepared.S),
        "--w-sentinel",
        str(W_sentinel),
        "--j-sentinel",
        str(J_sentinel),
        "--s-sentinel",
        str(S_sentinel),
        "--common-parent",
        str(prepared.run_root),
        "--drive-root",
        str(Path(prepared.run_root.anchor)),
        "--network-host",
        host,
        "--network-port",
        str(port),
    ]
    O_before = fingerprint_tree(prepared.O)
    if O_before.file_count != 0:
        raise RealisticJudgeError("fresh output root is not empty")
    allowlist = sorted(set(environment_allowlist))
    return JudgeBoundaryManifest(
        run_id=prepared.run_root.name,
        created_at=utc_now(),
        source_commit=prepared.source_commit,
        runtime=runtime,
        config_overrides=list(overrides),
        environment_name_allowlist=allowlist,
        api_key_environment_names_present=[],
        python_executable=str(python),
        python_executable_sha256=_sha_file(python),
        probe_sha256=_sha_file(probe),
        checker_sha256=_sha_file(checker),
        W=W_identity,
        J=J_identity,
        O=O_identity,
        S=S_identity,
        W_before=fingerprint_tree(prepared.W, include_git_oids={item.path: item.git_blob_oid for item in prepared.worker_source.files if item.git_blob_oid}),
        J_before=fingerprint_tree(prepared.J, include_git_oids={item.path: item.git_blob_oid for item in prepared.j_binding.source.files if item.git_blob_oid}),
        O_before=O_before,
        S_before=fingerprint_tree(prepared.S),
        worker_source_tree_oid=prepared.worker_source_tree_oid,
        worker_source=prepared.worker_source,
        j_source_runtime_binding=prepared.j_binding,
        command=command,
        command_sha256=sha256_bytes(canonical_json_bytes(command)),
        timeout_seconds=timeout_seconds,
        stdout_limit_bytes=stdout_limit_bytes,
    )


def _stream_record(raw: tuple[int, bytes, int, str, bytes, int, str, int], limit: int) -> StreamRecord:
    return StreamRecord(
        exit_code=raw[0],
        stdout_size=raw[2],
        stdout_sha256=raw[3],
        stdout_truncated=raw[2] > limit,
        stderr_size=raw[5],
        stderr_sha256=raw[6],
        stderr_truncated=raw[5] > limit,
        duration_ms=raw[7],
    )


def _decode_single_json(stdout: bytes, total: int, limit: int, label: str) -> dict[str, Any]:
    if total > limit:
        raise RealisticJudgeError(f"{label} stdout exceeded the frozen cap")
    try:
        value = json.loads(stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RealisticJudgeError(f"{label} stdout is not one UTF-8 JSON value") from exc
    if not isinstance(value, dict):
        raise RealisticJudgeError(f"{label} stdout JSON is not an object")
    return value


def _root_by_role(actor: Mapping[str, Any], role: str) -> Mapping[str, Any]:
    roots = actor.get("roots")
    if not isinstance(roots, list):
        raise RealisticJudgeError("Judge actor root matrix is missing")
    matches = [value for value in roots if isinstance(value, dict) and value.get("role") == role]
    if len(matches) != 1:
        raise RealisticJudgeError(f"Judge actor root {role} is not unique")
    return matches[0]


def _expect_outcome(value: object, expected: str, code: str, codes: list[str]) -> None:
    if not isinstance(value, dict) or value.get("outcome") != expected:
        codes.append(code)


def _verify_actor(actor: Mapping[str, Any], codes: list[str]) -> str | None:
    identity = actor.get("process_identity")
    identity_sha = identity.get("identity_sha256") if isinstance(identity, dict) else None
    if not isinstance(identity_sha, str):
        codes.append("PROCESS_IDENTITY_MISSING")
    for role in ("W", "J"):
        root = _root_by_role(actor, role)
        _expect_outcome(root.get("enumerate"), "success", f"{role}_ENUMERATE_NOT_SUCCESS", codes)
        _expect_outcome(root.get("read"), "success", f"{role}_READ_NOT_SUCCESS", codes)
        _expect_outcome(root.get("normalized_read"), "success", f"{role}_NORMALIZED_READ_NOT_SUCCESS", codes)
        for operation in ("create", "write", "replace", "delete"):
            _expect_outcome(
                root.get(operation),
                "access_denied",
                f"{role}_{operation.upper()}_NOT_DENIED",
                codes,
            )
    output = _root_by_role(actor, "O")
    for operation in ("create", "write", "read", "replace", "delete"):
        _expect_outcome(output.get(operation), "success", f"O_{operation.upper()}_NOT_SUCCESS", codes)
    before = output.get("enumerate_before")
    after = output.get("enumerate_after_cleanup")
    if not isinstance(before, dict) or before.get("outcome") != "success" or before.get("entry_count") != 0:
        codes.append("O_PRECONDITION_NOT_EMPTY")
    if not isinstance(after, dict) or after.get("outcome") != "success" or after.get("entry_count") != 0:
        codes.append("O_CLEANUP_NOT_EMPTY")
    state = _root_by_role(actor, "S")
    for operation in ("enumerate", "read", "normalized_read", "create", "write", "replace", "delete"):
        _expect_outcome(state.get(operation), "access_denied", f"S_{operation.upper()}_NOT_DENIED", codes)
    _expect_outcome(actor.get("common_parent_enumeration"), "access_denied", "COMMON_PARENT_ENUMERATION_NOT_DENIED", codes)
    _expect_outcome(actor.get("drive_root_enumeration"), "access_denied", "DRIVE_ROOT_ENUMERATION_NOT_DENIED", codes)
    network = actor.get("network")
    if not isinstance(network, dict) or network.get("outcome") != "access_denied" or network.get("win32_error") != 10013:
        codes.append("LOOPBACK_NOT_PERMISSION_DENIED")
    if actor.get("api_key_environment_names_present") != []:
        codes.append("API_KEY_ENVIRONMENT_NAME_PRESENT")
    variants = actor.get("escape_variants")
    if not isinstance(variants, dict):
        codes.append("ESCAPE_VARIANTS_MISSING")
    else:
        for name in ("symlink", "junction"):
            item = variants.get(name)
            if not isinstance(item, dict) or item.get("create_outcome") != "success":
                codes.append(f"{name.upper()}_CREATE_NOT_SUCCESS")
            elif not isinstance(item.get("read"), dict) or item["read"].get("outcome") != "access_denied":
                codes.append(f"{name.upper()}_READ_NOT_DENIED")
            if isinstance(item, dict) and item.get("link_exists_after_cleanup") is not False:
                codes.append(f"{name.upper()}_CLEANUP_FAILED")
        hardlink = variants.get("hardlink")
        if not isinstance(hardlink, dict) or hardlink.get("create_outcome") not in {"success", "access_denied"}:
            codes.append("HARDLINK_RESULT_UNCLASSIFIED")
        elif hardlink.get("create_outcome") == "success" and (
            not isinstance(hardlink.get("read"), dict)
            or hardlink["read"].get("outcome") != "access_denied"
        ):
            codes.append("HARDLINK_READ_NOT_DENIED")
        _expect_outcome(variants.get("alternate_data_stream"), "access_denied", "ADS_READ_NOT_DENIED", codes)
        _expect_outcome(variants.get("normalized_parent"), "access_denied", "S_NORMALIZED_READ_NOT_DENIED", codes)
    return identity_sha if isinstance(identity_sha, str) else None


def verification_codes(
    manifest: JudgeBoundaryManifest,
    *,
    probe_wrapper: Mapping[str, Any],
    checker_payload: Mapping[str, Any] | None,
    checker_exit_code: int,
    listener_ready: bool,
    listener_accepted: int,
    W_after: TreeFingerprint,
    J_after: TreeFingerprint,
    O_after: TreeFingerprint,
    S_after: TreeFingerprint,
) -> list[str]:
    codes: list[str] = []
    payload = probe_wrapper.get("payload")
    if probe_wrapper.get("operation_exit_code") != 0 or not isinstance(payload, dict):
        return ["PROBE_WRAPPER_FAILED"]
    parent = payload.get("parent")
    child_wrapper = payload.get("child_wrapper")
    child = child_wrapper.get("payload") if isinstance(child_wrapper, dict) else None
    if payload.get("child_exit_code") != 0 or not isinstance(parent, dict) or not isinstance(child, dict):
        codes.append("CHILD_PROBE_FAILED")
    else:
        parent_identity = _verify_actor(parent, codes)
        child_identity = _verify_actor(child, codes)
        if parent_identity != child_identity:
            codes.append("PARENT_CHILD_IDENTITY_MISMATCH")
        parent_public = {key: value for key, value in parent.items() if key not in {"actor", "process_identity"}}
        child_public = {key: value for key, value in child.items() if key not in {"actor", "process_identity"}}
        if parent_public != child_public:
            codes.append("PARENT_CHILD_MATRIX_MISMATCH")
    if not listener_ready:
        codes.append("LOOPBACK_LISTENER_NOT_READY")
    if listener_accepted != 0:
        codes.append("LOOPBACK_CONNECTION_ACCEPTED")
    if W_after != manifest.W_before:
        codes.append("W_MUTATED")
    if J_after != manifest.J_before:
        codes.append("J_MUTATED")
    if O_after.file_count != 0:
        codes.append("O_UNEXPECTED_OUTPUT")
    if S_after != manifest.S_before:
        codes.append("S_MUTATED")
    if checker_payload is None or checker_exit_code not in {0, 1}:
        codes.append("CHECKER_DID_NOT_RETURN_TYPED_RESULT")
    elif checker_payload.get("aggregate_status") not in {"pass", "fail"}:
        codes.append("CHECKER_AGGREGATE_STATUS_INVALID")
    return sorted(set(codes))


def execute_realistic_judge_boundary(
    prepared: PreparedJudgeRoots,
    *,
    probe_python_executable: Path,
    source_environment: Mapping[str, str] | None = None,
    timeout_seconds: int = 180,
    stdout_limit_bytes: int = 1_048_576,
) -> tuple[JudgeBoundaryManifest, JudgeBoundaryResult]:
    """Execute the frozen model-free Judge boundary and checker exactly once."""

    runtime = resolve_pinned_runtime_identity()
    verify_pinned_runtime_identity(runtime)
    python = Path(probe_python_executable).resolve(strict=True)
    environment = build_sanitized_environment(
        DEFAULT_ENVIRONMENT_NAME_ALLOWLIST,
        source=source_environment,
    )
    environment.update(
        {
            "TEMP": str(prepared.O),
            "TMP": str(prepared.O),
            "USERPROFILE": str(prepared.O),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
        }
    )
    if any(name.upper() in API_KEY_ENVIRONMENT_NAMES for name in environment):
        raise RealisticJudgeError("sanitized Judge environment contains an API-key name")
    with _LoopbackListener() as listener:
        manifest = _manifest(
            prepared,
            runtime=runtime,
            python=python,
            host=listener.host,
            port=listener.port,
            environment_allowlist=DEFAULT_ENVIRONMENT_NAME_ALLOWLIST,
            timeout_seconds=timeout_seconds,
            stdout_limit_bytes=stdout_limit_bytes,
        )
        manifest_sha = sha256_bytes(canonical_json_bytes(manifest))
        atomic_write(prepared.run_root / "judge-boundary-manifest.json", canonical_json_bytes(manifest))
        probe_raw = _run_command_capped(
            manifest.command,
            cwd=prepared.O,
            environment=environment,
            timeout_seconds=timeout_seconds,
            limit=stdout_limit_bytes,
        )
        probe_wrapper = _decode_single_json(
            probe_raw[1], probe_raw[2], stdout_limit_bytes, "Judge boundary probe"
        )
        checker_command = [
            *_sandbox_prefix(runtime, cwd=prepared.O, overrides=manifest.config_overrides),
            str(python),
            "-P",
            str(prepared.J / CHECKER_RELATIVE_PATH),
            "--workspace",
            str(prepared.W),
            "--experiment-id",
            "phase-d-profile-r-boundary",
            "--cell-id",
            "pristine-boundary",
        ]
        checker_raw = _run_command_capped(
            checker_command,
            cwd=prepared.O,
            environment=environment,
            timeout_seconds=timeout_seconds,
            limit=stdout_limit_bytes,
        )
        checker_payload: dict[str, Any] | None
        try:
            checker_payload = _decode_single_json(
                checker_raw[1], checker_raw[2], stdout_limit_bytes, "Profile R checker"
            )
        except RealisticJudgeError:
            checker_payload = None
    W_after = fingerprint_tree(prepared.W, include_git_oids={item.path: item.git_blob_oid for item in prepared.worker_source.files if item.git_blob_oid})
    J_after = fingerprint_tree(prepared.J, include_git_oids={item.path: item.git_blob_oid for item in prepared.j_binding.source.files if item.git_blob_oid})
    O_after = fingerprint_tree(prepared.O)
    S_after = fingerprint_tree(prepared.S)
    codes = verification_codes(
        manifest,
        probe_wrapper=probe_wrapper,
        checker_payload=checker_payload,
        checker_exit_code=checker_raw[0],
        listener_ready=True,
        listener_accepted=listener.accepted,
        W_after=W_after,
        J_after=J_after,
        O_after=O_after,
        S_after=S_after,
    )
    status: Literal[
        "JUDGE_RUNTIME_BOUNDARY_CANDIDATE",
        "CHALLENGE_NOT_READY",
        "CHALLENGE_INVALID",
    ]
    if "W_MUTATED" in codes or "J_MUTATED" in codes or "S_MUTATED" in codes or "LOOPBACK_CONNECTION_ACCEPTED" in codes:
        status = "CHALLENGE_INVALID"
    elif codes:
        status = "CHALLENGE_NOT_READY"
    else:
        status = "JUDGE_RUNTIME_BOUNDARY_CANDIDATE"
    values = {
        "schema_version": 1,
        "snapshot_id": SNAPSHOT_ID,
        "run_id": manifest.run_id,
        "completed_at": utc_now(),
        "status": status,
        "manifest_sha256": manifest_sha,
        "probe_process": _stream_record(probe_raw, stdout_limit_bytes).model_dump(mode="json"),
        "checker_process": _stream_record(checker_raw, stdout_limit_bytes).model_dump(mode="json"),
        "probe_payload": probe_wrapper,
        "checker_payload": checker_payload,
        "listener_ready": True,
        "listener_accepted_connection_count": listener.accepted,
        "W_after": W_after.model_dump(mode="json"),
        "J_after": J_after.model_dump(mode="json"),
        "O_after": O_after.model_dump(mode="json"),
        "S_after": S_after.model_dump(mode="json"),
        "verification_codes": codes,
    }
    result = JudgeBoundaryResult(
        **values,
        result_sha256=sha256_bytes(canonical_json_bytes(values)),
    )
    atomic_write(prepared.run_root / "judge-boundary-result.json", canonical_json_bytes(result))
    return manifest, result


def verify_realistic_judge_boundary(
    manifest: JudgeBoundaryManifest,
    result: JudgeBoundaryResult,
) -> Literal[
    "JUDGE_RUNTIME_BOUNDARY_CANDIDATE",
    "CHALLENGE_NOT_READY",
    "CHALLENGE_INVALID",
]:
    """Recompute immutable manifest/result bindings without trusting stored status."""

    if result.run_id != manifest.run_id:
        raise RealisticJudgeError("Judge manifest/result run ID mismatch")
    if result.manifest_sha256 != sha256_bytes(canonical_json_bytes(manifest)):
        raise RealisticJudgeError("Judge result does not bind the manifest")
    if result.result_sha256 != sha256_bytes(
        canonical_json_bytes(result.model_dump(mode="json", exclude={"result_sha256"}))
    ):
        raise RealisticJudgeError("Judge result self-hash mismatch")
    if result.status == "JUDGE_RUNTIME_BOUNDARY_CANDIDATE" and result.verification_codes:
        raise RealisticJudgeError("Judge candidate has verification failures")
    if result.status != "JUDGE_RUNTIME_BOUNDARY_CANDIDATE" and not result.verification_codes:
        raise RealisticJudgeError("Judge failure has no verification code")
    return result.status
