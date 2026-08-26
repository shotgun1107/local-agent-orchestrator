from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SOURCE_ROOT = REPOSITORY_ROOT / "tools/benchmark-runner/src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from benchmark_runner.profile_r_redesign import (  # noqa: E402
    PROFILE_R_TASK_IDS,
    canonical_json,
    qualify_reference_chain,
)


PROFILE_ROOT = Path(
    "benchmarks/fixtures/routing-realistic-high-difficulty-v1/"
    "realistic-compat-migration-001"
)
JUDGE_ROOT = Path(
    "benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/"
    "realistic-compat-migration-001"
)
ROUTING_SUITE = Path("tools/benchmark-runner/src/benchmark_runner/routing_suite.py")
ROUTING_LIVE = Path("tools/benchmark-runner/src/benchmark_runner/routing_live.py")

PLAN_NAMES = {
    "_build_routing_plan",
    "build_routing_s2_live_plan",
    "build_routing_s2_plan",
}
LIFECYCLE_NAMES = {
    "_run_all_routing_nonlive_cells",
    "_run_next_routing_nonlive_cell",
    "initialize_routing_s2_experiment",
    "run_all_routing_s2_nonlive_cells",
    "run_next_routing_s2_nonlive_cell",
}
STATUS_NAMES = {
    "_routing_nonlive_status",
    "_routing_nonlive_summary",
    "_routing_nonlive_summary_markdown",
    "routing_s2_nonlive_status",
}
EXPORT_NAMES = {
    "_export_routing_nonlive",
    "_verify_routing_nonlive_export",
    "export_routing_s2_nonlive",
    "verify_routing_s2_nonlive_export",
}
LIVE_EXPORT_NAMES = {
    "_s2_path_length_preflight",
    "export_routing_s2_live",
    "verify_routing_s2_live_export",
}


def _load_builder(repository: Path):
    path = repository / "tools/benchmark-runner/scripts/build_profile_r_judge_bundle.py"
    spec = importlib.util.spec_from_file_location("profile_r_judge_builder", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Profile R Judge builder cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _strip_definitions(payload: bytes, names: set[str]) -> bytes:
    text = payload.decode("utf-8")
    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)
    ranges: list[tuple[int, int]] = []
    observed: set[str] = set()
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if node.name not in names:
            continue
        start = min(
            [node.lineno, *(item.lineno for item in node.decorator_list)]
        )
        if node.end_lineno is None:
            raise RuntimeError(f"AST end line is unavailable: {node.name}")
        ranges.append((start - 1, node.end_lineno))
        observed.add(node.name)
    missing = names - observed
    if missing:
        raise RuntimeError(f"reference phase definitions are missing: {sorted(missing)}")
    for start, end in sorted(ranges, reverse=True):
        del lines[start:end]
    result = ("".join(lines).rstrip() + "\n").encode("utf-8")
    if b"\r" in result or b"\x00" in result:
        raise RuntimeError("reference phase source is not exact UTF-8 LF text")
    compile(result.decode("utf-8"), "reference-phase.py", "exec")
    return result


def _git(
    repository: Path,
    *arguments: str,
    environment: dict[str, str],
) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Git {' '.join(arguments)} failed: {completed.stderr.strip()}"
        )
    return completed.stdout.strip()


def _git_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_AUTHOR_NAME": "profile-r-reference",
            "GIT_AUTHOR_EMAIL": "profile-r@test.invalid",
            "GIT_COMMITTER_NAME": "profile-r-reference",
            "GIT_COMMITTER_EMAIL": "profile-r@test.invalid",
            "GIT_AUTHOR_DATE": "2026-01-01T00:00:00+00:00",
            "GIT_COMMITTER_DATE": "2026-01-01T00:00:00+00:00",
        }
    )
    return environment


def _copy_path(source_root: Path, target_root: Path, relative: str) -> None:
    source = source_root / relative
    target = target_root / relative
    if source.is_dir():
        if target.exists():
            shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target)
    elif source.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    else:
        raise RuntimeError(f"reference source path is unavailable: {relative}")


def _write(root: Path, relative: Path, payload: bytes) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _same_tree(left: Path, right: Path) -> bool:
    def state(root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*")
            if path.is_file() and ".git" not in path.relative_to(root).parts
        }

    return state(left) == state(right)


def build_reference_repository(
    repository: Path,
    output_repository: Path,
) -> tuple[dict[str, Any], dict[str, object]]:
    repository = repository.resolve(strict=True)
    if output_repository.exists():
        raise RuntimeError("reference repository output must be fresh")
    builder = _load_builder(repository)
    profile_root = repository / PROFILE_ROOT
    pristine = profile_root / "workspace"
    final = output_repository.parent / f"{output_repository.name}-final"
    if final.exists():
        raise RuntimeError("reference final scratch path must be fresh")
    builder.project_reference(
        repository,
        pristine,
        final,
        builder.load_json(repository / JUDGE_ROOT / "anonymization-map.json"),
        builder.load_json(profile_root / "r-change-composition.json"),
    )
    shutil.copytree(pristine, output_repository)
    environment = _git_environment()
    _git(output_repository, "init", "-q", "-b", "main", environment=environment)
    _git(output_repository, "config", "core.autocrlf", "false", environment=environment)
    _git(output_repository, "config", "core.filemode", "false", environment=environment)
    _git(output_repository, "config", "core.longpaths", "true", environment=environment)
    _git(output_repository, "add", "-A", environment=environment)
    _git(output_repository, "commit", "-q", "-m", "Profile R reference base", environment=environment)
    base_commit = _git(output_repository, "rev-parse", "HEAD", environment=environment)

    final_suite = (final / ROUTING_SUITE).read_bytes()
    final_live = (final / ROUTING_LIVE).read_bytes()
    suite_r02 = _strip_definitions(
        final_suite,
        PLAN_NAMES | LIFECYCLE_NAMES | STATUS_NAMES | EXPORT_NAMES,
    )
    suite_r06 = _strip_definitions(
        final_suite,
        LIFECYCLE_NAMES | STATUS_NAMES | EXPORT_NAMES,
    )
    suite_r08 = _strip_definitions(final_suite, STATUS_NAMES | EXPORT_NAMES)
    suite_r09 = _strip_definitions(final_suite, EXPORT_NAMES)
    live_r09 = _strip_definitions(final_live, LIVE_EXPORT_NAMES)

    effects: dict[str, list[str]] = {
        "R01": [
            "profile-r/work/migration-ledger.json",
            "profile-r/work/source-inventory.json",
        ],
        "R02": [
            "benchmarks/suites/sdk-routing-v1/stage.schema.json",
            "benchmarks/suites/sdk-routing-v1/suite.schema.json",
            "benchmarks/suites/sdk-routing-v1/suite.yaml",
            "benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml",
        ],
        "R03": [
            "benchmarks/fixtures/routing-v1/intermediate/three-stage-config-migration"
        ],
        "R04": [
            "benchmarks/fixtures/routing-v1/intermediate/three-stage-incident-analysis"
        ],
        "R05": ["benchmarks/manifests/sdk-routing-s2-intermediate.yaml"],
        "R06": [
            "tools/benchmark-runner/scripts/probe_sdk_routing_s1_plan.py",
            "tools/benchmark-runner/scripts/run_sdk_routing_s1.py",
        ],
        "R07": ["tools/benchmark-runner/src/benchmark_runner/s2_policy.py"],
        "R08": [
            "tools/benchmark-runner/src/benchmark_runner/adapter.py",
            "tools/benchmark-runner/src/benchmark_runner/sdk_cells.py",
        ],
        "R09": [
            "tools/benchmark-runner/src/benchmark_runner/s2_posthoc.py",
            "tools/benchmark-runner/src/benchmark_runner/sdk_pilot.py",
        ],
        "R10": ["benchmarks/posthoc-checks/sdk-routing-v1/s2/checkers"],
        "R11": [
            "tools/benchmark-runner/tests/test_judge.py",
            "tools/benchmark-runner/tests/test_routing_s2.py",
        ],
        "R12": ["tools/benchmark-runner/tests/test_routing_suite.py"],
        "R13": [
            "profile-r/work/operator-contract.json",
            "tools/benchmark-runner/README.md",
        ],
    }
    phased_sources = {
        "R02": {ROUTING_SUITE: suite_r02},
        "R06": {ROUTING_SUITE: suite_r06},
        "R08": {ROUTING_SUITE: suite_r08},
        "R09": {ROUTING_SUITE: suite_r09, ROUTING_LIVE: live_r09},
        "R10": {ROUTING_SUITE: final_suite, ROUTING_LIVE: final_live},
    }
    task_commits: dict[str, str] = {}
    for task_id in PROFILE_R_TASK_IDS:
        for relative in effects[task_id]:
            _copy_path(final, output_repository, relative)
        for relative, payload in phased_sources.get(task_id, {}).items():
            _write(output_repository, relative, payload)
        _git(output_repository, "add", "-A", environment=environment)
        if not _git(output_repository, "diff", "--cached", "--name-only", environment=environment):
            raise RuntimeError(f"{task_id} reference effect is empty")
        _git(output_repository, "commit", "-q", "-m", task_id, environment=environment)
        task_commits[task_id] = _git(
            output_repository,
            "rev-parse",
            "HEAD",
            environment=environment,
        )
    if not _same_tree(output_repository, final):
        raise RuntimeError("R13 reference tree differs from projected final solution")
    run = yaml.safe_load(
        (profile_root / "worker-public-overlay/benchmark-run.yaml").read_text(
            encoding="utf-8"
        )
    )
    seal = qualify_reference_chain(
        output_repository,
        base_commit=base_commit,
        task_commits=task_commits,
        task_write_scopes={
            str(task["key"]): list(task["write_scope"])
            for task in run["tasks"]
        },
    )
    chain = {
        "schema_version": 1,
        "profile": "R",
        "base_commit": base_commit,
        "tasks": [
            {"task_id": task_id, "commit": task_commits[task_id]}
            for task_id in PROFILE_R_TASK_IDS
        ],
    }
    shutil.rmtree(final)
    return chain, seal


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the dedicated Profile R R01-R13 reference repository."
    )
    parser.add_argument("--repository", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--output-repository", type=Path, required=True)
    parser.add_argument("--chain-output", type=Path, required=True)
    parser.add_argument("--seal-output", type=Path, required=True)
    parser.add_argument("--bundle-output", type=Path)
    args = parser.parse_args()
    chain, seal = build_reference_repository(
        args.repository,
        args.output_repository.resolve(),
    )
    for path, value in ((args.chain_output, chain), (args.seal_output, seal)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            ).encode("utf-8")
            + b"\n"
        )
    if args.bundle_output is not None:
        if args.bundle_output.exists():
            raise RuntimeError("reference bundle output must be fresh")
        args.bundle_output.parent.mkdir(parents=True, exist_ok=True)
        environment = _git_environment()
        _git(
            args.output_repository.resolve(strict=True),
            "bundle",
            "create",
            str(args.bundle_output.resolve()),
            "--all",
            environment=environment,
        )
    print(canonical_json({"status": "REFERENCE_CHAIN_BUILT", **chain}).decode("utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
