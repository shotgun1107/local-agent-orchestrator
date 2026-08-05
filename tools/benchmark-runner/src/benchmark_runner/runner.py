from __future__ import annotations

import hashlib
import json
import os
import platform
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from benchmark_runner.adapter import CellContext, FakeAdapter, VariantAdapter
from benchmark_runner.contract import (
    CellLifecycleState,
    CellStateRecord,
    EvidenceRef,
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
    MetricValue,
    VariantMetrics,
    utc_now,
)
from benchmark_runner.judge import StubJudge
from benchmark_runner.plan import ZERO_GIT_ID, ZERO_SHA256, build_r0_plan


class IntegrityError(RuntimeError):
    pass


class R0RunResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    experiment_id: str
    cell_id: str
    cell_state: Literal["SEALED"]
    outcome_state: str
    check_success: bool
    model_turns: Literal[0] = 0
    plan_path: str
    measurement_path: str
    sealed_measurement_sha256: str


TRANSITIONS: dict[CellLifecycleState, set[CellLifecycleState]] = {
    CellLifecycleState.PLANNED: {CellLifecycleState.PREPARED},
    CellLifecycleState.PREPARED: {CellLifecycleState.ACTIVE},
    CellLifecycleState.ACTIVE: {CellLifecycleState.CAPTURED},
    CellLifecycleState.CAPTURED: {CellLifecycleState.JUDGING},
    CellLifecycleState.JUDGING: {CellLifecycleState.SEALED},
}


def canonical_json_bytes(value: BaseModel | object) -> bytes:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_model(path: Path, model: BaseModel) -> None:
    atomic_write(path, canonical_json_bytes(model))


def _transition(
    record: CellStateRecord,
    target: CellLifecycleState,
    *,
    outcome_state: str | None = None,
    sealed_hash: str | None = None,
) -> CellStateRecord:
    if target not in TRANSITIONS.get(record.state, set()):
        raise ValueError(f"invalid Cell transition: {record.state} -> {target}")
    return record.model_copy(
        update={
            "state": target,
            "history": [*record.history, LifecycleEntry(state=target, at=utc_now())],
            "outcome_state": outcome_state if outcome_state is not None else record.outcome_state,
            "sealed_measurement_sha256": sealed_hash,
        }
    )


def _metric(
    status: MetricStatus,
    unit: str,
    *,
    value: object | None = None,
    source: str | None = None,
    evidence_ref: str | None = None,
) -> MetricValue:
    return MetricValue(
        status=status,
        value=value,
        unit=unit,
        source=source,
        evidence_ref=evidence_ref,
    )


def _evidence_ref(cell_dir: Path, path: Path) -> EvidenceRef:
    return EvidenceRef(
        path=path.relative_to(cell_dir).as_posix(),
        size=path.stat().st_size,
        sha256=sha256_file(path),
    )


class R0Runner:
    def __init__(self, adapter: VariantAdapter, judge: StubJudge | None = None) -> None:
        self.adapter = adapter
        self.judge = judge or StubJudge()

    def run(self, state_root: Path, created_at: datetime | None = None) -> R0RunResult:
        plan = build_r0_plan(created_at)
        planned_cell = plan.cells[0]
        experiment_dir = state_root.resolve() / plan.experiment_id
        experiment_dir.mkdir(parents=True, exist_ok=False)
        plan_path = experiment_dir / "execution-plan.json"
        _write_model(plan_path, plan)

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

        context = CellContext(
            experiment_id=plan.experiment_id,
            cell_id=planned_cell.cell_id,
        )
        preflight = self.adapter.preflight(context)
        if not preflight.ok:
            raise RuntimeError(f"Fake Adapter preflight failed: {preflight.detail}")

        record = _transition(record, CellLifecycleState.PREPARED)
        _write_model(state_path, record)
        record = _transition(record, CellLifecycleState.ACTIVE)
        _write_model(state_path, record)

        total_started = time.monotonic()
        variant_started = time.monotonic()
        variant_evidence = self.adapter.run(context)
        variant_seconds = time.monotonic() - variant_started
        raw_path = raw_dir / "fake-result.json"
        atomic_write(raw_path, canonical_json_bytes(variant_evidence.raw_payload))

        record = _transition(
            record,
            CellLifecycleState.CAPTURED,
            outcome_state=variant_evidence.outcome_state,
        )
        _write_model(state_path, record)
        record = _transition(record, CellLifecycleState.JUDGING)
        _write_model(state_path, record)

        judge_started = time.monotonic()
        judge_result = self.judge.evaluate(variant_evidence)
        judge_path = judge_dir / "result.json"
        _write_model(judge_path, judge_result)
        judge_seconds = time.monotonic() - judge_started
        total_seconds = time.monotonic() - total_started

        evidence = sorted(
            [_evidence_ref(cell_dir, raw_path), _evidence_ref(cell_dir, judge_path)],
            key=lambda item: item.path,
        )
        not_applicable_count = _metric(MetricStatus.NOT_APPLICABLE, "count")
        not_applicable_seconds = _metric(MetricStatus.NOT_APPLICABLE, "seconds")
        measurement = Measurement(
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
                fixture_source_commit=ZERO_GIT_ID,
                fixture_tree_before=ZERO_GIT_ID,
                fixture_tree_after=ZERO_GIT_ID,
                runner_commit="r0-uncommitted",
                variant_version="r0-fake/0.1.0",
                variant_artifact_sha256=ZERO_SHA256,
            ),
            environment=MeasurementEnvironment(
                os=platform.system().lower(),
                python_version=platform.python_version(),
                model="not_applicable",
                auth_method="not_applicable",
                reasoning_effort="not_applicable",
                surface_kind="fake",
                approval_mode="not_applicable",
                model_control="not_applicable",
                reasoning_control="not_applicable",
                treatment_control="not_applicable",
            ),
            outcome=MeasurementOutcome(
                state=variant_evidence.outcome_state,
                failure_kind=variant_evidence.failure_kind,
                check_success=judge_result.check_success,
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
                    value=0,
                    source="r0_fake_adapter",
                ),
                turn_count=_metric(
                    MetricStatus.MEASURED,
                    "count",
                    value=0,
                    source="r0_fake_adapter",
                ),
                attempt_count=_metric(
                    MetricStatus.MEASURED,
                    "count",
                    value=variant_evidence.attempt_count,
                    source="r0_fake_adapter",
                    evidence_ref="raw/fake-result.json",
                ),
                token_usage=_metric(MetricStatus.NOT_APPLICABLE, "tokens"),
            ),
            quality=MeasurementQuality(
                errors_found_by_automatic_checks=_metric(
                    MetricStatus.DERIVED,
                    "count",
                    value=len(judge_result.failed_check_ids),
                    source="r0_stub_judge",
                    evidence_ref="judge/result.json",
                ),
                human_errors_after_pass=_metric(MetricStatus.NOT_APPLICABLE, "count"),
            ),
            integrity=MeasurementIntegrity(
                scope_ok=True,
                evidence_hashes_ok=True,
                secret_findings=[],
            ),
            evidence=evidence,
            variant_metrics=VariantMetrics(
                schema_id="r0-fake/v1",
                values={
                    "automated_launch": self.adapter.capabilities().automated_launch,
                    "model_turns": 0,
                    "read_only": True,
                },
            ),
        )
        measurement_path = sealed_dir / "measurement.json"
        measurement_bytes = canonical_json_bytes(measurement)
        atomic_write(measurement_path, measurement_bytes)
        sealed_hash = sha256_bytes(measurement_bytes)

        record = _transition(
            record,
            CellLifecycleState.SEALED,
            outcome_state=variant_evidence.outcome_state,
            sealed_hash=sealed_hash,
        )
        _write_model(state_path, record)
        verify_sealed_cell(cell_dir)
        return R0RunResult(
            experiment_id=plan.experiment_id,
            cell_id=planned_cell.cell_id,
            cell_state="SEALED",
            outcome_state=variant_evidence.outcome_state,
            check_success=judge_result.check_success,
            plan_path=str(plan_path),
            measurement_path=str(measurement_path),
            sealed_measurement_sha256=sealed_hash,
        )


def verify_sealed_cell(cell_dir: Path) -> Measurement:
    root = cell_dir.resolve()
    state = CellStateRecord.model_validate_json((root / "cell-state.json").read_bytes())
    if state.state is not CellLifecycleState.SEALED or not state.sealed_measurement_sha256:
        raise IntegrityError("Cell is not sealed")
    measurement_path = root / "sealed" / "measurement.json"
    if sha256_file(measurement_path) != state.sealed_measurement_sha256:
        raise IntegrityError("Measurement hash does not match the Cell seal")
    measurement = Measurement.model_validate_json(measurement_path.read_bytes())
    for evidence in measurement.evidence:
        candidate = root / Path(evidence.path)
        cursor = root
        for part in Path(evidence.path).parts:
            cursor /= part
            if cursor.is_symlink():
                raise IntegrityError(f"unsafe or missing Evidence: {evidence.path}")
        path = candidate.resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise IntegrityError(f"unsafe or missing Evidence: {evidence.path}")
        if path.stat().st_size != evidence.size or sha256_file(path) != evidence.sha256:
            raise IntegrityError(f"Evidence hash mismatch: {evidence.path}")
    return measurement


def run_r0_fake_cell(
    state_root: Path,
    outcome: Literal["completed", "failed"] = "completed",
    created_at: datetime | None = None,
) -> R0RunResult:
    return R0Runner(FakeAdapter(outcome)).run(state_root, created_at)
