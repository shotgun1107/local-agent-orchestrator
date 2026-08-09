from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

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
    Win32CallObservation,
    build_windows_sandbox_provenance,
    build_runtime_boundary_manifest,
    collect_sdk_profile_provenance,
    effective_policy_evidence_from_projection,
    project_effective_policy,
    result_with_recomputed_verdict,
    runtime_boundary_profile_failure_path,
    sdk_profile_evidence_from_transcript,
    verify_effective_policy,
    verify_runtime_boundary_profile_failure,
    verify_runtime_boundary_bundle,
    verify_runtime_boundary_result,
    verify_sdk_profile_provenance,
    verify_probe_command_contract,
    write_runtime_boundary_bundle,
    write_runtime_boundary_profile_failure,
)


ZERO = "0" * 64
ONE = "1" * 64
TWO = "2" * 64
THREE = "3" * 64


def _sha(value: object) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def _identity(sid: str, *, elevated_raw: int = 0) -> WindowsProcessIdentityObservation:
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
        "restricted_sid_sha256s": [],
        "capability_sid_sha256s": [],
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


def _denied() -> FileReadObservation:
    return FileReadObservation(
        outcome="access_denied",
        bytes_read=0,
        content_sha256=None,
        win32_error=5,
    )


def _configuration() -> ConfigurationExpectation:
    return ConfigurationExpectation(
        default_permissions=":workspace",
        permission_profile_name=":workspace",
        config_overrides=[
            'default_permissions=":workspace"',
            'windows.sandbox="elevated"',
        ],
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
        configuration=_configuration(),
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
                        {"id": ":workspace", "allowed": True},
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
                    "config": {"default_permissions": ":workspace"},
                    "permissions": ":workspace",
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
                    "activePermissionProfile": {"id": ":workspace"},
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
                "default_permissions": ":workspace",
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
                target_exists_before=True,
                target_exists_after=True,
                source_sha256_before=manifest.fixtures.p08_replace_source_sha256,
                source_sha256_after=manifest.fixtures.p08_replace_source_sha256,
                target_sha256_before=manifest.fixtures.p08_replace_target_sha256,
                target_sha256_after=manifest.fixtures.p08_replace_target_sha256,
                win32_error=5,
            ),
            S_sentinel_sha256_before=manifest.S_sentinel.sha256,
            S_sentinel_sha256_after=manifest.S_sentinel.sha256,
            **common,
        ),
    ]


def test_complete_zero_turn_transcript_is_recomputed(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    evidence = sdk_profile_evidence_from_transcript(
        _handshake_frames(Path(manifest.W.resolved_absolute_path)),
        W=Path(manifest.W.resolved_absolute_path),
        resolved_executable_sha256=manifest.runtime.executable_sha256,
        config_identity_sha256=_sha(manifest.configuration),
    )

    assert evidence.derived_profile_passed is True
    assert evidence.method_ledger.client_request_method_counts == {
        "account/read": 1,
        "initialize": 1,
        "permissionProfile/list": 1,
        "thread/start": 1,
    }
    assert evidence.method_ledger.client_notification_method_counts == {"initialized": 1}
    assert evidence.workspace_permission_profile_match_count == 1
    assert evidence.workspace_permission_profile_allowed is True
    assert evidence.requested_permission_profile_id == ":workspace"
    assert evidence.active_permission_profile_id == ":workspace"
    assert evidence.thread_started_notification_count == 1
    assert evidence.turn_start_request_count == 0
    assert evidence.actual_model_turns == 0
    assert evidence.profile_failure_reason_codes == []
    assert verify_sdk_profile_provenance(manifest, evidence) is True


def test_manifest_builds_exact_profile_commands_without_legacy_sandbox(
    tmp_path: Path,
) -> None:
    fixture = _manifest(tmp_path)
    built = build_runtime_boundary_manifest(
        source_commit=fixture.source_commit,
        W=fixture.W,
        J=fixture.J,
        S=fixture.S,
        W_sentinel=fixture.W_sentinel,
        J_sentinel=fixture.J_sentinel,
        S_sentinel=fixture.S_sentinel,
        fixtures=fixture.fixtures,
        probe_python_executable=Path(fixture.probe_python_executable),
        probe_script_relative_path=fixture.probe_script_relative_path,
        environment_name_allowlist=fixture.environment_name_allowlist,
        runtime=fixture.runtime,
        created_at=fixture.created_at,
        probe_id=fixture.probe_id,
    )

    verify_probe_command_contract(built)
    for command in built.commands:
        assert command.argv[1:3] == ["sandbox", "windows"]
        assert "--permission-profile" in command.argv
        assert "--sandbox" not in command.argv
        assert 'default_permissions=":workspace"' in command.argv
        assert 'windows.sandbox="elevated"' in command.argv
    assert built.fixtures.p07_expected_answer_sha256 in built.commands[6].argv


def test_transcript_rejects_thread_mismatch_and_turn_start(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    frames = _handshake_frames(Path(manifest.W.resolved_absolute_path))
    frames[-1][1]["params"]["thread"]["id"] = "different-thread"  # type: ignore[index]
    frames.append(
        (
            "client_to_server",
            {"id": "turn-1", "method": "turn/start", "params": {"threadId": "thread-1"}},
        )
    )
    evidence = sdk_profile_evidence_from_transcript(
        frames,
        W=Path(manifest.W.resolved_absolute_path),
        resolved_executable_sha256=manifest.runtime.executable_sha256,
        config_identity_sha256=_sha(manifest.configuration),
    )

    assert evidence.thread_id_binding_equal is False
    assert evidence.turn_start_request_count == 1
    assert evidence.actual_model_turns == 1
    assert evidence.derived_profile_passed is False

    forged = evidence.model_copy(update={"derived_profile_passed": True})
    with pytest.raises(RuntimeBoundaryError, match="derived field mismatch"):
        verify_sdk_profile_provenance(manifest, forged)


def test_transcript_rejects_disallowed_workspace_profile(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    frames = _handshake_frames(Path(manifest.W.resolved_absolute_path))
    profile_response = next(
        frame
        for direction, frame in frames
        if direction == "server_to_client" and frame.get("id") == "profiles-1"
    )
    profile_response["result"]["data"][0]["allowed"] = False  # type: ignore[index]
    evidence = sdk_profile_evidence_from_transcript(
        frames,
        W=Path(manifest.W.resolved_absolute_path),
        resolved_executable_sha256=manifest.runtime.executable_sha256,
        config_identity_sha256=_sha(manifest.configuration),
    )

    assert evidence.workspace_permission_profile_allowed is False
    assert evidence.derived_profile_passed is False
    assert "WORKSPACE_PROFILE_NOT_ALLOWED" in evidence.profile_failure_reason_codes
    assert verify_sdk_profile_provenance(manifest, evidence) is False


def test_collector_uses_named_profile_and_guaranteed_thread_started(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _manifest(tmp_path)
    frames = _handshake_frames(Path(manifest.W.resolved_absolute_path))

    class FakeClient:
        def __init__(self) -> None:
            self.raw_calls: list[tuple[str, object]] = []
            self.waited_for: tuple[str, float] | None = None

        def start(self) -> None:
            return None

        def initialize(self) -> None:
            return None

        def account_read(self, _params: object) -> None:
            return None

        def _request_raw(self, method: str, params: object) -> dict[str, object]:
            self.raw_calls.append((method, params))
            return {}

        def wait_for_notification(self, method: str, timeout: float) -> bool:
            self.waited_for = (method, timeout)
            return True

        def close(self) -> None:
            return None

        def transcript(self) -> list[tuple[str, dict[str, object]]]:
            return frames

    client = FakeClient()
    monkeypatch.setattr(runtime_boundary, "verify_pinned_runtime_identity", lambda _runtime: None)
    monkeypatch.setattr(
        runtime_boundary,
        "_new_recording_client",
        lambda _manifest, _environment: client,
    )

    evidence = collect_sdk_profile_provenance(manifest, source_environment={})

    assert client.raw_calls[0] == (
        "permissionProfile/list",
        {"cwd": manifest.W.resolved_absolute_path},
    )
    method, params = client.raw_calls[1]
    assert method == "thread/start"
    assert isinstance(params, dict)
    assert params["permissions"] == ":workspace"
    assert "sandbox" not in params
    assert client.waited_for == ("thread/started", 2.0)
    assert evidence.derived_profile_passed is True


def test_profile_failure_is_written_beside_uncreated_bundle(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    frames = _handshake_frames(Path(manifest.W.resolved_absolute_path))
    profile_response = next(
        frame
        for direction, frame in frames
        if direction == "server_to_client" and frame.get("id") == "profiles-1"
    )
    profile_response["result"]["data"][0]["allowed"] = False  # type: ignore[index]
    evidence = sdk_profile_evidence_from_transcript(
        frames,
        W=Path(manifest.W.resolved_absolute_path),
        resolved_executable_sha256=manifest.runtime.executable_sha256,
        config_identity_sha256=_sha(manifest.configuration),
    )
    bundle = tmp_path / "candidate-bundle"

    failure_path = write_runtime_boundary_profile_failure(bundle, manifest, evidence)

    assert failure_path == runtime_boundary_profile_failure_path(bundle)
    assert failure_path.is_file()
    assert not bundle.exists()
    verified = verify_runtime_boundary_profile_failure(failure_path, manifest)
    assert verified.failure_reason_codes == evidence.profile_failure_reason_codes
    assert verified.actual_model_turns == 0
    with pytest.raises(RuntimeBoundaryError, match="retry is forbidden"):
        write_runtime_boundary_profile_failure(bundle, manifest, evidence)


def test_effective_policy_projection_is_redacted_and_recomputed() -> None:
    raw_secret = "do-not-store-this-value"
    response = {
        "id": "config-1",
        "result": {
            "config": {
                "default_permissions": ":workspace",
                "windows": {"sandbox": "elevated"},
                "service_token": raw_secret,
            },
            "layers": [
                {
                    "name": {"type": "cli"},
                    "version": "1",
                    "config": {"api_key": raw_secret, "safe": True},
                }
            ],
        },
    }
    projection = project_effective_policy(
        response,
        managed_source_identities=[
            PolicySourceIdentity(kind="managed", version="1", sha256=TWO)
        ],
    )
    evidence = effective_policy_evidence_from_projection(
        projection,
        source_response_sha256=_sha(response),
    )

    assert raw_secret not in evidence.projection.bytes_value().decode("utf-8")
    assert verify_effective_policy(evidence, configuration=_configuration()) is True

    forged = evidence.model_copy(update={"windows_sandbox": "unelevated"})
    with pytest.raises(RuntimeBoundaryError, match="derived field mismatch"):
        verify_effective_policy(forged, configuration=_configuration())


def test_candidate_result_and_exact_four_file_bundle(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    profile = sdk_profile_evidence_from_transcript(
        _handshake_frames(Path(manifest.W.resolved_absolute_path)),
        W=Path(manifest.W.resolved_absolute_path),
        resolved_executable_sha256=manifest.runtime.executable_sha256,
        config_identity_sha256=_sha(manifest.configuration),
    )
    policy = _policy()
    sandbox_identity = _identity("S-1-5-21-sandbox", elevated_raw=0)
    controller_identity = _identity("S-1-5-21-controller", elevated_raw=1)
    probes = _passing_probes(manifest, sandbox_identity)
    requirements = EmbeddedJsonEvidence.from_value(
        {"id": "requirements", "result": {"requirements": None}}
    )
    readiness = EmbeddedJsonEvidence.from_value(
        {"id": "readiness", "result": {"status": "ready"}}
    )
    windows = build_windows_sandbox_provenance(
        effective_policy=policy,
        config_requirements_response=requirements,
        readiness_response=readiness,
        controller_process_identity=controller_identity,
        probes=probes,
    )
    now = datetime(2026, 8, 9, tzinfo=timezone.utc)
    provisional = RuntimeBoundaryProbeResult(
        probe_id=manifest.probe_id,
        manifest_sha256=_sha(manifest),
        started_at=now,
        completed_at=now,
        runtime_identity_sha256=_sha(manifest.runtime),
        configuration_identity_sha256=_sha(manifest.configuration),
        sdk_profile_provenance=profile,
        effective_policy=policy,
        windows_sandbox_provenance=windows,
        windows_sandbox_kind=windows.observed_kind,
        actual_model_turns=0,
        probes=probes,
        aggregate_status="RUNTIME_BOUNDARY_NOT_PROVEN",
        failure_reason_codes=[],
    )
    result = result_with_recomputed_verdict(manifest, provisional)

    assert result.aggregate_status == "RUNTIME_BOUNDARY_CANDIDATE"
    assert verify_runtime_boundary_result(manifest, result) == "RUNTIME_BOUNDARY_CANDIDATE"

    bundle = tmp_path / "bundle"
    seal = write_runtime_boundary_bundle(bundle, manifest, result)
    assert seal.file_count == 4
    assert {path.name for path in bundle.iterdir()} == {
        "manifest.json",
        "result.json",
        "files.sha256",
        "bundle-seal.json",
    }
    verify_runtime_boundary_bundle(bundle)

    (bundle / "extra.txt").write_text("not allowed", encoding="utf-8")
    with pytest.raises(RuntimeBoundaryError, match="file set mismatch"):
        verify_runtime_boundary_bundle(bundle)
