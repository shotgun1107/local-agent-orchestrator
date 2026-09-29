"""Public synthetic inputs derived from v2 fixtures at 35072d4.

No assertions or grading logic. Loaded in the candidate container, never trusted
as a verdict. SDK/client/OS values are synthetic, not actual enforcement proof.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace


import benchmark_runner.runtime_boundary as runtime_boundary
from benchmark_runner.runner import canonical_json_bytes, sha256_bytes, sha256_file
from benchmark_runner.runtime_boundary import (
    ConfigurationExpectation,
    EffectivePolicyEvidence,
    EmbeddedJsonEvidence,
    EnumerationTargetObservation,
    FileMutationObservation,
    FileReadObservation,
    LinkAttemptObservation,
    P01ReadResult,
    P02ReadResult,
    P03ReadResult,
    P04EnumerationResult,
    P05LinkResult,
    P06ChildResult,
    P07InputScanResult,
    P08StateResult,
    PolicySourceIdentity,
    ProbeCommandSpec,
    ProbeFixtureSpec,
    ProbeProcessObservation,
    RootIdentity,
    RuntimeBoundaryError,
    RuntimeBoundaryProbeManifest,
    RuntimeBoundaryProbeResult,
    RuntimeIdentity,
    SentinelSpec,
    WindowsProcessIdentityObservation,
    WorkspaceAclTransitionObservation,
    Win32CallObservation,
    build_windows_sandbox_provenance,
    build_runtime_boundary_manifest,
    collect_sdk_profile_provenance,
    effective_policy_failure_reason_codes,
    effective_policy_evidence_from_projection,
    execute_frozen_probe_command,
    project_effective_policy,
    result_with_recomputed_verdict,
    runtime_boundary_policy_failure_path,
    runtime_boundary_probe_failure_path,
    runtime_boundary_profile_failure_path,
    sdk_profile_evidence_from_transcript,
    verify_effective_policy,
    verify_runtime_boundary_policy_failure,
    verify_runtime_boundary_probe_failure,
    verify_runtime_boundary_profile_failure,
    verify_runtime_boundary_bundle,
    verify_runtime_boundary_result,
    verify_sdk_profile_provenance,
    verify_probe_command_contract,
    write_runtime_boundary_bundle,
    write_runtime_boundary_policy_failure,
    write_runtime_boundary_profile_failure,
)


ZERO = "0" * 64
ONE = "1" * 64
TWO = "2" * 64
THREE = "3" * 64


def _sha(value: object) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def _identity(
    sid: str,
    *,
    elevated_raw: int = 0,
    restricted_sid_sha256s: list[str] | None = None,
    capability_sid_sha256s: list[str] | None = None,
) -> WindowsProcessIdentityObservation:
    calls = [
        Win32CallObservation(
            api="GetTokenInformation(TokenUser)",
            success=True,
            return_code=1,
            last_error=0,
        )
    ]
    raw = {
        "token_user_sid": sid,
        "integrity_level_sid": "S-1-16-4096",
        "token_is_elevated_raw": elevated_raw,
        "token_is_app_container_raw": 0,
        "restricted_sid_sha256s": sorted(set(restricted_sid_sha256s or [])),
        "capability_sid_sha256s": sorted(set(capability_sid_sha256s or [])),
        "calls": [item.model_dump(mode="json") for item in calls],
    }
    return WindowsProcessIdentityObservation(
        **raw,
        identity_sha256=_sha(raw),
    )


def _process(identity: WindowsProcessIdentityObservation) -> ProbeProcessObservation:
    empty_hash = sha256_bytes(b"")
    return ProbeProcessObservation(
        wrapper_exit_code=0,
        operation_exit_code=0,
        stdout_size=0,
        stdout_sha256=empty_hash,
        stdout_truncated=False,
        stderr_size=0,
        stderr_sha256=empty_hash,
        stderr_truncated=False,
        duration_ms=1,
        sandbox_process_identity=identity,
    )


def _workspace_acl_transition(
    sid: str,
    *,
    initial_acl_sha256: str = ZERO,
) -> WorkspaceAclTransitionObservation:
    initial_ace = "(A;OICIID;FA;;;SY)"
    added_ace = f"(A;OICI;0x1301bf;;;{sid})"
    initial_hash = sha256_bytes(initial_ace.encode("utf-8"))
    added_hash = sha256_bytes(added_ace.encode("utf-8"))
    return WorkspaceAclTransitionObservation(
        selection_method="initial_acl+exact_w_only_ace_delta+p01_restricted_sid",
        initial_W_acl_sddl_sha256=initial_acl_sha256,
        active_W_acl_sddl_sha256=ONE,
        initial_W_dacl_control_sha256=TWO,
        active_W_dacl_control_sha256=TWO,
        initial_W_ace_sha256s=[initial_hash],
        active_W_ace_sha256s=sorted([initial_hash, added_hash]),
        added_ace_sddl=added_ace,
        added_ace_sha256=added_hash,
        added_ace_type="A",
        added_ace_flags="OICI",
        added_ace_rights="0x1301bf",
        added_ace_object_guid="",
        added_ace_inherit_object_guid="",
        added_capability_sid=sid,
        added_capability_sid_sha256=sha256_bytes(sid.encode("utf-8")),
        removed_ace_sha256s=[],
        W_owner_unchanged=True,
        W_owner_group_descriptor_unchanged=True,
        W_volume_unchanged=True,
        J_identity_unchanged=True,
        S_identity_unchanged=True,
        P01_restricted_contains_added_ace_sid=True,
        derived_transition_passed=True,
    )


def _denied() -> FileReadObservation:
    return FileReadObservation(
        outcome="access_denied",
        bytes_read=0,
        content_sha256=None,
        win32_error=5,
    )


def _configuration(
    W: Path = Path("C:/runtime-boundary-w"),
    J: Path = Path("C:/runtime-boundary-j"),
    S: Path = Path("C:/runtime-boundary-s"),
) -> ConfigurationExpectation:
    return ConfigurationExpectation(
        default_permissions="runtime-boundary-worker",
        permission_profile_name="runtime-boundary-worker",
        config_overrides=list(
            runtime_boundary._runtime_boundary_config_overrides(W=W, J=J, S=S)
        ),
        include_managed_config=True,
        legacy_sandbox_settings_present=False,
        sdk_thread_sandbox_argument_omitted=True,
        sdk_turn_sandbox_argument_omitted=True,
        approval_mode="deny_all",
        approval_policy_wire_value="never",
        network_access="disabled",
    )


def _manifest(tmp_path: Path) -> RuntimeBoundaryProbeManifest:
    W = tmp_path / "W"
    J = tmp_path / "J"
    S = tmp_path / "S"
    for root in (W, J, S):
        root.mkdir()
    (W / "sentinel.txt").write_bytes(b"W")
    (J / "sentinel.txt").write_bytes(b"J")
    (S / "sentinel.txt").write_bytes(b"S")
    (W / "replace-source.txt").write_bytes(b"source")
    (S / "replace-target.txt").write_bytes(b"target")
    probe_script = W / "probe_runtime_boundary.py"
    probe_script.write_text("# frozen probe\n", encoding="utf-8")
    executable = tmp_path / "codex.exe"
    executable.write_bytes(b"codex")

    runtime = RuntimeIdentity(
        sdk_distribution="openai-codex",
        sdk_version="0.144.4",
        sdk_metadata_sha256=ZERO,
        cli_distribution="openai-codex-cli-bin",
        cli_version="0.144.4",
        cli_metadata_sha256=ZERO,
        cli_package_json_sha256=ZERO,
        cli_target="x86_64-pc-windows-msvc",
        sdk_resolved_executable=str(executable.resolve()),
        probe_resolved_executable=str(executable.resolve()),
        executable_sha256=sha256_file(executable),
        sdk_client_source_sha256=ZERO,
        sdk_generated_protocol_sha256=ZERO,
        resolution_method="codex_cli_bin.bundled_codex_path",
        codex_bin_override_present=False,
        launch_args_override_present=False,
    )
    roots = [
        RootIdentity(
            redacted_path_id=name,
            resolved_absolute_path=str(path.resolve()),
            volume_identity="volume",
            owner_sid="S-1-5-21-controller",
            acl_sddl_sha256=ZERO,
        )
        for name, path in (("W", W), ("J", J), ("S", S))
    ]
    commands = tuple(
        ProbeCommandSpec(
            probe_id=probe_id,
            argv=["codex", "probe", "operation", probe_id],
            argv_sha256=_sha(["codex", "probe", "operation", probe_id]),
            expected_class=f"EXPECTED_{probe_id}",
        )
        for probe_id in ("P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08")
    )
    allowlist = ["Path", "SystemRoot"]
    return RuntimeBoundaryProbeManifest(
        probe_id="runtime-boundary-test",
        created_at=datetime(2026, 8, 9, tzinfo=timezone.utc),
        source_commit="a" * 40,
        runtime=runtime,
        configuration=_configuration(W, J, S),
        environment_name_allowlist=allowlist,
        environment_contract_sha256=_sha(allowlist),
        api_key_environment_names_present=(),
        probe_python_executable=str(Path(sys.executable).resolve()),
        python_executable_sha256=sha256_file(Path(sys.executable)),
        W=roots[0],
        J=roots[1],
        S=roots[2],
        pairwise_parent_child=False,
        pairwise_reparse_target=False,
        W_sentinel=SentinelSpec(relative_path="sentinel.txt", size=1, sha256=sha256_file(W / "sentinel.txt")),
        J_sentinel=SentinelSpec(relative_path="sentinel.txt", size=1, sha256=sha256_file(J / "sentinel.txt")),
        S_sentinel=SentinelSpec(relative_path="sentinel.txt", size=1, sha256=sha256_file(S / "sentinel.txt")),
        fixtures=ProbeFixtureSpec(
            p05_symlink_path="symlink",
            p05_junction_path="junction",
            p07_expected_answer_sha256=THREE,
            p08_create_target="create-target.txt",
            p08_replace_source="replace-source.txt",
            p08_replace_source_size=6,
            p08_replace_source_sha256=sha256_file(W / "replace-source.txt"),
            p08_replace_target="replace-target.txt",
            p08_replace_target_size=6,
            p08_replace_target_sha256=sha256_file(S / "replace-target.txt"),
        ),
        probe_script_relative_path="probe_runtime_boundary.py",
        probe_script_sha256=sha256_file(probe_script),
        commands=commands,
    )


def _handshake_frames(W: Path, *, thread_id: str = "thread-1") -> list[tuple[str, dict[str, object]]]:
    return [
        (
            "client_to_server",
            {
                "id": "initialize-1",
                "method": "initialize",
                "params": {"capabilities": {"experimentalApi": True}},
            },
        ),
        ("server_to_client", {"id": "initialize-1", "result": {}}),
        ("client_to_server", {"method": "initialized"}),
        ("client_to_server", {"id": "account-1", "method": "account/read", "params": {}}),
        (
            "server_to_client",
            {"id": "account-1", "result": {"account": {"type": "chatgpt"}}},
        ),
        (
            "client_to_server",
            {
                "id": "profiles-1",
                "method": "permissionProfile/list",
                "params": {"cwd": str(W.resolve())},
            },
        ),
        (
            "server_to_client",
            {
                "id": "profiles-1",
                "result": {
                    "data": [
                        {"id": "runtime-boundary-worker", "allowed": True},
                        {"id": ":read-only", "allowed": True},
                    ],
                    "nextCursor": None,
                },
            },
        ),
        (
            "client_to_server",
            {
                "id": "thread-1-request",
                "method": "thread/start",
                "params": {
                    "cwd": str(W.resolve()),
                    "approvalPolicy": "never",
                    "config": {"default_permissions": "runtime-boundary-worker"},
                    "permissions": "runtime-boundary-worker",
                    "ephemeral": True,
                },
            },
        ),
        (
            "server_to_client",
            {
                "id": "thread-1-request",
                "result": {
                    "thread": {"id": thread_id},
                    "activePermissionProfile": {"id": "runtime-boundary-worker"},
                    "approvalPolicy": "never",
                    "cwd": str(W.resolve()),
                    "sandbox": "legacy-ignored",
                },
            },
        ),
        (
            "server_to_client",
            {
                "method": "thread/started",
                "params": {"thread": {"id": thread_id}},
            },
        ),
    ]


def _policy() -> EffectivePolicyEvidence:
    response = {
        "id": "config-1",
        "result": {
            "config": {
                "default_permissions": "runtime-boundary-worker",
                "windows": {"sandbox": "elevated"},
            },
            "layers": [
                {"name": {"type": "cli"}, "version": "1", "config": {"safe": True}}
            ],
        },
    }
    projection = project_effective_policy(
        response,
        managed_source_identities=[
            PolicySourceIdentity(kind="managed", version="1", sha256=ONE)
        ],
    )
    return effective_policy_evidence_from_projection(
        projection,
        source_response_sha256=_sha(response),
    )


def _passing_probes(
    manifest: RuntimeBoundaryProbeManifest,
    identity: WindowsProcessIdentityObservation,
) -> list[object]:
    process = _process(identity)
    common = {
        "process": process,
        "controller_precondition_ok": True,
        "controller_postcondition_ok": True,
        "derived_passed": True,
    }
    commands = manifest.commands
    return [
        P01ReadResult(
            probe_id="P01",
            argv_sha256=commands[0].argv_sha256,
            expected_class=commands[0].expected_class,
            path_role="W_sentinel",
            read=FileReadObservation(
                outcome="success",
                bytes_read=manifest.W_sentinel.size,
                content_sha256=manifest.W_sentinel.sha256,
                win32_error=None,
            ),
            **common,
        ),
        P02ReadResult(
            probe_id="P02",
            argv_sha256=commands[1].argv_sha256,
            expected_class=commands[1].expected_class,
            path_role="J_sentinel_absolute",
            read=_denied(),
            **common,
        ),
        P03ReadResult(
            probe_id="P03",
            argv_sha256=commands[2].argv_sha256,
            expected_class=commands[2].expected_class,
            path_role="J_sentinel_relative_from_W",
            normalized_target_path_id="J-sentinel",
            normalized_target_equals_manifest_J=True,
            read=_denied(),
            **common,
        ),
        P04EnumerationResult(
            probe_id="P04",
            argv_sha256=commands[3].argv_sha256,
            expected_class=commands[3].expected_class,
            targets=(
                EnumerationTargetObservation(
                    role="common_parent",
                    outcome="success",
                    enumeration_complete=True,
                    entry_count=0,
                    entry_name_sha256s=[],
                    forbidden_name_hash_match_count=0,
                    win32_error=None,
                ),
                EnumerationTargetObservation(
                    role="drive_root",
                    outcome="access_denied",
                    enumeration_complete=False,
                    entry_count=0,
                    entry_name_sha256s=[],
                    forbidden_name_hash_match_count=0,
                    win32_error=5,
                ),
            ),
            **common,
        ),
        P05LinkResult(
            probe_id="P05",
            argv_sha256=commands[4].argv_sha256,
            expected_class=commands[4].expected_class,
            attempts=tuple(
                LinkAttemptObservation(
                    link_kind=kind,
                    create_outcome="access_denied",
                    link_exists_after_create=False,
                    read=FileReadObservation(
                        outcome="not_attempted",
                        bytes_read=0,
                        content_sha256=None,
                        win32_error=None,
                    ),
                    link_exists_after_cleanup=False,
                )
                for kind in ("symlink", "junction")
            ),
            **common,
        ),
        P06ChildResult(
            probe_id="P06",
            argv_sha256=commands[5].argv_sha256,
            expected_class=commands[5].expected_class,
            child_spawn_outcome="success",
            child_exit_code=0,
            child_process_identity=identity,
            parent_child_identity_equal=True,
            child_read=_denied(),
            **common,
        ),
        P07InputScanResult(
            probe_id="P07",
            argv_sha256=commands[6].argv_sha256,
            expected_class=commands[6].expected_class,
            forbidden_value_sha256s=(
                manifest.J_sentinel.sha256,
                manifest.fixtures.p07_expected_answer_sha256,
            ),
            environment_scan_complete=True,
            environment_names_scanned=2,
            environment_values_scanned=2,
            environment_match_count=0,
            environment_matching_name_sha256s=[],
            argument_scan_complete=True,
            argument_values_scanned=3,
            argument_match_count=0,
            argument_matching_index_hashes=[],
            **common,
        ),
        P08StateResult(
            probe_id="P08",
            argv_sha256=commands[7].argv_sha256,
            expected_class=commands[7].expected_class,
            read=_denied(),
            create=FileMutationObservation(
                operation="create",
                outcome="access_denied",
                source_exists_before=None,
                source_exists_after=None,
                target_exists_before=False,
                target_exists_after=False,
                win32_error=5,
            ),
            replace=FileMutationObservation(
                operation="replace",
                outcome="access_denied",
                source_exists_before=True,
                source_exists_after=True,
                target_exists_before=False,
                target_exists_after=False,
                source_sha256_before=manifest.fixtures.p08_replace_source_sha256,
                source_sha256_after=manifest.fixtures.p08_replace_source_sha256,
                target_sha256_before=None,
                target_sha256_after=None,
                win32_error=5,
            ),
            S_sentinel_sha256_before=manifest.S_sentinel.sha256,
            S_sentinel_sha256_after=manifest.S_sentinel.sha256,
            **common,
        ),
    ]
