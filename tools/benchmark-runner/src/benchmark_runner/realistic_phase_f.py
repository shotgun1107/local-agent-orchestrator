"""One-Cell Phase F controller for the sealed realistic comparison Plan.

This module owns only dispatch order, durable one-shot claims, and state.  It
does not contain a Codex/SDK backend.  A later, separately approved adapter may
implement :class:`PhaseFCellBackend`; the model-free tests use an exact fake.
One call can dispatch at most one Cell and always returns before the next Cell.
"""

from __future__ import annotations

import os
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal, Protocol

from pydantic import Field, JsonValue, field_validator, model_validator

from benchmark_runner.contract import (
    ExecutionPlan,
    PlannedCell,
    Sha256,
    StrictModel,
    present_api_key_environment_names,
    utc_now,
)
from benchmark_runner.realistic_phase_e import (
    PHASE_E_TRACK,
    PhaseEStageManifest,
    VerifiedPhaseECandidateSnapshot,
    verify_phase_e_candidate_snapshot,
)
from benchmark_runner.realistic_routing import canonical_json_bytes, canonical_sha256
from benchmark_runner.runner import atomic_write, sha256_bytes, sha256_file


PHASE_F_STATE_FILENAME = "phase-f-state.json"
PHASE_F_PLAN_FILENAME = "execution-plan.json"
PHASE_F_CELLS_DIRECTORY = "cells"
PHASE_F_CLAIM_FILENAME = "dispatch-claim.json"
PHASE_F_BACKEND_RESULT_FILENAME = "backend-result.json"
PHASE_F_ANCHOR_DIRECTORY = "phase-f-cell-anchors"
PHASE_F_EXECUTION_ANCHOR_FILENAME = "execution-anchor.json"
PHASE_F_INITIAL_STATE_ANCHOR_FILENAME = "initial-state.json"
PHASE_F_CELL_ANCHOR_FILENAME = "cell-anchor.json"


class PhaseFControllerError(RuntimeError):
    """Raised when the sealed Plan or one-Cell dispatch contract is violated."""


def _timestamp_text(value: datetime) -> str:
    """Match Pydantic's canonical UTC JSON representation before hashing."""

    return value.isoformat().replace("+00:00", "Z")


class PhaseFRuntimeMode(StrEnum):
    MODEL_FREE_FAKE = "model_free_fake"
    LIVE_CHATGPT = "live_chatgpt"


class PhaseFCellLifecycle(StrEnum):
    PLANNED = "PLANNED"
    DISPATCH_CLAIMED = "DISPATCH_CLAIMED"
    SEALED = "SEALED"
    FAILED = "FAILED"


class PhaseFCellState(StrictModel):
    execution_ordinal: int = Field(ge=1, le=4)
    cell_id: str
    fixture_id: str
    variant_id: Literal["ss1", "b1"]
    lifecycle: PhaseFCellLifecycle
    claimed_at: datetime | None = None
    completed_at: datetime | None = None
    runtime_mode: PhaseFRuntimeMode | None = None
    actual_model_turns: int | None = Field(default=None, ge=0)
    backend_result_sha256: Sha256 | None = None
    failure_type: str | None = None
    automatic_retry: Literal[False] = False

    @field_validator("claimed_at", "completed_at")
    @classmethod
    def timestamps_have_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("Phase F Cell timestamp must include a timezone")
        return value

    @model_validator(mode="after")
    def lifecycle_fields_match(self) -> "PhaseFCellState":
        if self.lifecycle is PhaseFCellLifecycle.PLANNED:
            if any(
                value is not None
                for value in (
                    self.claimed_at,
                    self.completed_at,
                    self.runtime_mode,
                    self.actual_model_turns,
                    self.backend_result_sha256,
                    self.failure_type,
                )
            ):
                raise ValueError("planned Phase F Cell cannot have execution Evidence")
        elif self.lifecycle is PhaseFCellLifecycle.DISPATCH_CLAIMED:
            if self.claimed_at is None or self.runtime_mode is None:
                raise ValueError("claimed Phase F Cell requires claim time and runtime mode")
            if any(
                value is not None
                for value in (
                    self.completed_at,
                    self.actual_model_turns,
                    self.backend_result_sha256,
                    self.failure_type,
                )
            ):
                raise ValueError("claimed Phase F Cell cannot contain a terminal result")
        elif self.lifecycle is PhaseFCellLifecycle.SEALED:
            if (
                self.claimed_at is None
                or self.completed_at is None
                or self.runtime_mode is None
                or self.actual_model_turns is None
                or self.backend_result_sha256 is None
                or self.failure_type is not None
            ):
                raise ValueError("sealed Phase F Cell requires complete backend Evidence")
        elif (
            self.claimed_at is None
            or self.completed_at is None
            or self.runtime_mode is None
            or self.failure_type is None
            or self.actual_model_turns is not None
            or self.backend_result_sha256 is not None
        ):
            raise ValueError("failed Phase F Cell fields differ")
        if self.runtime_mode is PhaseFRuntimeMode.MODEL_FREE_FAKE:
            if self.actual_model_turns not in {None, 0}:
                raise ValueError("model-free fake Cell cannot report model turns")
        if (
            self.lifecycle is PhaseFCellLifecycle.SEALED
            and self.runtime_mode is PhaseFRuntimeMode.LIVE_CHATGPT
            and (self.actual_model_turns is None or self.actual_model_turns < 1)
        ):
            raise ValueError("live Phase F Cell must prove at least one model turn")
        return self


class PhaseFExecutionState(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["realistic_phase_f_execution_state"] = (
        "realistic_phase_f_execution_state"
    )
    experiment_id: str
    plan_fingerprint: Sha256
    plan_sha256: Sha256
    candidate_seal_sha256: Sha256
    candidate_seal_file_sha256: Sha256
    candidate_snapshot_sha256: Sha256
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    cells: list[PhaseFCellState] = Field(min_length=4, max_length=4)
    automatic_continuation: Literal[False] = False
    initialized_at: datetime
    state_sha256: Sha256

    @field_validator("initialized_at")
    @classmethod
    def timestamp_has_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Phase F timestamp must include a timezone")
        return value

    @model_validator(mode="after")
    def state_is_coherent(self) -> "PhaseFExecutionState":
        if [item.execution_ordinal for item in self.cells] != [1, 2, 3, 4]:
            raise ValueError("Phase F state must preserve exact Cell order")
        seen_nonsealed = False
        terminal_unsealed = 0
        for cell in self.cells:
            if cell.lifecycle is PhaseFCellLifecycle.SEALED:
                if seen_nonsealed:
                    raise ValueError("sealed Phase F Cells must form an ordinal prefix")
            else:
                seen_nonsealed = True
                if cell.lifecycle is not PhaseFCellLifecycle.PLANNED:
                    terminal_unsealed += 1
        if terminal_unsealed > 1:
            raise ValueError("Phase F state has more than one unsealed claimed Cell")
        payload = self.model_dump(mode="json", exclude={"state_sha256"})
        if self.state_sha256 != canonical_sha256(payload):
            raise ValueError("Phase F state hash mismatch")
        return self


class PhaseFDispatchRequest(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["realistic_phase_f_cell_dispatch"] = (
        "realistic_phase_f_cell_dispatch"
    )
    experiment_id: str
    plan_fingerprint: Sha256
    candidate_seal_sha256: Sha256
    candidate_snapshot_sha256: Sha256
    model_turn_ceiling: int = Field(ge=1)
    execution_ordinal: int = Field(ge=1, le=4)
    cell_id: str
    fixture_id: str
    variant_id: Literal["ss1", "b1"]
    runtime_mode: PhaseFRuntimeMode
    automatic_continuation: Literal[False] = False
    request_sha256: Sha256

    @model_validator(mode="after")
    def request_hash_matches(self) -> "PhaseFDispatchRequest":
        payload = self.model_dump(mode="json", exclude={"request_sha256"})
        if self.request_sha256 != canonical_sha256(payload):
            raise ValueError("Phase F dispatch request hash mismatch")
        return self


class PhaseFDispatchClaim(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["realistic_phase_f_dispatch_claim"] = (
        "realistic_phase_f_dispatch_claim"
    )
    request: PhaseFDispatchRequest
    claimed_at: datetime
    automatic_retry: Literal[False] = False
    claim_sha256: Sha256

    @model_validator(mode="after")
    def claim_hash_matches(self) -> "PhaseFDispatchClaim":
        payload = self.model_dump(mode="json", exclude={"claim_sha256"})
        if self.claim_sha256 != canonical_sha256(payload):
            raise ValueError("Phase F dispatch claim hash mismatch")
        return self


class PhaseFBackendResult(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["realistic_phase_f_backend_result"] = (
        "realistic_phase_f_backend_result"
    )
    experiment_id: str
    plan_fingerprint: Sha256
    candidate_seal_sha256: Sha256
    candidate_snapshot_sha256: Sha256
    model_turn_ceiling: int = Field(ge=1)
    execution_ordinal: int = Field(ge=1, le=4)
    cell_id: str
    fixture_id: str
    variant_id: Literal["ss1", "b1"]
    runtime_mode: PhaseFRuntimeMode
    request_sha256: Sha256
    outcome_state: str = Field(min_length=1)
    actual_model_turns: int = Field(ge=0)
    sealed_artifact_sha256: Sha256
    public_summary: dict[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def turn_count_matches_mode(self) -> "PhaseFBackendResult":
        if (
            self.runtime_mode is PhaseFRuntimeMode.MODEL_FREE_FAKE
            and self.actual_model_turns != 0
        ):
            raise ValueError("model-free fake result cannot contain model turns")
        if (
            self.runtime_mode is PhaseFRuntimeMode.LIVE_CHATGPT
            and self.actual_model_turns < 1
        ):
            raise ValueError("live backend result must prove a model turn")
        return self


class PhaseFModelTurnReceipt(StrictModel):
    schema_version: Literal[1] = 1
    ordinal: int = Field(ge=1)
    task_id: str = Field(min_length=1)
    status: Literal["accepted", "simulated", "start_outcome_unknown"]
    turn_id_sha256: Sha256 | None = None
    receipt_sha256: Sha256

    @model_validator(mode="after")
    def receipt_hash_matches(self) -> "PhaseFModelTurnReceipt":
        if self.status == "start_outcome_unknown" and self.turn_id_sha256 is not None:
            raise ValueError("uncertain Phase F turn cannot claim a turn ID")
        if self.status != "start_outcome_unknown" and self.turn_id_sha256 is None:
            raise ValueError("accepted Phase F turn requires a receipt identity")
        payload = self.model_dump(
            mode="json",
            exclude={"receipt_sha256"},
            exclude_none=True,
        )
        if self.receipt_sha256 != canonical_sha256(payload):
            raise ValueError("Phase F turn receipt hash mismatch")
        return self


class PhaseFModelTurnAccounting(StrictModel):
    schema_version: Literal[1] = 1
    basis: Literal["turn_start_requests_issued"] = "turn_start_requests_issued"
    runtime_mode: PhaseFRuntimeMode
    model_turn_ceiling: int = Field(ge=1)
    turn_start_attempts: int = Field(ge=0)
    actual_model_turns: int = Field(ge=0)
    runtime_reported_model_turns: int = Field(ge=0)
    receipts: list[PhaseFModelTurnReceipt]

    @model_validator(mode="after")
    def accounting_is_coherent(self) -> "PhaseFModelTurnAccounting":
        if [item.ordinal for item in self.receipts] != list(
            range(1, len(self.receipts) + 1)
        ):
            raise ValueError("Phase F turn receipt ordinals differ")
        if self.turn_start_attempts != len(self.receipts):
            raise ValueError("Phase F turn receipt count differs")
        expected_actual = (
            0
            if self.runtime_mode is PhaseFRuntimeMode.MODEL_FREE_FAKE
            else self.turn_start_attempts
        )
        if self.actual_model_turns != expected_actual:
            raise ValueError("Phase F actual turn accounting differs")
        if self.turn_start_attempts > self.model_turn_ceiling:
            raise ValueError("Phase F turn accounting exceeds its ceiling")
        return self


def phase_f_model_turn_receipt(
    *,
    ordinal: int,
    task_id: str,
    status: Literal["accepted", "simulated", "start_outcome_unknown"],
    turn_id: str | None,
) -> PhaseFModelTurnReceipt:
    values: dict[str, object] = {
        "schema_version": 1,
        "ordinal": ordinal,
        "task_id": task_id,
        "status": status,
    }
    if turn_id is not None:
        values["turn_id_sha256"] = sha256_bytes(turn_id.encode("utf-8"))
    return PhaseFModelTurnReceipt(
        **values,
        receipt_sha256=canonical_sha256(values),
    )


def phase_f_backend_result_matches_request(
    request: PhaseFDispatchRequest,
    result: PhaseFBackendResult,
) -> bool:
    return (
        result.experiment_id,
        result.plan_fingerprint,
        result.candidate_seal_sha256,
        result.candidate_snapshot_sha256,
        result.model_turn_ceiling,
        result.execution_ordinal,
        result.cell_id,
        result.fixture_id,
        result.variant_id,
        result.runtime_mode,
        result.request_sha256,
    ) == (
        request.experiment_id,
        request.plan_fingerprint,
        request.candidate_seal_sha256,
        request.candidate_snapshot_sha256,
        request.model_turn_ceiling,
        request.execution_ordinal,
        request.cell_id,
        request.fixture_id,
        request.variant_id,
        request.runtime_mode,
        request.request_sha256,
    )


class PhaseFCellBackend(Protocol):
    """Injected backend boundary; no concrete SDK implementation lives here."""

    runtime_mode: PhaseFRuntimeMode

    def run_one_cell(self, request: PhaseFDispatchRequest) -> PhaseFBackendResult: ...


class PhaseFOneCellRunResult(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["realistic_phase_f_one_cell_result"] = (
        "realistic_phase_f_one_cell_result"
    )
    experiment_id: str
    executed_cell_id: str
    executed_ordinal: int
    runtime_mode: PhaseFRuntimeMode
    actual_model_turns: int
    backend_result_sha256: Sha256
    cell_anchor_sha256: Sha256
    cell_anchor_file_sha256: Sha256
    next_cell_id: str | None
    next_execution_ordinal: int | None
    automatic_continuation: Literal[False] = False


class PhaseFExecutionAnchor(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["realistic_phase_f_execution_anchor"] = (
        "realistic_phase_f_execution_anchor"
    )
    experiment_id: str
    plan_sha256: Sha256
    candidate_seal_sha256: Sha256
    candidate_snapshot_sha256: Sha256
    initialized_state_sha256: Sha256
    anchor_sha256: Sha256

    @model_validator(mode="after")
    def anchor_hash_matches(self) -> "PhaseFExecutionAnchor":
        payload = self.model_dump(mode="json", exclude={"anchor_sha256"})
        if self.anchor_sha256 != canonical_sha256(payload):
            raise ValueError("Phase F execution anchor hash mismatch")
        return self


class PhaseFCellAnchor(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["realistic_phase_f_cell_anchor"] = "realistic_phase_f_cell_anchor"
    experiment_id: str
    execution_ordinal: int = Field(ge=1, le=4)
    cell_id: str
    request_sha256: Sha256
    candidate_snapshot_sha256: Sha256
    model_turn_ceiling: int = Field(ge=1)
    actual_model_turns: int = Field(ge=0)
    backend_result_sha256: Sha256
    sealed_artifact_sha256: Sha256
    previous_anchor_sha256: Sha256
    anchor_sha256: Sha256

    @model_validator(mode="after")
    def anchor_hash_matches(self) -> "PhaseFCellAnchor":
        payload = self.model_dump(mode="json", exclude={"anchor_sha256"})
        if self.anchor_sha256 != canonical_sha256(payload):
            raise ValueError("Phase F Cell anchor hash mismatch")
        return self


def _state_with_hash(values: dict[str, object]) -> PhaseFExecutionState:
    return PhaseFExecutionState(**values, state_sha256=canonical_sha256(values))


def _request_for(
    *,
    plan: ExecutionPlan,
    snapshot: VerifiedPhaseECandidateSnapshot,
    cell: PlannedCell,
    runtime_mode: PhaseFRuntimeMode,
) -> PhaseFDispatchRequest:
    model_turn_ceiling = phase_f_cell_model_turn_ceiling(
        stage=snapshot.stage,
        cell=cell,
    )
    values: dict[str, object] = {
        "schema_version": 1,
        "kind": "realistic_phase_f_cell_dispatch",
        "experiment_id": plan.experiment_id,
        "plan_fingerprint": plan.plan_fingerprint,
        "candidate_seal_sha256": snapshot.seal.seal_sha256,
        "candidate_snapshot_sha256": snapshot.snapshot_sha256,
        "model_turn_ceiling": model_turn_ceiling,
        "execution_ordinal": cell.execution_ordinal,
        "cell_id": cell.cell_id,
        "fixture_id": cell.fixture_id,
        "variant_id": cell.variant_id,
        "runtime_mode": runtime_mode.value,
        "automatic_continuation": False,
    }
    return PhaseFDispatchRequest(**values, request_sha256=canonical_sha256(values))


def _claim_for(request: PhaseFDispatchRequest, claimed_at: datetime) -> PhaseFDispatchClaim:
    values: dict[str, object] = {
        "schema_version": 1,
        "kind": "realistic_phase_f_dispatch_claim",
        "request": request.model_dump(mode="json"),
        "claimed_at": _timestamp_text(claimed_at),
        "automatic_retry": False,
    }
    return PhaseFDispatchClaim(**values, claim_sha256=canonical_sha256(values))


def _write_new(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise PhaseFControllerError(f"Phase F write-once artifact exists: {path.name}") from exc


def _validated_anchor_root(
    *,
    repository: Path,
    candidate_root: Path,
    state_root: Path,
    anchor_root: Path,
) -> Path:
    anchor_root = anchor_root.resolve()
    forbidden = (repository.resolve(), candidate_root.resolve(), state_root.resolve())
    if any(
        anchor_root == root
        or anchor_root.is_relative_to(root)
        or root.is_relative_to(anchor_root)
        for root in forbidden
    ):
        raise PhaseFControllerError(
            "Phase F anchor root must be independent of source, candidate, and state"
        )
    return anchor_root


def _execution_anchor_root(anchor_root: Path, experiment_id: str) -> Path:
    return anchor_root / PHASE_F_ANCHOR_DIRECTORY / experiment_id


def _cell_anchor_path(
    anchor_root: Path,
    experiment_id: str,
    cell_id: str,
) -> Path:
    return (
        _execution_anchor_root(anchor_root, experiment_id)
        / PHASE_F_CELLS_DIRECTORY
        / cell_id
        / PHASE_F_CELL_ANCHOR_FILENAME
    )


def load_verified_phase_f_candidate(
    repository: Path,
    candidate_root: Path,
) -> VerifiedPhaseECandidateSnapshot:
    snapshot = verify_phase_e_candidate_snapshot(repository, candidate_root)
    seal = snapshot.seal
    plan = snapshot.plan
    if (
        plan.environment_fingerprint.get("source_commit") != seal.source_commit
        or plan.environment_fingerprint.get("auth_method") != "chatgpt"
        or plan.decision_policy.get("stage_id") != "realistic-high-difficulty-initial"
        or plan.decision_policy.get("one_cell_per_invocation") is not True
        or plan.decision_policy.get("explicit_confirmation_per_cell") is not True
        or plan.decision_policy.get("phase_f_model_usage_approved") is not False
        or next(
            (
                item.value
                for item in plan.plan_supplemented
                if item.field == "track"
            ),
            None,
        )
        != PHASE_E_TRACK
    ):
        raise PhaseFControllerError("Phase E Plan is not the approved Phase F input")
    expected = [
        (1, "realistic-compat-migration-001", "ss1"),
        (2, "realistic-compat-migration-001", "b1"),
        (3, "realistic-incident-repair-001", "b1"),
        (4, "realistic-incident-repair-001", "ss1"),
    ]
    actual = [
        (item.execution_ordinal, item.fixture_id, item.variant_id)
        for item in sorted(plan.cells, key=lambda value: value.execution_ordinal)
    ]
    if actual != expected:
        raise PhaseFControllerError("Phase F Plan Cell order differs")
    return snapshot


def phase_f_cell_model_turn_ceiling(
    *,
    stage: PhaseEStageManifest,
    cell: PlannedCell,
) -> int:
    """Resolve one Cell's turn ceiling from the verified candidate stage."""
    matching_stage_cells = [
        item for item in stage.cell_order if item.ordinal == cell.execution_ordinal
    ]
    if len(matching_stage_cells) != 1:
        raise PhaseFControllerError("Phase F stage Cell budget binding differs")
    stage_cell = matching_stage_cells[0]
    if stage_cell.variant_id != cell.variant_id:
        raise PhaseFControllerError("Phase F stage Cell variant binding differs")

    matching_profiles = [
        item for item in stage.profiles if item.profile_id == stage_cell.profile_id
    ]
    if (
        len(matching_profiles) != 1
        or matching_profiles[0].snapshot_id != cell.fixture_id
    ):
        raise PhaseFControllerError("Phase F stage Cell profile binding differs")

    profile_budgets = stage.budget.profile_budgets
    if profile_budgets is None:
        return stage.budget.total_turn_ceiling_per_variant
    matching_budgets = [
        item for item in profile_budgets if item.profile_id == stage_cell.profile_id
    ]
    if len(matching_budgets) != 1:
        raise PhaseFControllerError("Phase F stage Cell turn budget differs")
    return matching_budgets[0].total_turn_ceiling_per_variant


def initialize_phase_f_execution(
    *,
    repository: Path,
    candidate_root: Path,
    state_root: Path,
    anchor_root: Path | None = None,
    initialized_at: datetime | None = None,
) -> Path:
    """Bind one external state root to the sealed Phase E candidate, with 0 turns."""

    repository = repository.resolve()
    candidate_root = candidate_root.resolve()
    state_root = state_root.resolve()
    if anchor_root is None:
        anchor_root = state_root.parent / f"{state_root.name}-anchors"
    anchor_root = _validated_anchor_root(
        repository=repository,
        candidate_root=candidate_root,
        state_root=state_root,
        anchor_root=anchor_root,
    )
    if state_root.is_relative_to(repository) or state_root.is_relative_to(candidate_root):
        raise PhaseFControllerError("Phase F state root must be outside source and candidate")
    if present_api_key_environment_names():
        raise PhaseFControllerError("API key environment names are present")
    snapshot = load_verified_phase_f_candidate(repository, candidate_root)
    seal = snapshot.seal
    plan = snapshot.plan
    plan_bytes = snapshot.file_bytes(PHASE_F_PLAN_FILENAME)
    experiment_dir = state_root / plan.experiment_id
    experiment_dir.mkdir(parents=True, exist_ok=False)
    _write_new(experiment_dir / PHASE_F_PLAN_FILENAME, plan_bytes)
    _write_new(
        experiment_dir / "candidate-seal.json",
        snapshot.file_bytes("candidate-seal.json"),
    )
    cells = [
        PhaseFCellState(
            execution_ordinal=item.execution_ordinal,
            cell_id=item.cell_id,
            fixture_id=item.fixture_id,
            variant_id=item.variant_id,
            lifecycle=PhaseFCellLifecycle.PLANNED,
        )
        for item in sorted(plan.cells, key=lambda value: value.execution_ordinal)
    ]
    values: dict[str, object] = {
        "schema_version": 1,
        "kind": "realistic_phase_f_execution_state",
        "experiment_id": plan.experiment_id,
        "plan_fingerprint": plan.plan_fingerprint,
        "plan_sha256": sha256_bytes(plan_bytes),
        "candidate_seal_sha256": seal.seal_sha256,
        "candidate_seal_file_sha256": sha256_file(
            experiment_dir / "candidate-seal.json"
        ),
        "candidate_snapshot_sha256": snapshot.snapshot_sha256,
        "source_commit": seal.source_commit,
        "cells": [item.model_dump(mode="json") for item in cells],
        "automatic_continuation": False,
        "initialized_at": _timestamp_text(initialized_at or utc_now()),
    }
    state = _state_with_hash(values)
    state_bytes = canonical_json_bytes(state)
    _write_new(experiment_dir / PHASE_F_STATE_FILENAME, state_bytes)
    execution_anchor_root = _execution_anchor_root(anchor_root, plan.experiment_id)
    _write_new(
        execution_anchor_root / PHASE_F_INITIAL_STATE_ANCHOR_FILENAME,
        state_bytes,
    )
    anchor_values = {
        "schema_version": 1,
        "kind": "realistic_phase_f_execution_anchor",
        "experiment_id": plan.experiment_id,
        "plan_sha256": sha256_bytes(plan_bytes),
        "candidate_seal_sha256": seal.seal_sha256,
        "candidate_snapshot_sha256": snapshot.snapshot_sha256,
        "initialized_state_sha256": sha256_bytes(state_bytes),
    }
    execution_anchor = PhaseFExecutionAnchor(
        **anchor_values,
        anchor_sha256=canonical_sha256(anchor_values),
    )
    _write_new(
        execution_anchor_root / PHASE_F_EXECUTION_ANCHOR_FILENAME,
        canonical_json_bytes(execution_anchor),
    )
    return experiment_dir


def _load_execution(
    *,
    repository: Path,
    candidate_root: Path,
    experiment_dir: Path,
    anchor_root: Path,
) -> tuple[
    VerifiedPhaseECandidateSnapshot,
    PhaseFExecutionState,
]:
    repository = repository.resolve()
    candidate_root = candidate_root.resolve()
    experiment_dir = experiment_dir.resolve()
    state_root = experiment_dir.parent
    anchor_root = _validated_anchor_root(
        repository=repository,
        candidate_root=candidate_root,
        state_root=state_root,
        anchor_root=anchor_root,
    )
    snapshot = load_verified_phase_f_candidate(repository, candidate_root)
    seal = snapshot.seal
    candidate_plan = snapshot.plan
    candidate_plan_bytes = snapshot.file_bytes(PHASE_F_PLAN_FILENAME)
    candidate_stage = snapshot.stage
    persisted_plan_bytes = (experiment_dir / PHASE_F_PLAN_FILENAME).read_bytes()
    persisted_candidate_seal_bytes = (experiment_dir / "candidate-seal.json").read_bytes()
    candidate_seal_bytes = snapshot.file_bytes("candidate-seal.json")
    persisted_plan = ExecutionPlan.model_validate_json(persisted_plan_bytes)
    state = PhaseFExecutionState.model_validate_json(
        (experiment_dir / PHASE_F_STATE_FILENAME).read_bytes()
    )
    if (
        experiment_dir.name != candidate_plan.experiment_id
        or persisted_plan != candidate_plan
        or persisted_plan_bytes != candidate_plan_bytes
        or persisted_candidate_seal_bytes != candidate_seal_bytes
        or state.experiment_id != candidate_plan.experiment_id
        or state.plan_fingerprint != candidate_plan.plan_fingerprint
        or state.plan_sha256 != sha256_bytes(candidate_plan_bytes)
        or state.candidate_seal_sha256 != seal.seal_sha256
        or state.candidate_seal_file_sha256
        != sha256_bytes(candidate_seal_bytes)
        or state.candidate_snapshot_sha256 != snapshot.snapshot_sha256
        or state.source_commit != seal.source_commit
    ):
        raise PhaseFControllerError("Phase F state differs from the sealed candidate")
    execution_anchor_root = _execution_anchor_root(
        anchor_root,
        candidate_plan.experiment_id,
    )
    initial_state_bytes = (
        execution_anchor_root / PHASE_F_INITIAL_STATE_ANCHOR_FILENAME
    ).read_bytes()
    execution_anchor = PhaseFExecutionAnchor.model_validate_json(
        (execution_anchor_root / PHASE_F_EXECUTION_ANCHOR_FILENAME).read_bytes()
    )
    if (
        execution_anchor.experiment_id != candidate_plan.experiment_id
        or execution_anchor.plan_sha256 != sha256_bytes(candidate_plan_bytes)
        or execution_anchor.candidate_seal_sha256 != seal.seal_sha256
        or execution_anchor.candidate_snapshot_sha256 != snapshot.snapshot_sha256
        or execution_anchor.initialized_state_sha256 != sha256_bytes(initial_state_bytes)
    ):
        raise PhaseFControllerError("Phase F execution anchor differs")
    initial_state = PhaseFExecutionState.model_validate_json(initial_state_bytes)
    if (
        initial_state.experiment_id != candidate_plan.experiment_id
        or initial_state.plan_fingerprint != candidate_plan.plan_fingerprint
        or initial_state.plan_sha256 != sha256_bytes(candidate_plan_bytes)
        or initial_state.candidate_seal_sha256 != seal.seal_sha256
        or initial_state.candidate_snapshot_sha256 != snapshot.snapshot_sha256
        or initial_state.source_commit != seal.source_commit
        or [
            (
                item.execution_ordinal,
                item.cell_id,
                item.fixture_id,
                item.variant_id,
            )
            for item in initial_state.cells
        ]
        != [
            (
                item.execution_ordinal,
                item.cell_id,
                item.fixture_id,
                item.variant_id,
            )
            for item in state.cells
        ]
        or any(
            item.lifecycle is not PhaseFCellLifecycle.PLANNED
            for item in initial_state.cells
        )
    ):
        raise PhaseFControllerError("Phase F initial state anchor differs")
    previous_anchor_sha256 = execution_anchor.anchor_sha256
    for cell in state.cells:
        cell_dir = experiment_dir / PHASE_F_CELLS_DIRECTORY / cell.cell_id
        claim_path = cell_dir / PHASE_F_CLAIM_FILENAME
        result_path = cell_dir / PHASE_F_BACKEND_RESULT_FILENAME
        if cell.lifecycle is PhaseFCellLifecycle.PLANNED:
            if (
                claim_path.exists()
                or result_path.exists()
                or _cell_anchor_path(
                    anchor_root,
                    state.experiment_id,
                    cell.cell_id,
                ).exists()
            ):
                raise PhaseFControllerError("planned Phase F Cell has dispatch artifacts")
            continue
        claim = PhaseFDispatchClaim.model_validate_json(claim_path.read_bytes())
        if (
            claim.request.cell_id != cell.cell_id
            or claim.request.execution_ordinal != cell.execution_ordinal
            or claim.request.runtime_mode != cell.runtime_mode
            or claim.request.plan_fingerprint != state.plan_fingerprint
            or claim.request.candidate_seal_sha256 != state.candidate_seal_sha256
            or claim.request.candidate_snapshot_sha256
            != state.candidate_snapshot_sha256
        ):
            raise PhaseFControllerError("Phase F dispatch claim differs from state")
        planned_cell = next(
            item for item in candidate_plan.cells if item.cell_id == cell.cell_id
        )
        turn_ceiling = phase_f_cell_model_turn_ceiling(
            stage=candidate_stage,
            cell=planned_cell,
        )
        if claim.request.model_turn_ceiling != turn_ceiling:
            raise PhaseFControllerError("Phase F dispatch claim turn ceiling differs")
        if cell.lifecycle is PhaseFCellLifecycle.SEALED:
            if (
                not result_path.is_file()
                or sha256_file(result_path) != cell.backend_result_sha256
            ):
                raise PhaseFControllerError("sealed Phase F backend result differs")
            result = PhaseFBackendResult.model_validate_json(result_path.read_bytes())
            if (
                result.experiment_id != state.experiment_id
                or result.plan_fingerprint != state.plan_fingerprint
                or result.candidate_seal_sha256 != state.candidate_seal_sha256
                or result.candidate_snapshot_sha256
                != state.candidate_snapshot_sha256
                or result.model_turn_ceiling != turn_ceiling
                or result.execution_ordinal != cell.execution_ordinal
                or result.cell_id != cell.cell_id
                or result.fixture_id != cell.fixture_id
                or result.variant_id != cell.variant_id
                or result.runtime_mode != cell.runtime_mode
                or result.request_sha256 != claim.request.request_sha256
                or result.actual_model_turns != cell.actual_model_turns
            ):
                raise PhaseFControllerError("sealed Phase F backend result identity differs")
            if result.actual_model_turns > turn_ceiling:
                raise PhaseFControllerError(
                    "sealed Phase F Cell exceeds its candidate turn ceiling"
                )
            if result.public_summary.get("final_cell_sealed") is True:
                finalization_cell_root = result.public_summary.get(
                    "finalization_cell_root"
                )
                if not isinstance(finalization_cell_root, str):
                    raise PhaseFControllerError(
                        "sealed Phase F finalization root is unavailable"
                    )
                from benchmark_runner.realistic_phase_f_finalize import (
                    verify_phase_f_cell_finalization,
                )

                measurement = verify_phase_f_cell_finalization(
                    Path(finalization_cell_root),
                    expected_seal_file_sha256=result.sealed_artifact_sha256,
                )
                if (
                    measurement.variant_metrics.values.get("actual_model_turns")
                    != result.actual_model_turns
                ):
                    raise PhaseFControllerError(
                        "sealed Phase F finalization turn count differs"
                    )
            result_sha256 = sha256_file(result_path)
            cell_anchor = PhaseFCellAnchor.model_validate_json(
                _cell_anchor_path(
                    anchor_root,
                    state.experiment_id,
                    cell.cell_id,
                ).read_bytes()
            )
            if (
                cell_anchor.experiment_id != state.experiment_id
                or cell_anchor.execution_ordinal != cell.execution_ordinal
                or cell_anchor.cell_id != cell.cell_id
                or cell_anchor.request_sha256 != claim.request.request_sha256
                or cell_anchor.candidate_snapshot_sha256
                != state.candidate_snapshot_sha256
                or cell_anchor.model_turn_ceiling != turn_ceiling
                or cell_anchor.actual_model_turns != result.actual_model_turns
                or cell_anchor.backend_result_sha256 != result_sha256
                or cell_anchor.sealed_artifact_sha256
                != result.sealed_artifact_sha256
                or cell_anchor.previous_anchor_sha256 != previous_anchor_sha256
            ):
                raise PhaseFControllerError("sealed Phase F Cell anchor differs")
            previous_anchor_sha256 = cell_anchor.anchor_sha256
        elif (
            result_path.exists()
            or _cell_anchor_path(
                anchor_root,
                state.experiment_id,
                cell.cell_id,
            ).exists()
        ):
            raise PhaseFControllerError("unsealed Phase F Cell has a backend result")
    return snapshot, state


def phase_f_status(
    *,
    repository: Path,
    candidate_root: Path,
    experiment_dir: Path,
    anchor_root: Path | None = None,
) -> dict[str, object]:
    if anchor_root is None:
        state_root = experiment_dir.resolve().parent
        anchor_root = state_root.parent / f"{state_root.name}-anchors"
    snapshot, state = _load_execution(
        repository=repository,
        candidate_root=candidate_root,
        experiment_dir=experiment_dir,
        anchor_root=anchor_root,
    )
    plan = snapshot.plan
    next_cell = next(
        (item for item in state.cells if item.lifecycle is PhaseFCellLifecycle.PLANNED),
        None,
    )
    sealed = sum(
        item.lifecycle is PhaseFCellLifecycle.SEALED for item in state.cells
    )
    stopped = any(
        item.lifecycle
        in {PhaseFCellLifecycle.DISPATCH_CLAIMED, PhaseFCellLifecycle.FAILED}
        for item in state.cells
    )
    return {
        "schema_version": 1,
        "kind": "realistic_phase_f_status",
        "experiment_id": plan.experiment_id,
        "planned_cells": len(state.cells),
        "sealed_cells": sealed,
        "next_cell_id": None if next_cell is None else next_cell.cell_id,
        "next_execution_ordinal": (
            None if next_cell is None else next_cell.execution_ordinal
        ),
        "complete": sealed == len(state.cells),
        "stopped": stopped,
        "automatic_continuation": False,
        "cells": [item.model_dump(mode="json") for item in state.cells],
    }


def _replace_cell(
    state: PhaseFExecutionState,
    replacement: PhaseFCellState,
) -> PhaseFExecutionState:
    cells = [
        replacement if item.cell_id == replacement.cell_id else item
        for item in state.cells
    ]
    values = state.model_dump(mode="json", exclude={"state_sha256"})
    values["cells"] = [item.model_dump(mode="json") for item in cells]
    return _state_with_hash(values)


def run_next_phase_f_cell(
    *,
    repository: Path,
    candidate_root: Path,
    experiment_dir: Path,
    backend: PhaseFCellBackend,
    expected_execution_ordinal: int,
    confirm_cell_dispatch: bool,
    confirm_model_usage: bool,
    anchor_root: Path | None = None,
) -> PhaseFOneCellRunResult:
    """Dispatch exactly the next Cell once, persist its result, and return."""

    if not confirm_cell_dispatch:
        raise PhaseFControllerError("Phase F Cell requires explicit dispatch confirmation")
    if present_api_key_environment_names():
        raise PhaseFControllerError("API key environment names are present")
    try:
        runtime_mode = PhaseFRuntimeMode(backend.runtime_mode)
    except ValueError as exc:
        raise PhaseFControllerError("Phase F backend runtime mode is invalid") from exc
    if runtime_mode is PhaseFRuntimeMode.LIVE_CHATGPT and not confirm_model_usage:
        raise PhaseFControllerError("live Phase F Cell requires model-usage confirmation")
    if runtime_mode is PhaseFRuntimeMode.MODEL_FREE_FAKE and confirm_model_usage:
        raise PhaseFControllerError("model-free Phase F test cannot consume model approval")
    if anchor_root is None:
        state_root = experiment_dir.resolve().parent
        anchor_root = state_root.parent / f"{state_root.name}-anchors"
    snapshot, state = _load_execution(
        repository=repository,
        candidate_root=candidate_root,
        experiment_dir=experiment_dir,
        anchor_root=anchor_root,
    )
    plan = snapshot.plan
    stage = snapshot.stage
    if any(
        item.lifecycle
        in {PhaseFCellLifecycle.DISPATCH_CLAIMED, PhaseFCellLifecycle.FAILED}
        for item in state.cells
    ):
        raise PhaseFControllerError("Phase F execution is stopped before another Cell")
    next_state = next(
        (item for item in state.cells if item.lifecycle is PhaseFCellLifecycle.PLANNED),
        None,
    )
    if next_state is None:
        raise PhaseFControllerError("Phase F execution has no remaining Cell")
    if next_state.execution_ordinal != expected_execution_ordinal:
        raise PhaseFControllerError(
            f"Phase F next Cell is ordinal {next_state.execution_ordinal}, not "
            f"{expected_execution_ordinal}"
        )
    planned_cell = next(
        item for item in plan.cells if item.cell_id == next_state.cell_id
    )
    request = _request_for(
        plan=plan,
        snapshot=snapshot,
        cell=planned_cell,
        runtime_mode=runtime_mode,
    )
    claimed_at = utc_now()
    claim = _claim_for(request, claimed_at)
    cell_dir = experiment_dir / PHASE_F_CELLS_DIRECTORY / planned_cell.cell_id
    _write_new(cell_dir / PHASE_F_CLAIM_FILENAME, canonical_json_bytes(claim))
    claimed_state = next_state.model_copy(
        update={
            "lifecycle": PhaseFCellLifecycle.DISPATCH_CLAIMED,
            "claimed_at": claimed_at,
            "runtime_mode": runtime_mode,
        }
    )
    state = _replace_cell(state, claimed_state)
    atomic_write(experiment_dir / PHASE_F_STATE_FILENAME, canonical_json_bytes(state))
    try:
        backend_result = backend.run_one_cell(request)
    except Exception as exc:
        failed_state = claimed_state.model_copy(
            update={
                "lifecycle": PhaseFCellLifecycle.FAILED,
                "completed_at": utc_now(),
                "failure_type": type(exc).__name__,
            }
        )
        state = _replace_cell(state, failed_state)
        atomic_write(experiment_dir / PHASE_F_STATE_FILENAME, canonical_json_bytes(state))
        raise
    expected_identity = (
        plan.experiment_id,
        plan.plan_fingerprint,
        snapshot.seal.seal_sha256,
        snapshot.snapshot_sha256,
        request.model_turn_ceiling,
        planned_cell.execution_ordinal,
        planned_cell.cell_id,
        planned_cell.fixture_id,
        planned_cell.variant_id,
        runtime_mode,
        request.request_sha256,
    )
    actual_identity = (
        backend_result.experiment_id,
        backend_result.plan_fingerprint,
        backend_result.candidate_seal_sha256,
        backend_result.candidate_snapshot_sha256,
        backend_result.model_turn_ceiling,
        backend_result.execution_ordinal,
        backend_result.cell_id,
        backend_result.fixture_id,
        backend_result.variant_id,
        backend_result.runtime_mode,
        backend_result.request_sha256,
    )
    if actual_identity != expected_identity:
        failed_state = claimed_state.model_copy(
            update={
                "lifecycle": PhaseFCellLifecycle.FAILED,
                "completed_at": utc_now(),
                "failure_type": "BackendIdentityMismatch",
            }
        )
        state = _replace_cell(state, failed_state)
        atomic_write(experiment_dir / PHASE_F_STATE_FILENAME, canonical_json_bytes(state))
        raise PhaseFControllerError("Phase F backend result identity differs")
    turn_ceiling = phase_f_cell_model_turn_ceiling(
        stage=stage,
        cell=planned_cell,
    )
    if backend_result.actual_model_turns > turn_ceiling:
        failed_state = claimed_state.model_copy(
            update={
                "lifecycle": PhaseFCellLifecycle.FAILED,
                "completed_at": utc_now(),
                "failure_type": "ModelTurnCeilingExceeded",
            }
        )
        state = _replace_cell(state, failed_state)
        atomic_write(experiment_dir / PHASE_F_STATE_FILENAME, canonical_json_bytes(state))
        raise PhaseFControllerError(
            "Phase F backend result model turns "
            f"{backend_result.actual_model_turns} exceed candidate Cell ceiling "
            f"{turn_ceiling}"
        )
    result_bytes = canonical_json_bytes(backend_result)
    result_sha256 = sha256_bytes(result_bytes)
    _write_new(cell_dir / PHASE_F_BACKEND_RESULT_FILENAME, result_bytes)
    previous_anchor_sha256 = PhaseFExecutionAnchor.model_validate_json(
        (
            _execution_anchor_root(anchor_root.resolve(), plan.experiment_id)
            / PHASE_F_EXECUTION_ANCHOR_FILENAME
        ).read_bytes()
    ).anchor_sha256
    prior_sealed = sorted(
        (
            item
            for item in state.cells
            if item.lifecycle is PhaseFCellLifecycle.SEALED
        ),
        key=lambda item: item.execution_ordinal,
    )
    if prior_sealed:
        previous_anchor_sha256 = PhaseFCellAnchor.model_validate_json(
            _cell_anchor_path(
                anchor_root.resolve(),
                plan.experiment_id,
                prior_sealed[-1].cell_id,
            ).read_bytes()
        ).anchor_sha256
    anchor_values = {
        "schema_version": 1,
        "kind": "realistic_phase_f_cell_anchor",
        "experiment_id": plan.experiment_id,
        "execution_ordinal": planned_cell.execution_ordinal,
        "cell_id": planned_cell.cell_id,
        "request_sha256": request.request_sha256,
        "candidate_snapshot_sha256": snapshot.snapshot_sha256,
        "model_turn_ceiling": turn_ceiling,
        "actual_model_turns": backend_result.actual_model_turns,
        "backend_result_sha256": result_sha256,
        "sealed_artifact_sha256": backend_result.sealed_artifact_sha256,
        "previous_anchor_sha256": previous_anchor_sha256,
    }
    cell_anchor = PhaseFCellAnchor(
        **anchor_values,
        anchor_sha256=canonical_sha256(anchor_values),
    )
    _write_new(
        _cell_anchor_path(
            anchor_root.resolve(),
            plan.experiment_id,
            planned_cell.cell_id,
        ),
        canonical_json_bytes(cell_anchor),
    )
    cell_anchor_bytes = canonical_json_bytes(cell_anchor)
    sealed_state = claimed_state.model_copy(
        update={
            "lifecycle": PhaseFCellLifecycle.SEALED,
            "completed_at": utc_now(),
            "actual_model_turns": backend_result.actual_model_turns,
            "backend_result_sha256": result_sha256,
        }
    )
    state = _replace_cell(state, sealed_state)
    atomic_write(experiment_dir / PHASE_F_STATE_FILENAME, canonical_json_bytes(state))
    following = next(
        (item for item in state.cells if item.lifecycle is PhaseFCellLifecycle.PLANNED),
        None,
    )
    return PhaseFOneCellRunResult(
        experiment_id=plan.experiment_id,
        executed_cell_id=planned_cell.cell_id,
        executed_ordinal=planned_cell.execution_ordinal,
        runtime_mode=runtime_mode,
        actual_model_turns=backend_result.actual_model_turns,
        backend_result_sha256=result_sha256,
        cell_anchor_sha256=cell_anchor.anchor_sha256,
        cell_anchor_file_sha256=sha256_bytes(cell_anchor_bytes),
        next_cell_id=None if following is None else following.cell_id,
        next_execution_ordinal=(
            None if following is None else following.execution_ordinal
        ),
        automatic_continuation=False,
    )
