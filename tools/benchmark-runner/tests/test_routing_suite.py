from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from benchmark_runner.contract import ArtifactIdentity, CellStateRecord, Measurement
from benchmark_runner.routing_suite import (
    ROUTING_SCHEMAS,
    RoutingSuiteManifest,
    build_routing_s1_plan,
    compute_fixture_complexity,
    export_routing_schemas,
    initialize_routing_s1_experiment,
    load_routing_stage,
    load_routing_suite,
    run_next_routing_s1_nonlive_cell,
)
from benchmark_runner.runner import verify_sealed_cell
from benchmark_runner.sdk_baselines import SdkBaselineAdapter, SdkBaselineConfig
from benchmark_runner.sdk_cells import runner_source_sha256
from benchmark_runner.sdk_common import FakeSdkRuntime, FakeTurnScript, WorkerContract
from benchmark_runner.workspace import load_frozen_manifest


REPOSITORY_ROOT = Path(__file__).parents[3]
SUITE_ROOT = REPOSITORY_ROOT / "benchmarks" / "suites" / "sdk-routing-v1"
SUITE_PATH = SUITE_ROOT / "suite.yaml"
STAGE_PATH = SUITE_ROOT / "stages" / "s1-baseline.yaml"
B1_SOURCE_ROOT = REPOSITORY_ROOT / "stages" / "b1-sequential" / "src"

FIXED_CONFIG = '''ALLOWED_KEYS = {"name"}


def parse_config(value: dict[str, object]) -> dict[str, object]:
    unknown = set(value) - ALLOWED_KEYS
    if unknown:
        raise ValueError(f"unknown top-level keys: {sorted(unknown)}")
    return dict(value)
'''


def _git() -> Path:
    executable = shutil.which("git")
    assert executable is not None
    return Path(executable)


def _artifacts() -> tuple[ArtifactIdentity, list[ArtifactIdentity]]:
    runner_sha256 = runner_source_sha256()
    return (
        ArtifactIdentity(
            artifact_id="benchmark-runner",
            version="routing-suite-test",
            sha256=runner_sha256,
        ),
        [
            ArtifactIdentity(
                artifact_id="c2",
                version="routing-suite-test",
                sha256="2" * 64,
            ),
            ArtifactIdentity(
                artifact_id="b1",
                version="routing-suite-test",
                sha256="3" * 64,
            ),
        ],
    )


def _plan():
    runner, variants = _artifacts()
    return build_routing_s1_plan(
        repository_root=REPOSITORY_ROOT,
        suite_path=SUITE_PATH,
        stage_path=STAGE_PATH,
        runner=runner,
        variants=variants,
        environment_fingerprint={
            "runtime": "fake",
            "actual_model_turns": "0",
        },
        created_at=datetime(2026, 8, 7, tzinfo=timezone.utc),
    )


def _completed_result() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status_claim": "completed",
        "summary": "unknown-key validation implemented",
        "artifacts": [
            {
                "path": "src/config.py",
                "kind": "source",
                "description": "validated configuration parser",
            }
        ],
        "changed_paths": ["src/config.py"],
        "checks_run_by_worker": [],
        "assumptions": [],
        "warnings": [],
        "requested_followup": None,
    }


def test_routing_manifests_and_generated_schemas_match_contracts(tmp_path: Path) -> None:
    suite = load_routing_suite(SUITE_PATH)
    stage = load_routing_stage(STAGE_PATH)
    assert suite.design_revision == 2
    assert stage.purpose == "calibration_only"
    assert stage.planned_live_model_turns == 12
    assert [(cell.fixture_id, cell.variant_id) for cell in stage.cells] == [
        ("code-change", "c2"),
        ("code-change", "b1"),
        ("document-read", "b1"),
        ("document-read", "c2"),
        ("sequential-code-change", "b1"),
        ("sequential-code-change", "c2"),
        ("sequential-document", "c2"),
        ("sequential-document", "b1"),
    ]

    export_routing_schemas(tmp_path)
    assert sorted(path.name for path in tmp_path.iterdir()) == sorted(ROUTING_SCHEMAS)
    for filename in ROUTING_SCHEMAS:
        assert (tmp_path / filename).read_bytes() == (SUITE_ROOT / filename).read_bytes()

    with pytest.raises(ValidationError):
        RoutingSuiteManifest.model_validate(
            {
                **yaml.safe_load(SUITE_PATH.read_text(encoding="utf-8")),
                "unexpected": True,
            }
        )


def test_complexity_profiles_are_recomputed_from_frozen_fixture_trees() -> None:
    stage = load_routing_stage(STAGE_PATH)
    declarations = {profile.fixture_id: profile.complexity for profile in stage.profiles}
    fixtures = {}
    for selection in stage.fixture_manifests:
        manifest = load_frozen_manifest(REPOSITORY_ROOT / selection.path)
        fixtures.update({fixture.id: fixture for fixture in manifest.fixtures})

    for fixture_id, declared in declarations.items():
        calculated = compute_fixture_complexity(
            REPOSITORY_ROOT,
            fixtures[fixture_id],
            expected_write_files=declared.expected_write_files,
            verification_kind=declared.verification_kind,
            failure_profile=declared.failure_profile,
            solution_ambiguity=declared.solution_ambiguity,
        )
        assert calculated == declared


def test_s1_plan_has_exact_eight_cell_order_and_calibration_only_policy() -> None:
    plan = _plan()
    assert [(cell.fixture_id, cell.variant_id) for cell in plan.cells] == [
        ("code-change", "c2"),
        ("code-change", "b1"),
        ("document-read", "b1"),
        ("document-read", "c2"),
        ("sequential-code-change", "b1"),
        ("sequential-code-change", "c2"),
        ("sequential-document", "c2"),
        ("sequential-document", "b1"),
    ]
    assert plan.decision_policy["route_decision_allowed"] is False
    assert plan.decision_policy["planned_live_model_turns"] == 12
    assert plan.decision_policy["purpose"] == "calibration_only"
    assert len(plan.decision_policy["profiles"]) == 4
    assert any(
        supplement.field == "actual_model_turns" and supplement.value == 0
        for supplement in plan.plan_supplemented
    )
    assert _plan().plan_fingerprint == plan.plan_fingerprint


def test_model_free_runner_executes_exactly_one_next_cell_and_seals(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.syspath_prepend(str(B1_SOURCE_ROOT))
    from orchestrator.contract import RunSpec
    from orchestrator.worker import (
        build_task_envelope,
        render_worker_prompt,
        result_schema,
        task_semantics_sha256,
        validate_result,
    )

    plan = _plan()
    experiment_dir = initialize_routing_s1_experiment(tmp_path / "state", plan)

    def adapter_factory(cell, prepared):
        assert cell.cell_id == "cell_s1_code-change_1_c2"
        spec = RunSpec.model_validate(
            yaml.safe_load(
                (prepared.workspace / "benchmark-run.yaml").read_text(encoding="utf-8")
            )
        )
        task = build_task_envelope(
            spec.tasks[0],
            run_id="run-routing-s1",
            task_id="task-routing-s1-t1",
            attempt_id="attempt-routing-s1-t1",
            requirements_version=1,
            timeout_seconds=900,
            remaining_attempts=1,
        )
        contract = WorkerContract(
            render_prompt=render_worker_prompt,
            result_schema=result_schema,
            validate_result=lambda value: validate_result(value).model_dump(mode="json"),
            semantics_sha256=task_semantics_sha256,
        )
        return SdkBaselineAdapter(
            SdkBaselineConfig(
                variant_id="c2",
                tasks=(task,),
                contract=contract,
                runtime=FakeSdkRuntime(
                    prepared.workspace,
                    {
                        str(task.task_id): FakeTurnScript(
                            effects=(("src/config.py", FIXED_CONFIG),),
                            result=_completed_result(),
                        )
                    },
                ),
            )
        )

    result = run_next_routing_s1_nonlive_cell(
        repository_root=REPOSITORY_ROOT,
        suite_path=SUITE_PATH,
        stage_path=STAGE_PATH,
        experiment_dir=experiment_dir,
        adapter_factory=adapter_factory,
        benchmark_python=Path(sys.executable),
        git_executable=_git(),
    )
    assert result.cell_id == "cell_s1_code-change_1_c2"
    assert result.cell_state == "SEALED"
    assert result.check_success is True
    assert result.actual_model_turns == 0

    cell_dir = experiment_dir / "cells" / result.cell_id
    state = CellStateRecord.model_validate_json(
        (cell_dir / "cell-state.json").read_bytes()
    )
    assert state.state.value == "SEALED"
    measurement: Measurement = verify_sealed_cell(cell_dir)
    assert measurement.variant_metrics.values["actual_model_turns"] == 0
    assert not (experiment_dir / "cells" / plan.cells[1].cell_id).exists()
