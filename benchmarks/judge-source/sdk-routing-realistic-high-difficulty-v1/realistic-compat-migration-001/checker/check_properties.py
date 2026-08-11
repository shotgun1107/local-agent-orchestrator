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
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


BUNDLE_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = BUNDLE_ROOT / "property-catalog.json"
DAG_PATH = BUNDLE_ROOT / "prerequisite-dag.json"


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
    by_id = {str(item["property_id"]): item for item in definitions}
    results: dict[str, dict[str, object]] = {}

    def evaluate(property_id: str) -> dict[str, object]:
        if property_id in results:
            return results[property_id]
        definition = by_id[property_id]
        prerequisites = [str(value) for value in definition["prerequisite_ids"]]
        if prerequisites != sorted(set(prerequisites)) or any(
            value not in by_id for value in prerequisites
        ):
            raise ValueError("property prerequisite set is invalid")
        prerequisite_results = [evaluate(value) for value in prerequisites]
        if any(value["status"] != "pass" for value in prerequisite_results):
            result = {
                "property_id": property_id,
                "status": "blocked_by_prerequisite",
                "severity": definition["severity"],
                "reason_code": "PREREQUISITE_NOT_PASSED",
                "description": "A prerequisite property did not pass.",
                "evidence_refs": [],
                "prerequisite_ids": prerequisites,
                "checker_sha256": checker_sha256,
            }
        else:
            try:
                outcome = CHECKERS[property_id](workspace, catalog)
            except Exception:
                outcome = {
                    "status": "checker_error",
                    "reason_code": "CHECKER_EXCEPTION",
                    "description": "The property checker raised an exception.",
                    "evidence_refs": [],
                }
            result = {
                "property_id": property_id,
                "status": outcome["status"],
                "severity": definition["severity"],
                "reason_code": outcome["reason_code"],
                "description": outcome["description"],
                "evidence_refs": outcome["evidence_refs"],
                "prerequisite_ids": prerequisites,
                "checker_sha256": checker_sha256,
            }
        results[property_id] = result
        return result

    ordered_results = [evaluate(property_id) for property_id in ordered_ids]
    statuses = {str(item["status"]) for item in ordered_results}
    aggregate_status = (
        "checker_error"
        if "checker_error" in statuses
        else "fail"
        if statuses.intersection({"fail", "blocked_by_prerequisite"})
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


def _run_pytest(root: Path, *nodeids: str, timeout_seconds: float = 240.0) -> bool:
    environment = {
        name: os.environ[name]
        for name in ("SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP")
        if name in os.environ
    }
    python_paths = [
        root / "tools" / "benchmark-runner" / "src",
        root / "stages" / "b1-sequential" / "src",
    ]
    environment.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
            "PYTHONPATH": os.pathsep.join(str(path) for path in python_paths),
            "USERPROFILE": environment.get("TEMP", str(root)),
        }
    )
    try:
        with tempfile.TemporaryDirectory(
            prefix="profile-r-pytest-",
            dir=environment.get("TEMP"),
        ) as base_temp:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "-p",
                    "no:cacheprovider",
                    "--basetemp",
                    base_temp,
                    *nodeids,
                ],
                cwd=root,
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


def _stage_discriminator(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    node = "tools/benchmark-runner/tests/test_routing_s2.py::test_s2_stage_discriminator_rejects_cross_branch_bytes"
    return _outcome(
        root,
        _run_pytest(root, node),
        pass_code="STAGE_DISCRIMINATOR_EXACT",
        fail_code="STAGE_DISCRIMINATOR_FAILED",
        description="S1 and S2 stage bytes are accepted only by their exact Schema branch.",
        evidence=(
            "benchmarks/suites/sdk-routing-v1/stage.schema.json",
            "benchmarks/suites/sdk-routing-v1/stages/s1-baseline.yaml",
            "benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml",
            "tools/benchmark-runner/tests/test_routing_s2.py",
        ),
    )


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
    node = "tools/benchmark-runner/tests/test_routing_s2.py::test_s2_retry_reserve_is_independent_and_never_recycles_early_turns"
    return _outcome(
        root,
        _run_pytest(root, node),
        pass_code="RESERVE_ISOLATED",
        fail_code="RESERVE_REUSED_OR_MISCOUNTED",
        description="B1 retry and resume turns consume only the independent three-turn reserve.",
        evidence=(
            "tools/benchmark-runner/src/benchmark_runner/s2_policy.py",
            "tools/benchmark-runner/tests/test_routing_s2.py",
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
            "routing_s2_nonlive_status",
            "run_next_routing_s2_nonlive_cell",
            "export_routing_s2_nonlive",
            "verify_routing_s2_nonlive_export",
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


def _export_roundtrip(root: Path, _catalog: dict[str, Any]) -> dict[str, object]:
    node = "tools/benchmark-runner/tests/test_routing_s2.py::test_s2_fake_four_cell_plan_judge_property_seal_export"
    return _outcome(
        root,
        _run_pytest(root, node, timeout_seconds=360.0),
        pass_code="EXPORT_ROUNDTRIP_BOUND",
        fail_code="EXPORT_ROUNDTRIP_FAILED",
        description="The model-free create, status, seal, export, and verify path preserves the exact S2 identity.",
        evidence=(
            "tools/benchmark-runner/src/benchmark_runner/routing_suite.py",
            "tools/benchmark-runner/tests/test_routing_s2.py",
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
        generated_ok = _run_pytest(
            root,
            "tools/benchmark-runner/tests/test_routing_suite.py::test_routing_manifests_and_generated_schemas_match_contracts",
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
    expected = _load_json(BUNDLE_ROOT / "operator-contract.json")
    actual_path = root / "profile-r/work/operator-contract.json"
    readme_path = root / "tools/benchmark-runner/README.md"
    try:
        actual = _load_json(actual_path)
        readme = readme_path.read_text(encoding="utf-8")
        passed = actual == expected and all(
            f"`{command['command_id']}`" in readme for command in expected["commands"]
        ) and "<!-- profile-r-operator-contract:start -->" in readme and "<!-- profile-r-operator-contract:end -->" in readme
    except (KeyError, OSError, ValueError):
        passed = False
    return _outcome(
        root,
        passed,
        pass_code="OPERATOR_CONTRACT_ALIGNED",
        fail_code="OPERATOR_CONTRACT_DRIFT",
        description="The structured command, state, failure, and stop relations match the public operator surface.",
        evidence=("profile-r/work/operator-contract.json", "tools/benchmark-runner/README.md"),
    )


CHECKERS = {
    "R-P01-LEGACY-BYTES": _legacy_bytes,
    "R-P02-STAGE-DISCRIMINATOR": _stage_discriminator,
    "R-P03-PLAN-BINDING": _plan_binding,
    "R-P04-RESERVE-ISOLATION": _reserve_isolation,
    "R-P05-LIFECYCLE-REUSE": _lifecycle_reuse,
    "R-P06-EXPORT-ROUNDTRIP": _export_roundtrip,
    "R-P07-CROSS-CHECKOUT-REPRO": _cross_checkout,
    "R-P08-OPERATOR-CONTRACT": _operator_contract,
}


def evaluate_workspace(workspace: Path, *, experiment_id: str, cell_id: str) -> dict[str, object]:
    workspace = workspace.resolve(strict=True)
    catalog = _load_json(CATALOG_PATH)
    dag = _load_json(DAG_PATH)
    before = _workspace_sha256(workspace)
    checker_sha = _sha256(Path(__file__).read_bytes())
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
