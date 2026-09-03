"""Profile R B1 backend for one approved Phase F Cell.

This module keeps the B1 scheduler, ledger, deterministic Checks, retry, and
resume logic authoritative.  It only supplies the already-approved Phase F
runtime-contract-v2 transport and the common passive observation hook.
"""

from __future__ import annotations

import json
import queue
import threading
import time
from collections.abc import Callable, Mapping
from pathlib import Path, PurePosixPath
from typing import Any

from pydantic import JsonValue

from benchmark_runner.adapter import CellContext
from benchmark_runner.contract import present_api_key_environment_names
from benchmark_runner.realistic_phase_f import (
    PhaseFBackendResult,
    PhaseFDispatchRequest,
    PhaseFModelTurnAccounting,
    PhaseFModelTurnReceipt,
    PhaseFRuntimeMode,
    phase_f_model_turn_receipt,
)
from benchmark_runner.realistic_phase_f_sdk import (
    PHASE_F_PINNED_MODEL,
    PHASE_F_PINNED_REASONING_EFFORT,
    PHASE_F_PINNED_SDK_VERSION,
    PHASE_F_PERMISSION_PROFILE,
    PhaseFAppServerPort,
    phase_f_thread_start_params,
    phase_f_turn_start_params,
    verify_phase_f_thread_start,
)
from benchmark_runner.realistic_phase_f_ss1 import (
    PROFILE_R_FIXTURE_ID,
    PhaseFBoundaryTelemetry,
    build_profile_r_boundary_observation,
    build_profile_r_ss1_tasks,
    materialize_profile_r_workspace,
    refresh_profile_r_ss1_task,
    _file_state,
    _tree_sha256,
    _write_new,
)
from benchmark_runner.realistic_routing import (
    PassiveBoundaryRecord,
    canonical_json_bytes,
    common_safety_decision,
)
from benchmark_runner.runner import sha256_bytes, sha256_file
from benchmark_runner.workspace import git_environment_provenance

from orchestrator.contract import (
    FailureKind,
    InterruptOutcome,
    InterruptState,
    ResultEnvelope,
    RuntimeCapabilities,
    RuntimeFailure,
    RuntimeProfile,
    SessionState,
    TaskEnvelope,
    TerminalStatus,
    TokenCounts,
    UsageSnapshot,
    UsageStatus,
)
from orchestrator.ledger import Ledger
from orchestrator.runtime import (
    RuntimePort,
    RuntimeOutcome,
    SessionHandle,
    TurnHandle,
)
from orchestrator.schedule import (
    Orchestrator,
    TurnBoundaryContext,
    load_project,
    load_run_spec,
)
from orchestrator.worker import render_worker_prompt
from orchestrator.verify import (
    CHECK_TEMP_GIT_BOOTSTRAP_SUFFIX,
    validate_external_check_temp_root,
)


PHASE_F_B1_EVIDENCE_FILENAME = "b1-adapter-evidence.json"


class PhaseFB1BackendError(RuntimeError):
    """Raised when the Phase F/B1 bridge cannot preserve the frozen contract."""


AppServerPortFactory = Callable[[Path, tuple[str, ...]], PhaseFAppServerPort]


def _b1_adapter_outcome(
    state: str,
    report: Mapping[str, Any],
) -> tuple[str, str | None]:
    """Keep Check-environment failures out of the B1 product-failure bucket."""

    failure_kinds = {
        str(attempt.get("failure_kind"))
        for task in report.get("tasks", [])
        if isinstance(task, dict)
        for attempt in task.get("attempts", [])
        if isinstance(attempt, dict) and attempt.get("failure_kind") is not None
    }
    if "check_environment" in failure_kinds:
        return "infrastructure_error", "check_environment"
    if "check_mixed" in failure_kinds:
        return "infrastructure_error", "check_mixed"
    if "check_unknown" in failure_kinds:
        return "infrastructure_error", "check_unknown"
    outcome = {
        "COMPLETED": "completed",
        "FAILED": "failed",
        "BLOCKED": "blocked",
        "CANCELLED": "interrupted",
    }.get(state, "infrastructure_error")
    return outcome, None if outcome == "completed" else f"b1_{state.lower()}"


class PhaseFB1RuntimeV2(RuntimePort):
    """B1 RuntimePort using the same v2 app-server wire contract as SS1."""

    def __init__(
        self,
        workspace: Path,
        *,
        port: PhaseFAppServerPort,
        environ: Mapping[str, str] | None = None,
        interrupt_grace_seconds: float = 15.0,
    ) -> None:
        self.workspace = workspace.resolve()
        self.port = port
        self.environ = environ
        self.interrupt_grace_seconds = interrupt_grace_seconds
        self._opened = False
        self._preflight_complete = False
        self._actual_model_turns = 0
        self._thread_evidence: list[dict[str, JsonValue]] = []

    @property
    def actual_model_turns(self) -> int:
        return self._actual_model_turns

    @property
    def thread_evidence(self) -> tuple[dict[str, JsonValue], ...]:
        return tuple(dict(value) for value in self._thread_evidence)

    def preflight(self) -> None:
        if present_api_key_environment_names(self.environ):
            raise PhaseFB1BackendError("API key environment names are present")
        if self.port.sdk_version != PHASE_F_PINNED_SDK_VERSION:
            raise PhaseFB1BackendError("Phase F B1 SDK version differs")
        if not self._opened:
            self.port.open()
            self._opened = True
        if self.port.account_type() != "chatgpt":
            raise PhaseFB1BackendError("Phase F B1 requires ChatGPT authentication")
        if PHASE_F_PINNED_MODEL not in self.port.visible_model_ids():
            raise PhaseFB1BackendError("Phase F B1 pinned model is unavailable")
        matching = [
            item
            for item in self.port.permission_profiles(str(self.workspace))
            if item.get("id") == PHASE_F_PERMISSION_PROFILE
            and item.get("allowed") is True
        ]
        if len(matching) != 1:
            raise PhaseFB1BackendError("Phase F B1 permission profile differs")
        self._preflight_complete = True

    def capabilities(self) -> RuntimeCapabilities:
        return RuntimeCapabilities(
            runtime_name="codex_v2",
            runtime_version=PHASE_F_PINNED_SDK_VERSION,
            supports_interrupt=True,
            supports_usage=True,
            supports_resume=True,
            supports_output_schema=True,
        )

    def start_session(
        self,
        task_envelope: TaskEnvelope,
        runtime_profile: Any,
    ) -> SessionHandle:
        if not self._preflight_complete:
            raise PhaseFB1BackendError("Phase F B1 preflight did not run")
        if (
            runtime_profile.model != PHASE_F_PINNED_MODEL
            or runtime_profile.auth_method != "chatgpt"
            or runtime_profile.reasoning_effort != PHASE_F_PINNED_REASONING_EFFORT
        ):
            raise PhaseFB1BackendError("Phase F B1 runtime profile differs")
        observation = self.port.start_thread(
            phase_f_thread_start_params(self.workspace),
            notification_timeout_seconds=2.0,
        )
        thread_id = verify_phase_f_thread_start(observation, workspace=self.workspace)
        self._thread_evidence.append(
            {
                "thread_id_sha256": sha256_bytes(thread_id.encode("utf-8")),
                "transcript_sha256": observation.transcript_sha256,
                "permission_profile_id": PHASE_F_PERMISSION_PROFILE,
                "legacy_sandbox_arguments": False,
            }
        )
        return SessionHandle(
            id=thread_id,
            raw=thread_id,
            envelope=task_envelope,
            runtime_profile=runtime_profile,
        )

    def _start_turn(
        self,
        session_handle: SessionHandle,
        prompt: str,
        *,
        turn_no: int,
    ) -> TurnHandle:
        handle = self.port.start_turn(
            session_handle.id,
            prompt,
            phase_f_turn_start_params(
                self.workspace,
                ResultEnvelope.model_json_schema(),
            ),
        )
        self._actual_model_turns += 1
        return TurnHandle(
            id=f"{session_handle.id}:turn:{turn_no}",
            session=session_handle,
            raw=handle,
            turn_no=turn_no,
        )

    def start_turn(
        self,
        session_handle: SessionHandle,
        task_envelope: TaskEnvelope,
    ) -> TurnHandle:
        return self._start_turn(
            session_handle,
            render_worker_prompt(task_envelope, session_handle.initial_feedback),
            turn_no=1,
        )

    def resume_session(
        self,
        session_handle: SessionHandle,
        feedback_envelope: dict[str, Any],
    ) -> TurnHandle:
        return self._start_turn(
            session_handle,
            render_worker_prompt(session_handle.envelope, feedback_envelope),
            turn_no=2,
        )

    @staticmethod
    def _usage(result: object) -> UsageSnapshot:
        usage = getattr(result, "usage", None)
        total = getattr(usage, "total", None)
        if total is None:
            return UsageSnapshot(status=UsageStatus.UNKNOWN)
        return UsageSnapshot(
            status=UsageStatus.MEASURED,
            scope="thread_cumulative",
            total=TokenCounts(
                input_tokens=int(total.input_tokens),
                output_tokens=int(total.output_tokens),
                total_tokens=int(total.total_tokens),
            ),
        )

    def _collect(
        self,
        handle: TurnHandle,
        destination: queue.Queue[RuntimeOutcome],
    ) -> None:
        try:
            result = handle.raw.run()
            status = str(getattr(getattr(result, "status", None), "value", getattr(result, "status", "unknown")))
            terminal = {
                "runtime_turn_id": str(getattr(result, "id", handle.id)),
                "status": status,
                "started_at": getattr(result, "started_at", None),
                "completed_at": getattr(result, "completed_at", None),
                "duration_ms": getattr(result, "duration_ms", None),
            }
            if status == "completed":
                response = getattr(result, "final_response", None)
                try:
                    raw_result = json.loads(response or "")
                except (json.JSONDecodeError, TypeError):
                    raw_result = response
                destination.put(
                    RuntimeOutcome(
                        terminal_status=TerminalStatus.COMPLETED,
                        terminal_evidence=terminal,
                        raw_result=raw_result,
                        usage_snapshot=self._usage(result),
                    )
                )
            elif status == "interrupted":
                destination.put(
                    RuntimeOutcome(
                        terminal_status=TerminalStatus.CANCELLED,
                        terminal_evidence=terminal,
                        usage_snapshot=self._usage(result),
                    )
                )
            else:
                destination.put(
                    RuntimeOutcome(
                        terminal_status=TerminalStatus.FAILED,
                        terminal_evidence=terminal,
                        failure=RuntimeFailure(
                            kind=FailureKind.RUNTIME_UNKNOWN,
                            retryable=False,
                            redacted_message="Phase F B1 turn failed",
                            source_exception_type=type(getattr(result, "error", None)).__name__,
                        ),
                        usage_snapshot=self._usage(result),
                    )
                )
        except Exception as exc:
            destination.put(
                RuntimeOutcome(
                    terminal_status=TerminalStatus.FAILED,
                    terminal_evidence={"consumer": "failed"},
                    failure=RuntimeFailure(
                        kind=FailureKind.RUNTIME_UNKNOWN,
                        retryable=False,
                        redacted_message="Phase F B1 transport failed",
                        source_exception_type=type(exc).__name__,
                    ),
                    usage_snapshot=UsageSnapshot(status=UsageStatus.UNKNOWN),
                )
            )

    def await_terminal(
        self,
        turn_handle: TurnHandle,
        monotonic_deadline: float,
    ) -> RuntimeOutcome:
        destination: queue.Queue[RuntimeOutcome] = queue.Queue(maxsize=1)
        threading.Thread(
            target=self._collect,
            args=(turn_handle, destination),
            name=f"phase-f-b1-{turn_handle.turn_no}",
            daemon=True,
        ).start()
        try:
            return destination.get(
                timeout=max(0.0, monotonic_deadline - time.monotonic())
            )
        except queue.Empty:
            interrupted = self.interrupt(turn_handle)
            if interrupted.state is InterruptState.CONFIRMED:
                try:
                    return destination.get(timeout=self.interrupt_grace_seconds)
                except queue.Empty:
                    pass
            return RuntimeOutcome(
                terminal_status=TerminalStatus.UNKNOWN,
                terminal_evidence={
                    "deadline_exceeded": True,
                    "interrupt_state": interrupted.state,
                },
                failure=RuntimeFailure(
                    kind=FailureKind.TERMINAL_UNKNOWN,
                    retryable=False,
                    redacted_message="Phase F B1 terminal was not proven",
                    source_exception_type="RuntimeDeadlineExceeded",
                ),
                usage_snapshot=UsageSnapshot(status=UsageStatus.UNKNOWN),
            )

    def interrupt(self, turn_handle: TurnHandle) -> InterruptOutcome:
        try:
            turn_handle.raw.interrupt()
            turn_handle.interrupted.set()
            return InterruptOutcome(state=InterruptState.CONFIRMED)
        except Exception as exc:
            return InterruptOutcome(
                state=InterruptState.FAILED,
                terminal_evidence={"error_type": type(exc).__name__},
            )

    def close(self) -> None:
        if self._opened:
            self.port.close()
        self._opened = False
        self._preflight_complete = False


class _BudgetedB1Runtime(RuntimePort):
    """Fail closed before every B1 start/resume and preserve start receipts."""

    def __init__(
        self,
        delegate: RuntimePort,
        *,
        runtime_mode: PhaseFRuntimeMode,
        model_turn_ceiling: int | None,
        completion_deadline_monotonic: float | None = None,
    ) -> None:
        self.delegate = delegate
        self.runtime_mode = runtime_mode
        self.model_turn_ceiling = model_turn_ceiling
        self.completion_deadline_monotonic = completion_deadline_monotonic
        self._turn_start_attempts = 0
        self._receipts: list[PhaseFModelTurnReceipt] = []

    @property
    def actual_model_turns(self) -> int:
        if self.runtime_mode is PhaseFRuntimeMode.MODEL_FREE_FAKE:
            return 0
        return self._turn_start_attempts

    @property
    def runtime_reported_model_turns(self) -> int:
        if self.runtime_mode is PhaseFRuntimeMode.MODEL_FREE_FAKE:
            return 0
        value = getattr(self.delegate, "actual_model_turns", None)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise PhaseFB1BackendError("Phase F B1 runtime did not report model turns")
        return value

    @property
    def thread_evidence(self) -> tuple[dict[str, JsonValue], ...]:
        values = getattr(self.delegate, "thread_evidence", ())
        return tuple(dict(value) for value in values)

    def model_turn_accounting(self) -> PhaseFModelTurnAccounting:
        return PhaseFModelTurnAccounting(
            schema_version=(
                2 if self.completion_deadline_monotonic is not None else 1
            ),
            runtime_mode=self.runtime_mode,
            model_turn_ceiling=self.model_turn_ceiling,
            budget_mode=(
                "cell_completion_deadline"
                if self.completion_deadline_monotonic is not None
                else None
            ),
            turn_start_attempts=self._turn_start_attempts,
            actual_model_turns=self.actual_model_turns,
            runtime_reported_model_turns=self.runtime_reported_model_turns,
            receipts=list(self._receipts),
        )

    def preflight(self) -> None:
        preflight = getattr(self.delegate, "preflight", None)
        if callable(preflight):
            preflight()

    def capabilities(self) -> RuntimeCapabilities:
        return self.delegate.capabilities()

    def start_session(
        self,
        task_envelope: TaskEnvelope,
        runtime_profile: Any,
    ) -> SessionHandle:
        return self.delegate.start_session(task_envelope, runtime_profile)

    def _start(
        self,
        *,
        task_id: str,
        call: Callable[[], TurnHandle],
    ) -> TurnHandle:
        if (
            self.completion_deadline_monotonic is not None
            and time.monotonic() >= self.completion_deadline_monotonic
        ):
            raise PhaseFB1BackendError(
                "Phase F B1 Cell completion deadline reached before dispatch"
            )
        if (
            self.model_turn_ceiling is not None
            and self._turn_start_attempts >= self.model_turn_ceiling
        ):
            raise PhaseFB1BackendError(
                "Phase F B1 model turn ceiling reached before dispatch"
            )
        self._turn_start_attempts += 1
        ordinal = self._turn_start_attempts
        try:
            handle = call()
        except Exception:
            self._receipts.append(
                phase_f_model_turn_receipt(
                    ordinal=ordinal,
                    task_id=task_id,
                    status="start_outcome_unknown",
                    turn_id=None,
                )
            )
            raise
        self._receipts.append(
            phase_f_model_turn_receipt(
                ordinal=ordinal,
                task_id=task_id,
                status=(
                    "simulated"
                    if self.runtime_mode is PhaseFRuntimeMode.MODEL_FREE_FAKE
                    else "accepted"
                ),
                turn_id=handle.id,
            )
        )
        return handle

    def start_turn(
        self,
        session_handle: SessionHandle,
        task_envelope: TaskEnvelope,
    ) -> TurnHandle:
        return self._start(
            task_id=task_envelope.task_id,
            call=lambda: self.delegate.start_turn(session_handle, task_envelope),
        )

    def await_terminal(
        self,
        turn_handle: TurnHandle,
        monotonic_deadline: float,
    ) -> RuntimeOutcome:
        return self.delegate.await_terminal(turn_handle, monotonic_deadline)

    def resume_session(
        self,
        session_handle: SessionHandle,
        feedback_envelope: dict[str, Any],
    ) -> TurnHandle:
        return self._start(
            task_id=session_handle.envelope.task_id,
            call=lambda: self.delegate.resume_session(
                session_handle,
                feedback_envelope,
            ),
        )

    def interrupt(self, turn_handle: TurnHandle) -> InterruptOutcome:
        return self.delegate.interrupt(turn_handle)

    def close(self) -> None:
        self.delegate.close()


class ProfileRPhaseFB1Backend:
    """Run exactly Profile R/B1 Cell 2 through the existing B1 scheduler."""

    evidence_filename = PHASE_F_B1_EVIDENCE_FILENAME

    def __init__(
        self,
        *,
        repository: Path,
        artifact_root: Path,
        runtime_mode: PhaseFRuntimeMode,
        runtime_factory: Callable[[Path], RuntimePort],
        telemetry: PhaseFBoundaryTelemetry,
        check_temp_root: Path,
        protected_execution_roots: tuple[Path, ...] = (),
        environ: Mapping[str, str] | None = None,
        git_executable: Path | None = None,
        source_environment: Mapping[str, str] | None = None,
    ) -> None:
        self.repository = repository.resolve()
        self.artifact_root = artifact_root.resolve()
        self.runtime_mode = PhaseFRuntimeMode(runtime_mode)
        self.runtime_factory = runtime_factory
        self.telemetry = telemetry
        self.check_temp_root = validate_external_check_temp_root(
            check_temp_root,
            forbidden_roots=(
                self.repository,
                self.artifact_root,
                *protected_execution_roots,
            ),
            required_allocation_suffixes=(CHECK_TEMP_GIT_BOOTSTRAP_SUFFIX,),
            require_ntfs=True,
        )
        self.environ = environ
        self.git_executable = git_executable
        self.source_environment = source_environment
        self._completion_deadline_monotonic: float | None = None

    def bind_completion_deadline_monotonic(self, deadline: float) -> None:
        if deadline <= time.monotonic():
            raise PhaseFB1BackendError("Cell completion deadline is not in the future")
        self._completion_deadline_monotonic = deadline

    def run_one_cell(self, request: PhaseFDispatchRequest) -> PhaseFBackendResult:
        if present_api_key_environment_names(self.environ):
            raise PhaseFB1BackendError("API key environment names are present")
        if request.runtime_mode is not self.runtime_mode:
            raise PhaseFB1BackendError("Phase F B1 runtime mode differs")
        if (
            request.budget_mode == "cell_completion_deadline"
            and self._completion_deadline_monotonic is None
        ):
            raise PhaseFB1BackendError("Cell completion deadline was not bound")
        if (
            request.execution_ordinal != 2
            or request.fixture_id != PROFILE_R_FIXTURE_ID
            or request.variant_id != "b1"
        ):
            raise PhaseFB1BackendError("Profile R B1 backend accepts only Cell 2")
        cell_root = self.artifact_root / request.cell_id
        if cell_root.exists():
            raise PhaseFB1BackendError("Profile R B1 Cell already exists")
        cell_root.mkdir(parents=True, exist_ok=False)
        workspace = cell_root / "workspace"
        materialize_profile_r_workspace(
            self.repository,
            workspace,
            git_executable=self.git_executable,
            source_environment=self.source_environment,
        )
        git_provenance = git_environment_provenance(
            workspace=workspace,
            git_executable=self.git_executable,
            source_environment=(
                None
                if self.source_environment is None
                else dict(self.source_environment)
            ),
        )
        attested_git_executable = Path(
            str(git_provenance["git_executable_canonical_path"])
        )
        initial_tree = _tree_sha256(_file_state(workspace))
        public_tasks = build_profile_r_ss1_tasks(workspace)
        public_by_key = {task.task_id: task for task in public_tasks}
        run_scopes = tuple(
            scope for task in public_tasks for scope in task.write_scope
        )
        records: list[PassiveBoundaryRecord] = []
        observer_sha256 = sha256_file(
            self.repository
            / "tools/benchmark-runner/src/benchmark_runner/realistic_phase_f_ss1.py"
        )

        def observe(context: TurnBoundaryContext) -> PassiveBoundaryRecord:
            public_task = refresh_profile_r_ss1_task(
                workspace,
                public_by_key[context.task_spec.key],
            )
            before = {
                item.path: item.sha256
                for item in context.workspace_baseline.files
            }
            observation = build_profile_r_boundary_observation(
                task=public_task,
                before=before,
                after=_file_state(workspace),
                run_write_scopes=run_scopes,
                telemetry=self.telemetry,
                observer_implementation_sha256=observer_sha256,
            )
            decision = common_safety_decision(observation)
            if decision.stop:
                raise PhaseFB1BackendError(
                    "B1 passive safety stop: " + ",".join(decision.reason_codes)
                )
            record = PassiveBoundaryRecord.from_raw_ids(
                experiment_id=request.experiment_id,
                cell_id=request.cell_id,
                variant_id="b1",
                task_id=context.task_spec.key,
                raw_attempt_id=context.attempt_id,
                raw_thread_id=context.raw_session_id,
                turn_ordinal=context.turn_ordinal,
                boundary_ordinal=len(records) + 1,
                turn_kind=context.turn_kind,  # type: ignore[arg-type]
                observation=observation,
            )
            records.append(record)
            return record

        runtime = _BudgetedB1Runtime(
            self.runtime_factory(workspace),
            runtime_mode=self.runtime_mode,
            model_turn_ceiling=request.model_turn_ceiling,
            completion_deadline_monotonic=self._completion_deadline_monotonic,
        )
        if hasattr(runtime, "preflight"):
            runtime.preflight()  # type: ignore[attr-defined]
        loaded = load_project(workspace)
        spec_path = workspace / "benchmark-run.yaml"
        spec_text = spec_path.read_text(encoding="utf-8")
        spec = load_run_spec(spec_path)
        orchestrator = Orchestrator(
            loaded,
            state_root=cell_root / "b1-state",
            check_temp_root=self.check_temp_root,
            git_executable=attested_git_executable,
            source_environment=(
                None
                if self.source_environment is None
                else dict(self.source_environment)
            ),
            runtime_kind="injected_codex_v2",
            max_turns_override=request.model_turn_ceiling,
            completion_deadline_monotonic=self._completion_deadline_monotonic,
            runtime_port=runtime,
            runtime_profile_override=RuntimeProfile(
                runtime="codex",
                model=PHASE_F_PINNED_MODEL,
                auth_method="chatgpt",
                reasoning_effort=PHASE_F_PINNED_REASONING_EFFORT,
            ),
            auth_method_override="chatgpt",
            turn_boundary_observer=observe,
            check_temp_hostile_git_probe=True,
        )
        try:
            run_id = orchestrator.start(spec, original_spec=spec_text)
        finally:
            orchestrator.close()
        with Ledger(cell_root / "b1-state" / "ledger.sqlite") as ledger:
            snapshot = ledger.load_run_snapshot(run_id)
        b1_state_root = cell_root / "b1-state"
        artifact_by_id = {
            item["artifact_id"]: item for item in snapshot["artifacts"]
        }
        environment_diagnostics: dict[tuple[str, str], dict[str, JsonValue]] = {}
        structured_check_results: dict[
            tuple[str, str], dict[str, JsonValue]
        ] = {}
        for artifact in snapshot["artifacts"]:
            relative_path = str(artifact.get("relative_path", ""))
            attempt_id = artifact.get("attempt_id")
            parts = PurePosixPath(relative_path).parts
            if (
                artifact.get("kind") == "check_result"
                and relative_path.endswith("/result.json")
            ):
                if not isinstance(attempt_id, str) or len(parts) < 2:
                    raise PhaseFB1BackendError(
                        "B1 structured Check result identity is invalid"
                    )
                check_name = parts[-2]
                value = json.loads(
                    (b1_state_root / relative_path).read_text(encoding="utf-8")
                )
                if not isinstance(value, dict):
                    raise PhaseFB1BackendError(
                        "B1 structured Check result payload is invalid"
                    )
                key = (attempt_id, check_name)
                if key in structured_check_results:
                    raise PhaseFB1BackendError(
                        "B1 structured Check result is duplicated"
                    )
                structured_check_results[key] = value
                continue
            if (
                artifact.get("kind") != "check_result"
                or not relative_path.endswith("/environment-diagnostic.json")
            ):
                continue
            if not isinstance(attempt_id, str) or len(parts) < 2:
                raise PhaseFB1BackendError(
                    "B1 Check environment diagnostic identity is invalid"
                )
            check_name = parts[-2]
            value = json.loads(
                (b1_state_root / relative_path).read_text(encoding="utf-8")
            )
            if not isinstance(value, dict):
                raise PhaseFB1BackendError(
                    "B1 Check environment diagnostic payload is invalid"
                )
            key = (attempt_id, check_name)
            if key in environment_diagnostics:
                raise PhaseFB1BackendError(
                    "B1 Check environment diagnostic is duplicated"
                )
            environment_diagnostics[key] = value

        def public_stream(artifact_id: str | None) -> dict[str, JsonValue] | None:
            if artifact_id is None:
                return None
            artifact = artifact_by_id[artifact_id]
            data = (b1_state_root / artifact["relative_path"]).read_bytes()
            return {
                "sha256": sha256_bytes(data),
                "size_bytes": len(data),
                "text": data.decode("utf-8", errors="replace"),
            }

        task_external_keys = {
            str(item["task_id"]): str(item["external_key"])
            for item in snapshot["tasks"]
        }
        check_records: list[dict[str, JsonValue]] = []
        for item in snapshot["checks"]:
            check_key = (str(item["attempt_id"]), str(item["check_name"]))
            structured = structured_check_results.get(check_key)
            if structured is None:
                raise PhaseFB1BackendError("B1 structured Check result is missing")
            check_records.append(
                {
                    "task_id": item["task_id"],
                    "task_external_key": task_external_keys[str(item["task_id"])],
                    "attempt_id": item["attempt_id"],
                    "check_name": item["check_name"],
                    "state": item["state"],
                    "exit_code": item["exit_code"],
                    "stdout": public_stream(item["stdout_artifact_id"]),
                    "stderr": public_stream(item["stderr_artifact_id"]),
                    "environment_diagnostic": environment_diagnostics.get(
                        check_key
                    ),
                    "failure_classification": structured.get(
                        "failure_classification"
                    ),
                    "failure_classification_source": structured.get(
                        "failure_classification_source"
                    ),
                    "diagnostic_result": structured.get("diagnostic_result"),
                }
            )
        report_path = cell_root / "b1-state" / "runs" / run_id / "report" / "summary.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        metrics = report["metrics"]
        turn_accounting = runtime.model_turn_accounting()
        actual_model_turns = turn_accounting.actual_model_turns
        state = str(snapshot["run"]["state"])
        outcome, failure_kind = _b1_adapter_outcome(state, report)
        report_failure_kinds = {
            str(attempt.get("failure_kind"))
            for task in report.get("tasks", [])
            if isinstance(task, dict)
            for attempt in task.get("attempts", [])
            if isinstance(attempt, dict)
            and attempt.get("failure_kind") is not None
        }
        product_failure_present = bool(
            report_failure_kinds.intersection({"check_failed", "check_mixed"})
        )
        environment_failure_present = bool(
            report_failure_kinds.intersection(
                {"check_environment", "check_mixed", "check_unknown"}
            )
        )
        token_usage = (
            metrics["token_usage"]
            if metrics.get("usage_status") == "measured"
            else None
        )
        normalized_metrics: dict[str, JsonValue] = {
            "turn_count": int(metrics["turns"]),
            "session_count": int(metrics["sessions"]),
            "attempt_count": int(metrics["attempts"]),
            "token_usage_status": (
                "measured" if token_usage is not None else "unknown"
            ),
            "token_usage": token_usage,
            "model_active_seconds": metrics.get("model_active_seconds"),
            "b1_retry_count": sum(
                max(len(task["attempts"]) - 1, 0) for task in report["tasks"]
            ),
            "b1_resume_count": sum(
                int(attempt["resume_count"])
                for task in report["tasks"]
                for attempt in task["attempts"]
            ),
            "b1_environment_diagnostic_count": len(environment_diagnostics),
            "b1_invalid_environment": failure_kind in {
                "check_environment",
                "check_mixed",
                "check_unknown",
            },
            "comparison_valid": not environment_failure_present,
            "product_failure_present": product_failure_present,
            "environment_failure_present": environment_failure_present,
        }
        payload: dict[str, JsonValue] = {
            "schema_version": 1,
            "kind": "phase_f_profile_r_b1_adapter_evidence",
            "experiment_id": request.experiment_id,
            "cell_id": request.cell_id,
            "request_sha256": request.request_sha256,
            "fixture_id": request.fixture_id,
            "variant_id": request.variant_id,
            "runtime_mode": self.runtime_mode.value,
            "worker_tree_initial_sha256": initial_tree,
            "worker_tree_final_sha256": _tree_sha256(_file_state(workspace)),
            "git_provenance": git_provenance,
            "actual_model_turns": actual_model_turns,
            "model_turn_accounting": turn_accounting.model_dump(mode="json"),
            "adapter_outcome_state": outcome,
            "adapter_failure_kind": failure_kind,
            "adapter_attempt_count": int(metrics["attempts"]),
            "adapter_raw_payload": {
                "run_id": run_id,
                "report": report,
                "check_records": check_records,
                "boundary_records": [
                    record.model_dump(mode="json") for record in records
                ],
                "thread_start_evidence": list(
                    getattr(runtime, "thread_evidence", ())
                ),
            },
            "adapter_normalized_metrics": normalized_metrics,
            "judge_executed": False,
            "automatic_continuation": False,
        }
        evidence_bytes = canonical_json_bytes(payload)
        evidence_path = cell_root / PHASE_F_B1_EVIDENCE_FILENAME
        _write_new(evidence_path, evidence_bytes)
        return PhaseFBackendResult(
            schema_version=request.schema_version,
            experiment_id=request.experiment_id,
            plan_fingerprint=request.plan_fingerprint,
            candidate_seal_sha256=request.candidate_seal_sha256,
            candidate_snapshot_sha256=request.candidate_snapshot_sha256,
            model_turn_ceiling=request.model_turn_ceiling,
            budget_mode=request.budget_mode,
            cell_completion_deadline_seconds=(
                request.cell_completion_deadline_seconds
            ),
            execution_ordinal=request.execution_ordinal,
            cell_id=request.cell_id,
            fixture_id=request.fixture_id,
            variant_id=request.variant_id,
            runtime_mode=self.runtime_mode,
            request_sha256=request.request_sha256,
            outcome_state=outcome,
            actual_model_turns=actual_model_turns,
            sealed_artifact_sha256=sha256_bytes(evidence_bytes),
            public_summary={
                "task_count": int(metrics["tasks"]),
                "turn_count": int(metrics["turns"]),
                "session_count": int(metrics["sessions"]),
                "attempt_count": int(metrics["attempts"]),
                "boundary_record_count": len(records),
                "judge_executed": False,
                "automatic_continuation": False,
                "invalid_environment": failure_kind in {
                    "check_environment",
                    "check_mixed",
                    "check_unknown",
                },
            },
        )
