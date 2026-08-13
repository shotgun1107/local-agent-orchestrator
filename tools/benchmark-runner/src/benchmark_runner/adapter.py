from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Callable, Literal, Protocol

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError as JsonSchemaValidationError
from pydantic import JsonValue, ValidationError

from benchmark_runner.contract import (
    API_KEY_ENV_NAMES,
    B0Attestation,
    B0ManualSubmission,
    InterventionEvent,
    InterventionKind,
    OutcomeState,
    utc_now,
)


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


def _has_repeatable_b1_quality_regression(tasks: list[dict[str, JsonValue]]) -> bool:
    """Return true only for repeated deterministic check failures, not runtime failures."""

    return any(
        isinstance(task.get("attempts"), list)
        and len(task["attempts"]) >= 2
        and all(
            isinstance(attempt, dict) and attempt.get("failure_kind") == "check_failed"
            for attempt in task["attempts"]
        )
        for task in tasks
    )


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


class B0EventValidationError(ValueError):
    pass


@dataclass(frozen=True)
class B0DerivedMetrics:
    startup_action_count: int
    manual_copy_or_relay_count_excluding_start: int
    manual_copy_or_relay_count_including_start: int
    manual_recovery_count: int
    manual_recovery_seconds: float
    session_count: int
    turn_count: int
    attempt_count: int
    aborted: bool

    def public_payload(self) -> dict[str, JsonValue]:
        return {
            "startup_action_count": self.startup_action_count,
            "manual_copy_or_relay_count_excluding_start": (
                self.manual_copy_or_relay_count_excluding_start
            ),
            "manual_copy_or_relay_count_including_start": (
                self.manual_copy_or_relay_count_including_start
            ),
            "manual_recovery_count": self.manual_recovery_count,
            "manual_recovery_seconds": self.manual_recovery_seconds,
            "session_count": self.session_count,
            "turn_count": self.turn_count,
            "attempt_count": self.attempt_count,
            "aborted": self.aborted,
        }


def derive_b0_metrics(
    events: list[InterventionEvent],
    *,
    cell_id: str,
) -> B0DerivedMetrics:
    if not events:
        raise B0EventValidationError("B0 timeline is empty")
    if events[0].intervention_kind != "initial_prompt_copy":
        raise B0EventValidationError("B0 timeline must start with initial_prompt_copy")
    if sum(event.intervention_kind == "initial_prompt_copy" for event in events) != 1:
        raise B0EventValidationError("B0 timeline requires exactly one initial_prompt_copy")
    event_ids: set[str] = set()
    previous_offset = -1.0
    previous_timestamp: datetime | None = None
    recovery_started_at: float | None = None
    recovery_count = 0
    recovery_seconds = 0.0
    aborted = False
    for index, event in enumerate(events):
        if event.cell_id != cell_id:
            raise B0EventValidationError("B0 Event references a different Cell")
        if event.event_id in event_ids:
            raise B0EventValidationError("B0 Event IDs must be unique")
        event_ids.add(event.event_id)
        if event.monotonic_offset_seconds < previous_offset:
            raise B0EventValidationError("B0 monotonic offsets must not go backwards")
        if previous_timestamp is not None and event.timestamp < previous_timestamp:
            raise B0EventValidationError("B0 timestamps must not go backwards")
        previous_offset = event.monotonic_offset_seconds
        previous_timestamp = event.timestamp
        kind = event.intervention_kind
        if kind == "b1_start":
            raise B0EventValidationError("b1_start is not valid in a B0 timeline")
        if kind == "recovery_start":
            if recovery_started_at is not None:
                raise B0EventValidationError("B0 recovery intervals cannot overlap")
            recovery_started_at = event.monotonic_offset_seconds
        elif kind == "recovery_end":
            if recovery_started_at is None:
                raise B0EventValidationError("B0 recovery_end has no matching start")
            recovery_seconds += event.monotonic_offset_seconds - recovery_started_at
            recovery_count += 1
            recovery_started_at = None
        elif kind == "abort":
            if aborted or index != len(events) - 1:
                raise B0EventValidationError("B0 abort must occur once and be the final Event")
            aborted = True
    if recovery_started_at is not None:
        raise B0EventValidationError("B0 recovery interval was not closed")

    excluding_kinds = {"additional_prompt", "correction", "manual_retry"}
    startup = 1
    excluding = sum(event.intervention_kind in excluding_kinds for event in events)
    turns = sum(
        event.intervention_kind
        in {"initial_prompt_copy", "additional_prompt", "correction", "manual_retry"}
        for event in events
    )
    retries = sum(event.intervention_kind == "manual_retry" for event in events)
    replacements = sum(
        event.intervention_kind == "session_replacement" for event in events
    )
    return B0DerivedMetrics(
        startup_action_count=startup,
        manual_copy_or_relay_count_excluding_start=excluding,
        manual_copy_or_relay_count_including_start=startup + excluding,
        manual_recovery_count=recovery_count,
        manual_recovery_seconds=recovery_seconds,
        session_count=1 + replacements,
        turn_count=turns,
        attempt_count=1 + retries,
        aborted=aborted,
    )


class B0InterventionRecorder:
    def __init__(
        self,
        *,
        cell_id: str,
        path: Path,
        monotonic_clock: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], datetime] = utc_now,
    ) -> None:
        if path.exists():
            raise FileExistsError(f"B0 Intervention Event file already exists: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        self.cell_id = cell_id
        self.path = path
        self._monotonic_clock = monotonic_clock
        self._wall_clock = wall_clock
        self._started_at = monotonic_clock()
        self._next_id = 1

    def record(
        self,
        intervention_kind: InterventionKind,
        *,
        actor: Literal["user", "runner"] = "user",
        duration_seconds: float | None = None,
        note: str | None = None,
    ) -> InterventionEvent:
        now = self._wall_clock()
        event = InterventionEvent(
            created_at=now,
            event_id=f"evt_{self._next_id:06d}",
            cell_id=self.cell_id,
            timestamp=now,
            monotonic_offset_seconds=max(0.0, self._monotonic_clock() - self._started_at),
            intervention_kind=intervention_kind,
            actor=actor,
            duration_seconds=duration_seconds,
            note=note,
        )
        line = json.dumps(
            event.model_dump(mode="json"),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8") + b"\n"
        with self.path.open("ab") as handle:
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())
        self._next_id += 1
        return event

    def read_all(self) -> list[InterventionEvent]:
        if not self.path.is_file():
            return []
        events: list[InterventionEvent] = []
        try:
            for line in self.path.read_bytes().splitlines():
                if not line.strip():
                    raise B0EventValidationError("B0 Event JSONL contains a blank line")
                events.append(InterventionEvent.model_validate_json(line))
        except (OSError, ValidationError) as exc:
            raise B0EventValidationError("B0 Event JSONL is invalid") from exc
        return events


@dataclass(frozen=True)
class B0ManualSession:
    context: CellContext
    workspace: Path
    prompt_path: Path
    recorder: B0InterventionRecorder


class B0ManualInputProvider(Protocol):
    def collect(self, session: B0ManualSession) -> B0ManualSubmission | None: ...


@dataclass(frozen=True)
class B0AdapterConfig:
    workspace: Path
    prompt_path: Path
    events_path: Path
    input_provider: B0ManualInputProvider
    expected_model: str
    expected_reasoning_effort: str
    expected_surface_kind: str
    monotonic_clock: Callable[[], float] = time.monotonic
    wall_clock: Callable[[], datetime] = utc_now


class ConsoleB0ManualInputProvider:
    """Small sidecar loop. It observes a separate B0 Codex session; it never launches one."""

    def __init__(
        self,
        *,
        expected_model: str,
        expected_reasoning_effort: str,
        expected_surface_kind: str,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
    ) -> None:
        self.expected_model = expected_model
        self.expected_reasoning_effort = expected_reasoning_effort
        self.expected_surface_kind = expected_surface_kind
        self.input_fn = input_fn
        self.output_fn = output_fn

    def collect(self, session: B0ManualSession) -> B0ManualSubmission:
        self.output_fn(f"B0 workspace: {session.workspace}")
        self.output_fn(f"Fixed prompt: {session.prompt_path}")
        self.output_fn("[p] prompt  [a] additional  [c] correction  [m] retry")
        self.output_fn("[r] recovery toggle  [s] new session  [o] observe  [d] done  [x] abort")
        recovering = False
        while True:
            command = self.input_fn("b0> ").strip().lower()
            if command == "p":
                session.recorder.record("initial_prompt_copy")
            elif command == "a":
                session.recorder.record("additional_prompt")
            elif command == "c":
                session.recorder.record("correction")
            elif command == "m":
                session.recorder.record("manual_retry")
            elif command == "r":
                session.recorder.record("recovery_end" if recovering else "recovery_start")
                recovering = not recovering
            elif command == "s":
                session.recorder.record("session_replacement")
            elif command == "o":
                session.recorder.record("status_observation")
            elif command in {"d", "x"}:
                if command == "x":
                    session.recorder.record("abort")
                confirmed = self.input_fn("Timeline complete and controls confirmed? [y/N] ").strip().lower() == "y"
                attestation = B0Attestation(
                    status="confirmed" if confirmed else "refused",
                    confirmed_at=utc_now(),
                    timeline_complete=confirmed,
                    model=self.expected_model if confirmed else None,
                    reasoning_effort=self.expected_reasoning_effort if confirmed else None,
                    surface_kind=self.expected_surface_kind if confirmed else None,
                )
                return B0ManualSubmission(
                    outcome_state="interrupted" if command == "x" else "completed",
                    attestation=attestation,
                )


class B0ManualAdapter:
    def __init__(self, config: B0AdapterConfig) -> None:
        self.config = config

    def id(self) -> str:
        return "b0"

    def capabilities(self) -> VariantCapabilities:
        return VariantCapabilities(
            automated_launch=False,
            supports_usage=False,
            supports_attempt_count=True,
        )

    def preflight(self, context: CellContext) -> PreflightResult:
        if not self.config.workspace.is_dir():
            return PreflightResult(False, "B0 workspace is missing")
        if not self.config.prompt_path.is_file():
            return PreflightResult(False, "B0 fixed prompt is missing")
        if self.config.events_path.exists():
            return PreflightResult(False, "B0 Event sidecar is not empty")
        if not all(
            (
                self.config.expected_model,
                self.config.expected_reasoning_effort,
                self.config.expected_surface_kind,
            )
        ):
            return PreflightResult(False, "B0 control values are incomplete")
        return PreflightResult(True, f"B0 manual sidecar preflight passed for {context.cell_id}")

    def _failure(
        self,
        context: CellContext,
        *,
        failure_kind: str,
        error_kind: str,
        events: list[InterventionEvent],
        submission: B0ManualSubmission | None,
        derived: B0DerivedMetrics | None = None,
    ) -> VariantEvidence:
        return VariantEvidence(
            outcome_state="infrastructure_error",
            failure_kind=failure_kind,
            attempt_count=0,
            raw_payload={
                "adapter_id": self.id(),
                "cell_id": context.cell_id,
                "error_kind": error_kind,
                "stop_required": True,
                "stop_reason": failure_kind,
                "submission": submission.model_dump(mode="json") if submission else None,
                "event_count": len(events),
                "derived_metrics_untrusted": derived.public_payload() if derived else None,
            },
            normalized_metrics={
                "measurement_trusted": False,
                "event_count": len(events),
            },
        )

    def run(self, context: CellContext) -> VariantEvidence:
        recorder = B0InterventionRecorder(
            cell_id=context.cell_id,
            path=self.config.events_path,
            monotonic_clock=self.config.monotonic_clock,
            wall_clock=self.config.wall_clock,
        )
        submission: B0ManualSubmission | None = None
        try:
            raw_submission = self.config.input_provider.collect(
                B0ManualSession(
                    context=context,
                    workspace=self.config.workspace,
                    prompt_path=self.config.prompt_path,
                    recorder=recorder,
                )
            )
            submission = (
                B0ManualSubmission.model_validate(raw_submission)
                if raw_submission is not None
                else None
            )
        except Exception as exc:
            try:
                events = recorder.read_all()
            except B0EventValidationError:
                events = []
            return self._failure(
                context,
                failure_kind="b0_manual_input_failed",
                error_kind=type(exc).__name__,
                events=events,
                submission=None,
            )

        try:
            events = recorder.read_all()
            derived = derive_b0_metrics(events, cell_id=context.cell_id)
            if submission is not None:
                if derived.aborted != (submission.outcome_state == "interrupted"):
                    raise B0EventValidationError("B0 abort Event and outcome disagree")
        except B0EventValidationError as exc:
            return self._failure(
                context,
                failure_kind="measurement_event_invalid",
                error_kind=type(exc).__name__,
                events=locals().get("events", []),
                submission=submission,
            )
        if (
            submission is None
            or submission.attestation is None
            or submission.attestation.status != "confirmed"
            or not submission.attestation.timeline_complete
        ):
            return self._failure(
                context,
                failure_kind="measurement_attestation_missing",
                error_kind="B0AttestationMissing",
                events=events,
                submission=submission,
                derived=derived,
            )
        attestation = submission.attestation
        if (
            attestation.model != self.config.expected_model
            or attestation.reasoning_effort != self.config.expected_reasoning_effort
            or attestation.surface_kind != self.config.expected_surface_kind
        ):
            return self._failure(
                context,
                failure_kind="b0_control_attestation_invalid",
                error_kind="B0ControlMismatch",
                events=events,
                submission=submission,
                derived=derived,
            )
        metrics = derived.public_payload()
        metrics["measurement_trusted"] = True
        metrics["event_count"] = len(events)
        metrics["token_usage_status"] = "unknown"
        metrics["token_usage"] = None
        return VariantEvidence(
            outcome_state=submission.outcome_state,
            failure_kind=(
                None if submission.outcome_state == "completed" else f"b0_{submission.outcome_state}"
            ),
            attempt_count=derived.attempt_count,
            raw_payload={
                "adapter_id": self.id(),
                "cell_id": context.cell_id,
                "stop_required": submission.outcome_state != "completed",
                "stop_reason": (
                    None if submission.outcome_state == "completed" else f"b0_{submission.outcome_state}"
                ),
                "submission": submission.model_dump(mode="json"),
                "event_count": len(events),
                "derived_metrics": derived.public_payload(),
            },
            normalized_metrics=metrics,
        )


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
    python_path: Path | None = None
    invocation_cwd: Path | None = None
    max_model_turns: int | None = None
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
        self._preflight_evidence: dict[str, JsonValue] | None = None

    @property
    def preflight_evidence(self) -> dict[str, JsonValue] | None:
        return dict(self._preflight_evidence) if self._preflight_evidence else None

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
        if self.config.python_path is not None:
            # Bind ``python -m orchestrator`` to the frozen B1 source tree.  The
            # parent Runner's import path is not inherited reliably by the
            # subprocess, and inheriting an ambient PYTHONPATH could select a
            # different installed B1 package.
            environment["PYTHONPATH"] = str(self.config.python_path.resolve())
        if self.config.runtime == "fake":
            for name in API_KEY_ENV_NAMES:
                environment.pop(name, None)
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
                    cwd=(
                        str(self.config.invocation_cwd.resolve())
                        if self.config.invocation_cwd is not None
                        else None
                    ),
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
        try:
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
        except AdapterInfrastructureError:
            return PreflightResult(False, "B1 run validate invocation failed")
        if validation.exit_code != 0:
            return PreflightResult(False, "B1 run validate failed")
        if self.config.runtime == "codex":
            try:
                doctor = self._invoke(
                    [
                        "doctor",
                        "--project",
                        str(self.config.project.resolve()),
                        "--json",
                    ]
                )
                if doctor.exit_code != 0 or doctor.stdout_truncated:
                    raise AdapterInfrastructureError("B1 doctor failed")
                payload = json.loads(doctor.stdout)
                sdk = payload["codex_sdk"]
                login = payload["codex_login"]
                if (
                    payload["api_key_present"] is not False
                    or sdk["installed"] is not True
                    or sdk["pinned"] is not True
                    or sdk["version"] != "0.144.4"
                    or login["checked"] is not True
                    or login["authenticated"] is not True
                    or login["method"] != "chatgpt"
                ):
                    raise AdapterInfrastructureError("B1 doctor controls differ")
                self._preflight_evidence = {
                    "sdk_version": "0.144.4",
                    "sdk_pinned": True,
                    "account_type": "chatgpt",
                    "api_key_environment_names_present": [],
                    "actual_model_turns": 0,
                }
            except (
                AdapterInfrastructureError,
                json.JSONDecodeError,
                KeyError,
                TypeError,
            ):
                self._preflight_evidence = None
                return PreflightResult(False, "B1 live doctor preflight failed")
        return PreflightResult(True, f"B1 public CLI preflight passed for {context.cell_id}")

    def _terminal_failure(
        self,
        context: CellContext,
        captures: dict[str, CommandCapture],
        *,
        outcome_state: OutcomeState,
        failure_kind: str,
        error_kind: str,
    ) -> VariantEvidence:
        return VariantEvidence(
            outcome_state=outcome_state,
            failure_kind=failure_kind,
            attempt_count=0,
            raw_payload={
                "adapter_id": self.id(),
                "cell_id": context.cell_id,
                "error_kind": error_kind,
                "stop_required": True,
                "stop_reason": failure_kind,
                "commands": {
                    key: value.public_payload() for key, value in captures.items()
                },
            },
        )

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
        if self.config.max_model_turns is not None:
            start_arguments.extend(["--max-turns", str(self.config.max_model_turns)])
        if self.config.runtime == "fake":
            assert self.config.fake_fixture is not None
            start_arguments.extend(["--fake-fixture", str(self.config.fake_fixture.resolve())])
        try:
            start = self._invoke(start_arguments)
        except AdapterInfrastructureError as exc:
            return self._terminal_failure(
                context,
                {},
                outcome_state="infrastructure_error",
                failure_kind="b1_cli_invocation_failed",
                error_kind=type(exc).__name__,
            )
        captures: dict[str, CommandCapture] = {"start": start}
        early_exit_kinds = {
            5: "b1_integrity_failure",
            6: "b1_controller_locked",
            7: "b1_runtime_failure",
        }
        if start.exit_code == 130:
            return self._terminal_failure(
                context,
                captures,
                outcome_state="interrupted",
                failure_kind="b1_interrupted",
                error_kind="B1Exit130",
            )
        if start.exit_code in early_exit_kinds:
            return self._terminal_failure(
                context,
                captures,
                outcome_state="infrastructure_error",
                failure_kind=early_exit_kinds[start.exit_code],
                error_kind=f"B1Exit{start.exit_code}",
            )
        if start.exit_code not in {0, 3, 4}:
            return self._terminal_failure(
                context,
                captures,
                outcome_state="infrastructure_error",
                failure_kind="b1_unknown_exit_code",
                error_kind=f"B1Exit{start.exit_code}",
            )
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
            if report_capture.exit_code != 0:
                raise AdapterInfrastructureError("B1 public report command failed")
            report = self._public_json(report_capture, "report")
            if report["run_id"] != run_id:
                raise AdapterInfrastructureError("B1 report Run ID does not match status")
            integrity_capture = self._invoke(["recover", "check", run_id])
            captures["integrity"] = integrity_capture
            integrity = json.loads(integrity_capture.stdout)
            if integrity_capture.exit_code != 0 or not isinstance(integrity, dict) or not integrity.get("ok"):
                raise AdapterInfrastructureError("B1 integrity check failed")
        except (AdapterInfrastructureError, json.JSONDecodeError, KeyError, TypeError) as exc:
            return self._terminal_failure(
                context,
                captures,
                outcome_state="infrastructure_error",
                failure_kind="b1_public_contract_invalid",
                error_kind=type(exc).__name__,
            )

        state = str(status["state"])
        expected_terminal = {
            0: ("COMPLETED", 0),
            3: ("BLOCKED", 3),
            4: ("FAILED", 4),
        }
        expected_state, expected_status_exit = expected_terminal[start.exit_code]
        if state != expected_state or status_capture.exit_code != expected_status_exit:
            outcome: OutcomeState = "infrastructure_error"
            failure_kind = "b1_exit_state_mismatch"
        elif start.exit_code == 0:
            outcome = "completed"
            failure_kind = None
        elif start.exit_code == 3:
            outcome = "blocked"
            failure_kind = "b1_blocked"
        else:
            outcome = "failed"
            failure_kind = "b1_task_failed"

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
        task_attempts = [attempt for task in report["tasks"] for attempt in task["attempts"]]
        check_failed_attempts = [
            attempt for attempt in task_attempts if attempt.get("failure_kind") == "check_failed"
        ]
        repeatable_failure = _has_repeatable_b1_quality_regression(report["tasks"])
        normalized_metrics.update(
            {
                "b1_retry_count": sum(
                    max(len(task["attempts"]) - 1, 0) for task in report["tasks"]
                ),
                "b1_resume_count": sum(
                    int(attempt["resume_count"]) for attempt in task_attempts
                ),
                "b1_intermediate_check_changed_result": bool(check_failed_attempts),
                "b1_intermediate_check_changed_dispatch": any(
                    attempt.get("failure_kind") == "check_failed"
                    for task in report["tasks"]
                    for attempt in task["attempts"][:-1]
                ),
                "b1_repeatable_quality_regression": repeatable_failure,
            }
        )
        extra_turns = (
            normalized_metrics["b1_retry_count"]
            + normalized_metrics["b1_resume_count"]
        )
        normalized_metrics["dual_outcome_status"] = (
            "reported" if extra_turns > 0 else "not_applicable"
        )
        normalized_metrics["attempt_level_cost"] = "not_available"
        if extra_turns > 0:
            normalized_metrics["first_attempt_outcome"] = [
                {
                    "task_key": task["key"],
                    "state": task["attempts"][0]["state"],
                    "failure_kind": task["attempts"][0]["failure_kind"],
                }
                for task in report["tasks"]
                if task["attempts"]
            ]
            normalized_metrics["full_orchestrated_outcome"] = {
                "state": outcome,
                "failure_kind": failure_kind,
                "check_success": None,
                "turn_count": metrics["turns"],
                "token_usage_status": (
                    "measured" if measured_token_usage is not None else "unknown"
                ),
                "token_usage": measured_token_usage,
            }
        model_active_seconds = metrics.get("model_active_seconds")
        if isinstance(model_active_seconds, (int, float)) and not isinstance(
            model_active_seconds, bool
        ):
            normalized_metrics["model_active_seconds"] = float(model_active_seconds)
        worker_turns: list[dict[str, JsonValue]] = []
        for task in report["tasks"]:
            for attempt in task["attempts"]:
                hashes = {
                    "task_semantics_sha256": attempt["task_semantics_sha256"],
                    "prompt_sha256": attempt["initial_prompt_sha256"],
                    "output_schema_sha256": attempt["output_schema_sha256"],
                }
                if any(
                    not isinstance(value, str) or len(value) != 64
                    for value in hashes.values()
                ):
                    raise AdapterInfrastructureError(
                        "B1 report omitted worker-input hash Evidence"
                    )
                worker_turns.append(
                    {
                        "task_key": task["key"],
                        "attempt_no": attempt["attempt_no"],
                        **hashes,
                    }
                )
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
                "stop_required": outcome != "completed",
                "stop_reason": failure_kind,
                "status": status,
                "report": report,
                "integrity": integrity,
                "turns": worker_turns,
                "commands": {
                    key: value.public_payload() for key, value in captures.items()
                },
            },
            normalized_metrics=normalized_metrics,
        )
