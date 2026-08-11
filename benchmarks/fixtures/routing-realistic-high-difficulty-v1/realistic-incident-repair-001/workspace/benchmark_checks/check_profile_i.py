from __future__ import annotations

import ast
import fnmatch
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OBSERVATIONS_PATH = ROOT / "profile-i/evidence/public-observations.json"
LEDGER_PATH = ROOT / "profile-i/work/evidence-ledger.json"
CLAIMS_PATH = ROOT / "profile-i/work/incident-claims.json"
TASK_CONTRACTS_PATH = ROOT / "profile-i/work/task-contracts.json"
RUNTIME_PATH = ROOT / "tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py"
PROBE_PATH = ROOT / "tools/benchmark-runner/scripts/probe_runtime_boundary.py"
TEST_PATH = ROOT / "tools/benchmark-runner/tests/test_runtime_boundary.py"


TASK_REQUIREMENTS = {
    "I02": {
        "evidence_ids": {"O001", "O010"},
        "minimum_symbols": 2,
        "minimum_tests": 2,
        "write_scope": [
            "profile-i/work/task-contracts.json",
            "tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py",
            "tools/benchmark-runner/tests/test_runtime_boundary.py",
        ],
    },
    "I03": {
        "evidence_ids": {"O002", "O003", "O004", "O005", "O010"},
        "minimum_symbols": 2,
        "minimum_tests": 2,
        "write_scope": [
            "docs/design/sdk-routing-realistic-high-difficulty-implementation-candidate-spec.md",
            "docs/design/sdk-routing-realistic-high-difficulty-runtime-boundary-spec.md",
            "profile-i/work/task-contracts.json",
            "tools/benchmark-runner/scripts/probe_runtime_boundary.py",
            "tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py",
            "tools/benchmark-runner/tests/test_runtime_boundary.py",
        ],
    },
    "I04": {
        "evidence_ids": {"O006", "O007", "O008"},
        "minimum_symbols": 2,
        "minimum_tests": 2,
        "write_scope": [
            "profile-i/work/task-contracts.json",
            "tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py",
            "tools/benchmark-runner/tests/test_runtime_boundary.py",
        ],
    },
    "I05": {
        "evidence_ids": {"O009", "O011", "O012"},
        "minimum_symbols": 2,
        "minimum_tests": 2,
        "write_scope": [
            "profile-i/work/task-contracts.json",
            "tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py",
            "tools/benchmark-runner/tests/test_runtime_boundary.py",
        ],
    },
    "I06": {
        "evidence_ids": {"O013"},
        "minimum_symbols": 2,
        "minimum_tests": 2,
        "write_scope": [
            "profile-i/work/task-contracts.json",
            "tools/benchmark-runner/scripts/probe_runtime_boundary.py",
            "tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py",
            "tools/benchmark-runner/tests/test_runtime_boundary.py",
        ],
    },
    "I07": {
        "evidence_ids": {"O014"},
        "minimum_symbols": 2,
        "minimum_tests": 2,
        "write_scope": [
            "profile-i/work/task-contracts.json",
            "tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py",
            "tools/benchmark-runner/tests/test_runtime_boundary.py",
        ],
    },
    "I08": {
        "evidence_ids": {"O014"},
        "minimum_symbols": 3,
        "minimum_tests": 3,
        "write_scope": [
            "docs/design/sdk-routing-realistic-high-difficulty-implementation-candidate-spec.md",
            "docs/design/sdk-routing-realistic-high-difficulty-runtime-boundary-spec.md",
            "profile-i/work/evidence-ledger.json",
            "profile-i/work/incident-claims.json",
            "profile-i/work/task-contracts.json",
            "tools/benchmark-runner/scripts/probe_runtime_boundary.py",
            "tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py",
            "tools/benchmark-runner/tests/test_runtime_boundary.py",
        ],
    },
}


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path.name}")
    return value


def _canonical_hash(value: object) -> str:
    payload = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )
    return hashlib.sha256(payload).hexdigest()


def _observations() -> dict[str, dict[str, Any]]:
    payload = _load_object(OBSERVATIONS_PATH)
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("public observation records are missing")
    result: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("public observation is not an object")
        record = dict(record)
        stored = record.pop("observation_sha256", None)
        observation_id = record.get("observation_id")
        if not isinstance(observation_id, str) or stored != _canonical_hash(record):
            raise ValueError("public observation identity mismatch")
        if observation_id in result:
            raise ValueError("duplicate public observation")
        result[observation_id] = {**record, "observation_sha256": stored}
    if set(result) != {f"O{number:03d}" for number in range(1, 15)}:
        raise ValueError("public observation set mismatch")
    return result


def _ledger_errors(observations: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    payload = _load_object(LEDGER_PATH)
    records = payload.get("records")
    if not isinstance(records, list) or len(records) != len(observations):
        return ["EVIDENCE_LEDGER_SET_MISMATCH"]
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            errors.append("EVIDENCE_RECORD_INVALID")
            continue
        observation_id = record.get("observation_id")
        if observation_id not in observations or observation_id in seen:
            errors.append("EVIDENCE_ID_INVALID")
            continue
        seen.add(observation_id)
        if record.get("status") not in {"confirmed", "excluded", "unknown"}:
            errors.append("EVIDENCE_STATUS_UNCLASSIFIED")
        if not isinstance(record.get("reason_code"), str) or not record["reason_code"]:
            errors.append("EVIDENCE_REASON_MISSING")
        expected_hash = observations[observation_id]["observation_sha256"]
        if record.get("observation_sha256s") != [expected_hash]:
            errors.append("EVIDENCE_HASH_BINDING_MISMATCH")
        contradictions = record.get("contradiction_ids")
        if not isinstance(contradictions, list) or len(contradictions) != len(
            set(contradictions)
        ) or any(value not in observations for value in contradictions):
            errors.append("EVIDENCE_CONTRADICTION_INVALID")
    if seen != set(observations):
        errors.append("EVIDENCE_LEDGER_SET_MISMATCH")
    return sorted(set(errors))


def _claim_errors(observations: dict[str, dict[str, Any]], *, require_claims: bool) -> list[str]:
    errors: list[str] = []
    claims = _load_object(CLAIMS_PATH).get("claims")
    if not isinstance(claims, list):
        return ["INCIDENT_CLAIMS_INVALID"]
    if require_claims and not claims:
        errors.append("INCIDENT_CLAIMS_EMPTY")
    claim_ids: set[str] = set()
    observation_hashes = {
        key: value["observation_sha256"] for key, value in observations.items()
    }
    for claim in claims:
        if not isinstance(claim, dict):
            errors.append("INCIDENT_CLAIM_INVALID")
            continue
        claim_id = claim.get("claim_id")
        evidence_ids = claim.get("evidence_ids")
        if not isinstance(claim_id, str) or not claim_id or claim_id in claim_ids:
            errors.append("INCIDENT_CLAIM_ID_INVALID")
        else:
            claim_ids.add(claim_id)
        if claim.get("status") not in {"confirmed", "excluded", "unknown"}:
            errors.append("INCIDENT_CLAIM_STATUS_INVALID")
        if not isinstance(claim.get("reason_code"), str) or not claim["reason_code"]:
            errors.append("INCIDENT_CLAIM_REASON_MISSING")
        if not isinstance(evidence_ids, list) or not evidence_ids or any(
            value not in observations for value in evidence_ids
        ):
            errors.append("INCIDENT_CLAIM_EVIDENCE_INVALID")
            continue
        expected_hashes = sorted(observation_hashes[value] for value in evidence_ids)
        if claim.get("observation_sha256s") != expected_hashes:
            errors.append("INCIDENT_CLAIM_HASH_BINDING_MISMATCH")
        contradictions = claim.get("contradiction_ids")
        if not isinstance(contradictions, list) or len(contradictions) != len(
            set(contradictions)
        ) or any(value not in observations for value in contradictions):
            errors.append("INCIDENT_CLAIM_CONTRADICTION_INVALID")
    return sorted(set(errors))


def _definitions(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _path_allowed(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def _task_errors(task_id: str, observations: dict[str, dict[str, Any]]) -> list[str]:
    requirements = TASK_REQUIREMENTS[task_id]
    task_payload = _load_object(TASK_CONTRACTS_PATH).get("tasks")
    if not isinstance(task_payload, dict) or not isinstance(task_payload.get(task_id), dict):
        return ["TASK_DECLARATION_MISSING"]
    record = task_payload[task_id]
    errors: list[str] = []
    if record.get("completed") is not True:
        errors.append("TASK_NOT_DECLARED_COMPLETE")
    evidence_ids = record.get("evidence_ids")
    if not isinstance(evidence_ids, list) or not requirements["evidence_ids"] <= set(
        evidence_ids
    ) or any(value not in observations for value in evidence_ids):
        errors.append("TASK_EVIDENCE_BINDING_INCOMPLETE")
    changed_paths = record.get("changed_paths")
    if not isinstance(changed_paths, list) or not changed_paths or any(
        not isinstance(value, str)
        or not _path_allowed(value, requirements["write_scope"])
        for value in changed_paths
    ):
        errors.append("TASK_CHANGED_PATHS_INVALID")

    implementation_symbols = record.get("implementation_symbols")
    available_symbols = _definitions(RUNTIME_PATH) | _definitions(PROBE_PATH)
    if (
        not isinstance(implementation_symbols, list)
        or len(implementation_symbols) < requirements["minimum_symbols"]
        or len(implementation_symbols) != len(set(implementation_symbols))
        or any(value not in available_symbols for value in implementation_symbols)
    ):
        errors.append("TASK_IMPLEMENTATION_SYMBOLS_INVALID")
    test_names = record.get("test_names")
    available_tests = {name for name in _definitions(TEST_PATH) if name.startswith("test_")}
    if (
        not isinstance(test_names, list)
        or len(test_names) < requirements["minimum_tests"]
        or len(test_names) != len(set(test_names))
        or any(value not in available_tests for value in test_names)
    ):
        errors.append("TASK_TEST_DECLARATIONS_INVALID")
    return sorted(set(errors))


def check(task_id: str) -> list[str]:
    observations = _observations()
    if task_id == "I01":
        return sorted(
            set(_ledger_errors(observations) + _claim_errors(observations, require_claims=True))
        )
    errors = _task_errors(task_id, observations)
    if task_id == "I08":
        errors.extend(_ledger_errors(observations))
        errors.extend(_claim_errors(observations, require_claims=True))
        tasks = _load_object(TASK_CONTRACTS_PATH).get("tasks", {})
        if any(tasks.get(key, {}).get("completed") is not True for key in TASK_REQUIREMENTS):
            errors.append("TASK_SET_INCOMPLETE")
    return sorted(set(errors))


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"I01", *TASK_REQUIREMENTS}:
        print(json.dumps({"passed": False, "reason_codes": ["TASK_ID_INVALID"]}, sort_keys=True))
        return 2
    task_id = sys.argv[1]
    try:
        errors = check(task_id)
    except (OSError, ValueError, SyntaxError, json.JSONDecodeError):
        errors = ["PUBLIC_CONTRACT_INPUT_INVALID"]
    print(
        json.dumps(
            {"passed": not errors, "reason_codes": errors, "task_id": task_id},
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
