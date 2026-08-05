from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from orchestrator.ledger import Ledger
from orchestrator.schedule import Orchestrator, load_project, load_run_spec
from tests.conftest import git


def fixture_source(name: str) -> Path:
    repository = Path(__file__).resolve().parents[4]
    return repository / "benchmarks" / "fixtures" / name


def initialize_fixture(tmp_path: Path, name: str) -> Path:
    destination = tmp_path / name
    shutil.copytree(fixture_source(name), destination)
    git(destination, "init", "-b", "main")
    git(destination, "config", "user.name", "B1 Benchmark")
    git(destination, "config", "user.email", "b1-benchmark@example.invalid")
    git(destination, "add", ".")
    git(destination, "commit", "-m", "frozen fixture")
    return destination


def execute_fixture(root: Path, state: Path, effects: list[dict[str, str]]) -> dict:
    orchestrator = Orchestrator(
        load_project(root), state_root=state, runtime_kind="fake",
        fake_fixture={"effects": effects},
    )
    try:
        run_id = orchestrator.start(load_run_spec(root / "benchmark-run.yaml"))
    finally:
        orchestrator.close()
    with Ledger(state / "ledger.sqlite") as ledger:
        return ledger.load_run_snapshot(run_id)


def test_code_change_fixture_runs_without_core_changes(tmp_path: Path) -> None:
    root = initialize_fixture(tmp_path, "code-change")
    snapshot = execute_fixture(
        root,
        tmp_path / "code-state",
        [{
            "type": "write_file",
            "path": "src/config.py",
            "content": (
                "ALLOWED_KEYS = {'name'}\n\n\n"
                "def parse_config(value: dict[str, object]) -> dict[str, object]:\n"
                "    unknown = set(value) - ALLOWED_KEYS\n"
                "    if unknown:\n"
                "        raise ValueError(f'unknown keys: {sorted(unknown)}')\n"
                "    return dict(value)\n"
            ),
        }],
    )
    assert snapshot["run"]["state"] == "COMPLETED"


def test_document_fixture_runs_by_project_pack_only(tmp_path: Path) -> None:
    root = initialize_fixture(tmp_path, "document-read")
    snapshot = execute_fixture(
        root,
        tmp_path / "document-state",
        [{
            "type": "write_file",
            "path": "report.md",
            "content": "# 확인된 사실\n\n- 작업 A 완료\n- 작업 B 미실행\n\n# 미확인\n\n- 외부 배포 여부\n",
        }],
    )
    assert snapshot["run"]["state"] == "COMPLETED"


def test_core_contains_no_pilot_specific_identifiers() -> None:
    source_root = Path(__file__).resolve().parents[2] / "src" / "orchestrator"
    forbidden = ["EU4", "Brain", "이어서 작업", "P1", "P2", "P3"]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in source_root.glob("*.py"))
    assert all(value not in combined for value in forbidden)


def test_frozen_manifest_pins_fixture_commit_and_git_tree() -> None:
    repository = Path(__file__).resolve().parents[4]
    manifest = yaml.safe_load(
        (repository / "benchmarks" / "manifests" / "b0-b1-frozen.yaml").read_text(encoding="utf-8")
    )
    assert manifest["status"] == "frozen_before_execution"
    assert manifest["repetitions"] == 3
    for fixture in manifest["fixtures"]:
        assert len(fixture["commit"]) == 40
        assert len(fixture["git_tree"]) == 40
        recorded_tree = git(
            repository,
            "rev-parse",
            f"{fixture['commit']}:{fixture['path']}",
        ).stdout.strip()
        current_tree = git(repository, "rev-parse", f"HEAD:{fixture['path']}").stdout.strip()
        assert recorded_tree == fixture["git_tree"] == current_tree
