from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest
import yaml

from benchmark_runner.adapter import B1AdapterConfig, B1SequentialAdapter, CellContext
from benchmark_runner.failure_scenarios import CONFIG_SOURCE, NORMALIZATION_SOURCE
from benchmark_runner.sdk_baselines import SdkBaselineAdapter, SdkBaselineConfig
from benchmark_runner.sdk_common import FakeSdkRuntime, FakeTurnScript, WorkerContract
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


def _completed_result(*paths: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status_claim": "completed",
        "summary": "fake SDK vertical slice completed",
        "artifacts": [
            {"path": path, "kind": "file", "description": "fixture result"}
            for path in paths
        ],
        "changed_paths": list(paths),
        "checks_run_by_worker": [],
        "assumptions": [],
        "warnings": [],
        "requested_followup": None,
    }


def _fixture():
    manifest = load_frozen_manifest(MANIFEST_PATH)
    return next(item for item in manifest.fixtures if item.id == "sequential-code-change")


def _prepare(tmp_path: Path, name: str):
    return FixtureRestorer(REPOSITORY_ROOT, str(_git())).restore(
        _fixture(),
        tmp_path / name / "workspace",
    )


def _worker_contract(monkeypatch: pytest.MonkeyPatch):
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


def _task_envelopes(monkeypatch: pytest.MonkeyPatch, variant: str, workspace: Path):
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


def _sdk_scripts(tasks: tuple[object, ...], variant: str) -> dict[str, FakeTurnScript]:
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


def test_c0_c1_c2_share_contract_and_reach_the_same_judge(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contract = _worker_contract(monkeypatch)
    results = {}
    for variant in ("c0", "c1", "c2"):
        prepared = _prepare(tmp_path, variant)
        tasks = _task_envelopes(monkeypatch, variant, prepared.workspace)
        runtime = FakeSdkRuntime(prepared.workspace, _sdk_scripts(tasks, variant))
        adapter = SdkBaselineAdapter(
            SdkBaselineConfig(
                variant_id=variant,
                tasks=tasks,
                contract=contract,
                runtime=runtime,
            )
        )
        results[variant] = run_nonlive_vertical_slice(
            adapter=adapter,
            prepared=prepared,
            context=CellContext("exp-sdk-vertical", f"cell-{variant}"),
            benchmark_python=Path(sys.executable),
            git_executable=_git(),
            judge_dir=tmp_path / variant / "judge",
        )

    assert all(result.evidence.outcome_state == "completed" for result in results.values())
    assert all(result.judge.check_success is True for result in results.values())
    assert results["c0"].evidence.normalized_metrics["session_count"] == 1
    assert results["c0"].evidence.normalized_metrics["turn_count"] == 1
    assert results["c1"].evidence.normalized_metrics["session_count"] == 1
    assert results["c1"].evidence.normalized_metrics["turn_count"] == 2
    assert results["c2"].evidence.normalized_metrics["session_count"] == 2
    assert results["c2"].evidence.normalized_metrics["turn_count"] == 2
    assert results["c0"].evidence.normalized_metrics["token_usage"]["total_tokens"] == 15
    assert results["c1"].evidence.normalized_metrics["token_usage"]["total_tokens"] == 30
    assert results["c2"].evidence.normalized_metrics["token_usage"]["total_tokens"] == 30
    c1_hashes = [turn["task_semantics_sha256"] for turn in results["c1"].evidence.raw_payload["turns"]]
    c2_hashes = [turn["task_semantics_sha256"] for turn in results["c2"].evidence.raw_payload["turns"]]
    assert c1_hashes == c2_hashes
    assert all(
        turn["usage_delta"]["total_tokens"] == 15
        for variant in ("c0", "c1", "c2")
        for turn in results[variant].evidence.raw_payload["turns"]
    )


def test_b1_reaches_the_same_fixture_judge_without_model_turns(tmp_path: Path) -> None:
    prepared = _prepare(tmp_path, "b1")
    fake_fixture_path = tmp_path / "b1" / "fake-runtime.json"
    fake_fixture_path.write_text(
        json.dumps(
            {
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
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    adapter = B1SequentialAdapter(
        B1AdapterConfig(
            command_prefix=(sys.executable, "-m", "orchestrator"),
            project=prepared.workspace,
            run_spec=prepared.workspace / "benchmark-run.yaml",
            state_root=tmp_path / "b1" / "variant-state",
            schema_root=B1_SCHEMA_ROOT,
            runtime="fake",
            fake_fixture=fake_fixture_path,
        )
    )
    result = run_nonlive_vertical_slice(
        adapter=adapter,
        prepared=prepared,
        context=CellContext("exp-sdk-vertical", "cell-b1"),
        benchmark_python=Path(sys.executable),
        git_executable=_git(),
        judge_dir=tmp_path / "b1" / "judge",
    )

    assert result.evidence.outcome_state == "completed"
    assert result.judge.check_success is True
    assert result.evidence.raw_payload["actual_model_turns"] == 0
