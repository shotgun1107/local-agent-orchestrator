"""R6 installed-artifact experiment bootstrap and execution boundary."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, model_validator

from .contract import (
    ArtifactIdentity,
    CellLifecycleState,
    ExecutionPlan,
    ExperimentControl,
    ExperimentDisplayState,
    StrictModel,
)
from .plan import assert_plan_integrity
from .workspace import FixtureRestorer, load_frozen_manifest
from .runner import (
    R4ControllerError,
    R4ExperimentController,
    R4ExperimentCreated,
    R4RunNextResult,
    R6B0ManualDriver,
    R6B1SequentialDriver,
    atomic_write,
    canonical_json_bytes,
    create_r4_experiment_from_manifest,
    frozen_b0_b1_decision_policy,
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
    treatment_control: Literal["partial"] = "partial"

    @model_validator(mode="after")
    def exact_b0_b1_artifacts(self) -> R6RuntimeProfile:
        by_id = {item.artifact_id: item for item in self.variant_artifacts}
        if len(by_id) != len(self.variant_artifacts) or set(by_id) != {"b0", "b1"}:
            raise ValueError("R6 requires exactly one b0 and one b1 artifact")
        if by_id["b0"].sha256 != self.runner_artifact.sha256:
            raise ValueError("R6 b0 manual driver must be the frozen Runner artifact")
        return self


class R6FreezeResult(StrictModel):
    experiment_id: str
    execution_plan_path: str
    freeze_record_path: str
    actual_model_turns: Literal[0] = 0


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

    if os.environ.get("OPENAI_API_KEY"):
        raise R4ControllerError("OPENAI_API_KEY is present")
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


def _require_interactive_b0_stdin(experiment_dir: Path) -> None:
    """Fail before state mutation when the next live B0 Cell cannot read input."""

    experiment_dir = experiment_dir.resolve()
    status = status_r6_experiment(experiment_dir)
    next_cell_id = status.next_cell_id
    if next_cell_id is None:
        return
    state = status.cell_states[next_cell_id]
    if state not in {CellLifecycleState.PLANNED, CellLifecycleState.PREPARED}:
        return
    plan = ExecutionPlan.model_validate_json(
        (experiment_dir / "execution-plan.json").read_bytes()
    )
    assert_plan_integrity(plan)
    next_cell = next(cell for cell in plan.cells if cell.cell_id == next_cell_id)
    if next_cell.variant_id != "b0":
        return
    is_interactive = getattr(sys.stdin, "isatty", lambda: False)()
    if not is_interactive:
        raise R4ControllerError(
            "B0 run-next requires interactive stdin; no Cell state was changed"
        )


def run_next_r6_cell(experiment_dir: Path, *, confirm_model_usage: bool) -> R4RunNextResult:
    if not confirm_model_usage:
        raise R4ControllerError("R6 run-next requires --confirm-model-usage")
    _require_interactive_b0_stdin(experiment_dir)
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
