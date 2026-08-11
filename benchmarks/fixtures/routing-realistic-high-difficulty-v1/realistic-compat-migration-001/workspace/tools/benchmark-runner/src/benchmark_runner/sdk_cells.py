"""Runner-owned Measurement and sealing path for non-live SDK comparison Cells."""

from __future__ import annotations

import hashlib
import platform
import time
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue

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
    _r6_redact_bytes,
    _r6_redact_object,
    _source_tree_sha256,
    _transition,
    _write_model,
    atomic_write,
    canonical_json_bytes,
    sha256_bytes,
    verify_sealed_cell,
)
from benchmark_runner.workspace import PreparedFixture


RUNNER_FINGERPRINT_INPUTS = (
    "pyproject.toml",
    "src/benchmark_runner",
    "schemas",
)


def runner_source_sha256() -> str:
    """Fingerprint the exact Benchmark Runner sources that execute SDK Cells."""

    runner_root = Path(__file__).resolve().parents[2]
    return _source_tree_sha256(runner_root, RUNNER_FINGERPRINT_INPUTS)


class SdkSealedCellResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    experiment_id: str
    cell_id: str
    variant_id: str
    cell_state: Literal["SEALED"]
    outcome_state: str
    check_success: bool
    actual_model_turns: int = Field(ge=0)
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
    runner_sha256 = runner_source_sha256()
    if plan.runner.sha256 != runner_sha256:
        raise ValueError("Execution Plan Runner hash does not match the executing source tree")
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


def _assert_next_planned_cell(
    experiment_dir: Path,
    plan: ExecutionPlan,
    planned_cell: PlannedCell,
) -> None:
    """Require the immutable ordinal order and re-verify every predecessor seal."""

    for cell in sorted(plan.cells, key=lambda item: item.execution_ordinal):
        state_path = experiment_dir / "cells" / cell.cell_id / "cell-state.json"
        if not state_path.is_file():
            if cell.cell_id != planned_cell.cell_id:
                raise RuntimeError(
                    f"Cell {planned_cell.cell_id} is out of order; next Cell is {cell.cell_id}"
                )
            return
        state = CellStateRecord.model_validate_json(state_path.read_bytes())
        if state.state is not CellLifecycleState.SEALED:
            raise RuntimeError(f"Earlier Cell {cell.cell_id} is not SEALED")
        verify_sealed_cell(state_path.parent)
        if cell.cell_id == planned_cell.cell_id:
            raise RuntimeError(f"Cell {planned_cell.cell_id} is already SEALED")
    raise RuntimeError("Execution Plan has no remaining Cell")


def _assert_fake_runtime_boundary(adapter: VariantAdapter) -> None:
    """Prove the no-model boundary from concrete runtime configuration, not Evidence."""

    from benchmark_runner.adapter import B1SequentialAdapter
    from benchmark_runner.sdk_baselines import SdkBaselineAdapter
    from benchmark_runner.sdk_common import FakeSdkRuntime

    if type(adapter) is SdkBaselineAdapter:
        if type(adapter.config.runtime) is not FakeSdkRuntime:
            raise RuntimeError("non-live SDK baseline requires the exact FakeSdkRuntime")
        return
    if type(adapter) is B1SequentialAdapter:
        if adapter.config.runtime != "fake":
            raise RuntimeError("non-live B1 Cell requires runtime=fake")
        return
    raise RuntimeError("non-live Cell rejects unverified Adapter implementations")


def _assert_live_runtime_boundary(adapter: VariantAdapter) -> None:
    """Allow only the two reviewed ChatGPT-auth live runtime paths."""

    from benchmark_runner.adapter import B1SequentialAdapter
    from benchmark_runner.sdk_baselines import SdkBaselineAdapter
    from benchmark_runner.sdk_common import CodexSdkRuntime

    if type(adapter) is SdkBaselineAdapter:
        if type(adapter.config.runtime) is not CodexSdkRuntime:
            raise RuntimeError("live SDK baseline requires the exact CodexSdkRuntime")
        return
    if type(adapter) is B1SequentialAdapter:
        if adapter.config.runtime != "codex":
            raise RuntimeError("live B1 Cell requires runtime=codex")
        return
    raise RuntimeError("live Cell rejects unverified Adapter implementations")


_LOCAL_RUNTIME_IDENTIFIER_KEYS = {
    "run_id",
    "runtime_session_id",
    "runtime_turn_id",
    "session_id",
    "thread_id",
}


def _hashed_identifier(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _redact_local_runtime_identifiers(value: object) -> object:
    """Hash local SDK/B1 identifiers before Evidence can be exported to Git."""

    if isinstance(value, dict):
        output: dict[str, object] = {}
        for key, item in value.items():
            key_text = str(key)
            if key_text in _LOCAL_RUNTIME_IDENTIFIER_KEYS and isinstance(item, str):
                output[key_text] = _hashed_identifier(item)
            elif key_text == "thread_ids" and isinstance(item, list):
                output[key_text] = [
                    _hashed_identifier(entry) if isinstance(entry, str) else entry
                    for entry in item
                ]
            else:
                output[key_text] = _redact_local_runtime_identifiers(item)
        return output
    if isinstance(value, list):
        return [_redact_local_runtime_identifiers(item) for item in value]
    return value


def _public_variant_evidence(evidence: VariantEvidence) -> VariantEvidence:
    raw_payload = _redact_local_runtime_identifiers(evidence.raw_payload)
    normalized_metrics = _redact_local_runtime_identifiers(
        evidence.normalized_metrics
    )
    assert isinstance(raw_payload, dict)
    assert isinstance(normalized_metrics, dict)
    return VariantEvidence(
        outcome_state=evidence.outcome_state,
        failure_kind=evidence.failure_kind,
        attempt_count=evidence.attempt_count,
        raw_payload=raw_payload,  # type: ignore[arg-type]
        normalized_metrics=normalized_metrics,  # type: ignore[arg-type]
    )


def _actual_model_turns(adapter: VariantAdapter, evidence: VariantEvidence) -> int:
    from benchmark_runner.adapter import B1SequentialAdapter
    from benchmark_runner.sdk_baselines import SdkBaselineAdapter

    if type(adapter) is SdkBaselineAdapter:
        return int(getattr(adapter.config.runtime, "actual_model_turns", 0))
    if type(adapter) is B1SequentialAdapter and adapter.config.runtime == "codex":
        return int(evidence.normalized_metrics.get("turn_count", 0))
    return 0


def _adapter_preflight_evidence(adapter: VariantAdapter) -> dict[str, JsonValue]:
    if hasattr(adapter, "config") and hasattr(adapter.config, "runtime"):
        runtime_evidence = getattr(adapter.config.runtime, "preflight_evidence", None)
        if runtime_evidence:
            return dict(runtime_evidence)
    adapter_evidence = getattr(adapter, "preflight_evidence", None)
    if adapter_evidence:
        return dict(adapter_evidence)
    return {}


def _write_redacted_capture(
    *,
    cell_dir: Path,
    prepared: PreparedFixture,
    payload: dict[str, object],
    findings: set[str],
) -> bool:
    replacements = {
        str(prepared.workspace.resolve()): "<WORKSPACE>",
        str(cell_dir.resolve()): "<CELL_DIR>",
        str(Path.home().resolve()): "<HOME>",
    }
    redacted = _r6_redact_object(payload, replacements, findings)
    atomic_write(cell_dir / "raw" / "adapter-result.json", canonical_json_bytes(redacted))
    atomic_write(
        cell_dir / "raw" / "redaction-report.json",
        canonical_json_bytes(
            {
                "schema_version": 1,
                "secret_categories": sorted(findings),
                "source_bytes_changed": redacted != payload,
            }
        ),
    )
    return redacted != payload


def _redact_judge_evidence(
    *,
    cell_dir: Path,
    prepared: PreparedFixture,
    findings: set[str],
    source_bytes_changed: bool,
) -> None:
    replacements = {
        str(prepared.workspace.resolve()): "<WORKSPACE>",
        str(cell_dir.resolve()): "<CELL_DIR>",
        str(Path.home().resolve()): "<HOME>",
    }
    judge_dir = cell_dir / "judge"
    judge_bytes_changed = False
    for path in sorted(item for item in judge_dir.rglob("*") if item.is_file()):
        data = path.read_bytes()
        redacted = _r6_redact_bytes(data, replacements, findings)
        if redacted != data:
            atomic_write(path, redacted)
            judge_bytes_changed = True
    report_path = cell_dir / "raw" / "redaction-report.json"
    report = {
        "schema_version": 1,
        "secret_categories": sorted(findings),
        "source_bytes_changed": source_bytes_changed or judge_bytes_changed,
    }
    atomic_write(report_path, canonical_json_bytes(report))


def _assert_nonlive_evidence(evidence: VariantEvidence) -> None:
    turn_fields = [
        evidence.raw_payload[key]
        for key in ("model_turns", "actual_model_turns")
        if key in evidence.raw_payload
    ]
    if any(value != 0 for value in turn_fields):
        raise RuntimeError("non-live Evidence contradicts the verified fake-runtime boundary")


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
    runner_version: str,
    variant_version: str,
    variant_sha256: str,
    scenario_id: str | None,
    live: bool,
    actual_model_turns: int,
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
        "actual_model_turns": actual_model_turns,
        "terminal_claim_outcome": evidence.outcome_state,
        "downstream_turn_count": int(metrics.get("turn_count", 0)),
        "model_active_seconds": metrics.get("model_active_seconds"),
        "protected_files_ok": "runner_judge:check_integrity"
        not in judge.failed_check_ids,
    }
    for name in (
        "b1_retry_count",
        "b1_resume_count",
        "b1_intermediate_check_changed_result",
        "b1_intermediate_check_changed_dispatch",
        "b1_repeatable_quality_regression",
    ):
        if name in metrics:
            values[name] = metrics[name]
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
            runner_commit=runner_version,
            variant_version=variant_version,
            variant_artifact_sha256=variant_sha256,
        ),
        environment=MeasurementEnvironment(
            os=platform.system().lower(),
            python_version=platform.python_version(),
            model="gpt-5.6-terra" if live else "fake",
            auth_method="chatgpt" if live else "not_applicable_nonlive",
            reasoning_effort="low" if live else "not_applicable_nonlive",
            surface_kind=(
                "b1_cli_codex_runtime"
                if live and planned_cell.variant_id == "b1"
                else "sdk_controlled_codex_runtime"
                if live
                else "b1_cli_fake_runtime"
                if planned_cell.variant_id == "b1"
                else "sdk_controlled_fake_runtime"
            ),
            approval_mode="deny_all" if live else "not_applicable_nonlive",
            model_control="explicit_thread_and_turn" if live else "not_applicable_nonlive",
            reasoning_control="explicit_each_turn" if live else "not_applicable_nonlive",
            treatment_control="full" if live else "not_applicable",
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
            schema_id=(
                "sdk-controlled-live-pilot/v1"
                if live
                else "sdk-controlled-nonlive/v1"
            ),
            values=values,
        ),
    )


def _run_sdk_cell(
    *,
    experiment_dir: Path,
    plan: ExecutionPlan,
    planned_cell: PlannedCell,
    prepared: PreparedFixture,
    adapter: VariantAdapter,
    benchmark_python: Path,
    git_executable: Path,
    scenario_id: str | None = None,
    live: bool,
) -> SdkSealedCellResult:
    """Run one reviewed SDK Cell through the real Judge, Measurement, and seal."""

    experiment_dir = experiment_dir.resolve()
    if live:
        _assert_live_runtime_boundary(adapter)
    else:
        _assert_fake_runtime_boundary(adapter)
    variant_version, variant_sha256 = _assert_plan_and_fixture(
        experiment_dir,
        plan,
        planned_cell,
        prepared,
        adapter,
    )
    _assert_next_planned_cell(experiment_dir, plan, planned_cell)
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
    preflight_evidence = _adapter_preflight_evidence(adapter)
    if live and not preflight_evidence:
        runtime = getattr(getattr(adapter, "config", None), "runtime", None)
        close = getattr(runtime, "close", None)
        if callable(close):
            close()
        raise RuntimeError("live Adapter omitted model-free preflight Evidence")
    if live:
        preflight_findings: set[str] = set()
        replacements = {
            str(prepared.workspace.resolve()): "<WORKSPACE>",
            str(cell_dir.resolve()): "<CELL_DIR>",
            str(Path.home().resolve()): "<HOME>",
        }
        public_preflight = _r6_redact_object(
            preflight_evidence,
            replacements,
            preflight_findings,
        )
        if preflight_findings:
            raise RuntimeError("secret-like material found in live preflight Evidence")
        atomic_write(
            raw_dir / "preflight.json",
            canonical_json_bytes(public_preflight),
        )
    record = _transition(record, CellLifecycleState.PREPARED)
    _write_model(state_path, record)
    record = _transition(record, CellLifecycleState.ACTIVE)
    _write_model(state_path, record)

    total_started = time.monotonic()
    variant_started = time.monotonic()
    evidence = adapter.run(context)
    variant_seconds = time.monotonic() - variant_started
    actual_model_turns = _actual_model_turns(adapter, evidence)
    if live:
        if actual_model_turns < 1:
            raise RuntimeError("live Adapter returned no proven model turn")
        evidence = _public_variant_evidence(evidence)
    else:
        _assert_nonlive_evidence(evidence)
    findings: set[str] = set()
    source_bytes_changed = _write_redacted_capture(
        cell_dir=cell_dir,
        prepared=prepared,
        payload={
            "outcome_state": evidence.outcome_state,
            "failure_kind": evidence.failure_kind,
            "attempt_count": evidence.attempt_count,
            "raw_payload": evidence.raw_payload,
            "normalized_metrics": evidence.normalized_metrics,
        },
        findings=findings,
    )
    if findings:
        record = _transition(
            record,
            CellLifecycleState.STOPPED,
            outcome_state="infrastructure_error",
            stop_reason="secret_evidence_detected",
        )
        _write_model(state_path, record)
        raise RuntimeError("secret-like material found in Adapter Evidence; Cell not sealed")
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
    _redact_judge_evidence(
        cell_dir=cell_dir,
        prepared=prepared,
        findings=findings,
        source_bytes_changed=source_bytes_changed,
    )
    if findings:
        record = _transition(
            record,
            CellLifecycleState.STOPPED,
            outcome_state="infrastructure_error",
            stop_reason="secret_evidence_detected",
        )
        _write_model(state_path, record)
        raise RuntimeError("secret-like material found in Judge Evidence; Cell not sealed")
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
        runner_version=plan.runner.version,
        variant_version=variant_version,
        variant_sha256=variant_sha256,
        scenario_id=scenario_id,
        live=live,
        actual_model_turns=actual_model_turns,
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
        actual_model_turns=actual_model_turns,
        measurement_path=str(measurement_path),
        sealed_measurement_sha256=sealed_hash,
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
    scenario_id: str | None = None,
) -> SdkSealedCellResult:
    """Run one fake-runtime Cell through the real Judge, Measurement, and seal."""

    return _run_sdk_cell(
        experiment_dir=experiment_dir,
        plan=plan,
        planned_cell=planned_cell,
        prepared=prepared,
        adapter=adapter,
        benchmark_python=benchmark_python,
        git_executable=git_executable,
        scenario_id=scenario_id,
        live=False,
    )


def run_sdk_live_cell(
    *,
    experiment_dir: Path,
    plan: ExecutionPlan,
    planned_cell: PlannedCell,
    prepared: PreparedFixture,
    adapter: VariantAdapter,
    benchmark_python: Path,
    git_executable: Path,
) -> SdkSealedCellResult:
    """Run one ChatGPT-auth pilot Cell and preserve export-safe sealed Evidence."""

    return _run_sdk_cell(
        experiment_dir=experiment_dir,
        plan=plan,
        planned_cell=planned_cell,
        prepared=prepared,
        adapter=adapter,
        benchmark_python=benchmark_python,
        git_executable=git_executable,
        live=True,
    )
