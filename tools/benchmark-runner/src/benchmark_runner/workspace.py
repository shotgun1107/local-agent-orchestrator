from __future__ import annotations

import hashlib
import os
import shutil
import stat
import subprocess
import tarfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal

import yaml
from pydantic import Field, JsonValue, field_validator, model_validator

from benchmark_runner.contract import StrictModel, validate_relative_path

GitObjectId = Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
CheckId = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")]


class WorkspaceError(RuntimeError):
    pass


class FrozenFixtureSpec(StrictModel):
    id: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9._-]*$")
    path: str
    commit: GitObjectId
    git_tree: GitObjectId
    success_check: CheckId

    _path_is_relative = field_validator("path")(validate_relative_path)


class FrozenManifest(StrictModel):
    schema_version: Literal[1]
    status: str = Field(min_length=1)
    frozen_at: str
    fixtures: list[FrozenFixtureSpec] = Field(min_length=1)
    variants: list[str] = Field(min_length=1)
    repetitions: int = Field(ge=1)
    model: dict[str, JsonValue]
    budgets: dict[str, JsonValue]
    human_intervention: dict[str, JsonValue]
    metrics: list[str] = Field(min_length=1)
    unknown_usage_rule: str = Field(min_length=1)
    failure_rule: str = Field(min_length=1)

    @model_validator(mode="after")
    def fixture_ids_are_unique(self) -> FrozenManifest:
        fixture_ids = [fixture.id for fixture in self.fixtures]
        if len(fixture_ids) != len(set(fixture_ids)):
            raise ValueError("fixture IDs must be unique")
        return self


class CheckCommandSpec(StrictModel):
    kind: Literal["command"]
    argv: list[str] = Field(min_length=1)
    cwd: str
    timeout_seconds: float = Field(gt=0)
    expected_exit_codes: list[int] = Field(min_length=1)

    _cwd_is_relative = field_validator("cwd")(validate_relative_path)


class ChecksFile(StrictModel):
    schema_version: Literal[1]
    checks: dict[CheckId, CheckCommandSpec]


class RunTask(StrictModel):
    key: str = Field(min_length=1)
    goal: str = Field(min_length=1)
    completion_criteria: list[dict[str, JsonValue]]
    depends_on: list[str]
    inputs: list[JsonValue]
    read_scope: list[str]
    write_scope: list[str]
    capability_profile: str = Field(min_length=1)
    workspace_mode: str = Field(min_length=1)
    check_names: list[str]
    approval: str = Field(min_length=1)

    @field_validator("write_scope")
    @classmethod
    def write_scopes_are_supported(cls, values: list[str]) -> list[str]:
        for value in values:
            validate_write_scope(value)
        return values


class BenchmarkRun(StrictModel):
    schema_version: Literal[1]
    request: dict[str, JsonValue]
    completion_criteria: list[dict[str, JsonValue]]
    constraints: list[str]
    assumptions: list[JsonValue]
    tasks: list[RunTask] = Field(min_length=1)


@dataclass(frozen=True)
class PreparedFixture:
    fixture: FrozenFixtureSpec
    workspace: Path
    checks: ChecksFile
    write_scopes: tuple[str, ...]
    protected_hashes: tuple[tuple[str, str], ...]


def _load_yaml(path: Path) -> object:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise WorkspaceError(f"cannot load YAML: {path}") from exc


def load_frozen_manifest(path: Path) -> FrozenManifest:
    return FrozenManifest.model_validate(_load_yaml(path))


def validate_write_scope(value: str) -> str:
    validate_relative_path(value)
    if value == "." or value.endswith("/"):
        raise ValueError("write scope must name a file or end with /**")
    if "*" not in value:
        return value
    if value.endswith("/**") and "*" not in value[:-3]:
        directory = value[:-3]
        if directory and validate_relative_path(directory) == directory:
            return value
    raise ValueError("write scope supports only exact paths and <directory>/**")


def path_matches_write_scope(path: str, scope: str) -> bool:
    validate_relative_path(path)
    validate_write_scope(scope)
    if scope.endswith("/**"):
        prefix = scope[:-3] + "/"
        return path.startswith(prefix) and len(path) > len(prefix)
    return path == scope


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_git(
    git_executable: str,
    repository: Path,
    args: list[str],
    *,
    env: dict[str, str] | None = None,
) -> bytes:
    result = subprocess.run(
        [git_executable, "-C", str(repository), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise WorkspaceError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout


def _safe_extract_fixture(archive: bytes, prefix: str, target: Path) -> None:
    prefix_path = PurePosixPath(prefix)
    if prefix_path.is_absolute() or ".." in prefix_path.parts or str(prefix_path) != prefix:
        raise WorkspaceError("fixture archive prefix is unsafe")
    target.mkdir(parents=True, exist_ok=False)
    seen: set[str] = set()
    seen_platform: set[str] = set()
    with tarfile.open(fileobj=BytesIO(archive), mode="r:") as bundle:
        for member in bundle.getmembers():
            raw_name = member.name.rstrip("/")
            member_path = PurePosixPath(raw_name)
            if (
                not raw_name
                or member_path.is_absolute()
                or ".." in member_path.parts
                or "\\" in raw_name
            ):
                raise WorkspaceError(f"unsafe archive member: {member.name}")
            if member_path == prefix_path:
                if not member.isdir():
                    raise WorkspaceError("fixture archive prefix must be a directory")
                continue
            if prefix_path.is_relative_to(member_path):
                if not member.isdir():
                    raise WorkspaceError("fixture archive ancestor must be a directory")
                continue
            try:
                relative = member_path.relative_to(prefix_path)
            except ValueError as exc:
                raise WorkspaceError(f"archive member escapes fixture prefix: {member.name}") from exc
            relative_text = relative.as_posix()
            validate_relative_path(relative_text)
            platform_key = relative_text.casefold() if os.name == "nt" else relative_text
            if relative_text in seen or platform_key in seen_platform:
                raise WorkspaceError(f"duplicate archive member: {relative_text}")
            seen.add(relative_text)
            seen_platform.add(platform_key)
            destination = target.joinpath(*relative.parts)
            if member.isdir():
                destination.mkdir(parents=True, exist_ok=False)
                continue
            if not member.isfile() or member.issym() or member.islnk():
                raise WorkspaceError(f"unsupported archive member type: {member.name}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            source = bundle.extractfile(member)
            if source is None:
                raise WorkspaceError(f"cannot read archive member: {member.name}")
            with destination.open("xb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
            executable = bool(member.mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
            destination.chmod(0o755 if executable else 0o644)


def _protected_hashes(workspace: Path) -> tuple[tuple[str, str], ...]:
    paths = [workspace / ".orchestrator" / "checks.yaml"]
    paths.extend(
        sorted(
            path
            for path in (workspace / "benchmark_checks").rglob("*")
            if path.is_file()
        )
    )
    return tuple(
        (path.relative_to(workspace).as_posix(), sha256_file(path))
        for path in paths
    )


class FixtureRestorer:
    def __init__(self, source_repository: Path, git_executable: str = "git") -> None:
        self.source_repository = source_repository.resolve()
        self.git_executable = git_executable

    def verify_source(self, fixture: FrozenFixtureSpec) -> str:
        actual_tree = _run_git(
            self.git_executable,
            self.source_repository,
            ["rev-parse", f"{fixture.commit}:{fixture.path}"],
        ).decode("ascii").strip()
        if actual_tree != fixture.git_tree:
            raise WorkspaceError(
                f"fixture tree mismatch: expected {fixture.git_tree}, got {actual_tree}"
            )
        return actual_tree

    def open_existing(
        self,
        fixture: FrozenFixtureSpec,
        workspace: Path,
        *,
        require_clean: bool = False,
    ) -> PreparedFixture:
        """Reconstruct trusted baseline metadata without rewriting an existing workspace."""

        workspace = workspace.resolve()
        self.verify_source(fixture)
        if not workspace.is_dir() or not (workspace / ".git").is_dir():
            raise WorkspaceError("prepared fixture workspace is missing or is not a Git repository")
        baseline_tree = _run_git(
            self.git_executable,
            workspace,
            ["rev-parse", "HEAD^{tree}"],
        ).decode("ascii").strip()
        if baseline_tree != fixture.git_tree:
            raise WorkspaceError(
                f"prepared baseline tree mismatch: expected {fixture.git_tree}, got {baseline_tree}"
            )
        if require_clean and _run_git(
            self.git_executable,
            workspace,
            ["status", "--porcelain"],
        ):
            raise WorkspaceError("prepared fixture worktree is not clean")
        checks = ChecksFile.model_validate(
            _load_yaml(workspace / ".orchestrator" / "checks.yaml")
        )
        benchmark_run = BenchmarkRun.model_validate(
            _load_yaml(workspace / "benchmark-run.yaml")
        )
        if fixture.success_check not in checks.checks:
            raise WorkspaceError(f"missing success Check: {fixture.success_check}")
        if fixture.success_check == "diff_check":
            raise WorkspaceError("success Check and diff_check must be distinct")
        if "diff_check" not in checks.checks:
            raise WorkspaceError("missing diff_check")
        scopes = tuple(
            dict.fromkeys(scope for task in benchmark_run.tasks for scope in task.write_scope)
        )
        return PreparedFixture(
            fixture=fixture,
            workspace=workspace,
            checks=checks,
            write_scopes=scopes,
            protected_hashes=_protected_hashes(workspace),
        )

    def restore(self, fixture: FrozenFixtureSpec, workspace: Path) -> PreparedFixture:
        workspace = workspace.resolve()
        self.verify_source(fixture)
        archive = _run_git(
            self.git_executable,
            self.source_repository,
            ["archive", "--format=tar", fixture.commit, "--", fixture.path],
        )
        _safe_extract_fixture(archive, fixture.path, workspace)

        _run_git(self.git_executable, workspace, ["init", "-q", "-b", "main"])
        _run_git(self.git_executable, workspace, ["config", "user.name", "benchmark-runner"])
        _run_git(
            self.git_executable,
            workspace,
            ["config", "user.email", "benchmark@local.invalid"],
        )
        _run_git(self.git_executable, workspace, ["add", "-A"])
        restored_tree = _run_git(
            self.git_executable,
            workspace,
            ["write-tree"],
        ).decode("ascii").strip()
        if restored_tree != fixture.git_tree:
            raise WorkspaceError(
                f"restored tree mismatch: expected {fixture.git_tree}, got {restored_tree}"
            )
        commit_env = os.environ.copy()
        commit_env.update(
            {
                "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
                "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z",
            }
        )
        _run_git(
            self.git_executable,
            workspace,
            ["commit", "-q", "-m", "benchmark baseline"],
            env=commit_env,
        )
        if _run_git(self.git_executable, workspace, ["status", "--porcelain"]):
            raise WorkspaceError("restored fixture worktree is not clean")

        return self.open_existing(fixture, workspace, require_clean=True)
