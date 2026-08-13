"""Manifest-driven, model-free vertical slice for SDK routing suite v1."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Callable
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Annotated, Any, Literal, TypeAlias

import yaml
from pydantic import Field, TypeAdapter, field_validator, model_validator

from benchmark_runner.adapter import VariantAdapter
from benchmark_runner.contract import (
    ArtifactIdentity,
    CellLifecycleState,
    CellStateRecord,
    ExecutionPlan,
    FixtureIdentity,
    Measurement,
    MeasurementIdentity,
    PlannedCell,
    StrictModel,
    validate_relative_path,
)
from benchmark_runner.plan import assert_plan_integrity, build_sdk_controlled_plan
from benchmark_runner.sdk_cells import (
    SdkSealedCellResult,
    initialize_sdk_experiment,
    run_sdk_nonlive_cell,
)
from benchmark_runner.runner import (
    _r5_assert_export_safe,
    atomic_write,
    canonical_json_bytes,
    verify_sealed_cell,
)
from benchmark_runner.workspace import (
    BenchmarkRun,
    FixtureRestorer,
    FrozenFixtureSpec,
    PreparedFixture,
    load_frozen_manifest,
    sha256_file,
)


class RoutingSuiteError(RuntimeError):
    pass


S1_EXPECTED_CELL_ORDER = [
    ("code-change", "c2"),
    ("code-change", "b1"),
    ("document-read", "b1"),
    ("document-read", "c2"),
    ("sequential-code-change", "b1"),
    ("sequential-code-change", "c2"),
    ("sequential-document", "c2"),
    ("sequential-document", "b1"),
]
S1_ALLOWED_OUTCOMES = [
    "CALIBRATION_PASS",
    "CALIBRATION_STOP",
    "CALIBRATION_INCONCLUSIVE",
]
S1_PLANNED_LIVE_MODEL_TURNS = 12
S2_EXPECTED_CELL_ORDER = [
    ("cell_s2_a_1_c2", "three-stage-config-migration", "c2"),
    ("cell_s2_a_1_b1", "three-stage-config-migration", "b1"),
    ("cell_s2_b_1_b1", "three-stage-incident-analysis", "b1"),
    ("cell_s2_b_1_c2", "three-stage-incident-analysis", "c2"),
]
S2_ALLOWED_OUTCOMES = [
    "S2_OBSERVATION_READY",
    "S2_POLICY_READY",
    "S2_EXPANSION_REQUIRED",
    "S2_INCONCLUSIVE",
    "S2_STOP",
    "S2_INCOMPLETE",
]
S2_BASE_LIVE_MODEL_TURNS = 12
S2_RETRY_RESUME_RESERVE_TURNS = 3
S2_MAX_ACTUAL_LIVE_MODEL_TURNS = 15
S3_EXPECTED_CELL_ORDER = [
    ("cell_s3_a_1_c2", "four-stage-compatibility-refactor", "c2"),
    ("cell_s3_a_1_b1", "four-stage-compatibility-refactor", "b1"),
    ("cell_s3_b_1_b1", "four-stage-conflicting-incident-report", "b1"),
    ("cell_s3_b_1_c2", "four-stage-conflicting-incident-report", "c2"),
]
S3_ALLOWED_OUTCOMES = [
    "S3_OBSERVATION_READY",
    "S3_POLICY_READY",
    "S3_REPLICATION_REQUIRED",
    "S3_INCONCLUSIVE",
    "S3_STOP",
    "S3_INCOMPLETE",
]
S3_BASE_LIVE_MODEL_TURNS = 16
S3_RETRY_RESUME_RESERVE_TURNS_PER_PROFILE = 2
S3_RETRY_RESUME_RESERVE_TURNS = 4
S3_MAX_ACTUAL_LIVE_MODEL_TURNS = 20
RoutingStageId: TypeAlias = Literal[
    "s1-baseline",
    "s2-intermediate",
    "s3-complex-high-risk",
]


class ExpectedWriteFiles(StrictModel):
    minimum: int = Field(ge=0)
    maximum: int = Field(ge=0)

    @model_validator(mode="after")
    def range_is_ordered(self) -> ExpectedWriteFiles:
        if self.maximum < self.minimum:
            raise ValueError("expected write file maximum must be >= minimum")
        return self


class FixtureComplexity(StrictModel):
    task_count: int = Field(ge=1)
    dependency_depth: int = Field(ge=1)
    dependency_edges: int = Field(ge=0)
    max_fan_in: int = Field(ge=0)
    worker_read_files: int = Field(ge=0)
    worker_read_bytes: int = Field(ge=0)
    expected_write_files: ExpectedWriteFiles
    write_modules: int = Field(ge=1)
    check_count: int = Field(ge=0)
    handoff_kind: Literal[
        "none",
        "filesystem_implicit",
        "declared_single",
        "declared_multiple",
    ]
    scope_overlap: Literal["not_applicable", "disjoint", "partial", "shared"]
    verification_kind: Literal[
        "public_to_worker",
        "post_hoc_property",
        "judge_only_verified",
        "judge_only_unverified",
        "partial",
        "human",
    ]
    failure_profile: Literal[
        "normal",
        "omission_risk",
        "compatibility_risk",
        "injected",
    ]
    solution_ambiguity: Literal["low", "medium", "high"]


class FixtureProfileDeclaration(StrictModel):
    fixture_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    complexity: FixtureComplexity


class FixtureManifestSelection(StrictModel):
    path: str
    fixture_ids: list[str] = Field(min_length=1)

    _path_is_relative = field_validator("path")(validate_relative_path)

    @model_validator(mode="after")
    def fixture_ids_are_unique(self) -> FixtureManifestSelection:
        if len(self.fixture_ids) != len(set(self.fixture_ids)):
            raise ValueError("fixture manifest selection IDs must be unique")
        return self


class RoutingS1CellDeclaration(StrictModel):
    fixture_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    variant_id: Literal["c2", "b1"]
    repetition: Literal[1] = 1


class RoutingS2CellDeclaration(StrictModel):
    cell_id: str = Field(pattern=r"^cell_s2_[ab]_[12]_(?:c2|b1)$")
    profile_alias: Literal["a", "b"]
    fixture_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    variant_id: Literal["c2", "b1"]
    repetition: Literal[1, 2] = 1


class RoutingS3CellDeclaration(StrictModel):
    cell_id: str = Field(pattern=r"^cell_s3_[ab]_[12]_(?:c2|b1)$")
    profile_alias: Literal["a", "b"]
    fixture_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    variant_id: Literal["c2", "b1"]
    repetition: Literal[1, 2] = 1


class RoutingS1StageManifest(StrictModel):
    schema_version: Literal[1]
    stage_id: Literal["s1-baseline"]
    status: Literal["implementation_candidate", "frozen_before_execution"]
    purpose: Literal["calibration_only"]
    fixture_manifests: list[FixtureManifestSelection] = Field(min_length=1)
    variants: list[Literal["c2", "b1"]] = Field(min_length=2, max_length=2)
    baseline_variant: Literal["c2"]
    candidate_variants: list[Literal["b1"]] = Field(min_length=1, max_length=1)
    profiles: list[FixtureProfileDeclaration] = Field(min_length=1)
    cells: list[RoutingS1CellDeclaration] = Field(min_length=1)
    planned_live_model_turns: int = Field(ge=1)
    allowed_outcomes: list[
        Literal[
            "CALIBRATION_PASS",
            "CALIBRATION_STOP",
            "CALIBRATION_INCONCLUSIVE",
        ]
    ] = Field(min_length=3, max_length=3)

    route_decision_allowed: Literal[False] = False

    @model_validator(mode="after")
    def stage_contract_is_consistent(self) -> RoutingS1StageManifest:
        if self.variants != ["c2", "b1"]:
            raise ValueError("S1 variants must be exactly [c2, b1]")
        if self.candidate_variants != ["b1"]:
            raise ValueError("S1 candidate variant must be exactly b1")
        fixture_ids = [profile.fixture_id for profile in self.profiles]
        if len(fixture_ids) != len(set(fixture_ids)):
            raise ValueError("S1 profile fixture IDs must be unique")
        selected = [
            fixture_id
            for manifest in self.fixture_manifests
            for fixture_id in manifest.fixture_ids
        ]
        if len(selected) != len(set(selected)):
            raise ValueError("S1 selected fixture IDs must be unique")
        if set(fixture_ids) != set(selected):
            raise ValueError("S1 profiles must match selected fixture IDs")
        cell_pairs = [(cell.fixture_id, cell.variant_id) for cell in self.cells]
        expected_pairs = {
            (fixture_id, variant)
            for fixture_id in selected
            for variant in self.variants
        }
        if len(cell_pairs) != len(set(cell_pairs)) or set(cell_pairs) != expected_pairs:
            raise ValueError("S1 must declare one C2 and one B1 Cell per fixture")
        if len(self.allowed_outcomes) != len(set(self.allowed_outcomes)):
            raise ValueError("S1 allowed outcomes must be unique")
        if cell_pairs != S1_EXPECTED_CELL_ORDER:
            raise ValueError("S1 Cell order differs from the frozen design")
        if self.planned_live_model_turns != S1_PLANNED_LIVE_MODEL_TURNS:
            raise ValueError("S1 planned live model turns must be exactly 12")
        if self.allowed_outcomes != S1_ALLOWED_OUTCOMES:
            raise ValueError("S1 allowed outcomes differ from the frozen design")
        task_counts = {profile.fixture_id: profile.complexity.task_count for profile in self.profiles}
        if sum(task_counts[cell.fixture_id] for cell in self.cells) != self.planned_live_model_turns:
            raise ValueError("S1 live turn budget differs from the fixture Task counts")
        return self


class RoutingS2StageManifest(StrictModel):
    schema_version: Literal[1]
    stage_id: Literal["s2-intermediate"]
    status: Literal["implementation_candidate", "frozen_before_execution"]
    purpose: Literal["profile_routing"]
    fixture_manifests: list[FixtureManifestSelection] = Field(min_length=1)
    variants: list[Literal["c2", "b1"]] = Field(min_length=2, max_length=2)
    baseline_variant: Literal["c2"]
    candidate_variants: list[Literal["b1"]] = Field(min_length=1, max_length=1)
    profile_aliases: dict[Literal["a", "b"], str]
    profiles: list[FixtureProfileDeclaration] = Field(min_length=2, max_length=2)
    cells: list[RoutingS2CellDeclaration] = Field(min_length=4, max_length=4)
    base_live_model_turns: Literal[12]
    b1_retry_resume_reserve_turns: Literal[3]
    max_actual_live_model_turns: Literal[15]
    route_decision_allowed: Literal[True]
    allowed_outcomes: list[
        Literal[
            "S2_OBSERVATION_READY",
            "S2_POLICY_READY",
            "S2_EXPANSION_REQUIRED",
            "S2_INCONCLUSIVE",
            "S2_STOP",
            "S2_INCOMPLETE",
        ]
    ] = Field(min_length=6, max_length=6)

    @model_validator(mode="after")
    def stage_contract_is_consistent(self) -> RoutingS2StageManifest:
        if self.variants != ["c2", "b1"] or self.candidate_variants != ["b1"]:
            raise ValueError("S2 variants must be exactly [c2, b1]")
        expected_aliases = {
            "a": "three-stage-config-migration",
            "b": "three-stage-incident-analysis",
        }
        if self.profile_aliases != expected_aliases:
            raise ValueError("S2 profile aliases differ from the frozen design")
        fixture_ids = [profile.fixture_id for profile in self.profiles]
        if len(fixture_ids) != len(set(fixture_ids)) or set(fixture_ids) != set(
            expected_aliases.values()
        ):
            raise ValueError("S2 profiles differ from the frozen design")
        selected = [
            fixture_id
            for manifest in self.fixture_manifests
            for fixture_id in manifest.fixture_ids
        ]
        if len(selected) != len(set(selected)) or set(selected) != set(fixture_ids):
            raise ValueError("S2 selected fixture IDs must match profiles")
        declared_order = [
            (cell.cell_id, cell.fixture_id, cell.variant_id) for cell in self.cells
        ]
        if declared_order != S2_EXPECTED_CELL_ORDER:
            raise ValueError("S2 Cell order differs from the frozen design")
        for cell in self.cells:
            if expected_aliases[cell.profile_alias] != cell.fixture_id:
                raise ValueError("S2 Cell alias differs from its fixture")
        if self.allowed_outcomes != S2_ALLOWED_OUTCOMES:
            raise ValueError("S2 allowed outcomes differ from the frozen design")
        task_counts = {
            profile.fixture_id: profile.complexity.task_count for profile in self.profiles
        }
        if any(count != 3 for count in task_counts.values()):
            raise ValueError("S2 profiles must each declare exactly three Tasks")
        if sum(task_counts[cell.fixture_id] for cell in self.cells) != self.base_live_model_turns:
            raise ValueError("S2 base turn budget differs from the fixture Task counts")
        if (
            self.base_live_model_turns + self.b1_retry_resume_reserve_turns
            != self.max_actual_live_model_turns
        ):
            raise ValueError("S2 maximum turn budget differs from base plus reserve")
        return self


class RoutingS3StageManifest(StrictModel):
    schema_version: Literal[1]
    stage_id: Literal["s3-complex-high-risk"]
    status: Literal["implementation_candidate", "frozen_before_execution"]
    purpose: Literal["complex_high_risk_routing"]
    fixture_manifests: list[FixtureManifestSelection] = Field(min_length=1)
    variants: list[Literal["c2", "b1"]] = Field(min_length=2, max_length=2)
    baseline_variant: Literal["c2"]
    candidate_variants: list[Literal["b1"]] = Field(min_length=1, max_length=1)
    profile_aliases: dict[Literal["a", "b"], str]
    profiles: list[FixtureProfileDeclaration] = Field(min_length=2, max_length=2)
    cells: list[RoutingS3CellDeclaration] = Field(min_length=4, max_length=4)
    base_live_model_turns: Literal[16]
    b1_retry_resume_reserve_turns_per_profile: Literal[2]
    b1_retry_resume_reserve_turns: Literal[4]
    max_actual_live_model_turns: Literal[20]
    route_decision_allowed: Literal[True]
    allowed_outcomes: list[
        Literal[
            "S3_OBSERVATION_READY",
            "S3_POLICY_READY",
            "S3_REPLICATION_REQUIRED",
            "S3_INCONCLUSIVE",
            "S3_STOP",
            "S3_INCOMPLETE",
        ]
    ] = Field(min_length=6, max_length=6)

    @model_validator(mode="after")
    def stage_contract_is_consistent(self) -> RoutingS3StageManifest:
        if self.variants != ["c2", "b1"] or self.candidate_variants != ["b1"]:
            raise ValueError("S3 variants must be exactly [c2, b1]")
        expected_aliases = {
            "a": "four-stage-compatibility-refactor",
            "b": "four-stage-conflicting-incident-report",
        }
        if self.profile_aliases != expected_aliases:
            raise ValueError("S3 profile aliases differ from the frozen design")
        fixture_ids = [profile.fixture_id for profile in self.profiles]
        if len(fixture_ids) != len(set(fixture_ids)) or set(fixture_ids) != set(
            expected_aliases.values()
        ):
            raise ValueError("S3 profiles differ from the frozen design")
        selected = [
            fixture_id
            for manifest in self.fixture_manifests
            for fixture_id in manifest.fixture_ids
        ]
        if len(selected) != len(set(selected)) or set(selected) != set(fixture_ids):
            raise ValueError("S3 selected fixture IDs must match profiles")
        declared_order = [
            (cell.cell_id, cell.fixture_id, cell.variant_id) for cell in self.cells
        ]
        if declared_order != S3_EXPECTED_CELL_ORDER:
            raise ValueError("S3 Cell order differs from the frozen design")
        for cell in self.cells:
            if expected_aliases[cell.profile_alias] != cell.fixture_id:
                raise ValueError("S3 Cell alias differs from its fixture")
        if self.allowed_outcomes != S3_ALLOWED_OUTCOMES:
            raise ValueError("S3 allowed outcomes differ from the frozen design")
        task_counts = {
            profile.fixture_id: profile.complexity.task_count for profile in self.profiles
        }
        if any(count != 4 for count in task_counts.values()):
            raise ValueError("S3 profiles must each declare exactly four Tasks")
        if sum(task_counts[cell.fixture_id] for cell in self.cells) != self.base_live_model_turns:
            raise ValueError("S3 base turn budget differs from the fixture Task counts")
        if (
            self.b1_retry_resume_reserve_turns_per_profile * 2
            != self.b1_retry_resume_reserve_turns
            or self.base_live_model_turns + self.b1_retry_resume_reserve_turns
            != self.max_actual_live_model_turns
        ):
            raise ValueError("S3 maximum turn budget differs from base plus reserve")
        return self


RoutingStage: TypeAlias = Annotated[
    RoutingS1StageManifest | RoutingS2StageManifest | RoutingS3StageManifest,
    Field(discriminator="stage_id"),
]
_ROUTING_STAGE_ADAPTER = TypeAdapter(RoutingStage)


class RoutingStageManifest:
    """Compatibility facade for the discriminated S1/S2/S3 stage union."""

    @classmethod
    def model_validate(cls, value: object) -> RoutingStage:
        return _ROUTING_STAGE_ADAPTER.validate_python(value)

    @classmethod
    def model_json_schema(cls) -> dict[str, Any]:
        return _ROUTING_STAGE_ADAPTER.json_schema()


class RoutingStageReference(StrictModel):
    stage_id: RoutingStageId
    path: str

    _path_is_relative = field_validator("path")(validate_relative_path)


class RoutingSuiteManifest(StrictModel):
    schema_version: Literal[1]
    suite_id: Literal["sdk-routing-v1"]
    design_revision: Literal[2, 3, 4]
    status: Literal["implementation_candidate", "frozen_before_execution"]
    stages: list[RoutingStageReference] = Field(min_length=1)
    live_turn_ceiling_including_pilot: Literal[31, 34, 43, 52, 72]
    auth_method: Literal["chatgpt"]
    api_key_policy: Literal["forbidden"]

    @model_validator(mode="after")
    def stage_ids_are_unique(self) -> RoutingSuiteManifest:
        stage_ids = [stage.stage_id for stage in self.stages]
        if len(stage_ids) != len(set(stage_ids)):
            raise ValueError("routing suite stage IDs must be unique")
        if self.design_revision == 2:
            if stage_ids != ["s1-baseline"] or self.live_turn_ceiling_including_pilot != 31:
                raise ValueError("routing suite revision 2 must preserve the S1-only contract")
        elif self.design_revision == 3:
            if stage_ids != ["s1-baseline", "s2-intermediate"]:
                raise ValueError("routing suite revision 3 must declare S1 then S2")
        elif (
            stage_ids != ["s1-baseline", "s2-intermediate", "s3-complex-high-risk"]
            or self.live_turn_ceiling_including_pilot != 72
        ):
            raise ValueError("routing suite revision 4 must declare S1, S2, then S3")
        return self


ROUTING_SCHEMAS = {
    "complexity.schema.json": FixtureComplexity,
    "stage.schema.json": RoutingStageManifest,
    "suite.schema.json": RoutingSuiteManifest,
}


def export_routing_schemas(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, model in ROUTING_SCHEMAS.items():
        data = json.dumps(
            model.model_json_schema(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n"
        (output_dir / filename).write_text(data, encoding="utf-8", newline="\n")


def _load_yaml(path: Path) -> object:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise RoutingSuiteError(f"cannot load routing YAML: {path}") from exc


def load_routing_suite(path: Path) -> RoutingSuiteManifest:
    return RoutingSuiteManifest.model_validate(_load_yaml(path))


def load_routing_stage(path: Path) -> RoutingStage:
    return RoutingStageManifest.model_validate(_load_yaml(path))


def _git(repository: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-c", "core.longpaths=true", "-C", str(repository), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RoutingSuiteError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout


def _frozen_file_bytes(
    repository_root: Path,
    fixture: FrozenFixtureSpec,
    relative_path: str,
) -> bytes:
    object_path = f"{fixture.commit}:{fixture.path}/{relative_path}"
    return _git(repository_root, "show", object_path)


def _frozen_files(
    repository_root: Path,
    fixture: FrozenFixtureSpec,
) -> dict[str, bytes]:
    tree = _git(
        repository_root,
        "rev-parse",
        f"{fixture.commit}:{fixture.path}",
    ).decode("ascii").strip()
    if tree != fixture.git_tree:
        raise RoutingSuiteError(f"fixture tree differs from frozen identity: {fixture.id}")
    names = _git(
        repository_root,
        "ls-tree",
        "-r",
        "--name-only",
        fixture.commit,
        "--",
        fixture.path,
    ).decode("utf-8").splitlines()
    prefix = fixture.path.rstrip("/") + "/"
    relative_names = [name[len(prefix) :] for name in names if name.startswith(prefix)]
    return {
        name: _frozen_file_bytes(repository_root, fixture, name)
        for name in relative_names
    }


def _scope_matches(path: str, scope: str) -> bool:
    if scope.endswith("/**"):
        prefix = scope[:-3].rstrip("/") + "/"
        return path.startswith(prefix)
    return path == scope


def _dependency_metrics(run: BenchmarkRun) -> tuple[int, int, int]:
    tasks = {task.key: task for task in run.tasks}
    if len(tasks) != len(run.tasks):
        raise RoutingSuiteError("benchmark Task keys must be unique")
    depth_cache: dict[str, int] = {}
    visiting: set[str] = set()

    def depth(key: str) -> int:
        if key in depth_cache:
            return depth_cache[key]
        if key in visiting:
            raise RoutingSuiteError("benchmark Task dependencies contain a cycle")
        visiting.add(key)
        task = tasks[key]
        unknown = set(task.depends_on) - set(tasks)
        if unknown:
            raise RoutingSuiteError(f"benchmark Task has unknown dependencies: {sorted(unknown)}")
        value = 1 + max((depth(parent) for parent in task.depends_on), default=0)
        visiting.remove(key)
        depth_cache[key] = value
        return value

    dependency_depth = max(depth(key) for key in tasks)
    dependency_edges = sum(len(task.depends_on) for task in run.tasks)
    max_fan_in = max(len(task.depends_on) for task in run.tasks)
    return dependency_depth, dependency_edges, max_fan_in


def _write_module(scope: str) -> str:
    path = PurePosixPath(scope[:-3] if scope.endswith("/**") else scope)
    return path.parts[0]


def _scopes_overlap(left: str, right: str) -> bool:
    left_prefix = left[:-3].rstrip("/") + "/" if left.endswith("/**") else None
    right_prefix = right[:-3].rstrip("/") + "/" if right.endswith("/**") else None
    if left_prefix and right_prefix:
        return left_prefix.startswith(right_prefix) or right_prefix.startswith(left_prefix)
    if left_prefix:
        return right.startswith(left_prefix)
    if right_prefix:
        return left.startswith(right_prefix)
    return left == right


def _scope_overlap(run: BenchmarkRun) -> str:
    if len(run.tasks) == 1:
        return "not_applicable"
    task_scopes = [tuple(task.write_scope) for task in run.tasks]
    overlapping_pairs = 0
    pair_count = 0
    exact_shared = True
    for index, left in enumerate(task_scopes):
        for right in task_scopes[index + 1 :]:
            pair_count += 1
            pair_overlaps = any(
                _scopes_overlap(left_scope, right_scope)
                for left_scope in left
                for right_scope in right
            )
            overlapping_pairs += int(pair_overlaps)
            exact_shared = exact_shared and set(left) == set(right)
    if overlapping_pairs == 0:
        return "disjoint"
    if pair_count and overlapping_pairs == pair_count and exact_shared:
        return "shared"
    return "partial"


def compute_fixture_complexity(
    repository_root: Path,
    fixture: FrozenFixtureSpec,
    *,
    expected_write_files: ExpectedWriteFiles,
    verification_kind: str,
    failure_profile: str,
    solution_ambiguity: str,
) -> FixtureComplexity:
    repository_root = repository_root.resolve()
    files = _frozen_files(repository_root, fixture)
    try:
        run_value = yaml.safe_load(files["benchmark-run.yaml"].decode("utf-8"))
    except (KeyError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise RoutingSuiteError(f"cannot load frozen benchmark run: {fixture.id}") from exc
    run = BenchmarkRun.model_validate(run_value)
    dependency_depth, dependency_edges, max_fan_in = _dependency_metrics(run)
    worker_files = {
        path: content
        for path, content in files.items()
        if not path.startswith(("benchmark_checks/", ".orchestrator/"))
        and any(
            _scope_matches(path, scope)
            for task in run.tasks
            for scope in task.read_scope
        )
    }
    input_count = sum(len(task.inputs) for task in run.tasks)
    handoff_kind = (
        "none"
        if len(run.tasks) == 1
        else "declared_single"
        if input_count == 1
        else "declared_multiple"
        if input_count > 1
        else "filesystem_implicit"
    )
    write_modules = {
        _write_module(scope)
        for task in run.tasks
        for scope in task.write_scope
    }
    return FixtureComplexity(
        task_count=len(run.tasks),
        dependency_depth=dependency_depth,
        dependency_edges=dependency_edges,
        max_fan_in=max_fan_in,
        worker_read_files=len(worker_files),
        worker_read_bytes=sum(len(content) for content in worker_files.values()),
        expected_write_files=expected_write_files,
        write_modules=len(write_modules),
        check_count=sum(len(task.check_names) for task in run.tasks),
        handoff_kind=handoff_kind,
        scope_overlap=_scope_overlap(run),
        verification_kind=verification_kind,
        failure_profile=failure_profile,
        solution_ambiguity=solution_ambiguity,
    )


def _resolve_stage(
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
) -> tuple[RoutingSuiteManifest, RoutingStageManifest]:
    repository_root = repository_root.resolve()
    suite_path = suite_path.resolve()
    stage_path = stage_path.resolve()
    suite = load_routing_suite(suite_path)
    stage = load_routing_stage(stage_path)
    reference = next(
        (item for item in suite.stages if item.stage_id == stage.stage_id),
        None,
    )
    if reference is None:
        raise RoutingSuiteError("routing stage is not declared by the suite")
    expected_path = (repository_root / reference.path).resolve()
    if expected_path != stage_path:
        raise RoutingSuiteError("routing stage path differs from the suite reference")
    if suite.status != stage.status:
        raise RoutingSuiteError("routing suite and stage freeze states differ")
    return suite, stage


def _fixture_specs(
    repository_root: Path,
    stage: RoutingStageManifest,
) -> list[FrozenFixtureSpec]:
    fixtures: list[FrozenFixtureSpec] = []
    for selection in stage.fixture_manifests:
        manifest = load_frozen_manifest(repository_root / selection.path)
        by_id = {fixture.id: fixture for fixture in manifest.fixtures}
        for fixture_id in selection.fixture_ids:
            try:
                fixtures.append(by_id[fixture_id])
            except KeyError as exc:
                raise RoutingSuiteError(
                    f"fixture {fixture_id} is missing from {selection.path}"
                ) from exc
    return fixtures


def _verified_profiles(
    repository_root: Path,
    stage: RoutingStageManifest,
    fixtures: list[FrozenFixtureSpec],
) -> dict[str, FixtureComplexity]:
    declarations = {item.fixture_id: item.complexity for item in stage.profiles}
    verified: dict[str, FixtureComplexity] = {}
    for fixture in fixtures:
        declared = declarations[fixture.id]
        calculated = compute_fixture_complexity(
            repository_root,
            fixture,
            expected_write_files=declared.expected_write_files,
            verification_kind=declared.verification_kind,
            failure_profile=declared.failure_profile,
            solution_ambiguity=declared.solution_ambiguity,
        )
        if calculated != declared:
            raise RoutingSuiteError(f"complexity profile differs for fixture {fixture.id}")
        verified[fixture.id] = calculated
    return verified


def _build_routing_plan(
    *,
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
    runner: ArtifactIdentity,
    variants: list[ArtifactIdentity],
    environment_fingerprint: dict[str, str],
    created_at: datetime | None = None,
    revision: int = 1,
    track: str,
    planned_actual_model_turns: int | None,
    require_frozen: bool,
) -> ExecutionPlan:
    repository_root = repository_root.resolve()
    suite_path = suite_path.resolve()
    stage_path = stage_path.resolve()
    suite, stage = _resolve_stage(repository_root, suite_path, stage_path)
    if require_frozen and (
        suite.status != "frozen_before_execution"
        or stage.status != "frozen_before_execution"
    ):
        raise RoutingSuiteError("routing live Plan requires frozen suite and stage manifests")
    if require_frozen:
        for selection in stage.fixture_manifests:
            manifest = load_frozen_manifest(repository_root / selection.path)
            if manifest.status != "frozen_before_execution":
                raise RoutingSuiteError("routing live Plan requires frozen fixture manifests")
    fixtures = _fixture_specs(repository_root, stage)
    profiles = _verified_profiles(repository_root, stage, fixtures)
    if isinstance(stage, RoutingS1StageManifest):
        cells = [
            PlannedCell(
                cell_id=f"cell_s1_{cell.fixture_id}_{cell.repetition}_{cell.variant_id}",
                block_id=f"block_s1_{cell.fixture_id}_{cell.repetition}",
                fixture_id=cell.fixture_id,
                repetition=cell.repetition,
                variant_id=cell.variant_id,
                execution_ordinal=index,
            )
            for index, cell in enumerate(stage.cells, start=1)
        ]
        stage_policy: dict[str, Any] = {
            "planned_live_model_turns": stage.planned_live_model_turns,
            "route_decision_allowed": stage.route_decision_allowed,
        }
    else:
        if isinstance(stage, RoutingS2StageManifest):
            from benchmark_runner.s2_posthoc import PROPERTY_IDS, checker_sha256
        else:
            from benchmark_runner.s3_posthoc import PROPERTY_IDS, checker_sha256

        stage_label = "s2" if isinstance(stage, RoutingS2StageManifest) else "s3"

        cells = [
            PlannedCell(
                cell_id=cell.cell_id,
                block_id=f"block_{stage_label}_{cell.profile_alias}_{cell.repetition}",
                fixture_id=cell.fixture_id,
                repetition=cell.repetition,
                variant_id=cell.variant_id,
                execution_ordinal=index,
            )
            for index, cell in enumerate(stage.cells, start=1)
        ]
        stage_policy = {
            "profile_aliases": dict(stage.profile_aliases),
            "base_live_model_turns": stage.base_live_model_turns,
            "b1_retry_resume_reserve_turns": stage.b1_retry_resume_reserve_turns,
            "max_actual_live_model_turns": stage.max_actual_live_model_turns,
            "route_decision_allowed": stage.route_decision_allowed,
            "posthoc_checks": {
                fixture_id: {
                    "checker_sha256": checker_sha256(fixture_id),
                    "property_ids": list(PROPERTY_IDS[fixture_id]),
                    "result_path": "judge/posthoc/result.json",
                }
                for fixture_id in stage.profile_aliases.values()
            },
        }
        if isinstance(stage, RoutingS3StageManifest):
            stage_policy["b1_retry_resume_reserve_turns_per_profile"] = (
                stage.b1_retry_resume_reserve_turns_per_profile
            )
    return build_sdk_controlled_plan(
        source_manifest_path=stage_path.relative_to(repository_root).as_posix(),
        source_manifest_sha256=sha256_file(stage_path),
        fixtures=[
            FixtureIdentity(
                fixture_id=fixture.id,
                source_commit=fixture.commit,
                git_tree=fixture.git_tree,
            )
            for fixture in fixtures
        ],
        runner=runner,
        variants=variants,
        cells=cells,
        baseline_variant=stage.baseline_variant,
        candidate_variants=list(stage.candidate_variants),
        decision_policy={
            "suite_id": suite.suite_id,
            "suite_sha256": sha256_file(suite_path),
            "stage_id": stage.stage_id,
            "purpose": stage.purpose,
            "allowed_outcomes": list(stage.allowed_outcomes),
            **stage_policy,
            "profiles": {
                fixture_id: profile.model_dump(mode="json")
                for fixture_id, profile in profiles.items()
            },
        },
        environment_fingerprint=environment_fingerprint,
        created_at=created_at,
        revision=revision,
        seed=0,
        track=track,
        planned_actual_model_turns=planned_actual_model_turns,
    )


def build_routing_s1_plan(
    *,
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
    runner: ArtifactIdentity,
    variants: list[ArtifactIdentity],
    environment_fingerprint: dict[str, str],
    created_at: datetime | None = None,
    revision: int = 1,
) -> ExecutionPlan:
    """Build the zero-turn S1 contract-validation Plan."""

    return _build_routing_plan(
        repository_root=repository_root,
        suite_path=suite_path,
        stage_path=stage_path,
        runner=runner,
        variants=variants,
        environment_fingerprint=environment_fingerprint,
        created_at=created_at,
        revision=revision,
        track="sdk_routing_s1_model_free_validation",
        planned_actual_model_turns=0,
        require_frozen=False,
    )


def build_routing_s1_live_plan(
    *,
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
    runner: ArtifactIdentity,
    variants: list[ArtifactIdentity],
    environment_fingerprint: dict[str, str],
    created_at: datetime | None = None,
    revision: int = 1,
) -> ExecutionPlan:
    """Build the immutable S1 live Plan only from frozen manifests."""

    return _build_routing_plan(
        repository_root=repository_root,
        suite_path=suite_path,
        stage_path=stage_path,
        runner=runner,
        variants=variants,
        environment_fingerprint=environment_fingerprint,
        created_at=created_at,
        revision=revision,
        track="sdk_routing_s1_live_calibration",
        planned_actual_model_turns=None,
        require_frozen=True,
    )


def build_routing_s2_plan(
    *,
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
    runner: ArtifactIdentity,
    variants: list[ArtifactIdentity],
    environment_fingerprint: dict[str, str],
    created_at: datetime | None = None,
    revision: int = 1,
) -> ExecutionPlan:
    """Build the zero-turn S2 contract-validation Plan."""

    plan = _build_routing_plan(
        repository_root=repository_root,
        suite_path=suite_path,
        stage_path=stage_path,
        runner=runner,
        variants=variants,
        environment_fingerprint=environment_fingerprint,
        created_at=created_at,
        revision=revision,
        track="sdk_routing_s2_model_free_validation",
        planned_actual_model_turns=0,
        require_frozen=False,
    )
    if plan.decision_policy.get("stage_id") != "s2-intermediate":
        raise RoutingSuiteError("S2 Plan builder requires the S2 stage")
    return plan


def build_routing_s2_live_plan(
    *,
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
    runner: ArtifactIdentity,
    variants: list[ArtifactIdentity],
    environment_fingerprint: dict[str, str],
    created_at: datetime | None = None,
    revision: int = 1,
) -> ExecutionPlan:
    """Build the immutable S2 live Plan only from frozen manifests."""

    plan = _build_routing_plan(
        repository_root=repository_root,
        suite_path=suite_path,
        stage_path=stage_path,
        runner=runner,
        variants=variants,
        environment_fingerprint=environment_fingerprint,
        created_at=created_at,
        revision=revision,
        track="sdk_routing_s2_live_initial",
        planned_actual_model_turns=None,
        require_frozen=True,
    )
    if plan.decision_policy.get("stage_id") != "s2-intermediate":
        raise RoutingSuiteError("S2 live Plan builder requires the S2 stage")
    return plan


def build_routing_s3_plan(
    *,
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
    runner: ArtifactIdentity,
    variants: list[ArtifactIdentity],
    environment_fingerprint: dict[str, str],
    created_at: datetime | None = None,
    revision: int = 1,
) -> ExecutionPlan:
    """Build the zero-turn S3 contract-validation Plan."""

    plan = _build_routing_plan(
        repository_root=repository_root,
        suite_path=suite_path,
        stage_path=stage_path,
        runner=runner,
        variants=variants,
        environment_fingerprint=environment_fingerprint,
        created_at=created_at,
        revision=revision,
        track="sdk_routing_s3_model_free_validation",
        planned_actual_model_turns=0,
        require_frozen=False,
    )
    if plan.decision_policy.get("stage_id") != "s3-complex-high-risk":
        raise RoutingSuiteError("S3 Plan builder requires the S3 stage")
    return plan


def build_routing_s3_live_plan(
    *,
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
    runner: ArtifactIdentity,
    variants: list[ArtifactIdentity],
    environment_fingerprint: dict[str, str],
    created_at: datetime | None = None,
    revision: int = 1,
) -> ExecutionPlan:
    """Build the immutable S3 live Plan only from frozen manifests."""

    plan = _build_routing_plan(
        repository_root=repository_root,
        suite_path=suite_path,
        stage_path=stage_path,
        runner=runner,
        variants=variants,
        environment_fingerprint=environment_fingerprint,
        created_at=created_at,
        revision=revision,
        track="sdk_routing_s3_live_initial",
        planned_actual_model_turns=None,
        require_frozen=True,
    )
    if plan.decision_policy.get("stage_id") != "s3-complex-high-risk":
        raise RoutingSuiteError("S3 live Plan builder requires the S3 stage")
    return plan


def _build_routing_reverse_live_plan(
    *,
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
    runner: ArtifactIdentity,
    variants: list[ArtifactIdentity],
    environment_fingerprint: dict[str, str],
    expansion_profile: str,
    initial_export_identity: dict[str, str],
    stage_id: Literal["s2-intermediate", "s3-complex-high-risk"],
    expected_gate_state: Literal["S2_EXPANSION_REQUIRED", "S3_REPLICATION_REQUIRED"],
    reverse_base_turns: int,
    reverse_reserve_turns: int,
    reverse_max_turns: int,
    reverse_track: str,
    created_at: datetime | None = None,
    revision: int = 1,
) -> ExecutionPlan:
    """Build one stage-bound reverse pair from the frozen initial stage."""

    initial_builder = (
        build_routing_s2_live_plan
        if stage_id == "s2-intermediate"
        else build_routing_s3_live_plan
    )
    initial = initial_builder(
        repository_root=repository_root,
        suite_path=suite_path,
        stage_path=stage_path,
        runner=runner,
        variants=variants,
        environment_fingerprint=environment_fingerprint,
        created_at=created_at,
        revision=revision,
    )
    aliases = initial.decision_policy.get("profile_aliases")
    if not isinstance(aliases, dict) or expansion_profile not in aliases.values():
        raise RoutingSuiteError("routing reverse Plan expansion profile is not frozen")
    alias = next(key for key, value in aliases.items() if value == expansion_profile)
    by_variant = {
        cell.variant_id: cell
        for cell in initial.cells
        if cell.fixture_id == expansion_profile
    }
    if set(by_variant) != {"c2", "b1"}:
        raise RoutingSuiteError("routing reverse Plan requires one frozen C2/B1 pair")
    expected_identity_keys = {
        "experiment_id",
        "plan_fingerprint",
        "export_sha256",
        "stage_state",
        "source_commit",
    }
    if (
        set(initial_export_identity) != expected_identity_keys
        or initial_export_identity.get("stage_state") != expected_gate_state
        or any(
            not isinstance(value, str) or not value
            for value in initial_export_identity.values()
        )
    ):
        raise RoutingSuiteError("routing reverse Plan initial export identity is invalid")
    initial_order = [
        cell.variant_id
        for cell in sorted(initial.cells, key=lambda item: item.execution_ordinal)
        if cell.fixture_id == expansion_profile
    ]
    reverse_order = tuple(reversed(initial_order))
    if set(reverse_order) != {"c2", "b1"} or len(reverse_order) != 2:
        raise RoutingSuiteError("routing reverse Plan cannot derive the frozen opposite order")
    stage_label = "s2" if stage_id == "s2-intermediate" else "s3"
    cells = [
        by_variant[variant_id].model_copy(
            update={
                "cell_id": f"cell_{stage_label}_{alias}_2_{variant_id}",
                "block_id": f"block_{stage_label}_{alias}_2",
                "execution_ordinal": ordinal,
            }
        )
        for ordinal, variant_id in enumerate(reverse_order, start=1)
    ]
    policy = {
        **initial.decision_policy,
        "execution_phase": "reverse",
        "expansion_profile": expansion_profile,
        "initial_export_identity": dict(initial_export_identity),
        "base_live_model_turns": reverse_base_turns,
        "b1_retry_resume_reserve_turns": reverse_reserve_turns,
        "max_actual_live_model_turns": reverse_max_turns,
    }
    return build_sdk_controlled_plan(
        source_manifest_path=initial.source_manifest.path,
        source_manifest_sha256=initial.source_manifest.sha256,
        fixtures=[
            fixture
            for fixture in initial.fixtures
            if fixture.fixture_id == expansion_profile
        ],
        runner=runner,
        variants=variants,
        cells=cells,
        baseline_variant=initial.baseline_variant,
        candidate_variants=list(initial.candidate_variants),
        decision_policy=policy,
        environment_fingerprint=environment_fingerprint,
        created_at=created_at,
        revision=revision,
        seed=0,
        track=reverse_track,
        planned_actual_model_turns=None,
    )


def build_routing_s2_reverse_live_plan(
    *,
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
    runner: ArtifactIdentity,
    variants: list[ArtifactIdentity],
    environment_fingerprint: dict[str, str],
    expansion_profile: str,
    initial_export_identity: dict[str, str],
    created_at: datetime | None = None,
    revision: int = 1,
) -> ExecutionPlan:
    """Build one separately approved S2 reverse pair."""

    return _build_routing_reverse_live_plan(
        repository_root=repository_root,
        suite_path=suite_path,
        stage_path=stage_path,
        runner=runner,
        variants=variants,
        environment_fingerprint=environment_fingerprint,
        expansion_profile=expansion_profile,
        initial_export_identity=initial_export_identity,
        stage_id="s2-intermediate",
        expected_gate_state="S2_EXPANSION_REQUIRED",
        reverse_base_turns=6,
        reverse_reserve_turns=3,
        reverse_max_turns=9,
        reverse_track="sdk_routing_s2_live_reverse",
        created_at=created_at,
        revision=revision,
    )


def build_routing_s3_reverse_live_plan(
    *,
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
    runner: ArtifactIdentity,
    variants: list[ArtifactIdentity],
    environment_fingerprint: dict[str, str],
    expansion_profile: str,
    initial_export_identity: dict[str, str],
    created_at: datetime | None = None,
    revision: int = 1,
) -> ExecutionPlan:
    """Build one separately approved S3 reverse pair."""

    return _build_routing_reverse_live_plan(
        repository_root=repository_root,
        suite_path=suite_path,
        stage_path=stage_path,
        runner=runner,
        variants=variants,
        environment_fingerprint=environment_fingerprint,
        expansion_profile=expansion_profile,
        initial_export_identity=initial_export_identity,
        stage_id="s3-complex-high-risk",
        expected_gate_state="S3_REPLICATION_REQUIRED",
        reverse_base_turns=8,
        reverse_reserve_turns=2,
        reverse_max_turns=10,
        reverse_track="sdk_routing_s3_live_reverse",
        created_at=created_at,
        revision=revision,
    )


def initialize_routing_s1_experiment(
    state_root: Path,
    plan: ExecutionPlan,
) -> Path:
    return initialize_sdk_experiment(state_root, plan)


def initialize_routing_s2_experiment(
    state_root: Path,
    plan: ExecutionPlan,
) -> Path:
    if plan.decision_policy.get("stage_id") != "s2-intermediate":
        raise RoutingSuiteError("S2 experiment requires an S2 Plan")
    return initialize_sdk_experiment(state_root, plan)


def initialize_routing_s3_experiment(
    state_root: Path,
    plan: ExecutionPlan,
) -> Path:
    if plan.decision_policy.get("stage_id") != "s3-complex-high-risk":
        raise RoutingSuiteError("S3 experiment requires an S3 Plan")
    return initialize_sdk_experiment(state_root, plan)


AdapterFactory = Callable[[PlannedCell, PreparedFixture], VariantAdapter]


def _run_next_routing_nonlive_cell(
    *,
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
    experiment_dir: Path,
    adapter_factory: AdapterFactory,
    benchmark_python: Path,
    git_executable: Path,
    expected_stage_id: RoutingStageId,
) -> SdkSealedCellResult:
    repository_root = repository_root.resolve()
    suite, stage = _resolve_stage(repository_root, suite_path, stage_path)
    del suite
    plan = ExecutionPlan.model_validate_json(
        (experiment_dir / "execution-plan.json").read_bytes()
    )
    if (
        plan.source_manifest.path != stage_path.resolve().relative_to(repository_root).as_posix()
        or plan.source_manifest.sha256 != sha256_file(stage_path)
        or plan.decision_policy.get("stage_id") != stage.stage_id
        or stage.stage_id != expected_stage_id
        or plan.decision_policy.get("route_decision_allowed")
        is not (expected_stage_id != "s1-baseline")
    ):
        raise RoutingSuiteError("routing Plan differs from the current stage contract")
    next_cell = next(
        (
            cell
            for cell in sorted(plan.cells, key=lambda item: item.execution_ordinal)
            if not (
                experiment_dir
                / "cells"
                / cell.cell_id
                / "cell-state.json"
            ).is_file()
        ),
        None,
    )
    if next_cell is None:
        raise RoutingSuiteError("routing Plan has no remaining Cell")
    fixtures = {fixture.id: fixture for fixture in _fixture_specs(repository_root, stage)}
    prepared = FixtureRestorer(repository_root, str(git_executable)).restore(
        fixtures[next_cell.fixture_id],
        experiment_dir / "cells" / next_cell.cell_id / "workspace",
    )
    adapter = adapter_factory(next_cell, prepared)
    post_judge_hook = None
    if expected_stage_id == "s2-intermediate":
        from benchmark_runner.s2_posthoc import run_posthoc_subprocess

        post_judge_hook = lambda current: run_posthoc_subprocess(
            repository_root=repository_root,
            benchmark_python=benchmark_python,
            fixture_id=current.fixture.id,
            workspace=current.workspace,
        )
    elif expected_stage_id == "s3-complex-high-risk":
        from benchmark_runner.s3_posthoc import run_posthoc_subprocess

        post_judge_hook = lambda current: run_posthoc_subprocess(
            repository_root=repository_root,
            benchmark_python=benchmark_python,
            fixture_id=current.fixture.id,
            workspace=current.workspace,
        )
    return run_sdk_nonlive_cell(
        experiment_dir=experiment_dir,
        plan=plan,
        planned_cell=next_cell,
        prepared=prepared,
        adapter=adapter,
        benchmark_python=benchmark_python,
        git_executable=git_executable,
        post_judge_hook=post_judge_hook,
    )


def run_next_routing_s1_nonlive_cell(
    *,
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
    experiment_dir: Path,
    adapter_factory: AdapterFactory,
    benchmark_python: Path,
    git_executable: Path,
) -> SdkSealedCellResult:
    return _run_next_routing_nonlive_cell(
        repository_root=repository_root,
        suite_path=suite_path,
        stage_path=stage_path,
        experiment_dir=experiment_dir,
        adapter_factory=adapter_factory,
        benchmark_python=benchmark_python,
        git_executable=git_executable,
        expected_stage_id="s1-baseline",
    )


def run_next_routing_s2_nonlive_cell(
    *,
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
    experiment_dir: Path,
    adapter_factory: AdapterFactory,
    benchmark_python: Path,
    git_executable: Path,
) -> SdkSealedCellResult:
    return _run_next_routing_nonlive_cell(
        repository_root=repository_root,
        suite_path=suite_path,
        stage_path=stage_path,
        experiment_dir=experiment_dir,
        adapter_factory=adapter_factory,
        benchmark_python=benchmark_python,
        git_executable=git_executable,
        expected_stage_id="s2-intermediate",
    )


def run_next_routing_s3_nonlive_cell(
    *,
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
    experiment_dir: Path,
    adapter_factory: AdapterFactory,
    benchmark_python: Path,
    git_executable: Path,
) -> SdkSealedCellResult:
    return _run_next_routing_nonlive_cell(
        repository_root=repository_root,
        suite_path=suite_path,
        stage_path=stage_path,
        experiment_dir=experiment_dir,
        adapter_factory=adapter_factory,
        benchmark_python=benchmark_python,
        git_executable=git_executable,
        expected_stage_id="s3-complex-high-risk",
    )


def _load_routing_plan(
    experiment_dir: Path,
    *,
    expected_stage_id: RoutingStageId = "s1-baseline",
) -> ExecutionPlan:
    try:
        plan = ExecutionPlan.model_validate_json(
            (experiment_dir / "execution-plan.json").read_bytes()
        )
    except (OSError, ValueError) as exc:
        raise RoutingSuiteError("routing Execution Plan is missing or invalid") from exc
    if experiment_dir.resolve().name != plan.experiment_id:
        raise RoutingSuiteError("routing Experiment directory differs from its Plan")
    track_values = [
        item.value for item in plan.plan_supplemented if item.field == "track"
    ]
    stage_label = {
        "s1-baseline": "s1",
        "s2-intermediate": "s2",
        "s3-complex-high-risk": "s3",
    }[expected_stage_id]
    expected_track = f"sdk_routing_{stage_label}_model_free_validation"
    expected_route = expected_stage_id != "s1-baseline"
    if (
        track_values != [expected_track]
        or plan.decision_policy.get("stage_id") != expected_stage_id
        or plan.decision_policy.get("route_decision_allowed") is not expected_route
    ):
        raise RoutingSuiteError("routing Plan is not the expected model-free validation track")
    return plan


def _run_all_routing_nonlive_cells(
    *,
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
    experiment_dir: Path,
    adapter_factory: AdapterFactory,
    benchmark_python: Path,
    git_executable: Path,
    expected_stage_id: RoutingStageId,
) -> list[SdkSealedCellResult]:
    """Run every remaining Cell through the existing one-Cell boundary."""

    plan = _load_routing_plan(
        experiment_dir,
        expected_stage_id=expected_stage_id,
    )
    results: list[SdkSealedCellResult] = []
    for _ in range(len(plan.cells)):
        status = _routing_nonlive_status(
            experiment_dir,
            expected_stage_id=expected_stage_id,
        )
        if status["complete"] is True:
            break
        results.append(
            _run_next_routing_nonlive_cell(
                repository_root=repository_root,
                suite_path=suite_path,
                stage_path=stage_path,
                experiment_dir=experiment_dir,
                adapter_factory=adapter_factory,
                benchmark_python=benchmark_python,
                git_executable=git_executable,
                expected_stage_id=expected_stage_id,
            )
        )
    final = _routing_nonlive_status(
        experiment_dir,
        expected_stage_id=expected_stage_id,
    )
    if final["complete"] is not True:
        raise RoutingSuiteError("routing model-free run did not seal every Cell")
    return results


def run_all_routing_s1_nonlive_cells(
    *,
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
    experiment_dir: Path,
    adapter_factory: AdapterFactory,
    benchmark_python: Path,
    git_executable: Path,
) -> list[SdkSealedCellResult]:
    return _run_all_routing_nonlive_cells(
        repository_root=repository_root,
        suite_path=suite_path,
        stage_path=stage_path,
        experiment_dir=experiment_dir,
        adapter_factory=adapter_factory,
        benchmark_python=benchmark_python,
        git_executable=git_executable,
        expected_stage_id="s1-baseline",
    )


def run_all_routing_s2_nonlive_cells(
    *,
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
    experiment_dir: Path,
    adapter_factory: AdapterFactory,
    benchmark_python: Path,
    git_executable: Path,
) -> list[SdkSealedCellResult]:
    return _run_all_routing_nonlive_cells(
        repository_root=repository_root,
        suite_path=suite_path,
        stage_path=stage_path,
        experiment_dir=experiment_dir,
        adapter_factory=adapter_factory,
        benchmark_python=benchmark_python,
        git_executable=git_executable,
        expected_stage_id="s2-intermediate",
    )


def run_all_routing_s3_nonlive_cells(
    *,
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
    experiment_dir: Path,
    adapter_factory: AdapterFactory,
    benchmark_python: Path,
    git_executable: Path,
) -> list[SdkSealedCellResult]:
    return _run_all_routing_nonlive_cells(
        repository_root=repository_root,
        suite_path=suite_path,
        stage_path=stage_path,
        experiment_dir=experiment_dir,
        adapter_factory=adapter_factory,
        benchmark_python=benchmark_python,
        git_executable=git_executable,
        expected_stage_id="s3-complex-high-risk",
    )


def _routing_nonlive_status(
    experiment_dir: Path,
    *,
    expected_stage_id: RoutingStageId,
) -> dict[str, Any]:
    """Derive model-free completion from independently verified Cell seals."""

    experiment_dir = experiment_dir.resolve()
    plan = _load_routing_plan(
        experiment_dir,
        expected_stage_id=expected_stage_id,
    )
    cells: list[dict[str, Any]] = []
    sealed_count = 0
    all_checks_passed = True
    all_properties_passed = True
    actual_model_turns = 0
    for cell in sorted(plan.cells, key=lambda item: item.execution_ordinal):
        cell_dir = experiment_dir / "cells" / cell.cell_id
        state_path = cell_dir / "cell-state.json"
        if not state_path.is_file():
            cells.append(
                {
                    "cell_id": cell.cell_id,
                    "fixture_id": cell.fixture_id,
                    "variant_id": cell.variant_id,
                    "state": "PLANNED",
                    "outcome_state": None,
                    "check_success": None,
                    "actual_model_turns": None,
                    "property_status": None,
                }
            )
            all_checks_passed = False
            if expected_stage_id != "s1-baseline":
                all_properties_passed = False
            continue
        try:
            state = CellStateRecord.model_validate_json(state_path.read_bytes())
        except (OSError, ValueError) as exc:
            raise RoutingSuiteError(f"invalid Cell state: {cell.cell_id}") from exc
        check_success: bool | None = None
        cell_turns: int | None = None
        property_status: str | None = None
        if state.state is CellLifecycleState.SEALED:
            measurement = verify_sealed_cell(cell_dir)
            check_success = measurement.outcome.check_success
            if expected_stage_id != "s1-baseline":
                candidate_status = measurement.variant_metrics.values.get(
                    "property_status"
                )
                if candidate_status not in {"pass", "fail", "checker_error"}:
                    raise RoutingSuiteError(
                        f"invalid property_status in Cell {cell.cell_id}"
                    )
                property_status = candidate_status
                all_properties_passed = (
                    all_properties_passed and property_status == "pass"
                )
            value = measurement.variant_metrics.values.get("actual_model_turns")
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise RoutingSuiteError(
                    f"invalid actual_model_turns in Cell {cell.cell_id}"
                )
            cell_turns = value
            actual_model_turns += value
            sealed_count += 1
            all_checks_passed = all_checks_passed and check_success
        else:
            all_checks_passed = False
            all_properties_passed = False
        cells.append(
            {
                "cell_id": cell.cell_id,
                "fixture_id": cell.fixture_id,
                "variant_id": cell.variant_id,
                "state": state.state.value,
                "outcome_state": state.outcome_state,
                "check_success": check_success,
                "actual_model_turns": cell_turns,
                "property_status": property_status,
            }
        )
    complete = sealed_count == len(plan.cells)
    if not complete:
        validation_status = "MODEL_FREE_INCOMPLETE"
    elif all_checks_passed and all_properties_passed and actual_model_turns == 0:
        validation_status = "MODEL_FREE_PASS"
    else:
        validation_status = "MODEL_FREE_FAIL"
    return {
        "schema_version": 1,
        "kind": f"sdk_routing_{ {'s1-baseline': 's1', 's2-intermediate': 's2', 's3-complex-high-risk': 's3'}[expected_stage_id] }_model_free_status",
        "experiment_id": plan.experiment_id,
        "stage_id": plan.decision_policy.get("stage_id"),
        "planned_cells": len(plan.cells),
        "sealed_cells": sealed_count,
        "complete": complete,
        "all_checks_passed": all_checks_passed,
        "all_properties_passed": all_properties_passed,
        "actual_model_turns": actual_model_turns,
        "validation_status": validation_status,
        "calibration_outcome_issued": False,
        "route_decision_issued": False,
        "cells": cells,
    }


def routing_s1_nonlive_status(experiment_dir: Path) -> dict[str, Any]:
    return _routing_nonlive_status(
        experiment_dir,
        expected_stage_id="s1-baseline",
    )


def routing_s2_nonlive_status(experiment_dir: Path) -> dict[str, Any]:
    return _routing_nonlive_status(
        experiment_dir,
        expected_stage_id="s2-intermediate",
    )


def routing_s3_nonlive_status(experiment_dir: Path) -> dict[str, Any]:
    return _routing_nonlive_status(
        experiment_dir,
        expected_stage_id="s3-complex-high-risk",
    )


def _routing_nonlive_summary(
    plan: ExecutionPlan,
    status: dict[str, Any],
    measurements: list[Measurement],
    *,
    stage_label: Literal["s1", "s2", "s3"],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for measurement in sorted(
        measurements, key=lambda item: item.identity.execution_ordinal
    ):
        rows.append(
            {
                "cell_id": measurement.identity.cell_id,
                "fixture_id": measurement.identity.fixture_id,
                "variant_id": measurement.identity.variant_id,
                "outcome_state": measurement.outcome.state,
                "check_success": measurement.outcome.check_success,
                "session_count": measurement.resource.session_count.value,
                "turn_count": measurement.resource.turn_count.value,
                "attempt_count": measurement.resource.attempt_count.value,
                "token_usage_status": measurement.resource.token_usage.status.value,
                "token_usage": measurement.resource.token_usage.value,
                "model_active_seconds": measurement.variant_metrics.values.get(
                    "model_active_seconds"
                ),
                "total_wall_clock_seconds": (
                    measurement.effort.total_wall_clock_seconds.value
                ),
                "actual_model_turns": measurement.variant_metrics.values[
                    "actual_model_turns"
                ],
                "property_status": measurement.variant_metrics.values.get(
                    "property_status"
                ),
                "checker_sha256": measurement.variant_metrics.values.get(
                    "checker_sha256"
                ),
            }
        )
    return {
        "schema_version": 1,
        "kind": f"sdk_routing_{stage_label}_model_free_summary",
        "experiment_id": plan.experiment_id,
        "stage_id": status["stage_id"],
        "validation_status": status["validation_status"],
        "complete": status["complete"],
        "actual_model_turns": status["actual_model_turns"],
        "calibration_outcome_issued": False,
        "route_decision_issued": False,
        "limitations": [
            "model-free contract validation only",
            "does not measure C2 or B1 model quality or resource usage",
            "does not authorize a routing decision",
        ],
        "cells": rows,
    }


def _routing_nonlive_summary_markdown(
    summary: dict[str, Any],
    *,
    stage_label: Literal["s1", "s2", "s3"],
) -> bytes:
    lines = [
        f"# SDK routing {stage_label.upper()} model-free validation",
        "",
        f"- Experiment: `{summary['experiment_id']}`",
        f"- Validation: `{summary['validation_status']}`",
        f"- Actual model turns: `{summary['actual_model_turns']}`",
        "- Calibration outcome issued: `false`",
        "- Route decision issued: `false`",
        "",
        "| Cell | Fixture | Variant | Outcome | Judge | Sessions | Turns |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for row in summary["cells"]:
        lines.append(
            f"| {row['cell_id']} | {row['fixture_id']} | {row['variant_id']} | "
            f"{row['outcome_state']} | {str(row['check_success']).lower()} | "
            f"{row['session_count']} | {row['turn_count']} |"
        )
    lines.extend(
        [
            "",
            "이 결과는 실행·봉인·export 계약의 비라이브 검증이다.",
            "`CALIBRATION_*` 또는 profile별 `ROUTE_*` 판정을 발행하지 않는다.",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def _aggregate_export_sha256(files: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(files):
        data = files[relative]
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(hashlib.sha256(data).digest())
    return digest.hexdigest()


def _export_routing_nonlive(
    *,
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
    experiment_dir: Path,
    results_root: Path,
    expected_stage_id: RoutingStageId,
) -> dict[str, Any]:
    """Export sealed model-free Cells without issuing a live verdict."""

    repository_root = repository_root.resolve()
    suite_path = suite_path.resolve()
    stage_path = stage_path.resolve()
    experiment_dir = experiment_dir.resolve()
    suite, stage = _resolve_stage(repository_root, suite_path, stage_path)
    plan = _load_routing_plan(
        experiment_dir,
        expected_stage_id=expected_stage_id,
    )
    if (
        plan.source_manifest.path != stage_path.relative_to(repository_root).as_posix()
        or plan.source_manifest.sha256 != sha256_file(stage_path)
        or plan.decision_policy.get("suite_sha256") != sha256_file(suite_path)
        or plan.decision_policy.get("stage_id") != stage.stage_id
    ):
        raise RoutingSuiteError("routing export inputs differ from the sealed Plan")
    status = _routing_nonlive_status(
        experiment_dir,
        expected_stage_id=expected_stage_id,
    )
    if status["complete"] is not True:
        raise RoutingSuiteError("routing export requires every planned Cell to be sealed")
    measurements = [
        verify_sealed_cell(experiment_dir / "cells" / cell.cell_id)
        for cell in sorted(plan.cells, key=lambda item: item.execution_ordinal)
    ]
    stage_label: Literal["s1", "s2", "s3"] = {
        "s1-baseline": "s1",
        "s2-intermediate": "s2",
        "s3-complex-high-risk": "s3",
    }[expected_stage_id]
    summary = _routing_nonlive_summary(
        plan,
        status,
        measurements,
        stage_label=stage_label,
    )
    export_root = (
        results_root.resolve()
        / f"sdk-routing-{stage_label}-model-free"
        / plan.experiment_id
    )
    if export_root.exists():
        raise RoutingSuiteError("routing export destination already exists")
    files: dict[str, bytes] = {
        "execution-plan.json": canonical_json_bytes(plan),
        "manifests/suite.yaml": suite_path.read_bytes(),
        "manifests/stage.yaml": stage_path.read_bytes(),
        "summary.json": canonical_json_bytes(summary),
        "summary.md": _routing_nonlive_summary_markdown(
            summary,
            stage_label=stage_label,
        ),
    }
    seals: list[dict[str, Any]] = []
    for cell, measurement in zip(
        sorted(plan.cells, key=lambda item: item.execution_ordinal),
        measurements,
        strict=True,
    ):
        cell_dir = experiment_dir / "cells" / cell.cell_id
        state = CellStateRecord.model_validate_json(
            (cell_dir / "cell-state.json").read_bytes()
        )
        if state.sealed_measurement_sha256 is None:
            raise RoutingSuiteError(f"sealed Cell omitted its hash: {cell.cell_id}")
        prefix = f"cells/{cell.cell_id}"
        measurement_relative = f"{prefix}/sealed/measurement.json"
        files[measurement_relative] = (
            cell_dir / "sealed" / "measurement.json"
        ).read_bytes()
        for evidence in measurement.evidence:
            files[f"{prefix}/{evidence.path}"] = (cell_dir / evidence.path).read_bytes()
        seals.append(
            {
                "cell_id": cell.cell_id,
                "fixture_id": cell.fixture_id,
                "variant_id": cell.variant_id,
                "measurement_path": measurement_relative,
                "sealed_measurement_sha256": state.sealed_measurement_sha256,
            }
        )
    files["seals.json"] = canonical_json_bytes(
        {
            "schema_version": 1,
            "kind": f"sdk_routing_{stage_label}_model_free_seals",
            "suite_id": suite.suite_id,
            "stage_id": stage.stage_id,
            "experiment_id": plan.experiment_id,
            "plan_fingerprint": plan.plan_fingerprint,
            "suite_sha256": sha256_file(suite_path),
            "stage_sha256": sha256_file(stage_path),
            "entries": seals,
        }
    )
    for relative, data in files.items():
        _r5_assert_export_safe(relative, data)
        atomic_write(export_root / relative, data)
    export_sha256 = _aggregate_export_sha256(files)
    atomic_write(
        export_root / "export-seal.json",
        canonical_json_bytes(
            {
                "schema_version": 1,
                "kind": f"sdk_routing_{stage_label}_model_free_export_seal",
                "experiment_id": plan.experiment_id,
                "file_count": len(files),
                "export_sha256": export_sha256,
            }
        ),
    )
    verified = _verify_routing_nonlive_export(
        export_root,
        expected_stage_id=expected_stage_id,
    )
    if verified["export_sha256"] != export_sha256:
        raise RoutingSuiteError("independent routing export verification disagreed")
    return {
        "experiment_id": plan.experiment_id,
        "validation_status": summary["validation_status"],
        "results_root": str(export_root),
        "file_count": len(files),
        "export_sha256": export_sha256,
    }


def export_routing_s1_nonlive(
    *,
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
    experiment_dir: Path,
    results_root: Path,
) -> dict[str, Any]:
    return _export_routing_nonlive(
        repository_root=repository_root,
        suite_path=suite_path,
        stage_path=stage_path,
        experiment_dir=experiment_dir,
        results_root=results_root,
        expected_stage_id="s1-baseline",
    )


def export_routing_s2_nonlive(
    *,
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
    experiment_dir: Path,
    results_root: Path,
) -> dict[str, Any]:
    return _export_routing_nonlive(
        repository_root=repository_root,
        suite_path=suite_path,
        stage_path=stage_path,
        experiment_dir=experiment_dir,
        results_root=results_root,
        expected_stage_id="s2-intermediate",
    )


def export_routing_s3_nonlive(
    *,
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
    experiment_dir: Path,
    results_root: Path,
) -> dict[str, Any]:
    return _export_routing_nonlive(
        repository_root=repository_root,
        suite_path=suite_path,
        stage_path=stage_path,
        experiment_dir=experiment_dir,
        results_root=results_root,
        expected_stage_id="s3-complex-high-risk",
    )


def _verify_routing_nonlive_export(
    export_root: Path,
    *,
    expected_stage_id: RoutingStageId,
) -> dict[str, Any]:
    """Verify only exported bytes; no source workspace is trusted."""

    export_root = export_root.resolve()
    try:
        plan = ExecutionPlan.model_validate_json(
            (export_root / "execution-plan.json").read_bytes()
        )
        assert_plan_integrity(plan)
        suite_bytes = (export_root / "manifests" / "suite.yaml").read_bytes()
        stage_bytes = (export_root / "manifests" / "stage.yaml").read_bytes()
        suite = RoutingSuiteManifest.model_validate(yaml.safe_load(suite_bytes))
        stage = RoutingStageManifest.model_validate(yaml.safe_load(stage_bytes))
        summary = json.loads((export_root / "summary.json").read_text(encoding="utf-8"))
        seals = json.loads((export_root / "seals.json").read_text(encoding="utf-8"))
        export_seal = json.loads(
            (export_root / "export-seal.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        raise RoutingSuiteError("routing export metadata is missing or invalid") from exc
    stage_label = {
        "s1-baseline": "s1",
        "s2-intermediate": "s2",
        "s3-complex-high-risk": "s3",
    }[expected_stage_id]
    expected_route = expected_stage_id != "s1-baseline"
    if (
        [item.value for item in plan.plan_supplemented if item.field == "track"]
        != [f"sdk_routing_{stage_label}_model_free_validation"]
        or [
            item.value
            for item in plan.plan_supplemented
            if item.field == "actual_model_turns"
        ]
        != [0]
        or plan.decision_policy.get("route_decision_allowed") is not expected_route
        or stage.stage_id != expected_stage_id
        or plan.experiment_id != seals.get("experiment_id")
        or plan.experiment_id != export_seal.get("experiment_id")
        or plan.experiment_id != summary.get("experiment_id")
        or plan.plan_fingerprint != seals.get("plan_fingerprint")
        or suite.suite_id != seals.get("suite_id")
        or stage.stage_id != seals.get("stage_id")
        or hashlib.sha256(suite_bytes).hexdigest() != seals.get("suite_sha256")
        or hashlib.sha256(stage_bytes).hexdigest() != seals.get("stage_sha256")
        or plan.source_manifest.sha256 != seals.get("stage_sha256")
        or plan.decision_policy.get("suite_sha256") != seals.get("suite_sha256")
        or plan.decision_policy.get("stage_id") != stage.stage_id
    ):
        raise RoutingSuiteError("routing export identities differ")
    reference = next(
        (item for item in suite.stages if item.stage_id == stage.stage_id),
        None,
    )
    planned_order = [
        (cell.fixture_id, cell.repetition, cell.variant_id)
        for cell in sorted(plan.cells, key=lambda item: item.execution_ordinal)
    ]
    declared_order = [
        (cell.fixture_id, cell.repetition, cell.variant_id) for cell in stage.cells
    ]
    if reference is None or planned_order != declared_order:
        raise RoutingSuiteError("routing export stage order differs from the Plan")
    summary_cells = summary.get("cells")
    if (
        summary.get("validation_status")
        not in {"MODEL_FREE_PASS", "MODEL_FREE_FAIL"}
        or summary.get("complete") is not True
        or not isinstance(summary.get("actual_model_turns"), int)
        or isinstance(summary.get("actual_model_turns"), bool)
        or summary.get("actual_model_turns") < 0
        or summary.get("calibration_outcome_issued") is not False
        or summary.get("route_decision_issued") is not False
        or not isinstance(summary_cells, list)
        or [row.get("cell_id") for row in summary_cells if isinstance(row, dict)]
        != [cell.cell_id for cell in sorted(plan.cells, key=lambda item: item.execution_ordinal)]
    ):
        raise RoutingSuiteError("routing export summary exceeds model-free scope")
    summary_by_cell = {
        row["cell_id"]: row for row in summary_cells if isinstance(row, dict)
    }
    expected_cells = {cell.cell_id: cell for cell in plan.cells}
    entries = seals.get("entries")
    if (
        not isinstance(entries, list)
        or len(entries) != len(expected_cells)
        or {entry.get("cell_id") for entry in entries if isinstance(entry, dict)}
        != set(expected_cells)
    ):
        raise RoutingSuiteError("routing export seal index differs from the Plan")
    measured_turns = 0
    all_checks_passed = True
    all_properties_passed = True
    for entry in entries:
        if not isinstance(entry, dict):
            raise RoutingSuiteError("routing export seal entry is invalid")
        cell = expected_cells[entry["cell_id"]]
        if (
            entry.get("fixture_id") != cell.fixture_id
            or entry.get("variant_id") != cell.variant_id
        ):
            raise RoutingSuiteError("routing export Cell identity differs")
        relative = entry.get("measurement_path")
        if not isinstance(relative, str):
            raise RoutingSuiteError("routing export Measurement path is invalid")
        measurement_path = (export_root / relative).resolve()
        if not measurement_path.is_relative_to(export_root) or not measurement_path.is_file():
            raise RoutingSuiteError("routing export Measurement is missing or unsafe")
        data = measurement_path.read_bytes()
        if hashlib.sha256(data).hexdigest() != entry.get("sealed_measurement_sha256"):
            raise RoutingSuiteError("routing export Measurement seal differs")
        measurement = Measurement.model_validate_json(data)
        expected_identity = MeasurementIdentity(
            experiment_id=plan.experiment_id,
            block_id=cell.block_id,
            cell_id=cell.cell_id,
            fixture_id=cell.fixture_id,
            repetition=cell.repetition,
            variant_id=cell.variant_id,
            execution_ordinal=cell.execution_ordinal,
        )
        fixture = next(
            item for item in plan.fixtures if item.fixture_id == cell.fixture_id
        )
        variant = next(
            item for item in plan.variants if item.artifact_id == cell.variant_id
        )
        if measurement.identity != expected_identity:
            raise RoutingSuiteError("routing export Measurement identity differs")
        if (
            measurement.provenance.manifest_sha256 != plan.source_manifest.sha256
            or measurement.provenance.fixture_source_commit != fixture.source_commit
            or measurement.provenance.fixture_tree_before != fixture.git_tree
            or measurement.provenance.runner_commit != plan.runner.version
            or measurement.provenance.variant_version != variant.version
            or measurement.provenance.variant_artifact_sha256 != variant.sha256
        ):
            raise RoutingSuiteError("routing export Measurement provenance differs")
        model_turns = measurement.variant_metrics.values.get("actual_model_turns")
        if not isinstance(model_turns, int) or isinstance(model_turns, bool) or model_turns < 0:
            raise RoutingSuiteError("routing export model turn count is invalid")
        measured_turns += model_turns
        all_checks_passed = all_checks_passed and measurement.outcome.check_success
        property_status = measurement.variant_metrics.values.get("property_status")
        if expected_stage_id != "s1-baseline":
            checker_contracts = plan.decision_policy.get("posthoc_checks")
            expected_checker = (
                checker_contracts.get(cell.fixture_id)
                if isinstance(checker_contracts, dict)
                else None
            )
            if (
                not isinstance(expected_checker, dict)
                or property_status not in {"pass", "fail", "checker_error"}
                or measurement.variant_metrics.values.get("checker_sha256")
                != expected_checker.get("checker_sha256")
            ):
                raise RoutingSuiteError("routing export property contract differs")
            all_properties_passed = (
                all_properties_passed and property_status == "pass"
            )
        row = summary_by_cell[cell.cell_id]
        if (
            row.get("fixture_id") != cell.fixture_id
            or row.get("variant_id") != cell.variant_id
            or row.get("outcome_state") != measurement.outcome.state
            or row.get("check_success") != measurement.outcome.check_success
            or row.get("actual_model_turns") != model_turns
            or row.get("property_status") != property_status
        ):
            raise RoutingSuiteError("routing export summary Cell differs from Measurement")
        cell_root = measurement_path.parents[1]
        for evidence in measurement.evidence:
            path = (cell_root / evidence.path).resolve()
            if not path.is_relative_to(cell_root) or not path.is_file():
                raise RoutingSuiteError("routing export Evidence is missing or unsafe")
            evidence_data = path.read_bytes()
            if (
                len(evidence_data) != evidence.size
                or hashlib.sha256(evidence_data).hexdigest() != evidence.sha256
            ):
                raise RoutingSuiteError("routing export Evidence hash differs")
    expected_validation = (
        "MODEL_FREE_PASS"
        if all_checks_passed and all_properties_passed and measured_turns == 0
        else "MODEL_FREE_FAIL"
    )
    if (
        summary.get("actual_model_turns") != measured_turns
        or summary.get("validation_status") != expected_validation
    ):
        raise RoutingSuiteError("routing export summary aggregate differs from Measurements")
    files = {
        path.relative_to(export_root).as_posix(): path.read_bytes()
        for path in export_root.rglob("*")
        if path.is_file() and path.name != "export-seal.json"
    }
    for relative, data in files.items():
        _r5_assert_export_safe(relative, data)
    value = _aggregate_export_sha256(files)
    if value != export_seal.get("export_sha256") or len(files) != export_seal.get(
        "file_count"
    ):
        raise RoutingSuiteError("routing export aggregate seal differs")
    return {
        "experiment_id": plan.experiment_id,
        "file_count": len(files),
        "export_sha256": value,
    }


def verify_routing_s1_nonlive_export(export_root: Path) -> dict[str, Any]:
    return _verify_routing_nonlive_export(
        export_root,
        expected_stage_id="s1-baseline",
    )


def verify_routing_s2_nonlive_export(export_root: Path) -> dict[str, Any]:
    return _verify_routing_nonlive_export(
        export_root,
        expected_stage_id="s2-intermediate",
    )


def verify_routing_s3_nonlive_export(export_root: Path) -> dict[str, Any]:
    return _verify_routing_nonlive_export(
        export_root,
        expected_stage_id="s3-complex-high-risk",
    )
