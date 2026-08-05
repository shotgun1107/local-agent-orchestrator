from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import socket
import statistics
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable, Literal, Protocol

from pydantic import BaseModel, ConfigDict

from benchmark_runner.adapter import (
    B0AdapterConfig,
    B0ManualAdapter,
    B0ManualInputProvider,
    B0ManualSession,
    B1AdapterConfig,
    B1SequentialAdapter,
    CellContext,
    ConsoleB0ManualInputProvider,
    FakeAdapter,
    VariantAdapter,
    VariantCapabilities,
    VariantEvidence,
)
from benchmark_runner.contract import (
    ArtifactIdentity,
    B0Attestation,
    B0ManualSubmission,
    CellLifecycleState,
    CellStateRecord,
    ControllerLockRecord,
    EvidenceRef,
    ExecutionPlan,
    ExperimentControl,
    ExperimentDisplayState,
    ExperimentStatus,
    FixtureIdentity,
    InterventionEvent,
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
    OutcomeState,
    PreflightRecord,
    PlannedCell,
    PRODUCER,
    StopHistoryEntry,
    VariantMetrics,
    utc_now,
    validate_relative_path,
)
from benchmark_runner.judge import (
    FixtureJudge,
    JudgeProcessRecord,
    StubJudge,
    _write_process_record,
    recover_orphan_judge_process,
)
from benchmark_runner.plan import (
    ZERO_GIT_ID,
    ZERO_SHA256,
    assert_plan_integrity,
    build_r0_plan,
    build_r2_plan,
    build_r3_plan,
    build_r4_plan,
)
from benchmark_runner.workspace import (
    ChecksFile,
    FixtureRestorer,
    FrozenFixtureSpec,
    PreparedFixture,
    load_frozen_manifest,
)


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


class R2RunResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    experiment_id: str
    cell_id: str
    cell_state: Literal["SEALED"]
    b1_run_id: str
    outcome_state: str
    check_success: bool
    actual_model_turns: Literal[0] = 0
    plan_path: str
    measurement_path: str
    sealed_measurement_sha256: str


class R3RunResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    experiment_id: str
    cell_id: str
    cell_state: Literal["SEALED"]
    outcome_state: str
    check_success: bool
    runner_model_turns: Literal[0] = 0
    stop_required: bool
    stop_reason: str | None
    plan_path: str
    measurement_path: str
    sealed_measurement_sha256: str


TRANSITIONS: dict[CellLifecycleState, set[CellLifecycleState]] = {
    CellLifecycleState.PLANNED: {CellLifecycleState.PREPARED},
    CellLifecycleState.PREPARED: {CellLifecycleState.ACTIVE},
    CellLifecycleState.ACTIVE: {
        CellLifecycleState.CAPTURED,
        CellLifecycleState.STOPPED,
    },
    CellLifecycleState.STOPPED: {CellLifecycleState.CAPTURED},
    CellLifecycleState.CAPTURED: {CellLifecycleState.JUDGING},
    CellLifecycleState.JUDGING: {
        CellLifecycleState.SEALED,
        CellLifecycleState.STOPPED,
    },
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
    stop_reason: str | None = None,
    sealed_hash: str | None = None,
) -> CellStateRecord:
    if target not in TRANSITIONS.get(record.state, set()):
        raise ValueError(f"invalid Cell transition: {record.state} -> {target}")
    return record.model_copy(
        update={
            "state": target,
            "history": [*record.history, LifecycleEntry(state=target, at=utc_now())],
            "outcome_state": outcome_state if outcome_state is not None else record.outcome_state,
            "stop_reason": stop_reason,
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
        assert_plan_integrity(plan)
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
    if state.cell_id != root.name:
        raise IntegrityError("Cell state identity does not match its directory")
    plan_path = root.parents[1] / "execution-plan.json"
    try:
        plan = ExecutionPlan.model_validate_json(plan_path.read_bytes())
        assert_plan_integrity(plan)
    except (OSError, ValueError) as exc:
        raise IntegrityError("Execution Plan integrity check failed") from exc
    measurement_path = root / "sealed" / "measurement.json"
    if sha256_file(measurement_path) != state.sealed_measurement_sha256:
        raise IntegrityError("Measurement hash does not match the Cell seal")
    measurement = Measurement.model_validate_json(measurement_path.read_bytes())
    planned_cell = next((cell for cell in plan.cells if cell.cell_id == state.cell_id), None)
    if planned_cell is None:
        raise IntegrityError("Sealed Cell is not declared in the Execution Plan")
    expected_identity = MeasurementIdentity(
        experiment_id=plan.experiment_id,
        block_id=planned_cell.block_id,
        cell_id=planned_cell.cell_id,
        fixture_id=planned_cell.fixture_id,
        repetition=planned_cell.repetition,
        variant_id=planned_cell.variant_id,
        execution_ordinal=planned_cell.execution_ordinal,
    )
    if measurement.identity != expected_identity:
        raise IntegrityError("Measurement identity does not match the Execution Plan")
    if measurement.provenance.manifest_sha256 != plan.source_manifest.sha256:
        raise IntegrityError("Measurement manifest hash does not match the Execution Plan")
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


def _source_tree_sha256(root: Path, included_paths: tuple[str, ...]) -> str:
    root = root.resolve()
    files: set[Path] = set()
    for relative in included_paths:
        candidate = root / relative
        if candidate.is_file():
            files.add(candidate)
        elif candidate.is_dir():
            files.update(path for path in candidate.rglob("*") if path.is_file())
        else:
            raise FileNotFoundError(f"source fingerprint input is missing: {candidate}")
    digest = hashlib.sha256()
    for path in sorted(files, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        if path.is_symlink():
            raise ValueError(f"source fingerprint rejects symlinks: {relative}")
        data = path.read_bytes()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def _git_head(repository: Path, git_executable: Path) -> str:
    result = subprocess.run(
        [str(git_executable), "-C", str(repository), "rev-parse", "HEAD"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError("cannot read Runner source commit")
    return result.stdout.strip()


def run_r2_b1_fake_cell(
    *,
    state_root: Path,
    source_repository: Path,
    manifest_path: Path,
    fixture_id: str,
    b1_command_prefix: tuple[str, ...],
    b1_project_root: Path,
    b1_schema_root: Path,
    fake_fixture: dict[str, object],
    benchmark_python: Path,
    git_executable: Path,
    created_at: datetime | None = None,
) -> R2RunResult:
    source_repository = source_repository.resolve()
    manifest_path = manifest_path.resolve()
    b1_project_root = b1_project_root.resolve()
    git_executable = git_executable.resolve()
    manifest = load_frozen_manifest(manifest_path)
    try:
        fixture = next(item for item in manifest.fixtures if item.id == fixture_id)
    except StopIteration as exc:
        raise ValueError(f"fixture is not declared in the frozen manifest: {fixture_id}") from exc
    manifest_relative = manifest_path.relative_to(source_repository).as_posix()
    manifest_sha256 = sha256_file(manifest_path)
    runner_root = Path(__file__).resolve().parents[2]
    runner_sha256 = _source_tree_sha256(
        runner_root,
        ("pyproject.toml", "src/benchmark_runner", "schemas"),
    )
    b1_sha256 = _source_tree_sha256(
        b1_project_root,
        ("pyproject.toml", "src/orchestrator", "templates/project-pack", "schemas/v1"),
    )
    plan = build_r2_plan(
        source_manifest_path=manifest_relative,
        source_manifest_sha256=manifest_sha256,
        fixture_id=fixture.id,
        fixture_source_commit=fixture.commit,
        fixture_git_tree=fixture.git_tree,
        runner_sha256=runner_sha256,
        b1_sha256=b1_sha256,
        created_at=created_at,
    )
    planned_cell = plan.cells[0]
    experiment_dir = state_root.resolve() / plan.experiment_id
    experiment_dir.mkdir(parents=True, exist_ok=False)
    plan_path = experiment_dir / "execution-plan.json"
    _write_model(plan_path, plan)

    cell_dir = experiment_dir / "cells" / planned_cell.cell_id
    raw_dir = cell_dir / "raw"
    events_dir = cell_dir / "events"
    judge_dir = cell_dir / "judge"
    sealed_dir = cell_dir / "sealed"
    for directory in (raw_dir, events_dir, judge_dir, sealed_dir):
        directory.mkdir(parents=True, exist_ok=False)
    state_path = cell_dir / "cell-state.json"
    record = CellStateRecord(
        cell_id=planned_cell.cell_id,
        state=CellLifecycleState.PLANNED,
        history=[LifecycleEntry(state=CellLifecycleState.PLANNED, at=utc_now())],
    )
    _write_model(state_path, record)

    prepared = FixtureRestorer(source_repository, str(git_executable)).restore(
        fixture,
        cell_dir / "workspace",
    )
    fake_fixture_path = raw_dir / "fake-runtime-input.json"
    atomic_write(fake_fixture_path, canonical_json_bytes(fake_fixture))
    adapter = B1SequentialAdapter(
        B1AdapterConfig(
            command_prefix=b1_command_prefix,
            project=prepared.workspace,
            run_spec=prepared.workspace / "benchmark-run.yaml",
            state_root=cell_dir / "variant-state",
            schema_root=b1_schema_root,
            runtime="fake",
            fake_fixture=fake_fixture_path,
        )
    )
    context = CellContext(
        experiment_id=plan.experiment_id,
        cell_id=planned_cell.cell_id,
    )
    preflight = adapter.preflight(context)
    if not preflight.ok:
        raise RuntimeError(f"B1 Adapter preflight failed: {preflight.detail}")
    record = _transition(record, CellLifecycleState.PREPARED)
    _write_model(state_path, record)
    record = _transition(record, CellLifecycleState.ACTIVE)
    _write_model(state_path, record)

    total_started = time.monotonic()
    variant_started = time.monotonic()
    b1_start_at = utc_now()
    b1_start_event = InterventionEvent(
        created_at=b1_start_at,
        event_id="evt_000001",
        cell_id=planned_cell.cell_id,
        timestamp=b1_start_at,
        monotonic_offset_seconds=max(0.0, time.monotonic() - total_started),
        intervention_kind="b1_start",
        actor="runner",
    )
    b1_events_path = events_dir / "interventions.jsonl"
    atomic_write(b1_events_path, canonical_json_bytes(b1_start_event) + b"\n")
    variant_evidence = adapter.run(context)
    variant_seconds = time.monotonic() - variant_started
    adapter_path = raw_dir / "adapter-result.json"
    atomic_write(adapter_path, canonical_json_bytes(variant_evidence.raw_payload))
    record = _transition(
        record,
        CellLifecycleState.CAPTURED,
        outcome_state=variant_evidence.outcome_state,
    )
    _write_model(state_path, record)
    record = _transition(record, CellLifecycleState.JUDGING)
    _write_model(state_path, record)

    judge_started = time.monotonic()
    judge_result = FixtureJudge(benchmark_python, git_executable).evaluate(
        prepared,
        judge_dir,
    )
    judge_seconds = time.monotonic() - judge_started
    total_seconds = time.monotonic() - total_started
    if judge_result.final_tree is None:
        raise RuntimeError("R2 Judge did not produce a final tree")

    evidence_paths = sorted(
        [
            path
            for directory in (raw_dir, events_dir, judge_dir)
            for path in directory.rglob("*")
            if path.is_file()
        ],
        key=lambda path: path.relative_to(cell_dir).as_posix(),
    )
    evidence = [_evidence_ref(cell_dir, path) for path in evidence_paths]
    metrics = variant_evidence.normalized_metrics
    token_usage_status = str(metrics.get("token_usage_status", "unknown"))
    token_usage = metrics.get("token_usage")
    if token_usage_status == "measured" and token_usage is not None:
        token_metric = _metric(
            MetricStatus.MEASURED,
            "tokens",
            value=token_usage,
            source="b1_public_run_report",
            evidence_ref="raw/adapter-result.json",
        )
    else:
        token_metric = _metric(
            MetricStatus.UNKNOWN,
            "tokens",
            source="b1_public_run_report",
            evidence_ref="raw/adapter-result.json",
        )
    b1_run_id = str(variant_evidence.raw_payload.get("run_id", "missing"))
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
            manifest_sha256=manifest_sha256,
            fixture_source_commit=fixture.commit,
            fixture_tree_before=fixture.git_tree,
            fixture_tree_after=judge_result.final_tree,
            runner_commit=(
                f"{_git_head(source_repository, git_executable)}"
                f"+source-{runner_sha256[:12]}"
            ),
            variant_version="0.1.0-source",
            variant_artifact_sha256=b1_sha256,
        ),
        environment=MeasurementEnvironment(
            os=platform.system().lower(),
            python_version=platform.python_version(),
            model="fake",
            auth_method="none",
            reasoning_effort="not_applicable",
            surface_kind="b1_cli_fake_runtime",
            approval_mode="none",
            model_control="not_applicable",
            reasoning_control="not_applicable_fake_runtime",
            treatment_control="not_applicable",
        ),
        outcome=MeasurementOutcome(
            state=variant_evidence.outcome_state,
            failure_kind=(
                variant_evidence.failure_kind
                if variant_evidence.failure_kind
                else None if judge_result.check_success else "independent_judge_failed"
            ),
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
            startup_action_count=_metric(
                MetricStatus.DERIVED,
                "count",
                value=1,
                source="intervention_events",
                evidence_ref="events/interventions.jsonl",
            ),
            manual_copy_or_relay_count_excluding_start=_metric(
                MetricStatus.DERIVED,
                "count",
                value=0,
                source="intervention_events",
                evidence_ref="events/interventions.jsonl",
            ),
            manual_copy_or_relay_count_including_start=_metric(
                MetricStatus.DERIVED,
                "count",
                value=1,
                source="intervention_events",
                evidence_ref="events/interventions.jsonl",
            ),
            manual_recovery_count=_metric(
                MetricStatus.DERIVED,
                "count",
                value=0,
                source="intervention_events",
                evidence_ref="events/interventions.jsonl",
            ),
            manual_recovery_seconds=_metric(
                MetricStatus.DERIVED,
                "seconds",
                value=0.0,
                source="intervention_events",
                evidence_ref="events/interventions.jsonl",
            ),
        ),
        resource=MeasurementResource(
            session_count=_metric(
                MetricStatus.MEASURED,
                "count",
                value=int(metrics.get("session_count", 0)),
                source="b1_public_run_report",
            ),
            turn_count=_metric(
                MetricStatus.MEASURED,
                "count",
                value=int(metrics.get("turn_count", 0)),
                source="b1_public_run_report",
            ),
            attempt_count=_metric(
                MetricStatus.MEASURED,
                "count",
                value=variant_evidence.attempt_count,
                source="b1_public_run_report",
            ),
            token_usage=token_metric,
        ),
        quality=MeasurementQuality(
            errors_found_by_automatic_checks=_metric(
                MetricStatus.DERIVED,
                "count",
                value=len(judge_result.failed_check_ids),
                source="fixture_v1_judge",
                evidence_ref="judge/result.json",
            ),
            human_errors_after_pass=_metric(MetricStatus.NOT_APPLICABLE, "count"),
        ),
        integrity=MeasurementIntegrity(
            scope_ok=not judge_result.scope_violations,
            evidence_hashes_ok=True,
            secret_findings=[],
        ),
        evidence=evidence,
        variant_metrics=VariantMetrics(
            schema_id="b1-public-cli/v1",
            values={
                "b1_run_id": b1_run_id,
                "b1_report_usage_status": metrics.get("b1_report_usage_status"),
                "b1_session_usage_statuses": metrics.get("b1_session_usage_statuses", []),
                "b1_token_usage_raw": metrics.get("b1_token_usage_raw"),
                "actual_model_turns": 0,
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
    return R2RunResult(
        experiment_id=plan.experiment_id,
        cell_id=planned_cell.cell_id,
        cell_state="SEALED",
        b1_run_id=b1_run_id,
        outcome_state=variant_evidence.outcome_state,
        check_success=judge_result.check_success,
        plan_path=str(plan_path),
        measurement_path=str(measurement_path),
        sealed_measurement_sha256=sealed_hash,
    )


def run_r3_b0_manual_cell(
    *,
    state_root: Path,
    source_repository: Path,
    manifest_path: Path,
    fixture_id: str,
    input_provider: B0ManualInputProvider,
    benchmark_python: Path,
    git_executable: Path,
    model: str,
    reasoning_effort: str,
    surface_kind: str,
    auth_method: str = "chatgpt",
    approval_mode: str = "user_confirmed",
    created_at: datetime | None = None,
) -> R3RunResult:
    """Run one B0 Cell with a manual sidecar and no model launch by the Runner."""

    source_repository = source_repository.resolve()
    manifest_path = manifest_path.resolve()
    git_executable = git_executable.resolve()
    manifest = load_frozen_manifest(manifest_path)
    try:
        fixture = next(item for item in manifest.fixtures if item.id == fixture_id)
    except StopIteration as exc:
        raise ValueError(f"fixture is not declared in the frozen manifest: {fixture_id}") from exc
    manifest_relative = manifest_path.relative_to(source_repository).as_posix()
    manifest_sha256 = sha256_file(manifest_path)
    runner_root = Path(__file__).resolve().parents[2]
    runner_sha256 = _source_tree_sha256(
        runner_root,
        ("pyproject.toml", "src/benchmark_runner", "schemas"),
    )
    plan = build_r3_plan(
        source_manifest_path=manifest_relative,
        source_manifest_sha256=manifest_sha256,
        fixture_id=fixture.id,
        fixture_source_commit=fixture.commit,
        fixture_git_tree=fixture.git_tree,
        runner_sha256=runner_sha256,
        b0_sha256=runner_sha256,
        model=model,
        reasoning_effort=reasoning_effort,
        surface_kind=surface_kind,
        created_at=created_at,
    )
    planned_cell = plan.cells[0]
    experiment_dir = state_root.resolve() / plan.experiment_id
    experiment_dir.mkdir(parents=True, exist_ok=False)
    plan_path = experiment_dir / "execution-plan.json"
    _write_model(plan_path, plan)

    cell_dir = experiment_dir / "cells" / planned_cell.cell_id
    raw_dir = cell_dir / "raw"
    events_dir = cell_dir / "events"
    judge_dir = cell_dir / "judge"
    sealed_dir = cell_dir / "sealed"
    for directory in (raw_dir, events_dir, judge_dir, sealed_dir):
        directory.mkdir(parents=True, exist_ok=False)
    state_path = cell_dir / "cell-state.json"
    record = CellStateRecord(
        cell_id=planned_cell.cell_id,
        state=CellLifecycleState.PLANNED,
        history=[LifecycleEntry(state=CellLifecycleState.PLANNED, at=utc_now())],
    )
    _write_model(state_path, record)

    prepared = FixtureRestorer(source_repository, str(git_executable)).restore(
        fixture,
        cell_dir / "workspace",
    )
    prompt_path = raw_dir / "b0-fixed-prompt.md"
    prompt = (
        "# B0 manual benchmark prompt\n\n"
        f"작업 디렉터리: `{prepared.workspace}`\n\n"
        f"모델: `{model}`\n\n"
        f"reasoning effort: `{reasoning_effort}`\n\n"
        "새 Codex 세션을 위 작업 디렉터리에서 시작한 뒤 "
        "`benchmark-run.yaml`의 request, completion criteria, constraints를 읽고 작업하라.\n"
        "`.orchestrator/checks.yaml`과 `benchmark_checks/**`는 수정하지 마라. "
        "완료 주장을 독립 Judge가 다시 검사한다.\n"
    ).encode("utf-8")
    atomic_write(prompt_path, prompt)
    events_path = events_dir / "interventions.jsonl"
    adapter = B0ManualAdapter(
        B0AdapterConfig(
            workspace=prepared.workspace,
            prompt_path=prompt_path,
            events_path=events_path,
            input_provider=input_provider,
            expected_model=model,
            expected_reasoning_effort=reasoning_effort,
            expected_surface_kind=surface_kind,
        )
    )
    context = CellContext(
        experiment_id=plan.experiment_id,
        cell_id=planned_cell.cell_id,
    )
    preflight = adapter.preflight(context)
    if not preflight.ok:
        raise RuntimeError(f"B0 Adapter preflight failed: {preflight.detail}")
    record = _transition(record, CellLifecycleState.PREPARED)
    _write_model(state_path, record)
    record = _transition(record, CellLifecycleState.ACTIVE)
    _write_model(state_path, record)

    total_started = time.monotonic()
    variant_started = time.monotonic()
    variant_evidence = adapter.run(context)
    variant_seconds = time.monotonic() - variant_started
    adapter_path = raw_dir / "adapter-result.json"
    atomic_write(adapter_path, canonical_json_bytes(variant_evidence.raw_payload))
    submission = variant_evidence.raw_payload.get("submission")
    if isinstance(submission, dict) and isinstance(submission.get("attestation"), dict):
        atomic_write(
            raw_dir / "attestation.json",
            canonical_json_bytes(submission["attestation"]),
        )
    stop_required = bool(variant_evidence.raw_payload.get("stop_required", False))
    stop_reason_value = variant_evidence.raw_payload.get("stop_reason")
    stop_reason = str(stop_reason_value) if stop_reason_value is not None else None
    if stop_required:
        atomic_write(
            experiment_dir / "experiment-stop.json",
            canonical_json_bytes(
                {
                    "cell_id": planned_cell.cell_id,
                    "created_at": utc_now().isoformat(),
                    "stop_reason": stop_reason,
                }
            ),
        )
    record = _transition(
        record,
        CellLifecycleState.CAPTURED,
        outcome_state=variant_evidence.outcome_state,
    )
    _write_model(state_path, record)
    record = _transition(record, CellLifecycleState.JUDGING)
    _write_model(state_path, record)

    judge_started = time.monotonic()
    judge_result = FixtureJudge(benchmark_python, git_executable).evaluate(
        prepared,
        judge_dir,
    )
    judge_seconds = time.monotonic() - judge_started
    total_seconds = time.monotonic() - total_started
    if judge_result.final_tree is None:
        raise RuntimeError("R3 Judge did not produce a final tree")
    if not judge_result.check_success:
        stop_required = True
        stop_reason = stop_reason or "independent_judge_failed"
        atomic_write(
            experiment_dir / "experiment-stop.json",
            canonical_json_bytes(
                {
                    "cell_id": planned_cell.cell_id,
                    "created_at": utc_now().isoformat(),
                    "stop_reason": stop_reason,
                }
            ),
        )

    evidence_paths = sorted(
        [
            path
            for directory in (raw_dir, events_dir, judge_dir)
            for path in directory.rglob("*")
            if path.is_file()
        ],
        key=lambda path: path.relative_to(cell_dir).as_posix(),
    )
    evidence = [_evidence_ref(cell_dir, path) for path in evidence_paths]
    metrics = variant_evidence.normalized_metrics
    measurement_trusted = metrics.get("measurement_trusted") is True

    def event_metric(name: str, unit: str) -> MetricValue:
        if measurement_trusted and metrics.get(name) is not None:
            return _metric(
                MetricStatus.DERIVED,
                unit,
                value=metrics[name],
                source="b0_intervention_events",
                evidence_ref="events/interventions.jsonl",
            )
        return _metric(
            MetricStatus.UNKNOWN,
            unit,
            source="b0_intervention_events_unattested_or_invalid",
            evidence_ref="events/interventions.jsonl" if events_path.is_file() else None,
        )

    b0_artifact = next(item for item in plan.variants if item.artifact_id == "b0")
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
            manifest_sha256=manifest_sha256,
            fixture_source_commit=fixture.commit,
            fixture_tree_before=fixture.git_tree,
            fixture_tree_after=judge_result.final_tree,
            runner_commit=(
                f"{_git_head(source_repository, git_executable)}"
                f"+source-{runner_sha256[:12]}"
            ),
            variant_version=b0_artifact.version,
            variant_artifact_sha256=b0_artifact.sha256,
        ),
        environment=MeasurementEnvironment(
            os=platform.system().lower(),
            python_version=platform.python_version(),
            model=model,
            auth_method=auth_method,
            reasoning_effort=reasoning_effort,
            surface_kind=surface_kind,
            approval_mode=approval_mode,
            model_control="user_attested",
            reasoning_control="user_attested",
            treatment_control="partial",
        ),
        outcome=MeasurementOutcome(
            state=variant_evidence.outcome_state,
            failure_kind=(
                variant_evidence.failure_kind
                if variant_evidence.failure_kind
                else None if judge_result.check_success else "independent_judge_failed"
            ),
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
            startup_action_count=event_metric("startup_action_count", "count"),
            manual_copy_or_relay_count_excluding_start=event_metric(
                "manual_copy_or_relay_count_excluding_start", "count"
            ),
            manual_copy_or_relay_count_including_start=event_metric(
                "manual_copy_or_relay_count_including_start", "count"
            ),
            manual_recovery_count=event_metric("manual_recovery_count", "count"),
            manual_recovery_seconds=event_metric("manual_recovery_seconds", "seconds"),
        ),
        resource=MeasurementResource(
            session_count=event_metric("session_count", "count"),
            turn_count=event_metric("turn_count", "count"),
            attempt_count=event_metric("attempt_count", "count"),
            token_usage=_metric(
                MetricStatus.UNKNOWN,
                "tokens",
                source="b0_surface_did_not_supply_runtime_usage",
            ),
        ),
        quality=MeasurementQuality(
            errors_found_by_automatic_checks=_metric(
                MetricStatus.DERIVED,
                "count",
                value=len(judge_result.failed_check_ids),
                source="fixture_v1_judge",
                evidence_ref="judge/result.json",
            ),
            human_errors_after_pass=_metric(MetricStatus.NOT_APPLICABLE, "count"),
        ),
        integrity=MeasurementIntegrity(
            scope_ok=not judge_result.scope_violations,
            evidence_hashes_ok=True,
            secret_findings=[],
        ),
        evidence=evidence,
        variant_metrics=VariantMetrics(
            schema_id="b0-manual-sidecar/v1",
            values={
                "automated_launch": False,
                "runner_model_turns": 0,
                "event_count": metrics.get("event_count", 0),
                "measurement_trusted": measurement_trusted,
                "attestation_status": (
                    submission.get("attestation", {}).get("status")
                    if isinstance(submission, dict)
                    and isinstance(submission.get("attestation"), dict)
                    else "missing"
                ),
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
    return R3RunResult(
        experiment_id=plan.experiment_id,
        cell_id=planned_cell.cell_id,
        cell_state="SEALED",
        outcome_state=variant_evidence.outcome_state,
        check_success=judge_result.check_success,
        stop_required=stop_required,
        stop_reason=stop_reason,
        plan_path=str(plan_path),
        measurement_path=str(measurement_path),
        sealed_measurement_sha256=sealed_hash,
    )


class R4ControllerError(RuntimeError):
    pass


class R4ControllerLockedError(R4ControllerError):
    pass


class R4InjectedCrash(BaseException):
    """Fault-injection boundary that behaves like process death, not a handled failure."""


class R4CapturedCell(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome_state: OutcomeState
    stop_reason: str | None = None


class R4SealedCell(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome_state: OutcomeState
    sealed_measurement_sha256: str
    stop_reason: str | None = None


class R4CellDriver(Protocol):
    def id(self) -> str: ...

    def capabilities(self) -> VariantCapabilities: ...

    def prepare(self, plan: ExecutionPlan, cell: PlannedCell, cell_dir: Path) -> None: ...

    def invoke(
        self,
        plan: ExecutionPlan,
        cell: PlannedCell,
        cell_dir: Path,
        *,
        deadline_seconds: float,
    ) -> R4CapturedCell: ...

    def validate_captured(
        self,
        plan: ExecutionPlan,
        cell: PlannedCell,
        cell_dir: Path,
    ) -> R4CapturedCell: ...

    def recover_active(self, cell_dir: Path) -> None: ...

    def recover_judging(self, cell_dir: Path) -> None: ...

    def judge_and_seal(
        self,
        plan: ExecutionPlan,
        cell: PlannedCell,
        cell_dir: Path,
        captured: R4CapturedCell,
    ) -> R4SealedCell: ...


class R4ExperimentCreated(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    experiment_id: str
    experiment_dir: str
    plan_path: str
    planned_cells: int


class R4RunNextResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    experiment_id: str
    cell_id: str | None
    action: Literal["sealed", "stopped_active_crash", "no_cells_remaining"]
    display_state: ExperimentDisplayState
    stop_reason: str | None = None


def _process_start_identity(pid: int) -> str | None:
    if pid <= 0:
        return None
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            process_query_limited_information = 0x1000
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            kernel32.OpenProcess.restype = wintypes.HANDLE
            kernel32.GetProcessTimes.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(wintypes.FILETIME),
                ctypes.POINTER(wintypes.FILETIME),
                ctypes.POINTER(wintypes.FILETIME),
                ctypes.POINTER(wintypes.FILETIME),
            ]
            kernel32.GetProcessTimes.restype = wintypes.BOOL
            kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
            if not handle:
                return None
            creation = wintypes.FILETIME()
            exit_time = wintypes.FILETIME()
            kernel_time = wintypes.FILETIME()
            user_time = wintypes.FILETIME()
            try:
                if not kernel32.GetProcessTimes(
                    handle,
                    creation,
                    exit_time,
                    kernel_time,
                    user_time,
                ):
                    return None
                value = (creation.dwHighDateTime << 32) | creation.dwLowDateTime
                return f"windows-filetime:{value}"
            finally:
                kernel32.CloseHandle(handle)
        except (AttributeError, OSError, ValueError):
            return None
    proc_stat = Path(f"/proc/{pid}/stat")
    if proc_stat.is_file():
        try:
            value = proc_stat.read_text(encoding="ascii")
            remainder = value[value.rfind(")") + 2 :].split()
            return f"proc-start-ticks:{remainder[19]}"
        except (OSError, IndexError, ValueError):
            return None
    return None


def _process_is_alive(pid: int) -> bool:
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.OpenProcess.restype = wintypes.HANDLE
            handle = kernel32.OpenProcess(0x1000, False, pid)
            if not handle:
                return False
            exit_code = wintypes.DWORD()
            try:
                if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                    return False
                return exit_code.value == 259
            finally:
                kernel32.CloseHandle(handle)
        except (AttributeError, OSError, ValueError):
            return False
    proc_status = Path(f"/proc/{pid}/status")
    if proc_status.is_file():
        try:
            state = next(
                line for line in proc_status.read_text(encoding="ascii").splitlines() if line.startswith("State:")
            )
            if "Z" in state.split():
                return False
        except (OSError, StopIteration):
            pass
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _append_jsonl(path: Path, value: object) -> None:
    data = canonical_json_bytes(value) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


class _ControllerLock:
    def __init__(self, path: Path, record: ControllerLockRecord) -> None:
        self.path = path
        self.record = record

    @classmethod
    def acquire(cls, experiment_dir: Path, experiment_id: str) -> _ControllerLock:
        path = experiment_dir / "lock.json"
        process_identity = _process_start_identity(os.getpid()) or f"pid-fallback:{os.getpid()}"
        record = ControllerLockRecord(
            controller_id=f"ctl_{uuid.uuid4().hex}",
            pid=os.getpid(),
            hostname=socket.gethostname(),
            process_start_identity=process_identity,
            acquired_at=utc_now(),
            runner_version="lao-bench/0.1.0-r4",
            experiment_id=experiment_id,
        )
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as handle:
                handle.write(canonical_json_bytes(record))
                handle.flush()
                os.fsync(handle.fileno())
        except FileExistsError as exc:
            raise R4ControllerLockedError(f"Experiment controller lock exists: {path}") from exc
        return cls(path, record)

    def release(self) -> None:
        try:
            current = ControllerLockRecord.model_validate_json(self.path.read_bytes())
        except (OSError, ValueError) as exc:
            raise R4ControllerLockedError("Controller lock changed while held") from exc
        if current.controller_id != self.record.controller_id:
            raise R4ControllerLockedError("Controller does not own the current lock")
        self.path.unlink()

    def __enter__(self) -> _ControllerLock:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.release()


def initialize_r4_experiment(state_root: Path, plan: ExecutionPlan) -> R4ExperimentCreated:
    assert_plan_integrity(plan)
    experiment_dir = state_root.resolve() / plan.experiment_id
    experiment_dir.mkdir(parents=True, exist_ok=False)
    plan_path = experiment_dir / "execution-plan.json"
    _write_model(plan_path, plan)
    _write_model(experiment_dir / "experiment-control.json", ExperimentControl())
    _append_jsonl(
        experiment_dir / "events" / "lifecycle.jsonl",
        {
            "event": "experiment_created",
            "at": utc_now().isoformat(),
            "experiment_id": plan.experiment_id,
            "planned_cells": len(plan.cells),
        },
    )
    for cell in plan.cells:
        cell_dir = experiment_dir / "cells" / cell.cell_id
        cell_dir.mkdir(parents=True, exist_ok=False)
        _write_model(
            cell_dir / "cell-state.json",
            CellStateRecord(
                cell_id=cell.cell_id,
                state=CellLifecycleState.PLANNED,
                history=[LifecycleEntry(state=CellLifecycleState.PLANNED, at=utc_now())],
            ),
        )
    return R4ExperimentCreated(
        experiment_id=plan.experiment_id,
        experiment_dir=str(experiment_dir),
        plan_path=str(plan_path),
        planned_cells=len(plan.cells),
    )


def create_r4_experiment_from_manifest(
    *,
    state_root: Path,
    source_repository: Path,
    manifest_path: Path,
    runner_artifact: ArtifactIdentity,
    variant_artifacts: list[ArtifactIdentity],
    baseline_variant: str,
    candidate_variant: str,
    seed: int,
    primary_metrics: list[str],
    decision_policy: dict[str, object],
    reasoning_control: str,
    environment_fingerprint: dict[str, str],
    created_at: datetime | None = None,
    revision: int = 1,
) -> R4ExperimentCreated:
    source_repository = source_repository.resolve()
    manifest_path = manifest_path.resolve()
    manifest = load_frozen_manifest(manifest_path)
    if set(manifest.variants) != {baseline_variant, candidate_variant}:
        raise R4ControllerError("Manifest variants differ from the requested comparison")
    manifest_model = manifest.model.get("allowed")
    if manifest_model is not None and environment_fingerprint.get("model") != manifest_model:
        raise R4ControllerError("Plan model differs from the manifest")
    manifest_auth = manifest.model.get("auth_method")
    planned_auth = environment_fingerprint.get("auth_method")
    if manifest_auth is not None and planned_auth is not None and planned_auth != manifest_auth:
        raise R4ControllerError("Plan auth method differs from the manifest")
    try:
        relative_manifest = manifest_path.relative_to(source_repository).as_posix()
    except ValueError as exc:
        raise R4ControllerError("Manifest is outside the source repository") from exc
    plan = build_r4_plan(
        source_manifest_path=relative_manifest,
        source_manifest_sha256=sha256_file(manifest_path),
        fixtures=[
            FixtureIdentity(
                fixture_id=fixture.id,
                source_commit=fixture.commit,
                git_tree=fixture.git_tree,
            )
            for fixture in manifest.fixtures
        ],
        repetitions=manifest.repetitions,
        runner=runner_artifact,
        variants=variant_artifacts,
        baseline_variant=baseline_variant,
        candidate_variant=candidate_variant,
        seed=seed,
        primary_metrics=primary_metrics,
        decision_policy=decision_policy,
        reasoning_control=reasoning_control,
        environment_fingerprint=environment_fingerprint,
        created_at=created_at,
        revision=revision,
    )
    return initialize_r4_experiment(state_root, plan)


class R4ExperimentController:
    def __init__(
        self,
        *,
        experiment_dir: Path,
        source_repository: Path,
        manifest_path: Path,
        benchmark_python: Path,
        git_executable: Path,
        current_runner_sha256: str,
        current_variant_sha256: dict[str, str],
        drivers: dict[str, R4CellDriver],
        preflight_environment: dict[str, str | bool],
        fault_hook: Callable[[str, PlannedCell], None] | None = None,
    ) -> None:
        self.experiment_dir = experiment_dir.resolve()
        self.source_repository = source_repository.resolve()
        self.manifest_path = manifest_path.resolve()
        self.benchmark_python = benchmark_python.resolve()
        self.git_executable = git_executable.resolve()
        self.current_runner_sha256 = current_runner_sha256
        self.current_variant_sha256 = dict(current_variant_sha256)
        self.drivers = dict(drivers)
        self.preflight_environment = dict(preflight_environment)
        self.fault_hook = fault_hook

    @property
    def plan_path(self) -> Path:
        return self.experiment_dir / "execution-plan.json"

    @property
    def control_path(self) -> Path:
        return self.experiment_dir / "experiment-control.json"

    def _plan(self) -> ExecutionPlan:
        try:
            plan = ExecutionPlan.model_validate_json(self.plan_path.read_bytes())
            assert_plan_integrity(plan)
        except (OSError, ValueError) as exc:
            raise R4ControllerError("Execution Plan integrity check failed") from exc
        if plan.experiment_id != self.experiment_dir.name:
            raise R4ControllerError("Experiment directory does not match the Plan")
        return plan

    def _control(self) -> ExperimentControl:
        try:
            return ExperimentControl.model_validate_json(self.control_path.read_bytes())
        except (OSError, ValueError) as exc:
            raise R4ControllerError("Experiment control record is invalid") from exc

    def _write_control(self, control: ExperimentControl) -> None:
        _write_model(self.control_path, control)

    def _cell_state(self, cell: PlannedCell) -> CellStateRecord:
        path = self.experiment_dir / "cells" / cell.cell_id / "cell-state.json"
        try:
            record = CellStateRecord.model_validate_json(path.read_bytes())
        except (OSError, ValueError) as exc:
            raise R4ControllerError(f"Cell state is invalid: {cell.cell_id}") from exc
        if record.cell_id != cell.cell_id:
            raise R4ControllerError("Cell state identity mismatch")
        return record

    def _write_transition(
        self,
        cell: PlannedCell,
        record: CellStateRecord,
        target: CellLifecycleState,
        *,
        outcome_state: str | None = None,
        stop_reason: str | None = None,
        sealed_hash: str | None = None,
    ) -> CellStateRecord:
        if self.fault_hook:
            self.fault_hook(f"before_state:{target.value}", cell)
        updated = _transition(
            record,
            target,
            outcome_state=outcome_state,
            stop_reason=stop_reason,
            sealed_hash=sealed_hash,
        )
        state_path = self.experiment_dir / "cells" / cell.cell_id / "cell-state.json"
        _write_model(state_path, updated)
        if self.fault_hook:
            self.fault_hook(f"after_state:{target.value}", cell)
        _append_jsonl(
            self.experiment_dir / "cells" / cell.cell_id / "events" / "lifecycle.jsonl",
            {
                "at": updated.history[-1].at.isoformat(),
                "cell_id": cell.cell_id,
                "state": target.value,
            },
        )
        return updated

    def _record_stop(self, reason: str) -> ExperimentControl:
        control = self._control()
        if control.stop_reason is None:
            control = control.model_copy(update={"stop_reason": reason})
            self._write_control(control)
            _append_jsonl(
                self.experiment_dir / "events" / "lifecycle.jsonl",
                {"event": "experiment_stopped", "at": utc_now().isoformat(), "reason": reason},
            )
        return control

    def _assert_current_artifacts(self, plan: ExecutionPlan) -> None:
        if self.current_runner_sha256 != plan.runner.sha256:
            raise R4ControllerError("Runner artifact changed; create a new revision")
        expected = {item.artifact_id: item.sha256 for item in plan.variants}
        if self.current_variant_sha256 != expected:
            raise R4ControllerError("Variant artifacts changed; create a new revision")

    def _task_deadline_seconds(self) -> float:
        manifest = load_frozen_manifest(self.manifest_path)
        value = manifest.budgets.get("task_timeout_seconds")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            raise R4ControllerError("Manifest task timeout is missing or invalid")
        return float(value)

    def _preflight_valid(self, plan: ExecutionPlan, control: ExperimentControl) -> bool:
        record = control.preflight
        if record is None or record.plan_fingerprint != plan.plan_fingerprint:
            return False
        evidence_path = self.experiment_dir / Path(record.evidence_path)
        if not evidence_path.is_file() or sha256_file(evidence_path) != record.evidence_sha256:
            return False
        try:
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        return (
            isinstance(evidence, dict)
            and evidence.get("plan_fingerprint") == plan.plan_fingerprint
            and evidence.get("runner_sha256") == plan.runner.sha256
        )

    def preflight(self) -> PreflightRecord:
        plan = self._plan()
        with _ControllerLock.acquire(self.experiment_dir, plan.experiment_id):
            if any(
                self._cell_state(cell).state is not CellLifecycleState.PLANNED
                for cell in plan.cells
            ):
                raise R4ControllerError("Preflight cannot change after Cell execution begins")
            if os.environ.get("OPENAI_API_KEY"):
                raise R4ControllerError("OPENAI_API_KEY is present")
            if not self.benchmark_python.is_file() or not self.git_executable.is_file():
                raise R4ControllerError("Benchmark Python or Git executable is missing")
            if sha256_file(self.manifest_path) != plan.source_manifest.sha256:
                raise R4ControllerError("Source manifest bytes changed")
            try:
                manifest_relative = self.manifest_path.relative_to(self.source_repository).as_posix()
            except ValueError as exc:
                raise R4ControllerError("Manifest is outside the source repository") from exc
            if manifest_relative != plan.source_manifest.path:
                raise R4ControllerError("Manifest path differs from the Plan")
            self._assert_current_artifacts(plan)
            manifest = load_frozen_manifest(self.manifest_path)
            manifest_fixtures = {fixture.id: fixture for fixture in manifest.fixtures}
            restorer = FixtureRestorer(self.source_repository, str(self.git_executable))
            verified_trees: dict[str, str] = {}
            for fixture in plan.fixtures:
                source_fixture = manifest_fixtures.get(fixture.fixture_id)
                if source_fixture is None or (
                    source_fixture.commit != fixture.source_commit
                    or source_fixture.git_tree != fixture.git_tree
                ):
                    raise R4ControllerError("Fixture identity differs from the manifest")
                verified_trees[fixture.fixture_id] = restorer.verify_source(source_fixture)
            expected_variants = {variant.artifact_id for variant in plan.variants}
            if set(self.drivers) != expected_variants:
                raise R4ControllerError("Registered Cell drivers differ from the Plan")
            capabilities = {
                variant_id: {
                    "automated_launch": driver.capabilities().automated_launch,
                    "supports_usage": driver.capabilities().supports_usage,
                    "supports_attempt_count": driver.capabilities().supports_attempt_count,
                }
                for variant_id, driver in sorted(self.drivers.items())
                if driver.id() == variant_id
            }
            if set(capabilities) != expected_variants:
                raise R4ControllerError("Cell driver ID does not match its registry key")
            if self.preflight_environment.get("validated_without_model_turn") is not True:
                raise R4ControllerError("Model/auth preflight was not established without a turn")
            for key in ("model", "auth_method", "reasoning_effort", "surface_kind"):
                expected_value = plan.environment_fingerprint.get(key)
                if expected_value is not None and self.preflight_environment.get(key) != expected_value:
                    raise R4ControllerError(f"Preflight environment mismatch: {key}")
            python_result = subprocess.run(
                [str(self.benchmark_python), "-c", "import platform; print(platform.python_version())"],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            git_result = subprocess.run(
                [str(self.git_executable), "--version"],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if python_result.returncode != 0 or git_result.returncode != 0:
                raise R4ControllerError("Benchmark Python or Git preflight failed")
            if not python_result.stdout.strip().startswith("3.12."):
                raise R4ControllerError("Benchmark Python must be 3.12.x")
            disk_free = shutil.disk_usage(self.experiment_dir).free
            if disk_free < 64 * 1024 * 1024:
                raise R4ControllerError("Insufficient free disk space")
            evidence = {
                "schema_version": 1,
                "completed_at": utc_now().isoformat(),
                "plan_fingerprint": plan.plan_fingerprint,
                "runner_sha256": plan.runner.sha256,
                "variant_sha256": dict(sorted(self.current_variant_sha256.items())),
                "fixture_trees": dict(sorted(verified_trees.items())),
                "capabilities": capabilities,
                "python_executable": str(self.benchmark_python),
                "python_version": python_result.stdout.strip(),
                "git_executable": str(self.git_executable),
                "git_version": git_result.stdout.strip(),
                "disk_free_bytes": disk_free,
                "task_deadline_seconds": self._task_deadline_seconds(),
                "environment": self.preflight_environment,
                "actual_model_turns": 0,
            }
            evidence_path = self.experiment_dir / "preflight" / "evidence.json"
            atomic_write(evidence_path, canonical_json_bytes(evidence))
            record = PreflightRecord(
                completed_at=utc_now(),
                evidence_path=evidence_path.relative_to(self.experiment_dir).as_posix(),
                evidence_sha256=sha256_file(evidence_path),
                plan_fingerprint=plan.plan_fingerprint,
            )
            control = self._control().model_copy(update={"preflight": record})
            self._write_control(control)
            return record

    def status(self) -> ExperimentStatus:
        plan = self._plan()
        control = self._control()
        states = {cell.cell_id: self._cell_state(cell).state for cell in plan.cells}
        sealed = sum(state is CellLifecycleState.SEALED for state in states.values())
        next_cell = next(
            (cell.cell_id for cell in plan.cells if states[cell.cell_id] is not CellLifecycleState.SEALED),
            None,
        )
        if control.superseded_by:
            display = ExperimentDisplayState.SUPERSEDED
        elif control.stop_reason:
            display = ExperimentDisplayState.STOPPED
        elif sealed == len(plan.cells) and control.export_sha256:
            display = ExperimentDisplayState.FROZEN
        elif sealed == len(plan.cells) and control.analysis_sha256:
            display = ExperimentDisplayState.ANALYZED
        elif sealed == len(plan.cells):
            display = ExperimentDisplayState.COMPLETED
        elif any(
            state not in {CellLifecycleState.PLANNED, CellLifecycleState.SEALED}
            for state in states.values()
        ):
            display = ExperimentDisplayState.RUNNING
        elif self._preflight_valid(plan, control):
            display = ExperimentDisplayState.PREFLIGHTED
        else:
            display = ExperimentDisplayState.CREATED
        return ExperimentStatus(
            experiment_id=plan.experiment_id,
            display_state=display,
            stop_reason=control.stop_reason,
            sealed_cells=sealed,
            planned_cells=len(plan.cells),
            next_cell_id=next_cell,
            cell_states=states,
        )

    def _require_runnable(self, plan: ExecutionPlan) -> ExperimentControl:
        control = self._control()
        if control.superseded_by:
            raise R4ControllerError("Experiment was superseded")
        if control.stop_reason:
            raise R4ControllerError(f"Experiment is stopped: {control.stop_reason}")
        if not self._preflight_valid(plan, control):
            raise R4ControllerError("Valid preflight Evidence is required")
        try:
            self._assert_current_artifacts(plan)
        except R4ControllerError:
            self._record_stop("artifact_fingerprint_changed")
            raise
        return control

    def _capture_path(self, cell: PlannedCell) -> Path:
        return self.experiment_dir / "cells" / cell.cell_id / "raw" / "controller-capture.json"

    def _read_capture(self, cell: PlannedCell) -> R4CapturedCell:
        try:
            return R4CapturedCell.model_validate_json(self._capture_path(cell).read_bytes())
        except (OSError, ValueError) as exc:
            raise R4ControllerError("Captured Variant Evidence is missing or invalid") from exc

    def _stop_active_after_crash(
        self,
        plan: ExecutionPlan,
        cell: PlannedCell,
        record: CellStateRecord,
    ) -> R4RunNextResult:
        reason = "active_crash_requires_manual_recovery"
        recover_active = getattr(self.drivers[cell.variant_id], "recover_active", None)
        if callable(recover_active):
            try:
                recover_active(self.experiment_dir / "cells" / cell.cell_id)
            except Exception as exc:
                reason = f"active_crash_recovery_failed:{type(exc).__name__}"
        self._write_transition(
            cell,
            record,
            CellLifecycleState.STOPPED,
            outcome_state="infrastructure_error",
            stop_reason=reason,
        )
        self._record_stop(reason)
        return R4RunNextResult(
            experiment_id=plan.experiment_id,
            cell_id=cell.cell_id,
            action="stopped_active_crash",
            display_state=ExperimentDisplayState.STOPPED,
            stop_reason=reason,
        )

    def run_next(self) -> R4RunNextResult:
        plan = self._plan()
        with _ControllerLock.acquire(self.experiment_dir, plan.experiment_id):
            active = next(
                (
                    (cell, self._cell_state(cell))
                    for cell in plan.cells
                    if self._cell_state(cell).state is CellLifecycleState.ACTIVE
                ),
                None,
            )
            if active is not None:
                return self._stop_active_after_crash(plan, active[0], active[1])
            self._require_runnable(plan)
            cell = next(
                (cell for cell in plan.cells if self._cell_state(cell).state is not CellLifecycleState.SEALED),
                None,
            )
            if cell is None:
                return R4RunNextResult(
                    experiment_id=plan.experiment_id,
                    cell_id=None,
                    action="no_cells_remaining",
                    display_state=ExperimentDisplayState.COMPLETED,
                )
            record = self._cell_state(cell)
            if record.state is CellLifecycleState.STOPPED:
                raise R4ControllerError("STOPPED Cell requires explicit captured-Evidence decision")
            driver = self.drivers[cell.variant_id]
            cell_dir = self.experiment_dir / "cells" / cell.cell_id
            try:
                if record.state is CellLifecycleState.PLANNED:
                    driver.prepare(plan, cell, cell_dir)
                    record = self._write_transition(cell, record, CellLifecycleState.PREPARED)
                if record.state is CellLifecycleState.PREPARED:
                    record = self._write_transition(cell, record, CellLifecycleState.ACTIVE)
                    captured = driver.invoke(
                        plan,
                        cell,
                        cell_dir,
                        deadline_seconds=self._task_deadline_seconds(),
                    )
                    _write_model(self._capture_path(cell), captured)
                    record = self._write_transition(
                        cell,
                        record,
                        CellLifecycleState.CAPTURED,
                        outcome_state=captured.outcome_state,
                    )
                else:
                    captured = self._read_capture(cell)
                recovering_judge = record.state is CellLifecycleState.JUDGING
                if record.state is CellLifecycleState.CAPTURED:
                    record = self._write_transition(cell, record, CellLifecycleState.JUDGING)
                if record.state is not CellLifecycleState.JUDGING:
                    raise R4ControllerError(f"Cell cannot continue from {record.state}")
                if recovering_judge:
                    driver.recover_judging(cell_dir)
                sealed = driver.judge_and_seal(plan, cell, cell_dir, captured)
                if sealed.outcome_state != captured.outcome_state:
                    raise R4ControllerError("Sealed outcome differs from captured outcome")
                measurement_path = cell_dir / "sealed" / "measurement.json"
                if (
                    not measurement_path.is_file()
                    or sha256_file(measurement_path) != sealed.sealed_measurement_sha256
                ):
                    raise R4ControllerError("Driver returned an invalid Measurement seal")
                record = self._write_transition(
                    cell,
                    record,
                    CellLifecycleState.SEALED,
                    outcome_state=sealed.outcome_state,
                    sealed_hash=sealed.sealed_measurement_sha256,
                )
            except R4InjectedCrash:
                raise
            except Exception as exc:
                current = self._cell_state(cell)
                if current.state in {CellLifecycleState.ACTIVE, CellLifecycleState.JUDGING}:
                    reason = f"runner_exception:{type(exc).__name__}"
                    self._write_transition(
                        cell,
                        current,
                        CellLifecycleState.STOPPED,
                        outcome_state="infrastructure_error",
                        stop_reason=reason,
                    )
                    self._record_stop(reason)
                raise
            if sealed.stop_reason:
                self._record_stop(sealed.stop_reason)
            status = self.status()
            return R4RunNextResult(
                experiment_id=plan.experiment_id,
                cell_id=cell.cell_id,
                action="sealed",
                display_state=status.display_state,
                stop_reason=status.stop_reason,
            )

    def accept_stopped_capture(
        self,
        cell_id: str,
        *,
        decided_by: str,
        evidence: str,
    ) -> None:
        plan = self._plan()
        with _ControllerLock.acquire(self.experiment_dir, plan.experiment_id):
            cell = next((item for item in plan.cells if item.cell_id == cell_id), None)
            if cell is None:
                raise R4ControllerError("Unknown Cell")
            record = self._cell_state(cell)
            if record.state is not CellLifecycleState.STOPPED:
                raise R4ControllerError("Only a STOPPED Cell can accept captured Evidence")
            captured = self.drivers[cell.variant_id].validate_captured(plan, cell, self.experiment_dir / "cells" / cell.cell_id)
            _write_model(self._capture_path(cell), captured)
            self._write_transition(
                cell,
                record,
                CellLifecycleState.CAPTURED,
                outcome_state=captured.outcome_state,
            )
            _append_jsonl(
                self.experiment_dir / "events" / "lifecycle.jsonl",
                {
                    "event": "stopped_capture_accepted",
                    "at": utc_now().isoformat(),
                    "cell_id": cell_id,
                    "decided_by": decided_by,
                    "evidence": evidence,
                },
            )

    def resume(self, *, decided_by: str, decision: str, evidence: str) -> None:
        plan = self._plan()
        with _ControllerLock.acquire(self.experiment_dir, plan.experiment_id):
            control = self._control()
            if control.superseded_by:
                raise R4ControllerError("Superseded Experiment cannot resume")
            if not control.stop_reason:
                raise R4ControllerError("Experiment is not stopped")
            entry = StopHistoryEntry(
                reason=control.stop_reason,
                decision=decision,
                decided_by=decided_by,
                decided_at=utc_now(),
                evidence=evidence,
            )
            self._write_control(
                control.model_copy(
                    update={
                        "stop_reason": None,
                        "stop_history": [*control.stop_history, entry],
                    }
                )
            )

    def supersede(self, new_experiment_id: str, *, decided_by: str, evidence: str) -> None:
        plan = self._plan()
        with _ControllerLock.acquire(self.experiment_dir, plan.experiment_id):
            if new_experiment_id == plan.experiment_id or not new_experiment_id.startswith("exp_"):
                raise R4ControllerError("Invalid superseding Experiment ID")
            control = self._control()
            history = list(control.stop_history)
            if control.stop_reason:
                history.append(
                    StopHistoryEntry(
                        reason=control.stop_reason,
                        decision="superseded",
                        decided_by=decided_by,
                        decided_at=utc_now(),
                        evidence=evidence,
                    )
                )
            self._write_control(
                control.model_copy(
                    update={
                        "stop_history": history,
                        "superseded_by": new_experiment_id,
                    }
                )
            )

    @staticmethod
    def recover_unlock(experiment_dir: Path, *, confirm_no_controller: bool) -> ControllerLockRecord:
        path = experiment_dir.resolve() / "lock.json"
        try:
            record = ControllerLockRecord.model_validate_json(path.read_bytes())
        except (OSError, ValueError) as exc:
            raise R4ControllerLockedError("Controller lock is missing or invalid") from exc
        if not confirm_no_controller:
            raise R4ControllerLockedError("Explicit --confirm-no-controller is required")
        if record.hostname == socket.gethostname() and _process_is_alive(record.pid):
            current_identity = _process_start_identity(record.pid)
            if (
                record.process_start_identity.startswith("pid-fallback:")
                or current_identity is None
                or current_identity == record.process_start_identity
            ):
                raise R4ControllerLockedError("The recorded controller process is still alive")
        path.unlink()
        _append_jsonl(
            experiment_dir.resolve() / "events" / "lifecycle.jsonl",
            {
                "event": "stale_controller_lock_removed",
                "at": utc_now().isoformat(),
                "controller_id": record.controller_id,
                "confirmed": True,
            },
        )
        return record


class R5AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    experiment_id: str
    summary_path: str
    markdown_path: str
    analysis_sha256: str
    verdicts: dict[str, str]


class R5ExportResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    experiment_id: str
    results_root: str
    export_sha256: str
    file_count: int
    idempotent: bool


class R5ExportVerification(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    experiment_id: str
    export_sha256: str
    file_count: int
    cell_count: int
    verified: Literal[True] = True


def frozen_b0_b1_decision_policy() -> dict[str, object]:
    """Return the exact policy that must be frozen into the first B0/B1 Plan."""

    return {
        "policy_id": "b0-b1-v1",
        "candidate_variant": "b1",
        "quality_check_success": "fixture_noninferior",
        "candidate_minimum_total_check_success": 1,
        "human_errors_after_pass": (
            "candidate_total_not_greater_or_all_not_applicable"
        ),
        "candidate_integrity_failure": "reject",
        "baseline_integrity_failure": "inconclusive",
        "manual_relay_metric": "manual_copy_or_relay_count_excluding_start",
        "manual_relay_gate": "candidate_total_strictly_less",
        "manual_recovery_seconds_gate": "candidate_total_not_greater",
        "fixture_relay_median": "warning_only_if_candidate_greater",
        "nonterminal_outcome": "inconclusive",
        "required_metric_unknown": "inconclusive",
        "adopt_verdict": "ADOPT_B1",
        "reject_verdict": "REJECT_B1",
        "inconclusive_verdict": "INCONCLUSIVE",
    }


_R5_NUMERIC_METRICS = (
    "variant_execution_seconds",
    "judge_seconds",
    "total_wall_clock_seconds",
    "startup_action_count",
    "manual_copy_or_relay_count_excluding_start",
    "manual_copy_or_relay_count_including_start",
    "manual_recovery_count",
    "manual_recovery_seconds",
    "session_count",
    "turn_count",
    "attempt_count",
    "errors_found_by_automatic_checks",
    "human_errors_after_pass",
)


def _r5_metric(measurement: Measurement, name: str) -> MetricValue:
    containers = (measurement.effort, measurement.resource, measurement.quality)
    for container in containers:
        if name in type(container).model_fields:
            return getattr(container, name)
    raise KeyError(f"unknown R5 metric: {name}")


def _r5_metric_snapshot(metric: MetricValue) -> dict[str, object]:
    return {
        "status": metric.status.value,
        "value": metric.value,
        "unit": metric.unit,
    }


def _r5_numeric_value(metric: MetricValue, name: str) -> int | float | None:
    if metric.status not in {MetricStatus.MEASURED, MetricStatus.DERIVED}:
        return None
    value = metric.value
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise IntegrityError(f"R5 numeric metric has a non-number value: {name}")
    return value


def _r5_aggregate_numeric(
    measurements: list[Measurement],
    name: str,
) -> dict[str, object]:
    cells: list[dict[str, object]] = []
    known: list[int | float] = []
    statuses: list[MetricStatus] = []
    for measurement in sorted(
        measurements,
        key=lambda item: item.identity.execution_ordinal,
    ):
        metric = _r5_metric(measurement, name)
        value = _r5_numeric_value(metric, name)
        statuses.append(metric.status)
        if value is not None:
            known.append(value)
        cells.append(
            {
                "cell_id": measurement.identity.cell_id,
                "status": metric.status.value,
                "value": value,
            }
        )
    if statuses and all(status is MetricStatus.NOT_APPLICABLE for status in statuses):
        coverage = "not_applicable"
    elif statuses and all(
        status in {MetricStatus.MEASURED, MetricStatus.DERIVED} for status in statuses
    ):
        coverage = "complete"
    elif known:
        coverage = "partial_or_unknown"
    else:
        coverage = "unknown"
    result: dict[str, object] = {
        "coverage": coverage,
        "known_count": len(known),
        "cell_count": len(cells),
        "cells": cells,
    }
    if coverage == "complete":
        result["total"] = sum(known)
        result["median"] = statistics.median(known)
    elif known:
        result["known_subtotal"] = sum(known)
    return result


def _r5_aggregate_token_usage(measurements: list[Measurement]) -> dict[str, object]:
    cells: list[dict[str, object]] = []
    totals = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    complete = True
    known_count = 0
    for measurement in sorted(
        measurements,
        key=lambda item: item.identity.execution_ordinal,
    ):
        metric = measurement.resource.token_usage
        value = metric.value
        valid = (
            metric.status in {MetricStatus.MEASURED, MetricStatus.DERIVED}
            and isinstance(value, dict)
            and all(
                isinstance(value.get(key), int) and not isinstance(value.get(key), bool)
                for key in totals
            )
        )
        if valid:
            known_count += 1
            for key in totals:
                totals[key] += int(value[key])
        else:
            complete = False
        cells.append(
            {
                "cell_id": measurement.identity.cell_id,
                "status": metric.status.value,
                "value": value if valid else None,
            }
        )
    result: dict[str, object] = {
        "coverage": "complete" if complete else "partial_or_unknown",
        "known_count": known_count,
        "cell_count": len(cells),
        "cells": cells,
    }
    if complete:
        result["total"] = totals
    elif known_count:
        result["known_subtotal"] = totals
    return result


def _r5_integrity_failed(measurement: Measurement) -> bool:
    return (
        not measurement.integrity.scope_ok
        or not measurement.integrity.evidence_hashes_ok
        or bool(measurement.integrity.secret_findings)
    )


def _r5_gate(
    gate_id: str,
    status: Literal["pass", "fail", "inconclusive", "not_applicable"],
    detail: object,
) -> dict[str, object]:
    return {"gate_id": gate_id, "status": status, "detail": detail}


def _r5_pair_metric(
    baseline: Measurement,
    candidate: Measurement,
    name: str,
) -> dict[str, object]:
    baseline_metric = _r5_metric(baseline, name)
    candidate_metric = _r5_metric(candidate, name)
    baseline_value = _r5_numeric_value(baseline_metric, name)
    candidate_value = _r5_numeric_value(candidate_metric, name)
    return {
        "baseline": _r5_metric_snapshot(baseline_metric),
        "candidate": _r5_metric_snapshot(candidate_metric),
        "candidate_minus_baseline": (
            candidate_value - baseline_value
            if baseline_value is not None and candidate_value is not None
            else None
        ),
    }


def _r5_candidate_decision(
    plan: ExecutionPlan,
    measurements: list[Measurement],
    candidate_variant: str,
) -> dict[str, object]:
    policy = plan.decision_policy
    baseline = [
        item for item in measurements if item.identity.variant_id == plan.baseline_variant
    ]
    candidate = [
        item for item in measurements if item.identity.variant_id == candidate_variant
    ]
    gates: list[dict[str, object]] = []

    candidate_integrity = [
        item.identity.cell_id for item in candidate if _r5_integrity_failed(item)
    ]
    gates.append(
        _r5_gate(
            "candidate_integrity",
            "fail" if candidate_integrity else "pass",
            {"failed_cells": candidate_integrity},
        )
    )
    baseline_integrity = [
        item.identity.cell_id for item in baseline if _r5_integrity_failed(item)
    ]
    gates.append(
        _r5_gate(
            "baseline_integrity",
            "inconclusive" if baseline_integrity else "pass",
            {"failed_cells": baseline_integrity},
        )
    )

    nonterminal_states = {"blocked", "interrupted", "timed_out", "infrastructure_error"}
    nonterminal = [
        item.identity.cell_id
        for item in [*baseline, *candidate]
        if item.outcome.state in nonterminal_states
    ]
    gates.append(
        _r5_gate(
            "terminal_measurements",
            "inconclusive" if nonterminal else "pass",
            {"nonterminal_cells": nonterminal},
        )
    )

    fixture_quality: list[dict[str, object]] = []
    quality_failed = False
    for fixture in plan.fixtures:
        baseline_count = sum(
            item.outcome.check_success
            for item in baseline
            if item.identity.fixture_id == fixture.fixture_id
        )
        candidate_count = sum(
            item.outcome.check_success
            for item in candidate
            if item.identity.fixture_id == fixture.fixture_id
        )
        passed = candidate_count >= baseline_count
        quality_failed = quality_failed or not passed
        fixture_quality.append(
            {
                "fixture_id": fixture.fixture_id,
                "baseline_check_success_count": baseline_count,
                "candidate_check_success_count": candidate_count,
                "noninferior": passed,
            }
        )
    gates.append(
        _r5_gate(
            "fixture_quality_noninferiority",
            "fail" if quality_failed else "pass",
            fixture_quality,
        )
    )

    candidate_success_count = sum(item.outcome.check_success for item in candidate)
    minimum_success = int(policy["candidate_minimum_total_check_success"])
    gates.append(
        _r5_gate(
            "candidate_minimum_quality_evidence",
            "inconclusive" if candidate_success_count < minimum_success else "pass",
            {
                "candidate_check_success_count": candidate_success_count,
                "required_minimum": minimum_success,
            },
        )
    )

    baseline_human = _r5_aggregate_numeric(baseline, "human_errors_after_pass")
    candidate_human = _r5_aggregate_numeric(candidate, "human_errors_after_pass")
    if (
        baseline_human["coverage"] == "not_applicable"
        and candidate_human["coverage"] == "not_applicable"
    ):
        human_status = "not_applicable"
    elif (
        baseline_human["coverage"] != "complete"
        or candidate_human["coverage"] != "complete"
    ):
        human_status = "inconclusive"
    elif candidate_human["total"] > baseline_human["total"]:
        human_status = "fail"
    else:
        human_status = "pass"
    gates.append(
        _r5_gate(
            "human_errors_after_pass",
            human_status,
            {"baseline": baseline_human, "candidate": candidate_human},
        )
    )

    baseline_relay = _r5_aggregate_numeric(
        baseline,
        "manual_copy_or_relay_count_excluding_start",
    )
    candidate_relay = _r5_aggregate_numeric(
        candidate,
        "manual_copy_or_relay_count_excluding_start",
    )
    if (
        baseline_relay["coverage"] != "complete"
        or candidate_relay["coverage"] != "complete"
    ):
        relay_status = "inconclusive"
    elif candidate_relay["total"] < baseline_relay["total"]:
        relay_status = "pass"
    elif candidate_relay["total"] == baseline_relay["total"]:
        relay_status = "inconclusive"
    else:
        relay_status = "fail"
    gates.append(
        _r5_gate(
            "manual_relay_reduction",
            relay_status,
            {"baseline": baseline_relay, "candidate": candidate_relay},
        )
    )

    baseline_recovery = _r5_aggregate_numeric(baseline, "manual_recovery_seconds")
    candidate_recovery = _r5_aggregate_numeric(candidate, "manual_recovery_seconds")
    if (
        baseline_recovery["coverage"] != "complete"
        or candidate_recovery["coverage"] != "complete"
    ):
        recovery_status = "inconclusive"
    elif candidate_recovery["total"] <= baseline_recovery["total"]:
        recovery_status = "pass"
    else:
        recovery_status = "fail"
    gates.append(
        _r5_gate(
            "manual_recovery_not_greater",
            recovery_status,
            {"baseline": baseline_recovery, "candidate": candidate_recovery},
        )
    )

    warnings: list[str] = []
    for fixture in plan.fixtures:
        baseline_fixture = [
            item for item in baseline if item.identity.fixture_id == fixture.fixture_id
        ]
        candidate_fixture = [
            item for item in candidate if item.identity.fixture_id == fixture.fixture_id
        ]
        baseline_median = _r5_aggregate_numeric(
            baseline_fixture,
            "manual_copy_or_relay_count_excluding_start",
        )
        candidate_median = _r5_aggregate_numeric(
            candidate_fixture,
            "manual_copy_or_relay_count_excluding_start",
        )
        if (
            baseline_median["coverage"] == "complete"
            and candidate_median["coverage"] == "complete"
            and candidate_median["median"] > baseline_median["median"]
        ):
            warnings.append(
                f"fixture {fixture.fixture_id}: candidate relay median is worse than baseline"
            )

    gate_status = {item["gate_id"]: item["status"] for item in gates}
    if gate_status["candidate_integrity"] == "fail":
        verdict = str(policy["reject_verdict"])
    elif any(
        gate_status[gate] == "inconclusive"
        for gate in (
            "baseline_integrity",
            "terminal_measurements",
            "candidate_minimum_quality_evidence",
        )
    ):
        verdict = str(policy["inconclusive_verdict"])
    elif gate_status["fixture_quality_noninferiority"] == "fail":
        verdict = str(policy["reject_verdict"])
    elif gate_status["human_errors_after_pass"] == "fail":
        verdict = str(policy["reject_verdict"])
    elif gate_status["human_errors_after_pass"] == "inconclusive":
        verdict = str(policy["inconclusive_verdict"])
    elif gate_status["manual_relay_reduction"] == "fail":
        verdict = str(policy["reject_verdict"])
    elif gate_status["manual_relay_reduction"] == "inconclusive":
        verdict = str(policy["inconclusive_verdict"])
    elif gate_status["manual_recovery_not_greater"] == "fail":
        verdict = str(policy["reject_verdict"])
    elif gate_status["manual_recovery_not_greater"] == "inconclusive":
        verdict = str(policy["inconclusive_verdict"])
    else:
        verdict = str(policy["adopt_verdict"])
    return {
        "candidate_variant": candidate_variant,
        "verdict": verdict,
        "gates": gates,
        "warnings": warnings,
    }


def build_r5_summary(
    plan: ExecutionPlan,
    measurements: list[Measurement],
) -> dict[str, object]:
    """Derive a deterministic summary from a complete set of verified Measurements."""

    assert_plan_integrity(plan)
    if plan.decision_policy != frozen_b0_b1_decision_policy():
        raise IntegrityError("Execution Plan does not contain the frozen B0/B1 decision policy")
    if plan.candidate_variants != [str(plan.decision_policy["candidate_variant"])]:
        raise IntegrityError("R5 decision policy candidate differs from the Execution Plan")
    by_cell = {item.identity.cell_id: item for item in measurements}
    if len(by_cell) != len(measurements):
        raise IntegrityError("R5 Measurements contain duplicate Cell IDs")
    planned_ids = {cell.cell_id for cell in plan.cells}
    if set(by_cell) != planned_ids:
        raise IntegrityError("R5 requires exactly one Measurement for every planned Cell")
    for cell in plan.cells:
        measurement = by_cell[cell.cell_id]
        if (
            measurement.identity.experiment_id != plan.experiment_id
            or measurement.identity.block_id != cell.block_id
            or measurement.identity.fixture_id != cell.fixture_id
            or measurement.identity.repetition != cell.repetition
            or measurement.identity.variant_id != cell.variant_id
            or measurement.identity.execution_ordinal != cell.execution_ordinal
        ):
            raise IntegrityError("R5 Measurement identity differs from the Execution Plan")

    ordered = [by_cell[cell.cell_id] for cell in plan.cells]
    cell_results: list[dict[str, object]] = []
    trend: list[dict[str, object]] = []
    for measurement in ordered:
        metrics = {
            name: _r5_metric_snapshot(_r5_metric(measurement, name))
            for name in _R5_NUMERIC_METRICS
        }
        metrics["token_usage"] = _r5_metric_snapshot(measurement.resource.token_usage)
        cell_results.append(
            {
                "cell_id": measurement.identity.cell_id,
                "block_id": measurement.identity.block_id,
                "fixture_id": measurement.identity.fixture_id,
                "repetition": measurement.identity.repetition,
                "variant_id": measurement.identity.variant_id,
                "execution_ordinal": measurement.identity.execution_ordinal,
                "outcome_state": measurement.outcome.state,
                "failure_kind": measurement.outcome.failure_kind,
                "check_success": measurement.outcome.check_success,
                "integrity": measurement.integrity.model_dump(mode="json"),
                "treatment_control": measurement.environment.treatment_control,
                "metrics": metrics,
            }
        )
        trend.append(
            {
                "execution_ordinal": measurement.identity.execution_ordinal,
                "cell_id": measurement.identity.cell_id,
                "variant_id": measurement.identity.variant_id,
                "fixture_id": measurement.identity.fixture_id,
                "manual_copy_or_relay_count_excluding_start": metrics[
                    "manual_copy_or_relay_count_excluding_start"
                ],
                "variant_execution_seconds": metrics["variant_execution_seconds"],
                "total_wall_clock_seconds": metrics["total_wall_clock_seconds"],
            }
        )

    blocks: list[dict[str, object]] = []
    for block_id in sorted({cell.block_id for cell in plan.cells}):
        block_cells = [cell for cell in plan.cells if cell.block_id == block_id]
        fixture_ids = {cell.fixture_id for cell in block_cells}
        repetitions = {cell.repetition for cell in block_cells}
        if len(fixture_ids) != 1 or len(repetitions) != 1:
            raise IntegrityError("R5 Block identity is inconsistent")
        baseline_cell = next(
            (cell for cell in block_cells if cell.variant_id == plan.baseline_variant),
            None,
        )
        if baseline_cell is None:
            raise IntegrityError("R5 Block has no baseline Cell")
        comparisons: list[dict[str, object]] = []
        for candidate_variant in plan.candidate_variants:
            candidate_cell = next(
                (cell for cell in block_cells if cell.variant_id == candidate_variant),
                None,
            )
            if candidate_cell is None:
                raise IntegrityError("R5 Block has no candidate Cell")
            baseline_measurement = by_cell[baseline_cell.cell_id]
            candidate_measurement = by_cell[candidate_cell.cell_id]
            comparisons.append(
                {
                    "candidate_variant": candidate_variant,
                    "baseline_cell_id": baseline_cell.cell_id,
                    "candidate_cell_id": candidate_cell.cell_id,
                    "baseline_check_success": baseline_measurement.outcome.check_success,
                    "candidate_check_success": candidate_measurement.outcome.check_success,
                    "metrics": {
                        name: _r5_pair_metric(
                            baseline_measurement,
                            candidate_measurement,
                            name,
                        )
                        for name in (
                            "manual_copy_or_relay_count_excluding_start",
                            "manual_recovery_seconds",
                            "variant_execution_seconds",
                            "total_wall_clock_seconds",
                        )
                    },
                }
            )
        blocks.append(
            {
                "block_id": block_id,
                "fixture_id": next(iter(fixture_ids)),
                "repetition": next(iter(repetitions)),
                "comparisons": comparisons,
            }
        )

    aggregates: dict[str, object] = {}
    for variant in [plan.baseline_variant, *plan.candidate_variants]:
        variant_measurements = [
            item for item in ordered if item.identity.variant_id == variant
        ]
        outcome_counts = {
            state: sum(item.outcome.state == state for item in variant_measurements)
            for state in (
                "completed",
                "failed",
                "blocked",
                "interrupted",
                "timed_out",
                "infrastructure_error",
            )
        }
        aggregates[variant] = {
            "cell_count": len(variant_measurements),
            "outcome_counts": outcome_counts,
            "check_success_count": sum(
                item.outcome.check_success for item in variant_measurements
            ),
            "check_failure_count": sum(
                not item.outcome.check_success for item in variant_measurements
            ),
            "metrics": {
                name: _r5_aggregate_numeric(variant_measurements, name)
                for name in _R5_NUMERIC_METRICS
            }
            | {"token_usage": _r5_aggregate_token_usage(variant_measurements)},
        }

    decisions = [
        _r5_candidate_decision(plan, ordered, candidate)
        for candidate in plan.candidate_variants
    ]
    treatment_controls = sorted(
        {measurement.environment.treatment_control for measurement in ordered}
    )
    limits = [
        "This 2-fixture x 3-repetition experiment is a local directional gate, not proof of universal superiority.",
        "Execution-order trends are descriptive; the balanced order does not remove learning effects.",
    ]
    if treatment_controls != ["full"]:
        limits.append(
            "Treatment control is not fully established, so results compare practical workflows and not orchestration alone."
        )
    return {
        "schema_version": 1,
        "kind": "comparison_summary",
        "producer": PRODUCER,
        "experiment_id": plan.experiment_id,
        "plan_fingerprint": plan.plan_fingerprint,
        "baseline_variant": plan.baseline_variant,
        "candidate_variants": plan.candidate_variants,
        "decision_policy": plan.decision_policy,
        "cell_results": cell_results,
        "blocks": blocks,
        "aggregates": aggregates,
        "decisions": decisions,
        "execution_ordinal_trend": trend,
        "treatment_control_values": treatment_controls,
        "interpretation_limits": limits,
    }


def render_r5_summary_markdown(summary: dict[str, object]) -> bytes:
    decisions = summary["decisions"]
    aggregates = summary["aggregates"]
    lines = [
        f"# B0/B1 비교 결과 — {summary['experiment_id']}",
        "",
        f"- Plan fingerprint: `{summary['plan_fingerprint']}`",
        f"- 기준 방식: `{summary['baseline_variant']}`",
        "",
        "## 판정",
        "",
    ]
    for decision in decisions:
        lines.append(
            f"- `{decision['candidate_variant']}`: **{decision['verdict']}**"
        )
        for gate in decision["gates"]:
            lines.append(f"  - {gate['gate_id']}: `{gate['status']}`")
        for warning in decision["warnings"]:
            lines.append(f"  - 경고: {warning}")
    lines.extend(["", "## 전체 집계", "", "| 방식 | Cell | Judge 성공 | 실패·중단 |", "|---|---:|---:|---:|"])
    for variant in [summary["baseline_variant"], *summary["candidate_variants"]]:
        aggregate = aggregates[variant]
        non_completed = aggregate["cell_count"] - aggregate["outcome_counts"]["completed"]
        lines.append(
            f"| {variant} | {aggregate['cell_count']} | {aggregate['check_success_count']} | {non_completed} |"
        )
    lines.extend(
        [
            "",
            "## 실행 순서 추세",
            "",
            "| 순서 | 방식 | fixture | 시작 제외 사람 중계 | Variant 시간(초) | 전체 시간(초) |",
            "|---:|---|---|---:|---:|---:|",
        ]
    )
    for point in summary["execution_ordinal_trend"]:
        def display(metric: dict[str, object]) -> object:
            return metric["value"] if metric["value"] is not None else metric["status"]

        lines.append(
            "| {ordinal} | {variant} | {fixture} | {relay} | {variant_seconds} | {total_seconds} |".format(
                ordinal=point["execution_ordinal"],
                variant=point["variant_id"],
                fixture=point["fixture_id"],
                relay=display(point["manual_copy_or_relay_count_excluding_start"]),
                variant_seconds=display(point["variant_execution_seconds"]),
                total_seconds=display(point["total_wall_clock_seconds"]),
            )
        )
    lines.extend(["", "## 해석 한계", ""])
    lines.extend(f"- {item}" for item in summary["interpretation_limits"])
    return ("\n".join(lines) + "\n").encode("utf-8")


def analyze_r5_experiment(experiment_dir: Path) -> R5AnalysisResult:
    root = experiment_dir.resolve()
    try:
        plan = ExecutionPlan.model_validate_json((root / "execution-plan.json").read_bytes())
        assert_plan_integrity(plan)
        control = ExperimentControl.model_validate_json(
            (root / "experiment-control.json").read_bytes()
        )
    except (OSError, ValueError) as exc:
        raise IntegrityError("R5 experiment records are missing or invalid") from exc
    if root.name != plan.experiment_id:
        raise IntegrityError("R5 experiment directory differs from the Plan")
    if control.superseded_by:
        raise IntegrityError("R5 cannot analyze a superseded Experiment")
    with _ControllerLock.acquire(root, plan.experiment_id):
        measurements = [
            verify_sealed_cell(root / "cells" / cell.cell_id) for cell in plan.cells
        ]
        summary = build_r5_summary(plan, measurements)
        summary_bytes = canonical_json_bytes(summary)
        markdown_bytes = render_r5_summary_markdown(summary)
        summary_path = root / "analysis" / "summary.json"
        markdown_path = root / "analysis" / "summary.md"
        for path, data in ((summary_path, summary_bytes), (markdown_path, markdown_bytes)):
            if path.exists() and path.read_bytes() != data:
                raise IntegrityError("Existing R5 analysis differs from deterministic output")
            atomic_write(path, data)
        analysis_sha256 = sha256_bytes(summary_bytes)
        current_control = ExperimentControl.model_validate_json(
            (root / "experiment-control.json").read_bytes()
        )
        if (
            current_control.analysis_sha256 is not None
            and current_control.analysis_sha256 != analysis_sha256
        ):
            raise IntegrityError("Experiment analysis seal differs from the current summary")
        _write_model(
            root / "experiment-control.json",
            current_control.model_copy(update={"analysis_sha256": analysis_sha256}),
        )
    return R5AnalysisResult(
        experiment_id=plan.experiment_id,
        summary_path=str(summary_path),
        markdown_path=str(markdown_path),
        analysis_sha256=analysis_sha256,
        verdicts={
            str(item["candidate_variant"]): str(item["verdict"])
            for item in summary["decisions"]
        },
    )


_R5_SENSITIVE_TEXT = (
    ("OpenAI-style secret", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b")),
    ("bearer token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]{16,}")),
    (
        "credential field",
        re.compile(
            r"(?i)[\"'](?:api[_-]?key|access[_-]?token|refresh[_-]?token)[\"']\s*:\s*[\"'][^\"']+[\"']"
        ),
    ),
    ("email address", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("Windows home path", re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s\"']+")),
    ("POSIX home path", re.compile(r"/(?:home|Users)/[^/\s\"']+")),
)


def _r5_assert_export_safe(relative_path: str, data: bytes) -> None:
    normalized = relative_path.replace("\\", "/")
    parts = tuple(part.lower() for part in normalized.split("/"))
    if (
        ".." in parts
        or ".git" in parts
        or "variant-state" in parts
        or "auth.json" in parts
        or normalized.startswith("/")
        or re.match(r"^[A-Za-z]:/", normalized)
    ):
        raise IntegrityError(f"R5 export contains a forbidden path: {relative_path}")
    if "sdk-stream" in normalized.lower() or "environment-dump" in normalized.lower():
        raise IntegrityError(f"R5 export contains a forbidden raw artifact: {relative_path}")
    text = data.decode("utf-8", errors="ignore")
    scan_text = text.replace("\\\\", "\\")
    if "auth.json" in scan_text.lower():
        raise IntegrityError(f"R5 export mentions auth.json: {relative_path}")
    for label, pattern in _R5_SENSITIVE_TEXT:
        if pattern.search(scan_text):
            raise IntegrityError(
                f"R5 sealed Evidence is not export-safe ({label}): {relative_path}; "
                "redact before sealing and create a new revision"
            )


def _r5_export_digest(files: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for relative_path in sorted(files):
        data = files[relative_path]
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(hashlib.sha256(data).digest())
    return digest.hexdigest()


def _r5_target_files(results_root: Path, plan: ExecutionPlan) -> set[str]:
    roots = [results_root / "comparisons" / plan.experiment_id]
    roots.extend(
        results_root / variant / plan.experiment_id
        for variant in [plan.baseline_variant, *plan.candidate_variants]
    )
    files: set[str] = set()
    for root in roots:
        if root.exists() and not root.is_dir():
            raise IntegrityError(f"R5 export target is not a directory: {root}")
        if root.is_dir():
            for path in root.rglob("*"):
                if path.is_symlink():
                    raise IntegrityError(f"R5 export target contains a symlink: {path}")
                if path.is_file():
                    files.add(path.relative_to(results_root).as_posix())
    return files


def _r5_source_measurements(
    experiment_dir: Path,
    plan: ExecutionPlan,
) -> tuple[list[Measurement], dict[str, CellStateRecord]]:
    measurements: list[Measurement] = []
    states: dict[str, CellStateRecord] = {}
    for cell in plan.cells:
        cell_dir = experiment_dir / "cells" / cell.cell_id
        measurement = verify_sealed_cell(cell_dir)
        state = CellStateRecord.model_validate_json(
            (cell_dir / "cell-state.json").read_bytes()
        )
        measurements.append(measurement)
        states[cell.cell_id] = state
    return measurements, states


def _r5_expected_export(
    *,
    results_root: Path,
    experiment_dir: Path,
    plan: ExecutionPlan,
    measurements: list[Measurement],
    states: dict[str, CellStateRecord],
    summary: dict[str, object],
) -> dict[str, bytes]:
    expected: dict[str, bytes] = {}
    comparison_prefix = f"comparisons/{plan.experiment_id}"
    expected[f"{comparison_prefix}/execution-plan.json"] = canonical_json_bytes(plan)
    expected[f"{comparison_prefix}/summary.json"] = canonical_json_bytes(summary)
    expected[f"{comparison_prefix}/summary.md"] = render_r5_summary_markdown(summary)
    seals: list[dict[str, object]] = []
    by_cell = {item.identity.cell_id: item for item in measurements}
    for cell in sorted(plan.cells, key=lambda item: item.cell_id):
        measurement = by_cell[cell.cell_id]
        state = states[cell.cell_id]
        if state.sealed_measurement_sha256 is None:
            raise IntegrityError("R5 source Cell has no Measurement seal")
        source_measurement = (
            experiment_dir / "cells" / cell.cell_id / "sealed" / "measurement.json"
        ).read_bytes()
        if sha256_bytes(source_measurement) != state.sealed_measurement_sha256:
            raise IntegrityError("R5 source Measurement differs from its Cell seal")
        cell_prefix = f"{cell.variant_id}/{plan.experiment_id}/{cell.cell_id}"
        measurement_relative = f"{cell_prefix}/sealed/measurement.json"
        expected[measurement_relative] = source_measurement
        for evidence in measurement.evidence:
            source_path = experiment_dir / "cells" / cell.cell_id / Path(evidence.path)
            data = source_path.read_bytes()
            destination_relative = f"{cell_prefix}/{evidence.path}"
            if destination_relative in expected:
                raise IntegrityError("R5 export path collision")
            expected[destination_relative] = data
        sealed_entry = next(
            (
                entry
                for entry in reversed(state.history)
                if entry.state is CellLifecycleState.SEALED
            ),
            None,
        )
        if sealed_entry is None:
            raise IntegrityError("R5 source Cell has no SEALED lifecycle entry")
        seals.append(
            {
                "cell_id": cell.cell_id,
                "variant_id": cell.variant_id,
                "measurement_path": measurement_relative,
                "sealed_measurement_sha256": state.sealed_measurement_sha256,
                "sealed_at": sealed_entry.at.isoformat(),
            }
        )
    expected[f"{comparison_prefix}/seals.json"] = canonical_json_bytes(
        {
            "schema_version": 1,
            "kind": "measurement_seals",
            "producer": PRODUCER,
            "experiment_id": plan.experiment_id,
            "plan_fingerprint": plan.plan_fingerprint,
            "entries": seals,
        }
    )
    for relative_path, data in expected.items():
        _r5_assert_export_safe(relative_path, data)
        destination = (results_root / Path(relative_path)).resolve()
        if not destination.is_relative_to(results_root):
            raise IntegrityError("R5 export path escaped the results root")
    return expected


def export_r5_experiment(
    experiment_dir: Path,
    results_root: Path,
) -> R5ExportResult:
    experiment_dir = experiment_dir.resolve()
    results_root = results_root.resolve()
    try:
        plan = ExecutionPlan.model_validate_json(
            (experiment_dir / "execution-plan.json").read_bytes()
        )
        assert_plan_integrity(plan)
        control = ExperimentControl.model_validate_json(
            (experiment_dir / "experiment-control.json").read_bytes()
        )
    except (OSError, ValueError) as exc:
        raise IntegrityError("R5 export source is missing or invalid") from exc
    if experiment_dir.name != plan.experiment_id:
        raise IntegrityError("R5 export directory differs from the Plan")
    if control.analysis_sha256 is None:
        raise IntegrityError("R5 export requires a sealed analysis")
    with _ControllerLock.acquire(experiment_dir, plan.experiment_id):
        measurements, states = _r5_source_measurements(experiment_dir, plan)
        summary = build_r5_summary(plan, measurements)
        summary_bytes = canonical_json_bytes(summary)
        markdown_bytes = render_r5_summary_markdown(summary)
        if sha256_bytes(summary_bytes) != control.analysis_sha256:
            raise IntegrityError("R5 analysis seal differs from the current Measurements")
        if (
            (experiment_dir / "analysis" / "summary.json").read_bytes() != summary_bytes
            or (experiment_dir / "analysis" / "summary.md").read_bytes() != markdown_bytes
        ):
            raise IntegrityError("R5 analysis files are not deterministic derivatives")
        expected = _r5_expected_export(
            results_root=results_root,
            experiment_dir=experiment_dir,
            plan=plan,
            measurements=measurements,
            states=states,
            summary=summary,
        )
        actual_before = _r5_target_files(results_root, plan)
        extra = actual_before - set(expected)
        if extra:
            raise IntegrityError(f"R5 export target contains unexpected files: {sorted(extra)}")
        idempotent = bool(actual_before) and actual_before == set(expected)
        for relative_path, data in expected.items():
            destination = results_root / Path(relative_path)
            if destination.exists():
                if not destination.is_file() or destination.read_bytes() != data:
                    raise IntegrityError(
                        f"Existing R5 export differs from deterministic output: {relative_path}"
                    )
            else:
                atomic_write(destination, data)
        actual_after = _r5_target_files(results_root, plan)
        if actual_after != set(expected):
            raise IntegrityError("R5 export did not produce the exact expected file set")
        for relative_path, data in expected.items():
            if (results_root / Path(relative_path)).read_bytes() != data:
                raise IntegrityError(f"R5 export verification failed: {relative_path}")
        export_sha256 = _r5_export_digest(expected)
        current_control = ExperimentControl.model_validate_json(
            (experiment_dir / "experiment-control.json").read_bytes()
        )
        if (
            current_control.export_sha256 is not None
            and current_control.export_sha256 != export_sha256
        ):
            raise IntegrityError("Experiment export seal differs from deterministic output")
        _write_model(
            experiment_dir / "experiment-control.json",
            current_control.model_copy(update={"export_sha256": export_sha256}),
        )
    verification = verify_r5_export(results_root, plan.experiment_id)
    if verification.export_sha256 != export_sha256:
        raise IntegrityError("Independent R5 export verification disagreed with export")
    return R5ExportResult(
        experiment_id=plan.experiment_id,
        results_root=str(results_root),
        export_sha256=export_sha256,
        file_count=len(expected),
        idempotent=idempotent,
    )


def verify_r5_export(results_root: Path, experiment_id: str) -> R5ExportVerification:
    results_root = results_root.resolve()
    comparison_dir = results_root / "comparisons" / experiment_id
    try:
        plan = ExecutionPlan.model_validate_json(
            (comparison_dir / "execution-plan.json").read_bytes()
        )
        assert_plan_integrity(plan)
        seals = json.loads((comparison_dir / "seals.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise IntegrityError("R5 exported Plan or seals index is invalid") from exc
    if plan.experiment_id != experiment_id:
        raise IntegrityError("R5 exported Plan identity mismatch")
    if not isinstance(seals, dict) or set(seals) != {
        "schema_version",
        "kind",
        "producer",
        "experiment_id",
        "plan_fingerprint",
        "entries",
    }:
        raise IntegrityError("R5 seals index fields are invalid")
    if (
        seals["schema_version"] != 1
        or seals["kind"] != "measurement_seals"
        or seals["producer"] != PRODUCER
        or seals["experiment_id"] != plan.experiment_id
        or seals["plan_fingerprint"] != plan.plan_fingerprint
        or not isinstance(seals["entries"], list)
    ):
        raise IntegrityError("R5 seals index identity is invalid")
    entries = seals["entries"]
    if [entry.get("cell_id") for entry in entries if isinstance(entry, dict)] != sorted(
        cell.cell_id for cell in plan.cells
    ):
        raise IntegrityError("R5 seals entries do not match all planned Cells")
    by_cell = {cell.cell_id: cell for cell in plan.cells}
    measurements: list[Measurement] = []
    expected_paths = {
        f"comparisons/{experiment_id}/execution-plan.json",
        f"comparisons/{experiment_id}/seals.json",
        f"comparisons/{experiment_id}/summary.json",
        f"comparisons/{experiment_id}/summary.md",
    }
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {
            "cell_id",
            "variant_id",
            "measurement_path",
            "sealed_measurement_sha256",
            "sealed_at",
        }:
            raise IntegrityError("R5 seal entry fields are invalid")
        cell_id = entry["cell_id"]
        cell = by_cell.get(cell_id)
        if cell is None or entry["variant_id"] != cell.variant_id:
            raise IntegrityError("R5 seal entry Cell identity is invalid")
        measurement_relative = entry["measurement_path"]
        expected_measurement_relative = (
            f"{cell.variant_id}/{experiment_id}/{cell.cell_id}/sealed/measurement.json"
        )
        if measurement_relative != expected_measurement_relative:
            raise IntegrityError("R5 seal Measurement path is invalid")
        measurement_path = (results_root / Path(measurement_relative)).resolve()
        if not measurement_path.is_relative_to(results_root) or not measurement_path.is_file():
            raise IntegrityError("R5 exported Measurement is missing")
        measurement_bytes = measurement_path.read_bytes()
        if sha256_bytes(measurement_bytes) != entry["sealed_measurement_sha256"]:
            raise IntegrityError("R5 exported Measurement hash differs from seals.json")
        measurement = Measurement.model_validate_json(measurement_bytes)
        if measurement.identity.cell_id != cell.cell_id:
            raise IntegrityError("R5 exported Measurement Cell identity differs")
        cell_root = measurement_path.parents[1]
        for evidence in measurement.evidence:
            evidence_path = (cell_root / Path(evidence.path)).resolve()
            if not evidence_path.is_relative_to(cell_root) or not evidence_path.is_file():
                raise IntegrityError("R5 exported Evidence is missing or unsafe")
            data = evidence_path.read_bytes()
            if len(data) != evidence.size or sha256_bytes(data) != evidence.sha256:
                raise IntegrityError("R5 exported Evidence differs from Measurement")
            relative = evidence_path.relative_to(results_root).as_posix()
            _r5_assert_export_safe(relative, data)
            expected_paths.add(relative)
        _r5_assert_export_safe(measurement_relative, measurement_bytes)
        expected_paths.add(measurement_relative)
        measurements.append(measurement)
    summary = build_r5_summary(plan, measurements)
    summary_bytes = canonical_json_bytes(summary)
    markdown_bytes = render_r5_summary_markdown(summary)
    if (comparison_dir / "summary.json").read_bytes() != summary_bytes:
        raise IntegrityError("R5 exported JSON summary is not deterministic")
    if (comparison_dir / "summary.md").read_bytes() != markdown_bytes:
        raise IntegrityError("R5 exported Markdown summary is not deterministic")
    actual_paths = _r5_target_files(results_root, plan)
    if actual_paths != expected_paths:
        raise IntegrityError("R5 export contains missing or unexpected files")
    files = {
        relative: (results_root / Path(relative)).read_bytes()
        for relative in expected_paths
    }
    for relative, data in files.items():
        _r5_assert_export_safe(relative, data)
    return R5ExportVerification(
        experiment_id=experiment_id,
        export_sha256=_r5_export_digest(files),
        file_count=len(files),
        cell_count=len(measurements),
    )


class R6PreparedRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fixture: FrozenFixtureSpec
    checks: ChecksFile
    write_scopes: list[str]
    protected_hashes: list[tuple[str, str]]


class R6ScriptedB0Config(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    writes: dict[str, str]
    interventions: list[str]
    outcome_state: Literal["completed", "failed", "blocked", "interrupted"] = "completed"
    delay_seconds: float = 0.0


class R6SidecarConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    variant_id: Literal["b0", "b1"]
    experiment_id: str
    cell_id: str
    workspace: str
    prompt_path: str | None = None
    events_path: str
    model: str
    reasoning_effort: str
    surface_kind: str
    b0_scripted: R6ScriptedB0Config | None = None
    b1_command_prefix: tuple[str, ...] = ()
    b1_state_root: str | None = None
    b1_schema_root: str | None = None
    b1_runtime: Literal["fake", "codex"] = "codex"
    b1_fake_fixture: str | None = None
    b1_pythonpath: str | None = None


class R6VariantEvidenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    variant_id: Literal["b0", "b1"]
    experiment_id: str
    cell_id: str
    outcome_state: OutcomeState
    failure_kind: str | None
    attempt_count: int
    raw_payload: dict[str, object]
    normalized_metrics: dict[str, object]
    variant_execution_seconds: float


class _R6ScriptedB0Provider:
    def __init__(self, config: R6ScriptedB0Config, controls: R6SidecarConfig) -> None:
        self.config = config
        self.controls = controls

    def collect(self, session: B0ManualSession) -> B0ManualSubmission:
        if self.config.delay_seconds < 0:
            raise ValueError("scripted B0 delay cannot be negative")
        if self.config.delay_seconds:
            time.sleep(self.config.delay_seconds)
        for relative_path, content in sorted(self.config.writes.items()):
            validate_relative_path(relative_path)
            destination = (session.workspace / Path(relative_path)).resolve()
            if not destination.is_relative_to(session.workspace.resolve()):
                raise ValueError("scripted B0 write escaped its workspace")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8", newline="\n")
        for intervention in self.config.interventions:
            session.recorder.record(intervention)  # type: ignore[arg-type]
        if self.config.outcome_state == "interrupted":
            session.recorder.record("abort")
        return B0ManualSubmission(
            outcome_state=self.config.outcome_state,
            attestation=B0Attestation(
                status="confirmed",
                confirmed_at=utc_now(),
                timeline_complete=True,
                model=self.controls.model,
                reasoning_effort=self.controls.reasoning_effort,
                surface_kind=self.controls.surface_kind,
            ),
        )


def run_r6_adapter_sidecar(config_path: Path, result_path: Path) -> None:
    """Internal bounded-process entrypoint used by the R6 live Cell drivers."""

    config = R6SidecarConfig.model_validate_json(config_path.read_bytes())
    workspace = Path(config.workspace).resolve()
    events_path = Path(config.events_path).resolve()
    context = CellContext(
        experiment_id=config.experiment_id,
        cell_id=config.cell_id,
    )
    if config.variant_id == "b0":
        if config.prompt_path is None:
            raise ValueError("R6 B0 sidecar requires a fixed prompt")
        provider: B0ManualInputProvider = (
            _R6ScriptedB0Provider(config.b0_scripted, config)
            if config.b0_scripted is not None
            else ConsoleB0ManualInputProvider(
                expected_model=config.model,
                expected_reasoning_effort=config.reasoning_effort,
                expected_surface_kind=config.surface_kind,
            )
        )
        adapter: VariantAdapter = B0ManualAdapter(
            B0AdapterConfig(
                workspace=workspace,
                prompt_path=Path(config.prompt_path).resolve(),
                events_path=events_path,
                input_provider=provider,
                expected_model=config.model,
                expected_reasoning_effort=config.reasoning_effort,
                expected_surface_kind=config.surface_kind,
            )
        )
    else:
        if not config.b1_command_prefix or config.b1_state_root is None or config.b1_schema_root is None:
            raise ValueError("R6 B1 sidecar configuration is incomplete")
        if config.b1_pythonpath:
            existing = os.environ.get("PYTHONPATH")
            os.environ["PYTHONPATH"] = os.pathsep.join(
                value for value in (config.b1_pythonpath, existing) if value
            )
        adapter = B1SequentialAdapter(
            B1AdapterConfig(
                command_prefix=tuple(config.b1_command_prefix),
                project=workspace,
                run_spec=workspace / "benchmark-run.yaml",
                state_root=Path(config.b1_state_root).resolve(),
                schema_root=Path(config.b1_schema_root).resolve(),
                runtime=config.b1_runtime,
                fake_fixture=(
                    Path(config.b1_fake_fixture).resolve()
                    if config.b1_fake_fixture is not None
                    else None
                ),
                timeout_seconds=24 * 60 * 60,
            )
        )
    preflight = adapter.preflight(context)
    if not preflight.ok:
        raise RuntimeError(f"R6 Adapter preflight failed: {preflight.detail}")
    started = time.monotonic()
    evidence: VariantEvidence = adapter.run(context)
    elapsed = time.monotonic() - started
    record = R6VariantEvidenceRecord(
        variant_id=config.variant_id,
        experiment_id=config.experiment_id,
        cell_id=config.cell_id,
        outcome_state=evidence.outcome_state,
        failure_kind=evidence.failure_kind,
        attempt_count=evidence.attempt_count,
        raw_payload=evidence.raw_payload,
        normalized_metrics=evidence.normalized_metrics,
        variant_execution_seconds=elapsed,
    )
    atomic_write(result_path.resolve(), canonical_json_bytes(record))


def _r6_redact_object(
    value: object,
    replacements: dict[str, str],
    findings: set[str],
) -> object:
    if isinstance(value, dict):
        return {
            str(key): _r6_redact_object(item, replacements, findings)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_r6_redact_object(item, replacements, findings) for item in value]
    if not isinstance(value, str):
        return value
    redacted = value
    for source, replacement in sorted(
        replacements.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        if source:
            redacted = redacted.replace(source, replacement)
            redacted = redacted.replace(source.replace("\\", "\\\\"), replacement)
    for label, pattern in _R5_SENSITIVE_TEXT:
        if pattern.search(redacted):
            if label in {"OpenAI-style secret", "bearer token", "credential field"}:
                findings.add(label)
                replacement = "<REDACTED_SECRET>"
            elif label == "email address":
                replacement = "<REDACTED_EMAIL>"
            else:
                replacement = "<HOME>"
            redacted = pattern.sub(replacement, redacted)
    redacted = re.sub(r"(?i)auth\.json", "<AUTH_FILE>", redacted)
    return redacted


def _r6_redact_bytes(
    data: bytes,
    replacements: dict[str, str],
    findings: set[str],
) -> bytes:
    try:
        value = json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError):
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            return data
        redacted = _r6_redact_object(text, replacements, findings)
        assert isinstance(redacted, str)
        return redacted.encode("utf-8")
    return canonical_json_bytes(_r6_redact_object(value, replacements, findings))


class _R6CellDriverBase:
    variant_id: Literal["b0", "b1"]

    def __init__(
        self,
        *,
        source_repository: Path,
        manifest_path: Path,
        benchmark_python: Path,
        git_executable: Path,
        runner_python: Path,
        model: str,
        reasoning_effort: str,
        surface_kind: str,
        auth_method: str,
        approval_mode: str,
        model_control: str,
        reasoning_control: str,
        treatment_control: Literal["full", "partial", "not_applicable"],
    ) -> None:
        self.source_repository = source_repository.resolve()
        self.manifest_path = manifest_path.resolve()
        self.benchmark_python = benchmark_python.resolve()
        self.git_executable = git_executable.resolve()
        self.runner_python = runner_python.resolve()
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.surface_kind = surface_kind
        self.auth_method = auth_method
        self.approval_mode = approval_mode
        self.model_control = model_control
        self.reasoning_control = reasoning_control
        self.treatment_control = treatment_control

    def id(self) -> str:
        return self.variant_id

    def _fixture(self, plan: ExecutionPlan, cell: PlannedCell) -> FrozenFixtureSpec:
        manifest = load_frozen_manifest(self.manifest_path)
        try:
            fixture = next(item for item in manifest.fixtures if item.id == cell.fixture_id)
            planned = next(item for item in plan.fixtures if item.fixture_id == cell.fixture_id)
        except StopIteration as exc:
            raise R4ControllerError("R6 Cell fixture is not declared") from exc
        if (
            fixture.commit != planned.source_commit
            or fixture.git_tree != planned.git_tree
            or sha256_file(self.manifest_path) != plan.source_manifest.sha256
        ):
            raise R4ControllerError("R6 fixture or manifest identity differs from the Plan")
        return fixture

    @staticmethod
    def _prepared_record_path(cell_dir: Path) -> Path:
        return cell_dir / "raw" / "prepared-fixture.json"

    def _prepared(self, cell_dir: Path) -> PreparedFixture:
        try:
            record = R6PreparedRecord.model_validate_json(
                self._prepared_record_path(cell_dir).read_bytes()
            )
        except (OSError, ValueError) as exc:
            raise R4ControllerError("R6 prepared fixture record is missing or invalid") from exc
        return PreparedFixture(
            fixture=record.fixture,
            workspace=(cell_dir / "workspace").resolve(),
            checks=record.checks,
            write_scopes=tuple(record.write_scopes),
            protected_hashes=tuple(record.protected_hashes),
        )

    def prepare(self, plan: ExecutionPlan, cell: PlannedCell, cell_dir: Path) -> None:
        if cell.variant_id != self.variant_id:
            raise R4ControllerError("R6 driver received another Variant's Cell")
        fixture = self._fixture(plan, cell)
        restorer = FixtureRestorer(self.source_repository, str(self.git_executable))
        workspace = cell_dir / "workspace"
        record_path = self._prepared_record_path(cell_dir)
        if workspace.is_dir():
            prepared = restorer.open_existing(fixture, workspace, require_clean=True)
        else:
            temporary = cell_dir / f".prepare-{uuid.uuid4().hex}"
            prepared_temporary = restorer.restore(fixture, temporary)
            os.replace(temporary, workspace)
            prepared = PreparedFixture(
                fixture=prepared_temporary.fixture,
                workspace=workspace.resolve(),
                checks=prepared_temporary.checks,
                write_scopes=prepared_temporary.write_scopes,
                protected_hashes=prepared_temporary.protected_hashes,
            )
        record = R6PreparedRecord(
            fixture=prepared.fixture,
            checks=prepared.checks,
            write_scopes=list(prepared.write_scopes),
            protected_hashes=list(prepared.protected_hashes),
        )
        if record_path.exists() and R6PreparedRecord.model_validate_json(
            record_path.read_bytes()
        ) != record:
            raise R4ControllerError("R6 prepared fixture metadata changed")
        atomic_write(record_path, canonical_json_bytes(record))
        self._prepare_variant(plan, cell, cell_dir, prepared)

    def _prepare_variant(
        self,
        plan: ExecutionPlan,
        cell: PlannedCell,
        cell_dir: Path,
        prepared: PreparedFixture,
    ) -> None:
        raise NotImplementedError

    def _sidecar_config(
        self,
        plan: ExecutionPlan,
        cell: PlannedCell,
        cell_dir: Path,
    ) -> R6SidecarConfig:
        raise NotImplementedError

    @staticmethod
    def _process_dir(cell_dir: Path) -> Path:
        return cell_dir / "variant-state" / "sidecar-process"

    @staticmethod
    def _result_path(cell_dir: Path) -> Path:
        return cell_dir / "variant-state" / "adapter-result.json"

    def _write_public_capture(
        self,
        cell_dir: Path,
        record: R6VariantEvidenceRecord,
    ) -> set[str]:
        replacements = {
            str((cell_dir / "workspace").resolve()): "<WORKSPACE>",
            str((cell_dir / "variant-state").resolve()): "<VARIANT_STATE>",
            str(self.source_repository): "<SOURCE_REPOSITORY>",
            str(Path.home().resolve()): "<HOME>",
        }
        findings: set[str] = set()
        redacted = _r6_redact_object(record.raw_payload, replacements, findings)
        raw_dir = cell_dir / "raw"
        atomic_write(raw_dir / "adapter-result.json", canonical_json_bytes(redacted))
        if isinstance(redacted, dict):
            submission = redacted.get("submission")
            if isinstance(submission, dict) and isinstance(submission.get("attestation"), dict):
                atomic_write(
                    raw_dir / "attestation.json",
                    canonical_json_bytes(submission["attestation"]),
                )
        atomic_write(
            raw_dir / "redaction-report.json",
            canonical_json_bytes(
                {
                    "schema_version": 1,
                    "secret_categories": sorted(findings),
                    "source_bytes_changed": redacted != record.raw_payload,
                }
            ),
        )
        return findings

    def invoke(
        self,
        plan: ExecutionPlan,
        cell: PlannedCell,
        cell_dir: Path,
        *,
        deadline_seconds: float,
    ) -> R4CapturedCell:
        config = self._sidecar_config(plan, cell, cell_dir)
        config_path = cell_dir / "variant-state" / "sidecar-config.json"
        result_path = self._result_path(cell_dir)
        atomic_write(config_path, canonical_json_bytes(config))
        if self.variant_id == "b1":
            event = InterventionEvent(
                created_at=utc_now(),
                event_id=f"evt_{cell.cell_id}_b1_start",
                cell_id=cell.cell_id,
                timestamp=utc_now(),
                monotonic_offset_seconds=0.0,
                intervention_kind="b1_start",
                actor="user",
            )
            _append_jsonl(cell_dir / "events" / "interventions.jsonl", event)
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONUTF8"] = "1"
        environment["PYTHONIOENCODING"] = "utf-8"
        environment["PYTHONPATH"] = os.pathsep.join(
            value for value in [*map(str, sys.path), environment.get("PYTHONPATH", "")] if value
        )
        popen_options: dict[str, object] = {}
        if os.name == "nt":
            popen_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            popen_options["start_new_session"] = True
        process = subprocess.Popen(
            [
                str(self.runner_python),
                "-m",
                "benchmark_runner",
                "internal-run-adapter",
                "--config",
                str(config_path),
                "--result",
                str(result_path),
            ],
            env=environment,
            shell=False,
            **popen_options,
        )
        identity = _process_start_identity(process.pid)
        if identity is None:
            process.kill()
            process.wait(timeout=5)
            raise R4ControllerError("R6 could not establish sidecar process identity")
        process_record = JudgeProcessRecord(
            check_id=f"variant:{self.variant_id}",
            pid=process.pid,
            process_start_identity=identity,
            process_group_kind=(
                "windows_new_process_group" if os.name == "nt" else "posix_session"
            ),
            status="running",
            started_at=utc_now().isoformat(),
        )
        _write_process_record(
            self._process_dir(cell_dir) / "active-process.json",
            process_record,
        )
        timed_out = False
        try:
            process.wait(timeout=deadline_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            recover_orphan_judge_process(self._process_dir(cell_dir))
            process.wait(timeout=5)
        if not timed_out:
            _write_process_record(
                self._process_dir(cell_dir) / "active-process.json",
                process_record.model_copy(
                    update={"status": "completed", "completed_at": utc_now().isoformat()}
                ),
            )
        if timed_out:
            record = R6VariantEvidenceRecord(
                variant_id=self.variant_id,
                experiment_id=plan.experiment_id,
                cell_id=cell.cell_id,
                outcome_state="timed_out",
                failure_kind=f"{self.variant_id}_deadline_exceeded",
                attempt_count=0,
                raw_payload={
                    "adapter_id": self.variant_id,
                    "cell_id": cell.cell_id,
                    "stop_required": True,
                    "stop_reason": f"{self.variant_id}_deadline_exceeded",
                },
                normalized_metrics={},
                variant_execution_seconds=deadline_seconds,
            )
            atomic_write(result_path, canonical_json_bytes(record))
        elif process.returncode != 0 or not result_path.is_file():
            record = R6VariantEvidenceRecord(
                variant_id=self.variant_id,
                experiment_id=plan.experiment_id,
                cell_id=cell.cell_id,
                outcome_state="infrastructure_error",
                failure_kind=f"{self.variant_id}_sidecar_failed",
                attempt_count=0,
                raw_payload={
                    "adapter_id": self.variant_id,
                    "cell_id": cell.cell_id,
                    "sidecar_exit_code": process.returncode,
                    "stop_required": True,
                    "stop_reason": f"{self.variant_id}_sidecar_failed",
                },
                normalized_metrics={},
                variant_execution_seconds=0.0,
            )
            atomic_write(result_path, canonical_json_bytes(record))
        else:
            record = R6VariantEvidenceRecord.model_validate_json(result_path.read_bytes())
        if (
            record.variant_id != self.variant_id
            or record.experiment_id != plan.experiment_id
            or record.cell_id != cell.cell_id
        ):
            raise R4ControllerError("R6 sidecar result identity mismatch")
        self._write_public_capture(cell_dir, record)
        stop_reason = record.raw_payload.get("stop_reason")
        return R4CapturedCell(
            outcome_state=record.outcome_state,
            stop_reason=str(stop_reason) if stop_reason else None,
        )

    def validate_captured(
        self,
        plan: ExecutionPlan,
        cell: PlannedCell,
        cell_dir: Path,
    ) -> R4CapturedCell:
        process_path = self._process_dir(cell_dir) / "active-process.json"
        if process_path.is_file():
            process = JudgeProcessRecord.model_validate_json(process_path.read_bytes())
            if (
                process.status == "running"
                and _process_is_alive(process.pid)
                and _process_start_identity(process.pid) == process.process_start_identity
            ):
                raise R4ControllerError("R6 Variant sidecar is still running")
        try:
            record = R6VariantEvidenceRecord.model_validate_json(
                self._result_path(cell_dir).read_bytes()
            )
        except (OSError, ValueError) as exc:
            raise R4ControllerError("R6 terminal Variant capture is missing") from exc
        if record.experiment_id != plan.experiment_id or record.cell_id != cell.cell_id:
            raise R4ControllerError("R6 terminal Variant capture identity mismatch")
        self._write_public_capture(cell_dir, record)
        stop_reason = record.raw_payload.get("stop_reason")
        return R4CapturedCell(
            outcome_state=record.outcome_state,
            stop_reason=str(stop_reason) if stop_reason else None,
        )

    def recover_active(self, cell_dir: Path) -> None:
        recover_orphan_judge_process(self._process_dir(cell_dir))

    def recover_judging(self, cell_dir: Path) -> None:
        recover_orphan_judge_process(cell_dir / "judge")

    def _redact_public_evidence(self, cell_dir: Path) -> set[str]:
        replacements = {
            str((cell_dir / "workspace").resolve()): "<WORKSPACE>",
            str((cell_dir / "variant-state").resolve()): "<VARIANT_STATE>",
            str(self.source_repository): "<SOURCE_REPOSITORY>",
            str(Path.home().resolve()): "<HOME>",
        }
        findings: set[str] = set()
        for directory in (cell_dir / "raw", cell_dir / "events", cell_dir / "judge"):
            if not directory.is_dir():
                continue
            for path in sorted(item for item in directory.rglob("*") if item.is_file()):
                data = path.read_bytes()
                redacted = _r6_redact_bytes(data, replacements, findings)
                if redacted != data:
                    atomic_write(path, redacted)
        return findings

    def judge_and_seal(
        self,
        plan: ExecutionPlan,
        cell: PlannedCell,
        cell_dir: Path,
        captured: R4CapturedCell,
    ) -> R4SealedCell:
        prepared = self._prepared(cell_dir)
        record = R6VariantEvidenceRecord.model_validate_json(
            self._result_path(cell_dir).read_bytes()
        )
        judge_started = time.monotonic()
        judge_result = FixtureJudge(
            self.benchmark_python,
            self.git_executable,
        ).evaluate(prepared, cell_dir / "judge")
        judge_seconds = time.monotonic() - judge_started
        if judge_result.final_tree is None:
            raise R4ControllerError("R6 Judge did not produce a final tree")
        findings = self._redact_public_evidence(cell_dir)
        evidence_paths = sorted(
            [
                path
                for directory in (cell_dir / "raw", cell_dir / "events", cell_dir / "judge")
                if directory.is_dir()
                for path in directory.rglob("*")
                if path.is_file()
                and path != cell_dir / "events" / "lifecycle.jsonl"
            ],
            key=lambda path: path.relative_to(cell_dir).as_posix(),
        )
        evidence = [_evidence_ref(cell_dir, path) for path in evidence_paths]
        metrics = record.normalized_metrics

        def numeric_metric(
            name: str,
            unit: str,
            *,
            source: str,
            evidence_ref: str | None = None,
        ) -> MetricValue:
            value = metrics.get(name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return _metric(
                    MetricStatus.UNKNOWN,
                    unit,
                    source=source,
                    evidence_ref=evidence_ref,
                )
            return _metric(
                MetricStatus.DERIVED,
                unit,
                value=value,
                source=source,
                evidence_ref=evidence_ref,
            )

        if self.variant_id == "b0":
            trusted = metrics.get("measurement_trusted") is True

            def b0_metric(name: str, unit: str) -> MetricValue:
                if trusted:
                    return numeric_metric(
                        name,
                        unit,
                        source="b0_intervention_events",
                        evidence_ref="events/interventions.jsonl",
                    )
                return _metric(
                    MetricStatus.UNKNOWN,
                    unit,
                    source="b0_intervention_events_unattested_or_invalid",
                    evidence_ref=(
                        "events/interventions.jsonl"
                        if (cell_dir / "events" / "interventions.jsonl").is_file()
                        else None
                    ),
                )

            startup = b0_metric("startup_action_count", "count")
            relay_excluding = b0_metric(
                "manual_copy_or_relay_count_excluding_start", "count"
            )
            relay_including = b0_metric(
                "manual_copy_or_relay_count_including_start", "count"
            )
            recovery_count = b0_metric("manual_recovery_count", "count")
            recovery_seconds = b0_metric("manual_recovery_seconds", "seconds")
            session_count = b0_metric("session_count", "count")
            turn_count = b0_metric("turn_count", "count")
            attempt_count = b0_metric("attempt_count", "count")
            token_usage = _metric(
                MetricStatus.UNKNOWN,
                "tokens",
                source="b0_surface_did_not_supply_runtime_usage",
            )
            variant_values = {
                "automated_launch": False,
                "event_count": metrics.get("event_count", 0),
                "measurement_trusted": trusted,
            }
        else:
            startup = _metric(
                MetricStatus.DERIVED,
                "count",
                value=1,
                source="intervention_events",
                evidence_ref="events/interventions.jsonl",
            )
            relay_excluding = _metric(
                MetricStatus.DERIVED,
                "count",
                value=0,
                source="intervention_events",
                evidence_ref="events/interventions.jsonl",
            )
            relay_including = _metric(
                MetricStatus.DERIVED,
                "count",
                value=1,
                source="intervention_events",
                evidence_ref="events/interventions.jsonl",
            )
            recovery_count = _metric(
                MetricStatus.DERIVED,
                "count",
                value=0,
                source="intervention_events",
                evidence_ref="events/interventions.jsonl",
            )
            recovery_seconds = _metric(
                MetricStatus.DERIVED,
                "seconds",
                value=0.0,
                source="intervention_events",
                evidence_ref="events/interventions.jsonl",
            )
            session_count = numeric_metric(
                "session_count", "count", source="b1_public_run_report"
            )
            turn_count = numeric_metric(
                "turn_count", "count", source="b1_public_run_report"
            )
            attempt_count = numeric_metric(
                "attempt_count", "count", source="b1_public_run_report"
            )
            token_value = metrics.get("token_usage")
            token_usage = (
                _metric(
                    MetricStatus.MEASURED,
                    "tokens",
                    value=token_value,
                    source="b1_public_run_report",
                )
                if metrics.get("token_usage_status") == "measured"
                and isinstance(token_value, dict)
                else _metric(
                    MetricStatus.UNKNOWN,
                    "tokens",
                    source="b1_public_run_report_partial_or_unknown",
                )
            )
            variant_values = {
                "b1_report_usage_status": metrics.get("b1_report_usage_status"),
                "b1_session_usage_statuses": metrics.get(
                    "b1_session_usage_statuses", []
                ),
                "b1_token_usage_raw": metrics.get("b1_token_usage_raw"),
                "runtime": record.raw_payload.get("runtime"),
                "actual_model_turns": record.raw_payload.get("actual_model_turns"),
            }
        fixture = self._fixture(plan, cell)
        artifact = next(
            item for item in plan.variants if item.artifact_id == self.variant_id
        )
        adapter_stop = record.raw_payload.get("stop_reason")
        stop_reason = str(adapter_stop) if adapter_stop else None
        if not judge_result.check_success and stop_reason is None:
            stop_reason = "independent_judge_failed"
        measurement = Measurement(
            created_at=utc_now(),
            identity=MeasurementIdentity(
                experiment_id=plan.experiment_id,
                block_id=cell.block_id,
                cell_id=cell.cell_id,
                fixture_id=cell.fixture_id,
                repetition=cell.repetition,
                variant_id=cell.variant_id,
                execution_ordinal=cell.execution_ordinal,
            ),
            provenance=MeasurementProvenance(
                manifest_sha256=plan.source_manifest.sha256,
                fixture_source_commit=fixture.commit,
                fixture_tree_before=fixture.git_tree,
                fixture_tree_after=judge_result.final_tree,
                runner_commit=plan.runner.version,
                variant_version=artifact.version,
                variant_artifact_sha256=artifact.sha256,
            ),
            environment=MeasurementEnvironment(
                os=platform.system().lower(),
                python_version=platform.python_version(),
                model=self.model,
                auth_method=self.auth_method,
                reasoning_effort=self.reasoning_effort,
                surface_kind=self.surface_kind,
                approval_mode=self.approval_mode,
                model_control=self.model_control,
                reasoning_control=self.reasoning_control,
                treatment_control=self.treatment_control,
            ),
            outcome=MeasurementOutcome(
                state=captured.outcome_state,
                failure_kind=(
                    record.failure_kind
                    if record.failure_kind
                    else None if judge_result.check_success else "independent_judge_failed"
                ),
                check_success=judge_result.check_success,
            ),
            effort=MeasurementEffort(
                variant_execution_seconds=_metric(
                    MetricStatus.MEASURED,
                    "seconds",
                    value=record.variant_execution_seconds,
                    source="runner_sidecar_monotonic_clock",
                ),
                judge_seconds=_metric(
                    MetricStatus.MEASURED,
                    "seconds",
                    value=judge_seconds,
                    source="runner_monotonic_clock",
                ),
                total_wall_clock_seconds=_metric(
                    MetricStatus.DERIVED,
                    "seconds",
                    value=record.variant_execution_seconds + judge_seconds,
                    source="variant_plus_judge_seconds",
                ),
                startup_action_count=startup,
                manual_copy_or_relay_count_excluding_start=relay_excluding,
                manual_copy_or_relay_count_including_start=relay_including,
                manual_recovery_count=recovery_count,
                manual_recovery_seconds=recovery_seconds,
            ),
            resource=MeasurementResource(
                session_count=session_count,
                turn_count=turn_count,
                attempt_count=attempt_count,
                token_usage=token_usage,
            ),
            quality=MeasurementQuality(
                errors_found_by_automatic_checks=_metric(
                    MetricStatus.DERIVED,
                    "count",
                    value=len(judge_result.failed_check_ids),
                    source="fixture_v1_judge",
                    evidence_ref="judge/result.json",
                ),
                human_errors_after_pass=_metric(
                    MetricStatus.NOT_APPLICABLE,
                    "count",
                ),
            ),
            integrity=MeasurementIntegrity(
                scope_ok=not judge_result.scope_violations,
                evidence_hashes_ok=True,
                secret_findings=sorted(findings),
            ),
            evidence=evidence,
            variant_metrics=VariantMetrics(
                schema_id=f"{self.variant_id}-r6-driver/v1",
                values=variant_values,
            ),
        )
        measurement_path = cell_dir / "sealed" / "measurement.json"
        measurement_bytes = canonical_json_bytes(measurement)
        atomic_write(measurement_path, measurement_bytes)
        sealed_hash = sha256_bytes(measurement_bytes)
        verify_model = Measurement.model_validate_json(measurement_bytes)
        if verify_model.identity.cell_id != cell.cell_id:
            raise R4ControllerError("R6 sealed Measurement identity mismatch")
        return R4SealedCell(
            outcome_state=captured.outcome_state,
            sealed_measurement_sha256=sealed_hash,
            stop_reason=stop_reason,
        )


class R6B0ManualDriver(_R6CellDriverBase):
    variant_id: Literal["b0"] = "b0"

    def __init__(
        self,
        *,
        scripted_by_fixture: dict[str, R6ScriptedB0Config] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)  # type: ignore[arg-type]
        self.scripted_by_fixture = dict(scripted_by_fixture or {})

    def capabilities(self) -> VariantCapabilities:
        return VariantCapabilities(
            automated_launch=False,
            supports_usage=False,
            supports_attempt_count=True,
        )

    @staticmethod
    def _prompt_bytes() -> bytes:
        return (
            "# B0 manual benchmark prompt\n\n"
            "Sidecar가 표시한 전용 workspace에서 새 Codex 작업을 시작하라.\n\n"
            "`benchmark-run.yaml`의 request, completion criteria, constraints를 읽고 작업하라.\n"
            "`.orchestrator/checks.yaml`과 `benchmark_checks/**`는 수정하지 마라.\n"
            "완료 주장은 독립 Judge가 다시 검사한다.\n"
        ).encode("utf-8")

    def _prepare_variant(
        self,
        plan: ExecutionPlan,
        cell: PlannedCell,
        cell_dir: Path,
        prepared: PreparedFixture,
    ) -> None:
        prompt_path = cell_dir / "raw" / "b0-fixed-prompt.md"
        if prompt_path.exists() and prompt_path.read_bytes() != self._prompt_bytes():
            raise R4ControllerError("R6 B0 fixed prompt changed")
        atomic_write(prompt_path, self._prompt_bytes())
        adapter = B0ManualAdapter(
            B0AdapterConfig(
                workspace=prepared.workspace,
                prompt_path=prompt_path,
                events_path=cell_dir / "events" / "interventions.jsonl",
                input_provider=ConsoleB0ManualInputProvider(
                    expected_model=self.model,
                    expected_reasoning_effort=self.reasoning_effort,
                    expected_surface_kind=self.surface_kind,
                ),
                expected_model=self.model,
                expected_reasoning_effort=self.reasoning_effort,
                expected_surface_kind=self.surface_kind,
            )
        )
        preflight = adapter.preflight(
            CellContext(experiment_id=plan.experiment_id, cell_id=cell.cell_id)
        )
        if not preflight.ok:
            raise R4ControllerError(f"R6 B0 preflight failed: {preflight.detail}")

    def _sidecar_config(
        self,
        plan: ExecutionPlan,
        cell: PlannedCell,
        cell_dir: Path,
    ) -> R6SidecarConfig:
        return R6SidecarConfig(
            variant_id="b0",
            experiment_id=plan.experiment_id,
            cell_id=cell.cell_id,
            workspace=str((cell_dir / "workspace").resolve()),
            prompt_path=str((cell_dir / "raw" / "b0-fixed-prompt.md").resolve()),
            events_path=str(
                (cell_dir / "events" / "interventions.jsonl").resolve()
            ),
            model=self.model,
            reasoning_effort=self.reasoning_effort,
            surface_kind=self.surface_kind,
            b0_scripted=self.scripted_by_fixture.get(cell.fixture_id),
        )


class R6B1SequentialDriver(_R6CellDriverBase):
    variant_id: Literal["b1"] = "b1"

    def __init__(
        self,
        *,
        command_prefix: tuple[str, ...],
        schema_root: Path,
        runtime: Literal["fake", "codex"] = "codex",
        fake_fixture_by_fixture: dict[str, Path] | None = None,
        b1_pythonpath: Path | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)  # type: ignore[arg-type]
        if not command_prefix:
            raise ValueError("R6 B1 command prefix cannot be empty")
        self.command_prefix = tuple(command_prefix)
        self.schema_root = schema_root.resolve()
        self.runtime = runtime
        self.fake_fixture_by_fixture = {
            key: value.resolve() for key, value in (fake_fixture_by_fixture or {}).items()
        }
        self.b1_pythonpath = b1_pythonpath.resolve() if b1_pythonpath else None

    def capabilities(self) -> VariantCapabilities:
        return VariantCapabilities(
            automated_launch=True,
            supports_usage=True,
            supports_attempt_count=True,
        )

    def _adapter(self, cell: PlannedCell, prepared: PreparedFixture) -> B1SequentialAdapter:
        fixture = self.fake_fixture_by_fixture.get(cell.fixture_id)
        if self.runtime == "fake" and fixture is None:
            raise R4ControllerError("R6 B1 FakeRuntime fixture is missing")
        return B1SequentialAdapter(
            B1AdapterConfig(
                command_prefix=self.command_prefix,
                project=prepared.workspace,
                run_spec=prepared.workspace / "benchmark-run.yaml",
                state_root=(prepared.workspace.parent / "variant-state" / "b1-state"),
                schema_root=self.schema_root,
                runtime=self.runtime,
                fake_fixture=fixture,
                timeout_seconds=60,
            )
        )

    def _prepare_variant(
        self,
        plan: ExecutionPlan,
        cell: PlannedCell,
        cell_dir: Path,
        prepared: PreparedFixture,
    ) -> None:
        previous_pythonpath = os.environ.get("PYTHONPATH")
        try:
            if self.b1_pythonpath:
                os.environ["PYTHONPATH"] = os.pathsep.join(
                    value
                    for value in (str(self.b1_pythonpath), previous_pythonpath)
                    if value
                )
            preflight = self._adapter(cell, prepared).preflight(
                CellContext(experiment_id=plan.experiment_id, cell_id=cell.cell_id)
            )
        finally:
            if previous_pythonpath is None:
                os.environ.pop("PYTHONPATH", None)
            else:
                os.environ["PYTHONPATH"] = previous_pythonpath
        if not preflight.ok:
            raise R4ControllerError(f"R6 B1 preflight failed: {preflight.detail}")

    def _sidecar_config(
        self,
        plan: ExecutionPlan,
        cell: PlannedCell,
        cell_dir: Path,
    ) -> R6SidecarConfig:
        fixture = self.fake_fixture_by_fixture.get(cell.fixture_id)
        return R6SidecarConfig(
            variant_id="b1",
            experiment_id=plan.experiment_id,
            cell_id=cell.cell_id,
            workspace=str((cell_dir / "workspace").resolve()),
            events_path=str(
                (cell_dir / "events" / "interventions.jsonl").resolve()
            ),
            model=self.model,
            reasoning_effort=self.reasoning_effort,
            surface_kind=self.surface_kind,
            b1_command_prefix=self.command_prefix,
            b1_state_root=str((cell_dir / "variant-state" / "b1-state").resolve()),
            b1_schema_root=str(self.schema_root),
            b1_runtime=self.runtime,
            b1_fake_fixture=str(fixture) if fixture else None,
            b1_pythonpath=str(self.b1_pythonpath) if self.b1_pythonpath else None,
        )
