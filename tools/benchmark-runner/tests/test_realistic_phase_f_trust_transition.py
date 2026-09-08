"""Model-free replay of native workspace trust registration and hostile drift."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace
import traceback

import pytest

from benchmark_runner.realistic_phase_f_b1 import PhaseFB1RuntimeV2
from benchmark_runner.realistic_phase_f_sdk import (
    CodexPhaseFAppServerPort, PhaseFConfigurationDriftError, PhaseFSdkContractError,
    PhaseFSdkRuntimeV2, phase_f_thread_start_params, phase_f_turn_start_params,
)
from benchmark_runner.realistic_routing import canonical_sha256
from test_realistic_phase_f_sdk import FakeRawClient, _config_overrides


def register_trust(client: FakeRawClient, *, project: Path | None = None) -> None:
    result = client.configuration_result
    user = result["layers"][0]
    old_meta = {key: user[key] for key in ("name", "version")}
    user["version"] = "registered-workspace-version"
    new_meta = {key: user[key] for key in ("name", "version")}
    key = str(project or client.workspace)
    for config in (result["config"], user["config"]):
        if config.get("projects") is None:
            config["projects"] = {}
        config["projects"][key] = {"trust_level": "trusted"}
    for name, origin in result["origins"].items():
        if origin == old_meta:
            result["origins"][name] = copy.deepcopy(new_meta)
    result["origins"][f"projects.{key}.trust_level"] = copy.deepcopy(new_meta)


def runtime_fixture(tmp_path: Path, mutation=None, *, register_during_start: bool = True):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    class RegisteringClient(FakeRawClient):
        def _request_raw(self, method, params=None):
            result = super()._request_raw(method, params)
            if register_during_start and method == "thread/start" and self.thread_count == 1:
                register_trust(self)
                if mutation is not None:
                    mutation(self)
            return result

    client = RegisteringClient(workspace)
    client.configuration_result["origins"]["model"] = {
        key: copy.deepcopy(client.configuration_result["layers"][0][key]) for key in ("name", "version")
    }
    port = CodexPhaseFAppServerPort(workspace, config_overrides=_config_overrides(),
        process_environment={}, client_factory=lambda _w, _o: client)
    return port, client


@pytest.mark.parametrize("initial_projects", ["absent", "null", "empty", "other"])
def test_b1_second_session_accepts_only_observed_own_trust_registration(tmp_path: Path, initial_projects: str) -> None:
    port, client = runtime_fixture(tmp_path)
    for config in (client.configuration_result["config"], client.configuration_result["layers"][0]["config"]):
        if initial_projects != "absent":
            config["projects"] = {"other-private-path": {"trust_level": "untrusted"}} if initial_projects == "other" else (None if initial_projects == "null" else {})
    runtime = PhaseFB1RuntimeV2(port.workspace, port=port, environ={})
    profile = SimpleNamespace(model="gpt-5.6-sol", auth_method="chatgpt", reasoning_effort="high")
    try:
        runtime.preflight()
        first = runtime.start_session(SimpleNamespace(), profile)
        second = runtime.start_session(SimpleNamespace(), profile)
        assert first.id != second.id
        assert client.thread_count == 2 and runtime.actual_model_turns == 0
        assert not any(name == "turn/start" for name, _ in client.calls)
        transition = runtime.thread_evidence[0]["configuration_transition"]
        assert transition["before_evidence_sha256"] != transition["after_evidence_sha256"]
        assert transition["evidence_sha256"] == canonical_sha256({k: v for k, v in transition.items() if k != "evidence_sha256"})
        assert transition["cwd_sha256"] == canonical_sha256(str(port.workspace))
        assert "configuration_transition" not in runtime.thread_evidence[1]
        assert str(port.workspace) not in json.dumps(transition)
        assert "other-private-path" not in json.dumps(transition)
        assert len([name for name, _ in client.calls if name == "config/read"]) == 5
    finally:
        runtime.close()
    assert port._configuration_payload is None and port._last_configuration_payload is None


def test_ss1_also_records_trust_transition_without_exposing_config(tmp_path: Path) -> None:
    port, _client = runtime_fixture(tmp_path)
    runtime = PhaseFSdkRuntimeV2(port.workspace, port=port, environ={})
    try:
        runtime.preflight()
        runtime.start_thread()
        assert runtime.thread_start_evidence["configuration_transition"]["kind"] == "phase_f_sdk_workspace_trust_registration"
        assert runtime.actual_model_turns == 0
    finally:
        runtime.close()


def mutate(client, attack):
    r = client.configuration_result
    user = r["layers"][0]
    key = str(client.workspace)
    if attack in {"model", "permission", "secret"}:
        r["config"][attack] = "synthetic-private-drift-do-not-leak"
    elif attack == "extra_project":
        user["config"]["projects"][str(client.workspace.parent / "sibling")] = {"trust_level": "trusted"}
    elif attack == "trust_extra_key":
        user["config"]["projects"][key]["extra"] = "synthetic-private-drift-do-not-leak"
    elif attack == "untrusted":
        user["config"]["projects"][key]["trust_level"] = "untrusted"
    elif attack == "missing_origin":
        r["origins"].pop(f"projects.{key}.trust_level")
    elif attack == "other_origin":
        r["origins"]["other"] = {"name": user["name"], "version": user["version"]}
    elif attack == "origin_source":
        r["origins"]["model"] = {"name": {"type": "system"}, "version": "new"}
    elif attack == "session_layer":
        r["layers"][1]["version"] = "different-session-layer"
    elif attack == "layer_order":
        r["layers"].reverse()
    elif attack == "missing_effective_trust":
        r["config"]["projects"].pop(key)
    elif attack == "cli":
        client.phase_f_cli_binary_sha256 = canonical_sha256("changed-cli")
    elif attack == "parse_error":
        client.configuration_error = ValueError("synthetic-private-drift-do-not-leak")
    elif attack == "parent_instead_of_workspace":
        for config in (r["config"], user["config"]):
            config["projects"][str(client.workspace.parent)] = config["projects"].pop(key)
    else:
        raise AssertionError(attack)


@pytest.mark.parametrize("attack", ["model", "permission", "secret", "extra_project", "trust_extra_key",
    "untrusted", "missing_origin", "other_origin", "origin_source", "session_layer", "layer_order",
    "missing_effective_trust", "cli", "parse_error", "parent_instead_of_workspace"])
def test_post_start_drift_blocks_first_turn_and_second_thread(tmp_path: Path, attack: str) -> None:
    port, client = runtime_fixture(tmp_path, lambda client: mutate(client, attack))
    try:
        port.open()
        port.validate_configuration(str(port.workspace))
        with pytest.raises(PhaseFSdkContractError) as failure:
            port.start_thread(phase_f_thread_start_params(port.workspace), notification_timeout_seconds=2)
        assert "synthetic-private-drift-do-not-leak" not in "".join(traceback.format_exception(failure.value))
        assert client.thread_count == 1
        with pytest.raises(PhaseFConfigurationDriftError, match="latched failed"):
            port.validate_configuration(str(port.workspace))
        with pytest.raises(PhaseFSdkContractError, match="preflight is required"):
            port.start_thread(phase_f_thread_start_params(port.workspace), notification_timeout_seconds=2)
        with pytest.raises(PhaseFSdkContractError, match="preflight is required"):
            port.start_turn("raw-thread-1", "must not dispatch", phase_f_turn_start_params(port.workspace, {}))
        assert not any(name == "turn/start" for name, _ in client.calls)
    finally:
        port.close()


def test_trust_change_outside_verified_thread_start_still_fails_closed(tmp_path: Path) -> None:
    port, client = runtime_fixture(tmp_path)
    try:
        port.open()
        port.validate_configuration(str(port.workspace))
        register_trust(client)
        with pytest.raises(PhaseFConfigurationDriftError, match="changed after preflight"):
            port.start_thread(phase_f_thread_start_params(port.workspace), notification_timeout_seconds=2)
        assert client.thread_count == 0
    finally:
        port.close()


@pytest.mark.parametrize("existing_trust", ["untrusted", "trusted", None])
def test_existing_workspace_record_cannot_be_replaced_under_trust_exception(tmp_path: Path, existing_trust: str | None) -> None:
    port, client = runtime_fixture(tmp_path)
    for config in (client.configuration_result["config"], client.configuration_result["layers"][0]["config"]):
        config["projects"] = {str(port.workspace): {"trust_level": existing_trust}}
    try:
        port.open()
        port.validate_configuration(str(port.workspace))
        with pytest.raises(PhaseFConfigurationDriftError):
            port.start_thread(phase_f_thread_start_params(port.workspace), notification_timeout_seconds=2)
    finally:
        port.close()


def test_later_version_only_change_is_not_hidden_after_trust_acceptance(tmp_path: Path) -> None:
    port, client = runtime_fixture(tmp_path)
    try:
        port.open()
        port.validate_configuration(str(port.workspace))
        port.start_thread(phase_f_thread_start_params(port.workspace), notification_timeout_seconds=2)
        client.configuration_result["layers"][0]["version"] = "later-drift"
        with pytest.raises(PhaseFConfigurationDriftError):
            port.start_thread(phase_f_thread_start_params(port.workspace), notification_timeout_seconds=2)
        assert client.thread_count == 1
    finally:
        port.close()


def test_registration_visible_between_verified_sessions_is_audited(tmp_path: Path) -> None:
    port, client = runtime_fixture(tmp_path, register_during_start=False)
    try:
        port.open()
        port.validate_configuration(str(port.workspace))
        first = port.start_thread(phase_f_thread_start_params(port.workspace), notification_timeout_seconds=2)
        assert first.configuration_transition is None
        register_trust(client)
        second = port.start_thread(phase_f_thread_start_params(port.workspace), notification_timeout_seconds=2)
        assert second.configuration_transition is not None
        assert client.thread_count == 2
        assert not any(name == "turn/start" for name, _ in client.calls)
    finally:
        port.close()


def test_origin_metadata_boolean_is_not_equated_with_integer(tmp_path: Path) -> None:
    def change_type(client):
        client.configuration_result["origins"]["model"]["name"]["synthetic_flag"] = 0

    port, client = runtime_fixture(tmp_path, change_type)
    user = client.configuration_result["layers"][0]
    user["name"]["synthetic_flag"] = False
    client.configuration_result["origins"]["model"] = {key: copy.deepcopy(user[key]) for key in ("name", "version")}
    try:
        port.open()
        port.validate_configuration(str(port.workspace))
        with pytest.raises(PhaseFConfigurationDriftError):
            port.start_thread(phase_f_thread_start_params(port.workspace), notification_timeout_seconds=2)
        assert not any(name == "turn/start" for name, _ in client.calls)
    finally:
        port.close()


def test_invalid_thread_provenance_never_arms_trust_exception(tmp_path: Path) -> None:
    def wrong_profile(client):
        client.frames[1][1]["result"]["activePermissionProfile"]["id"] = ":workspace"

    port, client = runtime_fixture(tmp_path, wrong_profile)
    try:
        port.open()
        port.validate_configuration(str(port.workspace))
        with pytest.raises(PhaseFSdkContractError):
            port.start_thread(phase_f_thread_start_params(port.workspace), notification_timeout_seconds=2)
        assert port._workspace_trust_thread_id is None
        with pytest.raises(PhaseFConfigurationDriftError):
            port.validate_configuration(str(port.workspace))
        assert not any(name == "turn/start" for name, _ in client.calls)
    finally:
        port.close()
