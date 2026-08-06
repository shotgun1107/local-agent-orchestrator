"""Build frozen R6 wheels and initialize the pre-execution experiment."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


def run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {command!r}\n{result.stdout}\n{result.stderr}"
        )
    return result.stdout.strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
        newline="\n",
    )


def git_archive_sources(git: Path, repository: Path) -> bytes:
    """Read the build snapshot without inheriting checkout EOL conversion."""

    archive = subprocess.run(
        [
            str(git),
            "-c",
            "core.autocrlf=false",
            "archive",
            "--format=tar",
            "HEAD",
            "tools/benchmark-runner",
            "stages/b1-sequential",
        ],
        cwd=repository,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
    )
    if archive.returncode != 0:
        raise RuntimeError(
            f"git archive failed: {archive.stderr.decode('utf-8', errors='replace')}"
        )
    return archive.stdout


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    value.add_argument("--repository", type=Path, required=True)
    value.add_argument("--python", type=Path, required=True)
    value.add_argument("--git", type=Path, required=True)
    value.add_argument("--codex", type=Path, required=True)
    value.add_argument("--artifact-root", type=Path, required=True)
    value.add_argument("--local-root", type=Path, required=True)
    value.add_argument("--seed", type=int, default=20260805)
    value.add_argument("--revision", type=int, default=1)
    value.add_argument("--model", default="gpt-5.6-terra")
    value.add_argument("--reasoning-effort", default="low")
    value.add_argument("--b0-codex-project-root", type=Path)
    return value


def default_b0_codex_project_root() -> Path:
    return (
        Path.home()
        / "Documents"
        / "ChatGPT"
        / "AI 오케스트레이터 실험실"
    ).resolve()


def main() -> int:
    args = parser().parse_args()
    repository = args.repository.resolve()
    python = args.python.resolve()
    git = args.git.resolve()
    codex = args.codex.resolve()
    artifact_root = args.artifact_root.resolve()
    local_root = args.local_root.resolve()
    b0_codex_project_root = (
        args.b0_codex_project_root.resolve()
        if args.b0_codex_project_root is not None
        else default_b0_codex_project_root()
    )
    for path in (repository, python, git, codex):
        if not path.exists():
            raise RuntimeError(f"required R6 path is missing: {path}")
    if artifact_root.exists() and any(artifact_root.iterdir()):
        raise RuntimeError("artifact root must be new or empty")
    if local_root.exists() and any(local_root.iterdir()):
        raise RuntimeError("local root must be new or empty")
    artifact_root.mkdir(parents=True, exist_ok=True)
    local_root.mkdir(parents=True, exist_ok=True)

    status = run([str(git), "status", "--porcelain"], cwd=repository)
    if status:
        raise RuntimeError("R6 artifact build requires a clean source worktree")
    source_commit = run([str(git), "rev-parse", "HEAD"], cwd=repository)
    commit_epoch = run([str(git), "show", "-s", "--format=%ct", "HEAD"], cwd=repository)
    build_env = os.environ.copy()
    build_env["SOURCE_DATE_EPOCH"] = commit_epoch
    build_env["PYTHONDONTWRITEBYTECODE"] = "1"
    build_env["PYTHONUTF8"] = "1"
    build_env["PYTHONIOENCODING"] = "utf-8"
    archive = git_archive_sources(git, repository)
    with tempfile.TemporaryDirectory(prefix="lao-r6-build-") as snapshot_name:
        snapshot = Path(snapshot_name)
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as bundle:
            bundle.extractall(snapshot, filter="data")
        for project in (
            snapshot / "tools" / "benchmark-runner",
            snapshot / "stages" / "b1-sequential",
        ):
            run(
                [
                    str(python),
                    "-m",
                    "pip",
                    "wheel",
                    str(project),
                    "--no-deps",
                    "--no-build-isolation",
                    "--no-cache-dir",
                    "--wheel-dir",
                    str(artifact_root),
                ],
                cwd=snapshot,
                env=build_env,
            )
    runner_wheel = next(artifact_root.glob("local_agent_orchestrator_benchmark_runner-*.whl"))
    b1_wheel = next(artifact_root.glob("local_agent_orchestrator_b1-*.whl"))
    package_root = local_root / "site"
    run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--no-cache-dir",
            "--target",
            str(package_root),
            str(runner_wheel),
            str(b1_wheel),
        ],
        cwd=local_root,
    )
    installed_env = os.environ.copy()
    installed_env["PYTHONPATH"] = str(package_root)
    installed_env["PYTHONDONTWRITEBYTECODE"] = "1"
    installed_env["PYTHONUTF8"] = "1"
    installed_env["PYTHONIOENCODING"] = "utf-8"
    canonical_source = local_root / "source"
    run(
        [
            str(git),
            "clone",
            "--no-hardlinks",
            "--no-checkout",
            str(repository),
            str(canonical_source),
        ],
        cwd=local_root,
    )
    run([str(git), "config", "core.autocrlf", "false"], cwd=canonical_source)
    run([str(git), "checkout", "--detach", source_commit], cwd=canonical_source)
    if run([str(git), "status", "--porcelain"], cwd=canonical_source):
        raise RuntimeError("canonical R6 source checkout is not clean")
    schema_root = local_root / "b1-public-schemas"
    run(
        [
            str(python),
            "-m",
            "orchestrator.cli",
            "schema",
            "export",
            "--output",
            str(schema_root),
        ],
        cwd=local_root,
        env=installed_env,
    )

    runner_sha = sha256(runner_wheel)
    b1_sha = sha256(b1_wheel)
    profile = {
        "schema_version": 1,
        "source_repository": str(canonical_source),
        "manifest_path": str(canonical_source / "benchmarks" / "manifests" / "b0-b1-frozen.yaml"),
        "runner_python": str(python),
        "benchmark_python": str(python),
        "git_executable": str(git),
        "codex_executable": str(codex),
        "runner_artifact_path": str(runner_wheel),
        "b1_artifact_path": str(b1_wheel),
        "b1_pythonpath": str(package_root),
        "b1_schema_root": str(schema_root),
        "b1_command_prefix": [str(python), "-m", "orchestrator.cli"],
        "runner_artifact": {
            "artifact_id": "benchmark-runner",
            "version": source_commit,
            "sha256": runner_sha,
        },
        "variant_artifacts": [
            {"artifact_id": "b0", "version": source_commit, "sha256": runner_sha},
            {"artifact_id": "b1", "version": f"0.1.0@{source_commit}", "sha256": b1_sha},
        ],
        "seed": args.seed,
        "model": args.model,
        "auth_method": "chatgpt",
        "reasoning_effort": args.reasoning_effort,
        "runtime_profile_id": "local_default",
        "plan_reasoning_control": "b1_profile_verified_b0_user_attested_each_cell",
        "common_surface_kind": "mixed_b0_codex_app_b1_codex_sdk",
        "b0_surface_kind": "codex_app_task",
        "b1_surface_kind": "codex_sdk_via_lao_cli",
        "b0_codex_project_root": str(b0_codex_project_root),
        "b0_codex_project_name": "AI 오케스트레이터 실험실",
        "b0_launch_policy": "background_thread_only",
        "treatment_control": "partial",
    }
    profile_path = local_root / "r6-runtime-profile.json"
    write_json(profile_path, profile)
    created_raw = run(
        [
            str(python),
            "-m",
            "benchmark_runner",
            "r6",
            "create",
            "--profile",
            str(profile_path),
            "--state-root",
            str(local_root / "experiments"),
            "--revision",
            str(args.revision),
        ],
        cwd=local_root,
        env=installed_env,
    )
    created = json.loads(created_raw)
    schemas = {
        path.name: sha256(path)
        for path in sorted(schema_root.glob("*.json"), key=lambda item: item.name)
    }
    build_record = {
        "schema_version": 1,
        "status": "built_from_clean_commit",
        "source_commit": source_commit,
        "actual_model_turns": 0,
        "runner": {"file": runner_wheel.name, "sha256": runner_sha},
        "b1": {"file": b1_wheel.name, "sha256": b1_sha, "public_schemas": schemas},
        "experiment_id": created["experiment_id"],
        "plan_path_local": str(Path(created["plan_path"]).relative_to(local_root)),
    }
    write_json(artifact_root / "build-record.json", build_record)
    print(json.dumps({**build_record, "local_root": str(local_root)}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
