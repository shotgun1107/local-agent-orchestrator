from __future__ import annotations

from pathlib import Path

import yaml

from orchestrator.contract import ResultArtifact, RunSpec
from orchestrator.worker import (
    build_oneshot_envelope,
    build_task_envelope,
    render_worker_prompt,
    task_semantics_sha256,
)


REPOSITORY_ROOT = Path(__file__).parents[4]
RUN_SPEC_PATH = (
    REPOSITORY_ROOT
    / "benchmarks"
    / "fixtures"
    / "sequential-code-change"
    / "benchmark-run.yaml"
)
DOCUMENT_RUN_SPEC_PATH = (
    REPOSITORY_ROOT
    / "benchmarks"
    / "fixtures"
    / "sequential-document"
    / "benchmark-run.yaml"
)


def _run_spec() -> RunSpec:
    return RunSpec.model_validate(
        yaml.safe_load(RUN_SPEC_PATH.read_text(encoding="utf-8"))
    )


def test_task_semantics_excludes_only_variant_identity_fields() -> None:
    task = _run_spec().tasks[0]
    first = build_task_envelope(
        task,
        run_id="run-c1",
        task_id="task-c1-t1",
        attempt_id="attempt-c1-t1",
        requirements_version=1,
        timeout_seconds=900,
        remaining_attempts=1,
    )
    second = build_task_envelope(
        task,
        run_id="run-c2",
        task_id="task-c2-t1",
        attempt_id="attempt-c2-t1",
        requirements_version=1,
        timeout_seconds=900,
        remaining_attempts=1,
    )

    assert task_semantics_sha256(first) == task_semantics_sha256(second)
    assert render_worker_prompt(first) != render_worker_prompt(second)
    assert "completed claim is evidence only" in render_worker_prompt(first)
    assert "artifacts.path must name one existing regular file" in render_worker_prompt(first)
    artifact_path = ResultArtifact.model_json_schema()["properties"]["path"]
    assert "Directory paths and glob patterns are invalid" in artifact_path["description"]


def test_c0_oneshot_preserves_all_task_information_without_task_boundaries() -> None:
    spec = _run_spec()
    envelope = build_oneshot_envelope(
        spec,
        run_id="run-c0",
        task_id="task-c0",
        attempt_id="attempt-c0",
        requirements_version=1,
        timeout_seconds=900,
        remaining_attempts=1,
    )

    assert spec.request.text in envelope.goal
    assert all(task.goal in envelope.goal for task in spec.tasks)
    assert envelope.write_scope == ["src/normalization.py", "src/config.py"]
    assert envelope.check_names == ["stage1", "diff_check", "acceptance"]
    assert envelope.workspace_mode == "shared_serial_write"


def test_c0_oneshot_preserves_declared_fixture_inputs() -> None:
    spec = RunSpec.model_validate(
        yaml.safe_load(DOCUMENT_RUN_SPEC_PATH.read_text(encoding="utf-8"))
    )
    envelope = build_oneshot_envelope(
        spec,
        run_id="run-c0",
        task_id="task-c0",
        attempt_id="attempt-c0",
        requirements_version=1,
        timeout_seconds=900,
        remaining_attempts=1,
    )

    assert [item.path for item in envelope.inputs] == ["evidence.md"]
