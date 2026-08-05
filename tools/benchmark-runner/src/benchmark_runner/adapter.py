from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO, Literal, Protocol

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError as JsonSchemaValidationError
from pydantic import JsonValue

from benchmark_runner.contract import OutcomeState


@dataclass(frozen=True)
class VariantCapabilities:
    automated_launch: bool
    supports_usage: bool
    supports_attempt_count: bool


@dataclass(frozen=True)
class CellContext:
    experiment_id: str
    cell_id: str


@dataclass(frozen=True)
class PreflightResult:
    ok: bool
    detail: str


@dataclass(frozen=True)
class VariantEvidence:
    outcome_state: OutcomeState
    failure_kind: str | None
    attempt_count: int
    raw_payload: dict[str, JsonValue]
    normalized_metrics: dict[str, JsonValue] = field(default_factory=dict)


class VariantAdapter(Protocol):
    def id(self) -> str: ...

    def capabilities(self) -> VariantCapabilities: ...

    def preflight(self, context: CellContext) -> PreflightResult: ...

    def run(self, context: CellContext) -> VariantEvidence: ...


class FakeAdapter:
    def __init__(self, outcome: Literal["completed", "failed"] = "completed") -> None:
        self._outcome = outcome

    def id(self) -> str:
        return "fake"

    def capabilities(self) -> VariantCapabilities:
        return VariantCapabilities(
            automated_launch=True,
            supports_usage=False,
            supports_attempt_count=True,
        )
    def preflight(self, context: CellContext) -> PreflightResult:
        return PreflightResult(ok=True, detail=f"R0 fake preflight for {context.cell_id}")

    def run(self, context: CellContext) -> VariantEvidence:
        failed = self._outcome == "failed"
        return VariantEvidence(
            outcome_state=self._outcome,
            failure_kind="fake_requested_failure" if failed else None,
            attempt_count=1,
            raw_payload={
                "adapter_id": self.id(),
                "cell_id": context.cell_id,
                "model_turns": 0,
                "outcome": self._outcome,
                "read_only": True,
            },
        )


class AdapterInfrastructureError(RuntimeError):
    pass


@dataclass(frozen=True)
class CommandCapture:
    exit_code: int
    stdout: str
    stderr: str
    stdout_size: int
    stderr_size: int
    stdout_sha256: str
    stderr_sha256: str
    stdout_truncated: bool
    stderr_truncated: bool

    def public_payload(self) -> dict[str, JsonValue]:
        return {
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "stdout_size": self.stdout_size,
            "stderr_size": self.stderr_size,
            "stdout_sha256": self.stdout_sha256,
            "stderr_sha256": self.stderr_sha256,
            "stdout_truncated": self.stdout_truncated,
            "stderr_truncated": self.stderr_truncated,
        }


@dataclass(frozen=True)
class B1AdapterConfig:
    command_prefix: tuple[str, ...]
    project: Path
    run_spec: Path
    state_root: Path
    schema_root: Path
    runtime: Literal["fake", "codex"] = "fake"
    fake_fixture: Path | None = None
    timeout_seconds: float = 300.0
    stream_limit_bytes: int = 1024 * 1024


class B1SequentialAdapter:
    """B1 CLI adapter; it never imports B1 modules or reads the B1 ledger."""

    def __init__(self, config: B1AdapterConfig) -> None:
        if not config.command_prefix:
            raise ValueError("B1 command prefix cannot be empty")
        if config.timeout_seconds <= 0 or config.stream_limit_bytes < 1:
            raise ValueError("B1 timeout and stream limit must be positive")
        if config.runtime == "fake" and config.fake_fixture is None:
            raise ValueError("B1 FakeRuntime requires a fake fixture")
        self.config = config
        self._validators = {
            "status": self._load_validator(config.schema_root / "run-status.schema.json"),
            "report": self._load_validator(config.schema_root / "run-report.schema.json"),
        }

    @staticmethod
    def _load_validator(path: Path) -> Draft202012Validator:
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
        except (OSError, json.JSONDecodeError, SchemaError) as exc:
            raise AdapterInfrastructureError(f"invalid B1 public Schema: {path}") from exc
        return Draft202012Validator(schema)

    def id(self) -> str:
        return "b1"

    def capabilities(self) -> VariantCapabilities:
        return VariantCapabilities(
            automated_launch=True,
            supports_usage=True,
            supports_attempt_count=True,
        )

    def _environment(self) -> dict[str, str]:
        environment = os.environ.copy()
        environment["LAO_STATE_ROOT"] = str(self.config.state_root.resolve())
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONUTF8"] = "1"
        environment["PYTHONIOENCODING"] = "utf-8"
        if self.config.runtime == "fake":
            environment.pop("OPENAI_API_KEY", None)
        return environment

    def _invoke(self, arguments: list[str]) -> CommandCapture:
        popen_options: dict[str, object] = {}
        if os.name == "nt":
            popen_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            popen_options["start_new_session"] = True
        try:
            with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
                process = subprocess.Popen(
                    [*self.config.command_prefix, *arguments],
                    stdin=subprocess.DEVNULL,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    env=self._environment(),
                    shell=False,
                    **popen_options,
                )
                try:
                    process.wait(timeout=self.config.timeout_seconds)
                except subprocess.TimeoutExpired:
                    if os.name == "nt":
                        taskkill = (
                            Path(os.environ.get("SystemRoot", r"C:\Windows"))
                            / "System32"
                            / "taskkill.exe"
                        )
                        try:
                            subprocess.run(
                                [str(taskkill), "/PID", str(process.pid), "/T", "/F"],
                                check=False,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                timeout=5,
                            )
                        except subprocess.TimeoutExpired:
                            process.kill()
                    else:
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
                    raise

                def summarize(handle: BinaryIO) -> tuple[str, int, str, bool]:
                    handle.seek(0)
                    digest = hashlib.sha256()
                    stored = bytearray()
                    total = 0
                    while chunk := handle.read(64 * 1024):
                        total += len(chunk)
                        digest.update(chunk)
                        remaining = self.config.stream_limit_bytes - len(stored)
                        if remaining > 0:
                            stored.extend(chunk[:remaining])
                    return (
                        bytes(stored).decode("utf-8", errors="replace"),
                        total,
                        digest.hexdigest(),
                        total > len(stored),
                    )

                stdout, stdout_size, stdout_hash, stdout_truncated = summarize(stdout_file)
                stderr, stderr_size, stderr_hash, stderr_truncated = summarize(stderr_file)
                exit_code = process.returncode
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise AdapterInfrastructureError(f"B1 CLI invocation failed: {arguments[:3]}") from exc
        return CommandCapture(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            stdout_size=stdout_size,
            stderr_size=stderr_size,
            stdout_sha256=stdout_hash,
            stderr_sha256=stderr_hash,
            stdout_truncated=stdout_truncated,
            stderr_truncated=stderr_truncated,
        )

    def _public_json(self, capture: CommandCapture, kind: str) -> dict[str, JsonValue]:
        if capture.stdout_truncated:
            raise AdapterInfrastructureError(f"B1 {kind} JSON exceeded the capture limit")
        try:
            value = json.loads(capture.stdout)
            self._validators[kind].validate(value)
        except (json.JSONDecodeError, JsonSchemaValidationError) as exc:
            raise AdapterInfrastructureError(f"B1 {kind} output violated its public Schema") from exc
        if not isinstance(value, dict):
            raise AdapterInfrastructureError(f"B1 {kind} output must be a JSON object")
        return value

    def preflight(self, context: CellContext) -> PreflightResult:
        executable = self.config.command_prefix[0]
        if not Path(executable).is_file() and shutil.which(executable) is None:
            return PreflightResult(False, "B1 CLI executable was not found")
        if not self.config.project.is_dir() or not self.config.run_spec.is_file():
            return PreflightResult(False, "B1 project or Run Spec is missing")
        state_root = self.config.state_root
        if state_root.exists() and any(state_root.iterdir()):
            return PreflightResult(False, "Cell B1 state root is not empty")
        validation = self._invoke(
            [
                "run",
                "validate",
                "--project",
                str(self.config.project.resolve()),
                "--spec",
                str(self.config.run_spec.resolve()),
            ]
        )
        if validation.exit_code != 0:
            return PreflightResult(False, "B1 run validate failed")
        return PreflightResult(True, f"B1 public CLI preflight passed for {context.cell_id}")

    def run(self, context: CellContext) -> VariantEvidence:
        start_arguments = [
            "run",
            "start",
            "--project",
            str(self.config.project.resolve()),
            "--spec",
            str(self.config.run_spec.resolve()),
            "--runtime",
            self.config.runtime,
        ]
        if self.config.runtime == "fake":
            assert self.config.fake_fixture is not None
            start_arguments.extend(["--fake-fixture", str(self.config.fake_fixture.resolve())])
        start = self._invoke(start_arguments)
        captures: dict[str, CommandCapture] = {"start": start}
        try:
            start_status = self._public_json(start, "status")
            run_id = str(start_status["run_id"])
            status_capture = self._invoke(["run", "status", run_id, "--json"])
            captures["status"] = status_capture
            status = self._public_json(status_capture, "status")
            if status["run_id"] != run_id:
                raise AdapterInfrastructureError("B1 status Run ID changed after launch")
            report_capture = self._invoke(["report", run_id, "--format", "json"])
            captures["report"] = report_capture
            report = self._public_json(report_capture, "report")
            if report["run_id"] != run_id:
                raise AdapterInfrastructureError("B1 report Run ID does not match status")
            integrity_capture = self._invoke(["recover", "check", run_id])
            captures["integrity"] = integrity_capture
            integrity = json.loads(integrity_capture.stdout)
            if integrity_capture.exit_code != 0 or not isinstance(integrity, dict) or not integrity.get("ok"):
                raise AdapterInfrastructureError("B1 integrity check failed")
        except (AdapterInfrastructureError, json.JSONDecodeError, KeyError, TypeError) as exc:
            return VariantEvidence(
                outcome_state="infrastructure_error",
                failure_kind="b1_public_contract_invalid",
                attempt_count=0,
                raw_payload={
                    "adapter_id": self.id(),
                    "cell_id": context.cell_id,
                    "error_kind": type(exc).__name__,
                    "commands": {
                        key: value.public_payload() for key, value in captures.items()
                    },
                },
            )

        state = str(status["state"])
        if start.exit_code == 0 and state == "COMPLETED":
            outcome: OutcomeState = "completed"
            failure_kind = None
        elif start.exit_code == 3 or state == "BLOCKED":
            outcome, failure_kind = "blocked", "b1_blocked"
        elif start.exit_code == 4 or state == "FAILED":
            outcome, failure_kind = "failed", "b1_task_failed"
        elif start.exit_code == 130:
            outcome, failure_kind = "interrupted", "b1_interrupted"
        else:
            outcome, failure_kind = "infrastructure_error", "b1_exit_state_mismatch"

        metrics = report["metrics"]
        usage_status = str(metrics["usage_status"])
        raw_token_usage = metrics["token_usage"]
        measured_token_usage: JsonValue | None = (
            raw_token_usage if usage_status == "measured" else None
        )
        normalized_metrics: dict[str, JsonValue] = {
            "turn_count": metrics["turns"],
            "session_count": metrics["sessions"],
            "attempt_count": metrics["attempts"],
            "token_usage_status": "measured" if measured_token_usage is not None else "unknown",
            "token_usage": measured_token_usage,
            "b1_token_usage_raw": raw_token_usage,
            "b1_report_usage_status": usage_status,
            "b1_session_usage_statuses": status["session_usage_statuses"],
        }
        return VariantEvidence(
            outcome_state=outcome,
            failure_kind=failure_kind,
            attempt_count=int(metrics["attempts"]),
            raw_payload={
                "adapter_id": self.id(),
                "cell_id": context.cell_id,
                "run_id": run_id,
                "runtime": self.config.runtime,
                "actual_model_turns": 0 if self.config.runtime == "fake" else None,
                "status": status,
                "report": report,
                "integrity": integrity,
                "commands": {
                    key: value.public_payload() for key, value in captures.items()
                },
            },
            normalized_metrics=normalized_metrics,
        )
