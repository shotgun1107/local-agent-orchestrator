from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from benchmark_runner.realistic_phase_e import (
    PHASE_E_STAGE_RELATIVE,
    PINNED_MODEL,
    PhaseECandidateError,
    PhaseEPreflightEvidence,
    PhaseEStageManifest,
    _git_source_tree_sha256,
    build_phase_e_plan,
    create_phase_e_candidate,
    verify_phase_e_candidate,
)
from benchmark_runner.runner import _source_tree_sha256


REPOSITORY = Path(__file__).resolve().parents[3]


def _head() -> str:
    return subprocess.run(
        ["git", "-C", str(REPOSITORY), "rev-parse", "HEAD"],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        encoding="ascii",
    ).stdout.strip()


def _preflight() -> PhaseEPreflightEvidence:
    return PhaseEPreflightEvidence(
        account_type="chatgpt",
        sdk_version="0.144.4",
        model=PINNED_MODEL,
        reasoning_effort="high",
        model_visible=True,
        actual_model_turns=0,
        api_key_environment_names_present=[],
        permission_profile_id="runtime-boundary-worker",
        legacy_sandbox_arguments=False,
    )


def test_stage_manifest_has_exact_four_cell_contract() -> None:
    stage = PhaseEStageManifest.model_validate_json(
        (REPOSITORY / PHASE_E_STAGE_RELATIVE).read_bytes()
    )
    assert [(item.ordinal, item.variant_id) for item in stage.cell_order] == [
        (1, "ss1"),
        (2, "b1"),
        (3, "b1"),
        (4, "ss1"),
    ]
    assert stage.budget.total_initial_turns == 32
    assert stage.budget.total_turn_ceiling == 40
    assert stage.dispatch.automatic_continuation is False
    assert stage.profiles[0].qualification_path == (
        "benchmarks/artifacts/profile-r-docker-judge-qualification-v10/qualification.json"
    )


def test_profile_r_requalification_is_exact_nine_cell_projection() -> None:
    path = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "profile-r-docker-judge-qualification-v10"
        / "qualification.json"
    )
    qualification = json.loads(path.read_text(encoding="utf-8"))

    assert qualification["schema_version"] == 1
    assert qualification["profile"] == "R"
    assert qualification["status"] == "CHALLENGE_READY"
    assert qualification["challenge_ready"] is True
    assert qualification["model_turns"] == 0
    assert qualification["image_reference"].endswith(
        "@sha256:ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab"
    )
    cells = qualification["cells"]
    assert [cell["ordinal"] for cell in cells] == list(range(1, 10))
    assert cells[0]["variant_id"] == "reference"
    assert cells[0]["aggregate_status"] == "pass"
    assert all(cell["matched_expectation"] is True for cell in cells)
    assert all(cell["aggregate_status"] == "fail" for cell in cells[1:])


def test_git_source_fingerprint_matches_worktree_algorithm() -> None:
    included = (
        "src/benchmark_runner/sdk_baselines.py",
        "src/benchmark_runner/sdk_common.py",
    )
    committed = _git_source_tree_sha256(
        REPOSITORY,
        _head(),
        "tools/benchmark-runner",
        included,
    )
    worktree = _source_tree_sha256(REPOSITORY / "tools/benchmark-runner", included)
    assert committed == worktree


def test_plan_and_candidate_are_reproducible_and_tamper_evident(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    source_commit = _head()
    created_at = datetime(2026, 8, 12, 0, 0, tzinfo=timezone.utc)
    plan, bindings = build_phase_e_plan(
        REPOSITORY,
        source_commit=source_commit,
        created_at=created_at,
    )
    assert [cell.variant_id for cell in plan.cells] == ["ss1", "b1", "b1", "ss1"]
    assert len(bindings.profiles) == 2
    candidate = tmp_path / "candidate"
    seal = create_phase_e_candidate(
        REPOSITORY,
        candidate,
        source_commit=source_commit,
        preflight=_preflight(),
        created_at=created_at,
    )
    assert seal.actual_model_turns == 0
    assert verify_phase_e_candidate(REPOSITORY, candidate) == seal
    with (candidate / "stage-manifest.json").open("ab") as stream:
        stream.write(b"\n")
    with pytest.raises(PhaseECandidateError, match="payload bytes changed"):
        verify_phase_e_candidate(REPOSITORY, candidate)


def test_checked_in_r07_candidate_verifies_against_its_source_commit() -> None:
    candidate = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "sdk-routing-realistic-high-difficulty-phase-e-v2"
    )
    seal = verify_phase_e_candidate(REPOSITORY, candidate)

    assert seal.source_commit == "ca7cd1e29d52d71385e73b9c8607efad7fa87174"
    assert seal.experiment_id == "exp_20260812_bd0b7fe5_1"
    assert seal.plan_fingerprint == (
        "bd0b7fe5b62ff24c1c5fa6e404cdc19e9d9765de0e2938949da9012bfc557c02"
    )
    assert seal.actual_model_turns == 0


def test_checked_in_company_r07_candidate_verifies_against_its_source_commit() -> None:
    candidate = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "sdk-routing-realistic-high-difficulty-phase-e-v3"
    )
    seal = verify_phase_e_candidate(REPOSITORY, candidate)

    assert seal.source_commit == "608044dfa8cdbed7520f722df80110f1ffa662de"
    assert seal.experiment_id == "exp_20260812_4053943d_1"
    assert seal.plan_fingerprint == (
        "4053943dee4bb1748db8a90a3390c54ffee712f03e7468d39c8f42c9121dada2"
    )
    assert seal.actual_model_turns == 0


def test_checked_in_r9_candidate_verifies_against_its_source_commit() -> None:
    candidate = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "sdk-routing-realistic-high-difficulty-phase-e-v4"
    )
    seal = verify_phase_e_candidate(REPOSITORY, candidate)

    assert seal.source_commit == "5a6790a69891ec4e48326bcfbab82306496f9d99"
    assert seal.experiment_id == "exp_20260813_44b11b86_1"
    assert seal.plan_fingerprint == (
        "44b11b8695d493a435f9bb0c2264a355f8aef52555a6c6275d7c75dfc9968c3c"
    )
    assert seal.actual_model_turns == 0


def test_checked_in_post_feedback_candidate_verifies_against_its_source_commit() -> None:
    candidate = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "sdk-routing-realistic-high-difficulty-phase-e-v5"
    )
    seal = verify_phase_e_candidate(REPOSITORY, candidate)

    assert seal.source_commit == "f4ee4b26e6bd2282099d521fa9426d1606ecf060"
    assert seal.experiment_id == "exp_20260813_a79e6015_1"
    assert seal.plan_fingerprint == (
        "a79e6015d22636ee4a7604f9b6d65b0719d48608e56168d1dd0c0a3c1621718d"
    )
    assert seal.actual_model_turns == 0


def test_checked_in_company_v7_candidate_verifies_against_its_source_commit() -> None:
    candidate = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "sdk-routing-realistic-high-difficulty-phase-e-v7"
    )
    seal = verify_phase_e_candidate(REPOSITORY, candidate)

    assert seal.source_commit == "b4e71ce89e5fe920c17b809c34170c13b788cb6e"
    assert seal.experiment_id == "exp_20260814_0a8bd290_1"
    assert seal.plan_fingerprint == (
        "0a8bd2908d45d6fe7b2d325137d452c3aafc07a3c8dc1da3f2dfe29d03857ad3"
    )
    assert seal.actual_model_turns == 0
