"""Fail-closed live controller and freeze boundary for SDK routing S1."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from benchmark_runner.adapter import B1SequentialAdapter, CellContext
from benchmark_runner.contract import (
    ArtifactIdentity,
    CellLifecycleState,
    CellStateRecord,
    ExecutionPlan,
    Measurement,
    MeasurementIdentity,
    PlannedCell,
    present_api_key_environment_names,
    utc_now,
)
from benchmark_runner.plan import assert_plan_integrity
from benchmark_runner.routing_suite import (
    S1_ALLOWED_OUTCOMES,
    S1_EXPECTED_CELL_ORDER,
    S1_PLANNED_LIVE_MODEL_TURNS,
    RoutingSuiteError,
    _aggregate_export_sha256,
    _fixture_specs,
    _resolve_stage,
    build_routing_s1_live_plan,
    build_routing_s2_live_plan,
    build_routing_s2_reverse_live_plan,
)
from benchmark_runner.runner import (
    _r5_assert_export_safe,
    _source_tree_sha256,
    atomic_write,
    canonical_json_bytes,
    verify_sealed_cell,
)
from benchmark_runner.sdk_cells import (
    SdkSealedCellResult,
    initialize_sdk_experiment,
    run_sdk_live_cell,
    runner_source_sha256,
)
from benchmark_runner.sdk_common import (
    PINNED_APPROVAL_MODE,
    PINNED_MODEL,
    PINNED_REASONING_EFFORT,
    PINNED_SANDBOX,
    PINNED_SDK_VERSION,
)
from benchmark_runner.sdk_pilot import (
    B1_FINGERPRINT_INPUTS,
    _adapter,
    _assert_runtime_profile,
    _assert_sdk_version,
    _git_executable,
    _runtime_profile_path,
    _task_envelopes,
    _worker_contract,
)
from benchmark_runner.workspace import FixtureRestorer, load_frozen_manifest, sha256_file
from benchmark_runner.s2_policy import (
    b1_dual_outcome_contract_valid,
    derive_s2_routing_policy,
    remaining_b1_retry_resume_reserve,
    s2_b1_turn_cap,
)
from benchmark_runner.s2_posthoc import checker_sha256, run_posthoc_subprocess


LIVE_TRACK = "sdk_routing_s1_live_calibration"
S2_LIVE_TRACK = "sdk_routing_s2_live_initial"
S2_REVERSE_LIVE_TRACK = "sdk_routing_s2_live_reverse"
STATE_FILENAME = "routing-s1-state.json"
STOP_FILENAME = "stop-record.json"
DISPATCH_MARKER_FILENAME = "live-dispatch-claimed.json"
REQUIRED_REGRESSION_CASES = (
    "s0_gate",
    "b1_retry_contracts",
    "b1_full",
    "runner_full",
    "implementation_log_check",
    "implementation_log_tests",
)
S2_REQUIRED_REGRESSION_CASES = (
    "s0_gate",
    "b1_retry_contracts",
    "b1_full",
    "runner_full",
    "s2_posthoc_property_contracts",
)


def _plan_stage_contract(plan: ExecutionPlan) -> dict[str, Any]:
    stage_id = plan.decision_policy.get("stage_id")
    if stage_id == "s1-baseline":
        return {
            "stage_id": stage_id,
            "label": "S1",
            "track": LIVE_TRACK,
            "route_decision_allowed": False,
            "stage_relative": "benchmarks/suites/sdk-routing-v1/stages/s1-baseline.yaml",
            "planned_cells": 8,
            "base_turns": S1_PLANNED_LIVE_MODEL_TURNS,
            "max_turns": S1_PLANNED_LIVE_MODEL_TURNS,
            "state_root_limit": 120,
        }
    if stage_id == "s2-intermediate":
        if plan.decision_policy.get("execution_phase") == "reverse":
            return {
                "stage_id": stage_id,
                "label": "S2 reverse",
                "track": S2_REVERSE_LIVE_TRACK,
                "route_decision_allowed": True,
                "stage_relative": "benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml",
                "planned_cells": 2,
                "base_turns": 6,
                "max_turns": 9,
                "state_root_limit": 40,
            }
        return {
            "stage_id": stage_id,
            "label": "S2",
            "track": S2_LIVE_TRACK,
            "route_decision_allowed": True,
            "stage_relative": "benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml",
            "planned_cells": 4,
            "base_turns": 12,
            "max_turns": 15,
            "state_root_limit": 40,
        }
    raise RoutingSuiteError("unsupported routing live stage")


def _qualifying_regression(
    value: object,
    source_commit: str,
    *,
    required_cases: tuple[str, ...] = REQUIRED_REGRESSION_CASES,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RoutingSuiteError("S1 live freeze regression record is not an object")
    cases = value.get("cases")
    if (
        value.get("schema_version") != 1
        or value.get("status") != "passed"
        or value.get("source_commit") != source_commit
        or value.get("actual_model_turns") != 0
        or value.get("python_version") != "Python 3.12.10"
        or not isinstance(value.get("completed_at"), str)
        or not isinstance(cases, list)
        or [case.get("name") for case in cases if isinstance(case, dict)]
        != list(required_cases)
        or any(
            not isinstance(case, dict)
            or set(case) != {"name", "exit_code", "elapsed_seconds", "summary_line"}
            or case.get("exit_code") != 0
            or not isinstance(case.get("elapsed_seconds"), (int, float))
            or isinstance(case.get("elapsed_seconds"), bool)
            or case.get("elapsed_seconds", -1) < 0
            or not isinstance(case.get("summary_line"), str)
            or not case.get("summary_line")
            for case in cases
        )
    ):
        raise RoutingSuiteError("S1 live freeze regression record does not qualify")
    return value


def _assert_external_short_state_root(
    repository_root: Path,
    state_root: Path,
    *,
    maximum_length: int = 120,
) -> None:
    if state_root.is_relative_to(repository_root) or len(str(state_root)) > maximum_length:
        raise RoutingSuiteError(
            "routing live state root must be a short path outside the source repository"
        )


def _state_path(state_root: Path) -> Path:
    return state_root.resolve() / STATE_FILENAME


def _load_state(state_root: Path) -> dict[str, Any]:
    try:
        value = json.loads(_state_path(state_root).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RoutingSuiteError("S1 live state metadata is missing or invalid") from exc
    required = {
        "schema_version",
        "repository_root",
        "state_root",
        "artifact_root",
        "experiment_id",
        "source_commit",
        "runtime_profile_sha256",
        "runner_source_sha256",
        "b1_source_sha256",
        "benchmark_python",
        "benchmark_python_sha256",
        "routing_controller_sha256",
        "fixture_manifest_sha256",
        "codex_sdk_runtime_sha256",
        "git_executable",
        "git_version",
        "git_sha256",
        "plan_fingerprint",
        "plan_sha256",
        "freeze_sha256",
    }
    if (
        not isinstance(value, dict)
        or frozenset(value)
        not in {
            frozenset(required),
            frozenset({*required, "stage_id"}),
            frozenset({*required, "stage_id", "initial_export_root"}),
        }
        or value["schema_version"] != 1
    ):
        raise RoutingSuiteError("S1 live state metadata differs from the frozen contract")
    return value


def _load_live_plan(state_root: Path) -> tuple[Path, ExecutionPlan, dict[str, Any]]:
    state = _load_state(state_root)
    repository_root = Path(state["repository_root"]).resolve()
    resolved_state_root = state_root.resolve()
    experiment_dir = resolved_state_root / str(state["experiment_id"])
    try:
        plan_bytes = (experiment_dir / "execution-plan.json").read_bytes()
        plan = ExecutionPlan.model_validate_json(plan_bytes)
        assert_plan_integrity(plan)
        contract = _plan_stage_contract(plan)
    except (OSError, ValueError) as exc:
        raise RoutingSuiteError("S1 live Execution Plan is missing or invalid") from exc
    _assert_external_short_state_root(
        repository_root,
        resolved_state_root,
        maximum_length=contract["state_root_limit"],
    )
    if resolved_state_root != Path(state["state_root"]).resolve():
        raise RoutingSuiteError("routing live state root moved after freeze")
    tracks = [item.value for item in plan.plan_supplemented if item.field == "track"]
    turn_guards = [
        item.value for item in plan.plan_supplemented if item.field == "actual_model_turns"
    ]
    if (
        plan.experiment_id != state["experiment_id"]
        or tracks != [contract["track"]]
        or turn_guards
        or plan.decision_policy.get("route_decision_allowed")
        is not contract["route_decision_allowed"]
        or plan.source_manifest.path
        != contract["stage_relative"]
        or state.get("stage_id", contract["stage_id"]) != contract["stage_id"]
        or plan.plan_fingerprint != state["plan_fingerprint"]
        or hashlib.sha256(plan_bytes).hexdigest() != state["plan_sha256"]
        or plan.environment_fingerprint.get("source_commit") != state["source_commit"]
        or plan.environment_fingerprint.get("runtime_profile_sha256")
        != state["runtime_profile_sha256"]
        or plan.environment_fingerprint.get("benchmark_python_path_sha256")
        != _path_sha256(Path(state["benchmark_python"]))
        or plan.environment_fingerprint.get("benchmark_python_sha256")
        != state["benchmark_python_sha256"]
        or plan.environment_fingerprint.get("routing_controller_sha256")
        != state["routing_controller_sha256"]
        or plan.environment_fingerprint.get("fixture_manifest_fingerprint")
        != json.dumps(
            state["fixture_manifest_sha256"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        or plan.environment_fingerprint.get("codex_sdk_runtime_sha256")
        != state["codex_sdk_runtime_sha256"]
        or plan.environment_fingerprint.get("git_version") != state["git_version"]
        or plan.environment_fingerprint.get("git_sha256") != state["git_sha256"]
        or plan.environment_fingerprint.get("git_executable_path_sha256")
        != _path_sha256(Path(state["git_executable"]))
        or (
            plan.decision_policy.get("execution_phase") == "reverse"
            and (
                not isinstance(state.get("initial_export_root"), str)
                or not state["initial_export_root"]
                or not isinstance(
                    plan.decision_policy.get("initial_export_identity"), dict
                )
            )
        )
    ):
        raise RoutingSuiteError("S1 live Plan differs from the frozen execution track")
    return experiment_dir, plan, state


def _copied_manifest_path(relative: str) -> str:
    return f"manifests/source/{relative}"


def _artifact_files_without_seal(artifact_root: Path) -> dict[str, bytes]:
    files = {
        name: (artifact_root / name).read_bytes()
        for name in (
            "execution-plan.json",
            "build-record.json",
            "preflight.json",
            "regression.json",
        )
        if (artifact_root / name).is_file()
    }
    manifest_root = artifact_root / "manifests" / "source"
    if manifest_root.is_dir():
        files.update(
            {
                path.relative_to(artifact_root).as_posix(): path.read_bytes()
                for path in manifest_root.rglob("*")
                if path.is_file()
            }
        )
    return files


def _routing_controller_sha256(repository_root: Path) -> str:
    digest = hashlib.sha256()
    for name in ("run_sdk_routing_s1.py", "probe_sdk_routing_s1_plan.py"):
        path = repository_root / "tools" / "benchmark-runner" / "scripts" / name
        data = path.read_bytes()
        encoded = name.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def _path_sha256(path: Path) -> str:
    return hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()


def _s2_path_length_preflight(
    *,
    repository_root: Path,
    state_root: Path,
    plan: ExecutionPlan,
    git_executable: Path,
) -> dict[str, Any]:
    """Create and remove each S2 Cell's longest representative paths."""

    preflight_root = state_root / "_path-preflight"
    records: list[dict[str, object]] = []
    try:
        for cell in plan.cells:
            fixture = next(
                item for item in plan.fixtures if item.fixture_id == cell.fixture_id
            )
            fixture_path = next(
                item.path
                for item in _fixture_specs(
                    repository_root,
                    _resolve_stage(
                        repository_root,
                        repository_root / "benchmarks/suites/sdk-routing-v1/suite.yaml",
                        repository_root
                        / "benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml",
                    )[1],
                )
                if item.id == fixture.fixture_id
            )
            prefix = fixture_path.rstrip("/") + "/"
            names = _git_at(
                git_executable,
                repository_root,
                "ls-tree",
                "-r",
                "--name-only",
                fixture.source_commit,
                "--",
                fixture_path,
            ).splitlines()
            relative_files = [
                Path(name[len(prefix) :]) for name in names if name.startswith(prefix)
            ]
            if not relative_files:
                raise RoutingSuiteError("S2 fixture tree has no files for path preflight")
            longest = max(relative_files, key=lambda item: len(str(item)))
            workspace_probe = preflight_root / cell.cell_id / "workspace" / longest
            git_probe = (
                preflight_root
                / cell.cell_id
                / "workspace"
                / ".git"
                / "objects"
                / "aa"
                / ("b" * 40)
            )
            for path in (workspace_probe, git_probe):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"s2-path-preflight")
                path.unlink()
            records.append(
                {
                    "cell_id": cell.cell_id,
                    "longest_fixture_path": longest.as_posix(),
                    "maximum_created_path_length": max(
                        len(str(workspace_probe.resolve())),
                        len(str(git_probe.resolve())),
                    ),
                }
            )
    except OSError as exc:
        raise RoutingSuiteError("S2 live path-length preflight failed") from exc
    finally:
        if preflight_root.exists():
            shutil.rmtree(preflight_root)
    return {
        "state_root_length": len(str(state_root.resolve())),
        "cells": records,
        "actual_model_turns": 0,
    }


def _git_identity() -> tuple[Path, str, str]:
    executable = _git_executable().resolve()
    result = subprocess.run(
        [str(executable), "--version"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )
    version = result.stdout.strip()
    if result.returncode != 0 or version != "git version 2.54.0.windows.1":
        raise RoutingSuiteError("S1 live freeze requires Git 2.54.0.windows.1")
    return executable, version, sha256_file(executable)


def _git_at(executable: Path, repository_root: Path, *arguments: str) -> str:
    result = subprocess.run(
        [str(executable), *arguments],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )
    if result.returncode != 0:
        raise RoutingSuiteError(f"pinned Git command failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _independent_live_plan_build(
    *,
    repository_root: Path,
    source_commit: str,
    benchmark_python: Path,
    git_executable: Path,
    expected_plan: ExecutionPlan,
) -> ExecutionPlan:
    temporary_parent = Path("C:/tmp") if Path("C:/tmp").is_dir() else None
    with tempfile.TemporaryDirectory(
        prefix="lao-s1-plan-", dir=str(temporary_parent) if temporary_parent else None
    ) as temporary_name:
        temporary = Path(temporary_name)
        clone = temporary / "source"

        def run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None):
            result = subprocess.run(
                command,
                cwd=cwd,
                env=env,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,
                shell=False,
            )
            if result.returncode != 0:
                detail = result.stderr.decode("utf-8", errors="replace")
                raise RoutingSuiteError(f"independent S1 Plan build failed: {detail}")
            return result.stdout

        run(
            [
                str(git_executable),
                "clone",
                "--no-hardlinks",
                "--no-checkout",
                str(repository_root),
                str(clone),
            ],
            cwd=temporary,
        )
        run(
            [str(git_executable), "config", "core.autocrlf", "false"],
            cwd=clone,
        )
        run(
            [str(git_executable), "checkout", "--detach", source_commit],
            cwd=clone,
        )
        if run([str(git_executable), "status", "--porcelain"], cwd=clone).strip():
            raise RoutingSuiteError("independent S1 Plan checkout is not clean")
        input_path = temporary / "plan-input.json"
        atomic_write(
            input_path,
            canonical_json_bytes(
                {
                    "runner": expected_plan.runner.model_dump(mode="json"),
                    "variants": [
                        item.model_dump(mode="json") for item in expected_plan.variants
                    ],
                    "environment_fingerprint": expected_plan.environment_fingerprint,
                    "created_at": expected_plan.created_at.isoformat(),
                    "revision": expected_plan.revision,
                    "decision_policy": expected_plan.decision_policy,
                }
            ),
        )
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(
            clone / "tools" / "benchmark-runner" / "src"
        )
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONUTF8"] = "1"
        environment["PYTHONIOENCODING"] = "utf-8"
        output = run(
            [
                str(benchmark_python),
                "-P",
                str(
                    clone
                    / "tools"
                    / "benchmark-runner"
                    / "scripts"
                    / "probe_sdk_routing_s1_plan.py"
                ),
                "--repository",
                str(clone),
                "--input",
                str(input_path),
                "--stage",
                str(expected_plan.decision_policy["stage_id"]),
            ],
            cwd=clone,
            env=environment,
        )
        try:
            rebuilt = ExecutionPlan.model_validate_json(output)
            assert_plan_integrity(rebuilt)
        except ValueError as exc:
            raise RoutingSuiteError("independent S1 Plan output is invalid") from exc
        return rebuilt


def _first_task_semantics(workspace: Path) -> tuple[list[str], list[str]]:
    contract = _worker_contract()
    c2 = [contract.semantics_sha256(task) for task in _task_envelopes("c2", workspace)]
    b1 = [contract.semantics_sha256(task) for task in _task_envelopes("b1", workspace)]
    if c2 != b1 or not c2:
        raise RoutingSuiteError("C2/B1 Task semantics parity failed")
    return c2, b1


def _assert_b1_module_origin(repository_root: Path, benchmark_python: Path) -> str:
    source_root = (repository_root / "stages" / "b1-sequential" / "src").resolve()
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(source_root)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [
            str(benchmark_python.resolve()),
            "-P",
            "-c",
            "import orchestrator; print(orchestrator.__file__)",
        ],
        cwd=source_root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )
    expected = (source_root / "orchestrator" / "__init__.py").resolve()
    try:
        actual = Path(result.stdout.strip()).resolve()
    except (OSError, ValueError) as exc:
        raise RoutingSuiteError("S1 live B1 module-origin probe was invalid") from exc
    if result.returncode != 0 or actual != expected:
        raise RoutingSuiteError("S1 live B1 module did not resolve to the frozen source tree")
    return expected.relative_to(repository_root).as_posix()


def _codex_sdk_runtime_identity() -> tuple[str, str]:
    module = importlib.import_module("openai_codex")
    cli_module = importlib.import_module("codex_cli_bin")
    module_file = Path(str(module.__file__)).resolve()
    cli_module_file = Path(str(cli_module.__file__)).resolve()
    prefix = Path(sys.prefix).resolve()
    site_packages = (prefix / "Lib" / "site-packages").resolve()
    package_root = module_file.parent
    if (
        package_root.name != "openai_codex"
        or not module_file.is_relative_to(site_packages)
        or module_file.is_symlink()
        or cli_module_file.parent.name != "codex_cli_bin"
        or not cli_module_file.is_relative_to(site_packages)
        or cli_module_file.is_symlink()
    ):
        raise RoutingSuiteError("S1 live Codex SDK module origin is not trusted")
    digest = hashlib.sha256()
    roots = (package_root, cli_module_file.parent)
    files = sorted(
        (
            (root.name, path, path.relative_to(root).as_posix())
            for root in roots
            for path in root.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix != ".pyc"
        ),
        key=lambda item: (item[0], item[2]),
    )
    if not files:
        raise RoutingSuiteError("S1 live Codex SDK package has no source files")
    for root_name, path, package_relative in files:
        if path.is_symlink():
            raise RoutingSuiteError("S1 live Codex SDK package contains a symlink")
        relative = f"{root_name}/{package_relative}".encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(path.stat().st_size.to_bytes(8, "big"))
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return module_file.relative_to(prefix).as_posix(), digest.hexdigest()


def _preflight_adapter(
    *,
    repository_root: Path,
    experiment_dir: Path,
    cell: PlannedCell,
    workspace: Path,
    benchmark_python: Path,
    b1_timeout_seconds: float = 2_000,
) -> dict[str, object]:
    adapter = _adapter(
        repository_root=repository_root,
        experiment_dir=experiment_dir,
        cell=cell,
        workspace=workspace,
        benchmark_python=benchmark_python,
        b1_timeout_seconds=b1_timeout_seconds,
    )
    result = adapter.preflight(CellContext(experiment_dir.name, cell.cell_id))
    runtime = getattr(getattr(adapter, "config", None), "runtime", None)
    evidence = getattr(runtime, "preflight_evidence", None)
    if evidence is None:
        evidence = getattr(adapter, "preflight_evidence", None)
    close = getattr(runtime, "close", None)
    if callable(close):
        close()
    if not result.ok or not evidence:
        raise RoutingSuiteError(f"S1 live preflight failed for {cell.cell_id}: {result.detail}")
    if (
        evidence.get("account_type") != "chatgpt"
        or evidence.get("sdk_version") != PINNED_SDK_VERSION
        or evidence.get("actual_model_turns") != 0
        or evidence.get("api_key_environment_names_present") != []
    ):
        raise RoutingSuiteError(f"S1 live preflight controls differ for {cell.cell_id}")
    return {
        "cell_id": cell.cell_id,
        "fixture_id": cell.fixture_id,
        "variant_id": cell.variant_id,
        "ok": True,
        "account_type": "chatgpt",
        "sdk_version": PINNED_SDK_VERSION,
        "api_key_environment_names_present": [],
        "actual_model_turns": 0,
    }


def create_routing_s1_live_candidate(
    *,
    repository_root: Path,
    suite_path: Path,
    stage_path: Path,
    state_root: Path,
    artifact_root: Path,
    regression_record_path: Path,
    benchmark_python: Path,
    revision: int = 1,
    created_at: datetime | None = None,
    initial_export_root: Path | None = None,
    expansion_profile: str | None = None,
) -> dict[str, Any]:
    """Create and independently seal the zero-turn S1 live execution candidate."""

    repository_root = repository_root.resolve()
    suite_path = suite_path.resolve()
    stage_path = stage_path.resolve()
    state_root = state_root.resolve()
    artifact_root = artifact_root.resolve()
    regression_record_path = regression_record_path.resolve()
    benchmark_python = benchmark_python.resolve()
    if benchmark_python != Path(sys.executable).resolve():
        raise RoutingSuiteError("S1 live benchmark Python must be the controller interpreter")
    suite, stage = _resolve_stage(repository_root, suite_path, stage_path)
    is_s2 = stage.stage_id == "s2-intermediate"
    is_reverse = initial_export_root is not None or expansion_profile is not None
    if is_reverse and (
        not is_s2 or initial_export_root is None or expansion_profile is None
    ):
        raise RoutingSuiteError(
            "S2 reverse freeze requires both initial export and expansion profile"
        )
    _assert_external_short_state_root(
        repository_root,
        state_root,
        maximum_length=40 if is_s2 else 120,
    )
    if platform.python_version() != "3.12.10":
        raise RoutingSuiteError("S1 live freeze requires Python 3.12.10")
    git_executable, git_version, git_sha256 = _git_identity()
    if present_api_key_environment_names():
        raise RoutingSuiteError("API key environment is present; S1 live freeze fails closed")
    if _git_at(git_executable, repository_root, "status", "--porcelain"):
        raise RoutingSuiteError("S1 live freeze requires a clean Git worktree")
    source_commit = _git_at(git_executable, repository_root, "rev-parse", "HEAD")
    if suite.status != "frozen_before_execution" or stage.status != "frozen_before_execution":
        raise RoutingSuiteError("S1 live freeze requires frozen suite and stage manifests")
    _assert_sdk_version()
    codex_sdk_module_origin, codex_sdk_runtime_sha256 = _codex_sdk_runtime_identity()
    runtime_profile = _runtime_profile_path()
    runtime_profile_sha256 = _assert_runtime_profile(runtime_profile)
    runner_sha256 = runner_source_sha256()
    benchmark_python_sha256 = sha256_file(benchmark_python)
    routing_controller_sha256 = _routing_controller_sha256(repository_root)
    b1_root = repository_root / "stages" / "b1-sequential"
    b1_sha256 = _source_tree_sha256(b1_root, B1_FINGERPRINT_INPUTS)
    b1_module_origin = _assert_b1_module_origin(repository_root, benchmark_python)
    fixture_manifest_sha256: dict[str, str] = {}
    for selection in stage.fixture_manifests:
        manifest_path = repository_root / selection.path
        if load_frozen_manifest(manifest_path).status != "frozen_before_execution":
            raise RoutingSuiteError("S1 live fixture manifest is not frozen")
        fixture_manifest_sha256[selection.path] = sha256_file(manifest_path)
    fixture_manifest_fingerprint = json.dumps(
        fixture_manifest_sha256, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    version = f"0.1.0@{source_commit}"
    environment = {
        "python": platform.python_version(),
        "sdk": f"openai-codex=={PINNED_SDK_VERSION}",
        "model": PINNED_MODEL,
        "reasoning_effort": PINNED_REASONING_EFFORT,
        "approval_mode": PINNED_APPROVAL_MODE,
        "sandbox": PINNED_SANDBOX,
        "auth_method": "chatgpt",
        "runtime_profile_sha256": runtime_profile_sha256,
        "source_commit": source_commit,
        "benchmark_python_path_sha256": _path_sha256(benchmark_python),
        "benchmark_python_sha256": benchmark_python_sha256,
        "routing_controller_sha256": routing_controller_sha256,
        "fixture_manifest_fingerprint": fixture_manifest_fingerprint,
        "codex_sdk_runtime_sha256": codex_sdk_runtime_sha256,
        "git_version": git_version,
        "git_sha256": git_sha256,
        "git_executable_path_sha256": _path_sha256(git_executable),
    }
    runner = ArtifactIdentity(
        artifact_id="benchmark-runner", version=version, sha256=runner_sha256
    )
    variants = [
        ArtifactIdentity(artifact_id="c2", version=version, sha256=runner_sha256),
        ArtifactIdentity(artifact_id="b1", version=version, sha256=b1_sha256),
    ]
    created = created_at or utc_now()
    common = dict(
        repository_root=repository_root,
        suite_path=suite_path,
        stage_path=stage_path,
        runner=runner,
        variants=variants,
        environment_fingerprint=environment,
        created_at=created,
        revision=revision,
    )
    initial_export_identity: dict[str, str] | None = None
    if is_reverse:
        assert initial_export_root is not None and expansion_profile is not None
        initial_export_root = initial_export_root.resolve()
        if not initial_export_root.is_relative_to(repository_root):
            raise RoutingSuiteError("S2 reverse initial export must be inside the repository")
        initial_relative = initial_export_root.relative_to(repository_root).as_posix()
        _git_at(git_executable, repository_root, "ls-files", "--error-unmatch", initial_relative)
        verified_initial = verify_routing_s2_live_export(initial_export_root)
        initial_plan = ExecutionPlan.model_validate_json(
            (initial_export_root / "execution-plan.json").read_bytes()
        )
        initial_summary = json.loads(
            (initial_export_root / "summary.json").read_text(encoding="utf-8")
        )
        if (
            initial_summary.get("stage_state") != "S2_EXPANSION_REQUIRED"
            or verified_initial.get("stage_state") != "S2_EXPANSION_REQUIRED"
        ):
            raise RoutingSuiteError("S2 reverse requires an expansion-required initial export")
        initial_export_identity = {
            "experiment_id": initial_plan.experiment_id,
            "plan_fingerprint": initial_plan.plan_fingerprint,
            "export_sha256": str(verified_initial["export_sha256"]),
            "stage_state": "S2_EXPANSION_REQUIRED",
            "source_commit": str(
                initial_plan.environment_fingerprint.get("source_commit", "")
            ),
        }
        plan = build_routing_s2_reverse_live_plan(
            **common,
            expansion_profile=expansion_profile,
            initial_export_identity=initial_export_identity,
        )
    else:
        builder = build_routing_s2_live_plan if is_s2 else build_routing_s1_live_plan
        plan = builder(**common)
    independent = _independent_live_plan_build(
        repository_root=repository_root,
        source_commit=source_commit,
        benchmark_python=benchmark_python,
        git_executable=git_executable,
        expected_plan=plan,
    )
    if independent != plan:
        raise RoutingSuiteError("independent S1 live Plan build disagreed")
    try:
        regression = json.loads(regression_record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RoutingSuiteError("S1 live freeze regression record is missing or invalid") from exc
    regression = _qualifying_regression(
        regression,
        source_commit,
        required_cases=(
            S2_REQUIRED_REGRESSION_CASES if is_s2 else REQUIRED_REGRESSION_CASES
        ),
    )
    if state_root.exists() or artifact_root.exists():
        raise RoutingSuiteError("S1 live freeze state or artifact root already exists")
    state_root.mkdir(parents=True)
    path_preflight = (
        _s2_path_length_preflight(
            repository_root=repository_root,
            state_root=state_root,
            plan=plan,
            git_executable=git_executable,
        )
        if is_s2
        else None
    )
    experiment_dir = initialize_sdk_experiment(state_root, plan)
    artifact_root.mkdir(parents=True)
    atomic_write(artifact_root / "execution-plan.json", canonical_json_bytes(plan))
    manifest_files = {
        suite_path.relative_to(repository_root).as_posix(): suite_path,
        stage_path.relative_to(repository_root).as_posix(): stage_path,
    }
    for selection in stage.fixture_manifests:
        manifest_files[selection.path] = repository_root / selection.path
    for relative, path in manifest_files.items():
        atomic_write(artifact_root / _copied_manifest_path(relative), path.read_bytes())
    build_record = {
        "schema_version": 1,
        "kind": f"sdk_routing_{'s2' if is_s2 else 's1'}_live_source_freeze",
        "source_commit": source_commit,
        "suite_sha256": sha256_file(suite_path),
        "stage_sha256": sha256_file(stage_path),
        "runner_source_sha256": runner_sha256,
        "b1_source_sha256": b1_sha256,
        "b1_module_origin": b1_module_origin,
        "b1_schema_root": "stages/b1-sequential/schemas/v1",
        "command_prefix_contract": [
            "<sha256-bound-benchmark-python>",
            "-P",
            "-m",
            "orchestrator",
        ],
        "benchmark_python_path_sha256": _path_sha256(benchmark_python),
        "benchmark_python_sha256": benchmark_python_sha256,
        "routing_controller_sha256": routing_controller_sha256,
        "fixture_manifest_sha256": fixture_manifest_sha256,
        "fixture_manifest_fingerprint": fixture_manifest_fingerprint,
        "b1_turn_cap_contract": (
            "task_count_3_plus_min(project_policy_8,remaining_b1_reserve_3)"
            if is_s2
            else "min(project_policy_8,remaining_global_12)"
        ),
        "codex_sdk_module_origin": codex_sdk_module_origin,
        "codex_sdk_runtime_sha256": codex_sdk_runtime_sha256,
        "git_executable_path_sha256": _path_sha256(git_executable),
        "git_version": git_version,
        "git_sha256": git_sha256,
        "runtime_profile_sha256": runtime_profile_sha256,
        "independent_plan_build": {
            "separate_clean_checkout": True,
            "separate_process": True,
            "source_commit": source_commit,
            "plan_fingerprint": independent.plan_fingerprint,
            "identical": independent == plan,
        },
        "actual_model_turns": 0,
        "path_length_preflight": path_preflight,
        "posthoc_checks": (
            plan.decision_policy.get("posthoc_checks") if is_s2 else None
        ),
        "initial_export_identity": initial_export_identity,
    }
    atomic_write(artifact_root / "build-record.json", canonical_json_bytes(build_record))
    restorer = FixtureRestorer(repository_root, str(git_executable))
    fixtures = {fixture.id: fixture for fixture in _fixture_specs(repository_root, stage)}
    preflights: list[dict[str, object]] = []
    semantics: dict[str, dict[str, list[str]]] = {}
    for cell in sorted(plan.cells, key=lambda item: item.execution_ordinal):
        prepared = restorer.restore(
            fixtures[cell.fixture_id],
            experiment_dir / "cells" / cell.cell_id / "workspace",
        )
        if cell.fixture_id not in semantics:
            c2_hashes, b1_hashes = _first_task_semantics(prepared.workspace)
            semantics[cell.fixture_id] = {"c2": c2_hashes, "b1": b1_hashes}
        preflights.append(
            _preflight_adapter(
                repository_root=repository_root,
                experiment_dir=experiment_dir,
                cell=cell,
                workspace=prepared.workspace,
                benchmark_python=benchmark_python,
                b1_timeout_seconds=3_300 if is_s2 else 2_000,
            )
        )
    preflight = {
        "schema_version": 1,
        "kind": f"sdk_routing_{'s2' if is_s2 else 's1'}_live_preflight",
        "experiment_id": plan.experiment_id,
        "plan_fingerprint": plan.plan_fingerprint,
        "api_key_environment_names_present": [],
        "actual_model_turns": 0,
        "task_semantics": semantics,
        "cells": preflights,
    }
    atomic_write(artifact_root / "preflight.json", canonical_json_bytes(preflight))
    atomic_write(artifact_root / "regression.json", canonical_json_bytes(regression))
    state = {
        "schema_version": 1,
        "stage_id": stage.stage_id,
        "repository_root": str(repository_root),
        "state_root": str(state_root),
        "artifact_root": str(artifact_root),
        "experiment_id": plan.experiment_id,
        "source_commit": source_commit,
        "runtime_profile_sha256": runtime_profile_sha256,
        "runner_source_sha256": runner_sha256,
        "b1_source_sha256": b1_sha256,
        "benchmark_python": str(benchmark_python),
        "benchmark_python_sha256": benchmark_python_sha256,
        "routing_controller_sha256": routing_controller_sha256,
        "fixture_manifest_sha256": fixture_manifest_sha256,
        "codex_sdk_runtime_sha256": codex_sdk_runtime_sha256,
        "git_executable": str(git_executable),
        "git_version": git_version,
        "git_sha256": git_sha256,
        "plan_fingerprint": plan.plan_fingerprint,
        "plan_sha256": hashlib.sha256(canonical_json_bytes(plan)).hexdigest(),
        "freeze_sha256": "",
    }
    if is_reverse:
        assert initial_export_root is not None
        state["initial_export_root"] = str(initial_export_root)
    atomic_write(_state_path(state_root), canonical_json_bytes(state))
    files = _artifact_files_without_seal(artifact_root)
    freeze_record = {
        "schema_version": 1,
        "kind": f"sdk_routing_{'s2' if is_s2 else 's1'}_live_freeze_seal",
        "status": "frozen_before_first_cell",
        "experiment_id": plan.experiment_id,
        "plan_fingerprint": plan.plan_fingerprint,
        "planned_cells": len(plan.cells),
        "planned_live_model_turns": (
            plan.decision_policy.get("max_actual_live_model_turns")
            if is_s2
            else S1_PLANNED_LIVE_MODEL_TURNS
        ),
        "actual_model_turns": 0,
        "file_count": len(files),
        "freeze_sha256": _aggregate_export_sha256(files),
    }
    atomic_write(artifact_root / "freeze-seal.json", canonical_json_bytes(freeze_record))
    verified = verify_routing_s1_live_freeze(artifact_root)
    state["freeze_sha256"] = verified["freeze_sha256"]
    atomic_write(_state_path(state_root), canonical_json_bytes(state))
    return {
        "experiment_id": plan.experiment_id,
        "state_root": str(state_root),
        "artifact_root": str(artifact_root),
        "planned_cells": len(plan.cells),
        "planned_live_model_turns": (
            plan.decision_policy.get("max_actual_live_model_turns")
            if is_s2
            else S1_PLANNED_LIVE_MODEL_TURNS
        ),
        "preflight_cells": len(preflights),
        "actual_model_turns": 0,
        "freeze_sha256": verified["freeze_sha256"],
    }


def verify_routing_s1_live_freeze(
    artifact_root: Path, *, require_exact_files: bool = True
) -> dict[str, Any]:
    """Verify the committed pre-execution artifact without trusting its source workspace."""

    artifact_root = artifact_root.resolve()
    if not artifact_root.is_dir() or artifact_root.is_symlink() or any(
        path.is_symlink() for path in artifact_root.rglob("*")
    ):
        raise RoutingSuiteError("S1 live freeze contains an unsafe path")
    try:
        plan_bytes = (artifact_root / "execution-plan.json").read_bytes()
        plan = ExecutionPlan.model_validate_json(plan_bytes)
        assert_plan_integrity(plan)
        contract = _plan_stage_contract(plan)
        build = json.loads((artifact_root / "build-record.json").read_text(encoding="utf-8"))
        preflight = json.loads((artifact_root / "preflight.json").read_text(encoding="utf-8"))
        regression = json.loads((artifact_root / "regression.json").read_text(encoding="utf-8"))
        seal = json.loads((artifact_root / "freeze-seal.json").read_text(encoding="utf-8"))
        suite_bytes = (
            artifact_root
            / _copied_manifest_path("benchmarks/suites/sdk-routing-v1/suite.yaml")
        ).read_bytes()
        stage_bytes = (
            artifact_root
            / _copied_manifest_path(contract["stage_relative"])
        ).read_bytes()
        from benchmark_runner.routing_suite import RoutingStageManifest, RoutingSuiteManifest

        suite = RoutingSuiteManifest.model_validate(yaml.safe_load(suite_bytes))
        stage = RoutingStageManifest.model_validate(yaml.safe_load(stage_bytes))
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        raise RoutingSuiteError("S1 live freeze metadata is missing or invalid") from exc
    tracks = [item.value for item in plan.plan_supplemented if item.field == "track"]
    is_reverse = plan.decision_policy.get("execution_phase") == "reverse"
    reverse_profile = plan.decision_policy.get("expansion_profile")
    expected_reverse_order = list(
        reversed(
            [
                item.variant_id
                for item in stage.cells
                if item.fixture_id == reverse_profile
            ]
        )
    )
    if (
        tracks != [contract["track"]]
        or [item for item in plan.plan_supplemented if item.field == "actual_model_turns"]
        or suite.status != "frozen_before_execution"
        or stage.status != "frozen_before_execution"
        or plan.source_manifest.sha256 != hashlib.sha256(stage_bytes).hexdigest()
        or plan.decision_policy.get("suite_sha256") != hashlib.sha256(suite_bytes).hexdigest()
        or plan.decision_policy.get("route_decision_allowed")
        is not contract["route_decision_allowed"]
        or plan.source_manifest.path
        != contract["stage_relative"]
        or plan.environment_fingerprint.get("sdk")
        != f"openai-codex=={PINNED_SDK_VERSION}"
        or plan.environment_fingerprint.get("python") != "3.12.10"
        or plan.environment_fingerprint.get("model") != PINNED_MODEL
        or plan.environment_fingerprint.get("reasoning_effort")
        != PINNED_REASONING_EFFORT
        or plan.environment_fingerprint.get("approval_mode") != PINNED_APPROVAL_MODE
        or plan.environment_fingerprint.get("sandbox") != PINNED_SANDBOX
        or plan.environment_fingerprint.get("auth_method") != "chatgpt"
        or plan.environment_fingerprint.get("source_commit") != build.get("source_commit")
        or plan.environment_fingerprint.get("runtime_profile_sha256")
        != build.get("runtime_profile_sha256")
        or plan.environment_fingerprint.get("benchmark_python_sha256")
        != build.get("benchmark_python_sha256")
        or plan.environment_fingerprint.get("benchmark_python_path_sha256")
        != build.get("benchmark_python_path_sha256")
        or plan.environment_fingerprint.get("routing_controller_sha256")
        != build.get("routing_controller_sha256")
        or plan.environment_fingerprint.get("fixture_manifest_fingerprint")
        != build.get("fixture_manifest_fingerprint")
        or plan.environment_fingerprint.get("codex_sdk_runtime_sha256")
        != build.get("codex_sdk_runtime_sha256")
        or plan.environment_fingerprint.get("git_version") != build.get("git_version")
        or plan.environment_fingerprint.get("git_sha256") != build.get("git_sha256")
        or plan.environment_fingerprint.get("git_executable_path_sha256")
        != build.get("git_executable_path_sha256")
        or (
            [(cell.fixture_id, cell.variant_id) for cell in plan.cells]
            != S1_EXPECTED_CELL_ORDER
            if contract["stage_id"] == "s1-baseline"
            else (
                [(cell.fixture_id, cell.variant_id) for cell in plan.cells]
                != [(reverse_profile, variant) for variant in expected_reverse_order]
                if is_reverse
                else [cell.cell_id for cell in plan.cells]
                != [item.cell_id for item in stage.cells]
            )
        )
    ):
        raise RoutingSuiteError("S1 live freeze Plan and manifests differ")
    runner = next((item for item in plan.variants if item.artifact_id == "c2"), None)
    b1 = next((item for item in plan.variants if item.artifact_id == "b1"), None)
    path_preflight = build.get("path_length_preflight")
    if (
        build.get("source_commit") != regression.get("source_commit")
        or build.get("suite_sha256") != hashlib.sha256(suite_bytes).hexdigest()
        or build.get("stage_sha256") != hashlib.sha256(stage_bytes).hexdigest()
        or build.get("runner_source_sha256") != plan.runner.sha256
        or runner is None
        or runner.sha256 != plan.runner.sha256
        or b1 is None
        or build.get("b1_source_sha256") != b1.sha256
        or build.get("b1_module_origin")
        != "stages/b1-sequential/src/orchestrator/__init__.py"
        or build.get("independent_plan_build")
        != {
            "separate_clean_checkout": True,
            "separate_process": True,
            "source_commit": build.get("source_commit"),
            "plan_fingerprint": plan.plan_fingerprint,
            "identical": True,
        }
        or build.get("command_prefix_contract")
        != ["<sha256-bound-benchmark-python>", "-P", "-m", "orchestrator"]
        or not isinstance(build.get("benchmark_python_sha256"), str)
        or len(build.get("benchmark_python_sha256")) != 64
        or not isinstance(build.get("benchmark_python_path_sha256"), str)
        or len(build.get("benchmark_python_path_sha256")) != 64
        or not isinstance(build.get("routing_controller_sha256"), str)
        or len(build.get("routing_controller_sha256")) != 64
        or build.get("codex_sdk_module_origin")
        != "Lib/site-packages/openai_codex/__init__.py"
        or not isinstance(build.get("codex_sdk_runtime_sha256"), str)
        or len(build.get("codex_sdk_runtime_sha256")) != 64
        or not isinstance(build.get("git_executable_path_sha256"), str)
        or len(build.get("git_executable_path_sha256")) != 64
        or build.get("git_version") != "git version 2.54.0.windows.1"
        or not isinstance(build.get("git_sha256"), str)
        or len(build.get("git_sha256")) != 64
        or build.get("b1_turn_cap_contract")
        != (
            "task_count_3_plus_min(project_policy_8,remaining_b1_reserve_3)"
            if contract["stage_id"] == "s2-intermediate"
            else "min(project_policy_8,remaining_global_12)"
        )
        or build.get("b1_schema_root") != "stages/b1-sequential/schemas/v1"
        or build.get("actual_model_turns") != 0
        or (
            contract["stage_id"] == "s2-intermediate"
            and build.get("posthoc_checks")
            != plan.decision_policy.get("posthoc_checks")
        )
        or (
            is_reverse
            and build.get("initial_export_identity")
            != plan.decision_policy.get("initial_export_identity")
        )
        or (
            not is_reverse
            and build.get("initial_export_identity") is not None
        )
        or (
            contract["stage_id"] == "s2-intermediate"
            and (
                not isinstance(path_preflight, dict)
                or path_preflight.get("actual_model_turns") != 0
                or not isinstance(path_preflight.get("state_root_length"), int)
                or path_preflight.get("state_root_length") > 40
                or [
                    item.get("cell_id")
                    for item in path_preflight.get("cells", [])
                    if isinstance(item, dict)
                ]
                != [cell.cell_id for cell in plan.cells]
            )
        )
    ):
        raise RoutingSuiteError("S1 live freeze build or regression evidence differs")
    _qualifying_regression(
        regression,
        str(build["source_commit"]),
        required_cases=(
            S2_REQUIRED_REGRESSION_CASES
            if contract["stage_id"] == "s2-intermediate"
            else REQUIRED_REGRESSION_CASES
        ),
    )
    frozen_fixtures = {}
    artifact_fixture_manifest_sha256: dict[str, str] = {}
    for selection in stage.fixture_manifests:
        manifest_path = artifact_root / _copied_manifest_path(selection.path)
        artifact_fixture_manifest_sha256[selection.path] = sha256_file(manifest_path)
        manifest = load_frozen_manifest(manifest_path)
        if manifest.status != "frozen_before_execution":
            raise RoutingSuiteError("S1 live freeze fixture manifest is not frozen")
        if manifest.model != {
            "allowed": PINNED_MODEL,
            "auth_method": "chatgpt",
        }:
            raise RoutingSuiteError("S1 live freeze fixture model controls differ")
        by_id = {fixture.id: fixture for fixture in manifest.fixtures}
        for fixture_id in selection.fixture_ids:
            try:
                frozen_fixtures[fixture_id] = by_id[fixture_id]
            except KeyError as exc:
                raise RoutingSuiteError("S1 live freeze fixture manifest differs") from exc
    if artifact_fixture_manifest_sha256 != build.get("fixture_manifest_sha256"):
        raise RoutingSuiteError("S1 live freeze fixture manifest hashes differ")
    if set(frozen_fixtures) != {item.fixture_id for item in plan.fixtures} or any(
        frozen_fixtures[item.fixture_id].commit != item.source_commit
        or frozen_fixtures[item.fixture_id].git_tree != item.git_tree
        for item in plan.fixtures
    ):
        raise RoutingSuiteError("S1 live freeze fixture identities differ")
    preflight_cells = preflight.get("cells")
    semantics = preflight.get("task_semantics")
    if (
        preflight.get("experiment_id") != plan.experiment_id
        or preflight.get("plan_fingerprint") != plan.plan_fingerprint
        or preflight.get("api_key_environment_names_present") != []
        or preflight.get("actual_model_turns") != 0
        or not isinstance(preflight_cells, list)
        or [item.get("cell_id") for item in preflight_cells if isinstance(item, dict)]
        != [cell.cell_id for cell in plan.cells]
        or any(
            not isinstance(item, dict)
            or item.get("ok") is not True
            or item.get("account_type") != "chatgpt"
            or item.get("sdk_version") != PINNED_SDK_VERSION
            or item.get("api_key_environment_names_present") != []
            or item.get("actual_model_turns") != 0
            for item in preflight_cells
        )
        or not isinstance(semantics, dict)
        or set(semantics) != {item.fixture_id for item in plan.fixtures}
        or any(
            not isinstance(value, dict)
            or value.get("c2") != value.get("b1")
            or not value.get("c2")
            for value in semantics.values()
        )
    ):
        raise RoutingSuiteError("S1 live freeze preflight evidence differs")
    expected_files = {
        "execution-plan.json",
        "build-record.json",
        "preflight.json",
        "regression.json",
        "freeze-seal.json",
        _copied_manifest_path("benchmarks/suites/sdk-routing-v1/suite.yaml"),
        _copied_manifest_path(contract["stage_relative"]),
        *(_copied_manifest_path(item.path) for item in stage.fixture_manifests),
    }
    actual_files = {
        path.relative_to(artifact_root).as_posix()
        for path in artifact_root.rglob("*")
        if path.is_file()
    }
    if require_exact_files and actual_files != expected_files:
        raise RoutingSuiteError("S1 live freeze file set differs")
    files = _artifact_files_without_seal(artifact_root)
    value = _aggregate_export_sha256(files)
    if (
        seal.get("status") != "frozen_before_first_cell"
        or seal.get("experiment_id") != plan.experiment_id
        or seal.get("plan_fingerprint") != plan.plan_fingerprint
        or seal.get("planned_cells") != contract["planned_cells"]
        or seal.get("planned_live_model_turns") != contract["max_turns"]
        or seal.get("actual_model_turns") != 0
        or seal.get("file_count") != len(files)
        or seal.get("freeze_sha256") != value
    ):
        raise RoutingSuiteError("S1 live freeze aggregate seal differs")
    for relative, data in files.items():
        _r5_assert_export_safe(relative, data)
    return {
        "experiment_id": plan.experiment_id,
        "plan_fingerprint": plan.plan_fingerprint,
        "plan_sha256": hashlib.sha256(plan_bytes).hexdigest(),
        "file_count": len(files),
        "freeze_sha256": value,
        "bindings": {
            "source_commit": build["source_commit"],
            "benchmark_python_path_sha256": build[
                "benchmark_python_path_sha256"
            ],
            "git_executable_path_sha256": build["git_executable_path_sha256"],
        },
    }


def _assert_live_source_boundary(
    *,
    repository_root: Path,
    plan: ExecutionPlan,
    state: dict[str, Any],
    adapter: object,
    benchmark_python: Path,
    remaining_model_turns: int,
    expected_b1_turn_cap: int | None = None,
    expected_b1_timeout_seconds: float = 2_000,
) -> None:
    current_runner = runner_source_sha256()
    current_b1 = _source_tree_sha256(
        repository_root / "stages" / "b1-sequential", B1_FINGERPRINT_INPUTS
    )
    c2 = next(item for item in plan.variants if item.artifact_id == "c2")
    b1 = next(item for item in plan.variants if item.artifact_id == "b1")
    if (
        current_runner != state["runner_source_sha256"]
        or current_runner != plan.runner.sha256
        or current_runner != c2.sha256
        or current_b1 != state["b1_source_sha256"]
        or current_b1 != b1.sha256
    ):
        raise RoutingSuiteError("S1 live executing source differs from the frozen Plan")
    if isinstance(adapter, B1SequentialAdapter):
        expected_prefix = (str(benchmark_python.resolve()), "-P", "-m", "orchestrator")
        expected_schema = (
            repository_root / "stages" / "b1-sequential" / "schemas" / "v1"
        ).resolve()
        expected_python_path = (
            repository_root / "stages" / "b1-sequential" / "src"
        ).resolve()
        if (
            adapter.config.command_prefix != expected_prefix
            or adapter.config.schema_root.resolve() != expected_schema
            or adapter.config.python_path is None
            or adapter.config.python_path.resolve() != expected_python_path
            or adapter.config.invocation_cwd is None
            or adapter.config.invocation_cwd.resolve() != expected_python_path
            or adapter.config.max_model_turns
            != (
                expected_b1_turn_cap
                if expected_b1_turn_cap is not None
                else min(8, remaining_model_turns)
            )
            or adapter.config.timeout_seconds != expected_b1_timeout_seconds
            or adapter.config.runtime != "codex"
        ):
            raise RoutingSuiteError("S1 live B1 command or Schema boundary differs")


def _stop_record(experiment_dir: Path) -> dict[str, Any] | None:
    path = experiment_dir / STOP_FILENAME
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RoutingSuiteError("S1 live stop record is invalid") from exc
    return value


def _write_stop_record(experiment_dir: Path, *, cell_id: str, reason: str) -> None:
    path = experiment_dir / STOP_FILENAME
    if path.exists():
        return
    atomic_write(
        path,
        canonical_json_bytes(
            {
                "schema_version": 1,
                "kind": "sdk_routing_s1_live_stop",
                "cell_id": cell_id,
                "reason": reason,
                "automatic_retry": False,
                "recorded_at": utc_now().isoformat(),
            }
        ),
    )


def _claim_cell_dispatch(experiment_dir: Path, cell_id: str) -> Path:
    """Durably claim a paid Cell once; a surviving claim forbids implicit retry."""

    path = experiment_dir / "cells" / cell_id / DISPATCH_MARKER_FILENAME
    payload = canonical_json_bytes(
        {
            "schema_version": 1,
            "kind": "sdk_routing_s1_live_dispatch_claim",
            "cell_id": cell_id,
            "automatic_retry": False,
            "claimed_at": utc_now().isoformat(),
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise RoutingSuiteError("S1 live Cell already has a durable dispatch claim") from exc
    return path


def _token_total(measurement: Measurement) -> int | None:
    value = measurement.resource.token_usage.value
    status = measurement.resource.token_usage.status
    if getattr(status, "value", status) != "measured" or not isinstance(value, dict):
        return None
    total = value.get("total_tokens")
    return total if isinstance(total, int) and not isinstance(total, bool) and total >= 0 else None


def _wall_seconds(measurement: Measurement) -> float | None:
    value = measurement.effort.total_wall_clock_seconds.value
    status = measurement.effort.total_wall_clock_seconds.status
    if getattr(status, "value", status) != "measured":
        return None
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _assert_live_measurement_contract(
    cell: PlannedCell,
    measurement: Measurement,
    *,
    stage_id: str = "s1-baseline",
) -> None:
    environment = measurement.environment
    if (
        environment.model != PINNED_MODEL
        or environment.auth_method != "chatgpt"
        or environment.python_version != "3.12.10"
        or environment.reasoning_effort != PINNED_REASONING_EFFORT
        or environment.approval_mode != PINNED_APPROVAL_MODE
        or environment.model_control != "explicit_thread_and_turn"
        or environment.reasoning_control != "explicit_each_turn"
        or environment.treatment_control != "full"
        or environment.surface_kind
        != (
            "b1_cli_codex_runtime"
            if cell.variant_id == "b1"
            else "sdk_controlled_codex_runtime"
        )
    ):
        raise RoutingSuiteError("S1 live export Measurement environment differs")
    values = measurement.variant_metrics.values
    actual_turns = values.get("actual_model_turns")
    turn_count = measurement.resource.turn_count
    session_count = measurement.resource.session_count
    attempt_count = measurement.resource.attempt_count
    if (
        measurement.variant_metrics.schema_id != "sdk-controlled-live-pilot/v1"
        or not isinstance(actual_turns, int)
        or isinstance(actual_turns, bool)
        or actual_turns < 1
        or getattr(turn_count.status, "value", turn_count.status) != "measured"
        or turn_count.value != actual_turns
        or getattr(session_count.status, "value", session_count.status) != "measured"
        or not isinstance(session_count.value, int)
        or isinstance(session_count.value, bool)
        or session_count.value < 1
        or getattr(attempt_count.status, "value", attempt_count.status) != "measured"
        or not isinstance(attempt_count.value, int)
        or isinstance(attempt_count.value, bool)
        or attempt_count.value < 1
        or values.get("protected_files_ok") not in {True, False}
    ):
        raise RoutingSuiteError("S1 live export Measurement resource contract differs")
    if stage_id == "s2-intermediate":
        model_active = values.get("model_active_seconds")
        wall = _wall_seconds(measurement)
        checker_sha256 = values.get("checker_sha256")
        maximum_turns = 3 if cell.variant_id == "c2" else 6
        maximum_model_active = (
            2_700
            if cell.variant_id == "c2"
            else min(2_700 + 900 * max(0, actual_turns - 3), 3_300)
        )
        if (
            actual_turns > maximum_turns
            or not isinstance(model_active, (int, float))
            or isinstance(model_active, bool)
            or not 0 <= float(model_active) <= maximum_model_active
            or wall is None
            or not 0 <= wall <= 3_300
            or values.get("property_status") not in {"pass", "fail", "checker_error"}
            or not isinstance(checker_sha256, str)
            or len(checker_sha256) != 64
        ):
            raise RoutingSuiteError("S2 live Measurement property or limit contract differs")
    if cell.variant_id == "b1":
        for name in ("b1_retry_count", "b1_resume_count"):
            value = values.get(name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise RoutingSuiteError("S1 live export B1 retry metrics differ")
        for name in (
            "b1_intermediate_check_changed_result",
            "b1_intermediate_check_changed_dispatch",
            "b1_repeatable_quality_regression",
        ):
            if values.get(name) not in {True, False}:
                raise RoutingSuiteError("S1 live export B1 control metrics differ")
        if (
            stage_id == "s2-intermediate"
            and actual_turns
            > 3 + values["b1_retry_count"] + values["b1_resume_count"]
        ):
            raise RoutingSuiteError("S2 live B1 turns exceed retry/resume attribution")
        if stage_id == "s2-intermediate" and not b1_dual_outcome_contract_valid(
            measurement
        ):
            raise RoutingSuiteError("S2 live B1 dual outcome contract differs")
    token = measurement.resource.token_usage
    token_status = getattr(token.status, "value", token.status)
    if token_status == "measured":
        value = token.value
        if (
            not isinstance(value, dict)
            or any(
                not isinstance(value.get(name), int)
                or isinstance(value.get(name), bool)
                or value[name] < 0
                for name in ("input_tokens", "output_tokens", "total_tokens")
            )
            or value["total_tokens"] != value["input_tokens"] + value["output_tokens"]
        ):
            raise RoutingSuiteError("S1 live export token accounting differs")
    elif token_status != "unknown" or token.value is not None:
        raise RoutingSuiteError("S1 live export token status differs")


def _assert_live_measurement_plan_binding(
    plan: ExecutionPlan, cell: PlannedCell, measurement: Measurement
) -> None:
    expected_identity = MeasurementIdentity(
        experiment_id=plan.experiment_id,
        block_id=cell.block_id,
        cell_id=cell.cell_id,
        fixture_id=cell.fixture_id,
        repetition=cell.repetition,
        variant_id=cell.variant_id,
        execution_ordinal=cell.execution_ordinal,
    )
    fixture = next(item for item in plan.fixtures if item.fixture_id == cell.fixture_id)
    variant = next(item for item in plan.variants if item.artifact_id == cell.variant_id)
    if measurement.identity != expected_identity:
        raise RoutingSuiteError("S1 live Measurement identity differs from the Plan")
    if (
        measurement.provenance.manifest_sha256 != plan.source_manifest.sha256
        or measurement.provenance.fixture_source_commit != fixture.source_commit
        or measurement.provenance.fixture_tree_before != fixture.git_tree
        or measurement.provenance.runner_commit != plan.runner.version
        or measurement.provenance.variant_version != variant.version
        or measurement.provenance.variant_artifact_sha256 != variant.sha256
    ):
        raise RoutingSuiteError("S1 live Measurement provenance differs from the Plan")


def _calibration_outcome(measurements: list[Measurement]) -> str:
    if len(measurements) != 8:
        raise RoutingSuiteError("S1 calibration requires eight Measurements")
    turn_values = [item.variant_metrics.values.get("actual_model_turns") for item in measurements]
    if any(
        not isinstance(value, int) or isinstance(value, bool) or value < 0
        for value in turn_values
    ):
        raise RoutingSuiteError("S1 calibration model turn count is invalid")
    actual_turns = sum(turn_values)
    if actual_turns > S1_PLANNED_LIVE_MODEL_TURNS or any(
        not item.integrity.scope_ok
        or not item.integrity.evidence_hashes_ok
        or bool(item.integrity.secret_findings)
        or item.variant_metrics.values.get("protected_files_ok") is not True
        or (
            item.identity.variant_id == "b1"
            and item.variant_metrics.values.get("b1_repeatable_quality_regression")
            is True
        )
        for item in measurements
    ):
        return "CALIBRATION_STOP"
    if not all(
        item.outcome.check_success
        and item.outcome.state == "completed"
        and item.outcome.failure_kind is None
        for item in measurements
    ):
        return "CALIBRATION_INCONCLUSIVE"
    tokens = {"c2": 0, "b1": 0}
    walls = {"c2": 0.0, "b1": 0.0}
    for measurement in measurements:
        token = _token_total(measurement)
        wall = _wall_seconds(measurement)
        if token is None or wall is None:
            return "CALIBRATION_INCONCLUSIVE"
        tokens[measurement.identity.variant_id] += token
        walls[measurement.identity.variant_id] += wall
    if tokens["c2"] <= 0 or walls["c2"] <= 0:
        return "CALIBRATION_INCONCLUSIVE"
    if tokens["b1"] / tokens["c2"] > 1.50 or walls["b1"] / walls["c2"] > 2.00:
        return "CALIBRATION_STOP"
    if actual_turns != S1_PLANNED_LIVE_MODEL_TURNS:
        return "CALIBRATION_INCONCLUSIVE"
    return "CALIBRATION_PASS"


def routing_s1_live_status(state_root: Path) -> dict[str, Any]:
    experiment_dir, plan, state = _load_live_plan(state_root)
    contract = _plan_stage_contract(plan)
    stop = _stop_record(experiment_dir)
    rows: list[dict[str, Any]] = []
    measurements: list[Measurement] = []
    sealed = 0
    for cell in sorted(plan.cells, key=lambda item: item.execution_ordinal):
        path = experiment_dir / "cells" / cell.cell_id / "cell-state.json"
        dispatch_claim = path.parent / DISPATCH_MARKER_FILENAME
        if not path.is_file():
            if dispatch_claim.is_file():
                stop = stop or {
                    "schema_version": 1,
                    "kind": "sdk_routing_s1_live_stop",
                    "cell_id": cell.cell_id,
                    "reason": "durable dispatch claim exists without a sealed Cell",
                    "automatic_retry": False,
                }
            rows.append(
                {
                    "cell_id": cell.cell_id,
                    "fixture_id": cell.fixture_id,
                    "variant_id": cell.variant_id,
                    "state": "PLANNED",
                    "outcome_state": None,
                }
            )
            continue
        record = CellStateRecord.model_validate_json(path.read_bytes())
        if record.state is not CellLifecycleState.SEALED:
            stop = stop or {
                "schema_version": 1,
                "kind": "sdk_routing_s1_live_stop",
                "cell_id": cell.cell_id,
                "reason": f"Cell remained {record.state.value}",
                "automatic_retry": False,
            }
        else:
            measurement = verify_sealed_cell(path.parent)
            _assert_live_measurement_plan_binding(plan, cell, measurement)
            _assert_live_measurement_contract(
                cell,
                measurement,
                stage_id=contract["stage_id"],
            )
            measurements.append(measurement)
            sealed += 1
        rows.append(
            {
                "cell_id": cell.cell_id,
                "fixture_id": cell.fixture_id,
                "variant_id": cell.variant_id,
                "state": record.state.value,
                "outcome_state": record.outcome_state,
            }
        )
    complete = sealed == len(plan.cells)
    turn_values = [item.variant_metrics.values.get("actual_model_turns") for item in measurements]
    if any(
        not isinstance(value, int) or isinstance(value, bool) or value < 0
        for value in turn_values
    ):
        raise RoutingSuiteError("S1 live Measurement model turn count is invalid")
    actual_turns = sum(turn_values)
    if contract["stage_id"] == "s2-intermediate":
        posthoc_results: dict[str, dict[str, object]] = {}
        for measurement in measurements:
            path = (
                experiment_dir
                / "cells"
                / measurement.identity.cell_id
                / "judge"
                / "posthoc"
                / "result.json"
            )
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise RoutingSuiteError("S2 live post-hoc Evidence is invalid") from exc
            if not isinstance(value, dict):
                raise RoutingSuiteError("S2 live post-hoc Evidence is not an object")
            posthoc_results[measurement.identity.cell_id] = value
        checker_contracts = plan.decision_policy.get("posthoc_checks")
        infrastructure_stop = (
            stop is not None
            or actual_turns > contract["max_turns"]
            or not isinstance(checker_contracts, dict)
            or any(
                not item.integrity.scope_ok
                or not item.integrity.evidence_hashes_ok
                or bool(item.integrity.secret_findings)
                or item.variant_metrics.values.get("protected_files_ok") is not True
                or item.variant_metrics.values.get("property_status") == "checker_error"
                or item.outcome.state == "infrastructure_error"
                or item.outcome.failure_kind
                in {
                    "transient_runtime",
                    "runtime_dispatch_failed",
                    "runtime_timeout",
                    "timeout",
                    "timed_out",
                    "checker_error",
                }
                or not isinstance(checker_contracts.get(item.identity.fixture_id), dict)
                or item.variant_metrics.values.get("checker_sha256")
                != checker_contracts[item.identity.fixture_id].get("checker_sha256")
                or posthoc_results[item.identity.cell_id].get("checker_sha256")
                != checker_contracts[item.identity.fixture_id].get("checker_sha256")
                for item in measurements
            )
        )
        policy_plan = plan
        policy_measurements = measurements
        policy_posthoc = posthoc_results
        additional_plans: tuple[ExecutionPlan, ...] = ()
        initial_experiment_id: str | None = None
        combined_actual_turns = actual_turns
        if plan.decision_policy.get("execution_phase") == "reverse":
            (
                initial_plan,
                initial_measurements,
                initial_posthoc,
                _,
            ) = _verified_s2_initial_export(plan=plan, state=state)
            policy_plan = initial_plan
            additional_plans = (plan,)
            policy_measurements = [*initial_measurements, *measurements]
            policy_posthoc = {**initial_posthoc, **posthoc_results}
            initial_experiment_id = initial_plan.experiment_id
            combined_actual_turns += sum(
                item.variant_metrics.values["actual_model_turns"]
                for item in initial_measurements
            )
        policy = derive_s2_routing_policy(
            plan=policy_plan,
            additional_plans=additional_plans,
            measurements=policy_measurements,
            sealed_cell_ids={item.identity.cell_id for item in policy_measurements},
            posthoc_results=policy_posthoc,
        )
        stage_state = (
            "S2_STOP"
            if infrastructure_stop
            else policy["stage_state"]
            if complete
            else "S2_INCOMPLETE"
        )
        return {
            "schema_version": 1,
            "kind": "sdk_routing_s2_live_status",
            "experiment_id": plan.experiment_id,
            "initial_experiment_id": initial_experiment_id,
            "planned_cells": len(plan.cells),
            "sealed_cells": sealed,
            "complete": complete,
            "actual_model_turns": actual_turns,
            "combined_actual_model_turns": combined_actual_turns,
            "remaining_b1_retry_resume_reserve": remaining_b1_retry_resume_reserve(
                measurements
            ),
            "stage_state": stage_state,
            "routing_policy": policy if complete else None,
            "route_decision_issued": any(
                item.get("route_issued") is True
                for item in policy["profiles"].values()
            ) if complete else False,
            "stop_before_next_cell": infrastructure_stop,
            "stop_record": stop,
            "cells": rows,
        }
    immediate_stop = any(
        item.identity.variant_id != "b1"
        and (
            not item.integrity.scope_ok
            or not item.integrity.evidence_hashes_ok
            or bool(item.integrity.secret_findings)
            or item.variant_metrics.values.get("protected_files_ok") is not True
        )
        for item in measurements
    )
    pair_stop = False
    for index in range(0, len(measurements) - 1, 2):
        pair = measurements[index : index + 2]
        if len(pair) == 2 and any(
            item.identity.variant_id == "b1"
            and (
                    not item.integrity.scope_ok
                    or not item.integrity.evidence_hashes_ok
                    or bool(item.integrity.secret_findings)
                    or item.variant_metrics.values.get("protected_files_ok") is not True
                    or item.variant_metrics.values.get(
                        "b1_repeatable_quality_regression"
                    )
                    is True
            )
            for item in pair
        ):
            pair_stop = True
    turn_budget_exhausted = actual_turns >= S1_PLANNED_LIVE_MODEL_TURNS and not complete
    terminal_stop = (
        stop is not None or immediate_stop or pair_stop or turn_budget_exhausted
    )
    outcome = (
        _calibration_outcome(measurements)
        if complete
        else "CALIBRATION_STOP" if terminal_stop else None
    )
    return {
        "schema_version": 1,
        "kind": "sdk_routing_s1_live_status",
        "experiment_id": plan.experiment_id,
        "planned_cells": len(plan.cells),
        "sealed_cells": sealed,
        "complete": complete,
        "actual_model_turns": actual_turns,
        "calibration_outcome": outcome,
        "calibration_outcome_issued": outcome is not None,
        "route_decision_issued": False,
        "stop_before_next_cell": terminal_stop or outcome == "CALIBRATION_STOP",
        "stop_record": stop,
        "cells": rows,
    }


def run_next_routing_s1_live_cell(
    *,
    state_root: Path,
    benchmark_python: Path,
    confirm_model_usage: bool,
) -> dict[str, Any]:
    """Run exactly one frozen S1 Cell after an explicit per-Cell confirmation."""

    if not confirm_model_usage:
        raise RoutingSuiteError("S1 live Cell requires explicit model-usage confirmation")
    if benchmark_python.resolve() != Path(sys.executable).resolve():
        raise RoutingSuiteError("S1 live benchmark Python must be the controller interpreter")
    if present_api_key_environment_names():
        raise RoutingSuiteError("API key environment is present; S1 live execution fails closed")
    experiment_dir, plan, state = _load_live_plan(state_root)
    contract = _plan_stage_contract(plan)
    is_s2 = contract["stage_id"] == "s2-intermediate"
    status = routing_s1_live_status(state_root)
    if status["complete"] or status["stop_before_next_cell"]:
        raise RoutingSuiteError("S1 live status forbids another Cell")
    repository_root = Path(state["repository_root"]).resolve()
    artifact_root = Path(state["artifact_root"]).resolve()
    if (
        benchmark_python.resolve() != Path(state["benchmark_python"]).resolve()
        or sha256_file(benchmark_python.resolve()) != state["benchmark_python_sha256"]
        or plan.environment_fingerprint.get("benchmark_python_sha256")
        != state["benchmark_python_sha256"]
    ):
        raise RoutingSuiteError("S1 live Python executable changed after freeze")
    verified_freeze = verify_routing_s1_live_freeze(artifact_root)
    if (
        verified_freeze["experiment_id"] != plan.experiment_id
        or verified_freeze["plan_fingerprint"] != plan.plan_fingerprint
        or verified_freeze["plan_fingerprint"] != state["plan_fingerprint"]
        or verified_freeze["plan_sha256"] != state["plan_sha256"]
        or verified_freeze["freeze_sha256"] != state["freeze_sha256"]
        or verified_freeze["bindings"]
        != {
            "source_commit": state["source_commit"],
            "benchmark_python_path_sha256": _path_sha256(
                Path(state["benchmark_python"])
            ),
            "git_executable_path_sha256": _path_sha256(
                Path(state["git_executable"])
            ),
        }
    ):
        raise RoutingSuiteError("S1 live state and freeze artifact differ")
    if (
        _routing_controller_sha256(repository_root) != state["routing_controller_sha256"]
        or plan.environment_fingerprint.get("routing_controller_sha256")
        != state["routing_controller_sha256"]
    ):
        raise RoutingSuiteError("S1 live controller changed after freeze")
    current_git, current_git_version, current_git_sha256 = _git_identity()
    if (
        current_git != Path(state["git_executable"]).resolve()
        or current_git_version != state["git_version"]
        or current_git_sha256 != state["git_sha256"]
        or plan.environment_fingerprint.get("git_version") != state["git_version"]
        or plan.environment_fingerprint.get("git_sha256") != state["git_sha256"]
        or plan.environment_fingerprint.get("git_executable_path_sha256")
        != _path_sha256(current_git)
    ):
        raise RoutingSuiteError("S1 live Git executable changed after freeze")
    _assert_b1_module_origin(repository_root, benchmark_python)
    current_sdk_origin, current_sdk_sha256 = _codex_sdk_runtime_identity()
    if (
        current_sdk_origin != "Lib/site-packages/openai_codex/__init__.py"
        or current_sdk_sha256 != state["codex_sdk_runtime_sha256"]
        or plan.environment_fingerprint.get("codex_sdk_runtime_sha256")
        != state["codex_sdk_runtime_sha256"]
    ):
        raise RoutingSuiteError("S1 live Codex SDK source changed after freeze")
    if _assert_runtime_profile(_runtime_profile_path()) != state["runtime_profile_sha256"]:
        raise RoutingSuiteError("S1 live runtime profile changed")
    suite_path = repository_root / "benchmarks" / "suites" / "sdk-routing-v1" / "suite.yaml"
    stage_path = (
        repository_root
        / "benchmarks"
        / "suites"
        / "sdk-routing-v1"
        / "stages"
        / f"{contract['stage_id']}.yaml"
    )
    suite, stage = _resolve_stage(repository_root, suite_path, stage_path)
    current_fixture_manifests = {
        selection.path: sha256_file(repository_root / selection.path)
        for selection in stage.fixture_manifests
    }
    if (
        current_fixture_manifests != state["fixture_manifest_sha256"]
        or plan.environment_fingerprint.get("fixture_manifest_fingerprint")
        != json.dumps(
            state["fixture_manifest_sha256"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    ):
        raise RoutingSuiteError("S1 live fixture manifest bytes changed after freeze")
    if suite.status != "frozen_before_execution" or stage.status != "frozen_before_execution":
        raise RoutingSuiteError("S1 live manifests are no longer frozen")
    if (
        sha256_file(stage_path) != plan.source_manifest.sha256
        or sha256_file(suite_path) != plan.decision_policy.get("suite_sha256")
    ):
        raise RoutingSuiteError("S1 live manifest bytes changed after freeze")
    if is_s2:
        posthoc_checks = plan.decision_policy.get("posthoc_checks")
        if not isinstance(posthoc_checks, dict) or any(
            not isinstance(posthoc_checks.get(fixture_id), dict)
            or posthoc_checks[fixture_id].get("checker_sha256")
            != checker_sha256(fixture_id)
            for fixture_id in plan.decision_policy.get("profiles", {})
        ):
            raise RoutingSuiteError("S2 live checker source changed after freeze")
    next_cell = next(
        cell
        for cell in sorted(plan.cells, key=lambda item: item.execution_ordinal)
        if not (experiment_dir / "cells" / cell.cell_id / "cell-state.json").is_file()
    )
    fixtures = {fixture.id: fixture for fixture in _fixture_specs(repository_root, stage)}
    prepared = FixtureRestorer(repository_root, str(current_git)).open_existing(
        fixtures[next_cell.fixture_id],
        experiment_dir / "cells" / next_cell.cell_id / "workspace",
        require_clean=True,
    )
    next_planned_turns = len(_task_envelopes(next_cell.variant_id, prepared.workspace))
    if status["actual_model_turns"] + next_planned_turns > contract["max_turns"]:
        _write_stop_record(
            experiment_dir,
            cell_id=next_cell.cell_id,
            reason="next Cell would exceed the frozen 12-turn ceiling",
        )
        raise RoutingSuiteError("routing live turn ceiling forbids the next Cell")
    sealed_measurements = [
        verify_sealed_cell(experiment_dir / "cells" / cell.cell_id)
        for cell in sorted(plan.cells, key=lambda item: item.execution_ordinal)
        if (experiment_dir / "cells" / cell.cell_id / "sealed" / "measurement.json").is_file()
    ]
    b1_turn_cap = (
        s2_b1_turn_cap(sealed_measurements)
        if is_s2 and next_cell.variant_id == "b1"
        else min(8, contract["max_turns"] - status["actual_model_turns"])
        if next_cell.variant_id == "b1"
        else None
    )
    adapter = _adapter(
        repository_root=repository_root,
        experiment_dir=experiment_dir,
        cell=next_cell,
        workspace=prepared.workspace,
        benchmark_python=benchmark_python.resolve(),
        max_model_turns=b1_turn_cap,
        b1_timeout_seconds=3_300 if is_s2 else 2_000,
    )
    _assert_live_source_boundary(
        repository_root=repository_root,
        plan=plan,
        state=state,
        adapter=adapter,
        benchmark_python=benchmark_python,
        remaining_model_turns=contract["max_turns"] - status["actual_model_turns"],
        expected_b1_turn_cap=b1_turn_cap,
        expected_b1_timeout_seconds=3_300 if is_s2 else 2_000,
    )
    _claim_cell_dispatch(experiment_dir, next_cell.cell_id)
    try:
        result: SdkSealedCellResult = run_sdk_live_cell(
            experiment_dir=experiment_dir,
            plan=plan,
            planned_cell=next_cell,
            prepared=prepared,
            adapter=adapter,
            benchmark_python=benchmark_python.resolve(),
            git_executable=current_git,
            post_judge_hook=(
                lambda current: run_posthoc_subprocess(
                    repository_root=repository_root,
                    benchmark_python=benchmark_python.resolve(),
                    fixture_id=current.fixture.id,
                    workspace=current.workspace,
                )
            )
            if is_s2
            else None,
        )
    except Exception as exc:
        try:
            _write_stop_record(
                experiment_dir,
                cell_id=next_cell.cell_id,
                reason=f"{type(exc).__name__}: live Cell failed before a valid seal",
            )
        except Exception:
            pass
        raise
    return result.model_dump(mode="json")


def _measurement_summary_rows(measurements: list[Measurement]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for measurement in sorted(measurements, key=lambda item: item.identity.execution_ordinal):
        rows.append(
            {
                "cell_id": measurement.identity.cell_id,
                "fixture_id": measurement.identity.fixture_id,
                "profile_id": measurement.identity.fixture_id,
                "pair_id": f"pair_s1_{measurement.identity.fixture_id}_1",
                "variant_id": measurement.identity.variant_id,
                "outcome_state": measurement.outcome.state,
                "failure_kind": measurement.outcome.failure_kind,
                "check_success": measurement.outcome.check_success,
                "scope_ok": measurement.integrity.scope_ok,
                "protected_files_ok": measurement.variant_metrics.values.get(
                    "protected_files_ok"
                ),
                "evidence_hashes_ok": measurement.integrity.evidence_hashes_ok,
                "secret_findings": measurement.integrity.secret_findings,
                "session_count": measurement.resource.session_count.value,
                "turn_count": measurement.resource.turn_count.value,
                "attempt_count": measurement.resource.attempt_count.value,
                "token_usage_status": measurement.resource.token_usage.status.value,
                "token_usage": measurement.resource.token_usage.value,
                "model_active_seconds": measurement.variant_metrics.values.get(
                    "model_active_seconds"
                ),
                "total_wall_clock_seconds": measurement.effort.total_wall_clock_seconds.value,
                "actual_model_turns": measurement.variant_metrics.values["actual_model_turns"],
                "b1_retry_count": measurement.variant_metrics.values.get(
                    "b1_retry_count"
                ),
                "b1_resume_count": measurement.variant_metrics.values.get(
                    "b1_resume_count"
                ),
                "b1_intermediate_check_changed_result": measurement.variant_metrics.values.get(
                    "b1_intermediate_check_changed_result"
                ),
                "b1_intermediate_check_changed_dispatch": measurement.variant_metrics.values.get(
                    "b1_intermediate_check_changed_dispatch"
                ),
                "b1_repeatable_quality_regression": measurement.variant_metrics.values.get(
                    "b1_repeatable_quality_regression"
                ),
            }
        )
    return rows


def _live_summary(plan: ExecutionPlan, status: dict[str, Any], measurements: list[Measurement]):
    rows = _measurement_summary_rows(measurements)
    pairs = []
    for fixture_id, _ in S1_EXPECTED_CELL_ORDER:
        if any(item["profile_id"] == fixture_id for item in pairs):
            continue
        pair_rows = [row for row in rows if row["fixture_id"] == fixture_id]
        if pair_rows:
            pairs.append(
                {
                    "profile_id": fixture_id,
                    "pair_id": f"pair_s1_{fixture_id}_1",
                    "cell_ids": [row["cell_id"] for row in pair_rows],
                }
            )
    return {
        "schema_version": 1,
        "kind": "sdk_routing_s1_live_summary",
        "experiment_id": plan.experiment_id,
        "planned_cells": len(plan.cells),
        "sealed_cells": len(measurements),
        "complete": status["complete"],
        "calibration_outcome": status["calibration_outcome"],
        "actual_model_turns": status["actual_model_turns"],
        "calibration_outcome_issued": True,
        "route_decision_issued": False,
        "stop_record": status["stop_record"],
        "profile_pairs": pairs,
        "limitations": [
            "one pair per small deterministic fixture",
            "public worker-visible Checks",
            "does not authorize profile ROUTE_* or B1 default adoption",
        ],
        "cells": rows,
    }


def _live_summary_markdown(summary: dict[str, Any]) -> bytes:
    lines = [
        "# SDK routing S1 live calibration",
        "",
        f"- Experiment: `{summary['experiment_id']}`",
        f"- Calibration: `{summary['calibration_outcome']}`",
        f"- Actual model turns: `{summary['actual_model_turns']}`",
        "- Route decision issued: `false`",
        "",
        "| Cell | Profile / pair | Variant | Outcome / failure | Judge | Scope / protected / Evidence | Retry / resume | Turns |",
        "|---|---|---|---|---:|---|---|---:|",
    ]
    for row in summary["cells"]:
        lines.append(
            f"| {row['cell_id']} | {row['profile_id']} / {row['pair_id']} | "
            f"{row['variant_id']} | {row['outcome_state']} / {row['failure_kind']} | "
            f"{str(row['check_success']).lower()} | "
            f"{str(row['scope_ok']).lower()} / {str(row['protected_files_ok']).lower()} / "
            f"{str(row['evidence_hashes_ok']).lower()} | "
            f"{row['b1_retry_count']} / {row['b1_resume_count']} | "
            f"{row['turn_count']} |"
        )
    lines.extend(
        [
            "",
            "이 결과는 작은 공개 Check fixture의 calibration이며 profile별 `ROUTE_*`를 발행하지 않는다.",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def export_routing_s1_live(*, state_root: Path, results_root: Path) -> dict[str, Any]:
    experiment_dir, plan, state = _load_live_plan(state_root)
    status = routing_s1_live_status(state_root)
    if status["calibration_outcome"] not in S1_ALLOWED_OUTCOMES:
        raise RoutingSuiteError("S1 live export requires a terminal calibration outcome")
    if status["complete"] is not True and status["calibration_outcome"] != "CALIBRATION_STOP":
        raise RoutingSuiteError("partial S1 live export is allowed only for CALIBRATION_STOP")
    measurements = [
        verify_sealed_cell(experiment_dir / "cells" / cell.cell_id)
        for cell in sorted(plan.cells, key=lambda item: item.execution_ordinal)
        if (experiment_dir / "cells" / cell.cell_id / "cell-state.json").is_file()
        and CellStateRecord.model_validate_json(
            (experiment_dir / "cells" / cell.cell_id / "cell-state.json").read_bytes()
        ).state
        is CellLifecycleState.SEALED
    ]
    summary = _live_summary(plan, status, measurements)
    export_root = results_root.resolve() / "sdk-routing-v1" / plan.experiment_id
    if export_root.exists():
        raise RoutingSuiteError("S1 live export destination already exists")
    artifact_root = Path(state["artifact_root"]).resolve()
    files: dict[str, bytes] = {
        "execution-plan.json": (artifact_root / "execution-plan.json").read_bytes(),
        "summary.json": canonical_json_bytes(summary),
        "summary.md": _live_summary_markdown(summary),
        "build-record.json": (artifact_root / "build-record.json").read_bytes(),
        "preflight.json": (artifact_root / "preflight.json").read_bytes(),
        "regression.json": (artifact_root / "regression.json").read_bytes(),
        "freeze-seal.json": (artifact_root / "freeze-seal.json").read_bytes(),
    }
    for path in (artifact_root / "manifests" / "source").rglob("*"):
        if path.is_file():
            files[path.relative_to(artifact_root).as_posix()] = path.read_bytes()
    stop_path = experiment_dir / STOP_FILENAME
    if stop_path.is_file():
        files[f"terminal/{STOP_FILENAME}"] = stop_path.read_bytes()
    elif status["stop_record"] is not None:
        files[f"terminal/{STOP_FILENAME}"] = canonical_json_bytes(status["stop_record"])
    for cell in sorted(plan.cells, key=lambda item: item.execution_ordinal):
        claim = experiment_dir / "cells" / cell.cell_id / DISPATCH_MARKER_FILENAME
        if claim.is_file():
            files[f"terminal/{cell.cell_id}-{DISPATCH_MARKER_FILENAME}"] = claim.read_bytes()
    seals = []
    by_cell = {item.identity.cell_id: item for item in measurements}
    for cell in sorted(plan.cells, key=lambda item: item.execution_ordinal):
        measurement = by_cell.get(cell.cell_id)
        if measurement is None:
            continue
        cell_dir = experiment_dir / "cells" / cell.cell_id
        record = CellStateRecord.model_validate_json((cell_dir / "cell-state.json").read_bytes())
        if record.sealed_measurement_sha256 is None:
            raise RoutingSuiteError("sealed S1 live Cell omitted its Measurement hash")
        prefix = f"cells/{cell.cell_id}"
        measurement_relative = f"{prefix}/sealed/measurement.json"
        files[measurement_relative] = (cell_dir / "sealed" / "measurement.json").read_bytes()
        for evidence in measurement.evidence:
            files[f"{prefix}/{evidence.path}"] = (cell_dir / evidence.path).read_bytes()
        seals.append(
            {
                "cell_id": cell.cell_id,
                "fixture_id": cell.fixture_id,
                "variant_id": cell.variant_id,
                "measurement_path": measurement_relative,
                "sealed_measurement_sha256": record.sealed_measurement_sha256,
            }
        )
    files["seals.json"] = canonical_json_bytes(
        {
            "schema_version": 1,
            "kind": "sdk_routing_s1_live_seals",
            "experiment_id": plan.experiment_id,
            "plan_fingerprint": plan.plan_fingerprint,
            "entries": seals,
        }
    )
    for relative, data in files.items():
        _r5_assert_export_safe(relative, data)
        atomic_write(export_root / relative, data)
    export_sha256 = _aggregate_export_sha256(files)
    atomic_write(
        export_root / "export-seal.json",
        canonical_json_bytes(
            {
                "schema_version": 1,
                "kind": "sdk_routing_s1_live_export_seal",
                "experiment_id": plan.experiment_id,
                "file_count": len(files),
                "export_sha256": export_sha256,
            }
        ),
    )
    verified = verify_routing_s1_live_export(export_root)
    return {
        "experiment_id": plan.experiment_id,
        "calibration_outcome": summary["calibration_outcome"],
        "results_root": str(export_root),
        "file_count": len(files),
        "export_sha256": verified["export_sha256"],
    }


def verify_routing_s1_live_export(export_root: Path) -> dict[str, Any]:
    """Verify a live export using only exported bytes."""

    export_root = export_root.resolve()
    freeze_verified = verify_routing_s1_live_freeze(
        export_root, require_exact_files=False
    )
    try:
        plan = ExecutionPlan.model_validate_json(
            (export_root / "execution-plan.json").read_bytes()
        )
        assert_plan_integrity(plan)
        summary = json.loads((export_root / "summary.json").read_text(encoding="utf-8"))
        seals = json.loads((export_root / "seals.json").read_text(encoding="utf-8"))
        export_seal = json.loads(
            (export_root / "export-seal.json").read_text(encoding="utf-8")
        )
        freeze_seal = json.loads(
            (export_root / "freeze-seal.json").read_text(encoding="utf-8")
        )
        suite_bytes = (
            export_root
            / _copied_manifest_path("benchmarks/suites/sdk-routing-v1/suite.yaml")
        ).read_bytes()
        stage_bytes = (
            export_root
            / _copied_manifest_path(
                "benchmarks/suites/sdk-routing-v1/stages/s1-baseline.yaml"
            )
        ).read_bytes()
        from benchmark_runner.routing_suite import RoutingStageManifest, RoutingSuiteManifest

        suite = RoutingSuiteManifest.model_validate(yaml.safe_load(suite_bytes))
        stage = RoutingStageManifest.model_validate(yaml.safe_load(stage_bytes))
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        raise RoutingSuiteError("S1 live export metadata is missing or invalid") from exc
    if (
        [item.value for item in plan.plan_supplemented if item.field == "track"]
        != [LIVE_TRACK]
        or [item for item in plan.plan_supplemented if item.field == "actual_model_turns"]
        or suite.status != "frozen_before_execution"
        or stage.status != "frozen_before_execution"
        or plan.source_manifest.sha256 != hashlib.sha256(stage_bytes).hexdigest()
        or plan.decision_policy.get("suite_sha256") != hashlib.sha256(suite_bytes).hexdigest()
        or plan.decision_policy.get("route_decision_allowed") is not False
        or summary.get("experiment_id") != plan.experiment_id
        or summary.get("calibration_outcome_issued") is not True
        or summary.get("route_decision_issued") is not False
        or summary.get("calibration_outcome") not in S1_ALLOWED_OUTCOMES
        or seals.get("experiment_id") != plan.experiment_id
        or seals.get("plan_fingerprint") != plan.plan_fingerprint
        or export_seal.get("experiment_id") != plan.experiment_id
        or freeze_verified["experiment_id"] != plan.experiment_id
        or freeze_verified["freeze_sha256"] != freeze_seal.get("freeze_sha256")
        or freeze_seal.get("experiment_id") != plan.experiment_id
        or freeze_seal.get("plan_fingerprint") != plan.plan_fingerprint
        or freeze_seal.get("status") != "frozen_before_first_cell"
    ):
        raise RoutingSuiteError("S1 live export identities differ")
    entries = seals.get("entries")
    ordered_cells = sorted(plan.cells, key=lambda item: item.execution_ordinal)
    expected_cells = {cell.cell_id: cell for cell in ordered_cells}
    entry_ids = [entry.get("cell_id") for entry in entries if isinstance(entry, dict)] if isinstance(entries, list) else []
    if (
        not isinstance(entries, list)
        or entry_ids != [cell.cell_id for cell in ordered_cells[: len(entries)]]
        or (len(entries) != len(expected_cells) and summary.get("calibration_outcome") != "CALIBRATION_STOP")
    ):
        raise RoutingSuiteError("S1 live export seal index differs")
    measurements: list[Measurement] = []
    expected_cell_paths: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise RoutingSuiteError("S1 live export seal entry is invalid")
        cell = expected_cells[entry["cell_id"]]
        if (
            entry.get("fixture_id") != cell.fixture_id
            or entry.get("variant_id") != cell.variant_id
        ):
            raise RoutingSuiteError("S1 live export seal entry provenance differs")
        relative = entry.get("measurement_path")
        if not isinstance(relative, str):
            raise RoutingSuiteError("S1 live export Measurement path is invalid")
        path = (export_root / relative).resolve()
        if not path.is_relative_to(export_root) or not path.is_file() or path.is_symlink():
            raise RoutingSuiteError("S1 live export Measurement is missing or unsafe")
        data = path.read_bytes()
        expected_cell_paths.add(relative)
        if hashlib.sha256(data).hexdigest() != entry.get("sealed_measurement_sha256"):
            raise RoutingSuiteError("S1 live export Measurement seal differs")
        measurement = Measurement.model_validate_json(data)
        _assert_live_measurement_plan_binding(plan, cell, measurement)
        _assert_live_measurement_contract(cell, measurement)
        cell_root = path.parents[1]
        for evidence in measurement.evidence:
            evidence_path = (cell_root / evidence.path).resolve()
            if (
                not evidence_path.is_relative_to(cell_root)
                or not evidence_path.is_file()
                or evidence_path.is_symlink()
            ):
                raise RoutingSuiteError("S1 live export Evidence is missing or unsafe")
            evidence_data = evidence_path.read_bytes()
            expected_cell_paths.add(
                f"cells/{cell.cell_id}/{evidence.path}"
            )
            if (
                len(evidence_data) != evidence.size
                or hashlib.sha256(evidence_data).hexdigest() != evidence.sha256
            ):
                raise RoutingSuiteError("S1 live export Evidence hash differs")
        measurements.append(measurement)
    actual_turns = sum(
        item.variant_metrics.values["actual_model_turns"] for item in measurements
    )
    complete = len(measurements) == len(plan.cells)
    stop_payload = None
    stop_path = export_root / "terminal" / STOP_FILENAME
    if stop_path.is_file():
        if stop_path.is_symlink():
            raise RoutingSuiteError("S1 live export stop record is unsafe")
        stop_payload = json.loads(stop_path.read_text(encoding="utf-8"))
        if (
            not isinstance(stop_payload, dict)
            or stop_payload.get("kind") != "sdk_routing_s1_live_stop"
            or stop_payload.get("automatic_retry") is not False
            or stop_payload.get("cell_id") not in expected_cells
            or not isinstance(stop_payload.get("reason"), str)
            or not stop_payload.get("reason")
        ):
            raise RoutingSuiteError("S1 live export stop record differs")
    measured_ids = {item.identity.cell_id for item in measurements}
    unsealed_claim = False
    terminal_root = export_root / "terminal"
    if terminal_root.is_dir():
        for claim_path in terminal_root.glob(f"*-{DISPATCH_MARKER_FILENAME}"):
            if claim_path.is_symlink():
                raise RoutingSuiteError("S1 live export dispatch claim is unsafe")
            claim = json.loads(claim_path.read_text(encoding="utf-8"))
            claim_cell = claim.get("cell_id") if isinstance(claim, dict) else None
            if (
                not isinstance(claim, dict)
                or claim.get("kind") != "sdk_routing_s1_live_dispatch_claim"
                or claim.get("automatic_retry") is not False
                or claim_cell not in expected_cells
                or claim_path.name != f"{claim_cell}-{DISPATCH_MARKER_FILENAME}"
            ):
                raise RoutingSuiteError("S1 live export dispatch claim differs")
            unsealed_claim = unsealed_claim or claim_cell not in measured_ids
    unsafe_measurement = any(
        not item.integrity.scope_ok
        or not item.integrity.evidence_hashes_ok
        or bool(item.integrity.secret_findings)
        or item.variant_metrics.values.get("protected_files_ok") is not True
        or (
            item.identity.variant_id == "b1"
            and item.variant_metrics.values.get("b1_repeatable_quality_regression")
            is True
        )
        for item in measurements
    )
    if complete:
        measured_outcome = _calibration_outcome(measurements)
    elif stop_payload is not None or unsealed_claim or unsafe_measurement or actual_turns >= S1_PLANNED_LIVE_MODEL_TURNS:
        measured_outcome = "CALIBRATION_STOP"
    else:
        raise RoutingSuiteError("partial S1 live export lacks independently verifiable stop evidence")
    expected_rows = _measurement_summary_rows(measurements)
    expected_pairs = []
    for fixture_id, _ in S1_EXPECTED_CELL_ORDER:
        if any(item["profile_id"] == fixture_id for item in expected_pairs):
            continue
        pair_rows = [row for row in expected_rows if row["fixture_id"] == fixture_id]
        if pair_rows:
            expected_pairs.append(
                {
                    "profile_id": fixture_id,
                    "pair_id": f"pair_s1_{fixture_id}_1",
                    "cell_ids": [row["cell_id"] for row in pair_rows],
                }
            )
    if (
        set(summary) != {
            "schema_version",
            "kind",
            "experiment_id",
            "planned_cells",
            "sealed_cells",
            "complete",
            "calibration_outcome",
            "actual_model_turns",
            "calibration_outcome_issued",
            "route_decision_issued",
            "stop_record",
            "profile_pairs",
            "limitations",
            "cells",
        }
        or summary.get("schema_version") != 1
        or summary.get("kind") != "sdk_routing_s1_live_summary"
        or summary.get("calibration_outcome") != measured_outcome
        or summary.get("actual_model_turns") != actual_turns
        or summary.get("planned_cells") != len(plan.cells)
        or summary.get("sealed_cells") != len(measurements)
        or summary.get("complete") is not complete
        or summary.get("stop_record") != stop_payload
        or summary.get("profile_pairs") != expected_pairs
        or summary.get("limitations")
        != [
            "one pair per small deterministic fixture",
            "public worker-visible Checks",
            "does not authorize profile ROUTE_* or B1 default adoption",
        ]
        or summary.get("cells") != expected_rows
    ):
        raise RoutingSuiteError("S1 live export summary differs from Measurements")
    if (export_root / "summary.md").read_bytes() != _live_summary_markdown(summary):
        raise RoutingSuiteError("S1 live export Markdown summary differs")
    files = {
        path.relative_to(export_root).as_posix(): path.read_bytes()
        for path in export_root.rglob("*")
        if path.is_file()
        and path.relative_to(export_root).as_posix() != "export-seal.json"
    }
    for relative, data in files.items():
        _r5_assert_export_safe(relative, data)
    expected_paths = {
        "execution-plan.json",
        "build-record.json",
        "preflight.json",
        "regression.json",
        "freeze-seal.json",
        "summary.json",
        "summary.md",
        "seals.json",
        *(
            _copied_manifest_path(relative)
            for relative in (
                "benchmarks/suites/sdk-routing-v1/suite.yaml",
                "benchmarks/suites/sdk-routing-v1/stages/s1-baseline.yaml",
                *(selection.path for selection in stage.fixture_manifests),
            )
        ),
        *expected_cell_paths,
    }
    if stop_path.is_file():
        expected_paths.add(f"terminal/{STOP_FILENAME}")
    if terminal_root.is_dir():
        expected_paths.update(
            path.relative_to(export_root).as_posix()
            for path in terminal_root.glob(f"*-{DISPATCH_MARKER_FILENAME}")
            if path.is_file()
        )
    if set(files) != expected_paths:
        raise RoutingSuiteError("S1 live export file set differs from the frozen contract")
    value = _aggregate_export_sha256(files)
    if value != export_seal.get("export_sha256") or len(files) != export_seal.get(
        "file_count"
    ):
        raise RoutingSuiteError("S1 live export aggregate seal differs")
    return {
        "experiment_id": plan.experiment_id,
        "calibration_outcome": measured_outcome,
        "file_count": len(files),
        "export_sha256": value,
    }


def _s2_posthoc_results(
    root: Path,
    measurements: list[Measurement],
) -> dict[str, dict[str, object]]:
    values: dict[str, dict[str, object]] = {}
    for measurement in measurements:
        path = (
            root
            / "cells"
            / measurement.identity.cell_id
            / "judge"
            / "posthoc"
            / "result.json"
        )
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RoutingSuiteError("S2 post-hoc result is missing or invalid") from exc
        if not isinstance(value, dict):
            raise RoutingSuiteError("S2 post-hoc result must be an object")
        values[measurement.identity.cell_id] = value
    return values


def _load_verified_s2_export(
    export_root: Path,
) -> tuple[
    ExecutionPlan,
    list[Measurement],
    dict[str, dict[str, object]],
    dict[str, Any],
]:
    """Load an S2 export only after its complete aggregate seal verifies."""

    export_root = export_root.resolve()
    verified = verify_routing_s2_live_export(export_root)
    plan = ExecutionPlan.model_validate_json(
        (export_root / "execution-plan.json").read_bytes()
    )
    seals = json.loads((export_root / "seals.json").read_text(encoding="utf-8"))
    entries = seals.get("entries")
    if not isinstance(entries, list):
        raise RoutingSuiteError("S2 initial export seal index is invalid")
    measurements = [
        Measurement.model_validate_json(
            (export_root / str(entry["measurement_path"])).read_bytes()
        )
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("measurement_path"), str)
    ]
    if len(measurements) != len(entries):
        raise RoutingSuiteError("S2 initial export Measurement index is invalid")
    return plan, measurements, _s2_posthoc_results(export_root, measurements), verified


def _verified_s2_initial_export(
    *, plan: ExecutionPlan, state: dict[str, Any]
) -> tuple[
    ExecutionPlan,
    list[Measurement],
    dict[str, dict[str, object]],
    dict[str, Any],
]:
    """Reopen and bind the committed initial S2 export used by a reverse Plan."""

    root_value = state.get("initial_export_root")
    expected = plan.decision_policy.get("initial_export_identity")
    if not isinstance(root_value, str) or not isinstance(expected, dict):
        raise RoutingSuiteError("S2 reverse initial export binding is missing")
    initial_plan, measurements, posthoc, verified = _load_verified_s2_export(
        Path(root_value)
    )
    actual = {
        "experiment_id": initial_plan.experiment_id,
        "plan_fingerprint": initial_plan.plan_fingerprint,
        "export_sha256": str(verified["export_sha256"]),
        "stage_state": str(verified["stage_state"]),
        "source_commit": str(
            initial_plan.environment_fingerprint.get("source_commit", "")
        ),
    }
    if (
        actual != expected
        or initial_plan.decision_policy.get("execution_phase") == "reverse"
        or verified.get("stage_state") != "S2_EXPANSION_REQUIRED"
    ):
        raise RoutingSuiteError("S2 reverse initial export identity differs")
    return initial_plan, measurements, posthoc, verified


def _s2_summary_rows(measurements: list[Measurement]) -> list[dict[str, Any]]:
    return [
        {
            "cell_id": item.identity.cell_id,
            "fixture_id": item.identity.fixture_id,
            "variant_id": item.identity.variant_id,
            "execution_ordinal": item.identity.execution_ordinal,
            "outcome_state": item.outcome.state,
            "failure_kind": item.outcome.failure_kind,
            "check_success": item.outcome.check_success,
            "property_status": item.variant_metrics.values.get("property_status"),
            "checker_sha256": item.variant_metrics.values.get("checker_sha256"),
            "actual_model_turns": item.variant_metrics.values.get("actual_model_turns"),
            "token_usage_status": item.resource.token_usage.status.value,
            "token_usage": item.resource.token_usage.value,
            "model_active_seconds": item.variant_metrics.values.get(
                "model_active_seconds"
            ),
            "total_wall_clock_seconds": item.effort.total_wall_clock_seconds.value,
            "b1_retry_count": item.variant_metrics.values.get("b1_retry_count"),
            "b1_resume_count": item.variant_metrics.values.get("b1_resume_count"),
            "b1_intermediate_check_changed_result": item.variant_metrics.values.get(
                "b1_intermediate_check_changed_result"
            ),
            "b1_intermediate_check_changed_dispatch": item.variant_metrics.values.get(
                "b1_intermediate_check_changed_dispatch"
            ),
            "b1_repeatable_quality_regression": item.variant_metrics.values.get(
                "b1_repeatable_quality_regression"
            ),
            "dual_outcome_status": item.variant_metrics.values.get(
                "dual_outcome_status"
            ),
            "first_attempt_outcome": item.variant_metrics.values.get(
                "first_attempt_outcome"
            ),
            "full_orchestrated_outcome": item.variant_metrics.values.get(
                "full_orchestrated_outcome"
            ),
            "attempt_level_cost": item.variant_metrics.values.get(
                "attempt_level_cost"
            ),
        }
        for item in sorted(
            measurements,
            key=lambda value: value.identity.execution_ordinal,
        )
    ]


def export_routing_s2_live(*, state_root: Path, results_root: Path) -> dict[str, Any]:
    """Export a completed S2 Plan and its deterministic profile policy."""

    experiment_dir, plan, state = _load_live_plan(state_root)
    if _plan_stage_contract(plan)["stage_id"] != "s2-intermediate":
        raise RoutingSuiteError("S2 live export requires an S2 Plan")
    status = routing_s1_live_status(state_root)
    if status.get("complete") is not True:
        raise RoutingSuiteError("S2 live export requires every planned Cell sealed")
    measurements = [
        verify_sealed_cell(experiment_dir / "cells" / cell.cell_id)
        for cell in sorted(plan.cells, key=lambda value: value.execution_ordinal)
    ]
    posthoc_results = _s2_posthoc_results(experiment_dir, measurements)
    is_reverse = plan.decision_policy.get("execution_phase") == "reverse"
    policy_plan = plan
    policy_measurements = measurements
    policy_posthoc = posthoc_results
    additional_plans: tuple[ExecutionPlan, ...] = ()
    initial_export_root: Path | None = None
    initial_plan: ExecutionPlan | None = None
    if is_reverse:
        (
            initial_plan,
            initial_measurements,
            initial_posthoc,
            _,
        ) = _verified_s2_initial_export(plan=plan, state=state)
        initial_export_root = Path(state["initial_export_root"]).resolve()
        policy_plan = initial_plan
        additional_plans = (plan,)
        policy_measurements = [*initial_measurements, *measurements]
        policy_posthoc = {**initial_posthoc, **posthoc_results}
    policy = derive_s2_routing_policy(
        plan=policy_plan,
        additional_plans=additional_plans,
        measurements=policy_measurements,
        sealed_cell_ids={item.identity.cell_id for item in policy_measurements},
        posthoc_results=policy_posthoc,
    )
    if policy != status.get("routing_policy"):
        raise RoutingSuiteError("S2 status and routing policy derivation differ")
    summary = {
        "schema_version": 1,
        "kind": "sdk_routing_s2_live_summary",
        "experiment_id": plan.experiment_id,
        "stage_state": policy["stage_state"],
        "planned_cells": len(plan.cells),
        "sealed_cells": len(measurements),
        "complete": True,
        "actual_model_turns": status["actual_model_turns"],
        "remaining_b1_retry_resume_reserve": status[
            "remaining_b1_retry_resume_reserve"
        ],
        "route_decision_issued": status["route_decision_issued"],
        "global_b1_default_issued": False,
        "cells": _s2_summary_rows(measurements),
    }
    if is_reverse:
        assert initial_plan is not None
        summary.update(
            {
                "execution_phase": "reverse",
                "initial_experiment_id": initial_plan.experiment_id,
                "combined_actual_model_turns": status["combined_actual_model_turns"],
            }
        )
    export_root = results_root.resolve() / "sdk-routing-s2-v1" / plan.experiment_id
    if export_root.exists():
        raise RoutingSuiteError("S2 live export destination already exists")
    artifact_root = Path(state["artifact_root"]).resolve()
    files: dict[str, bytes] = {
        "execution-plan.json": (artifact_root / "execution-plan.json").read_bytes(),
        "build-record.json": (artifact_root / "build-record.json").read_bytes(),
        "preflight.json": (artifact_root / "preflight.json").read_bytes(),
        "regression.json": (artifact_root / "regression.json").read_bytes(),
        "freeze-seal.json": (artifact_root / "freeze-seal.json").read_bytes(),
        "summary.json": canonical_json_bytes(summary),
        "routing-policy-v1.json": canonical_json_bytes(policy),
    }
    for path in (artifact_root / "manifests" / "source").rglob("*"):
        if path.is_file():
            files[path.relative_to(artifact_root).as_posix()] = path.read_bytes()
    if is_reverse:
        assert initial_export_root is not None
        files["initial-export-binding.json"] = canonical_json_bytes(
            plan.decision_policy["initial_export_identity"]
        )
        for path in initial_export_root.rglob("*"):
            if path.is_file():
                relative = path.relative_to(initial_export_root).as_posix()
                files[f"initial-export/{relative}"] = path.read_bytes()
    seals: list[dict[str, object]] = []
    for cell, measurement in zip(
        sorted(plan.cells, key=lambda value: value.execution_ordinal),
        measurements,
        strict=True,
    ):
        cell_dir = experiment_dir / "cells" / cell.cell_id
        record = CellStateRecord.model_validate_json(
            (cell_dir / "cell-state.json").read_bytes()
        )
        if record.sealed_measurement_sha256 is None:
            raise RoutingSuiteError("sealed S2 Cell omitted its Measurement hash")
        prefix = f"cells/{cell.cell_id}"
        measurement_path = f"{prefix}/sealed/measurement.json"
        files[measurement_path] = (
            cell_dir / "sealed" / "measurement.json"
        ).read_bytes()
        for evidence in measurement.evidence:
            files[f"{prefix}/{evidence.path}"] = (cell_dir / evidence.path).read_bytes()
        claim = cell_dir / DISPATCH_MARKER_FILENAME
        if claim.is_file():
            files[f"terminal/{cell.cell_id}-{DISPATCH_MARKER_FILENAME}"] = claim.read_bytes()
        seals.append(
            {
                "cell_id": cell.cell_id,
                "fixture_id": cell.fixture_id,
                "variant_id": cell.variant_id,
                "measurement_path": measurement_path,
                "sealed_measurement_sha256": record.sealed_measurement_sha256,
            }
        )
    files["seals.json"] = canonical_json_bytes(
        {
            "schema_version": 1,
            "kind": "sdk_routing_s2_live_seals",
            "experiment_id": plan.experiment_id,
            "plan_fingerprint": plan.plan_fingerprint,
            "entries": seals,
        }
    )
    for relative, data in files.items():
        _r5_assert_export_safe(relative, data)
        atomic_write(export_root / relative, data)
    export_sha256 = _aggregate_export_sha256(files)
    atomic_write(
        export_root / "export-seal.json",
        canonical_json_bytes(
            {
                "schema_version": 1,
                "kind": "sdk_routing_s2_live_export_seal",
                "experiment_id": plan.experiment_id,
                "file_count": len(files),
                "export_sha256": export_sha256,
            }
        ),
    )
    verified = verify_routing_s2_live_export(export_root)
    return {
        "experiment_id": plan.experiment_id,
        "stage_state": policy["stage_state"],
        "results_root": str(export_root),
        "file_count": len(files),
        "export_sha256": verified["export_sha256"],
    }


def verify_routing_s2_live_export(export_root: Path) -> dict[str, Any]:
    """Verify an S2 live export using only its sealed bytes."""

    export_root = export_root.resolve()
    freeze = verify_routing_s1_live_freeze(export_root, require_exact_files=False)
    try:
        plan = ExecutionPlan.model_validate_json(
            (export_root / "execution-plan.json").read_bytes()
        )
        assert_plan_integrity(plan)
        summary = json.loads((export_root / "summary.json").read_text(encoding="utf-8"))
        policy = json.loads(
            (export_root / "routing-policy-v1.json").read_text(encoding="utf-8")
        )
        seals = json.loads((export_root / "seals.json").read_text(encoding="utf-8"))
        export_seal = json.loads(
            (export_root / "export-seal.json").read_text(encoding="utf-8")
        )
        from benchmark_runner.routing_suite import RoutingStageManifest

        stage = RoutingStageManifest.model_validate(
            yaml.safe_load(
                (
                    export_root
                    / _copied_manifest_path(
                        "benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml"
                    )
                ).read_bytes()
            )
        )
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        raise RoutingSuiteError("S2 live export metadata is missing or invalid") from exc
    contract = _plan_stage_contract(plan)
    is_reverse = plan.decision_policy.get("execution_phase") == "reverse"
    expected_policy_experiment_id = (
        plan.decision_policy.get("initial_export_identity", {}).get("experiment_id")
        if is_reverse
        else plan.experiment_id
    )
    if (
        contract["stage_id"] != "s2-intermediate"
        or freeze["experiment_id"] != plan.experiment_id
        or summary.get("experiment_id") != plan.experiment_id
        or policy.get("experiment_id") != expected_policy_experiment_id
        or seals.get("experiment_id") != plan.experiment_id
        or seals.get("plan_fingerprint") != plan.plan_fingerprint
        or export_seal.get("experiment_id") != plan.experiment_id
    ):
        raise RoutingSuiteError("S2 live export identities differ")
    entries = seals.get("entries")
    ordered = sorted(plan.cells, key=lambda value: value.execution_ordinal)
    if (
        not isinstance(entries, list)
        or [item.get("cell_id") for item in entries if isinstance(item, dict)]
        != [cell.cell_id for cell in ordered]
    ):
        raise RoutingSuiteError("S2 live export seal index differs")
    measurements: list[Measurement] = []
    expected_cell_paths: set[str] = set()
    for cell, entry in zip(ordered, entries, strict=True):
        if not isinstance(entry, dict):
            raise RoutingSuiteError("S2 live export seal entry is invalid")
        relative = entry.get("measurement_path")
        if not isinstance(relative, str):
            raise RoutingSuiteError("S2 live export Measurement path is invalid")
        path = (export_root / relative).resolve()
        if (
            not path.is_relative_to(export_root)
            or path.is_symlink()
            or not path.is_file()
        ):
            raise RoutingSuiteError("S2 live export Measurement path is unsafe")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != entry.get("sealed_measurement_sha256"):
            raise RoutingSuiteError("S2 live export Measurement seal differs")
        measurement = Measurement.model_validate_json(data)
        _assert_live_measurement_plan_binding(plan, cell, measurement)
        _assert_live_measurement_contract(
            cell,
            measurement,
            stage_id="s2-intermediate",
        )
        expected_cell_paths.add(relative)
        cell_root = path.parents[1]
        for evidence in measurement.evidence:
            evidence_path = (cell_root / evidence.path).resolve()
            if (
                not evidence_path.is_relative_to(cell_root)
                or evidence_path.is_symlink()
                or not evidence_path.is_file()
            ):
                raise RoutingSuiteError("S2 live export Evidence path is unsafe")
            evidence_data = evidence_path.read_bytes()
            if (
                len(evidence_data) != evidence.size
                or hashlib.sha256(evidence_data).hexdigest() != evidence.sha256
            ):
                raise RoutingSuiteError("S2 live export Evidence hash differs")
            expected_cell_paths.add(f"cells/{cell.cell_id}/{evidence.path}")
        measurements.append(measurement)
    posthoc_results = _s2_posthoc_results(export_root, measurements)
    policy_plan = plan
    policy_measurements = measurements
    policy_posthoc = posthoc_results
    additional_plans: tuple[ExecutionPlan, ...] = ()
    nested_paths: set[str] = set()
    initial_plan: ExecutionPlan | None = None
    if is_reverse:
        initial_root = export_root / "initial-export"
        (
            initial_plan,
            initial_measurements,
            initial_posthoc,
            initial_verified,
        ) = _load_verified_s2_export(initial_root)
        try:
            binding = json.loads(
                (export_root / "initial-export-binding.json").read_text(
                    encoding="utf-8"
                )
            )
        except (OSError, json.JSONDecodeError) as exc:
            raise RoutingSuiteError("S2 reverse export binding is invalid") from exc
        actual_binding = {
            "experiment_id": initial_plan.experiment_id,
            "plan_fingerprint": initial_plan.plan_fingerprint,
            "export_sha256": str(initial_verified["export_sha256"]),
            "stage_state": str(initial_verified["stage_state"]),
            "source_commit": str(
                initial_plan.environment_fingerprint.get("source_commit", "")
            ),
        }
        if (
            binding != actual_binding
            or binding != plan.decision_policy.get("initial_export_identity")
            or initial_verified.get("stage_state") != "S2_EXPANSION_REQUIRED"
        ):
            raise RoutingSuiteError("S2 reverse export binding differs")
        policy_plan = initial_plan
        additional_plans = (plan,)
        policy_measurements = [*initial_measurements, *measurements]
        policy_posthoc = {**initial_posthoc, **posthoc_results}
        nested_paths = {
            f"initial-export/{path.relative_to(initial_root).as_posix()}"
            for path in initial_root.rglob("*")
            if path.is_file()
        }
    derived = derive_s2_routing_policy(
        plan=policy_plan,
        additional_plans=additional_plans,
        measurements=policy_measurements,
        sealed_cell_ids={item.identity.cell_id for item in policy_measurements},
        posthoc_results=policy_posthoc,
    )
    expected_summary = {
        "schema_version": 1,
        "kind": "sdk_routing_s2_live_summary",
        "experiment_id": plan.experiment_id,
        "stage_state": derived["stage_state"],
        "planned_cells": len(plan.cells),
        "sealed_cells": len(measurements),
        "complete": True,
        "actual_model_turns": sum(
            item.variant_metrics.values["actual_model_turns"]
            for item in measurements
        ),
        "remaining_b1_retry_resume_reserve": remaining_b1_retry_resume_reserve(
            measurements
        ),
        "route_decision_issued": any(
            item.get("route_issued") is True
            for item in derived["profiles"].values()
        ),
        "global_b1_default_issued": False,
        "cells": _s2_summary_rows(measurements),
    }
    if is_reverse:
        assert initial_plan is not None
        expected_summary.update(
            {
                "execution_phase": "reverse",
                "initial_experiment_id": initial_plan.experiment_id,
                "combined_actual_model_turns": sum(
                    item.variant_metrics.values["actual_model_turns"]
                    for item in policy_measurements
                ),
            }
        )
    if policy != derived or summary != expected_summary:
        raise RoutingSuiteError("S2 live export policy or summary differs")
    files = {
        path.relative_to(export_root).as_posix(): path.read_bytes()
        for path in export_root.rglob("*")
        if path.is_file()
        and path.relative_to(export_root).as_posix() != "export-seal.json"
    }
    for relative, data in files.items():
        _r5_assert_export_safe(relative, data)
    expected_paths = {
        "execution-plan.json",
        "build-record.json",
        "preflight.json",
        "regression.json",
        "freeze-seal.json",
        "summary.json",
        "routing-policy-v1.json",
        "seals.json",
        _copied_manifest_path("benchmarks/suites/sdk-routing-v1/suite.yaml"),
        _copied_manifest_path(
            "benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml"
        ),
        *(_copied_manifest_path(item.path) for item in stage.fixture_manifests),
        *expected_cell_paths,
        *(
            f"terminal/{cell.cell_id}-{DISPATCH_MARKER_FILENAME}"
            for cell in ordered
        ),
        *nested_paths,
    }
    if is_reverse:
        expected_paths.add("initial-export-binding.json")
    if set(files) != expected_paths:
        raise RoutingSuiteError("S2 live export file set differs")
    value = _aggregate_export_sha256(files)
    if (
        value != export_seal.get("export_sha256")
        or len(files) != export_seal.get("file_count")
    ):
        raise RoutingSuiteError("S2 live export aggregate seal differs")
    return {
        "experiment_id": plan.experiment_id,
        "stage_state": derived["stage_state"],
        "file_count": len(files),
        "export_sha256": value,
    }


# Stage-generic public names. The S1 names remain stable for frozen callers.
create_routing_live_candidate = create_routing_s1_live_candidate
verify_routing_live_freeze = verify_routing_s1_live_freeze
routing_live_status = routing_s1_live_status
run_next_routing_live_cell = run_next_routing_s1_live_cell
