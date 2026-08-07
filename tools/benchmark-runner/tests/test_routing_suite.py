from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from benchmark_runner.adapter import B1AdapterConfig, B1SequentialAdapter
from benchmark_runner.contract import ArtifactIdentity, CellStateRecord, Measurement
from benchmark_runner.failure_scenarios import CONFIG_SOURCE, NORMALIZATION_SOURCE
from benchmark_runner.routing_suite import (
    ROUTING_SCHEMAS,
    RoutingSuiteError,
    RoutingSuiteManifest,
    build_routing_s1_plan,
    compute_fixture_complexity,
    export_routing_s1_nonlive,
    export_routing_schemas,
    initialize_routing_s1_experiment,
    load_routing_stage,
    load_routing_suite,
    routing_s1_nonlive_status,
    run_all_routing_s1_nonlive_cells,
    run_next_routing_s1_nonlive_cell,
    verify_routing_s1_nonlive_export,
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
B1_SCHEMA_ROOT = REPOSITORY_ROOT / "stages" / "b1-sequential" / "schemas" / "v1"

FIXED_CONFIG = '''ALLOWED_KEYS = {"name"}


def parse_config(value: dict[str, object]) -> dict[str, object]:
    unknown = set(value) - ALLOWED_KEYS
    if unknown:
        raise ValueError(f"unknown top-level keys: {sorted(unknown)}")
    return dict(value)
'''

SIMPLE_REPORT = """# 상태 보고서

## 확인된 사실

- 작업 A는 완료됐다.
- 작업 B는 아직 실행되지 않았다.

## 미확인
- 외부 배포 여부는 확인하지 못했다.
"""

EVIDENCE_REPORT = """E1: 배포는 2026-07-31 09:00 UTC에 시작됐다.
E2: 배포 버전은 2.4.1이었다.
E3: 09:12 UTC에 오류율 경보가 발생했다.
E4: 운영자는 09:18 UTC에 롤백을 시작했다.
E5: 09:27 UTC에 오류율이 정상 범위로 돌아왔다.
E6: 직접 원인은 잘못된 캐시 주소였다.
U1: 설정 파일 승인자는 미확인이다.
U2: 고객별 영향 건수는 미확인이다.
"""

FINAL_REPORT = """# 운영 보고서

## 확인된 사실

- 배포는 2026-07-31 09:00 UTC에 시작됐다. (E1)
- 배포 버전은 2.4.1이었다. (E2)
- 09:12 UTC에 오류율 경보가 발생했다. (E3)
- 09:18 UTC에 롤백을 시작했다. (E4)
- 09:27 UTC에 오류율이 정상 범위로 돌아왔다. (E5)
- 직접 원인은 잘못된 캐시 주소였다. (E6)

## 미확인

- 설정 파일 승인자는 미확인이다. (U1)
- 고객별 영향 건수는 미확인이다. (U2)
"""


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


def _completed_result(*paths: str) -> dict[str, object]:
    changed_paths = list(paths) or ["src/config.py"]
    return {
        "schema_version": 1,
        "status_claim": "completed",
        "summary": "deterministic routing-suite fixture completed",
        "artifacts": [
            {
                "path": path,
                "kind": "file",
                "description": "scripted model-free result",
            }
            for path in changed_paths
        ],
        "changed_paths": changed_paths,
        "checks_run_by_worker": [],
        "assumptions": [],
        "warnings": [],
        "requested_followup": None,
    }


def _worker_contract(monkeypatch: pytest.MonkeyPatch) -> WorkerContract:
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


def _task_envelopes(monkeypatch, prepared, variant_id: str):
    monkeypatch.syspath_prepend(str(B1_SOURCE_ROOT))
    from orchestrator.contract import RunSpec
    from orchestrator.worker import build_task_envelope

    spec = RunSpec.model_validate(
        yaml.safe_load(
            (prepared.workspace / "benchmark-run.yaml").read_text(encoding="utf-8")
        )
    )
    return tuple(
        build_task_envelope(
            task,
            run_id=f"run-routing-{variant_id}-{prepared.fixture.id}",
            task_id=f"task-routing-{variant_id}-{prepared.fixture.id}-{task.key.lower()}",
            attempt_id=(
                f"attempt-routing-{variant_id}-{prepared.fixture.id}-{task.key.lower()}"
            ),
            requirements_version=1,
            timeout_seconds=900,
            remaining_attempts=1,
        )
        for task in spec.tasks
    )


def _fixture_turns(fixture_id: str):
    if fixture_id == "code-change":
        return [(("src/config.py", FIXED_CONFIG),)]
    if fixture_id == "document-read":
        return [(("report.md", SIMPLE_REPORT),)]
    if fixture_id == "sequential-code-change":
        return [
            (("src/normalization.py", NORMALIZATION_SOURCE),),
            (("src/config.py", CONFIG_SOURCE),),
        ]
    if fixture_id == "sequential-document":
        return [
            (("evidence.md", EVIDENCE_REPORT),),
            (("report.md", FINAL_REPORT),),
        ]
    raise AssertionError(f"unexpected routing fixture: {fixture_id}")


def _fake_scripts(tasks, fixture_id: str) -> dict[str, FakeTurnScript]:
    turns = _fixture_turns(fixture_id)
    assert len(tasks) == len(turns)
    return {
        str(task.task_id): FakeTurnScript(
            effects=effects,
            result=_completed_result(*(path for path, _ in effects)),
        )
        for task, effects in zip(tasks, turns, strict=True)
    }


def _b1_fake_fixture(fixture_id: str) -> dict[str, object]:
    return {
        "scenario": "complete",
        "turns": [
            {
                "effects": [
                    {"type": "write_file", "path": path, "content": content}
                    for path, content in effects
                ],
                "result": _completed_result(*(path for path, _ in effects)),
            }
            for effects in _fixture_turns(fixture_id)
        ],
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


def test_model_free_status_and_export_reject_an_incomplete_suite(
    tmp_path: Path,
) -> None:
    plan = _plan()
    experiment_dir = initialize_routing_s1_experiment(tmp_path / "state", plan)

    status = routing_s1_nonlive_status(experiment_dir)
    assert status["validation_status"] == "MODEL_FREE_INCOMPLETE"
    assert status["sealed_cells"] == 0
    assert status["complete"] is False
    assert status["calibration_outcome_issued"] is False
    assert status["route_decision_issued"] is False

    with pytest.raises(RoutingSuiteError, match="every planned Cell"):
        export_routing_s1_nonlive(
            repository_root=REPOSITORY_ROOT,
            suite_path=SUITE_PATH,
            stage_path=STAGE_PATH,
            experiment_dir=experiment_dir,
            results_root=tmp_path / "results",
        )


def test_all_eight_model_free_cells_seal_export_and_detect_tampering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.syspath_prepend(str(B1_SOURCE_ROOT))
    plan = _plan()
    experiment_dir = initialize_routing_s1_experiment(tmp_path / "state", plan)
    contract = _worker_contract(monkeypatch)

    def adapter_factory(cell, prepared):
        tasks = _task_envelopes(monkeypatch, prepared, cell.variant_id)
        if cell.variant_id == "c2":
            return SdkBaselineAdapter(
                SdkBaselineConfig(
                    variant_id="c2",
                    tasks=tasks,
                    contract=contract,
                    runtime=FakeSdkRuntime(
                        prepared.workspace,
                        _fake_scripts(tasks, prepared.fixture.id),
                    ),
                )
            )
        assert cell.variant_id == "b1"
        fake_fixture_path = tmp_path / "fake-fixtures" / f"{cell.cell_id}.json"
        fake_fixture_path.parent.mkdir(parents=True, exist_ok=True)
        fake_fixture_path.write_text(
            json.dumps(_b1_fake_fixture(prepared.fixture.id), ensure_ascii=False),
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

    results = run_all_routing_s1_nonlive_cells(
        repository_root=REPOSITORY_ROOT,
        suite_path=SUITE_PATH,
        stage_path=STAGE_PATH,
        experiment_dir=experiment_dir,
        adapter_factory=adapter_factory,
        benchmark_python=Path(sys.executable),
        git_executable=_git(),
    )
    assert [result.cell_id for result in results] == [cell.cell_id for cell in plan.cells]
    assert all(result.cell_state == "SEALED" for result in results)
    assert all(result.check_success for result in results)
    assert all(result.actual_model_turns == 0 for result in results)

    status = routing_s1_nonlive_status(experiment_dir)
    assert status["validation_status"] == "MODEL_FREE_PASS"
    assert status["sealed_cells"] == status["planned_cells"] == 8
    assert status["actual_model_turns"] == 0
    assert status["calibration_outcome_issued"] is False
    assert status["route_decision_issued"] is False

    exported = export_routing_s1_nonlive(
        repository_root=REPOSITORY_ROOT,
        suite_path=SUITE_PATH,
        stage_path=STAGE_PATH,
        experiment_dir=experiment_dir,
        results_root=tmp_path / "results",
    )
    assert exported["validation_status"] == "MODEL_FREE_PASS"
    export_root = Path(exported["results_root"])
    verified = verify_routing_s1_nonlive_export(export_root)
    assert verified["experiment_id"] == plan.experiment_id
    assert verified["export_sha256"] == exported["export_sha256"]

    summary = json.loads((export_root / "summary.json").read_text(encoding="utf-8"))
    assert len(summary["cells"]) == 8
    assert summary["calibration_outcome_issued"] is False
    assert summary["route_decision_issued"] is False
    assert (export_root / "manifests" / "suite.yaml").read_bytes() == SUITE_PATH.read_bytes()
    assert (export_root / "manifests" / "stage.yaml").read_bytes() == STAGE_PATH.read_bytes()

    first_measurement = export_root / "cells" / plan.cells[0].cell_id / "sealed" / "measurement.json"
    first_measurement.write_bytes(first_measurement.read_bytes() + b" ")
    with pytest.raises(RoutingSuiteError, match="Measurement seal differs"):
        verify_routing_s1_nonlive_export(export_root)
