"""Workspace, Artifact, fingerprint, scope, and deterministic Check verification."""

from __future__ import annotations

import fnmatch
import json
import os
import re
import signal
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Iterator

from pydantic import ValidationError

from .contract import (
    CheckFailureClassification,
    CheckResult,
    CheckState,
    CommandCheck,
    FingerprintEntry,
    InputFingerprint,
    ResultEnvelope,
    TaskSpec,
    WorkspaceBaseline,
    canonical_json,
    sha256_bytes,
    sha256_json,
    utc_now,
    validate_relative_path,
)


PUBLIC_CHECK_FEEDBACK_PREFIX = "WORKER_FEEDBACK:"
PUBLIC_CHECK_FEEDBACK_MAX_BYTES = 16_384
CHECK_FAILURE_CLASS_PREFIX = "CHECK_FAILURE_CLASS:"
CHECK_ENVIRONMENT_DIAGNOSTIC_PREFIX = "CHECK_ENVIRONMENT_DIAGNOSTIC:"
CHECK_ENVIRONMENT_DIAGNOSTIC_MAX_BYTES = 4_096
CHECK_ENVIRONMENT_DIAGNOSTIC_KEYS = frozenset(
    {
        "schema_version",
        "stage",
        "command_ordinal",
        "return_code",
        "stderr_sha256",
        "safe_error_code",
        "path_lengths",
    }
)
CHECK_ENVIRONMENT_STAGE_PATTERN = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")
CHECK_ENVIRONMENT_ERROR_CODE_PATTERN = re.compile(r"[A-Z][A-Z0-9_]{0,95}\Z")
CHECK_ENVIRONMENT_PATH_LENGTH_KEYS = frozenset(
    {
        "temp_root",
        "junit_file",
        "deepest_observed",
        "growth_target",
        "probe_repository",
        "probe_relative",
        "probe_file",
        "git_config",
    }
)
CHECK_ENVIRONMENT_ORDINAL_MAX = 64
CHECK_ENVIRONMENT_RETURN_CODE_MIN = -(2**31)
CHECK_ENVIRONMENT_RETURN_CODE_MAX = (2**32) - 1
CHECK_ENVIRONMENT_PATH_LENGTH_MAX = 1_000_000
CHECK_TEMP_MARKER = ".lao-check-allocation"
CHECK_TEMP_ALLOCATION_ID_LENGTH = 32
CHECK_TEMP_GIT_BOOTSTRAP_SUFFIX = ("git-probe", ".git", "config")
CHECK_TEMP_HOSTILE_TRACKED_PATH_LENGTH = 320
WINDOWS_LEGACY_PATH_LIMIT = 260
DEFAULT_CHECK_TERMINATION_GRACE_SECONDS = 15.0
WINDOWS_CREATE_SUSPENDED = 0x00000004


@dataclass(frozen=True, slots=True)
class CheckTempAllocation:
    root: Path
    path: Path
    allocation_id: str


def _cleanup_path(path: Path) -> str:
    """Return an absolute path that remains deletable past MAX_PATH on Windows."""

    resolved = str(path.resolve())
    if os.name != "nt" or resolved.startswith("\\\\?\\"):
        return resolved
    if resolved.startswith("\\\\"):
        return "\\\\?\\UNC\\" + resolved[2:]
    return "\\\\?\\" + resolved


def _retry_check_temp_cleanup(function: Any, path: str, error: OSError) -> None:
    """Retry removal only when Windows marked a Check-owned file read-only."""

    if not isinstance(error, PermissionError):
        raise error
    os.chmod(path, stat.S_IWRITE)
    function(path)


def _is_reparse_point(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        attributes = getattr(path.stat(), "st_file_attributes", 0)
    except OSError as exc:
        raise VerificationError(
            "check_environment",
            "Check temp path metadata is unavailable",
        ) from exc
    return bool(attributes & 0x400)


def _assert_no_reparse_ancestors(path: Path) -> None:
    current = path
    while True:
        if current.exists() and _is_reparse_point(current):
            raise VerificationError(
                "check_environment",
                "Check temp root or ancestor is a reparse point",
            )
        if current.parent == current:
            return
        current = current.parent


def _windows_filesystem_name(path: Path) -> str | None:
    if os.name != "nt":
        return None
    import ctypes

    root = str(Path(path).resolve().anchor)
    filesystem = ctypes.create_unicode_buffer(261)
    result = ctypes.windll.kernel32.GetVolumeInformationW(
        root,
        None,
        0,
        None,
        None,
        None,
        filesystem,
        len(filesystem),
    )
    if not result:
        raise VerificationError(
            "check_environment",
            "Check temp filesystem identity is unavailable",
        )
    return filesystem.value


def validate_external_check_temp_root(
    root: Path,
    *,
    forbidden_roots: Iterable[Path],
    required_descendant_headroom: int = 0,
    required_allocation_suffixes: Iterable[tuple[str, ...]] = (),
    require_ntfs: bool = False,
) -> Path:
    raw = Path(root)
    if not raw.is_absolute():
        raise VerificationError("check_environment", "Check temp root must be absolute")
    resolved = raw.resolve()
    for forbidden in forbidden_roots:
        boundary = Path(forbidden).resolve()
        if (
            resolved == boundary
            or resolved in boundary.parents
            or boundary in resolved.parents
        ):
            raise VerificationError(
                "check_environment",
                "Check temp root overlaps a protected execution root",
            )
    if required_descendant_headroom < 0:
        raise VerificationError(
            "check_environment",
            "Check temp path headroom must be nonnegative",
        )
    if (
        os.name == "nt"
        and len(str(resolved)) + required_descendant_headroom
        >= WINDOWS_LEGACY_PATH_LIMIT
    ):
        raise VerificationError(
            "check_environment",
            "Check temp root does not preserve the required Windows path headroom",
        )
    for suffix in required_allocation_suffixes:
        candidate = resolved / ("a" * CHECK_TEMP_ALLOCATION_ID_LENGTH)
        for component in suffix:
            part = PurePosixPath(component)
            if (
                len(part.parts) != 1
                or part.parts[0] in {"", ".", ".."}
                or "\\" in component
            ):
                raise VerificationError(
                    "check_environment",
                    "Check temp required allocation suffix is invalid",
                )
            candidate /= component
        if os.name == "nt" and len(str(candidate)) >= WINDOWS_LEGACY_PATH_LIMIT:
            raise VerificationError(
                "check_environment",
                (
                    "Check temp root does not preserve exact Windows path headroom "
                    f"for allocation descendant {'/'.join(suffix)}"
                ),
            )
    if require_ntfs and os.name == "nt":
        filesystem = _windows_filesystem_name(resolved)
        if filesystem is None or filesystem.casefold() != "ntfs":
            raise VerificationError(
                "check_environment",
                "Check temp root must be located on NTFS",
            )
    _assert_no_reparse_ancestors(resolved)
    return resolved


def _minimal_process_environment(source: dict[str, str]) -> dict[str, str]:
    keep = ("SystemRoot", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT")
    return {key: source[key] for key in keep if key in source}


def _resolve_git_executable(
    git_executable: Path | None,
    source: dict[str, str],
) -> Path:
    candidate = git_executable
    if candidate is None:
        discovered = shutil.which("git", path=source.get("PATH"))
        if not discovered:
            raise VerificationError("check_environment", "Git executable is unavailable")
        candidate = Path(discovered)
    resolved = Path(candidate).resolve()
    if not resolved.is_file():
        raise VerificationError("check_environment", "Git executable is not a file")
    return resolved


def build_hermetic_git_environment(
    *,
    workspace: Path,
    git_executable: Path,
    environ: dict[str, str] | None = None,
) -> dict[str, str]:
    source = dict(os.environ if environ is None else environ)
    git_path = Path(git_executable).resolve()
    environment = _minimal_process_environment(source)
    path_parts = [str(git_path.parent)]
    system_root = environment.get("SystemRoot") or environment.get("SYSTEMROOT")
    if system_root:
        path_parts.append(str(Path(system_root) / "System32"))
    environment.update(
        {
            "PATH": os.pathsep.join(dict.fromkeys(path_parts)),
            "HOME": str(Path(workspace).resolve()),
            "USERPROFILE": str(Path(workspace).resolve()),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
            "GCM_INTERACTIVE": "Never",
            "GIT_CONFIG_COUNT": "5",
            "GIT_CONFIG_KEY_0": "core.longpaths",
            "GIT_CONFIG_VALUE_0": "true",
            "GIT_CONFIG_KEY_1": "core.autocrlf",
            "GIT_CONFIG_VALUE_1": "false",
            "GIT_CONFIG_KEY_2": "credential.interactive",
            "GIT_CONFIG_VALUE_2": "false",
            "GIT_CONFIG_KEY_3": "core.hooksPath",
            "GIT_CONFIG_VALUE_3": os.devnull,
            "GIT_CONFIG_KEY_4": "safe.directory",
            "GIT_CONFIG_VALUE_4": str(Path(workspace).resolve()),
        }
    )
    return environment


@dataclass(frozen=True, slots=True)
class PublicCheckFeedback:
    """Explicitly published Check diagnostics that are safe to show a retry Worker."""

    messages: tuple[str, ...]
    transmitted_bytes: int
    truncated: bool


class VerificationError(RuntimeError):
    def __init__(
        self,
        stage: str,
        message: str,
        *,
        retryable: bool = False,
        public_feedback: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.stage = stage
        self.retryable = retryable
        self.public_feedback = public_feedback


def extract_public_check_feedback(result: CheckResult) -> PublicCheckFeedback:
    """Return explicitly marked, UTF-8-bounded Worker-safe Check feedback.

    Unmarked stdout/stderr remains verifier-only.  Marked lines keep indentation so
    public tracebacks and assertion details remain useful to the retry Worker.
    """

    messages: list[str] = []
    remaining = PUBLIC_CHECK_FEEDBACK_MAX_BYTES
    truncated = False
    for stream in (result.stdout, result.stderr):
        for line in stream.splitlines():
            if not line.startswith(PUBLIC_CHECK_FEEDBACK_PREFIX):
                continue
            message = line[len(PUBLIC_CHECK_FEEDBACK_PREFIX):].rstrip()
            if not message.strip():
                continue
            if remaining <= 0:
                truncated = True
                continue
            encoded = message.encode("utf-8")
            if len(encoded) > remaining:
                truncated = True
                encoded = encoded[:remaining]
                while encoded:
                    try:
                        message = encoded.decode("utf-8")
                        break
                    except UnicodeDecodeError:
                        encoded = encoded[:-1]
                else:
                    message = ""
            if message:
                messages.append(message)
                remaining -= len(message.encode("utf-8"))
    transmitted = PUBLIC_CHECK_FEEDBACK_MAX_BYTES - remaining
    return PublicCheckFeedback(
        messages=tuple(messages),
        transmitted_bytes=transmitted,
        truncated=truncated,
    )


def extract_check_environment_diagnostic(result: CheckResult) -> dict[str, Any] | None:
    """Parse one bounded, canonical verifier-only environment diagnostic record."""

    payloads = [
        line[len(CHECK_ENVIRONMENT_DIAGNOSTIC_PREFIX):]
        for stream in (result.stdout, result.stderr)
        for line in stream.splitlines()
        if line.startswith(CHECK_ENVIRONMENT_DIAGNOSTIC_PREFIX)
    ]
    if not payloads:
        return None
    if len(payloads) != 1:
        raise VerificationError(
            "check_environment",
            "Check emitted multiple environment diagnostic records",
        )
    encoded = payloads[0].encode("utf-8")
    if len(encoded) > CHECK_ENVIRONMENT_DIAGNOSTIC_MAX_BYTES:
        raise VerificationError(
            "check_environment",
            "Check environment diagnostic record exceeds the byte limit",
        )
    try:
        value = json.loads(encoded)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError(
            "check_environment",
            "Check environment diagnostic record is invalid JSON",
        ) from exc
    if type(value) is not dict or canonical_json(value) != payloads[0]:
        raise VerificationError(
            "check_environment",
            "Check environment diagnostic record is not canonical version 1",
        )
    if set(value) != CHECK_ENVIRONMENT_DIAGNOSTIC_KEYS:
        raise VerificationError(
            "check_environment",
            "Check environment diagnostic record has an unexpected schema",
        )
    schema_version = value["schema_version"]
    stage = value["stage"]
    command_ordinal = value["command_ordinal"]
    return_code = value["return_code"]
    stderr_sha256 = value["stderr_sha256"]
    safe_error_code = value["safe_error_code"]
    path_lengths = value["path_lengths"]
    if type(schema_version) is not int or schema_version != 1:
        raise VerificationError(
            "check_environment",
            "Check environment diagnostic schema version is invalid",
        )
    if (
        not isinstance(stage, str)
        or CHECK_ENVIRONMENT_STAGE_PATTERN.fullmatch(stage) is None
    ):
        raise VerificationError(
            "check_environment",
            "Check environment diagnostic stage is invalid",
        )
    if (
        type(command_ordinal) is not int
        or not 0 <= command_ordinal <= CHECK_ENVIRONMENT_ORDINAL_MAX
    ):
        raise VerificationError(
            "check_environment",
            "Check environment diagnostic command ordinal is invalid",
        )
    if return_code is not None and (
        type(return_code) is not int
        or not CHECK_ENVIRONMENT_RETURN_CODE_MIN
        <= return_code
        <= CHECK_ENVIRONMENT_RETURN_CODE_MAX
    ):
        raise VerificationError(
            "check_environment",
            "Check environment diagnostic return code is invalid",
        )
    if (
        not isinstance(stderr_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", stderr_sha256) is None
    ):
        raise VerificationError(
            "check_environment",
            "Check environment diagnostic stderr hash is invalid",
        )
    if (
        not isinstance(safe_error_code, str)
        or CHECK_ENVIRONMENT_ERROR_CODE_PATTERN.fullmatch(safe_error_code) is None
    ):
        raise VerificationError(
            "check_environment",
            "Check environment diagnostic safe error code is invalid",
        )
    if (
        type(path_lengths) is not dict
        or not set(path_lengths).issubset(CHECK_ENVIRONMENT_PATH_LENGTH_KEYS)
    ):
        raise VerificationError(
            "check_environment",
            "Check environment diagnostic path-length keys are invalid",
        )
    if any(
        type(path_length) is not int
        or not 0 <= path_length <= CHECK_ENVIRONMENT_PATH_LENGTH_MAX
        for path_length in path_lengths.values()
    ):
        raise VerificationError(
            "check_environment",
            "Check environment diagnostic path length is invalid",
        )
    if result.failure_classification is not CheckFailureClassification.ENVIRONMENT:
        raise VerificationError(
            "check_environment",
            "Check environment diagnostic record lacks ENVIRONMENT classification",
        )
    return value


def path_matches(path: str, patterns: Iterable[str]) -> bool:
    normalized = PurePosixPath(path).as_posix()
    for pattern in patterns:
        if pattern.endswith("/**"):
            prefix = pattern[:-3].rstrip("/")
            if normalized == prefix or normalized.startswith(prefix + "/"):
                return True
        if fnmatch.fnmatchcase(normalized, pattern) or PurePosixPath(normalized).match(pattern):
            return True
    return False


def _file_entry(root: Path, relative: str) -> FingerprintEntry:
    data = (root / relative).read_bytes()
    return FingerprintEntry(path=relative, sha256=sha256_bytes(data), size=len(data))


class GitWorkspace:
    def __init__(
        self,
        root: Path,
        *,
        git_executable: Path | None = None,
        environ: dict[str, str] | None = None,
    ):
        self.root = Path(root).resolve()
        self._source_environment = dict(os.environ if environ is None else environ)
        self.git_executable = _resolve_git_executable(
            git_executable,
            self._source_environment,
        )
        self.git_environment = build_hermetic_git_environment(
            workspace=self.root,
            git_executable=self.git_executable,
            environ=self._source_environment,
        )

    def _git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(self.git_executable), *args],
            cwd=self.root,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            shell=False,
            check=check,
            env=self.git_environment,
        )

    def doctor(self) -> dict[str, Any]:
        result = self._git("rev-parse", "--show-toplevel", check=False)
        if result.returncode != 0:
            return {"healthy": False, "reason": "not_git_repository"}
        actual = Path(result.stdout.strip()).resolve()
        return {"healthy": actual == self.root, "repository_root": str(actual)}

    def git_directory(self) -> Path:
        result = self._git("rev-parse", "--absolute-git-dir", check=False)
        if result.returncode != 0:
            raise VerificationError("check_environment", "Git directory is unavailable")
        directory = Path(result.stdout.strip()).resolve()
        if not directory.is_dir():
            raise VerificationError("check_environment", "Git directory is not a directory")
        return directory

    def head_revision(self) -> str:
        result = self._git("rev-parse", "HEAD", check=False)
        return result.stdout.strip() if result.returncode == 0 else "UNBORN"

    def status(self) -> dict[str, Any]:
        result = self._git("status", "--porcelain=v1", "--untracked-files=normal")
        lines = [line for line in result.stdout.splitlines() if line]
        return {"clean": not lines, "entries": lines}

    def list_files(self, path_scopes: Iterable[str] | None = None) -> list[str]:
        result = subprocess.run(
            [str(self.git_executable), "ls-files", "-co", "--exclude-standard", "-z"],
            cwd=self.root,
            capture_output=True,
            shell=False,
            check=True,
            env=self.git_environment,
        )
        files = sorted(
            path.replace("\\", "/")
            for path in result.stdout.decode("utf-8", errors="surrogateescape").split("\0")
            if path
        )
        scopes = list(path_scopes or [])
        return [path for path in files if not scopes or path_matches(path, scopes)]

    def capture_baseline(self, path_scopes: Iterable[str] | None = None) -> WorkspaceBaseline:
        entries = [_file_entry(self.root, path) for path in self.list_files(path_scopes)]
        return WorkspaceBaseline(
            head_revision=self.head_revision(),
            files=entries,
            sha256=sha256_json([entry.model_dump(mode="json") for entry in entries]),
        )

    def changed_paths(self, baseline: WorkspaceBaseline) -> list[str]:
        current = self.capture_baseline()
        before = {entry.path: (entry.sha256, entry.size) for entry in baseline.files}
        after = {entry.path: (entry.sha256, entry.size) for entry in current.files}
        return sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))

    def normalize_untracked_python_bytecode(self, changed_paths: Iterable[str]) -> list[str]:
        """Remove only untracked ``__pycache__/*.pyc`` execution byproducts."""

        tracked = {
            path
            for path in self._git("ls-files", "--cached", "-z").stdout.split("\0")
            if path
        }
        normalized: list[str] = []
        for raw_path in changed_paths:
            relative_path = PurePosixPath(raw_path).as_posix()
            path = PurePosixPath(relative_path)
            if (
                "__pycache__" not in path.parts
                or path.suffix != ".pyc"
                or relative_path in tracked
            ):
                continue
            candidate = self.root.joinpath(*path.parts)
            current = self.root
            unsafe_component = False
            for part in path.parts:
                current /= part
                is_junction = getattr(current, "is_junction", lambda: False)
                if current.is_symlink() or is_junction():
                    unsafe_component = True
                    break
            if unsafe_component or not candidate.is_file():
                continue
            candidate.unlink()
            normalized.append(relative_path)
        return sorted(normalized)

    def fingerprint_inputs(self, task: TaskSpec) -> InputFingerprint:
        scopes = [*task.read_scope, *(item.path for item in task.inputs)]
        entries = [_file_entry(self.root, path) for path in self.list_files(scopes)]
        manifest = [entry.model_dump(mode="json") for entry in entries]
        return InputFingerprint(manifest=entries, sha256=sha256_json(manifest))


class ArtifactStore:
    def __init__(self, state_root: Path):
        self.state_root = Path(state_root).resolve()
        self.state_root.mkdir(parents=True, exist_ok=True)

    def resolve(self, relative_path: str) -> Path:
        validate_relative_path(relative_path)
        target = (self.state_root / PurePosixPath(relative_path)).resolve()
        if self.state_root not in target.parents and target != self.state_root:
            raise VerificationError("artifact_path", "Artifact path escaped state root")
        return target

    def write_bytes(self, relative_path: str, data: bytes) -> dict[str, Any]:
        target = self.resolve(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, target)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)
        return {
            "relative_path": PurePosixPath(relative_path).as_posix(),
            "sha256": sha256_bytes(data),
            "size_bytes": len(data),
        }

    def write_text(self, relative_path: str, text: str) -> dict[str, Any]:
        return self.write_bytes(relative_path, text.encode("utf-8"))

    def write_json(self, relative_path: str, value: Any) -> dict[str, Any]:
        return self.write_text(relative_path, canonical_json(value) + "\n")

    def verify(self, relative_path: str, expected_sha256: str) -> bool:
        target = self.resolve(relative_path)
        return target.is_file() and sha256_bytes(target.read_bytes()) == expected_sha256


def hash_project_pack(pack_root: Path) -> tuple[str, list[dict[str, Any]]]:
    pack_root = Path(pack_root).resolve()
    if not pack_root.is_dir():
        raise VerificationError("project_pack", f"missing Project Pack: {pack_root}")
    manifest: list[dict[str, Any]] = []
    for path in sorted(pack_root.rglob("*")):
        if path.is_symlink():
            raise VerificationError("project_pack", "Project Pack symlinks are forbidden")
        if path.is_file():
            data = path.read_bytes()
            manifest.append({
                "path": path.relative_to(pack_root).as_posix(),
                "size": len(data),
                "sha256": sha256_bytes(data),
            })
    return sha256_json(manifest), manifest


def validate_result_schema(raw_result: Any) -> ResultEnvelope:
    if isinstance(raw_result, str):
        try:
            raw_result = json.loads(raw_result)
        except json.JSONDecodeError as exc:
            raise VerificationError("result_schema", "runtime result is not JSON", retryable=True) from exc
    try:
        return ResultEnvelope.model_validate(raw_result)
    except ValidationError as exc:
        raise VerificationError("result_schema", str(exc), retryable=True) from exc


def validate_write_scope(task: TaskSpec, changed_paths: Iterable[str]) -> list[str]:
    changed = [PurePosixPath(path).as_posix() for path in changed_paths]
    violations = [path for path in changed if not path_matches(path, task.write_scope)]
    if violations:
        raise VerificationError("write_scope", f"out-of-scope changes: {violations}")
    return changed


def validate_freshness(
    original: InputFingerprint,
    current: InputFingerprint,
    task: TaskSpec,
    changed_paths: Iterable[str],
) -> None:
    changed = set(changed_paths)
    before = {entry.path: (entry.sha256, entry.size) for entry in original.manifest}
    after = {entry.path: (entry.sha256, entry.size) for entry in current.manifest}
    stale = []
    for path in before.keys() | after.keys():
        if before.get(path) == after.get(path):
            continue
        if path in changed and path_matches(path, task.write_scope):
            continue
        stale.append(path)
    if stale:
        raise VerificationError("freshness", f"input changed while Attempt ran: {sorted(stale)}", retryable=True)


def validate_declared_artifacts(result: ResultEnvelope, workspace: GitWorkspace) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for artifact in result.artifacts:
        path = (workspace.root / artifact.path).resolve()
        if workspace.root not in path.parents or not path.is_file():
            raise VerificationError("declared_artifacts", f"declared Artifact missing: {artifact.path}")
        data = path.read_bytes()
        evidence.append({"path": artifact.path, "sha256": sha256_bytes(data), "size": len(data)})
    return evidence


def validate_result_artifact_path_types(
    result: ResultEnvelope,
    workspace: GitWorkspace,
) -> None:
    """Return retryable guidance before a directory claim reaches final verification."""

    for artifact in result.artifacts:
        path = (workspace.root / artifact.path).resolve()
        if workspace.root in path.parents and path.is_dir():
            raise VerificationError(
                "result_schema",
                (
                    "ResultEnvelope artifacts.path must name one existing regular file; "
                    f"directory paths are invalid: {artifact.path}. Use a concrete "
                    "manifest or index file for a directory output."
                ),
                retryable=True,
            )


@contextmanager
def isolated_check_temp_directory(temp_root: Path) -> Iterator[CheckTempAllocation]:
    """Create and remove one marker-bound allocation below an explicit root."""

    root = Path(temp_root).resolve()
    allocation_id = uuid.uuid4().hex
    if len(allocation_id) != CHECK_TEMP_ALLOCATION_ID_LENGTH:
        raise VerificationError(
            "check_environment",
            "Check temp allocation identifier length differs",
        )
    allocation = root / allocation_id
    marker = allocation / CHECK_TEMP_MARKER
    try:
        root.mkdir(parents=True, exist_ok=True)
        _assert_no_reparse_ancestors(root)
        allocation.mkdir(exist_ok=False)
        _assert_no_reparse_ancestors(allocation)
        marker.write_text(allocation_id + "\n", encoding="ascii", newline="\n")
    except OSError as exc:
        raise VerificationError(
            "check_environment",
            "external Check temp allocation is unavailable",
        ) from exc
    try:
        yield CheckTempAllocation(
            root=root,
            path=allocation.resolve(),
            allocation_id=allocation_id,
        )
    finally:
        try:
            if marker.read_text(encoding="ascii") != allocation_id + "\n":
                raise VerificationError(
                    "check_environment",
                    "Check temp allocation ownership marker differs",
                )
            shutil.rmtree(
                _cleanup_path(allocation),
                onexc=_retry_check_temp_cleanup,
            )
            if allocation.exists():
                raise VerificationError(
                    "check_environment",
                    "Check temp allocation cleanup left residue",
                )
        except VerificationError:
            raise
        except OSError as exc:
            error_code = getattr(exc, "winerror", None) or exc.errno or "unknown"
            raise VerificationError(
                "check_environment",
                (
                    "Check temp allocation cleanup failed "
                    f"({type(exc).__name__}, code={error_code})"
                ),
            ) from exc


def build_check_environment(
    *,
    temp_directory: Path,
    python_executable: Path | None = None,
    git_executable: Path | None = None,
    git_safe_directory: Path | None = None,
    environ: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build the deterministic, secret-free environment used by command Checks."""

    source = dict(os.environ if environ is None else environ)
    python_path = Path(python_executable or sys.executable).resolve()
    resolved_git = git_executable
    if resolved_git is None:
        resolved_git = _resolve_git_executable(None, source)
    git_path = Path(resolved_git).resolve()
    temp_path = Path(temp_directory).resolve()
    if not temp_path.is_dir():
        raise VerificationError(
            "check_environment",
            "external Check temp directory is missing",
        )
    environment = _minimal_process_environment(source)
    path_parts = [str(python_path.parent), str(git_path.parent)]
    system_root = environment.get("SystemRoot") or environment.get("SYSTEMROOT")
    if system_root:
        path_parts.append(str(Path(system_root) / "System32"))
    environment.update(
        {
            "PATH": os.pathsep.join(dict.fromkeys(path_parts)),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
            "GCM_INTERACTIVE": "Never",
            "GIT_CONFIG_COUNT": "5" if git_safe_directory is not None else "4",
            "GIT_CONFIG_KEY_0": "core.longpaths",
            "GIT_CONFIG_VALUE_0": "true",
            "GIT_CONFIG_KEY_1": "core.autocrlf",
            "GIT_CONFIG_VALUE_1": "false",
            "GIT_CONFIG_KEY_2": "credential.interactive",
            "GIT_CONFIG_VALUE_2": "false",
            "GIT_CONFIG_KEY_3": "core.hooksPath",
            "GIT_CONFIG_VALUE_3": os.devnull,
            "TEMP": str(temp_path),
            "TMP": str(temp_path),
            "TMPDIR": str(temp_path),
            # Some production checks call Path.home().  Bind both platform
            # conventions to the secret-free, Check-owned allocation instead
            # of inheriting the operator's real profile directory.
            "HOME": str(temp_path),
            "USERPROFILE": str(temp_path),
        }
    )
    if git_safe_directory is not None:
        environment.update(
            {
                "GIT_CONFIG_KEY_4": "safe.directory",
                "GIT_CONFIG_VALUE_4": str(Path(git_safe_directory).resolve()),
            }
        )
    return environment


def _hostile_check_git_probe(
    workspace: GitWorkspace,
    *,
    allocation: CheckTempAllocation,
    environment: dict[str, str],
    termination_grace_seconds: float,
) -> None:
    """Exercise Git bootstrap and a long tracked descendant below the real allocation."""

    repository = allocation.path / CHECK_TEMP_GIT_BOOTSTRAP_SUFFIX[0]
    try:
        repository.mkdir(parents=False, exist_ok=False)
    except OSError as exc:
        raise VerificationError(
            "check_environment",
            "hostile external Check Git probe repository is unavailable",
        ) from exc
    leaf = "probe.txt"
    descendant = repository
    while len(str(descendant / leaf)) < CHECK_TEMP_HOSTILE_TRACKED_PATH_LENGTH:
        remaining = CHECK_TEMP_HOSTILE_TRACKED_PATH_LENGTH - len(str(descendant / leaf)) - 1
        descendant /= "g" * min(max(remaining, 1), 40)
    try:
        descendant.mkdir(parents=True, exist_ok=False)
        probe_file = descendant / leaf
        probe_file.write_text("hostile external Check Git probe\n", encoding="utf-8")
    except OSError as exc:
        raise VerificationError(
            "check_environment",
            "hostile external Check tracked path is unavailable",
        ) from exc
    relative = probe_file.relative_to(repository).as_posix()
    commands = (
        ("git_init", [str(workspace.git_executable), "-C", str(repository), "init", "-q"]),
        ("git_add", [str(workspace.git_executable), "-C", str(repository), "add", "--", relative]),
        (
            "git_status",
            [
                str(workspace.git_executable),
                "-C",
                str(repository),
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
            ],
        ),
    )
    for stage, command in commands:
        try:
            completed, timed_out = _run_bounded_check_process(
                command,
                cwd=workspace.root,
                timeout_seconds=30,
                termination_grace_seconds=termination_grace_seconds,
                environment=environment,
            )
        except OSError as exc:
            raise VerificationError(
                "check_environment",
                f"hostile external Check Git probe could not run ({stage})",
            ) from exc
        if timed_out or completed.returncode != 0:
            stderr_sha256 = sha256_bytes((completed.stderr or "").encode("utf-8"))
            raise VerificationError(
                "check_environment",
                (
                    "hostile external Check Git probe failed "
                    f"({stage}, exit={completed.returncode}, stderr_sha256={stderr_sha256})"
                ),
            )
    if relative not in (completed.stdout or ""):
        raise VerificationError(
            "check_environment",
            "hostile external Check Git probe did not stage the tracked descendant",
        )


def preflight_check_environment(
    workspace: GitWorkspace,
    *,
    temp_root: Path,
    hostile_git_probe: bool = False,
    termination_grace_seconds: float = DEFAULT_CHECK_TERMINATION_GRACE_SECONDS,
) -> None:
    """Fail before model dispatch unless a Check subprocess can use its temp root."""

    if hostile_git_probe:
        validate_external_check_temp_root(
            temp_root,
            forbidden_roots=(),
            required_allocation_suffixes=(CHECK_TEMP_GIT_BOOTSTRAP_SUFFIX,),
        )
    with isolated_check_temp_directory(temp_root) as allocation:
        environment = build_check_environment(
            temp_directory=allocation.path,
            git_executable=workspace.git_executable,
            git_safe_directory=workspace.root,
        )
        probe = (
            "import os,tempfile;"
            "p=tempfile.NamedTemporaryFile(delete=True);"
            "assert os.path.commonpath([os.path.realpath(p.name),os.path.realpath(os.environ['TEMP'])])"
            "==os.path.realpath(os.environ['TEMP']);"
            "p.close()"
        )
        try:
            completed, timed_out = _run_bounded_check_process(
                [str(Path(sys.executable).resolve()), "-c", probe],
                cwd=workspace.root,
                timeout_seconds=10,
                termination_grace_seconds=termination_grace_seconds,
                environment=environment,
            )
        except OSError as exc:
            raise VerificationError(
                "check_environment",
                "external Check temp probe could not run",
            ) from exc
        if timed_out or completed.returncode != 0:
            raise VerificationError(
                "check_environment",
                "external Check temp probe failed",
            )
        if hostile_git_probe:
            _hostile_check_git_probe(
                workspace,
                allocation=allocation,
                environment=environment,
                termination_grace_seconds=termination_grace_seconds,
            )


def resolve_check_argv(argv: list[str], *, git_executable: Path) -> list[str]:
    """Bind bare tool names whose identity is part of the Check contract."""

    resolved = list(argv)
    if resolved[0].casefold() in {"python", "python.exe"}:
        resolved[0] = str(Path(sys.executable).resolve())
    elif resolved[0].casefold() in {"git", "git.exe"}:
        resolved[0] = str(Path(git_executable).resolve())
    return resolved


def _terminate_check_process_tree(
    process: subprocess.Popen[str],
    *,
    grace_seconds: float,
    windows_job_handle: int | None = None,
) -> None:
    """Terminate the complete Check process tree within a bounded grace period."""

    grace = max(float(grace_seconds), 0.0)
    if os.name == "nt":
        if windows_job_handle is not None:
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
            kernel32.TerminateJobObject.restype = wintypes.BOOL
            handle = wintypes.HANDLE(windows_job_handle)
            if not kernel32.TerminateJobObject(handle, 1):
                raise OSError(ctypes.get_last_error(), "TerminateJobObject failed")
            deadline = time.monotonic() + grace
            while _windows_job_active_processes(windows_job_handle) != 0:
                if time.monotonic() >= deadline:
                    raise OSError(
                        "Check Job still has active processes after termination grace"
                    )
                time.sleep(min(0.01, max(0.0, deadline - time.monotonic())))
        # The Check root is launched in its own process group, but CTRL_BREAK is
        # cooperative and the root can exit before its pytest/Git descendants.
        # taskkill /T walks the tree while the root still exists and /F makes
        # cleanup independent of the child application's signal handling.
        else:
            taskkill = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "taskkill.exe"
            try:
                completed = subprocess.run(
                    [str(taskkill), "/PID", str(process.pid), "/T", "/F"],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=max(grace, 1.0),
                    shell=False,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired):
                completed = None
            if completed is None or completed.returncode != 0:
                try:
                    process.kill()
                except OSError:
                    pass
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        if grace:
            try:
                process.wait(timeout=grace)
            except subprocess.TimeoutExpired:
                pass
        # Even if the group leader already exited, kill any descendant that
        # ignored SIGTERM before relinquishing the Check-owned TEMP directory.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    try:
        process.wait(timeout=max(grace, 1.0))
    except subprocess.TimeoutExpired:
        try:
            process.kill()
        except OSError:
            pass
        process.wait(timeout=max(grace, 1.0))


def _windows_job_active_processes(job_handle: int) -> int:
    """Return the number of processes that Windows still accounts to a Job."""

    import ctypes
    from ctypes import wintypes

    class JOBOBJECT_BASIC_ACCOUNTING_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("TotalUserTime", ctypes.c_longlong),
            ("TotalKernelTime", ctypes.c_longlong),
            ("ThisPeriodTotalUserTime", ctypes.c_longlong),
            ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
            ("TotalPageFaultCount", wintypes.DWORD),
            ("TotalProcesses", wintypes.DWORD),
            ("ActiveProcesses", wintypes.DWORD),
            ("TotalTerminatedProcesses", wintypes.DWORD),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.QueryInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.c_void_p,
    ]
    kernel32.QueryInformationJobObject.restype = wintypes.BOOL
    information = JOBOBJECT_BASIC_ACCOUNTING_INFORMATION()
    if not kernel32.QueryInformationJobObject(
        wintypes.HANDLE(job_handle),
        1,
        ctypes.byref(information),
        ctypes.sizeof(information),
        None,
    ):
        raise OSError(ctypes.get_last_error(), "QueryInformationJobObject failed")
    return int(information.ActiveProcesses)


def _create_windows_kill_on_close_job() -> int:
    """Create a Windows Job whose close operation kills every descendant."""

    import ctypes
    from ctypes import wintypes

    class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    kernel32.SetInformationJobObject.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    handle = kernel32.CreateJobObjectW(None, None)
    if not handle:
        raise OSError(ctypes.get_last_error(), "CreateJobObjectW failed")
    information = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    information.BasicLimitInformation.LimitFlags = 0x00002000
    if not kernel32.SetInformationJobObject(
        handle,
        9,
        ctypes.byref(information),
        ctypes.sizeof(information),
    ):
        error = ctypes.get_last_error()
        kernel32.CloseHandle(handle)
        raise OSError(error, "SetInformationJobObject failed")
    return int(handle)


def _assign_and_resume_windows_job(
    process: subprocess.Popen[str],
    job_handle: int,
) -> None:
    """Bind a CREATE_SUSPENDED process to its Job before it can spawn children."""

    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    process_handle = wintypes.HANDLE(int(process._handle))  # type: ignore[attr-defined]
    if not kernel32.AssignProcessToJobObject(
        wintypes.HANDLE(job_handle),
        process_handle,
    ):
        raise OSError(ctypes.get_last_error(), "AssignProcessToJobObject failed")
    ntdll = ctypes.WinDLL("ntdll")
    ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
    ntdll.NtResumeProcess.restype = wintypes.LONG
    status = int(ntdll.NtResumeProcess(process_handle))
    if status != 0:
        raise OSError(status, "NtResumeProcess failed")


def _close_windows_job(job_handle: int) -> None:
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    if not kernel32.CloseHandle(wintypes.HANDLE(job_handle)):
        raise OSError(ctypes.get_last_error(), "CloseHandle for Check Job failed")


def _posix_process_group_has_members(process_group_id: int) -> bool:
    try:
        os.killpg(process_group_id, 0)
        return True
    except ProcessLookupError:
        return False


def _run_bounded_check_process(
    argv: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    timeout_seconds: float,
    termination_grace_seconds: float,
) -> tuple[subprocess.CompletedProcess[str], bool]:
    """Run one Check in an isolated process group and reap its tree on timeout."""

    popen_options: dict[str, Any] = {}
    windows_job_handle: int | None = None
    if os.name == "nt":
        windows_job_handle = _create_windows_kill_on_close_job()
        popen_options["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | WINDOWS_CREATE_SUSPENDED
        )
    else:
        popen_options["start_new_session"] = True
    try:
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            env=environment,
            **popen_options,
        )
        try:
            def terminate_owned_process_tree() -> None:
                nonlocal windows_job_handle
                handle = windows_job_handle
                try:
                    _terminate_check_process_tree(
                        process,
                        grace_seconds=termination_grace_seconds,
                        windows_job_handle=handle,
                    )
                finally:
                    if handle is not None:
                        try:
                            _close_windows_job(handle)
                        finally:
                            windows_job_handle = None

            if windows_job_handle is not None:
                _assign_and_resume_windows_job(process, windows_job_handle)
            try:
                stdout, stderr = process.communicate(timeout=timeout_seconds)
                timed_out = False
            except subprocess.TimeoutExpired:
                timed_out = True
                terminate_owned_process_tree()
                try:
                    stdout, stderr = process.communicate(
                        timeout=max(float(termination_grace_seconds), 1.0)
                    )
                except subprocess.TimeoutExpired as exc:
                    raise OSError(
                        "Check process streams did not close after tree termination"
                    ) from exc
            if not timed_out:
                active_descendants = (
                    windows_job_handle is not None
                    and _windows_job_active_processes(windows_job_handle) != 0
                ) or (
                    os.name != "nt" and _posix_process_group_has_members(process.pid)
                )
                if active_descendants:
                    terminate_owned_process_tree()
                    raise OSError("Check process left active descendants")
        except BaseException:
            if windows_job_handle is not None or (
                os.name != "nt" and _posix_process_group_has_members(process.pid)
            ):
                terminate_owned_process_tree()
            raise
    finally:
        if windows_job_handle is not None:
            _close_windows_job(windows_job_handle)
    return subprocess.CompletedProcess(
        argv,
        process.returncode,
        stdout or "",
        stderr or "",
    ), timed_out


def _check_failure_classification(
    *,
    state: CheckState,
    stdout: str,
    stderr: str,
) -> tuple[CheckFailureClassification | None, str]:
    if state is CheckState.PASSED:
        return None, "passed"
    if state is CheckState.ERROR:
        return CheckFailureClassification.ENVIRONMENT, "controller_runtime"
    markers = {
        line[len(CHECK_FAILURE_CLASS_PREFIX):].strip()
        for stream in (stdout, stderr)
        for line in stream.splitlines()
        if line.startswith(CHECK_FAILURE_CLASS_PREFIX)
    }
    allowed = {value.value for value in CheckFailureClassification}
    if len(markers) == 1 and next(iter(markers)) in allowed:
        return CheckFailureClassification(next(iter(markers))), "check_protocol"
    return CheckFailureClassification.UNKNOWN, "unclassified"


def run_command_check(
    check_name: str,
    check: CommandCheck,
    workspace: GitWorkspace,
    *,
    temp_root: Path,
    termination_grace_seconds: float = DEFAULT_CHECK_TERMINATION_GRACE_SECONDS,
) -> CheckResult:
    cwd = (workspace.root / check.cwd).resolve()
    if workspace.root not in cwd.parents and cwd != workspace.root:
        raise VerificationError("check", f"Check cwd escaped repository: {check.cwd}")
    started = utc_now()
    try:
        execution_argv = resolve_check_argv(
            check.argv,
            git_executable=workspace.git_executable,
        )
        with isolated_check_temp_directory(temp_root) as allocation:
            completed, timed_out = _run_bounded_check_process(
                execution_argv,
                cwd=cwd,
                timeout_seconds=check.timeout_seconds,
                termination_grace_seconds=termination_grace_seconds,
                environment=build_check_environment(
                    temp_directory=allocation.path,
                    git_executable=workspace.git_executable,
                    git_safe_directory=workspace.root,
                ),
            )
        if timed_out:
            return CheckResult(
                check_name=check_name,
                state=CheckState.ERROR,
                argv=check.argv,
                exit_code=None,
                stdout=completed.stdout,
                stderr=completed.stderr + "\ncheck timed out",
                started_at=started,
                ended_at=utc_now(),
                failure_classification=CheckFailureClassification.ENVIRONMENT,
                failure_classification_source="controller_runtime",
                temp_root=str(allocation.root),
                temp_allocation_id=allocation.allocation_id,
            )
        state = CheckState.PASSED if completed.returncode in check.expected_exit_codes else CheckState.FAILED
        failure_classification, classification_source = _check_failure_classification(
            state=state,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
        return CheckResult(
            check_name=check_name,
            state=state,
            argv=check.argv,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            started_at=started,
            ended_at=utc_now(),
            failure_classification=failure_classification,
            failure_classification_source=classification_source,
            temp_root=str(allocation.root),
            temp_allocation_id=allocation.allocation_id,
        )
    except OSError as exc:
        return CheckResult(
            check_name=check_name,
            state=CheckState.ERROR,
            argv=check.argv,
            exit_code=None,
            stdout="",
            stderr=f"{type(exc).__name__}: {exc}",
            started_at=started,
            ended_at=utc_now(),
            failure_classification=CheckFailureClassification.ENVIRONMENT,
            failure_classification_source="controller_runtime",
            temp_root=str(Path(temp_root).resolve()),
            temp_allocation_id="unallocated-or-cleaned",
        )


def scan_state_for_secrets(state_root: Path) -> list[str]:
    patterns = [
        re_compile.encode("ascii")
        for re_compile in [r"sk-[A-Za-z0-9_-]{12,}", r'(?i)"(?:access_token|refresh_token|api_key)"\s*:\s*"[^\"]+"']
    ]
    import re

    compiled = [re.compile(pattern) for pattern in patterns]
    findings: list[str] = []
    for path in Path(state_root).rglob("*"):
        if not path.is_file() or path.name == "controller.lock" or path.name.endswith(("-wal", "-shm")):
            continue
        try:
            data = path.read_bytes()
        except OSError:
            findings.append(path.relative_to(state_root).as_posix() + " (unreadable)")
            continue
        if any(pattern.search(data) for pattern in compiled):
            findings.append(path.relative_to(state_root).as_posix())
    return sorted(findings)
