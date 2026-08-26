"""Model-free Profile R R01-R13 reference and information-boundary contracts."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


PROFILE_R_TASK_IDS = tuple(f"R{number:02d}" for number in range(1, 14))
PROFILE_R_PROPERTY_IDS = (
    "R-P01-SOURCE-BOUNDARY",
    "R-P02-DISCRIMINATOR",
    "R-P03-CONFIG-FIXTURE",
    "R-P04-INCIDENT-FIXTURE",
    "R-P05-MANIFEST-BINDING",
    "R-P06-PLAN-BINDING",
    "R-P07-ROUTING-POLICY",
    "R-P08-LIFECYCLE-REUSE",
    "R-P09-STATUS-POSTHOC",
    "R-P10-EXPORT-VERIFY",
    "R-P11-S2-E2E",
    "R-P12-S1-PORTABILITY",
    "R-P13-OPERATOR-SEMANTICS",
)
PROFILE_R_MUTATION_IDS = tuple(
    property_id.lower().replace("_", "-")
    for property_id in PROFILE_R_PROPERTY_IDS
)
FORBIDDEN_WORKER_PREFIXES = (
    "benchmarks/artifacts/profile-r-task-pack-",
    "benchmarks/reference-source/",
    "docs/reviews/",
    "docs/prompts/benchmark-runner/chatgpt-pro-",
    "artifacts/reference/",
    "artifacts/reviewer/",
)
FORBIDDEN_WORKER_NAMES = frozenset(
    {
        "reference.patch",
        "reference-task-chain.json",
        "redesign-decision.json",
    }
)


class ProfileRRedesignError(RuntimeError):
    """Raised when a redesign qualification invariant is violated."""


def _run_git(
    repository: Path,
    *arguments: str,
    environment: Mapping[str, str] | None = None,
) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        env=None if environment is None else dict(environment),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ProfileRRedesignError(
            f"Git {' '.join(arguments)} failed with exit {result.returncode}"
        )
    return result.stdout


def _apply_git_patch(repository: Path, patch: bytes) -> None:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repository),
            "apply",
            "--whitespace=error-all",
            "-",
        ],
        input=patch,
        stdin=None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ProfileRRedesignError(
            "Git apply failed with exit "
            f"{result.returncode}: "
            + result.stderr.decode("utf-8", errors="replace").strip()
        )


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def expected_task_checks(task_ids: Sequence[str], index: int) -> tuple[str, ...]:
    if tuple(task_ids) != PROFILE_R_TASK_IDS:
        raise ProfileRRedesignError("Profile R Task identity/order differs")
    if index < 0 or index >= len(task_ids):
        raise ProfileRRedesignError("Profile R Task index is out of range")
    return (
        *(f"{task_id.lower()}_contract" for task_id in task_ids[: index + 1]),
        "diff_check",
    )


def project_change_surface(run_spec: Mapping[str, Any]) -> dict[str, object]:
    tasks = run_spec.get("tasks")
    if not isinstance(tasks, list):
        raise ProfileRRedesignError("benchmark-run tasks are unavailable")
    task_ids = tuple(str(task.get("key")) for task in tasks if isinstance(task, dict))
    if task_ids != PROFILE_R_TASK_IDS:
        raise ProfileRRedesignError("benchmark-run Task order differs")
    projected = []
    for index, task in enumerate(tasks):
        assert isinstance(task, dict)
        own_check = task.get("own_check")
        expected_checks = list(expected_task_checks(task_ids, index))
        if own_check != expected_checks[-2] or "check_names" in task:
            raise ProfileRRedesignError(
                f"{task_ids[index]} own Check source differs or duplicates projection"
            )
        write_scope = task.get("write_scope")
        if not isinstance(write_scope, list) or not all(
            isinstance(value, str) for value in write_scope
        ):
            raise ProfileRRedesignError("Task write scope is invalid")
        projected.append(
            {"task_id": task_ids[index], "write_paths": list(write_scope)}
        )
    return {"schema_version": 2, "tasks": projected}


def changed_files(
    repository: Path,
    parent: str,
    child: str,
) -> list[tuple[str, str]]:
    output = _run_git(
        repository,
        "diff",
        "--no-renames",
        "--name-status",
        parent,
        child,
    ).decode("utf-8")
    records: list[tuple[str, str]] = []
    for raw in output.splitlines():
        status, separator, path = raw.partition("\t")
        if not separator or status not in {"A", "M"}:
            raise ProfileRRedesignError(
                f"unsupported reference effect: {raw}"
            )
        normalized = PurePosixPath(path).as_posix()
        if normalized != path or PurePosixPath(path).is_absolute():
            raise ProfileRRedesignError(f"unsafe reference path: {path}")
        records.append((status, path))
    return records


def read_reference_text_blob(
    repository: Path,
    commit: str,
    path: str,
) -> str:
    payload = _run_git(repository, "show", f"{commit}:{path}")
    if b"\x00" in payload:
        raise ProfileRRedesignError(f"binary reference effect is forbidden: {path}")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProfileRRedesignError(f"non-UTF8 reference effect: {path}") from exc
    if "\r" in text:
        raise ProfileRRedesignError(f"reference effect is not exact-LF: {path}")
    return text


def assert_linear_reference_commit(
    repository: Path,
    *,
    expected_parent: str,
    commit: str,
) -> None:
    parents = _run_git(
        repository,
        "show",
        "-s",
        "--format=%P",
        commit,
    ).decode("ascii").strip().split()
    if parents != [expected_parent]:
        raise ProfileRRedesignError(
            f"{commit} is not the exact next linear Task commit"
        )


def _scope_matches(path: str, scope: str) -> bool:
    if scope.endswith("/**"):
        prefix = scope[:-3].rstrip("/") + "/"
        return path.startswith(prefix)
    return fnmatch.fnmatchcase(path, scope)


def qualify_reference_chain(
    repository: Path,
    *,
    base_commit: str,
    task_commits: Mapping[str, str],
    task_write_scopes: Mapping[str, Sequence[str]],
) -> dict[str, object]:
    if tuple(task_commits) != PROFILE_R_TASK_IDS:
        raise ProfileRRedesignError("reference chain Task order differs")
    entries: dict[str, dict[str, object]] = {
        "base": {
            "commit": base_commit,
            "tree": _run_git(
                repository, "rev-parse", f"{base_commit}^{{tree}}"
            ).decode("ascii").strip(),
        }
    }
    parent = base_commit
    for task_id in PROFILE_R_TASK_IDS:
        commit = task_commits[task_id]
        assert_linear_reference_commit(
            repository,
            expected_parent=parent,
            commit=commit,
        )
        effects = changed_files(repository, parent, commit)
        if not effects:
            raise ProfileRRedesignError(
                f"{task_id} reference commit has no Task effect"
            )
        scopes = tuple(task_write_scopes[task_id])
        escaped = [
            path
            for _status, path in effects
            if not any(_scope_matches(path, scope) for scope in scopes)
        ]
        if escaped:
            raise ProfileRRedesignError(
                f"{task_id} reference commit escaped write scope: {escaped}"
            )
        effect_records = []
        for status, path in effects:
            text = read_reference_text_blob(repository, commit, path)
            effect_records.append(
                {
                    "status": status,
                    "path": path,
                    "size": len(text.encode("utf-8")),
                    "sha256": sha256(text.encode("utf-8")),
                }
            )
        entries[task_id] = {
            "commit": commit,
            "tree": _run_git(
                repository, "rev-parse", f"{commit}^{{tree}}"
            ).decode("ascii").strip(),
            "effects": effect_records,
        }
        parent = commit
    payload = {
        "schema_version": 1,
        "profile": "R",
        "reference_chain": entries,
    }
    payload["seal_sha256"] = sha256(canonical_json(payload))
    return payload


def apply_reference_task_diff(
    *,
    reference_repository: Path,
    worker_repository: Path,
    parent: str,
    child: str,
    expected_tree: str,
) -> str:
    """Apply one text-only Task diff and require its exact intermediate tree."""

    effects = changed_files(reference_repository, parent, child)
    if not effects:
        raise ProfileRRedesignError("reference Task diff is empty")
    for _status, path in effects:
        read_reference_text_blob(reference_repository, child, path)
    patch = _run_git(
        reference_repository,
        "diff",
        "--no-renames",
        "--full-index",
        parent,
        child,
    )
    _apply_git_patch(worker_repository, patch)
    observed = working_tree_hash(worker_repository)
    if observed != expected_tree:
        raise ProfileRRedesignError(
            "Worker intermediate tree differs from the sealed reference tree"
        )
    return observed


def working_tree_hash(repository: Path) -> str:
    with tempfile.TemporaryDirectory(prefix="profile-r-index-") as raw:
        temporary = Path(raw)
        index = temporary / "index"
        object_directory = temporary / "objects"
        object_directory.mkdir()
        git_dir_value = _run_git(
            repository,
            "rev-parse",
            "--git-dir",
        ).decode("utf-8").strip()
        git_dir = Path(git_dir_value)
        if not git_dir.is_absolute():
            git_dir = repository / git_dir
        environment = os.environ.copy()
        environment["GIT_INDEX_FILE"] = str(index)
        environment["GIT_OBJECT_DIRECTORY"] = str(object_directory)
        environment["GIT_ALTERNATE_OBJECT_DIRECTORIES"] = str(
            (git_dir / "objects").resolve()
        )
        _run_git(repository, "read-tree", "HEAD", environment=environment)
        _run_git(repository, "add", "-A", environment=environment)
        return _run_git(
            repository, "write-tree", environment=environment
        ).decode("ascii").strip()


def assert_worker_information_boundary(worker_root: Path) -> None:
    paths = {
        path.relative_to(worker_root).as_posix()
        for path in worker_root.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(worker_root).parts
    }
    forbidden = sorted(
        path
        for path in paths
        if PurePosixPath(path).name in FORBIDDEN_WORKER_NAMES
        or any(path.startswith(prefix) for prefix in FORBIDDEN_WORKER_PREFIXES)
    )
    if forbidden:
        raise ProfileRRedesignError(
            f"review/reference information leaked into Worker snapshot: {forbidden}"
        )
    git_dir = worker_root / ".git"
    if git_dir.is_dir():
        unreachable = _run_git(
            worker_root,
            "fsck",
            "--no-reflogs",
            "--unreachable",
        ).decode("utf-8").strip()
        if unreachable:
            raise ProfileRRedesignError(
                "Worker repository contains unreachable Git objects"
            )
