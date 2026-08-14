from __future__ import annotations

import os
import json
import shutil
import sys
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

import pytest

from benchmark_runner.realistic_phase_f_live import (
    PolicyAttestedPhaseFBoundaryTelemetry,
    build_profile_r_phase_f_b1_live_stack,
    build_profile_r_phase_f_live_stack,
    run_profile_r_phase_f_zero_turn_preflight,
)
from benchmark_runner.realistic_phase_f_sdk import (
    PHASE_F_PINNED_SDK_VERSION,
    PhaseFAppServerPort,
    build_phase_f_config_overrides,
)
from benchmark_runner.realistic_phase_f_ss1 import materialize_profile_r_workspace
from benchmark_runner.realistic_routing import Ss1TaskRequest
from benchmark_runner.sdk_baselines import SS1ObserverContext


REPOSITORY = Path(__file__).resolve().parents[3]
GIT_EXECUTABLE = Path(shutil.which("git") or "git").resolve()
CANDIDATE_ROOT = (
    REPOSITORY
    / "benchmarks"
    / "artifacts"
    / "sdk-routing-realistic-high-difficulty-phase-e-v1"
)


class DormantPort(PhaseFAppServerPort):
    sdk_version = PHASE_F_PINNED_SDK_VERSION

    def open(self) -> None:
        raise AssertionError("construction must not open app-server")

    def account_type(self) -> str:
        raise AssertionError

    def visible_model_ids(self) -> tuple[str, ...]:
        raise AssertionError

    def permission_profiles(self, cwd: str) -> tuple[Mapping[str, Any], ...]:
        raise AssertionError(cwd)

    def start_thread(self, params: Mapping[str, Any], **kwargs: Any) -> Any:
        raise AssertionError((params, kwargs))

    def start_turn(
        self,
        thread_id: str,
        prompt: str,
        params: Mapping[str, Any],
    ) -> Any:
        raise AssertionError((thread_id, prompt, params))

    def close(self) -> None:
        raise AssertionError


class FakePreflightPort(DormantPort):
    def __init__(self) -> None:
        self.open_count = 0
        self.close_count = 0

    def open(self) -> None:
        self.open_count += 1

    def account_type(self) -> str:
        return "chatgpt"

    def visible_model_ids(self) -> tuple[str, ...]:
        return ("gpt-5.6-sol",)

    def permission_profiles(self, cwd: str) -> tuple[Mapping[str, Any], ...]:
        assert Path(cwd).is_dir()
        return ({"id": "runtime-boundary-worker", "allowed": True},)

    def close(self) -> None:
        self.close_count += 1


class NameOnlyApiKeyMapping(Mapping[str, str]):
    def __iter__(self) -> Iterator[str]:
        return iter(("OPENAI_API_KEY",))

    def __len__(self) -> int:
        return 1

    def __getitem__(self, key: str) -> str:
        raise AssertionError(f"secret value was read: {key}")


def _context(task_id: str = "R01") -> SS1ObserverContext:
    return SS1ObserverContext(
        experiment_id="exp-test",
        cell_id="cell-test",
        task=Ss1TaskRequest(
            task_id=task_id,
            goal="test",
            completion_criteria=["done"],
            declared_inputs=[],
            predecessor_artifacts=[],
            read_scope=["**"],
            write_scope=["**"],
        ),
        raw_attempt_id="attempt-1",
        raw_thread_id="thread-1",
        turn_ordinal=1,
        task_turn_ordinal=1,
        boundary_ordinal=1,
        turn_kind="initial",
        terminal_status="completed",
        error_kind=None,
    )


def test_config_builder_grants_only_exact_workspace_write(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    overrides = build_phase_f_config_overrides(workspace)

    assert len(overrides) == 5
    filesystem = overrides[2]
    assert '":root"="deny"' in filesystem
    assert f'{json.dumps(str(workspace.resolve()))}="write"' in filesystem
    assert "workspace-write" not in "\n".join(overrides).lower()


def test_policy_telemetry_scans_changed_worker_files_and_keeps_js_unexposed(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    telemetry = PolicyAttestedPhaseFBoundaryTelemetry(REPOSITORY)
    telemetry.bind(workspace, build_phase_f_config_overrides(workspace))
    (workspace / "safe.txt").write_text("safe output\n", encoding="utf-8")

    clear = telemetry.observe(_context(), changed_paths=("safe.txt",))

    assert clear.secret_scan.status == "clear"
    assert clear.judge_access.status == "clear"
    assert clear.state_access.status == "clear"
    catalog = json.loads(
        (
            REPOSITORY
            / "benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/"
            "realistic-compat-migration-001/solution-leakage-catalog.json"
        ).read_text(encoding="utf-8")
    )
    secret = catalog["forbidden_worker_literals"][0]
    (workspace / "leak.txt").write_text(secret, encoding="utf-8")

    finding = telemetry.observe(_context(), changed_paths=("leak.txt",))

    assert finding.secret_scan.status == "finding"
    assert len(finding.secret_scan.finding_ids) == 1


def test_live_stack_construction_is_side_effect_free_and_binds_runtime_policy(
    tmp_path: Path,
) -> None:
    calls: list[tuple[Path, tuple[str, ...]]] = []

    def port_factory(workspace: Path, overrides: tuple[str, ...]) -> DormantPort:
        calls.append((workspace.resolve(), overrides))
        return DormantPort()

    stack = build_profile_r_phase_f_live_stack(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        artifact_root=tmp_path / "backend",
        docker_raw_root=tmp_path / "docker-raw",
        docker_executable=Path(sys.executable),
        git_executable=GIT_EXECUTABLE,
        execution_environment_root=(tmp_path / "execution-environment").resolve(),
        source_commit="a" * 40,
        environ={},
        source_environment={
            "PATH": os.environ.get("PATH", ""),
            **(
                {"SYSTEMROOT": os.environ["SYSTEMROOT"]}
                if os.name == "nt"
                else {}
            ),
        },
        app_server_port_factory=port_factory,
    )
    assert calls == []
    workspace = tmp_path / "workspace"
    materialize_profile_r_workspace(REPOSITORY, workspace)

    runtime = stack.runtime_factory(workspace)

    assert len(calls) == 1
    assert calls[0] == (workspace.resolve(), build_phase_f_config_overrides(workspace))
    assert runtime.actual_model_turns == 0
    assert stack.telemetry.config_sha256 is not None


def test_live_stack_rejects_api_key_name_without_reading_value(tmp_path: Path) -> None:
    with pytest.raises(Exception, match="API key environment names"):
        build_profile_r_phase_f_live_stack(
            repository=REPOSITORY,
            candidate_root=CANDIDATE_ROOT,
            artifact_root=tmp_path / "backend",
            docker_raw_root=tmp_path / "docker-raw",
            docker_executable=Path(sys.executable),
            git_executable=GIT_EXECUTABLE,
            execution_environment_root=(tmp_path / "execution-environment").resolve(),
            source_commit="a" * 40,
            environ=NameOnlyApiKeyMapping(),
            source_environment={},
        )


def test_b1_live_stack_threads_one_explicit_external_check_temp_root(
    tmp_path: Path,
) -> None:
    environment_root = (tmp_path / "short-environment-root").resolve()

    stack = build_profile_r_phase_f_b1_live_stack(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        artifact_root=tmp_path / "backend",
        docker_raw_root=tmp_path / "docker-raw",
        docker_executable=Path(sys.executable),
        git_executable=GIT_EXECUTABLE,
        execution_environment_root=environment_root,
        source_commit="a" * 40,
        environ={},
        source_environment={
            "PATH": str(GIT_EXECUTABLE.parent),
            **(
                {"SYSTEMROOT": os.environ["SYSTEMROOT"]}
                if os.name == "nt"
                else {}
            ),
        },
        app_server_port_factory=lambda workspace, overrides: DormantPort(),
    )

    worker = stack.backend.worker_backend
    assert worker.check_temp_root == environment_root / "b1-check-temp"
    assert worker.git_executable == GIT_EXECUTABLE
    assert not environment_root.exists()


def test_zero_turn_preflight_never_starts_thread_or_turn(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    port = FakePreflightPort()

    evidence = run_profile_r_phase_f_zero_turn_preflight(
        workspace,
        environ={},
        app_server_port_factory=lambda _workspace, _overrides: port,
    )

    assert evidence.actual_model_turns == 0
    assert evidence.thread_started is False
    assert evidence.auth_method == "chatgpt"
    assert evidence.model == "gpt-5.6-sol"
    assert evidence.permission_profile == "runtime-boundary-worker"
    assert port.open_count == 1
    assert port.close_count == 1


@pytest.mark.skipif(
    os.environ.get("LAO_PHASE_F_SDK_PREFLIGHT") != "1",
    reason="explicit zero-turn SDK preflight opt-in required",
)
def test_real_sdk_zero_turn_preflight(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    materialize_profile_r_workspace(REPOSITORY, workspace)

    evidence = run_profile_r_phase_f_zero_turn_preflight(
        workspace,
        environ=os.environ,
    )

    assert evidence.actual_model_turns == 0
    assert evidence.thread_started is False
