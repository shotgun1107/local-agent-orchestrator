"""Trusted JSON-only F14 oracle. Never imports or executes a Worker file.

These are synthetic behavioral contracts, not evidence of actual Windows ACL or
SDK enforcement. The untrusted side reports return values, never case verdicts.
"""
from __future__ import annotations

import base64
import hashlib
import json
import math
from collections import Counter
from pathlib import Path, PurePosixPath, PureWindowsPath

from benchmark_runner.profile_i_semantic_execution import canonical, digest, parse, read_file

CASES = ("profile", "collector", "configuration", "windows", "workspace-acl", "controller-acl", "link", "child-scan", "policy", "state", "bundle")
PROPERTIES = {
    "I-P01": ("profile", "collector"), "I-P02": ("configuration",), "I-P03": ("windows",),
    "I-P04": ("workspace-acl",), "I-P05": ("controller-acl",), "I-P06": ("link",),
    "I-P07": ("child-scan", "policy"), "I-P08": ("state",), "I-P09": ("bundle",), "I-P10": ("claims",),
}
DEPENDENCIES = {key: () for key in PROPERTIES}
DEPENDENCIES.update({"I-P04": ("I-P03",), "I-P05": ("I-P03",), "I-P06": ("I-P04", "I-P05"),
    "I-P07": ("I-P04", "I-P05"), "I-P08": ("I-P05",), "I-P09": tuple(list(PROPERTIES)[:8])})
PUBLIC_TASKS = {"I01": ("I-P10",), "I02": ("I-P01", "I-P02"), "I03": ("I-P03",), "I04": ("I-P04", "I-P05"),
    "I05": ("I-P06",), "I06": ("I-P07",), "I07": ("I-P08",), "I08": ("I-P09",)}


def same(left, right):
    return canonical(left) == canonical(right)


def error(value, *names):
    return type(value) is dict and set(value) == {"error"} and value["error"] in names


def returned(value, expected):
    return same(value, {"value": expected})


def bounded(value, depth=0):
    if depth > 48:
        raise ValueError("JSON_DEPTH")
    if type(value) is dict:
        if len(value) > 256:
            raise ValueError("JSON_WIDTH")
        for key, item in value.items():
            if len(key) > 256:
                raise ValueError("JSON_KEY")
            bounded(item, depth + 1)
    elif type(value) is list:
        if len(value) > 1024:
            raise ValueError("JSON_WIDTH")
        for item in value:
            bounded(item, depth + 1)
    elif type(value) is float and not math.isfinite(value):
        raise ValueError("JSON_NONFINITE")
    elif type(value) not in (str, int, float, bool, type(None)):
        raise ValueError("JSON_TYPE")


def profile_values(value, *, nonce=None):
    expected = dict(derived_profile_passed=True, actual_model_turns=0, turn_start_request_count=0,
        selected_permission_profile_allowed=True, selected_permission_profile_match_count=1,
        requested_permission_profile_id="runtime-boundary-worker", active_permission_profile_id="runtime-boundary-worker",
        thread_started_notification_count=1, thread_start_request_count=1, thread_id_binding_equal=True,
        sandbox_key_present_in_thread_start_request=False, profile_failure_reason_codes=[])
    if any(key not in value or not same(value[key], wanted) for key, wanted in expected.items()):
        return False
    ledger = value["method_ledger"]
    if (not same(ledger["client_request_method_counts"], {"account/read": 1, "initialize": 1, "permissionProfile/list": 1, "thread/start": 1})
        or not same(ledger["client_notification_method_counts"], {"initialized": 1})):
        return False
    decoded = []
    for index, packet in enumerate(value["transcript"]):
        embedded = packet["message"]
        raw = base64.b64decode(embedded["canonical_json_b64"], validate=True)
        message = parse(raw)
        if (not same(packet["sequence"], index) or digest(raw) != embedded["sha256"] or not same(len(raw), embedded["byte_length"])
            or raw != json.dumps(message, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()):
            return False
        decoded.append((packet["direction"], message))
    requests = [m for d,m in decoded if d == "client_to_server" and "method" in m and "id" in m]
    notifications = [m for d,m in decoded if d == "client_to_server" and "method" in m and "id" not in m]
    if (not same(dict(Counter(m["method"] for m in requests)), ledger["client_request_method_counts"])
        or not same(dict(Counter(m["method"] for m in notifications)), ledger["client_notification_method_counts"])):
        return False
    thread_request = next(m for m in requests if m["method"] == "thread/start")
    responses = [m for d,m in decoded if d == "server_to_client" and m.get("id") == thread_request["id"]]
    starts = [m for d,m in decoded if d == "server_to_client" and m.get("method") == "thread/started"]
    if len(responses) != 1 or len(starts) != 1:
        return False
    thread_id = responses[0]["result"]["thread"]["id"]
    if type(thread_id) is not str or starts[0]["params"]["thread"]["id"] != thread_id:
        return False
    expected_hash = digest(thread_id.encode())
    return (value["thread_start_response_thread_id_sha256"] == value["thread_started_notification_thread_id_sha256"] == expected_hash
        and (nonce is None or thread_id == nonce) and "sandbox" not in thread_request["params"]
        and thread_request["params"]["permissions"] == "runtime-boundary-worker")


def check(case, value, nonce):
    if case == "profile":
        return (profile_values(value["good"], nonce=nonce) and returned(value["verified"], True)
            and value["bad"]["thread_id_binding_equal"] is False and same(value["bad"]["actual_model_turns"], 1)
            and same(value["bad"]["turn_start_request_count"], 1) and value["bad"]["derived_profile_passed"] is False
            and value["denied"]["selected_permission_profile_allowed"] is False and value["denied"]["derived_profile_passed"] is False
            and "SELECTED_PROFILE_NOT_ALLOWED" in value["denied"]["profile_failure_reason_codes"]
            and error(value["forged"], "RuntimeBoundaryError"))
    if case == "collector":
        calls = value["calls"]
        return (len(calls) == 2 and calls[0][0] == "permissionProfile/list" and calls[1][0] == "thread/start"
            and set(calls[0][1]) == {"cwd"} and calls[0][1]["cwd"] == calls[1][1]["cwd"]
            and calls[1][1]["permissions"] == "runtime-boundary-worker" and "sandbox" not in calls[1][1]
            and same(value["waited"], ["thread/started", 2.0]) and profile_values(value["evidence"], nonce=nonce))
    if case == "configuration":
        built = value["built"]
        commands = built["commands"]
        overrides = built["configuration"]["config_overrides"]
        fs = next(v.split("=", 1)[1] for v in overrides if v.startswith("permissions.runtime-boundary-worker.filesystem="))
        import tomllib
        access = tomllib.loads("fs=" + fs)["fs"]
        path_type = PureWindowsPath if ":" in built["W"]["resolved_absolute_path"][:3] else PurePosixPath
        root = str(path_type(built["W"]["resolved_absolute_path"]).parent)
        expected_access = {":minimal": "read", ":root": "deny", root: "deny",
                           built["J"]["resolved_absolute_path"]: "deny", built["S"]["resolved_absolute_path"]: "deny"}
        expected_fixed = {'default_permissions="runtime-boundary-worker"', 'permissions.runtime-boundary-worker.extends=":workspace"',
                          'permissions.runtime-boundary-worker.network.enabled=false', 'windows.sandbox="elevated"'}
        return (len(overrides) == 5 and set(overrides) - {"permissions.runtime-boundary-worker.filesystem=" + fs} == expected_fixed
            and same(access, expected_access) and len(commands) == 8 and [c["probe_id"] for c in commands] == [f"P{i:02d}" for i in range(1, 9)]
            and all(c["argv"][1:3] == ["sandbox", "--cd"] and "--permission-profile" in c["argv"] and "--sandbox" not in c["argv"]
                and all(v in c["argv"] for v in overrides) for c in commands)
            and built["fixtures"]["p07_expected_answer_sha256"] in commands[6]["argv"] and returned(value["verified"], None)
            and error(value["weakened"], "ValidationError", "ValueError") and error(value["unbound"], "ValidationError", "ValueError"))
    if case == "windows":
        rows = [item["value"] for item in value]
        return (len(rows) == 5 and same(rows[0][:2], ["elevated", True]) and type(rows[0][2]) is str and len(rows[0][2]) == 64
            and all(len(row) == 3 and row[0] != "elevated" and row[1] is False and row[2] != rows[0][2] for row in rows[1:]))
    if case == "workspace-acl":
        return len(value) == 4 and returned(value[0], True) and all(error(v, "RuntimeBoundaryError") for v in value[1:])
    if case == "controller-acl":
        owner = "S-1-5-21-synthetic-owner"
        return (len(value) == 2 and returned(value[0], {"owner": owner, "control": "PAI", "aces":
            ["(A;OICI;FA;;;SY)", "(A;OICI;FA;;;BA)", f"(A;OICI;FA;;;{owner})"]}) and error(value[1], "RuntimeBoundaryError"))
    if case == "link":
        row = value["observation"]
        return row["link_kind"] == "junction" and row["link_exists_after_create"] is True and row["link_exists_after_cleanup"] is False and value["remaining"] is False
    if case == "child-scan":
        return same(value, [{"value": v} for v in [True, True, False, False, False, False, False]])
    if case == "state":
        return same(value, [{"value": v} for v in [True, False, False]])
    if case == "policy":
        embedded = value["evidence"]["projection"]
        raw = base64.b64decode(embedded["canonical_json_b64"], validate=True)
        projection = parse(raw)
        return (b"synthetic-" + nonce.encode() not in raw and digest(raw) == embedded["sha256"] and same(len(raw), embedded["byte_length"])
            and projection["legacy_sandbox_mode_present"] is False and projection["legacy_sandbox_workspace_write_present"] is False
            and returned(value["verified"], True) and error(value["forged"], "RuntimeBoundaryError")
            and same(value["legacy_codes"], ["LEGACY_SANDBOX_MODE_PRESENT", "LEGACY_SANDBOX_WORKSPACE_WRITE_PRESENT"]))
    if case == "bundle":
        files = value["files"]
        if set(files) != {"manifest.json", "result.json", "files.sha256", "bundle-seal.json"}:
            return False
        manifest, result, seal = [parse(files[name].encode()) for name in ("manifest.json", "result.json", "bundle-seal.json")]
        expected = "".join(f"{digest(files[name].encode())}  {name}\n" for name in ("manifest.json", "result.json"))
        return (files["files.sha256"] == expected and seal["files_manifest_sha256"] == digest(expected.encode())
            and seal["aggregate_sha256"] == digest(expected.encode()) and same(seal["file_count"], 4)
            and result["manifest_sha256"] == digest(files["manifest.json"].encode())
            and result["probe_id"] == manifest["probe_id"] == seal["probe_id"] and seal["source_commit"] == manifest["source_commit"]
            and result["aggregate_status"] == "RUNTIME_BOUNDARY_CANDIDATE" and same(result["actual_model_turns"], 0)
            and result["failure_reason_codes"] == [] and profile_values(result["sdk_profile_provenance"])
            and len(result["probes"]) == 8 and all(p["derived_passed"] is True for p in result["probes"])
            and returned(value["verified"], 3) and error(value["extra"], "RuntimeBoundaryError"))
    raise ValueError("UNKNOWN_CASE")


def grade(request: dict, stdout: bytes, *, exit_code: int | None) -> dict:
    result = {"case": request["case"], "passed": False, "reason": "INVALID_OBSERVATION"}
    try:
        if type(exit_code) is not int or exit_code != 0 or len(stdout) > 1_048_576:
            return result
        value = parse(stdout)
        bounded(value)
        if (type(value) is not dict or set(value) != {"version", "case", "nonce", "observations"}
            or not same({k: value[k] for k in ("version", "case", "nonce")}, request)):
            return result
        result["passed"] = bool(check(request["case"], value["observations"], request["nonce"]))
        result["reason"] = "MATCH" if result["passed"] else "BEHAVIOR_MISMATCH"
    except (ValueError, KeyError, TypeError, IndexError, StopIteration, RecursionError, OverflowError):
        pass
    return result


def claims(workspace: Path) -> dict:
    result = {"case": "claims", "passed": False, "reason": "CLAIM_MISMATCH"}
    try:
        def read(name):
            value = parse(read_file(workspace / name))
            bounded(value)
            return value
        records = read("profile-i/evidence/public-observations.json")["records"]
        by_id = {r["observation_id"]: r["observation_sha256"] for r in records}
        ledger = read("profile-i/work/evidence-ledger.json")["records"]
        stated = read("profile-i/work/incident-claims.json")["claims"]
        tasks = read("profile-i/work/task-contracts.json")["tasks"]
        result["passed"] = (len(records) == len(ledger) == 14 and set(by_id) == {f"O{i:03d}" for i in range(1, 15)}
            and {r["observation_id"] for r in ledger} == set(by_id)
            and all(r["status"] in {"confirmed", "excluded", "unknown"} and r["observation_sha256s"] == [by_id[r["observation_id"]]] for r in ledger)
            and bool(stated) and all(r["status"] in {"confirmed", "excluded", "unknown"} and r["evidence_ids"]
                and r["observation_sha256s"] == sorted(by_id[k] for k in r["evidence_ids"]) for r in stated)
            and set(tasks) == {f"I{i:02d}" for i in range(2, 9)} and all(t["completed"] is True for t in tasks.values()))
        result["reason"] = "MATCH" if result["passed"] else "CLAIM_MISMATCH"
    except (OSError, ValueError, TypeError, KeyError):
        pass
    return result


def aggregate(cases: list[dict], task_id: str | None = None):
    if len(cases) != len(CASES) + 1 or {c["case"] for c in cases} != {*CASES, "claims"}:
        raise ValueError("EXACT_CASE_SET_REQUIRED")
    if any(type(c["passed"]) is not bool for c in cases):
        raise ValueError("EXACT_BOOLEAN_REQUIRED")
    selected = set(PROPERTIES if task_id is None else PUBLIC_TASKS[task_id])
    for _ in PROPERTIES:
        selected.update(dep for key in list(selected) for dep in DEPENDENCIES[key])
    by_case, states, rows = {c["case"]: c for c in cases}, {}, []
    for key, names in PROPERTIES.items():
        if key not in selected:
            continue
        state = "blocked_by_prerequisite" if any(states[dep] != "pass" for dep in DEPENDENCIES[key]) else "pass" if all(by_case[n]["passed"] for n in names) else "fail"
        states[key] = state
        rows.append({"property_id": key, "status": state, "cases": [by_case[n] for n in names]})
    return {"properties": rows, "behavior_passed": all(v == "pass" for v in states.values()),
        "scope": "synthetic_behavior_only", "oracle_isolation": "host_oracle_container_candidate",
        "comparison_authorized": False, "challenge_ready": False, "os_enforcement_verified": False}
