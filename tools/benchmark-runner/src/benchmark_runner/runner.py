from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Literal

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
)
from benchmark_runner.contract import (
    CellLifecycleState,
    CellStateRecord,
    EvidenceRef,
    ExecutionPlan,
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
