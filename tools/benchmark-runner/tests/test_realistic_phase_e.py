from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

import benchmark_runner.realistic_phase_e as phase_e
from benchmark_runner.contract import ExecutionPlan
from benchmark_runner.plan import recompute_plan_fingerprint
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
from benchmark_runner.realistic_routing import canonical_json_bytes, canonical_sha256
from benchmark_runner.runner import _source_tree_sha256


REPOSITORY = Path(__file__).resolve().parents[3]
V2_SOURCE_COMMIT = "cb691e56c8cd439e494f5519ebae65ccda669ed2"


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


def _v2_stage_bytes() -> bytes:
    return (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "sdk-routing-realistic-high-difficulty-phase-e-v16"
        / "stage-manifest.json"
    ).read_bytes()


def _create_worktree_v2_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Exercise v2 from the exact historical v16 source commit."""

    source_commit = V2_SOURCE_COMMIT
    original_git_text = phase_e._git_text

    def git_text(repository: Path, *args: str) -> str:
        if args == ("status", "--porcelain=v1"):
            return ""
        if args == ("rev-parse", "HEAD"):
            return source_commit
        return original_git_text(repository, *args)

    monkeypatch.setattr(phase_e, "_git_text", git_text)
    candidate = tmp_path / "candidate-v2"
    create_phase_e_candidate(
        REPOSITORY,
        candidate,
        source_commit=source_commit,
        preflight=_preflight(),
        created_at=datetime(2026, 8, 23, 0, 0, tzinfo=timezone.utc),
    )
    return candidate


def _reseal_candidate(candidate: Path) -> None:
    records: list[dict[str, Any]] = []
    for relative in phase_e.PAYLOAD_FILES:
        payload = (candidate / relative).read_bytes()
        records.append(
            {
                "path": relative,
                "size": len(payload),
                "sha256": sha256(payload).hexdigest(),
            }
        )
    files_bytes = "".join(
        f"{record['sha256']}  {record['path']}\n" for record in records
    ).encode("utf-8")
    (candidate / "files.sha256").write_bytes(files_bytes)
    seal = json.loads((candidate / "candidate-seal.json").read_text(encoding="utf-8"))
    plan = json.loads((candidate / "execution-plan.json").read_text(encoding="utf-8"))
    seal["experiment_id"] = plan["experiment_id"]
    seal["plan_fingerprint"] = plan["plan_fingerprint"]
    seal["payload_files"] = records
    seal["files_manifest_sha256"] = sha256(files_bytes).hexdigest()
    seal["seal_sha256"] = canonical_sha256(
        {key: value for key, value in seal.items() if key != "seal_sha256"}
    )
    (candidate / "candidate-seal.json").write_bytes(canonical_json_bytes(seal))


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
    assert stage.budget.total_initial_turns == 42
    assert stage.budget.total_turn_ceiling == 50
    assert stage.dispatch.automatic_continuation is False
    assert stage.schema_version == 3
    assert stage.profiles[0].qualification_path == (
        "benchmarks/artifacts/profile-r-docker-judge-qualification-v21/qualification.json"
    )
    assert stage.profiles[0].docker_environment_path == (
        "benchmarks/artifacts/profile-r-docker-judge-qualification-v21/"
        "docker-environment.json"
    )
    assert stage.profiles[0].task_pack_qualification_path == (
        "benchmarks/artifacts/profile-r-task-pack-q4/qualification.json"
    )
    assert stage.profiles[0].task_budget_path == (
        "benchmarks/artifacts/profile-r-task-pack-q4/task-budget.json"
    )
    assert stage.profiles[0].task_count == 13
    assert stage.profiles[1].docker_environment_path is None
    assert stage.profiles[1].task_count == 8
    assert stage.budget.profile_budgets is not None
    assert [item.task_count for item in stage.budget.profile_budgets] == [13, 8]


def test_v2_stage_requires_only_profile_r_qualification_sibling() -> None:
    raw = json.loads(_v2_stage_bytes())

    missing = json.loads(_v2_stage_bytes())
    missing["profiles"][0].pop("docker_environment_path")
    with pytest.raises(ValueError, match="Profile R requires"):
        PhaseEStageManifest.model_validate(missing)

    wrong_sibling = json.loads(_v2_stage_bytes())
    wrong_sibling["profiles"][0]["docker_environment_path"] = (
        "benchmarks/artifacts/profile-r-docker-judge-qualification-v15/other.json"
    )
    with pytest.raises(ValueError, match="Profile R requires"):
        PhaseEStageManifest.model_validate(wrong_sibling)

    profile_i_claim = json.loads(_v2_stage_bytes())
    profile_i_claim["profiles"][1]["docker_environment_path"] = (
        "benchmarks/artifacts/profile-i-docker-judge-qualification-v1/"
        "docker-environment.json"
    )
    with pytest.raises(ValueError, match="Profile I cannot claim"):
        PhaseEStageManifest.model_validate(profile_i_claim)

    raw["schema_version"] = 1
    with pytest.raises(ValueError, match="v1 profiles cannot claim"):
        PhaseEStageManifest.model_validate(raw)


@pytest.mark.parametrize(
    ("section", "field", "replacement"),
    [
        (None, "schema_version", 2),
        ("qualification", "source_commit", "0" * 40),
        ("qualification", "batch_id", "different-batch"),
        ("qualification", "status", "NOT_READY"),
        ("qualification", "actual_model_turns", 1),
        ("image", "reference", "different-image"),
    ],
)
def test_v2_binding_rejects_docker_environment_semantic_mismatch(
    section: str | None,
    field: str,
    replacement: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stage = PhaseEStageManifest.model_validate_json(_v2_stage_bytes())
    environment_path = stage.profiles[0].docker_environment_path
    assert environment_path is not None
    original_git_bytes = phase_e._git_bytes
    environment = json.loads(
        original_git_bytes(REPOSITORY, V2_SOURCE_COMMIT, environment_path)
    )
    target = environment if section is None else environment[section]
    target[field] = replacement
    mismatched_environment = canonical_json_bytes(environment)

    def git_bytes(repository: Path, commit: str, relative: str) -> bytes:
        if relative == environment_path:
            return mismatched_environment
        return original_git_bytes(repository, commit, relative)

    monkeypatch.setattr(phase_e, "_git_bytes", git_bytes)
    with pytest.raises(PhaseECandidateError, match="environment and qualification differ"):
        phase_e.build_source_bindings(REPOSITORY, V2_SOURCE_COMMIT, stage)


def test_v2_candidate_binds_exact_git_environment_in_binding_plan_and_seal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = _create_worktree_v2_candidate(tmp_path, monkeypatch)
    seal = verify_phase_e_candidate(REPOSITORY, candidate)
    bindings = json.loads((candidate / "source-bindings.json").read_text(encoding="utf-8"))
    plan = json.loads((candidate / "execution-plan.json").read_text(encoding="utf-8"))
    profile_r, profile_i = bindings["profiles"]
    expected_path = (
        "benchmarks/artifacts/profile-r-docker-judge-qualification-v15/"
        "docker-environment.json"
    )
    expected_sha = sha256(
        phase_e._git_bytes(REPOSITORY, V2_SOURCE_COMMIT, expected_path)
    ).hexdigest()

    assert expected_sha == (
        "e14c6dd61e0dc85b0a9e459af00b6451f1bdbe51935745a8e6ba6b3fb45692e3"
    )
    assert bindings["schema_version"] == 2
    assert profile_r["docker_environment_path"] == expected_path
    assert profile_r["docker_environment_sha256"] == expected_sha
    assert "docker_environment_path" not in profile_i
    assert "docker_environment_sha256" not in profile_i
    assert plan["environment_fingerprint"]["docker_environment_path"] == expected_path
    assert plan["environment_fingerprint"]["docker_environment_sha256"] == expected_sha
    assert seal.schema_version == 2
    assert seal.docker_environment_path == expected_path
    assert seal.docker_environment_sha256 == expected_sha


def test_v2_verifier_rejects_binding_tamper_even_when_candidate_is_resealed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = _create_worktree_v2_candidate(tmp_path, monkeypatch)
    bindings_path = candidate / "source-bindings.json"
    bindings = json.loads(bindings_path.read_text(encoding="utf-8"))
    bindings["profiles"][0]["docker_environment_sha256"] = "0" * 64
    bindings["bindings_sha256"] = canonical_sha256(
        {key: value for key, value in bindings.items() if key != "bindings_sha256"}
    )
    bindings_path.write_bytes(canonical_json_bytes(bindings))
    _reseal_candidate(candidate)

    with pytest.raises(PhaseECandidateError, match="differs across binding"):
        verify_phase_e_candidate(REPOSITORY, candidate)


def test_v2_verifier_rejects_partial_plan_identity_even_when_resealed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = _create_worktree_v2_candidate(tmp_path, monkeypatch)
    plan_path = candidate / "execution-plan.json"
    raw_plan = json.loads(plan_path.read_text(encoding="utf-8"))
    raw_plan["environment_fingerprint"].pop("docker_environment_path")
    plan = ExecutionPlan.model_validate(raw_plan)
    fingerprint = recompute_plan_fingerprint(plan)
    raw_plan["plan_fingerprint"] = fingerprint
    raw_plan["experiment_id"] = f"exp_20260823_{fingerprint[:8]}_1"
    plan_path.write_bytes(canonical_json_bytes(raw_plan))
    _reseal_candidate(candidate)

    with pytest.raises(PhaseECandidateError, match="differs across binding"):
        verify_phase_e_candidate(REPOSITORY, candidate)


def test_v2_verifier_rejects_seal_identity_tamper_with_valid_self_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = _create_worktree_v2_candidate(tmp_path, monkeypatch)
    seal_path = candidate / "candidate-seal.json"
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    seal["docker_environment_sha256"] = "0" * 64
    seal["seal_sha256"] = canonical_sha256(
        {key: value for key, value in seal.items() if key != "seal_sha256"}
    )
    seal_path.write_bytes(canonical_json_bytes(seal))

    with pytest.raises(PhaseECandidateError, match="differs across binding"):
        verify_phase_e_candidate(REPOSITORY, candidate)


def test_v2_verifier_rejects_missing_source_environment_blob(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = _create_worktree_v2_candidate(tmp_path, monkeypatch)
    original_git_bytes = phase_e._git_bytes
    environment_path = (
        "benchmarks/artifacts/profile-r-docker-judge-qualification-v15/"
        "docker-environment.json"
    )

    def missing_environment(repository: Path, commit: str, relative: str) -> bytes:
        if relative == environment_path:
            raise PhaseECandidateError("synthetic missing Docker environment blob")
        return original_git_bytes(repository, commit, relative)

    monkeypatch.setattr(phase_e, "_git_bytes", missing_environment)
    with pytest.raises(PhaseECandidateError, match="missing Docker environment blob"):
        verify_phase_e_candidate(REPOSITORY, candidate)


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


def test_company_profile_r_requalification_v15_is_exact_nine_cell_projection() -> None:
    path = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "profile-r-docker-judge-qualification-v15"
        / "qualification.json"
    )
    qualification = json.loads(path.read_text(encoding="utf-8"))
    environment = json.loads(
        (path.parent / "docker-environment.json").read_text(encoding="utf-8")
    )

    assert qualification["source_commit"] == "47d92e80fab04381e751de0847f7ff51c9218325"
    assert qualification["batch_id"] == "profile-r-docker-matrix-q18-company"
    assert qualification["status"] == "CHALLENGE_READY"
    assert qualification["challenge_ready"] is True
    assert qualification["model_turns"] == 0
    assert qualification["image_reference"].endswith(
        "@sha256:ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab"
    )
    assert [cell["ordinal"] for cell in qualification["cells"]] == list(range(1, 10))
    assert all(cell["matched_expectation"] is True for cell in qualification["cells"])
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
    assert environment["image"]["id"].endswith(
        qualification["image_reference"].split("@", 1)[1]
    )


def test_profile_r_redesign_q19_v16_is_exact_fourteen_cell_projection() -> None:
    path = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "profile-r-docker-judge-qualification-v16"
        / "qualification.json"
    )
    qualification = json.loads(path.read_text(encoding="utf-8"))
    environment = json.loads(
        (path.parent / "docker-environment.json").read_text(encoding="utf-8")
    )

    assert qualification["schema_version"] == 2
    assert qualification["source_commit"] == (
        "71713a1cb5713088df877e0b2485b1b8006ca930"
    )
    assert qualification["batch_id"] == (
        "profile-r-docker-matrix-q19-company-r01-r13"
    )
    assert qualification["status"] == "CHALLENGE_READY"
    assert qualification["challenge_ready"] is True
    assert qualification["model_turns"] == 0
    assert [cell["ordinal"] for cell in qualification["cells"]] == list(
        range(1, 15)
    )
    assert qualification["cells"][0]["variant_id"] == "reference"
    assert qualification["cells"][0]["aggregate_status"] == "pass"
    assert all(
        cell["matched_expectation"] is True for cell in qualification["cells"]
    )
    assert all(
        cell["aggregate_status"] == "fail"
        for cell in qualification["cells"][1:]
    )
    assert all(len(cell["properties"]) == 13 for cell in qualification["cells"])
    assert all(
        property_result["status"] != "blocked_by_prerequisite"
        for cell in qualification["cells"]
        for property_result in cell["properties"]
    )
    assert environment["qualification"] == {
        "source_commit": qualification["source_commit"],
        "batch_id": qualification["batch_id"],
        "status": "CHALLENGE_READY",
        "matched_expectations": 14,
        "cell_count": 14,
        "actual_model_turns": 0,
        "residual_profile_r_containers": 0,
    }
    assert environment["image"]["reference"] == qualification["image_reference"]
    assert environment["image"]["id"].endswith(
        qualification["image_reference"].split("@", 1)[1]
    )


def test_profile_r_redesign_q21_v18_is_exact_fourteen_cell_projection() -> None:
    path = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "profile-r-docker-judge-qualification-v18"
        / "qualification.json"
    )
    qualification = json.loads(path.read_text(encoding="utf-8"))
    environment = json.loads(
        (path.parent / "docker-environment.json").read_text(encoding="utf-8")
    )

    assert qualification["schema_version"] == 2
    assert qualification["source_commit"] == (
        "8d4627f75eca3233203ad906d2a19f1255591ee7"
    )
    assert qualification["batch_id"] == (
        "profile-r-docker-matrix-q21-company-r01-r13"
    )
    assert qualification["status"] == "CHALLENGE_READY"
    assert qualification["challenge_ready"] is True
    assert qualification["model_turns"] == 0
    assert [cell["ordinal"] for cell in qualification["cells"]] == list(
        range(1, 15)
    )
    assert qualification["cells"][0]["variant_id"] == "reference"
    assert qualification["cells"][0]["aggregate_status"] == "pass"
    assert all(
        cell["matched_expectation"] is True for cell in qualification["cells"]
    )
    assert all(
        cell["aggregate_status"] == "fail"
        for cell in qualification["cells"][1:]
    )
    assert environment["qualification"] == {
        "source_commit": qualification["source_commit"],
        "batch_id": qualification["batch_id"],
        "status": "CHALLENGE_READY",
        "matched_expectations": 14,
        "cell_count": 14,
        "actual_model_turns": 0,
        "residual_profile_r_containers": 0,
    }
    assert environment["image"]["reference"] == qualification["image_reference"]
    assert all(len(cell["properties"]) == 13 for cell in qualification["cells"])
    assert all(
        property_result["status"] != "blocked_by_prerequisite"
        for cell in qualification["cells"]
        for property_result in cell["properties"]
    )
    assert environment["image"]["id"].endswith(
        qualification["image_reference"].split("@", 1)[1]
    )


def test_profile_r_redesign_q22_v19_is_exact_fourteen_cell_projection() -> None:
    path = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "profile-r-docker-judge-qualification-v19"
        / "qualification.json"
    )
    qualification = json.loads(path.read_text(encoding="utf-8"))
    environment = json.loads(
        (path.parent / "docker-environment.json").read_text(encoding="utf-8")
    )

    assert qualification["schema_version"] == 2
    assert qualification["source_commit"] == (
        "202ece7ebe14a3fa37c9324e32351fb5f85ff8e3"
    )
    assert qualification["batch_id"] == (
        "profile-r-docker-matrix-q22-company-r01-r13"
    )
    assert qualification["status"] == "CHALLENGE_READY"
    assert qualification["challenge_ready"] is True
    assert qualification["model_turns"] == 0
    assert [cell["ordinal"] for cell in qualification["cells"]] == list(
        range(1, 15)
    )
    assert qualification["cells"][0]["variant_id"] == "reference"
    assert qualification["cells"][0]["aggregate_status"] == "pass"
    assert all(
        cell["matched_expectation"] is True for cell in qualification["cells"]
    )
    assert all(
        cell["aggregate_status"] == "fail"
        for cell in qualification["cells"][1:]
    )
    assert all(len(cell["properties"]) == 13 for cell in qualification["cells"])
    assert all(
        property_result["status"] != "blocked_by_prerequisite"
        for cell in qualification["cells"]
        for property_result in cell["properties"]
    )
    assert environment["qualification"] == {
        "source_commit": qualification["source_commit"],
        "batch_id": qualification["batch_id"],
        "status": "CHALLENGE_READY",
        "matched_expectations": 14,
        "cell_count": 14,
        "actual_model_turns": 0,
        "residual_profile_r_containers": 0,
    }
    assert environment["image"]["reference"] == qualification["image_reference"]
    assert environment["image"]["id"].endswith(
        qualification["image_reference"].split("@", 1)[1]
    )


def test_profile_r_redesign_q24_v21_is_exact_fourteen_cell_projection() -> None:
    path = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "profile-r-docker-judge-qualification-v21"
        / "qualification.json"
    )
    qualification = json.loads(path.read_text(encoding="utf-8"))
    environment = json.loads(
        (path.parent / "docker-environment.json").read_text(encoding="utf-8")
    )

    assert qualification["schema_version"] == 2
    assert qualification["source_commit"] == (
        "3a5bb87b54b09341125e9fbe15df248774595886"
    )
    assert qualification["batch_id"] == (
        "profile-r-docker-matrix-q24-company-r01-r13"
    )
    assert qualification["status"] == "CHALLENGE_READY"
    assert qualification["challenge_ready"] is True
    assert qualification["model_turns"] == 0
    assert [cell["ordinal"] for cell in qualification["cells"]] == list(
        range(1, 15)
    )
    assert qualification["cells"][0]["variant_id"] == "reference"
    assert qualification["cells"][0]["aggregate_status"] == "pass"
    assert all(
        cell["matched_expectation"] is True for cell in qualification["cells"]
    )
    assert all(
        cell["aggregate_status"] == "fail"
        for cell in qualification["cells"][1:]
    )
    assert all(len(cell["properties"]) == 13 for cell in qualification["cells"])
    assert all(
        property_result["status"] != "blocked_by_prerequisite"
        for cell in qualification["cells"]
        for property_result in cell["properties"]
    )
    assert environment["qualification"] == {
        "source_commit": qualification["source_commit"],
        "batch_id": qualification["batch_id"],
        "status": "CHALLENGE_READY",
        "matched_expectations": 14,
        "cell_count": 14,
        "actual_model_turns": 0,
        "residual_profile_r_containers": 0,
    }
    assert environment["image"]["reference"] == qualification["image_reference"]
    assert environment["image"]["id"].endswith(
        qualification["image_reference"].split("@", 1)[1]
    )


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
    assert bindings.schema_version == 3
    profile_r = bindings.profiles[0]
    assert profile_r.qualification_sha256 == (
        "2c93d1029c4d6efb8caa52692c4a9d83c04da881e84cee83f6aa95b48383dec3"
    )
    assert profile_r.task_pack_qualification_sha256 == (
        "6dad99081990a188a5c32351eca297d38036f331cb85d2a8a55c719031ed9c66"
    )
    assert profile_r.task_pack_qualification_seal_sha256 == (
        "2a61a30beee918cbbc6969e8e3a75a461a6999f4b2cb81f5f689a09adb56b027"
    )
    assert profile_r.task_budget_sha256 == (
        "a0872bb16e0215e7ee864e83778bac211b06a459506de63a8a93546d69a33794"
    )
    assert profile_r.task_budget_seal_sha256 == (
        "2f1eeb6c43dbf0672a1ba756db2598573c6b3e2f92385e08381f762aa6f5c39d"
    )
    assert plan.decision_policy["planned_initial_model_turns"] == 42
    assert plan.decision_policy["planned_model_turn_ceiling"] == 50
    assert plan.environment_fingerprint[
        "profile_r_task_pack_qualification_seal_sha256"
    ] == profile_r.task_pack_qualification_seal_sha256
    assert plan.environment_fingerprint[
        "profile_r_task_budget_seal_sha256"
    ] == profile_r.task_budget_seal_sha256
    candidate = tmp_path / "candidate"
    seal = create_phase_e_candidate(
        REPOSITORY,
        candidate,
        source_commit=source_commit,
        preflight=_preflight(),
        created_at=created_at,
    )
    assert seal.schema_version == 3
    assert seal.planned_initial_model_turns == 42
    assert seal.planned_model_turn_ceiling == 50
    assert seal.actual_model_turns == 0
    assert verify_phase_e_candidate(REPOSITORY, candidate) == seal
    with (candidate / "stage-manifest.json").open("ab") as stream:
        stream.write(b"\n")
    with pytest.raises(PhaseECandidateError, match="payload bytes changed"):
        verify_phase_e_candidate(REPOSITORY, candidate)


def test_checked_in_original_v1_candidate_remains_byte_compatible() -> None:
    candidate = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "sdk-routing-realistic-high-difficulty-phase-e-v1"
    )
    seal = verify_phase_e_candidate(REPOSITORY, candidate)

    assert seal.schema_version == 1
    assert seal.source_commit == "79f9100125e2d5f6cecb3fe00b93e461afe1cdfd"
    assert seal.experiment_id == "exp_20260812_77e111e8_1"
    assert seal.seal_sha256 == (
        "1e93ef12f11f7f05902ba7f0e25708f72dc9ed2e65ccea74956938caa5e57fc7"
    )
    assert seal.docker_environment_path is None
    assert seal.docker_environment_sha256 is None
    assert seal.actual_model_turns == 0


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
    plan = json.loads((candidate / "execution-plan.json").read_text(encoding="utf-8"))

    assert seal.schema_version == 1
    assert seal.source_commit == "c5e1ae2df58554970ffd98d17946ac94393c3a5d"
    assert seal.docker_environment_path is None
    assert seal.docker_environment_sha256 is None
    assert bindings["schema_version"] == 1
    assert all("docker_environment_path" not in item for item in bindings["profiles"])
    assert all("docker_environment_sha256" not in item for item in bindings["profiles"])
    assert "docker_environment_path" not in plan["environment_fingerprint"]
    assert "docker_environment_sha256" not in plan["environment_fingerprint"]
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


def test_checked_in_environment_bound_v15_candidate_verifies_against_its_source_commit() -> None:
    candidate = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "sdk-routing-realistic-high-difficulty-phase-e-v15"
    )
    seal = verify_phase_e_candidate(REPOSITORY, candidate)
    bindings = json.loads((candidate / "source-bindings.json").read_text(encoding="utf-8"))
    plan = json.loads((candidate / "execution-plan.json").read_text(encoding="utf-8"))
    profile_r, profile_i = bindings["profiles"]
    expected_path = (
        "benchmarks/artifacts/profile-r-docker-judge-qualification-v14/"
        "docker-environment.json"
    )
    expected_sha = "70c43e4993cb2ccb520d150b94fe11f154b36e7232ee9be6b3e531f89e0ef1b5"

    assert seal.schema_version == 2
    assert seal.source_commit == "c7fde69d9e873bd8a8a3db8e73619660c1844883"
    assert bindings["source_tree"] == "4c678371c1f1532fd9d120831b9fc50e23970d25"
    assert bindings["bindings_sha256"] == (
        "a1b1df5b0f9e6afae66d135082c0f599362040e04618cd665550db8997a58787"
    )
    assert profile_r["docker_environment_path"] == expected_path
    assert profile_r["docker_environment_sha256"] == expected_sha
    assert "docker_environment_path" not in profile_i
    assert "docker_environment_sha256" not in profile_i
    assert plan["environment_fingerprint"]["docker_environment_path"] == expected_path
    assert plan["environment_fingerprint"]["docker_environment_sha256"] == expected_sha
    assert seal.docker_environment_path == expected_path
    assert seal.docker_environment_sha256 == expected_sha
    assert seal.experiment_id == "exp_20260823_c09b6abc_1"
    assert seal.plan_fingerprint == (
        "c09b6abcd5264b115b7d575a049b806f1f9caa700be037438cc550c5aafbce90"
    )
    assert seal.seal_sha256 == (
        "2af49f567071bc0694fa965f12f34bcfb616c6ebda97f4b491fedbdb54b6df0d"
    )
    assert seal.files_manifest_sha256 == (
        "4c87754ebaa95157e20981d5d28a6204830f303b76997b6801fe1ecb24d7afc3"
    )
    assert sha256((candidate / "candidate-seal.json").read_bytes()).hexdigest() == (
        "8d638023b2daf1a030095dd7153007eac91faa07fb5d5246e80b9aad0cbd231d"
    )
    assert seal.actual_model_turns == 0


def test_checked_in_company_environment_bound_v16_candidate_verifies() -> None:
    candidate = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "sdk-routing-realistic-high-difficulty-phase-e-v16"
    )
    seal = verify_phase_e_candidate(REPOSITORY, candidate)
    bindings = json.loads(
        (candidate / "source-bindings.json").read_text(encoding="utf-8")
    )
    plan = json.loads((candidate / "execution-plan.json").read_text(encoding="utf-8"))
    expected_environment = (
        "benchmarks/artifacts/profile-r-docker-judge-qualification-v15/"
        "docker-environment.json"
    )

    assert seal.schema_version == 2
    assert seal.source_commit == "cb691e56c8cd439e494f5519ebae65ccda669ed2"
    assert seal.experiment_id == "exp_20260825_f944f0e1_1"
    assert seal.plan_fingerprint == (
        "f944f0e16a6b14a209430a592efa67c5d1029edac1812c141eb663951135a9c0"
    )
    assert seal.seal_sha256 == (
        "2449166fdba9937cf09411a92f47904e7908e1b6869ae8732fd0c1dec251d80d"
    )
    assert seal.files_manifest_sha256 == (
        "a2e0ac54a6d2969daae0c67aeb5f1ed2557a72820f5cfa7239c58473fa848dec"
    )
    assert seal.docker_environment_path == expected_environment
    assert seal.docker_environment_sha256 == (
        "e14c6dd61e0dc85b0a9e459af00b6451f1bdbe51935745a8e6ba6b3fb45692e3"
    )
    assert seal.actual_model_turns == 0
    assert bindings["source_tree"] == "6c578c3c5d55ad96f54323afae7b99093b5c3035"
    assert bindings["bindings_sha256"] == (
        "b78b2afeebf657e348ed17e07e91c351572769b58e2ad2155fff1f84ec1de02d"
    )
    assert plan["environment_fingerprint"]["docker_environment_path"] == (
        expected_environment
    )
    assert sha256((candidate / "candidate-seal.json").read_bytes()).hexdigest() == (
        "88a478b3f35312d6cd826de2a3091366e2b5a94328f844c16da4993c12974d86"
    )


def test_checked_in_profile_r_redesign_v17_candidate_verifies() -> None:
    candidate = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "sdk-routing-realistic-high-difficulty-phase-e-v17"
    )
    seal = verify_phase_e_candidate(REPOSITORY, candidate)
    bindings = json.loads(
        (candidate / "source-bindings.json").read_text(encoding="utf-8")
    )
    plan = json.loads((candidate / "execution-plan.json").read_text(encoding="utf-8"))
    profile_r = bindings["profiles"][0]

    assert seal.schema_version == 3
    assert seal.source_commit == "e09652b69730cf30b4e9b363c44bd79c40afdb12"
    assert seal.experiment_id == "exp_20260826_3d512c44_1"
    assert seal.plan_fingerprint == (
        "3d512c44d88892b7abc0cc13390d33bd5e291fb2c69e01391dda32b3cc2fd017"
    )
    assert seal.seal_sha256 == (
        "5a460cfc47d5a52988d0a10527a4b7cf3bba88e02cf83ea9204da73e9ad922f7"
    )
    assert seal.files_manifest_sha256 == (
        "9b0fc0cd4497b64dac7cbf08260481c0c74277812a8d4fb4e4014c9083679f95"
    )
    assert seal.planned_initial_model_turns == 42
    assert seal.planned_model_turn_ceiling == 50
    assert seal.actual_model_turns == 0
    assert bindings["source_tree"] == "2335871b436bed7f6113270498983a35adcc52a0"
    assert bindings["bindings_sha256"] == (
        "4517a004944e25904a8719c13500e4bd2bbd6def0c7a81894c91d44aaa213f7e"
    )
    assert profile_r["task_count"] == 13
    assert profile_r["qualification_sha256"] == (
        "2afc443afe5f0604ce9b7b1bd4765826d97d7bbbb54a706b699583fcc9fcc648"
    )
    assert profile_r["task_pack_qualification_seal_sha256"] == (
        "ad803c61aecf533eccba6d6690dc9945bbf2212724df81e66cf5272e894738dc"
    )
    assert profile_r["task_budget_seal_sha256"] == (
        "756c984117324a4f875231d565b92979e1e8d9e8fc6457a80c0d3288dcfdfbd6"
    )
    assert plan["environment_fingerprint"][
        "profile_r_task_pack_qualification_seal_sha256"
    ] == profile_r["task_pack_qualification_seal_sha256"]
    assert plan["environment_fingerprint"][
        "profile_r_task_budget_seal_sha256"
    ] == profile_r["task_budget_seal_sha256"]
    assert sha256((candidate / "candidate-seal.json").read_bytes()).hexdigest() == (
        "ed1ed4af631dda0f12cc62ec8452e6d1dd03f7a9ac6330a7041b0b59b38557b1"
    )


def test_checked_in_profile_r_p1_hardened_v18_candidate_verifies() -> None:
    candidate = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "sdk-routing-realistic-high-difficulty-phase-e-v18"
    )
    seal = verify_phase_e_candidate(REPOSITORY, candidate)
    bindings = json.loads(
        (candidate / "source-bindings.json").read_text(encoding="utf-8")
    )
    plan = json.loads((candidate / "execution-plan.json").read_text(encoding="utf-8"))
    profile_r = bindings["profiles"][0]

    assert seal.schema_version == 3
    assert seal.source_commit == "7d0b35d057ae84fc005fd3cf3e8bf9df310f05b7"
    assert seal.experiment_id == "exp_20260901_d7869ee7_1"
    assert seal.plan_fingerprint == (
        "d7869ee7bca8ee6339f62f8d0d080bbf9f815b10e092261faac44e37c6643742"
    )
    assert seal.seal_sha256 == (
        "dd7db2bcbd17ab8aef4c2128ee165ba1a0c2ed08fa9b1665a98922a760a619fe"
    )
    assert seal.files_manifest_sha256 == (
        "fdcb1f30238605db03123fda523bb638eba93cf053f2a01fa9ff68afb46210bf"
    )
    assert seal.planned_initial_model_turns == 42
    assert seal.planned_model_turn_ceiling == 50
    assert seal.actual_model_turns == 0
    assert bindings["source_tree"] == "c01e7175af1414b380c9c9870dfbce37e14e0bed"
    assert bindings["bindings_sha256"] == (
        "d104d2cd4fe9a9276431abbe509d9563fdc9db3e9d8c449ebb01342b04c4149e"
    )
    assert profile_r["task_count"] == 13
    assert profile_r["qualification_sha256"] == (
        "2afc443afe5f0604ce9b7b1bd4765826d97d7bbbb54a706b699583fcc9fcc648"
    )
    assert profile_r["task_pack_qualification_seal_sha256"] == (
        "ad803c61aecf533eccba6d6690dc9945bbf2212724df81e66cf5272e894738dc"
    )
    assert profile_r["task_budget_seal_sha256"] == (
        "756c984117324a4f875231d565b92979e1e8d9e8fc6457a80c0d3288dcfdfbd6"
    )
    assert plan["environment_fingerprint"][
        "profile_r_task_pack_qualification_seal_sha256"
    ] == profile_r["task_pack_qualification_seal_sha256"]
    assert plan["environment_fingerprint"][
        "profile_r_task_budget_seal_sha256"
    ] == profile_r["task_budget_seal_sha256"]
    assert sha256((candidate / "candidate-seal.json").read_bytes()).hexdigest() == (
        "59651c8bccba8b4e5d42fa68aa2d5a6658d6c5dd4aa2e5ea78879ac79a69c2dd"
    )


def test_checked_in_profile_r_q21_q2_v19_candidate_verifies() -> None:
    candidate = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "sdk-routing-realistic-high-difficulty-phase-e-v19"
    )
    seal = verify_phase_e_candidate(REPOSITORY, candidate)
    bindings = json.loads(
        (candidate / "source-bindings.json").read_text(encoding="utf-8")
    )
    plan = json.loads((candidate / "execution-plan.json").read_text(encoding="utf-8"))
    profile_r = bindings["profiles"][0]

    assert seal.schema_version == 3
    assert seal.source_commit == "e3f59b125e89a473b2e68ec18dbb0f099cded67e"
    assert seal.experiment_id == "exp_20260901_2c5e0215_1"
    assert seal.plan_fingerprint == (
        "2c5e02150a577c5066de019ea51e45871c562ec9ceb19966708151248aeb1961"
    )
    assert seal.seal_sha256 == (
        "dfb6b4a878630c5ebd70c212065a3af64d55d3e3bf7b919c726c163f8485f869"
    )
    assert seal.files_manifest_sha256 == (
        "5f586a9d711073bcecefd5da9c8fab0869dbe2673f3b07a85817919b9ffd72c8"
    )
    assert seal.planned_initial_model_turns == 42
    assert seal.planned_model_turn_ceiling == 50
    assert seal.actual_model_turns == 0
    assert bindings["source_tree"] == "ca7d83a376d35a6bc29482a1590f4acbf72ec685"
    assert bindings["bindings_sha256"] == (
        "8fe908ed19b2f780bbd412504cf0e954f03eab8dbd5c4d26c04e01d7b628c2a2"
    )
    assert profile_r["task_count"] == 13
    assert profile_r["qualification_sha256"] == (
        "27d49bf2cfb218dce77270d6f0a943f846023000adccf9db3372e3883c23d554"
    )
    assert profile_r["task_pack_qualification_sha256"] == (
        "487f7691d4cce64db8d7b997164ca45179df3186e0c4ed7eed99db5c8c2964f9"
    )
    assert profile_r["task_pack_qualification_seal_sha256"] == (
        "61181ffa0867c67b7d087059f777d5838f5c61a3d6250d45422c04d945312c11"
    )
    assert profile_r["task_budget_sha256"] == (
        "3e2dbd5c8bdc040c5b57d1aaac3dd9473d929b83f35f4e7bc4c09b91c94c146d"
    )
    assert profile_r["task_budget_seal_sha256"] == (
        "0a1f77373b5db871c3a1967834fac5985ce38d6e8cb2511a5165cafb638df60b"
    )
    assert plan["environment_fingerprint"][
        "profile_r_task_pack_qualification_seal_sha256"
    ] == profile_r["task_pack_qualification_seal_sha256"]
    assert plan["environment_fingerprint"][
        "profile_r_task_budget_seal_sha256"
    ] == profile_r["task_budget_seal_sha256"]
    assert sha256((candidate / "candidate-seal.json").read_bytes()).hexdigest() == (
        "7937338cc885f5e3693fe30422c39068a5c22c0d0a423e20676b90d1abe597ce"
    )


def test_checked_in_profile_r_q22_q3_v20_candidate_verifies() -> None:
    candidate = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "sdk-routing-realistic-high-difficulty-phase-e-v20"
    )
    seal = verify_phase_e_candidate(REPOSITORY, candidate)
    bindings = json.loads(
        (candidate / "source-bindings.json").read_text(encoding="utf-8")
    )
    plan = json.loads((candidate / "execution-plan.json").read_text(encoding="utf-8"))
    profile_r = bindings["profiles"][0]

    assert seal.schema_version == 3
    assert seal.source_commit == "df5c6648b3ecbf10d243484b033c7827587b3600"
    assert seal.experiment_id == "exp_20260902_16d616c2_1"
    assert seal.plan_fingerprint == (
        "16d616c2585e24f0929ed7d68f61de341d4fcf40eb62eb5b2beb7c42ebea14d2"
    )
    assert seal.seal_sha256 == (
        "1745413dd71e3f6d7a9232c4e166f0ec4e058c97671ec59815cff319f85697a7"
    )
    assert seal.files_manifest_sha256 == (
        "bf0a62ffec621fa762dfa857fcdd9ebd24f1e1cdf14bba57dd767d0033e6a224"
    )
    assert seal.planned_initial_model_turns == 42
    assert seal.planned_model_turn_ceiling == 50
    assert seal.actual_model_turns == 0
    assert bindings["source_tree"] == "a8ecfa70f4b97d68e7067a8a72ab82edda2214ae"
    assert bindings["bindings_sha256"] == (
        "4707cb18de97b7250a9ff917e244a02300fb61a98eb7829f151800a7b35b473d"
    )
    assert profile_r["task_count"] == 13
    assert profile_r["qualification_sha256"] == (
        "b4e0753d99572221c9d9edc1b7fda12d30237e87b6eaf6e9d4dc00b459fac40f"
    )
    assert profile_r["qualification_seal_sha256"] == (
        "553d5327f04000f2d605056d627b03e2ed713f8da5f6ccb65437232d0d8ad397"
    )
    assert profile_r["docker_environment_sha256"] == (
        "e6c5e425c4defcc092b5198d7efc8fbdb8deb6beaa69b2f4d18ca061a9d28822"
    )
    assert profile_r["task_pack_qualification_sha256"] == (
        "601a699e8c7b073a572db0079209eedd4180fea0707e69223758d93f811eb992"
    )
    assert profile_r["task_pack_qualification_seal_sha256"] == (
        "724558225db9917f8963b3c54cefef92407192ad529cdf07c621796e5866ec62"
    )
    assert profile_r["task_budget_sha256"] == (
        "43ef9eddc225fcd4dac9e03e5196bd2a90c6b36ef6b3d6f079c4f5607430d39f"
    )
    assert profile_r["task_budget_seal_sha256"] == (
        "5cb10ca6d7dbcba20edfbfa3362e129d19230cff6e0fbdccac01accb54fb0c2d"
    )
    assert plan["environment_fingerprint"][
        "profile_r_task_pack_qualification_seal_sha256"
    ] == profile_r["task_pack_qualification_seal_sha256"]
    assert plan["environment_fingerprint"][
        "profile_r_task_budget_seal_sha256"
    ] == profile_r["task_budget_seal_sha256"]
    assert sha256((candidate / "candidate-seal.json").read_bytes()).hexdigest() == (
        "bfbd5e491c48b5cf3fa4a465b399b0afe740ca6ebbe219d4a3c8b5ca23ca5176"
    )


def test_checked_in_profile_r_q24_q4_v21_candidate_verifies() -> None:
    candidate = (
        REPOSITORY
        / "benchmarks"
        / "artifacts"
        / "sdk-routing-realistic-high-difficulty-phase-e-v21"
    )
    seal = verify_phase_e_candidate(REPOSITORY, candidate)
    bindings = json.loads(
        (candidate / "source-bindings.json").read_text(encoding="utf-8")
    )
    profile_r = bindings["profiles"][0]

    assert seal.schema_version == 3
    assert seal.source_commit == "d229827fae3addd1e42487a27e4068d47620be71"
    assert seal.experiment_id == "exp_20260902_697bf1d0_1"
    assert seal.plan_fingerprint == (
        "697bf1d00157b7c0c9bc74890f6c3703fda81b0b481a94c8613512e8d1625712"
    )
    assert seal.seal_sha256 == (
        "8e8a814934359d6ab59f08b57989054f77117f01938ca80810a6113384c479a7"
    )
    assert seal.files_manifest_sha256 == (
        "71441c26af8b1b33c645472bb05bfe3a1d975fde5bda4bcff7bfc7f06d369aa3"
    )
    assert seal.actual_model_turns == 0
    assert bindings["source_tree"] == "bd456ceff9ff857940a55d2b83ddcf7b51f54a73"
    assert bindings["bindings_sha256"] == (
        "5c97703007e336c8f8a69ff2b5e3836e223c4d0de8af86718e14a157d7a5d1c9"
    )
    assert profile_r["qualification_sha256"] == (
        "2c93d1029c4d6efb8caa52692c4a9d83c04da881e84cee83f6aa95b48383dec3"
    )
    assert profile_r["qualification_seal_sha256"] == (
        "d61d6dd8335f21d186ef0eaf0943ef0a0d5c50b4285c8cb21474445b420536bd"
    )
    assert profile_r["docker_environment_sha256"] == (
        "0bd6b3d8e36ea36b59b98a740fccd24b46d3ad1c3aeb6c9657bc97f21aa191c0"
    )
    assert profile_r["task_pack_qualification_sha256"] == (
        "6dad99081990a188a5c32351eca297d38036f331cb85d2a8a55c719031ed9c66"
    )
    assert profile_r["task_pack_qualification_seal_sha256"] == (
        "2a61a30beee918cbbc6969e8e3a75a461a6999f4b2cb81f5f689a09adb56b027"
    )
    assert profile_r["task_budget_sha256"] == (
        "a0872bb16e0215e7ee864e83778bac211b06a459506de63a8a93546d69a33794"
    )
    assert profile_r["task_budget_seal_sha256"] == (
        "2f1eeb6c43dbf0672a1ba756db2598573c6b3e2f92385e08381f762aa6f5c39d"
    )
    assert sha256((candidate / "candidate-seal.json").read_bytes()).hexdigest() == (
        "342df792e9e869615affc7b364236b5489c15d4e04b0adfe474196f106961357"
    )
