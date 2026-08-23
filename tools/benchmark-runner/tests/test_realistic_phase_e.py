from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from hashlib import sha256
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
        "benchmarks/artifacts/profile-r-docker-judge-qualification-v14/qualification.json"
    )


def test_profile_r_requalification_is_exact_nine_cell_projection() -> None:
    path = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "profile-r-docker-judge-qualification-v14"
        / "qualification.json"
    )
    qualification = json.loads(path.read_text(encoding="utf-8"))
    environment = json.loads((path.parent / "docker-environment.json").read_text(encoding="utf-8"))

    assert qualification["schema_version"] == 1
    assert qualification["profile"] == "R"
    assert qualification["source_commit"] == "6cc1063c457fe3153d45ac869af7d588f3208628"
    assert qualification["batch_id"] == "profile-r-docker-matrix-q17-home"
    assert qualification["status"] == "CHALLENGE_READY"
    assert qualification["challenge_ready"] is True
    assert qualification["model_turns"] == 0
    assert qualification["image_reference"].endswith(
        "@sha256:5610c2a6756229170ff4475789f7c163e1d5fe26967ef284936124b2a1c6ad89"
    )
    cells = qualification["cells"]
    assert [cell["ordinal"] for cell in cells] == list(range(1, 10))
    assert cells[0]["variant_id"] == "reference"
    assert cells[0]["aggregate_status"] == "pass"
    assert all(cell["matched_expectation"] is True for cell in cells)
    assert all(cell["aggregate_status"] == "fail" for cell in cells[1:])
    assert environment["qualification"] == {
        "source_commit": qualification["source_commit"],
        "batch_id": qualification["batch_id"],
        "status": "CHALLENGE_READY",
        "matched_expectations": 9,
        "cell_count": 9,
        "actual_model_turns": 0,
        "residual_profile_r_containers": 0,
    }
    assert environment["image"]["reference"] == qualification["image_reference"]
    assert environment["image"]["id"].endswith(qualification["image_reference"].split("@", 1)[1])


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


def test_checked_in_environment_remediation_v9_candidate_verifies_against_its_source_commit() -> None:
    candidate = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "sdk-routing-realistic-high-difficulty-phase-e-v9"
    )
    seal = verify_phase_e_candidate(REPOSITORY, candidate)

    assert seal.source_commit == "f17c43e816ba585bdb8324c4ecb41e27e3112372"
    assert seal.experiment_id == "exp_20260814_1c971b08_1"
    assert seal.plan_fingerprint == (
        "1c971b08ea50d73e88b00f8679f52dec01870c596ad9769a533d2e591b48a784"
    )
    assert seal.actual_model_turns == 0


def test_checked_in_hardened_r07_v12_candidate_verifies_against_its_source_commit() -> None:
    candidate = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "sdk-routing-realistic-high-difficulty-phase-e-v12"
    )
    seal = verify_phase_e_candidate(REPOSITORY, candidate)

    assert seal.source_commit == "3cb559355f0feb0403ef486dcce14a9cc8c25506"
    assert seal.experiment_id == "exp_20260815_3a34f942_1"
    assert seal.plan_fingerprint == (
        "3a34f9425baec6bfc55b0168fb76c74eda8343b3bcf13a7e716085f2779c44af"
    )
    assert seal.seal_sha256 == (
        "0268930ed6456250aa3256f27d8f47cf67425cf27872905911111e41b90fd54f"
    )
    assert seal.actual_model_turns == 0


def test_checked_in_hardened_r07_v13_candidate_verifies_against_its_source_commit() -> None:
    candidate = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "sdk-routing-realistic-high-difficulty-phase-e-v13"
    )
    seal = verify_phase_e_candidate(REPOSITORY, candidate)

    assert seal.source_commit == "20053fc7ffb4794fddd16858bd1a56ece3314e93"
    assert seal.experiment_id == "exp_20260823_00f2916f_1"
    assert seal.plan_fingerprint == (
        "00f2916fdc41f4912e19648adb3d15a84e39118749544162ad83045b6ac1fc25"
    )
    assert seal.seal_sha256 == (
        "1d9df197dad859feb37831e696552a0639b00fe3498f7c0871c95b06e0af26bb"
    )
    assert seal.actual_model_turns == 0


def test_checked_in_hardened_r07_v14_candidate_verifies_against_its_source_commit() -> None:
    candidate = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "sdk-routing-realistic-high-difficulty-phase-e-v14"
    )
    seal = verify_phase_e_candidate(REPOSITORY, candidate)
    bindings = json.loads((candidate / "source-bindings.json").read_text(encoding="utf-8"))

    assert seal.source_commit == "c5e1ae2df58554970ffd98d17946ac94393c3a5d"
    assert bindings["source_tree"] == "3f42f200145de525d2bfe9ca8e6bca5705c0cab9"
    assert bindings["bindings_sha256"] == (
        "f82c4acd367dd8babecec79c8d43c5989648277cbea8d962ea05f8230ccd632d"
    )
    assert seal.experiment_id == "exp_20260823_bba38a2e_1"
    assert seal.plan_fingerprint == (
        "bba38a2e78808af7a51fdea1d669e1c55f6bf3899264b72482a0a25483f1841e"
    )
    assert seal.seal_sha256 == (
        "ab0fc7dd2618da0adde7797d5d30690adbb614192a46d866543ec509a721d4b0"
    )
    assert seal.files_manifest_sha256 == (
        "de498c920448390227af72cb7b273a754868e6abbc45534f1b8dc7bc43fc04ba"
    )
    assert sha256((candidate / "candidate-seal.json").read_bytes()).hexdigest() == (
        "ca84ee54b354b4d99cf3a4ff03a36078bf82d9257f3d296a3f8ab3b81add9531"
    )
    assert seal.actual_model_turns == 0
