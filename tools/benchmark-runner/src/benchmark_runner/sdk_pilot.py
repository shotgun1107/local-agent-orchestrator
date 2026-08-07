"""Reproducible four-Cell live pilot for the SDK-controlled comparison."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from benchmark_runner.adapter import B1AdapterConfig, B1SequentialAdapter, CellContext
from benchmark_runner.contract import (
    ArtifactIdentity,
    CellLifecycleState,
    CellStateRecord,
    ExecutionPlan,
    FixtureIdentity,
    Measurement,
    PlannedCell,
    present_api_key_environment_names,
    utc_now,
)
from benchmark_runner.plan import build_sdk_controlled_plan
from benchmark_runner.runner import (
    _r5_assert_export_safe,
    _source_tree_sha256,
    atomic_write,
    canonical_json_bytes,
    verify_sealed_cell,
)
from benchmark_runner.sdk_baselines import SdkBaselineAdapter, SdkBaselineConfig
from benchmark_runner.sdk_cells import (
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
    CodexSdkRuntime,
    WorkerContract,
)
from benchmark_runner.workspace import FixtureRestorer, load_frozen_manifest, sha256_file


PILOT_VARIANTS = ("c0", "c1", "c2", "b1")
MANIFEST_RELATIVE = "benchmarks/manifests/sdk-controlled-pilot-v1.yaml"
B1_FINGERPRINT_INPUTS = (
    "pyproject.toml",
    "src/orchestrator",
    "schemas",
    "templates",
)


def _git(repository_root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repository_root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _git_executable() -> Path:
    executable = shutil.which("git")
    if executable is None:
        raise RuntimeError("Git executable was not found")
    return Path(executable).resolve()


def _runtime_profile_path() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "local-agent-orchestrator" / "runtime-profiles.yaml"


def _assert_runtime_profile(path: Path) -> str:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        profile = payload["profiles"]["local_default"]
    except (OSError, TypeError, KeyError, yaml.YAMLError) as exc:
        raise RuntimeError("local_default runtime profile is missing or invalid") from exc
    expected = {
        "runtime": "codex",
        "model": PINNED_MODEL,
        "auth_method": "chatgpt",
        "reasoning_effort": PINNED_REASONING_EFFORT,
    }
    if profile != expected:
        raise RuntimeError("local_default runtime profile differs from the pilot controls")
    return sha256_file(path)


def _assert_sdk_version() -> None:
    try:
        import openai_codex
    except ImportError as exc:
        raise RuntimeError("openai-codex is not installed") from exc
    if getattr(openai_codex, "__version__", None) != PINNED_SDK_VERSION:
        raise RuntimeError(f"pilot requires openai-codex=={PINNED_SDK_VERSION}")


def _worker_contract() -> WorkerContract:
    from orchestrator.worker import (
        render_worker_prompt,
        result_schema,
        task_semantics_sha256,
        validate_result,
    )

    return WorkerContract(
        render_prompt=render_worker_prompt,
        result_schema=result_schema,
        validate_result=lambda value: validate_result(value).model_dump(mode="json"),
        semantics_sha256=task_semantics_sha256,
    )


def _task_envelopes(variant: str, workspace: Path) -> tuple[object, ...]:
    from orchestrator.contract import RunSpec
    from orchestrator.worker import build_oneshot_envelope, build_task_envelope

    spec = RunSpec.model_validate(
        yaml.safe_load((workspace / "benchmark-run.yaml").read_text(encoding="utf-8"))
    )
    if variant == "c0":
        return (
            build_oneshot_envelope(
                spec,
                run_id="pilot-c0",
                task_id="pilot-c0-oneshot",
                attempt_id="pilot-c0-attempt-1",
                requirements_version=1,
                timeout_seconds=900,
                remaining_attempts=1,
            ),
        )
    return tuple(
        build_task_envelope(
            task,
            run_id=f"pilot-{variant}",
            task_id=f"pilot-{variant}-{task.key.lower()}",
            attempt_id=f"pilot-{variant}-{task.key.lower()}-attempt-1",
            requirements_version=1,
            timeout_seconds=900,
            remaining_attempts=1,
        )
        for task in spec.tasks
    )


def _adapter(
    *,
    repository_root: Path,
    experiment_dir: Path,
    cell: PlannedCell,
    workspace: Path,
    benchmark_python: Path,
    max_model_turns: int | None = None,
):
    if cell.variant_id in {"c0", "c1", "c2"}:
        return SdkBaselineAdapter(
            SdkBaselineConfig(
                variant_id=cell.variant_id,  # type: ignore[arg-type]
                tasks=_task_envelopes(cell.variant_id, workspace),
                contract=_worker_contract(),
                runtime=CodexSdkRuntime(workspace),
            )
        )
    if cell.variant_id == "b1":
        return B1SequentialAdapter(
            B1AdapterConfig(
                command_prefix=(str(benchmark_python), "-P", "-m", "orchestrator"),
                project=workspace,
                run_spec=workspace / "benchmark-run.yaml",
                state_root=experiment_dir / "cells" / cell.cell_id / "variant-state",
                schema_root=repository_root / "stages" / "b1-sequential" / "schemas" / "v1",
                python_path=repository_root / "stages" / "b1-sequential" / "src",
                invocation_cwd=repository_root / "stages" / "b1-sequential" / "src",
                max_model_turns=max_model_turns,
                runtime="codex",
                timeout_seconds=2_000,
            )
        )
    raise RuntimeError(f"unsupported pilot variant: {cell.variant_id}")


def _state_metadata_path(state_root: Path) -> Path:
    return state_root.resolve() / "pilot-state.json"


def _load_state(state_root: Path) -> dict[str, Any]:
    try:
        payload = json.loads(_state_metadata_path(state_root).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("pilot state metadata is missing or invalid") from exc
    return payload


def _load_plan(state_root: Path) -> tuple[Path, ExecutionPlan, dict[str, Any]]:
    state = _load_state(state_root)
    experiment_dir = state_root.resolve() / str(state["experiment_id"])
    plan = ExecutionPlan.model_validate_json(
        (experiment_dir / "execution-plan.json").read_bytes()
    )
    if plan.experiment_id != state["experiment_id"]:
        raise RuntimeError("pilot state and Execution Plan identity differ")
    return experiment_dir, plan, state


def create_sdk_pilot(
    *,
    repository_root: Path,
    state_root: Path,
    artifact_root: Path,
    benchmark_python: Path,
    revision: int = 1,
    created_at: datetime | None = None,
) -> dict[str, Any]:
    """Freeze a clean source revision and prove all four adapters without a turn."""

    repository_root = repository_root.resolve()
    state_root = state_root.resolve()
    artifact_root = artifact_root.resolve()
    if present_api_key_environment_names():
        raise RuntimeError("API key environment is present; ChatGPT pilot fails closed")
    if _git(repository_root, "status", "--porcelain"):
        raise RuntimeError("pilot creation requires a clean Git worktree")
    source_commit = _git(repository_root, "rev-parse", "HEAD")
    _assert_sdk_version()
    profile_path = _runtime_profile_path()
    profile_sha256 = _assert_runtime_profile(profile_path)
    manifest_path = repository_root / MANIFEST_RELATIVE
    manifest = load_frozen_manifest(manifest_path)
    if manifest.variants != list(PILOT_VARIANTS) or manifest.repetitions != 1:
        raise RuntimeError("pilot manifest does not declare the exact four-Cell ladder")
    if manifest.model != {
        "allowed": PINNED_MODEL,
        "auth_method": "chatgpt",
        "reasoning_effort": PINNED_REASONING_EFFORT,
        "sdk": f"openai-codex=={PINNED_SDK_VERSION}",
        "approval_mode": PINNED_APPROVAL_MODE,
        "sandbox": PINNED_SANDBOX,
    }:
        raise RuntimeError("pilot manifest model controls differ")
    fixture = next(
        (item for item in manifest.fixtures if item.id == "sequential-code-change"),
        None,
    )
    if fixture is None or len(manifest.fixtures) != 1:
        raise RuntimeError("pilot requires only sequential-code-change")
    cells = [
        PlannedCell(
            cell_id=f"cell_pilot_{variant}",
            block_id="block_pilot",
            fixture_id=fixture.id,
            repetition=1,
            variant_id=variant,
            execution_ordinal=index,
        )
        for index, variant in enumerate(PILOT_VARIANTS, start=1)
    ]
    runner_sha256 = runner_source_sha256()
    b1_root = repository_root / "stages" / "b1-sequential"
    b1_sha256 = _source_tree_sha256(b1_root, B1_FINGERPRINT_INPUTS)
    version = f"0.1.0@{source_commit}"
    plan = build_sdk_controlled_plan(
        source_manifest_path=MANIFEST_RELATIVE,
        source_manifest_sha256=sha256_file(manifest_path),
        fixtures=[
            FixtureIdentity(
                fixture_id=fixture.id,
                source_commit=fixture.commit,
                git_tree=fixture.git_tree,
            )
        ],
        runner=ArtifactIdentity(
            artifact_id="benchmark-runner",
            version=version,
            sha256=runner_sha256,
        ),
        variants=[
            ArtifactIdentity(
                artifact_id=variant,
                version=version,
                sha256=b1_sha256 if variant == "b1" else runner_sha256,
            )
            for variant in PILOT_VARIANTS
        ],
        cells=cells,
        baseline_variant="c2",
        candidate_variants=["b1"],
        decision_policy={
            "track": "exploratory_pilot",
            "confirmatory": False,
            "required_cells": 4,
            "all_cells_must_seal": True,
        },
        environment_fingerprint={
            "python": platform.python_version(),
            "sdk": f"openai-codex=={PINNED_SDK_VERSION}",
            "model": PINNED_MODEL,
            "reasoning_effort": PINNED_REASONING_EFFORT,
            "approval_mode": PINNED_APPROVAL_MODE,
            "sandbox": PINNED_SANDBOX,
            "auth_method": "chatgpt",
            "runtime_profile_sha256": profile_sha256,
            "source_commit": source_commit,
        },
        created_at=created_at or utc_now(),
        revision=revision,
        seed=0,
        track="sdk_controlled_live_pilot",
        planned_actual_model_turns=None,
    )
    if state_root.exists():
        raise RuntimeError("pilot state root already exists")
    state_root.mkdir(parents=True)
    experiment_dir = initialize_sdk_experiment(state_root, plan)
    if artifact_root.exists():
        raise RuntimeError("pilot artifact root already exists")
    artifact_root.mkdir(parents=True)
    atomic_write(artifact_root / "execution-plan.json", canonical_json_bytes(plan))
    atomic_write(
        artifact_root / "build-record.json",
        canonical_json_bytes(
            {
                "schema_version": 1,
                "kind": "sdk_controlled_live_pilot_source_freeze",
                "source_commit": source_commit,
                "manifest": MANIFEST_RELATIVE,
                "manifest_sha256": sha256_file(manifest_path),
                "runner_source_sha256": runner_sha256,
                "b1_source_sha256": b1_sha256,
                "runtime_profile_sha256": profile_sha256,
                "actual_model_turns": 0,
            }
        ),
    )
    restorer = FixtureRestorer(repository_root, str(_git_executable()))
    preflights: list[dict[str, object]] = []
    for cell in plan.cells:
        prepared = restorer.restore(
            fixture,
            experiment_dir / "cells" / cell.cell_id / "workspace",
        )
        adapter = _adapter(
            repository_root=repository_root,
            experiment_dir=experiment_dir,
            cell=cell,
            workspace=prepared.workspace,
            benchmark_python=benchmark_python,
        )
        result = adapter.preflight(CellContext(plan.experiment_id, cell.cell_id))
        runtime = getattr(getattr(adapter, "config", None), "runtime", None)
        evidence = getattr(runtime, "preflight_evidence", None)
        if evidence is None:
            evidence = getattr(adapter, "preflight_evidence", None)
        close = getattr(runtime, "close", None)
        if callable(close):
            close()
        if not result.ok or not evidence:
            raise RuntimeError(f"pilot preflight failed for {cell.cell_id}: {result.detail}")
        preflights.append(
            {
                "cell_id": cell.cell_id,
                "variant_id": cell.variant_id,
                "ok": True,
                "account_type": evidence.get("account_type"),
                "sdk_version": evidence.get("sdk_version"),
                "actual_model_turns": evidence.get("actual_model_turns"),
            }
        )
    atomic_write(
        artifact_root / "preflight.json",
        canonical_json_bytes(
            {
                "schema_version": 1,
                "experiment_id": plan.experiment_id,
                "plan_fingerprint": plan.plan_fingerprint,
                "api_key_environment_names_present": [],
                "actual_model_turns": 0,
                "cells": preflights,
            }
        ),
    )
    state = {
        "schema_version": 1,
        "repository_root": str(repository_root),
        "artifact_root": str(artifact_root),
        "experiment_id": plan.experiment_id,
        "source_commit": source_commit,
        "runtime_profile_sha256": profile_sha256,
    }
    atomic_write(_state_metadata_path(state_root), canonical_json_bytes(state))
    return {
        "experiment_id": plan.experiment_id,
        "state_root": str(state_root),
        "artifact_root": str(artifact_root),
        "preflight_cells": len(preflights),
        "actual_model_turns": 0,
    }


def run_next_sdk_pilot_cell(
    *,
    state_root: Path,
    benchmark_python: Path,
    confirm_model_usage: bool,
) -> dict[str, Any]:
    if not confirm_model_usage:
        raise RuntimeError("live pilot requires explicit model-usage confirmation")
    if present_api_key_environment_names():
        raise RuntimeError("API key environment is present; ChatGPT pilot fails closed")
    experiment_dir, plan, state = _load_plan(state_root)
    repository_root = Path(state["repository_root"]).resolve()
    if _git(repository_root, "rev-parse", "HEAD") != state["source_commit"]:
        raise RuntimeError("pilot source commit changed")
    if runner_source_sha256() != plan.runner.sha256:
        raise RuntimeError("pilot Runner source changed")
    if _assert_runtime_profile(_runtime_profile_path()) != state["runtime_profile_sha256"]:
        raise RuntimeError("pilot runtime profile changed")
    next_cell = next(
        (
            cell
            for cell in sorted(plan.cells, key=lambda item: item.execution_ordinal)
            if not (experiment_dir / "cells" / cell.cell_id / "cell-state.json").is_file()
        ),
        None,
    )
    if next_cell is None:
        raise RuntimeError("pilot has no remaining Cell")
    manifest = load_frozen_manifest(repository_root / MANIFEST_RELATIVE)
    fixture = next(item for item in manifest.fixtures if item.id == next_cell.fixture_id)
    prepared = FixtureRestorer(repository_root, str(_git_executable())).open_existing(
        fixture,
        experiment_dir / "cells" / next_cell.cell_id / "workspace",
        require_clean=True,
    )
    adapter = _adapter(
        repository_root=repository_root,
        experiment_dir=experiment_dir,
        cell=next_cell,
        workspace=prepared.workspace,
        benchmark_python=benchmark_python,
    )
    result = run_sdk_live_cell(
        experiment_dir=experiment_dir,
        plan=plan,
        planned_cell=next_cell,
        prepared=prepared,
        adapter=adapter,
        benchmark_python=benchmark_python,
        git_executable=_git_executable(),
    )
    return result.model_dump(mode="json")


def sdk_pilot_status(state_root: Path) -> dict[str, Any]:
    experiment_dir, plan, _ = _load_plan(state_root)
    cells: list[dict[str, object]] = []
    sealed = 0
    for cell in sorted(plan.cells, key=lambda item: item.execution_ordinal):
        path = experiment_dir / "cells" / cell.cell_id / "cell-state.json"
        if not path.is_file():
            cells.append(
                {"cell_id": cell.cell_id, "variant_id": cell.variant_id, "state": "PLANNED"}
            )
            continue
        record = CellStateRecord.model_validate_json(path.read_bytes())
        if record.state is CellLifecycleState.SEALED:
            verify_sealed_cell(path.parent)
            sealed += 1
        cells.append(
            {
                "cell_id": cell.cell_id,
                "variant_id": cell.variant_id,
                "state": record.state.value,
                "outcome_state": record.outcome_state,
            }
        )
    return {
        "experiment_id": plan.experiment_id,
        "sealed_cells": sealed,
        "planned_cells": len(plan.cells),
        "complete": sealed == len(plan.cells),
        "cells": cells,
    }


def _summary(plan: ExecutionPlan, measurements: list[Measurement]) -> dict[str, Any]:
    rows = []
    for measurement in sorted(
        measurements, key=lambda item: item.identity.execution_ordinal
    ):
        rows.append(
            {
                "cell_id": measurement.identity.cell_id,
                "variant_id": measurement.identity.variant_id,
                "outcome_state": measurement.outcome.state,
                "check_success": measurement.outcome.check_success,
                "session_count": measurement.resource.session_count.value,
                "turn_count": measurement.resource.turn_count.value,
                "token_usage_status": measurement.resource.token_usage.status.value,
                "token_usage": measurement.resource.token_usage.value,
                "model_active_seconds": measurement.variant_metrics.values.get(
                    "model_active_seconds"
                ),
                "total_wall_clock_seconds": measurement.effort.total_wall_clock_seconds.value,
                "actual_model_turns": measurement.variant_metrics.values[
                    "actual_model_turns"
                ],
            }
        )
    return {
        "schema_version": 1,
        "kind": "sdk_controlled_live_pilot_summary",
        "experiment_id": plan.experiment_id,
        "confirmatory": False,
        "verdict": "PILOT_PASS" if all(row["check_success"] for row in rows) else "PILOT_FAIL",
        "cells": rows,
    }


def _summary_markdown(summary: dict[str, Any]) -> bytes:
    lines = [
        "# SDK 통제 4-Cell live pilot",
        "",
        f"- Experiment: `{summary['experiment_id']}`",
        f"- 판정: `{summary['verdict']}`",
        "- 성격: confirmatory 결과가 아닌 실제 연결 사전시험",
        "",
        "| Variant | Outcome | Judge | Sessions | Turns | Tokens | Wall seconds |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary["cells"]:
        token = row["token_usage"]
        token_text = (
            str(token["total_tokens"])
            if isinstance(token, dict) and "total_tokens" in token
            else row["token_usage_status"]
        )
        lines.append(
            f"| {row['variant_id']} | {row['outcome_state']} | "
            f"{str(row['check_success']).lower()} | {row['session_count']} | "
            f"{row['turn_count']} | {token_text} | "
            f"{float(row['total_wall_clock_seconds']):.3f} |"
        )
    lines.extend(["", "이 결과는 본 비교의 채택 판정에 합산하지 않는다.", ""])
    return "\n".join(lines).encode("utf-8")


def export_sdk_pilot(*, state_root: Path, results_root: Path) -> dict[str, Any]:
    experiment_dir, plan, _ = _load_plan(state_root)
    status = sdk_pilot_status(state_root)
    if status["complete"] is not True:
        raise RuntimeError("pilot export requires four sealed Cells")
    measurements = [
        verify_sealed_cell(experiment_dir / "cells" / cell.cell_id)
        for cell in plan.cells
    ]
    summary = _summary(plan, measurements)
    export_root = results_root.resolve() / "sdk-controlled-pilot" / plan.experiment_id
    if export_root.exists():
        raise RuntimeError("pilot export destination already exists")
    files: dict[str, bytes] = {
        "execution-plan.json": canonical_json_bytes(plan),
        "summary.json": canonical_json_bytes(summary),
        "summary.md": _summary_markdown(summary),
    }
    seals = []
    for cell, measurement in zip(plan.cells, measurements, strict=True):
        cell_dir = experiment_dir / "cells" / cell.cell_id
        record = CellStateRecord.model_validate_json(
            (cell_dir / "cell-state.json").read_bytes()
        )
        if record.sealed_measurement_sha256 is None:
            raise RuntimeError("sealed pilot Cell omitted its Measurement hash")
        prefix = f"cells/{cell.cell_id}"
        measurement_relative = f"{prefix}/sealed/measurement.json"
        files[measurement_relative] = (
            cell_dir / "sealed" / "measurement.json"
        ).read_bytes()
        for evidence in measurement.evidence:
            files[f"{prefix}/{evidence.path}"] = (cell_dir / evidence.path).read_bytes()
        seals.append(
            {
                "cell_id": cell.cell_id,
                "variant_id": cell.variant_id,
                "measurement_path": measurement_relative,
                "sealed_measurement_sha256": record.sealed_measurement_sha256,
            }
        )
    files["seals.json"] = canonical_json_bytes(
        {
            "schema_version": 1,
            "experiment_id": plan.experiment_id,
            "plan_fingerprint": plan.plan_fingerprint,
            "entries": seals,
        }
    )
    for relative, data in files.items():
        _r5_assert_export_safe(relative, data)
        atomic_write(export_root / relative, data)
    digest = hashlib.sha256()
    for relative in sorted(files):
        data = files[relative]
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(hashlib.sha256(data).digest())
    export_sha256 = digest.hexdigest()
    atomic_write(
        export_root / "export-seal.json",
        canonical_json_bytes(
            {
                "schema_version": 1,
                "experiment_id": plan.experiment_id,
                "file_count": len(files),
                "export_sha256": export_sha256,
            }
        ),
    )
    verification = verify_sdk_pilot_export(export_root)
    if verification["export_sha256"] != export_sha256:
        raise RuntimeError("independent pilot export verification disagreed")
    return {
        "experiment_id": plan.experiment_id,
        "verdict": summary["verdict"],
        "results_root": str(export_root),
        "file_count": len(files),
        "export_sha256": export_sha256,
    }


def verify_sdk_pilot_export(export_root: Path) -> dict[str, Any]:
    export_root = export_root.resolve()
    try:
        plan = ExecutionPlan.model_validate_json(
            (export_root / "execution-plan.json").read_bytes()
        )
        seals = json.loads((export_root / "seals.json").read_text(encoding="utf-8"))
        export_seal = json.loads(
            (export_root / "export-seal.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError("pilot export metadata is missing or invalid") from exc
    if (
        plan.experiment_id != seals.get("experiment_id")
        or plan.experiment_id != export_seal.get("experiment_id")
        or plan.plan_fingerprint != seals.get("plan_fingerprint")
    ):
        raise RuntimeError("pilot export identities differ")
    expected_cells = {cell.cell_id for cell in plan.cells}
    entries = seals.get("entries")
    if not isinstance(entries, list) or {
        entry.get("cell_id") for entry in entries if isinstance(entry, dict)
    } != expected_cells:
        raise RuntimeError("pilot export seal index differs from the Plan")
    for entry in entries:
        if not isinstance(entry, dict):
            raise RuntimeError("pilot export seal entry is invalid")
        relative = entry.get("measurement_path")
        if not isinstance(relative, str):
            raise RuntimeError("pilot export Measurement path is invalid")
        measurement_path = (export_root / relative).resolve()
        if not measurement_path.is_relative_to(export_root) or not measurement_path.is_file():
            raise RuntimeError("pilot export Measurement is missing or unsafe")
        data = measurement_path.read_bytes()
        if hashlib.sha256(data).hexdigest() != entry.get("sealed_measurement_sha256"):
            raise RuntimeError("pilot export Measurement seal differs")
        measurement = Measurement.model_validate_json(data)
        if measurement.identity.cell_id != entry.get("cell_id"):
            raise RuntimeError("pilot export Measurement identity differs")
        cell_root = measurement_path.parents[1]
        for evidence in measurement.evidence:
            path = (cell_root / evidence.path).resolve()
            if not path.is_relative_to(cell_root) or not path.is_file():
                raise RuntimeError("pilot export Evidence is missing or unsafe")
            evidence_data = path.read_bytes()
            if (
                len(evidence_data) != evidence.size
                or hashlib.sha256(evidence_data).hexdigest() != evidence.sha256
            ):
                raise RuntimeError("pilot export Evidence hash differs")
    files = {
        path.relative_to(export_root).as_posix(): path.read_bytes()
        for path in export_root.rglob("*")
        if path.is_file() and path.name != "export-seal.json"
    }
    for relative, data in files.items():
        _r5_assert_export_safe(relative, data)
    digest = hashlib.sha256()
    for relative in sorted(files):
        data = files[relative]
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(hashlib.sha256(data).digest())
    value = digest.hexdigest()
    if value != export_seal.get("export_sha256") or len(files) != export_seal.get(
        "file_count"
    ):
        raise RuntimeError("pilot export aggregate seal differs")
    return {
        "experiment_id": plan.experiment_id,
        "file_count": len(files),
        "export_sha256": value,
    }
