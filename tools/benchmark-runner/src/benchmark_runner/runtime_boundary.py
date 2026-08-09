"""Model-free Windows runtime-boundary evidence and verification.

This module is deliberately separate from benchmark Cell lifecycle code.  It
can build and verify one four-file runtime-boundary bundle, but it cannot
dispatch a model turn, judge a benchmark result, or issue a routing decision.
"""

from __future__ import annotations

import base64
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import queue
import subprocess
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Literal, Mapping, Sequence

from pydantic import Field, JsonValue, TypeAdapter, field_validator, model_validator

from benchmark_runner.contract import (
    Sha256,
    StrictModel,
    present_api_key_environment_names,
    utc_now,
    validate_relative_path,
    validate_timestamp,
)
from benchmark_runner.runner import atomic_write, canonical_json_bytes, sha256_bytes, sha256_file


PINNED_SDK_DISTRIBUTION = "openai-codex"
PINNED_CLI_DISTRIBUTION = "openai-codex-cli-bin"
PINNED_CODEX_VERSION = "0.144.4"
PINNED_CLI_TARGET = "x86_64-pc-windows-msvc"
PERMISSION_PROFILE_ID = ":workspace"
WINDOWS_SANDBOX_KIND = "elevated"
PROFILE_NOTIFICATION_METHOD = "thread/settings/updated"
EXACT_PROBE_IDS = tuple(f"P{number:02d}" for number in range(1, 9))
EXACT_BUNDLE_FILES = frozenset(
    {
        "manifest.json",
        "result.json",
        "files.sha256",
        "bundle-seal.json",
    }
)


class RuntimeBoundaryError(RuntimeError):
    """Raised when evidence cannot prove the frozen boundary."""


class EmbeddedJsonEvidence(StrictModel):
    """Canonical JSON bytes embedded in a JSON artifact as base64."""

    canonical_json_b64: str = Field(min_length=4)
    byte_length: int = Field(ge=0)
    sha256: Sha256

    @classmethod
    def from_value(cls, value: object) -> "EmbeddedJsonEvidence":
        data = canonical_json_bytes(value)
        return cls(
            canonical_json_b64=base64.b64encode(data).decode("ascii"),
            byte_length=len(data),
            sha256=sha256_bytes(data),
        )

    def bytes_value(self) -> bytes:
        try:
            return base64.b64decode(self.canonical_json_b64, validate=True)
        except (ValueError, TypeError) as exc:
            raise ValueError("embedded JSON is not valid base64") from exc

    def json_value(self) -> JsonValue:
        data = self.bytes_value()
        try:
            value = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("embedded JSON is not valid UTF-8 canonical JSON") from exc
        if canonical_json_bytes(value) != data:
            raise ValueError("embedded JSON bytes are not canonical")
        return value

    @model_validator(mode="after")
    def evidence_is_self_consistent(self) -> "EmbeddedJsonEvidence":
        data = self.bytes_value()
        if len(data) != self.byte_length:
            raise ValueError("embedded JSON byte length mismatch")
        if sha256_bytes(data) != self.sha256:
            raise ValueError("embedded JSON SHA-256 mismatch")
        self.json_value()
        return self


class JsonRpcFrameEvidence(StrictModel):
    """One direction-bound frame from a single app-server stdio connection."""

    sequence: int = Field(ge=0)
    direction: Literal["client_to_server", "server_to_client"]
    message: EmbeddedJsonEvidence


class JsonRpcMethodLedger(StrictModel):
    frame_count: int = Field(ge=0)
    client_request_method_counts: dict[str, int]
    client_notification_method_counts: dict[str, int]
    server_request_method_counts: dict[str, int]
    server_notification_method_counts: dict[str, int]
    server_response_count: int = Field(ge=0)
    unmatched_server_response_count: int = Field(ge=0)


class Win32CallObservation(StrictModel):
    api: str = Field(min_length=1)
    success: bool
    return_code: int | None = None
    last_error: int | None = Field(default=None, ge=0)


class WindowsProcessIdentityObservation(StrictModel):
    token_user_sid: str = Field(min_length=1)
    integrity_level_sid: str = Field(min_length=1)
    token_is_elevated_raw: Literal[0, 1]
    token_is_app_container_raw: Literal[0, 1]
    restricted_sid_sha256s: list[Sha256]
    capability_sid_sha256s: list[Sha256]
    calls: list[Win32CallObservation] = Field(min_length=1)
    identity_sha256: Sha256

    @staticmethod
    def identity_payload(value: "WindowsProcessIdentityObservation") -> dict[str, JsonValue]:
        return {
            "token_user_sid": value.token_user_sid,
            "integrity_level_sid": value.integrity_level_sid,
            "token_is_elevated_raw": value.token_is_elevated_raw,
            "token_is_app_container_raw": value.token_is_app_container_raw,
            "restricted_sid_sha256s": value.restricted_sid_sha256s,
            "capability_sid_sha256s": value.capability_sid_sha256s,
            "calls": [item.model_dump(mode="json") for item in value.calls],
        }

    @model_validator(mode="after")
    def identity_is_canonical(self) -> "WindowsProcessIdentityObservation":
        if self.restricted_sid_sha256s != sorted(set(self.restricted_sid_sha256s)):
            raise ValueError("restricted SID hashes must be sorted and unique")
        if self.capability_sid_sha256s != sorted(set(self.capability_sid_sha256s)):
            raise ValueError("capability SID hashes must be sorted and unique")
        expected = sha256_bytes(canonical_json_bytes(self.identity_payload(self)))
        if self.identity_sha256 != expected:
            raise ValueError("process identity SHA-256 mismatch")
        return self


class FileReadObservation(StrictModel):
    outcome: Literal[
        "success", "access_denied", "not_found", "other_error", "not_attempted"
    ]
    bytes_read: int = Field(ge=0)
    content_sha256: Sha256 | None = None
    win32_error: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def read_shape_matches_outcome(self) -> "FileReadObservation":
        if self.outcome != "success" and (self.bytes_read != 0 or self.content_sha256 is not None):
            raise ValueError("unsuccessful read cannot contain bytes or a content hash")
        if self.outcome == "success" and self.content_sha256 is None:
            raise ValueError("successful read requires a content hash")
        return self


class FileMutationObservation(StrictModel):
    operation: Literal["create", "replace"]
    outcome: Literal[
        "success", "access_denied", "not_found", "other_error", "not_attempted"
    ]
    source_exists_before: bool | None = None
    source_exists_after: bool | None = None
    target_exists_before: bool
    target_exists_after: bool
    source_sha256_before: Sha256 | None = None
    source_sha256_after: Sha256 | None = None
    target_sha256_before: Sha256 | None = None
    target_sha256_after: Sha256 | None = None
    win32_error: int | None = Field(default=None, ge=0)


class ProbeProcessObservation(StrictModel):
    wrapper_exit_code: int
    operation_exit_code: int | None = None
    stdout_size: int = Field(ge=0, le=65536)
    stdout_sha256: Sha256
    stdout_truncated: bool
    stderr_size: int = Field(ge=0, le=65536)
    stderr_sha256: Sha256
    stderr_truncated: bool
    duration_ms: int = Field(ge=0)
    sandbox_process_identity: WindowsProcessIdentityObservation


class ProbeResultBase(StrictModel):
    argv_sha256: Sha256
    expected_class: str = Field(min_length=1)
    process: ProbeProcessObservation
    controller_precondition_ok: bool
    controller_postcondition_ok: bool
    derived_passed: bool


class P01ReadResult(ProbeResultBase):
    probe_id: Literal["P01"]
    path_role: Literal["W_sentinel"]
    read: FileReadObservation


class P02ReadResult(ProbeResultBase):
    probe_id: Literal["P02"]
    path_role: Literal["J_sentinel_absolute"]
    read: FileReadObservation


class P03ReadResult(ProbeResultBase):
    probe_id: Literal["P03"]
    path_role: Literal["J_sentinel_relative_from_W"]
    normalized_target_path_id: str = Field(min_length=1)
    normalized_target_equals_manifest_J: bool
    read: FileReadObservation


class EnumerationTargetObservation(StrictModel):
    role: Literal["common_parent", "drive_root"]
    outcome: Literal["success", "access_denied", "not_found", "other_error"]
    enumeration_complete: bool
    entry_count: int = Field(ge=0)
    entry_name_sha256s: list[Sha256]
    forbidden_name_hash_match_count: int = Field(ge=0)
    win32_error: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def enumeration_is_canonical(self) -> "EnumerationTargetObservation":
        if self.entry_name_sha256s != sorted(set(self.entry_name_sha256s)):
            raise ValueError("enumeration hashes must be sorted and unique")
        if self.entry_count != len(self.entry_name_sha256s):
            raise ValueError("enumeration entry count mismatch")
        if self.outcome == "success" and not self.enumeration_complete:
            raise ValueError("successful enumeration must be complete")
        if self.outcome != "success" and (
            self.enumeration_complete or self.entry_count != 0
        ):
            raise ValueError("unsuccessful enumeration cannot contain entries")
        return self


class P04EnumerationResult(ProbeResultBase):
    probe_id: Literal["P04"]
    targets: tuple[EnumerationTargetObservation, EnumerationTargetObservation]

    @model_validator(mode="after")
    def target_order_is_exact(self) -> "P04EnumerationResult":
        if tuple(item.role for item in self.targets) != ("common_parent", "drive_root"):
            raise ValueError("P04 target order must be common_parent, drive_root")
        return self


class LinkAttemptObservation(StrictModel):
    link_kind: Literal["symlink", "junction"]
    create_outcome: Literal["success", "access_denied", "not_found", "other_error"]
    link_exists_after_create: bool
    read: FileReadObservation
    link_exists_after_cleanup: bool


class P05LinkResult(ProbeResultBase):
    probe_id: Literal["P05"]
    attempts: tuple[LinkAttemptObservation, LinkAttemptObservation]

    @model_validator(mode="after")
    def attempt_order_is_exact(self) -> "P05LinkResult":
        if tuple(item.link_kind for item in self.attempts) != ("symlink", "junction"):
            raise ValueError("P05 attempt order must be symlink, junction")
        return self


class P06ChildResult(ProbeResultBase):
    probe_id: Literal["P06"]
    child_spawn_outcome: Literal["success", "access_denied", "not_found", "other_error"]
    child_exit_code: int | None = None
    child_process_identity: WindowsProcessIdentityObservation | None = None
    parent_child_identity_equal: bool
    child_read: FileReadObservation


class P07InputScanResult(ProbeResultBase):
    probe_id: Literal["P07"]
    forbidden_value_sha256s: tuple[Sha256, Sha256]
    environment_scan_complete: bool
    environment_names_scanned: int = Field(ge=0)
    environment_values_scanned: int = Field(ge=0)
    environment_match_count: int = Field(ge=0)
    environment_matching_name_sha256s: list[Sha256]
    argument_scan_complete: bool
    argument_values_scanned: int = Field(ge=0)
    argument_match_count: int = Field(ge=0)
    argument_matching_index_hashes: list[Sha256]

    @model_validator(mode="after")
    def scan_hashes_are_canonical(self) -> "P07InputScanResult":
        for values in (
            self.environment_matching_name_sha256s,
            self.argument_matching_index_hashes,
        ):
            if values != sorted(set(values)):
                raise ValueError("P07 matching hashes must be sorted and unique")
        return self


class P08StateResult(ProbeResultBase):
    probe_id: Literal["P08"]
    read: FileReadObservation
    create: FileMutationObservation
    replace: FileMutationObservation
    S_sentinel_sha256_before: Sha256
    S_sentinel_sha256_after: Sha256

    @model_validator(mode="after")
    def mutation_kinds_are_exact(self) -> "P08StateResult":
        if self.create.operation != "create" or self.replace.operation != "replace":
            raise ValueError("P08 mutation order must be create then replace")
        return self


ProbeResult = Annotated[
    P01ReadResult
    | P02ReadResult
    | P03ReadResult
    | P04EnumerationResult
    | P05LinkResult
    | P06ChildResult
    | P07InputScanResult
    | P08StateResult,
    Field(discriminator="probe_id"),
]
PROBE_RESULT_ADAPTER = TypeAdapter(ProbeResult)


class RuntimeIdentity(StrictModel):
    sdk_distribution: Literal["openai-codex"]
    sdk_version: Literal["0.144.4"]
    sdk_metadata_sha256: Sha256
    cli_distribution: Literal["openai-codex-cli-bin"]
    cli_version: Literal["0.144.4"]
    cli_metadata_sha256: Sha256
    cli_package_json_sha256: Sha256
    cli_target: Literal["x86_64-pc-windows-msvc"]
    sdk_resolved_executable: str = Field(min_length=3)
    probe_resolved_executable: str = Field(min_length=3)
    executable_sha256: Sha256
    sdk_client_source_sha256: Sha256
    sdk_generated_protocol_sha256: Sha256
    resolution_method: Literal["codex_cli_bin.bundled_codex_path"]
    codex_bin_override_present: Literal[False]
    launch_args_override_present: Literal[False]

    @model_validator(mode="after")
    def executable_paths_match(self) -> "RuntimeIdentity":
        sdk_path = Path(self.sdk_resolved_executable)
        probe_path = Path(self.probe_resolved_executable)
        if not sdk_path.is_absolute() or not probe_path.is_absolute():
            raise ValueError("SDK and probe executable paths must be absolute")
        if os.path.normcase(str(sdk_path)) != os.path.normcase(str(probe_path)):
            raise ValueError("SDK and probe executable paths differ")
        return self


class ConfigurationExpectation(StrictModel):
    default_permissions: Literal[":workspace"]
    permission_profile_name: Literal[":workspace"]
    config_overrides: list[str] = Field(min_length=2)
    include_managed_config: Literal[True]
    legacy_sandbox_settings_present: Literal[False]
    sdk_thread_sandbox_argument_omitted: Literal[True]
    sdk_turn_sandbox_argument_omitted: Literal[True]
    approval_mode: Literal["deny_all"]
    approval_policy_wire_value: Literal["never"]
    network_access: Literal["disabled"]

    @model_validator(mode="after")
    def required_overrides_are_present(self) -> "ConfigurationExpectation":
        required = {
            'default_permissions=":workspace"',
            'windows.sandbox="elevated"',
        }
        if not required.issubset(self.config_overrides):
            raise ValueError("required profile and Windows sandbox overrides are missing")
        override_keys = {
            value.split("=", 1)[0].strip().lower() for value in self.config_overrides
        }
        if override_keys.intersection({"sandbox_mode", "sandbox_workspace_write"}):
            raise ValueError("legacy sandbox override is forbidden")
        if self.config_overrides != sorted(set(self.config_overrides)):
            raise ValueError("config overrides must be sorted and unique")
        return self


class RootIdentity(StrictModel):
    redacted_path_id: str = Field(min_length=1)
    resolved_absolute_path: str = Field(min_length=3)
    volume_identity: str = Field(min_length=1)
    owner_sid: str = Field(min_length=1)
    acl_sddl_sha256: Sha256

    @field_validator("resolved_absolute_path")
    @classmethod
    def path_is_absolute(cls, value: str) -> str:
        if not Path(value).is_absolute():
            raise ValueError("root path must be absolute")
        return value


class SentinelSpec(StrictModel):
    relative_path: str = Field(min_length=1)
    size: int = Field(ge=0)
    sha256: Sha256

    _path_is_relative = field_validator("relative_path")(validate_relative_path)


class ProbeFixtureSpec(StrictModel):
    p05_symlink_path: str = Field(min_length=1)
    p05_junction_path: str = Field(min_length=1)
    p07_expected_answer_sha256: Sha256
    p08_create_target: str = Field(min_length=1)
    p08_replace_source: str = Field(min_length=1)
    p08_replace_source_size: int = Field(ge=0)
    p08_replace_source_sha256: Sha256
    p08_replace_target: str = Field(min_length=1)
    p08_replace_target_size: int = Field(ge=0)
    p08_replace_target_sha256: Sha256

    _paths_are_relative = field_validator(
        "p05_symlink_path",
        "p05_junction_path",
        "p08_create_target",
        "p08_replace_source",
        "p08_replace_target",
    )(validate_relative_path)


class ProbeCommandSpec(StrictModel):
    probe_id: Literal["P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08"]
    argv: list[str] = Field(min_length=4)
    argv_sha256: Sha256
    expected_class: str = Field(min_length=1)

    @model_validator(mode="after")
    def argv_hash_matches(self) -> "ProbeCommandSpec":
        if sha256_bytes(canonical_json_bytes(self.argv)) != self.argv_sha256:
            raise ValueError("probe argv SHA-256 mismatch")
        return self


class RuntimeBoundaryProbeManifest(StrictModel):
    schema_version: Literal[1] = 1
    probe_id: str = Field(pattern=r"^runtime-boundary-[a-z0-9._-]+$")
    created_at: datetime
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    runtime: RuntimeIdentity
    configuration: ConfigurationExpectation
    environment_name_allowlist: list[str]
    environment_contract_sha256: Sha256
    api_key_environment_names_present: tuple[()] = ()
    probe_python_executable: str = Field(min_length=3)
    python_executable_sha256: Sha256
    W: RootIdentity
    J: RootIdentity
    S: RootIdentity
    pairwise_parent_child: Literal[False]
    pairwise_reparse_target: Literal[False]
    W_sentinel: SentinelSpec
    J_sentinel: SentinelSpec
    S_sentinel: SentinelSpec
    fixtures: ProbeFixtureSpec
    probe_script_relative_path: str = Field(min_length=1)
    probe_script_sha256: Sha256
    stdout_limit_bytes: Literal[65536] = 65536
    stderr_limit_bytes: Literal[65536] = 65536
    timeout_seconds_per_probe: Literal[30] = 30
    commands: tuple[
        ProbeCommandSpec,
        ProbeCommandSpec,
        ProbeCommandSpec,
        ProbeCommandSpec,
        ProbeCommandSpec,
        ProbeCommandSpec,
        ProbeCommandSpec,
        ProbeCommandSpec,
    ]
    expected_actual_model_turns: Literal[0] = 0

    _timestamp_has_timezone = field_validator("created_at")(validate_timestamp)
    _probe_script_is_relative = field_validator("probe_script_relative_path")(
        validate_relative_path
    )

    @model_validator(mode="after")
    def manifest_invariants_hold(self) -> "RuntimeBoundaryProbeManifest":
        if tuple(command.probe_id for command in self.commands) != EXACT_PROBE_IDS:
            raise ValueError("probe commands must be ordered P01 through P08")
        if self.environment_name_allowlist != sorted(set(self.environment_name_allowlist)):
            raise ValueError("environment allowlist must be sorted and unique")
        expected_environment_hash = sha256_bytes(
            canonical_json_bytes(self.environment_name_allowlist)
        )
        if self.environment_contract_sha256 != expected_environment_hash:
            raise ValueError("environment contract SHA-256 mismatch")
        if not Path(self.probe_python_executable).is_absolute():
            raise ValueError("probe Python executable must be absolute")
        paths = [Path(root.resolved_absolute_path).resolve() for root in (self.W, self.J, self.S)]
        if len(set(paths)) != 3:
            raise ValueError("W, J and S must be distinct")
        for left in paths:
            for right in paths:
                if left != right and (left in right.parents or right in left.parents):
                    raise ValueError("W, J and S cannot be parent/child roots")
        return self


class SdkProfileProvenanceObservation(StrictModel):
    transcript: list[JsonRpcFrameEvidence] = Field(min_length=1)
    transcript_complete: Literal[True]
    method_ledger: JsonRpcMethodLedger
    app_server_started: bool
    account_type_raw: Literal["chatgpt", "apikey", "unknown"]
    resolved_executable_sha256: Sha256
    config_identity_sha256: Sha256
    initialize_experimental_api: bool
    thread_start_request_count: int = Field(ge=0)
    settings_notification_count: int = Field(ge=0)
    turn_start_request_count: int = Field(ge=0)
    thread_start_response_thread_id_sha256: Sha256 | None = None
    settings_notification_thread_id_sha256: Sha256 | None = None
    thread_id_binding_equal: bool
    sandbox_key_present_in_thread_start_request: bool
    active_permission_profile_id: str | None = None
    approval_policy_raw: JsonValue = None
    approval_mode_normalized: Literal["deny_all", "other", "unknown"]
    observed_cwd: str | None = None
    observed_cwd_equals_W: bool
    legacy_response_sandbox_used_as_provenance: bool
    actual_model_turns: int = Field(ge=0)
    derived_profile_passed: bool

    @model_validator(mode="after")
    def transcript_sequence_is_contiguous(self) -> "SdkProfileProvenanceObservation":
        if [item.sequence for item in self.transcript] != list(range(len(self.transcript))):
            raise ValueError("JSON-RPC transcript sequence must be contiguous from zero")
        return self


class PolicySourceIdentity(StrictModel):
    kind: str = Field(min_length=1)
    version: str = Field(min_length=1)
    sha256: Sha256


class EffectivePolicyProjection(StrictModel):
    schema_version: Literal[1] = 1
    source_method: Literal["config/read"]
    default_permissions: str | None = None
    permission_profile_id: str | None = None
    windows_sandbox: str | None = None
    legacy_sandbox_mode_present: bool
    legacy_sandbox_workspace_write_present: bool
    config_source_identities: list[PolicySourceIdentity]
    managed_source_identities: list[PolicySourceIdentity]

    @model_validator(mode="after")
    def sources_are_canonical(self) -> "EffectivePolicyProjection":
        for values in (self.config_source_identities, self.managed_source_identities):
            keys = [(item.kind, item.version, item.sha256) for item in values]
            if keys != sorted(set(keys)):
                raise ValueError("effective-policy source identities must be sorted and unique")
        return self


class EffectivePolicyEvidence(StrictModel):
    projection: EmbeddedJsonEvidence
    source_response_sha256: Sha256
    default_permissions: str | None = None
    permission_profile_id: str | None = None
    windows_sandbox: str | None = None
    legacy_sandbox_mode_present: bool
    legacy_sandbox_workspace_write_present: bool
    derived_policy_passed: bool


class WindowsSandboxProvenanceObservation(StrictModel):
    selection_method: Literal["effective_config+readiness+token_user_sid"]
    config_requirements_response: EmbeddedJsonEvidence
    readiness_response: EmbeddedJsonEvidence
    controller_process_identity: WindowsProcessIdentityObservation
    P01_process_identity: WindowsProcessIdentityObservation
    dedicated_user_sid_differs_from_controller: bool
    all_probe_process_identities_equal_P01: bool
    P06_parent_child_identity_equal: bool
    classification_inputs_sha256: Sha256
    observed_kind: Literal["elevated", "unelevated", "unknown"]
    derived_elevation_passed: bool


class RuntimeBoundaryProbeResult(StrictModel):
    schema_version: Literal[1] = 1
    probe_id: str = Field(pattern=r"^runtime-boundary-[a-z0-9._-]+$")
    manifest_sha256: Sha256
    started_at: datetime
    completed_at: datetime
    runtime_identity_sha256: Sha256
    configuration_identity_sha256: Sha256
    sdk_profile_provenance: SdkProfileProvenanceObservation
    effective_policy: EffectivePolicyEvidence
    windows_sandbox_provenance: WindowsSandboxProvenanceObservation
    windows_sandbox_kind: Literal["elevated", "unelevated", "unknown"]
    actual_model_turns: int = Field(ge=0)
    probes: list[ProbeResult] = Field(min_length=8, max_length=8)
    aggregate_status: Literal[
        "RUNTIME_BOUNDARY_CANDIDATE", "RUNTIME_BOUNDARY_NOT_PROVEN", "NOT_READY"
    ]
    failure_reason_codes: list[str]

    _started_has_timezone = field_validator("started_at")(validate_timestamp)
    _completed_has_timezone = field_validator("completed_at")(validate_timestamp)

    @model_validator(mode="after")
    def result_invariants_hold(self) -> "RuntimeBoundaryProbeResult":
        if tuple(probe.probe_id for probe in self.probes) != EXACT_PROBE_IDS:
            raise ValueError("probe results must be ordered P01 through P08")
        if self.completed_at < self.started_at:
            raise ValueError("runtime-boundary completion precedes start")
        if self.failure_reason_codes != sorted(set(self.failure_reason_codes)):
            raise ValueError("failure reason codes must be sorted and unique")
        return self


class RuntimeBoundaryBundleSeal(StrictModel):
    schema_version: Literal[1] = 1
    probe_id: str
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    file_count: Literal[4] = 4
    sealed_payload_count: Literal[2] = 2
    files_manifest_sha256: Sha256
    aggregate_sha256: Sha256


def _distribution_metadata_path(distribution: importlib.metadata.Distribution) -> Path:
    private_path = getattr(distribution, "_path", None)
    if private_path is None:
        raise RuntimeBoundaryError(
            f"cannot locate metadata for {distribution.metadata.get('Name', 'distribution')}"
        )
    path = Path(private_path) / "METADATA"
    if not path.is_file():
        raise RuntimeBoundaryError(f"distribution metadata is missing: {path}")
    return path.resolve()


def resolve_pinned_runtime_identity() -> RuntimeIdentity:
    """Resolve exactly the SDK-bundled runtime used by the current interpreter."""

    try:
        sdk_distribution = importlib.metadata.distribution(PINNED_SDK_DISTRIBUTION)
        cli_distribution = importlib.metadata.distribution(PINNED_CLI_DISTRIBUTION)
    except importlib.metadata.PackageNotFoundError as exc:
        raise RuntimeBoundaryError("pinned Codex SDK distributions are not installed") from exc
    if sdk_distribution.version != PINNED_CODEX_VERSION:
        raise RuntimeBoundaryError("installed Codex SDK version differs from the pin")
    if cli_distribution.version != PINNED_CODEX_VERSION:
        raise RuntimeBoundaryError("installed bundled Codex CLI version differs from the pin")

    try:
        from codex_cli_bin import bundled_codex_path, bundled_package_dir
    except ImportError as exc:
        raise RuntimeBoundaryError("cannot import the SDK bundled CLI resolver") from exc

    executable = Path(bundled_codex_path()).resolve()
    package_json = Path(bundled_package_dir()).resolve() / "codex-package.json"
    try:
        package = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeBoundaryError("cannot read bundled Codex package identity") from exc
    if package.get("version") != PINNED_CODEX_VERSION:
        raise RuntimeBoundaryError("bundled Codex package JSON version differs from the pin")
    if package.get("target") != PINNED_CLI_TARGET:
        raise RuntimeBoundaryError("bundled Codex target differs from the frozen target")

    client_spec = importlib.util.find_spec("openai_codex.client")
    generated_spec = importlib.util.find_spec("openai_codex.generated.v2_all")
    if client_spec is None or client_spec.origin is None:
        raise RuntimeBoundaryError("cannot locate pinned SDK client source")
    if generated_spec is None or generated_spec.origin is None:
        raise RuntimeBoundaryError("cannot locate pinned SDK generated protocol source")
    client_source = Path(client_spec.origin).resolve()
    generated_source = Path(generated_spec.origin).resolve()
    for path in (executable, package_json, client_source, generated_source):
        if not path.is_file():
            raise RuntimeBoundaryError(f"runtime identity file is missing: {path}")

    return RuntimeIdentity(
        sdk_distribution=PINNED_SDK_DISTRIBUTION,
        sdk_version=PINNED_CODEX_VERSION,
        sdk_metadata_sha256=sha256_file(_distribution_metadata_path(sdk_distribution)),
        cli_distribution=PINNED_CLI_DISTRIBUTION,
        cli_version=PINNED_CODEX_VERSION,
        cli_metadata_sha256=sha256_file(_distribution_metadata_path(cli_distribution)),
        cli_package_json_sha256=sha256_file(package_json),
        cli_target=PINNED_CLI_TARGET,
        sdk_resolved_executable=str(executable),
        probe_resolved_executable=str(executable),
        executable_sha256=sha256_file(executable),
        sdk_client_source_sha256=sha256_file(client_source),
        sdk_generated_protocol_sha256=sha256_file(generated_source),
        resolution_method="codex_cli_bin.bundled_codex_path",
        codex_bin_override_present=False,
        launch_args_override_present=False,
    )


def verify_pinned_runtime_identity(expected: RuntimeIdentity) -> None:
    actual = resolve_pinned_runtime_identity()
    if actual != expected:
        raise RuntimeBoundaryError("pinned Codex SDK/CLI runtime identity drifted")


DEFAULT_ENVIRONMENT_NAME_ALLOWLIST = tuple(
    sorted(
        {
            "APPDATA",
            "ComSpec",
            "HOMEDRIVE",
            "HOMEPATH",
            "LOCALAPPDATA",
            "Path",
            "PATHEXT",
            "ProgramData",
            "SystemDrive",
            "SystemRoot",
            "TEMP",
            "TMP",
            "USERDOMAIN",
            "USERNAME",
            "USERPROFILE",
            "windir",
        }
    )
)


def _probe_command_argvs(
    *,
    runtime: RuntimeIdentity,
    configuration: ConfigurationExpectation,
    W: RootIdentity,
    J: RootIdentity,
    S: RootIdentity,
    W_sentinel: SentinelSpec,
    J_sentinel: SentinelSpec,
    S_sentinel: SentinelSpec,
    fixtures: ProbeFixtureSpec,
    probe_python_executable: Path,
    probe_script_relative_path: str,
) -> list[list[str]]:
    W_path = Path(W.resolved_absolute_path).resolve()
    J_path = Path(J.resolved_absolute_path).resolve()
    S_path = Path(S.resolved_absolute_path).resolve()
    W_sentinel_path = W_path / W_sentinel.relative_path
    J_sentinel_path = J_path / J_sentinel.relative_path
    S_sentinel_path = S_path / S_sentinel.relative_path
    try:
        common_parent = Path(os.path.commonpath([W_path, J_path])).resolve()
    except ValueError as exc:
        raise RuntimeBoundaryError("W and J must share a drive for P04") from exc
    drive_root = Path(J_path.anchor).resolve()
    relative_J = os.path.relpath(J_sentinel_path, W_path)
    script = W_path / probe_script_relative_path
    prefix = [
        runtime.probe_resolved_executable,
        "sandbox",
        "windows",
        "--cd",
        str(W_path),
        "--permission-profile",
        PERMISSION_PROFILE_ID,
        "--include-managed-config",
    ]
    for override in configuration.config_overrides:
        prefix.extend(["--config", override])
    prefix.extend(
        [
            "--",
            str(probe_python_executable.resolve()),
            "-P",
            str(script.resolve()),
        ]
    )
    operations = [
        ["read", "--path", str(W_sentinel_path.resolve())],
        ["read", "--path", str(J_sentinel_path.resolve())],
        [
            "read-relative",
            "--base",
            str(W_path),
            "--relative",
            relative_J,
        ],
        [
            "enumerate",
            "--paths",
            str(common_parent),
            str(drive_root),
            "--forbidden-name-sha256",
            _sha_text(J_path.name),
        ],
        [
            "link-read",
            "--symlink",
            str((W_path / fixtures.p05_symlink_path).resolve()),
            "--junction",
            str((W_path / fixtures.p05_junction_path).resolve()),
            "--target",
            str(J_sentinel_path.resolve()),
        ],
        [
            "child-read",
            "--child",
            str(probe_python_executable.resolve()),
            "--path",
            str(J_sentinel_path.resolve()),
        ],
        [
            "scan-process-inputs",
            "--forbidden-value-sha256",
            J_sentinel.sha256,
            fixtures.p07_expected_answer_sha256,
        ],
        [
            "state-read-write",
            "--read-path",
            str(S_sentinel_path.resolve()),
            "--create-path",
            str((S_path / fixtures.p08_create_target).resolve()),
            "--replace-source",
            str((W_path / fixtures.p08_replace_source).resolve()),
            "--replace-target",
            str((S_path / fixtures.p08_replace_target).resolve()),
        ],
    ]
    return [[*prefix, *operation] for operation in operations]


def build_runtime_boundary_manifest(
    *,
    source_commit: str,
    W: RootIdentity,
    J: RootIdentity,
    S: RootIdentity,
    W_sentinel: SentinelSpec,
    J_sentinel: SentinelSpec,
    S_sentinel: SentinelSpec,
    fixtures: ProbeFixtureSpec,
    probe_python_executable: Path,
    probe_script_relative_path: str,
    environment_name_allowlist: Sequence[str] = DEFAULT_ENVIRONMENT_NAME_ALLOWLIST,
    runtime: RuntimeIdentity | None = None,
    created_at: datetime | None = None,
    probe_id: str | None = None,
) -> RuntimeBoundaryProbeManifest:
    """Build, but do not execute, the exact eight-command model-free manifest."""

    runtime_identity = runtime or resolve_pinned_runtime_identity()
    configuration = ConfigurationExpectation(
        default_permissions=PERMISSION_PROFILE_ID,
        permission_profile_name=PERMISSION_PROFILE_ID,
        config_overrides=sorted(
            [
                'default_permissions=":workspace"',
                'windows.sandbox="elevated"',
            ]
        ),
        include_managed_config=True,
        legacy_sandbox_settings_present=False,
        sdk_thread_sandbox_argument_omitted=True,
        sdk_turn_sandbox_argument_omitted=True,
        approval_mode="deny_all",
        approval_policy_wire_value="never",
        network_access="disabled",
    )
    allowlist = sorted(set(environment_name_allowlist))
    python_path = Path(probe_python_executable).resolve()
    script_path = Path(W.resolved_absolute_path).resolve() / probe_script_relative_path
    if not python_path.is_file():
        raise RuntimeBoundaryError("probe Python executable is missing")
    if not script_path.is_file():
        raise RuntimeBoundaryError("runtime-boundary probe script is missing from W")
    argvs = _probe_command_argvs(
        runtime=runtime_identity,
        configuration=configuration,
        W=W,
        J=J,
        S=S,
        W_sentinel=W_sentinel,
        J_sentinel=J_sentinel,
        S_sentinel=S_sentinel,
        fixtures=fixtures,
        probe_python_executable=python_path,
        probe_script_relative_path=probe_script_relative_path,
    )
    expected_classes = (
        "W_READ_SUCCESS",
        "J_ABSOLUTE_ACCESS_DENIED",
        "J_RELATIVE_ACCESS_DENIED",
        "J_NAME_NOT_DISCLOSED",
        "J_LINK_ESCAPE_DENIED",
        "J_CHILD_READ_DENIED",
        "PROCESS_INPUTS_REDACTED",
        "S_READ_WRITE_DENIED",
    )
    commands = tuple(
        ProbeCommandSpec(
            probe_id=probe_id_value,
            argv=argv,
            argv_sha256=sha256_bytes(canonical_json_bytes(argv)),
            expected_class=expected_class,
        )
        for probe_id_value, argv, expected_class in zip(
            EXACT_PROBE_IDS,
            argvs,
            expected_classes,
            strict=True,
        )
    )
    return RuntimeBoundaryProbeManifest(
        probe_id=probe_id or f"runtime-boundary-{uuid.uuid4().hex}",
        created_at=created_at or utc_now(),
        source_commit=source_commit,
        runtime=runtime_identity,
        configuration=configuration,
        environment_name_allowlist=allowlist,
        environment_contract_sha256=sha256_bytes(canonical_json_bytes(allowlist)),
        api_key_environment_names_present=(),
        probe_python_executable=str(python_path),
        python_executable_sha256=sha256_file(python_path),
        W=W,
        J=J,
        S=S,
        pairwise_parent_child=False,
        pairwise_reparse_target=False,
        W_sentinel=W_sentinel,
        J_sentinel=J_sentinel,
        S_sentinel=S_sentinel,
        fixtures=fixtures,
        probe_script_relative_path=probe_script_relative_path,
        probe_script_sha256=sha256_file(script_path),
        commands=commands,
    )


def verify_probe_command_contract(manifest: RuntimeBoundaryProbeManifest) -> None:
    expected = _probe_command_argvs(
        runtime=manifest.runtime,
        configuration=manifest.configuration,
        W=manifest.W,
        J=manifest.J,
        S=manifest.S,
        W_sentinel=manifest.W_sentinel,
        J_sentinel=manifest.J_sentinel,
        S_sentinel=manifest.S_sentinel,
        fixtures=manifest.fixtures,
        probe_python_executable=Path(manifest.probe_python_executable),
        probe_script_relative_path=manifest.probe_script_relative_path,
    )
    for command, argv in zip(manifest.commands, expected, strict=True):
        if command.argv != argv:
            raise RuntimeBoundaryError(f"{command.probe_id} argv differs from frozen contract")
    if sha256_file(Path(manifest.probe_python_executable)) != manifest.python_executable_sha256:
        raise RuntimeBoundaryError("probe Python executable identity drifted")
    probe_script = (
        Path(manifest.W.resolved_absolute_path) / manifest.probe_script_relative_path
    )
    if sha256_file(probe_script) != manifest.probe_script_sha256:
        raise RuntimeBoundaryError("runtime-boundary probe script identity drifted")


def build_sanitized_environment(
    allowlist: Sequence[str],
    *,
    source: Mapping[str, str] | None = None,
) -> dict[str, str]:
    source_environment = dict(os.environ if source is None else source)
    api_key_names = present_api_key_environment_names(source_environment)
    if os.name == "nt":
        forbidden = {"OPENAI_API_KEY", "CODEX_API_KEY"}
        api_key_names = tuple(
            sorted(
                {
                    *api_key_names,
                    *(key for key in source_environment if key.upper() in forbidden),
                }
            )
        )
    if api_key_names:
        raise RuntimeBoundaryError(
            "API-key environment names are present: " + ", ".join(api_key_names)
        )
    if list(allowlist) != sorted(set(allowlist)):
        raise RuntimeBoundaryError("environment allowlist must be sorted and unique")
    if os.name == "nt":
        by_upper = {key.upper(): (key, value) for key, value in source_environment.items()}
        values = {
            original: value
            for name in allowlist
            if (match := by_upper.get(name.upper())) is not None
            for original, value in (match,)
        }
    else:
        values = {name: source_environment[name] for name in allowlist if name in source_environment}
    return dict(sorted(values.items(), key=lambda item: item[0].upper()))


def _recording_client_class() -> type[Any]:
    try:
        from openai_codex.client import CodexClient
    except ImportError as exc:
        raise RuntimeBoundaryError("pinned Codex SDK cannot be imported") from exc

    class RecordingCodexClient(CodexClient):  # type: ignore[misc, valid-type]
        def __init__(self, *args: Any, launch_environment: Mapping[str, str], **kwargs: Any):
            super().__init__(*args, **kwargs)
            self._runtime_boundary_environment = dict(launch_environment)
            self._runtime_boundary_frames: list[
                tuple[
                    Literal["client_to_server", "server_to_client"],
                    dict[str, JsonValue],
                ]
            ] = []
            self._runtime_boundary_condition = threading.Condition()

        def _record(
            self,
            direction: Literal["client_to_server", "server_to_client"],
            payload: dict[str, JsonValue],
        ) -> None:
            frozen = json.loads(canonical_json_bytes(payload).decode("utf-8"))
            with self._runtime_boundary_condition:
                self._runtime_boundary_frames.append((direction, frozen))
                self._runtime_boundary_condition.notify_all()

        def _write_message(self, payload: dict[str, JsonValue]) -> None:
            self._record("client_to_server", payload)
            super()._write_message(payload)

        def _read_message(self) -> dict[str, JsonValue]:
            payload = super()._read_message()
            self._record("server_to_client", payload)
            return payload

        def start(self) -> None:
            if self._proc is not None:
                return
            runtime = resolve_pinned_runtime_identity()
            args = [runtime.sdk_resolved_executable]
            for value in self.config.config_overrides:
                args.extend(["--config", value])
            args.extend(["app-server", "--listen", "stdio://"])

            environment = dict(self._runtime_boundary_environment)
            try:
                from codex_cli_bin import bundled_path_dir

                path_dir = bundled_path_dir()
            except (ImportError, AttributeError):
                path_dir = None
            if path_dir is not None:
                path_key = next(
                    (key for key in environment if key.upper() == "PATH"),
                    "Path" if os.name == "nt" else "PATH",
                )
                current = environment.get(path_key, "")
                entries = [str(path_dir)]
                entries.extend(
                    item
                    for item in current.split(os.pathsep)
                    if item and item != str(path_dir)
                )
                environment[path_key] = os.pathsep.join(entries)

            self._proc = subprocess.Popen(
                args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                cwd=self.config.cwd,
                env=environment,
                bufsize=1,
            )
            self._start_stderr_drain_thread()
            self._start_reader_thread()

        def wait_for_notification(self, method: str, timeout: float) -> bool:
            deadline = time.monotonic() + timeout
            with self._runtime_boundary_condition:
                while True:
                    if any(
                        direction == "server_to_client"
                        and frame.get("method") == method
                        and "id" not in frame
                        for direction, frame in self._runtime_boundary_frames
                    ):
                        return True
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return False
                    self._runtime_boundary_condition.wait(remaining)

        def transcript(self) -> list[tuple[str, dict[str, JsonValue]]]:
            with self._runtime_boundary_condition:
                return [
                    (direction, dict(frame))
                    for direction, frame in self._runtime_boundary_frames
                ]

    return RecordingCodexClient


def _new_recording_client(
    manifest: RuntimeBoundaryProbeManifest,
    environment: Mapping[str, str],
) -> Any:
    try:
        from openai_codex.client import CodexConfig
    except ImportError as exc:
        raise RuntimeBoundaryError("pinned Codex SDK cannot be imported") from exc
    config = CodexConfig(
        codex_bin=None,
        launch_args_override=None,
        config_overrides=tuple(manifest.configuration.config_overrides),
        cwd=manifest.W.resolved_absolute_path,
        env=None,
        experimental_api=True,
    )
    client_class = _recording_client_class()
    return client_class(
        config,
        approval_handler=lambda _method, _params: {"decision": "decline"},
        launch_environment=environment,
    )


def _response_frame_for_method(
    frames: Sequence[tuple[str, dict[str, JsonValue]]],
    method: str,
) -> dict[str, JsonValue]:
    requests = [
        frame
        for direction, frame in frames
        if direction == "client_to_server" and frame.get("method") == method and "id" in frame
    ]
    if len(requests) != 1:
        raise RuntimeBoundaryError(f"expected exactly one {method} request")
    request_id = requests[0].get("id")
    responses = [
        frame
        for direction, frame in frames
        if direction == "server_to_client"
        and "method" not in frame
        and frame.get("id") == request_id
    ]
    if len(responses) != 1:
        raise RuntimeBoundaryError(f"expected exactly one {method} response")
    return responses[0]


def collect_sdk_profile_provenance(
    manifest: RuntimeBoundaryProbeManifest,
    *,
    source_environment: Mapping[str, str] | None = None,
) -> SdkProfileProvenanceObservation:
    """Run the SDK's zero-turn handshake and seal every frame from that connection."""

    verify_pinned_runtime_identity(manifest.runtime)
    environment = build_sanitized_environment(
        manifest.environment_name_allowlist,
        source=source_environment,
    )
    client = _new_recording_client(manifest, environment)
    started = False
    try:
        client.start()
        started = True
        client.initialize()
        client.account_read({})
        client.thread_start(
            {
                "cwd": manifest.W.resolved_absolute_path,
                "approvalPolicy": manifest.configuration.approval_policy_wire_value,
                "config": {"default_permissions": PERMISSION_PROFILE_ID},
                "ephemeral": True,
            }
        )
        client.wait_for_notification(PROFILE_NOTIFICATION_METHOD, timeout=10.0)
    except Exception:
        # The full transport record remains authoritative; derivation will fail closed.
        pass
    finally:
        client.close()
    frames = client.transcript()
    if not frames:
        raise RuntimeBoundaryError("app-server produced no zero-turn transcript")
    return sdk_profile_evidence_from_transcript(
        frames,
        W=Path(manifest.W.resolved_absolute_path),
        resolved_executable_sha256=manifest.runtime.executable_sha256,
        config_identity_sha256=sha256_bytes(canonical_json_bytes(manifest.configuration)),
        app_server_started=started,
    )


def collect_effective_policy_surfaces(
    manifest: RuntimeBoundaryProbeManifest,
    *,
    source_environment: Mapping[str, str] | None = None,
) -> tuple[EffectivePolicyEvidence, EmbeddedJsonEvidence, EmbeddedJsonEvidence]:
    """Collect redacted effective policy plus raw non-secret readiness surfaces."""

    verify_pinned_runtime_identity(manifest.runtime)
    environment = build_sanitized_environment(
        manifest.environment_name_allowlist,
        source=source_environment,
    )
    client = _new_recording_client(manifest, environment)
    try:
        client.start()
        client.initialize()
        client._request_raw(
            "config/read",
            {"cwd": manifest.W.resolved_absolute_path, "includeLayers": True},
        )
        client._request_raw("configRequirements/read", None)
        client._request_raw("windowsSandbox/readiness", None)
    finally:
        client.close()
    frames = client.transcript()
    config_response = _response_frame_for_method(frames, "config/read")
    requirements_response = _response_frame_for_method(frames, "configRequirements/read")
    readiness_response = _response_frame_for_method(frames, "windowsSandbox/readiness")
    redacted_config_response = redact_sensitive_json(config_response)
    managed_identity = PolicySourceIdentity(
        kind="configRequirements/read",
        version=PINNED_CODEX_VERSION,
        sha256=sha256_bytes(canonical_json_bytes(redact_sensitive_json(requirements_response))),
    )
    projection = project_effective_policy(
        _json_object(redacted_config_response, "redacted config/read response"),
        managed_source_identities=[managed_identity],
    )
    policy = effective_policy_evidence_from_projection(
        projection,
        source_response_sha256=sha256_bytes(canonical_json_bytes(redacted_config_response)),
    )
    return (
        policy,
        EmbeddedJsonEvidence.from_value(requirements_response),
        EmbeddedJsonEvidence.from_value(readiness_response),
    )


def observe_controller_process_identity(
    manifest: RuntimeBoundaryProbeManifest,
) -> WindowsProcessIdentityObservation:
    """Call the frozen helper's Win32 observer in this Controller process."""

    verify_probe_command_contract(manifest)
    script = (
        Path(manifest.W.resolved_absolute_path) / manifest.probe_script_relative_path
    ).resolve()
    module_name = f"_runtime_boundary_probe_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, script)
    if spec is None or spec.loader is None:
        raise RuntimeBoundaryError("cannot load the frozen process identity observer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    observer = getattr(module, "observe_process_identity", None)
    if not callable(observer):
        raise RuntimeBoundaryError("frozen probe lacks the process identity observer")
    return WindowsProcessIdentityObservation.model_validate(observer())


def _file_matches(path: Path, *, size: int, sha256: str) -> bool:
    try:
        return path.is_file() and path.stat().st_size == size and sha256_file(path) == sha256
    except OSError:
        return False


def _probe_precondition(manifest: RuntimeBoundaryProbeManifest, probe_id: str) -> bool:
    W = Path(manifest.W.resolved_absolute_path)
    J = Path(manifest.J.resolved_absolute_path)
    S = Path(manifest.S.resolved_absolute_path)
    W_sentinel = W / manifest.W_sentinel.relative_path
    J_sentinel = J / manifest.J_sentinel.relative_path
    S_sentinel = S / manifest.S_sentinel.relative_path
    if not _file_matches(
        W_sentinel,
        size=manifest.W_sentinel.size,
        sha256=manifest.W_sentinel.sha256,
    ):
        return False
    if probe_id in {"P02", "P03", "P04", "P05", "P06", "P07"} and not _file_matches(
        J_sentinel,
        size=manifest.J_sentinel.size,
        sha256=manifest.J_sentinel.sha256,
    ):
        return False
    if probe_id == "P05":
        return not any(
            (W / value).exists() or (W / value).is_symlink()
            for value in (
                manifest.fixtures.p05_symlink_path,
                manifest.fixtures.p05_junction_path,
            )
        )
    if probe_id == "P08":
        source = W / manifest.fixtures.p08_replace_source
        target = S / manifest.fixtures.p08_replace_target
        create = S / manifest.fixtures.p08_create_target
        return (
            _file_matches(
                S_sentinel,
                size=manifest.S_sentinel.size,
                sha256=manifest.S_sentinel.sha256,
            )
            and not create.exists()
            and _file_matches(
                source,
                size=manifest.fixtures.p08_replace_source_size,
                sha256=manifest.fixtures.p08_replace_source_sha256,
            )
            and _file_matches(
                target,
                size=manifest.fixtures.p08_replace_target_size,
                sha256=manifest.fixtures.p08_replace_target_sha256,
            )
        )
    return True


def _probe_postcondition(manifest: RuntimeBoundaryProbeManifest, probe_id: str) -> bool:
    # The frozen Controller conditions are symmetric except for the attempted operations.
    return _probe_precondition(manifest, probe_id)


def _drain_binary_stream(
    stream: Any,
    *,
    limit: int,
    destination: queue.Queue[tuple[bytes, int, str]],
) -> None:
    captured = bytearray()
    total = 0
    digest = hashlib.sha256()
    try:
        while True:
            chunk = stream.read(8192)
            if not chunk:
                break
            total += len(chunk)
            digest.update(chunk)
            if len(captured) < limit + 1:
                captured.extend(chunk[: limit + 1 - len(captured)])
    finally:
        destination.put((bytes(captured), total, digest.hexdigest()))


def _run_command_capped(
    argv: Sequence[str],
    *,
    cwd: Path,
    environment: Mapping[str, str],
    timeout_seconds: int,
    limit: int,
) -> tuple[int, bytes, int, str, bytes, int, str, int]:
    started = time.monotonic()
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    process = subprocess.Popen(
        list(argv),
        cwd=cwd,
        env=dict(environment),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=creationflags,
    )
    if process.stdout is None or process.stderr is None:
        process.kill()
        raise RuntimeBoundaryError("probe process streams were not created")
    stdout_queue: queue.Queue[tuple[bytes, int, str]] = queue.Queue(maxsize=1)
    stderr_queue: queue.Queue[tuple[bytes, int, str]] = queue.Queue(maxsize=1)
    stdout_thread = threading.Thread(
        target=_drain_binary_stream,
        kwargs={"stream": process.stdout, "limit": limit, "destination": stdout_queue},
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=_drain_binary_stream,
        kwargs={"stream": process.stderr, "limit": limit, "destination": stderr_queue},
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()
    try:
        return_code = process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        process.kill()
        process.wait(timeout=2)
        raise RuntimeBoundaryError("runtime-boundary probe timed out") from exc
    stdout_thread.join(timeout=2)
    stderr_thread.join(timeout=2)
    if stdout_thread.is_alive() or stderr_thread.is_alive():
        raise RuntimeBoundaryError("runtime-boundary stream collector did not stop")
    stdout, stdout_total, stdout_hash = stdout_queue.get_nowait()
    stderr, stderr_total, stderr_hash = stderr_queue.get_nowait()
    duration_ms = int((time.monotonic() - started) * 1000)
    return (
        return_code,
        stdout,
        stdout_total,
        stdout_hash,
        stderr,
        stderr_total,
        stderr_hash,
        duration_ms,
    )


def execute_frozen_probe_command(
    manifest: RuntimeBoundaryProbeManifest,
    command: ProbeCommandSpec,
    *,
    source_environment: Mapping[str, str] | None = None,
) -> ProbeResult:
    """Execute one frozen probe exactly once; the caller owns sequencing and stop rules."""

    verify_pinned_runtime_identity(manifest.runtime)
    verify_probe_command_contract(manifest)
    expected_command = manifest.commands[EXACT_PROBE_IDS.index(command.probe_id)]
    if command != expected_command:
        raise RuntimeBoundaryError("requested probe command is not the frozen manifest entry")
    environment = build_sanitized_environment(
        manifest.environment_name_allowlist,
        source=source_environment,
    )
    precondition = _probe_precondition(manifest, command.probe_id)
    if not precondition:
        raise RuntimeBoundaryError(
            f"{command.probe_id} Controller precondition failed before dispatch"
        )
    S_sentinel_path = (
        Path(manifest.S.resolved_absolute_path) / manifest.S_sentinel.relative_path
    )
    S_before = sha256_file(S_sentinel_path) if command.probe_id == "P08" else None
    (
        wrapper_exit_code,
        stdout,
        stdout_total,
        stdout_hash,
        _stderr,
        stderr_total,
        stderr_hash,
        duration_ms,
    ) = _run_command_capped(
        command.argv,
        cwd=Path(manifest.W.resolved_absolute_path),
        environment=environment,
        timeout_seconds=manifest.timeout_seconds_per_probe,
        limit=manifest.stdout_limit_bytes,
    )
    stdout_truncated = stdout_total > manifest.stdout_limit_bytes
    stderr_truncated = stderr_total > manifest.stderr_limit_bytes
    if stdout_truncated:
        raise RuntimeBoundaryError("runtime-boundary probe stdout exceeded the frozen limit")
    try:
        raw = json.loads(stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeBoundaryError("runtime-boundary probe stdout is not one JSON object") from exc
    payload = _json_object(raw, "runtime-boundary probe output")
    operation_payload = _json_object(payload.get("payload"), "runtime-boundary operation payload")
    identity = WindowsProcessIdentityObservation.model_validate(
        payload.get("sandbox_process_identity")
    )
    operation_exit_code = payload.get("operation_exit_code")
    if not isinstance(operation_exit_code, int):
        raise RuntimeBoundaryError("runtime-boundary operation exit code is missing")
    process = ProbeProcessObservation(
        wrapper_exit_code=wrapper_exit_code,
        operation_exit_code=operation_exit_code,
        stdout_size=min(stdout_total, manifest.stdout_limit_bytes),
        stdout_sha256=stdout_hash,
        stdout_truncated=stdout_truncated,
        stderr_size=min(stderr_total, manifest.stderr_limit_bytes),
        stderr_sha256=stderr_hash,
        stderr_truncated=stderr_truncated,
        duration_ms=duration_ms,
        sandbox_process_identity=identity,
    )
    postcondition = _probe_postcondition(manifest, command.probe_id)
    common: dict[str, Any] = {
        "probe_id": command.probe_id,
        "argv_sha256": command.argv_sha256,
        "expected_class": command.expected_class,
        "process": process,
        "controller_precondition_ok": precondition,
        "controller_postcondition_ok": postcondition,
        "derived_passed": False,
    }
    if command.probe_id == "P01":
        common.update(path_role="W_sentinel", read=operation_payload.get("read"))
    elif command.probe_id == "P02":
        common.update(path_role="J_sentinel_absolute", read=operation_payload.get("read"))
    elif command.probe_id == "P03":
        argv = command.argv
        base = Path(argv[argv.index("--base") + 1])
        relative = argv[argv.index("--relative") + 1]
        normalized = (base / relative).resolve()
        expected = (
            Path(manifest.J.resolved_absolute_path) / manifest.J_sentinel.relative_path
        ).resolve()
        common.update(
            path_role="J_sentinel_relative_from_W",
            normalized_target_path_id=_sha_text(os.path.normcase(str(normalized))),
            normalized_target_equals_manifest_J=(
                os.path.normcase(str(normalized)) == os.path.normcase(str(expected))
            ),
            read=operation_payload.get("read"),
        )
    elif command.probe_id == "P04":
        raw_targets = operation_payload.get("targets")
        if not isinstance(raw_targets, list) or len(raw_targets) != 2:
            raise RuntimeBoundaryError("P04 did not return two enumeration targets")
        common["targets"] = [
            {"role": role, **_json_object(value, "P04 target")}
            for role, value in zip(("common_parent", "drive_root"), raw_targets, strict=True)
        ]
    elif command.probe_id == "P05":
        common["attempts"] = operation_payload.get("attempts")
    elif command.probe_id == "P06":
        child_identity_raw = operation_payload.get("child_process_identity")
        child_identity = (
            WindowsProcessIdentityObservation.model_validate(child_identity_raw)
            if child_identity_raw is not None
            else None
        )
        common.update(
            child_spawn_outcome=operation_payload.get("child_spawn_outcome"),
            child_exit_code=operation_payload.get("child_exit_code"),
            child_process_identity=child_identity,
            parent_child_identity_equal=(
                child_identity is not None
                and child_identity.identity_sha256 == identity.identity_sha256
            ),
            child_read=operation_payload.get("child_read"),
        )
    elif command.probe_id == "P07":
        common.update(operation_payload)
    elif command.probe_id == "P08":
        S_after = sha256_file(S_sentinel_path) if S_sentinel_path.is_file() else "0" * 64
        common.update(
            read=operation_payload.get("read"),
            create=operation_payload.get("create"),
            replace=operation_payload.get("replace"),
            S_sentinel_sha256_before=S_before,
            S_sentinel_sha256_after=S_after,
        )
    else:
        raise AssertionError(f"unhandled probe ID: {command.probe_id}")
    parsed = PROBE_RESULT_ADAPTER.validate_python(common)
    return parsed.model_copy(update={"derived_passed": recompute_probe_pass(manifest, parsed)})


def _json_object(value: JsonValue, label: str) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _request_key(value: JsonValue) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _response_for_request(
    frames: Sequence[JsonRpcFrameEvidence],
    request: dict[str, JsonValue],
) -> dict[str, JsonValue] | None:
    request_id = request.get("id")
    for frame in frames:
        message = _json_object(frame.message.json_value(), "JSON-RPC frame")
        if (
            frame.direction == "server_to_client"
            and "method" not in message
            and message.get("id") == request_id
        ):
            return message
    return None


def _requests(
    frames: Sequence[JsonRpcFrameEvidence], method: str
) -> list[dict[str, JsonValue]]:
    values: list[dict[str, JsonValue]] = []
    for frame in frames:
        message = _json_object(frame.message.json_value(), "JSON-RPC frame")
        if (
            frame.direction == "client_to_server"
            and message.get("method") == method
            and "id" in message
        ):
            values.append(message)
    return values


def _notifications(
    frames: Sequence[JsonRpcFrameEvidence],
    method: str,
    *,
    direction: Literal["client_to_server", "server_to_client"] = "server_to_client",
) -> list[dict[str, JsonValue]]:
    values: list[dict[str, JsonValue]] = []
    for frame in frames:
        message = _json_object(frame.message.json_value(), "JSON-RPC frame")
        if (
            frame.direction == direction
            and message.get("method") == method
            and "id" not in message
        ):
            values.append(message)
    return values


def derive_json_rpc_method_ledger(
    frames: Sequence[JsonRpcFrameEvidence],
) -> JsonRpcMethodLedger:
    client_request_ids: set[str] = set()
    client_requests: dict[str, int] = {}
    client_notifications: dict[str, int] = {}
    server_requests: dict[str, int] = {}
    server_notifications: dict[str, int] = {}
    response_count = 0
    unmatched_response_count = 0

    for frame in frames:
        message = _json_object(frame.message.json_value(), "JSON-RPC frame")
        method = message.get("method")
        has_id = "id" in message
        if frame.direction == "client_to_server":
            if isinstance(method, str):
                target = client_requests if has_id else client_notifications
                target[method] = target.get(method, 0) + 1
                if has_id:
                    client_request_ids.add(_request_key(message.get("id")))
        elif isinstance(method, str):
            target = server_requests if has_id else server_notifications
            target[method] = target.get(method, 0) + 1
        elif has_id:
            response_count += 1
            if _request_key(message.get("id")) not in client_request_ids:
                unmatched_response_count += 1

    return JsonRpcMethodLedger(
        frame_count=len(frames),
        client_request_method_counts=dict(sorted(client_requests.items())),
        client_notification_method_counts=dict(sorted(client_notifications.items())),
        server_request_method_counts=dict(sorted(server_requests.items())),
        server_notification_method_counts=dict(sorted(server_notifications.items())),
        server_response_count=response_count,
        unmatched_server_response_count=unmatched_response_count,
    )


def _result_object(
    response: dict[str, JsonValue] | None,
    label: str,
) -> dict[str, JsonValue]:
    if response is None or "error" in response:
        return {}
    result = response.get("result")
    return result if isinstance(result, dict) else {}


def _account_type_from_response(response: dict[str, JsonValue] | None) -> str:
    result = _result_object(response, "account/read response")
    account = result.get("account")
    if not isinstance(account, dict):
        return "unknown"
    value = account.get("type")
    if value == "chatgpt":
        return "chatgpt"
    if value == "apiKey":
        return "apikey"
    return "unknown"


def _approval_mode(value: JsonValue) -> Literal["deny_all", "other", "unknown"]:
    if value == "never":
        return "deny_all"
    if value is None:
        return "unknown"
    return "other"


def derive_sdk_profile_provenance(
    transcript: Sequence[JsonRpcFrameEvidence],
    *,
    W: Path,
) -> dict[str, Any]:
    frames = list(transcript)
    ledger = derive_json_rpc_method_ledger(frames)
    initialize_requests = _requests(frames, "initialize")
    account_requests = _requests(frames, "account/read")
    thread_requests = _requests(frames, "thread/start")
    turn_requests = _requests(frames, "turn/start")
    settings_notifications = _notifications(frames, PROFILE_NOTIFICATION_METHOD)
    initialized_notifications = _notifications(
        frames,
        "initialized",
        direction="client_to_server",
    )

    initialize_experimental = False
    if len(initialize_requests) == 1:
        params = initialize_requests[0].get("params")
        if isinstance(params, dict):
            capabilities = params.get("capabilities")
            if isinstance(capabilities, dict):
                initialize_experimental = capabilities.get("experimentalApi") is True

    account_response = (
        _response_for_request(frames, account_requests[0]) if len(account_requests) == 1 else None
    )
    account_type = _account_type_from_response(account_response)

    thread_params: dict[str, JsonValue] = {}
    thread_response: dict[str, JsonValue] | None = None
    response_thread_id: str | None = None
    if len(thread_requests) == 1:
        raw_params = thread_requests[0].get("params")
        if isinstance(raw_params, dict):
            thread_params = raw_params
        thread_response = _response_for_request(frames, thread_requests[0])
        thread_result = _result_object(thread_response, "thread/start response")
        thread = thread_result.get("thread")
        if isinstance(thread, dict) and isinstance(thread.get("id"), str):
            response_thread_id = str(thread["id"])

    notification_thread_id: str | None = None
    active_profile: str | None = None
    approval_raw: JsonValue = None
    observed_cwd: str | None = None
    if len(settings_notifications) == 1:
        params = settings_notifications[0].get("params")
        if isinstance(params, dict):
            if isinstance(params.get("threadId"), str):
                notification_thread_id = str(params["threadId"])
            settings = params.get("threadSettings")
            if isinstance(settings, dict):
                active = settings.get("activePermissionProfile")
                if isinstance(active, dict) and isinstance(active.get("id"), str):
                    active_profile = str(active["id"])
                approval_raw = settings.get("approvalPolicy")
                if isinstance(settings.get("cwd"), str):
                    observed_cwd = str(settings["cwd"])

    response_hash = _sha_text(response_thread_id) if response_thread_id is not None else None
    notification_hash = (
        _sha_text(notification_thread_id) if notification_thread_id is not None else None
    )
    thread_ids_equal = (
        response_thread_id is not None
        and notification_thread_id is not None
        and response_thread_id == notification_thread_id
    )
    sandbox_present = "sandbox" in thread_params
    cwd_equal = observed_cwd is not None and Path(observed_cwd).resolve() == W.resolve()
    config = thread_params.get("config")
    request_default_permissions = (
        config.get("default_permissions") if isinstance(config, dict) else None
    )
    request_contract_ok = (
        thread_params.get("cwd") == str(W.resolve())
        and thread_params.get("approvalPolicy") == "never"
        and request_default_permissions == PERMISSION_PROFILE_ID
        and not sandbox_present
    )
    passed = all(
        (
            len(initialize_requests) == 1,
            initialize_experimental,
            _response_for_request(frames, initialize_requests[0]) is not None
            if len(initialize_requests) == 1
            else False,
            len(initialized_notifications) == 1,
            len(account_requests) == 1,
            account_type == "chatgpt",
            account_response is not None,
            len(thread_requests) == 1,
            thread_response is not None,
            len(settings_notifications) == 1,
            len(turn_requests) == 0,
            request_contract_ok,
            thread_ids_equal,
            active_profile == PERMISSION_PROFILE_ID,
            approval_raw == "never",
            cwd_equal,
            ledger.client_request_method_counts
            == {"account/read": 1, "initialize": 1, "thread/start": 1},
            ledger.client_notification_method_counts == {"initialized": 1},
            ledger.server_request_method_counts == {},
            ledger.server_response_count == 3,
            ledger.unmatched_server_response_count == 0,
        )
    )
    return {
        "method_ledger": ledger,
        "account_type_raw": account_type,
        "initialize_experimental_api": initialize_experimental,
        "thread_start_request_count": len(thread_requests),
        "settings_notification_count": len(settings_notifications),
        "turn_start_request_count": len(turn_requests),
        "thread_start_response_thread_id_sha256": response_hash,
        "settings_notification_thread_id_sha256": notification_hash,
        "thread_id_binding_equal": thread_ids_equal,
        "sandbox_key_present_in_thread_start_request": sandbox_present,
        "active_permission_profile_id": active_profile,
        "approval_policy_raw": approval_raw,
        "approval_mode_normalized": _approval_mode(approval_raw),
        "observed_cwd": observed_cwd,
        "observed_cwd_equals_W": cwd_equal,
        "legacy_response_sandbox_used_as_provenance": False,
        "actual_model_turns": len(turn_requests),
        "derived_profile_passed": passed,
    }


def sdk_profile_evidence_from_transcript(
    frames: Sequence[
        tuple[
            Literal["client_to_server", "server_to_client"],
            dict[str, JsonValue],
        ]
    ],
    *,
    W: Path,
    resolved_executable_sha256: str,
    config_identity_sha256: str,
    app_server_started: bool = True,
) -> SdkProfileProvenanceObservation:
    transcript = [
        JsonRpcFrameEvidence(
            sequence=index,
            direction=direction,
            message=EmbeddedJsonEvidence.from_value(frame),
        )
        for index, (direction, frame) in enumerate(frames)
    ]
    derived = derive_sdk_profile_provenance(transcript, W=W)
    return SdkProfileProvenanceObservation(
        transcript=transcript,
        transcript_complete=True,
        app_server_started=app_server_started,
        resolved_executable_sha256=resolved_executable_sha256,
        config_identity_sha256=config_identity_sha256,
        **derived,
    )


def verify_sdk_profile_provenance(
    manifest: RuntimeBoundaryProbeManifest,
    evidence: SdkProfileProvenanceObservation,
) -> bool:
    derived = derive_sdk_profile_provenance(
        evidence.transcript,
        W=Path(manifest.W.resolved_absolute_path),
    )
    for field, value in derived.items():
        if getattr(evidence, field) != value:
            raise RuntimeBoundaryError(f"SDK profile derived field mismatch: {field}")
    if evidence.resolved_executable_sha256 != manifest.runtime.executable_sha256:
        raise RuntimeBoundaryError("SDK profile executable identity mismatch")
    expected_config_identity = sha256_bytes(canonical_json_bytes(manifest.configuration))
    if evidence.config_identity_sha256 != expected_config_identity:
        raise RuntimeBoundaryError("SDK profile configuration identity mismatch")
    return evidence.app_server_started and bool(derived["derived_profile_passed"])


_SENSITIVE_KEY_PARTS = (
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "credential",
    "password",
    "secret",
    "token",
)


def redact_sensitive_json(value: JsonValue) -> JsonValue:
    """Remove secret-bearing values before policy evidence is persisted or hashed."""

    if isinstance(value, list):
        return [redact_sensitive_json(item) for item in value]
    if isinstance(value, dict):
        redacted: dict[str, JsonValue] = {}
        for key, item in value.items():
            normalized = key.lower().replace("-", "_")
            if any(part in normalized for part in _SENSITIVE_KEY_PARTS):
                redacted[key] = "<redacted>"
            else:
                redacted[key] = redact_sensitive_json(item)
        return redacted
    return value


def _source_identities(layers: JsonValue) -> list[PolicySourceIdentity]:
    if not isinstance(layers, list):
        return []
    identities: list[PolicySourceIdentity] = []
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        name = layer.get("name")
        kind = "unknown"
        if isinstance(name, dict) and isinstance(name.get("type"), str):
            kind = str(name["type"])
        version = str(layer.get("version") or "unknown")
        config = redact_sensitive_json(layer.get("config"))
        identities.append(
            PolicySourceIdentity(
                kind=kind,
                version=version,
                sha256=sha256_bytes(canonical_json_bytes(config)),
            )
        )
    return sorted(identities, key=lambda item: (item.kind, item.version, item.sha256))


def project_effective_policy(
    config_read_response: dict[str, JsonValue],
    *,
    managed_source_identities: Sequence[PolicySourceIdentity] = (),
) -> EffectivePolicyProjection:
    result = _result_object(config_read_response, "config/read response")
    config = result.get("config")
    config_obj = config if isinstance(config, dict) else {}
    windows = config_obj.get("windows")
    windows_obj = windows if isinstance(windows, dict) else {}
    default_permissions = config_obj.get("default_permissions")
    if default_permissions is None:
        default_permissions = config_obj.get("defaultPermissions")
    return EffectivePolicyProjection(
        source_method="config/read",
        default_permissions=(
            str(default_permissions) if isinstance(default_permissions, str) else None
        ),
        permission_profile_id=(
            str(default_permissions) if isinstance(default_permissions, str) else None
        ),
        windows_sandbox=(
            str(windows_obj.get("sandbox"))
            if isinstance(windows_obj.get("sandbox"), str)
            else None
        ),
        legacy_sandbox_mode_present=(
            "sandbox_mode" in config_obj or "sandboxMode" in config_obj
        ),
        legacy_sandbox_workspace_write_present=(
            "sandbox_workspace_write" in config_obj
            or "sandboxWorkspaceWrite" in config_obj
        ),
        config_source_identities=_source_identities(result.get("layers")),
        managed_source_identities=sorted(
            set(managed_source_identities),
            key=lambda item: (item.kind, item.version, item.sha256),
        ),
    )


def effective_policy_evidence_from_projection(
    projection: EffectivePolicyProjection,
    *,
    source_response_sha256: str,
) -> EffectivePolicyEvidence:
    passed = (
        projection.default_permissions == PERMISSION_PROFILE_ID
        and projection.permission_profile_id == PERMISSION_PROFILE_ID
        and projection.windows_sandbox == WINDOWS_SANDBOX_KIND
        and not projection.legacy_sandbox_mode_present
        and not projection.legacy_sandbox_workspace_write_present
        and bool(projection.config_source_identities)
        and bool(projection.managed_source_identities)
    )
    return EffectivePolicyEvidence(
        projection=EmbeddedJsonEvidence.from_value(projection),
        source_response_sha256=source_response_sha256,
        default_permissions=projection.default_permissions,
        permission_profile_id=projection.permission_profile_id,
        windows_sandbox=projection.windows_sandbox,
        legacy_sandbox_mode_present=projection.legacy_sandbox_mode_present,
        legacy_sandbox_workspace_write_present=(
            projection.legacy_sandbox_workspace_write_present
        ),
        derived_policy_passed=passed,
    )


def verify_effective_policy(
    evidence: EffectivePolicyEvidence,
    *,
    configuration: ConfigurationExpectation | None = None,
) -> bool:
    projection = EffectivePolicyProjection.model_validate(evidence.projection.json_value())
    expected = effective_policy_evidence_from_projection(
        projection,
        source_response_sha256=evidence.source_response_sha256,
    )
    for field in (
        "default_permissions",
        "permission_profile_id",
        "windows_sandbox",
        "legacy_sandbox_mode_present",
        "legacy_sandbox_workspace_write_present",
        "derived_policy_passed",
    ):
        if getattr(evidence, field) != getattr(expected, field):
            raise RuntimeBoundaryError(f"effective policy derived field mismatch: {field}")
    if configuration is not None:
        if evidence.default_permissions != configuration.default_permissions:
            raise RuntimeBoundaryError("effective default permissions differ from manifest")
        if evidence.permission_profile_id != configuration.permission_profile_name:
            raise RuntimeBoundaryError("effective permission profile differs from manifest")
    return evidence.derived_policy_passed


def _response_result(value: EmbeddedJsonEvidence) -> dict[str, JsonValue]:
    frame = _json_object(value.json_value(), "app-server response")
    return _result_object(frame, "app-server response")


def _allowed_windows_implementations(
    evidence: EmbeddedJsonEvidence,
) -> list[str] | None:
    result = _response_result(evidence)
    if "requirements" not in result:
        return []
    requirements = result.get("requirements")
    if requirements is None:
        return None
    if not isinstance(requirements, dict):
        return []
    value = requirements.get("allowedWindowsSandboxImplementations")
    if value is None:
        value = requirements.get("allowed_windows_sandbox_implementations")
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return []
    return [str(item) for item in value]


def _readiness_status(evidence: EmbeddedJsonEvidence) -> str | None:
    result = _response_result(evidence)
    status = result.get("status")
    return str(status) if isinstance(status, str) else None


def _classification_payload(
    *,
    effective_policy: EffectivePolicyEvidence,
    requirements: EmbeddedJsonEvidence,
    readiness: EmbeddedJsonEvidence,
    controller: WindowsProcessIdentityObservation,
    P01: WindowsProcessIdentityObservation,
    all_probe_equal: bool,
    P06_child_equal: bool,
) -> dict[str, JsonValue]:
    return {
        "effective_policy_sha256": effective_policy.projection.sha256,
        "requirements_sha256": requirements.sha256,
        "readiness_sha256": readiness.sha256,
        "controller_identity_sha256": controller.identity_sha256,
        "P01_identity_sha256": P01.identity_sha256,
        "all_probe_process_identities_equal_P01": all_probe_equal,
        "P06_parent_child_identity_equal": P06_child_equal,
    }


def derive_windows_sandbox_kind(
    *,
    effective_policy: EffectivePolicyEvidence,
    config_requirements_response: EmbeddedJsonEvidence,
    readiness_response: EmbeddedJsonEvidence,
    controller_process_identity: WindowsProcessIdentityObservation,
    P01_process_identity: WindowsProcessIdentityObservation,
    all_probe_process_identities_equal_P01: bool,
    P06_parent_child_identity_equal: bool,
) -> tuple[Literal["elevated", "unelevated", "unknown"], bool, str]:
    policy_ok = verify_effective_policy(effective_policy)
    allowed = _allowed_windows_implementations(config_requirements_response)
    requirements_ok = allowed is None or WINDOWS_SANDBOX_KIND in allowed
    readiness_ok = _readiness_status(readiness_response) == "ready"
    sid_differs = (
        controller_process_identity.token_user_sid
        != P01_process_identity.token_user_sid
    )
    payload = _classification_payload(
        effective_policy=effective_policy,
        requirements=config_requirements_response,
        readiness=readiness_response,
        controller=controller_process_identity,
        P01=P01_process_identity,
        all_probe_equal=all_probe_process_identities_equal_P01,
        P06_child_equal=P06_parent_child_identity_equal,
    )
    classification_hash = sha256_bytes(canonical_json_bytes(payload))
    elevated = all(
        (
            policy_ok,
            requirements_ok,
            readiness_ok,
            sid_differs,
            all_probe_process_identities_equal_P01,
            P06_parent_child_identity_equal,
        )
    )
    if elevated:
        return "elevated", True, classification_hash
    if effective_policy.windows_sandbox == "unelevated" or not sid_differs:
        return "unelevated", False, classification_hash
    return "unknown", False, classification_hash


def verify_windows_sandbox_provenance(
    evidence: WindowsSandboxProvenanceObservation,
    *,
    effective_policy: EffectivePolicyEvidence,
) -> bool:
    kind, passed, classification_hash = derive_windows_sandbox_kind(
        effective_policy=effective_policy,
        config_requirements_response=evidence.config_requirements_response,
        readiness_response=evidence.readiness_response,
        controller_process_identity=evidence.controller_process_identity,
        P01_process_identity=evidence.P01_process_identity,
        all_probe_process_identities_equal_P01=(
            evidence.all_probe_process_identities_equal_P01
        ),
        P06_parent_child_identity_equal=evidence.P06_parent_child_identity_equal,
    )
    sid_differs = (
        evidence.controller_process_identity.token_user_sid
        != evidence.P01_process_identity.token_user_sid
    )
    expected = {
        "dedicated_user_sid_differs_from_controller": sid_differs,
        "classification_inputs_sha256": classification_hash,
        "observed_kind": kind,
        "derived_elevation_passed": passed,
    }
    for field, value in expected.items():
        if getattr(evidence, field) != value:
            raise RuntimeBoundaryError(f"Windows sandbox derived field mismatch: {field}")
    return passed


def build_windows_sandbox_provenance(
    *,
    effective_policy: EffectivePolicyEvidence,
    config_requirements_response: EmbeddedJsonEvidence,
    readiness_response: EmbeddedJsonEvidence,
    controller_process_identity: WindowsProcessIdentityObservation,
    probes: Sequence[ProbeResult],
) -> WindowsSandboxProvenanceObservation:
    if tuple(probe.probe_id for probe in probes) != EXACT_PROBE_IDS:
        raise RuntimeBoundaryError("Windows sandbox provenance requires P01 through P08")
    P01_identity = probes[0].process.sandbox_process_identity
    all_probe_equal = all(
        probe.process.sandbox_process_identity.identity_sha256
        == P01_identity.identity_sha256
        for probe in probes
    )
    P06 = probes[5]
    if not isinstance(P06, P06ChildResult):
        raise RuntimeBoundaryError("P06 result has the wrong type")
    P06_equal = (
        P06.child_process_identity is not None
        and P06.child_process_identity.identity_sha256
        == P06.process.sandbox_process_identity.identity_sha256
    )
    kind, passed, classification_hash = derive_windows_sandbox_kind(
        effective_policy=effective_policy,
        config_requirements_response=config_requirements_response,
        readiness_response=readiness_response,
        controller_process_identity=controller_process_identity,
        P01_process_identity=P01_identity,
        all_probe_process_identities_equal_P01=all_probe_equal,
        P06_parent_child_identity_equal=P06_equal,
    )
    return WindowsSandboxProvenanceObservation(
        selection_method="effective_config+readiness+token_user_sid",
        config_requirements_response=config_requirements_response,
        readiness_response=readiness_response,
        controller_process_identity=controller_process_identity,
        P01_process_identity=P01_identity,
        dedicated_user_sid_differs_from_controller=(
            controller_process_identity.token_user_sid != P01_identity.token_user_sid
        ),
        all_probe_process_identities_equal_P01=all_probe_equal,
        P06_parent_child_identity_equal=P06_equal,
        classification_inputs_sha256=classification_hash,
        observed_kind=kind,
        derived_elevation_passed=passed,
    )


def _process_passed(process: ProbeProcessObservation) -> bool:
    return (
        process.wrapper_exit_code == 0
        and process.operation_exit_code == 0
        and not process.stdout_truncated
        and not process.stderr_truncated
    )


def _denied_without_content(read: FileReadObservation) -> bool:
    return (
        read.outcome == "access_denied"
        and read.bytes_read == 0
        and read.content_sha256 is None
    )


def recompute_probe_pass(
    manifest: RuntimeBoundaryProbeManifest,
    probe: ProbeResult,
) -> bool:
    common = (
        _process_passed(probe.process)
        and probe.controller_precondition_ok
        and probe.controller_postcondition_ok
    )
    if not common:
        return False
    if isinstance(probe, P01ReadResult):
        return (
            probe.read.outcome == "success"
            and probe.read.bytes_read == manifest.W_sentinel.size
            and probe.read.content_sha256 == manifest.W_sentinel.sha256
        )
    if isinstance(probe, P02ReadResult):
        return _denied_without_content(probe.read)
    if isinstance(probe, P03ReadResult):
        return probe.normalized_target_equals_manifest_J and _denied_without_content(
            probe.read
        )
    if isinstance(probe, P04EnumerationResult):
        forbidden = _sha_text(Path(manifest.J.resolved_absolute_path).name)
        for target in probe.targets:
            if target.outcome == "access_denied":
                if target.entry_count != 0 or target.entry_name_sha256s:
                    return False
                continue
            if target.outcome != "success" or not target.enumeration_complete:
                return False
            actual_matches = sum(
                1 for value in target.entry_name_sha256s if value == forbidden
            )
            if actual_matches != target.forbidden_name_hash_match_count or actual_matches != 0:
                return False
        return True
    if isinstance(probe, P05LinkResult):
        for attempt in probe.attempts:
            if attempt.create_outcome == "access_denied":
                if attempt.link_exists_after_create:
                    return False
            elif attempt.create_outcome == "success":
                if not attempt.link_exists_after_create or not _denied_without_content(
                    attempt.read
                ):
                    return False
            else:
                return False
            if attempt.link_exists_after_cleanup:
                return False
        return True
    if isinstance(probe, P06ChildResult):
        return (
            probe.child_spawn_outcome == "success"
            and probe.child_exit_code == 0
            and probe.child_process_identity is not None
            and probe.parent_child_identity_equal
            and probe.child_process_identity.identity_sha256
            == probe.process.sandbox_process_identity.identity_sha256
            and _denied_without_content(probe.child_read)
        )
    if isinstance(probe, P07InputScanResult):
        expected = (
            manifest.J_sentinel.sha256,
            manifest.fixtures.p07_expected_answer_sha256,
        )
        return (
            probe.forbidden_value_sha256s == expected
            and probe.environment_scan_complete
            and probe.argument_scan_complete
            and probe.environment_match_count == 0
            and not probe.environment_matching_name_sha256s
            and probe.argument_match_count == 0
            and not probe.argument_matching_index_hashes
        )
    if isinstance(probe, P08StateResult):
        return (
            _denied_without_content(probe.read)
            and probe.create.outcome == "access_denied"
            and not probe.create.target_exists_before
            and not probe.create.target_exists_after
            and probe.replace.outcome == "access_denied"
            and probe.replace.source_exists_before is True
            and probe.replace.source_exists_after is True
            and probe.replace.target_exists_before
            and probe.replace.target_exists_after
            and probe.replace.source_sha256_before
            == manifest.fixtures.p08_replace_source_sha256
            and probe.replace.source_sha256_after
            == manifest.fixtures.p08_replace_source_sha256
            and probe.replace.target_sha256_before
            == manifest.fixtures.p08_replace_target_sha256
            and probe.replace.target_sha256_after
            == manifest.fixtures.p08_replace_target_sha256
            and probe.S_sentinel_sha256_before == manifest.S_sentinel.sha256
            and probe.S_sentinel_sha256_after == manifest.S_sentinel.sha256
        )
    raise AssertionError(f"unhandled probe type: {type(probe).__name__}")


def _has_not_ready_disclosure(probes: Sequence[ProbeResult]) -> bool:
    for probe in probes:
        reads: list[FileReadObservation] = []
        if isinstance(probe, P01ReadResult):
            continue
        if isinstance(probe, (P02ReadResult, P03ReadResult)):
            reads.append(probe.read)
        elif isinstance(probe, P05LinkResult):
            reads.extend(attempt.read for attempt in probe.attempts)
        elif isinstance(probe, P06ChildResult):
            reads.append(probe.child_read)
        elif isinstance(probe, P08StateResult):
            reads.append(probe.read)
            if probe.create.outcome == "success" or probe.replace.outcome == "success":
                return True
        if any(read.bytes_read > 0 for read in reads):
            return True
    return False


def verify_runtime_boundary_result(
    manifest: RuntimeBoundaryProbeManifest,
    result: RuntimeBoundaryProbeResult,
) -> Literal["RUNTIME_BOUNDARY_CANDIDATE", "RUNTIME_BOUNDARY_NOT_PROVEN", "NOT_READY"]:
    manifest_hash = sha256_bytes(canonical_json_bytes(manifest))
    if result.probe_id != manifest.probe_id:
        raise RuntimeBoundaryError("probe ID mismatch")
    if result.manifest_sha256 != manifest_hash:
        raise RuntimeBoundaryError("manifest SHA-256 mismatch")
    runtime_hash = sha256_bytes(canonical_json_bytes(manifest.runtime))
    if result.runtime_identity_sha256 != runtime_hash:
        raise RuntimeBoundaryError("runtime identity SHA-256 mismatch")
    configuration_hash = sha256_bytes(canonical_json_bytes(manifest.configuration))
    if result.configuration_identity_sha256 != configuration_hash:
        raise RuntimeBoundaryError("configuration identity SHA-256 mismatch")

    profile_passed = verify_sdk_profile_provenance(
        manifest,
        result.sdk_profile_provenance,
    )
    policy_passed = verify_effective_policy(
        result.effective_policy,
        configuration=manifest.configuration,
    )

    P01_identity = result.probes[0].process.sandbox_process_identity
    all_probe_equal = all(
        probe.process.sandbox_process_identity.identity_sha256
        == P01_identity.identity_sha256
        for probe in result.probes
    )
    P06 = result.probes[5]
    if not isinstance(P06, P06ChildResult):
        raise RuntimeBoundaryError("P06 result has the wrong type")
    P06_equal = (
        P06.child_process_identity is not None
        and P06.child_process_identity.identity_sha256
        == P06.process.sandbox_process_identity.identity_sha256
    )
    windows = result.windows_sandbox_provenance
    if windows.P01_process_identity != P01_identity:
        raise RuntimeBoundaryError("Windows provenance P01 identity mismatch")
    if windows.all_probe_process_identities_equal_P01 != all_probe_equal:
        raise RuntimeBoundaryError("stored all-probe identity equality mismatch")
    if windows.P06_parent_child_identity_equal != P06_equal:
        raise RuntimeBoundaryError("stored P06 identity equality mismatch")
    elevation_passed = verify_windows_sandbox_provenance(
        windows,
        effective_policy=result.effective_policy,
    )
    if result.windows_sandbox_kind != windows.observed_kind:
        raise RuntimeBoundaryError("Windows sandbox kind mismatch")

    probe_passes: list[bool] = []
    failure_codes: list[str] = []
    for command, probe in zip(manifest.commands, result.probes, strict=True):
        if probe.argv_sha256 != command.argv_sha256:
            raise RuntimeBoundaryError(
                f"{probe.probe_id} argv identity differs from the manifest"
            )
        if probe.expected_class != command.expected_class:
            raise RuntimeBoundaryError(
                f"{probe.probe_id} expected class differs from the manifest"
            )
        expected = recompute_probe_pass(manifest, probe)
        if probe.derived_passed != expected:
            raise RuntimeBoundaryError(
                f"stored {probe.probe_id} pass differs from verifier calculation"
            )
        probe_passes.append(expected)
        if not expected:
            failure_codes.append(f"{probe.probe_id}_FAILED")
    if not profile_passed:
        failure_codes.append("SDK_PROFILE_NOT_PROVEN")
    if not policy_passed:
        failure_codes.append("EFFECTIVE_POLICY_NOT_PROVEN")
    if not elevation_passed:
        failure_codes.append("ELEVATED_NOT_PROVEN")
    if result.actual_model_turns != result.sdk_profile_provenance.actual_model_turns:
        raise RuntimeBoundaryError("actual model-turn count mismatch")
    if result.actual_model_turns != 0:
        failure_codes.append("MODEL_TURN_OBSERVED")

    if _has_not_ready_disclosure(result.probes):
        status = "NOT_READY"
        failure_codes.append("BOUNDARY_DISCLOSURE_OR_MUTATION")
    elif (
        profile_passed
        and policy_passed
        and elevation_passed
        and all(probe_passes)
        and result.actual_model_turns == 0
    ):
        status = "RUNTIME_BOUNDARY_CANDIDATE"
    else:
        status = "RUNTIME_BOUNDARY_NOT_PROVEN"
    expected_codes = sorted(set(failure_codes))
    if result.aggregate_status != status:
        raise RuntimeBoundaryError("stored aggregate status differs from verifier calculation")
    if result.failure_reason_codes != expected_codes:
        raise RuntimeBoundaryError("stored failure reason codes differ from verifier calculation")
    return status


def result_with_recomputed_verdict(
    manifest: RuntimeBoundaryProbeManifest,
    result: RuntimeBoundaryProbeResult,
) -> RuntimeBoundaryProbeResult:
    probes = [
        probe.model_copy(update={"derived_passed": recompute_probe_pass(manifest, probe)})
        for probe in result.probes
    ]
    provisional = result.model_copy(
        update={
            "probes": probes,
            "aggregate_status": "RUNTIME_BOUNDARY_NOT_PROVEN",
            "failure_reason_codes": [],
        }
    )
    try:
        verify_runtime_boundary_result(manifest, provisional)
    except RuntimeBoundaryError as exc:
        # Derive status/codes without trusting the caller's placeholders.
        text = str(exc)
        if "stored aggregate status" not in text and "failure reason codes" not in text:
            raise
    profile = verify_sdk_profile_provenance(manifest, provisional.sdk_profile_provenance)
    policy = verify_effective_policy(
        provisional.effective_policy,
        configuration=manifest.configuration,
    )
    elevation = verify_windows_sandbox_provenance(
        provisional.windows_sandbox_provenance,
        effective_policy=provisional.effective_policy,
    )
    codes = [f"{probe.probe_id}_FAILED" for probe in probes if not probe.derived_passed]
    if not profile:
        codes.append("SDK_PROFILE_NOT_PROVEN")
    if not policy:
        codes.append("EFFECTIVE_POLICY_NOT_PROVEN")
    if not elevation:
        codes.append("ELEVATED_NOT_PROVEN")
    if provisional.actual_model_turns != 0:
        codes.append("MODEL_TURN_OBSERVED")
    if _has_not_ready_disclosure(probes):
        status = "NOT_READY"
        codes.append("BOUNDARY_DISCLOSURE_OR_MUTATION")
    elif profile and policy and elevation and all(item.derived_passed for item in probes):
        status = "RUNTIME_BOUNDARY_CANDIDATE"
    else:
        status = "RUNTIME_BOUNDARY_NOT_PROVEN"
    completed = provisional.model_copy(
        update={
            "aggregate_status": status,
            "failure_reason_codes": sorted(set(codes)),
        }
    )
    verify_runtime_boundary_result(manifest, completed)
    return completed


def execute_runtime_boundary_probe(
    manifest: RuntimeBoundaryProbeManifest,
    bundle_root: Path,
    *,
    confirm_model_free_probe: bool = False,
    source_environment: Mapping[str, str] | None = None,
) -> RuntimeBoundaryProbeResult:
    """Execute Phase B once, with no retry and no model turn.

    The explicit confirmation is intentionally separate from model-usage approval.
    This function never calls ``turn/start``; the transcript verifier enforces that.
    """

    if not confirm_model_free_probe:
        raise RuntimeBoundaryError("explicit model-free probe approval is required")
    verify_pinned_runtime_identity(manifest.runtime)
    verify_probe_command_contract(manifest)
    started_at = utc_now()
    profile = collect_sdk_profile_provenance(
        manifest,
        source_environment=source_environment,
    )
    if not verify_sdk_profile_provenance(manifest, profile):
        raise RuntimeBoundaryError("SDK :workspace profile provenance was not proven")
    policy, requirements, readiness = collect_effective_policy_surfaces(
        manifest,
        source_environment=source_environment,
    )
    if not verify_effective_policy(policy, configuration=manifest.configuration):
        raise RuntimeBoundaryError("effective :workspace/elevated policy was not proven")
    if _readiness_status(readiness) != "ready":
        raise RuntimeBoundaryError("native Windows sandbox is not ready")
    allowed = _allowed_windows_implementations(requirements)
    if allowed is not None and WINDOWS_SANDBOX_KIND not in allowed:
        raise RuntimeBoundaryError("managed requirements disallow the elevated sandbox")

    controller_identity = observe_controller_process_identity(manifest)
    probes: list[ProbeResult] = []
    for command in manifest.commands:
        probe = execute_frozen_probe_command(
            manifest,
            command,
            source_environment=source_environment,
        )
        probes.append(probe)
        if _has_not_ready_disclosure(probes):
            raise RuntimeBoundaryError(
                f"{command.probe_id} disclosed or mutated a Controller-only boundary; NOT_READY"
            )

    windows = build_windows_sandbox_provenance(
        effective_policy=policy,
        config_requirements_response=requirements,
        readiness_response=readiness,
        controller_process_identity=controller_identity,
        probes=probes,
    )
    provisional = RuntimeBoundaryProbeResult(
        probe_id=manifest.probe_id,
        manifest_sha256=sha256_bytes(canonical_json_bytes(manifest)),
        started_at=started_at,
        completed_at=utc_now(),
        runtime_identity_sha256=sha256_bytes(canonical_json_bytes(manifest.runtime)),
        configuration_identity_sha256=sha256_bytes(
            canonical_json_bytes(manifest.configuration)
        ),
        sdk_profile_provenance=profile,
        effective_policy=policy,
        windows_sandbox_provenance=windows,
        windows_sandbox_kind=windows.observed_kind,
        actual_model_turns=profile.actual_model_turns,
        probes=probes,
        aggregate_status="RUNTIME_BOUNDARY_NOT_PROVEN",
        failure_reason_codes=[],
    )
    completed = result_with_recomputed_verdict(manifest, provisional)
    write_runtime_boundary_bundle(bundle_root, manifest, completed)
    return completed


def _files_manifest_bytes(files: Mapping[str, bytes]) -> bytes:
    lines = [f"{sha256_bytes(data)}  {name}" for name, data in sorted(files.items())]
    return ("\n".join(lines) + "\n").encode("utf-8")


def write_runtime_boundary_bundle(
    bundle_root: Path,
    manifest: RuntimeBoundaryProbeManifest,
    result: RuntimeBoundaryProbeResult,
) -> RuntimeBoundaryBundleSeal:
    root = Path(bundle_root)
    if root.exists() and any(root.iterdir()):
        raise RuntimeBoundaryError("runtime-boundary bundle directory must be absent or empty")
    root.mkdir(parents=True, exist_ok=True)
    verify_runtime_boundary_result(manifest, result)
    payloads = {
        "manifest.json": canonical_json_bytes(manifest),
        "result.json": canonical_json_bytes(result),
    }
    files_bytes = _files_manifest_bytes(payloads)
    seal = RuntimeBoundaryBundleSeal(
        probe_id=manifest.probe_id,
        source_commit=manifest.source_commit,
        files_manifest_sha256=sha256_bytes(files_bytes),
        aggregate_sha256=sha256_bytes(files_bytes),
    )
    for name, data in payloads.items():
        atomic_write(root / name, data)
    atomic_write(root / "files.sha256", files_bytes)
    atomic_write(root / "bundle-seal.json", canonical_json_bytes(seal))
    return seal


def verify_runtime_boundary_bundle(
    bundle_root: Path,
) -> tuple[RuntimeBoundaryProbeManifest, RuntimeBoundaryProbeResult, RuntimeBoundaryBundleSeal]:
    root = Path(bundle_root)
    if not root.is_dir():
        raise RuntimeBoundaryError("runtime-boundary bundle directory is missing")
    actual = {path.name for path in root.iterdir() if path.is_file()}
    if actual != EXACT_BUNDLE_FILES:
        raise RuntimeBoundaryError("runtime-boundary bundle file set mismatch")
    if any(path.is_dir() for path in root.iterdir()):
        raise RuntimeBoundaryError("runtime-boundary bundle cannot contain directories")
    manifest = RuntimeBoundaryProbeManifest.model_validate_json(
        (root / "manifest.json").read_bytes()
    )
    result = RuntimeBoundaryProbeResult.model_validate_json((root / "result.json").read_bytes())
    seal = RuntimeBoundaryBundleSeal.model_validate_json(
        (root / "bundle-seal.json").read_bytes()
    )
    payloads = {
        "manifest.json": (root / "manifest.json").read_bytes(),
        "result.json": (root / "result.json").read_bytes(),
    }
    expected_files = _files_manifest_bytes(payloads)
    actual_files = (root / "files.sha256").read_bytes()
    if actual_files != expected_files:
        raise RuntimeBoundaryError("runtime-boundary files.sha256 mismatch")
    if seal.probe_id != manifest.probe_id or seal.source_commit != manifest.source_commit:
        raise RuntimeBoundaryError("runtime-boundary seal identity mismatch")
    if seal.files_manifest_sha256 != sha256_bytes(actual_files):
        raise RuntimeBoundaryError("runtime-boundary seal files hash mismatch")
    if seal.aggregate_sha256 != sha256_bytes(actual_files):
        raise RuntimeBoundaryError("runtime-boundary aggregate hash mismatch")
    verify_runtime_boundary_result(manifest, result)
    return manifest, result, seal
