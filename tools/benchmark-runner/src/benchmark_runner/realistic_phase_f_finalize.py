"""Model-free Phase F tail: Judge observation, Measurement, and Cell seal.

The finalizer wraps the already assembled Profile R SS1 backend.  A Judge port
is injected; tests use :class:`FakePhaseFJudgePort`, so this module neither
starts Docker nor opens Codex.  The public Measurement models are reused while
the realistic property Judge remains a separate, typed boundary.
"""

from __future__ import annotations

import json
import platform
import time
from pathlib import Path
from typing import Literal, Mapping, Protocol

from pydantic import Field, JsonValue, model_validator

from benchmark_runner.contract import (
    EvidenceRef,
    ExecutionPlan,
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
    Sha256,
    StrictModel,
    VariantMetrics,
    utc_now,
)
from benchmark_runner.realistic_phase_f import (
    PhaseFBackendResult,
    PhaseFDispatchRequest,
    PhaseFModelTurnAccounting,
    PhaseFRuntimeMode,
    load_verified_phase_f_candidate,
    phase_f_backend_result_matches_request,
    phase_f_cell_completion_deadline_seconds,
    phase_f_cell_model_turn_ceiling,
)
from benchmark_runner.realistic_routing import canonical_json_bytes, canonical_sha256
from benchmark_runner.runner import sha256_bytes, sha256_file


PHASE_F_FINAL_DIRECTORY = "final"
PHASE_F_JUDGE_DIRECTORY = "judge"
PHASE_F_SEALED_DIRECTORY = "sealed"
PHASE_F_MEASUREMENT_FILENAME = "measurement.json"
PHASE_F_CELL_SEAL_FILENAME = "cell-seal.json"


class PhaseFFinalizationError(RuntimeError):
    """Raised when Judge/Measurement/seal evidence cannot be reproduced."""


class PhaseFJudgeFile(StrictModel):
    path: str = Field(min_length=1)
    size: int = Field(ge=0)
    sha256: Sha256


class PhaseFJudgeObservation(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["phase_f_realistic_judge_observation"] = (
        "phase_f_realistic_judge_observation"
    )
    status: Literal[
        "CHECKS_PASSED",
        "CHECKS_FAILED",
        "JUDGE_RUNTIME_ERROR",
        "CHALLENGE_INVALID",
    ]
    judge_kind: Literal["model_free_fake", "docker_property"]
    docker_executed: bool
    actual_model_turns: Literal[0] = 0
    check_success: bool
    failed_property_ids: list[str]
    duration_seconds: float = Field(ge=0)
    raw_manifest_sha256: Sha256 | None = None
    raw_result_sha256: Sha256 | None = None
    files: list[PhaseFJudgeFile] = Field(min_length=1)
    observation_sha256: Sha256

    @model_validator(mode="after")
    def observation_is_canonical(self) -> "PhaseFJudgeObservation":
        paths = [item.path for item in self.files]
        if paths != sorted(set(paths)):
            raise ValueError("Phase F Judge files must be sorted and unique")
        if self.failed_property_ids != sorted(set(self.failed_property_ids)):
            raise ValueError("Phase F failed property IDs must be sorted and unique")
        if self.check_success != (self.status == "CHECKS_PASSED"):
            raise ValueError("Phase F Judge success flag differs from status")
        if self.status == "CHECKS_FAILED" and not self.failed_property_ids:
            raise ValueError("failed Judge result must name a failed property")
        if self.status != "CHECKS_FAILED" and self.failed_property_ids:
            raise ValueError("non-check failure cannot claim failed properties")
        if self.judge_kind == "model_free_fake":
            if self.docker_executed or any(
                value is not None
                for value in (self.raw_manifest_sha256, self.raw_result_sha256)
            ):
                raise ValueError("fake Judge cannot claim Docker raw Evidence")
        elif (
            not self.docker_executed
            or self.raw_manifest_sha256 is None
            or self.raw_result_sha256 is None
        ):
            raise ValueError("Docker Judge must bind its raw manifest and result")
        payload = self.model_dump(mode="json", exclude={"observation_sha256"})
        if self.observation_sha256 != canonical_sha256(payload):
            raise ValueError("Phase F Judge observation hash differs")
        return self


class PhaseFJudgePort(Protocol):
    def run(
        self,
        *,
        workspace: Path,
        output_root: Path,
        request: PhaseFDispatchRequest,
    ) -> PhaseFJudgeObservation: ...


class PhaseFWorkerBackend(Protocol):
    artifact_root: Path
    runtime_mode: PhaseFRuntimeMode
    evidence_filename: str

    def run_one_cell(self, request: PhaseFDispatchRequest) -> PhaseFBackendResult: ...


class FakePhaseFJudgePort:
    """Deterministic model-free Judge port for finalizer contract tests."""

    def __init__(self, *, check_success: bool = True) -> None:
        self.check_success = check_success
        self.calls: list[str] = []

    def run(
        self,
        *,
        workspace: Path,
        output_root: Path,
        request: PhaseFDispatchRequest,
    ) -> PhaseFJudgeObservation:
        if not workspace.is_dir() or output_root.exists():
            raise PhaseFFinalizationError("Fake Judge roots are invalid")
        output_root.mkdir(parents=True, exist_ok=False)
        self.calls.append(request.cell_id)
        manifest = {
            "schema_version": 1,
            "kind": "fake_phase_f_judge_manifest",
            "cell_id": request.cell_id,
            "workspace_tree_observed": True,
            "docker_executed": False,
            "model_turns": 0,
        }
        status = "CHECKS_PASSED" if self.check_success else "CHECKS_FAILED"
        result = {
            "schema_version": 1,
            "kind": "fake_phase_f_judge_result",
            "cell_id": request.cell_id,
            "status": status,
            "failed_property_ids": [] if self.check_success else ["R-P02-FAKE"],
            "docker_executed": False,
            "model_turns": 0,
        }
        _write_new(output_root / "manifest.json", canonical_json_bytes(manifest))
        _write_new(output_root / "result.json", canonical_json_bytes(result))
        files = _judge_files(output_root)
        values = {
            "schema_version": 1,
            "kind": "phase_f_realistic_judge_observation",
            "status": status,
            "judge_kind": "model_free_fake",
            "docker_executed": False,
            "actual_model_turns": 0,
            "check_success": self.check_success,
            "failed_property_ids": result["failed_property_ids"],
            "duration_seconds": 0.001,
            "raw_manifest_sha256": None,
            "raw_result_sha256": None,
            "files": [item.model_dump(mode="json") for item in files],
        }
        return PhaseFJudgeObservation(
            **values,
            observation_sha256=canonical_sha256(values),
        )


class PhaseFCellSeal(StrictModel):
    schema_version: Literal[1, 2] = 1
    kind: Literal["phase_f_realistic_cell_seal"] = "phase_f_realistic_cell_seal"
    experiment_id: str
    plan_fingerprint: Sha256
    candidate_seal_sha256: Sha256
    candidate_snapshot_sha256: Sha256
    execution_ordinal: int = Field(ge=1, le=4)
    cell_id: str
    fixture_id: str
    variant_id: Literal["ss1", "b1"]
    request_sha256: Sha256
    runtime_mode: PhaseFRuntimeMode
    model_turn_ceiling: int | None = Field(default=None, ge=1)
    budget_mode: Literal["cell_completion_deadline"] | None = None
    cell_completion_deadline_seconds: int | None = Field(default=None, gt=0)
    actual_model_turns: int = Field(ge=0)
    adapter_evidence_path: str = Field(min_length=1)
    worker_artifact_sha256: Sha256
    judge_observation_sha256: Sha256
    measurement_sha256: Sha256
    files: list[EvidenceRef]
    seal_sha256: Sha256

    @model_validator(mode="after")
    def seal_is_canonical(self) -> "PhaseFCellSeal":
        paths = [item.path for item in self.files]
        if paths != sorted(set(paths)):
            raise ValueError("Phase F Cell seal files must be sorted and unique")
        if self.schema_version == 1 and self.model_turn_ceiling is None:
            raise ValueError("legacy Phase F Cell seal requires a turn ceiling")
        if self.schema_version == 2 and (
            self.model_turn_ceiling is not None
            or self.budget_mode != "cell_completion_deadline"
            or self.cell_completion_deadline_seconds != 9000
        ):
            raise ValueError("Phase F Cell seal deadline differs")
        payload = self.model_dump(
            mode="json", exclude={"seal_sha256"}, exclude_none=True
        )
        if self.seal_sha256 != canonical_sha256(payload):
            raise ValueError("Phase F Cell seal self-hash differs")
        return self


def _write_new(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(payload)
        handle.flush()


def _judge_files(root: Path) -> list[PhaseFJudgeFile]:
    return [
        PhaseFJudgeFile(
            path=path.relative_to(root).as_posix(),
            size=path.stat().st_size,
            sha256=sha256_file(path),
        )
        for path in sorted(
            (item for item in root.rglob("*") if item.is_file()),
            key=lambda item: item.relative_to(root).as_posix(),
        )
    ]


def _verify_judge_observation(
    root: Path,
    observation: PhaseFJudgeObservation,
) -> None:
    actual = _judge_files(root)
    if actual != observation.files:
        raise PhaseFFinalizationError("Phase F Judge file evidence differs")
    payload = observation.model_dump(mode="json", exclude={"observation_sha256"})
    if canonical_sha256(payload) != observation.observation_sha256:
        raise PhaseFFinalizationError("Phase F Judge observation hash differs")


def _metric(
    status: MetricStatus,
    unit: str,
    *,
    value: JsonValue | None = None,
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


def _evidence_ref(cell_root: Path, path: Path) -> EvidenceRef:
    return EvidenceRef(
        path=path.relative_to(cell_root).as_posix(),
        size=path.stat().st_size,
        sha256=sha256_file(path),
    )


def _strict_nonnegative_int(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise PhaseFFinalizationError(f"Phase F {label} is invalid")
    return value


def _verify_adapter_turn_evidence(
    *,
    request: PhaseFDispatchRequest,
    expected_actual_model_turns: int,
    adapter_payload: Mapping[str, object],
) -> tuple[PhaseFModelTurnAccounting, int]:
    """Cross-check every turn count and receipt before Judge execution."""

    expected_identity = (
        request.experiment_id,
        request.cell_id,
        request.request_sha256,
        request.fixture_id,
        request.variant_id,
        request.runtime_mode.value,
    )
    actual_identity = (
        adapter_payload.get("experiment_id"),
        adapter_payload.get("cell_id"),
        adapter_payload.get("request_sha256"),
        adapter_payload.get("fixture_id"),
        adapter_payload.get("variant_id"),
        adapter_payload.get("runtime_mode"),
    )
    if actual_identity != expected_identity:
        raise PhaseFFinalizationError("Phase F adapter Evidence identity differs")

    try:
        accounting = PhaseFModelTurnAccounting.model_validate(
            adapter_payload.get("model_turn_accounting")
        )
    except Exception as exc:
        raise PhaseFFinalizationError(
            "Phase F model turn accounting is invalid"
        ) from exc
    top_level_actual = _strict_nonnegative_int(
        adapter_payload.get("actual_model_turns"),
        "adapter actual model turn count",
    )
    raw = adapter_payload.get("adapter_raw_payload")
    metrics = adapter_payload.get("adapter_normalized_metrics")
    if not isinstance(raw, dict) or not isinstance(metrics, dict):
        raise PhaseFFinalizationError("Phase F adapter Evidence shape differs")
    normalized_turns = _strict_nonnegative_int(
        metrics.get("turn_count"),
        "normalized turn count",
    )
    boundary_records = raw.get("boundary_records")
    if not isinstance(boundary_records, list):
        raise PhaseFFinalizationError("Phase F boundary records are unavailable")

    logical_counts = [
        normalized_turns,
        len(boundary_records),
        accounting.turn_start_attempts,
    ]
    raw_actual_model_turns: int | None = None
    if request.variant_id == "ss1":
        turns = raw.get("turns")
        if not isinstance(turns, list):
            raise PhaseFFinalizationError("Phase F SS1 turn records are unavailable")
        logical_counts.append(len(turns))
        raw_actual_model_turns = _strict_nonnegative_int(
            raw.get("actual_model_turns"),
            "SS1 raw actual model turn count",
        )
    else:
        report = raw.get("report")
        if not isinstance(report, dict) or not isinstance(report.get("metrics"), dict):
            raise PhaseFFinalizationError("Phase F B1 ledger report is unavailable")
        logical_counts.append(
            _strict_nonnegative_int(
                report["metrics"].get("turns"),
                "B1 ledger turn count",
            )
        )

    if len(set(logical_counts)) != 1:
        raise PhaseFFinalizationError("Phase F adapter turn counts differ before Judge")
    logical_turn_count = logical_counts[0]
    if (
        accounting.runtime_mode is not request.runtime_mode
        or accounting.model_turn_ceiling != request.model_turn_ceiling
        or accounting.budget_mode != request.budget_mode
        or accounting.actual_model_turns != expected_actual_model_turns
        or accounting.runtime_reported_model_turns != expected_actual_model_turns
        or top_level_actual != expected_actual_model_turns
        or (
            raw_actual_model_turns is not None
            and raw_actual_model_turns != expected_actual_model_turns
        )
    ):
        raise PhaseFFinalizationError("Phase F authoritative turn counts differ before Judge")
    expected_receipt_status = (
        "simulated"
        if request.runtime_mode is PhaseFRuntimeMode.MODEL_FREE_FAKE
        else "accepted"
    )
    if any(item.status != expected_receipt_status for item in accounting.receipts):
        raise PhaseFFinalizationError("Phase F turn acceptance is uncertain before Judge")
    if request.runtime_mode is PhaseFRuntimeMode.LIVE_CHATGPT:
        if logical_turn_count != expected_actual_model_turns:
            raise PhaseFFinalizationError(
                "Phase F live turn records differ from actual model turns"
            )
    elif expected_actual_model_turns != 0:
        raise PhaseFFinalizationError("Phase F model-free result consumed model turns")
    return accounting, logical_turn_count


def _measurement(
    *,
    plan: ExecutionPlan,
    request: PhaseFDispatchRequest,
    worker: PhaseFBackendResult,
    adapter_payload: Mapping[str, object],
    judge: PhaseFJudgeObservation,
    evidence: list[EvidenceRef],
    adapter_evidence_filename: str,
    worker_seconds: float,
    total_seconds: float,
) -> Measurement:
    planned = next(item for item in plan.cells if item.cell_id == request.cell_id)
    fixture = next(item for item in plan.fixtures if item.fixture_id == request.fixture_id)
    raw = adapter_payload.get("adapter_raw_payload")
    metrics = adapter_payload.get("adapter_normalized_metrics")
    if not isinstance(raw, dict) or not isinstance(metrics, dict):
        raise PhaseFFinalizationError("Phase F adapter Evidence shape differs")
    records = raw.get("boundary_records")
    if not isinstance(records, list):
        raise PhaseFFinalizationError("Phase F boundary records are unavailable")
    scope_ok = True
    secret_findings: list[str] = []
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("observation"), dict):
            raise PhaseFFinalizationError("Phase F boundary record is invalid")
        observation = record["observation"]
        if observation.get("outside_task_scope_paths") or observation.get(
            "outside_run_scope_paths"
        ):
            scope_ok = False
        protected = observation.get("protected_files")
        if not isinstance(protected, list):
            raise PhaseFFinalizationError("Phase F protected file Evidence is invalid")
        if any(isinstance(item, dict) and item.get("changed") is True for item in protected):
            scope_ok = False
        secret_scan = observation.get("secret_scan")
        if isinstance(secret_scan, dict) and isinstance(secret_scan.get("finding_ids"), list):
            secret_findings.extend(str(value) for value in secret_scan["finding_ids"])
    not_applicable_count = _metric(MetricStatus.NOT_APPLICABLE, "count")
    not_applicable_seconds = _metric(MetricStatus.NOT_APPLICABLE, "seconds")
    token_metric = _metric(MetricStatus.NOT_APPLICABLE, "tokens")
    adapter_source = f"{request.variant_id}_adapter"
    if request.runtime_mode is PhaseFRuntimeMode.LIVE_CHATGPT:
        usage = metrics.get("token_usage")
        token_metric = (
            _metric(
                MetricStatus.MEASURED,
                "tokens",
                value=usage,
                source=adapter_source,
                evidence_ref=adapter_evidence_filename,
            )
            if isinstance(usage, dict)
            else _metric(MetricStatus.UNKNOWN, "tokens")
        )
    final_tree = adapter_payload.get("worker_tree_final_sha256")
    if not isinstance(final_tree, str) or len(final_tree) != 64:
        raise PhaseFFinalizationError("Phase F final Worker tree hash is invalid")
    outcome_state = worker.outcome_state
    failure_kind = adapter_payload.get("adapter_failure_kind")
    if outcome_state == "completed" and not judge.check_success:
        outcome_state = "failed"
        failure_kind = "independent_judge_failed"
    elif outcome_state == "completed":
        failure_kind = None
    return Measurement(
        created_at=utc_now(),
        identity=MeasurementIdentity(
            experiment_id=plan.experiment_id,
            block_id=planned.block_id,
            cell_id=planned.cell_id,
            fixture_id=planned.fixture_id,
            repetition=planned.repetition,
            variant_id=planned.variant_id,
            execution_ordinal=planned.execution_ordinal,
        ),
        provenance=MeasurementProvenance(
            manifest_sha256=plan.source_manifest.sha256,
            fixture_source_commit=fixture.source_commit,
            fixture_tree_before=fixture.git_tree,
            fixture_tree_after=final_tree,
            runner_commit=plan.runner.version,
            variant_version=f"phase-f-profile-r-{request.variant_id}/v1",
            variant_artifact_sha256=worker.sealed_artifact_sha256,
        ),
        environment=MeasurementEnvironment(
            os=platform.system().lower(),
            python_version=platform.python_version(),
            model=(
                plan.environment_fingerprint["model"]
                if request.runtime_mode is PhaseFRuntimeMode.LIVE_CHATGPT
                else "fake"
            ),
            auth_method=(
                "chatgpt"
                if request.runtime_mode is PhaseFRuntimeMode.LIVE_CHATGPT
                else "not_applicable_nonlive"
            ),
            reasoning_effort=(
                plan.environment_fingerprint["reasoning_effort"]
                if request.runtime_mode is PhaseFRuntimeMode.LIVE_CHATGPT
                else "not_applicable_nonlive"
            ),
            surface_kind=f"phase_f_profile_r_{request.variant_id}",
            approval_mode=(
                "deny_all"
                if request.runtime_mode is PhaseFRuntimeMode.LIVE_CHATGPT
                else "not_applicable_nonlive"
            ),
            model_control="runtime_contract_v2",
            reasoning_control="explicit_each_turn",
            treatment_control=(
                "full"
                if request.runtime_mode is PhaseFRuntimeMode.LIVE_CHATGPT
                else "not_applicable"
            ),
        ),
        outcome=MeasurementOutcome(
            state=outcome_state,
            failure_kind=(None if failure_kind is None else str(failure_kind)),
            check_success=judge.check_success,
        ),
        effort=MeasurementEffort(
            variant_execution_seconds=_metric(
                MetricStatus.MEASURED,
                "seconds",
                value=worker_seconds,
                source="phase_f_monotonic_clock",
            ),
            judge_seconds=_metric(
                MetricStatus.MEASURED,
                "seconds",
                value=judge.duration_seconds,
                source="judge_observation",
            ),
            total_wall_clock_seconds=_metric(
                MetricStatus.MEASURED,
                "seconds",
                value=total_seconds,
                source="phase_f_monotonic_clock",
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
                source=adapter_source,
                evidence_ref=adapter_evidence_filename,
            ),
            turn_count=_metric(
                MetricStatus.MEASURED,
                "count",
                value=int(metrics.get("turn_count", 0)),
                source=adapter_source,
                evidence_ref=adapter_evidence_filename,
            ),
            attempt_count=_metric(
                MetricStatus.MEASURED,
                "count",
                value=int(adapter_payload.get("adapter_attempt_count", 1)),
                source=adapter_source,
                evidence_ref=adapter_evidence_filename,
            ),
            token_usage=token_metric,
        ),
        quality=MeasurementQuality(
            errors_found_by_automatic_checks=_metric(
                MetricStatus.DERIVED,
                "count",
                value=len(judge.failed_property_ids),
                source="realistic_property_judge",
                evidence_ref=f"{PHASE_F_FINAL_DIRECTORY}/{PHASE_F_JUDGE_DIRECTORY}/result.json",
            ),
            human_errors_after_pass=_metric(MetricStatus.NOT_APPLICABLE, "count"),
        ),
        integrity=MeasurementIntegrity(
            scope_ok=scope_ok,
            evidence_hashes_ok=True,
            secret_findings=sorted(set(secret_findings)),
        ),
        evidence=sorted(evidence, key=lambda item: item.path),
        variant_metrics=VariantMetrics(
            schema_id="phase-f-realistic-profile-r/v1",
            values={
                "actual_model_turns": worker.actual_model_turns,
                "judge_status": judge.status,
                "judge_kind": judge.judge_kind,
                "judge_docker_executed": judge.docker_executed,
                "judge_model_turns": judge.actual_model_turns,
                "judge_observation_sha256": judge.observation_sha256,
                "failed_property_ids": judge.failed_property_ids,
                "automatic_continuation": False,
            },
        ),
    )


class ProfileRPhaseFCellFinalizerBackend:
    """Wrap one Profile R variant with an injected Judge and final seal."""

    def __init__(
        self,
        *,
        repository: Path,
        candidate_root: Path,
        worker_backend: PhaseFWorkerBackend,
        judge: PhaseFJudgePort,
    ) -> None:
        self.repository = repository.resolve()
        self.candidate_root = candidate_root.resolve()
        self.worker_backend = worker_backend
        self.judge = judge
        self.runtime_mode = worker_backend.runtime_mode
        self._completion_deadline_monotonic: float | None = None

    def bind_completion_deadline_monotonic(self, deadline: float) -> None:
        if deadline <= time.monotonic():
            raise PhaseFFinalizationError("Cell completion deadline is not in the future")
        self._completion_deadline_monotonic = deadline
        bind_worker = getattr(
            self.worker_backend, "bind_completion_deadline_monotonic", None
        )
        if not callable(bind_worker):
            raise PhaseFFinalizationError(
                "completion-budget Worker cannot bind the Cell deadline"
            )
        bind_worker(deadline)
        bind_judge = getattr(self.judge, "bind_completion_deadline_monotonic", None)
        if callable(bind_judge):
            bind_judge(deadline)

    def _require_time_remaining(self) -> None:
        if (
            self._completion_deadline_monotonic is not None
            and time.monotonic() >= self._completion_deadline_monotonic
        ):
            raise PhaseFFinalizationError("Cell completion deadline exceeded")

    def _plan(
        self,
        request: PhaseFDispatchRequest,
    ):
        snapshot = load_verified_phase_f_candidate(
            self.repository,
            self.candidate_root,
        )
        plan = snapshot.plan
        stage = snapshot.stage
        planned = next((item for item in plan.cells if item.cell_id == request.cell_id), None)
        turn_ceiling = None
        completion_deadline = None
        if planned is not None:
            if request.budget_mode == "cell_completion_deadline":
                completion_deadline = phase_f_cell_completion_deadline_seconds(
                    stage=stage, cell=planned
                )
            else:
                turn_ceiling = phase_f_cell_model_turn_ceiling(
                    stage=stage, cell=planned
                )
        if (
            planned is None
            or plan.plan_fingerprint != request.plan_fingerprint
            or snapshot.seal.seal_sha256 != request.candidate_seal_sha256
            or snapshot.snapshot_sha256 != request.candidate_snapshot_sha256
            or turn_ceiling != request.model_turn_ceiling
            or completion_deadline != request.cell_completion_deadline_seconds
            or planned.execution_ordinal != request.execution_ordinal
            or planned.fixture_id != request.fixture_id
            or planned.variant_id != request.variant_id
        ):
            raise PhaseFFinalizationError("Phase F finalizer Plan identity differs")
        return snapshot

    def run_one_cell(self, request: PhaseFDispatchRequest) -> PhaseFBackendResult:
        snapshot = self._plan(request)
        if (
            request.budget_mode == "cell_completion_deadline"
            and self._completion_deadline_monotonic is None
        ):
            raise PhaseFFinalizationError("Cell completion deadline was not bound")
        self._require_time_remaining()
        plan = snapshot.plan
        stage = snapshot.stage
        total_started = time.monotonic()
        worker_started = time.monotonic()
        worker = self.worker_backend.run_one_cell(request)
        self._require_time_remaining()
        worker_seconds = time.monotonic() - worker_started
        if not phase_f_backend_result_matches_request(request, worker):
            raise PhaseFFinalizationError(
                "Phase F worker result identity differs before Judge"
            )
        planned_cell = next(item for item in plan.cells if item.cell_id == request.cell_id)
        turn_ceiling = request.model_turn_ceiling
        if (
            turn_ceiling is not None
            and worker.actual_model_turns > turn_ceiling
        ):
            raise PhaseFFinalizationError(
                "Phase F worker model turns "
                f"{worker.actual_model_turns} exceed candidate Cell ceiling "
                f"{turn_ceiling} before Judge"
            )
        cell_root = self.worker_backend.artifact_root / request.cell_id
        workspace = cell_root / "workspace"
        adapter_path = cell_root / self.worker_backend.evidence_filename
        if worker.sealed_artifact_sha256 != sha256_file(adapter_path):
            raise PhaseFFinalizationError("Phase F worker artifact hash differs")
        adapter_payload = json.loads(adapter_path.read_text(encoding="utf-8"))
        if not isinstance(adapter_payload, dict):
            raise PhaseFFinalizationError("Phase F adapter Evidence is invalid")
        _verify_adapter_turn_evidence(
            request=request,
            expected_actual_model_turns=worker.actual_model_turns,
            adapter_payload=adapter_payload,
        )
        final_root = cell_root / PHASE_F_FINAL_DIRECTORY
        judge_root = final_root / PHASE_F_JUDGE_DIRECTORY
        self._require_time_remaining()
        observation = self.judge.run(
            workspace=workspace,
            output_root=judge_root,
            request=request,
        )
        self._require_time_remaining()
        _verify_judge_observation(judge_root, observation)
        evidence = [_evidence_ref(cell_root, adapter_path)]
        evidence.extend(
            _evidence_ref(cell_root, judge_root / item.path)
            for item in observation.files
        )
        measurement = _measurement(
            plan=plan,
            request=request,
            worker=worker,
            adapter_payload=adapter_payload,
            judge=observation,
            evidence=evidence,
            adapter_evidence_filename=self.worker_backend.evidence_filename,
            worker_seconds=worker_seconds,
            total_seconds=time.monotonic() - total_started,
        )
        sealed_root = final_root / PHASE_F_SEALED_DIRECTORY
        measurement_path = sealed_root / PHASE_F_MEASUREMENT_FILENAME
        measurement_bytes = canonical_json_bytes(measurement)
        _write_new(measurement_path, measurement_bytes)
        seal_files = [*evidence, _evidence_ref(cell_root, measurement_path)]
        values = {
            "schema_version": request.schema_version,
            "kind": "phase_f_realistic_cell_seal",
            "experiment_id": request.experiment_id,
            "plan_fingerprint": request.plan_fingerprint,
            "candidate_seal_sha256": request.candidate_seal_sha256,
            "candidate_snapshot_sha256": request.candidate_snapshot_sha256,
            "execution_ordinal": request.execution_ordinal,
            "cell_id": request.cell_id,
            "fixture_id": request.fixture_id,
            "variant_id": request.variant_id,
            "request_sha256": request.request_sha256,
            "runtime_mode": request.runtime_mode.value,
            **(
                {
                    "budget_mode": "cell_completion_deadline",
                    "cell_completion_deadline_seconds": (
                        request.cell_completion_deadline_seconds
                    ),
                }
                if request.budget_mode == "cell_completion_deadline"
                else {"model_turn_ceiling": request.model_turn_ceiling}
            ),
            "actual_model_turns": worker.actual_model_turns,
            "adapter_evidence_path": self.worker_backend.evidence_filename,
            "worker_artifact_sha256": worker.sealed_artifact_sha256,
            "judge_observation_sha256": observation.observation_sha256,
            "measurement_sha256": sha256_bytes(measurement_bytes),
            "files": [
                item.model_dump(mode="json")
                for item in sorted(seal_files, key=lambda value: value.path)
            ],
        }
        seal = PhaseFCellSeal(**values, seal_sha256=canonical_sha256(values))
        seal_bytes = canonical_json_bytes(seal)
        _write_new(sealed_root / PHASE_F_CELL_SEAL_FILENAME, seal_bytes)
        verify_phase_f_cell_finalization(
            cell_root,
            expected_seal_file_sha256=sha256_bytes(seal_bytes),
        )
        return worker.model_copy(
            update={
                "outcome_state": measurement.outcome.state,
                "sealed_artifact_sha256": sha256_bytes(seal_bytes),
                "public_summary": {
                    **worker.public_summary,
                    "judge_status": observation.status,
                    "judge_check_success": observation.check_success,
                    "measurement_sha256": sha256_bytes(measurement_bytes),
                    "final_cell_sealed": True,
                    "finalization_cell_root": str(cell_root.resolve()),
                    "automatic_continuation": False,
                },
            }
        )


def verify_phase_f_cell_finalization(
    cell_root: Path,
    *,
    expected_seal_file_sha256: str,
) -> Measurement:
    """Recompute every final seal file reference without trusting stored status."""

    cell_root = cell_root.resolve()
    sealed_root = cell_root / PHASE_F_FINAL_DIRECTORY / PHASE_F_SEALED_DIRECTORY
    seal_path = sealed_root / PHASE_F_CELL_SEAL_FILENAME
    if sha256_file(seal_path) != expected_seal_file_sha256:
        raise PhaseFFinalizationError("Phase F external Cell seal hash differs")
    seal = PhaseFCellSeal.model_validate_json(seal_path.read_bytes())
    for item in seal.files:
        path = (cell_root / item.path).resolve()
        if not path.is_relative_to(cell_root) or not path.is_file():
            raise PhaseFFinalizationError("Phase F sealed Evidence path is unavailable")
        if path.stat().st_size != item.size or sha256_file(path) != item.sha256:
            raise PhaseFFinalizationError("Phase F sealed Evidence bytes differ")
    measurement_path = sealed_root / PHASE_F_MEASUREMENT_FILENAME
    if sha256_file(measurement_path) != seal.measurement_sha256:
        raise PhaseFFinalizationError("Phase F Measurement hash differs")
    measurement = Measurement.model_validate_json(measurement_path.read_bytes())
    request = PhaseFDispatchRequest(
        schema_version=seal.schema_version,
        experiment_id=seal.experiment_id,
        plan_fingerprint=seal.plan_fingerprint,
        candidate_seal_sha256=seal.candidate_seal_sha256,
        candidate_snapshot_sha256=seal.candidate_snapshot_sha256,
        model_turn_ceiling=seal.model_turn_ceiling,
        budget_mode=seal.budget_mode,
        cell_completion_deadline_seconds=seal.cell_completion_deadline_seconds,
        execution_ordinal=seal.execution_ordinal,
        cell_id=seal.cell_id,
        fixture_id=seal.fixture_id,
        variant_id=seal.variant_id,
        runtime_mode=seal.runtime_mode,
        automatic_continuation=False,
        request_sha256=seal.request_sha256,
    )
    adapter_path = (cell_root / seal.adapter_evidence_path).resolve()
    if not adapter_path.is_relative_to(cell_root) or not adapter_path.is_file():
        raise PhaseFFinalizationError("Phase F sealed adapter Evidence is unavailable")
    adapter_ref = next(
        (item for item in seal.files if item.path == seal.adapter_evidence_path),
        None,
    )
    if adapter_ref is None or adapter_ref.sha256 != seal.worker_artifact_sha256:
        raise PhaseFFinalizationError("Phase F sealed adapter identity differs")
    adapter_payload = json.loads(adapter_path.read_text(encoding="utf-8"))
    if not isinstance(adapter_payload, dict):
        raise PhaseFFinalizationError("Phase F sealed adapter Evidence is invalid")
    _accounting, logical_turn_count = _verify_adapter_turn_evidence(
        request=request,
        expected_actual_model_turns=seal.actual_model_turns,
        adapter_payload=adapter_payload,
    )
    measurement_turn_count = measurement.resource.turn_count.value
    if (
        measurement.identity.cell_id != seal.cell_id
        or measurement.identity.experiment_id != seal.experiment_id
        or measurement.identity.execution_ordinal != seal.execution_ordinal
        or measurement.identity.fixture_id != seal.fixture_id
        or measurement.identity.variant_id != seal.variant_id
        or measurement.provenance.variant_artifact_sha256
        != seal.worker_artifact_sha256
        or measurement.variant_metrics.values.get("judge_observation_sha256")
        != seal.judge_observation_sha256
        or measurement.variant_metrics.values.get("actual_model_turns")
        != seal.actual_model_turns
        or measurement_turn_count != logical_turn_count
    ):
        raise PhaseFFinalizationError("Phase F Measurement identity differs from seal")
    return measurement
