from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest
import yaml

from benchmark_runner.adapter import B1AdapterConfig, B1SequentialAdapter, CellContext
from benchmark_runner.failure_scenarios import FAILURE_SCENARIOS, FailureScenario
from benchmark_runner.sdk_baselines import SdkBaselineAdapter, SdkBaselineConfig
from benchmark_runner.sdk_common import FakeSdkRuntime, WorkerContract
from benchmark_runner.sdk_vertical_slice import run_nonlive_vertical_slice
from benchmark_runner.workspace import FixtureRestorer, load_frozen_manifest


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


def _prepare(tmp_path: Path, cell_id: str):
    manifest = load_frozen_manifest(MANIFEST_PATH)
    fixture = next(
        item for item in manifest.fixtures if item.id == "sequential-code-change"
    )
    return FixtureRestorer(REPOSITORY_ROOT, str(_git())).restore(
        fixture,
        tmp_path / cell_id / "workspace",
    )


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


def _tasks(monkeypatch: pytest.MonkeyPatch, variant: str, workspace: Path):
    monkeypatch.syspath_prepend(str(B1_SOURCE_ROOT))
    from orchestrator.contract import RunSpec
    from orchestrator.worker import build_task_envelope

    spec = RunSpec.model_validate(
        yaml.safe_load((workspace / "benchmark-run.yaml").read_text(encoding="utf-8"))
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


@pytest.mark.parametrize("scenario", FAILURE_SCENARIOS, ids=lambda item: item.scenario_id)
@pytest.mark.parametrize("variant", ("c1", "c2", "b1"))
def test_failure_injection_gate_matches_frozen_expectations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    scenario: FailureScenario,
    variant: str,
) -> None:
    cell_id = f"cell-{scenario.scenario_id}-{variant}"
    prepared = _prepare(tmp_path, cell_id)
    if variant in {"c1", "c2"}:
        tasks = _tasks(monkeypatch, variant, prepared.workspace)
        task_ids = tuple(str(task.task_id) for task in tasks)
        assert len(task_ids) == 2
        adapter = SdkBaselineAdapter(
            SdkBaselineConfig(
                variant_id=variant,
                tasks=tasks,
                contract=_contract(monkeypatch),
                runtime=FakeSdkRuntime(
                    prepared.workspace,
                    scenario.sdk_scripts((task_ids[0], task_ids[1])),
                ),
            )
        )
    else:
        fake_fixture_path = tmp_path / cell_id / "fake-runtime.json"
        fake_fixture_path.write_text(
            json.dumps(scenario.b1_fixture(), ensure_ascii=False),
            encoding="utf-8",
        )
        adapter = B1SequentialAdapter(
            B1AdapterConfig(
                command_prefix=(sys.executable, "-m", "orchestrator"),
                project=prepared.workspace,
                run_spec=prepared.workspace / "benchmark-run.yaml",
                state_root=tmp_path / cell_id / "variant-state",
                schema_root=B1_SCHEMA_ROOT,
                runtime="fake",
                fake_fixture=fake_fixture_path,
            )
        )

    result = run_nonlive_vertical_slice(
        adapter=adapter,
        prepared=prepared,
        context=CellContext("exp-failure-gate", cell_id),
        benchmark_python=Path(sys.executable),
        git_executable=_git(),
        judge_dir=tmp_path / cell_id / "judge",
    )

    if variant in {"c1", "c2"}:
        assert result.evidence.outcome_state == "completed"
        assert result.evidence.normalized_metrics["turn_count"] == 2
        assert result.judge.check_success is scenario.baseline_judge_success
    else:
        assert result.evidence.outcome_state == "blocked"
        assert result.evidence.normalized_metrics["turn_count"] == 1
        assert result.evidence.normalized_metrics["session_count"] == 1
        assert result.evidence.raw_payload["actual_model_turns"] == 0
        assert result.judge.check_success is scenario.b1_judge_success
