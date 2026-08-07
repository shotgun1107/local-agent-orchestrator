"""Manifest-driven, model-free vertical slice for SDK routing suite v1."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Literal

import yaml
from pydantic import Field, field_validator, model_validator

from benchmark_runner.adapter import VariantAdapter
from benchmark_runner.contract import (
    ArtifactIdentity,
    ExecutionPlan,
    FixtureIdentity,
    PlannedCell,
    StrictModel,
    validate_relative_path,
)
from benchmark_runner.plan import build_sdk_controlled_plan
from benchmark_runner.sdk_cells import (
    SdkSealedCellResult,
    initialize_sdk_experiment,
    run_sdk_nonlive_cell,
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


class RoutingCellDeclaration(StrictModel):
    fixture_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    variant_id: Literal["c2", "b1"]
    repetition: Literal[1] = 1


class RoutingStageManifest(StrictModel):
    schema_version: Literal[1]
    stage_id: Literal["s1-baseline"]
    status: Literal["implementation_candidate", "frozen_before_execution"]
    purpose: Literal["calibration_only"]
    fixture_manifests: list[FixtureManifestSelection] = Field(min_length=1)
    variants: list[Literal["c2", "b1"]] = Field(min_length=2, max_length=2)
    baseline_variant: Literal["c2"]
    candidate_variants: list[Literal["b1"]] = Field(min_length=1, max_length=1)
    profiles: list[FixtureProfileDeclaration] = Field(min_length=1)
    cells: list[RoutingCellDeclaration] = Field(min_length=1)
    planned_live_model_turns: int = Field(ge=1)
    allowed_outcomes: list[
        Literal[
            "CALIBRATION_PASS",
            "CALIBRATION_STOP",
            "CALIBRATION_INCONCLUSIVE",
        ]
    ] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def stage_contract_is_consistent(self) -> RoutingStageManifest:
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
        return self


class RoutingStageReference(StrictModel):
    stage_id: Literal["s1-baseline"]
    path: str

    _path_is_relative = field_validator("path")(validate_relative_path)


class RoutingSuiteManifest(StrictModel):
    schema_version: Literal[1]
    suite_id: Literal["sdk-routing-v1"]
    design_revision: Literal[2]
    status: Literal["implementation_candidate", "frozen_before_execution"]
    stages: list[RoutingStageReference] = Field(min_length=1)
    live_turn_ceiling_including_pilot: Literal[31]
    auth_method: Literal["chatgpt"]
    api_key_policy: Literal["forbidden"]

    @model_validator(mode="after")
    def stage_ids_are_unique(self) -> RoutingSuiteManifest:
        stage_ids = [stage.stage_id for stage in self.stages]
        if len(stage_ids) != len(set(stage_ids)):
            raise ValueError("routing suite stage IDs must be unique")
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


def load_routing_stage(path: Path) -> RoutingStageManifest:
    return RoutingStageManifest.model_validate(_load_yaml(path))


def _git(repository: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repository), *args],
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
    repository_root = repository_root.resolve()
    suite_path = suite_path.resolve()
    stage_path = stage_path.resolve()
    suite, stage = _resolve_stage(repository_root, suite_path, stage_path)
    fixtures = _fixture_specs(repository_root, stage)
    profiles = _verified_profiles(repository_root, stage, fixtures)
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
            "planned_live_model_turns": stage.planned_live_model_turns,
            "route_decision_allowed": False,
            "profiles": {
                fixture_id: profile.model_dump(mode="json")
                for fixture_id, profile in profiles.items()
            },
        },
        environment_fingerprint=environment_fingerprint,
        created_at=created_at,
        revision=revision,
        seed=0,
        track="sdk_routing_s1_model_free_validation",
        planned_actual_model_turns=0,
    )


def initialize_routing_s1_experiment(
    state_root: Path,
    plan: ExecutionPlan,
) -> Path:
    return initialize_sdk_experiment(state_root, plan)


AdapterFactory = Callable[[PlannedCell, PreparedFixture], VariantAdapter]


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
        or plan.decision_policy.get("route_decision_allowed") is not False
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
    return run_sdk_nonlive_cell(
        experiment_dir=experiment_dir,
        plan=plan,
        planned_cell=next_cell,
        prepared=prepared,
        adapter=adapter,
        benchmark_python=benchmark_python,
        git_executable=git_executable,
    )
