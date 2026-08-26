"""Public contracts, enums, identifiers, and configuration validation for B1."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

CORE_VERSION = "0.1.0"
SCHEMA_VERSION = 1
ID_PREFIXES = {
    "run",
    "task",
    "attempt",
    "session",
    "artifact",
    "check",
    "decision",
    "event",
}
TASK_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_-]{0,31}$")
PROJECT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")


class ContractError(ValueError):
    """Raised when a public contract violates a B1 invariant."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RunState(StrEnum):
    DRAFT = "DRAFT"
    READY = "READY"
    RUNNING = "RUNNING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


class TaskState(StrEnum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    REPORTED = "REPORTED"
    VERIFYING = "VERIFYING"
    SUCCEEDED = "SUCCEEDED"
    RETRYABLE_FAILED = "RETRYABLE_FAILED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    SUPERSEDED = "SUPERSEDED"


class AttemptState(StrEnum):
    CREATED = "CREATED"
    DISPATCHING = "DISPATCHING"
    RUNNING = "RUNNING"
    REPORTED = "REPORTED"
    VERIFYING = "VERIFYING"
    SUCCEEDED = "SUCCEEDED"
    RETRYABLE_FAILED = "RETRYABLE_FAILED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"
    QUARANTINED = "QUARANTINED"
    DISPATCH_UNCERTAIN = "DISPATCH_UNCERTAIN"


class SessionState(StrEnum):
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    INTERRUPTING = "INTERRUPTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"
    QUARANTINED = "QUARANTINED"


class CheckState(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


class CheckFailureClassification(StrEnum):
    PRODUCT_ASSERTION = "PRODUCT_ASSERTION"
    ENVIRONMENT = "ENVIRONMENT"
    MIXED_PRODUCT_AND_ENVIRONMENT = "MIXED_PRODUCT_AND_ENVIRONMENT"
    UNKNOWN = "UNKNOWN"


class CheckDiagnosticNode(StrictModel):
    node_id: str = Field(min_length=1)
    classification: CheckFailureClassification | None
    passed: bool
    reason_code: str = Field(pattern=r"^[A-Z][A-Z0-9_]{0,95}$")

    @model_validator(mode="after")
    def failure_requires_classification(self) -> "CheckDiagnosticNode":
        if self.passed != (self.classification is None):
            raise ValueError(
                "passed diagnostic nodes must omit classification and failed nodes must set it"
            )
        if self.classification == CheckFailureClassification.MIXED_PRODUCT_AND_ENVIRONMENT:
            raise ValueError("mixed classification is aggregate-only")
        return self


class CheckDiagnosticResult(StrictModel):
    schema_version: Literal[1]
    task_id: str = Field(min_length=1)
    classification: CheckFailureClassification | None
    comparison_valid: bool
    product_failure_present: bool
    environment_failure_present: bool
    nodes: list[CheckDiagnosticNode]

    @model_validator(mode="after")
    def aggregate_matches_nodes(self) -> "CheckDiagnosticResult":
        failed = {
            node.classification for node in self.nodes if not node.passed
        }
        if not failed:
            expected = None
        elif failed == {CheckFailureClassification.PRODUCT_ASSERTION}:
            expected = CheckFailureClassification.PRODUCT_ASSERTION
        elif failed == {CheckFailureClassification.ENVIRONMENT}:
            expected = CheckFailureClassification.ENVIRONMENT
        elif {
            CheckFailureClassification.PRODUCT_ASSERTION,
            CheckFailureClassification.ENVIRONMENT,
        } <= failed:
            expected = CheckFailureClassification.MIXED_PRODUCT_AND_ENVIRONMENT
        else:
            expected = CheckFailureClassification.UNKNOWN
        if self.classification != expected:
            raise ValueError("diagnostic aggregate classification differs from nodes")
        if self.product_failure_present != (
            CheckFailureClassification.PRODUCT_ASSERTION in failed
        ):
            raise ValueError("diagnostic product failure flag differs")
        if self.environment_failure_present != (
            CheckFailureClassification.ENVIRONMENT in failed
        ):
            raise ValueError("diagnostic environment failure flag differs")
        if self.comparison_valid != (
            expected
            in {None, CheckFailureClassification.PRODUCT_ASSERTION}
        ):
            raise ValueError("diagnostic comparison validity differs")
        return self


class WorkspaceMode(StrEnum):
    READ_ONLY = "read_only"
    SHARED_SERIAL_WRITE = "shared_serial_write"


class SandboxMode(StrEnum):
    READ_ONLY = "read_only"
    WORKSPACE_WRITE = "workspace_write"


class UsageStatus(StrEnum):
    MEASURED = "measured"
    UNKNOWN = "unknown"
    UNSUPPORTED = "unsupported"


class ReportUsageStatus(StrEnum):
    MEASURED = "measured"
    PARTIAL_OR_UNKNOWN = "partial_or_unknown"


class TerminalStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class StatusClaim(StrEnum):
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


class FailureKind(StrEnum):
    TRANSIENT_RUNTIME = "transient_runtime"
    RUNTIME_UNKNOWN = "runtime_unknown"
    MALFORMED_RESULT = "malformed_result"
    CHECK_FAILED = "check_failed"
    CHECK_ENVIRONMENT = "check_environment"
    CHECK_MIXED = "check_mixed"
    CHECK_UNKNOWN = "check_unknown"
    STALE_INPUT = "stale_input"
    SCOPE_VIOLATION = "scope_violation"
    TIMEOUT = "timeout"
    DISPATCH_UNCERTAIN = "dispatch_uncertain"
    TERMINAL_UNKNOWN = "terminal_unknown"
    ARTIFACT_CORRUPT = "artifact_corrupt"
    INTERNAL = "internal"


class InterruptState(StrEnum):
    NOT_REQUESTED = "not_requested"
    REQUESTED = "requested"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def new_id(prefix: str) -> str:
    if prefix not in ID_PREFIXES:
        raise ContractError(f"unsupported id prefix: {prefix}")
    return f"{prefix}_{uuid.uuid4().hex}"


def canonical_json(value: Any) -> str:
    def jsonable(item: Any) -> Any:
        if isinstance(item, BaseModel):
            return jsonable(item.model_dump(mode="json"))
        if isinstance(item, dict):
            return {str(key): jsonable(nested) for key, nested in item.items()}
        if isinstance(item, (list, tuple, set)):
            return [jsonable(nested) for nested in item]
        if isinstance(item, StrEnum):
            return item.value
        return item

    return json.dumps(jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def validate_relative_path(value: str, *, allow_glob: bool = False) -> str:
    if not value or "\\" in value:
        raise ValueError("path must be a non-empty POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("absolute paths and '..' are forbidden")
    if not allow_glob and any(ch in value for ch in "*?[]"):
        raise ValueError("globs are not allowed here")
    return value


def validate_scope(value: str, *, writable: bool) -> str:
    value = validate_relative_path(value, allow_glob=True)
    first = PurePosixPath(value).parts[0] if PurePosixPath(value).parts else ""
    if writable and first in {".git", ".orchestrator"}:
        raise ValueError("writes to .git/** and .orchestrator/** are forbidden")
    return value


class RequestSpec(StrictModel):
    source: str = Field(min_length=1)
    text: str = Field(min_length=1)


class RunCriterion(StrictModel):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    satisfied_by_tasks: list[str] = Field(min_length=1)


class TaskCriterion(StrictModel):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    check_names: list[str] = Field(min_length=1)


class InputRef(StrictModel):
    artifact_id: str | None = None
    path: str
    sha256: str | None = None

    @field_validator("path")
    @classmethod
    def _path(cls, value: str) -> str:
        return validate_relative_path(value)


class TaskSpec(StrictModel):
    key: str
    goal: str = Field(min_length=1)
    completion_criteria: list[TaskCriterion] = Field(min_length=1)
    depends_on: list[str] = Field(default_factory=list)
    inputs: list[InputRef] = Field(default_factory=list)
    read_scope: list[str] = Field(min_length=1)
    write_scope: list[str] = Field(default_factory=list)
    capability_profile: str = Field(min_length=1)
    workspace_mode: WorkspaceMode
    own_check: str | None = Field(default=None, min_length=1)
    check_names: list[str] = Field(min_length=1)
    approval: Literal["none"]

    @field_validator("key")
    @classmethod
    def _key(cls, value: str) -> str:
        if not TASK_KEY_RE.fullmatch(value):
            raise ValueError("invalid Task key")
        return value

    @field_validator("read_scope")
    @classmethod
    def _read_scope(cls, values: list[str]) -> list[str]:
        return [validate_scope(value, writable=False) for value in values]

    @field_validator("write_scope")
    @classmethod
    def _write_scope(cls, values: list[str]) -> list[str]:
        return [validate_scope(value, writable=True) for value in values]

    @model_validator(mode="after")
    def _workspace_invariants(self) -> "TaskSpec":
        if self.workspace_mode == WorkspaceMode.READ_ONLY and self.write_scope:
            raise ValueError("read_only tasks must have an empty write_scope")
        for criterion in self.completion_criteria:
            if not set(criterion.check_names).issubset(self.check_names):
                raise ValueError(f"criterion {criterion.id} references a check not assigned to the task")
        return self


class RunSpec(StrictModel):
    schema_version: Literal[1]
    request: RequestSpec
    completion_criteria: list[RunCriterion] = Field(min_length=1)
    constraints: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    tasks: list[TaskSpec] = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def derive_cumulative_checks(cls, value: Any) -> Any:
        if not isinstance(value, dict) or not isinstance(value.get("tasks"), list):
            return value
        tasks = value["tasks"]
        if not tasks or not all(isinstance(task, dict) for task in tasks):
            return value
        own_checks = [task.get("own_check") for task in tasks]
        if not any(own_checks):
            return value
        if not all(isinstance(item, str) and item for item in own_checks):
            raise ValueError("cumulative own_check declarations must be all-or-none")
        projected = [
            {
                **task,
                "check_names": [*own_checks[: index + 1], "diff_check"],
            }
            for index, task in enumerate(tasks)
        ]
        return {**value, "tasks": projected}

    @model_validator(mode="after")
    def _graph_invariants(self) -> "RunSpec":
        keys = [task.key for task in self.tasks]
        if len(keys) != len(set(keys)):
            raise ValueError("Task keys must be unique")
        known = set(keys)
        graph = {task.key: set(task.depends_on) for task in self.tasks}
        for key, dependencies in graph.items():
            missing = dependencies - known
            if missing:
                raise ValueError(f"Task {key} has missing dependencies: {sorted(missing)}")
            if key in dependencies:
                raise ValueError(f"Task {key} depends on itself")
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(key: str) -> None:
            if key in visiting:
                raise ValueError("Task dependency cycle detected")
            if key in visited:
                return
            visiting.add(key)
            for dependency in graph[key]:
                visit(dependency)
            visiting.remove(key)
            visited.add(key)

        for key in keys:
            visit(key)
        for criterion in self.completion_criteria:
            if not set(criterion.satisfied_by_tasks).issubset(known):
                raise ValueError(f"Run criterion {criterion.id} references an unknown Task")
        own_checks = [task.own_check for task in self.tasks]
        if any(value is not None for value in own_checks) and any(
            value is None for value in own_checks
        ):
            raise ValueError("cumulative own_check declarations must be all-or-none")
        for index, task in enumerate(self.tasks if all(own_checks) else []):
            expected_checks = [
                *(str(item.own_check) for item in self.tasks[: index + 1]),
                "diff_check",
            ]
            if task.check_names != expected_checks:
                raise ValueError(
                    f"Task {task.key} cumulative checks differ: "
                    f"expected {expected_checks}, got {task.check_names}"
                )
        return self


class ProjectConfig(StrictModel):
    schema_version: Literal[1]
    project_id: str
    core_compat: str
    repository_root: str
    default_capability_profile: str
    default_policy: str

    @field_validator("project_id")
    @classmethod
    def _project_id(cls, value: str) -> str:
        if not PROJECT_ID_RE.fullmatch(value):
            raise ValueError("invalid project_id")
        return value

    @field_validator("repository_root")
    @classmethod
    def _repository_root(cls, value: str) -> str:
        return validate_relative_path(value)

    @field_validator("core_compat")
    @classmethod
    def _core_compat(cls, value: str) -> str:
        if value != ">=0.1,<0.2":
            raise ValueError("B1 supports core_compat '>=0.1,<0.2' only")
        return value


class CapabilityProfile(StrictModel):
    runtime: Literal["fake", "codex"]
    runtime_profile: str
    sandbox: SandboxMode
    workspace_mode: WorkspaceMode


class CapabilitiesConfig(StrictModel):
    schema_version: Literal[1]
    profiles: dict[str, CapabilityProfile]


class Policy(StrictModel):
    max_concurrent_attempts: Literal[1]
    max_attempts_per_task: int = Field(ge=1)
    max_resume_per_attempt: int = Field(ge=0, le=1)
    max_turns_per_run: int = Field(ge=1)
    run_timeout_seconds: int = Field(gt=0)
    task_timeout_seconds: int = Field(gt=0)
    interrupt_grace_seconds: int = Field(ge=0)
    check_timeout_seconds: int = Field(gt=0)
    unknown_usage_allowed: bool
    require_clean_worktree: bool
    allow_external_actions: Literal[False]


class PoliciesConfig(StrictModel):
    schema_version: Literal[1]
    policies: dict[str, Policy]


class CommandCheck(StrictModel):
    kind: Literal["command"]
    argv: list[str] = Field(min_length=1)
    cwd: str
    timeout_seconds: int = Field(gt=0)
    expected_exit_codes: list[int] = Field(min_length=1)

    @field_validator("cwd")
    @classmethod
    def _cwd(cls, value: str) -> str:
        return validate_relative_path(value)


class ChecksConfig(StrictModel):
    schema_version: Literal[1]
    checks: dict[str, CommandCheck]


class RuntimeProfile(StrictModel):
    runtime: Literal["codex"]
    model: str = Field(min_length=1)
    auth_method: Literal["chatgpt"]
    reasoning_effort: str = Field(min_length=1)


class RuntimeProfilesConfig(StrictModel):
    schema_version: Literal[1]
    profiles: dict[str, RuntimeProfile]


class ProjectPack(StrictModel):
    root: str
    project: ProjectConfig
    capabilities: CapabilitiesConfig
    policies: PoliciesConfig
    checks: ChecksConfig
    sha256: str


class TaskLimits(StrictModel):
    timeout_seconds: int = Field(gt=0)
    remaining_attempts: int = Field(ge=0)


class TaskEnvelope(StrictModel):
    schema_version: Literal[1]
    run_id: str
    task_id: str
    attempt_id: str
    requirements_version: int = Field(ge=1)
    dispatch_token: str
    goal: str
    completion_criteria: list[str]
    inputs: list[InputRef]
    read_scope: list[str]
    write_scope: list[str]
    workspace_mode: WorkspaceMode
    check_names: list[str]
    limits: TaskLimits
    result_schema_path: str


class ResultArtifact(StrictModel):
    path: str = Field(
        description=(
            "Project-relative path to one existing regular file. Directory paths "
            "and glob patterns are invalid; represent a directory output with a "
            "concrete manifest or index file."
        )
    )
    kind: str
    description: str

    @field_validator("path")
    @classmethod
    def _path(cls, value: str) -> str:
        return validate_relative_path(value)


class WorkerCheckClaim(StrictModel):
    check_name: str
    claimed_status: str


class ResultEnvelope(StrictModel):
    schema_version: Literal[1]
    status_claim: StatusClaim
    summary: str
    artifacts: list[ResultArtifact]
    changed_paths: list[str]
    checks_run_by_worker: list[WorkerCheckClaim]
    assumptions: list[str]
    warnings: list[str]
    requested_followup: str | None

    @field_validator("changed_paths")
    @classmethod
    def _changed_paths(cls, values: list[str]) -> list[str]:
        return [validate_relative_path(value) for value in values]


class RuntimeCapabilities(StrictModel):
    runtime_name: str
    runtime_version: str
    supports_interrupt: bool
    supports_usage: bool
    supports_resume: bool
    supports_output_schema: bool


class RuntimeFailure(StrictModel):
    kind: FailureKind
    retryable: bool
    redacted_message: str
    source_exception_type: str


class TokenCounts(StrictModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)


class RunStatusTask(StrictModel):
    key: str = Field(min_length=1)
    state: TaskState
    attempts: int = Field(ge=0)
    active_attempt_id: str | None


class RunStatusEnvelope(StrictModel):
    schema_version: Literal[1]
    run_id: str = Field(min_length=1)
    state: RunState
    turns_used: int = Field(ge=0)
    tasks: list[RunStatusTask]
    session_usage_statuses: list[UsageStatus] = Field(
        description=(
            "Per-session measurement availability. unsupported remains unknown to "
            "benchmark consumers and is never treated as not_applicable."
        )
    )


class RunReportAttempt(StrictModel):
    attempt_no: int = Field(ge=1)
    state: AttemptState
    failure_kind: str | None
    resume_count: int = Field(ge=0)
    task_semantics_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    initial_prompt_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    output_schema_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


class RunReportTask(StrictModel):
    key: str = Field(min_length=1)
    state: TaskState
    attempts: list[RunReportAttempt]


class RunReportMetrics(StrictModel):
    turns: int = Field(ge=0)
    sessions: int = Field(ge=0)
    tasks: int = Field(ge=0)
    attempts: int = Field(ge=0)
    checks_passed: int = Field(ge=0)
    checks_failed: int = Field(ge=0)
    wall_clock_seconds: float | None = Field(default=None, ge=0)
    model_active_seconds: float | None = Field(default=None, ge=0)
    usage_status: ReportUsageStatus
    token_usage: TokenCounts = Field(
        description=(
            "Aggregate token counts only when usage_status=measured; otherwise these "
            "integers are an incomplete subtotal and must not be promoted to a measured total."
        )
    )
    decisions: int = Field(ge=0)
    manual_copy_or_relay_count: int | None = Field(default=None, ge=0)
    manual_recovery_seconds: float | None = Field(default=None, ge=0)


class RunReportEnvelope(StrictModel):
    schema_version: Literal[1]
    run_id: str = Field(min_length=1)
    state: RunState
    project_id: str = Field(min_length=1)
    request: str
    metrics: RunReportMetrics
    tasks: list[RunReportTask]


class UsageSnapshot(StrictModel):
    status: UsageStatus
    scope: str | None = None
    total: TokenCounts | None = None


class RuntimeOutcome(StrictModel):
    terminal_status: TerminalStatus
    terminal_evidence: dict[str, Any]
    raw_result: Any | None = None
    usage_snapshot: UsageSnapshot | None = None
    failure: RuntimeFailure | None = None


class InterruptOutcome(StrictModel):
    state: InterruptState
    terminal_evidence: dict[str, Any] = Field(default_factory=dict)


class ArtifactMetadata(StrictModel):
    artifact_id: str
    run_id: str
    task_id: str | None
    attempt_id: str | None
    kind: str
    relative_path: str
    sha256: str
    size_bytes: int
    media_type: str | None
    sensitivity: str
    retention: str
    producer: str


class CheckResult(StrictModel):
    check_name: str
    state: CheckState
    argv: list[str]
    exit_code: int | None
    stdout: str
    stderr: str
    started_at: str
    ended_at: str
    failure_classification: CheckFailureClassification | None = None
    diagnostic_result: CheckDiagnosticResult | None = None
    failure_classification_source: Literal[
        "passed",
        "structured_check_protocol",
        "check_protocol",
        "controller_runtime",
        "unclassified",
    ]
    temp_root: str
    temp_allocation_id: str


class FingerprintEntry(StrictModel):
    path: str
    sha256: str
    size: int


class InputFingerprint(StrictModel):
    manifest: list[FingerprintEntry]
    sha256: str


class WorkspaceBaseline(StrictModel):
    head_revision: str
    files: list[FingerprintEntry]
    sha256: str


def load_yaml_model(path: Any, model: type[StrictModel]) -> StrictModel:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)
        return model.model_validate(raw)
    except (OSError, yaml.YAMLError, ValidationError) as exc:
        raise ContractError(f"invalid {path}: {exc}") from exc
