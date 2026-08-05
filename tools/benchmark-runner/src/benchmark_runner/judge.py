from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO, Literal

from pydantic import Field

from benchmark_runner.adapter import VariantEvidence
from benchmark_runner.contract import StrictModel
from benchmark_runner.workspace import (
    CheckCommandSpec,
    GitObjectId,
    PreparedFixture,
    path_matches_write_scope,
    sha256_file,
    validate_relative_path,
)

STREAM_LIMIT_BYTES = 1024 * 1024
TERMINATION_GRACE_SECONDS = 5.0


class StreamResult(StrictModel):
    path: str
    stored_bytes: int
    total_bytes: int
    sha256: str
    truncated: bool


class CheckResult(StrictModel):
    check_id: str
    status: Literal["passed", "failed", "timed_out", "infrastructure_error"]
    exit_code: int | None
    duration_seconds: float
    stdout: StreamResult
    stderr: StreamResult


class FileResult(StrictModel):
    path: str
    size: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class JudgeResult(StrictModel):
    judge_kind: Literal["r0_stub", "fixture_v1"] = "r0_stub"
    check_success: bool
    failed_check_ids: list[str]
    scope_violations: list[str] = Field(default_factory=list)
    changed_paths: list[str] = Field(default_factory=list)
    check_results: list[CheckResult] = Field(default_factory=list)
    judge_workspace_unchanged: bool = True
    baseline_tree: GitObjectId | None = None
    final_tree: GitObjectId | None = None
    final_diff: FileResult | None = None


class StubJudge:
    def evaluate(self, evidence: VariantEvidence) -> JudgeResult:
        success = evidence.outcome_state == "completed"
        return JudgeResult(
            check_success=success,
            failed_check_ids=[] if success else ["runner_judge:r0_stub"],
        )


@dataclass
class _StreamAccumulator:
    limit: int
    digest: Any = field(default_factory=hashlib.sha256)
    stored: bytearray = field(default_factory=bytearray)
    total: int = 0
    error: BaseException | None = None

    def consume(self, stream: BinaryIO) -> None:
        try:
            for chunk in iter(lambda: stream.read(64 * 1024), b""):
                self.total += len(chunk)
                self.digest.update(chunk)
                remaining = self.limit - len(self.stored)
                if remaining > 0:
                    self.stored.extend(chunk[:remaining])
        except BaseException as exc:  # pragma: no cover - defensive thread boundary
            self.error = exc
        finally:
            stream.close()


def _minimal_environment(benchmark_python: Path, git_executable: Path) -> dict[str, str]:
    keep = ("SystemRoot", "WINDIR", "COMSPEC", "TEMP", "TMP", "PATHEXT")
    environment = {key: os.environ[key] for key in keep if key in os.environ}
    path_parts = [str(benchmark_python.parent), str(git_executable.parent)]
    if "SystemRoot" in environment:
        path_parts.append(str(Path(environment["SystemRoot"]) / "System32"))
    environment.update(
        {
            "PATH": os.pathsep.join(dict.fromkeys(path_parts)),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
        }
    )
    return environment


def _terminate_process_group(process: subprocess.Popen[bytes], grace_seconds: float) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        try:
            process.send_signal(signal.CTRL_BREAK_EVENT)
        except (OSError, ValueError):
            process.terminate()
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
    try:
        process.wait(timeout=grace_seconds)
        return
    except subprocess.TimeoutExpired:
        pass
    if os.name == "nt":
        taskkill = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "taskkill.exe"
        try:
            subprocess.run(
                [str(taskkill), "/PID", str(process.pid), "/T", "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=grace_seconds,
            )
        except subprocess.TimeoutExpired:
            process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=grace_seconds)


def _status_paths(git_executable: Path, workspace: Path) -> list[str]:
    result = subprocess.run(
        [
            str(git_executable),
            "-C",
            str(workspace),
            "status",
            "--porcelain=v2",
            "-z",
            "--untracked-files=all",
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"cannot inspect fixture worktree: {detail}")
    records = result.stdout.split(b"\0")
    paths: list[str] = []
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        additional_paths: list[bytes] = []
        if not record:
            continue
        if record.startswith(b"1 "):
            raw_path = record.split(b" ", 8)[8]
        elif record.startswith(b"2 "):
            fields = record.split(b" ", 9)
            raw_path = fields[9]
            if index >= len(records) or not records[index]:
                raise RuntimeError("incomplete git rename/copy status record")
            if fields[8].startswith(b"R"):
                additional_paths.append(records[index])
            index += 1  # rename/copy source path is the following NUL record
        elif record.startswith(b"u "):
            raw_path = record.split(b" ", 10)[10]
        elif record.startswith(b"? "):
            raw_path = record[2:]
        elif record.startswith(b"! "):
            continue
        else:
            raise RuntimeError("unsupported git status porcelain v2 record")
        path = raw_path.decode("utf-8", errors="strict")
        validate_relative_path(path)
        paths.append(path)
        for additional_path in additional_paths:
            decoded = additional_path.decode("utf-8", errors="strict")
            validate_relative_path(decoded)
            paths.append(decoded)
    return sorted(set(paths))


def _has_symlink_component(workspace: Path, relative_path: str) -> bool:
    cursor = workspace
    for part in Path(relative_path).parts:
        cursor /= part
        if cursor.is_symlink():
            return True
    return False


def _git_bytes(
    git_executable: Path,
    workspace: Path,
    args: list[str],
    *,
    env: dict[str, str] | None = None,
) -> bytes:
    result = subprocess.run(
        [str(git_executable), "-C", str(workspace), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout


def _snapshot_workspace(
    git_executable: Path,
    workspace: Path,
    judge_dir: Path,
) -> tuple[str, FileResult]:
    judge_dir.mkdir(parents=True, exist_ok=True)
    temporary_index = judge_dir / f".final-index.{uuid.uuid4().hex}"
    environment = os.environ.copy()
    environment["GIT_INDEX_FILE"] = str(temporary_index)
    try:
        _git_bytes(git_executable, workspace, ["read-tree", "HEAD"], env=environment)
        _git_bytes(git_executable, workspace, ["add", "-A"], env=environment)
        final_tree = _git_bytes(
            git_executable,
            workspace,
            ["write-tree"],
            env=environment,
        ).decode("ascii").strip()
        diff = _git_bytes(
            git_executable,
            workspace,
            ["diff", "--binary", "--no-ext-diff", "HEAD", final_tree],
            env=environment,
        )
    finally:
        temporary_index.unlink(missing_ok=True)
        temporary_index.with_suffix(temporary_index.suffix + ".lock").unlink(missing_ok=True)
    diff_path = judge_dir / "final.diff"
    diff_path.write_bytes(diff)
    return final_tree, FileResult(
        path=diff_path.relative_to(judge_dir).as_posix(),
        size=len(diff),
        sha256=hashlib.sha256(diff).hexdigest(),
    )


def _write_result(judge_dir: Path, result: JudgeResult) -> None:
    data = (
        json.dumps(
            result.model_dump(mode="json"),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    judge_dir.mkdir(parents=True, exist_ok=True)
    path = judge_dir / "result.json"
    temporary = judge_dir / f".{path.name}.{uuid.uuid4().hex}.tmp"
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class FixtureJudge:
    def __init__(
        self,
        benchmark_python: Path,
        git_executable: Path | None = None,
        *,
        stream_limit_bytes: int = STREAM_LIMIT_BYTES,
        termination_grace_seconds: float = TERMINATION_GRACE_SECONDS,
    ) -> None:
        self.benchmark_python = benchmark_python.resolve()
        resolved_git = git_executable or Path(shutil.which("git") or "")
        if not self.benchmark_python.is_file():
            raise ValueError("benchmark Python does not exist")
        if not resolved_git or not resolved_git.resolve().is_file():
            raise ValueError("Git executable does not exist")
        if stream_limit_bytes < 1:
            raise ValueError("stream limit must be positive")
        if termination_grace_seconds <= 0:
            raise ValueError("termination grace must be positive")
        self.git_executable = resolved_git.resolve()
        self.stream_limit_bytes = stream_limit_bytes
        self.termination_grace_seconds = termination_grace_seconds

    def _run_check(
        self,
        check_id: str,
        check: CheckCommandSpec,
        workspace: Path,
        judge_dir: Path,
    ) -> CheckResult:
        command = list(check.argv)
        if command[0] == "python":
            command[0] = str(self.benchmark_python)
        elif command[0] == "git":
            command[0] = str(self.git_executable)
        else:
            raise RuntimeError(f"unsupported R1 Check executable: {command[0]}")
        cwd = (workspace / check.cwd).resolve()
        if not cwd.is_relative_to(workspace) or not cwd.is_dir():
            raise RuntimeError(f"unsafe Check cwd: {check.cwd}")
        environment = _minimal_environment(self.benchmark_python, self.git_executable)
        popen_options: dict[str, object] = {}
        if os.name == "nt":
            popen_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            popen_options["start_new_session"] = True
        started = time.monotonic()
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **popen_options,
        )
        assert process.stdout is not None and process.stderr is not None
        stdout = _StreamAccumulator(self.stream_limit_bytes)
        stderr = _StreamAccumulator(self.stream_limit_bytes)
        threads = [
            threading.Thread(target=stdout.consume, args=(process.stdout,), daemon=True),
            threading.Thread(target=stderr.consume, args=(process.stderr,), daemon=True),
        ]
        for thread in threads:
            thread.start()
        timed_out = False
        try:
            process.wait(timeout=check.timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            _terminate_process_group(process, self.termination_grace_seconds)
        for thread in threads:
            thread.join(timeout=self.termination_grace_seconds)
        if any(thread.is_alive() for thread in threads) or stdout.error or stderr.error:
            raise RuntimeError("failed to capture Check output")
        duration = time.monotonic() - started
        judge_dir.mkdir(parents=True, exist_ok=True)
        stdout_path = judge_dir / f"{check_id}.stdout.txt"
        stderr_path = judge_dir / f"{check_id}.stderr.txt"
        stdout_path.write_bytes(bytes(stdout.stored))
        stderr_path.write_bytes(bytes(stderr.stored))

        def summary(path: Path, accumulator: _StreamAccumulator) -> StreamResult:
            return StreamResult(
                path=path.relative_to(judge_dir).as_posix(),
                stored_bytes=len(accumulator.stored),
                total_bytes=accumulator.total,
                sha256=accumulator.digest.hexdigest(),
                truncated=accumulator.total > len(accumulator.stored),
            )

        if timed_out:
            status = "timed_out"
            exit_code = process.returncode
        else:
            exit_code = process.returncode
            status = "passed" if exit_code in check.expected_exit_codes else "failed"
        return CheckResult(
            check_id=check_id,
            status=status,
            exit_code=exit_code,
            duration_seconds=duration,
            stdout=summary(stdout_path, stdout),
            stderr=summary(stderr_path, stderr),
        )

    def evaluate(self, prepared: PreparedFixture, judge_dir: Path) -> JudgeResult:
        workspace = prepared.workspace.resolve()
        judge_dir = judge_dir.resolve()
        if judge_dir.is_relative_to(workspace):
            raise ValueError("Judge Evidence directory must be outside the fixture workspace")

        def finish(
            result: JudgeResult,
            snapshot: tuple[str, FileResult] | None = None,
        ) -> JudgeResult:
            final_tree, final_diff = snapshot or _snapshot_workspace(
                self.git_executable, workspace, judge_dir
            )
            completed = result.model_copy(
                update={
                    "baseline_tree": prepared.fixture.git_tree,
                    "final_tree": final_tree,
                    "final_diff": final_diff,
                }
            )
            _write_result(judge_dir, completed)
            return completed

        actual_baseline_tree = _git_bytes(
            self.git_executable,
            workspace,
            ["rev-parse", "HEAD^{tree}"],
        ).decode("ascii").strip()
        if actual_baseline_tree != prepared.fixture.git_tree:
            return finish(
                JudgeResult(
                    judge_kind="fixture_v1",
                    check_success=False,
                    failed_check_ids=["runner_judge:baseline_tree_integrity"],
                )
            )

        integrity_failures: list[str] = []
        for relative_path, expected_hash in prepared.protected_hashes:
            path = workspace / Path(relative_path)
            if (
                _has_symlink_component(workspace, relative_path)
                or not path.is_file()
                or sha256_file(path) != expected_hash
            ):
                integrity_failures.append(relative_path)
        if integrity_failures:
            return finish(
                JudgeResult(
                    judge_kind="fixture_v1",
                    check_success=False,
                    failed_check_ids=["runner_judge:check_integrity"],
                    scope_violations=integrity_failures,
                    judge_workspace_unchanged=True,
                )
            )

        changed_before = _status_paths(self.git_executable, workspace)
        scope_violations = [
            path
            for path in changed_before
            if path == ".orchestrator/checks.yaml"
            or path.startswith("benchmark_checks/")
            or _has_symlink_component(workspace, path)
            or not any(
                path_matches_write_scope(path, scope) for scope in prepared.write_scopes
            )
        ]
        if scope_violations:
            return finish(
                JudgeResult(
                    judge_kind="fixture_v1",
                    check_success=False,
                    failed_check_ids=["runner_judge:write_scope"],
                    scope_violations=scope_violations,
                    changed_paths=changed_before,
                    judge_workspace_unchanged=True,
                )
            )

        ordered_checks = [prepared.fixture.success_check, "diff_check"]
        worker_tree, _ = _snapshot_workspace(
            self.git_executable,
            workspace,
            judge_dir,
        )
        check_results: list[CheckResult] = []
        failed_check_ids: list[str] = []
        for check_id in ordered_checks:
            result = self._run_check(
                check_id,
                prepared.checks.checks[check_id],
                workspace,
                judge_dir,
            )
            check_results.append(result)
            if result.status != "passed":
                failed_check_ids.append(f"runner_judge:{check_id}")
        changed_after = _status_paths(self.git_executable, workspace)
        final_snapshot = _snapshot_workspace(
            self.git_executable,
            workspace,
            judge_dir,
        )
        workspace_unchanged = (
            changed_after == changed_before and final_snapshot[0] == worker_tree
        )
        if not workspace_unchanged:
            failed_check_ids.append("runner_judge:self_modified_workspace")
        return finish(
            JudgeResult(
                judge_kind="fixture_v1",
                check_success=not failed_check_ids,
                failed_check_ids=failed_check_ids,
                changed_paths=changed_after,
                check_results=check_results,
                judge_workspace_unchanged=workspace_unchanged,
            ),
            final_snapshot,
        )
