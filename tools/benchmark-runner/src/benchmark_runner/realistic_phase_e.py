"""Phase E zero-turn live candidate for the realistic SS1/B1 comparison.

This module freezes and verifies the four-Cell Execution Plan.  It deliberately
contains no Worker dispatch function: model use remains a separate Phase F
approval.  Source bytes are read from one exact Git commit and the candidate
seal is independently reproducible from versioned inputs.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Literal, Mapping

import yaml
from pydantic import Field, JsonValue, field_validator, model_validator

from benchmark_runner.contract import (
    ArtifactIdentity,
    ExecutionPlan,
    FixtureIdentity,
    PlanSupplement,
    PlannedCell,
    Sha256,
    StrictModel,
    present_api_key_environment_names,
    utc_now,
    validate_relative_path,
)
from benchmark_runner.plan import (
    assert_plan_integrity,
    build_sdk_controlled_plan,
    recompute_plan_fingerprint,
)
from benchmark_runner.realistic_routing import (
    B1PlanContract,
    CommonBudgetContract,
    PassiveBoundaryObservation,
    PassiveBoundaryRecord,
    ProfileBudgetContract,
    PropertyEvaluationEnvelope,
    REALISTIC_STAGE_ID,
    REALISTIC_SUITE_ID,
    REALISTIC_SUPPLEMENT_FIELD,
    RealisticRoutingPlanSupplement,
    Ss1PlanContract,
    canonical_json_bytes,
    canonical_sha256,
    neutral_review_prompt_sha256,
    parse_realistic_plan_supplement,
    ss1_result_schema,
)
from benchmark_runner.runner import atomic_write, sha256_file
from benchmark_runner.sdk_cells import RUNNER_FINGERPRINT_INPUTS


PHASE_E_TRACK = "sdk_routing_realistic_high_difficulty_live_initial"
PHASE_E_STAGE_RELATIVE = (
    "benchmarks/suites/sdk-routing-realistic-high-difficulty-v1/"
    "stages/realistic-high-difficulty-initial.json"
)
PHASE_E_CANDIDATE_KIND = "sdk_routing_realistic_phase_e_candidate"
PINNED_SDK_VERSION = "0.144.4"
PINNED_MODEL = "gpt-5.6-sol"
PINNED_REASONING_EFFORT = "high"
RUNTIME_BOUNDARY_ROOT = (
    "benchmarks/source-raw/runtime-boundary-phaseb-p001-p015-v1/raw/P015/"
    "S/runtime-boundary"
)
RUNTIME_BOUNDARY_FILES = {
    "manifest": f"{RUNTIME_BOUNDARY_ROOT}/manifest.json",
    "result": f"{RUNTIME_BOUNDARY_ROOT}/result.json",
    "files": f"{RUNTIME_BOUNDARY_ROOT}/files.sha256",
    "seal": f"{RUNTIME_BOUNDARY_ROOT}/bundle-seal.json",
}
COMPARISON_SPEC = "docs/design/sdk-routing-realistic-high-difficulty-comparison-spec.md"
IMPLEMENTATION_SPEC = (
    "docs/design/sdk-routing-realistic-high-difficulty-implementation-candidate-spec.md"
)
RUNTIME_BOUNDARY_SPEC = (
    "docs/design/sdk-routing-realistic-high-difficulty-runtime-boundary-spec.md"
)
B1_REPORT_SCHEMA = "stages/b1-sequential/schemas/v1/run-report.schema.json"
B1_RESULT_SCHEMA = "stages/b1-sequential/schemas/v1/result-envelope.schema.json"
B1_FEEDBACK_TEMPLATE = (
    "A public Controller Check did not satisfy the declared completion criteria. "
    "Review only the bounded public check summary and the original Task; do not "
    "infer hidden Judge requirements. Return the ResultEnvelope schema."
)
PAYLOAD_FILES = (
    "execution-plan.json",
    "phase-e-preflight.json",
    "source-bindings.json",
    "stage-manifest.json",
)
ALL_CANDIDATE_FILES = (*PAYLOAD_FILES, "files.sha256", "candidate-seal.json")


class PhaseERuntimeContract(StrictModel):
    version: Literal[2]
    permission_profile_id: Literal["runtime-boundary-worker"]
    default_permissions_override: Literal["runtime-boundary-worker"]
    thread_sandbox_argument: Literal["omitted"]
    turn_sandbox_argument: Literal["omitted"]
    legacy_sandbox_settings_present: Literal[False]
    approval_mode: Literal["deny_all"]
    approval_policy_wire_value: Literal["never"]
    active_profile_provenance_required: Literal[True]


class PhaseEProfileSpec(StrictModel):
    profile_id: Literal[
        "repository-wide-compatibility-migration",
        "evidence-bound-incident-repair",
    ]
    snapshot_id: Literal[
        "realistic-compat-migration-001",
        "realistic-incident-repair-001",
    ]
    fixture_path: str = Field(min_length=1)
    worker_manifest_path: str = Field(min_length=1)
    judge_path: str = Field(min_length=1)
    qualification_path: str = Field(min_length=1)
    docker_environment_path: str | None = None
    task_pack_qualification_path: str | None = None
    task_budget_path: str | None = None
    task_count: int = Field(ge=1)

    @field_validator(
        "docker_environment_path",
        "task_pack_qualification_path",
        "task_budget_path",
    )
    @classmethod
    def environment_path_is_safe(cls, value: str | None) -> str | None:
        return validate_relative_path(value) if value is not None else None


class PhaseECellSpec(StrictModel):
    ordinal: int = Field(ge=1, le=4)
    profile_id: Literal[
        "repository-wide-compatibility-migration",
        "evidence-bound-incident-repair",
    ]
    variant_id: Literal["ss1", "b1"]


class PhaseEProfileTurnBudget(StrictModel):
    profile_id: Literal[
        "repository-wide-compatibility-migration",
        "evidence-bound-incident-repair",
    ]
    task_count: int = Field(gt=0)
    base_turns_per_variant: int = Field(gt=0)
    total_turn_ceiling_per_variant: int = Field(gt=0)


class PhaseEBudget(StrictModel):
    task_initial_turns: Literal[1]
    task_extra_turn_ceiling: Literal[1]
    variant_extra_turn_ceiling: Literal[2]
    base_turns_per_variant: int = Field(gt=0)
    total_turn_ceiling_per_variant: int = Field(gt=0)
    total_initial_turns: int = Field(gt=0)
    total_turn_ceiling: int = Field(gt=0)
    model_active_seconds_ceiling_per_variant: int = Field(gt=0)
    wall_clock_seconds_ceiling_per_variant: int = Field(gt=0)
    unused_reserve_transfer: Literal["forbidden"]
    profile_budgets: list[PhaseEProfileTurnBudget] | None = None

    @model_validator(mode="after")
    def exact_turn_arithmetic(self) -> "PhaseEBudget":
        if self.profile_budgets is None:
            if (
                self.base_turns_per_variant != 8
                or self.total_turn_ceiling_per_variant != 10
                or self.total_initial_turns != 32
                or self.total_turn_ceiling != 40
            ):
                raise ValueError("legacy Phase E budget differs")
            return self
        if [item.profile_id for item in self.profile_budgets] != [
            "repository-wide-compatibility-migration",
            "evidence-bound-incident-repair",
        ]:
            raise ValueError("Phase E profile budget order differs")
        if [item.task_count for item in self.profile_budgets] != [13, 8]:
            raise ValueError("Phase E profile Task counts differ")
        for item in self.profile_budgets:
            if item.base_turns_per_variant != item.task_count:
                raise ValueError("Phase E profile base turns differ")
            if item.total_turn_ceiling_per_variant != item.task_count + 2:
                raise ValueError("Phase E profile turn ceiling differs")
        if (
            self.base_turns_per_variant != 13
            or self.total_turn_ceiling_per_variant != 15
            or self.total_initial_turns != 42
            or self.total_turn_ceiling != 50
        ):
            raise ValueError("Phase E v3 aggregate budget differs")
        return self


class PhaseEDispatchPolicy(StrictModel):
    one_cell_per_invocation: Literal[True]
    explicit_confirmation_per_cell: Literal[True]
    automatic_continuation: Literal[False]
    retry_after_unsealed_failure: Literal[False]
    stop_after_first_profile_pair: Literal[True]


class PhaseEClaimPolicy(StrictModel):
    route_decision_allowed: Literal[False]
    single_run_generalization_allowed: Literal[False]
    b1_default_adoption_allowed: Literal[False]


class PhaseEStageManifest(StrictModel):
    schema_version: Literal[1, 2, 3]
    status: Literal["frozen_before_model_use"]
    suite_id: Literal["sdk-routing-realistic-high-difficulty-v1"]
    stage_id: Literal["realistic-high-difficulty-initial"]
    track: Literal[PHASE_E_TRACK]
    model: Literal[PINNED_MODEL]
    reasoning_effort: Literal[PINNED_REASONING_EFFORT]
    auth_method: Literal["chatgpt"]
    api_key_environment_names_forbidden: list[
        Literal["CODEX_API_KEY", "OPENAI_API_KEY"]
    ]
    runtime_contract: PhaseERuntimeContract
    profiles: list[PhaseEProfileSpec] = Field(min_length=2, max_length=2)
    cell_order: list[PhaseECellSpec] = Field(min_length=4, max_length=4)
    budget: PhaseEBudget
    dispatch: PhaseEDispatchPolicy
    claims: PhaseEClaimPolicy

    @model_validator(mode="after")
    def exact_stage_contract(self) -> "PhaseEStageManifest":
        if self.api_key_environment_names_forbidden != [
            "CODEX_API_KEY",
            "OPENAI_API_KEY",
        ]:
            raise ValueError("Phase E API-key name list differs")
        if [item.profile_id for item in self.profiles] != [
            "repository-wide-compatibility-migration",
            "evidence-bound-incident-repair",
        ]:
            raise ValueError("Phase E profile order differs")
        profile_r, profile_i = self.profiles
        if self.schema_version == 1:
            if any(item.docker_environment_path is not None for item in self.profiles):
                raise ValueError("Phase E v1 profiles cannot claim Docker environment identity")
            if any(
                item.task_pack_qualification_path is not None
                or item.task_budget_path is not None
                for item in self.profiles
            ):
                raise ValueError("Phase E v1 profiles cannot claim redesign artifacts")
        else:
            expected_environment = str(
                PurePosixPath(profile_r.qualification_path).with_name(
                    "docker-environment.json"
                )
            )
            if profile_r.docker_environment_path != expected_environment:
                raise ValueError(
                    "Phase E v2 Profile R requires its qualification sibling "
                    "docker-environment.json"
                )
            if profile_i.docker_environment_path is not None:
                raise ValueError("Phase E Profile I cannot claim Docker environment identity")
        if self.schema_version in {1, 2}:
            if [item.task_count for item in self.profiles] != [8, 8]:
                raise ValueError("legacy Phase E profile Task counts differ")
            if self.budget.profile_budgets is not None:
                raise ValueError("legacy Phase E cannot claim profile budgets")
            if any(
                item.task_pack_qualification_path is not None
                or item.task_budget_path is not None
                for item in self.profiles
            ):
                raise ValueError("legacy Phase E cannot claim redesign artifacts")
        else:
            if [item.task_count for item in self.profiles] != [13, 8]:
                raise ValueError("Phase E v3 profile Task counts differ")
            if self.budget.profile_budgets is None:
                raise ValueError("Phase E v3 requires profile budgets")
            if (
                profile_r.task_pack_qualification_path is None
                or profile_r.task_budget_path is None
            ):
                raise ValueError("Phase E v3 Profile R redesign artifacts are missing")
            if (
                profile_i.task_pack_qualification_path is not None
                or profile_i.task_budget_path is not None
            ):
                raise ValueError("Phase E v3 Profile I cannot claim Profile R artifacts")
        expected = [
            (1, "repository-wide-compatibility-migration", "ss1"),
            (2, "repository-wide-compatibility-migration", "b1"),
            (3, "evidence-bound-incident-repair", "b1"),
            (4, "evidence-bound-incident-repair", "ss1"),
        ]
        actual = [(item.ordinal, item.profile_id, item.variant_id) for item in self.cell_order]
        if actual != expected:
            raise ValueError("Phase E Cell order differs from the approved order")
        if (
            self.budget.model_active_seconds_ceiling_per_variant
            > self.budget.wall_clock_seconds_ceiling_per_variant
        ):
            raise ValueError("model-active ceiling cannot exceed wall-clock ceiling")
        return self


class PhaseEPreflightEvidence(StrictModel):
    schema_version: Literal[1] = 1
    account_type: Literal["chatgpt"]
    sdk_version: Literal[PINNED_SDK_VERSION]
    model: Literal[PINNED_MODEL]
    reasoning_effort: Literal[PINNED_REASONING_EFFORT]
    model_visible: Literal[True]
    actual_model_turns: Literal[0]
    api_key_environment_names_present: list[str] = Field(max_length=0)
    permission_profile_id: Literal["runtime-boundary-worker"]
    legacy_sandbox_arguments: Literal[False]


class PhaseEProfileBinding(StrictModel):
    profile_id: str
    snapshot_id: str
    fixture_path: str
    fixture_tree_oid: str = Field(pattern=r"^[0-9a-f]{40}$")
    worker_manifest_path: str
    worker_manifest_sha256: Sha256
    judge_path: str
    judge_tree_oid: str = Field(pattern=r"^[0-9a-f]{40}$")
    judge_bundle_manifest_sha256: Sha256
    property_catalog_sha256: Sha256
    prerequisite_dag_sha256: Sha256
    qualification_path: str
    qualification_sha256: Sha256
    qualification_manifest_sha256: Sha256
    qualification_result_sha256: Sha256
    qualification_seal_sha256: Sha256
    task_pack_qualification_path: str | None = None
    task_pack_qualification_sha256: Sha256 | None = None
    task_pack_qualification_seal_sha256: Sha256 | None = None
    task_budget_path: str | None = None
    task_budget_sha256: Sha256 | None = None
    task_budget_seal_sha256: Sha256 | None = None
    docker_environment_path: str | None = None
    docker_environment_sha256: Sha256 | None = None
    task_count: int = Field(ge=1)
    challenge_ready: Literal[True]

    @field_validator(
        "docker_environment_path",
        "task_pack_qualification_path",
        "task_budget_path",
    )
    @classmethod
    def environment_path_is_safe(cls, value: str | None) -> str | None:
        return validate_relative_path(value) if value is not None else None

    @model_validator(mode="after")
    def environment_identity_is_complete(self) -> "PhaseEProfileBinding":
        if (self.docker_environment_path is None) != (
            self.docker_environment_sha256 is None
        ):
            raise ValueError("Phase E Docker environment identity must be path/SHA complete")
        task_pack_values = (
            self.task_pack_qualification_path,
            self.task_pack_qualification_sha256,
            self.task_pack_qualification_seal_sha256,
        )
        if any(value is not None for value in task_pack_values) and not all(
            value is not None for value in task_pack_values
        ):
            raise ValueError("Phase E Task Pack identity must be path/SHA/seal complete")
        task_budget_values = (
            self.task_budget_path,
            self.task_budget_sha256,
            self.task_budget_seal_sha256,
        )
        if any(value is not None for value in task_budget_values) and not all(
            value is not None for value in task_budget_values
        ):
            raise ValueError("Phase E task budget identity must be path/SHA/seal complete")
        return self


class PhaseESourceBindings(StrictModel):
    schema_version: Literal[1, 2, 3] = 1
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    source_tree: str = Field(pattern=r"^[0-9a-f]{40}$")
    stage_manifest_path: Literal[PHASE_E_STAGE_RELATIVE]
    stage_manifest_sha256: Sha256
    comparison_spec_sha256: Sha256
    implementation_spec_sha256: Sha256
    runtime_boundary_spec_sha256: Sha256
    runtime_boundary_manifest_sha256: Sha256
    runtime_boundary_result_sha256: Sha256
    runtime_boundary_files_sha256: Sha256
    runtime_boundary_bundle_sha256: Sha256
    profiles: list[PhaseEProfileBinding] = Field(min_length=2, max_length=2)
    bindings_sha256: Sha256

    @model_validator(mode="after")
    def self_hash_matches(self) -> "PhaseESourceBindings":
        profile_r, profile_i = self.profiles
        if self.schema_version == 1:
            if any(item.docker_environment_path is not None for item in self.profiles):
                raise ValueError("Phase E v1 bindings cannot claim Docker environment identity")
        else:
            expected_environment = str(
                PurePosixPath(profile_r.qualification_path).with_name(
                    "docker-environment.json"
                )
            )
            if (
                profile_r.profile_id != "repository-wide-compatibility-migration"
                or profile_r.docker_environment_path != expected_environment
                or profile_r.docker_environment_sha256 is None
            ):
                raise ValueError("Phase E v2 Profile R Docker environment identity differs")
            if (
                profile_i.profile_id != "evidence-bound-incident-repair"
                or profile_i.docker_environment_path is not None
                or profile_i.docker_environment_sha256 is not None
            ):
                raise ValueError("Phase E v2 Profile I cannot claim Docker environment identity")
        if self.schema_version in {1, 2}:
            if any(
                item.task_pack_qualification_path is not None
                or item.task_budget_path is not None
                for item in self.profiles
            ):
                raise ValueError("legacy Phase E bindings cannot claim redesign artifacts")
        else:
            if (
                profile_r.task_count != 13
                or profile_r.task_pack_qualification_path is None
                or profile_r.task_pack_qualification_sha256 is None
                or profile_r.task_pack_qualification_seal_sha256 is None
                or profile_r.task_budget_path is None
                or profile_r.task_budget_sha256 is None
                or profile_r.task_budget_seal_sha256 is None
            ):
                raise ValueError("Phase E v3 Profile R redesign identity differs")
            if (
                profile_i.task_count != 8
                or profile_i.task_pack_qualification_path is not None
                or profile_i.task_budget_path is not None
            ):
                raise ValueError("Phase E v3 Profile I redesign identity differs")
        payload = self.model_dump(
            mode="json",
            exclude={"bindings_sha256"},
            exclude_none=True,
        )
        if self.bindings_sha256 != canonical_sha256(payload):
            raise ValueError("Phase E source-bindings hash mismatch")
        return self


class PhaseECandidateFile(StrictModel):
    path: str
    size: int = Field(ge=0)
    sha256: Sha256


class PhaseECandidateSeal(StrictModel):
    schema_version: Literal[1, 2, 3] = 1
    kind: Literal[PHASE_E_CANDIDATE_KIND] = PHASE_E_CANDIDATE_KIND
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    experiment_id: str
    plan_fingerprint: Sha256
    planned_cells: Literal[4]
    planned_initial_model_turns: int = Field(gt=0)
    planned_model_turn_ceiling: int = Field(gt=0)
    actual_model_turns: Literal[0]
    docker_environment_path: str | None = None
    docker_environment_sha256: Sha256 | None = None
    payload_files: list[PhaseECandidateFile] = Field(min_length=4, max_length=4)
    files_manifest_sha256: Sha256
    seal_sha256: Sha256

    @field_validator("payload_files")
    @classmethod
    def files_are_exact(cls, values: list[PhaseECandidateFile]) -> list[PhaseECandidateFile]:
        if [item.path for item in values] != list(PAYLOAD_FILES):
            raise ValueError("Phase E candidate payload file set differs")
        return values

    @field_validator("docker_environment_path")
    @classmethod
    def environment_path_is_safe(cls, value: str | None) -> str | None:
        return validate_relative_path(value) if value is not None else None

    @model_validator(mode="after")
    def self_hash_matches(self) -> "PhaseECandidateSeal":
        has_path = self.docker_environment_path is not None
        has_sha = self.docker_environment_sha256 is not None
        if self.schema_version == 1 and (has_path or has_sha):
            raise ValueError("Phase E v1 seal cannot claim Docker environment identity")
        if self.schema_version in {2, 3} and not (has_path and has_sha):
            raise ValueError("Phase E v2+ seal requires Docker environment path/SHA")
        expected_turns = (42, 50) if self.schema_version == 3 else (32, 40)
        if (
            self.planned_initial_model_turns,
            self.planned_model_turn_ceiling,
        ) != expected_turns:
            raise ValueError("Phase E candidate turn totals differ")
        payload = self.model_dump(
            mode="json",
            exclude={"seal_sha256"},
            exclude_none=True,
        )
        if self.seal_sha256 != canonical_sha256(payload):
            raise ValueError("Phase E candidate seal hash mismatch")
        return self


class PhaseECandidateError(RuntimeError):
    """Raised when the zero-turn candidate cannot be frozen or verified."""


def _git(repository: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repository), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise PhaseECandidateError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout


def _git_text(repository: Path, *args: str) -> str:
    return _git(repository, *args).decode("ascii").strip()


def _git_bytes(repository: Path, commit: str, relative: str) -> bytes:
    return _git(repository, "show", f"{commit}:{relative}")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_source_tree_sha256(
    repository: Path,
    commit: str,
    root_relative: str,
    included_paths: tuple[str, ...],
) -> str:
    """Reproduce ``_source_tree_sha256`` from exact committed Git blobs."""

    root_relative = root_relative.strip("/")
    selected: dict[str, bytes] = {}
    for included in included_paths:
        relative = included.strip("/")
        git_path = f"{root_relative}/{relative}"
        raw = _git(
            repository,
            "ls-tree",
            "-r",
            "-z",
            commit,
            "--",
            git_path,
        )
        entries = []
        for record in raw.split(b"\0"):
            if not record:
                continue
            metadata, encoded_path = record.split(b"\t", 1)
            mode, kind, _oid = metadata.decode("ascii").split(" ", 2)
            if kind != "blob":
                raise PhaseECandidateError(
                    f"source fingerprint rejects non-blob entry: {encoded_path!r}"
                )
            entries.append((mode, encoded_path.decode("utf-8")))
        if not entries:
            raise PhaseECandidateError(
                f"source fingerprint input is missing: {git_path}"
            )
        for mode, path in entries:
            relative_to_root = path.removeprefix(f"{root_relative}/")
            parts = Path(relative_to_root).parts
            if "__pycache__" in parts or Path(relative_to_root).suffix in {".pyc", ".pyo"}:
                continue
            if mode == "120000":
                raise PhaseECandidateError(
                    f"source fingerprint rejects symlink: {relative_to_root}"
                )
            selected[relative_to_root] = _git_bytes(repository, commit, path)
    digest = hashlib.sha256()
    for relative in sorted(selected):
        data = selected[relative]
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def _json(data: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PhaseECandidateError(f"{label} is not canonical UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise PhaseECandidateError(f"{label} must be a JSON object")
    return value


def load_phase_e_stage(repository: Path, commit: str = "HEAD") -> PhaseEStageManifest:
    return PhaseEStageManifest.model_validate_json(
        _git_bytes(repository.resolve(), commit, PHASE_E_STAGE_RELATIVE)
    )


def _profile_binding(
    repository: Path,
    commit: str,
    profile: PhaseEProfileSpec,
) -> PhaseEProfileBinding:
    run_payload = yaml.safe_load(
        _git_bytes(repository, commit, f"{profile.fixture_path}/benchmark-run.yaml")
    )
    if not isinstance(run_payload, dict) or not isinstance(run_payload.get("tasks"), list):
        raise PhaseECandidateError(f"{profile.snapshot_id} benchmark-run.yaml is invalid")
    if len(run_payload["tasks"]) != profile.task_count:
        raise PhaseECandidateError(f"{profile.snapshot_id} Task count differs")
    qualification_bytes = _git_bytes(repository, commit, profile.qualification_path)
    qualification = _json(qualification_bytes, profile.qualification_path)
    if (
        qualification.get("status") != "CHALLENGE_READY"
        or qualification.get("challenge_ready") is not True
        or qualification.get("model_turns") != 0
        or qualification.get("snapshot_id") != profile.snapshot_id
    ):
        raise PhaseECandidateError(f"{profile.snapshot_id} qualification is not ready")
    task_pack_qualification_sha256 = None
    task_pack_qualification_seal_sha256 = None
    task_budget_sha256 = None
    task_budget_seal_sha256 = None
    if profile.task_pack_qualification_path is not None:
        task_pack_bytes = _git_bytes(
            repository,
            commit,
            profile.task_pack_qualification_path,
        )
        task_pack = _json(task_pack_bytes, profile.task_pack_qualification_path)
        expected_task_ids = [f"R{ordinal:02d}" for ordinal in range(1, 14)]
        task_pack_without_seal = {
            key: value for key, value in task_pack.items() if key != "seal_sha256"
        }
        if (
            task_pack.get("status") != "TASK_PACK_READY"
            or task_pack.get("model_turns") != 0
            or task_pack.get("snapshot_id") != profile.snapshot_id
            or task_pack.get("task_ids") != expected_task_ids
            or not isinstance(task_pack.get("reference_chain_seal_sha256"), str)
            or not isinstance(task_pack.get("public_negative_matrix_sha256"), str)
            or not isinstance(task_pack.get("seal_sha256"), str)
            or task_pack.get("seal_sha256")
            != canonical_sha256(task_pack_without_seal)
        ):
            raise PhaseECandidateError(
                f"{profile.snapshot_id} Task Pack qualification is not ready"
            )
        task_pack_qualification_sha256 = _sha256(task_pack_bytes)
        task_pack_qualification_seal_sha256 = str(task_pack["seal_sha256"])
    if profile.task_budget_path is not None:
        task_budget_bytes = _git_bytes(
            repository,
            commit,
            profile.task_budget_path,
        )
        task_budget = _json(task_budget_bytes, profile.task_budget_path)
        expected_task_ids = [f"R{ordinal:02d}" for ordinal in range(1, 14)]
        per_task = task_budget.get("per_task_maximum_turns")
        task_budget_without_seal = {
            key: value for key, value in task_budget.items() if key != "seal_sha256"
        }
        if (
            task_budget.get("status") != "PROFILE_R_TASK_BUDGET_SEALED"
            or task_budget.get("model_turns") != 0
            or task_budget.get("snapshot_id") != profile.snapshot_id
            or task_budget.get("task_ids") != expected_task_ids
            or not isinstance(per_task, dict)
            or list(per_task) != expected_task_ids
            or any(value != 2 for value in per_task.values())
            or task_budget.get("base_turns_per_cell") != 13
            or task_budget.get("maximum_actual_model_turns_per_cell") != 15
            or task_budget.get("retry_resume_maximum_turns") != 2
            or task_budget.get("ss1_b1_identical") is not True
            or not isinstance(task_budget.get("seal_sha256"), str)
            or task_budget.get("seal_sha256")
            != canonical_sha256(task_budget_without_seal)
        ):
            raise PhaseECandidateError(
                f"{profile.snapshot_id} Task budget is not sealed"
            )
        task_budget_sha256 = _sha256(task_budget_bytes)
        task_budget_seal_sha256 = str(task_budget["seal_sha256"])
    docker_environment_sha256 = None
    if profile.docker_environment_path is not None:
        docker_environment_bytes = _git_bytes(
            repository,
            commit,
            profile.docker_environment_path,
        )
        docker_environment = _json(
            docker_environment_bytes,
            profile.docker_environment_path,
        )
        environment_qualification = docker_environment.get("qualification")
        environment_image = docker_environment.get("image")
        if (
            type(docker_environment.get("schema_version")) is not int
            or docker_environment.get("schema_version") != 1
            or not isinstance(environment_qualification, dict)
            or not isinstance(environment_image, dict)
            or environment_qualification.get("source_commit")
            != qualification.get("source_commit")
            or environment_qualification.get("batch_id")
            != qualification.get("batch_id")
            or environment_qualification.get("status")
            != qualification.get("status")
            or environment_qualification.get("actual_model_turns")
            != qualification.get("model_turns")
            or environment_image.get("reference")
            != qualification.get("image_reference")
        ):
            raise PhaseECandidateError(
                f"{profile.snapshot_id} Docker environment and qualification differ"
            )
        docker_environment_sha256 = _sha256(docker_environment_bytes)
    judge_bundle = f"{profile.judge_path}/bundle-manifest.json"
    return PhaseEProfileBinding(
        profile_id=profile.profile_id,
        snapshot_id=profile.snapshot_id,
        fixture_path=profile.fixture_path,
        fixture_tree_oid=_git_text(repository, "rev-parse", f"{commit}:{profile.fixture_path}"),
        worker_manifest_path=profile.worker_manifest_path,
        worker_manifest_sha256=_sha256(_git_bytes(repository, commit, profile.worker_manifest_path)),
        judge_path=profile.judge_path,
        judge_tree_oid=_git_text(repository, "rev-parse", f"{commit}:{profile.judge_path}"),
        judge_bundle_manifest_sha256=_sha256(_git_bytes(repository, commit, judge_bundle)),
        property_catalog_sha256=_sha256(
            _git_bytes(repository, commit, f"{profile.judge_path}/property-catalog.json")
        ),
        prerequisite_dag_sha256=_sha256(
            _git_bytes(repository, commit, f"{profile.judge_path}/prerequisite-dag.json")
        ),
        qualification_path=profile.qualification_path,
        qualification_sha256=_sha256(qualification_bytes),
        qualification_manifest_sha256=str(qualification["manifest_sha256"]),
        qualification_result_sha256=str(qualification["result_sha256"]),
        qualification_seal_sha256=str(qualification["seal_sha256"]),
        task_pack_qualification_path=profile.task_pack_qualification_path,
        task_pack_qualification_sha256=task_pack_qualification_sha256,
        task_pack_qualification_seal_sha256=(
            task_pack_qualification_seal_sha256
        ),
        task_budget_path=profile.task_budget_path,
        task_budget_sha256=task_budget_sha256,
        task_budget_seal_sha256=task_budget_seal_sha256,
        docker_environment_path=profile.docker_environment_path,
        docker_environment_sha256=docker_environment_sha256,
        task_count=profile.task_count,
        challenge_ready=True,
    )


def build_source_bindings(
    repository: Path,
    source_commit: str,
    stage: PhaseEStageManifest,
) -> PhaseESourceBindings:
    repository = repository.resolve()
    profiles = [_profile_binding(repository, source_commit, item) for item in stage.profiles]
    values: dict[str, Any] = {
        "schema_version": stage.schema_version,
        "source_commit": source_commit,
        "source_tree": _git_text(repository, "rev-parse", f"{source_commit}^{{tree}}"),
        "stage_manifest_path": PHASE_E_STAGE_RELATIVE,
        "stage_manifest_sha256": _sha256(
            _git_bytes(repository, source_commit, PHASE_E_STAGE_RELATIVE)
        ),
        "comparison_spec_sha256": _sha256(_git_bytes(repository, source_commit, COMPARISON_SPEC)),
        "implementation_spec_sha256": _sha256(
            _git_bytes(repository, source_commit, IMPLEMENTATION_SPEC)
        ),
        "runtime_boundary_spec_sha256": _sha256(
            _git_bytes(repository, source_commit, RUNTIME_BOUNDARY_SPEC)
        ),
        "runtime_boundary_manifest_sha256": _sha256(
            _git_bytes(repository, source_commit, RUNTIME_BOUNDARY_FILES["manifest"])
        ),
        "runtime_boundary_result_sha256": _sha256(
            _git_bytes(repository, source_commit, RUNTIME_BOUNDARY_FILES["result"])
        ),
        "runtime_boundary_files_sha256": _sha256(
            _git_bytes(repository, source_commit, RUNTIME_BOUNDARY_FILES["files"])
        ),
        "runtime_boundary_bundle_sha256": _sha256(
            _git_bytes(repository, source_commit, RUNTIME_BOUNDARY_FILES["seal"])
        ),
        "profiles": [
            item.model_dump(mode="json", exclude_none=True) for item in profiles
        ],
    }
    return PhaseESourceBindings(**values, bindings_sha256=canonical_sha256(values))


def _docker_environment_identity(
    bindings: PhaseESourceBindings,
) -> dict[str, str]:
    """Return the v2 Profile R identity and no fields for historical v1."""

    if bindings.schema_version == 1:
        return {}
    profile_r = bindings.profiles[0]
    if (
        profile_r.docker_environment_path is None
        or profile_r.docker_environment_sha256 is None
    ):
        raise PhaseECandidateError("Phase E v2 Profile R Docker environment is missing")
    return {
        "docker_environment_path": profile_r.docker_environment_path,
        "docker_environment_sha256": profile_r.docker_environment_sha256,
    }


def _profile_r_redesign_identity(
    bindings: PhaseESourceBindings,
) -> dict[str, str]:
    if bindings.schema_version != 3:
        return {}
    profile_r = bindings.profiles[0]
    values = {
        "profile_r_task_pack_qualification_path": (
            profile_r.task_pack_qualification_path
        ),
        "profile_r_task_pack_qualification_sha256": (
            profile_r.task_pack_qualification_sha256
        ),
        "profile_r_task_pack_qualification_seal_sha256": (
            profile_r.task_pack_qualification_seal_sha256
        ),
        "profile_r_task_budget_path": profile_r.task_budget_path,
        "profile_r_task_budget_sha256": profile_r.task_budget_sha256,
        "profile_r_task_budget_seal_sha256": (
            profile_r.task_budget_seal_sha256
        ),
    }
    if any(value is None for value in values.values()):
        raise PhaseECandidateError("Phase E v3 Profile R redesign identity is incomplete")
    return {key: str(value) for key, value in values.items()}


def probe_phase_e_preflight(
    *,
    environ: Mapping[str, str] | None = None,
) -> PhaseEPreflightEvidence:
    present = present_api_key_environment_names(environ)
    if present:
        raise PhaseECandidateError(
            f"API key environment names are present: {', '.join(present)}"
        )
    try:
        import openai_codex
        from openai_codex import Codex
    except ImportError as exc:
        raise PhaseECandidateError("openai-codex is unavailable") from exc
    if str(getattr(openai_codex, "__version__", "")) != PINNED_SDK_VERSION:
        raise PhaseECandidateError("openai-codex version differs")
    with Codex() as client:
        response = client.account(refresh_token=False)
        account = getattr(response, "account", None)
        root = getattr(account, "root", None)
        account_type = getattr(getattr(root, "type", None), "value", getattr(root, "type", None))
        if account_type != "chatgpt":
            raise PhaseECandidateError("Phase E requires an active ChatGPT login")
        model_response = client._client.model_list(include_hidden=True)
        models = getattr(model_response, "data", getattr(model_response, "models", []))
        model_ids = {
            str(getattr(item, "model", getattr(item, "id", ""))) for item in models
        }
    if PINNED_MODEL not in model_ids:
        raise PhaseECandidateError(f"{PINNED_MODEL} is not visible to the active account")
    return PhaseEPreflightEvidence(
        account_type="chatgpt",
        sdk_version=PINNED_SDK_VERSION,
        model=PINNED_MODEL,
        reasoning_effort=PINNED_REASONING_EFFORT,
        model_visible=True,
        actual_model_turns=0,
        api_key_environment_names_present=[],
        permission_profile_id="runtime-boundary-worker",
        legacy_sandbox_arguments=False,
    )


def _combined_hash(values: Mapping[str, str]) -> str:
    return canonical_sha256(dict(sorted(values.items())))


def _supplement(
    repository: Path,
    source_commit: str,
    bindings: PhaseESourceBindings,
) -> RealisticRoutingPlanSupplement:
    base_result = _json(_git_bytes(repository, source_commit, B1_RESULT_SCHEMA), B1_RESULT_SCHEMA)
    module_bytes = _git_bytes(
        repository,
        source_commit,
        "tools/benchmark-runner/src/benchmark_runner/realistic_routing.py",
    )
    profile_catalogs = {
        item.profile_id: item.property_catalog_sha256 for item in bindings.profiles
    }
    profile_dags = {
        item.profile_id: item.prerequisite_dag_sha256 for item in bindings.profiles
    }
    qualifications = {
        item.profile_id: item.qualification_sha256 for item in bindings.profiles
    }
    redesigned = bindings.schema_version == 3
    return RealisticRoutingPlanSupplement(
        schema_version=2 if redesigned else 1,
        suite_id=REALISTIC_SUITE_ID,
        stage_id=REALISTIC_STAGE_ID,
        comparison_spec_sha256=bindings.comparison_spec_sha256,
        implementation_spec_sha256=bindings.implementation_spec_sha256,
        runtime_boundary_spec_sha256=bindings.runtime_boundary_spec_sha256,
        machine_variant_ids=("ss1", "b1"),
        ss1=Ss1PlanContract(
            result_schema_sha256=canonical_sha256(ss1_result_schema(base_result)),
            neutral_review_prompt_sha256=neutral_review_prompt_sha256(),
            review_trigger_position="after_observer_before_next_dispatch",
            task_initial_turns=1,
            task_extra_turn_ceiling=1,
            variant_extra_turn_ceiling=2,
        ),
        b1=B1PlanContract(
            public_report_schema_sha256=_sha256(
                _git_bytes(repository, source_commit, B1_REPORT_SCHEMA)
            ),
            observer_hook_schema_sha256=canonical_sha256(
                PassiveBoundaryRecord.model_json_schema()
            ),
            feedback_template_sha256=_sha256(B1_FEEDBACK_TEMPLATE.encode("utf-8")),
            feedback_stdout_stderr_byte_cap=65_536,
            selection="resume_if_same_thread_safe_else_retry",
            task_initial_turns=1,
            task_extra_turn_ceiling=1,
            variant_extra_turn_ceiling=2,
        ),
        common_budget=CommonBudgetContract(
            task_count=13 if redesigned else 8,
            base_turns_per_variant=13 if redesigned else 8,
            total_turn_ceiling_per_variant=15 if redesigned else 10,
            model_active_seconds_ceiling_per_variant=7200,
            wall_clock_seconds_ceiling_per_variant=9000,
            wall_clock_scope="from_adapter_run_entry_through_adapter_terminal",
            unused_reserve_transfer="forbidden",
        ),
        profile_budgets=(
            [
                ProfileBudgetContract(
                    profile_id="repository-wide-compatibility-migration",
                    task_count=13,
                    base_turns_per_variant=13,
                    total_turn_ceiling_per_variant=15,
                ),
                ProfileBudgetContract(
                    profile_id="evidence-bound-incident-repair",
                    task_count=8,
                    base_turns_per_variant=8,
                    total_turn_ceiling_per_variant=10,
                ),
            ]
            if redesigned
            else None
        ),
        observer_schema_sha256=canonical_sha256(
            PassiveBoundaryObservation.model_json_schema()
        ),
        observer_implementation_sha256=_sha256(module_bytes),
        runtime_boundary_manifest_sha256=bindings.runtime_boundary_manifest_sha256,
        runtime_boundary_result_sha256=bindings.runtime_boundary_result_sha256,
        runtime_boundary_bundle_sha256=bindings.runtime_boundary_bundle_sha256,
        challenge_eligibility_manifest_sha256=_combined_hash(qualifications),
        property_catalog_sha256=_combined_hash(profile_catalogs),
        property_prerequisite_dag_sha256=_combined_hash(profile_dags),
        property_evaluation_schema_sha256=canonical_sha256(
            PropertyEvaluationEnvelope.model_json_schema()
        ),
        triage_policy_sha256=_sha256(module_bytes),
        rater_contract_sha256_or_not_applicable="not_applicable",
    )


def build_phase_e_plan(
    repository: Path,
    *,
    source_commit: str,
    created_at: datetime | None = None,
    revision: int = 1,
) -> tuple[ExecutionPlan, PhaseESourceBindings]:
    repository = repository.resolve()
    stage = load_phase_e_stage(repository, source_commit)
    bindings = build_source_bindings(repository, source_commit, stage)
    fixture_by_profile = {
        item.profile_id: FixtureIdentity(
            fixture_id=item.snapshot_id,
            source_commit=source_commit,
            git_tree=item.fixture_tree_oid,
        )
        for item in bindings.profiles
    }
    cells = [
        PlannedCell(
            cell_id=f"cell_phase-e_{item.ordinal}_{fixture_by_profile[item.profile_id].fixture_id}_{item.variant_id}",
            block_id=f"block_phase-e_{fixture_by_profile[item.profile_id].fixture_id}",
            fixture_id=fixture_by_profile[item.profile_id].fixture_id,
            repetition=1,
            variant_id=item.variant_id,
            execution_ordinal=item.ordinal,
        )
        for item in stage.cell_order
    ]
    variants = [
        ArtifactIdentity(
            artifact_id="ss1",
            version=f"phase-e@{source_commit}",
            sha256=_git_source_tree_sha256(
                repository,
                source_commit,
                "tools/benchmark-runner",
                (
                    "src/benchmark_runner/sdk_baselines.py",
                    "src/benchmark_runner/sdk_common.py",
                    "src/benchmark_runner/realistic_routing.py",
                    "src/benchmark_runner/sdk_cells.py",
                ),
            ),
        ),
        ArtifactIdentity(
            artifact_id="b1",
            version=f"phase-e@{source_commit}",
            sha256=_combined_hash(
                {
                    "b1": _git_source_tree_sha256(
                        repository,
                        source_commit,
                        "stages/b1-sequential",
                        ("pyproject.toml", "src", "schemas"),
                    ),
                    "runner_adapter": _git_source_tree_sha256(
                        repository,
                        source_commit,
                        "tools/benchmark-runner",
                        (
                            "src/benchmark_runner/adapter.py",
                            "src/benchmark_runner/realistic_routing.py",
                            "src/benchmark_runner/sdk_cells.py",
                        ),
                    ),
                }
            ),
        ),
    ]
    environment_fingerprint = {
        "source_commit": source_commit,
        "source_tree": bindings.source_tree,
        "source_bindings_sha256": bindings.bindings_sha256,
        "model": stage.model,
        "reasoning_effort": stage.reasoning_effort,
        "auth_method": stage.auth_method,
        "runtime_contract_version": str(stage.runtime_contract.version),
        "permission_profile_id": stage.runtime_contract.permission_profile_id,
        "legacy_sandbox_arguments": "false",
        **_docker_environment_identity(bindings),
        **_profile_r_redesign_identity(bindings),
    }
    base = build_sdk_controlled_plan(
        source_manifest_path=PHASE_E_STAGE_RELATIVE,
        source_manifest_sha256=bindings.stage_manifest_sha256,
        fixtures=list(fixture_by_profile.values()),
        runner=ArtifactIdentity(
            artifact_id="benchmark-runner",
            version=f"phase-e@{source_commit}",
            sha256=_git_source_tree_sha256(
                repository,
                source_commit,
                "tools/benchmark-runner",
                RUNNER_FINGERPRINT_INPUTS,
            ),
        ),
        variants=variants,
        cells=cells,
        baseline_variant="ss1",
        candidate_variants=["b1"],
        decision_policy={
            "stage_id": REALISTIC_STAGE_ID,
            "model": stage.model,
            "reasoning_effort": stage.reasoning_effort,
            "planned_initial_model_turns": stage.budget.total_initial_turns,
            "planned_model_turn_ceiling": stage.budget.total_turn_ceiling,
            "one_cell_per_invocation": True,
            "explicit_confirmation_per_cell": True,
            "stop_after_first_profile_pair": True,
            "route_decision_allowed": False,
            "phase_f_model_usage_approved": False,
        },
        environment_fingerprint=environment_fingerprint,
        created_at=created_at or utc_now(),
        revision=revision,
        seed=0,
        track=PHASE_E_TRACK,
        planned_actual_model_turns=None,
    )
    supplement = _supplement(repository, source_commit, bindings)
    with_supplement = base.model_copy(
        update={
            "reasoning_control": f"{stage.reasoning_effort}_explicit_each_turn",
            "plan_supplemented": [
                *base.plan_supplemented,
                PlanSupplement(
                    field=REALISTIC_SUPPLEMENT_FIELD,
                    value=supplement.model_dump(mode="json", exclude_none=True),
                    source=PHASE_E_STAGE_RELATIVE,
                ),
            ],
        }
    )
    fingerprint = recompute_plan_fingerprint(with_supplement)
    plan = with_supplement.model_copy(
        update={
            "plan_fingerprint": fingerprint,
            "experiment_id": (
                f"exp_{with_supplement.created_at:%Y%m%d}_{fingerprint[:8]}_{revision}"
            ),
        }
    )
    assert_plan_integrity(plan)
    parse_realistic_plan_supplement(
        plan.plan_supplemented,
        expected_source=PHASE_E_STAGE_RELATIVE,
    )
    return plan, bindings


def _file_record(root: Path, relative: str) -> PhaseECandidateFile:
    path = root / relative
    return PhaseECandidateFile(path=relative, size=path.stat().st_size, sha256=sha256_file(path))


def _files_manifest_bytes(records: list[PhaseECandidateFile]) -> bytes:
    return "".join(f"{item.sha256}  {item.path}\n" for item in records).encode("utf-8")


def create_phase_e_candidate(
    repository: Path,
    output_root: Path,
    *,
    source_commit: str | None = None,
    preflight: PhaseEPreflightEvidence | None = None,
    created_at: datetime | None = None,
) -> PhaseECandidateSeal:
    repository = repository.resolve()
    if present_api_key_environment_names():
        raise PhaseECandidateError("API key environment names are present")
    if _git_text(repository, "status", "--porcelain=v1"):
        raise PhaseECandidateError("Phase E candidate requires a clean source commit")
    source_commit = source_commit or _git_text(repository, "rev-parse", "HEAD")
    if source_commit != _git_text(repository, "rev-parse", "HEAD"):
        raise PhaseECandidateError("Phase E candidate source must be current HEAD")
    preflight = preflight or probe_phase_e_preflight()
    if preflight.actual_model_turns != 0:
        raise PhaseECandidateError("Phase E preflight consumed a model turn")
    plan, bindings = build_phase_e_plan(
        repository,
        source_commit=source_commit,
        created_at=created_at,
    )
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=False)
    atomic_write(output_root / "execution-plan.json", canonical_json_bytes(plan))
    atomic_write(output_root / "phase-e-preflight.json", canonical_json_bytes(preflight))
    atomic_write(
        output_root / "source-bindings.json",
        canonical_json_bytes(bindings.model_dump(mode="json", exclude_none=True)),
    )
    atomic_write(
        output_root / "stage-manifest.json",
        _git_bytes(repository, source_commit, PHASE_E_STAGE_RELATIVE),
    )
    records = [_file_record(output_root, relative) for relative in PAYLOAD_FILES]
    files_bytes = _files_manifest_bytes(records)
    atomic_write(output_root / "files.sha256", files_bytes)
    values = {
        "schema_version": bindings.schema_version,
        "kind": PHASE_E_CANDIDATE_KIND,
        "source_commit": source_commit,
        "experiment_id": plan.experiment_id,
        "plan_fingerprint": plan.plan_fingerprint,
        "planned_cells": 4,
        "planned_initial_model_turns": int(
            plan.decision_policy["planned_initial_model_turns"]
        ),
        "planned_model_turn_ceiling": int(
            plan.decision_policy["planned_model_turn_ceiling"]
        ),
        "actual_model_turns": 0,
        **_docker_environment_identity(bindings),
        "payload_files": [item.model_dump(mode="json") for item in records],
        "files_manifest_sha256": _sha256(files_bytes),
    }
    seal = PhaseECandidateSeal(**values, seal_sha256=canonical_sha256(values))
    atomic_write(
        output_root / "candidate-seal.json",
        canonical_json_bytes(seal.model_dump(mode="json", exclude_none=True)),
    )
    verify_phase_e_candidate(repository, output_root)
    return seal


def verify_phase_e_candidate(repository: Path, candidate_root: Path) -> PhaseECandidateSeal:
    repository = repository.resolve()
    candidate_root = candidate_root.resolve()
    actual_names = tuple(sorted(path.name for path in candidate_root.iterdir() if path.is_file()))
    if actual_names != tuple(sorted(ALL_CANDIDATE_FILES)):
        raise PhaseECandidateError("Phase E candidate file set differs")
    seal = PhaseECandidateSeal.model_validate_json(
        (candidate_root / "candidate-seal.json").read_bytes()
    )
    records = [_file_record(candidate_root, relative) for relative in PAYLOAD_FILES]
    if records != seal.payload_files:
        raise PhaseECandidateError("Phase E candidate payload bytes changed")
    files_bytes = _files_manifest_bytes(records)
    if (candidate_root / "files.sha256").read_bytes() != files_bytes:
        raise PhaseECandidateError("Phase E files manifest differs")
    if _sha256(files_bytes) != seal.files_manifest_sha256:
        raise PhaseECandidateError("Phase E files manifest hash differs")
    plan = ExecutionPlan.model_validate_json((candidate_root / "execution-plan.json").read_bytes())
    preflight = PhaseEPreflightEvidence.model_validate_json(
        (candidate_root / "phase-e-preflight.json").read_bytes()
    )
    bindings = PhaseESourceBindings.model_validate_json(
        (candidate_root / "source-bindings.json").read_bytes()
    )
    stage = PhaseEStageManifest.model_validate_json(
        (candidate_root / "stage-manifest.json").read_bytes()
    )
    assert_plan_integrity(plan)
    if not (
        stage.schema_version == bindings.schema_version == seal.schema_version
    ):
        raise PhaseECandidateError("Phase E candidate schema versions differ")
    binding_environment = _docker_environment_identity(bindings)
    environment_fields = (
        "docker_environment_path",
        "docker_environment_sha256",
    )
    plan_environment = {
        key: plan.environment_fingerprint[key]
        for key in environment_fields
        if key in plan.environment_fingerprint
    }
    seal_environment = {
        key: value
        for key, value in {
            "docker_environment_path": seal.docker_environment_path,
            "docker_environment_sha256": seal.docker_environment_sha256,
        }.items()
        if value is not None
    }
    if (
        plan_environment != binding_environment
        or seal_environment != binding_environment
    ):
        raise PhaseECandidateError(
            "Phase E Docker environment identity differs across binding, Plan, and seal"
        )
    if binding_environment:
        source_environment_sha256 = _sha256(
            _git_bytes(
                repository,
                seal.source_commit,
                binding_environment["docker_environment_path"],
            )
        )
        if (
            source_environment_sha256
            != binding_environment["docker_environment_sha256"]
        ):
            raise PhaseECandidateError(
                "Phase E Docker environment SHA differs from source commit Git bytes"
            )
    if (
        plan.experiment_id != seal.experiment_id
        or plan.plan_fingerprint != seal.plan_fingerprint
        or bindings.source_commit != seal.source_commit
        or preflight.actual_model_turns != 0
    ):
        raise PhaseECandidateError("Phase E candidate identities differ")
    expected_plan, expected_bindings = build_phase_e_plan(
        repository,
        source_commit=seal.source_commit,
        created_at=plan.created_at,
        revision=plan.revision,
    )
    if plan != expected_plan or bindings != expected_bindings:
        raise PhaseECandidateError("Phase E candidate is not reproducible from its source commit")
    source_stage = _git_bytes(repository, seal.source_commit, PHASE_E_STAGE_RELATIVE)
    if (candidate_root / "stage-manifest.json").read_bytes() != source_stage:
        raise PhaseECandidateError("Phase E copied stage manifest differs")
    if stage.model != preflight.model or stage.reasoning_effort != preflight.reasoning_effort:
        raise PhaseECandidateError("Phase E preflight and stage controls differ")
    if present_api_key_environment_names():
        raise PhaseECandidateError("API key environment names are present during verification")
    return seal
