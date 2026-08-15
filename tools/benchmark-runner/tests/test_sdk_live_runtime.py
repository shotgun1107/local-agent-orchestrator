from __future__ import annotations

import inspect
import hashlib
import json
import shutil
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from benchmark_runner.adapter import CellContext
from benchmark_runner.contract import ArtifactIdentity, FixtureIdentity, PlannedCell
from benchmark_runner.failure_scenarios import CONFIG_SOURCE, NORMALIZATION_SOURCE
from benchmark_runner.plan import build_sdk_controlled_plan
from benchmark_runner.runner import verify_sealed_cell
from benchmark_runner.sdk_baselines import SdkBaselineAdapter, SdkBaselineConfig
from benchmark_runner.sdk_common import (
    PINNED_MODEL,
    PINNED_REASONING_EFFORT,
    CodexSdkBindings,
    CodexSdkRuntime,
    WorkerContract,
)
from benchmark_runner.sdk_cells import (
    initialize_sdk_experiment,
    run_sdk_live_cell,
    runner_source_sha256,
)
from benchmark_runner.workspace import FixtureRestorer, load_frozen_manifest


COMPLETED_RESULT = {
    "schema_version": 1,
    "status_claim": "completed",
    "summary": "mocked SDK result",
    "artifacts": [],
    "changed_paths": [],
    "checks_run_by_worker": [],
    "assumptions": [],
    "warnings": [],
    "requested_followup": None,
}
RESULT_SCHEMA = {"title": "ResultEnvelope", "type": "object"}
REPOSITORY_ROOT = Path(__file__).parents[3]
MANIFEST_PATH = (
    REPOSITORY_ROOT / "benchmarks" / "manifests" / "sdk-controlled-pilot-v1.yaml"
)
B1_SOURCE_ROOT = REPOSITORY_ROOT / "stages" / "b1-sequential" / "src"


def _git() -> Path:
    executable = shutil.which("git")
    assert executable is not None
    return Path(executable)


@dataclass
class MockTurnResult:
    status: Any
    final_response: str | None
    usage: Any
    duration_ms: int | None = 125


class MockTurnHandle:
    def __init__(self, result: MockTurnResult) -> None:
        self.result = result
        self.run_calls = 0
        self.interrupt_calls = 0

    def run(self) -> MockTurnResult:
        self.run_calls += 1
        return self.result

    def interrupt(self) -> None:
        self.interrupt_calls += 1


class MockThread:
    def __init__(self, thread_id: str) -> None:
        self.id = thread_id
        self.turn_calls: list[tuple[str, dict[str, Any]]] = []
        self.handles: list[MockTurnHandle] = []

    def turn(self, prompt: str, **kwargs: Any) -> MockTurnHandle:
        turn_no = len(self.turn_calls) + 1
        self.turn_calls.append((prompt, kwargs))
        usage = SimpleNamespace(
            total=SimpleNamespace(
                input_tokens=10 * turn_no,
                output_tokens=5 * turn_no,
                total_tokens=15 * turn_no,
            )
        )
        handle = MockTurnHandle(
            MockTurnResult(
                status=SimpleNamespace(value="completed"),
                final_response=json.dumps(COMPLETED_RESULT),
                usage=usage,
            )
        )
        self.handles.append(handle)
        return handle


class MockClient:
    def __init__(self, account_type: str = "chatgpt") -> None:
        self.account_type = account_type
        self.account_calls: list[bool] = []
        self.thread_start_calls: list[dict[str, Any]] = []
        self.threads: list[MockThread] = []

    def account(self, *, refresh_token: bool = False) -> Any:
        self.account_calls.append(refresh_token)
        return SimpleNamespace(
            account=SimpleNamespace(root=SimpleNamespace(type=self.account_type))
        )

    def thread_start(self, **kwargs: Any) -> MockThread:
        self.thread_start_calls.append(kwargs)
        thread = MockThread(f"mock-thread-{len(self.threads) + 1}")
        self.threads.append(thread)
        return thread


class MockCodexContext:
    def __init__(self, client: MockClient) -> None:
        self.client = client
        self.enter_calls = 0
        self.exit_calls: list[tuple[Any, Any, Any]] = []

    def __enter__(self) -> MockClient:
        self.enter_calls += 1
        return self.client

    def __exit__(self, *args: Any) -> None:
        self.exit_calls.append(args)


def _bindings(context: MockCodexContext) -> CodexSdkBindings:
    return CodexSdkBindings(
        sdk_version="0.144.4",
        codex_factory=lambda: context,
        approval_deny_all="DENY_ALL",
        sandbox_workspace_write="WORKSPACE_WRITE",
    )


def test_mocked_sdk_preflight_and_turn_use_every_frozen_option(tmp_path: Path) -> None:
    client = MockClient()
    context = MockCodexContext(client)
    runtime = CodexSdkRuntime(
        tmp_path,
        bindings=_bindings(context),
        environ={},
    )

    runtime.preflight()
    assert context.enter_calls == 1
    assert client.account_calls == [False]
    assert client.thread_start_calls == []
    assert runtime.actual_model_turns == 0
    assert runtime.preflight_evidence == {
        "sdk_version": "0.144.4",
        "account_type": "chatgpt",
        "model": PINNED_MODEL,
        "reasoning_effort": PINNED_REASONING_EFFORT,
        "thread_sandbox": "workspace_write",
        "turn_sandbox": "workspace_write",
        "thread_approval_mode": "deny_all",
        "turn_approval_mode": "deny_all",
        "output_schema_title": "ResultEnvelope",
        "validated_without_model_turn": True,
        "actual_model_turns": 0,
        "cwd": str(tmp_path.resolve()),
        "ephemeral": False,
        "service_tier": "unspecified",
        "summary": "unspecified",
        "api_key_environment_names_present": [],
    }

    thread = runtime.start_thread()
    assert client.thread_start_calls == [
        {
            "approval_mode": "DENY_ALL",
            "cwd": str(tmp_path.resolve()),
            "ephemeral": False,
            "model": PINNED_MODEL,
            "sandbox": "WORKSPACE_WRITE",
        }
    ]
    result = runtime.run_turn(
        thread,
        task_id="T1",
        prompt="fixed prompt",
        output_schema=RESULT_SCHEMA,
    )
    assert client.threads[0].turn_calls == [
        (
            "fixed prompt",
            {
                "approval_mode": "DENY_ALL",
                "cwd": str(tmp_path.resolve()),
                "effort": PINNED_REASONING_EFFORT,
                "model": PINNED_MODEL,
                "output_schema": RESULT_SCHEMA,
                "sandbox": "WORKSPACE_WRITE",
            },
        )
    ]
    assert result.terminal_status == "completed"
    assert result.raw_result == COMPLETED_RESULT
    assert result.cumulative_usage is not None
    assert result.cumulative_usage.public_payload() == {
        "input_tokens": 10,
        "output_tokens": 5,
        "total_tokens": 15,
    }
    assert result.duration_seconds == 0.125
    assert runtime.actual_model_turns == 1

    runtime.close()
    assert len(context.exit_calls) == 1


def test_same_thread_reports_cumulative_usage_and_new_thread_restarts_it(
    tmp_path: Path,
) -> None:
    client = MockClient()
    runtime = CodexSdkRuntime(
        tmp_path,
        bindings=_bindings(MockCodexContext(client)),
        environ={},
    )
    runtime.preflight()
    first_thread = runtime.start_thread()
    first = runtime.run_turn(
        first_thread, task_id="T1", prompt="one", output_schema=RESULT_SCHEMA
    )
    second = runtime.run_turn(
        first_thread, task_id="T2", prompt="two", output_schema=RESULT_SCHEMA
    )
    new_thread = runtime.start_thread()
    fresh = runtime.run_turn(
        new_thread, task_id="T2", prompt="two", output_schema=RESULT_SCHEMA
    )
    assert first.cumulative_usage is not None
    assert second.cumulative_usage is not None
    assert fresh.cumulative_usage is not None
    assert first.cumulative_usage.total_tokens == 15
    assert second.cumulative_usage.total_tokens == 30
    assert fresh.cumulative_usage.total_tokens == 15
    assert runtime.actual_model_turns == 3
    runtime.close()


@dataclass(frozen=True)
class MockTask:
    task_id: str


@pytest.mark.parametrize(
    ("variant", "task_count", "expected_threads", "expected_tokens"),
    [
        ("c0", 1, 1, 15),
        ("c1", 2, 1, 30),
        ("c2", 2, 2, 30),
    ],
)
def test_baseline_adapters_use_the_mocked_live_runtime_contract(
    tmp_path: Path,
    variant: str,
    task_count: int,
    expected_threads: int,
    expected_tokens: int,
) -> None:
    client = MockClient()
    context = MockCodexContext(client)
    runtime = CodexSdkRuntime(
        tmp_path,
        bindings=_bindings(context),
        environ={},
    )
    adapter = SdkBaselineAdapter(
        SdkBaselineConfig(
            variant_id=variant,
            tasks=tuple(MockTask(f"T{index}") for index in range(1, task_count + 1)),
            contract=WorkerContract(
                render_prompt=lambda task: f"prompt:{task.task_id}",
                result_schema=lambda: RESULT_SCHEMA,
                validate_result=lambda value: value,
                semantics_sha256=lambda task: str(task.task_id[-1]) * 64,
            ),
            runtime=runtime,
        )
    )
    preflight = adapter.preflight(CellContext("exp-mocked-sdk", f"cell-{variant}"))
    assert preflight.ok is True
    evidence = adapter.run(CellContext("exp-mocked-sdk", f"cell-{variant}"))
    assert evidence.outcome_state == "completed"
    assert evidence.normalized_metrics["session_count"] == expected_threads
    assert evidence.normalized_metrics["turn_count"] == task_count
    assert evidence.normalized_metrics["token_usage"]["total_tokens"] == expected_tokens
    assert runtime.actual_model_turns == task_count
    assert len(client.thread_start_calls) == expected_threads
    assert len(context.exit_calls) == 1


class InterruptibleTurnHandle:
    def __init__(self) -> None:
        self.interrupted = threading.Event()
        self.interrupt_calls = 0

    def run(self) -> MockTurnResult:
        self.interrupted.wait(1)
        return MockTurnResult(
            status=SimpleNamespace(value="interrupted"),
            final_response=None,
            usage=None,
            duration_ms=None,
        )

    def interrupt(self) -> None:
        self.interrupt_calls += 1
        self.interrupted.set()


def test_timeout_interrupts_the_live_turn_handle_without_model_use(tmp_path: Path) -> None:
    handle = InterruptibleTurnHandle()

    class InterruptibleThread(MockThread):
        def turn(self, prompt: str, **kwargs: Any) -> InterruptibleTurnHandle:
            self.turn_calls.append((prompt, kwargs))
            return handle

    client = MockClient()
    client.thread_start = lambda **kwargs: InterruptibleThread("mock-timeout-thread")
    runtime = CodexSdkRuntime(
        tmp_path,
        bindings=_bindings(MockCodexContext(client)),
        environ={},
        timeout_seconds=0.01,
        interrupt_grace_seconds=0.2,
    )
    runtime.preflight()
    result = runtime.run_turn(
        runtime.start_thread(),
        task_id="T1",
        prompt="blocked",
        output_schema=RESULT_SCHEMA,
    )
    assert handle.interrupt_calls == 1
    assert result.terminal_status == "interrupted"
    assert runtime.actual_model_turns == 1
    runtime.close()


@pytest.mark.parametrize("name", ["OPENAI_API_KEY", "CODEX_API_KEY"])
def test_api_key_environment_fails_before_sdk_start(
    tmp_path: Path,
    name: str,
) -> None:
    factory_calls = 0

    def factory() -> MockCodexContext:
        nonlocal factory_calls
        factory_calls += 1
        return MockCodexContext(MockClient())

    runtime = CodexSdkRuntime(
        tmp_path,
        bindings=CodexSdkBindings(
            sdk_version="0.144.4",
            codex_factory=factory,
            approval_deny_all="DENY_ALL",
            sandbox_workspace_write="WORKSPACE_WRITE",
        ),
        environ={name: "present-but-never-reported"},
    )
    with pytest.raises(RuntimeError, match=name):
        runtime.preflight()
    assert factory_calls == 0
    assert runtime.actual_model_turns == 0


def test_wrong_sdk_or_account_fails_closed_without_turn(tmp_path: Path) -> None:
    wrong_version_context = MockCodexContext(MockClient())
    wrong_version = CodexSdkRuntime(
        tmp_path,
        bindings=CodexSdkBindings(
            sdk_version="0.145.0",
            codex_factory=lambda: wrong_version_context,
            approval_deny_all="DENY_ALL",
            sandbox_workspace_write="WORKSPACE_WRITE",
        ),
        environ={},
    )
    with pytest.raises(RuntimeError, match="0.144.4"):
        wrong_version.preflight()
    assert wrong_version_context.enter_calls == 0

    api_context = MockCodexContext(MockClient(account_type="apiKey"))
    wrong_account = CodexSdkRuntime(
        tmp_path,
        bindings=_bindings(api_context),
        environ={},
    )
    with pytest.raises(RuntimeError, match="ChatGPT authentication"):
        wrong_account.preflight()
    assert len(api_context.exit_calls) == 1
    assert wrong_account.actual_model_turns == 0


def test_installed_0144_sdk_exposes_the_mocked_contract_surface() -> None:
    openai_codex = pytest.importorskip("openai_codex")
    assert openai_codex.__version__ == "0.144.4"
    thread_start = inspect.signature(openai_codex.Codex.thread_start).parameters
    thread_run = inspect.signature(openai_codex.api.Thread.run).parameters
    thread_turn = inspect.signature(openai_codex.api.Thread.turn).parameters
    assert {
        "approval_mode",
        "cwd",
        "ephemeral",
        "model",
        "sandbox",
    } <= thread_start.keys()
    assert {
        "approval_mode",
        "cwd",
        "effort",
        "model",
        "output_schema",
        "sandbox",
    } <= thread_run.keys()
    assert thread_run.keys() == thread_turn.keys()


def test_mocked_live_cell_reaches_judge_measurement_and_seal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = load_frozen_manifest(MANIFEST_PATH)
    fixture = manifest.fixtures[0]
    cell = PlannedCell(
        cell_id="cell_pilot_c0",
        block_id="block_pilot",
        fixture_id=fixture.id,
        repetition=1,
        variant_id="c0",
        execution_ordinal=1,
    )
    plan = build_sdk_controlled_plan(
        source_manifest_path=MANIFEST_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
        source_manifest_sha256=hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest(),
        fixtures=[
            FixtureIdentity(
                fixture_id=fixture.id,
                source_commit=fixture.commit,
                git_tree=fixture.git_tree,
            )
        ],
        runner=ArtifactIdentity(
            artifact_id="benchmark-runner",
            version="mock-live",
            sha256=runner_source_sha256(),
        ),
        variants=[
            ArtifactIdentity(
                artifact_id="c0",
                version="mock-live",
                sha256="2" * 64,
            )
        ],
        cells=[cell],
        baseline_variant="c0",
        candidate_variants=[],
        decision_policy={"track": "mock_live"},
        environment_fingerprint={"runtime": "mocked_codex"},
        track="sdk_controlled_live_pilot",
        planned_actual_model_turns=None,
    )
    experiment_dir = initialize_sdk_experiment(tmp_path / "state", plan)
    prepared = FixtureRestorer(REPOSITORY_ROOT, str(_git())).restore(
        fixture,
        experiment_dir / "cells" / cell.cell_id / "workspace",
    )
    monkeypatch.syspath_prepend(str(B1_SOURCE_ROOT))
    from orchestrator.contract import RunSpec
    from orchestrator.worker import (
        build_oneshot_envelope,
        render_worker_prompt,
        result_schema,
        task_semantics_sha256,
        validate_result,
    )
    import yaml

    spec = RunSpec.model_validate(
        yaml.safe_load(
            (prepared.workspace / "benchmark-run.yaml").read_text(encoding="utf-8")
        )
    )
    task = build_oneshot_envelope(
        spec,
        run_id="mock-live-run",
        task_id="mock-live-task",
        attempt_id="mock-live-attempt",
        requirements_version=1,
        timeout_seconds=900,
        remaining_attempts=1,
    )

    class WritingHandle(MockTurnHandle):
        def run(self) -> MockTurnResult:
            (prepared.workspace / "src" / "normalization.py").write_text(
                NORMALIZATION_SOURCE,
                encoding="utf-8",
                newline="\n",
            )
            (prepared.workspace / "src" / "config.py").write_text(
                CONFIG_SOURCE,
                encoding="utf-8",
                newline="\n",
            )
            return super().run()

    class WritingThread(MockThread):
        def turn(self, prompt: str, **kwargs: Any) -> WritingHandle:
            self.turn_calls.append((prompt, kwargs))
            usage = SimpleNamespace(
                total=SimpleNamespace(
                    input_tokens=20,
                    output_tokens=10,
                    total_tokens=30,
                )
            )
            handle = WritingHandle(
                MockTurnResult(
                    status=SimpleNamespace(value="completed"),
                    final_response=json.dumps(
                        {
                            **COMPLETED_RESULT,
                            "artifacts": [
                                {
                                    "path": "src/normalization.py",
                                    "kind": "file",
                                    "description": "mocked live result",
                                },
                                {
                                    "path": "src/config.py",
                                    "kind": "file",
                                    "description": "mocked live result",
                                },
                            ],
                            "changed_paths": [
                                "src/normalization.py",
                                "src/config.py",
                            ],
                        }
                    ),
                    usage=usage,
                )
            )
            self.handles.append(handle)
            return handle

    client = MockClient()

    def start_thread(**kwargs: Any) -> WritingThread:
        client.thread_start_calls.append(kwargs)
        thread = WritingThread("private-live-thread-id")
        client.threads.append(thread)
        return thread

    client.thread_start = start_thread  # type: ignore[method-assign]
    runtime = CodexSdkRuntime(
        prepared.workspace,
        bindings=_bindings(MockCodexContext(client)),
        environ={},
    )
    adapter = SdkBaselineAdapter(
        SdkBaselineConfig(
            variant_id="c0",
            tasks=(task,),
            contract=WorkerContract(
                render_prompt=render_worker_prompt,
                result_schema=result_schema,
                validate_result=lambda value: validate_result(value).model_dump(
                    mode="json"
                ),
                semantics_sha256=task_semantics_sha256,
            ),
            runtime=runtime,
        )
    )

    result = run_sdk_live_cell(
        experiment_dir=experiment_dir,
        plan=plan,
        planned_cell=cell,
        prepared=prepared,
        adapter=adapter,
        benchmark_python=Path(sys.executable),
        git_executable=_git(),
    )

    assert result.cell_state == "SEALED"
    assert result.actual_model_turns == 1
    assert result.check_success is True
    measurement = verify_sealed_cell(experiment_dir / "cells" / cell.cell_id)
    assert measurement.environment.model == PINNED_MODEL
    assert measurement.environment.auth_method == "chatgpt"
    assert measurement.variant_metrics.schema_id == "sdk-controlled-live-pilot/v1"
    assert measurement.variant_metrics.values["actual_model_turns"] == 1
    adapter_result = json.loads(
        (
            experiment_dir
            / "cells"
            / cell.cell_id
            / "raw"
            / "adapter-result.json"
        ).read_text(encoding="utf-8")
    )
    assert adapter_result["raw_payload"]["thread_ids"] == [
        "sha256:"
        + hashlib.sha256(b"private-live-thread-id").hexdigest()
    ]
    preflight = (
        experiment_dir / "cells" / cell.cell_id / "raw" / "preflight.json"
    ).read_text(encoding="utf-8")
    assert "private-live-thread-id" not in preflight
    assert str(prepared.workspace) not in preflight
