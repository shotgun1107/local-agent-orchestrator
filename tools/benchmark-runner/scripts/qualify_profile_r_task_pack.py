from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

from benchmark_runner.profile_r_redesign import (
    PROFILE_R_PROPERTY_IDS,
    PROFILE_R_MUTATION_IDS,
    PROFILE_R_TASK_IDS,
    apply_reference_task_diff,
    assert_worker_information_boundary,
    canonical_json,
    project_change_surface,
    qualify_reference_chain,
    sha256,
)


PROFILE_RELATIVE = Path(
    "benchmarks/fixtures/routing-realistic-high-difficulty-v1/"
    "realistic-compat-migration-001"
)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def _worker_manifest_exact(worker_root: Path, manifest: dict[str, Any]) -> None:
    records = manifest.get("files")
    if not isinstance(records, list):
        raise RuntimeError("Worker manifest records are unavailable")
    expected = []
    for record in records:
        path = str(record["path"])
        payload = (worker_root / path).read_bytes()
        if hashlib.sha256(payload).hexdigest() != record["worker_sha256"]:
            raise RuntimeError(f"Worker manifest hash differs: {path}")
        expected.append(path)
    actual = sorted(
        path.relative_to(worker_root).as_posix()
        for path in worker_root.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(worker_root).parts
    )
    if actual != sorted(expected):
        raise RuntimeError("Worker file set differs from manifest")


def qualify(
    repository: Path,
    *,
    qualification_id: str = "profile-r-task-pack-q1",
) -> dict[str, object]:
    if re.fullmatch(r"profile-r-task-pack-q[1-9][0-9]*", qualification_id) is None:
        raise RuntimeError("Task Pack qualification ID is invalid")
    root = repository / PROFILE_RELATIVE
    overlay = root / "worker-public-overlay"
    worker = root / "workspace"
    manifest_path = root / "worker-snapshot-manifest.json"
    run_path = overlay / "benchmark-run.yaml"
    surface_path = overlay / "profile-r/requirements/change-surface.json"
    run = yaml.safe_load(run_path.read_text(encoding="utf-8"))
    if not isinstance(run, dict):
        raise RuntimeError("benchmark-run is invalid")
    projection = project_change_surface(run)
    surface = _load_json(surface_path)
    if surface != projection:
        raise RuntimeError("change-surface projection differs")
    manifest = _load_json(manifest_path)
    _worker_manifest_exact(worker, manifest)
    assert_worker_information_boundary(worker)
    payload: dict[str, object] = {
        "schema_version": 1,
        "profile": "R",
        "snapshot_id": "realistic-compat-migration-001",
        "qualification_id": qualification_id,
        "status": "STRUCTURE_READY",
        "model_turns": 0,
        "task_ids": list(PROFILE_R_TASK_IDS),
        "property_ids": list(PROFILE_R_PROPERTY_IDS),
        "benchmark_run_sha256": sha256(run_path.read_bytes()),
        "change_surface_sha256": sha256(surface_path.read_bytes()),
        "worker_manifest_sha256": sha256(manifest_path.read_bytes()),
        "worker_tree_aggregate_sha256": manifest["worker_tree_aggregate_sha256"],
        "worker_information_boundary_passed": True,
        "negative_mutation_ids": list(PROFILE_R_MUTATION_IDS),
        "remaining_requirements": [
            "sealed reference R01-R13 commit chain",
            "positive intermediate-tree transitions",
            "independent public negative mutation matrix",
        ],
    }
    payload["seal_sha256"] = sha256(canonical_json(payload))
    return payload


def _git(repository: Path, *arguments: str, input_bytes: bytes | None = None) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        input=input_bytes,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Git {' '.join(arguments)} failed with exit {completed.returncode}: "
            + completed.stderr.decode("utf-8", errors="replace").strip()
        )
    return completed.stdout.decode("utf-8", errors="strict").strip()


def _initialize_worker_git(worker: Path) -> None:
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_AUTHOR_NAME": "profile-r-task-pack",
            "GIT_AUTHOR_EMAIL": "profile-r@test.invalid",
            "GIT_COMMITTER_NAME": "profile-r-task-pack",
            "GIT_COMMITTER_EMAIL": "profile-r@test.invalid",
            "GIT_AUTHOR_DATE": "2026-01-01T00:00:00+00:00",
            "GIT_COMMITTER_DATE": "2026-01-01T00:00:00+00:00",
        }
    )
    for arguments in (
        ("init", "-q", "-b", "main"),
        ("config", "core.autocrlf", "false"),
        ("config", "core.filemode", "false"),
        ("config", "core.longpaths", "true"),
        ("add", "-A"),
    ):
        completed = subprocess.run(
            ["git", "-C", str(worker), *arguments],
            env=environment,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"Worker Git bootstrap failed: {' '.join(arguments)}")
    completed = subprocess.run(
        ["git", "-C", str(worker), "commit", "-q", "-m", "Profile R Worker baseline"],
        env=environment,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("Worker Git baseline commit failed")


def _run_public_check(
    worker: Path,
    *,
    task_id: str,
    check_name: str,
    check_spec: dict[str, Any],
) -> dict[str, object]:
    argv = [str(value) for value in check_spec["argv"]]
    if argv[0] == "python":
        argv[0] = sys.executable
    with tempfile.TemporaryDirectory(prefix="profile-r-q1-check-") as raw:
        environment = os.environ.copy()
        environment.update(
            {
                "TEMP": raw,
                "TMP": raw,
                "TMPDIR": raw,
                "PYTHONUTF8": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
            }
        )
        environment.pop("PYTHONPATH", None)
        completed = subprocess.run(
            argv,
            cwd=worker / str(check_spec.get("cwd", ".")),
            env=environment,
            capture_output=True,
            timeout=int(check_spec["timeout_seconds"]),
            check=False,
        )
    expected_codes = list(check_spec["expected_exit_codes"])
    return {
        "task_id": task_id,
        "check_name": check_name,
        "passed": completed.returncode in expected_codes,
        "return_code": completed.returncode,
        "stdout_sha256": sha256(completed.stdout),
        "stderr_sha256": sha256(completed.stderr),
        "stdout_lines": completed.stdout.decode(
            "utf-8", errors="replace"
        ).splitlines(),
    }


def qualify_full(
    repository: Path,
    *,
    qualification_id: str = "profile-r-task-pack-q1",
    reference_repository: Path,
    reference_chain_path: Path,
    negative_mutations: Path,
) -> dict[str, object]:
    structure = qualify(repository, qualification_id=qualification_id)
    chain_bytes = reference_chain_path.read_bytes()
    chain = _load_json(reference_chain_path)
    expected_self = str(chain.get("seal_sha256", ""))
    without_self = {key: value for key, value in chain.items() if key != "seal_sha256"}
    if expected_self != sha256(canonical_json(without_self)):
        raise RuntimeError("reference chain self-seal differs")
    entries = chain.get("reference_chain")
    if not isinstance(entries, dict) or set(entries) != {"base", *PROFILE_R_TASK_IDS}:
        raise RuntimeError("reference chain entries differ")
    root = repository / PROFILE_RELATIVE
    run = yaml.safe_load((root / "worker-public-overlay/benchmark-run.yaml").read_text(encoding="utf-8"))
    checks = yaml.safe_load((root / "worker-public-overlay/.orchestrator/checks.yaml").read_text(encoding="utf-8"))["checks"]
    recomputed_chain = qualify_reference_chain(
        reference_repository,
        base_commit=str(entries["base"]["commit"]),
        task_commits={
            task_id: str(entries[task_id]["commit"])
            for task_id in PROFILE_R_TASK_IDS
        },
        task_write_scopes={
            str(task["key"]): list(task["write_scope"])
            for task in run["tasks"]
        },
    )
    if recomputed_chain != chain:
        raise RuntimeError("reference chain differs from its repository")
    with tempfile.TemporaryDirectory(prefix=f"{qualification_id}-") as raw:
        temporary = Path(raw)
        worker = temporary / "worker"
        shutil.copytree(root / "workspace", worker)
        _initialize_worker_git(worker)
        if _git(worker, "rev-parse", "HEAD^{tree}") != entries["base"]["tree"]:
            raise RuntimeError("Worker baseline tree differs from reference base")
        assert_worker_information_boundary(worker)
        positive = []
        parent = str(entries["base"]["commit"])
        for index, task in enumerate(run["tasks"]):
            task_id = str(task["key"])
            child = str(entries[task_id]["commit"])
            tree = apply_reference_task_diff(
                reference_repository=reference_repository,
                worker_repository=worker,
                parent=parent,
                child=child,
                expected_tree=str(entries[task_id]["tree"]),
            )
            check_names = [
                f"{value.lower()}_contract"
                for value in PROFILE_R_TASK_IDS[: index + 1]
            ] + ["diff_check"]
            check_results = [
                _run_public_check(
                    worker,
                    task_id=task_id,
                    check_name=check_name,
                    check_spec=checks[check_name],
                )
                for check_name in check_names
            ]
            if not all(item["passed"] for item in check_results):
                failed = [item["check_name"] for item in check_results if not item["passed"]]
                raise RuntimeError(f"{task_id} positive public Checks failed: {failed}")
            positive.append(
                {
                    "task_id": task_id,
                    "tree": tree,
                    "checks": [
                        {
                            key: value
                            for key, value in item.items()
                            if key != "stdout_lines"
                        }
                        for item in check_results
                    ],
                }
            )
            parent = child
        assert_worker_information_boundary(worker)
        final_worker = worker
        mutation_paths = {
            path.stem: path for path in negative_mutations.glob("*.patch")
        }
        if set(mutation_paths) != set(PROFILE_R_MUTATION_IDS):
            raise RuntimeError("public negative mutation file set differs")
        negative = []
        for index, mutation_id in enumerate(PROFILE_R_MUTATION_IDS, 1):
            mutated = temporary / f"negative-{mutation_id}"
            shutil.copytree(final_worker, mutated)
            _git(
                mutated,
                "apply",
                "--whitespace=error-all",
                "-",
                input_bytes=mutation_paths[mutation_id].read_bytes(),
            )
            task_id = f"R{index:02d}"
            check_name = f"r{index:02d}_contract"
            result = _run_public_check(
                mutated,
                task_id=task_id,
                check_name=check_name,
                check_spec=checks[check_name],
            )
            rejected = (
                result["return_code"] == 1
                and result["stdout_lines"][:2]
                == [
                    f"{task_id}_PUBLIC_CONTRACT_FAILED",
                    "CHECK_FAILURE_CLASS:PRODUCT_ASSERTION",
                ]
            )
            if not rejected:
                raise RuntimeError(
                    f"{task_id} public contract accepted its known-bad mutation"
                )
            negative.append(
                {
                    "mutation_id": mutation_id,
                    "task_id": task_id,
                    "contract_rejected": True,
                    "return_code": result["return_code"],
                    "stdout_sha256": result["stdout_sha256"],
                    "stderr_sha256": result["stderr_sha256"],
                }
            )
    payload: dict[str, object] = {
        **{
            key: value
            for key, value in structure.items()
            if key not in {"seal_sha256", "remaining_requirements", "status"}
        },
        "status": "TASK_PACK_READY",
        "snapshot_id": "realistic-compat-migration-001",
        "reference_chain_sha256": sha256(chain_bytes),
        "reference_chain_seal_sha256": expected_self,
        "positive_transitions": positive,
        "public_negative_matrix": negative,
        "public_negative_matrix_sha256": sha256(canonical_json(negative)),
    }
    payload["seal_sha256"] = sha256(canonical_json(payload))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Model-free structural qualification for Profile R Task Pack q1."
    )
    parser.add_argument(
        "--repository",
        type=Path,
        default=Path(__file__).resolve().parents[3],
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--reference-repository", type=Path)
    parser.add_argument("--reference-chain-seal", type=Path)
    parser.add_argument("--negative-mutations", type=Path)
    parser.add_argument(
        "--qualification-id",
        default="profile-r-task-pack-q1",
    )
    args = parser.parse_args()
    full_values = (
        args.reference_repository,
        args.reference_chain_seal,
        args.negative_mutations,
    )
    if any(value is not None for value in full_values) and not all(
        value is not None for value in full_values
    ):
        parser.error("full q1 requires reference repository, chain seal, and mutations")
    if all(value is not None for value in full_values):
        result = qualify_full(
            args.repository.resolve(strict=True),
            qualification_id=args.qualification_id,
            reference_repository=args.reference_repository.resolve(strict=True),
            reference_chain_path=args.reference_chain_seal.resolve(strict=True),
            negative_mutations=args.negative_mutations.resolve(strict=True),
        )
    else:
        result = qualify(
            args.repository.resolve(strict=True),
            qualification_id=args.qualification_id,
        )
    payload = json.dumps(
        result, ensure_ascii=False, sort_keys=True, indent=2
    ) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8", newline="\n")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
