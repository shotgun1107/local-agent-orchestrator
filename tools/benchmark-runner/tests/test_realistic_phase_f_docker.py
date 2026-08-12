from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence

import pytest

from benchmark_runner.realistic_docker_judge import (
    DockerRawExecution,
    SubprocessDockerExecutionBackend,
    build_docker_controller_environment,
)
from benchmark_runner.realistic_docker_judge_matrix import GitPatchBackend
from benchmark_runner.realistic_judge import (
    PreparedJudgeRoots,
    SourceRuntimeBinding,
    fingerprint_tree,
)
from benchmark_runner.realistic_phase_f import PhaseFDispatchRequest
from benchmark_runner.realistic_phase_f_docker import (
    PhaseFDockerJudgePort,
    _copy_worker_snapshot,
)
from benchmark_runner.realistic_phase_f_ss1 import materialize_profile_r_workspace
from benchmark_runner.realistic_routing import canonical_json_bytes, canonical_sha256
from benchmark_runner.runner import sha256_bytes


REPOSITORY = Path(__file__).resolve().parents[3]
CANDIDATE_PLAN = (
    REPOSITORY
    / "benchmarks"
    / "artifacts"
    / "sdk-routing-realistic-high-difficulty-phase-e-v1"
    / "execution-plan.json"
)
REFERENCE_PATCH_RELATIVE = (
    "benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/"
    "realistic-compat-migration-001/reference.patch"
)


def _request() -> PhaseFDispatchRequest:
    values = {
        "schema_version": 1,
        "kind": "realistic_phase_f_cell_dispatch",
        "experiment_id": "exp_phase_f_test",
        "plan_fingerprint": "a" * 64,
        "candidate_seal_sha256": "b" * 64,
        "execution_ordinal": 1,
        "cell_id": "cell_phase-e_1_realistic-compat-migration-001_ss1",
        "fixture_id": "realistic-compat-migration-001",
        "variant_id": "ss1",
        "runtime_mode": "model_free_fake",
        "automatic_continuation": False,
    }
    return PhaseFDispatchRequest(
        **values,
        request_sha256=canonical_sha256(values),
    )


class FakeRootsFactory:
    def prepare(
        self,
        *,
        repository: Path,
        base_root: Path,
        source_commit: str,
        request: PhaseFDispatchRequest,
        workspace: Path,
    ) -> PreparedJudgeRoots:
        del repository, request
        run_root = base_root / "phase-f-profile-r-test"
        W = run_root / "worker-observed"
        J_parent = run_root / ".judge-private"
        J = J_parent / "runtime"
        O = run_root / "output"
        S_parent = run_root / ".state-private"
        S = S_parent / "state"
        _copy_worker_snapshot(workspace, W)
        for root in (J, O, S):
            root.mkdir(parents=True, exist_ok=True)
        checker = J / "checker" / "check_properties.py"
        checker.parent.mkdir(parents=True)
        checker.write_text("print('fake backend owns stdout')\n", encoding="utf-8")
        worker = fingerprint_tree(W)
        judge = fingerprint_tree(J)
        binding = SourceRuntimeBinding.model_construct(
            source_commit=source_commit,
            source_tree_oid="c" * 40,
            source=judge,
            runtime=judge,
            source_runtime_relative_paths_equal=True,
            source_runtime_bytes_equal=True,
            runtime_root_identity_sha256="d" * 64,
            runtime_parent_identity_sha256="e" * 64,
            binding_sha256="f" * 64,
        )
        return PreparedJudgeRoots(
            run_root=run_root,
            W=W,
            J_parent=J_parent,
            J=J,
            O=O,
            S_parent=S_parent,
            S=S,
            source_commit=source_commit,
            worker_source_tree_oid="1" * 40,
            worker_source=worker,
            j_binding=binding,
        )


def _checker_payload(*, success: bool) -> bytes:
    return canonical_json_bytes(
        {
            "checker_run_status": "completed",
            "aggregate_status": "pass" if success else "fail",
            "workspace_mutated": False,
            "properties": [
                {
                    "property_id": f"R-P{number:02d}",
                    "status": (
                        "fail" if not success and number == 2 else "pass"
                    ),
                }
                for number in range(1, 9)
            ],
        }
    )


class FakeDockerBackend:
    def __init__(self, *, success: bool = True) -> None:
        self.success = success
        self.commands: list[list[str]] = []

    def execute(
        self,
        command: Sequence[str],
        **_: object,
    ) -> DockerRawExecution:
        self.commands.append(list(command))
        stdout = _checker_payload(success=self.success)
        stderr = b""
        return DockerRawExecution(
            started=True,
            exit_code=0 if self.success else 1,
            stdout=stdout,
            stdout_total=len(stdout),
            stdout_sha256=sha256_bytes(stdout),
            stderr=stderr,
            stderr_total=0,
            stderr_sha256=sha256_bytes(stderr),
            duration_ms=25,
        )


def _environment() -> dict[str, str]:
    values = {"PATH": os.environ.get("PATH", "")}
    if os.name == "nt":
        values["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    return values


def test_worker_snapshot_excludes_git_and_cache_metadata(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "README.md").write_text("worker\n", encoding="utf-8")
    (source / ".git").mkdir()
    (source / ".git" / "config").write_text("git\n", encoding="utf-8")
    (source / "pkg" / "__pycache__").mkdir(parents=True)
    (source / "pkg" / "__pycache__" / "x.pyc").write_bytes(b"cache")

    snapshot = _copy_worker_snapshot(source, tmp_path / "target")

    assert [item.path for item in snapshot.files] == ["README.md"]


def test_phase_f_docker_port_uses_existing_judge_without_real_docker(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "README.md").write_text("modified worker\n", encoding="utf-8")
    backend = FakeDockerBackend(success=True)
    output_root = tmp_path / "cell" / "final" / "judge"
    port = PhaseFDockerJudgePort(
        repository=REPOSITORY,
        raw_root=tmp_path / "raw",
        source_commit="a" * 40,
        docker_executable=Path(sys.executable),
        execution_backend=backend,
        source_environment=_environment(),
        roots_factory=FakeRootsFactory(),
    )

    observation = port.run(
        workspace=workspace,
        output_root=output_root,
        request=_request(),
    )

    assert observation.status == "CHECKS_PASSED"
    assert observation.check_success is True
    assert observation.judge_kind == "docker_property"
    assert observation.docker_executed is True
    assert observation.actual_model_turns == 0
    assert observation.raw_manifest_sha256 is not None
    assert observation.raw_result_sha256 is not None
    assert [item.path for item in observation.files] == ["manifest.json", "result.json"]
    assert len(backend.commands) == 1
    command = backend.commands[0]
    assert command[command.index("--network") + 1] == "none"
    assert "--read-only" in command
    assert command[-1] == "phase-f-r-1-ss1"
    public_bytes = b"".join(path.read_bytes() for path in output_root.iterdir())
    assert str(tmp_path).encode("utf-8") not in public_bytes
    assert not (output_root / "raw").exists()


def test_phase_f_docker_port_preserves_failed_property_ids(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "README.md").write_text("incorrect worker\n", encoding="utf-8")
    output_root = tmp_path / "cell" / "final" / "judge"
    port = PhaseFDockerJudgePort(
        repository=REPOSITORY,
        raw_root=tmp_path / "raw",
        source_commit="a" * 40,
        docker_executable=Path(sys.executable),
        execution_backend=FakeDockerBackend(success=False),
        source_environment=_environment(),
        roots_factory=FakeRootsFactory(),
    )

    observation = port.run(
        workspace=workspace,
        output_root=output_root,
        request=_request(),
    )

    assert observation.status == "CHECKS_FAILED"
    assert observation.check_success is False
    assert observation.failed_property_ids == ["R-P02"]
    result = json.loads((output_root / "result.json").read_text(encoding="utf-8"))
    assert result["failed_property_ids"] == ["R-P02"]


@pytest.mark.skipif(
    os.environ.get("LAO_PHASE_F_DOCKER_SMOKE") != "1",
    reason="explicit model-free Docker smoke opt-in required",
)
def test_phase_f_docker_port_real_reference_smoke(tmp_path: Path) -> None:
    docker = shutil.which("docker")
    if docker is None:
        pytest.fail("Docker executable is unavailable")
    plan = json.loads(CANDIDATE_PLAN.read_text(encoding="utf-8"))
    source_commit = plan["environment_fingerprint"]["source_commit"]
    workspace = tmp_path / "reference-worker"
    materialize_profile_r_workspace(REPOSITORY, workspace)
    patch = subprocess.run(
        [
            "git",
            "-C",
            str(REPOSITORY),
            "show",
            f"{source_commit}:{REFERENCE_PATCH_RELATIVE}",
        ],
        check=True,
        capture_output=True,
    ).stdout
    environment = build_docker_controller_environment(os.environ)
    GitPatchBackend().apply(workspace, patch, environment=environment)
    output_root = tmp_path / "cell" / "final" / "judge"
    port = PhaseFDockerJudgePort(
        repository=REPOSITORY,
        raw_root=tmp_path / "raw",
        source_commit=source_commit,
        docker_executable=Path(docker),
        execution_backend=SubprocessDockerExecutionBackend(),
        source_environment=os.environ,
    )

    observation = port.run(
        workspace=workspace,
        output_root=output_root,
        request=_request(),
    )

    assert observation.status == "CHECKS_PASSED"
    assert observation.failed_property_ids == []
    assert observation.actual_model_turns == 0
    result = json.loads((output_root / "result.json").read_text(encoding="utf-8"))
    assert result["status"] == "CHECKS_PASSED"
    assert result["model_turns"] == 0
