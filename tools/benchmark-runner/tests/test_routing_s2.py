from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from benchmark_runner.routing_suite import (
    RoutingS1StageManifest,
    RoutingS2StageManifest,
    RoutingStageManifest,
    build_routing_s2_plan,
    build_routing_s2_reverse_live_plan,
    compute_fixture_complexity,
    export_routing_s2_nonlive,
    initialize_routing_s2_experiment,
    routing_s2_nonlive_status,
    run_all_routing_s2_nonlive_cells,
    verify_routing_s2_nonlive_export,
)
from benchmark_runner.adapter import B1AdapterConfig, B1SequentialAdapter
from benchmark_runner.contract import ArtifactIdentity
from benchmark_runner.sdk_baselines import SdkBaselineAdapter, SdkBaselineConfig
from benchmark_runner.sdk_cells import runner_source_sha256
from benchmark_runner.sdk_common import FakeSdkRuntime, FakeTurnScript, WorkerContract
from benchmark_runner.workspace import FrozenFixtureSpec, load_frozen_manifest
from benchmark_runner.s2_posthoc import (
    CONFIG_FIXTURE_ID,
    INCIDENT_FIXTURE_ID,
    PROPERTY_IDS,
    evaluate_posthoc,
)
from benchmark_runner.s2_policy import remaining_b1_retry_resume_reserve, s2_b1_turn_cap
from benchmark_runner.s2_policy import derive_s2_routing_policy
from benchmark_runner.runner import verify_sealed_cell


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_ROOT = REPOSITORY_ROOT / "benchmarks" / "fixtures" / "routing-v1" / "intermediate"
GOLDEN_ROOT = (
    REPOSITORY_ROOT / "benchmarks" / "posthoc-checks" / "sdk-routing-v1" / "s2" / "golden"
)
B1_SOURCE_ROOT = REPOSITORY_ROOT / "stages" / "b1-sequential" / "src"
B1_SCHEMA_ROOT = REPOSITORY_ROOT / "stages" / "b1-sequential" / "schemas" / "v1"


def test_s2_reverse_live_plan_is_one_bound_c2_then_b1_pair() -> None:
    suite_path = (
        REPOSITORY_ROOT / "benchmarks" / "suites" / "sdk-routing-v1" / "suite.yaml"
    )
    plan = build_routing_s2_reverse_live_plan(
        repository_root=REPOSITORY_ROOT,
        suite_path=suite_path,
        stage_path=suite_path.parent / "stages" / "s2-intermediate.yaml",
        runner=ArtifactIdentity(
            artifact_id="benchmark-runner", version="reverse-test", sha256="1" * 64
        ),
        variants=[
            ArtifactIdentity(artifact_id="c2", version="reverse-test", sha256="2" * 64),
            ArtifactIdentity(artifact_id="b1", version="reverse-test", sha256="3" * 64),
        ],
        environment_fingerprint={"runtime": "fake"},
        expansion_profile=INCIDENT_FIXTURE_ID,
        initial_export_identity={
            "experiment_id": "exp_20260808_11111111_1",
            "plan_fingerprint": "1" * 64,
            "export_sha256": "2" * 64,
            "stage_state": "S2_EXPANSION_REQUIRED",
            "source_commit": "3" * 40,
        },
        created_at=datetime(2026, 8, 8, tzinfo=timezone.utc),
    )

    assert [cell.cell_id for cell in plan.cells] == [
        "cell_s2_b_2_c2",
        "cell_s2_b_2_b1",
    ]
    assert [cell.execution_ordinal for cell in plan.cells] == [1, 2]
    assert plan.decision_policy["execution_phase"] == "reverse"
    assert plan.decision_policy["expansion_profile"] == INCIDENT_FIXTURE_ID
    assert plan.decision_policy["base_live_model_turns"] == 6
    assert plan.decision_policy["max_actual_live_model_turns"] == 9


def _copy_fixture(tmp_path: Path, fixture_id: str, *, golden: bool) -> Path:
    workspace = tmp_path / fixture_id
    shutil.copytree(FIXTURE_ROOT / fixture_id, workspace)
    if golden:
        shutil.copytree(GOLDEN_ROOT / fixture_id, workspace, dirs_exist_ok=True)
    return workspace


def _property_status(result: dict[str, object], property_id: str) -> str:
    properties = result["properties"]
    assert isinstance(properties, list)
    return next(
        item["status"]
        for item in properties
        if isinstance(item, dict) and item.get("property_id") == property_id
    )


def _replace(path: Path, old: str, new: str) -> None:
    value = path.read_text(encoding="utf-8")
    assert old in value
    path.write_text(value.replace(old, new, 1), encoding="utf-8", newline="\n")


def test_s2_stage_discriminator_rejects_cross_branch_bytes() -> None:
    s1_path = (
        REPOSITORY_ROOT
        / "benchmarks"
        / "suites"
        / "sdk-routing-v1"
        / "stages"
        / "s1-baseline.yaml"
    )
    s1_value = yaml.safe_load(s1_path.read_text(encoding="utf-8"))
    s1 = RoutingStageManifest.model_validate(s1_value)
    assert isinstance(s1, RoutingS1StageManifest)
    with pytest.raises(ValidationError):
        RoutingS2StageManifest.model_validate(s1_value)

    complexity = {
        "task_count": 3,
        "dependency_depth": 3,
        "dependency_edges": 2,
        "max_fan_in": 1,
        "worker_read_files": 10,
        "worker_read_bytes": 1000,
        "expected_write_files": {"minimum": 6, "maximum": 6},
        "write_modules": 4,
        "check_count": 6,
        "handoff_kind": "declared_multiple",
        "scope_overlap": "disjoint",
        "verification_kind": "post_hoc_property",
        "failure_profile": "compatibility_risk",
        "solution_ambiguity": "low",
    }
    incident_complexity = {
        **complexity,
        "expected_write_files": {"minimum": 7, "maximum": 7},
        "write_modules": 3,
        "failure_profile": "omission_risk",
        "solution_ambiguity": "medium",
    }
    s2_value = {
        "schema_version": 1,
        "stage_id": "s2-intermediate",
        "status": "implementation_candidate",
        "purpose": "profile_routing",
        "fixture_manifests": [
            {
                "path": "benchmarks/manifests/sdk-routing-s2-intermediate.yaml",
                "fixture_ids": [CONFIG_FIXTURE_ID, INCIDENT_FIXTURE_ID],
            }
        ],
        "variants": ["c2", "b1"],
        "baseline_variant": "c2",
        "candidate_variants": ["b1"],
        "profile_aliases": {"a": CONFIG_FIXTURE_ID, "b": INCIDENT_FIXTURE_ID},
        "profiles": [
            {"fixture_id": CONFIG_FIXTURE_ID, "complexity": complexity},
            {"fixture_id": INCIDENT_FIXTURE_ID, "complexity": incident_complexity},
        ],
        "cells": [
            {"cell_id": "cell_s2_a_1_c2", "profile_alias": "a", "fixture_id": CONFIG_FIXTURE_ID, "variant_id": "c2"},
            {"cell_id": "cell_s2_a_1_b1", "profile_alias": "a", "fixture_id": CONFIG_FIXTURE_ID, "variant_id": "b1"},
            {"cell_id": "cell_s2_b_1_b1", "profile_alias": "b", "fixture_id": INCIDENT_FIXTURE_ID, "variant_id": "b1"},
            {"cell_id": "cell_s2_b_1_c2", "profile_alias": "b", "fixture_id": INCIDENT_FIXTURE_ID, "variant_id": "c2"},
        ],
        "base_live_model_turns": 12,
        "b1_retry_resume_reserve_turns": 3,
        "max_actual_live_model_turns": 15,
        "route_decision_allowed": True,
        "allowed_outcomes": [
            "S2_OBSERVATION_READY",
            "S2_POLICY_READY",
            "S2_EXPANSION_REQUIRED",
            "S2_INCONCLUSIVE",
            "S2_STOP",
            "S2_INCOMPLETE",
        ],
    }
    s2 = RoutingStageManifest.model_validate(s2_value)
    assert isinstance(s2, RoutingS2StageManifest)
    with pytest.raises(ValidationError):
        RoutingS1StageManifest.model_validate(s2_value)


def test_s2_frozen_fixture_manifest_matches_live_model_controls() -> None:
    manifest = load_frozen_manifest(
        REPOSITORY_ROOT / "benchmarks" / "manifests" / "sdk-routing-s2-intermediate.yaml"
    )
    assert manifest.status == "frozen_before_execution"
    assert manifest.model == {
        "allowed": "gpt-5.6-terra",
        "auth_method": "chatgpt",
    }


@pytest.mark.parametrize("fixture_id", [CONFIG_FIXTURE_ID, INCIDENT_FIXTURE_ID])
def test_s2_posthoc_pristine_golden_and_label_parity(tmp_path: Path, fixture_id: str) -> None:
    pristine = _copy_fixture(tmp_path / "pristine", fixture_id, golden=False)
    assert evaluate_posthoc(fixture_id, pristine)["property_status"] == "fail"

    workspace = _copy_fixture(tmp_path / "golden", fixture_id, golden=True)
    c2_result = evaluate_posthoc(fixture_id, workspace)
    b1_result = evaluate_posthoc(fixture_id, workspace)
    assert c2_result == b1_result
    assert c2_result["property_status"] == "pass"
    assert [item["property_id"] for item in c2_result["properties"]] == list(
        PROPERTY_IDS[fixture_id]
    )


CONFIG_MUTATIONS = {
    "CFG-P1": (
        "migration/legacy.py",
        '"max_retries": validated["retries"],',
        '"max_retries": validated["retries"] + 1,',
    ),
    "CFG-P2": (
        "runtime/serializer.py",
        "return json.dumps(parse(mapping), ensure_ascii=False, sort_keys=True, separators=(\",\", \":\"))",
        "return json.dumps({**parse(mapping), \"timeout_seconds\": 31}, ensure_ascii=False, sort_keys=True, separators=(\",\", \":\"))",
    ),
    "CFG-P3": (
        "migration/legacy.py",
        "return dict(validated)",
        "return {**validated, \"max_retries\": validated[\"max_retries\"] + 1}",
    ),
    "CFG-P4": (
        "schema/model.py",
        "raise UnknownVersionError(str(version))",
        "raise InvalidTypeError(str(version))",
    ),
    "CFG-P5": (
        "schema/model.py",
        "normalized = _normalize(mapping)",
        "mapping.pop(\"endpoint\", None)\n    normalized = _normalize(mapping)",
    ),
}


@pytest.mark.parametrize("property_id", list(CONFIG_MUTATIONS))
def test_config_property_mutation_is_rejected(tmp_path: Path, property_id: str) -> None:
    workspace = _copy_fixture(tmp_path, CONFIG_FIXTURE_ID, golden=True)
    relative, old, new = CONFIG_MUTATIONS[property_id]
    _replace(workspace / relative, old, new)
    result = evaluate_posthoc(CONFIG_FIXTURE_ID, workspace)
    assert result["property_status"] == "fail"
    assert _property_status(result, property_id) == "fail"


def _mutate_incident(workspace: Path, property_id: str) -> None:
    if property_id == "INC-P1":
        path = workspace / "analysis/evidence-ledger.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["evidence"][0]["exact_excerpt"] += " changed"
    elif property_id == "INC-P2":
        path = workspace / "timeline/events.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["events"][0]["evidence_ids"] = ["e-a3"]
    elif property_id == "INC-P3":
        path = workspace / "report/action-plan.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["actions"][0]["reference_ids"] = ["dangling"]
    elif property_id == "INC-P4":
        path = workspace / "report/final-report.md"
        _replace(path, "Deployment of release 42 began", "Release 42 deployment began")
        return
    else:
        path = workspace / "report/final-report.md"
        _replace(path, "verify: e-c2,u-approval", "verify: e-c2")
        return
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
        newline="\n",
    )


@pytest.mark.parametrize("property_id", list(PROPERTY_IDS[INCIDENT_FIXTURE_ID]))
def test_incident_property_mutation_is_rejected(tmp_path: Path, property_id: str) -> None:
    workspace = _copy_fixture(tmp_path, INCIDENT_FIXTURE_ID, golden=True)
    _mutate_incident(workspace, property_id)
    result = evaluate_posthoc(INCIDENT_FIXTURE_ID, workspace)
    assert result["property_status"] == "fail"
    assert _property_status(result, property_id) == "fail"


class _Identity:
    variant_id = "b1"


class _VariantMetrics:
    def __init__(self, retry: int, resume: int) -> None:
        self.values = {"b1_retry_count": retry, "b1_resume_count": resume}


class _ReserveMeasurement:
    def __init__(self, retry: int, resume: int) -> None:
        self.identity = _Identity()
        self.variant_metrics = _VariantMetrics(retry, resume)


def test_s2_retry_reserve_is_independent_and_never_recycles_early_turns() -> None:
    measurements = [_ReserveMeasurement(1, 0), _ReserveMeasurement(0, 1)]
    assert remaining_b1_retry_resume_reserve(measurements) == 1  # type: ignore[arg-type]
    assert s2_b1_turn_cap(measurements) == 4  # type: ignore[arg-type]


def _git(repository: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _create_s2_source_repository(tmp_path: Path) -> tuple[Path, Path, Path]:
    source = tmp_path / "source"
    for fixture_id in (CONFIG_FIXTURE_ID, INCIDENT_FIXTURE_ID):
        target = source / "benchmarks" / "fixtures" / "routing-v1" / "intermediate" / fixture_id
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(FIXTURE_ROOT / fixture_id, target)
    _git(source, "init", "-q", "-b", "main")
    _git(source, "config", "user.name", "routing-s2-test")
    _git(source, "config", "user.email", "routing-s2@test.invalid")
    _git(source, "config", "core.autocrlf", "false")
    _git(source, "config", "core.longpaths", "true")
    _git(source, "add", "-A")
    _git(source, "commit", "-q", "-m", "fixture source")
    commit = _git(source, "rev-parse", "HEAD")
    fixture_specs: list[FrozenFixtureSpec] = []
    for fixture_id, success_check in (
        (CONFIG_FIXTURE_ID, "s2_config_acceptance"),
        (INCIDENT_FIXTURE_ID, "s2_incident_acceptance"),
    ):
        relative = f"benchmarks/fixtures/routing-v1/intermediate/{fixture_id}"
        fixture_specs.append(
            FrozenFixtureSpec(
                id=fixture_id,
                path=relative,
                commit=commit,
                git_tree=_git(source, "rev-parse", f"HEAD:{relative}"),
                success_check=success_check,
            )
        )
    manifest_path = source / "benchmarks" / "manifests" / "sdk-routing-s2-intermediate.yaml"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "status": "implementation_candidate",
                "frozen_at": "model_free_test",
                "fixtures": [item.model_dump(mode="json") for item in fixture_specs],
                "variants": ["c2", "b1"],
                "repetitions": 1,
                "model": {"name": "fake"},
                "budgets": {"actual_model_turns": 0},
                "human_intervention": {"allowed": False},
                "metrics": ["check_success", "property_status"],
                "unknown_usage_rule": "preserve",
                "failure_rule": "seal_each_variant",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
        newline="\n",
    )
    complexities = {}
    for fixture in fixture_specs:
        config = fixture.id == CONFIG_FIXTURE_ID
        complexities[fixture.id] = compute_fixture_complexity(
            source,
            fixture,
            expected_write_files={"minimum": 6 if config else 7, "maximum": 6 if config else 7},
            verification_kind="post_hoc_property",
            failure_profile="compatibility_risk" if config else "omission_risk",
            solution_ambiguity="low" if config else "medium",
        )
    stage_path = source / "benchmarks" / "suites" / "sdk-routing-v1" / "stages" / "s2-intermediate.yaml"
    stage_path.parent.mkdir(parents=True, exist_ok=True)
    stage_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "stage_id": "s2-intermediate",
                "status": "implementation_candidate",
                "purpose": "profile_routing",
                "fixture_manifests": [{"path": "benchmarks/manifests/sdk-routing-s2-intermediate.yaml", "fixture_ids": [CONFIG_FIXTURE_ID, INCIDENT_FIXTURE_ID]}],
                "variants": ["c2", "b1"],
                "baseline_variant": "c2",
                "candidate_variants": ["b1"],
                "profile_aliases": {"a": CONFIG_FIXTURE_ID, "b": INCIDENT_FIXTURE_ID},
                "profiles": [{"fixture_id": fixture_id, "complexity": complexities[fixture_id].model_dump(mode="json")} for fixture_id in (CONFIG_FIXTURE_ID, INCIDENT_FIXTURE_ID)],
                "cells": [
                    {"cell_id": "cell_s2_a_1_c2", "profile_alias": "a", "fixture_id": CONFIG_FIXTURE_ID, "variant_id": "c2"},
                    {"cell_id": "cell_s2_a_1_b1", "profile_alias": "a", "fixture_id": CONFIG_FIXTURE_ID, "variant_id": "b1"},
                    {"cell_id": "cell_s2_b_1_b1", "profile_alias": "b", "fixture_id": INCIDENT_FIXTURE_ID, "variant_id": "b1"},
                    {"cell_id": "cell_s2_b_1_c2", "profile_alias": "b", "fixture_id": INCIDENT_FIXTURE_ID, "variant_id": "c2"},
                ],
                "base_live_model_turns": 12,
                "b1_retry_resume_reserve_turns": 3,
                "max_actual_live_model_turns": 15,
                "route_decision_allowed": True,
                "allowed_outcomes": ["S2_OBSERVATION_READY", "S2_POLICY_READY", "S2_EXPANSION_REQUIRED", "S2_INCONCLUSIVE", "S2_STOP", "S2_INCOMPLETE"],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
        newline="\n",
    )
    suite_path = stage_path.parents[1] / "suite.yaml"
    suite_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "suite_id": "sdk-routing-v1",
                "design_revision": 3,
                "status": "implementation_candidate",
                "stages": [
                    {"stage_id": "s1-baseline", "path": "benchmarks/suites/sdk-routing-v1/stages/s1-baseline.yaml"},
                    {"stage_id": "s2-intermediate", "path": "benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml"},
                ],
                "live_turn_ceiling_including_pilot": 34,
                "auth_method": "chatgpt",
                "api_key_policy": "forbidden",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
        newline="\n",
    )
    return source, suite_path, stage_path


def _completed_result(paths: list[str]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status_claim": "completed",
        "summary": "deterministic S2 model-free result",
        "artifacts": [{"path": path, "kind": "file", "description": "golden model-free output"} for path in paths],
        "changed_paths": paths,
        "checks_run_by_worker": [],
        "assumptions": [],
        "warnings": [],
        "requested_followup": None,
    }


def _golden_turns(fixture_id: str) -> list[tuple[tuple[str, str], ...]]:
    groups = (
        [("schema/errors.py", "schema/model.py"), ("migration/legacy.py", "runtime/parser.py"), ("runtime/serializer.py", "cli/config_cli.py")]
        if fixture_id == CONFIG_FIXTURE_ID
        else [("analysis/evidence-ledger.json", "analysis/uncertainties.json"), ("timeline/events.json", "timeline/hypotheses.json"), ("report/final-report.md", "report/claims.json", "report/action-plan.json")]
    )
    return [
        tuple(
            (relative, (GOLDEN_ROOT / fixture_id / relative).read_text(encoding="utf-8"))
            for relative in group
        )
        for group in groups
    ]


def test_s2_fake_four_cell_plan_judge_property_seal_export(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, suite_path, stage_path = _create_s2_source_repository(tmp_path)
    runner_sha = runner_source_sha256()
    plan = build_routing_s2_plan(
        repository_root=source,
        suite_path=suite_path,
        stage_path=stage_path,
        runner=ArtifactIdentity(artifact_id="benchmark-runner", version="s2-test", sha256=runner_sha),
        variants=[
            ArtifactIdentity(artifact_id="c2", version="s2-test", sha256="2" * 64),
            ArtifactIdentity(artifact_id="b1", version="s2-test", sha256="3" * 64),
        ],
        environment_fingerprint={"runtime": "fake", "actual_model_turns": "0"},
        created_at=datetime(2026, 8, 8, tzinfo=timezone.utc),
    )
    assert [cell.cell_id for cell in plan.cells] == [
        "cell_s2_a_1_c2", "cell_s2_a_1_b1", "cell_s2_b_1_b1", "cell_s2_b_1_c2"
    ]
    assert plan.decision_policy["base_live_model_turns"] == 12
    assert plan.decision_policy["max_actual_live_model_turns"] == 15
    experiment_dir = initialize_routing_s2_experiment(tmp_path / "state", plan)
    monkeypatch.syspath_prepend(str(B1_SOURCE_ROOT))
    from orchestrator.contract import RunSpec
    from orchestrator.worker import build_task_envelope, render_worker_prompt, result_schema, task_semantics_sha256, validate_result

    worker_contract = WorkerContract(
        render_prompt=render_worker_prompt,
        result_schema=result_schema,
        validate_result=lambda value: validate_result(value).model_dump(mode="json"),
        semantics_sha256=task_semantics_sha256,
    )

    def adapter_factory(cell, prepared):
        spec = RunSpec.model_validate(yaml.safe_load((prepared.workspace / "benchmark-run.yaml").read_text(encoding="utf-8")))
        tasks = tuple(
            build_task_envelope(
                task,
                run_id=f"run-{cell.cell_id}",
                task_id=f"task-{cell.cell_id}-{task.key.lower()}",
                attempt_id=f"attempt-{cell.cell_id}-{task.key.lower()}",
                requirements_version=1,
                timeout_seconds=900,
                remaining_attempts=1,
            )
            for task in spec.tasks
        )
        turns = _golden_turns(cell.fixture_id)
        if cell.variant_id == "c2":
            scripts = {
                str(task.task_id): FakeTurnScript(
                    effects=effects,
                    result=_completed_result([path for path, _ in effects]),
                )
                for task, effects in zip(tasks, turns, strict=True)
            }
            return SdkBaselineAdapter(
                SdkBaselineConfig(
                    variant_id="c2",
                    tasks=tasks,
                    contract=worker_contract,
                    runtime=FakeSdkRuntime(prepared.workspace, scripts),
                )
            )
        fake_path = tmp_path / "fake" / f"{cell.cell_id}.json"
        fake_path.parent.mkdir(parents=True, exist_ok=True)
        fake_path.write_text(
            json.dumps(
                {
                    "scenario": "complete",
                    "turns": [
                        {
                            "effects": [{"type": "write_file", "path": path, "content": content} for path, content in effects],
                            "result": _completed_result([path for path, _ in effects]),
                        }
                        for effects in turns
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return B1SequentialAdapter(
            B1AdapterConfig(
                command_prefix=(sys.executable, "-m", "orchestrator"),
                project=prepared.workspace,
                run_spec=prepared.workspace / "benchmark-run.yaml",
                state_root=tmp_path / "b1-state" / cell.cell_id,
                schema_root=B1_SCHEMA_ROOT,
                runtime="fake",
                fake_fixture=fake_path,
            )
        )

    results = run_all_routing_s2_nonlive_cells(
        repository_root=source,
        suite_path=suite_path,
        stage_path=stage_path,
        experiment_dir=experiment_dir,
        adapter_factory=adapter_factory,
        benchmark_python=Path(sys.executable),
        git_executable=Path(shutil.which("git") or "git"),
    )
    assert len(results) == 4
    assert all(result.check_success for result in results)
    status = routing_s2_nonlive_status(experiment_dir)
    assert status["validation_status"] == "MODEL_FREE_PASS"
    assert status["all_properties_passed"] is True
    assert status["actual_model_turns"] == 0
    live_shaped_measurements = []
    posthoc_results = {}
    for cell in plan.cells:
        cell_dir = experiment_dir / "cells" / cell.cell_id
        measurement = verify_sealed_cell(cell_dir)
        values = dict(measurement.variant_metrics.values)
        values["actual_model_turns"] = 3
        values["model_active_seconds"] = 1.0
        live_shaped_measurements.append(
            measurement.model_copy(
                update={
                    "resource": measurement.resource.model_copy(
                        update={
                            "turn_count": measurement.resource.turn_count.model_copy(
                                update={"value": 3}
                            )
                        }
                    ),
                    "variant_metrics": measurement.variant_metrics.model_copy(
                        update={"values": values}
                    ),
                }
            )
        )
        posthoc_results[cell.cell_id] = json.loads(
            (cell_dir / "judge" / "posthoc" / "result.json").read_text(encoding="utf-8")
        )
    policy = derive_s2_routing_policy(
        plan=plan,
        measurements=live_shaped_measurements,
        sealed_cell_ids={cell.cell_id for cell in plan.cells},
        posthoc_results=posthoc_results,
    )
    assert policy["stage_state"] == "S2_OBSERVATION_READY"
    assert {
        value["state"] for value in policy["profiles"].values()
    } == {"C2_SUFFICIENT_OBSERVED_SINGLE_PAIR"}
    assert policy["global_b1_default_issued"] is False
    assert policy["runner_identity"] == plan.runner.model_dump(mode="json")
    assert policy["checker_identities"] == plan.decision_policy["posthoc_checks"]
    assert len(policy["source_identity"]) == 1
    for measurement in live_shaped_measurements:
        if measurement.identity.variant_id == "b1":
            values = measurement.variant_metrics.values
            assert values["dual_outcome_status"] == "not_applicable"
            assert values["attempt_level_cost"] == "not_available"
            assert "first_attempt_outcome" not in values
            assert "full_orchestrated_outcome" not in values

    def failed_c2(measurement):
        values = dict(measurement.variant_metrics.values)
        values["property_status"] = "fail"
        return measurement.model_copy(
            update={
                "outcome": measurement.outcome.model_copy(
                    update={"failure_kind": "check_failed", "check_success": False}
                ),
                "variant_metrics": measurement.variant_metrics.model_copy(
                    update={"values": values}
                ),
            }
        )

    def b1_with_control(measurement):
        resource = measurement.resource.model_copy(
            update={
                "turn_count": measurement.resource.turn_count.model_copy(
                    update={"value": 4}
                )
            }
        )
        values = dict(measurement.variant_metrics.values)
        values.update(
            {
                "actual_model_turns": 4,
                "b1_retry_count": 1,
                "b1_intermediate_check_changed_result": True,
                "dual_outcome_status": "reported",
                "attempt_level_cost": "not_available",
                "first_attempt_outcome": [
                    {
                        "task_key": f"T{number}",
                        "state": "failed" if number == 1 else "completed",
                        "failure_kind": "check_failed" if number == 1 else None,
                    }
                    for number in range(1, 4)
                ],
                "full_orchestrated_outcome": {
                    "state": measurement.outcome.state,
                    "failure_kind": measurement.outcome.failure_kind,
                    "check_success": measurement.outcome.check_success,
                    "turn_count": 4,
                    "token_usage_status": measurement.resource.token_usage.status.value,
                    "token_usage": measurement.resource.token_usage.value,
                },
            }
        )
        return measurement.model_copy(
            update={
                "resource": resource,
                "variant_metrics": measurement.variant_metrics.model_copy(
                    update={"values": values}
                ),
            }
        )

    a_c2_index = next(
        index
        for index, item in enumerate(live_shaped_measurements)
        if item.identity.cell_id == "cell_s2_a_1_c2"
    )
    failed_initial = list(live_shaped_measurements)
    failed_initial[a_c2_index] = failed_c2(failed_initial[a_c2_index])
    failed_posthoc = json.loads(json.dumps(posthoc_results))
    failed_posthoc["cell_s2_a_1_c2"]["property_status"] = "fail"
    failed_posthoc["cell_s2_a_1_c2"]["properties"][0]["status"] = "fail"
    expansion = derive_s2_routing_policy(
        plan=plan,
        measurements=failed_initial,
        sealed_cell_ids={cell.cell_id for cell in plan.cells},
        posthoc_results=failed_posthoc,
    )
    assert expansion["stage_state"] == "S2_EXPANSION_REQUIRED"
    assert (
        expansion["profiles"][CONFIG_FIXTURE_ID]["state"]
        == "EXPANSION_REQUIRED"
    )

    controlled_initial = list(failed_initial)
    a_b1_index = next(
        index
        for index, item in enumerate(controlled_initial)
        if item.identity.cell_id == "cell_s2_a_1_b1"
    )
    controlled_initial[a_b1_index] = b1_with_control(
        controlled_initial[a_b1_index]
    )
    initial_c2_cell = next(
        cell for cell in plan.cells if cell.cell_id == "cell_s2_a_1_c2"
    )
    initial_b1_cell = next(
        cell for cell in plan.cells if cell.cell_id == "cell_s2_a_1_b1"
    )
    reverse_b1_cell = initial_b1_cell.model_copy(
        update={
            "cell_id": "cell_s2_a_2_b1",
            "block_id": "block_s2_a_2",
            "execution_ordinal": 1,
        }
    )
    reverse_c2_cell = initial_c2_cell.model_copy(
        update={
            "cell_id": "cell_s2_a_2_c2",
            "block_id": "block_s2_a_2",
            "execution_ordinal": 2,
        }
    )
    reverse_plan = plan.model_copy(
        update={
            "experiment_id": "exp_20260808_44444444_1",
            "plan_fingerprint": "4" * 64,
            "cells": [reverse_b1_cell, reverse_c2_cell],
        }
    )

    def bind_reverse(measurement, cell):
        return measurement.model_copy(
            update={
                "identity": measurement.identity.model_copy(
                    update={
                        "experiment_id": reverse_plan.experiment_id,
                        "block_id": cell.block_id,
                        "cell_id": cell.cell_id,
                        "execution_ordinal": cell.execution_ordinal,
                    }
                )
            }
        )

    reverse_b1 = bind_reverse(
        b1_with_control(live_shaped_measurements[a_b1_index]),
        reverse_b1_cell,
    )
    reverse_c2 = bind_reverse(
        failed_c2(live_shaped_measurements[a_c2_index]),
        reverse_c2_cell,
    )
    route_posthoc = json.loads(json.dumps(failed_posthoc))
    route_posthoc[reverse_b1_cell.cell_id] = json.loads(
        json.dumps(posthoc_results["cell_s2_a_1_b1"])
    )
    route_posthoc[reverse_c2_cell.cell_id] = json.loads(
        json.dumps(failed_posthoc["cell_s2_a_1_c2"])
    )
    route_measurements = [*controlled_initial, reverse_b1, reverse_c2]
    routed = derive_s2_routing_policy(
        plan=plan,
        additional_plans=(reverse_plan,),
        measurements=route_measurements,
        sealed_cell_ids={item.identity.cell_id for item in route_measurements},
        posthoc_results=route_posthoc,
    )
    assert routed["stage_state"] == "S2_POLICY_READY"
    assert (
        routed["profiles"][CONFIG_FIXTURE_ID]["state"]
        == "ROUTE_B1_PROVISIONAL"
    )
    assert routed["global_b1_default_issued"] is False
    exported = export_routing_s2_nonlive(
        repository_root=source,
        suite_path=suite_path,
        stage_path=stage_path,
        experiment_dir=experiment_dir,
        results_root=tmp_path / "results",
    )
    verified = verify_routing_s2_nonlive_export(Path(exported["results_root"]))
    assert verified["export_sha256"] == exported["export_sha256"]
