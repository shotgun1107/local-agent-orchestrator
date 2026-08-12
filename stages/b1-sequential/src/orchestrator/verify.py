"""Workspace, Artifact, fingerprint, scope, and deterministic Check verification."""

from __future__ import annotations

import fnmatch
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from pydantic import ValidationError

from .contract import (
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


class VerificationError(RuntimeError):
    def __init__(self, stage: str, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.stage = stage
        self.retryable = retryable


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
    def __init__(self, root: Path):
        self.root = Path(root).resolve()

    def _git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=self.root,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            shell=False,
            check=check,
        )

    def doctor(self) -> dict[str, Any]:
        result = self._git("rev-parse", "--show-toplevel", check=False)
        if result.returncode != 0:
            return {"healthy": False, "reason": "not_git_repository"}
        actual = Path(result.stdout.strip()).resolve()
        return {"healthy": actual == self.root, "repository_root": str(actual)}

    def head_revision(self) -> str:
        result = self._git("rev-parse", "HEAD", check=False)
        return result.stdout.strip() if result.returncode == 0 else "UNBORN"

    def status(self) -> dict[str, Any]:
        result = self._git("status", "--porcelain=v1", "--untracked-files=normal")
        lines = [line for line in result.stdout.splitlines() if line]
        return {"clean": not lines, "entries": lines}

    def list_files(self, path_scopes: Iterable[str] | None = None) -> list[str]:
        result = subprocess.run(
            ["git", "ls-files", "-co", "--exclude-standard", "-z"],
            cwd=self.root,
            capture_output=True,
            shell=False,
            check=True,
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


def build_check_environment(
    *,
    python_executable: Path | None = None,
    git_executable: Path | None = None,
    environ: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build the deterministic, secret-free environment used by command Checks."""

    source = os.environ if environ is None else environ
    python_path = Path(python_executable or sys.executable).resolve()
    resolved_git = git_executable
    if resolved_git is None:
        discovered = shutil.which("git", path=source.get("PATH"))
        if not discovered:
            raise VerificationError("check_environment", "Git executable is unavailable")
        resolved_git = Path(discovered)
    git_path = Path(resolved_git).resolve()
    keep = ("SystemRoot", "WINDIR", "COMSPEC", "TEMP", "TMP", "PATHEXT")
    environment = {key: source[key] for key in keep if key in source}
    path_parts = [str(python_path.parent), str(git_path.parent)]
    if "SystemRoot" in environment:
        path_parts.append(str(Path(environment["SystemRoot"]) / "System32"))
    environment.update(
        {
            "PATH": os.pathsep.join(dict.fromkeys(path_parts)),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
        }
    )
    return environment


def resolve_check_argv(argv: list[str]) -> list[str]:
    """Bind bare tool names whose identity is part of the Check contract."""

    resolved = list(argv)
    if resolved[0].casefold() in {"python", "python.exe"}:
        resolved[0] = str(Path(sys.executable).resolve())
    elif resolved[0].casefold() in {"git", "git.exe"}:
        discovered = shutil.which("git", path=os.environ.get("PATH"))
        if not discovered:
            raise VerificationError("check_environment", "Git executable is unavailable")
        resolved[0] = str(Path(discovered).resolve())
    return resolved


def run_command_check(check_name: str, check: CommandCheck, workspace: GitWorkspace) -> CheckResult:
    cwd = (workspace.root / check.cwd).resolve()
    if workspace.root not in cwd.parents and cwd != workspace.root:
        raise VerificationError("check", f"Check cwd escaped repository: {check.cwd}")
    started = utc_now()
    try:
        execution_argv = resolve_check_argv(check.argv)
        completed = subprocess.run(
            execution_argv,
            cwd=cwd,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=check.timeout_seconds,
            shell=False,
            env=build_check_environment(),
            check=False,
        )
        state = CheckState.PASSED if completed.returncode in check.expected_exit_codes else CheckState.FAILED
        return CheckResult(
            check_name=check_name,
            state=state,
            argv=check.argv,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            started_at=started,
            ended_at=utc_now(),
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
