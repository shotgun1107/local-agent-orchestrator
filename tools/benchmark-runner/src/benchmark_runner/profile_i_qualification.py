"""Closed native F14 preparation matrix; no model, Cell or promotion authority.

The agent must have explicit authorization for continuous preparatory diagnostics
before calling run_approved. CLI exposes saved-result verification, not execution.
Every variant still needs a sealed plan, fresh native no-op and one-shot dispatch.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

from benchmark_runner import profile_i_isolated_execution as execution
from benchmark_runner import profile_i_isolated_oracle as oracle
from benchmark_runner import profile_i_semantic_execution as binding

MODULE = "tools/benchmark-runner/src/benchmark_runner/profile_i_qualification.py"
VARIANTS = tuple(execution.VARIANTS)
LIMIT = 1_048_576


def read_sealed(path, field, expected):
    return execution.unseal(binding.parse(binding.read_file(path)), field, expected)


def prepare(repo: Path, root: Path, *, source_commit: str, git_executable: Path, docker_executable: Path, token: str):
    repo, root = binding.checked(repo), binding.checked(root)
    if root.exists() or not re.fullmatch("[a-z0-9-]{1,24}", token):
        raise ValueError("FRESH_MATRIX_ROOT_AND_TOKEN_REQUIRED")
    rows = []
    for variant in VARIANTS:
        plan = execution.prepare(repo, root / variant, git_executable=git_executable, docker_executable=docker_executable,
            source_commit=source_commit, diagnostic_id="f14-" + token + "-" + variant, variant=variant)
        rows.append({"variant": variant, "plan_sha256": plan["plan_sha256"]})
    code = binding._git(repo, git_executable, "cat-file", "blob", source_commit + ":" + MODULE)
    value = execution.seal({"version": 1, "kind": "f14_fixed_preparation_matrix", "source_commit": source_commit,
        "verifier_sha256": binding.digest(code.replace(b"\r\n", b"\n")), "variants": rows,
        "scope": "fixed_synthetic_qualification_only", "comparison_authorized": False, "model_turns": 0, "phase_f_claims": 0}, "manifest_sha256")
    binding._write_new(root / "matrix.json", binding.canonical(value))
    return value


def manifest(root, expected):
    root = binding.checked(root)
    value = read_sealed(root / "matrix.json", "manifest_sha256", expected)
    if (not oracle.same(value.get("version"), 1)
        or value.get("kind") != "f14_fixed_preparation_matrix" or value.get("scope") != "fixed_synthetic_qualification_only"
        or value.get("comparison_authorized") is not False or not oracle.same(value.get("model_turns"), 0)
        or not oracle.same(value.get("phase_f_claims"), 0) or [r["variant"] for r in value["variants"]] != list(VARIANTS)
        or value["verifier_sha256"] != binding.digest(binding.read_file(Path(__file__)).replace(b"\r\n", b"\n"))):
        raise ValueError("MATRIX_CONTRACT_OR_VERIFIER_CHANGED")
    if (not re.fullmatch(r"[0-9a-f]{40}", value["source_commit"])
        or any(set(row) != {"variant", "plan_sha256"} or not re.fullmatch(r"[0-9a-f]{64}", row["plan_sha256"]) for row in value["variants"])):
        raise ValueError("MATRIX_IDENTITIES")
    return value


def read_run(root: Path, *, plan_sha256: str, result_sha256: str):
    """Recompute saved observations without executing candidate or requiring HEAD.

Historical verification requires this oracle's exact recorded code bytes. It
verifies bounded captured prefixes; a dropped tail cannot be independently read.
"""
    root = binding.checked(root)
    plan = read_sealed(root / "plan.json", "plan_sha256", plan_sha256)
    result = read_sealed(root / "result.json", "result_sha256", result_sha256)
    if (not oracle.same(result.get("evidence_version"), 2) or result.get("execution_backend") != "native_docker"
        or result.get("plan_sha256") != plan_sha256 or result.get("variant") != plan["variant"]
        or result.get("input_unchanged") is not True or result.get("comparison_authorized") is not False
        or result.get("challenge_ready") is not False or result.get("os_enforcement_verified") is not False
        or not oracle.same(result.get("model_turns"), 0)
        or not oracle.same(result.get("phase_f_claims"), 0)):
        raise ValueError("NATIVE_RESULT_CONTRACT")
    current_oracle = binding.read_file(Path(oracle.__file__)).replace(b"\r\n", b"\n")
    if binding.digest(current_oracle) != plan["sources"][execution.TRUSTED[1]]:
        raise ValueError("ORACLE_REVISION_CHANGED")
    legacy = read_sealed(root / "binding/plan.json", "plan_sha256", plan["binding_sha256"])
    for name in ("worker", "judge", "bundle"):
        if binding.inventory(root / "binding" / name) != legacy[name + "_files"]:
            raise ValueError("INPUT_CHANGED")
    for name, field in (("driver", "driver_files"), ("requests", "request_files")):
        if binding.inventory(root / name) != plan[field]:
            raise ValueError("INPUT_CHANGED")
    if binding.digest(binding.read_file(root / "variant.py")) != plan["candidate_sha256"]:
        raise ValueError("VARIANT_CHANGED")
    closure = binding.parse(binding.read_file(root / "preflight.json"))
    marker = binding.parse(binding.read_file(root / "dispatch.json"))
    execution.unseal(closure, "receipt_sha256", marker["closure_sha256"])
    if (marker["approved_plan_sha256"] != plan_sha256 or closure["plan_sha256"] != plan_sha256 or closure["verdict"] != "GO"
        or closure["rehearsal_backend"] != "native_docker" or closure["failures"] != []
        or result["final_environment"] != closure["environment"] or closure["environment"]["failures"] != []
        or [r["case"] for r in closure["rehearsals"]] != list(oracle.CASES)
        or any(not execution.valid_noop(plan, request, row["observation"]) for request,row in zip(plan["requests"], closure["rehearsals"], strict=True))):
        raise ValueError("NATIVE_CLOSURE_OR_FINAL_ENVIRONMENT")
    if (type(marker.get("created_unix")) is not int or type(closure.get("created_unix")) is not int
        or not 0 <= marker["created_unix"] - closure["created_unix"] <= 600
        or closure.get("comparison_authorized") is not False
        or any(not oracle.same(closure.get(k), 0) for k in ("model_turns", "phase_f_claims", "judge_workloads"))):
        raise ValueError("CLOSURE_AUTHORITY")
    processes = result["processes"]
    if not processes or [p["case"] for p in processes] != list(oracle.CASES[:len(processes)]):
        raise ValueError("PROCESS_SEQUENCE")
    cases, files, streams = [], set(), {}
    for index, process in enumerate(processes):
        case = process["case"]
        if process["started"] is not True or type(process["timed_out"]) is not bool or process["cleanup_succeeded"] is False:
            raise ValueError("PROCESS_UNPROVEN")
        for stream in ("stdout", "stderr"):
            name = case + "." + stream
            data = binding.read_file(root / "streams" / name)
            files.add(name)
            streams[name] = data
            size, total = process[stream + "_size"], process[stream + "_total"]
            if (type(size) is not int or type(total) is not int or size != len(data) or size != min(total, LIMIT) or size < 0
                or binding.digest(data) != process[stream + "_prefix_sha256"]
                or (total == size and binding.digest(data) != process[stream + "_sha256"])):
                raise ValueError("STREAM_IDENTITY")
        complete = (not process["timed_out"] and type(process["exit_code"]) is int and process["exit_code"] == 0
                    and process["stdout_total"] <= LIMIT and process["stderr_total"] <= LIMIT)
        if complete:
            cases.append(oracle.grade(plan["requests"][index], streams[case + ".stdout"], exit_code=0))
        elif index != len(processes) - 1:
            raise ValueError("CONTINUATION_AFTER_PROCESS_FAILURE")
    if {r["path"] for r in binding.inventory(root / "streams")} != files:
        raise ValueError("STREAM_SET")
    observed = {c["case"] for c in cases}
    cases.extend({"case": case, "passed": False, "reason": "NOT_COMPLETED"} for case in oracle.CASES if case not in observed)
    cases.append(oracle.claims(root / "binding/worker"))
    calculated = oracle.aggregate(cases)
    incomplete = len(processes) != len(oracle.CASES) or not complete
    if result["failure"] != ("EXECUTION_INCOMPLETE" if incomplete else None):
        raise ValueError("FAILURE_CLASSIFICATION")
    if result["failure"] is not None:
        calculated["behavior_passed"] = False
    if any(not oracle.same(result[k], value) for k,value in calculated.items()):
        raise ValueError("VERDICT_RECOMPUTATION")
    return plan, result, {c["case"]: c for c in cases}, streams


def matches(variant, result, cases, streams):
    p = result["processes"][0]
    if variant in {"reference", "equivalent"}:
        return result["failure"] is None and result["behavior_passed"] is True and len(result["processes"]) == len(oracle.CASES)
    if result["behavior_passed"] is not False or not cases["claims"]["passed"]:
        return False
    if variant == "constant-success":
        return (result["failure"] is None and cases["profile"]["passed"] is False
            and cases["profile"]["reason"] == "BEHAVIOR_MISMATCH" and all(row["passed"] for key,row in cases.items() if key != "profile"))
    if variant == "forged-json":
        return (cases["profile"]["passed"] is False and
            ((p["exit_code"] == 0 and cases["profile"]["reason"] == "INVALID_OBSERVATION") or
             (p["exit_code"] == 1 and p["stderr_total"] > 0 and result["failure"] == "EXECUTION_INCOMPLETE")))
    if variant == "empty-exit":
        return (result["failure"] is None and len(result["processes"]) == len(oracle.CASES)
            and all(row["exit_code"] == row["stdout_total"] == row["stderr_total"] == 0 for row in result["processes"]))
    if result["failure"] != "EXECUTION_INCOMPLETE" or len(result["processes"]) != 1:
        return False
    if variant == "nonzero-exit":
        return p["exit_code"] == 7 and not p["timed_out"] and p["stdout_total"] == p["stderr_total"] == 0
    if variant == "timeout":
        return p["timed_out"] is True and p["exit_code"] is None and p["cleanup_succeeded"] is True
    if variant == "output-flood":
        return p["stdout_total"] > LIMIT and p["stdout_size"] == LIMIT and streams["profile.stdout"] == b"x" * LIMIT
    if variant == "write-readonly":
        stderr = streams["profile.stderr"]
        return p["exit_code"] == 1 and b"/workspace/f14-forbidden-write" in stderr and any(v in stderr for v in (b"Read-only file system", b"Permission denied"))
    return False


def verify_run(root, plan_sha256, result_sha256):
    plan, result, cases, streams = read_run(root, plan_sha256=plan_sha256, result_sha256=result_sha256)
    return {"variant": plan["variant"], "source_commit": plan["source_commit"], "plan_sha256": plan_sha256, "result_sha256": result_sha256,
        "matched_expectation": bool(matches(plan["variant"], result, cases, streams)), "behavior_passed": result["behavior_passed"],
        "process_count": len(result["processes"]), "input_unchanged": True, "final_environment_verified": True}


def run_approved(root: Path, expected: str, *, authorization_note: str):
    """Explicitly authorized preparation only. Never automatically retry a run."""
    root = binding.checked(root)
    value = manifest(root, expected)
    if not authorization_note.strip() or len(authorization_note) > 2000:
        raise ValueError("EXPLICIT_AUTHORIZATION_NOTE_REQUIRED")
    binding._write_new(root / "matrix-start.json", binding.canonical({"manifest_sha256": expected, "authorization_note": authorization_note}))
    rows, failure = [], None
    for row in value["variants"]:
        variant = row["variant"]
        try:
            print("preflight " + variant, flush=True)
            path = root / variant / "plan.json"
            closure = execution.preflight(path, row["plan_sha256"], rehearse=True)
            binding._write_new(path.parent / "preflight.json", binding.canonical(closure))
            if closure["verdict"] != "GO":
                failure = "PREFLIGHT_NO_GO:" + variant
                break
            print("dispatch " + variant, flush=True)
            result = execution.dispatch(path, approved_plan_sha256=row["plan_sha256"], closure=closure, expected_closure_sha256=closure["receipt_sha256"])
            checked = verify_run(path.parent, row["plan_sha256"], result["result_sha256"])
        except (OSError, ValueError, KeyError, TypeError, binding.DockerJudgeError):
            # Keep the one-shot marker and raw evidence; never disclose exception
            # text or silently retry a partially completed diagnostic.
            failure = "DIAGNOSTIC_OR_VERIFICATION_FAILED:" + variant
            break
        rows.append(checked)
        print(binding.canonical(checked).decode().strip(), flush=True)
        if not checked["matched_expectation"]:
            failure = "UNEXPECTED_RESULT:" + variant
            break
    summary = execution.seal({"version": 1, "manifest_sha256": expected, "rows": rows, "failure": failure,
        "qualification_passed": failure is None and len(rows) == len(VARIANTS), "scope": value["scope"],
        "comparison_authorized": False, "challenge_ready": False, "model_turns": 0, "phase_f_claims": 0}, "summary_sha256")
    binding._write_new(root / "matrix-result.json", binding.canonical(summary))
    return summary


def verify_matrix(root: Path, expected_manifest: str, expected_summary: str):
    root = binding.checked(root)
    value = manifest(root, expected_manifest)
    summary = read_sealed(root / "matrix-result.json", "summary_sha256", expected_summary)
    if (not oracle.same(summary.get("version"), 1) or summary["manifest_sha256"] != expected_manifest or summary["scope"] != value["scope"]
        or summary["comparison_authorized"] is not False or summary["challenge_ready"] is not False
        or any(not oracle.same(summary.get(k), 0) for k in ("model_turns", "phase_f_claims"))):
        raise ValueError("SUMMARY_SCOPE")
    saved = summary["rows"]
    if (not isinstance(saved, list) or len(saved) > len(VARIANTS)
        or [r["variant"] for r in saved] != list(VARIANTS[:len(saved)])):
        raise ValueError("SUMMARY_VARIANT_SEQUENCE")
    start = binding.parse(binding.read_file(root / "matrix-start.json"))
    if start.get("manifest_sha256") != expected_manifest or not isinstance(start.get("authorization_note"), str) or not start["authorization_note"].strip():
        raise ValueError("MATRIX_START_AUTHORITY")
    rows = [verify_run(root / expected["variant"], expected["plan_sha256"], row["result_sha256"])
            for row,expected in zip(summary["rows"], value["variants"], strict=False)]
    if (not oracle.same(rows, summary["rows"]) or any(r["source_commit"] != value["source_commit"] for r in rows)
        or not oracle.same(summary["qualification_passed"], summary["failure"] is None and len(rows) == len(VARIANTS) and all(r["matched_expectation"] for r in rows))):
        raise ValueError("SUMMARY_RECOMPUTATION")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--summary-sha256", required=True)
    args = parser.parse_args()
    print(binding.canonical(verify_matrix(args.root, args.manifest_sha256, args.summary_sha256)).decode())


if __name__ == "__main__":
    main()
