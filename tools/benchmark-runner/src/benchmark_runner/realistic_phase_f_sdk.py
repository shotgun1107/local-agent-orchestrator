"""Runtime-contract-v2 SDK boundary for the first Phase F SS1 Cell.

The runtime is deliberately split at :class:`PhaseFAppServerPort`.  The
production port may wrap ``openai-codex==0.144.4`` later; tests inject a fake
port, so importing and exercising this module never opens an app-server or a
model turn by itself.

This module owns the exact thread/turn wire options.  It does not prepare a
Worker workspace, run SS1, invoke a Judge, or continue to another Cell.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
from collections.abc import Callable, Sequence
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping, Protocol

from pydantic import JsonValue, model_validator

from benchmark_runner.contract import Sha256, StrictModel, present_api_key_environment_names
from benchmark_runner.realistic_routing import canonical_sha256
from benchmark_runner.sdk_common import SdkRuntime, SdkThread, SdkTurnResult, SdkUsage


PHASE_F_RUNTIME_CONTRACT_VERSION = 2
PHASE_F_PINNED_SDK_VERSION = "0.144.4"
PHASE_F_PINNED_MODEL = "gpt-5.6-sol"
PHASE_F_PINNED_REASONING_EFFORT = "high"
PHASE_F_PERMISSION_PROFILE = "runtime-boundary-worker"
PHASE_F_APPROVAL_POLICY_WIRE = "never"
PHASE_F_APPROVAL_MODE = "deny_all"
PHASE_F_THREAD_NOTIFICATION_TIMEOUT_SECONDS = 2.0
PHASE_F_CONFIGURATION_TIMEOUT_SECONDS = 15.0


class PhaseFSdkContractError(RuntimeError):
    """Raised before or at the exact SDK boundary when v2 is violated."""


class PhaseFConfigurationValidationEvidence(StrictModel):
    """Only hashes of config/read payloads; never config values or diagnostics."""

    schema_version: Literal[1] = 1
    source_method: Literal["config/read"] = "config/read"
    sdk_version: Literal[PHASE_F_PINNED_SDK_VERSION] = PHASE_F_PINNED_SDK_VERSION
    cli_version: Literal[PHASE_F_PINNED_SDK_VERSION] = PHASE_F_PINNED_SDK_VERSION
    cli_binary_sha256: Sha256
    cwd_sha256: Sha256
    config_overrides_sha256: Sha256
    effective_config_sha256: Sha256
    config_layers_sha256: Sha256
    user_config_path_sha256: Sha256
    evidence_sha256: Sha256

    @model_validator(mode="after")
    def evidence_is_canonical(self) -> "PhaseFConfigurationValidationEvidence":
        payload = self.model_dump(mode="json", exclude={"evidence_sha256"})
        if self.evidence_sha256 != canonical_sha256(payload):
            raise ValueError("Phase F configuration validation hash differs")
        return self


def build_phase_f_worker_process_environment(
    environ: Mapping[str, str] | None,
    *,
    python_executable: Path | None = None,
) -> dict[str, str]:
    """Make the Worker shell resolve ``python`` to the Controller interpreter."""

    source = os.environ if environ is None else environ
    present = present_api_key_environment_names(source)
    if present:
        raise PhaseFSdkContractError(
            "API key environment names are present: " + ", ".join(present)
        )
    executable = Path(python_executable or sys.executable).resolve(strict=True)
    environment = {str(name): str(value) for name, value in source.items()}
    environment.pop("PYTHONHOME", None)
    environment.pop("PYTHONPATH", None)
    python_directory = str(executable.parent)
    existing = [
        value
        for value in environment.get("PATH", "").split(os.pathsep)
        if value and Path(value).resolve(strict=False) != executable.parent
    ]
    environment["PATH"] = os.pathsep.join([python_directory, *existing])
    virtual_environment = executable.parent.parent
    if (virtual_environment / "pyvenv.cfg").is_file():
        environment["VIRTUAL_ENV"] = str(virtual_environment)
    else:
        environment.pop("VIRTUAL_ENV", None)
    environment.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
        }
    )
    return environment


def build_phase_f_config_overrides(workspace: Path) -> tuple[str, ...]:
    """Bind runtime-v2 root-deny policy to one exact Worker workspace."""

    root = Path(workspace).resolve(strict=True)
    if not root.is_dir():
        raise PhaseFSdkContractError("Phase F workspace is not a directory")
    encoded = json.dumps(str(root), ensure_ascii=False)
    filesystem = (
        '{":minimal"="read",":root"="deny",'
        + encoded
        + '="write"}'
    )
    return validate_phase_f_config_overrides(
        (
            'default_permissions="runtime-boundary-worker"',
            'permissions.runtime-boundary-worker.extends=":workspace"',
            "permissions.runtime-boundary-worker.filesystem=" + filesystem,
            "permissions.runtime-boundary-worker.network.enabled=false",
            'windows.sandbox="elevated"',
        )
    )


@dataclass(frozen=True)
class PhaseFThreadStartObservation:
    """Raw facts required to accept one persistent SS1 thread."""

    request: Mapping[str, JsonValue]
    response: Mapping[str, JsonValue]
    notification: Mapping[str, JsonValue]
    transcript_sha256: str


class PhaseFTurnHandle(Protocol):
    def run(self) -> Any: ...

    def interrupt(self) -> None: ...


class PhaseFAppServerPort(Protocol):
    """Small injectable boundary around the pinned app-server transport."""

    sdk_version: str

    def open(self) -> None: ...

    def validate_configuration(self, cwd: str) -> PhaseFConfigurationValidationEvidence: ...

    def account_type(self) -> str: ...

    def visible_model_ids(self) -> tuple[str, ...]: ...

    def permission_profiles(self, cwd: str) -> tuple[Mapping[str, JsonValue], ...]: ...

    def start_thread(
        self,
        params: Mapping[str, JsonValue],
        *,
        notification_timeout_seconds: float,
    ) -> PhaseFThreadStartObservation: ...

    def start_turn(
        self,
        thread_id: str,
        prompt: str,
        params: Mapping[str, JsonValue],
    ) -> PhaseFTurnHandle: ...

    def close(self) -> None: ...


class PhaseFRawCodexClient(Protocol):
    """The tested subset of ``openai_codex.client.CodexClient``."""

    phase_f_cli_binary_sha256: str

    def start(self) -> None: ...

    def initialize(self) -> Any: ...

    def account_read(self, params: Mapping[str, JsonValue]) -> Any: ...

    def model_list(self, include_hidden: bool = False) -> Any: ...

    def _request_raw(
        self,
        method: str,
        params: Mapping[str, JsonValue] | None = None,
    ) -> JsonValue: ...

    def wait_for_notification(self, method: str, timeout: float) -> bool: ...

    def transcript(self) -> list[tuple[str, Mapping[str, JsonValue]]]: ...

    def turn_start(
        self,
        thread_id: str,
        input_items: str,
        params: Mapping[str, JsonValue] | None = None,
    ) -> Any: ...

    def close(self) -> None: ...


RawClientFactory = Callable[[Path, tuple[str, ...]], PhaseFRawCodexClient]
TurnHandleFactory = Callable[[PhaseFRawCodexClient, str, str], PhaseFTurnHandle]


def validate_phase_f_config_overrides(overrides: Sequence[str]) -> tuple[str, ...]:
    """Validate the five runtime-v2 app-server overrides before launch."""

    values = tuple(overrides)
    required_prefixes = (
        'default_permissions="runtime-boundary-worker"',
        'permissions.runtime-boundary-worker.extends=":workspace"',
        "permissions.runtime-boundary-worker.filesystem=",
        "permissions.runtime-boundary-worker.network.enabled=false",
        'windows.sandbox="elevated"',
    )
    if len(values) != len(required_prefixes) or len(set(values)) != len(values):
        raise PhaseFSdkContractError("Phase F requires exactly five config overrides")
    for index, prefix in enumerate(required_prefixes):
        if not values[index].startswith(prefix):
            raise PhaseFSdkContractError(
                f"Phase F config override {index + 1} differs"
            )
    joined = "\n".join(values).lower()
    if "sandbox_mode" in joined or "sandbox_workspace_write" in joined:
        raise PhaseFSdkContractError("Phase F config contains legacy sandbox settings")
    filesystem = values[2]
    if '":minimal"="read"' not in filesystem or '":root"="deny"' not in filesystem:
        raise PhaseFSdkContractError("Phase F filesystem profile is incomplete")
    return values


def _recording_codex_client_factory(
    workspace: Path,
    config_overrides: tuple[str, ...],
    *,
    process_environment: Mapping[str, str],
) -> PhaseFRawCodexClient:
    """Create the real pinned SDK client lazily; construction makes no turn."""

    try:
        from importlib.metadata import version
        from codex_cli_bin import bundled_codex_path
        from openai_codex.client import CodexClient, CodexConfig
    except ImportError as exc:
        raise PhaseFSdkContractError(
            "install openai-codex==0.144.4 for the Phase F live port"
        ) from exc

    if (
        version("openai-codex") != PHASE_F_PINNED_SDK_VERSION
        or version("openai-codex-cli-bin") != PHASE_F_PINNED_SDK_VERSION
    ):
        raise PhaseFSdkContractError("Phase F installed SDK/CLI version differs")
    cli_binary = Path(bundled_codex_path()).resolve(strict=True)
    cli_binary_sha256 = hashlib.sha256(cli_binary.read_bytes()).hexdigest()

    class RecordingCodexClient(CodexClient):  # type: ignore[misc, valid-type]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self._phase_f_frames: list[
                tuple[str, Mapping[str, JsonValue]]
            ] = []
            self._phase_f_condition = threading.Condition()
            self.phase_f_cli_binary_sha256 = cli_binary_sha256

        def start(self) -> None:
            if (
                Path(bundled_codex_path()).resolve(strict=True) != cli_binary
                or hashlib.sha256(cli_binary.read_bytes()).hexdigest() != cli_binary_sha256
            ):
                raise PhaseFSdkContractError("Phase F CLI changed before launch")
            super().start()

        def _record(self, direction: str, payload: Mapping[str, JsonValue]) -> None:
            frozen = json.loads(json.dumps(payload, sort_keys=True))
            with self._phase_f_condition:
                self._phase_f_frames.append((direction, frozen))
                self._phase_f_condition.notify_all()

        def _write_message(self, payload: dict[str, JsonValue]) -> None:
            self._record("client_to_server", payload)
            super()._write_message(payload)

        def _read_message(self) -> dict[str, JsonValue]:
            payload = super()._read_message()
            self._record("server_to_client", payload)
            return payload

        def wait_for_notification(self, method: str, timeout: float) -> bool:
            deadline = time.monotonic() + timeout
            with self._phase_f_condition:
                while True:
                    if any(
                        direction == "server_to_client"
                        and frame.get("method") == method
                        and "id" not in frame
                        for direction, frame in self._phase_f_frames
                    ):
                        return True
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return False
                    self._phase_f_condition.wait(remaining)

        def transcript(self) -> list[tuple[str, Mapping[str, JsonValue]]]:
            with self._phase_f_condition:
                return [
                    (direction, dict(frame))
                    for direction, frame in self._phase_f_frames
                ]

    config = CodexConfig(
        codex_bin=None,
        launch_args_override=None,
        config_overrides=config_overrides,
        cwd=str(workspace),
        env=dict(process_environment),
        experimental_api=True,
    )
    return RecordingCodexClient(
        config,
        approval_handler=lambda _method, _params: {"decision": "decline"},
    )


def _default_turn_handle_factory(
    client: PhaseFRawCodexClient,
    thread_id: str,
    turn_id: str,
) -> PhaseFTurnHandle:
    try:
        from openai_codex import TurnHandle
    except ImportError as exc:
        raise PhaseFSdkContractError(
            "install openai-codex==0.144.4 for the Phase F live port"
        ) from exc
    return TurnHandle(client, thread_id, turn_id)  # type: ignore[arg-type]


def _attribute_or_key(value: object, name: str) -> object:
    if isinstance(value, Mapping):
        return value.get(name)
    return getattr(value, name, None)


class CodexPhaseFAppServerPort:
    """Concrete pinned SDK port.  Nothing starts until ``open()`` is called."""

    sdk_version = PHASE_F_PINNED_SDK_VERSION

    def __init__(
        self,
        workspace: Path,
        *,
        config_overrides: Sequence[str],
        process_environment: Mapping[str, str] | None = None,
        client_factory: RawClientFactory | None = None,
        turn_handle_factory: TurnHandleFactory = _default_turn_handle_factory,
        configuration_timeout_seconds: float = PHASE_F_CONFIGURATION_TIMEOUT_SECONDS,
    ) -> None:
        if configuration_timeout_seconds <= 0:
            raise ValueError("Phase F configuration timeout must be positive")
        self._configuration_timeout_seconds = configuration_timeout_seconds
        self.workspace = Path(workspace).resolve()
        self.config_overrides = validate_phase_f_config_overrides(config_overrides)
        worker_environment = build_phase_f_worker_process_environment(
            process_environment,
            python_executable=Path(sys.executable),
        )
        self._expected_user_config = (
            Path(worker_environment.get("CODEX_HOME") or Path.home() / ".codex")
            / "config.toml"
        ).resolve()
        self._client_factory = (
            client_factory
            if client_factory is not None
            else lambda path, overrides: _recording_codex_client_factory(
                path,
                overrides,
                process_environment=worker_environment,
            )
        )
        self._turn_handle_factory = turn_handle_factory
        self._client: PhaseFRawCodexClient | None = None
        self._account_type = "unknown"
        self._models: tuple[str, ...] = ()
        self._configuration_evidence: PhaseFConfigurationValidationEvidence | None = None

    def _require_client(self) -> PhaseFRawCodexClient:
        if self._client is None:
            raise PhaseFSdkContractError("Phase F app-server port is not open")
        return self._client

    def open(self) -> None:
        if self._client is not None:
            return
        client = self._client_factory(self.workspace, self.config_overrides)
        try:
            client.start()
            client.initialize()
        except Exception:
            client.close()
            raise PhaseFSdkContractError("Phase F app-server preflight startup failed") from None
        self._client = client

    def account_type(self) -> str:
        account = self._require_client().account_read({})
        account_value = _attribute_or_key(account, "account")
        root = _attribute_or_key(account_value, "root")
        account_type = _attribute_or_key(root, "type")
        self._account_type = str(
            _attribute_or_key(account_type, "value") or account_type or "none"
        )
        return self._account_type

    def visible_model_ids(self) -> tuple[str, ...]:
        response = self._require_client().model_list(include_hidden=True)
        items = _attribute_or_key(response, "data") or _attribute_or_key(response, "models") or ()
        self._models = tuple(sorted({
            str(_attribute_or_key(item, "model") or _attribute_or_key(item, "id"))
            for item in items  # type: ignore[union-attr]
            if _attribute_or_key(item, "model") or _attribute_or_key(item, "id")
        }))
        return self._models

    def _read_configuration(self, cwd: str) -> PhaseFConfigurationValidationEvidence:
        if Path(cwd).resolve() != self.workspace:
            raise PhaseFSdkContractError("Phase F config validation workspace differs")
        client = self._require_client()
        # The pinned server parses its own layered ConfigToml here without
        # thread/start. A Python TOML syntax check is not an equivalent gate.
        results: list[Any] = []
        failed = threading.Event()
        finished = threading.Event()

        def read() -> None:
            try:
                results.append(client._request_raw(
                    "config/read", {"cwd": str(self.workspace), "includeLayers": True}
                ))
            except Exception:
                failed.set()
            finally:
                finished.set()

        reader = threading.Thread(target=read, name="phase-f-config-read", daemon=True)
        reader.start()
        if not finished.wait(self._configuration_timeout_seconds):
            self.close()
            reader.join(timeout=2.0)
            raise PhaseFSdkContractError("Phase F configuration validation timed out")
        if failed.is_set() or not results:
            # Config decoder errors can quote raw TOML values. Do not chain them.
            raise PhaseFSdkContractError(
                "Phase F configuration validation failed (config/read)"
            ) from None
        result = results[0]
        try:
            if not isinstance(result, Mapping):
                raise ValueError
            config = result.get("config")
            layers = result.get("layers")
            origins = result.get("origins")
            if (
                not isinstance(config, Mapping)
                or not isinstance(origins, Mapping)
                or not isinstance(layers, list)
                or not layers
            ):
                raise ValueError
            user_layers = []
            for layer in layers:
                if (
                    not isinstance(layer, Mapping)
                    or not isinstance(layer.get("name"), Mapping)
                    or not isinstance(layer.get("config"), Mapping)
                    or not isinstance(layer.get("version"), str)
                    or not layer["version"]
                ):
                    raise ValueError
                if layer["name"].get("type") == "user":
                    user_layers.append(layer)
            if len(user_layers) != 1:
                raise ValueError
            user_layer = user_layers[0]
            user_file = user_layer["name"].get("file")
            if (
                not isinstance(user_file, str)
                or not Path(user_file).is_absolute()
                or Path(user_file).resolve() != self._expected_user_config
                or user_layer.get("disabledReason") is not None
                or user_layer["name"].get("profile") is not None
            ):
                raise ValueError
            values = {
                "schema_version": 1,
                "source_method": "config/read",
                "sdk_version": PHASE_F_PINNED_SDK_VERSION,
                "cli_version": PHASE_F_PINNED_SDK_VERSION,
                "cli_binary_sha256": client.phase_f_cli_binary_sha256,
                "cwd_sha256": canonical_sha256(str(self.workspace)),
                "config_overrides_sha256": canonical_sha256(list(self.config_overrides)),
                "effective_config_sha256": canonical_sha256(dict(config)),
                "config_layers_sha256": canonical_sha256(
                    {"layers": layers, "origins": origins}
                ),
                "user_config_path_sha256": canonical_sha256(str(self._expected_user_config)),
            }
            return PhaseFConfigurationValidationEvidence(
                **values, evidence_sha256=canonical_sha256(values)
            )
        except Exception:
            # Response validation errors may also contain raw config values.
            raise PhaseFSdkContractError(
                "Phase F configuration provenance is invalid or from a different user"
            ) from None

    def validate_configuration(self, cwd: str) -> PhaseFConfigurationValidationEvidence:
        baseline = self._configuration_evidence
        self._configuration_evidence = None
        current = self._read_configuration(cwd)
        if baseline is not None and current != baseline:
            raise PhaseFSdkContractError("Phase F configuration changed after preflight")
        self._configuration_evidence = current
        return current

    def permission_profiles(
        self,
        cwd: str,
    ) -> tuple[Mapping[str, JsonValue], ...]:
        result = self._require_client()._request_raw(
            "permissionProfile/list",
            {"cwd": cwd},
        )
        if isinstance(result, list):
            items = result
        elif isinstance(result, Mapping):
            items = result.get("data") or result.get("profiles") or []
        else:
            items = []
        if not isinstance(items, list) or any(not isinstance(item, Mapping) for item in items):
            raise PhaseFSdkContractError("permissionProfile/list response is invalid")
        return tuple(dict(item) for item in items)

    def start_thread(
        self,
        params: Mapping[str, JsonValue],
        *,
        notification_timeout_seconds: float,
    ) -> PhaseFThreadStartObservation:
        client = self._require_client()
        if self._configuration_evidence is None:
            raise PhaseFSdkContractError("Phase F configuration preflight is required")
        self.validate_configuration(str(self.workspace))
        transcript_offset = len(client.transcript())
        result = client._request_raw("thread/start", params)
        if not isinstance(result, Mapping):
            raise PhaseFSdkContractError("thread/start response is invalid")
        deadline = time.monotonic() + notification_timeout_seconds
        while True:
            frames = client.transcript()
            notifications = [
                frame
                for direction, frame in frames[transcript_offset:]
                if direction == "server_to_client"
                and frame.get("method") == "thread/started"
                and "id" not in frame
            ]
            if notifications:
                break
            if time.monotonic() >= deadline:
                raise PhaseFSdkContractError("thread/started notification timed out")
            time.sleep(0.01)
        if len(notifications) != 1:
            raise PhaseFSdkContractError("thread/started notification count differs")
        return PhaseFThreadStartObservation(
            request=dict(params),
            response=dict(result),
            notification=dict(notifications[0]),
            transcript_sha256=canonical_sha256(
                [[direction, dict(frame)] for direction, frame in frames]
            ),
        )

    def start_turn(
        self,
        thread_id: str,
        prompt: str,
        params: Mapping[str, JsonValue],
    ) -> PhaseFTurnHandle:
        client = self._require_client()
        started = client.turn_start(thread_id, prompt, params=dict(params))
        turn = _attribute_or_key(started, "turn")
        turn_id = _attribute_or_key(turn, "id")
        if not isinstance(turn_id, str) or not turn_id:
            raise PhaseFSdkContractError("turn/start response has no turn ID")
        return self._turn_handle_factory(client, thread_id, turn_id)

    def close(self) -> None:
        client = self._client
        self._client = None
        self._account_type = "unknown"
        self._models = ()
        self._configuration_evidence = None
        if client is not None:
            client.close()


def phase_f_thread_start_params(workspace: Path) -> dict[str, JsonValue]:
    """Return the exact v2 thread request; legacy ``sandbox`` is absent."""

    return {
        "approvalPolicy": PHASE_F_APPROVAL_POLICY_WIRE,
        "config": {"default_permissions": PHASE_F_PERMISSION_PROFILE},
        "cwd": str(workspace.resolve()),
        "ephemeral": False,
        "model": PHASE_F_PINNED_MODEL,
        "permissions": PHASE_F_PERMISSION_PROFILE,
    }


def phase_f_turn_start_params(
    workspace: Path,
    output_schema: Mapping[str, Any],
) -> dict[str, JsonValue]:
    """Return exact per-turn overrides; legacy ``sandboxPolicy`` is absent."""

    return {
        "approvalPolicy": PHASE_F_APPROVAL_POLICY_WIRE,
        "cwd": str(workspace.resolve()),
        "effort": PHASE_F_PINNED_REASONING_EFFORT,
        "model": PHASE_F_PINNED_MODEL,
        "outputSchema": json.loads(json.dumps(output_schema)),
    }


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PhaseFSdkContractError(f"{label} must be an object")
    return value


def _thread_id(value: object, label: str) -> str:
    thread = _mapping(value, label).get("thread")
    thread_id = _mapping(thread, f"{label}.thread").get("id")
    if not isinstance(thread_id, str) or not thread_id:
        raise PhaseFSdkContractError(f"{label} has no thread ID")
    return thread_id


def verify_phase_f_thread_start(
    observation: PhaseFThreadStartObservation,
    *,
    workspace: Path,
) -> str:
    """Recompute the active-profile binding from raw request/response/event."""

    expected = phase_f_thread_start_params(workspace)
    request = dict(observation.request)
    if request != expected:
        raise PhaseFSdkContractError("Phase F thread/start request differs")
    if "sandbox" in request:
        raise PhaseFSdkContractError("Phase F thread/start used legacy sandbox")

    response = _mapping(observation.response, "thread/start response")
    active = _mapping(
        response.get("activePermissionProfile"),
        "thread/start response activePermissionProfile",
    )
    if active.get("id") != PHASE_F_PERMISSION_PROFILE:
        raise PhaseFSdkContractError("Phase F active permission profile differs")
    if response.get("approvalPolicy") != PHASE_F_APPROVAL_POLICY_WIRE:
        raise PhaseFSdkContractError("Phase F response approval policy differs")
    if str(response.get("cwd", "")) != str(workspace.resolve()):
        raise PhaseFSdkContractError("Phase F response cwd differs")

    response_thread_id = _thread_id(response, "thread/start response")
    notification = _mapping(observation.notification, "thread/started notification")
    if notification.get("method") != "thread/started":
        raise PhaseFSdkContractError("Phase F required thread/started is missing")
    params = _mapping(notification.get("params"), "thread/started params")
    notification_thread_id = _thread_id(params, "thread/started params")
    if notification_thread_id != response_thread_id:
        raise PhaseFSdkContractError("Phase F thread response/event IDs differ")
    if len(observation.transcript_sha256) != 64:
        raise PhaseFSdkContractError("Phase F transcript hash is invalid")
    return response_thread_id


class PhaseFSdkRuntimeV2(SdkRuntime):
    """SS1-compatible runtime using only the approved v2 wire contract."""

    def __init__(
        self,
        workspace: Path,
        *,
        port: PhaseFAppServerPort,
        environ: Mapping[str, str] | None = None,
        timeout_seconds: float = 900.0,
        interrupt_grace_seconds: float = 15.0,
    ) -> None:
        if timeout_seconds <= 0 or interrupt_grace_seconds < 0:
            raise ValueError("Phase F SDK timeout settings are invalid")
        self.workspace = Path(workspace).resolve()
        self.port = port
        self.environ = environ
        self.timeout_seconds = timeout_seconds
        self.interrupt_grace_seconds = interrupt_grace_seconds
        self._opened = False
        self._preflight_complete = False
        self._configuration_evidence: PhaseFConfigurationValidationEvidence | None = None
        self._thread: SdkThread | None = None
        self._actual_model_turns = 0
        self._thread_start_evidence: dict[str, JsonValue] | None = None

    @property
    def actual_model_turns(self) -> int:
        return self._actual_model_turns

    @property
    def thread_start_evidence(self) -> dict[str, JsonValue] | None:
        return dict(self._thread_start_evidence) if self._thread_start_evidence else None

    @property
    def configuration_validation_evidence(self) -> PhaseFConfigurationValidationEvidence | None:
        return self._configuration_evidence

    def _assert_environment(self) -> None:
        present = present_api_key_environment_names(self.environ)
        if present:
            raise PhaseFSdkContractError(
                "API key environment names are present: " + ", ".join(present)
            )
        if not self.workspace.is_absolute() or not self.workspace.is_dir():
            raise PhaseFSdkContractError(
                "Phase F workspace must be an existing absolute directory"
            )

    def preflight(self) -> None:
        self._preflight_complete = False
        self._configuration_evidence = None
        self._assert_environment()
        if self.port.sdk_version != PHASE_F_PINNED_SDK_VERSION:
            raise PhaseFSdkContractError("Phase F SDK version differs")
        if not self._opened:
            self.port.open()
            self._opened = True
        self._configuration_evidence = self.port.validate_configuration(str(self.workspace))
        if not isinstance(self._configuration_evidence, PhaseFConfigurationValidationEvidence):
            raise PhaseFSdkContractError("Phase F configuration validation Evidence is missing")
        if self.port.account_type() != "chatgpt":
            raise PhaseFSdkContractError("Phase F requires ChatGPT authentication")
        if PHASE_F_PINNED_MODEL not in self.port.visible_model_ids():
            raise PhaseFSdkContractError("Phase F pinned model is not visible")
        profiles = tuple(self.port.permission_profiles(str(self.workspace)))
        matching = [
            item
            for item in profiles
            if item.get("id") == PHASE_F_PERMISSION_PROFILE
            and item.get("allowed") is True
        ]
        if len(matching) != 1:
            raise PhaseFSdkContractError(
                "Phase F permission profile is missing, duplicated, or forbidden"
            )
        self._preflight_complete = True

    def start_thread(self) -> SdkThread:
        self._assert_environment()
        if not self._preflight_complete:
            raise PhaseFSdkContractError("Phase F preflight must run before thread/start")
        if self._thread is not None:
            raise PhaseFSdkContractError("Phase F SS1 permits exactly one thread")
        observation = self.port.start_thread(
            phase_f_thread_start_params(self.workspace),
            notification_timeout_seconds=PHASE_F_THREAD_NOTIFICATION_TIMEOUT_SECONDS,
        )
        thread_id = verify_phase_f_thread_start(
            observation,
            workspace=self.workspace,
        )
        self._thread = SdkThread(thread_id)
        self._thread_start_evidence = {
            "runtime_contract_version": PHASE_F_RUNTIME_CONTRACT_VERSION,
            "thread_id_sha256": canonical_sha256(thread_id),
            "transcript_sha256": observation.transcript_sha256,
            "permission_profile_id": PHASE_F_PERMISSION_PROFILE,
            "approval_mode": PHASE_F_APPROVAL_MODE,
            "approval_policy_wire": PHASE_F_APPROVAL_POLICY_WIRE,
            "legacy_sandbox_arguments": False,
        }
        return self._thread

    @staticmethod
    def _terminal_status(result: object) -> str:
        status = getattr(result, "status", "unknown")
        return str(getattr(status, "value", status))

    @staticmethod
    def _raw_result(result: object) -> Any:
        response = getattr(result, "final_response", None)
        if not isinstance(response, str):
            return response
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return response

    @staticmethod
    def _usage(result: object) -> SdkUsage | None:
        usage = getattr(result, "usage", None)
        total = getattr(usage, "total", None)
        if total is None:
            return None
        try:
            return SdkUsage(
                input_tokens=int(total.input_tokens),
                output_tokens=int(total.output_tokens),
                total_tokens=int(total.total_tokens),
            )
        except (AttributeError, TypeError, ValueError):
            return None

    def run_turn(
        self,
        thread: SdkThread,
        *,
        task_id: str,
        prompt: str,
        output_schema: dict[str, Any],
    ) -> SdkTurnResult:
        del task_id
        self._assert_environment()
        if self._thread is None or thread != self._thread:
            raise PhaseFSdkContractError("Phase F turn used an unknown SS1 thread")
        if output_schema.get("title") != "ResultEnvelope":
            raise PhaseFSdkContractError("Phase F turn requires ResultEnvelope")
        params = phase_f_turn_start_params(self.workspace, output_schema)
        if "sandboxPolicy" in params or "sandbox" in params:
            raise PhaseFSdkContractError("Phase F turn used legacy sandbox")

        handle = self.port.start_turn(thread.id, prompt, params)
        self._actual_model_turns += 1
        result_box: list[Any] = []
        error_box: list[BaseException] = []
        finished = threading.Event()
        started = time.monotonic()

        def consume() -> None:
            try:
                result_box.append(handle.run())
            except BaseException as exc:  # transport errors are normalized below
                error_box.append(exc)
            finally:
                finished.set()

        threading.Thread(target=consume, name="phase-f-sdk-turn", daemon=True).start()
        if not finished.wait(self.timeout_seconds):
            try:
                handle.interrupt()
            except Exception:
                pass
            if not finished.wait(self.interrupt_grace_seconds):
                return SdkTurnResult(
                    terminal_status="unknown",
                    raw_result=None,
                    cumulative_usage=None,
                    duration_seconds=time.monotonic() - started,
                    error_kind="SdkTurnTimeout",
                )
        if error_box:
            return SdkTurnResult(
                terminal_status="unknown",
                raw_result={"error_kind": type(error_box[0]).__name__},
                cumulative_usage=None,
                duration_seconds=time.monotonic() - started,
                error_kind=type(error_box[0]).__name__,
            )
        if not result_box:
            return SdkTurnResult(
                terminal_status="unknown",
                raw_result=None,
                cumulative_usage=None,
                duration_seconds=time.monotonic() - started,
                error_kind="SdkTurnResultMissing",
            )
        raw = result_box[0]
        duration_ms = getattr(raw, "duration_ms", None)
        return SdkTurnResult(
            terminal_status=self._terminal_status(raw),
            raw_result=self._raw_result(raw),
            cumulative_usage=self._usage(raw),
            duration_seconds=(
                float(duration_ms) / 1000.0
                if isinstance(duration_ms, (int, float)) and duration_ms >= 0
                else time.monotonic() - started
            ),
        )

    def close(self) -> None:
        if self._opened:
            self.port.close()
        self._opened = False
        self._preflight_complete = False
        self._configuration_evidence = None
        self._thread = None
