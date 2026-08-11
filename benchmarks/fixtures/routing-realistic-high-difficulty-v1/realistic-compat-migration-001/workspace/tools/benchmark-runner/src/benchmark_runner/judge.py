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
from benchmark_runner.contract import StrictModel, utc_now
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
    normalized_transient_paths: list[str] = Field(default_factory=list)
    check_results: list[CheckResult] = Field(default_factory=list)
    judge_workspace_unchanged: bool = True
    baseline_tree: GitObjectId | None = None
    final_tree: GitObjectId | None = None
    final_diff: FileResult | None = None


class JudgeProcessRecord(StrictModel):
    check_id: str
    pid: int = Field(gt=0)
    process_start_identity: str
    process_group_kind: Literal["windows_new_process_group", "posix_session"]
    status: Literal["running", "completed", "recovered_terminated", "already_gone"]
    started_at: str
    completed_at: str | None = None


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


def build_check_environment(benchmark_python: Path, git_executable: Path) -> dict[str, str]:
    keep = ("SystemRoot", "WINDIR", "COMSPEC", "TEMP", "TMP", "PATHEXT")
    environment = {key: os.environ[key] for key in keep if key in os.environ}
    path_parts = [str(benchmark_python.parent), str(git_executable.parent)]
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


def _process_start_identity(pid: int) -> str | None:
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.OpenProcess.restype = wintypes.HANDLE
            handle = kernel32.OpenProcess(0x1000, False, pid)
            if not handle:
                return None
            creation = wintypes.FILETIME()
            exit_time = wintypes.FILETIME()
            kernel_time = wintypes.FILETIME()
            user_time = wintypes.FILETIME()
            try:
                if not kernel32.GetProcessTimes(
                    handle,
                    ctypes.byref(creation),
                    ctypes.byref(exit_time),
                    ctypes.byref(kernel_time),
                    ctypes.byref(user_time),
                ):
                    return None
                value = (creation.dwHighDateTime << 32) | creation.dwLowDateTime
                return f"windows-filetime:{value}"
            finally:
                kernel32.CloseHandle(handle)
        except (AttributeError, OSError, ValueError):
            return None
    proc_stat = Path(f"/proc/{pid}/stat")
    if proc_stat.is_file():
        try:
            value = proc_stat.read_text(encoding="ascii")
            fields = value[value.rfind(")") + 2 :].split()
            return f"proc-start-ticks:{fields[19]}"
        except (OSError, IndexError, ValueError):
            return None
    return None


def _pid_is_alive(pid: int) -> bool:
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.OpenProcess.restype = wintypes.HANDLE
            handle = kernel32.OpenProcess(0x1000, False, pid)
            if not handle:
                return False
            exit_code = wintypes.DWORD()
            try:
                if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                    return False
                return exit_code.value == 259
            finally:
                kernel32.CloseHandle(handle)
        except (AttributeError, OSError, ValueError):
            return False
    proc_status = Path(f"/proc/{pid}/status")
    if proc_status.is_file():
        try:
            state = next(
                line for line in proc_status.read_text(encoding="ascii").splitlines() if line.startswith("State:")
            )
            if "Z" in state.split():
                return False
        except (OSError, StopIteration):
            pass
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _write_process_record(path: Path, record: JudgeProcessRecord) -> None:
    data = json.dumps(
        record.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        for attempt in range(20):
            try:
                os.replace(temporary, path)
                break
            except PermissionError:
                if os.name != "nt" or attempt == 19:
                    raise
                time.sleep(0.01)
    finally:
        temporary.unlink(missing_ok=True)


def _windows_descendant_pids(root_pid: int) -> list[int]:
    if os.name != "nt":
        return []
    try:
        import ctypes
        from ctypes import wintypes

        class ProcessEntry32W(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD),
                ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.c_size_t),
                ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", wintypes.LONG),
                ("dwFlags", wintypes.DWORD),
                ("szExeFile", wintypes.WCHAR * 260),
            ]

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry32W)]
        kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry32W)]
        snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
        invalid_handle = ctypes.c_void_p(-1).value
        if snapshot == invalid_handle:
            return []
        parent_by_pid: dict[int, int] = {}
        entry = ProcessEntry32W()
        entry.dwSize = ctypes.sizeof(entry)
        try:
            ok = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
            while ok:
                parent_by_pid[int(entry.th32ProcessID)] = int(entry.th32ParentProcessID)
                ok = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
        finally:
            kernel32.CloseHandle(snapshot)
        children: dict[int, list[int]] = {}
        for pid, parent in parent_by_pid.items():
            children.setdefault(parent, []).append(pid)
        descendants: list[int] = []

        def visit(parent: int) -> None:
            for child in children.get(parent, []):
                visit(child)
                descendants.append(child)

        visit(root_pid)
        return descendants
    except (AttributeError, OSError, ValueError):
        return []


def _windows_terminate_pid(pid: int) -> None:
    if os.name != "nt" or not _pid_is_alive(pid):
        return
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.restype = wintypes.HANDLE
        handle = kernel32.OpenProcess(0x0001, False, pid)
        if handle:
            try:
                kernel32.TerminateProcess(handle, 15)
            finally:
                kernel32.CloseHandle(handle)
            return
    except (AttributeError, OSError, ValueError):
        pass
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass


def recover_orphan_judge_process(
    judge_dir: Path,
    *,
    grace_seconds: float = TERMINATION_GRACE_SECONDS,
) -> Literal["none", "already_terminal", "already_gone", "terminated"]:
    record_path = judge_dir.resolve() / "active-process.json"
    if not record_path.is_file():
        return "none"
    try:
        record = JudgeProcessRecord.model_validate_json(record_path.read_bytes())
    except (OSError, ValueError) as exc:
        raise RuntimeError("Judge process recovery record is invalid") from exc
    if record.status != "running":
        return "already_terminal"
    identity = _process_start_identity(record.pid)
    if not _pid_is_alive(record.pid) or identity != record.process_start_identity:
        _write_process_record(
            record_path,
            record.model_copy(
                update={"status": "already_gone", "completed_at": utc_now().isoformat()}
            ),
        )
        return "already_gone"
    if os.name == "nt":
        descendants = _windows_descendant_pids(record.pid)
        try:
            os.kill(record.pid, signal.CTRL_BREAK_EVENT)
        except OSError:
            pass
        cooperative_deadline = time.monotonic() + min(1.0, grace_seconds / 2)
        while _pid_is_alive(record.pid) and time.monotonic() < cooperative_deadline:
            time.sleep(0.01)
        taskkill = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "taskkill.exe"
        if _pid_is_alive(record.pid):
            subprocess.run(
                [str(taskkill), "/PID", str(record.pid), "/T", "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=grace_seconds,
            )
        if _pid_is_alive(record.pid):
            try:
                os.kill(record.pid, signal.SIGTERM)
            except OSError:
                pass
        for descendant_pid in descendants:
            _windows_terminate_pid(descendant_pid)
        _windows_terminate_pid(record.pid)
    else:
        descendants = []
        try:
            os.killpg(record.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + grace_seconds
    while (
        _pid_is_alive(record.pid)
        or any(_pid_is_alive(pid) for pid in descendants)
    ) and time.monotonic() < deadline:
        time.sleep(0.01)
    if _pid_is_alive(record.pid) or any(_pid_is_alive(pid) for pid in descendants):
        raise RuntimeError("Judge process group could not be terminated")
    _write_process_record(
        record_path,
        record.model_copy(
            update={"status": "recovered_terminated", "completed_at": utc_now().isoformat()}
        ),
    )
    return "terminated"


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


def _normalize_untracked_python_bytecode(
    git_executable: Path,
    workspace: Path,
    changed_paths: list[str],
) -> list[str]:
    tracked_raw = _git_bytes(
        git_executable,
        workspace,
        ["ls-files", "-z", "--cached"],
    )
    tracked_paths = {
        path.decode("utf-8", errors="strict")
        for path in tracked_raw.split(b"\0")
        if path
    }
    normalized: list[str] = []
    for relative_path in changed_paths:
        path = Path(relative_path)
        if (
            "__pycache__" not in path.parts
            or path.suffix not in {".pyc", ".pyo"}
            or relative_path in tracked_paths
            or _has_symlink_component(workspace, relative_path)
        ):
            continue
        candidate = workspace / path
        if not candidate.is_file():
            continue
        candidate.unlink()
        normalized.append(relative_path)
    return sorted(normalized)


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
        environment = build_check_environment(self.benchmark_python, self.git_executable)
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
        process_identity = _process_start_identity(process.pid)
        if process_identity is None:
            _terminate_process_group(process, self.termination_grace_seconds)
            raise RuntimeError("cannot establish Judge process start identity")
        process_record_path = judge_dir / "active-process.json"
        process_record = JudgeProcessRecord(
            check_id=check_id,
            pid=process.pid,
            process_start_identity=process_identity,
            process_group_kind=(
                "windows_new_process_group" if os.name == "nt" else "posix_session"
            ),
            status="running",
            started_at=utc_now().isoformat(),
        )
        _write_process_record(process_record_path, process_record)
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
        _write_process_record(
            process_record_path,
            process_record.model_copy(
                update={"status": "completed", "completed_at": utc_now().isoformat()}
            ),
        )
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

        normalized_transient_paths: list[str] = []

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
                    "normalized_transient_paths": normalized_transient_paths,
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

        normalized_transient_paths = _normalize_untracked_python_bytecode(
            self.git_executable,
            workspace,
            _status_paths(self.git_executable, workspace),
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
