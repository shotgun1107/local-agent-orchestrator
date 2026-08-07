from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest
import yaml

from benchmark_runner.adapter import B1AdapterConfig, B1SequentialAdapter
from benchmark_runner.contract import (
    ArtifactIdentity,
    CellStateRecord,
    FixtureIdentity,
    Measurement,
    PlannedCell,
)
from benchmark_runner.failure_scenarios import (
    CONFIG_SOURCE,
    FAILURE_SCENARIOS,
    NORMALIZATION_SOURCE,
    FailureScenario,
)
from benchmark_runner.plan import build_sdk_controlled_plan
from benchmark_runner.runner import IntegrityError, verify_sealed_cell
from benchmark_runner.sdk_baselines import SdkBaselineAdapter, SdkBaselineConfig
from benchmark_runner.sdk_cells import (
    initialize_sdk_experiment,
    run_sdk_nonlive_cell,
    runner_source_sha256,
)
from benchmark_runner.sdk_common import (
    FakeSdkRuntime,
    FakeTurnScript,
    SdkLiveControlSettings,
    WorkerContract,
    validate_sdk_live_controls,
)
from benchmark_runner.workspace import FixtureRestorer, FrozenFixtureSpec, load_frozen_manifest


REPOSITORY_ROOT = Path(__file__).parents[3]
MANIFEST_PATH = (
    REPOSITORY_ROOT
    / "benchmarks"
    / "manifests"
    / "b0-b1-sequential-followup.yaml"
)
B1_ROOT = REPOSITORY_ROOT / "stages" / "b1-sequential"
B1_SOURCE_ROOT = B1_ROOT / "src"
B1_SCHEMA_ROOT = B1_ROOT / "schemas" / "v1"
def _git() -> Path:
    executable = shutil.which("git")
    assert executable is not None
    return Path(executable)


def _fixture() -> FrozenFixtureSpec:
    manifest = load_frozen_manifest(MANIFEST_PATH)
    return next(item for item in manifest.fixtures if item.id == "sequential-code-change")


def _contract(monkeypatch: pytest.MonkeyPatch) -> WorkerContract:
    monkeypatch.syspath_prepend(str(B1_SOURCE_ROOT))
    from orchestrator.worker import (
        render_worker_prompt,
        result_schema,
        task_semantics_sha256,
        validate_result,
    )

    return WorkerContract(
        render_prompt=render_worker_prompt,
        result_schema=result_schema,
        validate_result=lambda value: validate_result(value).model_dump(mode="json"),
        semantics_sha256=task_semantics_sha256,
    )


def _tasks(
    monkeypatch: pytest.MonkeyPatch,
    variant: str,
    workspace: Path,
) -> tuple[object, ...]:
    monkeypatch.syspath_prepend(str(B1_SOURCE_ROOT))
    from orchestrator.contract import RunSpec
    from orchestrator.worker import build_oneshot_envelope, build_task_envelope

    spec = RunSpec.model_validate(
        yaml.safe_load((workspace / "benchmark-run.yaml").read_text(encoding="utf-8"))
    )
    if variant == "c0":
        return (
            build_oneshot_envelope(
                spec,
                run_id="run-c0",
                task_id="task-c0",
                attempt_id="attempt-c0",
                requirements_version=1,
                timeout_seconds=900,
                remaining_attempts=1,
            ),
        )
    return tuple(
        build_task_envelope(
            task,
            run_id=f"run-{variant}",
            task_id=f"task-{variant}-{task.key.lower()}",
            attempt_id=f"attempt-{variant}-{task.key.lower()}",
            requirements_version=1,
            timeout_seconds=900,
            remaining_attempts=1,
        )
        for task in spec.tasks
    )


def _completed_result(*paths: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status_claim": "completed",
        "summary": "sealed non-live Cell completed",
        "artifacts": [
            {"path": path, "kind": "file", "description": "scripted result"}
            for path in paths
        ],
        "changed_paths": list(paths),
        "checks_run_by_worker": [],
        "assumptions": [],
        "warnings": [],
        "requested_followup": None,
    }


def _normal_scripts(tasks: tuple[object, ...], variant: str) -> dict[str, FakeTurnScript]:
    if variant == "c0":
        return {
            str(tasks[0].task_id): FakeTurnScript(
                effects=(
                    ("src/normalization.py", NORMALIZATION_SOURCE),
                    ("src/config.py", CONFIG_SOURCE),
                ),
                result=_completed_result("src/normalization.py", "src/config.py"),
            )
        }
    return {
        str(tasks[0].task_id): FakeTurnScript(
            effects=(("src/normalization.py", NORMALIZATION_SOURCE),),
            result=_completed_result("src/normalization.py"),
        ),
        str(tasks[1].task_id): FakeTurnScript(
            effects=(("src/config.py", CONFIG_SOURCE),),
            result=_completed_result("src/config.py"),
        ),
    }


def _plan(
    cells: list[PlannedCell],
    fixture: FrozenFixtureSpec,
    *,
    runner_sha256: str | None = None,
):
    manifest_sha256 = hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()
    return build_sdk_controlled_plan(
        source_manifest_path=MANIFEST_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
        source_manifest_sha256=manifest_sha256,
        fixtures=[
            FixtureIdentity(
                fixture_id=fixture.id,
                source_commit=fixture.commit,
                git_tree=fixture.git_tree,
            )
        ],
        runner=ArtifactIdentity(
            artifact_id="benchmark-runner",
            version="sdk-controlled-source-v1",
            sha256=runner_sha256 or runner_source_sha256(),
        ),
        variants=[
            ArtifactIdentity(
                artifact_id=variant,
                version=f"{variant}-nonlive-v1",
                sha256=str(index) * 64,
            )
            for index, variant in enumerate(("c0", "c1", "c2", "b1"), start=2)
        ],
        cells=cells,
        baseline_variant="c2",
        candidate_variants=["b1"],
        decision_policy={"nonlive_contract_gate": True},
        environment_fingerprint={
            "sdk": "openai-codex==0.144.4",
            "runtime": "fake",
            "actual_model_turns": "0",
        },
    )


def _restore(experiment_dir: Path, cell: PlannedCell):
    return FixtureRestorer(REPOSITORY_ROOT, str(_git())).restore(
        _fixture(),
        experiment_dir / "cells" / cell.cell_id / "workspace",
    )


def _sdk_adapter(
    monkeypatch: pytest.MonkeyPatch,
    prepared,
    variant: str,
    scripts: dict[str, FakeTurnScript] | None = None,
):
    tasks = _tasks(monkeypatch, variant, prepared.workspace)
    return SdkBaselineAdapter(
        SdkBaselineConfig(
            variant_id=variant,
            tasks=tasks,
            contract=_contract(monkeypatch),
            runtime=FakeSdkRuntime(
                prepared.workspace,
                scripts or _normal_scripts(tasks, variant),
            ),
        )
    )


def _b1_adapter(
    tmp_path: Path,
    prepared,
    cell: PlannedCell,
    fixture_payload: dict[str, object],
):
    script_dir = tmp_path / "scripted-runtime"
    script_dir.mkdir(parents=True, exist_ok=True)
    fake_fixture_path = script_dir / f"{cell.cell_id}.json"
    fake_fixture_path.write_text(
        json.dumps(fixture_payload, ensure_ascii=False),
        encoding="utf-8",
    )
    return B1SequentialAdapter(
        B1AdapterConfig(
            command_prefix=(sys.executable, "-m", "orchestrator"),
            project=prepared.workspace,
            run_spec=prepared.workspace / "benchmark-run.yaml",
            state_root=tmp_path / "variant-state" / cell.cell_id,
            schema_root=B1_SCHEMA_ROOT,
            runtime="fake",
            fake_fixture=fake_fixture_path,
        )
    )


def _normal_b1_fixture() -> dict[str, object]:
    return {
        "scenario": "complete",
        "turns": [
            {
                "effects": [
                    {
                        "type": "write_file",
                        "path": "src/normalization.py",
                        "content": NORMALIZATION_SOURCE,
                    }
                ],
                "result": _completed_result("src/normalization.py"),
            },
            {
                "effects": [
                    {
                        "type": "write_file",
                        "path": "src/config.py",
                        "content": CONFIG_SOURCE,
                    }
                ],
                "result": _completed_result("src/config.py"),
            },
        ],
    }


def _live_controls(cwd: Path, **updates: object) -> SdkLiveControlSettings:
    values = {
        "sdk_version": "0.144.4",
        "account_type": "chatgpt",
        "model": "gpt-5.6-terra",
        "reasoning_effort": "low",
        "thread_sandbox": "workspace_write",
        "turn_sandbox": "workspace_write",
        "thread_approval_mode": "deny_all",
        "turn_approval_mode": "deny_all",
        "cwd": cwd,
        "ephemeral": False,
        "output_schema_title": "ResultEnvelope",
        "validated_without_model_turn": True,
        "actual_model_turns": 0,
    }
    values.update(updates)
    return SdkLiveControlSettings(**values)


def test_live_control_preflight_is_no_turn_and_fail_closed(tmp_path: Path) -> None:
    evidence = validate_sdk_live_controls(_live_controls(tmp_path), environ={})
    assert evidence["account_type"] == "chatgpt"
    assert evidence["actual_model_turns"] == 0
    assert evidence["thread_sandbox"] == evidence["turn_sandbox"] == "workspace_write"
    assert evidence["thread_approval_mode"] == evidence["turn_approval_mode"] == "deny_all"
    assert evidence["ephemeral"] is False

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        validate_sdk_live_controls(
            _live_controls(tmp_path),
            environ={"OPENAI_API_KEY": "value-is-never-read-or-reported"},
        )
    with pytest.raises(RuntimeError, match="reasoning_effort"):
        validate_sdk_live_controls(
            _live_controls(tmp_path, reasoning_effort="medium"),
            environ={},
        )


def test_four_normal_variants_reach_sealed_measurements(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture()
    cells = [
        PlannedCell(
            cell_id=f"cell_normal_{variant}",
            block_id="block_normal",
            fixture_id=fixture.id,
            repetition=1,
            variant_id=variant,
            execution_ordinal=index,
        )
        for index, variant in enumerate(("c0", "c1", "c2", "b1"), start=1)
    ]
    plan = _plan(cells, fixture)
    experiment_dir = initialize_sdk_experiment(tmp_path / "normal", plan)
    measurements: dict[str, Measurement] = {}

    for cell in cells:
        prepared = _restore(experiment_dir, cell)
        adapter = (
            _b1_adapter(tmp_path, prepared, cell, _normal_b1_fixture())
            if cell.variant_id == "b1"
            else _sdk_adapter(monkeypatch, prepared, cell.variant_id)
        )
        result = run_sdk_nonlive_cell(
            experiment_dir=experiment_dir,
            plan=plan,
            planned_cell=cell,
            prepared=prepared,
            adapter=adapter,
            benchmark_python=Path(sys.executable),
            git_executable=_git(),
        )
        assert result.cell_state == "SEALED"
        assert result.check_success is True
        cell_dir = experiment_dir / "cells" / cell.cell_id
        state = CellStateRecord.model_validate_json(
            (cell_dir / "cell-state.json").read_bytes()
        )
        assert [entry.state.value for entry in state.history] == [
            "PLANNED",
            "PREPARED",
            "ACTIVE",
            "CAPTURED",
            "JUDGING",
            "SEALED",
        ]
        assert state.sealed_measurement_sha256 == result.sealed_measurement_sha256
        measurements[cell.variant_id] = verify_sealed_cell(cell_dir)

    assert measurements["c0"].resource.session_count.value == 1
    assert measurements["c0"].resource.turn_count.value == 1
    assert measurements["c1"].resource.session_count.value == 1
    assert measurements["c1"].resource.turn_count.value == 2
    assert measurements["c2"].resource.session_count.value == 2
    assert measurements["c2"].resource.turn_count.value == 2
    assert measurements["b1"].resource.session_count.value == 2
    assert measurements["b1"].resource.turn_count.value == 2
    assert all(
        measurement.variant_metrics.values["actual_model_turns"] == 0
        for measurement in measurements.values()
    )
    for variant in ("c0", "c1", "c2"):
        turns = measurements[variant].variant_metrics.values["turns"]
        assert all(turn["result_envelope"]["status_claim"] == "completed" for turn in turns)
        assert all("usage_cumulative" in turn for turn in turns)
        assert turns[-1]["downstream_dispatched"] is False
    assert measurements["c1"].variant_metrics.values["turns"][0][
        "downstream_dispatched"
    ] is True
    assert measurements["c2"].variant_metrics.values["turns"][0][
        "downstream_dispatched"
    ] is True
    c2_turns = measurements["c2"].variant_metrics.values["turns"]
    b1_turns = measurements["b1"].variant_metrics.values["turns"]
    assert [turn["task_semantics_sha256"] for turn in b1_turns] == [
        turn["task_semantics_sha256"] for turn in c2_turns
    ]
    assert [turn["output_schema_sha256"] for turn in b1_turns] == [
        turn["output_schema_sha256"] for turn in c2_turns
    ]
    assert all(len(turn["prompt_sha256"]) == 64 for turn in b1_turns)

    tampered = experiment_dir / "cells" / cells[0].cell_id / "judge" / "result.json"
    tampered.write_bytes(tampered.read_bytes() + b"\n")
    with pytest.raises(IntegrityError, match="Evidence hash mismatch"):
        verify_sealed_cell(experiment_dir / "cells" / cells[0].cell_id)


def test_nine_failure_cells_share_one_plan_and_all_seal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture()
    variants = ("c1", "c2", "b1")
    cells: list[PlannedCell] = []
    scenarios_by_cell: dict[str, FailureScenario] = {}
    for repetition, scenario in enumerate(FAILURE_SCENARIOS, start=1):
        for variant in variants:
            cell = PlannedCell(
                cell_id=f"cell_{scenario.scenario_id}_{variant}",
                block_id=f"block_{scenario.scenario_id}",
                fixture_id=fixture.id,
                repetition=repetition,
                variant_id=variant,
                execution_ordinal=len(cells) + 1,
            )
            cells.append(cell)
            scenarios_by_cell[cell.cell_id] = scenario
    plan = _plan(cells, fixture)
    experiment_dir = initialize_sdk_experiment(tmp_path / "failure-gate", plan)

    for cell in cells:
        scenario = scenarios_by_cell[cell.cell_id]
        prepared = _restore(experiment_dir, cell)
        if cell.variant_id == "b1":
            adapter = _b1_adapter(tmp_path, prepared, cell, scenario.b1_fixture())
        else:
            tasks = _tasks(monkeypatch, cell.variant_id, prepared.workspace)
            task_ids = tuple(str(task.task_id) for task in tasks)
            adapter = _sdk_adapter(
                monkeypatch,
                prepared,
                cell.variant_id,
                scenario.sdk_scripts((task_ids[0], task_ids[1])),
            )
        result = run_sdk_nonlive_cell(
            experiment_dir=experiment_dir,
            plan=plan,
            planned_cell=cell,
            prepared=prepared,
            adapter=adapter,
            benchmark_python=Path(sys.executable),
            git_executable=_git(),
            scenario_id=scenario.scenario_id,
        )
        measurement = verify_sealed_cell(
            experiment_dir / "cells" / cell.cell_id
        )
        assert result.cell_state == "SEALED"
        assert measurement.variant_metrics.values["scenario_id"] == scenario.scenario_id
        if cell.variant_id == "b1":
            assert result.outcome_state == "blocked"
            assert measurement.resource.turn_count.value == 1
            assert result.check_success is scenario.b1_judge_success
        else:
            assert result.outcome_state == "completed"
            assert measurement.resource.turn_count.value == 2
            assert result.check_success is scenario.baseline_judge_success
            turns = measurement.variant_metrics.values["turns"]
            assert [turn["downstream_dispatched"] for turn in turns] == [True, False]


def test_nonlive_rejects_unverified_runtime_before_dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture()
    cell = PlannedCell(
        cell_id="cell_runtime_attack_c2",
        block_id="block_runtime_attack",
        fixture_id=fixture.id,
        repetition=1,
        variant_id="c2",
        execution_ordinal=1,
    )
    plan = _plan([cell], fixture)
    experiment_dir = initialize_sdk_experiment(tmp_path / "runtime-attack", plan)
    prepared = _restore(experiment_dir, cell)
    tasks = _tasks(monkeypatch, "c2", prepared.workspace)

    class CountingRuntime:
        turns = 0

        def preflight(self) -> None:
            return None

        def start_thread(self):
            raise AssertionError("dispatch must not be reached")

        def run_turn(self, *args, **kwargs):
            self.turns += 1
            raise AssertionError("dispatch must not be reached")

    runtime = CountingRuntime()
    adapter = SdkBaselineAdapter(
        SdkBaselineConfig(
            variant_id="c2",
            tasks=tasks,
            contract=_contract(monkeypatch),
            runtime=runtime,
        )
    )
    with pytest.raises(RuntimeError, match="exact FakeSdkRuntime"):
        run_sdk_nonlive_cell(
            experiment_dir=experiment_dir,
            plan=plan,
            planned_cell=cell,
            prepared=prepared,
            adapter=adapter,
            benchmark_python=Path(sys.executable),
            git_executable=_git(),
        )
    assert runtime.turns == 0


def test_execution_plan_order_is_enforced_before_adapter_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture()
    cells = [
        PlannedCell(
            cell_id=f"cell_order_{index}_c0",
            block_id="block_order",
            fixture_id=fixture.id,
            repetition=index,
            variant_id="c0",
            execution_ordinal=index,
        )
        for index in (1, 2)
    ]
    plan = _plan(cells, fixture)
    experiment_dir = initialize_sdk_experiment(tmp_path / "order-attack", plan)
    prepared = _restore(experiment_dir, cells[1])
    adapter = _sdk_adapter(monkeypatch, prepared, "c0")
    with pytest.raises(RuntimeError, match="out of order"):
        run_sdk_nonlive_cell(
            experiment_dir=experiment_dir,
            plan=plan,
            planned_cell=cells[1],
            prepared=prepared,
            adapter=adapter,
            benchmark_python=Path(sys.executable),
            git_executable=_git(),
        )
    first_prepared = _restore(experiment_dir, cells[0])
    first_adapter = _sdk_adapter(monkeypatch, first_prepared, "c0")
    run_sdk_nonlive_cell(
        experiment_dir=experiment_dir,
        plan=plan,
        planned_cell=cells[0],
        prepared=first_prepared,
        adapter=first_adapter,
        benchmark_python=Path(sys.executable),
        git_executable=_git(),
    )
    first_judge = experiment_dir / "cells" / cells[0].cell_id / "judge" / "result.json"
    first_judge.write_bytes(first_judge.read_bytes() + b"\n")
    with pytest.raises(IntegrityError, match="Evidence hash mismatch"):
        run_sdk_nonlive_cell(
            experiment_dir=experiment_dir,
            plan=plan,
            planned_cell=cells[1],
            prepared=prepared,
            adapter=adapter,
            benchmark_python=Path(sys.executable),
            git_executable=_git(),
        )


def test_runner_source_hash_cannot_be_supplied_arbitrarily(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture()
    cell = PlannedCell(
        cell_id="cell_runner_hash_c0",
        block_id="block_runner_hash",
        fixture_id=fixture.id,
        repetition=1,
        variant_id="c0",
        execution_ordinal=1,
    )
    plan = _plan([cell], fixture, runner_sha256="c" * 64)
    experiment_dir = initialize_sdk_experiment(tmp_path / "runner-hash", plan)
    prepared = _restore(experiment_dir, cell)
    adapter = _sdk_adapter(monkeypatch, prepared, "c0")
    with pytest.raises(ValueError, match="executing source tree"):
        run_sdk_nonlive_cell(
            experiment_dir=experiment_dir,
            plan=plan,
            planned_cell=cell,
            prepared=prepared,
            adapter=adapter,
            benchmark_python=Path(sys.executable),
            git_executable=_git(),
        )


def test_secret_like_adapter_evidence_is_redacted_and_never_sealed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture()
    cell = PlannedCell(
        cell_id="cell_secret_attack_c0",
        block_id="block_secret_attack",
        fixture_id=fixture.id,
        repetition=1,
        variant_id="c0",
        execution_ordinal=1,
    )
    plan = _plan([cell], fixture)
    experiment_dir = initialize_sdk_experiment(tmp_path / "secret-attack", plan)
    prepared = _restore(experiment_dir, cell)
    tasks = _tasks(monkeypatch, "c0", prepared.workspace)
    result = _completed_result("src/normalization.py", "src/config.py")
    result["summary"] = "do not export sk-ABCDEFGHIJKLMNOP"
    adapter = _sdk_adapter(
        monkeypatch,
        prepared,
        "c0",
        {
            str(tasks[0].task_id): FakeTurnScript(
                effects=(
                    ("src/normalization.py", NORMALIZATION_SOURCE),
                    ("src/config.py", CONFIG_SOURCE),
                ),
                result=result,
            )
        },
    )
    with pytest.raises(RuntimeError, match="secret-like material"):
        run_sdk_nonlive_cell(
            experiment_dir=experiment_dir,
            plan=plan,
            planned_cell=cell,
            prepared=prepared,
            adapter=adapter,
            benchmark_python=Path(sys.executable),
            git_executable=_git(),
        )
    cell_dir = experiment_dir / "cells" / cell.cell_id
    raw = (cell_dir / "raw" / "adapter-result.json").read_text(encoding="utf-8")
    report = json.loads(
        (cell_dir / "raw" / "redaction-report.json").read_text(encoding="utf-8")
    )
    assert "sk-ABCDEFGHIJKLMNOP" not in raw
    assert "<REDACTED_SECRET>" in raw
    assert report["secret_categories"] == ["OpenAI-style secret"]
    assert not (cell_dir / "sealed" / "measurement.json").exists()
    state = CellStateRecord.model_validate_json(
        (cell_dir / "cell-state.json").read_bytes()
    )
    assert state.state.value == "STOPPED"
    assert state.stop_reason == "secret_evidence_detected"
