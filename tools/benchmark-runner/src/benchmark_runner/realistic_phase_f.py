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
    PhaseECandidateSeal,
    PhaseEStageManifest,
    verify_phase_e_candidate,
)
from benchmark_runner.realistic_routing import canonical_json_bytes, canonical_sha256
from benchmark_runner.runner import atomic_write, sha256_bytes, sha256_file


PHASE_F_STATE_FILENAME = "phase-f-state.json"
PHASE_F_PLAN_FILENAME = "execution-plan.json"
PHASE_F_CELLS_DIRECTORY = "cells"
PHASE_F_CLAIM_FILENAME = "dispatch-claim.json"
PHASE_F_BACKEND_RESULT_FILENAME = "backend-result.json"


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
    next_cell_id: str | None
    next_execution_ordinal: int | None
    automatic_continuation: Literal[False] = False


def _state_with_hash(values: dict[str, object]) -> PhaseFExecutionState:
    return PhaseFExecutionState(**values, state_sha256=canonical_sha256(values))


def _request_for(
    *,
    plan: ExecutionPlan,
    seal: PhaseECandidateSeal,
    cell: PlannedCell,
    runtime_mode: PhaseFRuntimeMode,
) -> PhaseFDispatchRequest:
    values: dict[str, object] = {
        "schema_version": 1,
        "kind": "realistic_phase_f_cell_dispatch",
        "experiment_id": plan.experiment_id,
        "plan_fingerprint": plan.plan_fingerprint,
        "candidate_seal_sha256": seal.seal_sha256,
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


def load_verified_phase_f_candidate(
    repository: Path,
    candidate_root: Path,
) -> tuple[PhaseECandidateSeal, ExecutionPlan, bytes, PhaseEStageManifest]:
    plan_path = candidate_root / PHASE_F_PLAN_FILENAME
    stage_path = candidate_root / "stage-manifest.json"
    plan_bytes = plan_path.read_bytes()
    stage_bytes = stage_path.read_bytes()
    seal = verify_phase_e_candidate(repository, candidate_root)
    if plan_path.read_bytes() != plan_bytes or stage_path.read_bytes() != stage_bytes:
        raise PhaseFControllerError("Phase E candidate changed during verification")
    plan = ExecutionPlan.model_validate_json(plan_bytes)
    stage = PhaseEStageManifest.model_validate_json(stage_bytes)
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
    return seal, plan, plan_bytes, stage


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
    initialized_at: datetime | None = None,
) -> Path:
    """Bind one external state root to the sealed Phase E candidate, with 0 turns."""

    repository = repository.resolve()
    candidate_root = candidate_root.resolve()
    state_root = state_root.resolve()
    if state_root.is_relative_to(repository) or state_root.is_relative_to(candidate_root):
        raise PhaseFControllerError("Phase F state root must be outside source and candidate")
    if present_api_key_environment_names():
        raise PhaseFControllerError("API key environment names are present")
    seal, plan, plan_bytes, _stage = load_verified_phase_f_candidate(
        repository, candidate_root
    )
    experiment_dir = state_root / plan.experiment_id
    experiment_dir.mkdir(parents=True, exist_ok=False)
    _write_new(experiment_dir / PHASE_F_PLAN_FILENAME, plan_bytes)
    _write_new(
        experiment_dir / "candidate-seal.json",
        (candidate_root / "candidate-seal.json").read_bytes(),
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
            candidate_root / "candidate-seal.json"
        ),
        "source_commit": seal.source_commit,
        "cells": [item.model_dump(mode="json") for item in cells],
        "automatic_continuation": False,
        "initialized_at": _timestamp_text(initialized_at or utc_now()),
    }
    state = _state_with_hash(values)
    _write_new(experiment_dir / PHASE_F_STATE_FILENAME, canonical_json_bytes(state))
    return experiment_dir


def _load_execution(
    *,
    repository: Path,
    candidate_root: Path,
    experiment_dir: Path,
) -> tuple[
    PhaseECandidateSeal,
    ExecutionPlan,
    PhaseEStageManifest,
    PhaseFExecutionState,
]:
    repository = repository.resolve()
    candidate_root = candidate_root.resolve()
    experiment_dir = experiment_dir.resolve()
    (
        seal,
        candidate_plan,
        candidate_plan_bytes,
        candidate_stage,
    ) = load_verified_phase_f_candidate(repository, candidate_root)
    persisted_plan_bytes = (experiment_dir / PHASE_F_PLAN_FILENAME).read_bytes()
    persisted_candidate_seal_bytes = (experiment_dir / "candidate-seal.json").read_bytes()
    candidate_seal_bytes = (candidate_root / "candidate-seal.json").read_bytes()
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
        != sha256_file(candidate_root / "candidate-seal.json")
        or state.source_commit != seal.source_commit
    ):
        raise PhaseFControllerError("Phase F state differs from the sealed candidate")
    for cell in state.cells:
        cell_dir = experiment_dir / PHASE_F_CELLS_DIRECTORY / cell.cell_id
        claim_path = cell_dir / PHASE_F_CLAIM_FILENAME
        result_path = cell_dir / PHASE_F_BACKEND_RESULT_FILENAME
        if cell.lifecycle is PhaseFCellLifecycle.PLANNED:
            if claim_path.exists() or result_path.exists():
                raise PhaseFControllerError("planned Phase F Cell has dispatch artifacts")
            continue
        claim = PhaseFDispatchClaim.model_validate_json(claim_path.read_bytes())
        if (
            claim.request.cell_id != cell.cell_id
            or claim.request.execution_ordinal != cell.execution_ordinal
            or claim.request.runtime_mode != cell.runtime_mode
            or claim.request.plan_fingerprint != state.plan_fingerprint
            or claim.request.candidate_seal_sha256 != state.candidate_seal_sha256
        ):
            raise PhaseFControllerError("Phase F dispatch claim differs from state")
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
                or result.execution_ordinal != cell.execution_ordinal
                or result.cell_id != cell.cell_id
                or result.fixture_id != cell.fixture_id
                or result.variant_id != cell.variant_id
                or result.runtime_mode != cell.runtime_mode
                or result.request_sha256 != claim.request.request_sha256
                or result.actual_model_turns != cell.actual_model_turns
            ):
                raise PhaseFControllerError("sealed Phase F backend result identity differs")
            planned_cell = next(
                item for item in candidate_plan.cells if item.cell_id == cell.cell_id
            )
            turn_ceiling = phase_f_cell_model_turn_ceiling(
                stage=candidate_stage,
                cell=planned_cell,
            )
            if result.actual_model_turns > turn_ceiling:
                raise PhaseFControllerError(
                    "sealed Phase F Cell exceeds its candidate turn ceiling"
                )
        elif result_path.exists():
            raise PhaseFControllerError("unsealed Phase F Cell has a backend result")
    return seal, candidate_plan, candidate_stage, state


def phase_f_status(
    *,
    repository: Path,
    candidate_root: Path,
    experiment_dir: Path,
) -> dict[str, object]:
    _, plan, _stage, state = _load_execution(
        repository=repository,
        candidate_root=candidate_root,
        experiment_dir=experiment_dir,
    )
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
    seal, plan, stage, state = _load_execution(
        repository=repository,
        candidate_root=candidate_root,
        experiment_dir=experiment_dir,
    )
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
        seal=seal,
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
        next_cell_id=None if following is None else following.cell_id,
        next_execution_ordinal=(
            None if following is None else following.execution_ordinal
        ),
        automatic_continuation=False,
    )
