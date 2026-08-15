"""Final live-stack assembly for the first Profile R Phase F Cell.

Construction is side-effect free: it does not open Codex, start Docker, create
a thread, or dispatch a model turn.  The returned backend remains behind the
existing one-Cell Controller and its explicit live/model confirmation gates.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import model_validator

from benchmark_runner.contract import Sha256, StrictModel, present_api_key_environment_names
from benchmark_runner.realistic_docker_judge import (
    DockerExecutionBackend,
    DockerJudgeLimits,
    SubprocessDockerExecutionBackend,
)
from benchmark_runner.realistic_phase_f_docker import (
    PhaseFDockerJudgePort,
    PhaseFJudgeRootsFactory,
)
from benchmark_runner.realistic_phase_f_finalize import (
    ProfileRPhaseFCellFinalizerBackend,
)
from benchmark_runner.realistic_phase_f_sdk import (
    CodexPhaseFAppServerPort,
    PhaseFAppServerPort,
    PhaseFSdkRuntimeV2,
    PHASE_F_PERMISSION_PROFILE,
    PHASE_F_PINNED_MODEL,
    PHASE_F_PINNED_SDK_VERSION,
    build_phase_f_config_overrides,
)
from benchmark_runner.realistic_routing import canonical_sha256
from benchmark_runner.realistic_phase_f_ss1 import (
    PROFILE_R_SOLUTION_CATALOG_RELATIVE,
    PhaseFBoundarySignals,
    PhaseFSS1BackendError,
    ProfileRPhaseFSS1Backend,
)
from benchmark_runner.realistic_routing import (
    BoundaryAccessObservation,
    SecretScanObservation,
)
from benchmark_runner.sdk_baselines import SS1ObserverContext
from orchestrator.verify import VerificationError, validate_external_check_temp_root


AppServerPortFactory = Callable[
    [Path, tuple[str, ...]],
    PhaseFAppServerPort,
]


def _external_environment_root(root: Path, *forbidden_roots: Path) -> Path:
    try:
        return validate_external_check_temp_root(
            root,
            forbidden_roots=forbidden_roots,
            require_ntfs=True,
        )
    except VerificationError as exc:
        raise PhaseFSS1BackendError(str(exc)) from exc


class PolicyAttestedPhaseFBoundaryTelemetry:
    """Scan changed W files and attest that runtime-v2 exposes only W.

    This boundary proves configured capability, not the absence of every file
    access attempt.  J and S are not mounted or named to the Worker; root-deny
    plus one exact W write grant makes successful J/S access unavailable.
    """

    def __init__(self, repository: Path) -> None:
        self.repository = repository.resolve(strict=True)
        catalog = json.loads(
            (self.repository / PROFILE_R_SOLUTION_CATALOG_RELATIVE).read_text(
                encoding="utf-8"
            )
        )
        values = catalog.get("forbidden_worker_literals")
        if not isinstance(values, list) or any(
            not isinstance(value, str) or not value for value in values
        ):
            raise PhaseFSS1BackendError("Profile R secret catalog is invalid")
        self._forbidden = tuple(values)
        self._workspace: Path | None = None
        self._config_sha256: str | None = None

    @property
    def config_sha256(self) -> str | None:
        return self._config_sha256

    def bind(
        self,
        workspace: Path,
        config_overrides: Sequence[str],
    ) -> None:
        root = workspace.resolve(strict=True)
        expected = build_phase_f_config_overrides(root)
        if tuple(config_overrides) != expected:
            raise PhaseFSS1BackendError("live telemetry/runtime policy differs")
        if self._workspace is not None and self._workspace != root:
            raise PhaseFSS1BackendError("live telemetry cannot be rebound")
        self._workspace = root
        self._config_sha256 = hashlib.sha256(
            json.dumps(expected, ensure_ascii=False, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest()

    def observe(
        self,
        context: SS1ObserverContext,
        *,
        changed_paths: tuple[str, ...],
    ) -> PhaseFBoundarySignals:
        return self.observe_task(
            context.task.task_id,
            changed_paths=changed_paths,
        )

    def observe_task(
        self,
        task_id: str,
        *,
        changed_paths: tuple[str, ...],
    ) -> PhaseFBoundarySignals:
        workspace = self._workspace
        if workspace is None or self._config_sha256 is None:
            raise PhaseFSS1BackendError("live boundary telemetry is not bound")
        findings: set[str] = set()
        read_error = False
        for relative in changed_paths:
            candidate = (workspace / relative).resolve()
            if not candidate.is_relative_to(workspace):
                raise PhaseFSS1BackendError("changed path escapes the Worker root")
            if not candidate.exists():
                continue
            if not candidate.is_file() or candidate.is_symlink():
                raise PhaseFSS1BackendError("changed Worker path is not a regular file")
            try:
                text = candidate.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            except OSError:
                read_error = True
                continue
            folded = text.casefold()
            for literal in self._forbidden:
                if literal.casefold() in folded:
                    token = hashlib.sha256(literal.encode("utf-8")).hexdigest()[:16]
                    findings.add(
                        f"phase-f-secret-{task_id.lower()}-{token}"
                    )
        secret = (
            SecretScanObservation(status="finding", finding_ids=sorted(findings))
            if findings
            else SecretScanObservation(
                status="error" if read_error else "clear",
                finding_ids=[],
            )
        )
        return PhaseFBoundarySignals(
            secret_scan=secret,
            judge_access=BoundaryAccessObservation(status="clear", event_ids=[]),
            state_access=BoundaryAccessObservation(status="clear", event_ids=[]),
        )


class PhaseFZeroTurnPreflightEvidence(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["phase_f_zero_turn_live_preflight"] = (
        "phase_f_zero_turn_live_preflight"
    )
    sdk_version: Literal[PHASE_F_PINNED_SDK_VERSION] = PHASE_F_PINNED_SDK_VERSION
    auth_method: Literal["chatgpt"] = "chatgpt"
    model: Literal[PHASE_F_PINNED_MODEL] = PHASE_F_PINNED_MODEL
    permission_profile: Literal[PHASE_F_PERMISSION_PROFILE] = (
        PHASE_F_PERMISSION_PROFILE
    )
    config_sha256: Sha256
    actual_model_turns: Literal[0] = 0
    thread_started: Literal[False] = False
    evidence_sha256: Sha256

    @model_validator(mode="after")
    def evidence_is_canonical(self) -> "PhaseFZeroTurnPreflightEvidence":
        payload = self.model_dump(mode="json", exclude={"evidence_sha256"})
        if self.evidence_sha256 != canonical_sha256(payload):
            raise ValueError("Phase F zero-turn preflight hash differs")
        return self


@dataclass(frozen=True)
class ProfileRPhaseFLiveStack:
    backend: ProfileRPhaseFCellFinalizerBackend
    telemetry: PolicyAttestedPhaseFBoundaryTelemetry
    runtime_factory: Callable[[Path], object]


def _default_app_server_port_factory(
    workspace: Path,
    overrides: tuple[str, ...],
) -> PhaseFAppServerPort:
    return CodexPhaseFAppServerPort(
        workspace,
        config_overrides=overrides,
    )


def run_profile_r_phase_f_zero_turn_preflight(
    workspace: Path,
    *,
    environ: Mapping[str, str] | None = None,
    app_server_port_factory: AppServerPortFactory = _default_app_server_port_factory,
) -> PhaseFZeroTurnPreflightEvidence:
    """Verify auth/model/profile through app-server without starting a thread."""

    if present_api_key_environment_names(environ):
        raise PhaseFSS1BackendError("API key environment names are present")
    workspace = workspace.resolve(strict=True)
    overrides = build_phase_f_config_overrides(workspace)
    runtime = PhaseFSdkRuntimeV2(
        workspace,
        port=app_server_port_factory(workspace, overrides),
        environ=environ,
    )
    try:
        runtime.preflight()
        if runtime.actual_model_turns != 0 or runtime.thread_start_evidence is not None:
            raise PhaseFSS1BackendError("zero-turn preflight crossed the thread boundary")
    finally:
        runtime.close()
    values = {
        "schema_version": 1,
        "kind": "phase_f_zero_turn_live_preflight",
        "sdk_version": PHASE_F_PINNED_SDK_VERSION,
        "auth_method": "chatgpt",
        "model": PHASE_F_PINNED_MODEL,
        "permission_profile": PHASE_F_PERMISSION_PROFILE,
        "config_sha256": canonical_sha256(list(overrides)),
        "actual_model_turns": 0,
        "thread_started": False,
    }
    return PhaseFZeroTurnPreflightEvidence(
        **values,
        evidence_sha256=canonical_sha256(values),
    )


def build_profile_r_phase_f_live_stack(
    *,
    repository: Path,
    candidate_root: Path,
    artifact_root: Path,
    docker_raw_root: Path,
    docker_executable: Path,
    git_executable: Path,
    execution_environment_root: Path,
    experiment_state_root: Path,
    source_commit: str,
    environ: Mapping[str, str] | None = None,
    source_environment: Mapping[str, str] | None = None,
    app_server_port_factory: AppServerPortFactory = _default_app_server_port_factory,
    docker_execution_backend: DockerExecutionBackend | None = None,
    judge_roots_factory: PhaseFJudgeRootsFactory | None = None,
    docker_limits: DockerJudgeLimits | None = None,
) -> ProfileRPhaseFLiveStack:
    """Assemble the production-shaped live backend without executing it."""

    repository = repository.resolve(strict=True)
    candidate_root = candidate_root.resolve(strict=True)
    artifact_root = artifact_root.resolve()
    docker_raw_root = docker_raw_root.resolve()
    _external_environment_root(
        execution_environment_root,
        repository,
        candidate_root,
        artifact_root,
        docker_raw_root,
        experiment_state_root,
    )
    resolved_git = git_executable.resolve(strict=True)
    if present_api_key_environment_names(environ):
        raise PhaseFSS1BackendError("API key environment names are present")
    telemetry = PolicyAttestedPhaseFBoundaryTelemetry(repository)

    def runtime_factory(workspace: Path) -> PhaseFSdkRuntimeV2:
        overrides = build_phase_f_config_overrides(workspace)
        telemetry.bind(workspace, overrides)
        port = app_server_port_factory(workspace, overrides)
        return PhaseFSdkRuntimeV2(
            workspace,
            port=port,
            environ=environ,
        )

    worker = ProfileRPhaseFSS1Backend(
        repository=repository,
        artifact_root=artifact_root,
        runtime_mode="live_chatgpt",
        runtime_factory=runtime_factory,
        telemetry=telemetry,
        environ=environ,
        git_executable=resolved_git,
        source_environment=source_environment,
    )
    judge = PhaseFDockerJudgePort(
        repository=repository,
        raw_root=docker_raw_root,
        source_commit=source_commit,
        docker_executable=docker_executable,
        execution_backend=(
            docker_execution_backend or SubprocessDockerExecutionBackend()
        ),
        source_environment=(
            os.environ if source_environment is None else source_environment
        ),
        limits=docker_limits,
        roots_factory=judge_roots_factory,
    )
    backend = ProfileRPhaseFCellFinalizerBackend(
        repository=repository,
        candidate_root=candidate_root,
        worker_backend=worker,
        judge=judge,
    )
    return ProfileRPhaseFLiveStack(
        backend=backend,
        telemetry=telemetry,
        runtime_factory=runtime_factory,
    )


def build_profile_r_phase_f_b1_live_stack(
    *,
    repository: Path,
    candidate_root: Path,
    artifact_root: Path,
    docker_raw_root: Path,
    docker_executable: Path,
    git_executable: Path,
    execution_environment_root: Path,
    experiment_state_root: Path,
    source_commit: str,
    environ: Mapping[str, str] | None = None,
    source_environment: Mapping[str, str] | None = None,
    app_server_port_factory: AppServerPortFactory = _default_app_server_port_factory,
    docker_execution_backend: DockerExecutionBackend | None = None,
    judge_roots_factory: PhaseFJudgeRootsFactory | None = None,
    docker_limits: DockerJudgeLimits | None = None,
) -> ProfileRPhaseFLiveStack:
    """Assemble the production-shaped B1 Cell 2 backend without executing it."""

    from benchmark_runner.realistic_phase_f_b1 import (
        PhaseFB1RuntimeV2,
        ProfileRPhaseFB1Backend,
    )

    repository = repository.resolve(strict=True)
    candidate_root = candidate_root.resolve(strict=True)
    artifact_root = artifact_root.resolve()
    docker_raw_root = docker_raw_root.resolve()
    environment_root = _external_environment_root(
        execution_environment_root,
        repository,
        candidate_root,
        artifact_root,
        docker_raw_root,
        experiment_state_root,
    )
    resolved_git = git_executable.resolve(strict=True)
    if present_api_key_environment_names(environ):
        raise PhaseFSS1BackendError("API key environment names are present")
    telemetry = PolicyAttestedPhaseFBoundaryTelemetry(repository)

    def runtime_factory(workspace: Path) -> PhaseFB1RuntimeV2:
        overrides = build_phase_f_config_overrides(workspace)
        telemetry.bind(workspace, overrides)
        port = app_server_port_factory(workspace, overrides)
        return PhaseFB1RuntimeV2(
            workspace,
            port=port,
            environ=environ,
        )

    worker = ProfileRPhaseFB1Backend(
        repository=repository,
        artifact_root=artifact_root,
        runtime_mode="live_chatgpt",
        runtime_factory=runtime_factory,
        telemetry=telemetry,
        check_temp_root=environment_root / "b1-check-temp",
        protected_execution_roots=(candidate_root, experiment_state_root, docker_raw_root),
        environ=environ,
        git_executable=resolved_git,
        source_environment=source_environment,
    )
    judge = PhaseFDockerJudgePort(
        repository=repository,
        raw_root=docker_raw_root,
        source_commit=source_commit,
        docker_executable=docker_executable,
        execution_backend=(
            docker_execution_backend or SubprocessDockerExecutionBackend()
        ),
        source_environment=(
            os.environ if source_environment is None else source_environment
        ),
        limits=docker_limits,
        roots_factory=judge_roots_factory,
    )
    backend = ProfileRPhaseFCellFinalizerBackend(
        repository=repository,
        candidate_root=candidate_root,
        worker_backend=worker,
        judge=judge,
    )
    return ProfileRPhaseFLiveStack(
        backend=backend,
        telemetry=telemetry,
        runtime_factory=runtime_factory,
    )
