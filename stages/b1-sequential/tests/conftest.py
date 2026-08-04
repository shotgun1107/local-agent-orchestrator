from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from orchestrator.contract import RunSpec


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=root, text=True, encoding="utf-8", errors="replace",
        capture_output=True, shell=False, check=True,
    )


@pytest.fixture
def project_factory(tmp_path: Path):
    counter = 0

    def create(*, check_fails: bool = False, task_timeout: int = 5) -> Path:
        nonlocal counter
        counter += 1
        root = tmp_path / f"project-{counter}"
        root.mkdir()
        template = Path(__file__).parents[1] / "templates" / "project-pack" / ".orchestrator"
        shutil.copytree(template, root / ".orchestrator")
        project_file = root / ".orchestrator" / "project.yaml"
        project = yaml.safe_load(project_file.read_text(encoding="utf-8"))
        project["project_id"] = f"fixture-{counter}"
        project_file.write_text(yaml.safe_dump(project, sort_keys=False), encoding="utf-8")
        checks_file = root / ".orchestrator" / "checks.yaml"
        checks = yaml.safe_load(checks_file.read_text(encoding="utf-8"))
        checks["checks"]["test_check"] = {
            "kind": "command",
            "argv": ["python", "-c", "import sys; sys.exit(1)" if check_fails else "print('ok')"],
            "cwd": ".",
            "timeout_seconds": 10,
            "expected_exit_codes": [0],
        }
        checks_file.write_text(yaml.safe_dump(checks, sort_keys=False), encoding="utf-8")
        policies_file = root / ".orchestrator" / "policies.yaml"
        policies = yaml.safe_load(policies_file.read_text(encoding="utf-8"))
        policies["policies"]["b1_safe"]["task_timeout_seconds"] = task_timeout
        policies["policies"]["b1_safe"]["interrupt_grace_seconds"] = 1
        policies_file.write_text(yaml.safe_dump(policies, sort_keys=False), encoding="utf-8")
        (root / "README.md").write_text("fixture input\n", encoding="utf-8")
        (root / "src").mkdir()
        (root / "src" / "existing.txt").write_text("original\n", encoding="utf-8")
        git(root, "init", "-b", "main")
        git(root, "config", "user.name", "B1 Tests")
        git(root, "config", "user.email", "b1-tests@example.invalid")
        git(root, "add", ".")
        git(root, "commit", "-m", "fixture")
        return root

    return create


def make_spec(
    *,
    workspace_mode: str = "read_only",
    check_name: str = "test_check",
    write_scope: list[str] | None = None,
    tasks: int = 1,
) -> RunSpec:
    task_specs = []
    for index in range(tasks):
        key = f"T{index + 1}"
        task_specs.append({
            "key": key,
            "goal": f"fixture task {index + 1}",
            "completion_criteria": [{"id": f"TC{index + 1}", "text": "Check passes", "check_names": [check_name]}],
            "depends_on": [] if index == 0 else [f"T{index}"],
            "inputs": [],
            "read_scope": ["README.md", "src/**"],
            "write_scope": write_scope or [],
            "capability_profile": "document_read" if workspace_mode == "read_only" else "code_change",
            "workspace_mode": workspace_mode,
            "check_names": [check_name],
            "approval": "none",
        })
    return RunSpec.model_validate({
        "schema_version": 1,
        "request": {"source": "test", "text": "Run the deterministic fixture"},
        "completion_criteria": [{
            "id": "RC1",
            "text": "All fixture Tasks pass",
            "satisfied_by_tasks": [task["key"] for task in task_specs],
        }],
        "constraints": [],
        "assumptions": [],
        "tasks": task_specs,
    })
