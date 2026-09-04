from __future__ import annotations

import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest

from benchmark_runner.profile_r_redesign import (
    PROFILE_R_TASK_IDS,
    ProfileRRedesignError,
    apply_reference_task_diff,
    assert_worker_information_boundary,
    canonical_json,
    project_change_surface,
    qualify_reference_chain,
    sha256,
    working_tree_hash,
)
from benchmark_runner.realistic_phase_e import PhaseEStageManifest


def _git(root: Path, *arguments: str) -> str:
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_AUTHOR_NAME": "profile-r-test",
            "GIT_AUTHOR_EMAIL": "profile-r@test.invalid",
            "GIT_COMMITTER_NAME": "profile-r-test",
            "GIT_COMMITTER_EMAIL": "profile-r@test.invalid",
            "GIT_AUTHOR_DATE": "2026-01-01T00:00:00+00:00",
            "GIT_COMMITTER_DATE": "2026-01-01T00:00:00+00:00",
        }
    )
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()


def _reference_repository(tmp_path: Path) -> tuple[Path, str, dict[str, str]]:
    root = tmp_path / "reference"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "core.autocrlf", "false")
    (root / "base.txt").write_text("base\n", encoding="utf-8", newline="\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "base")
    base = _git(root, "rev-parse", "HEAD")
    commits = {}
    for task_id in PROFILE_R_TASK_IDS:
        path = root / f"{task_id}.txt"
        path.write_text(f"{task_id}\n", encoding="utf-8", newline="\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", task_id)
        commits[task_id] = _git(root, "rev-parse", "HEAD")
    return root, base, commits


def test_change_surface_and_cumulative_checks_are_deterministic() -> None:
    tasks = []
    for task_id in PROFILE_R_TASK_IDS:
        tasks.append(
            {
                "key": task_id,
                "own_check": f"{task_id.lower()}_contract",
                "write_scope": [f"{task_id}.txt"],
            }
        )
    assert project_change_surface({"tasks": tasks}) == {
        "schema_version": 2,
        "tasks": [
            {"task_id": task_id, "write_paths": [f"{task_id}.txt"]}
            for task_id in PROFILE_R_TASK_IDS
        ],
    }


def test_reference_chain_seals_every_intermediate_tree(tmp_path: Path) -> None:
    root, base, commits = _reference_repository(tmp_path)
    seal = qualify_reference_chain(
        root,
        base_commit=base,
        task_commits=commits,
        task_write_scopes={
            task_id: [f"{task_id}.txt"] for task_id in PROFILE_R_TASK_IDS
        },
    )
    assert list(seal["reference_chain"]) == ["base", *PROFILE_R_TASK_IDS]
    assert len(seal["seal_sha256"]) == 64

    worker = tmp_path / "worker"
    subprocess.run(
        ["git", "clone", "-q", str(root), str(worker)],
        check=True,
        capture_output=True,
    )
    _git(worker, "config", "core.longpaths", "true")
    _git(worker, "checkout", "-q", base)
    assert apply_reference_task_diff(
        reference_repository=root,
        worker_repository=worker,
        parent=base,
        child=commits["R01"],
        expected_tree=str(seal["reference_chain"]["R01"]["tree"]),
    ) == seal["reference_chain"]["R01"]["tree"]


def test_reference_chain_rejects_scope_escape(tmp_path: Path) -> None:
    root, base, commits = _reference_repository(tmp_path)
    scopes = {task_id: [f"{task_id}.txt"] for task_id in PROFILE_R_TASK_IDS}
    scopes["R13"] = ["different.txt"]
    with pytest.raises(ProfileRRedesignError, match="escaped write scope"):
        qualify_reference_chain(
            root,
            base_commit=base,
            task_commits=commits,
            task_write_scopes=scopes,
        )


def test_working_tree_hash_uses_uncommitted_bytes(tmp_path: Path) -> None:
    root, _base, _commits = _reference_repository(tmp_path)
    committed = _git(root, "rev-parse", "HEAD^{tree}")
    (root / "R13.txt").write_text("changed\n", encoding="utf-8", newline="\n")
    assert working_tree_hash(root) != committed
    assert _git(root, "fsck", "--no-reflogs", "--unreachable") == ""


def test_worker_information_boundary_rejects_review_and_hidden_objects(
    tmp_path: Path,
) -> None:
    worker = tmp_path / "worker"
    worker.mkdir()
    (worker / "allowed.txt").write_text("ok\n", encoding="utf-8")
    assert_worker_information_boundary(worker)
    leaked = worker / "docs/reviews/profile-r.txt"
    leaked.parent.mkdir(parents=True)
    leaked.write_text("answer\n", encoding="utf-8")
    with pytest.raises(ProfileRRedesignError, match="leaked"):
        assert_worker_information_boundary(worker)


def _phase_e_v3_stage() -> dict[str, object]:
    repository = Path(__file__).resolve().parents[3]
    path = (
        repository
        / "benchmarks/suites/sdk-routing-realistic-high-difficulty-v1/stages"
        / "realistic-high-difficulty-initial.json"
    )
    value = json.loads(path.read_text(encoding="utf-8"))
    value["schema_version"] = 3
    profile_r = value["profiles"][0]
    profile_r["task_count"] = 13
    profile_r["task_pack_qualification_path"] = (
        "benchmarks/artifacts/profile-r-task-pack-q1/qualification.json"
    )
    profile_r["task_budget_path"] = (
        "benchmarks/artifacts/profile-r-task-pack-q1/task-budget.json"
    )
    value["budget"] = {
        "task_initial_turns": 1,
        "task_extra_turn_ceiling": 1,
        "variant_extra_turn_ceiling": 2,
        "base_turns_per_variant": 13,
        "total_turn_ceiling_per_variant": 15,
        "total_initial_turns": 42,
        "total_turn_ceiling": 50,
        "model_active_seconds_ceiling_per_variant": 7200,
        "wall_clock_seconds_ceiling_per_variant": 9000,
        "unused_reserve_transfer": "forbidden",
        "profile_budgets": [
                {
                    "profile_id": "repository-wide-compatibility-migration",
                    "task_count": 13,
                    "base_turns_per_variant": 13,
                    "total_turn_ceiling_per_variant": 15,
                },
                {
                    "profile_id": "evidence-bound-incident-repair",
                    "task_count": 8,
                    "base_turns_per_variant": 8,
                    "total_turn_ceiling_per_variant": 10,
                },
        ],
    }
    return value


def test_phase_e_v3_requires_direct_task_pack_and_budget_bindings() -> None:
    stage = PhaseEStageManifest.model_validate(_phase_e_v3_stage())
    assert [profile.task_count for profile in stage.profiles] == [13, 8]
    assert stage.budget.total_initial_turns == 42
    assert stage.budget.total_turn_ceiling == 50

    missing = _phase_e_v3_stage()
    del missing["profiles"][0]["task_pack_qualification_path"]
    with pytest.raises(ValueError, match="redesign artifacts are missing"):
        PhaseEStageManifest.model_validate(missing)


def test_task_budget_requires_ready_q1_and_seals_equal_variant_deadlines(
    tmp_path: Path,
) -> None:
    repository = Path(__file__).resolve().parents[3]
    script = repository / "tools/benchmark-runner/scripts/build_profile_r_task_budget.py"
    spec = importlib.util.spec_from_file_location("profile_r_task_budget", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    q1_path = tmp_path / "qualification.json"
    qualification = {
        "model_turns": 0,
        "seal_sha256": "a" * 64,
        "snapshot_id": "realistic-compat-migration-001",
        "status": "STRUCTURE_READY",
        "task_ids": list(PROFILE_R_TASK_IDS),
    }
    q1_path.write_text(json.dumps(qualification), encoding="utf-8")
    with pytest.raises(RuntimeError, match="not ready"):
        module.build_budget(q1_path)

    qualification["status"] = "TASK_PACK_READY"
    q1_path.write_text(json.dumps(qualification), encoding="utf-8")
    budget = module.build_budget(q1_path)
    assert budget["schema_version"] == 2
    assert budget["budget_mode"] == "cell_completion_deadline"
    assert budget["cell_completion_deadline_seconds"] == 9000
    assert budget["hard_limit_fields"] == ["cell_completion_deadline_seconds"]
    assert "actual_model_turns" in budget["measurement_only_fields"]
    assert "per_task_maximum_turns" not in budget
    assert "maximum_actual_model_turns_per_cell" not in budget
    assert "retry_resume_maximum_turns" not in budget
    assert budget["ss1_b1_identical"] is True


def test_task_pack_qualification_id_can_advance_without_changing_q1_default() -> None:
    repository = Path(__file__).resolve().parents[3]
    script = repository / "tools/benchmark-runner/scripts/qualify_profile_r_task_pack.py"
    spec = importlib.util.spec_from_file_location("profile_r_task_pack", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    q1 = module.qualify(repository)
    q2 = module.qualify(
        repository,
        qualification_id="profile-r-task-pack-q2",
    )
    assert q1["qualification_id"] == "profile-r-task-pack-q1"
    assert q2["qualification_id"] == "profile-r-task-pack-q2"
    assert q1["seal_sha256"] != q2["seal_sha256"]
    with pytest.raises(RuntimeError, match="ID is invalid"):
        module.qualify(
            repository,
            qualification_id="profile-r-task-pack-latest",
        )


def test_task_pack_stdout_projection_excludes_transient_temp_paths() -> None:
    repository = Path(__file__).resolve().parents[3]
    script = repository / "tools/benchmark-runner/scripts/qualify_profile_r_task_pack.py"
    spec = importlib.util.spec_from_file_location("profile_r_task_pack_projection", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def payload(temp_root: str, deepest: str, growth: str) -> bytes:
        evidence = {
            "schema_version": 1,
            "temp_root": temp_root,
            "deepest_path": deepest,
            "growth_probe_path": growth,
            "growth_probe_path_length": 300,
            "probe_repository_path_length": 120,
            "growth_margin": 40,
            "pytest": {
                "tests": 7,
                "failures": 0,
                "errors": 0,
                "skipped": 0,
                "warnings": 0,
            },
        }
        return (
            "CHECK_DIAGNOSTIC_RESULT:{}\n"
            "CHECK_ENVIRONMENT_EVIDENCE:"
            + json.dumps(evidence, sort_keys=True, separators=(",", ":"))
            + "\nWORKER_FEEDBACK:"
            + temp_root
            + "\nR11_PUBLIC_CONTRACT_OK\n"
        ).encode("utf-8")

    first = module._public_check_stdout_projection(
        payload("C:/temp/one", "C:/temp/one/deep", "C:/temp/one/growth")
    )
    second = module._public_check_stdout_projection(
        payload("D:/other/two", "D:/other/two/deep", "D:/other/two/growth")
    )

    assert first == second


def test_repository_reference_bundle_matches_chain_and_self_seals(
    tmp_path: Path,
) -> None:
    repository = Path(__file__).resolve().parents[3]
    root = (
        repository
        / "benchmarks/reference-source/sdk-routing-realistic-high-difficulty-v1"
        / "realistic-compat-migration-001"
    )
    manifest = json.loads(
        (root / "reference-repository-manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["seal_sha256"] == sha256(
        canonical_json(
            {key: value for key, value in manifest.items() if key != "seal_sha256"}
        )
    )
    for field in ("bundle", "chain", "chain_seal"):
        record = manifest[field]
        assert sha256((root / record["path"]).read_bytes()) == record["sha256"]
    clone = tmp_path / "reference"
    subprocess.run(
        ["git", "clone", "-q", str(root / manifest["bundle"]["path"]), str(clone)],
        check=True,
        capture_output=True,
    )
    _git(clone, "config", "core.longpaths", "true")
    chain = json.loads((root / manifest["chain"]["path"]).read_text(encoding="utf-8"))
    run = json.loads(json.dumps(chain))
    seal = json.loads(
        (root / manifest["chain_seal"]["path"]).read_text(encoding="utf-8")
    )
    recomputed = qualify_reference_chain(
        clone,
        base_commit=str(run["base_commit"]),
        task_commits={
            str(item["task_id"]): str(item["commit"])
            for item in run["tasks"]
        },
        task_write_scopes={
            task_id: [
                str(effect["path"])
                for effect in seal["reference_chain"][task_id]["effects"]
            ]
            for task_id in PROFILE_R_TASK_IDS
        },
    )
    assert recomputed == seal


@pytest.mark.parametrize(
    ("artifact_name", "qualification_id"),
    (
        ("profile-r-task-pack-q1", "profile-r-task-pack-q1"),
        ("profile-r-task-pack-q2", "profile-r-task-pack-q2"),
        ("profile-r-task-pack-q3", "profile-r-task-pack-q3"),
        ("profile-r-task-pack-q4", "profile-r-task-pack-q4"),
        ("profile-r-task-pack-q5", "profile-r-task-pack-q5"),
        ("profile-r-task-pack-q6", "profile-r-task-pack-q6"),
        ("profile-r-task-pack-q7", "profile-r-task-pack-q7"),
    ),
)
def test_task_pack_artifact_and_budget_are_self_sealed(
    artifact_name: str,
    qualification_id: str,
) -> None:
    repository = Path(__file__).resolve().parents[3]
    root = repository / "benchmarks/artifacts" / artifact_name
    manifest = json.loads(
        (root / "artifact-manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["seal_sha256"] == sha256(
        canonical_json(
            {key: value for key, value in manifest.items() if key != "seal_sha256"}
        )
    )
    for field in ("qualification", "task_budget"):
        record = manifest[field]
        payload = (root / record["path"]).read_bytes()
        assert len(payload) == record["size"]
        assert sha256(payload) == record["sha256"]
        value = json.loads(payload.decode("utf-8"))
        assert value["seal_sha256"] == record["seal_sha256"]
        assert value["seal_sha256"] == sha256(
            canonical_json(
                {key: item for key, item in value.items() if key != "seal_sha256"}
            )
        )
    qualification = json.loads(
        (root / "qualification.json").read_text(encoding="utf-8")
    )
    budget = json.loads((root / "task-budget.json").read_text(encoding="utf-8"))
    assert qualification["status"] == "TASK_PACK_READY"
    assert qualification["qualification_id"] == qualification_id
    assert budget["status"] == "PROFILE_R_TASK_BUDGET_SEALED"
    assert budget["task_pack_qualification_seal_sha256"] == qualification[
        "seal_sha256"
    ]
    if qualification_id == "profile-r-task-pack-q6":
        assert qualification["incident_regressions"] == [
            {
                "contract_rejected": True,
                "regression_id": "v22-r10-missing-run-all",
                "return_code": 1,
                "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "stdout_sha256": "db0d9237acdc9535df73d80ad4df5163865b391c2a97aa5ab0f665749de13fda",
                "task_id": "R10",
            }
        ]
    if qualification_id == "profile-r-task-pack-q7":
        assert [
            item["equivalent_id"]
            for item in qualification["public_equivalent_implementations"]
        ] == [
            "r11-equivalent-write-effects",
            "r13-equivalent-operator-vocabulary",
        ]
        assert all(
            item["contract_accepted"] is True
            for item in qualification["public_equivalent_implementations"]
        )
