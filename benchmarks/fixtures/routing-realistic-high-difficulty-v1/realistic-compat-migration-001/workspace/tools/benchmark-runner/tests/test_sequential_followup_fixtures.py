from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from benchmark_runner.contract import ArtifactIdentity, ExecutionPlan
from benchmark_runner.runner import (
    create_r4_experiment_from_manifest,
    frozen_b0_b1_decision_policy,
)
from benchmark_runner.workspace import FixtureRestorer, load_frozen_manifest


REPOSITORY = Path(__file__).resolve().parents[3]
FIXTURES = REPOSITORY / "benchmarks" / "fixtures"
MANIFEST = REPOSITORY / "benchmarks" / "manifests" / "b0-b1-sequential-followup.yaml"


def _run(workspace: Path, *argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv),
        cwd=workspace,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )


def _copy(tmp_path: Path, fixture_id: str) -> Path:
    workspace = tmp_path / fixture_id
    shutil.copytree(FIXTURES / fixture_id, workspace)
    return workspace


def test_sequential_code_fixture_requires_both_stages(tmp_path: Path) -> None:
    workspace = _copy(tmp_path, "sequential-code-change")
    assert _run(workspace, "python", "-m", "unittest", "benchmark_checks.test_stage1").returncode != 0
    (workspace / "src" / "normalization.py").write_text(
        "def normalize_key(value):\n"
        "    if not isinstance(value, str):\n"
        "        raise ValueError('key must be a string')\n"
        "    normalized = value.strip().lower().replace('-', '_')\n"
        "    if not normalized:\n"
        "        raise ValueError('key must not be empty')\n"
        "    return normalized\n",
        encoding="utf-8",
        newline="\n",
    )
    assert _run(workspace, "python", "-m", "unittest", "benchmark_checks.test_stage1").returncode == 0
    assert _run(workspace, "python", "-m", "unittest", "benchmark_checks.test_acceptance").returncode != 0
    (workspace / "src" / "config.py").write_text(
        "from collections.abc import Mapping\n"
        "from typing import Any\n"
        "from .normalization import normalize_key\n\n"
        "ALLOWED_KEYS = {'timeout_seconds', 'max_retries'}\n\n"
        "def parse_config(raw: Mapping[str, Any]) -> dict[str, Any]:\n"
        "    parsed = {}\n"
        "    for key, value in raw.items():\n"
        "        normalized = normalize_key(key)\n"
        "        if normalized not in ALLOWED_KEYS or normalized in parsed:\n"
        "            raise ValueError(normalized)\n"
        "        parsed[normalized] = value\n"
        "    return parsed\n",
        encoding="utf-8",
        newline="\n",
    )
    assert _run(workspace, "python", "-m", "unittest", "benchmark_checks.test_acceptance").returncode == 0


def test_sequential_document_fixture_requires_evidence_then_report(tmp_path: Path) -> None:
    workspace = _copy(tmp_path, "sequential-document")
    assert _run(workspace, "python", "benchmark_checks/check_evidence.py").returncode != 0
    (workspace / "evidence.md").write_text(
        "E1: 배포는 2099-07-31 09:00 UTC에 시작됐다.\n"
        "E2: 배포 버전은 2.4.1이었다.\n"
        "E3: 09:12 UTC에 오류율 경보가 발생했다.\n"
        "E4: 운영자는 09:18 UTC에 롤백을 시작했다.\n"
        "E5: 09:27 UTC에 오류율이 정상 범위로 돌아왔다.\n"
        "E6: 직접 원인은 잘못된 캐시 주소였다.\n"
        "U1: 설정 파일 승인자는 미확인이다.\n"
        "U2: 고객별 영향 건수는 미확인이다.\n",
        encoding="utf-8",
        newline="\n",
    )
    assert _run(workspace, "python", "benchmark_checks/check_evidence.py").returncode == 0
    assert _run(workspace, "python", "benchmark_checks/check_report.py").returncode != 0
    (workspace / "report.md").write_text(
        "# 운영 보고서\n\n"
        "## 확인된 사실\n\n"
        "- 배포는 2099-07-31 09:00 UTC에 시작됐다. (E1)\n"
        "- 배포 버전은 2.4.1이었다. (E2)\n"
        "- 09:12 UTC에 오류율 경보가 발생했다. (E3)\n"
        "- 09:18 UTC에 롤백을 시작했다. (E4)\n"
        "- 09:27 UTC에 오류율이 정상 범위로 돌아왔다. (E5)\n"
        "- 직접 원인은 잘못된 캐시 주소였다. (E6)\n\n"
        "## 미확인\n\n"
        "- 설정 파일 승인자는 미확인이다. (U1)\n"
        "- 고객별 영향 건수는 미확인이다. (U2)\n",
        encoding="utf-8",
        newline="\n",
    )
    assert _run(workspace, "python", "benchmark_checks/check_report.py").returncode == 0


@pytest.mark.parametrize("fixture_id", ["sequential-code-change", "sequential-document"])
def test_sequential_fixture_declares_two_ordered_tasks(fixture_id: str) -> None:
    import yaml

    raw = yaml.safe_load((FIXTURES / fixture_id / "benchmark-run.yaml").read_text(encoding="utf-8"))
    tasks = raw["tasks"]
    assert [task["key"] for task in tasks] == ["T1", "T2"]
    assert tasks[0]["depends_on"] == []
    assert tasks[1]["depends_on"] == ["T1"]


def test_followup_manifest_restores_both_frozen_fixture_trees(tmp_path: Path) -> None:
    manifest = load_frozen_manifest(MANIFEST)
    assert [item.id for item in manifest.fixtures] == [
        "sequential-code-change",
        "sequential-document",
    ]
    restorer = FixtureRestorer(REPOSITORY, shutil.which("git") or "git")
    for fixture in manifest.fixtures:
        prepared = restorer.restore(fixture, tmp_path / fixture.id)
        assert prepared.fixture.git_tree == fixture.git_tree


def test_followup_manifest_builds_a_balanced_twelve_cell_plan(tmp_path: Path) -> None:
    created = create_r4_experiment_from_manifest(
        state_root=tmp_path / "state",
        source_repository=REPOSITORY,
        manifest_path=MANIFEST,
        runner_artifact=ArtifactIdentity(
            artifact_id="benchmark-runner",
            version="test",
            sha256="1" * 64,
        ),
        variant_artifacts=[
            ArtifactIdentity(artifact_id="b0", version="test", sha256="1" * 64),
            ArtifactIdentity(artifact_id="b1", version="test", sha256="2" * 64),
        ],
        baseline_variant="b0",
        candidate_variant="b1",
        seed=20990806,
        primary_metrics=[
            "check_success",
            "manual_copy_or_relay_count_excluding_start",
        ],
        decision_policy=frozen_b0_b1_decision_policy(),
        reasoning_control="test",
        environment_fingerprint={
            "model": "gpt-5.6-terra",
            "auth_method": "chatgpt",
        },
        revision=1,
    )
    plan = ExecutionPlan.model_validate_json(Path(created.plan_path).read_bytes())
    assert len(plan.cells) == 12
    assert {cell.fixture_id for cell in plan.cells} == {
        "sequential-code-change",
        "sequential-document",
    }
    assert sum(cell.variant_id == "b0" for cell in plan.cells) == 6
    assert sum(cell.variant_id == "b1" for cell in plan.cells) == 6
