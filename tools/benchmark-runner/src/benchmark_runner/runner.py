from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
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
    B1AdapterConfig,
    B1SequentialAdapter,
    CellContext,
    FakeAdapter,
    VariantAdapter,
    VariantCapabilities,
)
from benchmark_runner.contract import (
    ArtifactIdentity,
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
    StopHistoryEntry,
    VariantMetrics,
    utc_now,
)
from benchmark_runner.judge import FixtureJudge, StubJudge
from benchmark_runner.plan import (
    ZERO_GIT_ID,
    ZERO_SHA256,
    assert_plan_integrity,
    build_r0_plan,
    build_r2_plan,
    build_r3_plan,
    build_r4_plan,
)
from benchmark_runner.workspace import FixtureRestorer, load_frozen_manifest


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
