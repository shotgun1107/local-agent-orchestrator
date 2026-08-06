"""R6 installed-artifact experiment bootstrap and execution boundary."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, model_validator

from .contract import (
    ArtifactIdentity,
    B0Attestation,
    CellLifecycleState,
    CellStateRecord,
    ExecutionPlan,
    ExperimentControl,
    ExperimentDisplayState,
    StrictModel,
    present_api_key_environment_names,
    utc_now,
)
from .plan import assert_plan_integrity
from .workspace import FixtureRestorer, load_frozen_manifest
from .runner import (
    R4ControllerError,
    R4ExperimentController,
    R4ExperimentCreated,
    R4PrepareNextResult,
    R4RunNextResult,
    R6PreparedRecord,
    R6B0ControlKind,
    R6B0ManualDriver,
    R6B0TaskPromptPlan,
    R6B1SequentialDriver,
    _process_is_alive,
    _process_start_identity,
    atomic_write,
    canonical_json_bytes,
    create_r4_experiment_from_manifest,
    enqueue_r6_b0_control_command,
    frozen_b0_b1_decision_policy,
    read_r6_b0_control_commands,
    sha256_file,
)


class R6RuntimeProfile(StrictModel):
    """Local, secret-free wiring for one frozen B0/B1 experiment."""

    schema_version: Literal[1] = 1
    source_repository: str = Field(min_length=1)
    manifest_path: str = Field(min_length=1)
    runner_python: str = Field(min_length=1)
    benchmark_python: str = Field(min_length=1)
    git_executable: str = Field(min_length=1)
    codex_executable: str = Field(min_length=1)
    runner_artifact_path: str = Field(min_length=1)
    b1_artifact_path: str = Field(min_length=1)
    b1_pythonpath: str = Field(min_length=1)
    b1_schema_root: str = Field(min_length=1)
    b1_command_prefix: list[str] = Field(min_length=1)
    runner_artifact: ArtifactIdentity
    variant_artifacts: list[ArtifactIdentity]
    seed: int
    model: str = Field(min_length=1)
    auth_method: Literal["chatgpt"] = "chatgpt"
    reasoning_effort: str = Field(min_length=1)
    runtime_profile_id: str = Field(min_length=1)
    plan_reasoning_control: str = Field(min_length=1)
    common_surface_kind: str = Field(min_length=1)
    b0_surface_kind: str = Field(min_length=1)
    b1_surface_kind: str = Field(min_length=1)
    b0_codex_project_root: str | None = None
    b0_codex_project_name: str = Field(
        default="AI 오케스트레이터 실험실",
        min_length=1,
    )
    b0_launch_policy: Literal["background_thread_only"] = "background_thread_only"
    treatment_control: Literal["partial"] = "partial"

    @model_validator(mode="after")
    def exact_b0_b1_artifacts(self) -> R6RuntimeProfile:
        by_id = {item.artifact_id: item for item in self.variant_artifacts}
        if len(by_id) != len(self.variant_artifacts) or set(by_id) != {"b0", "b1"}:
            raise ValueError("R6 requires exactly one b0 and one b1 artifact")
        if by_id["b0"].sha256 != self.runner_artifact.sha256:
            raise ValueError("R6 b0 manual driver must be the frozen Runner artifact")
        if self.b0_codex_project_root is not None:
            root = Path(self.b0_codex_project_root)
            if root.name != self.b0_codex_project_name:
                raise ValueError("R6 B0 Codex project path and project name must match")
        return self


class R6FreezeResult(StrictModel):
    experiment_id: str
    execution_plan_path: str
    freeze_record_path: str
    actual_model_turns: Literal[0] = 0


class R6B0PreparedResult(StrictModel):
    experiment_id: str
    cell_id: str
    action: Literal["prepared", "already_prepared"]
    workspace: str
    prompt_path: str
    prompt_paths: list[str]
    prompt_plan_path: str
    codex_project_root: str | None = None
    codex_project_name: str = "AI 오케스트레이터 실험실"
    launch_policy: Literal["background_thread_only"] = "background_thread_only"
    cell_state: Literal["PREPARED"] = "PREPARED"
    actual_model_turns: Literal[0] = 0


class R6B0StartResult(StrictModel):
    experiment_id: str
    cell_id: str
    controller_pid: int
    cell_state: Literal["ACTIVE"] = "ACTIVE"
    workspace: str
    prompt_path: str
    prompt_paths: list[str]
    prompt_plan_path: str
    codex_project_root: str | None = None
    codex_project_name: str = "AI 오케스트레이터 실험실"
    launch_policy: Literal["background_thread_only"] = "background_thread_only"


class R6B0CommandResult(StrictModel):
    experiment_id: str
    cell_id: str
    sequence: int
    kind: str
    received_at: str
    task_key: str | None = None
    prompt_path: str | None = None
    prompt_sha256: str | None = None


class R6B0CompleteResult(StrictModel):
    experiment_id: str
    cell_id: str
    cell_state: str
    display_state: ExperimentDisplayState
    stop_reason: str | None = None


class R6B0ControllerProcess(StrictModel):
    schema_version: Literal[1] = 1
    experiment_id: str
    cell_id: str
    pid: int
    process_start_identity: str
    status: Literal["running", "completed"]
    started_at: str
    completed_at: str | None = None
    stdout_path: str
    stderr_path: str


def _resolve(value: str, base: Path) -> str:
    path = Path(value)
    return str((path if path.is_absolute() else base / path).resolve())


def load_r6_profile(path: Path) -> R6RuntimeProfile:
    path = path.resolve()
    profile = R6RuntimeProfile.model_validate_json(path.read_bytes())
    base = path.parent
    path_fields = (
        "source_repository",
        "manifest_path",
        "runner_python",
        "benchmark_python",
        "git_executable",
        "codex_executable",
        "runner_artifact_path",
        "b1_artifact_path",
        "b1_pythonpath",
        "b1_schema_root",
    )
    updates = {field: _resolve(str(getattr(profile, field)), base) for field in path_fields}
    if profile.b0_codex_project_root is not None:
        updates["b0_codex_project_root"] = _resolve(profile.b0_codex_project_root, base)
    command = list(profile.b1_command_prefix)
    command[0] = _resolve(command[0], base)
    updates["b1_command_prefix"] = command
    return profile.model_copy(update=updates)


def _assert_profile_artifacts(profile: R6RuntimeProfile) -> None:
    runner_path = Path(profile.runner_artifact_path)
    b1_path = Path(profile.b1_artifact_path)
    if not runner_path.is_file() or sha256_file(runner_path) != profile.runner_artifact.sha256:
        raise R4ControllerError("Frozen Runner artifact is missing or changed")
    by_id = {item.artifact_id: item for item in profile.variant_artifacts}
    if not b1_path.is_file() or sha256_file(b1_path) != by_id["b1"].sha256:
        raise R4ControllerError("Frozen B1 artifact is missing or changed")
    required_paths = (
        profile.source_repository,
        profile.manifest_path,
        profile.runner_python,
        profile.benchmark_python,
        profile.git_executable,
        profile.codex_executable,
        profile.b1_pythonpath,
        profile.b1_schema_root,
        profile.b1_command_prefix[0],
    )
    if any(not Path(value).exists() for value in required_paths):
        raise R4ControllerError("R6 runtime profile references a missing path")
    if profile.b0_codex_project_root is not None:
        source_repository = Path(profile.source_repository).resolve()
        project_root = Path(profile.b0_codex_project_root).resolve()
        if project_root == source_repository or project_root.is_relative_to(source_repository):
            raise R4ControllerError("R6 B0 Codex project must be outside the source repository")
    schema_names = sorted(path.name for path in Path(profile.b1_schema_root).glob("*.json"))
    if schema_names != [
        "result-envelope.schema.json",
        "run-report.schema.json",
        "run-spec.schema.json",
        "run-status.schema.json",
        "task-envelope.schema.json",
    ]:
        raise R4ControllerError("Frozen B1 public Schema bundle is incomplete")


def create_r6_experiment(
    profile_path: Path,
    state_root: Path,
    *,
    revision: int = 1,
) -> R4ExperimentCreated:
    if revision < 1:
        raise R4ControllerError("R6 revision must be positive")
    profile = load_r6_profile(profile_path)
    _assert_profile_artifacts(profile)
    environment = {
        "model": profile.model,
        "auth_method": profile.auth_method,
        "reasoning_effort": profile.reasoning_effort,
        "surface_kind": profile.common_surface_kind,
        "treatment_control": profile.treatment_control,
    }
    created = create_r4_experiment_from_manifest(
        state_root=state_root,
        source_repository=Path(profile.source_repository),
        manifest_path=Path(profile.manifest_path),
        runner_artifact=profile.runner_artifact,
        variant_artifacts=profile.variant_artifacts,
        baseline_variant="b0",
        candidate_variant="b1",
        seed=profile.seed,
        primary_metrics=[
            "check_success",
            "manual_copy_or_relay_count_excluding_start",
            "manual_recovery_seconds",
            "human_errors_after_pass",
        ],
        decision_policy=frozen_b0_b1_decision_policy(),
        reasoning_control=profile.plan_reasoning_control,
        environment_fingerprint=environment,
        revision=revision,
    )
    destination = Path(created.experiment_dir) / "runtime" / "r6-runtime.json"
    atomic_write(destination, canonical_json_bytes(profile))
    return created


def _run_json(
    command: list[str],
    *,
    pythonpath: str | None = None,
    timeout_seconds: float = 30,
) -> tuple[int, dict[str, object], str]:
    environment = os.environ.copy()
    if pythonpath:
        environment["PYTHONPATH"] = os.pathsep.join(
            value for value in (pythonpath, environment.get("PYTHONPATH")) if value
        )
    result = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
        env=environment,
        shell=False,
    )
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError:
        value = {}
    return result.returncode, value if isinstance(value, dict) else {}, result.stderr.strip()


def collect_r6_environment(profile: R6RuntimeProfile) -> dict[str, str | bool]:
    """Verify the real B1 auth/profile boundary without consuming a model turn."""

    present_keys = present_api_key_environment_names()
    if present_keys:
        raise R4ControllerError(
            f"API key environment is present ({', '.join(present_keys)})"
        )
    manifest = load_frozen_manifest(Path(profile.manifest_path))
    with tempfile.TemporaryDirectory(prefix="lao-r6-doctor-") as temporary:
        doctor_project = Path(temporary) / "project"
        FixtureRestorer(
            Path(profile.source_repository),
            profile.git_executable,
        ).restore(manifest.fixtures[0], doctor_project)
        doctor_command = [
            *profile.b1_command_prefix,
            "doctor",
            "--project",
            str(doctor_project),
            "--json",
        ]
        doctor_exit, doctor, doctor_stderr = _run_json(
            doctor_command,
            pythonpath=profile.b1_pythonpath,
        )
    if not doctor:
        raise R4ControllerError(
            f"B1 doctor returned no JSON without a model turn (exit={doctor_exit}): {doctor_stderr}"
        )
    sdk = doctor.get("codex_sdk")
    login = doctor.get("codex_login")
    if not isinstance(sdk, dict) or sdk.get("pinned") is not True:
        raise R4ControllerError("B1 doctor did not verify the pinned Codex SDK")
    if not isinstance(login, dict) or (
        login.get("authenticated") is not True or login.get("method") != "chatgpt"
    ):
        raise R4ControllerError(
            f"B1 doctor did not verify ChatGPT authentication (exit={doctor_exit})"
        )
    workspace = doctor.get("workspace")
    worktree = doctor.get("worktree")
    if (
        not isinstance(workspace, dict)
        or workspace.get("healthy") is not True
        or not isinstance(worktree, dict)
        or worktree.get("clean") is not True
    ):
        raise R4ControllerError("B1 doctor did not verify a clean standalone Git workspace")
    if doctor_exit != 0:
        raise R4ControllerError(f"B1 doctor failed without a model turn (exit={doctor_exit})")

    profiles_path = doctor.get("runtime_profiles_path")
    if not isinstance(profiles_path, str) or not Path(profiles_path).is_file():
        raise R4ControllerError("B1 runtime profile file was not found")
    profiles = yaml.safe_load(Path(profiles_path).read_text(encoding="utf-8"))
    selected = profiles.get("profiles", {}).get(profile.runtime_profile_id, {})
    expected = {
        "runtime": "codex",
        "model": profile.model,
        "auth_method": profile.auth_method,
        "reasoning_effort": profile.reasoning_effort,
    }
    if selected != expected:
        raise R4ControllerError("B1 runtime profile differs from the frozen R6 controls")

    codex = subprocess.run(
        [profile.codex_executable, "--version"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        shell=False,
    )
    if codex.returncode != 0 or not codex.stdout.strip():
        raise R4ControllerError("Codex CLI version check failed")
    return {
        "validated_without_model_turn": True,
        "model": profile.model,
        "auth_method": profile.auth_method,
        "reasoning_effort": profile.reasoning_effort,
        "surface_kind": profile.common_surface_kind,
        "treatment_control": profile.treatment_control,
        "b0_model_control": "user_attested_each_cell",
        "b0_reasoning_control": "user_attested_each_cell",
        "b1_model_control": "runtime_profile_verified",
        "b1_reasoning_control": "runtime_profile_verified",
        "codex_sdk_version": str(sdk.get("version", "unknown")),
        "codex_cli_version": codex.stdout.strip(),
        "runtime_profile_id": profile.runtime_profile_id,
        "actual_model_turns": "0",
    }


def _controller(
    experiment_dir: Path,
    *,
    preflight_environment: dict[str, str | bool] | None = None,
) -> R4ExperimentController:
    experiment_dir = experiment_dir.resolve()
    profile = load_r6_profile(experiment_dir / "runtime" / "r6-runtime.json")
    _assert_profile_artifacts(profile)
    by_id = {item.artifact_id: item for item in profile.variant_artifacts}
    common = {
        "source_repository": Path(profile.source_repository),
        "manifest_path": Path(profile.manifest_path),
        "benchmark_python": Path(profile.benchmark_python),
        "git_executable": Path(profile.git_executable),
        "runner_python": Path(profile.runner_python),
        "model": profile.model,
        "reasoning_effort": profile.reasoning_effort,
        "auth_method": profile.auth_method,
        "treatment_control": profile.treatment_control,
    }
    drivers = {
        "b0": R6B0ManualDriver(
            **common,
            surface_kind=profile.b0_surface_kind,
            approval_mode="not_applicable_user_session",
            model_control="user_attested_each_cell",
            reasoning_control="user_attested_each_cell",
            codex_project_root=(
                Path(profile.b0_codex_project_root)
                if profile.b0_codex_project_root is not None
                else None
            ),
        ),
        "b1": R6B1SequentialDriver(
            **common,
            surface_kind=profile.b1_surface_kind,
            approval_mode="deny_all",
            model_control="runtime_profile_verified",
            reasoning_control="runtime_profile_verified",
            command_prefix=tuple(profile.b1_command_prefix),
            schema_root=Path(profile.b1_schema_root),
            runtime="codex",
            b1_pythonpath=Path(profile.b1_pythonpath),
        ),
    }
    return R4ExperimentController(
        experiment_dir=experiment_dir,
        source_repository=Path(profile.source_repository),
        manifest_path=Path(profile.manifest_path),
        benchmark_python=Path(profile.benchmark_python),
        git_executable=Path(profile.git_executable),
        current_runner_sha256=profile.runner_artifact.sha256,
        current_variant_sha256={key: value.sha256 for key, value in by_id.items()},
        drivers=drivers,
        preflight_environment=preflight_environment or {},
    )


def preflight_r6_experiment(experiment_dir: Path):
    profile = load_r6_profile(experiment_dir / "runtime" / "r6-runtime.json")
    environment = collect_r6_environment(profile)
    return _controller(experiment_dir, preflight_environment=environment).preflight()


def status_r6_experiment(experiment_dir: Path):
    return _controller(experiment_dir).status()


def _next_r6_cell(experiment_dir: Path):
    experiment_dir = experiment_dir.resolve()
    status = status_r6_experiment(experiment_dir)
    next_cell_id = status.next_cell_id
    if next_cell_id is None:
        raise R4ControllerError("No R6 Cell remains")
    plan = ExecutionPlan.model_validate_json(
        (experiment_dir / "execution-plan.json").read_bytes()
    )
    assert_plan_integrity(plan)
    next_cell = next(cell for cell in plan.cells if cell.cell_id == next_cell_id)
    return status, next_cell


def _require_next_b0(experiment_dir: Path, *states: CellLifecycleState):
    status, cell = _next_r6_cell(experiment_dir)
    if cell.variant_id != "b0":
        raise R4ControllerError("The next R6 Cell is not B0")
    state = status.cell_states[cell.cell_id]
    if states and state not in set(states):
        expected = ", ".join(item.value for item in states)
        raise R4ControllerError(f"B0 Cell must be in {expected}, not {state.value}")
    return status, cell


def _b0_task_prompt_plan(cell_dir: Path) -> R6B0TaskPromptPlan:
    path = cell_dir / "raw" / "b0-task-prompt-plan.json"
    try:
        plan = R6B0TaskPromptPlan.model_validate_json(path.read_bytes())
    except (OSError, ValueError) as exc:
        raise R4ControllerError("B0 Task prompt plan is missing or invalid") from exc
    if not plan.prompts:
        raise R4ControllerError("B0 Task prompt plan is empty")
    for expected_ordinal, prompt in enumerate(plan.prompts, start=1):
        if prompt.ordinal != expected_ordinal:
            raise R4ControllerError("B0 Task prompt ordinals are not contiguous")
        prompt_path = (cell_dir / prompt.relative_path).resolve()
        if not prompt_path.is_relative_to(cell_dir.resolve()):
            raise R4ControllerError("B0 Task prompt escaped its Cell directory")
        if not prompt_path.is_file() or sha256_file(prompt_path) != prompt.sha256:
            raise R4ControllerError("B0 Task prompt is missing or changed")
    return plan


def _b0_task_prompt_paths(cell_dir: Path, plan: R6B0TaskPromptPlan) -> list[str]:
    return [str((cell_dir / item.relative_path).resolve()) for item in plan.prompts]


def prepare_r6_b0_cell(experiment_dir: Path) -> R6B0PreparedResult:
    """Prepare the next B0 workspace without activating its 900-second deadline."""

    experiment_dir = experiment_dir.resolve()
    _require_next_b0(
        experiment_dir,
        CellLifecycleState.PLANNED,
        CellLifecycleState.PREPARED,
    )
    prepared: R4PrepareNextResult = _controller(experiment_dir).prepare_next()
    cell_dir = experiment_dir / "cells" / prepared.cell_id
    profile = load_r6_profile(experiment_dir / "runtime" / "r6-runtime.json")
    record = R6PreparedRecord.model_validate_json(
        (cell_dir / "raw" / "prepared-fixture.json").read_bytes()
    )
    prompt_plan = _b0_task_prompt_plan(cell_dir)
    prompt_paths = _b0_task_prompt_paths(cell_dir, prompt_plan)
    workspace = record.workspace or str((cell_dir / "workspace").resolve())
    return R6B0PreparedResult(
        experiment_id=prepared.experiment_id,
        cell_id=prepared.cell_id,
        action=prepared.action,
        workspace=workspace,
        prompt_path=prompt_paths[0],
        prompt_paths=prompt_paths,
        prompt_plan_path=str((cell_dir / "raw" / "b0-task-prompt-plan.json").resolve()),
        codex_project_root=profile.b0_codex_project_root,
        codex_project_name=profile.b0_codex_project_name,
        launch_policy=profile.b0_launch_policy,
    )


def _b0_controller_record_path(experiment_dir: Path, cell_id: str) -> Path:
    return (
        experiment_dir
        / "cells"
        / cell_id
        / "variant-state"
        / "b0-controller-process"
        / "process.json"
    )


def _require_b0_controller_running(
    experiment_dir: Path,
    cell_id: str,
) -> R6B0ControllerProcess:
    path = _b0_controller_record_path(experiment_dir, cell_id)
    try:
        record = R6B0ControllerProcess.model_validate_json(path.read_bytes())
    except (OSError, ValueError) as exc:
        raise R4ControllerError("B0 controller process record is missing or invalid") from exc
    if (
        record.status != "running"
        or not _process_is_alive(record.pid)
        or _process_start_identity(record.pid) != record.process_start_identity
    ):
        raise R4ControllerError("B0 controller process is not running")
    return record


def start_r6_b0_cell(
    experiment_dir: Path,
    *,
    confirm_model_usage: bool,
    activation_timeout_seconds: float = 30.0,
) -> R6B0StartResult:
    """Start run-next in a hidden process and return only after the B0 Cell is ACTIVE."""

    if not confirm_model_usage:
        raise R4ControllerError("R6 B0 start requires --confirm-model-usage")
    experiment_dir = experiment_dir.resolve()
    status, cell = _require_next_b0(experiment_dir, CellLifecycleState.PREPARED)
    profile = load_r6_profile(experiment_dir / "runtime" / "r6-runtime.json")
    _assert_profile_artifacts(profile)
    record_path = _b0_controller_record_path(experiment_dir, cell.cell_id)
    if record_path.exists():
        raise R4ControllerError("B0 controller process record already exists")
    process_dir = record_path.parent
    process_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = process_dir / "stdout.txt"
    stderr_path = process_dir / "stderr.txt"
    environment = os.environ.copy()
    package_root = str(Path(__file__).resolve().parents[1])
    environment["PYTHONPATH"] = os.pathsep.join(
        value for value in (package_root, environment.get("PYTHONPATH")) if value
    )
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    command = [
        profile.runner_python,
        "-m",
        "benchmark_runner",
        "r6",
        "run-next",
        "--experiment-dir",
        str(experiment_dir),
        "--confirm-model-usage",
    ]
    popen_options: dict[str, object] = {}
    if os.name == "nt":
        popen_options["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        )
    else:
        popen_options["start_new_session"] = True
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            cwd=experiment_dir,
            env=environment,
            shell=False,
            **popen_options,
        )
    identity = _process_start_identity(process.pid)
    if identity is None:
        process.terminate()
        raise R4ControllerError("R6 could not establish B0 controller identity")
    process_record = R6B0ControllerProcess(
        experiment_id=status.experiment_id,
        cell_id=cell.cell_id,
        pid=process.pid,
        process_start_identity=identity,
        status="running",
        started_at=utc_now().isoformat(),
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
    )
    atomic_write(record_path, canonical_json_bytes(process_record))
    deadline = time.monotonic() + activation_timeout_seconds
    state_path = experiment_dir / "cells" / cell.cell_id / "cell-state.json"
    while time.monotonic() < deadline:
        state = CellStateRecord.model_validate_json(state_path.read_bytes()).state
        if state is CellLifecycleState.ACTIVE:
            cell_dir = state_path.parent
            prompt_plan = _b0_task_prompt_plan(cell_dir)
            prompt_paths = _b0_task_prompt_paths(cell_dir, prompt_plan)
            return R6B0StartResult(
                experiment_id=process_record.experiment_id,
                cell_id=cell.cell_id,
                controller_pid=process.pid,
                workspace=(
                    R6PreparedRecord.model_validate_json(
                        (state_path.parent / "raw" / "prepared-fixture.json").read_bytes()
                    ).workspace
                    or str((state_path.parent / "workspace").resolve())
                ),
                prompt_path=prompt_paths[0],
                prompt_paths=prompt_paths,
                prompt_plan_path=str((cell_dir / "raw" / "b0-task-prompt-plan.json").resolve()),
                codex_project_root=profile.b0_codex_project_root,
                codex_project_name=profile.b0_codex_project_name,
                launch_policy=profile.b0_launch_policy,
            )
        exit_code = process.poll()
        if exit_code is not None:
            detail = stderr_path.read_text(encoding="utf-8", errors="replace").strip()
            raise R4ControllerError(
                f"B0 controller exited before activation (exit={exit_code}): {detail}"
            )
        time.sleep(0.05)
    process.terminate()
    raise R4ControllerError("B0 controller did not activate before the start timeout")


def record_r6_b0_event(
    experiment_dir: Path,
    *,
    kind: R6B0ControlKind,
    task_key: str | None = None,
) -> R6B0CommandResult:
    experiment_dir = experiment_dir.resolve()
    status, cell = _require_next_b0(experiment_dir, CellLifecycleState.ACTIVE)
    _require_b0_controller_running(experiment_dir, cell.cell_id)
    if kind in {"complete", "abort"}:
        raise R4ControllerError("Use B0 complete for terminal commands")
    cell_dir = experiment_dir / "cells" / cell.cell_id
    prompt_path: str | None = None
    prompt_sha256: str | None = None
    if task_key is not None:
        plan = _b0_task_prompt_plan(cell_dir)
        existing = read_r6_b0_control_commands(
            cell_dir / "variant-state" / "b0-control",
            cell_id=cell.cell_id,
        )
        recorded = [command for command in existing if command.task_key is not None]
        if len(recorded) >= len(plan.prompts):
            raise R4ControllerError("Every planned B0 Task prompt is already recorded")
        expected = plan.prompts[len(recorded)]
        if task_key != expected.task_key or kind != expected.event_kind:
            raise R4ControllerError(
                f"Next B0 Task prompt must be {expected.event_kind} for {expected.task_key}"
            )
        prompt_path = str((cell_dir / expected.relative_path).resolve())
        prompt_sha256 = expected.sha256
    command = enqueue_r6_b0_control_command(
        cell_dir / "variant-state" / "b0-control",
        cell_id=cell.cell_id,
        kind=kind,
        task_key=task_key,
        prompt_sha256=prompt_sha256,
    )
    return R6B0CommandResult(
        experiment_id=status.experiment_id,
        cell_id=cell.cell_id,
        sequence=command.sequence,
        kind=command.kind,
        received_at=command.received_at.isoformat(),
        task_key=command.task_key,
        prompt_path=prompt_path,
        prompt_sha256=command.prompt_sha256,
    )


def _assert_b0_task_prompt_evidence(experiment_dir: Path, cell_id: str) -> None:
    cell_dir = experiment_dir / "cells" / cell_id
    plan = _b0_task_prompt_plan(cell_dir)
    if len(plan.prompts) == 1:
        return
    commands = read_r6_b0_control_commands(
        cell_dir / "variant-state" / "b0-control",
        cell_id=cell_id,
    )
    recorded = [command for command in commands if command.task_key is not None]
    expected = [
        (prompt.event_kind, prompt.task_key, prompt.sha256)
        for prompt in plan.prompts
    ]
    actual = [
        (command.kind, command.task_key, command.prompt_sha256)
        for command in recorded
    ]
    if actual != expected:
        raise R4ControllerError(
            "B0 completion requires every planned Task prompt in the frozen order"
        )


def complete_r6_b0_cell(
    experiment_dir: Path,
    *,
    outcome: Literal["completed", "interrupted"],
    confirm_timeline: bool,
    model: str,
    reasoning_effort: str,
    surface_kind: str,
    completion_timeout_seconds: float = 60.0,
) -> R6B0CompleteResult:
    experiment_dir = experiment_dir.resolve()
    status, cell = _require_next_b0(experiment_dir, CellLifecycleState.ACTIVE)
    _require_b0_controller_running(experiment_dir, cell.cell_id)
    profile = load_r6_profile(experiment_dir / "runtime" / "r6-runtime.json")
    if (
        not confirm_timeline
        or model != profile.model
        or reasoning_effort != profile.reasoning_effort
        or surface_kind != profile.b0_surface_kind
    ):
        raise R4ControllerError("B0 controls and complete timeline must be explicitly confirmed")
    _assert_b0_task_prompt_evidence(experiment_dir, cell.cell_id)
    attestation = B0Attestation(
        status="confirmed",
        confirmed_at=utc_now(),
        timeline_complete=True,
        model=model,
        reasoning_effort=reasoning_effort,
        surface_kind=surface_kind,
    )
    enqueue_r6_b0_control_command(
        experiment_dir / "cells" / cell.cell_id / "variant-state" / "b0-control",
        cell_id=cell.cell_id,
        kind="complete" if outcome == "completed" else "abort",
        attestation=attestation,
    )
    deadline = time.monotonic() + completion_timeout_seconds
    while time.monotonic() < deadline:
        current = status_r6_experiment(experiment_dir)
        state = current.cell_states[cell.cell_id]
        if state in {CellLifecycleState.SEALED, CellLifecycleState.STOPPED}:
            process_path = _b0_controller_record_path(experiment_dir, cell.cell_id)
            if process_path.is_file():
                record = R6B0ControllerProcess.model_validate_json(process_path.read_bytes())
                atomic_write(
                    process_path,
                    canonical_json_bytes(
                        record.model_copy(
                            update={
                                "status": "completed",
                                "completed_at": utc_now().isoformat(),
                            }
                        )
                    ),
                )
            return R6B0CompleteResult(
                experiment_id=status.experiment_id,
                cell_id=cell.cell_id,
                cell_state=state.value,
                display_state=current.display_state,
                stop_reason=current.stop_reason,
            )
        time.sleep(0.05)
    raise R4ControllerError("B0 Cell did not seal before the completion timeout")


def run_next_r6_cell(experiment_dir: Path, *, confirm_model_usage: bool) -> R4RunNextResult:
    if not confirm_model_usage:
        raise R4ControllerError("R6 run-next requires --confirm-model-usage")
    profile = load_r6_profile(experiment_dir / "runtime" / "r6-runtime.json")
    environment = collect_r6_environment(profile)
    return _controller(experiment_dir, preflight_environment=environment).run_next()


def freeze_r6_pre_execution(
    experiment_dir: Path,
    regression_record: Path,
    output_dir: Path,
) -> R6FreezeResult:
    """Emit a sanitized freeze record only before the first real Cell starts."""

    experiment_dir = experiment_dir.resolve()
    regression_record = regression_record.resolve()
    output_dir = output_dir.resolve()
    status = status_r6_experiment(experiment_dir)
    if status.display_state is not ExperimentDisplayState.PREFLIGHTED:
        raise R4ControllerError("R6 freeze requires a valid preflight and zero started Cells")
    if any(state is not CellLifecycleState.PLANNED for state in status.cell_states.values()):
        raise R4ControllerError("R6 freeze requires every Cell to remain PLANNED")
    if any((experiment_dir / "cells" / cell_id / "workspace").exists() for cell_id in status.cell_states):
        raise R4ControllerError("R6 freeze refuses a prepared Cell workspace")

    plan_path = experiment_dir / "execution-plan.json"
    plan = ExecutionPlan.model_validate_json(plan_path.read_bytes())
    assert_plan_integrity(plan)
    control = ExperimentControl.model_validate_json(
        (experiment_dir / "experiment-control.json").read_bytes()
    )
    if control.preflight is None:
        raise R4ControllerError("R6 preflight record is missing")
    evidence_path = experiment_dir / control.preflight.evidence_path
    if sha256_file(evidence_path) != control.preflight.evidence_sha256:
        raise R4ControllerError("R6 preflight Evidence changed")
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    if evidence.get("actual_model_turns") != 0:
        raise R4ControllerError("R6 preflight unexpectedly consumed a model turn")

    regression = json.loads(regression_record.read_text(encoding="utf-8"))
    if (
        regression.get("status") != "passed"
        or regression.get("actual_model_turns") != 0
        or regression.get("source_commit") != plan.runner.version
    ):
        raise R4ControllerError("R6 non-live regression record is not valid for this Plan")
    output_dir.mkdir(parents=True, exist_ok=True)
    frozen_plan = output_dir / "execution-plan.json"
    freeze_path = output_dir / "pre-execution-freeze.json"
    if frozen_plan.exists() or freeze_path.exists():
        raise R4ControllerError("R6 freeze outputs already exist")
    atomic_write(frozen_plan, plan_path.read_bytes())
    safe_environment = evidence.get("environment")
    if not isinstance(safe_environment, dict):
        raise R4ControllerError("R6 preflight environment Evidence is invalid")
    freeze_record = {
        "schema_version": 1,
        "status": "frozen_before_first_cell",
        "experiment_id": plan.experiment_id,
        "plan_fingerprint": plan.plan_fingerprint,
        "execution_plan_sha256": sha256_file(frozen_plan),
        "source_commit": plan.runner.version,
        "runner_artifact": plan.runner.model_dump(mode="json"),
        "variant_artifacts": [item.model_dump(mode="json") for item in plan.variants],
        "manifest_sha256": plan.source_manifest.sha256,
        "fixture_trees": evidence.get("fixture_trees"),
        "decision_policy": plan.decision_policy,
        "environment": safe_environment,
        "python_version": evidence.get("python_version"),
        "git_version": evidence.get("git_version"),
        "task_deadline_seconds": evidence.get("task_deadline_seconds"),
        "preflight_evidence_sha256": control.preflight.evidence_sha256,
        "nonlive_regression_sha256": sha256_file(regression_record),
        "planned_cells": status.planned_cells,
        "planned_cell_state_count": len(status.cell_states),
        "actual_model_turns": 0,
        "limits": [
            "B0 model and reasoning are user-attested at each Cell start.",
            "B0 Codex App and B1 CLI/SDK surfaces make treatment_control partial.",
            "The paid 12-Cell comparison has not started; no adoption verdict exists.",
        ],
    }
    atomic_write(freeze_path, canonical_json_bytes(freeze_record))
    return R6FreezeResult(
        experiment_id=plan.experiment_id,
        execution_plan_path=str(frozen_plan),
        freeze_record_path=str(freeze_path),
    )
