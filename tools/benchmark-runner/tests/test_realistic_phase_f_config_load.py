"""Opt-in, zero-thread tests of the actual pinned CLI decoder with synthetic homes."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import traceback

import pytest

from benchmark_runner.realistic_phase_f_sdk import (
    CodexPhaseFAppServerPort,
    PhaseFSdkContractError,
    _recording_codex_client_factory,
    build_phase_f_config_overrides,
    build_phase_f_worker_process_environment,
)

pytestmark = pytest.mark.skipif(
    os.environ.get("LAO_PHASE_F_CONFIG_LOAD_PREFLIGHT") != "1",
    reason="explicit pinned CLI config-only probe opt-in required; no threads or models",
)


@pytest.mark.parametrize("case", ["valid", "feature_table", "invalid_integer", "valid_drift", "project_invalid"])
def test_pinned_cli_parses_config_before_any_thread(case: str, tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    fixture_home = tmp_path / "synthetic-codex-home"
    fixture_home.mkdir()
    config = fixture_home / "config.toml"
    valid = '[features]\njs_repl = true\n'
    content = valid
    if case == "feature_table":
        content = '[features.context_management]\nexperimental_mode = true\n'
    elif case == "invalid_integer":
        content = 'model_context_window = "synthetic-private-config-value"\n'
    elif case == "project_invalid":
        content = f'[projects.{json.dumps(str(workspace))}]\ntrust_level = "trusted"\n'
        project_config = workspace / ".codex" / "config.toml"
        project_config.parent.mkdir()
        project_config.write_text(
            'model_context_window = "synthetic-private-config-value"\n', encoding="utf-8"
        )
    config.write_text(content, encoding="utf-8")
    initial_config_sha256 = hashlib.sha256(config.read_bytes()).hexdigest()
    environment = build_phase_f_worker_process_environment(
        {**os.environ, "CODEX_HOME": str(fixture_home)}
    )
    clients = []

    def guarded_client(path: Path, overrides: tuple[str, ...]):
        client = _recording_codex_client_factory(
            path, overrides, process_environment=environment
        )
        write_message = client._write_message

        def write_allowed(payload):
            assert payload.get("method") in {"initialize", "initialized", "config/read"}
            write_message(payload)

        client._write_message = write_allowed
        clients.append(client)
        return client

    port = CodexPhaseFAppServerPort(
        workspace,
        config_overrides=build_phase_f_config_overrides(workspace),
        process_environment=environment,
        client_factory=guarded_client,
    )
    try:
        port.open()
        if case in {"feature_table", "invalid_integer", "project_invalid"}:
            with pytest.raises(PhaseFSdkContractError, match=r"configuration validation failed \(config/read\)") as captured:
                port.validate_configuration(str(workspace))
            formatted = "".join(traceback.format_exception(captured.value))
            assert "synthetic-private-config-value" not in formatted
            assert "invalid type:" not in formatted
            assert config.read_text(encoding="utf-8") == content
        else:
            first = port.validate_configuration(str(workspace))
            assert first == port.validate_configuration(str(workspace))
            assert first.cli_binary_sha256 == clients[0].phase_f_cli_binary_sha256
            assert len(first.evidence_sha256) == 64
            if case == "valid_drift":
                config.write_text('model_reasoning_effort = "medium"\n' + valid, encoding="utf-8")
                with pytest.raises(PhaseFSdkContractError, match="changed after preflight"):
                    port.validate_configuration(str(workspace))
            else:
                assert hashlib.sha256(config.read_bytes()).hexdigest() == initial_config_sha256
    finally:
        process = clients[0]._proc if clients else None
        port.close()
        if process is not None:
            assert process.poll() is not None
    methods = [
        frame.get("method")
        for direction, frame in clients[0].transcript()
        if direction == "client_to_server"
    ]
    assert set(methods) <= {"initialize", "initialized", "config/read"}
    assert methods.count("config/read") >= 1
    if case in {"feature_table", "invalid_integer", "project_invalid"}:
        parser_errors = [
            frame.get("error", {}).get("message", "")
            for direction, frame in clients[0].transcript()
            if direction == "server_to_client" and isinstance(frame.get("error"), dict)
        ]
        assert any("invalid type:" in message for message in parser_errors)
        assert hashlib.sha256(config.read_bytes()).hexdigest() == initial_config_sha256
    for directory in ("sessions", "archived_sessions"):
        assert not list((fixture_home / directory).rglob("*.jsonl"))
