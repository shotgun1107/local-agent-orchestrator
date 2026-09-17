"""Bound, one-shot Profile I *reviewed reference diagnostic* integration.

Never imports Worker code on the host and never grants comparison readiness.
The shared-process v2 oracle is NOT hostile-Worker-safe. General Worker input,
automatic matrix execution, Phase F claims and candidate promotion are excluded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import time
from typing import Any

from benchmark_runner.realistic_docker_judge import (
    DOCKER_JUDGE_IMAGE, DockerJudgeError, DockerJudgeLimits, DockerJudgeMount,
    SubprocessDockerExecutionBackend, build_docker_controller_environment,
    build_docker_judge_command,
)

ROOT = "tools/benchmark-runner/qualifications/profile-i-semantic-v2"
LEGACY = "benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-incident-repair-001"
FIXTURE = "benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-incident-repair-001/workspace"
SOURCE_FILES = {f"checker/{name}": f"{ROOT}/{name}" for name in
                ("check_properties.py", "test_behavior.py", "semantic-contract.json")}
SOURCE_FILES.update({"public-behavior-contract.md": f"{ROOT}/README.md"})
SOURCE_FILES.update({name: f"{LEGACY}/{name}" for name in
                     ("reference.patch", "property-catalog.json", "prerequisite-dag.json", "failure-lineage.json")})
RUNTIME_FILES = tuple(name for name in SOURCE_FILES if name.startswith("checker/"))
PURPOSE = "reviewed_reference_diagnostic_only"
ISOLATION = "shared_python_process_not_hostile_safe"
MARKER = "PROFILE_I_DIAGNOSTIC_RESULT:"
CLAIM = "I-P10-EVIDENCE-CLAIM-ALIGNMENT"
MAX_BYTES = 128 * 1024 * 1024
MAX_FILE_BYTES = 4 * 1024 * 1024


class SemanticExecutionError(ValueError):
    pass


def canonical(value) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse(data: bytes):
    if len(data) > MAX_FILE_BYTES:
        raise SemanticExecutionError("JSON_SIZE_LIMIT")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise SemanticExecutionError("DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    def invalid(_value):
        raise SemanticExecutionError("NONFINITE_JSON")
    try:
        return json.loads(data, object_pairs_hook=pairs, parse_constant=invalid)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise SemanticExecutionError("INVALID_JSON") from exc


def checked(path: Path) -> Path:
    path = Path(os.path.abspath(path))
    if any(c in str(path) for c in (",", "\n", "\r", "\0")):
        raise SemanticExecutionError("UNSAFE_MOUNT_PATH")
    for part in (path, *path.parents):
        if part.is_symlink() or part.is_junction():
            raise SemanticExecutionError("LINKED_PATH")
    return path


def relative(name: str) -> str:
    p = PurePosixPath(name)
    if (not name or p.is_absolute() or p.as_posix() != name or "\\" in name or ":" in name
            or any(part in {".", "..", "", ".git", "__pycache__", ".pytest_cache"} for part in p.parts)):
        raise SemanticExecutionError("UNSAFE_RELATIVE_PATH")
    return name


def read_file(path: Path) -> bytes:
    path = checked(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > MAX_FILE_BYTES:
        raise SemanticExecutionError("UNSUPPORTED_FILE")
    data = path.read_bytes()
    after = path.lstat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise SemanticExecutionError("FILE_CHANGED_DURING_READ")
    return data


def inventory(root: Path) -> list[dict]:
    root = checked(root)
    if not root.is_dir():
        raise SemanticExecutionError("DIRECTORY_MISSING")
    rows, aliases, total = [], set(), 0
    def unreadable(_error):
        raise SemanticExecutionError("TREE_UNREADABLE")
    for parent, dirs, files in os.walk(root, followlinks=False, onerror=unreadable):
        if Path(parent) != root and not dirs and not files:
            raise SemanticExecutionError("EMPTY_UNTRACKED_DIRECTORY")
        for name in (*dirs, *files):
            path = checked(Path(parent) / name)
            key = relative(path.relative_to(root).as_posix())
            if key.casefold() in aliases or len(aliases) >= 10000 or len(PurePosixPath(key).parts) > 40:
                raise SemanticExecutionError("TREE_LIMIT_OR_ALIAS")
            aliases.add(key.casefold())
        for name in files:
            path = Path(parent) / name
            data = read_file(path)
            total += len(data)
            if total > MAX_BYTES:
                raise SemanticExecutionError("TREE_SIZE_LIMIT")
            rows.append({"path": path.relative_to(root).as_posix(), "size": len(data), "sha256": digest(data)})
    return sorted(rows, key=lambda row: row["path"])


def worker_hash(rows: list[dict]) -> str:
    # Exact same serialization as the v2 checker; no host import of that checker.
    return digest(json.dumps([(r["path"], r["sha256"]) for r in rows], separators=(",", ":")).encode())


def _write_new(path: Path, data: bytes):
    checked(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def _git(repo: Path, executable: Path, *args: str, input_data=None, cwd=None) -> bytes:
    env = os.environ.copy()
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    result = subprocess.run([str(executable), *args], cwd=cwd or repo, input=input_data,
        env=env, capture_output=True, timeout=30, shell=False,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    if result.returncode:
        raise SemanticExecutionError("GIT_OPERATION_FAILED")
    return result.stdout


def validate_contract(contract: dict):
    if set(contract) != {"schema_version", "kind", "purpose", "comparison_authorized", "oracle_isolation", "properties", "public_tasks"}:
        raise SemanticExecutionError("CONTRACT_FIELDS")
    if (type(contract["schema_version"]) is not int or contract["schema_version"] != 1
        or contract["kind"] != "profile_i_semantic_case_contract" or contract["purpose"] != PURPOSE
        or contract["comparison_authorized"] is not False or contract["oracle_isolation"] != ISOLATION):
        raise SemanticExecutionError("CONTRACT_SCOPE")
    rows = contract["properties"]
    if not isinstance(rows, list) or len(rows) != 10:
        raise SemanticExecutionError("PROPERTY_SET")
    ids = [row["property_id"] for row in rows]
    if ids != sorted(set(ids)) or any(not p.startswith(f"I-P{i:02d}-") for i, p in enumerate(ids, 1)):
        raise SemanticExecutionError("PROPERTY_ORDER")
    prior = set()
    for row in rows:
        if set(row) != {"property_id", "prerequisite_ids", "case_ids"}:
            raise SemanticExecutionError("PROPERTY_FIELDS")
        deps, cases = row["prerequisite_ids"], row["case_ids"]
        if (not isinstance(deps, list) or len(deps) != len(set(deps)) or not set(deps) <= prior
                or not isinstance(cases, list) or not cases or len(cases) != len(set(cases)) or len(cases) > 32
                or any(not isinstance(c, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,120}", c) for c in cases)):
            raise SemanticExecutionError("CASE_OR_PREREQUISITE")
        prior.add(row["property_id"])
    tasks = contract["public_tasks"]
    if set(tasks) != {f"I{i:02d}" for i in range(1, 9)}:
        raise SemanticExecutionError("TASK_SET")
    if any(not isinstance(v, list) or not v or len(v) != len(set(v)) or not set(v) <= prior for v in tasks.values()):
        raise SemanticExecutionError("TASK_PROPERTIES")


def selected_properties(contract: dict, task_id: str | None):
    validate_contract(contract)
    by_id = {row["property_id"]: row for row in contract["properties"]}
    pending = list(by_id if task_id is None else contract["public_tasks"][task_id])
    selected = set()
    while pending:
        key = pending.pop()
        if key not in selected:
            selected.add(key)
            pending.extend(by_id[key]["prerequisite_ids"])
    return [by_id[key] for key in sorted(selected)]


def command_for(plan: dict, root: Path, *, noop: bool = False):
    mounts = [DockerJudgeMount(role=role, host_path=str(checked(root / name)), container_path=target, read_only=readonly)
        for role, name, target, readonly in (("W", "worker", "/workspace", True), ("J", "judge", "/judge", True), ("O", "output", "/output", False))]
    command = build_docker_judge_command(docker_executable=Path(plan["docker_executable"]),
        container_name=plan["diagnostic_id"], mounts=mounts, limits=DockerJudgeLimits.model_validate(plan["limits"]), cell_id=plan["diagnostic_id"])
    command[-3] = "profile-i-semantic-diagnostic"
    command.extend(["--invocation-sha256", plan["invocation_sha256"]])
    if plan["task_id"] is not None:
        command.extend(["--task-id", plan["task_id"]])
    if noop:
        # Same image/mount/network/user/limits, but never import Worker/checker code.
        marker = ".f14-noop-" + plan["invocation_sha256"][:12]
        program = ("import hashlib,importlib.metadata as m,json,pathlib,sys; "
            "j=pathlib.Path('/judge/checker'); "
            f"p=pathlib.Path('/output/{marker}'); "
            "f=p.open('xb'); f.write(b'noop'); f.close(); assert p.read_bytes()==b'noop'; p.unlink(); "
            "print(json.dumps({'python':list(sys.version_info[:3]),'packages':{n:m.version(n) for n in ['pytest','pydantic']},"
            "'checker_sha256':hashlib.sha256((j/'check_properties.py').read_bytes()).hexdigest(),"
            "'oracle_sha256':hashlib.sha256((j/'test_behavior.py').read_bytes()).hexdigest(),"
            "'contract_sha256':hashlib.sha256((j/'semantic-contract.json').read_bytes()).hexdigest(),"
            "'workspace_exists':pathlib.Path('/workspace').is_dir(),'output_io':True}))")
        command = command[:command.index(DOCKER_JUDGE_IMAGE) + 1] + ["python", "-I", "-c", program]
    return command


def prepare(repository: Path, root: Path, *, git_executable: Path, docker_executable: Path,
            source_commit: str, diagnostic_id: str, task_id: str | None = None) -> dict:
    repo, root = checked(repository), checked(root)
    git_executable, docker_executable = checked(git_executable), checked(docker_executable)
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit) or not re.fullmatch(r"f14-[a-z0-9-]{1,60}", diagnostic_id):
        raise SemanticExecutionError("SOURCE_OR_DIAGNOSTIC_ID")
    if root.exists() or not any(base in root.parents for base in (repo.parent / "tmp", repo.parent / "evidence")):
        raise SemanticExecutionError("FRESH_LAO_OUTPUT_REQUIRED")
    if _git(repo, git_executable, "rev-parse", "HEAD").strip().decode() != source_commit or _git(repo, git_executable, "status", "--porcelain"):
        raise SemanticExecutionError("CLEAN_PINNED_SOURCE_REQUIRED")
    payloads = {name: _git(repo, git_executable, "cat-file", "blob", f"{source_commit}:{path}") for name, path in SOURCE_FILES.items()}
    contract = parse(payloads["checker/semantic-contract.json"])
    selected_properties(contract, task_id)
    source_tree = _git(repo, git_executable, "rev-parse", source_commit + "^{tree}").strip().decode()
    listing = _git(repo, git_executable, "ls-tree", "-r", "-z", "--full-tree", source_commit, "--", FIXTURE)
    worker_files = {}
    for item in listing.split(b"\0"):
        if not item:
            continue
        metadata, raw_name = item.split(b"\t", 1)
        if metadata.split()[0] not in {b"100644", b"100755"}:
            raise SemanticExecutionError("UNSUPPORTED_GIT_ENTRY")
        path = raw_name.decode()
        name = relative(path[len(FIXTURE) + 1:])
        worker_files[name] = _git(repo, git_executable, "cat-file", "blob", metadata.split()[2].decode())
    if not worker_files or len(worker_files) > 10000 or sum(map(len, worker_files.values())) > MAX_BYTES:
        raise SemanticExecutionError("WORKER_SOURCE_LIMIT")
    root.mkdir(parents=True)
    for name, data in payloads.items():
        _write_new(root / "bundle" / name, data)
    for name in RUNTIME_FILES:
        _write_new(root / "judge" / name, payloads[name])
    for name, data in worker_files.items():
        _write_new(root / "worker" / name, data)
    # Only the exact known reference patch from the pinned source is applied.
    patch_args = ("-c", "core.autocrlf=false", "-c", "core.longpaths=true", "apply", "--no-index", "--whitespace=nowarn")
    _git(repo, git_executable, *patch_args, "--check", "-", input_data=payloads["reference.patch"], cwd=root / "worker")
    _git(repo, git_executable, *patch_args, "-", input_data=payloads["reference.patch"], cwd=root / "worker")
    (root / "output").mkdir()
    worker, judge, bundle = inventory(root / "worker"), inventory(root / "judge"), inventory(root / "bundle")
    plan = {"schema_version": 1, "kind": "profile_i_semantic_diagnostic_plan", "purpose": PURPOSE,
        "comparison_authorized": False, "oracle_isolation": ISOLATION, "source_commit": source_commit,
        "source_tree": source_tree, "repository": str(repo), "source_files": dict(SOURCE_FILES),
        "source_branch": _git(repo, git_executable, "symbolic-ref", "--short", "HEAD").strip().decode(),
        "source_origin": _git(repo, git_executable, "remote", "get-url", "origin").strip().decode(),
        "diagnostic_id": diagnostic_id, "task_id": task_id, "variant": "pinned_reference",
        "docker_executable": str(docker_executable), "docker_executable_sha256": _executable_hash(docker_executable),
        "git_executable": str(git_executable), "git_executable_sha256": _executable_hash(git_executable),
        "image_reference": DOCKER_JUDGE_IMAGE, "docker_context": "desktop-linux",
        "required_os": "linux", "required_architecture": "amd64", "limits": DockerJudgeLimits().model_dump(),
        "worker_files": worker, "worker_sha256": worker_hash(worker), "judge_files": judge, "bundle_files": bundle,
        "contract": contract, "contract_sha256": digest(payloads["checker/semantic-contract.json"]),
        "model_turns": 0, "sdk_threads": 0, "phase_f_claims": 0, "automatic_continuation": False}
    plan["invocation_sha256"] = digest(canonical(plan))
    plan["command"] = command_for(plan, root)
    plan["noop_command"] = command_for(plan, root, noop=True)
    plan["plan_sha256"] = digest(canonical(plan))
    _write_new(root / "plan.json", canonical(plan))
    verify_plan(root / "plan.json", plan["plan_sha256"])
    return plan


def _executable_hash(path: Path) -> str:
    path = checked(path)
    before = path.stat()
    # Installed Git may legitimately use hard-linked executables. Pin all bytes
    # and file identity; payload trees still reject hard links via read_file.
    if not path.is_file() or before.st_size > 256 * 1024 * 1024:
        raise SemanticExecutionError("EXECUTABLE_LIMIT")
    with path.open("rb") as stream:
        result = hashlib.file_digest(stream, "sha256").hexdigest()
    after = path.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise SemanticExecutionError("EXECUTABLE_CHANGED")
    return result


def verify_plan(path: Path, expected_sha256: str) -> dict:
    plan = parse(read_file(path))
    if (not isinstance(plan, dict) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256) or plan.get("plan_sha256") != expected_sha256
        or digest(canonical({k: v for k, v in plan.items() if k != "plan_sha256"})) != expected_sha256):
        raise SemanticExecutionError("PLAN_IDENTITY")
    if plan.get("purpose") != PURPOSE or plan.get("variant") != "pinned_reference" or plan.get("comparison_authorized") is not False:
        raise SemanticExecutionError("DIAGNOSTIC_SCOPE")
    literals = {"schema_version": 1, "kind": "profile_i_semantic_diagnostic_plan", "oracle_isolation": ISOLATION,
                "required_os": "linux", "required_architecture": "amd64", "model_turns": 0, "sdk_threads": 0,
                "phase_f_claims": 0, "automatic_continuation": False}
    if any(type(plan.get(key)) is not type(value) or plan.get(key) != value for key, value in literals.items()):
        raise SemanticExecutionError("PLAN_SCOPE_FIELDS")
    if plan["limits"] != DockerJudgeLimits().model_dump():
        raise SemanticExecutionError("PLAN_LIMITS")
    if plan.get("source_files") != SOURCE_FILES or plan.get("image_reference") != DOCKER_JUDGE_IMAGE or plan.get("docker_context") != "desktop-linux":
        raise SemanticExecutionError("SOURCE_OR_RUNTIME_CONTRACT")
    root = checked(path).parent
    repo, git = checked(Path(plan["repository"])), checked(Path(plan["git_executable"]))
    if _executable_hash(git) != plan["git_executable_sha256"]:
        raise SemanticExecutionError("GIT_EXECUTABLE_CHANGED")
    if _git(repo, git, "rev-parse", "HEAD").strip().decode() != plan["source_commit"] or _git(repo, git, "status", "--porcelain"):
        raise SemanticExecutionError("SOURCE_CHECKOUT_CHANGED")
    if (_git(repo, git, "symbolic-ref", "--short", "HEAD").strip().decode() != plan["source_branch"]
        or _git(repo, git, "remote", "get-url", "origin").strip().decode() != plan["source_origin"]):
        raise SemanticExecutionError("SOURCE_BRANCH_OR_ORIGIN_CHANGED")
    if _git(repo, git, "rev-parse", plan["source_commit"] + "^{tree}").strip().decode() != plan["source_tree"]:
        raise SemanticExecutionError("SOURCE_TREE_CHANGED")
    for name, source in SOURCE_FILES.items():
        if read_file(root / "bundle" / name) != _git(repo, git, "cat-file", "blob", f"{plan['source_commit']}:{source}"):
            raise SemanticExecutionError("BUNDLE_SOURCE_MISMATCH")
    if _executable_hash(Path(plan["docker_executable"])) != plan["docker_executable_sha256"]:
        raise SemanticExecutionError("DOCKER_EXECUTABLE_CHANGED")
    for name, records in (("worker", plan["worker_files"]), ("judge", plan["judge_files"]), ("bundle", plan["bundle_files"])):
        if inventory(root / name) != records:
            raise SemanticExecutionError("INPUT_TREE_CHANGED")
    if inventory(root / "output"):
        raise SemanticExecutionError("OUTPUT_NOT_EMPTY")
    if [r["path"] for r in plan["judge_files"]] != sorted(RUNTIME_FILES):
        raise SemanticExecutionError("JUDGE_VIEW_LEAKS_REFERENCE")
    contract = parse(read_file(root / "judge/checker/semantic-contract.json"))
    selected_properties(contract, plan["task_id"])
    if contract != plan["contract"] or digest(read_file(root / "judge/checker/semantic-contract.json")) != plan["contract_sha256"]:
        raise SemanticExecutionError("CASE_CONTRACT_CHANGED")
    if plan["worker_sha256"] != worker_hash(plan["worker_files"]):
        raise SemanticExecutionError("WORKER_HASH")
    invocation = {k: v for k, v in plan.items() if k not in {"plan_sha256", "invocation_sha256", "command", "noop_command"}}
    if plan["invocation_sha256"] != digest(canonical(invocation)):
        raise SemanticExecutionError("INVOCATION_IDENTITY")
    if plan["command"] != command_for(plan, root) or plan["noop_command"] != command_for(plan, root, noop=True):
        raise SemanticExecutionError("COMMAND_CHANGED")
    return plan


def verify_observation(plan: dict, stdout: bytes, *, exit_code: int) -> dict:
    if len(stdout) > plan["limits"]["stdout_limit_bytes"]:
        raise SemanticExecutionError("OUTPUT_LIMIT")
    lines = [line[len(MARKER):] for line in stdout.decode("utf-8").splitlines() if line.startswith(MARKER)]
    if len(lines) != 1:
        raise SemanticExecutionError("RESULT_MARKER_COUNT")
    value = parse(lines[0].encode())
    required = {"schema_version", "kind", "properties", "behavior_passed", "scope", "os_enforcement_verified",
        "challenge_ready", "model_turns", "experiment_id", "cell_id", "checker_run_status", "aggregate_status",
        "checker_sha256", "oracle_sha256", "case_set_sha256", "workspace_before_sha256", "workspace_after_sha256",
        "workspace_mutated", "invocation_sha256", "task_id", "contract_sha256", "oracle_isolation", "comparison_authorized"}
    if not isinstance(value, dict) or set(value) != required:
        raise SemanticExecutionError("RESULT_FIELDS")
    files = {r["path"]: r["sha256"] for r in plan["judge_files"]}
    expected = {"schema_version": 2, "kind": "profile_i_behavior_observation", "scope": "synthetic_behavior_only",
        "os_enforcement_verified": False, "challenge_ready": False, "model_turns": 0,
        "experiment_id": "profile-i-semantic-diagnostic", "cell_id": plan["diagnostic_id"], "checker_run_status": "completed",
        "checker_sha256": files["checker/check_properties.py"], "oracle_sha256": files["checker/test_behavior.py"],
        "workspace_before_sha256": plan["worker_sha256"], "workspace_after_sha256": plan["worker_sha256"],
        "workspace_mutated": False, "invocation_sha256": plan["invocation_sha256"], "task_id": plan["task_id"],
        "contract_sha256": plan["contract_sha256"], "oracle_isolation": ISOLATION, "comparison_authorized": False}
    if any(type(value[key]) is not type(wanted) or value[key] != wanted for key, wanted in expected.items()):
        raise SemanticExecutionError("RESULT_IDENTITY_OR_SCOPE")
    mapping = {r["property_id"]: r["case_ids"] for r in plan["contract"]["properties"] if r["property_id"] != CLAIM}
    if value["case_set_sha256"] != digest(json.dumps(mapping, sort_keys=True).encode()):
        raise SemanticExecutionError("CASE_SET_HASH")
    selected = selected_properties(plan["contract"], plan["task_id"])
    rows = value["properties"]
    if not isinstance(rows, list) or [r["property_id"] for r in rows] != [r["property_id"] for r in selected]:
        raise SemanticExecutionError("RESULT_PROPERTY_SET")
    statuses = {}
    for row, requirement in zip(rows, selected, strict=True):
        if set(row) != {"property_id", "status", "cases"}:
            raise SemanticExecutionError("RESULT_PROPERTY_FIELDS")
        blocked = any(statuses[p] != "pass" for p in requirement["prerequisite_ids"])
        cases = row["cases"]
        if blocked:
            if row["status"] != "blocked_by_prerequisite" or cases != []:
                raise SemanticExecutionError("PREREQUISITE_NOT_ENFORCED")
        else:
            if not isinstance(cases, list) or [c["case_id"] for c in cases] != requirement["case_ids"]:
                raise SemanticExecutionError("CASE_COVERAGE")
            if any(set(c) != {"case_id", "passed"} or type(c["passed"]) is not bool for c in cases):
                raise SemanticExecutionError("CASE_RESULT_TYPE")
            if row["status"] != ("pass" if all(c["passed"] for c in cases) else "fail"):
                raise SemanticExecutionError("CASE_AGGREGATE")
        statuses[row["property_id"]] = row["status"]
    passed = all(status == "pass" for status in statuses.values())
    if type(value["behavior_passed"]) is not bool or value["behavior_passed"] != passed or value["aggregate_status"] != ("pass" if passed else "fail") or exit_code != (0 if passed else 1):
        raise SemanticExecutionError("RESULT_AGGREGATE_OR_EXIT")
    return value


def _environment(plan, source_environment=None):
    values = os.environ if source_environment is None else source_environment
    if any(name.upper() in {"DOCKER_HOST", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH"} for name in values):
        raise SemanticExecutionError("UNBOUND_DOCKER_ENDPOINT_OVERRIDE")
    environment = build_docker_controller_environment(values)
    environment["DOCKER_CONTEXT"] = plan["docker_context"]
    return environment


def inspect_environment(plan: dict, *, source_environment=None, runner=subprocess.run) -> dict:
    environment = _environment(plan, source_environment)
    observations, failures = {}, []
    commands = {"context": ["context", "inspect", plan["docker_context"]],
                "server": ["version", "--format", "{{json .Server}}"],
                "image": ["image", "inspect", plan["image_reference"]],
                "residue": ["container", "ls", "--all", "--filter", "name=^/" + plan["diagnostic_id"] + "$", "--format", "{{json .Names}}"]}
    for key, args in commands.items():
        try:
            result = runner([plan["docker_executable"], *args], env=environment, capture_output=True,
                            timeout=10, shell=False, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            if result.returncode or len(result.stdout) > MAX_FILE_BYTES:
                raise SemanticExecutionError("DOCKER_INSPECTION_FAILED")
            observations[key] = bool(result.stdout.strip()) if key == "residue" else parse(result.stdout)
        except (OSError, subprocess.TimeoutExpired, SemanticExecutionError):
            failures.append(key.upper() + "_UNAVAILABLE")
    image = observations.get("image")
    server = observations.get("server")
    context = observations.get("context")
    if not isinstance(context, list) or len(context) != 1 or not isinstance(context[0], dict) or context[0].get("Name") != plan["docker_context"]:
        failures.append("CONTEXT_UNVERIFIED")
    if not isinstance(image, list) or len(image) != 1 or not isinstance(image[0], dict):
        failures.append("IMAGE_UNVERIFIED")
    elif (not isinstance(image[0].get("RepoDigests"), list) or plan["image_reference"] not in image[0]["RepoDigests"]
          or image[0].get("Os") != "linux" or image[0].get("Architecture") != "amd64"
          or not re.fullmatch(r"sha256:[0-9a-f]{64}", str(image[0].get("Id")))):
        failures.append("IMAGE_IDENTITY_MISMATCH")
    if not isinstance(server, dict) or server.get("Os") != "linux" or server.get("Arch") not in {"amd64", "x86_64"}:
        failures.append("SERVER_PLATFORM_UNVERIFIED")
    if observations.get("residue") is not False:
        failures.append("CONTAINER_ABSENCE_UNVERIFIED")
    return {"failures": sorted(set(failures)), "identity_sha256": digest(canonical(observations)),
            "image_id": image[0].get("Id") if isinstance(image, list) and image and isinstance(image[0], dict) and re.fullmatch(r"sha256:[0-9a-f]{64}", str(image[0].get("Id"))) else None,
            "server_version": server.get("Version") if isinstance(server, dict) else None}


def valid_noop(plan: dict, noop) -> bool:
    if not isinstance(noop, dict):
        return False
    version = noop.get("python")
    hashes = {r["path"]: r["sha256"] for r in plan["judge_files"]}
    return (isinstance(version, list) and len(version) == 3 and all(type(n) is int for n in version)
        and version[:2] == [3, 12] and version[2] >= 0
        and noop.get("packages") == {"pytest": "8.4.2", "pydantic": "2.13.4"}
        and noop.get("output_io") is True and noop.get("workspace_exists") is True
        and all(noop.get(key) == hashes[path] for key, path in (("checker_sha256", "checker/check_properties.py"),
            ("oracle_sha256", "checker/test_behavior.py"), ("contract_sha256", "checker/semantic-contract.json"))))


def preflight(plan_path: Path, expected_sha256: str, *, rehearse=False, backend=None, source_environment=None, inspector=inspect_environment) -> dict:
    plan = verify_plan(plan_path, expected_sha256)
    if (plan_path.parent / "dispatch.json").exists():
        raise SemanticExecutionError("DIAGNOSTIC_ALREADY_DISPATCHED")
    observed = inspector(plan, source_environment=source_environment)
    failures = list(observed["failures"])
    noop = None
    if rehearse and not failures:
        raw = (backend or SubprocessDockerExecutionBackend()).execute(plan["noop_command"], cwd=plan_path.parent,
            environment=_environment(plan, source_environment), timeout_seconds=30, cleanup_timeout_seconds=15,
            limit=65536, container_name=plan["diagnostic_id"])
        if not raw.started or raw.timed_out or raw.exit_code != 0 or raw.stdout_total > 65536 or raw.cleanup_succeeded is False:
            failures.append("NOOP_FAILED")
        else:
            try:
                noop = parse(raw.stdout)
            except SemanticExecutionError:
                noop = {}
            if not valid_noop(plan, noop):
                failures.append("NOOP_BINDING_FAILED")
        verify_plan(plan_path, expected_sha256)
        after = inspector(plan, source_environment=source_environment)
        if after != observed:
            failures.append("ENVIRONMENT_CHANGED")
    else:
        failures.append("NOOP_NOT_PERFORMED")
    result = {"schema_version": 1, "kind": "profile_i_semantic_preflight", "plan_sha256": expected_sha256,
        "purpose": PURPOSE, "environment": observed, "noop": noop, "failures": sorted(set(failures)),
        "verdict": "NO-GO" if failures else "GO", "comparison_authorized": False,
        "judge_workloads": 0, "model_turns": 0, "phase_f_claims": 0, "created_unix": int(time.time())}
    result["receipt_sha256"] = digest(canonical(result))
    return result


def dispatch_diagnostic(plan_path: Path, *, approved_plan_sha256: str, closure: dict, expected_closure_sha256: str,
                        backend=None, source_environment=None, inspector=inspect_environment) -> dict:
    plan = verify_plan(plan_path, approved_plan_sha256)
    if (not isinstance(closure, dict) or closure.get("receipt_sha256") != expected_closure_sha256
        or digest(canonical({k: v for k, v in closure.items() if k != "receipt_sha256"})) != expected_closure_sha256
        or closure.get("plan_sha256") != approved_plan_sha256 or closure.get("verdict") != "GO"
        or closure.get("kind") != "profile_i_semantic_preflight" or closure.get("purpose") != PURPOSE
        or closure.get("comparison_authorized") is not False
        or any(type(closure.get(k)) is not int or closure[k] != 0 for k in ("judge_workloads", "model_turns", "phase_f_claims"))
        or closure.get("failures") != [] or not valid_noop(plan, closure.get("noop"))
        or type(closure.get("created_unix")) is not int
        or not 0 <= time.time() - closure.get("created_unix", 0) <= 600):
        raise SemanticExecutionError("FRESH_APPROVED_CLOSURE_REQUIRED")
    if inspector(plan, source_environment=source_environment) != closure["environment"]:
        raise SemanticExecutionError("ENVIRONMENT_CHANGED")
    # A one-shot local marker prevents automatic/manual reuse of this diagnostic.
    _write_new(plan_path.parent / "dispatch.json", canonical({"plan_sha256": approved_plan_sha256}))
    limits = plan["limits"]
    raw = (backend or SubprocessDockerExecutionBackend()).execute(plan["command"], cwd=plan_path.parent,
        environment=_environment(plan, source_environment), timeout_seconds=limits["timeout_seconds"],
        cleanup_timeout_seconds=limits["cleanup_timeout_seconds"], limit=limits["stdout_limit_bytes"],
        container_name=plan["diagnostic_id"])
    observation, failure = None, None
    try:
        if not raw.started or raw.timed_out or raw.stdout_total > limits["stdout_limit_bytes"] or raw.cleanup_succeeded is False:
            raise SemanticExecutionError("PROCESS_NOT_COMPLETE")
        observation = verify_observation(plan, raw.stdout, exit_code=raw.exit_code)
        for name in ("worker", "judge", "bundle"):
            if inventory(plan_path.parent / name) != plan[name + "_files"]:
                raise SemanticExecutionError("INPUT_CHANGED_AFTER_EXECUTION")
    except (SemanticExecutionError, UnicodeError, KeyError, TypeError) as exc:
        failure = str(exc) if isinstance(exc, SemanticExecutionError) else "MALFORMED_RESULT"
        observation = None
    result = {"schema_version": 1, "kind": "profile_i_semantic_diagnostic_result", "plan_sha256": approved_plan_sha256,
        "diagnostic_passed": observation is not None and observation["behavior_passed"], "observation": observation,
        "failure": failure, "comparison_authorized": False, "challenge_ready": False, "model_turns": 0,
        "stdout_sha256": raw.stdout_sha256, "stderr_sha256": raw.stderr_sha256}
    result["result_sha256"] = digest(canonical(result))
    _write_new(plan_path.parent / "diagnostic-result.json", canonical(result))
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    create = sub.add_parser("prepare")
    for flag in ("repository", "root", "git-executable", "docker-executable"):
        create.add_argument("--" + flag, type=Path, required=True)
    create.add_argument("--source-commit", required=True)
    create.add_argument("--diagnostic-id", required=True)
    create.add_argument("--task-id", choices=[f"I{i:02d}" for i in range(1, 9)])
    for action in ("verify", "preflight"):
        p = sub.add_parser(action)
        p.add_argument("--plan", type=Path, required=True)
        p.add_argument("--plan-sha256", required=True)
        if action == "preflight":
            p.add_argument("--rehearse-noop", action="store_true")
            p.add_argument("--receipt-name", default="preflight.json")
    args = parser.parse_args(argv)
    try:
        if args.action == "prepare":
            result = prepare(args.repository, args.root, git_executable=args.git_executable, docker_executable=args.docker_executable,
                             source_commit=args.source_commit, diagnostic_id=args.diagnostic_id, task_id=args.task_id)
        elif args.action == "verify":
            plan = verify_plan(args.plan, args.plan_sha256)
            result = {"verified": True, "plan_sha256": plan["plan_sha256"], "comparison_authorized": False}
        else:
            if not re.fullmatch(r"preflight(?:-[a-z0-9-]+)?\.json", args.receipt_name):
                raise SemanticExecutionError("UNSAFE_RECEIPT_NAME")
            if (args.plan.parent / args.receipt_name).exists():
                raise SemanticExecutionError("RECEIPT_ALREADY_EXISTS")
            result = preflight(args.plan, args.plan_sha256, rehearse=args.rehearse_noop)
            _write_new(args.plan.parent / args.receipt_name, canonical(result))
        print(canonical(result).decode(), end="")
        return 2 if result.get("verdict") == "NO-GO" else 0
    except (SemanticExecutionError, DockerJudgeError, OSError, KeyError, TypeError, subprocess.TimeoutExpired):
        print('{"error":"SEMANTIC_PREPARATION_FAILED","comparison_authorized":false}')
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
