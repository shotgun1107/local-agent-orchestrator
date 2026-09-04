"""Deterministic judge-only property checker for Profile R.

This module receives only a frozen Worker tree.  It does not read the historical
reference commit, reference patch, mutation patches, or model/session metadata.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError


BUNDLE_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = BUNDLE_ROOT / "property-catalog.json"
DAG_PATH = BUNDLE_ROOT / "prerequisite-dag.json"
PROTECTED_CHECKER_PATH = Path(__file__).with_name("protected_behavior_checks.py")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _workspace_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(
        (
            path
            for path in root.rglob("*")
            if path.is_file()
            and ".git" not in path.relative_to(root).parts
            and ".pytest_cache" not in path.relative_to(root).parts
            and "__pycache__" not in path.relative_to(root).parts
        ),
        key=lambda path: path.relative_to(root).as_posix().encode("utf-8"),
    )
    for path in files:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        payload = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _evidence(root: Path, *relative_paths: str) -> list[dict[str, str]]:
    values: list[dict[str, str]] = []
    for relative in sorted(set(relative_paths)):
        path = root / relative
        if path.is_file():
            values.append({"path": relative, "sha256": _sha256(path.read_bytes())})
    return values


def _outcome(
    root: Path,
    passed: bool,
    *,
    pass_code: str,
    fail_code: str,
    description: str,
    evidence: tuple[str, ...],
) -> dict[str, object]:
    return {
        "status": "pass" if passed else "fail",
        "reason_code": pass_code if passed else fail_code,
        "description": description,
        "evidence_refs": _evidence(root, *evidence),
    }


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return _sha256(payload)


def _evaluate_checks(
    *,
    catalog: dict[str, Any],
    dag: dict[str, Any],
    workspace: Path,
    experiment_id: str,
    cell_id: str,
    checker_sha256: str,
    workspace_before_sha256: str,
    workspace_after_sha256: str,
) -> dict[str, object]:
    definitions = catalog.get("properties")
    dag_entries = dag.get("properties")
    if not isinstance(definitions, list) or not isinstance(dag_entries, list):
        raise ValueError("property catalog or prerequisite DAG is invalid")
    expected_dag = [
        {
            "property_id": item["property_id"],
            "prerequisite_ids": item["prerequisite_ids"],
        }
        for item in definitions
    ]
    if dag_entries != expected_dag:
        raise ValueError("property catalog and prerequisite DAG differ")
    ordered_ids = [str(item["property_id"]) for item in definitions]
    if ordered_ids != sorted(set(ordered_ids)) or set(CHECKERS) != set(ordered_ids):
        raise ValueError("property catalog order or checker set differs")
    ordered_results: list[dict[str, object]] = []
    for property_id, definition in zip(ordered_ids, definitions, strict=True):
        prerequisites = [str(value) for value in definition["prerequisite_ids"]]
        if prerequisites:
            raise ValueError(
                "Profile R redesign requires independently executed properties"
            )
        try:
            outcome = CHECKERS[property_id](workspace, catalog)
        except Exception as exc:
            outcome = {
                "status": "checker_error",
                "reason_code": "CHECKER_EXCEPTION",
                "description": (
                    "The property checker raised "
                    f"{type(exc).__name__}."
                ),
                "evidence_refs": [],
            }
        ordered_results.append(
            {
                "property_id": property_id,
                "status": outcome["status"],
                "severity": definition["severity"],
                "reason_code": outcome["reason_code"],
                "description": outcome["description"],
                "evidence_refs": outcome["evidence_refs"],
                "prerequisite_ids": [],
                "checker_sha256": checker_sha256,
            }
        )
    statuses = {str(item["status"]) for item in ordered_results}
    aggregate_status = (
        "checker_error"
        if "checker_error" in statuses
        else "fail"
        if "fail" in statuses
        else "pass"
    )
    process = {
        "exit_code": 0,
        "timed_out": False,
        "stdout_size": 0,
        "stdout_sha256": _sha256(b""),
        "stdout_truncated": False,
        "stderr_size": 0,
        "stderr_sha256": _sha256(b""),
        "stderr_truncated": False,
    }
    payload: dict[str, object] = {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "cell_id": cell_id,
        "fixture_id": "realistic-compat-migration-001",
        "catalog_sha256": _canonical_sha256(
            [
                {"property_id": item["property_id"], "severity": item["severity"]}
                for item in definitions
            ]
        ),
        "prerequisite_dag_sha256": _canonical_sha256(expected_dag),
        "checker_sha256": checker_sha256,
        "ordered_property_ids": ordered_ids,
        "checker_run_status": "completed",
        "aggregate_status": aggregate_status,
        "process": process,
        "workspace_before_sha256": workspace_before_sha256,
        "workspace_after_sha256": workspace_after_sha256,
        "workspace_mutated": workspace_before_sha256 != workspace_after_sha256,
        "properties": ordered_results,
    }
    payload["envelope_sha256"] = _canonical_sha256(payload)
    return payload


def _checker_identity_sha256() -> str:
    digest = hashlib.sha256()
    for path in (Path(__file__).resolve(), PROTECTED_CHECKER_PATH.resolve()):
        payload = path.read_bytes()
        relative = path.relative_to(BUNDLE_ROOT).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _run_protected_check(
    root: Path,
    property_id: str,
    *,
    timeout_seconds: float = 240.0,
) -> bool:
    environment = {
        name: os.environ[name]
        for name in ("SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP")
        if name in os.environ
    }
    environment.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
            "USERPROFILE": environment.get("TEMP", str(root)),
        }
    )
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-P",
                str(PROTECTED_CHECKER_PATH.resolve()),
                "--workspace",
                str(root.resolve()),
                "--property-id",
                property_id,
            ],
            cwd=BUNDLE_ROOT,
            env=environment,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and len(result.stdout) <= 1_000_000 and len(result.stderr) <= 1_000_000


def _legacy_bytes(root: Path, catalog: dict[str, Any]) -> dict[str, object]:
    expected = catalog["legacy_byte_contract"]
    passed = isinstance(expected, dict) and all(
        (root / relative).is_file()
        and _sha256((root / relative).read_bytes()) == digest
        for relative, digest in expected.items()
    )
    return _outcome(
        root,
        passed,
        pass_code="LEGACY_BYTES_PRESERVED",
        fail_code="LEGACY_BYTES_DRIFTED",
        description="The frozen legacy Plan, Measurement, and export Schema bytes are preserved.",
        evidence=tuple(expected),
    )


def _source_boundary(root: Path, catalog: dict[str, Any]) -> dict[str, object]:
    legacy = _legacy_bytes(root, catalog)
    passed = legacy["status"] == "pass"
    try:
        import yaml

        run = yaml.safe_load((root / "benchmark-run.yaml").read_text(encoding="utf-8"))
        surface = _load_json(root / "profile-r/requirements/change-surface.json")
        expected = {
            "schema_version": 2,
            "tasks": [
                {
                    "task_id": task["key"],
                    "write_paths": task["write_scope"],
                }
                for task in run["tasks"]
            ],
        }
        passed = passed and surface == expected
    except (KeyError, OSError, TypeError, ValueError):
        passed = False
    return _outcome(
        root,
        passed,
        pass_code="SOURCE_BOUNDARY_EXACT",
        fail_code="SOURCE_BOUNDARY_DRIFTED",
        description="The legacy bytes and projected R01-R13 source boundary are exact.",
        evidence=(
            "benchmark-run.yaml",
            "profile-r/requirements/change-surface.json",
            *tuple(catalog["legacy_byte_contract"]),
        ),
    )


def _stage_discriminator(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    return _outcome(
        root,
        _run_protected_check(root, "R-P02-DISCRIMINATOR"),
        pass_code="STAGE_DISCRIMINATOR_EXACT",
        fail_code="STAGE_DISCRIMINATOR_FAILED",
        description="S1 and S2 stage bytes are accepted only by their exact Schema branch.",
        evidence=(
            "benchmarks/suites/sdk-routing-v1/stage.schema.json",
            "benchmarks/suites/sdk-routing-v1/stages/s1-baseline.yaml",
            "benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml",
            "tools/benchmark-runner/src/benchmark_runner/routing_suite.py",
        ),
    )


def _run_hidden_python(root: Path, cwd: Path, source: str) -> bool:
    environment = {
        name: os.environ[name]
        for name in ("SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP")
        if name in os.environ
    }
    environment.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
            "PROFILE_R_WORKSPACE": str(root.resolve()),
        }
    )
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", source],
        cwd=cwd,
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        check=False,
    )
    return result.returncode == 0


def _config_fixture(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    fixture = root / "benchmarks/fixtures/routing-v1/intermediate/three-stage-config-migration"
    source = r'''
import contextlib, io, json, sys
from pathlib import Path
sys.path.insert(0, ".")
from cli.config_cli import main
from runtime.parser import parse_config
from runtime.serializer import serialize_config
current_text = Path("inputs/current.json").read_text(encoding="utf-8")
current = json.loads(current_text)
serialized = serialize_config(parse_config(current_text))
assert parse_config(serialized) == current
stdout, stderr = io.StringIO(), io.StringIO()
with contextlib.redirect_stderr(stderr):
    code = main(["inputs/current.json"], stdout=stdout)
expected = json.dumps({"config": current, "ok": True}, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
assert code == 0 and stdout.getvalue() == expected
assert stderr.getvalue() == ""
'''
    passed = fixture.is_dir() and _run_hidden_python(root, fixture, source)
    return _outcome(
        root,
        passed,
        pass_code="CONFIG_FIXTURE_SEMANTICS_VALID",
        fail_code="CONFIG_FIXTURE_SEMANTICS_FAILED",
        description="The configuration fixture parses, serializes, and executes its CLI contract behaviorally.",
        evidence=(
            "benchmarks/fixtures/routing-v1/intermediate/three-stage-config-migration/benchmark-run.yaml",
            "benchmarks/fixtures/routing-v1/intermediate/three-stage-config-migration/runtime/parser.py",
            "benchmarks/fixtures/routing-v1/intermediate/three-stage-config-migration/runtime/serializer.py",
        ),
    )


def _incident_fixture(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    base = root / "benchmarks/fixtures/routing-v1/intermediate/three-stage-incident-analysis"
    passed = False
    try:
        evidence = _load_json(base / "analysis/evidence-ledger.json")["evidence"]
        uncertainties = _load_json(base / "analysis/uncertainties.json")["uncertainties"]
        events = _load_json(base / "timeline/events.json")["events"]
        hypotheses = _load_json(base / "timeline/hypotheses.json")["hypotheses"]
        claims = _load_json(base / "report/claims.json")["claims"]
        actions = _load_json(base / "report/action-plan.json")["actions"]
        evidence_ids = {item["evidence_id"] for item in evidence}
        uncertainty_ids = {item["uncertainty_id"] for item in uncertainties}
        all_refs_valid = all(
            set(item.get("evidence_ids", [])) <= evidence_ids
            and set(item.get("uncertainty_ids", [])) <= uncertainty_ids
            for item in [*events, *hypotheses]
        ) and all(
            bool(item.get("evidence_ids"))
            and set(item["evidence_ids"]) <= evidence_ids
            and "evidence_id" not in item
            for item in claims
        )
        report = (base / "report/final-report.md").read_text(encoding="utf-8")
        headings = [line[3:] for line in report.splitlines() if line.startswith("## ")]
        passed = (
            bool(evidence and uncertainties and events and hypotheses and claims and actions)
            and all_refs_valid
            and headings == ["확인된 사실", "상충", "미확인", "권고"]
        )
    except (KeyError, OSError, TypeError, ValueError):
        passed = False
    return _outcome(
        root,
        passed,
        pass_code="INCIDENT_FIXTURE_SEMANTICS_VALID",
        fail_code="INCIDENT_FIXTURE_SEMANTICS_FAILED",
        description="The incident fixture preserves evidence, uncertainty, timeline, claim, action, and report relationships.",
        evidence=(
            "benchmarks/fixtures/routing-v1/intermediate/three-stage-incident-analysis/analysis/evidence-ledger.json",
            "benchmarks/fixtures/routing-v1/intermediate/three-stage-incident-analysis/report/final-report.md",
        ),
    )


def _manifest_binding(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    path = root / "benchmarks/manifests/sdk-routing-s2-intermediate.yaml"
    passed = False
    try:
        import yaml

        value = yaml.safe_load(path.read_text(encoding="utf-8"))
        fixtures = value["fixtures"]
        passed = (
            [item["id"] for item in fixtures]
            == ["three-stage-config-migration", "three-stage-incident-analysis"]
            and all(re.fullmatch(r"[0-9a-f]{40}", item["commit"]) for item in fixtures)
            and all(re.fullmatch(r"[0-9a-f]{40}", item["git_tree"]) for item in fixtures)
            and value["budgets"]["max_actual_live_model_turns"] == 15
        )
        if passed:
            passed = all(
                _git_tree_oid(root / str(item["path"])) == item["git_tree"]
                for item in fixtures
            )
    except (KeyError, OSError, TypeError, ValueError):
        passed = False
    return _outcome(
        root,
        passed,
        pass_code="MANIFEST_IDENTITIES_BOUND",
        fail_code="MANIFEST_IDENTITIES_DRIFTED",
        description="The S2 fixture manifest binds both exact fixture identities and budgets.",
        evidence=("benchmarks/manifests/sdk-routing-s2-intermediate.yaml",),
    )


def _git_object_oid(kind: str, payload: bytes) -> str:
    header = f"{kind} {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload, usedforsecurity=False).hexdigest()


def _git_tree_oid(root: Path) -> str:
    records: list[tuple[bytes, bytes]] = []
    for path in root.iterdir():
        name = path.name.encode("utf-8")
        if path.is_dir():
            oid = _git_tree_oid(path)
            sort_key = name + b"/"
            mode = b"40000"
        elif path.is_file():
            oid = _git_object_oid("blob", path.read_bytes())
            sort_key = name
            mode = b"100644"
        else:
            raise ValueError("fixture tree contains a non-file entry")
        records.append((sort_key, mode + b" " + name + b"\0" + bytes.fromhex(oid)))
    payload = b"".join(record for _key, record in sorted(records))
    return _git_object_oid("tree", payload)


def _plan_binding(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    stage_path = root / "benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml"
    source_path = root / "tools/benchmark-runner/src/benchmark_runner/routing_suite.py"
    expected_order = [
        "cell_s2_a_1_c2",
        "cell_s2_a_1_b1",
        "cell_s2_b_1_b1",
        "cell_s2_b_1_c2",
    ]
    passed = False
    try:
        import yaml

        stage = yaml.safe_load(stage_path.read_text(encoding="utf-8"))
        source = source_path.read_text(encoding="utf-8")
        passed = (
            [item["cell_id"] for item in stage["cells"]] == expected_order
            and stage["base_live_model_turns"] == 12
            and stage["b1_retry_resume_reserve_turns"] == 3
            and stage["max_actual_live_model_turns"] == 15
            and "def build_routing_s2_plan(" in source
            and "source_manifest" in source
            and "stage_id" in source
        )
    except (KeyError, OSError, TypeError, ValueError):
        passed = False
    return _outcome(
        root,
        passed,
        pass_code="PLAN_IDENTITY_BOUND",
        fail_code="PLAN_IDENTITY_OR_ORDER_DRIFTED",
        description="The S2 Plan binds the declared source, stage, cell order, and turn budgets.",
        evidence=(
            "benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml",
            "tools/benchmark-runner/src/benchmark_runner/routing_suite.py",
        ),
    )


def _reserve_isolation(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    return _outcome(
        root,
        _run_protected_check(root, "R-P07-ROUTING-POLICY"),
        pass_code="RESERVE_ISOLATED",
        fail_code="RESERVE_REUSED_OR_MISCOUNTED",
        description="B1 retry and resume turns consume only the independent three-turn reserve.",
        evidence=(
            "tools/benchmark-runner/src/benchmark_runner/s2_policy.py",
        ),
    )


def _top_level_functions(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _lifecycle_reuse(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    duplicate_paths = (
        "tools/benchmark-runner/src/benchmark_runner/routing_s2_live.py",
        "tools/benchmark-runner/src/benchmark_runner/s2_controller.py",
        "tools/benchmark-runner/src/benchmark_runner/s2_judge.py",
    )
    suite = root / "tools/benchmark-runner/src/benchmark_runner/routing_suite.py"
    live = root / "tools/benchmark-runner/src/benchmark_runner/routing_live.py"
    try:
        suite_functions = _top_level_functions(suite)
        live_functions = _top_level_functions(live)
        passed = not any((root / path).exists() for path in duplicate_paths) and {
            "initialize_routing_s2_experiment",
            "run_next_routing_s2_nonlive_cell",
        } <= suite_functions and {
            "create_routing_s1_live_candidate",
            "routing_s1_live_status",
            "run_next_routing_s1_live_cell",
        } <= live_functions
    except (OSError, SyntaxError):
        passed = False
    return _outcome(
        root,
        passed,
        pass_code="LIFECYCLE_REUSED",
        fail_code="DUPLICATE_OR_MISSING_LIFECYCLE",
        description="S2 extends the shared routing lifecycle without a parallel Controller or Judge.",
        evidence=(
            "tools/benchmark-runner/src/benchmark_runner/routing_live.py",
            "tools/benchmark-runner/src/benchmark_runner/routing_suite.py",
        ),
    )


def _status_posthoc(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    suite = root / "tools/benchmark-runner/src/benchmark_runner/routing_suite.py"
    posthoc = root / "tools/benchmark-runner/src/benchmark_runner/s2_posthoc.py"
    passed = False
    try:
        suite_functions = _top_level_functions(suite)
        posthoc_functions = _top_level_functions(posthoc)
        passed = (
            "routing_s2_nonlive_status" in suite_functions
            and "evaluate_posthoc" in posthoc_functions
            and _run_hidden_python(
                root,
                root,
                r'''
import os, sys
from pathlib import Path
workspace = Path(os.environ["PROFILE_R_WORKSPACE"])
sys.path.insert(0, str(workspace / "tools/benchmark-runner/src"))
from benchmark_runner.s2_posthoc import PROPERTY_IDS
assert dict(PROPERTY_IDS) == {
    "three-stage-config-migration": ("CFG-P1", "CFG-P2", "CFG-P3", "CFG-P4", "CFG-P5"),
    "three-stage-incident-analysis": ("INC-P1", "INC-P2", "INC-P3", "INC-P4", "INC-P5"),
}
''',
            )
        )
    except (OSError, SyntaxError):
        passed = False
    return _outcome(
        root,
        passed,
        pass_code="STATUS_POSTHOC_ALIGNED",
        fail_code="STATUS_POSTHOC_FAILED",
        description="S2 status and deterministic post-hoc evaluation remain on the shared implementation path.",
        evidence=(
            "tools/benchmark-runner/src/benchmark_runner/routing_suite.py",
            "tools/benchmark-runner/src/benchmark_runner/s2_posthoc.py",
        ),
    )


def _export_roundtrip(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    return _outcome(
        root,
        _run_protected_check(
            root,
            "R-P10-EXPORT-VERIFY",
            timeout_seconds=360.0,
        ),
        pass_code="EXPORT_ROUNDTRIP_BOUND",
        fail_code="EXPORT_ROUNDTRIP_FAILED",
        description="The model-free create, status, seal, export, and verify path preserves the exact S2 identity.",
        evidence=(
            "tools/benchmark-runner/src/benchmark_runner/routing_suite.py",
            "benchmarks/suites/sdk-routing-v1/suite.yaml",
            "benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml",
        ),
    )


def _cross_checkout(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    attributes = root / ".gitattributes"
    checked = (
        "benchmarks/suites/sdk-routing-v1/stage.schema.json",
        "benchmarks/suites/sdk-routing-v1/suite.schema.json",
        "benchmarks/suites/sdk-routing-v1/stages/s1-baseline.yaml",
        "benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml",
    )
    try:
        policy = attributes.read_text(encoding="utf-8")
        bytes_ok = all(b"\r\n" not in (root / path).read_bytes() for path in checked)
        generated_ok = _run_protected_check(
            root,
            "R-P07-CROSS-CHECKOUT-REPRO",
        )
        passed = "* text=auto eol=lf" in policy and bytes_ok and generated_ok
    except OSError:
        passed = False
    return _outcome(
        root,
        passed,
        pass_code="CROSS_CHECKOUT_REPRODUCIBLE",
        fail_code="CROSS_CHECKOUT_DRIFT",
        description="Generated routing bytes remain reproducible under the frozen LF checkout policy.",
        evidence=(".gitattributes", *checked),
    )


def _operator_contract(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    actual_path = root / "profile-r/work/operator-contract.json"
    schema_path = root / "profile-r/requirements/operator-contract-schema.json"
    readme_path = root / "tools/benchmark-runner/README.md"
    expected_ids = ("create", "status", "run-next", "export", "verify")
    expected_symbols = {
        "create": "routing_suite:initialize_routing_s2_experiment",
        "status": "routing_suite:routing_s2_nonlive_status",
        "run-next": "routing_suite:run_next_routing_s2_nonlive_cell",
        "export": "routing_suite:export_routing_s2_nonlive",
        "verify": "routing_suite:verify_routing_s2_nonlive_export",
    }
    expected_stops = {
        "create": True,
        "status": False,
        "run-next": True,
        "export": True,
        "verify": True,
    }

    def public_schema_exists(value: object) -> bool:
        if not isinstance(value, str):
            return False
        relative = PurePosixPath(value)
        return (
            not relative.is_absolute()
            and all(part not in {"", ".", ".."} for part in relative.parts)
            and root.joinpath(*relative.parts).is_file()
        )

    try:
        actual = _load_json(actual_path)
        schema = _load_json(schema_path)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(actual)
        commands = actual["commands"]
        command_ids = tuple(command["command_id"] for command in commands)
        readme = readme_path.read_text(encoding="utf-8")
        passed = (
            set(actual) == {"schema_version", "commands"}
            and actual["schema_version"] == 1
            and command_ids == expected_ids
            and all(
                command["implementation_symbol"]
                == expected_symbols[command["command_id"]]
                and command["stop_before_next_dispatch"]
                is expected_stops[command["command_id"]]
                and bool(command["argv"])
                and bool(command["success_exit_codes"])
                and bool(command["failure_map"])
                and public_schema_exists(command["public_schema"])
                for command in commands
            )
            and all(f"`{command_id}`" in readme for command_id in expected_ids)
            and "<!-- profile-r-operator-contract:start -->" in readme
            and "<!-- profile-r-operator-contract:end -->" in readme
        )
    except (KeyError, OSError, SchemaError, TypeError, ValidationError, ValueError):
        passed = False
    return _outcome(
        root,
        passed,
        pass_code="OPERATOR_CONTRACT_ALIGNED",
        fail_code="OPERATOR_CONTRACT_DRIFT",
        description="The structured command, state, failure, and stop relations match the public operator surface.",
        evidence=("profile-r/work/operator-contract.json", "tools/benchmark-runner/README.md"),
    )


def _s2_e2e(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    test_path = root / "tools/benchmark-runner/tests/test_routing_s2.py"
    passed = False
    try:
        source = test_path.read_text(encoding="utf-8")
        passed = all(
            value in source
            for value in (
                "cell_s2_a_1_c2",
                "cell_s2_a_1_b1",
                "cell_s2_b_1_b1",
                "cell_s2_b_1_c2",
                "cell_state",
                "check_success",
                "sealed_measurement_sha256",
                "actual_model_turns",
            )
        ) and _run_protected_check(
            root,
            "R-P11-S2-E2E",
            timeout_seconds=360.0,
        )
    except OSError:
        passed = False
    return _outcome(
        root,
        passed,
        pass_code="S2_E2E_EXACT",
        fail_code="S2_E2E_FAILED",
        description="The exact four S2 Cells require explicit effects, successful Checks, Measurements, and seals.",
        evidence=("tools/benchmark-runner/tests/test_routing_s2.py",),
    )


def _s1_portability(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    return _outcome(
        root,
        _run_protected_check(
            root,
            "R-P12-S1-PORTABILITY",
            timeout_seconds=360.0,
        ),
        pass_code="S1_SELF_CONTAINED",
        fail_code="S1_PORTABILITY_FAILED",
        description="Legacy S1 regressions rebuild deterministic local Git identities without historical objects.",
        evidence=("tools/benchmark-runner/tests/test_routing_suite.py",),
    )


CHECKERS = {
    "R-P01-SOURCE-BOUNDARY": _source_boundary,
    "R-P02-DISCRIMINATOR": _stage_discriminator,
    "R-P03-CONFIG-FIXTURE": _config_fixture,
    "R-P04-INCIDENT-FIXTURE": _incident_fixture,
    "R-P05-MANIFEST-BINDING": _manifest_binding,
    "R-P06-PLAN-BINDING": _plan_binding,
    "R-P07-ROUTING-POLICY": _reserve_isolation,
    "R-P08-LIFECYCLE-REUSE": _lifecycle_reuse,
    "R-P09-STATUS-POSTHOC": _status_posthoc,
    "R-P10-EXPORT-VERIFY": _export_roundtrip,
    "R-P11-S2-E2E": _s2_e2e,
    "R-P12-S1-PORTABILITY": _s1_portability,
    "R-P13-OPERATOR-SEMANTICS": _operator_contract,
}


def evaluate_workspace(workspace: Path, *, experiment_id: str, cell_id: str) -> dict[str, object]:
    workspace = workspace.resolve(strict=True)
    catalog = _load_json(CATALOG_PATH)
    dag = _load_json(DAG_PATH)
    before = _workspace_sha256(workspace)
    checker_sha = _checker_identity_sha256()
    return _evaluate_checks(
        catalog=catalog,
        dag=dag,
        workspace=workspace,
        experiment_id=experiment_id,
        cell_id=cell_id,
        checker_sha256=checker_sha,
        workspace_before_sha256=before,
        workspace_after_sha256=_workspace_sha256(workspace),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--experiment-id", default="phase-d-profile-r")
    parser.add_argument("--cell-id", default="reference")
    args = parser.parse_args(argv)
    result = evaluate_workspace(args.workspace, experiment_id=args.experiment_id, cell_id=args.cell_id)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["aggregate_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
