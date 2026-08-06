from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

import benchmark_runner.r6 as r6_module
from benchmark_runner.contract import (
    ArtifactIdentity,
    ExecutionPlan,
    ExperimentControl,
    PreflightRecord,
    utc_now,
)
from benchmark_runner.r6 import (
    R6RuntimeProfile,
    collect_r6_environment,
    create_r6_experiment,
    freeze_r6_pre_execution,
    prepare_r6_b0_cell,
    run_next_r6_cell,
    status_r6_experiment,
)
from benchmark_runner.runner import (
    R4ControllerError,
    atomic_write,
    canonical_json_bytes,
    sha256_file,
)


REPOSITORY = Path(__file__).resolve().parents[3]


def _profile(tmp_path: Path) -> tuple[Path, R6RuntimeProfile]:
    runner_wheel = tmp_path / "runner.whl"
    b1_wheel = tmp_path / "b1.whl"
    runner_wheel.write_bytes(b"runner-r6")
    b1_wheel.write_bytes(b"b1-r6")
    schemas = tmp_path / "schemas"
    shutil.copytree(REPOSITORY / "stages" / "b1-sequential" / "schemas" / "v1", schemas)
    package_root = tmp_path / "site"
    package_root.mkdir()
    git = shutil.which("git")
    assert git is not None
    profile = R6RuntimeProfile(
        source_repository=str(REPOSITORY),
        manifest_path=str(REPOSITORY / "benchmarks" / "manifests" / "b0-b1-frozen.yaml"),
        runner_python=sys.executable,
        benchmark_python=sys.executable,
        git_executable=git,
        codex_executable=sys.executable,
        runner_artifact_path=str(runner_wheel),
        b1_artifact_path=str(b1_wheel),
        b1_pythonpath=str(package_root),
        b1_schema_root=str(schemas),
        b1_command_prefix=[sys.executable, "-m", "orchestrator.cli"],
        runner_artifact=ArtifactIdentity(
            artifact_id="benchmark-runner",
            version="test-commit",
            sha256=sha256_file(runner_wheel),
        ),
        variant_artifacts=[
            ArtifactIdentity(
                artifact_id="b0",
                version="test-commit",
                sha256=sha256_file(runner_wheel),
            ),
            ArtifactIdentity(
                artifact_id="b1",
                version="0.1.0-test",
                sha256=sha256_file(b1_wheel),
            ),
        ],
        seed=20260805,
        model="gpt-5.6-terra",
        reasoning_effort="low",
        runtime_profile_id="local_default",
        plan_reasoning_control="b1_profile_verified_b0_attested_each_cell",
        common_surface_kind="mixed_b0_codex_app_b1_codex_sdk",
        b0_surface_kind="codex_app_task",
        b1_surface_kind="codex_sdk_via_lao_cli",
    )
    profile_path = tmp_path / "profile.json"
    profile_path.write_bytes(canonical_json_bytes(profile))
    return profile_path, profile


def test_create_status_and_paid_run_guard(tmp_path: Path) -> None:
    profile_path, _ = _profile(tmp_path)
    created = create_r6_experiment(profile_path, tmp_path / "state")
    experiment_dir = Path(created.experiment_dir)
    assert status_r6_experiment(experiment_dir).display_state == "CREATED"
    stored = json.loads((experiment_dir / "runtime" / "r6-runtime.json").read_text(encoding="utf-8"))
    assert Path(stored["runner_artifact_path"]).is_absolute()
    with pytest.raises(R4ControllerError, match="confirm-model-usage"):
        run_next_r6_cell(experiment_dir, confirm_model_usage=False)
    assert status_r6_experiment(experiment_dir).display_state == "CREATED"


def test_create_accepts_explicit_revision_without_id_collision(tmp_path: Path) -> None:
    profile_path, _ = _profile(tmp_path)
    revision_1 = create_r6_experiment(profile_path, tmp_path / "state", revision=1)
    revision_2 = create_r6_experiment(profile_path, tmp_path / "state", revision=2)
    plan_2 = ExecutionPlan.model_validate_json(
        (Path(revision_2.experiment_dir) / "execution-plan.json").read_bytes()
    )

    assert revision_1.experiment_id != revision_2.experiment_id
    assert revision_2.experiment_id.endswith("_2")
    assert plan_2.revision == 2


def test_b0_prepare_requires_preflight_before_cell_state_changes(tmp_path: Path) -> None:
    profile_path, profile = _profile(tmp_path)
    profile_path.write_bytes(canonical_json_bytes(profile.model_copy(update={"seed": 0})))
    created = create_r6_experiment(profile_path, tmp_path / "state", revision=2)
    experiment_dir = Path(created.experiment_dir)
    status_before = status_r6_experiment(experiment_dir)
    assert status_before.next_cell_id == "cell_code-change_1_b0"

    with pytest.raises(R4ControllerError, match="Valid preflight"):
        prepare_r6_b0_cell(experiment_dir)

    status_after = status_r6_experiment(experiment_dir)
    assert status_after.cell_states == status_before.cell_states
    assert status_after.display_state == "CREATED"
    assert not (
        experiment_dir / "cells" / "cell_code-change_1_b0" / "workspace"
    ).exists()


def test_create_rejects_changed_frozen_artifact(tmp_path: Path) -> None:
    profile_path, profile = _profile(tmp_path)
    Path(profile.runner_artifact_path).write_bytes(b"tampered")
    with pytest.raises(R4ControllerError, match="Runner artifact"):
        create_r6_experiment(profile_path, tmp_path / "state")


def test_collect_environment_checks_doctor_profile_without_turn(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, profile = _profile(tmp_path)
    profiles_path = tmp_path / "runtime-profiles.yaml"
    profiles_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "profiles": {
                    "local_default": {
                        "runtime": "codex",
                        "model": "gpt-5.6-terra",
                        "auth_method": "chatgpt",
                        "reasoning_effort": "low",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    def fake_run_json(command, *, pythonpath=None, timeout_seconds=30):
        assert "doctor" in command
        assert pythonpath == profile.b1_pythonpath
        doctor_project = Path(command[command.index("--project") + 1])
        assert (doctor_project / ".git").is_dir()
        return (
            0,
            {
                "codex_sdk": {"installed": True, "pinned": True, "version": "0.144.4"},
                "codex_login": {"checked": True, "authenticated": True, "method": "chatgpt"},
                "workspace": {"healthy": True},
                "worktree": {"clean": True, "entries": []},
                "runtime_profiles_path": str(profiles_path),
            },
            "",
        )

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(r6_module, "_run_json", fake_run_json)
    original_run = subprocess.run

    def fake_subprocess_run(command, *args, **kwargs):
        if command == [profile.codex_executable, "--version"]:
            return SimpleNamespace(
                returncode=0,
                stdout="codex-cli 0.144.4\n",
                stderr="",
            )
        return original_run(command, *args, **kwargs)

    monkeypatch.setattr(r6_module.subprocess, "run", fake_subprocess_run)
    evidence = collect_r6_environment(profile)
    assert evidence["validated_without_model_turn"] is True
    assert evidence["actual_model_turns"] == "0"
    assert evidence["b1_reasoning_control"] == "runtime_profile_verified"


def test_freeze_requires_preflight_and_preserves_zero_started_cells(tmp_path: Path) -> None:
    profile_path, profile = _profile(tmp_path)
    created = create_r6_experiment(profile_path, tmp_path / "state")
    experiment_dir = Path(created.experiment_dir)
    plan = ExecutionPlan.model_validate_json(
        (experiment_dir / "execution-plan.json").read_bytes()
    )
    evidence_path = experiment_dir / "preflight" / "evidence.json"
    evidence = {
        "plan_fingerprint": plan.plan_fingerprint,
        "runner_sha256": plan.runner.sha256,
        "actual_model_turns": 0,
        "fixture_trees": {item.fixture_id: item.git_tree for item in plan.fixtures},
        "python_version": "3.12.test",
        "git_version": "git version test",
        "task_deadline_seconds": 900,
        "environment": {
            "validated_without_model_turn": True,
            "model": profile.model,
            "auth_method": profile.auth_method,
            "reasoning_effort": profile.reasoning_effort,
            "surface_kind": profile.common_surface_kind,
        },
    }
    atomic_write(evidence_path, canonical_json_bytes(evidence))
    control_path = experiment_dir / "experiment-control.json"
    control = ExperimentControl.model_validate_json(control_path.read_bytes()).model_copy(
        update={
            "preflight": PreflightRecord(
                completed_at=utc_now(),
                evidence_path=evidence_path.relative_to(experiment_dir).as_posix(),
                evidence_sha256=sha256_file(evidence_path),
                plan_fingerprint=plan.plan_fingerprint,
            )
        }
    )
    atomic_write(control_path, canonical_json_bytes(control))
    regression_path = tmp_path / "nonlive.json"
    atomic_write(
        regression_path,
        canonical_json_bytes(
            {
                "status": "passed",
                "source_commit": plan.runner.version,
                "actual_model_turns": 0,
            }
        ),
    )
    result = freeze_r6_pre_execution(
        experiment_dir,
        regression_path,
        tmp_path / "frozen",
    )
    frozen = json.loads(Path(result.freeze_record_path).read_text(encoding="utf-8"))
    assert frozen["status"] == "frozen_before_first_cell"
    assert frozen["planned_cells"] == 12
    assert frozen["actual_model_turns"] == 0
    assert "paid 12-Cell" in frozen["limits"][-1]
