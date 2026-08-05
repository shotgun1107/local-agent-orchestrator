import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from benchmark_runner.cli import main
from benchmark_runner.contract import (
    ArtifactIdentity,
    CellLifecycleState,
    CellStateRecord,
    EvidenceRef,
    ExperimentControl,
    FixtureIdentity,
    LifecycleEntry,
    Measurement,
    MeasurementEffort,
    MeasurementEnvironment,
    MeasurementIdentity,
    MeasurementIntegrity,
    MeasurementOutcome,
    MeasurementProvenance,
    MeasurementQuality,
    MeasurementResource,
    MetricStatus,
    MetricValue,
    VariantMetrics,
)
from benchmark_runner.plan import build_r4_plan
from benchmark_runner.runner import (
    _r5_assert_export_safe,
    IntegrityError,
    analyze_r5_experiment,
    canonical_json_bytes,
    export_r5_experiment,
    frozen_b0_b1_decision_policy,
    initialize_r4_experiment,
    sha256_bytes,
    verify_r5_export,
)

FROZEN_TIME = datetime(2026, 8, 5, tzinfo=timezone.utc)


def _metric(
    value: object | None,
    unit: str,
    status: MetricStatus = MetricStatus.MEASURED,
) -> MetricValue:
    return MetricValue(status=status, value=value, unit=unit, source="r5-test")


def _plan():
    return build_r4_plan(
        source_manifest_path="benchmarks/manifests/b0-b1-frozen.yaml",
        source_manifest_sha256="a" * 64,
        fixtures=[
            FixtureIdentity(
                fixture_id="code-change",
                source_commit="1" * 40,
                git_tree="2" * 40,
            ),
            FixtureIdentity(
                fixture_id="document-read",
                source_commit="1" * 40,
                git_tree="3" * 40,
            ),
        ],
        repetitions=3,
        runner=ArtifactIdentity(
            artifact_id="benchmark-runner",
            version="r5-test",
            sha256="4" * 64,
        ),
        variants=[
            ArtifactIdentity(artifact_id="b0", version="manual", sha256="5" * 64),
            ArtifactIdentity(artifact_id="b1", version="sequential", sha256="6" * 64),
        ],
        baseline_variant="b0",
        candidate_variant="b1",
        seed=20260805,
        primary_metrics=[
            "check_success",
            "manual_copy_or_relay_count_excluding_start",
        ],
        decision_policy=frozen_b0_b1_decision_policy(),
        reasoning_control="not_established_test",
        environment_fingerprint={
            "model": "gpt-5.6-terra",
            "auth_method": "chatgpt",
            "reasoning_effort": "not_established",
            "surface_kind": "test",
        },
        created_at=FROZEN_TIME,
    )


def _sealed_experiment(
    tmp_path: Path,
    overrides: dict[str, dict[str, object]] | None = None,
) -> tuple[Path, object]:
    plan = _plan()
    created = initialize_r4_experiment(tmp_path / "state", plan)
    experiment_dir = Path(created.experiment_dir)
    overrides = overrides or {}
    variant_artifacts = {item.artifact_id: item for item in plan.variants}
    fixtures = {item.fixture_id: item for item in plan.fixtures}
    for cell in plan.cells:
        values = overrides.get(cell.cell_id, {})
        check_success = bool(values.get("check_success", True))
        outcome_state = str(
            values.get("outcome_state", "completed" if check_success else "failed")
        )
        relay = values.get("relay", 2 if cell.variant_id == "b0" else 0)
        relay_status = MetricStatus(str(values.get("relay_status", "derived")))
        recovery_seconds = values.get("recovery_seconds", 0.0)
        human_errors = values.get("human_errors")
        human_status = (
            MetricStatus.MEASURED
            if human_errors is not None
            else MetricStatus.NOT_APPLICABLE
        )
        cell_dir = experiment_dir / "cells" / cell.cell_id
        evidence_path = cell_dir / "judge" / "result.json"
        evidence_payload = values.get(
            "evidence_payload",
            {"cell_id": cell.cell_id, "check_success": check_success},
        )
        evidence_bytes = canonical_json_bytes(evidence_payload)
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_bytes(evidence_bytes)
        fixture = fixtures[cell.fixture_id]
        artifact = variant_artifacts[cell.variant_id]
        token_usage = (
            _metric(
                {"input_tokens": 10, "output_tokens": 2, "total_tokens": 12},
                "tokens",
            )
            if cell.variant_id == "b1"
            else _metric(None, "tokens", MetricStatus.UNKNOWN)
        )
        measurement = Measurement(
            created_at=FROZEN_TIME,
            identity=MeasurementIdentity(
                experiment_id=plan.experiment_id,
                block_id=cell.block_id,
                cell_id=cell.cell_id,
                fixture_id=cell.fixture_id,
                repetition=cell.repetition,
                variant_id=cell.variant_id,
                execution_ordinal=cell.execution_ordinal,
            ),
            provenance=MeasurementProvenance(
                manifest_sha256=plan.source_manifest.sha256,
                fixture_source_commit=fixture.source_commit,
                fixture_tree_before=fixture.git_tree,
                fixture_tree_after=fixture.git_tree,
                runner_commit="7" * 40,
                variant_version=artifact.version,
                variant_artifact_sha256=artifact.sha256,
            ),
            environment=MeasurementEnvironment(
                os="test",
                python_version="3.12.10",
                model="gpt-5.6-terra",
                auth_method="chatgpt",
                reasoning_effort="not_established",
                surface_kind="test",
                approval_mode="deny_all",
                model_control="established",
                reasoning_control="not_established",
                treatment_control=str(values.get("treatment_control", "partial")),
            ),
            outcome=MeasurementOutcome(
                state=outcome_state,
                failure_kind=values.get("failure_kind"),
                check_success=check_success,
            ),
            effort=MeasurementEffort(
                variant_execution_seconds=_metric(
                    float(values.get("variant_seconds", 10.0)), "seconds"
                ),
                judge_seconds=_metric(1.0, "seconds"),
                total_wall_clock_seconds=_metric(
                    float(values.get("variant_seconds", 10.0)) + 1.0,
                    "seconds",
                ),
                startup_action_count=_metric(1, "count", MetricStatus.DERIVED),
                manual_copy_or_relay_count_excluding_start=_metric(
                    relay if relay_status in {MetricStatus.MEASURED, MetricStatus.DERIVED} else None,
                    "count",
                    relay_status,
                ),
                manual_copy_or_relay_count_including_start=_metric(
                    int(relay) + 1 if relay_status in {MetricStatus.MEASURED, MetricStatus.DERIVED} else None,
                    "count",
                    relay_status,
                ),
                manual_recovery_count=_metric(0, "count", MetricStatus.DERIVED),
                manual_recovery_seconds=_metric(
                    float(recovery_seconds), "seconds", MetricStatus.DERIVED
                ),
            ),
            resource=MeasurementResource(
                session_count=_metric(1, "count", MetricStatus.DERIVED),
                turn_count=_metric(1, "count", MetricStatus.DERIVED),
                attempt_count=_metric(1, "count", MetricStatus.DERIVED),
                token_usage=token_usage,
            ),
            quality=MeasurementQuality(
                errors_found_by_automatic_checks=_metric(
                    0 if check_success else 1,
                    "count",
                    MetricStatus.DERIVED,
                ),
                human_errors_after_pass=_metric(
                    human_errors,
                    "count",
                    human_status,
                ),
            ),
            integrity=MeasurementIntegrity(
                scope_ok=bool(values.get("scope_ok", True)),
                evidence_hashes_ok=bool(values.get("evidence_hashes_ok", True)),
                secret_findings=list(values.get("secret_findings", [])),
            ),
            evidence=[
                EvidenceRef(
                    path="judge/result.json",
                    size=len(evidence_bytes),
                    sha256=sha256_bytes(evidence_bytes),
                )
            ],
            variant_metrics=VariantMetrics(
                schema_id=f"{cell.variant_id}.r5-test",
                values={},
            ),
        )
        measurement_bytes = canonical_json_bytes(measurement)
        measurement_path = cell_dir / "sealed" / "measurement.json"
        measurement_path.parent.mkdir(parents=True, exist_ok=True)
        measurement_path.write_bytes(measurement_bytes)
        state = CellStateRecord(
            cell_id=cell.cell_id,
            state=CellLifecycleState.SEALED,
            history=[
                LifecycleEntry(state=CellLifecycleState.PLANNED, at=FROZEN_TIME),
                LifecycleEntry(state=CellLifecycleState.SEALED, at=FROZEN_TIME),
            ],
            outcome_state=outcome_state,
            sealed_measurement_sha256=sha256_bytes(measurement_bytes),
        )
        (cell_dir / "cell-state.json").write_bytes(canonical_json_bytes(state))
    return experiment_dir, plan


def _variant_overrides(plan, variant_id: str, **values: object) -> dict[str, dict[str, object]]:
    return {
        cell.cell_id: dict(values)
        for cell in plan.cells
        if cell.variant_id == variant_id
    }


def test_r5_adopts_when_quality_is_preserved_and_relay_is_lower(tmp_path: Path) -> None:
    experiment_dir, plan = _sealed_experiment(tmp_path)

    result = analyze_r5_experiment(experiment_dir)
    first_bytes = Path(result.summary_path).read_bytes()
    repeated = analyze_r5_experiment(experiment_dir)
    summary = json.loads(first_bytes)

    assert result.verdicts == {"b1": "ADOPT_B1"}
    assert repeated.analysis_sha256 == result.analysis_sha256
    assert Path(result.summary_path).read_bytes() == first_bytes
    assert len(summary["cell_results"]) == 12
    assert len(summary["blocks"]) == 6
    assert summary["aggregates"]["b0"]["cell_count"] == 6
    assert summary["aggregates"]["b1"]["cell_count"] == 6
    assert summary["aggregates"]["b0"]["metrics"]["token_usage"]["coverage"] == (
        "partial_or_unknown"
    )
    assert summary["treatment_control_values"] == ["partial"]
    control = ExperimentControl.model_validate_json(
        (experiment_dir / "experiment-control.json").read_bytes()
    )
    assert control.analysis_sha256 == result.analysis_sha256
    assert plan.experiment_id == result.experiment_id


def test_r5_rejects_quality_regression(tmp_path: Path) -> None:
    plan = _plan()
    candidate = next(cell for cell in plan.cells if cell.variant_id == "b1")
    experiment_dir, _ = _sealed_experiment(
        tmp_path,
        {candidate.cell_id: {"check_success": False, "outcome_state": "failed"}},
    )

    result = analyze_r5_experiment(experiment_dir)

    assert result.verdicts["b1"] == "REJECT_B1"


def test_r5_interrupted_cell_is_preserved_and_inconclusive(tmp_path: Path) -> None:
    plan = _plan()
    candidate = next(cell for cell in plan.cells if cell.variant_id == "b1")
    experiment_dir, _ = _sealed_experiment(
        tmp_path,
        {
            candidate.cell_id: {
                "check_success": False,
                "outcome_state": "interrupted",
                "failure_kind": "user_interrupt",
            }
        },
    )

    result = analyze_r5_experiment(experiment_dir)
    summary = json.loads(Path(result.summary_path).read_text(encoding="utf-8"))

    assert result.verdicts["b1"] == "INCONCLUSIVE"
    row = next(item for item in summary["cell_results"] if item["cell_id"] == candidate.cell_id)
    assert row["outcome_state"] == "interrupted"


def test_r5_unknown_required_metric_is_not_imputed(tmp_path: Path) -> None:
    plan = _plan()
    candidate = next(cell for cell in plan.cells if cell.variant_id == "b1")
    experiment_dir, _ = _sealed_experiment(
        tmp_path,
        {candidate.cell_id: {"relay_status": "unknown", "relay": None}},
    )

    result = analyze_r5_experiment(experiment_dir)
    summary = json.loads(Path(result.summary_path).read_text(encoding="utf-8"))

    assert result.verdicts["b1"] == "INCONCLUSIVE"
    relay = summary["aggregates"]["b1"]["metrics"][
        "manual_copy_or_relay_count_excluding_start"
    ]
    assert relay["coverage"] == "partial_or_unknown"
    assert "total" not in relay
    assert relay["known_subtotal"] == 0


def test_r5_relay_tie_is_inconclusive_and_worse_is_rejected(tmp_path: Path) -> None:
    plan = _plan()
    tied_dir, _ = _sealed_experiment(
        tmp_path / "tie",
        _variant_overrides(plan, "b1", relay=2),
    )
    worse_dir, _ = _sealed_experiment(
        tmp_path / "worse",
        _variant_overrides(plan, "b1", relay=3),
    )

    assert analyze_r5_experiment(tied_dir).verdicts["b1"] == "INCONCLUSIVE"
    assert analyze_r5_experiment(worse_dir).verdicts["b1"] == "REJECT_B1"


def test_r5_rejects_more_recovery_or_human_errors(tmp_path: Path) -> None:
    plan = _plan()
    recovery_dir, _ = _sealed_experiment(
        tmp_path / "recovery",
        _variant_overrides(plan, "b1", recovery_seconds=1.0),
    )
    human_overrides = _variant_overrides(plan, "b0", human_errors=0)
    human_overrides.update(_variant_overrides(plan, "b1", human_errors=1))
    human_dir, _ = _sealed_experiment(tmp_path / "human", human_overrides)

    assert analyze_r5_experiment(recovery_dir).verdicts["b1"] == "REJECT_B1"
    assert analyze_r5_experiment(human_dir).verdicts["b1"] == "REJECT_B1"


def test_r5_integrity_failure_has_variant_sensitive_precedence(tmp_path: Path) -> None:
    plan = _plan()
    candidate_dir, _ = _sealed_experiment(
        tmp_path / "candidate",
        _variant_overrides(plan, "b1", scope_ok=False),
    )
    baseline_dir, _ = _sealed_experiment(
        tmp_path / "baseline",
        _variant_overrides(plan, "b0", scope_ok=False),
    )

    assert analyze_r5_experiment(candidate_dir).verdicts["b1"] == "REJECT_B1"
    assert analyze_r5_experiment(baseline_dir).verdicts["b1"] == "INCONCLUSIVE"


def test_r5_reports_fixture_median_warning_without_changing_gate(tmp_path: Path) -> None:
    plan = _plan()
    overrides: dict[str, dict[str, object]] = {}
    for cell in plan.cells:
        if cell.fixture_id == "code-change":
            overrides[cell.cell_id] = {"relay": 0 if cell.variant_id == "b0" else 1}
        else:
            overrides[cell.cell_id] = {"relay": 5 if cell.variant_id == "b0" else 0}
    experiment_dir, _ = _sealed_experiment(tmp_path, overrides)

    result = analyze_r5_experiment(experiment_dir)
    summary = json.loads(Path(result.summary_path).read_text(encoding="utf-8"))

    assert result.verdicts["b1"] == "ADOPT_B1"
    assert summary["decisions"][0]["warnings"] == [
        "fixture code-change: candidate relay median is worse than baseline"
    ]


def test_r5_requires_some_candidate_quality_evidence(tmp_path: Path) -> None:
    plan = _plan()
    overrides = {
        cell.cell_id: {"check_success": False, "outcome_state": "failed"}
        for cell in plan.cells
    }
    experiment_dir, _ = _sealed_experiment(tmp_path, overrides)

    result = analyze_r5_experiment(experiment_dir)

    assert result.verdicts["b1"] == "INCONCLUSIVE"


def test_r5_refuses_incomplete_or_tampered_source(tmp_path: Path) -> None:
    experiment_dir, plan = _sealed_experiment(tmp_path / "tamper")
    first_cell = plan.cells[0]
    evidence = experiment_dir / "cells" / first_cell.cell_id / "judge" / "result.json"
    evidence.write_bytes(evidence.read_bytes() + b" ")
    with pytest.raises(IntegrityError, match="Evidence hash mismatch"):
        analyze_r5_experiment(experiment_dir)

    incomplete_plan = _plan()
    created = initialize_r4_experiment(tmp_path / "incomplete", incomplete_plan)
    with pytest.raises(IntegrityError, match="not sealed"):
        analyze_r5_experiment(Path(created.experiment_dir))


def test_r5_export_is_idempotent_and_seals_every_measurement(tmp_path: Path) -> None:
    experiment_dir, plan = _sealed_experiment(tmp_path)
    analyze_r5_experiment(experiment_dir)
    results_root = tmp_path / "results"

    first = export_r5_experiment(experiment_dir, results_root)
    second = export_r5_experiment(experiment_dir, results_root)
    verified = verify_r5_export(results_root, plan.experiment_id)
    seals = json.loads(
        (results_root / "comparisons" / plan.experiment_id / "seals.json").read_text(
            encoding="utf-8"
        )
    )

    assert first.idempotent is False
    assert second.idempotent is True
    assert first.export_sha256 == second.export_sha256 == verified.export_sha256
    assert verified.cell_count == 12
    assert len(seals["entries"]) == 12
    assert [entry["cell_id"] for entry in seals["entries"]] == sorted(
        cell.cell_id for cell in plan.cells
    )
    control = ExperimentControl.model_validate_json(
        (experiment_dir / "experiment-control.json").read_bytes()
    )
    assert control.export_sha256 == verified.export_sha256


def test_r5_export_verifier_detects_one_byte_measurement_change(tmp_path: Path) -> None:
    experiment_dir, plan = _sealed_experiment(tmp_path)
    analyze_r5_experiment(experiment_dir)
    results_root = tmp_path / "results"
    export_r5_experiment(experiment_dir, results_root)
    first_cell = plan.cells[0]
    measurement = (
        results_root
        / first_cell.variant_id
        / plan.experiment_id
        / first_cell.cell_id
        / "sealed"
        / "measurement.json"
    )
    measurement.write_bytes(measurement.read_bytes() + b" ")

    with pytest.raises(IntegrityError, match="differs from seals.json"):
        verify_r5_export(results_root, plan.experiment_id)


@pytest.mark.parametrize(
    "unsafe_value",
    [
        "sk-this_is_a_fake_but_token_shaped_secret",
        "alex@example.com",
        r"C:\Users\alex\private\file.txt",
        "copied from auth.json",
    ],
)
def test_r5_export_blocks_sensitive_sealed_evidence(
    tmp_path: Path,
    unsafe_value: str,
) -> None:
    plan = _plan()
    first_cell = plan.cells[0]
    experiment_dir, _ = _sealed_experiment(
        tmp_path,
        {first_cell.cell_id: {"evidence_payload": {"value": unsafe_value}}},
    )
    analyze_r5_experiment(experiment_dir)

    with pytest.raises(IntegrityError, match="export"):
        export_r5_experiment(experiment_dir, tmp_path / "results")


def test_r5_export_scans_ascii_secrets_inside_non_utf8_evidence() -> None:
    with pytest.raises(IntegrityError, match="OpenAI-style secret"):
        _r5_assert_export_safe(
            "b1/exp/cell/raw/binary.bin",
            b"\xff\xfesk-this_is_a_fake_but_token_shaped_secret\x00",
        )


def test_r5_export_rejects_unexpected_existing_file(tmp_path: Path) -> None:
    experiment_dir, plan = _sealed_experiment(tmp_path)
    analyze_r5_experiment(experiment_dir)
    results_root = tmp_path / "results"
    export_r5_experiment(experiment_dir, results_root)
    unexpected = results_root / "comparisons" / plan.experiment_id / "manual-note.txt"
    unexpected.write_text("not part of the deterministic export", encoding="utf-8")

    with pytest.raises(IntegrityError, match="unexpected files"):
        export_r5_experiment(experiment_dir, results_root)


def test_r5_cli_compare_export_and_verify(tmp_path: Path, capsys) -> None:
    experiment_dir, plan = _sealed_experiment(tmp_path)
    results_root = tmp_path / "results"

    assert main(["compare", "--experiment-dir", str(experiment_dir)]) == 0
    compared = json.loads(capsys.readouterr().out)
    assert compared["verdicts"] == {"b1": "ADOPT_B1"}

    assert main(
        [
            "export",
            "--experiment-dir",
            str(experiment_dir),
            "--results-root",
            str(results_root),
        ]
    ) == 0
    exported = json.loads(capsys.readouterr().out)
    assert exported["idempotent"] is False

    assert main(
        [
            "verify-export",
            "--results-root",
            str(results_root),
            "--experiment-id",
            plan.experiment_id,
        ]
    ) == 0
    verified = json.loads(capsys.readouterr().out)
    assert verified["verified"] is True
    assert verified["export_sha256"] == exported["export_sha256"]
