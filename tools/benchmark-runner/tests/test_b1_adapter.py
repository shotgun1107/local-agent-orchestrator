from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

from benchmark_runner.adapter import B1AdapterConfig, B1SequentialAdapter, CellContext
from benchmark_runner.judge import FixtureJudge
from benchmark_runner.workspace import FixtureRestorer, load_frozen_manifest

REPOSITORY_ROOT = Path(__file__).parents[3]
MANIFEST_PATH = REPOSITORY_ROOT / "benchmarks" / "manifests" / "b0-b1-frozen.yaml"
B1_SCHEMA_ROOT = REPOSITORY_ROOT / "stages" / "b1-sequential" / "schemas" / "v1"

SOLUTIONS = {
    "code-change": {
        "path": "src/config.py",
        "content": (
            'ALLOWED_KEYS = {"name"}\n\n\n'
            "def parse_config(value: dict[str, object]) -> dict[str, object]:\n"
            "    unknown_keys = set(value) - ALLOWED_KEYS\n"
            "    if unknown_keys:\n"
            '        raise ValueError(f"unknown top-level keys: {sorted(unknown_keys)}")\n'
            "    return dict(value)\n"
        ),
    },
    "document-read": {
        "path": "report.md",
        "content": (
            "# 상태 보고서\n\n"
            "## 확인된 사실\n\n"
            "- 작업 A는 완료됐다.\n"
            "- 작업 B는 아직 실행되지 않았다.\n\n"
            "## 미확인\n"
            "- 외부 배포 여부는 확인하지 못했다.\n"
        ),
    },
}


def _git() -> Path:
    executable = shutil.which("git")
    assert executable is not None
    return Path(executable)


def _restore(tmp_path: Path, fixture_id: str):
    manifest = load_frozen_manifest(MANIFEST_PATH)
    fixture = next(item for item in manifest.fixtures if item.id == fixture_id)
    return FixtureRestorer(REPOSITORY_ROOT, str(_git())).restore(
        fixture,
        tmp_path / "workspace",
    )


def _fake_fixture(tmp_path: Path, fixture_id: str) -> Path:
    solution = SOLUTIONS[fixture_id]
    result = {
        "schema_version": 1,
        "status_claim": "completed",
        "summary": "deterministic R2 FakeRuntime solution",
        "artifacts": [],
        "changed_paths": [solution["path"]],
        "checks_run_by_worker": [],
        "assumptions": [],
        "warnings": [],
        "requested_followup": None,
    }
    path = tmp_path / "fake-runtime.json"
    path.write_text(
        json.dumps(
            {
                "scenario": "complete",
                "effects": [{"type": "write_file", **solution}],
                "result": result,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


@pytest.mark.parametrize("fixture_id", ["code-change", "document-read"])
def test_b1_fake_adapter_uses_public_cli_then_independent_judge(
    tmp_path: Path,
    fixture_id: str,
) -> None:
    prepared = _restore(tmp_path, fixture_id)
    adapter = B1SequentialAdapter(
        B1AdapterConfig(
            command_prefix=(sys.executable, "-m", "orchestrator"),
            project=prepared.workspace,
            run_spec=prepared.workspace / "benchmark-run.yaml",
            state_root=tmp_path / "variant-state",
            schema_root=B1_SCHEMA_ROOT,
            fake_fixture=_fake_fixture(tmp_path, fixture_id),
        )
    )
    context = CellContext(experiment_id="exp_r2_test", cell_id="cell_r2_test")
    assert adapter.preflight(context).ok is True
    evidence = adapter.run(context)

    assert evidence.outcome_state == "completed"
    assert evidence.failure_kind is None
    assert evidence.attempt_count == 1
    assert evidence.normalized_metrics["turn_count"] == 1
    assert evidence.normalized_metrics["session_count"] == 1
    assert evidence.normalized_metrics["token_usage_status"] == "measured"
    assert evidence.normalized_metrics["token_usage"] == {
        "input_tokens": 10,
        "output_tokens": 5,
        "total_tokens": 15,
    }
    assert evidence.normalized_metrics["b1_session_usage_statuses"] == ["measured"]
    judge = FixtureJudge(Path(sys.executable), _git()).evaluate(
        prepared,
        tmp_path / "judge",
    )
    assert judge.check_success is True


def test_runner_adapter_has_no_b1_internal_import() -> None:
    source = (
        REPOSITORY_ROOT
        / "tools"
        / "benchmark-runner"
        / "src"
        / "benchmark_runner"
        / "adapter.py"
    ).read_text(encoding="utf-8")
    assert "from orchestrator" not in source
    assert "import orchestrator" not in source
