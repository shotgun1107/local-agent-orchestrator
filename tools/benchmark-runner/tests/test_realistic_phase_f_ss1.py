from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPOSITORY = Path(__file__).resolve().parents[3]
GIT_EXECUTABLE = Path(shutil.which("git") or "git").resolve()
B1_SOURCE = REPOSITORY / "stages" / "b1-sequential" / "src"
if str(B1_SOURCE) not in sys.path:
    sys.path.insert(0, str(B1_SOURCE))

from orchestrator.runtime import FakeRuntime as B1FakeRuntime

from benchmark_runner.realistic_phase_f import (
    PHASE_F_CELLS_DIRECTORY,
    PHASE_F_CLAIM_FILENAME,
    PhaseFCellLifecycle,
    PhaseFRuntimeMode,
    initialize_phase_f_execution,
    phase_f_status,
    run_next_phase_f_cell,
)
from benchmark_runner.realistic_phase_f_b1 import ProfileRPhaseFB1Backend
from benchmark_runner.realistic_phase_f_finalize import (
    PHASE_F_CELL_SEAL_FILENAME,
    PHASE_F_FINAL_DIRECTORY,
    PHASE_F_SEALED_DIRECTORY,
    FakePhaseFJudgePort,
    ProfileRPhaseFCellFinalizerBackend,
)
from benchmark_runner.realistic_phase_f_ss1 import (
    PHASE_F_SS1_EVIDENCE_FILENAME,
    PROFILE_R_EXPECTED_TASK_IDS,
    PROFILE_R_WORKER_MANIFEST_RELATIVE,
    PROFILE_R_WORKER_RELATIVE,
    ModelFreeClearBoundaryTelemetry,
    PhaseFSS1BackendError,
    ProfileRPhaseFSS1Backend,
    build_profile_r_ss1_tasks,
    materialize_profile_r_workspace,
    refresh_profile_r_ss1_task,
)
from benchmark_runner.sdk_common import FakeSdkRuntime, FakeTurnScript
from benchmark_runner.workspace import (
    build_hermetic_git_environment,
    path_matches_write_scope,
)


CANDIDATE_ROOT = (
    REPOSITORY
    / "benchmarks"
    / "artifacts"
    / "sdk-routing-realistic-high-difficulty-phase-e-v1"
)
REFERENCE_PATCH = (
    REPOSITORY
    / "benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/"
    "realistic-compat-migration-001/reference.patch"
)
R07_PUBLIC_FIX_COMMIT = "f0bd978"
R07_PUBLIC_FIX_PATH = "tools/benchmark-runner/tests/test_routing_s2.py"


def _completed_result(task_id: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status_claim": "completed",
        "summary": f"model-free completion for {task_id}",
        "artifacts": [],
        "changed_paths": [],
        "checks_run_by_worker": [],
        "assumptions": [],
        "warnings": [],
        "requested_followup": None,
        "needs_additional_review": False,
        "additional_review_reason": None,
    }


def _b1_completed_result(task_id: str, changed_paths: list[str]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status_claim": "completed",
        "summary": f"model-free B1 completion for {task_id}",
        "artifacts": [],
        "changed_paths": changed_paths,
        "checks_run_by_worker": [],
        "assumptions": [],
        "warnings": [],
        "requested_followup": None,
    }


def _reference_b1_runtime(
    *,
    workspace: Path,
    reference_workspace: Path,
    source_environment: dict[str, str],
) -> B1FakeRuntime:
    materialize_profile_r_workspace(
        REPOSITORY,
        reference_workspace,
        git_executable=GIT_EXECUTABLE,
        source_environment=source_environment,
    )
    git_environment = build_hermetic_git_environment(
        git_executable=GIT_EXECUTABLE,
        home=reference_workspace,
        source_environment=source_environment,
    )
    applied = subprocess.run(
        [
            str(GIT_EXECUTABLE),
            "-C",
            str(reference_workspace),
            "apply",
            "--no-index",
            "--whitespace=nowarn",
            "-",
        ],
        input=REFERENCE_PATCH.read_bytes(),
        capture_output=True,
        check=False,
        env=git_environment,
    )
    assert applied.returncode == 0, applied.stderr.decode("utf-8", errors="replace")
    repository_git_environment = build_hermetic_git_environment(
        git_executable=GIT_EXECUTABLE,
        home=REPOSITORY,
        source_environment=source_environment,
    )
    r07_fix = subprocess.run(
        [
            str(GIT_EXECUTABLE),
            "-C",
            str(REPOSITORY),
            "show",
            "--format=",
            R07_PUBLIC_FIX_COMMIT,
            "--",
            R07_PUBLIC_FIX_PATH,
        ],
        capture_output=True,
        check=False,
        env=repository_git_environment,
    )
    assert r07_fix.returncode == 0, r07_fix.stderr.decode(
        "utf-8", errors="replace"
    )
    applied_r07_fix = subprocess.run(
        [
            str(GIT_EXECUTABLE),
            "-C",
            str(reference_workspace),
            "apply",
            "--no-index",
            "--whitespace=nowarn",
            "-",
        ],
        input=r07_fix.stdout,
        capture_output=True,
        check=False,
        env=git_environment,
    )
    assert applied_r07_fix.returncode == 0, applied_r07_fix.stderr.decode(
        "utf-8", errors="replace"
    )
    reference_files = sorted(
        path
        for path in reference_workspace.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(reference_workspace).parts
    )
    turns: list[dict[str, object]] = []
    for task in build_profile_r_ss1_tasks(workspace):
        selected = [
            path
            for path in reference_files
            if any(
                path_matches_write_scope(
                    path.relative_to(reference_workspace).as_posix(),
                    scope,
                )
                for scope in task.write_scope
            )
        ]
        changed_paths = [
            path.relative_to(reference_workspace).as_posix() for path in selected
        ]
        turns.append(
            {
                "effects": [
                    {
                        "type": "write_file",
                        "path": relative,
                        "content": (reference_workspace / relative).read_text(
                            encoding="utf-8"
                        ),
                    }
                    for relative in changed_paths
                ],
                "result": _b1_completed_result(task.task_id, changed_paths),
            }
        )
    return B1FakeRuntime("complete", workspace=workspace, fixture={"turns": turns})


def _runtime_factory(
    captured: list[FakeSdkRuntime],
    *,
    omit_effects_for: frozenset[str] = frozenset(),
):
    effects = {
        "R02": (
            (
                "benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml",
                "schema_version: 1\nstage_id: s2-intermediate\n",
            ),
            (
                "benchmarks/manifests/sdk-routing-s2-intermediate.yaml",
                "schema_version: 1\nstatus: fake\n",
            ),
        ),
        "R05": (
            (
                "tools/benchmark-runner/src/benchmark_runner/s2_policy.py",
                '"""Model-free fake S2 policy."""\n',
            ),
        ),
        "R06": (
            (
                "tools/benchmark-runner/src/benchmark_runner/s2_posthoc.py",
                '"""Model-free fake S2 posthoc."""\n',
            ),
        ),
        "R07": (
            (
                "tools/benchmark-runner/tests/test_routing_s2.py",
                "def test_model_free_placeholder():\n    assert True\n",
            ),
        ),
    }

    def create(workspace: Path) -> FakeSdkRuntime:
        runtime = FakeSdkRuntime(
            workspace,
            {
                task_id: FakeTurnScript(
                    effects=(
                        () if task_id in omit_effects_for else effects.get(task_id, ())
                    ),
                    result=_completed_result(task_id),
                )
                for task_id in PROFILE_R_EXPECTED_TASK_IDS
            },
        )
        captured.append(runtime)
        return runtime

    return create


def _initialize(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    return initialize_phase_f_execution(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        state_root=tmp_path / "state",
    )


def test_materialized_profile_r_workspace_matches_manifest_and_has_clean_baseline(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    manifest = materialize_profile_r_workspace(REPOSITORY, workspace)
    expected = json.loads(
        (REPOSITORY / PROFILE_R_WORKER_MANIFEST_RELATIVE).read_text(encoding="utf-8")
    )

    assert manifest == expected
    assert len(manifest["files"]) == 130
    assert (
        subprocess.run(
            ["git", "-C", str(workspace), "config", "--bool", "core.autocrlf"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        ).stdout.strip()
        == "false"
    )
    assert (
        subprocess.run(
            ["git", "-C", str(workspace), "status", "--porcelain=v1"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        ).stdout
        == ""
    )


def test_profile_r_task_compilation_preserves_order_and_classifies_predecessors() -> None:
    workspace = REPOSITORY / PROFILE_R_WORKER_RELATIVE
    tasks = build_profile_r_ss1_tasks(workspace)
    by_id = {task.task_id: task for task in tasks}

    assert tuple(task.task_id for task in tasks) == PROFILE_R_EXPECTED_TASK_IDS
    assert [item.path for item in by_id["R01"].declared_inputs] == [
        "profile-r/requirements/change-surface.json",
        "profile-r/requirements/migration-contract.md",
    ]
    assert by_id["R01"].predecessor_artifacts == []
    assert [item.path for item in by_id["R02"].predecessor_artifacts] == [
        "profile-r/work/migration-ledger.json",
        "profile-r/work/source-inventory.json",
    ]
    assert by_id["R02"].declared_inputs == []
    assert by_id["R04"].predecessor_artifacts[0].sha256 != ""
    assert all(task.read_scope == sorted(task.read_scope) for task in tasks)
    assert all(task.write_scope == sorted(task.write_scope) for task in tasks)


def test_profile_r_task_hashes_are_refreshed_after_predecessor_output_exists(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    materialize_profile_r_workspace(REPOSITORY, workspace)
    task = build_profile_r_ss1_tasks(workspace)[3]
    target = workspace / "benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("schema_version: 1\n", encoding="utf-8", newline="\n")
    manifest = workspace / "benchmarks/manifests/sdk-routing-s2-intermediate.yaml"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("schema_version: 1\n", encoding="utf-8", newline="\n")

    refreshed = refresh_profile_r_ss1_task(workspace, task)

    assert refreshed.predecessor_artifacts[0].sha256 != task.predecessor_artifacts[0].sha256


def test_profile_r_ss1_fake_backend_runs_all_tasks_in_one_thread_and_stops_at_cell_one(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    experiment_dir = _initialize(tmp_path, monkeypatch)
    runtimes: list[FakeSdkRuntime] = []
    backend = ProfileRPhaseFSS1Backend(
        repository=REPOSITORY,
        artifact_root=tmp_path / "backend",
        runtime_mode=PhaseFRuntimeMode.MODEL_FREE_FAKE,
        runtime_factory=_runtime_factory(runtimes),
        telemetry=ModelFreeClearBoundaryTelemetry(),
        environ={},
    )

    result = run_next_phase_f_cell(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        experiment_dir=experiment_dir,
        backend=backend,
        expected_execution_ordinal=1,
        confirm_cell_dispatch=True,
        confirm_model_usage=False,
    )

    assert result.executed_ordinal == 1
    assert result.actual_model_turns == 0
    assert result.next_execution_ordinal == 2
    assert result.automatic_continuation is False
    assert len(runtimes) == 1
    runtime = runtimes[0]
    assert runtime.actual_model_turns == 0
    assert len(runtime.started_threads) == 1
    assert [turn["task_id"] for turn in runtime.turns] == list(
        PROFILE_R_EXPECTED_TASK_IDS
    )
    assert {turn["thread_id"] for turn in runtime.turns} == {
        runtime.started_threads[0]
    }
    assert all('"check_names"' not in str(turn["prompt"]) for turn in runtime.turns)

    cell_root = tmp_path / "backend" / result.executed_cell_id
    evidence = json.loads(
        (cell_root / PHASE_F_SS1_EVIDENCE_FILENAME).read_text(encoding="utf-8")
    )
    assert evidence["task_count"] == 8
    assert evidence["actual_model_turns"] == 0
    assert len(evidence["adapter_raw_payload"]["boundary_records"]) == 8
    assert evidence["adapter_normalized_metrics"]["session_count"] == 1
    assert evidence["adapter_normalized_metrics"]["turn_count"] == 8
    assert (
        evidence["task_template_sha256"][3]
        != evidence["dispatched_task_semantics_sha256"][3]
    )
    assert evidence["judge_executed"] is False
    assert evidence["automatic_continuation"] is False
    assert evidence["worker_tree_initial_sha256"] != evidence["worker_tree_final_sha256"]

    status = phase_f_status(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        experiment_dir=experiment_dir,
    )
    assert [item["lifecycle"] for item in status["cells"]] == [
        PhaseFCellLifecycle.SEALED.value,
        PhaseFCellLifecycle.PLANNED.value,
        PhaseFCellLifecycle.PLANNED.value,
        PhaseFCellLifecycle.PLANNED.value,
    ]
    second = status["cells"][1]
    assert not (
        experiment_dir
        / PHASE_F_CELLS_DIRECTORY
        / second["cell_id"]
        / PHASE_F_CLAIM_FILENAME
    ).exists()


@pytest.mark.parametrize("acceptance_run", (1, 2))
def test_model_free_phase_f_runs_ss1_then_b1_only_with_separate_explicit_dispatches(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    acceptance_run: int,
) -> None:
    hostile_temp = tmp_path / f"host-temp-must-not-be-used-{acceptance_run}"
    monkeypatch.setenv("TEMP", str(hostile_temp))
    monkeypatch.setenv("TMP", str(hostile_temp))
    monkeypatch.setenv("TMPDIR", str(hostile_temp))
    source_environment = {
        "PATH": str(GIT_EXECUTABLE.parent),
        **(
            {"SYSTEMROOT": os.environ["SYSTEMROOT"]}
            if os.name == "nt"
            else {}
        ),
        "HOME": str(tmp_path / "hostile-home"),
        "GIT_CONFIG_GLOBAL": str(tmp_path / "hostile-global-config"),
    }
    experiment_dir = _initialize(tmp_path, monkeypatch)
    artifact_root = tmp_path / "backend"
    ss1_runtimes: list[FakeSdkRuntime] = []
    ss1 = ProfileRPhaseFCellFinalizerBackend(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        worker_backend=ProfileRPhaseFSS1Backend(
            repository=REPOSITORY,
            artifact_root=artifact_root,
            runtime_mode=PhaseFRuntimeMode.MODEL_FREE_FAKE,
            runtime_factory=_runtime_factory(ss1_runtimes),
            telemetry=ModelFreeClearBoundaryTelemetry(),
            environ={},
            git_executable=GIT_EXECUTABLE,
            source_environment=source_environment,
        ),
        judge=FakePhaseFJudgePort(check_success=True),
    )

    first = run_next_phase_f_cell(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        experiment_dir=experiment_dir,
        backend=ss1,
        expected_execution_ordinal=1,
        confirm_cell_dispatch=True,
        confirm_model_usage=False,
    )

    after_ss1 = phase_f_status(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        experiment_dir=experiment_dir,
    )
    assert first.executed_ordinal == 1
    assert first.next_execution_ordinal == 2
    assert first.automatic_continuation is False
    assert len(ss1_runtimes) == 1
    assert len(ss1_runtimes[0].started_threads) == 1
    assert [turn["task_id"] for turn in ss1_runtimes[0].turns] == list(
        PROFILE_R_EXPECTED_TASK_IDS
    )
    assert [item["lifecycle"] for item in after_ss1["cells"]] == [
        PhaseFCellLifecycle.SEALED.value,
        PhaseFCellLifecycle.PLANNED.value,
        PhaseFCellLifecycle.PLANNED.value,
        PhaseFCellLifecycle.PLANNED.value,
    ]
    cell_two_id = str(after_ss1["cells"][1]["cell_id"])
    assert not (artifact_root / cell_two_id).exists()

    b1_runtimes: list[B1FakeRuntime] = []

    def b1_runtime_factory(workspace: Path) -> B1FakeRuntime:
        runtime = _reference_b1_runtime(
            workspace=workspace,
            reference_workspace=tmp_path / "reference-worker",
            source_environment=source_environment,
        )
        b1_runtimes.append(runtime)
        return runtime

    b1 = ProfileRPhaseFCellFinalizerBackend(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        worker_backend=ProfileRPhaseFB1Backend(
            repository=REPOSITORY,
            artifact_root=artifact_root,
            runtime_mode=PhaseFRuntimeMode.MODEL_FREE_FAKE,
            runtime_factory=b1_runtime_factory,
            telemetry=ModelFreeClearBoundaryTelemetry(),
            check_temp_root=tmp_path / "check-temp",
            environ={},
            git_executable=GIT_EXECUTABLE,
            source_environment=source_environment,
        ),
        judge=FakePhaseFJudgePort(check_success=True),
    )

    second = run_next_phase_f_cell(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        experiment_dir=experiment_dir,
        backend=b1,
        expected_execution_ordinal=2,
        confirm_cell_dispatch=True,
        confirm_model_usage=False,
    )

    after_b1 = phase_f_status(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        experiment_dir=experiment_dir,
    )
    assert second.executed_ordinal == 2
    assert second.next_execution_ordinal == 3
    assert second.automatic_continuation is False
    assert len(b1_runtimes) == 1
    assert b1_runtimes[0].turn_count >= 1
    b1_evidence = json.loads(
        (
            artifact_root
            / second.executed_cell_id
            / "b1-adapter-evidence.json"
        ).read_text(encoding="utf-8")
    )
    report_metrics = b1_evidence["adapter_raw_payload"]["report"]["metrics"]
    assert report_metrics["checks_passed"] == 16
    assert report_metrics["checks_failed"] == 0
    assert [item["lifecycle"] for item in after_b1["cells"]] == [
        PhaseFCellLifecycle.SEALED.value,
        PhaseFCellLifecycle.SEALED.value,
        PhaseFCellLifecycle.PLANNED.value,
        PhaseFCellLifecycle.PLANNED.value,
    ]
    for cell_id in (first.executed_cell_id, second.executed_cell_id):
        assert (
            artifact_root
            / cell_id
            / PHASE_F_FINAL_DIRECTORY
            / PHASE_F_SEALED_DIRECTORY
            / PHASE_F_CELL_SEAL_FILENAME
        ).is_file()
    cell_three = after_b1["cells"][2]
    assert not (
        experiment_dir
        / PHASE_F_CELLS_DIRECTORY
        / str(cell_three["cell_id"])
        / PHASE_F_CLAIM_FILENAME
    ).exists()
    assert not (artifact_root / str(cell_three["cell_id"])).exists()
    assert not hostile_temp.exists()
    assert (tmp_path / "check-temp").is_dir()
    assert list((tmp_path / "check-temp").iterdir()) == []


def test_ss1_task_resolution_failure_is_preserved_sealed_and_stops_before_b1(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    experiment_dir = _initialize(tmp_path, monkeypatch)
    artifact_root = tmp_path / "backend"
    runtimes: list[FakeSdkRuntime] = []
    backend = ProfileRPhaseFCellFinalizerBackend(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        worker_backend=ProfileRPhaseFSS1Backend(
            repository=REPOSITORY,
            artifact_root=artifact_root,
            runtime_mode=PhaseFRuntimeMode.MODEL_FREE_FAKE,
            runtime_factory=_runtime_factory(
                runtimes,
                omit_effects_for=frozenset({"R05"}),
            ),
            telemetry=ModelFreeClearBoundaryTelemetry(),
            environ={},
        ),
        judge=FakePhaseFJudgePort(check_success=True),
    )

    result = run_next_phase_f_cell(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        experiment_dir=experiment_dir,
        backend=backend,
        expected_execution_ordinal=1,
        confirm_cell_dispatch=True,
        confirm_model_usage=False,
    )

    cell_root = artifact_root / result.executed_cell_id
    evidence = json.loads(
        (cell_root / PHASE_F_SS1_EVIDENCE_FILENAME).read_text(encoding="utf-8")
    )
    status = phase_f_status(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        experiment_dir=experiment_dir,
    )

    assert evidence["adapter_outcome_state"] == "infrastructure_error"
    assert evidence["adapter_failure_kind"] == "ss1_task_resolution_failed"
    assert len(evidence["dispatched_task_semantics_sha256"]) == 5
    assert result.next_execution_ordinal == 2
    assert [item["lifecycle"] for item in status["cells"]] == [
        PhaseFCellLifecycle.SEALED.value,
        PhaseFCellLifecycle.PLANNED.value,
        PhaseFCellLifecycle.PLANNED.value,
        PhaseFCellLifecycle.PLANNED.value,
    ]
    assert (
        cell_root
        / PHASE_F_FINAL_DIRECTORY
        / PHASE_F_SEALED_DIRECTORY
        / PHASE_F_CELL_SEAL_FILENAME
    ).is_file()


def test_live_backend_refuses_model_free_clear_telemetry(tmp_path: Path) -> None:
    with pytest.raises(PhaseFSS1BackendError, match="fake clear telemetry"):
        ProfileRPhaseFSS1Backend(
            repository=REPOSITORY,
            artifact_root=tmp_path / "backend",
            runtime_mode=PhaseFRuntimeMode.LIVE_CHATGPT,
            runtime_factory=lambda workspace: FakeSdkRuntime(workspace, {}),
            telemetry=ModelFreeClearBoundaryTelemetry(),
            environ={},
        )
