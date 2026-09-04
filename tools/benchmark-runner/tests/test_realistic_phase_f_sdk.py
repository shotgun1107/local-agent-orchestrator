from __future__ import annotations

import hashlib
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import pytest

from benchmark_runner.realistic_phase_f_sdk import (
    CodexPhaseFAppServerPort,
    PHASE_F_APPROVAL_POLICY_WIRE,
    PHASE_F_PERMISSION_PROFILE,
    PHASE_F_PINNED_MODEL,
    PHASE_F_PINNED_REASONING_EFFORT,
    PHASE_F_PINNED_SDK_VERSION,
    PhaseFAppServerPort,
    PhaseFSdkContractError,
    PhaseFSdkRuntimeV2,
    PhaseFThreadStartObservation,
    build_phase_f_worker_process_environment,
    phase_f_thread_start_params,
    phase_f_turn_start_params,
    validate_phase_f_config_overrides,
    verify_phase_f_thread_start,
)


def test_worker_process_environment_pins_controller_python_and_strips_overrides() -> None:
    environment = build_phase_f_worker_process_environment(
        {
            "PATH": os.pathsep.join(("synthetic-bin", str(Path(sys.executable).parent))),
            "PYTHONHOME": "forbidden-home",
            "PYTHONPATH": "forbidden-path",
        },
        python_executable=Path(sys.executable),
    )

    assert Path(environment["PATH"].split(os.pathsep)[0]) == Path(
        sys.executable
    ).resolve().parent
    assert "PYTHONHOME" not in environment
    assert "PYTHONPATH" not in environment
    assert environment["PYTHONDONTWRITEBYTECODE"] == "1"
    assert environment["PYTHONIOENCODING"] == "utf-8"
    assert environment["PYTHONUTF8"] == "1"


@dataclass
class FakeUsageTotal:
    input_tokens: int = 7
    output_tokens: int = 3
    total_tokens: int = 10


@dataclass
class FakeUsage:
    total: FakeUsageTotal = field(default_factory=FakeUsageTotal)


@dataclass
class FakeTurnResult:
    status: str = "completed"
    final_response: str = '{"status_claim":"completed"}'
    usage: FakeUsage = field(default_factory=FakeUsage)
    duration_ms: int = 25


class FakeTurnHandle:
    def __init__(self) -> None:
        self.run_count = 0
        self.interrupt_count = 0

    def run(self) -> FakeTurnResult:
        self.run_count += 1
        return FakeTurnResult()

    def interrupt(self) -> None:
        self.interrupt_count += 1


class FakeAppServerPort(PhaseFAppServerPort):
    sdk_version = PHASE_F_PINNED_SDK_VERSION

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace.resolve()
        self.open_count = 0
        self.close_count = 0
        self.thread_requests: list[Mapping[str, Any]] = []
        self.turn_requests: list[tuple[str, str, Mapping[str, Any]]] = []
        self.handle = FakeTurnHandle()
        self.account = "chatgpt"
        self.models = (PHASE_F_PINNED_MODEL,)
        self.profiles: tuple[Mapping[str, Any], ...] = (
            {"id": PHASE_F_PERMISSION_PROFILE, "allowed": True},
        )
        self.active_profile = PHASE_F_PERMISSION_PROFILE
        self.notification_thread_id = "phase-f-thread-1"

    def open(self) -> None:
        self.open_count += 1

    def account_type(self) -> str:
        return self.account

    def visible_model_ids(self) -> tuple[str, ...]:
        return self.models

    def permission_profiles(self, cwd: str) -> tuple[Mapping[str, Any], ...]:
        assert cwd == str(self.workspace)
        return self.profiles

    def start_thread(
        self,
        params: Mapping[str, Any],
        *,
        notification_timeout_seconds: float,
    ) -> PhaseFThreadStartObservation:
        assert notification_timeout_seconds == 2.0
        self.thread_requests.append(dict(params))
        response = {
            "thread": {"id": "phase-f-thread-1"},
            "activePermissionProfile": {"id": self.active_profile},
            "approvalPolicy": PHASE_F_APPROVAL_POLICY_WIRE,
            "cwd": str(self.workspace),
        }
        notification = {
            "method": "thread/started",
            "params": {"thread": {"id": self.notification_thread_id}},
        }
        return PhaseFThreadStartObservation(
            request=dict(params),
            response=response,
            notification=notification,
            transcript_sha256=hashlib.sha256(b"fake-transcript").hexdigest(),
        )

    def start_turn(
        self,
        thread_id: str,
        prompt: str,
        params: Mapping[str, Any],
    ) -> FakeTurnHandle:
        self.turn_requests.append((thread_id, prompt, dict(params)))
        return self.handle

    def close(self) -> None:
        self.close_count += 1


class FakeRawClient:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.calls: list[tuple[str, Any]] = []
        self.frames: list[tuple[str, Mapping[str, Any]]] = []
        self.thread_count = 0

    def start(self) -> None:
        self.calls.append(("start", None))

    def initialize(self) -> object:
        self.calls.append(("initialize", None))
        return object()

    def account_read(self, params: Mapping[str, Any]) -> Mapping[str, Any]:
        self.calls.append(("account/read", dict(params)))
        return {"account": {"root": {"type": "chatgpt"}}}

    def model_list(self, include_hidden: bool = False) -> Mapping[str, Any]:
        self.calls.append(("model/list", include_hidden))
        return {"data": [{"model": PHASE_F_PINNED_MODEL}]}

    def _request_raw(
        self,
        method: str,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        self.calls.append((method, None if params is None else dict(params)))
        if method == "permissionProfile/list":
            return {
                "data": [{"id": PHASE_F_PERMISSION_PROFILE, "allowed": True}]
            }
        if method == "thread/start":
            self.thread_count += 1
            request_id = f"request-{self.thread_count}"
            thread_id = f"raw-thread-{self.thread_count}"
            request = {"id": request_id, "method": method, "params": dict(params or {})}
            response = {
                "id": request_id,
                "result": {
                    "thread": {"id": thread_id},
                    "activePermissionProfile": {"id": PHASE_F_PERMISSION_PROFILE},
                    "approvalPolicy": "never",
                    "cwd": str(self.workspace),
                },
            }
            notification = {
                "method": "thread/started",
                "params": {"thread": {"id": thread_id}},
            }
            self.frames.extend(
                [
                    ("client_to_server", request),
                    ("server_to_client", response),
                    ("server_to_client", notification),
                ]
            )
            return response["result"]
        raise AssertionError(f"unexpected raw method: {method}")

    def wait_for_notification(self, method: str, timeout: float) -> bool:
        self.calls.append(("wait", (method, timeout)))
        return True

    def transcript(self) -> list[tuple[str, Mapping[str, Any]]]:
        return list(self.frames)

    def turn_start(
        self,
        thread_id: str,
        input_items: str,
        params: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        self.calls.append(
            (
                "turn/start",
                {"thread_id": thread_id, "input": input_items, "params": dict(params or {})},
            )
        )
        return {"turn": {"id": "raw-turn-1"}}

    def close(self) -> None:
        self.calls.append(("close", None))


def _config_overrides() -> tuple[str, ...]:
    return (
        'default_permissions="runtime-boundary-worker"',
        'permissions.runtime-boundary-worker.extends=":workspace"',
        'permissions.runtime-boundary-worker.filesystem={":minimal"="read",":root"="deny"}',
        "permissions.runtime-boundary-worker.network.enabled=false",
        'windows.sandbox="elevated"',
    )


def _runtime(tmp_path: Path) -> tuple[PhaseFSdkRuntimeV2, FakeAppServerPort]:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    port = FakeAppServerPort(workspace)
    runtime = PhaseFSdkRuntimeV2(workspace, port=port, environ={})
    return runtime, port


def _schema() -> dict[str, Any]:
    return {"title": "ResultEnvelope", "type": "object"}


def test_fake_transport_uses_exact_v2_thread_and_turn_contract(tmp_path: Path) -> None:
    runtime, port = _runtime(tmp_path)

    runtime.preflight()
    thread = runtime.start_thread()
    result = runtime.run_turn(
        thread,
        task_id="R01",
        prompt="perform R01",
        output_schema=_schema(),
    )

    assert port.open_count == 1
    assert port.thread_requests == [phase_f_thread_start_params(port.workspace)]
    assert "sandbox" not in port.thread_requests[0]
    assert port.thread_requests[0]["permissions"] == PHASE_F_PERMISSION_PROFILE
    assert port.thread_requests[0]["approvalPolicy"] == "never"
    assert port.turn_requests == [
        (
            "phase-f-thread-1",
            "perform R01",
            phase_f_turn_start_params(port.workspace, _schema()),
        )
    ]
    assert "sandboxPolicy" not in port.turn_requests[0][2]
    assert port.turn_requests[0][2]["effort"] == PHASE_F_PINNED_REASONING_EFFORT
    assert result.terminal_status == "completed"
    assert result.cumulative_usage is not None
    assert result.cumulative_usage.total_tokens == 10
    assert runtime.actual_model_turns == 1
    assert runtime.thread_start_evidence is not None
    assert runtime.thread_start_evidence["legacy_sandbox_arguments"] is False


def test_ss1_reuses_one_thread_and_refuses_second_thread(tmp_path: Path) -> None:
    runtime, port = _runtime(tmp_path)
    runtime.preflight()
    thread = runtime.start_thread()

    runtime.run_turn(thread, task_id="R01", prompt="one", output_schema=_schema())
    runtime.run_turn(thread, task_id="R02", prompt="two", output_schema=_schema())

    assert [request[0] for request in port.turn_requests] == [thread.id, thread.id]
    assert len(port.thread_requests) == 1
    assert runtime.actual_model_turns == 2
    with pytest.raises(PhaseFSdkContractError, match="exactly one thread"):
        runtime.start_thread()


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("account", "ChatGPT authentication"),
        ("model", "model is not visible"),
        ("profile", "missing, duplicated, or forbidden"),
    ],
)
def test_preflight_fails_closed_before_thread(
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    runtime, port = _runtime(tmp_path)
    if mutation == "account":
        port.account = "apikey"
    elif mutation == "model":
        port.models = ()
    else:
        port.profiles = ({"id": PHASE_F_PERMISSION_PROFILE, "allowed": False},)

    with pytest.raises(PhaseFSdkContractError, match=message):
        runtime.preflight()

    assert port.thread_requests == []
    assert port.turn_requests == []


@pytest.mark.parametrize("mutation", ["profile", "thread"])
def test_thread_provenance_mismatch_blocks_first_turn(
    tmp_path: Path,
    mutation: str,
) -> None:
    runtime, port = _runtime(tmp_path)
    runtime.preflight()
    if mutation == "profile":
        port.active_profile = ":workspace"
    else:
        port.notification_thread_id = "different-thread"

    with pytest.raises(PhaseFSdkContractError):
        runtime.start_thread()

    assert port.turn_requests == []
    assert runtime.actual_model_turns == 0


def test_api_key_name_blocks_before_port_open(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    port = FakeAppServerPort(workspace)
    runtime = PhaseFSdkRuntimeV2(
        workspace,
        port=port,
        environ={"OPENAI_API_KEY": "value-is-never-read-or-logged"},
    )

    with pytest.raises(PhaseFSdkContractError, match="API key environment names"):
        runtime.preflight()

    assert port.open_count == 0
    assert port.thread_requests == []


def test_module_has_no_direct_subprocess_implementation() -> None:
    source = Path(__file__).resolve().parents[1] / "src" / "benchmark_runner" / "realistic_phase_f_sdk.py"
    text = source.read_text(encoding="utf-8")
    assert "subprocess" not in text


def test_concrete_port_uses_raw_profile_request_and_injected_turn_handle(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    client = FakeRawClient(workspace)
    handle = FakeTurnHandle()
    factory_calls: list[tuple[Path, tuple[str, ...]]] = []

    def client_factory(path: Path, overrides: tuple[str, ...]) -> FakeRawClient:
        factory_calls.append((path, overrides))
        return client

    def handle_factory(
        actual_client: FakeRawClient,
        thread_id: str,
        turn_id: str,
    ) -> FakeTurnHandle:
        assert actual_client is client
        assert (thread_id, turn_id) == ("raw-thread-1", "raw-turn-1")
        return handle

    port = CodexPhaseFAppServerPort(
        workspace,
        config_overrides=_config_overrides(),
        client_factory=client_factory,
        turn_handle_factory=handle_factory,
    )
    runtime = PhaseFSdkRuntimeV2(workspace, port=port, environ={})

    runtime.preflight()
    thread = runtime.start_thread()
    result = runtime.run_turn(
        thread,
        task_id="R01",
        prompt="perform R01",
        output_schema=_schema(),
    )

    assert factory_calls == [(workspace.resolve(), _config_overrides())]
    raw_thread = next(value for name, value in client.calls if name == "thread/start")
    assert raw_thread == phase_f_thread_start_params(workspace)
    raw_turn = next(value for name, value in client.calls if name == "turn/start")
    assert raw_turn["params"] == phase_f_turn_start_params(workspace, _schema())
    assert "sandbox" not in raw_thread
    assert "sandboxPolicy" not in raw_turn["params"]
    assert result.terminal_status == "completed"
    assert runtime.actual_model_turns == 1


def test_default_codex_client_receives_the_pinned_worker_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import benchmark_runner.realistic_phase_f_sdk as sdk_module

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    client = FakeRawClient(workspace)
    captured: dict[str, str] = {}

    def client_factory(
        path: Path,
        overrides: tuple[str, ...],
        *,
        process_environment: Mapping[str, str],
    ) -> FakeRawClient:
        assert path == workspace.resolve()
        assert overrides == _config_overrides()
        captured.update(process_environment)
        return client

    monkeypatch.setattr(
        sdk_module,
        "_recording_codex_client_factory",
        client_factory,
    )
    port = CodexPhaseFAppServerPort(
        workspace,
        config_overrides=_config_overrides(),
        process_environment={"PATH": "synthetic-tail"},
    )

    port.open()
    port.close()

    assert Path(captured["PATH"].split(os.pathsep)[0]) == Path(
        sys.executable
    ).resolve().parent
    assert captured["PYTHONDONTWRITEBYTECODE"] == "1"


def test_concrete_port_scopes_thread_notification_to_each_request(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    client = FakeRawClient(workspace)
    port = CodexPhaseFAppServerPort(
        workspace,
        config_overrides=_config_overrides(),
        client_factory=lambda _path, _overrides: client,
    )

    port.open()
    first = port.start_thread(
        phase_f_thread_start_params(workspace),
        notification_timeout_seconds=2.0,
    )
    second = port.start_thread(
        phase_f_thread_start_params(workspace),
        notification_timeout_seconds=2.0,
    )
    port.close()

    assert verify_phase_f_thread_start(first, workspace=workspace) == "raw-thread-1"
    assert verify_phase_f_thread_start(second, workspace=workspace) == "raw-thread-2"


@pytest.mark.parametrize(
    "overrides",
    [
        (),
        _config_overrides()[:-1],
        _config_overrides()[:2]
        + ('permissions.runtime-boundary-worker.filesystem={":root"="deny"}',)
        + _config_overrides()[3:],
        _config_overrides()[:-1] + ('sandbox_mode="workspace-write"',),
    ],
)
def test_config_override_contract_fails_closed(overrides: tuple[str, ...]) -> None:
    with pytest.raises(PhaseFSdkContractError):
        validate_phase_f_config_overrides(overrides)
