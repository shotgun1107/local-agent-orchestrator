"""Workspace, Artifact, fingerprint, scope, and deterministic Check verification."""

from __future__ import annotations

import fnmatch
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
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
CHECK_TEMP_MARKER = ".lao-check-allocation"
WINDOWS_LEGACY_PATH_LIMIT = 260


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


def preflight_check_environment(workspace: GitWorkspace, *, temp_root: Path) -> None:
    """Fail before model dispatch unless a Check subprocess can use its temp root."""

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
            completed = subprocess.run(
                [str(Path(sys.executable).resolve()), "-c", probe],
                cwd=workspace.root,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                shell=False,
                env=environment,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise VerificationError(
                "check_environment",
                "external Check temp probe could not run",
            ) from exc
        if completed.returncode != 0:
            raise VerificationError(
                "check_environment",
                "external Check temp probe failed",
            )


def resolve_check_argv(argv: list[str], *, git_executable: Path) -> list[str]:
    """Bind bare tool names whose identity is part of the Check contract."""

    resolved = list(argv)
    if resolved[0].casefold() in {"python", "python.exe"}:
        resolved[0] = str(Path(sys.executable).resolve())
    elif resolved[0].casefold() in {"git", "git.exe"}:
        resolved[0] = str(Path(git_executable).resolve())
    return resolved


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
            completed = subprocess.run(
                execution_argv,
                cwd=cwd,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=check.timeout_seconds,
                shell=False,
                env=build_check_environment(
                    temp_directory=allocation.path,
                    git_executable=workspace.git_executable,
                    git_safe_directory=workspace.root,
                ),
                check=False,
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
    except subprocess.TimeoutExpired as exc:
        return CheckResult(
            check_name=check_name,
            state=CheckState.ERROR,
            argv=check.argv,
            exit_code=None,
            stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
            stderr=((exc.stderr or "") if isinstance(exc.stderr, str) else "") + "\ncheck timed out",
            started_at=started,
            ended_at=utc_now(),
            failure_classification=CheckFailureClassification.ENVIRONMENT,
            failure_classification_source="controller_runtime",
            temp_root=str(Path(temp_root).resolve()),
            temp_allocation_id="unallocated-or-cleaned",
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
