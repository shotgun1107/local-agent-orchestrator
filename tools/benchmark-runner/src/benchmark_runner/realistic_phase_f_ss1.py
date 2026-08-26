"""Profile R SS1 backend assembly for the first Phase F Cell.

The module joins already-versioned boundaries: the Profile R Worker snapshot,
the Phase C SS1 adapter, an injected SDK runtime, and the Phase F one-Cell
controller result.  It does not run the Judge and does not create a runtime by
itself.  Model-free tests inject :class:`FakeSdkRuntime`; a future live caller
must inject runtime-contract-v2 and a real boundary telemetry implementation.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from jsonschema import Draft202012Validator
from pydantic import JsonValue

from benchmark_runner.adapter import CellContext
from benchmark_runner.contract import present_api_key_environment_names
from benchmark_runner.realistic_phase_f import (
    PhaseFBackendResult,
    PhaseFDispatchRequest,
    PhaseFRuntimeMode,
)
from benchmark_runner.realistic_routing import (
    BoundaryAccessObservation,
    ChangedPath,
    EvidenceReference,
    PassiveBoundaryInput,
    PassiveBoundaryObservation,
    ProtectedFileObservation,
    SecretScanObservation,
    Ss1TaskRequest,
    build_ss1_worker_contract,
    canonical_json_bytes,
    canonical_sha256,
)
from benchmark_runner.workspace import build_hermetic_git_environment
from benchmark_runner.runner import sha256_bytes
from benchmark_runner.sdk_baselines import (
    SS1ObserverContext,
    SS1PersistentAdapter,
    SS1PersistentConfig,
)
from benchmark_runner.sdk_common import SdkRuntime, SdkThread, SdkTurnResult, WorkerContract
from benchmark_runner.workspace import (
    BenchmarkRun,
    RunTask,
    git_environment_provenance,
    load_benchmark_run,
    path_matches_write_scope,
    sha256_file,
)


PROFILE_R_FIXTURE_ID = "realistic-compat-migration-001"
PROFILE_R_WORKER_RELATIVE = (
    "benchmarks/fixtures/routing-realistic-high-difficulty-v1/"
    "realistic-compat-migration-001/workspace"
)
PROFILE_R_WORKER_MANIFEST_RELATIVE = (
    "benchmarks/fixtures/routing-realistic-high-difficulty-v1/"
    "realistic-compat-migration-001/worker-snapshot-manifest.json"
)
PROFILE_R_SOLUTION_CATALOG_RELATIVE = (
    "benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/"
    "realistic-compat-migration-001/solution-leakage-catalog.json"
)
PROFILE_R_RESULT_SCHEMA_RELATIVE = (
    "stages/b1-sequential/schemas/v1/result-envelope.schema.json"
)
PROFILE_R_EXPECTED_TASK_IDS = tuple(f"R{number:02d}" for number in range(1, 14))
PROFILE_R_PROTECTED_SCOPES = (
    ".orchestrator/**",
    "benchmark_checks/**",
    "profile-r/requirements/**",
    "README.md",
    "benchmark-run.yaml",
)
PHASE_F_SS1_EVIDENCE_FILENAME = "ss1-adapter-evidence.json"
MISSING_PATH_SHA256 = hashlib.sha256(b"phase-f-missing-path-v1").hexdigest()


class PhaseFSS1BackendError(RuntimeError):
    """Raised before a result is accepted across the Profile R SS1 boundary."""


@dataclass(frozen=True)
class PhaseFBoundarySignals:
    """Controller-side observations unavailable in the Worker prompt."""

    secret_scan: SecretScanObservation
    judge_access: BoundaryAccessObservation
    state_access: BoundaryAccessObservation


class PhaseFBoundaryTelemetry(Protocol):
    def observe_task(
        self,
        task_id: str,
        *,
        changed_paths: tuple[str, ...],
    ) -> PhaseFBoundarySignals: ...

    def observe(
        self,
        context: SS1ObserverContext,
        *,
        changed_paths: tuple[str, ...],
    ) -> PhaseFBoundarySignals: ...


class ModelFreeClearBoundaryTelemetry:
    """Explicit fake-only telemetry used by contract tests, never live Cells."""

    def observe_task(
        self,
        task_id: str,
        *,
        changed_paths: tuple[str, ...],
    ) -> PhaseFBoundarySignals:
        del task_id, changed_paths
        return PhaseFBoundarySignals(
            secret_scan=SecretScanObservation(status="clear", finding_ids=[]),
            judge_access=BoundaryAccessObservation(status="clear", event_ids=[]),
            state_access=BoundaryAccessObservation(status="clear", event_ids=[]),
        )

    def observe(
        self,
        context: SS1ObserverContext,
        *,
        changed_paths: tuple[str, ...],
    ) -> PhaseFBoundarySignals:
        return self.observe_task(
            context.task.task_id,
            changed_paths=changed_paths,
        )


RuntimeFactory = Callable[[Path], SdkRuntime]


def _workspace_files(root: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in root.rglob("*")
            if path.is_file()
            and not {".git", ".pytest_cache", "__pycache__"}.intersection(
                path.relative_to(root).parts
            )
        ),
        key=lambda path: path.relative_to(root).as_posix().encode("utf-8"),
    )


def _file_state(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in _workspace_files(root)
    }


def _tree_sha256(state: Mapping[str, str]) -> str:
    payload = "".join(
        f"{digest}  {path}\n"
        for path, digest in sorted(
            state.items(), key=lambda item: item[0].encode("utf-8")
        )
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _write_new(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _run_git(
    workspace: Path,
    git_executable: Path,
    environment: Mapping[str, str],
    *arguments: str,
) -> None:
    result = subprocess.run(
        [
            str(git_executable),
            "-C",
            str(workspace),
            *arguments,
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=dict(environment),
    )
    if result.returncode != 0:
        raise PhaseFSS1BackendError(
            f"Profile R workspace git {' '.join(arguments)} failed"
        )


def materialize_profile_r_workspace(
    repository: Path,
    target: Path,
    *,
    git_executable: Path | None = None,
    source_environment: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Copy the exact committed Worker manifest into a fresh Git workspace."""

    repository = repository.resolve()
    target = target.resolve()
    source_env = dict(os.environ if source_environment is None else source_environment)
    candidate_git = git_executable
    if candidate_git is None:
        discovered = shutil.which("git", path=source_env.get("PATH"))
        if not discovered:
            raise PhaseFSS1BackendError("Profile R Git executable is unavailable")
        candidate_git = Path(discovered)
    resolved_git = Path(candidate_git).resolve(strict=True)
    source = repository / PROFILE_R_WORKER_RELATIVE
    manifest_path = repository / PROFILE_R_WORKER_MANIFEST_RELATIVE
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = manifest.get("files")
    if (
        manifest.get("snapshot_id") != PROFILE_R_FIXTURE_ID
        or manifest.get("status") != "ANONYMIZED_WORKER_TASK_PACK_CANDIDATE"
        or not isinstance(records, list)
    ):
        raise PhaseFSS1BackendError("Profile R Worker manifest identity differs")
    if target.exists():
        raise PhaseFSS1BackendError("Profile R Worker target already exists")
    target.mkdir(parents=True, exist_ok=False)
    seen: set[str] = set()
    seen_platform: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise PhaseFSS1BackendError("Profile R Worker manifest entry is invalid")
        relative = record.get("path")
        expected_sha256 = record.get("worker_sha256")
        if not isinstance(relative, str) or not isinstance(expected_sha256, str):
            raise PhaseFSS1BackendError("Profile R Worker manifest path/hash is invalid")
        path = Path(relative)
        if (
            path.is_absolute()
            or "\\" in relative
            or any(part in {"", ".", ".."} for part in path.parts)
        ):
            raise PhaseFSS1BackendError("Profile R Worker path is unsafe")
        platform_key = relative.casefold() if os.name == "nt" else relative
        if relative in seen or platform_key in seen_platform:
            raise PhaseFSS1BackendError("Profile R Worker path is duplicated")
        seen.add(relative)
        seen_platform.add(platform_key)
        source_path = source / path
        if not source_path.is_file() or source_path.is_symlink():
            raise PhaseFSS1BackendError("Profile R Worker source file is unavailable")
        payload = source_path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != expected_sha256:
            raise PhaseFSS1BackendError("Profile R Worker source hash differs")
        _write_new(target / path, payload)
    if len(records) != manifest.get("file_count") or set(_file_state(target)) != seen:
        raise PhaseFSS1BackendError("Profile R Worker file set differs")
    git_environment = build_hermetic_git_environment(
        git_executable=resolved_git,
        home=target,
        source_environment=source_env,
        additions={
            "GIT_AUTHOR_NAME": "Phase F Fixture",
            "GIT_AUTHOR_EMAIL": "phase-f-fixture@example.invalid",
            "GIT_COMMITTER_NAME": "Phase F Fixture",
            "GIT_COMMITTER_EMAIL": "phase-f-fixture@example.invalid",
        },
    )
    _run_git(target, resolved_git, git_environment, "init", "-q")
    _run_git(
        target,
        resolved_git,
        git_environment,
        "config",
        "core.longpaths",
        "true",
    )
    _run_git(
        target,
        resolved_git,
        git_environment,
        "config",
        "core.autocrlf",
        "false",
    )
    _run_git(target, resolved_git, git_environment, "add", "--all")
    _run_git(
        target,
        resolved_git,
        git_environment,
        "commit",
        "-q",
        "-m",
        "Profile R Worker baseline",
    )
    return manifest


def _base_worker_contract(workspace: Path) -> WorkerContract:
    schema = json.loads(
        (workspace / PROFILE_R_RESULT_SCHEMA_RELATIVE).read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    def validate(value: Any) -> dict[str, JsonValue]:
        validator.validate(value)
        if not isinstance(value, dict):
            raise ValueError("ResultEnvelope must be an object")
        return json.loads(json.dumps(value))

    return WorkerContract(
        render_prompt=lambda value: str(value),
        result_schema=lambda: json.loads(json.dumps(schema)),
        validate_result=validate,
        semantics_sha256=canonical_sha256,
    )


def _transitive_dependencies(run: BenchmarkRun, task: RunTask) -> set[str]:
    by_id = {item.key: item for item in run.tasks}
    result: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in result:
            return
        result.add(task_id)
        for predecessor in by_id[task_id].depends_on:
            visit(predecessor)

    for predecessor in task.depends_on:
        visit(predecessor)
    return result


def build_profile_r_ss1_tasks(workspace: Path) -> tuple[Ss1TaskRequest, ...]:
    """Compile the public 13-Task pack without Controller Check fields."""

    run = load_benchmark_run(workspace / "benchmark-run.yaml")
    if tuple(task.key for task in run.tasks) != PROFILE_R_EXPECTED_TASK_IDS:
        raise PhaseFSS1BackendError("Profile R public Task order differs")
    by_id = {task.key: task for task in run.tasks}
    compiled: list[Ss1TaskRequest] = []
    for task in run.tasks:
        predecessors = _transitive_dependencies(run, task)
        predecessor_scopes = tuple(
            scope
            for predecessor in predecessors
            for scope in by_id[predecessor].write_scope
        )
        declared: list[EvidenceReference] = []
        predecessor_artifacts: list[EvidenceReference] = []
        for raw_input in task.inputs:
            if not isinstance(raw_input, dict) or set(raw_input) != {"path"}:
                raise PhaseFSS1BackendError("Profile R public Task input is invalid")
            relative = raw_input.get("path")
            if not isinstance(relative, str):
                raise PhaseFSS1BackendError("Profile R public Task input path is invalid")
            source = workspace / relative
            is_predecessor = any(
                path_matches_write_scope(relative, scope)
                for scope in predecessor_scopes
            )
            if not source.is_file() and not is_predecessor:
                raise PhaseFSS1BackendError("Profile R declared Task input is missing")
            reference = EvidenceReference(
                path=relative,
                sha256=(sha256_file(source) if source.is_file() else MISSING_PATH_SHA256),
            )
            if is_predecessor:
                predecessor_artifacts.append(reference)
            else:
                declared.append(reference)
        criteria = []
        for criterion in task.completion_criteria:
            text = criterion.get("text")
            if not isinstance(text, str) or not text:
                raise PhaseFSS1BackendError("Profile R completion criterion is invalid")
            criteria.append(text)
        compiled.append(
            Ss1TaskRequest(
                task_id=task.key,
                goal=task.goal,
                completion_criteria=criteria,
                declared_inputs=sorted(declared, key=lambda item: item.path),
                predecessor_artifacts=sorted(
                    predecessor_artifacts, key=lambda item: item.path
                ),
                read_scope=sorted(set(task.read_scope)),
                write_scope=sorted(set(task.write_scope)),
            )
        )
    return tuple(compiled)


def refresh_profile_r_ss1_task(
    workspace: Path,
    task: Ss1TaskRequest,
) -> Ss1TaskRequest:
    """Bind one Task's public evidence hashes immediately before dispatch."""

    def refresh(values: Iterable[EvidenceReference]) -> list[EvidenceReference]:
        refreshed: list[EvidenceReference] = []
        for value in values:
            path = workspace / value.path
            if not path.is_file():
                raise PhaseFSS1BackendError(
                    f"Profile R Task input is unavailable at dispatch: {value.path}"
                )
            refreshed.append(EvidenceReference(path=value.path, sha256=sha256_file(path)))
        return refreshed

    return task.model_copy(
        update={
            "declared_inputs": refresh(task.declared_inputs),
            "predecessor_artifacts": refresh(task.predecessor_artifacts),
        }
    )


@dataclass(frozen=True)
class _TurnWorkspaceRecord:
    task_id: str
    before: Mapping[str, str]
    after: Mapping[str, str]


class _WorkspaceTrackingRuntime:
    def __init__(self, workspace: Path, delegate: SdkRuntime) -> None:
        self.workspace = workspace
        self.delegate = delegate
        self.records: list[_TurnWorkspaceRecord] = []

    @property
    def actual_model_turns(self) -> int | None:
        value = getattr(self.delegate, "actual_model_turns", None)
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    def preflight(self) -> None:
        self.delegate.preflight()

    def start_thread(self) -> SdkThread:
        return self.delegate.start_thread()

    def run_turn(
        self,
        thread: SdkThread,
        *,
        task_id: str,
        prompt: str,
        output_schema: dict[str, Any],
    ) -> SdkTurnResult:
        before = _file_state(self.workspace)
        result = self.delegate.run_turn(
            thread,
            task_id=task_id,
            prompt=prompt,
            output_schema=output_schema,
        )
        after = _file_state(self.workspace)
        self.records.append(_TurnWorkspaceRecord(task_id, before, after))
        return result

    def close(self) -> None:
        self.delegate.close()


class _ProfileRObserver:
    def __init__(
        self,
        workspace: Path,
        tracking_runtime: _WorkspaceTrackingRuntime,
        tasks: Iterable[Ss1TaskRequest],
        telemetry: PhaseFBoundaryTelemetry,
    ) -> None:
        self.workspace = workspace
        self.tracking_runtime = tracking_runtime
        self.telemetry = telemetry
        self.run_write_scopes = tuple(
            scope for task in tasks for scope in task.write_scope
        )
        self.next_record = 0
        self.implementation_sha256 = sha256_file(Path(__file__))

    @staticmethod
    def _matches(path: str, scopes: Iterable[str]) -> bool:
        return any(path_matches_write_scope(path, scope) for scope in scopes)

    def __call__(self, context: SS1ObserverContext) -> PassiveBoundaryObservation:
        if self.next_record >= len(self.tracking_runtime.records):
            raise PhaseFSS1BackendError("Profile R observer has no terminal snapshot")
        record = self.tracking_runtime.records[self.next_record]
        self.next_record += 1
        if record.task_id != context.task.task_id:
            raise PhaseFSS1BackendError("Profile R observer Task identity differs")
        return build_profile_r_boundary_observation(
            task=context.task,
            before=record.before,
            after=record.after,
            run_write_scopes=self.run_write_scopes,
            telemetry=self.telemetry,
            observer_implementation_sha256=self.implementation_sha256,
        )


def build_profile_r_boundary_observation(
    *,
    task: Ss1TaskRequest,
    before: Mapping[str, str],
    after: Mapping[str, str],
    run_write_scopes: Iterable[str],
    telemetry: PhaseFBoundaryTelemetry,
    observer_implementation_sha256: str,
) -> PassiveBoundaryObservation:
    """Build the identical passive observation used by SS1 and B1."""

    paths = sorted(
        set(before) | set(after), key=lambda value: value.encode("utf-8")
    )
    changed = tuple(path for path in paths if before.get(path) != after.get(path))
    changed_models = [
        ChangedPath(
            path=path,
            change_kind=(
                "added"
                if path not in before
                else "deleted"
                if path not in after
                else "modified"
            ),
        )
        for path in changed
    ]
    protected_paths = sorted(
        {
            path
            for path in paths
            if any(
                path_matches_write_scope(path, scope)
                for scope in PROFILE_R_PROTECTED_SCOPES
            )
        },
        key=lambda value: value.encode("utf-8"),
    )
    protected = [
        ProtectedFileObservation(
            path=path,
            before_sha256=before.get(path, MISSING_PATH_SHA256),
            after_sha256=after.get(path, MISSING_PATH_SHA256),
            changed=before.get(path) != after.get(path),
        )
        for path in protected_paths
    ]
    signals = telemetry.observe_task(task.task_id, changed_paths=changed)
    run_scopes = tuple(run_write_scopes)
    return PassiveBoundaryObservation.from_input(
        PassiveBoundaryInput(
            declared_read_scope=task.read_scope,
            declared_write_scope=task.write_scope,
            changed_paths=changed_models,
            outside_task_scope_paths=[
                path
                for path in changed
                if not any(
                    path_matches_write_scope(path, scope)
                    for scope in task.write_scope
                )
            ],
            outside_run_scope_paths=[
                path
                for path in changed
                if not any(
                    path_matches_write_scope(path, scope) for scope in run_scopes
                )
            ],
            protected_files=protected,
            declared_inputs=task.declared_inputs,
            predecessor_artifacts=task.predecessor_artifacts,
            workspace_tree_before_sha256=_tree_sha256(before),
            workspace_tree_after_sha256=_tree_sha256(after),
            secret_scan=signals.secret_scan,
            judge_access=signals.judge_access,
            state_access=signals.state_access,
            observer_implementation_sha256=observer_implementation_sha256,
        )
    )


def _forbidden_prompt_fragments(repository: Path) -> tuple[str, ...]:
    catalog = json.loads(
        (repository / PROFILE_R_SOLUTION_CATALOG_RELATIVE).read_text(encoding="utf-8")
    )
    values = catalog.get("forbidden_worker_literals")
    if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
        raise PhaseFSS1BackendError("Profile R leakage catalog is invalid")
    return tuple(values)


class ProfileRPhaseFSS1Backend:
    """Run exactly Profile R/SS1 Cell 1 through existing Phase C machinery."""

    evidence_filename = PHASE_F_SS1_EVIDENCE_FILENAME

    def __init__(
        self,
        *,
        repository: Path,
        artifact_root: Path,
        runtime_mode: PhaseFRuntimeMode,
        runtime_factory: RuntimeFactory,
        telemetry: PhaseFBoundaryTelemetry,
        environ: Mapping[str, str] | None = None,
        git_executable: Path | None = None,
        source_environment: Mapping[str, str] | None = None,
    ) -> None:
        self.repository = repository.resolve()
        self.artifact_root = artifact_root.resolve()
        self.runtime_mode = PhaseFRuntimeMode(runtime_mode)
        self.runtime_factory = runtime_factory
        self.telemetry = telemetry
        self.environ = environ
        self.git_executable = git_executable
        self.source_environment = source_environment
        if (
            self.runtime_mode is PhaseFRuntimeMode.LIVE_CHATGPT
            and isinstance(telemetry, ModelFreeClearBoundaryTelemetry)
        ):
            raise PhaseFSS1BackendError("live Phase F cannot use fake clear telemetry")

    def run_one_cell(self, request: PhaseFDispatchRequest) -> PhaseFBackendResult:
        if present_api_key_environment_names(self.environ):
            raise PhaseFSS1BackendError("API key environment names are present")
        if request.runtime_mode is not self.runtime_mode:
            raise PhaseFSS1BackendError("Phase F backend/request runtime mode differs")
        if (
            request.execution_ordinal != 1
            or request.fixture_id != PROFILE_R_FIXTURE_ID
            or request.variant_id != "ss1"
        ):
            raise PhaseFSS1BackendError("Profile R SS1 backend accepts only Cell 1")
        cell_root = self.artifact_root / request.cell_id
        if cell_root.exists():
            raise PhaseFSS1BackendError("Profile R SS1 backend Cell already exists")
        cell_root.mkdir(parents=True, exist_ok=False)
        workspace = cell_root / "workspace"
        materialize_profile_r_workspace(
            self.repository,
            workspace,
            git_executable=self.git_executable,
            source_environment=self.source_environment,
        )
        git_provenance = git_environment_provenance(
            workspace=workspace,
            git_executable=self.git_executable,
            source_environment=(
                None
                if self.source_environment is None
                else dict(self.source_environment)
            ),
        )
        initial_worker_tree_sha256 = _tree_sha256(_file_state(workspace))
        tasks = build_profile_r_ss1_tasks(workspace)
        forbidden_fragments = _forbidden_prompt_fragments(self.repository)
        delegate = self.runtime_factory(workspace)
        tracking_runtime = _WorkspaceTrackingRuntime(workspace, delegate)
        observer = _ProfileRObserver(
            workspace,
            tracking_runtime,
            tasks,
            self.telemetry,
        )
        contract = build_ss1_worker_contract(
            _base_worker_contract(workspace),
            forbidden_prompt_fragments=forbidden_fragments,
        )
        adapter = SS1PersistentAdapter(
            SS1PersistentConfig(
                tasks=tasks,
                contract=contract,
                runtime=tracking_runtime,
                observer=observer,
                task_resolver=lambda task: refresh_profile_r_ss1_task(
                    workspace, task
                ),
                forbidden_prompt_fragments=forbidden_fragments,
            )
        )
        evidence = adapter.run(CellContext(request.experiment_id, request.cell_id))
        actual_model_turns = tracking_runtime.actual_model_turns
        if actual_model_turns is None:
            raise PhaseFSS1BackendError("Phase F runtime did not report model turns")
        if self.runtime_mode is PhaseFRuntimeMode.MODEL_FREE_FAKE:
            actual_model_turns = 0
        turns = evidence.raw_payload.get("turns")
        if not isinstance(turns, list):
            raise PhaseFSS1BackendError("SS1 adapter turn Evidence is unavailable")
        initial_turns = [
            turn
            for turn in turns
            if isinstance(turn, dict) and turn.get("turn_kind") == "initial"
        ]
        dispatched_task_semantics = [
            turn.get("task_semantics_sha256") for turn in initial_turns
        ]
        dispatched_task_ids = [turn.get("task_id") for turn in initial_turns]
        expected_task_prefix = [
            task.task_id for task in tasks[: len(initial_turns)]
        ]
        if (
            len(initial_turns) > len(tasks)
            or (
                str(evidence.outcome_state) == "completed"
                and len(initial_turns) != len(tasks)
            )
            or dispatched_task_ids != expected_task_prefix
            or any(not isinstance(value, str) for value in dispatched_task_semantics)
        ):
            raise PhaseFSS1BackendError("SS1 initial Task semantics Evidence differs")
        evidence_payload: dict[str, JsonValue] = {
            "schema_version": 1,
            "kind": "phase_f_profile_r_ss1_adapter_evidence",
            "experiment_id": request.experiment_id,
            "cell_id": request.cell_id,
            "request_sha256": request.request_sha256,
            "fixture_id": request.fixture_id,
            "variant_id": request.variant_id,
            "runtime_mode": self.runtime_mode.value,
            "worker_manifest_sha256": sha256_file(
                self.repository / PROFILE_R_WORKER_MANIFEST_RELATIVE
            ),
            "worker_tree_initial_sha256": initial_worker_tree_sha256,
            "worker_tree_final_sha256": _tree_sha256(_file_state(workspace)),
            "git_provenance": git_provenance,
            "task_count": len(tasks),
            "task_template_sha256": [canonical_sha256(task) for task in tasks],
            "dispatched_task_semantics_sha256": dispatched_task_semantics,
            "actual_model_turns": actual_model_turns,
            "adapter_outcome_state": str(evidence.outcome_state),
            "adapter_failure_kind": evidence.failure_kind,
            "adapter_attempt_count": evidence.attempt_count,
            "adapter_raw_payload": evidence.raw_payload,
            "adapter_normalized_metrics": evidence.normalized_metrics,
            "judge_executed": False,
            "automatic_continuation": False,
        }
        evidence_bytes = canonical_json_bytes(evidence_payload)
        evidence_path = cell_root / PHASE_F_SS1_EVIDENCE_FILENAME
        _write_new(evidence_path, evidence_bytes)
        return PhaseFBackendResult(
            experiment_id=request.experiment_id,
            plan_fingerprint=request.plan_fingerprint,
            execution_ordinal=request.execution_ordinal,
            cell_id=request.cell_id,
            fixture_id=request.fixture_id,
            variant_id=request.variant_id,
            runtime_mode=self.runtime_mode,
            request_sha256=request.request_sha256,
            outcome_state=str(evidence.outcome_state),
            actual_model_turns=actual_model_turns,
            sealed_artifact_sha256=sha256_bytes(evidence_bytes),
            public_summary={
                "task_count": len(tasks),
                "turn_count": evidence.normalized_metrics.get("turn_count", 0),
                "session_count": evidence.normalized_metrics.get("session_count", 0),
                "boundary_record_count": len(
                    evidence.raw_payload.get("boundary_records", [])
                ),
                "judge_executed": False,
                "automatic_continuation": False,
            },
        )
