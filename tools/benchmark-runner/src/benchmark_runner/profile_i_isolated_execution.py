"""F14 v3: frozen host oracle, read-only candidate container, bounded JSON.

No Worker import on the host. Preparation/preflight are not qualification.
Actual dispatch requires a fresh closure AND a separate user approval turn.
This module never grants Phase E/F promotion, model use, or comparison readiness.
"""
from __future__ import annotations

import argparse
import ast
import importlib.metadata
import json
from pathlib import Path
import re
import secrets
import sys
import time

from benchmark_runner import profile_i_semantic_execution as binding
from benchmark_runner import profile_i_isolated_oracle as oracle

ROOT = "tools/benchmark-runner/qualifications/profile-i-semantic-v3"
SOURCES = {name: f"{ROOT}/{name}" for name in ("probe.py", "probe_fixtures.py", "runner_support.py")}
TRUSTED = ("tools/benchmark-runner/src/benchmark_runner/profile_i_isolated_execution.py",
           "tools/benchmark-runner/src/benchmark_runner/profile_i_isolated_oracle.py")
PURPOSE = "isolated_reference_qualification"
Error = binding.SemanticExecutionError
WORKER_MODULE = "tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py"
# Inspected controls are appended as bytes only; never imported/evaluated here.
VARIANTS = {
    "reference": b"",
    "equivalent": b"\n_original_recompute = recompute_probe_pass\ndef independently_named_recompute(*args, **kwargs):\n    return _original_recompute(*args, **kwargs)\nrecompute_probe_pass = independently_named_recompute\n",
    "constant-success": b"\nverify_sdk_profile_provenance = lambda *args, **kwargs: True\n",
    "forged-json": b"\nimport json\njson.dumps = lambda *args, **kwargs: '{\"passed\":true}'\n",
    "empty-exit": b"\nimport os\nos._exit(0)\n",
    "nonzero-exit": b"\nimport os\nos._exit(7)\n",
    "timeout": b"\nimport time\nwhile True:\n    time.sleep(1)\n",
    "output-flood": b"\nimport os\nfor _n in range(512):\n    os.write(1, b'x' * 4096)\n",
    "write-readonly": b"\nfrom pathlib import Path\nPath('/workspace/f14-forbidden-write').write_bytes(b'synthetic')\n",
}


def seal(value, field):
    return {**value, field: binding.digest(binding.canonical(value))}


def unseal(value, field, expected):
    if (not isinstance(value, dict) or not re.fullmatch("[0-9a-f]{64}", expected)
        or value.get(field) != expected or binding.digest(binding.canonical({k:v for k,v in value.items() if k != field})) != expected):
        raise Error("INVALID_SEAL")
    return value


def command(plan, root, case, *, noop=False):
    argv = [plan["docker_executable"], "run", "--rm", "--pull", "never", "--name", plan["diagnostic_id"],
        "--network", "none", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--pids-limit", "64", "--memory", "512m", "--cpus", "1", "--user", "65532:65532"]
    for source, target in ((root / "binding/worker", "/workspace"), (root / "driver", "/driver"), (root / "requests" / case, "/request")):
        argv.extend(["--mount", f"type=bind,source={binding.checked(source)},target={target},readonly"])
    argv.extend(["--mount", f"type=bind,source={binding.checked(root / 'variant.py')},target=/workspace/{WORKER_MODULE},readonly"])
    argv += ["--tmpfs", "/tmp:rw,noexec,nosuid,size=32m", "--workdir", "/tmp",
        "--env", "PYTHONDONTWRITEBYTECODE=1", "--env", "PYTHONIOENCODING=utf-8", "--env", "PYTHONUTF8=1", plan["image_reference"]]
    if not noop:
        return argv + ["python", "-I", "/driver/probe.py"]
    # Only standard library / package metadata; no Worker or driver code import.
    script = "\n".join([
        "import hashlib,importlib.metadata as m,json,os,pathlib,sys",
        "p=pathlib.Path('/tmp/preflight-io'); p.write_bytes(b'noop'); assert p.read_bytes()==b'noop'; p.unlink()",
        "readonly=[]",
        "for root in ['/workspace','/driver','/request']:",
        " p=pathlib.Path(root)/'.preflight-write-check'",
        " try:",
        "  p.open('xb').close(); p.unlink(); readonly.append(False)",
        " except (PermissionError,OSError): readonly.append(True)",
        "status=dict(line.split(':',1) for line in pathlib.Path('/proc/self/status').read_text().splitlines() if ':' in line)",
        "files={name:hashlib.sha256((pathlib.Path('/driver')/name).read_bytes()).hexdigest() for name in ['probe.py','probe_fixtures.py','runner_support.py']}",
        "print(json.dumps(dict(python=list(sys.version_info[:3]),packages={n:m.version(n) for n in ['pytest','pydantic']},driver=files,request=hashlib.sha256(pathlib.Path('/request/request.json').read_bytes()).hexdigest(),candidate=hashlib.sha256(pathlib.Path('/workspace/tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py').read_bytes()).hexdigest(),uid=os.getuid(),caps=status['CapEff'].strip(),no_new_privs=status['NoNewPrivs'].strip(),readonly=readonly,tmp_io=True)))",
    ])
    return argv + ["python", "-I", "-c", script]


def prepare(repo: Path, root: Path, *, git_executable: Path, docker_executable: Path, source_commit: str, diagnostic_id: str, variant="reference"):
    repo, root = binding.checked(repo), binding.checked(root)
    if root.exists() or variant not in VARIANTS:
        raise Error("FRESH_ROOT_REQUIRED")
    legacy = binding.prepare(repo, root / "binding", git_executable=git_executable, docker_executable=docker_executable,
        source_commit=source_commit, diagnostic_id=diagnostic_id)
    candidate = binding.read_file(root / "binding/worker" / WORKER_MODULE) + VARIANTS[variant]
    binding._write_new(root / "variant.py", candidate)
    sources = {}
    for name, path in SOURCES.items():
        data = binding._git(repo, git_executable, "cat-file", "blob", source_commit + ":" + path)
        binding._write_new(root / "driver" / name, data)
        sources[path] = binding.digest(data)
    for path in TRUSTED:
        data = binding._git(repo, git_executable, "cat-file", "blob", source_commit + ":" + path)
        sources[path] = binding.digest(data)
    requests = [{"version": 3, "case": case, "nonce": secrets.token_hex(16)} for case in oracle.CASES]
    for request in requests:
        binding._write_new(root / "requests" / request["case"] / "request.json", binding.canonical(request))
    plan = {"version": 3, "purpose": PURPOSE, "oracle_isolation": "host_oracle_container_candidate",
        "variant": variant, "candidate_sha256": binding.digest(candidate),
        "comparison_authorized": False, "automatic_continuation": False, "model_turns": 0, "phase_f_claims": 0,
        "repository": str(repo), "source_commit": source_commit, "source_tree": legacy["source_tree"],
        "binding_sha256": legacy["plan_sha256"], "sources": sources, "requests": requests,
        "diagnostic_id": diagnostic_id, "image_reference": binding.DOCKER_JUDGE_IMAGE, "docker_context": "desktop-linux",
        "docker_executable": legacy["docker_executable"], "python_executable": sys.executable,
        "python_sha256": binding._executable_hash(Path(sys.executable)), "python_version": list(sys.version_info[:3]),
        "driver_files": binding.inventory(root / "driver"), "request_files": binding.inventory(root / "requests"),
        "properties": oracle.PROPERTIES, "dependencies": oracle.DEPENDENCIES, "public_tasks": oracle.PUBLIC_TASKS}
    plan["commands"] = {case: command(plan, root, case) for case in oracle.CASES}
    plan["noop_commands"] = {case: command(plan, root, case, noop=True) for case in oracle.CASES}
    plan = seal(plan, "plan_sha256")
    binding._write_new(root / "plan.json", binding.canonical(plan))
    verify(root / "plan.json", plan["plan_sha256"])
    return plan


def verify(path: Path, expected: str):
    root = binding.checked(path).parent
    plan = unseal(binding.parse(binding.read_file(path)), "plan_sha256", expected)
    literals = {"version": 3, "purpose": PURPOSE, "oracle_isolation": "host_oracle_container_candidate", "comparison_authorized": False,
        "automatic_continuation": False, "model_turns": 0, "phase_f_claims": 0, "image_reference": binding.DOCKER_JUDGE_IMAGE,
        "docker_context": "desktop-linux", "properties": oracle.PROPERTIES, "dependencies": oracle.DEPENDENCIES, "public_tasks": oracle.PUBLIC_TASKS}
    if any(not oracle.same(plan.get(k), v) for k,v in literals.items()):
        raise Error("FIXED_SCOPE_CHANGED")
    legacy = binding.verify_plan(root / "binding/plan.json", plan["binding_sha256"])
    if any(plan[k] != legacy[k] for k in ("repository", "source_commit", "source_tree", "docker_executable", "diagnostic_id")):
        raise Error("BINDING_CHANGED")
    if plan["variant"] not in VARIANTS:
        raise Error("UNREVIEWED_VARIANT")
    candidate = binding.read_file(root / "binding/worker" / WORKER_MODULE) + VARIANTS[plan["variant"]]
    if binding.read_file(root / "variant.py") != candidate or binding.digest(candidate) != plan["candidate_sha256"]:
        raise Error("CANDIDATE_VARIANT_CHANGED")
    utility_imports = {a.name for node in ast.walk(ast.parse(candidate)) if isinstance(node, ast.ImportFrom)
                       and node.module == "benchmark_runner.runner" for a in node.names}
    if utility_imports != {"atomic_write", "canonical_json_bytes", "sha256_bytes", "sha256_file"}:
        raise Error("FIXTURE_DEPENDENCY_CONTRACT_CHANGED")
    if (sys.executable != plan["python_executable"] or list(sys.version_info[:3]) != plan["python_version"]
        or binding._executable_hash(Path(sys.executable)) != plan["python_sha256"]):
        raise Error("HOST_PYTHON_CHANGED")
    repo, git = Path(plan["repository"]), Path(legacy["git_executable"])
    if set(plan["sources"]) != {*SOURCES.values(), *TRUSTED}:
        raise Error("SOURCE_SET_CHANGED")
    for source, sha in plan["sources"].items():
        data = binding._git(repo, git, "cat-file", "blob", plan["source_commit"] + ":" + source)
        if binding.digest(data) != sha:
            raise Error("SOURCE_BYTES_CHANGED")
        if source in TRUSTED and binding.read_file(repo / source).replace(b"\r\n", b"\n") != data.replace(b"\r\n", b"\n"):
            raise Error("HOST_ORACLE_CHANGED")
    for name, source in SOURCES.items():
        if binding.digest(binding.read_file(root / "driver" / name)) != plan["sources"][source]:
            raise Error("DRIVER_CHANGED")
    for directory in ("driver", "requests"):
        if binding.inventory(root / directory) != plan["driver_files" if directory == "driver" else "request_files"]:
            raise Error("INPUT_SET_CHANGED")
    if [r.get("case") for r in plan["requests"]] != list(oracle.CASES):
        raise Error("CASE_SET_CHANGED")
    for request in plan["requests"]:
        if (set(request) != {"version", "case", "nonce"} or type(request["version"]) is not int or request["version"] != 3
            or not re.fullmatch("[0-9a-f]{32}", request["nonce"])):
            raise Error("REQUEST_CHANGED")
        if binding.read_file(root / "requests" / request["case"] / "request.json") != binding.canonical(request):
            raise Error("REQUEST_BYTES_CHANGED")
    for field, noop in (("commands", False), ("noop_commands", True)):
        if plan[field] != {case: command(plan, root, case, noop=noop) for case in oracle.CASES}:
            raise Error("COMMAND_CHANGED")
    return plan


def valid_noop(plan, request, value):
    required = {"python", "packages", "driver", "request", "candidate", "uid", "caps", "no_new_privs", "readonly", "tmp_io"}
    if type(value) is not dict or set(value) != required:
        return False
    return (type(value["python"]) is list and len(value["python"]) == 3 and all(type(n) is int for n in value["python"])
        and value["python"][:2] == [3, 12] and value["packages"] == {"pytest": "8.4.2", "pydantic": "2.13.4"}
        and value["driver"] == {name: plan["sources"][source] for name,source in SOURCES.items()}
        and value["request"] == binding.digest(binding.canonical(request)) and oracle.same(value["uid"], 65532)
        and value["candidate"] == plan["candidate_sha256"]
        and value["caps"] == "0000000000000000" and value["no_new_privs"] == "1"
        and oracle.same(value["readonly"], [True, True, True]) and value["tmp_io"] is True)


def completed(raw, limit):
    return (raw.started and not raw.timed_out and type(raw.exit_code) is int and raw.exit_code == 0
        and raw.stdout_total <= limit and raw.stderr_total <= limit and raw.cleanup_succeeded is not False)


def preflight(path, expected, *, rehearse=False, backend=None, inspector=binding.inspect_environment, source_environment=None):
    plan = verify(path, expected)
    if (path.parent / "dispatch.json").exists():
        raise Error("ALREADY_DISPATCHED")
    environment = binding._environment(plan, source_environment)
    observed = inspector(plan, source_environment=source_environment)
    failures, rehearsals = list(observed["failures"]), []
    if not rehearse:
        failures.append("NOOP_NOT_PERFORMED")
    elif not failures:
        engine = backend or binding.SubprocessDockerExecutionBackend()
        for request in plan["requests"]:
            try:
                raw = engine.execute(plan["noop_commands"][request["case"]], cwd=path.parent, environment=environment,
                    timeout_seconds=30, cleanup_timeout_seconds=15, limit=65536, container_name=plan["diagnostic_id"])
                value = binding.parse(raw.stdout) if completed(raw, 65536) else None
                if not valid_noop(plan, request, value):
                    raise Error("NOOP_FAILED")
                rehearsals.append({"case": request["case"], "observation": value})
                if inspector(plan, source_environment=source_environment) != observed:
                    raise Error("ENVIRONMENT_CHANGED")
            except (OSError, ValueError, binding.DockerJudgeError):
                failures.append("NOOP_OR_ENVIRONMENT_FAILED")
                break
    if len(rehearsals) != len(oracle.CASES):
        failures.append("INCOMPLETE_REHEARSAL")
    verify(path, expected)
    return seal({"version": 3, "purpose": PURPOSE, "plan_sha256": expected, "created_unix": int(time.time()),
        "rehearsal_backend": "native_docker" if backend is None and inspector is binding.inspect_environment else "injected_test_backend",
        "environment": observed, "rehearsals": rehearsals, "failures": sorted(set(failures)), "verdict": "NO-GO" if failures else "GO",
        "model_turns": 0, "judge_workloads": 0, "phase_f_claims": 0, "comparison_authorized": False}, "receipt_sha256")


def dispatch(path, *, approved_plan_sha256, closure, expected_closure_sha256, backend=None,
             inspector=binding.inspect_environment, source_environment=None):
    plan = verify(path, approved_plan_sha256)
    unseal(closure, "receipt_sha256", expected_closure_sha256)
    fixed = dict(version=3, purpose=PURPOSE, plan_sha256=approved_plan_sha256, verdict="GO", failures=[], model_turns=0,
                 judge_workloads=0, phase_f_claims=0, comparison_authorized=False,
                 rehearsal_backend="native_docker" if backend is None and inspector is binding.inspect_environment else "injected_test_backend")
    if (any(not oracle.same(closure.get(k),v) for k,v in fixed.items()) or type(closure.get("created_unix")) is not int
        or not 0 <= time.time() - closure["created_unix"] <= 600
        or [r["case"] for r in closure.get("rehearsals", [])] != list(oracle.CASES)
        or any(not valid_noop(plan, request, row["observation"]) for request,row in zip(plan["requests"], closure["rehearsals"], strict=True))):
        raise Error("FRESH_APPROVED_CLOSURE_REQUIRED")
    if inspector(plan, source_environment=source_environment) != closure["environment"]:
        raise Error("ENVIRONMENT_CHANGED")
    environment = binding._environment(plan, source_environment)
    root = path.parent
    binding._write_new(root / "dispatch.json", binding.canonical({"approved_plan_sha256": approved_plan_sha256,
        "closure_sha256": expected_closure_sha256, "created_unix": int(time.time())}))
    engine = backend or binding.SubprocessDockerExecutionBackend()
    cases, records, failure = [], [], None
    for request in plan["requests"]:
        try:
            verify(path, approved_plan_sha256)
            if inspector(plan, source_environment=source_environment) != closure["environment"]:
                raise Error("ENVIRONMENT_CHANGED")
            raw = engine.execute(plan["commands"][request["case"]], cwd=root, environment=environment,
                timeout_seconds=30, cleanup_timeout_seconds=15, limit=1_048_576, container_name=plan["diagnostic_id"])
            # Backend retains one sentinel byte past the limit. Persist only
            # the contractual prefix while keeping full-stream counts/hashes.
            stdout, stderr = raw.stdout[:1_048_576], raw.stderr[:1_048_576]
            records.append({"case": request["case"], "started": raw.started, "exit_code": raw.exit_code, "timed_out": raw.timed_out,
                "stdout_sha256": raw.stdout_sha256, "stderr_sha256": raw.stderr_sha256, "cleanup_succeeded": raw.cleanup_succeeded,
                "stdout_total": raw.stdout_total, "stderr_total": raw.stderr_total,
                "stdout_size": len(stdout), "stderr_size": len(stderr),
                "stdout_prefix_sha256": binding.digest(stdout), "stderr_prefix_sha256": binding.digest(stderr)})
            # Bounded streams remain private evidence, never Git or executed code.
            binding._write_new(root / "streams" / (request["case"] + ".stdout"), stdout)
            binding._write_new(root / "streams" / (request["case"] + ".stderr"), stderr)
            if not completed(raw, 1_048_576):
                raise Error("PROCESS_NOT_COMPLETE")
            cases.append(oracle.grade(request, raw.stdout, exit_code=raw.exit_code))
            if inspector(plan, source_environment=source_environment) != closure["environment"]:
                raise Error("ENVIRONMENT_CHANGED")
        except (OSError, ValueError, binding.DockerJudgeError):
            failure = "EXECUTION_INCOMPLETE"
            break
    input_unchanged = True
    try:
        verify(path, approved_plan_sha256)
    except (OSError, ValueError):
        input_unchanged = False
        failure = "INPUT_CHANGED"
    try:
        final_environment = inspector(plan, source_environment=source_environment)
        if final_environment != closure["environment"]:
            failure = "ENVIRONMENT_CHANGED"
    except (OSError, ValueError, binding.DockerJudgeError):
        final_environment = None
        failure = "ENVIRONMENT_UNVERIFIED"
    completed_cases = {r["case"] for r in cases}
    cases.extend({"case": case, "passed": False, "reason": "NOT_COMPLETED"} for case in oracle.CASES if case not in completed_cases)
    cases.append(oracle.claims(root / "binding/worker"))
    result = oracle.aggregate(cases)
    if failure:
        result["behavior_passed"] = False
    result.update(version=3, evidence_version=2, purpose=PURPOSE, variant=plan["variant"], plan_sha256=approved_plan_sha256,
        input_unchanged=input_unchanged, final_environment=final_environment, failure=failure, processes=records,
        execution_backend=fixed["rehearsal_backend"], model_turns=0, phase_f_claims=0)
    result = seal(result, "result_sha256")
    binding._write_new(root / "result.json", binding.canonical(result))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("prepare")
    for flag in ("repository", "root", "git-executable", "docker-executable"):
        p.add_argument("--" + flag, type=Path, required=True)
    p.add_argument("--source-commit", required=True)
    p.add_argument("--diagnostic-id", required=True)
    p.add_argument("--variant", choices=sorted(VARIANTS), default="reference")
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
                source_commit=args.source_commit, diagnostic_id=args.diagnostic_id, variant=args.variant)
        elif args.action == "verify":
            plan = verify(args.plan, args.plan_sha256)
            result = {"verified": True, "plan_sha256": plan["plan_sha256"], "comparison_authorized": False}
        else:
            if not re.fullmatch(r"preflight(?:-[a-z0-9-]+)?\.json", args.receipt_name) or (args.plan.parent / args.receipt_name).exists():
                raise Error("FRESH_RECEIPT_REQUIRED")
            result = preflight(args.plan, args.plan_sha256, rehearse=args.rehearse_noop)
            binding._write_new(args.plan.parent / args.receipt_name, binding.canonical(result))
        print(binding.canonical(result).decode(), end="")
        return 2 if result.get("verdict") == "NO-GO" else 0
    except (ValueError, OSError, KeyError, TypeError, binding.DockerJudgeError):
        print('{"error":"ISOLATED_PREPARATION_FAILED","comparison_authorized":false}')
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
