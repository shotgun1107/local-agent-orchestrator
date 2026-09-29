"""Explicitly authorized, fixed model-free Linux supervisor probe; never a Judge.

Library calls only: prepare first, inspect its external plan hash, then run once.
No candidate, SDK, model, Cell or general runtime permission is implied.
"""
from __future__ import annotations

from pathlib import Path
import sys
import time

from benchmark_runner import profile_i_semantic_execution as binding
from benchmark_runner import profile_i_isolated_execution as seals

SCRIPT = "tools/benchmark-runner/qualifications/profile-i-semantic-v4/supervisor_boundary.py"
ORIGIN = "https://github.com/shotgun1107/local-agent-orchestrator.git"
BRANCH = "codex/phase-d-artifacts"


def source(repo, git, expected):
    if (binding._git(repo, git, "rev-parse", "HEAD").decode().strip() != expected
        or binding._git(repo, git, "status", "--porcelain=v1").strip()
        or binding._git(repo, git, "branch", "--show-current").decode().strip() != BRANCH
        or binding._git(repo, git, "remote", "get-url", "origin").decode().strip() != ORIGIN):
        raise ValueError("CLEAN_PINNED_SOURCE_REQUIRED")


def commands(plan):
    prefix = [plan["docker_executable"],"run","--rm","--pull","never","--name",plan["diagnostic_id"],
        "--network","none","--read-only","--cap-drop","ALL","--security-opt","no-new-privileges",
        "--pids-limit","64","--memory","512m","--cpus","1","--user","65532:65532",
        "--mount",f"type=bind,source={Path(plan['root']) / 'driver'},target=/driver,readonly",
        "--tmpfs","/tmp:rw,noexec,nosuid,size=32m","--workdir","/tmp",
        "--env","PYTHONDONTWRITEBYTECODE=1",plan["image_reference"],"python","-I","-B"]
    noop = '\n'.join([
        "import hashlib,json,os,pathlib,sys",
        "s=dict(x.split(':',1) for x in pathlib.Path('/proc/self/status').read_text().splitlines() if ':' in x)",
        "p=pathlib.Path('/tmp/io');p.write_bytes(b'probe');assert p.read_bytes()==b'probe';p.unlink()",
        "readonly=False",
        "try: pathlib.Path('/driver/write-check').write_bytes(b'probe')",
        "except OSError: readonly=True",
        "print(json.dumps(dict(uid=os.getuid(),caps=s['CapEff'].strip(),nnp=s['NoNewPrivs'].strip(),readonly=readonly,python=list(sys.version_info[:2]),script_sha256=hashlib.sha256(pathlib.Path('/driver/supervisor_boundary.py').read_bytes()).hexdigest())))",
    ])
    return prefix+["-c",noop], prefix+["/driver/supervisor_boundary.py"]


def prepare(repo: Path, root: Path, *, git: Path, docker: Path, source_commit: str):
    repo, root = binding.checked(repo), binding.checked(root)
    if root.exists() or not any(base in root.parents for base in (Path("C:/LAO/evidence"),Path("C:/LAO/tmp"))):
        raise ValueError("FRESH_LAO_ROOT_REQUIRED")
    source(repo,git,source_commit)
    code = binding._git(repo,git,"cat-file","blob",source_commit+":"+SCRIPT)
    plan = {"version":1,"purpose":"supervisor_boundary_probe_only","source_commit":source_commit,
        "repository":str(repo),"root":str(root),"git_executable":str(git),"docker_executable":str(docker),
        "docker_sha256":binding._executable_hash(docker),"diagnostic_id":"f14-supervisor-boundary-20260929",
        "image_reference":binding.DOCKER_JUDGE_IMAGE,"docker_context":"desktop-linux","script_sha256":binding.digest(code),
        "python_executable":sys.executable,"python_sha256":binding._executable_hash(Path(sys.executable)),
        "comparison_authorized":False,"challenge_ready":False,"model_turns":0,"phase_f_claims":0}
    binding._write_new(root/"driver/supervisor_boundary.py",code)
    plan["noop_command"],plan["probe_command"] = commands(plan)
    plan=seals.seal(plan,"plan_sha256")
    binding._write_new(root/"plan.json",binding.canonical(plan))
    return plan


def verify(path, expected):
    path=binding.checked(path)
    p=seals.unseal(binding.parse(binding.read_file(path)),"plan_sha256",expected)
    source(Path(p["repository"]),Path(p["git_executable"]),p["source_commit"])
    if (str(path.parent)!=p["root"] or p["purpose"]!="supervisor_boundary_probe_only"
        or p["image_reference"]!=binding.DOCKER_JUDGE_IMAGE or p["docker_context"]!="desktop-linux"
        or p["comparison_authorized"] is not False or p["challenge_ready"] is not False
        or type(p["model_turns"]) is not int or p["model_turns"]!=0 or type(p["phase_f_claims"]) is not int or p["phase_f_claims"]!=0
        or p["python_executable"]!=sys.executable or p["python_sha256"]!=binding._executable_hash(Path(sys.executable))
        or p["docker_sha256"]!=binding._executable_hash(Path(p["docker_executable"]))
        or binding.digest(binding.read_file(path.parent/"driver/supervisor_boundary.py"))!=p["script_sha256"]
        or (p["noop_command"],p["probe_command"])!=commands(p)):
        raise ValueError("PROBE_BINDING_CHANGED")
    return p


def run_approved(path: Path, expected: str, *, authorization_note: str):
    p=verify(path,expected)
    root=path.parent
    if not authorization_note.strip(): raise ValueError("EXPLICIT_AUTHORIZATION_REQUIRED")
    binding._write_new(root/"started.json",binding.canonical({"plan_sha256":expected,"authorization_note":authorization_note}))
    env=binding._environment(p)
    initial=binding.inspect_environment(p)
    engine=binding.SubprocessDockerExecutionBackend()
    rows=[]
    passed=False
    failure=None
    noop_completed_at=None
    try:
        if initial["failures"]: raise ValueError("ENVIRONMENT_NO_GO")
        for kind in ("noop","probe"):
            verify(path,expected)
            if binding.inspect_environment(p)!=initial: raise ValueError("ENVIRONMENT_CHANGED")
            if kind=="probe" and (noop_completed_at is None or not 0 <= time.monotonic()-noop_completed_at <= 600):
                raise ValueError("FRESH_NOOP_REQUIRED")
            raw=engine.execute(p[kind+"_command"],cwd=root,environment=env,timeout_seconds=15,cleanup_timeout_seconds=15,
                limit=65536,container_name=p["diagnostic_id"])
            binding._write_new(root/(kind+".stdout"),raw.stdout)
            binding._write_new(root/(kind+".stderr"),raw.stderr)
            if not seals.completed(raw,65536): raise ValueError("PROCESS_FAILED")
            data=binding.parse(raw.stdout)
            if kind=="noop":
                wanted={"uid":65532,"caps":"0000000000000000","nnp":"1","readonly":True,"python":[3,12],"script_sha256":p["script_sha256"]}
                if binding.canonical(data)!=binding.canonical(wanted): raise ValueError("NOOP_MISMATCH")
                noop_completed_at=time.monotonic()
            elif (data.get("kind")!="supervisor_boundary_probe" or data.get("uid")!=65532 or data.get("parent_dumpable")!=0
                or binding.canonical(data.get("child_parent_procfs_denied"))!=binding.canonical({k:True for k in ("fd/1","fd/2","mem","environ")})
                or data.get("captured_forged_verdict_is_not_a_verdict") is not True
                or data.get("comparison_authorized") is not False or data.get("challenge_ready") is not False):
                raise ValueError("PROBE_FAILED")
            rows.append({"kind":kind,"observation":data,"exit_code":raw.exit_code,"stdout_sha256":raw.stdout_sha256,"stderr_sha256":raw.stderr_sha256})
        verify(path,expected)
        passed=True
    except (OSError,ValueError,binding.DockerJudgeError) as error:
        failure=type(error).__name__
    final=binding.inspect_environment(p)
    if final!=initial or final["failures"]: failure="FINAL_ENVIRONMENT_CHANGED"
    passed=passed and final==initial and not final["failures"]
    result=seals.seal({"version":1,"plan_sha256":expected,"created_unix":int(time.time()),"source_commit":p["source_commit"],
        "initial_environment":initial,"final_environment":final,"rows":rows,"native_boundary_probe_passed":passed,"failure":failure,
        "comparison_authorized":False,"challenge_ready":False,"model_turns":0,"phase_f_claims":0},"result_sha256")
    binding._write_new(root/"result.json",binding.canonical(result))
    return result
