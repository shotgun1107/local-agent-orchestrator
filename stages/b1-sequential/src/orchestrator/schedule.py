"""Sequential B1 scheduler and application use cases."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import yaml
from pydantic import ValidationError

from .contract import (
    AttemptState,
    CapabilitiesConfig,
    ChecksConfig,
    CORE_VERSION,
    FailureKind,
    PoliciesConfig,
    Policy,
    ProjectConfig,
    ProjectPack,
    ResultEnvelope,
    RunSpec,
    RunState,
    RuntimeProfile,
    RunReportEnvelope,
    RuntimeProfilesConfig,
    SandboxMode,
    SessionState,
    TaskSpec,
    TaskEnvelope,
    TaskState,
    TerminalStatus,
    UsageStatus,
    WorkspaceMode,
    canonical_json,
    load_yaml_model,
    new_id,
    sha256_bytes,
    utc_now,
)
from .ledger import IntegrityViolation, Ledger, LedgerError, StateConflict
from .recover import ControllerLock, reconcile
from .runtime import CodexRuntime, DispatchUncertain, FakeRuntime, RuntimePort
from .worker import (
    build_task_envelope,
    render_worker_prompt,
    result_schema,
    task_semantics_sha256,
)
from .verify import (
    ArtifactStore,
    GitWorkspace,
    VerificationError,
    hash_project_pack,
    extract_public_check_feedback,
    run_command_check,
    validate_declared_artifacts,
    validate_result_artifact_path_types,
    validate_freshness,
    validate_result_schema,
    validate_write_scope,
)


class ConfigurationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TurnBoundaryContext:
    """Public-safe facts available immediately after one B1 terminal turn.

    The hook runs before ResultEnvelope validation and before Controller Checks.
    It observes the workspace but does not decide scheduling, retry, or Check
    outcomes; those remain owned by the B1 scheduler.
    """

    run_id: str
    task_spec: TaskSpec
    task_envelope: TaskEnvelope
    attempt_id: str
    attempt_no: int
    raw_session_id: str
    raw_turn_id: str
    turn_ordinal: int
    turn_kind: str
    terminal_status: str
    error_kind: str | None
    workspace_baseline: Any


TurnBoundaryObserver = Callable[[TurnBoundaryContext], Any]


@dataclass(frozen=True, slots=True)
class LoadedProject:
    project_root: Path
    pack_root: Path
    pack: ProjectPack


def load_project(project_path: Path) -> LoadedProject:
    project_path = Path(project_path).resolve()
    pack_root = project_path / ".orchestrator"
    project = load_yaml_model(pack_root / "project.yaml", ProjectConfig)
    capabilities = load_yaml_model(pack_root / "capabilities.yaml", CapabilitiesConfig)
    policies = load_yaml_model(pack_root / "policies.yaml", PoliciesConfig)
    checks = load_yaml_model(pack_root / "checks.yaml", ChecksConfig)
    if project.default_capability_profile not in capabilities.profiles:
        raise ConfigurationError("default capability profile does not exist")
    if project.default_policy not in policies.policies:
        raise ConfigurationError("default policy does not exist")
    project_root = (project_path / project.repository_root).resolve()
    if project_path not in project_root.parents and project_root != project_path:
        raise ConfigurationError("repository_root escaped the project path")
    digest, _ = hash_project_pack(pack_root)
    pack = ProjectPack(
        root=str(pack_root),
        project=project,
        capabilities=capabilities,
        policies=policies,
        checks=checks,
        sha256=digest,
    )
    return LoadedProject(project_root=project_root, pack_root=pack_root, pack=pack)


def load_run_spec(path: Path) -> RunSpec:
    return load_yaml_model(Path(path), RunSpec)  # type: ignore[return-value]


def validate_run_against_project(spec: RunSpec, loaded: LoadedProject) -> None:
    profiles = loaded.pack.capabilities.profiles
    checks = loaded.pack.checks.checks
    policy = loaded.pack.policies.policies[loaded.pack.project.default_policy]
    for task in spec.tasks:
        if task.capability_profile not in profiles:
            raise ConfigurationError(f"Task {task.key} uses unknown capability profile")
        profile = profiles[task.capability_profile]
        if profile.workspace_mode != task.workspace_mode:
            raise ConfigurationError(f"Task {task.key} workspace_mode differs from capability profile")
        missing = set(task.check_names) - checks.keys()
        if missing:
            raise ConfigurationError(f"Task {task.key} uses unknown Checks: {sorted(missing)}")
        over_timeout = [name for name in task.check_names if checks[name].timeout_seconds > policy.check_timeout_seconds]
        if over_timeout:
            raise ConfigurationError(f"Task {task.key} Check timeout exceeds policy: {over_timeout}")
        for criterion in task.completion_criteria:
            if not criterion.check_names:
                raise ConfigurationError(f"Task criterion {criterion.id} has no deterministic Check")
    for criterion in spec.completion_criteria:
        if not criterion.satisfied_by_tasks:
            raise ConfigurationError(f"Run criterion {criterion.id} has no required Task")


def default_runtime_profiles_path() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "local-agent-orchestrator" / "runtime-profiles.yaml"


def load_runtime_profile(name: str, path: Path | None = None) -> RuntimeProfile:
    profiles = load_yaml_model(path or default_runtime_profiles_path(), RuntimeProfilesConfig)
    try:
        return profiles.profiles[name]  # type: ignore[attr-defined]
    except KeyError as exc:
        raise ConfigurationError(f"runtime profile not found: {name}") from exc


def state_root_for(project_id: str) -> Path:
    explicit = os.environ.get("LAO_STATE_ROOT")
    if explicit:
        return Path(explicit).resolve()
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return (base / "local-agent-orchestrator" / "projects" / project_id).resolve()


def artifact_base(run_id: str, task_key: str | None = None, attempt_no: int | None = None) -> str:
    base = f"runs/{run_id}"
    if task_key is not None:
        base += f"/tasks/{task_key}"
    if attempt_no is not None:
        base += f"/attempts/{attempt_no:03d}"
    return base


class Orchestrator:
    def __init__(
        self,
        loaded: LoadedProject,
        *,
        state_root: Path | None = None,
        runtime_kind: str = "fake",
        fake_scenario: str = "complete",
        fake_fixture: dict[str, Any] | None = None,
        runtime_profiles_path: Path | None = None,
        max_turns_override: int | None = None,
        runtime_port: RuntimePort | None = None,
        runtime_profile_override: Any | None = None,
        auth_method_override: str | None = None,
        turn_boundary_observer: TurnBoundaryObserver | None = None,
    ) -> None:
        self.loaded = loaded
        self.state_root = Path(state_root or state_root_for(loaded.pack.project.project_id)).resolve()
        self.store = ArtifactStore(self.state_root)
        self.workspace = GitWorkspace(loaded.project_root)
        self.policy: Policy = loaded.pack.policies.policies[loaded.pack.project.default_policy]
        if max_turns_override is not None:
            if max_turns_override < 1 or max_turns_override > self.policy.max_turns_per_run:
                raise ConfigurationError("max turns override must be within the project policy")
            self.policy = self.policy.model_copy(
                update={"max_turns_per_run": max_turns_override}
            )
        self.runtime_kind = runtime_kind
        self.runtime_profiles_path = runtime_profiles_path
        self.turn_boundary_observer = turn_boundary_observer
        if runtime_port is not None:
            if runtime_profile_override is None or auth_method_override is None:
                raise ConfigurationError(
                    "injected runtime requires explicit profile and auth method"
                )
            self.runtime = runtime_port
            self.runtime_profile = runtime_profile_override
            self.auth_method = auth_method_override
        elif runtime_kind == "fake":
            self.runtime: RuntimePort = FakeRuntime(
                fake_scenario,
                workspace=loaded.project_root,
                fixture=fake_fixture,
                interrupt_grace_seconds=min(0.2, self.policy.interrupt_grace_seconds),
            )
            self.runtime_profile: Any = {"runtime": "fake"}
            self.auth_method = "none"
        elif runtime_kind == "codex":
            capability = loaded.pack.capabilities.profiles[loaded.pack.project.default_capability_profile]
            self.runtime_profile = load_runtime_profile(capability.runtime_profile, runtime_profiles_path)
            if self.runtime_profile.auth_method != "chatgpt":
                raise ConfigurationError("B1 Codex runtime requires ChatGPT authentication")
            self.runtime = CodexRuntime(
                workspace=loaded.project_root,
                interrupt_grace_seconds=self.policy.interrupt_grace_seconds,
            )
            self.auth_method = "chatgpt"
        else:
            raise ConfigurationError(f"unsupported runtime: {runtime_kind}")

    def close(self) -> None:
        self.runtime.close()

    def _assert_project_pack_unchanged(self, expected: str) -> None:
        actual, _ = hash_project_pack(self.loaded.pack_root)
        if actual != expected:
            raise VerificationError("project_pack", "Project Pack changed during Run")

    def _persist(
        self,
        ledger: Ledger,
        *,
        run_id: str,
        relative_path: str,
        value: Any,
        kind: str,
        task_id: str | None = None,
        attempt_id: str | None = None,
        producer: str = "controller",
        media_type: str = "application/json",
    ) -> dict[str, Any]:
        if isinstance(value, bytes):
            written = self.store.write_bytes(relative_path, value)
        elif media_type == "application/json":
            written = self.store.write_json(relative_path, value)
        else:
            written = self.store.write_text(relative_path, str(value))
        return ledger.register_artifact({
            **written,
            "run_id": run_id,
            "task_id": task_id,
            "attempt_id": attempt_id,
            "kind": kind,
            "media_type": media_type,
            "sensitivity": "project_local",
            "retention": "run",
            "producer": producer,
        })

    def start(self, spec: RunSpec, *, original_spec: str | None = None) -> str:
        validate_run_against_project(spec, self.loaded)
        health = self.workspace.doctor()
        if not health.get("healthy"):
            raise ConfigurationError(f"workspace doctor failed: {health}")
        if self.policy.require_clean_worktree and not self.workspace.status()["clean"]:
            raise ConfigurationError("workspace must be clean before Run creation")
        with ControllerLock(self.state_root):
            with Ledger(self.state_root / "ledger.sqlite") as ledger:
                run = ledger.create_run({
                    "project_id": self.loaded.pack.project.project_id,
                    "request_text": spec.request.text,
                    "request_source": spec.request.source,
                    "requirements_version": 1,
                    "completion_criteria": spec.completion_criteria,
                    "constraints": spec.constraints,
                    "assumptions": spec.assumptions,
                    "auth_method": self.auth_method,
                    "policy_name": self.loaded.pack.project.default_policy,
                    "project_pack_sha256": self.loaded.pack.sha256,
                    "core_version": CORE_VERSION,
                    "max_turns": self.policy.max_turns_per_run,
                    "timeout_seconds": self.policy.run_timeout_seconds,
                })
                run_id = run["run_id"]
                self._persist(
                    ledger, run_id=run_id, relative_path=f"runs/{run_id}/request/original.txt",
                    value=spec.request.text + "\n", kind="request", producer="user", media_type="text/plain",
                )
                spec_text = original_spec or yaml.safe_dump(spec.model_dump(mode="json"), allow_unicode=True, sort_keys=False)
                self._persist(
                    ledger, run_id=run_id, relative_path=f"runs/{run_id}/request/run-spec.yaml",
                    value=spec_text, kind="run_spec", producer="user", media_type="application/yaml",
                )
                self._persist(
                    ledger, run_id=run_id, relative_path=f"runs/{run_id}/request/project-root.txt",
                    value=str(self.loaded.project_root), kind="project_file", media_type="text/plain",
                )
                ledger.create_tasks(run_id, spec.tasks)
                run = ledger.transition("run", run_id, run["version"], RunState.READY, "run_ready", {})
                ledger.transition("run", run_id, run["version"], RunState.RUNNING, "run_started", {})
                self._drive(ledger, run_id, spec)
                self.generate_report(ledger, run_id)
                return run_id

    def resume(self, run_id: str, spec: RunSpec) -> str:
        validate_run_against_project(spec, self.loaded)
        with ControllerLock(self.state_root):
            with Ledger(self.state_root / "ledger.sqlite") as ledger:
                run = ledger.get("run", run_id)
                if run["state"] in {RunState.COMPLETED, RunState.FAILED, RunState.CANCELLED}:
                    return run_id
                actions = reconcile(ledger, run_id, self.store)
                if any(action["action"] in {"dispatch_uncertain", "quarantined", "blocked_artifact_corrupt"} for action in actions):
                    self.generate_report(ledger, run_id)
                    return run_id
                self._drive(ledger, run_id, spec)
                self.generate_report(ledger, run_id)
                return run_id

    def _drive(self, ledger: Ledger, run_id: str, spec: RunSpec) -> None:
        specs = {task.key: task for task in spec.tasks}
        while True:
            run = ledger.get("run", run_id)
            if run["state"] in {RunState.COMPLETED, RunState.FAILED, RunState.BLOCKED, RunState.CANCELLED}:
                return
            from datetime import UTC, datetime

            run_started = datetime.fromisoformat(run["started_at"].replace("Z", "+00:00"))
            if (datetime.now(UTC) - run_started).total_seconds() > self.policy.run_timeout_seconds:
                ledger.transition("run", run_id, run["version"], RunState.BLOCKED, "run_timeout", {})
                return
            pending_verification = ledger.connection.execute(
                """SELECT a.* FROM attempts a JOIN tasks t ON t.task_id=a.task_id
                   WHERE t.run_id=? AND a.state IN ('REPORTED','VERIFYING') ORDER BY t.ordinal LIMIT 1""",
                (run_id,),
            ).fetchone()
            if pending_verification:
                self._resume_verification(ledger, run_id, dict(pending_verification), specs)
                continue
            task = self._select_next(ledger, run_id)
            if task is None:
                tasks = ledger.list_tasks(run_id)
                if tasks and all(row["state"] == TaskState.SUCCEEDED for row in tasks):
                    run = ledger.get("run", run_id)
                    run = ledger.transition("run", run_id, run["version"], RunState.VERIFYING, "run_verifying", {})
                    self._assert_project_pack_unchanged(run["project_pack_sha256"])
                    ledger.transition("run", run_id, run["version"], RunState.COMPLETED, "run_completed", {})
                else:
                    run = ledger.get("run", run_id)
                    target = RunState.FAILED if any(row["state"] == TaskState.FAILED for row in tasks) else RunState.BLOCKED
                    ledger.transition("run", run_id, run["version"], target, "run_no_runnable_task", {})
                return
            if run["turns_used"] >= run["max_turns"]:
                ledger.transition(
                    "run",
                    run_id,
                    run["version"],
                    RunState.BLOCKED,
                    "run_turn_budget_exhausted",
                    {"max_turns": run["max_turns"]},
                )
                return
            task_spec = specs[task["external_key"]]
            try:
                self._execute_task(ledger, run_id, task, task_spec)
            except VerificationError as exc:
                run = ledger.get("run", run_id)
                ledger.transition(
                    "run", run_id, run["version"], RunState.BLOCKED,
                    "run_verification_boundary_failed", {"stage": exc.stage, "message": str(exc)},
                )
                return

    def _select_next(self, ledger: Ledger, run_id: str) -> dict[str, Any] | None:
        if ledger.any_active_attempt():
            return None
        run = ledger.get("run", run_id)
        for task in ledger.list_tasks(run_id):
            if task["state"] == TaskState.PENDING and ledger.dependencies_succeeded(task["task_id"]):
                task = ledger.transition("task", task["task_id"], task["version"], TaskState.READY, "task_ready", {})
            if (
                task["state"] == TaskState.READY
                and task["requirements_version"] == run["requirements_version"]
                and ledger.dependencies_succeeded(task["task_id"])
            ):
                return task
        return None

    def _attempt_reason(self, attempts: list[dict[str, Any]]) -> str:
        if not attempts:
            return "initial"
        failure = attempts[-1]["failure_kind"]
        return {
            FailureKind.TRANSIENT_RUNTIME: "retry_transient",
            FailureKind.STALE_INPUT: "retry_stale",
            FailureKind.CHECK_FAILED: "retry_check",
        }.get(failure, "manual_recovery")

    def _retry_feedback(
        self,
        ledger: Ledger,
        attempts: list[dict[str, Any]],
        spec: TaskSpec,
    ) -> dict[str, Any] | None:
        if not attempts or attempts[-1]["failure_kind"] != FailureKind.CHECK_FAILED:
            return None
        row = ledger.connection.execute(
            """SELECT payload_json FROM events
               WHERE aggregate_id=? AND event_type='attempt_finished'
               ORDER BY seq DESC LIMIT 1""",
            (attempts[-1]["attempt_id"],),
        ).fetchone()
        if row is None:
            return None
        try:
            payload = json.loads(row["payload_json"])
        except (json.JSONDecodeError, TypeError):
            return None
        feedback = payload.get("public_check_feedback")
        if not isinstance(feedback, dict):
            return None
        check_name = feedback.get("check_name")
        messages = feedback.get("messages")
        exit_code = feedback.get("exit_code")
        if (
            check_name not in spec.check_names
            or not isinstance(messages, list)
            or not messages
            or not all(isinstance(message, str) and message for message in messages)
            or (exit_code is not None and not isinstance(exit_code, int))
        ):
            return None
        return {
            "failure": "checks",
            "check_name": check_name,
            "exit_code": exit_code,
            "public_feedback": messages,
            "allowed_write_scope": spec.write_scope,
            "remaining_completion_criteria": [
                criterion.text for criterion in spec.completion_criteria
            ],
        }

    def _execute_task(self, ledger: Ledger, run_id: str, task: dict[str, Any], spec: TaskSpec) -> None:
        run = ledger.get("run", run_id)
        self._assert_project_pack_unchanged(run["project_pack_sha256"])
        attempts = ledger.list_attempts(task["task_id"])
        attempt_no = len(attempts) + 1
        if attempt_no > self.policy.max_attempts_per_task:
            task = ledger.get("task", task["task_id"])
            ledger.transition("task", task["task_id"], task["version"], TaskState.FAILED, "task_attempt_budget_exhausted", {})
            return
        baseline = self.workspace.capture_baseline()
        fingerprint = self.workspace.fingerprint_inputs(spec)
        attempt_id = new_id("attempt")
        envelope = build_task_envelope(
            spec,
            run_id=run_id,
            task_id=task["task_id"],
            attempt_id=attempt_id,
            requirements_version=run["requirements_version"],
            timeout_seconds=self.policy.task_timeout_seconds,
            remaining_attempts=self.policy.max_attempts_per_task - attempt_no,
        )
        retry_feedback = self._retry_feedback(ledger, attempts, spec)
        attempt = ledger.begin_attempt(
            task["task_id"], attempt_no, self._attempt_reason(attempts), canonical_json(envelope),
            fingerprint.sha256, attempt_id=attempt_id,
        )
        base = artifact_base(run_id, task["external_key"], attempt_no)
        self._persist(
            ledger, run_id=run_id, task_id=task["task_id"], attempt_id=attempt_id,
            relative_path=f"{base}/input/task-envelope.json", value=envelope, kind="task_envelope",
        )
        self._persist(
            ledger, run_id=run_id, task_id=task["task_id"], attempt_id=attempt_id,
            relative_path=f"{base}/input/fingerprint.json", value=fingerprint, kind="fingerprint",
        )
        baseline_artifact = self._persist(
            ledger, run_id=run_id, task_id=task["task_id"], attempt_id=attempt_id,
            relative_path=f"{base}/input/workspace-baseline.json", value=baseline,
            kind="workspace_baseline",
        )
        ledger.set_baseline_artifact(attempt_id, baseline_artifact["artifact_id"])
        try:
            session_handle = self.runtime.start_session(envelope, self.runtime_profile)
            session_handle.initial_feedback = retry_feedback
            capabilities = self.runtime.capabilities()
            capability_profile = self.loaded.pack.capabilities.profiles[spec.capability_profile]
            session = ledger.create_session(
                attempt_id,
                capabilities.runtime_name,
                capabilities.runtime_version,
                session_handle.id,
                capability_profile.runtime_profile,
                str(self.loaded.project_root),
                str(capability_profile.sandbox),
                capabilities.model_dump(mode="json"),
                "unknown" if capabilities.supports_usage else "unsupported",
            )
            turn = self.runtime.start_turn(session_handle, envelope)
            ledger.mark_dispatched(attempt_id, session["session_id"], turn.id)
            self._persist(
                ledger, run_id=run_id, task_id=task["task_id"], attempt_id=attempt_id,
                relative_path=f"{base}/runtime/launch.json",
                value={
                    "runtime_name": capabilities.runtime_name,
                    "runtime_version": capabilities.runtime_version,
                    "runtime_session_id": session_handle.id,
                    "runtime_turn_id": turn.id,
                    "sandbox": str(capability_profile.sandbox),
                    "approval_mode": "deny_all",
                },
                kind="runtime_observation",
            )
        except DispatchUncertain as exc:
            if "session" in locals():
                ledger.update_session_terminal(
                    session["session_id"], SessionState.UNKNOWN,
                    {"dispatch_uncertain": True}, "unknown", None,
                )
            ledger.finish_attempt(
                attempt_id, AttemptState.DISPATCH_UNCERTAIN, TaskState.BLOCKED,
                FailureKind.DISPATCH_UNCERTAIN, {"message": str(exc)},
            )
            return
        except Exception as exc:
            if "session" in locals() and session["state"] == SessionState.STARTING:
                ledger.update_session_terminal(
                    session["session_id"], SessionState.UNKNOWN,
                    {"dispatch_error_type": type(exc).__name__}, "unknown", None,
                )
            self._finish_runtime_exception(ledger, attempt_id, exc)
            return
        self._consume_turns(
            ledger, run_id, task, spec, attempt, session, session_handle, turn,
            baseline, fingerprint, base,
        )

    def _consume_turns(
        self,
        ledger: Ledger,
        run_id: str,
        task: dict[str, Any],
        spec: TaskSpec,
        attempt: dict[str, Any],
        session: dict[str, Any],
        session_handle: Any,
        turn: Any,
        baseline: Any,
        fingerprint: Any,
        base: str,
    ) -> None:
        turn_no = 1
        while True:
            ledger.increment_turns(run_id)
            outcome = self.runtime.await_terminal(
                turn, time.monotonic() + self.policy.task_timeout_seconds
            )
            usage = outcome.usage_snapshot.model_dump(mode="json") if outcome.usage_snapshot else None
            ledger.append_usage_snapshot(session["session_id"], turn.id, usage)
            self._persist(
                ledger, run_id=run_id, task_id=task["task_id"], attempt_id=attempt["attempt_id"],
                relative_path=f"{base}/runtime/turns/{turn_no:03d}-terminal.json",
                value=outcome.terminal_evidence, kind="terminal_evidence", producer="runtime",
            )
            if self.turn_boundary_observer is not None:
                try:
                    observation = self.turn_boundary_observer(
                        TurnBoundaryContext(
                            run_id=run_id,
                            task_spec=spec,
                            task_envelope=TaskEnvelope.model_validate_json(
                                attempt["task_contract_json"]
                            ),
                            attempt_id=attempt["attempt_id"],
                            attempt_no=int(attempt["attempt_no"]),
                            raw_session_id=str(session_handle.id),
                            raw_turn_id=str(turn.id),
                            turn_ordinal=int(ledger.get("run", run_id)["turns_used"]),
                            turn_kind=(
                                "b1_resume"
                                if turn_no > 1
                                else "b1_retry"
                                if int(attempt["attempt_no"]) > 1
                                else "initial"
                            ),
                            terminal_status=str(outcome.terminal_status),
                            error_kind=(
                                None
                                if outcome.failure is None
                                else outcome.failure.source_exception_type
                            ),
                            workspace_baseline=baseline,
                        )
                    )
                    self._persist(
                        ledger,
                        run_id=run_id,
                        task_id=task["task_id"],
                        attempt_id=attempt["attempt_id"],
                        relative_path=(
                            f"{base}/runtime/turns/{turn_no:03d}-boundary.json"
                        ),
                        value=observation,
                        kind="runtime_observation",
                        producer="controller",
                    )
                except Exception as exc:
                    raise VerificationError(
                        "boundary_observer",
                        f"B1 turn boundary observer failed: {type(exc).__name__}",
                    ) from exc
            if outcome.terminal_status != TerminalStatus.COMPLETED:
                self._handle_runtime_outcome_failure(ledger, run_id, task, attempt, session, outcome)
                return
            result_artifact = self._persist(
                ledger, run_id=run_id, task_id=task["task_id"], attempt_id=attempt["attempt_id"],
                relative_path=f"{base}/output/turns/{turn_no:03d}/result-envelope.json",
                value=outcome.raw_result, kind="result_envelope", producer="runtime",
            )
            if outcome.terminal_evidence.get("corrupt_result_artifact"):
                self.store.resolve(result_artifact["relative_path"]).write_text(
                    "corrupted after registration", encoding="utf-8"
                )
            try:
                ledger.record_result_event(
                    self.runtime.capabilities().runtime_name, turn.id, result_artifact["sha256"], attempt["attempt_id"]
                )
                if outcome.terminal_evidence.get("duplicate_delivery"):
                    ledger.record_result_event(
                        self.runtime.capabilities().runtime_name,
                        turn.id,
                        "0" * 64 if outcome.terminal_evidence.get("conflicting_duplicate") else result_artifact["sha256"],
                        attempt["attempt_id"],
                    )
            except IntegrityViolation as exc:
                ledger.update_session_terminal(
                    session["session_id"], SessionState.QUARANTINED,
                    {**outcome.terminal_evidence, "integrity_error": str(exc)},
                    usage["status"] if usage else "unknown", None,
                )
                ledger.finish_attempt(
                    attempt["attempt_id"], AttemptState.BLOCKED, TaskState.BLOCKED,
                    FailureKind.ARTIFACT_CORRUPT, {"message": str(exc)},
                )
                return
            try:
                result = validate_result_schema(outcome.raw_result)
                validate_result_artifact_path_types(result, self.workspace)
            except VerificationError as exc:
                current_attempt = ledger.get("attempt", attempt["attempt_id"])
                if (
                    exc.retryable
                    and self.runtime.capabilities().supports_resume
                    and current_attempt["resume_count"] < self.policy.max_resume_per_attempt
                    and ledger.get("run", run_id)["turns_used"]
                    < ledger.get("run", run_id)["max_turns"]
                ):
                    ledger.increment_resume(attempt["attempt_id"], self.policy.max_resume_per_attempt)
                    turn = self.runtime.resume_session(
                        session_handle,
                        {
                            "failure": exc.stage,
                            "message": str(exc),
                            "allowed_write_scope": spec.write_scope,
                            "remaining_completion_criteria": [criterion.text for criterion in spec.completion_criteria],
                        },
                    )
                    ledger.set_active_turn(session["session_id"], turn.id)
                    turn_no += 1
                    continue
                ledger.update_session_terminal(
                    session["session_id"], SessionState.FAILED, outcome.terminal_evidence,
                    usage["status"] if usage else "unknown", None,
                )
                ledger.finish_attempt(
                    attempt["attempt_id"], AttemptState.FAILED, TaskState.FAILED,
                    FailureKind.MALFORMED_RESULT, {"message": str(exc)},
                )
                return
            ledger.update_session_terminal(
                session["session_id"], SessionState.COMPLETED, outcome.terminal_evidence,
                usage["status"] if usage else "unknown", None,
            )
            ledger.set_result_claim(attempt["attempt_id"], result.status_claim)
            if result.status_claim != "completed":
                target_attempt = AttemptState.BLOCKED if result.status_claim == "blocked" else AttemptState.FAILED
                target_task = TaskState.BLOCKED if result.status_claim == "blocked" else TaskState.FAILED
                ledger.finish_attempt(
                    attempt["attempt_id"], target_attempt, target_task,
                    FailureKind.RUNTIME_UNKNOWN, {"worker_claim": result.status_claim},
                )
                return
            current_attempt = ledger.get("attempt", attempt["attempt_id"])
            current_task = ledger.get("task", task["task_id"])
            ledger.transition(
                "attempt", attempt["attempt_id"], current_attempt["version"], AttemptState.REPORTED,
                "attempt_reported", {"result_sha256": result_artifact["sha256"]},
            )
            ledger.transition(
                "task", task["task_id"], current_task["version"], TaskState.REPORTED,
                "task_reported", {"attempt_id": attempt["attempt_id"]},
            )
            self._verify_and_finish(
                ledger, run_id, task, spec, attempt["attempt_id"], result, baseline, fingerprint, base,
                external_changed_paths=outcome.terminal_evidence.get("external_changed_paths", []),
            )
            return

    def _handle_runtime_outcome_failure(
        self,
        ledger: Ledger,
        run_id: str,
        task: dict[str, Any],
        attempt: dict[str, Any],
        session: dict[str, Any],
        outcome: Any,
    ) -> None:
        usage_status = outcome.usage_snapshot.status if outcome.usage_snapshot else UsageStatus.UNKNOWN
        if outcome.terminal_status == TerminalStatus.UNKNOWN:
            ledger.update_session_terminal(
                session["session_id"], SessionState.QUARANTINED, outcome.terminal_evidence,
                usage_status, None,
            )
            ledger.finish_attempt(
                attempt["attempt_id"], AttemptState.QUARANTINED, TaskState.BLOCKED,
                FailureKind.TERMINAL_UNKNOWN, {"failure": outcome.failure.model_dump(mode="json") if outcome.failure else None},
            )
            return
        if outcome.terminal_status == TerminalStatus.CANCELLED:
            ledger.update_session_terminal(
                session["session_id"], SessionState.CANCELLED, outcome.terminal_evidence,
                usage_status, None, interrupt_state="confirmed",
            )
            ledger.finish_attempt(
                attempt["attempt_id"], AttemptState.FAILED, TaskState.FAILED,
                FailureKind.TIMEOUT, {"terminal_status": outcome.terminal_status},
            )
            return
        ledger.update_session_terminal(
            session["session_id"], SessionState.FAILED, outcome.terminal_evidence,
            usage_status, None,
        )
        retryable = bool(outcome.failure and outcome.failure.retryable)
        failure_kind = outcome.failure.kind if outcome.failure else FailureKind.RUNTIME_UNKNOWN
        self._finish_or_retry(ledger, task, attempt["attempt_id"], failure_kind, retryable, {
            "failure": outcome.failure.model_dump(mode="json") if outcome.failure else None,
        })

    def _finish_runtime_exception(self, ledger: Ledger, attempt_id: str, exc: Exception) -> None:
        attempt = ledger.get("attempt", attempt_id)
        task = ledger.get("task", attempt["task_id"])
        ledger.finish_attempt(
            attempt_id, AttemptState.DISPATCH_UNCERTAIN, TaskState.BLOCKED,
            FailureKind.DISPATCH_UNCERTAIN, {"error_type": type(exc).__name__},
        )

    def _finish_or_retry(
        self,
        ledger: Ledger,
        task: dict[str, Any],
        attempt_id: str,
        failure_kind: FailureKind,
        retryable: bool,
        payload: dict[str, Any],
    ) -> None:
        attempts = ledger.list_attempts(task["task_id"])
        if retryable and len(attempts) < self.policy.max_attempts_per_task:
            _, updated_task = ledger.finish_attempt(
                attempt_id, AttemptState.RETRYABLE_FAILED, TaskState.RETRYABLE_FAILED,
                failure_kind, payload,
            )
            ledger.transition(
                "task", updated_task["task_id"], updated_task["version"], TaskState.READY,
                "task_retry_ready", {"failure_kind": failure_kind},
            )
        else:
            ledger.finish_attempt(
                attempt_id, AttemptState.FAILED, TaskState.FAILED, failure_kind, payload,
            )

    def _verify_and_finish(
        self,
        ledger: Ledger,
        run_id: str,
        task: dict[str, Any],
        spec: TaskSpec,
        attempt_id: str,
        result: ResultEnvelope,
        baseline: Any,
        fingerprint: Any,
        base: str,
        external_changed_paths: list[str] | None = None,
    ) -> None:
        current_attempt = ledger.get("attempt", attempt_id)
        current_task = ledger.get("task", task["task_id"])
        if current_attempt["state"] == AttemptState.REPORTED:
            ledger.transition(
                "attempt", attempt_id, current_attempt["version"], AttemptState.VERIFYING,
                "attempt_verifying", {},
            )
        if current_task["state"] == TaskState.REPORTED:
            ledger.transition(
                "task", current_task["task_id"], current_task["version"], TaskState.VERIFYING,
                "task_verifying", {},
            )
        try:
            self._assert_project_pack_unchanged(ledger.get("run", run_id)["project_pack_sha256"])
            corrupt = [
                row["relative_path"]
                for row in ledger.connection.execute(
                    "SELECT relative_path, sha256 FROM artifacts WHERE attempt_id=?", (attempt_id,)
                ).fetchall()
                if not self.store.verify(row["relative_path"], row["sha256"])
            ]
            if corrupt:
                raise VerificationError("artifact_integrity", f"Artifact hash mismatch: {corrupt}")
            changed = self.workspace.changed_paths(baseline)
            normalized_bytecode = self.workspace.normalize_untracked_python_bytecode(changed)
            if normalized_bytecode:
                changed = self.workspace.changed_paths(baseline)
            validate_declared_artifacts(result, self.workspace)
            validate_write_scope(spec, changed)
            current_fingerprint = self.workspace.fingerprint_inputs(spec)
            if external_changed_paths:
                raise VerificationError(
                    "freshness",
                    f"input changed externally while Attempt ran: {sorted(external_changed_paths)}",
                    retryable=True,
                )
            validate_freshness(fingerprint, current_fingerprint, spec, changed)
            passed: set[str] = set()
            for check_name in spec.check_names:
                existing = ledger.connection.execute(
                    "SELECT * FROM checks WHERE attempt_id=? AND check_name=?", (attempt_id, check_name)
                ).fetchone()
                if existing:
                    if existing["state"] == "PASSED":
                        passed.add(check_name)
                        continue
                    if existing["state"] == "PENDING":
                        ledger.start_check(existing["check_id"])
                        existing = ledger.connection.execute(
                            "SELECT * FROM checks WHERE check_id=?", (existing["check_id"],)
                        ).fetchone()
                    if existing["state"] == "RUNNING":
                        ledger.finish_check(existing["check_id"], {
                            "attempt_id": attempt_id,
                            "check_name": check_name,
                            "input_fingerprint": fingerprint.sha256,
                            "state": "ERROR",
                            "exit_code": None,
                        })
                    raise VerificationError("checks", f"previous Check {check_name} did not pass", retryable=True)
                definition = self.loaded.pack.checks.checks[check_name]
                check_record = ledger.create_check({
                    "task_id": task["task_id"],
                    "attempt_id": attempt_id,
                    "requirements_version": 1,
                    "check_name": check_name,
                    "argv": definition.argv,
                })
                ledger.start_check(check_record["check_id"])
                check_result = run_command_check(check_name, definition, self.workspace)
                check_base = f"{base}/checks/{check_name}"
                stdout_artifact = self._persist(
                    ledger, run_id=run_id, task_id=task["task_id"], attempt_id=attempt_id,
                    relative_path=f"{check_base}/stdout.txt", value=check_result.stdout,
                    kind="check_stdout", producer="verifier", media_type="text/plain",
                )
                stderr_artifact = self._persist(
                    ledger, run_id=run_id, task_id=task["task_id"], attempt_id=attempt_id,
                    relative_path=f"{check_base}/stderr.txt", value=check_result.stderr,
                    kind="check_stderr", producer="verifier", media_type="text/plain",
                )
                self._persist(
                    ledger, run_id=run_id, task_id=task["task_id"], attempt_id=attempt_id,
                    relative_path=f"{check_base}/result.json", value=check_result,
                    kind="check_result", producer="verifier",
                )
                ledger.finish_check(check_record["check_id"], {
                    "task_id": task["task_id"],
                    "attempt_id": attempt_id,
                    "requirements_version": 1,
                    "check_name": check_name,
                    "argv": definition.argv,
                    "state": check_result.state,
                    "exit_code": check_result.exit_code,
                    "stdout_artifact_id": stdout_artifact["artifact_id"],
                    "stderr_artifact_id": stderr_artifact["artifact_id"],
                    "started_at": check_result.started_at,
                    "ended_at": check_result.ended_at,
                    "input_fingerprint": fingerprint.sha256,
                })
                if check_result.state != "PASSED":
                    messages = extract_public_check_feedback(check_result)
                    raise VerificationError(
                        "checks",
                        f"Check failed: {check_name}",
                        retryable=True,
                        public_feedback=(
                            {
                                "check_name": check_name,
                                "exit_code": check_result.exit_code,
                                "messages": messages,
                            }
                            if messages
                            else None
                        ),
                    )
                passed.add(check_name)
            for criterion in spec.completion_criteria:
                if not set(criterion.check_names).issubset(passed):
                    raise VerificationError("completion_criteria", f"criterion not proven: {criterion.id}")
            ledger.finish_attempt(
                attempt_id, AttemptState.SUCCEEDED, TaskState.SUCCEEDED, None,
                {
                    "changed_paths": changed,
                    "checks": sorted(passed),
                    "normalized_transient_paths": normalized_bytecode,
                },
            )
        except VerificationError as exc:
            failure_payload: dict[str, Any] = {
                "stage": exc.stage,
                "message": str(exc),
            }
            if exc.public_feedback is not None:
                failure_payload["public_check_feedback"] = exc.public_feedback
            failure_kind = {
                "write_scope": FailureKind.SCOPE_VIOLATION,
                "freshness": FailureKind.STALE_INPUT,
                "checks": FailureKind.CHECK_FAILED,
                "project_pack": FailureKind.ARTIFACT_CORRUPT,
                "declared_artifacts": FailureKind.ARTIFACT_CORRUPT,
                "artifact_integrity": FailureKind.ARTIFACT_CORRUPT,
            }.get(exc.stage, FailureKind.INTERNAL)
            if failure_kind in {FailureKind.SCOPE_VIOLATION, FailureKind.ARTIFACT_CORRUPT}:
                ledger.finish_attempt(
                    attempt_id, AttemptState.BLOCKED, TaskState.BLOCKED, failure_kind,
                    failure_payload,
                )
            else:
                self._finish_or_retry(
                    ledger, task, attempt_id, failure_kind, exc.retryable,
                    failure_payload,
                )

    def _resume_verification(
        self,
        ledger: Ledger,
        run_id: str,
        attempt: dict[str, Any],
        specs: dict[str, TaskSpec],
    ) -> None:
        task = ledger.get("task", attempt["task_id"])
        spec = specs[task["external_key"]]
        artifacts = ledger.connection.execute(
            "SELECT kind, relative_path FROM artifacts WHERE attempt_id=?", (attempt["attempt_id"],)
        ).fetchall()
        by_kind: dict[str, list[str]] = {}
        for row in artifacts:
            by_kind.setdefault(row["kind"], []).append(row["relative_path"])
        required = {"result_envelope", "workspace_baseline", "fingerprint"}
        if not required.issubset(by_kind):
            ledger.finish_attempt(
                attempt["attempt_id"], AttemptState.BLOCKED, TaskState.BLOCKED,
                FailureKind.ARTIFACT_CORRUPT, {"missing_kinds": sorted(required - by_kind.keys())},
            )
            return
        try:
            result = validate_result_schema(json.loads(self.store.resolve(sorted(by_kind["result_envelope"])[-1]).read_text(encoding="utf-8")))
            from .contract import InputFingerprint, WorkspaceBaseline

            baseline = WorkspaceBaseline.model_validate_json(self.store.resolve(by_kind["workspace_baseline"][0]).read_text(encoding="utf-8"))
            fingerprint = InputFingerprint.model_validate_json(self.store.resolve(by_kind["fingerprint"][0]).read_text(encoding="utf-8"))
        except Exception as exc:
            ledger.finish_attempt(
                attempt["attempt_id"], AttemptState.BLOCKED, TaskState.BLOCKED,
                FailureKind.ARTIFACT_CORRUPT, {"message": str(exc)},
            )
            return
        base = artifact_base(run_id, task["external_key"], attempt["attempt_no"])
        self._verify_and_finish(ledger, run_id, task, spec, attempt["attempt_id"], result, baseline, fingerprint, base)

    def generate_report(self, ledger: Ledger, run_id: str) -> dict[str, Any]:
        snapshot = ledger.load_run_snapshot(run_id)
        run = snapshot["run"]
        token_totals = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        unknown_usage = False
        for session in snapshot["sessions"]:
            if session["usage_status"] != "measured" or not session["usage_json"]:
                unknown_usage = True
                continue
            usage = json.loads(session["usage_json"])
            for usage_snapshot in usage.get("snapshots", []):
                delta = usage_snapshot.get("delta")
                if not isinstance(delta, dict):
                    unknown_usage = True
                    continue
                for key in token_totals:
                    token_totals[key] += int(delta.get(key, 0))
        wall_clock_seconds = None
        if run["started_at"] and run["ended_at"]:
            from datetime import datetime

            wall_clock_seconds = round(
                (
                    datetime.fromisoformat(run["ended_at"].replace("Z", "+00:00"))
                    - datetime.fromisoformat(run["started_at"].replace("Z", "+00:00"))
                ).total_seconds(),
                3,
            )
        terminal_durations_ms: list[float] = []
        terminal_duration_complete = True
        terminal_artifacts = [
            artifact
            for artifact in snapshot["artifacts"]
            if artifact["kind"] == "terminal_evidence"
        ]
        for artifact in terminal_artifacts:
            try:
                terminal = json.loads(
                    self.store.resolve(artifact["relative_path"]).read_text(
                        encoding="utf-8"
                    )
                )
                duration_ms = terminal.get("duration_ms")
                if (
                    not isinstance(duration_ms, (int, float))
                    or isinstance(duration_ms, bool)
                    or duration_ms < 0
                ):
                    terminal_duration_complete = False
                    continue
                terminal_durations_ms.append(float(duration_ms))
            except (OSError, json.JSONDecodeError, TypeError):
                terminal_duration_complete = False
        model_active_seconds = (
            round(sum(terminal_durations_ms) / 1000.0, 3)
            if terminal_duration_complete
            and len(terminal_artifacts) == run["turns_used"]
            else None
        )
        output_schema_sha256 = sha256_bytes(
            canonical_json(result_schema()).encode("utf-8")
        )

        def report_attempt(attempt: dict[str, Any]) -> dict[str, Any]:
            envelope = TaskEnvelope.model_validate_json(attempt["task_contract_json"])
            return {
                "attempt_no": attempt["attempt_no"],
                "state": attempt["state"],
                "failure_kind": attempt["failure_kind"],
                "resume_count": attempt["resume_count"],
                "task_semantics_sha256": task_semantics_sha256(envelope),
                "initial_prompt_sha256": sha256_bytes(
                    render_worker_prompt(envelope).encode("utf-8")
                ),
                "output_schema_sha256": output_schema_sha256,
            }
        report = RunReportEnvelope(
            schema_version=1,
            run_id=run_id,
            state=run["state"],
            project_id=run["project_id"],
            request=run["request_text"],
            metrics={
                "turns": run["turns_used"],
                "sessions": len(snapshot["sessions"]),
                "tasks": len(snapshot["tasks"]),
                "attempts": sum(len(task["attempts"]) for task in snapshot["tasks"]),
                "checks_passed": sum(1 for check in snapshot["checks"] if check["state"] == "PASSED"),
                "checks_failed": sum(1 for check in snapshot["checks"] if check["state"] in {"FAILED", "ERROR"}),
                "wall_clock_seconds": wall_clock_seconds,
                "model_active_seconds": model_active_seconds,
                "usage_status": "partial_or_unknown" if unknown_usage else "measured",
                "token_usage": token_totals,
                "decisions": len(snapshot["decisions"]),
                "manual_copy_or_relay_count": None,
                "manual_recovery_seconds": None,
            },
            tasks=[
                {
                    "key": task["external_key"],
                    "state": task["state"],
                    "attempts": [report_attempt(attempt) for attempt in task["attempts"]],
                }
                for task in snapshot["tasks"]
            ],
        ).model_dump(mode="json")
        base = f"runs/{run_id}/report"
        self._persist(
            ledger, run_id=run_id, relative_path=f"{base}/summary.json",
            value=report, kind="report", media_type="application/json",
        )
        lines = [
            f"# Run {run_id}",
            "",
            f"- 상태: {run['state']}",
            f"- 프로젝트: {run['project_id']}",
            f"- Task: {report['metrics']['tasks']}",
            f"- Attempt: {report['metrics']['attempts']}",
            f"- Turn: {report['metrics']['turns']}",
            f"- Session: {report['metrics']['sessions']}",
            f"- Wall-clock(초): {report['metrics']['wall_clock_seconds']}",
            f"- Usage 상태: {report['metrics']['usage_status']}",
            "",
            "## Task 결과",
            "",
            *[f"- {task['key']}: {task['state']}" for task in report["tasks"]],
            "",
        ]
        self._persist(
            ledger, run_id=run_id, relative_path=f"{base}/summary.md",
            value="\n".join(lines), kind="report", media_type="text/markdown",
        )
        return report


def read_run_spec_from_state(state_root: Path, run_id: str) -> RunSpec:
    path = ArtifactStore(state_root).resolve(f"runs/{run_id}/request/run-spec.yaml")
    try:
        return RunSpec.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    except (OSError, ValidationError, yaml.YAMLError) as exc:
        raise ConfigurationError(f"cannot restore Run Spec: {exc}") from exc


def read_project_root_from_state(state_root: Path, run_id: str) -> Path:
    path = ArtifactStore(state_root).resolve(f"runs/{run_id}/request/project-root.txt")
    return Path(path.read_text(encoding="utf-8").strip()).resolve()
