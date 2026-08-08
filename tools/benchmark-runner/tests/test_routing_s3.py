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

from benchmark_runner.adapter import B1AdapterConfig, B1SequentialAdapter
from benchmark_runner.contract import ArtifactIdentity
from benchmark_runner.routing_suite import (
    RoutingS2StageManifest,
    RoutingS3StageManifest,
    RoutingStageManifest,
    build_routing_s3_plan,
    build_routing_s3_reverse_live_plan,
    compute_fixture_complexity,
    export_routing_s3_nonlive,
    initialize_routing_s3_experiment,
    routing_s3_nonlive_status,
    run_all_routing_s3_nonlive_cells,
    verify_routing_s3_nonlive_export,
)
from benchmark_runner.runner import verify_sealed_cell
from benchmark_runner.routing_live import _plan_stage_contract
from benchmark_runner.s2_policy import (
    derive_s3_routing_policy,
    remaining_s3_b1_retry_resume_reserve,
    s3_b1_turn_cap,
)
from benchmark_runner.s3_posthoc import (
    COMPATIBILITY_FIXTURE_ID,
    INCIDENT_FIXTURE_ID,
    PROPERTY_IDS,
    evaluate_posthoc,
    run_posthoc_subprocess,
)
from benchmark_runner.sdk_baselines import SdkBaselineAdapter, SdkBaselineConfig
from benchmark_runner.sdk_cells import runner_source_sha256
from benchmark_runner.sdk_common import FakeSdkRuntime, FakeTurnScript, WorkerContract
from benchmark_runner.workspace import FrozenFixtureSpec


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_ROOT = (
    REPOSITORY_ROOT / "benchmarks" / "fixtures" / "routing-v1" / "complex-high-risk"
)
GOLDEN_ROOT = (
    REPOSITORY_ROOT / "benchmarks" / "posthoc-checks" / "sdk-routing-v1" / "s3" / "golden"
)
B1_SOURCE_ROOT = REPOSITORY_ROOT / "stages" / "b1-sequential" / "src"
B1_SCHEMA_ROOT = REPOSITORY_ROOT / "stages" / "b1-sequential" / "schemas" / "v1"


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


@pytest.mark.parametrize("fixture_id", [COMPATIBILITY_FIXTURE_ID, INCIDENT_FIXTURE_ID])
def test_s3_posthoc_pristine_golden_parity_and_subprocess(
    tmp_path: Path,
    fixture_id: str,
) -> None:
    pristine = _copy_fixture(tmp_path / "pristine", fixture_id, golden=False)
    assert evaluate_posthoc(fixture_id, pristine)["property_status"] == "fail"
    workspace = _copy_fixture(tmp_path / "golden", fixture_id, golden=True)
    c2 = evaluate_posthoc(fixture_id, workspace)
    b1 = evaluate_posthoc(fixture_id, workspace)
    assert c2 == b1
    assert c2["property_status"] == "pass"
    assert [item["property_id"] for item in c2["properties"]] == list(
        PROPERTY_IDS[fixture_id]
    )
    isolated = run_posthoc_subprocess(
        repository_root=REPOSITORY_ROOT,
        benchmark_python=Path(sys.executable),
        fixture_id=fixture_id,
        workspace=workspace,
    )
    assert isolated == c2
    assert set(isolated) == {
        "fixture_id",
        "checker_sha256",
        "property_status",
        "properties",
    }


COMPAT_MUTATIONS = {
    "HCR-P1": (
        "schema/model.py",
        'PUBLIC_FIELDS = ("endpoint", "max_retries", "timeout_seconds", "mode", "version")',
        'PUBLIC_FIELDS = ("endpoint", "timeout_seconds", "max_retries", "mode", "version")',
    ),
    "HCR-P2": (
        "migration/upgrade.py",
        "return validate(value)",
        'value["max_retries"] += 1\n    return validate(value)',
    ),
    "HCR-P3": (
        "integration/adapter.py",
        "return parse(payload)",
        'return {**parse(payload), "timeout_seconds": 999}',
    ),
    "HCR-P4": (
        "compat/legacy_api.py",
        "return normalize_legacy(payload)",
        'return {**normalize_legacy(payload), "mode": "fast"}',
    ),
    "HCR-P5a": (
        "migration/upgrade.py",
        "value = dict(payload)",
        'value = dict(payload)\n    if "version" in value and not any(alias in value for alias in ALIASES):\n        value["max_retries"] += 1',
    ),
    "HCR-P5b": (
        "runtime/serializer.py",
        "return validate(payload)",
        'return {**validate(payload), "timeout_seconds": validate(payload)["timeout_seconds"] + 1}',
    ),
    "HCR-P6": (
        "benchmark-run.yaml",
        'write_scope: ["schema/model.py", "schema/errors.py"]',
        'write_scope: ["schema/model.py", "schema/errors.py", "README.md"]',
    ),
}


@pytest.mark.parametrize("property_id", list(COMPAT_MUTATIONS))
def test_s3_compatibility_property_mutation_is_rejected(
    tmp_path: Path,
    property_id: str,
) -> None:
    workspace = _copy_fixture(tmp_path, COMPATIBILITY_FIXTURE_ID, golden=True)
    relative, old, new = COMPAT_MUTATIONS[property_id]
    _replace(workspace / relative, old, new)
    result = evaluate_posthoc(COMPATIBILITY_FIXTURE_ID, workspace)
    assert result["property_status"] == "fail"
    assert _property_status(result, property_id) == "fail"


def _mutate_incident(workspace: Path, property_id: str) -> None:
    if property_id == "HCI-P1":
        path = workspace / "analysis/evidence-ledger.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["evidence"][0]["exact_excerpt"] += " changed"
    elif property_id == "HCI-P2":
        path = workspace / "analysis/evidence-ledger.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["evidence"] = [item for item in payload["evidence"] if item["evidence_id"] != "E9"]
    elif property_id == "HCI-P3":
        path = workspace / "timeline/conflict-groups.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["groups"][0]["evidence_ids"] = ["E3", "E4"]
    elif property_id == "HCI-P4":
        path = workspace / "analysis/alternative-matrix.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["alternatives"] = [payload["alternatives"][0]]
    elif property_id == "HCI-P5":
        path = workspace / "report/claims.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["claims"][0]["status"] = "uncertain"
    else:
        path = workspace / "report/action-plan.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["actions"][0]["reference_ids"] = ["DANGLING"]
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
        newline="\n",
    )


@pytest.mark.parametrize("property_id", list(PROPERTY_IDS[INCIDENT_FIXTURE_ID]))
def test_s3_incident_property_mutation_is_rejected(
    tmp_path: Path,
    property_id: str,
) -> None:
    workspace = _copy_fixture(tmp_path, INCIDENT_FIXTURE_ID, golden=True)
    _mutate_incident(workspace, property_id)
    result = evaluate_posthoc(INCIDENT_FIXTURE_ID, workspace)
    assert result["property_status"] == "fail"
    assert _property_status(result, property_id) == "fail"


def _complexity_payload() -> dict[str, object]:
    return {
        "task_count": 4,
        "dependency_depth": 4,
        "dependency_edges": 6,
        "max_fan_in": 3,
        "worker_read_files": 1,
        "worker_read_bytes": 1,
        "expected_write_files": {"minimum": 10, "maximum": 10},
        "write_modules": 6,
        "check_count": 8,
        "handoff_kind": "declared_multiple",
        "scope_overlap": "partial",
        "verification_kind": "post_hoc_property",
        "failure_profile": "compatibility_risk",
        "solution_ambiguity": "high",
    }


def _s3_stage_value() -> dict[str, object]:
    compatibility = _complexity_payload()
    incident = {
        **_complexity_payload(),
        "expected_write_files": {"minimum": 9, "maximum": 9},
        "write_modules": 3,
        "scope_overlap": "disjoint",
        "failure_profile": "omission_risk",
    }
    return {
        "schema_version": 1,
        "stage_id": "s3-complex-high-risk",
        "status": "implementation_candidate",
        "purpose": "complex_high_risk_routing",
        "fixture_manifests": [{"path": "benchmarks/manifests/sdk-routing-s3-complex-high-risk.yaml", "fixture_ids": [COMPATIBILITY_FIXTURE_ID, INCIDENT_FIXTURE_ID]}],
        "variants": ["c2", "b1"],
        "baseline_variant": "c2",
        "candidate_variants": ["b1"],
        "profile_aliases": {"a": COMPATIBILITY_FIXTURE_ID, "b": INCIDENT_FIXTURE_ID},
        "profiles": [{"fixture_id": COMPATIBILITY_FIXTURE_ID, "complexity": compatibility}, {"fixture_id": INCIDENT_FIXTURE_ID, "complexity": incident}],
        "cells": [
            {"cell_id": "cell_s3_a_1_c2", "profile_alias": "a", "fixture_id": COMPATIBILITY_FIXTURE_ID, "variant_id": "c2"},
            {"cell_id": "cell_s3_a_1_b1", "profile_alias": "a", "fixture_id": COMPATIBILITY_FIXTURE_ID, "variant_id": "b1"},
            {"cell_id": "cell_s3_b_1_b1", "profile_alias": "b", "fixture_id": INCIDENT_FIXTURE_ID, "variant_id": "b1"},
            {"cell_id": "cell_s3_b_1_c2", "profile_alias": "b", "fixture_id": INCIDENT_FIXTURE_ID, "variant_id": "c2"},
        ],
        "base_live_model_turns": 16,
        "b1_retry_resume_reserve_turns_per_profile": 2,
        "b1_retry_resume_reserve_turns": 4,
        "max_actual_live_model_turns": 20,
        "route_decision_allowed": True,
        "allowed_outcomes": ["S3_OBSERVATION_READY", "S3_POLICY_READY", "S3_REPLICATION_REQUIRED", "S3_INCONCLUSIVE", "S3_STOP", "S3_INCOMPLETE"],
    }


def test_s3_stage_discriminator_and_exact_budget_contract() -> None:
    stage = RoutingStageManifest.model_validate(_s3_stage_value())
    assert isinstance(stage, RoutingS3StageManifest)
    with pytest.raises(ValidationError):
        RoutingS2StageManifest.model_validate(_s3_stage_value())
    invalid = _s3_stage_value()
    invalid["max_actual_live_model_turns"] = 21
    with pytest.raises(ValidationError):
        RoutingStageManifest.model_validate(invalid)


class _ReserveIdentity:
    variant_id = "b1"

    def __init__(self, fixture_id: str) -> None:
        self.fixture_id = fixture_id


class _ReserveMetrics:
    def __init__(self, retry: int, resume: int) -> None:
        self.values = {"b1_retry_count": retry, "b1_resume_count": resume}


class _ReserveMeasurement:
    def __init__(self, fixture_id: str, retry: int, resume: int) -> None:
        self.identity = _ReserveIdentity(fixture_id)
        self.variant_metrics = _ReserveMetrics(retry, resume)


def test_s3_retry_reserve_is_profile_local() -> None:
    values = [
        _ReserveMeasurement(COMPATIBILITY_FIXTURE_ID, 1, 0),
        _ReserveMeasurement(INCIDENT_FIXTURE_ID, 0, 2),
    ]
    assert remaining_s3_b1_retry_resume_reserve(values, fixture_id=COMPATIBILITY_FIXTURE_ID) == 1  # type: ignore[arg-type]
    assert remaining_s3_b1_retry_resume_reserve(values, fixture_id=INCIDENT_FIXTURE_ID) == 0  # type: ignore[arg-type]
    assert s3_b1_turn_cap(values, fixture_id=COMPATIBILITY_FIXTURE_ID) == 5  # type: ignore[arg-type]


def test_s3_reverse_plan_requires_its_own_gate_and_opposite_order(tmp_path: Path) -> None:
    source, suite_path, stage_path = _create_s3_source_repository(tmp_path)
    for path in (
        suite_path,
        stage_path,
        source / "benchmarks" / "manifests" / "sdk-routing-s3-complex-high-risk.yaml",
    ):
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
        value["status"] = "frozen_before_execution"
        if path.name == "sdk-routing-s3-complex-high-risk.yaml":
            value["model"] = {"allowed": "gpt-5.6-terra", "auth_method": "chatgpt"}
        path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8", newline="\n")
    common = {
        "repository_root": source,
        "suite_path": suite_path,
        "stage_path": stage_path,
        "runner": ArtifactIdentity(artifact_id="benchmark-runner", version="s3-reverse", sha256="1" * 64),
        "variants": [
            ArtifactIdentity(artifact_id="c2", version="s3-reverse", sha256="2" * 64),
            ArtifactIdentity(artifact_id="b1", version="s3-reverse", sha256="3" * 64),
        ],
        "environment_fingerprint": {"runtime": "fake"},
        "expansion_profile": COMPATIBILITY_FIXTURE_ID,
        "created_at": datetime(2026, 8, 8, tzinfo=timezone.utc),
    }
    identity = {
        "experiment_id": "exp_20260808_11111111_1",
        "plan_fingerprint": "4" * 64,
        "export_sha256": "5" * 64,
        "stage_state": "S3_REPLICATION_REQUIRED",
        "source_commit": "6" * 40,
    }
    plan = build_routing_s3_reverse_live_plan(
        **common,
        initial_export_identity=identity,
    )
    assert [cell.cell_id for cell in plan.cells] == [
        "cell_s3_a_2_b1",
        "cell_s3_a_2_c2",
    ]
    assert _plan_stage_contract(plan) == {
        "stage_id": "s3-complex-high-risk",
        "label": "S3 reverse",
        "track": "sdk_routing_s3_live_reverse",
        "route_decision_allowed": True,
        "stage_relative": "benchmarks/suites/sdk-routing-v1/stages/s3-complex-high-risk.yaml",
        "planned_cells": 2,
        "base_turns": 8,
        "max_turns": 10,
        "state_root_limit": 40,
        "reverse_gate_state": "S3_REPLICATION_REQUIRED",
    }
    wrong = {**identity, "stage_state": "S2_EXPANSION_REQUIRED"}
    with pytest.raises(Exception, match="initial export identity is invalid"):
        build_routing_s3_reverse_live_plan(
            **common,
            initial_export_identity=wrong,
        )


def _git(repository: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _create_s3_source_repository(tmp_path: Path) -> tuple[Path, Path, Path]:
    source = tmp_path / "source"
    for fixture_id in (COMPATIBILITY_FIXTURE_ID, INCIDENT_FIXTURE_ID):
        target = source / "benchmarks" / "fixtures" / "routing-v1" / "complex-high-risk" / fixture_id
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(FIXTURE_ROOT / fixture_id, target)
    _git(source, "init", "-q", "-b", "main")
    _git(source, "config", "user.name", "routing-s3-test")
    _git(source, "config", "user.email", "routing-s3@test.invalid")
    _git(source, "config", "core.autocrlf", "false")
    _git(source, "config", "core.longpaths", "true")
    _git(source, "add", "-A")
    _git(source, "commit", "-q", "-m", "fixture source")
    commit = _git(source, "rev-parse", "HEAD")
    fixture_specs: list[FrozenFixtureSpec] = []
    for fixture_id, success_check in (
        (COMPATIBILITY_FIXTURE_ID, "s3_compat_acceptance"),
        (INCIDENT_FIXTURE_ID, "s3_incident_acceptance"),
    ):
        relative = f"benchmarks/fixtures/routing-v1/complex-high-risk/{fixture_id}"
        fixture_specs.append(
            FrozenFixtureSpec(
                id=fixture_id,
                path=relative,
                commit=commit,
                git_tree=_git(source, "rev-parse", f"HEAD:{relative}"),
                success_check=success_check,
            )
        )
    manifest_path = source / "benchmarks" / "manifests" / "sdk-routing-s3-complex-high-risk.yaml"
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
        is_compat = fixture.id == COMPATIBILITY_FIXTURE_ID
        complexities[fixture.id] = compute_fixture_complexity(
            source,
            fixture,
            expected_write_files={"minimum": 10 if is_compat else 9, "maximum": 10 if is_compat else 9},
            verification_kind="post_hoc_property",
            failure_profile="compatibility_risk" if is_compat else "omission_risk",
            solution_ambiguity="high",
        )
    stage_value = _s3_stage_value()
    stage_value["profiles"] = [
        {"fixture_id": fixture_id, "complexity": complexities[fixture_id].model_dump(mode="json")}
        for fixture_id in (COMPATIBILITY_FIXTURE_ID, INCIDENT_FIXTURE_ID)
    ]
    stage_path = source / "benchmarks" / "suites" / "sdk-routing-v1" / "stages" / "s3-complex-high-risk.yaml"
    stage_path.parent.mkdir(parents=True, exist_ok=True)
    stage_path.write_text(yaml.safe_dump(stage_value, sort_keys=False), encoding="utf-8", newline="\n")
    suite_path = stage_path.parents[1] / "suite.yaml"
    suite_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "suite_id": "sdk-routing-v1",
                "design_revision": 4,
                "status": "implementation_candidate",
                "stages": [
                    {"stage_id": "s1-baseline", "path": "benchmarks/suites/sdk-routing-v1/stages/s1-baseline.yaml"},
                    {"stage_id": "s2-intermediate", "path": "benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml"},
                    {"stage_id": "s3-complex-high-risk", "path": "benchmarks/suites/sdk-routing-v1/stages/s3-complex-high-risk.yaml"},
                ],
                "live_turn_ceiling_including_pilot": 72,
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
        "summary": "deterministic S3 model-free result",
        "artifacts": [{"path": path, "kind": "file", "description": "golden model-free output"} for path in paths],
        "changed_paths": paths,
        "checks_run_by_worker": [],
        "assumptions": [],
        "warnings": [],
        "requested_followup": None,
    }


def _golden_turns(fixture_id: str) -> list[tuple[tuple[str, str], ...]]:
    groups = (
        [
            ("schema/model.py", "schema/errors.py"),
            ("migration/upgrade.py", "migration/legacy.py"),
            ("migration/legacy.py", "runtime/parser.py", "runtime/serializer.py", "integration/adapter.py"),
            ("integration/adapter.py", "compat/legacy_api.py", "compat/roundtrip.py", "cli/config_cli.py"),
        ]
        if fixture_id == COMPATIBILITY_FIXTURE_ID
        else [
            ("analysis/evidence-ledger.json", "analysis/uncertainties.json"),
            ("timeline/events.json", "timeline/conflict-groups.json"),
            ("analysis/hypotheses.json", "analysis/alternative-matrix.json"),
            ("report/claims.json", "report/action-plan.json", "report/final-report.md"),
        ]
    )
    return [
        tuple(
            (relative, (GOLDEN_ROOT / fixture_id / relative).read_text(encoding="utf-8"))
            for relative in group
        )
        for group in groups
    ]


def test_s3_fake_four_cell_plan_judge_property_seal_export(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, suite_path, stage_path = _create_s3_source_repository(tmp_path)
    plan = build_routing_s3_plan(
        repository_root=source,
        suite_path=suite_path,
        stage_path=stage_path,
        runner=ArtifactIdentity(artifact_id="benchmark-runner", version="s3-test", sha256=runner_source_sha256()),
        variants=[
            ArtifactIdentity(artifact_id="c2", version="s3-test", sha256="2" * 64),
            ArtifactIdentity(artifact_id="b1", version="s3-test", sha256="3" * 64),
        ],
        environment_fingerprint={"runtime": "fake", "actual_model_turns": "0"},
        created_at=datetime(2026, 8, 8, tzinfo=timezone.utc),
    )
    assert [cell.cell_id for cell in plan.cells] == [
        "cell_s3_a_1_c2", "cell_s3_a_1_b1", "cell_s3_b_1_b1", "cell_s3_b_1_c2"
    ]
    assert plan.decision_policy["base_live_model_turns"] == 16
    assert plan.decision_policy["max_actual_live_model_turns"] == 20
    experiment_dir = initialize_routing_s3_experiment(tmp_path / "state", plan)
    monkeypatch.syspath_prepend(str(B1_SOURCE_ROOT))
    from orchestrator.contract import RunSpec
    from orchestrator.worker import (
        build_task_envelope,
        render_worker_prompt,
        result_schema,
        task_semantics_sha256,
        validate_result,
    )

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

    results = run_all_routing_s3_nonlive_cells(
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
    status = routing_s3_nonlive_status(experiment_dir)
    assert status["validation_status"] == "MODEL_FREE_PASS"
    assert status["all_properties_passed"] is True
    assert status["actual_model_turns"] == 0
    exported = export_routing_s3_nonlive(
        repository_root=source,
        suite_path=suite_path,
        stage_path=stage_path,
        experiment_dir=experiment_dir,
        results_root=tmp_path / "results",
    )
    assert verify_routing_s3_nonlive_export(Path(exported["results_root"]))["export_sha256"] == exported["export_sha256"]

    live_measurements = []
    posthoc_results = {}
    for cell in plan.cells:
        cell_dir = experiment_dir / "cells" / cell.cell_id
        measurement = verify_sealed_cell(cell_dir)
        values = dict(measurement.variant_metrics.values)
        values["actual_model_turns"] = 4
        values["model_active_seconds"] = 1.0
        live_measurements.append(
            measurement.model_copy(
                update={
                    "resource": measurement.resource.model_copy(
                        update={"turn_count": measurement.resource.turn_count.model_copy(update={"value": 4})}
                    ),
                    "variant_metrics": measurement.variant_metrics.model_copy(update={"values": values}),
                }
            )
        )
        posthoc_results[cell.cell_id] = json.loads(
            (cell_dir / "judge" / "posthoc" / "result.json").read_text(encoding="utf-8")
        )
    policy = derive_s3_routing_policy(
        plan=plan,
        measurements=live_measurements,
        sealed_cell_ids={cell.cell_id for cell in plan.cells},
        posthoc_results=posthoc_results,
    )
    assert policy["stage_state"] == "S3_OBSERVATION_READY"
    assert {value["state"] for value in policy["profiles"].values()} == {
        "C2_SUFFICIENT_OBSERVED_SINGLE_PAIR"
    }
    assert policy["global_b1_default_issued"] is False
