from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


REPOSITORY = Path(__file__).resolve().parents[3]
GIT_EXECUTABLE = Path(shutil.which("git") or "git").resolve()
B1_SOURCE = REPOSITORY / "stages" / "b1-sequential" / "src"
if str(B1_SOURCE) not in sys.path:
    sys.path.insert(0, str(B1_SOURCE))

from orchestrator.recover import ControllerLock
from orchestrator.runtime import FakeRuntime as B1FakeRuntime

from benchmark_runner.realistic_phase_f import (
    PHASE_F_CELLS_DIRECTORY,
    PHASE_F_CLAIM_FILENAME,
    PHASE_F_STATE_FILENAME,
    PhaseFCellLifecycle,
    PhaseFRuntimeMode,
    initialize_phase_f_execution,
    phase_f_status,
    run_next_phase_f_cell,
)
from benchmark_runner.realistic_phase_f_b1 import ProfileRPhaseFB1Backend
from benchmark_runner.realistic_phase_e import ALL_CANDIDATE_FILES
from benchmark_runner.realistic_phase_f_finalize import (
    PHASE_F_CELL_SEAL_FILENAME,
    PHASE_F_FINAL_DIRECTORY,
    PHASE_F_MEASUREMENT_FILENAME,
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
    sha256_file,
)


CANDIDATE_ROOT = (
    REPOSITORY
    / "benchmarks"
    / "artifacts"
    / "sdk-routing-realistic-high-difficulty-phase-e-v16"
)
REFERENCE_PATCH = (
    REPOSITORY
    / "benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/"
    "realistic-compat-migration-001/reference.patch"
)
R07_PUBLIC_FIX_PATH = "tools/benchmark-runner/tests/test_routing_s2.py"
CHECK_ENVIRONMENT_EVIDENCE_PREFIX = "CHECK_ENVIRONMENT_EVIDENCE:"
ACCEPTANCE_EVIDENCE_ROOT_ENV = "LAO_PHASE_F_ACCEPTANCE_EVIDENCE_ROOT"
ACCEPTANCE_COMMAND_ENV = "LAO_PHASE_F_ACCEPTANCE_COMMAND"


def _paths_overlap(left: Path, right: Path) -> bool:
    a = left.resolve()
    b = right.resolve()
    return a == b or a in b.parents or b in a.parents


def _path_identity(path: Path) -> dict[str, object]:
    canonical = str(path.resolve())
    return {
        "canonical_path_sha256": hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest(),
        "canonical_path_length": len(canonical),
    }


def _processes_referencing(path: Path) -> list[str]:
    needle = str(path.resolve())
    if os.name == "nt":
        quoted = needle.replace("'", "''")
        script = (
            f"$needle='{quoted}';"
            "Get-CimInstance Win32_Process | "
            "Where-Object { $_.Name -match '^(python|git)' -and "
            "$_.CommandLine -like ('*' + $needle + '*') } | "
            "ForEach-Object { \"$($_.ProcessId):$($_.Name)\" }"
        )
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
        if completed.returncode != 0:
            pytest.skip("Windows process inventory is unavailable in this sandbox")
        return [line for line in completed.stdout.splitlines() if line.strip()]
    processes: list[str] = []
    proc = Path("/proc")
    if not proc.is_dir():
        return processes
    for command_line in proc.glob("[0-9]*/cmdline"):
        try:
            text = command_line.read_bytes().replace(b"\0", b" ").decode(
                "utf-8", errors="replace"
            )
        except OSError:
            continue
        if needle in text and command_line.parent.name != str(os.getpid()):
            processes.append(command_line.parent.name)
    return processes


def _write_acceptance_evidence(
    *,
    acceptance_run: int,
    experiment_dir: Path,
    artifact_root: Path,
    ss1_cell_id: str,
    b1_cell_id: str,
    attestation: dict[str, object],
) -> None:
    configured = os.environ.get(ACCEPTANCE_EVIDENCE_ROOT_ENV)
    if not configured:
        return
    command = os.environ.get(ACCEPTANCE_COMMAND_ENV)
    if not command:
        raise AssertionError(f"{ACCEPTANCE_COMMAND_ENV} is required for Evidence export")
    repository_status = subprocess.run(
        [
            str(GIT_EXECUTABLE),
            "-C",
            str(REPOSITORY),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=True,
    ).stdout.splitlines()
    candidate_relative = CANDIDATE_ROOT.relative_to(REPOSITORY).as_posix()
    expected_generated_candidate = {
        f"?? {candidate_relative}/{name}" for name in ALL_CANDIDATE_FILES
    }
    if not repository_status:
        generated_candidate_files: list[str] = []
    else:
        assert set(repository_status) == expected_generated_candidate
        generated_candidate_files = sorted(expected_generated_candidate)
    head = subprocess.run(
        [str(GIT_EXECUTABLE), "-C", str(REPOSITORY), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        encoding="ascii",
        errors="strict",
        check=True,
    ).stdout.strip()
    tree = subprocess.run(
        [str(GIT_EXECUTABLE), "-C", str(REPOSITORY), "rev-parse", "HEAD^{tree}"],
        capture_output=True,
        text=True,
        encoding="ascii",
        errors="strict",
        check=True,
    ).stdout.strip()
    run_root = Path(configured).resolve() / f"acceptance-{acceptance_run}"
    run_root.mkdir(parents=True, exist_ok=False)
    payload_root = run_root / "payload"
    payload_root.mkdir()
    sources = {
        "phase-f-state.json": experiment_dir / PHASE_F_STATE_FILENAME,
        "ss1-adapter-evidence.json": artifact_root / ss1_cell_id / PHASE_F_SS1_EVIDENCE_FILENAME,
        "ss1-measurement.json": artifact_root / ss1_cell_id / PHASE_F_FINAL_DIRECTORY / PHASE_F_SEALED_DIRECTORY / PHASE_F_MEASUREMENT_FILENAME,
        "ss1-cell-seal.json": artifact_root / ss1_cell_id / PHASE_F_FINAL_DIRECTORY / PHASE_F_SEALED_DIRECTORY / PHASE_F_CELL_SEAL_FILENAME,
        "b1-adapter-evidence.json": artifact_root / b1_cell_id / "b1-adapter-evidence.json",
        "b1-measurement.json": artifact_root / b1_cell_id / PHASE_F_FINAL_DIRECTORY / PHASE_F_SEALED_DIRECTORY / PHASE_F_MEASUREMENT_FILENAME,
        "b1-cell-seal.json": artifact_root / b1_cell_id / PHASE_F_FINAL_DIRECTORY / PHASE_F_SEALED_DIRECTORY / PHASE_F_CELL_SEAL_FILENAME,
    }
    files: list[dict[str, object]] = []
    for name, source in sources.items():
        target = payload_root / name
        target.write_bytes(source.read_bytes())
        files.append(
            {
                "path": f"payload/{name}",
                "size_bytes": target.stat().st_size,
                "sha256": sha256_file(target),
            }
        )
    record = {
        "schema_version": 1,
        "acceptance_run": acceptance_run,
        "exact_test_command": command,
        "checkout_head": head,
        "checkout_tree": tree,
        "checkout_source_changes": 0,
        "generated_candidate_files": generated_candidate_files,
        "candidate_root_identity": _path_identity(CANDIDATE_ROOT),
        "candidate_seal_sha256": sha256_file(CANDIDATE_ROOT / "candidate-seal.json"),
        "attestation": attestation,
        "files": files,
    }
    encoded = (json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    (run_root / "acceptance-attestation.json").write_bytes(encoded)
    manifest_lines = [f"{item['sha256']}  {item['path']}" for item in files]
    manifest_lines.append(
        f"{hashlib.sha256(encoded).hexdigest()}  acceptance-attestation.json"
    )
    (run_root / "files.sha256").write_text(
        "\n".join(manifest_lines) + "\n",
        encoding="ascii",
        newline="\n",
    )


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
    alternate_deep_r07_repository: bool = False,
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
    if alternate_deep_r07_repository:
        r07_test = reference_workspace / R07_PUBLIC_FIX_PATH
        original = 'source = tmp_path / "source"'
        replacement = (
            'source = tmp_path / '
            '"alternate-valid-worker-internal-repository-root"'
        )
        content = r07_test.read_text(encoding="utf-8")
        assert content.count(original) == 1
        r07_test.write_text(
            content.replace(original, replacement),
            encoding="utf-8",
            newline="\n",
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
        ),
        "R03": (
            (
                "benchmarks/fixtures/routing-v1/intermediate/three-stage-config-migration/benchmark-run.yaml",
                "schema_version: 1\ntasks: []\n",
            ),
        ),
        "R04": (
            (
                "benchmarks/fixtures/routing-v1/intermediate/three-stage-incident-analysis/benchmark-run.yaml",
                "schema_version: 1\ntasks: []\n",
            ),
        ),
        "R05": (
            (
                "benchmarks/manifests/sdk-routing-s2-intermediate.yaml",
                "schema_version: 1\nstatus: fake\n",
            ),
        ),
        "R07": (
            (
                "tools/benchmark-runner/src/benchmark_runner/s2_policy.py",
                '"""Model-free fake S2 policy."""\n',
            ),
        ),
        "R09": (
            (
                "tools/benchmark-runner/src/benchmark_runner/s2_posthoc.py",
                '"""Model-free fake S2 posthoc."""\n',
            ),
        ),
        "R11": (
            (
                "tools/benchmark-runner/tests/test_routing_s2.py",
                "def test_model_free_placeholder():\n    assert True\n",
            ),
        ),
        "R12": (
            (
                "tools/benchmark-runner/tests/test_routing_suite.py",
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


def test_model_free_fake_effects_stay_within_each_task_write_scope() -> None:
    workspace = REPOSITORY / PROFILE_R_WORKER_RELATIVE
    tasks = build_profile_r_ss1_tasks(workspace)
    runtime = _runtime_factory([])(workspace)

    for task in tasks:
        script = runtime.scripts[task.task_id]
        assert isinstance(script, FakeTurnScript)
        assert all(
            any(path_matches_write_scope(path, scope) for scope in task.write_scope)
            for path, _content in script.effects
        ), task.task_id


def test_profile_r_task_hashes_are_refreshed_after_predecessor_output_exists(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    materialize_profile_r_workspace(REPOSITORY, workspace)
    task = build_profile_r_ss1_tasks(workspace)[4]
    target = workspace / "benchmarks/fixtures/routing-v1/intermediate/three-stage-config-migration/benchmark-run.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("schema_version: 1\n", encoding="utf-8", newline="\n")
    manifest = workspace / "benchmarks/fixtures/routing-v1/intermediate/three-stage-incident-analysis/benchmark-run.yaml"
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
    assert evidence["task_count"] == 13
    assert evidence["actual_model_turns"] == 0
    assert len(evidence["adapter_raw_payload"]["boundary_records"]) == 13
    assert evidence["adapter_normalized_metrics"]["session_count"] == 1
    assert evidence["adapter_normalized_metrics"]["turn_count"] == 13
    assert (
        evidence["task_template_sha256"][4]
        != evidence["dispatched_task_semantics_sha256"][4]
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
    hostile_home = tmp_path / "hostile-home"
    hostile_hooks = hostile_home / "hooks"
    hostile_hooks.mkdir(parents=True)
    hostile_config = tmp_path / "hostile-global-config"
    hostile_config.write_text(
        "[core]\n"
        "\tautocrlf = true\n"
        "\tlongpaths = false\n"
        f"\thooksPath = {hostile_hooks.as_posix()}\n",
        encoding="utf-8",
    )
    source_environment = {
        "PATH": str(GIT_EXECUTABLE.parent),
        **(
            {"SYSTEMROOT": os.environ["SYSTEMROOT"]}
            if os.name == "nt"
            else {}
        ),
        "HOME": str(hostile_home),
        "GIT_CONFIG_GLOBAL": str(hostile_config),
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
    assert first.actual_model_turns == 0
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
            alternate_deep_r07_repository=acceptance_run == 2,
        )
        b1_runtimes.append(runtime)
        return runtime

    check_temp_token = hashlib.sha256(str(tmp_path).encode("utf-8")).hexdigest()[:12]
    check_temp_root = Path(tempfile.gettempdir()) / f"pfa{check_temp_token[:4]}"
    if check_temp_root.exists():
        shutil.rmtree(check_temp_root)
    b1 = ProfileRPhaseFCellFinalizerBackend(
        repository=REPOSITORY,
        candidate_root=CANDIDATE_ROOT,
        worker_backend=ProfileRPhaseFB1Backend(
            repository=REPOSITORY,
            artifact_root=artifact_root,
            runtime_mode=PhaseFRuntimeMode.MODEL_FREE_FAKE,
            runtime_factory=b1_runtime_factory,
            telemetry=ModelFreeClearBoundaryTelemetry(),
            check_temp_root=check_temp_root,
            protected_execution_roots=(CANDIDATE_ROOT, experiment_dir),
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
    assert second.actual_model_turns == 0
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
    assert report_metrics["checks_passed"] == 104
    assert report_metrics["checks_failed"] == 0
    check_records = b1_evidence["adapter_raw_payload"]["check_records"]
    public_records = {
        item["task_external_key"]: item
        for item in check_records
        if item["check_name"].endswith("_contract")
    }
    assert set(public_records) == set(PROFILE_R_EXPECTED_TASK_IDS)
    assert all(
        item["state"] == "PASSED" and item["exit_code"] == 0
        for item in public_records.values()
    )
    for task_id, expected_tests in (("R11", 7), ("R12", 5)):
        stdout = public_records[task_id]["stdout"]["text"]
        evidence_line = next(
            line
            for line in stdout.splitlines()
            if line.startswith(CHECK_ENVIRONMENT_EVIDENCE_PREFIX)
        )
        environment_evidence = json.loads(
            evidence_line.removeprefix(CHECK_ENVIRONMENT_EVIDENCE_PREFIX)
        )
        assert environment_evidence["pytest"] == {
            "tests": expected_tests,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "warnings": 0,
        }
        assert environment_evidence["growth_margin"] >= 32
    for provenance in (
        json.loads(
            (
                artifact_root
                / first.executed_cell_id
                / PHASE_F_SS1_EVIDENCE_FILENAME
            ).read_text(encoding="utf-8")
        )["git_provenance"],
        b1_evidence["git_provenance"],
    ):
        assert len(provenance["git_executable_sha256"]) == 64
        assert provenance["git_version"].startswith("git version ")
        assert len(provenance["config_scope_origin_sha256"]) == 64
    assert [item["lifecycle"] for item in after_b1["cells"]] == [
        PhaseFCellLifecycle.SEALED.value,
        PhaseFCellLifecycle.SEALED.value,
        PhaseFCellLifecycle.PLANNED.value,
        PhaseFCellLifecycle.PLANNED.value,
    ]
    for cell_id in (first.executed_cell_id, second.executed_cell_id):
        sealed_root = (
            artifact_root
            / cell_id
            / PHASE_F_FINAL_DIRECTORY
            / PHASE_F_SEALED_DIRECTORY
        )
        assert (
            sealed_root / PHASE_F_CELL_SEAL_FILENAME
        ).is_file()
        measurement = json.loads(
            (sealed_root / PHASE_F_MEASUREMENT_FILENAME).read_text(encoding="utf-8")
        )
        assert measurement["integrity"]["scope_ok"] is True
        assert measurement["integrity"]["evidence_hashes_ok"] is True
        assert measurement["integrity"]["secret_findings"] == []
    cell_three = after_b1["cells"][2]
    assert not (
        experiment_dir
        / PHASE_F_CELLS_DIRECTORY
        / str(cell_three["cell_id"])
        / PHASE_F_CLAIM_FILENAME
    ).exists()
    assert not (artifact_root / str(cell_three["cell_id"])).exists()
    assert not hostile_temp.exists()
    assert check_temp_root.is_dir()
    assert list(check_temp_root.iterdir()) == []
    protected_roots = (
        REPOSITORY,
        CANDIDATE_ROOT,
        experiment_dir,
        artifact_root,
    )
    assert all(not _paths_overlap(check_temp_root, root) for root in protected_roots)
    if os.name == "nt":
        assert len(str(check_temp_root.resolve())) + 210 < 260
    b1_state_root = artifact_root / second.executed_cell_id / "b1-state"
    with ControllerLock(b1_state_root):
        pass
    unexpected_lock_files = [
        path
        for path in artifact_root.rglob("*.lock")
        if path.name != "controller.lock"
    ]
    assert unexpected_lock_files == []
    assert _processes_referencing(experiment_dir) == []
    assert _processes_referencing(artifact_root) == []
    assert _processes_referencing(check_temp_root) == []
    attestation = {
        "actual_model_turns": 0,
        "automatic_continuation": False,
        "cell_lifecycles": [item["lifecycle"] for item in after_b1["cells"]],
        "public_check_ids": sorted(public_records),
        "public_checks_passed": 8,
        "path_identities": {
            "phase_f_state": _path_identity(experiment_dir),
            "artifact_root": _path_identity(artifact_root),
            "ss1_workspace": _path_identity(
                artifact_root / first.executed_cell_id / "workspace"
            ),
            "b1_workspace": _path_identity(
                artifact_root / second.executed_cell_id / "workspace"
            ),
            "check_temp_root": _path_identity(check_temp_root),
            "protected_roots": [_path_identity(root) for root in protected_roots],
        },
        "paths_non_overlapping": True,
        "external_check_temp_residue": 0,
        "child_process_residue": 0,
        "active_controller_lock_residue": 0,
        "controller_lock_reacquired": True,
        "unexpected_lock_file_residue": 0,
        "r07_environment": environment_evidence,
    }
    _write_acceptance_evidence(
        acceptance_run=acceptance_run,
        experiment_dir=experiment_dir,
        artifact_root=artifact_root,
        ss1_cell_id=first.executed_cell_id,
        b1_cell_id=second.executed_cell_id,
        attestation=attestation,
    )
    shutil.rmtree(check_temp_root)
    assert not check_temp_root.exists()


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
