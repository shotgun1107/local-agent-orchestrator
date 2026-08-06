"""Runner-owned Measurement and sealing path for non-live SDK comparison Cells."""

from __future__ import annotations

import platform
import time
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, JsonValue

from benchmark_runner.adapter import CellContext, VariantAdapter, VariantEvidence
from benchmark_runner.contract import (
    CellLifecycleState,
    CellStateRecord,
    ExecutionPlan,
    LifecycleEntry,
    Measurement,
    MeasurementEffort,
    MeasurementEnvironment,
    MeasurementIdentity,
    MeasurementIntegrity,
    MeasurementOutcome,
    MeasurementProvenance,
    MeasurementQuality,
    MeasurementResource,
    MetricStatus,
    PlannedCell,
    VariantMetrics,
    utc_now,
)
from benchmark_runner.judge import FixtureJudge, JudgeResult
from benchmark_runner.plan import assert_plan_integrity
from benchmark_runner.runner import (
    _evidence_ref,
    _metric,
    _transition,
    _write_model,
    atomic_write,
    canonical_json_bytes,
    sha256_bytes,
    verify_sealed_cell,
)
from benchmark_runner.workspace import PreparedFixture


class SdkSealedCellResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    experiment_id: str
    cell_id: str
    variant_id: str
    cell_state: Literal["SEALED"]
    outcome_state: str
    check_success: bool
    actual_model_turns: Literal[0] = 0
    measurement_path: str
    sealed_measurement_sha256: str


def initialize_sdk_experiment(state_root: Path, plan: ExecutionPlan) -> Path:
    """Create the immutable Plan root used by one non-live comparison track."""

    assert_plan_integrity(plan)
    experiment_dir = state_root.resolve() / plan.experiment_id
    experiment_dir.mkdir(parents=True, exist_ok=False)
    _write_model(experiment_dir / "execution-plan.json", plan)
    return experiment_dir


def _assert_plan_and_fixture(
    experiment_dir: Path,
    plan: ExecutionPlan,
    planned_cell: PlannedCell,
    prepared: PreparedFixture,
    adapter: VariantAdapter,
) -> tuple[str, str]:
    assert_plan_integrity(plan)
    if experiment_dir.name != plan.experiment_id:
        raise ValueError("Experiment directory does not match the Execution Plan")
    persisted = ExecutionPlan.model_validate_json(
        (experiment_dir / "execution-plan.json").read_bytes()
    )
    if persisted != plan:
        raise ValueError("Persisted Execution Plan does not match the supplied Plan")
    declared_cell = next(
        (cell for cell in plan.cells if cell.cell_id == planned_cell.cell_id),
        None,
    )
    if declared_cell != planned_cell:
        raise ValueError("Cell is not declared exactly by the Execution Plan")
    if adapter.id() != planned_cell.variant_id:
        raise ValueError("Adapter ID does not match the planned Variant")
    fixture = next(
        (item for item in plan.fixtures if item.fixture_id == planned_cell.fixture_id),
        None,
    )
    if fixture is None:
        raise ValueError("Planned fixture identity is missing")
    if (
        prepared.fixture.id != fixture.fixture_id
        or prepared.fixture.commit != fixture.source_commit
        or prepared.fixture.git_tree != fixture.git_tree
    ):
        raise ValueError("Prepared fixture does not match the Execution Plan")
    variant = next(
        (item for item in plan.variants if item.artifact_id == planned_cell.variant_id),
        None,
    )
    if variant is None:
        raise ValueError("Planned Variant artifact identity is missing")
    return variant.version, variant.sha256


def _assert_nonlive_evidence(evidence: VariantEvidence) -> None:
    turn_fields = [
        evidence.raw_payload[key]
        for key in ("model_turns", "actual_model_turns")
        if key in evidence.raw_payload
    ]
    if not turn_fields or any(value != 0 for value in turn_fields):
        raise RuntimeError("non-live Cell did not prove actual_model_turns=0")


def _token_metric(evidence: VariantEvidence):
    metrics = evidence.normalized_metrics
    if metrics.get("token_usage_status") == "measured" and metrics.get("token_usage") is not None:
        return _metric(
            MetricStatus.MEASURED,
            "tokens",
            value=metrics["token_usage"],
            source="variant_normalized_metrics",
            evidence_ref="raw/adapter-result.json",
        )
    return _metric(
        MetricStatus.UNKNOWN,
        "tokens",
        source="variant_normalized_metrics",
        evidence_ref="raw/adapter-result.json",
    )


def _measurement(
    *,
    plan: ExecutionPlan,
    planned_cell: PlannedCell,
    prepared: PreparedFixture,
    evidence: VariantEvidence,
    judge: JudgeResult,
    cell_dir: Path,
    variant_seconds: float,
    judge_seconds: float,
    total_seconds: float,
    runner_commit: str,
    variant_version: str,
    variant_sha256: str,
    scenario_id: str | None,
) -> Measurement:
    if judge.final_tree is None:
        raise RuntimeError("SDK comparison Judge did not produce a final tree")
    evidence_paths = sorted(
        [
            path
            for directory in (cell_dir / "raw", cell_dir / "judge")
            for path in directory.rglob("*")
            if path.is_file()
        ],
        key=lambda path: path.relative_to(cell_dir).as_posix(),
    )
    refs = [_evidence_ref(cell_dir, path) for path in evidence_paths]
    metrics = evidence.normalized_metrics
    not_applicable_count = _metric(MetricStatus.NOT_APPLICABLE, "count")
    not_applicable_seconds = _metric(MetricStatus.NOT_APPLICABLE, "seconds")
    values: dict[str, JsonValue] = {
        "adapter_id": planned_cell.variant_id,
        "actual_model_turns": 0,
        "terminal_claim_outcome": evidence.outcome_state,
        "downstream_turn_count": int(metrics.get("turn_count", 0)),
    }
    if scenario_id is not None:
        values["scenario_id"] = scenario_id
    if "turns" in evidence.raw_payload:
        values["turns"] = evidence.raw_payload["turns"]
    return Measurement(
        created_at=utc_now(),
        identity=MeasurementIdentity(
            experiment_id=plan.experiment_id,
            block_id=planned_cell.block_id,
            cell_id=planned_cell.cell_id,
            fixture_id=planned_cell.fixture_id,
            repetition=planned_cell.repetition,
            variant_id=planned_cell.variant_id,
            execution_ordinal=planned_cell.execution_ordinal,
        ),
        provenance=MeasurementProvenance(
            manifest_sha256=plan.source_manifest.sha256,
            fixture_source_commit=prepared.fixture.commit,
            fixture_tree_before=prepared.fixture.git_tree,
            fixture_tree_after=judge.final_tree,
            runner_commit=runner_commit,
            variant_version=variant_version,
            variant_artifact_sha256=variant_sha256,
        ),
        environment=MeasurementEnvironment(
            os=platform.system().lower(),
            python_version=platform.python_version(),
            model="fake",
            auth_method="not_applicable_nonlive",
            reasoning_effort="not_applicable_nonlive",
            surface_kind=(
                "b1_cli_fake_runtime"
                if planned_cell.variant_id == "b1"
                else "sdk_controlled_fake_runtime"
            ),
            approval_mode="not_applicable_nonlive",
            model_control="not_applicable_nonlive",
            reasoning_control="not_applicable_nonlive",
            treatment_control="not_applicable",
        ),
        outcome=MeasurementOutcome(
            state=evidence.outcome_state,
            failure_kind=(
                evidence.failure_kind
                if evidence.failure_kind
                else None if judge.check_success else "independent_judge_failed"
            ),
            check_success=judge.check_success,
        ),
        effort=MeasurementEffort(
            variant_execution_seconds=_metric(
                MetricStatus.MEASURED,
                "seconds",
                value=variant_seconds,
                source="runner_monotonic_clock",
            ),
            judge_seconds=_metric(
                MetricStatus.MEASURED,
                "seconds",
                value=judge_seconds,
                source="runner_monotonic_clock",
            ),
            total_wall_clock_seconds=_metric(
                MetricStatus.MEASURED,
                "seconds",
                value=total_seconds,
                source="runner_monotonic_clock",
            ),
            startup_action_count=not_applicable_count,
            manual_copy_or_relay_count_excluding_start=not_applicable_count,
            manual_copy_or_relay_count_including_start=not_applicable_count,
            manual_recovery_count=not_applicable_count,
            manual_recovery_seconds=not_applicable_seconds,
        ),
        resource=MeasurementResource(
            session_count=_metric(
                MetricStatus.MEASURED,
                "count",
                value=int(metrics.get("session_count", 0)),
                source="variant_normalized_metrics",
                evidence_ref="raw/adapter-result.json",
            ),
            turn_count=_metric(
                MetricStatus.MEASURED,
                "count",
                value=int(metrics.get("turn_count", 0)),
                source="variant_normalized_metrics",
                evidence_ref="raw/adapter-result.json",
            ),
            attempt_count=_metric(
                MetricStatus.MEASURED,
                "count",
                value=evidence.attempt_count,
                source="variant_evidence",
                evidence_ref="raw/adapter-result.json",
            ),
            token_usage=_token_metric(evidence),
        ),
        quality=MeasurementQuality(
            errors_found_by_automatic_checks=_metric(
                MetricStatus.DERIVED,
                "count",
                value=len(judge.failed_check_ids),
                source="fixture_v1_judge",
                evidence_ref="judge/result.json",
            ),
            human_errors_after_pass=_metric(MetricStatus.NOT_APPLICABLE, "count"),
        ),
        integrity=MeasurementIntegrity(
            scope_ok=not judge.scope_violations,
            evidence_hashes_ok=True,
            secret_findings=[],
        ),
        evidence=refs,
        variant_metrics=VariantMetrics(
            schema_id="sdk-controlled-nonlive/v1",
            values=values,
        ),
    )


def run_sdk_nonlive_cell(
    *,
    experiment_dir: Path,
    plan: ExecutionPlan,
    planned_cell: PlannedCell,
    prepared: PreparedFixture,
    adapter: VariantAdapter,
    benchmark_python: Path,
    git_executable: Path,
    runner_commit: str,
    scenario_id: str | None = None,
) -> SdkSealedCellResult:
    """Run one fake-runtime Cell through the real Judge, Measurement, and seal."""

    experiment_dir = experiment_dir.resolve()
    variant_version, variant_sha256 = _assert_plan_and_fixture(
        experiment_dir,
        plan,
        planned_cell,
        prepared,
        adapter,
    )
    cell_dir = experiment_dir / "cells" / planned_cell.cell_id
    raw_dir = cell_dir / "raw"
    judge_dir = cell_dir / "judge"
    sealed_dir = cell_dir / "sealed"
    for directory in (raw_dir, judge_dir, sealed_dir):
        directory.mkdir(parents=True, exist_ok=False)

    state_path = cell_dir / "cell-state.json"
    record = CellStateRecord(
        cell_id=planned_cell.cell_id,
        state=CellLifecycleState.PLANNED,
        history=[LifecycleEntry(state=CellLifecycleState.PLANNED, at=utc_now())],
    )
    _write_model(state_path, record)
    context = CellContext(plan.experiment_id, planned_cell.cell_id)
    preflight = adapter.preflight(context)
    if not preflight.ok:
        raise RuntimeError(f"{adapter.id()} preflight failed: {preflight.detail}")
    record = _transition(record, CellLifecycleState.PREPARED)
    _write_model(state_path, record)
    record = _transition(record, CellLifecycleState.ACTIVE)
    _write_model(state_path, record)

    total_started = time.monotonic()
    variant_started = time.monotonic()
    evidence = adapter.run(context)
    variant_seconds = time.monotonic() - variant_started
    _assert_nonlive_evidence(evidence)
    atomic_write(
        raw_dir / "adapter-result.json",
        canonical_json_bytes(
            {
                "outcome_state": evidence.outcome_state,
                "failure_kind": evidence.failure_kind,
                "attempt_count": evidence.attempt_count,
                "raw_payload": evidence.raw_payload,
                "normalized_metrics": evidence.normalized_metrics,
            }
        ),
    )
    record = _transition(
        record,
        CellLifecycleState.CAPTURED,
        outcome_state=evidence.outcome_state,
    )
    _write_model(state_path, record)
    record = _transition(record, CellLifecycleState.JUDGING)
    _write_model(state_path, record)

    judge_started = time.monotonic()
    judge = FixtureJudge(benchmark_python, git_executable).evaluate(prepared, judge_dir)
    judge_seconds = time.monotonic() - judge_started
    total_seconds = time.monotonic() - total_started
    measurement = _measurement(
        plan=plan,
        planned_cell=planned_cell,
        prepared=prepared,
        evidence=evidence,
        judge=judge,
        cell_dir=cell_dir,
        variant_seconds=variant_seconds,
        judge_seconds=judge_seconds,
        total_seconds=total_seconds,
        runner_commit=runner_commit,
        variant_version=variant_version,
        variant_sha256=variant_sha256,
        scenario_id=scenario_id,
    )
    measurement_path = sealed_dir / "measurement.json"
    measurement_bytes = canonical_json_bytes(measurement)
    atomic_write(measurement_path, measurement_bytes)
    sealed_hash = sha256_bytes(measurement_bytes)
    record = _transition(
        record,
        CellLifecycleState.SEALED,
        outcome_state=evidence.outcome_state,
        sealed_hash=sealed_hash,
    )
    _write_model(state_path, record)
    verify_sealed_cell(cell_dir)
    return SdkSealedCellResult(
        experiment_id=plan.experiment_id,
        cell_id=planned_cell.cell_id,
        variant_id=planned_cell.variant_id,
        cell_state="SEALED",
        outcome_state=evidence.outcome_state,
        check_success=judge.check_success,
        measurement_path=str(measurement_path),
        sealed_measurement_sha256=sealed_hash,
    )
