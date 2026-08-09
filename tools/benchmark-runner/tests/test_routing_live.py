from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

import benchmark_runner.routing_live as routing_live
from benchmark_runner.contract import ArtifactIdentity, Measurement
from benchmark_runner.routing_live import (
    LIVE_TRACK,
    _aggregate_export_sha256,
    _artifact_files_without_seal,
    _calibration_outcome,
    _claim_cell_dispatch,
    _codex_sdk_runtime_identity,
    _copied_manifest_path,
    _assert_b1_module_origin,
    _assert_external_short_state_root,
    _assert_live_measurement_contract,
    create_routing_s1_live_candidate,
    export_routing_s1_live,
    routing_s1_live_status,
    run_next_routing_s1_live_cell,
    verify_routing_s1_live_freeze,
    verify_routing_s1_live_export,
)
from benchmark_runner.routing_suite import (
    S1_EXPECTED_CELL_ORDER,
    RoutingSuiteError,
    build_routing_s1_live_plan,
)
from benchmark_runner.runner import atomic_write, canonical_json_bytes
from benchmark_runner.sdk_cells import runner_source_sha256


REPOSITORY_ROOT = Path(__file__).parents[3]
SUITE_PATH = REPOSITORY_ROOT / "benchmarks" / "suites" / "sdk-routing-v1" / "suite.yaml"
STAGE_PATH = SUITE_PATH.parent / "stages" / "s1-baseline.yaml"
PILOT_MEASUREMENT = (
    REPOSITORY_ROOT
    / "benchmarks"
    / "results"
    / "sdk-controlled-pilot"
    / "exp_20260807_a3046b4b_2"
    / "cells"
    / "cell_pilot_c2"
    / "sealed"
    / "measurement.json"
)


def _live_plan():
    runner_sha = runner_source_sha256()
    fixture_manifest_sha256 = {
        relative: hashlib.sha256((REPOSITORY_ROOT / relative).read_bytes()).hexdigest()
        for relative in (
            "benchmarks/manifests/b0-b1-frozen.yaml",
            "benchmarks/manifests/b0-b1-sequential-followup.yaml",
        )
    }
    return build_routing_s1_live_plan(
        repository_root=REPOSITORY_ROOT,
        suite_path=SUITE_PATH,
        stage_path=STAGE_PATH,
        runner=ArtifactIdentity(
            artifact_id="benchmark-runner",
            version="0.1.0@test-source",
            sha256=runner_sha,
        ),
        variants=[
            ArtifactIdentity(
                artifact_id="c2", version="0.1.0@test-source", sha256=runner_sha
            ),
            ArtifactIdentity(
                artifact_id="b1", version="0.1.0@test-source", sha256="b" * 64
            ),
        ],
        environment_fingerprint={
            "python": "3.12.10",
            "sdk": "openai-codex==0.144.4",
            "model": "gpt-5.6-terra",
            "reasoning_effort": "low",
            "approval_mode": "deny_all",
            "sandbox": "workspace_write",
            "auth_method": "chatgpt",
            "runtime_profile_sha256": "f" * 64,
            "source_commit": "test-source",
            "benchmark_python_path_sha256": "8" * 64,
            "benchmark_python_sha256": "e" * 64,
            "routing_controller_sha256": "d" * 64,
            "fixture_manifest_fingerprint": json.dumps(
                fixture_manifest_sha256, sort_keys=True, separators=(",", ":")
            ),
            "codex_sdk_runtime_sha256": "c" * 64,
            "git_version": "git version 2.54.0.windows.1",
            "git_sha256": "9" * 64,
            "git_executable_path_sha256": "7" * 64,
        },
        created_at=datetime(2026, 8, 7, tzinfo=timezone.utc),
    )


def _freeze_artifact(tmp_path: Path) -> tuple[Path, object]:
    plan = _live_plan()
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    atomic_write(artifact / "execution-plan.json", canonical_json_bytes(plan))
    for relative in (
        "benchmarks/suites/sdk-routing-v1/suite.yaml",
        "benchmarks/suites/sdk-routing-v1/stages/s1-baseline.yaml",
        "benchmarks/manifests/b0-b1-frozen.yaml",
        "benchmarks/manifests/b0-b1-sequential-followup.yaml",
    ):
        atomic_write(
            artifact / _copied_manifest_path(relative),
            (REPOSITORY_ROOT / relative).read_bytes(),
        )
    build = {
        "schema_version": 1,
        "kind": "sdk_routing_s1_live_source_freeze",
        "source_commit": "test-source",
        "suite_sha256": plan.decision_policy["suite_sha256"],
        "stage_sha256": plan.source_manifest.sha256,
        "runner_source_sha256": plan.runner.sha256,
        "b1_source_sha256": "b" * 64,
        "b1_schema_root": "stages/b1-sequential/schemas/v1",
        "command_prefix_contract": [
            "<sha256-bound-benchmark-python>",
            "-P",
            "-m",
            "orchestrator",
        ],
        "benchmark_python_path_sha256": "8" * 64,
        "benchmark_python_sha256": "e" * 64,
        "routing_controller_sha256": "d" * 64,
        "fixture_manifest_sha256": json.loads(
            plan.environment_fingerprint["fixture_manifest_fingerprint"]
        ),
        "fixture_manifest_fingerprint": plan.environment_fingerprint[
            "fixture_manifest_fingerprint"
        ],
        "b1_turn_cap_contract": "min(project_policy_8,remaining_global_12)",
        "codex_sdk_module_origin": "Lib/site-packages/openai_codex/__init__.py",
        "codex_sdk_runtime_sha256": "c" * 64,
        "b1_module_origin": "stages/b1-sequential/src/orchestrator/__init__.py",
        "runtime_profile_sha256": "f" * 64,
        "git_executable_path_sha256": "7" * 64,
        "git_version": "git version 2.54.0.windows.1",
        "git_sha256": "9" * 64,
        "independent_plan_build": {
            "separate_clean_checkout": True,
            "separate_process": True,
            "source_commit": "test-source",
            "plan_fingerprint": plan.plan_fingerprint,
            "identical": True,
        },
        "actual_model_turns": 0,
    }
    atomic_write(artifact / "build-record.json", canonical_json_bytes(build))
    semantics = {
        fixture.fixture_id: {"c2": ["a" * 64], "b1": ["a" * 64]}
        for fixture in plan.fixtures
    }
    cells = [
        {
            "cell_id": cell.cell_id,
            "fixture_id": cell.fixture_id,
            "variant_id": cell.variant_id,
            "ok": True,
            "account_type": "chatgpt",
            "sdk_version": "0.144.4",
            "api_key_environment_names_present": [],
            "actual_model_turns": 0,
        }
        for cell in plan.cells
    ]
    atomic_write(
        artifact / "preflight.json",
        canonical_json_bytes(
            {
                "schema_version": 1,
                "kind": "sdk_routing_s1_live_preflight",
                "experiment_id": plan.experiment_id,
                "plan_fingerprint": plan.plan_fingerprint,
                "api_key_environment_names_present": [],
                "actual_model_turns": 0,
                "task_semantics": semantics,
                "cells": cells,
            }
        ),
    )
    atomic_write(
        artifact / "regression.json",
        canonical_json_bytes(
            {
                "schema_version": 1,
                "status": "passed",
                "completed_at": "2026-08-07T00:00:00+00:00",
                "source_commit": "test-source",
                "python_version": "Python 3.12.10",
                "actual_model_turns": 0,
                "cases": [
                    {
                        "name": name,
                        "exit_code": 0,
                        "elapsed_seconds": 1.0,
                        "summary_line": "passed",
                    }
                    for name in (
                        "s0_gate",
                        "b1_retry_contracts",
                        "b1_full",
                        "runner_full",
                        "implementation_log_check",
                        "implementation_log_tests",
                    )
                ],
            }
        ),
    )
    files = _artifact_files_without_seal(artifact)
    atomic_write(
        artifact / "freeze-seal.json",
        canonical_json_bytes(
            {
                "schema_version": 1,
                "kind": "sdk_routing_s1_live_freeze_seal",
                "status": "frozen_before_first_cell",
                "experiment_id": plan.experiment_id,
                "plan_fingerprint": plan.plan_fingerprint,
                "planned_cells": 8,
                "planned_live_model_turns": 12,
                "actual_model_turns": 0,
                "file_count": len(files),
                "freeze_sha256": _aggregate_export_sha256(files),
            }
        ),
    )
    return artifact, plan


def _regression_record(source_commit: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "passed",
        "completed_at": "2026-08-07T00:00:00+00:00",
        "source_commit": source_commit,
        "python_version": "Python 3.12.10",
        "actual_model_turns": 0,
        "cases": [
            {
                "name": name,
                "exit_code": 0,
                "elapsed_seconds": 1.0,
                "summary_line": "passed",
            }
            for name in (
                "s0_gate",
                "b1_retry_contracts",
                "b1_full",
                "runner_full",
                "implementation_log_check",
                "implementation_log_tests",
            )
        ],
    }


def test_live_plan_requires_frozen_exact_contract() -> None:
    plan = _live_plan()
    assert [(cell.fixture_id, cell.variant_id) for cell in plan.cells] == S1_EXPECTED_CELL_ORDER
    assert [item.value for item in plan.plan_supplemented if item.field == "track"] == [
        LIVE_TRACK
    ]
    assert not [
        item for item in plan.plan_supplemented if item.field == "actual_model_turns"
    ]
    assert plan.decision_policy["planned_live_model_turns"] == 12
    assert plan.decision_policy["route_decision_allowed"] is False


def test_freeze_bundle_is_self_contained_and_plan_tampering_is_rejected(
    tmp_path: Path,
) -> None:
    artifact, plan = _freeze_artifact(tmp_path)
    verified = verify_routing_s1_live_freeze(artifact)
    assert verified["experiment_id"] == plan.experiment_id

    atomic_write(artifact / "unexpected.json", b"{}")
    with pytest.raises(RoutingSuiteError, match="file set differs"):
        verify_routing_s1_live_freeze(artifact)
    (artifact / "unexpected.json").unlink()

    payload = json.loads((artifact / "execution-plan.json").read_text(encoding="utf-8"))
    payload["decision_policy"]["route_decision_allowed"] = True
    atomic_write(artifact / "execution-plan.json", canonical_json_bytes(payload))
    files = _artifact_files_without_seal(artifact)
    seal = json.loads((artifact / "freeze-seal.json").read_text(encoding="utf-8"))
    seal["freeze_sha256"] = _aggregate_export_sha256(files)
    atomic_write(artifact / "freeze-seal.json", canonical_json_bytes(seal))
    with pytest.raises(RoutingSuiteError, match="metadata is missing or invalid"):
        verify_routing_s1_live_freeze(artifact)


def test_live_runner_requires_explicit_confirmation_before_state_access(tmp_path: Path) -> None:
    with pytest.raises(RoutingSuiteError, match="explicit model-usage confirmation"):
        run_next_routing_s1_live_cell(
            state_root=tmp_path / "missing",
            benchmark_python=Path(sys.executable),
            confirm_model_usage=False,
        )


def test_regression_record_and_external_state_root_fail_closed(tmp_path: Path) -> None:
    artifact, _ = _freeze_artifact(tmp_path)
    regression = json.loads((artifact / "regression.json").read_text(encoding="utf-8"))
    regression["cases"] = []
    atomic_write(artifact / "regression.json", canonical_json_bytes(regression))
    files = _artifact_files_without_seal(artifact)
    seal = json.loads((artifact / "freeze-seal.json").read_text(encoding="utf-8"))
    seal["freeze_sha256"] = _aggregate_export_sha256(files)
    atomic_write(artifact / "freeze-seal.json", canonical_json_bytes(seal))
    with pytest.raises(RoutingSuiteError, match="regression record does not qualify"):
        verify_routing_s1_live_freeze(artifact)

    with pytest.raises(RoutingSuiteError, match="short path outside"):
        _assert_external_short_state_root(REPOSITORY_ROOT, REPOSITORY_ROOT / "state")


def test_b1_module_origin_and_dispatch_claim_are_bound(tmp_path: Path) -> None:
    expected = _assert_b1_module_origin(REPOSITORY_ROOT, Path(sys.executable))
    assert expected == "stages/b1-sequential/src/orchestrator/__init__.py"
    experiment = tmp_path / "experiment"
    marker = _claim_cell_dispatch(experiment, "cell_example")
    assert marker.is_file()
    with pytest.raises(RoutingSuiteError, match="already has a durable dispatch claim"):
        _claim_cell_dispatch(experiment, "cell_example")


def test_installed_codex_sdk_runtime_identity_includes_bundled_cli() -> None:
    pytest.importorskip("openai_codex")
    pytest.importorskip("codex_cli_bin")
    origin, digest = _codex_sdk_runtime_identity()
    assert origin == "Lib/site-packages/openai_codex/__init__.py"
    assert len(digest) == 64


def test_candidate_create_and_confirm_true_dispatches_at_most_one_mocked_cell(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_commit = "a" * 40
    regression_path = tmp_path / "regression.json"
    atomic_write(regression_path, canonical_json_bytes(_regression_record(source_commit)))
    original_git_at = routing_live._git_at
    git_executable = routing_live._git_executable().resolve()
    git_sha256 = routing_live.sha256_file(git_executable)

    def fake_git_at(executable: Path, repository: Path, *arguments: str) -> str:
        if arguments == ("status", "--porcelain"):
            return ""
        if arguments == ("rev-parse", "HEAD"):
            return source_commit
        return original_git_at(executable, repository, *arguments)

    monkeypatch.setattr(routing_live, "_git_at", fake_git_at)
    monkeypatch.setattr(
        routing_live,
        "_git_identity",
        lambda: (git_executable, "git version 2.54.0.windows.1", git_sha256),
    )
    monkeypatch.setattr(
        routing_live,
        "_independent_live_plan_build",
        lambda **values: values["expected_plan"],
    )
    monkeypatch.setattr(routing_live, "_assert_sdk_version", lambda: None)
    monkeypatch.setattr(
        routing_live,
        "_codex_sdk_runtime_identity",
        lambda: ("Lib/site-packages/openai_codex/__init__.py", "c" * 64),
    )
    monkeypatch.setattr(routing_live, "_runtime_profile_path", lambda: tmp_path / "profile")
    monkeypatch.setattr(routing_live, "_assert_runtime_profile", lambda _: "f" * 64)
    monkeypatch.setattr(
        routing_live,
        "_assert_b1_module_origin",
        lambda *_: "stages/b1-sequential/src/orchestrator/__init__.py",
    )
    monkeypatch.setattr(
        routing_live,
        "_preflight_adapter",
        lambda **values: {
            "cell_id": values["cell"].cell_id,
            "fixture_id": values["cell"].fixture_id,
            "variant_id": values["cell"].variant_id,
            "ok": True,
            "account_type": "chatgpt",
            "sdk_version": "0.144.4",
            "api_key_environment_names_present": [],
            "actual_model_turns": 0,
        },
    )
    state_root = tmp_path / "state"
    artifact_root = tmp_path / "artifact"
    created = create_routing_s1_live_candidate(
        repository_root=REPOSITORY_ROOT,
        suite_path=SUITE_PATH,
        stage_path=STAGE_PATH,
        state_root=state_root,
        artifact_root=artifact_root,
        regression_record_path=regression_path,
        benchmark_python=Path(sys.executable),
        created_at=datetime(2026, 8, 7, tzinfo=timezone.utc),
    )
    assert created["preflight_cells"] == 8
    assert created["actual_model_turns"] == 0
    verify_routing_s1_live_freeze(artifact_root)
    experiment_dir, plan, state = routing_live._load_live_plan(state_root)
    b1_cell = plan.cells[1]
    b1_adapter = routing_live._adapter(
        repository_root=REPOSITORY_ROOT,
        experiment_dir=experiment_dir,
        cell=b1_cell,
        workspace=experiment_dir / "cells" / b1_cell.cell_id / "workspace",
        benchmark_python=Path(sys.executable),
        max_model_turns=8,
    )
    routing_live._assert_live_source_boundary(
        repository_root=REPOSITORY_ROOT,
        plan=plan,
        state=state,
        adapter=b1_adapter,
        benchmark_python=Path(sys.executable),
        remaining_model_turns=11,
    )
    assert b1_adapter.config.max_model_turns == 8

    calls: list[str] = []

    class FakeResult:
        def model_dump(self, *, mode: str):
            return {"cell_id": calls[-1], "mode": mode}

    def fake_live_cell(**values):
        calls.append(values["planned_cell"].cell_id)
        return FakeResult()

    monkeypatch.setattr(routing_live, "_adapter", lambda **_: object())
    monkeypatch.setattr(routing_live, "_assert_live_source_boundary", lambda **_: None)
    monkeypatch.setattr(routing_live, "run_sdk_live_cell", fake_live_cell)
    result = run_next_routing_s1_live_cell(
        state_root=state_root,
        benchmark_python=Path(sys.executable),
        confirm_model_usage=True,
    )
    assert result["cell_id"] == "cell_s1_code-change_1_c2"
    assert calls == ["cell_s1_code-change_1_c2"]
    with pytest.raises(RoutingSuiteError, match="status forbids another Cell"):
        run_next_routing_s1_live_cell(
            state_root=state_root,
            benchmark_python=Path(sys.executable),
            confirm_model_usage=True,
        )
    assert calls == ["cell_s1_code-change_1_c2"]
    status = routing_s1_live_status(state_root)
    assert status["calibration_outcome"] == "CALIBRATION_STOP"
    assert status["sealed_cells"] == 0
    exported = export_routing_s1_live(
        state_root=state_root,
        results_root=tmp_path / "results",
    )
    export_root = Path(exported["results_root"])
    assert verify_routing_s1_live_export(export_root)["calibration_outcome"] == (
        "CALIBRATION_STOP"
    )

    def reseal_export() -> None:
        export_files = {
            path.relative_to(export_root).as_posix(): path.read_bytes()
            for path in export_root.rglob("*")
            if path.is_file()
            and path.relative_to(export_root).as_posix() != "export-seal.json"
        }
        export_seal = json.loads(
            (export_root / "export-seal.json").read_text(encoding="utf-8")
        )
        export_seal["export_sha256"] = _aggregate_export_sha256(export_files)
        export_seal["file_count"] = len(export_files)
        atomic_write(export_root / "export-seal.json", canonical_json_bytes(export_seal))

    original_markdown = (export_root / "summary.md").read_bytes()
    atomic_write(export_root / "summary.md", b"ROUTE_B1\n")
    reseal_export()
    with pytest.raises(RoutingSuiteError, match="Markdown summary differs"):
        verify_routing_s1_live_export(export_root)
    atomic_write(export_root / "summary.md", original_markdown)

    atomic_write(export_root / "routing-policy-v1.json", b'{"route":"ROUTE_B1"}')
    reseal_export()
    with pytest.raises(RoutingSuiteError, match="file set differs"):
        verify_routing_s1_live_export(export_root)
    (export_root / "routing-policy-v1.json").unlink()

    summary = json.loads((export_root / "summary.json").read_text(encoding="utf-8"))
    summary["sealed_cells"] = 1
    atomic_write(export_root / "summary.json", canonical_json_bytes(summary))
    reseal_export()
    with pytest.raises(RoutingSuiteError, match="summary differs"):
        verify_routing_s1_live_export(export_root)


def _calibration_measurements() -> list[Measurement]:
    base = Measurement.model_validate_json(PILOT_MEASUREMENT.read_bytes())
    plan = _live_plan()
    measurements = []
    task_counts = {
        "code-change": 1,
        "document-read": 1,
        "sequential-code-change": 2,
        "sequential-document": 2,
    }
    for cell in sorted(plan.cells, key=lambda item: item.execution_ordinal):
        ordinal = cell.execution_ordinal
        fixture_id = cell.fixture_id
        variant_id = cell.variant_id
        turns = task_counts[fixture_id]
        identity = base.identity.model_copy(
            update={
                "experiment_id": plan.experiment_id,
                "block_id": cell.block_id,
                "cell_id": cell.cell_id,
                "fixture_id": fixture_id,
                "repetition": cell.repetition,
                "variant_id": variant_id,
                "execution_ordinal": ordinal,
            }
        )
        fixture = next(item for item in plan.fixtures if item.fixture_id == fixture_id)
        variant = next(item for item in plan.variants if item.artifact_id == variant_id)
        provenance = base.provenance.model_copy(
            update={
                "manifest_sha256": plan.source_manifest.sha256,
                "fixture_source_commit": fixture.source_commit,
                "fixture_tree_before": fixture.git_tree,
                "runner_commit": plan.runner.version,
                "variant_version": variant.version,
                "variant_artifact_sha256": variant.sha256,
            }
        )
        environment = base.environment.model_copy(
            update={
                "surface_kind": (
                    "b1_cli_codex_runtime"
                    if variant_id == "b1"
                    else "sdk_controlled_codex_runtime"
                )
            }
        )
        token_usage = base.resource.token_usage.model_copy(
            update={
                "value": {
                    "input_tokens": 900,
                    "output_tokens": 100,
                    "total_tokens": 1000,
                }
            }
        )
        resource = base.resource.model_copy(
            update={
                "token_usage": token_usage,
                "turn_count": base.resource.turn_count.model_copy(update={"value": turns}),
                "session_count": base.resource.session_count.model_copy(
                    update={"value": turns}
                ),
                "attempt_count": base.resource.attempt_count.model_copy(
                    update={"value": turns if variant_id == "b1" else 1}
                ),
            }
        )
        wall = base.effort.total_wall_clock_seconds.model_copy(update={"value": 10.0})
        effort = base.effort.model_copy(update={"total_wall_clock_seconds": wall})
        values = dict(base.variant_metrics.values)
        values["actual_model_turns"] = turns
        values["protected_files_ok"] = True
        if variant_id == "b1":
            values.update(
                {
                    "b1_retry_count": 0,
                    "b1_resume_count": 0,
                    "b1_intermediate_check_changed_result": False,
                    "b1_intermediate_check_changed_dispatch": False,
                    "b1_repeatable_quality_regression": False,
                }
            )
        metrics = base.variant_metrics.model_copy(update={"values": values})
        measurements.append(
            base.model_copy(
                update={
                    "identity": identity,
                    "provenance": provenance,
                    "environment": environment,
                    "resource": resource,
                    "effort": effort,
                    "variant_metrics": metrics,
                    "outcome": base.outcome.model_copy(update={"check_success": True}),
                    "integrity": base.integrity.model_copy(
                        update={
                            "scope_ok": True,
                            "evidence_hashes_ok": True,
                            "secret_findings": [],
                        }
                    ),
                }
            )
        )
    return measurements


def test_calibration_outcome_is_deterministic_and_never_routes() -> None:
    measurements = _calibration_measurements()
    assert _calibration_outcome(measurements) == "CALIBRATION_PASS"

    unknown = measurements[0].resource.token_usage.model_copy(
        update={"status": "unknown", "value": None}
    )
    measurements[0] = measurements[0].model_copy(
        update={"resource": measurements[0].resource.model_copy(update={"token_usage": unknown})}
    )
    assert _calibration_outcome(measurements) == "CALIBRATION_INCONCLUSIVE"

    measurements = _calibration_measurements()
    measurements[0] = measurements[0].model_copy(
        update={
            "outcome": measurements[0].outcome.model_copy(
                update={
                    "state": "failed",
                    "failure_kind": "transient_runtime",
                    "check_success": True,
                }
            )
        }
    )
    assert _calibration_outcome(measurements) == "CALIBRATION_INCONCLUSIVE"

    measurements = _calibration_measurements()
    b1_index = next(
        index for index, item in enumerate(measurements) if item.identity.variant_id == "b1"
    )
    measurements[b1_index] = measurements[b1_index].model_copy(
        update={
            "integrity": measurements[b1_index].integrity.model_copy(
                update={"scope_ok": False}
            )
        }
    )
    assert _calibration_outcome(measurements) == "CALIBRATION_STOP"

    measurements = _calibration_measurements()
    b1_index = next(
        index for index, item in enumerate(measurements) if item.identity.variant_id == "b1"
    )
    values = dict(measurements[b1_index].variant_metrics.values)
    values["b1_repeatable_quality_regression"] = True
    measurements[b1_index] = measurements[b1_index].model_copy(
        update={
            "variant_metrics": measurements[b1_index].variant_metrics.model_copy(
                update={"values": values}
            )
        }
    )
    assert _calibration_outcome(measurements) == "CALIBRATION_STOP"


def test_c2_integrity_failure_stops_before_its_b1_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _live_plan()
    first = plan.cells[0]
    cell_dir = tmp_path / "cells" / first.cell_id
    atomic_write(
        cell_dir / "cell-state.json",
        canonical_json_bytes(
            {
                "cell_id": first.cell_id,
                "state": "SEALED",
                "history": [
                    {"state": "PLANNED", "at": "2026-08-07T00:00:00+00:00"},
                    {"state": "SEALED", "at": "2026-08-07T00:00:01+00:00"},
                ],
                "outcome_state": "completed",
                "stop_reason": None,
                "sealed_measurement_sha256": "a" * 64,
            }
        ),
    )
    measurement = _calibration_measurements()[0]
    measurement = measurement.model_copy(
        update={
            "integrity": measurement.integrity.model_copy(update={"scope_ok": False})
        }
    )
    monkeypatch.setattr(
        routing_live,
        "_load_live_plan",
        lambda _: (tmp_path, plan, {}),
    )
    monkeypatch.setattr(routing_live, "verify_sealed_cell", lambda _: measurement)
    status = routing_s1_live_status(tmp_path)
    assert status["sealed_cells"] == 1
    assert status["calibration_outcome"] == "CALIBRATION_STOP"
    assert status["stop_before_next_cell"] is True
    assert status["cells"][1]["state"] == "PLANNED"

    values = dict(measurement.variant_metrics.values)
    values["actual_model_turns"] = 2
    malformed = measurement.model_copy(
        update={
            "variant_metrics": measurement.variant_metrics.model_copy(
                update={"values": values}
            )
        }
    )
    monkeypatch.setattr(routing_live, "verify_sealed_cell", lambda _: malformed)
    with pytest.raises(RoutingSuiteError, match="resource contract differs"):
        routing_s1_live_status(tmp_path)


def test_live_measurement_contract_rejects_surface_and_turn_tampering() -> None:
    cell = _live_plan().cells[0]
    measurement = _calibration_measurements()[0]
    _assert_live_measurement_contract(cell, measurement)

    wrong_environment = measurement.environment.model_copy(
        update={"surface_kind": "b1_cli_codex_runtime"}
    )
    with pytest.raises(RoutingSuiteError, match="environment differs"):
        _assert_live_measurement_contract(
            cell, measurement.model_copy(update={"environment": wrong_environment})
        )

    values = dict(measurement.variant_metrics.values)
    values["actual_model_turns"] = 2
    with pytest.raises(RoutingSuiteError, match="resource contract differs"):
        _assert_live_measurement_contract(
            cell,
            measurement.model_copy(
                update={
                    "variant_metrics": measurement.variant_metrics.model_copy(
                        update={"values": values}
                    )
                }
            ),
        )
