from __future__ import annotations

import ast
import importlib
import inspect
import json
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "tools" / "benchmark-runner" / "src"
REQUIREMENTS = ROOT / "profile-r" / "requirements"
WORK = ROOT / "profile-r" / "work"
WORKER_FEEDBACK_PREFIX = "WORKER_FEEDBACK:"
WORKER_FEEDBACK_MAX_BYTES = 12_288
CHECK_FAILURE_CLASS_PREFIX = "CHECK_FAILURE_CLASS:"


class PublicContractError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        public_feedback: list[str] | None = None,
        failure_classification: str = "PRODUCT_ASSERTION",
    ) -> None:
        super().__init__(message)
        self.public_feedback = public_feedback
        self.failure_classification = failure_classification


def _decode_utf8_prefix(data: bytes, limit: int) -> str:
    chunk = data[:limit]
    while chunk:
        try:
            return chunk.decode("utf-8")
        except UnicodeDecodeError:
            chunk = chunk[:-1]
    return ""


def _decode_utf8_suffix(data: bytes, limit: int) -> str:
    chunk = data[-limit:]
    while chunk:
        try:
            return chunk.decode("utf-8")
        except UnicodeDecodeError:
            chunk = chunk[1:]
    return ""


def _bounded_public_feedback(lines: list[str]) -> list[str]:
    text = "\n".join(line.rstrip() for line in lines).strip()
    encoded = text.encode("utf-8")
    if len(encoded) <= WORKER_FEEDBACK_MAX_BYTES:
        return text.splitlines()
    marker = "\n...[public pytest diagnostic truncated by byte limit]...\n"
    marker_bytes = marker.encode("utf-8")
    remaining = WORKER_FEEDBACK_MAX_BYTES - len(marker_bytes)
    head_limit = remaining // 2
    tail_limit = remaining - head_limit
    bounded = (
        _decode_utf8_prefix(encoded, head_limit)
        + marker
        + _decode_utf8_suffix(encoded, tail_limit)
    )
    return bounded.splitlines()


def _public_pytest_failure_feedback(
    result: subprocess.CompletedProcess[str],
) -> list[str]:
    combined = "\n".join((result.stdout or "", result.stderr or ""))
    hint: str | None = None
    if "Filename too long" in combined:
        hint = (
            "the isolated S2 Git repository exceeded the Windows path limit. Preserve "
            "core.longpaths=true for the temporary repository and the shared frozen-object "
            "Git reads; shortening or skipping the regression is not an acceptable fix."
        )
    elif (
        "test_s2_fake_four_cell_plan_judge_property_seal_export" in combined
        and "b1 preflight failed: B1 run validate failed" in combined
    ):
        hint = (
            "the prepared S2 B1 fixture still uses legacy project.yaml fields purpose, "
            "requirements, and task_order. Before B1 preflight, replace them with the "
            "current public ProjectConfig fields core_compat, repository_root, "
            "default_capability_profile, and default_policy while preserving "
            "schema_version and project_id."
        )
    elif (
        "test_s2_fake_four_cell_plan_judge_property_seal_export" in combined
        and "FrozenManifest" in combined
        and "extra_forbidden" in combined
    ):
        hint = (
            "test_s2_fake_four_cell_plan_judge_property_seal_export built the strict "
            "FrozenManifest/FrozenFixtureSpec input with S2-only extra fields. Convert "
            "only the fields declared by those public models; stage_id, purpose, "
            "initial_cell_order, and fixture profile are not valid frozen-manifest fields."
        )
    elif (
        "test_s2_fake_four_cell_plan_judge_property_seal_export" in combined
        and (
            "assert all(result.check_success" in combined
            or "test_cli_success_json" in combined
            or "JSONDecodeError" in combined
        )
    ):
        hint = (
            "the Fake four-Cell regression claimed completion without materializing every "
            "Task output. Preserve the existing GOLDEN_ROOT/_golden_turns flow and give each "
            "C2 FakeTurnScript and B1 fake turn explicit write_file effects for the exact "
            "golden bytes; result envelopes alone do not change the workspace."
        )
    workspace_variants = {
        str(ROOT),
        str(ROOT).replace("\\", "/"),
    }
    diagnostic = combined.replace("\x00", "\\0")
    for workspace in sorted(workspace_variants, key=len, reverse=True):
        diagnostic = diagnostic.replace(workspace, "<WORKSPACE>")
    lines = [
        f"public S2 pytest exited {result.returncode}",
        "rerun: python -m pytest -q tools/benchmark-runner/tests/test_routing_s2.py",
    ]
    if hint:
        lines.append(f"controller hint: {hint}")
    if diagnostic.strip():
        lines.extend(["public pytest diagnostic:", *diagnostic.splitlines()])
    else:
        lines.append("public pytest produced no decodable stdout or stderr")
    return _bounded_public_feedback(lines)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PublicContractError(f"invalid public JSON: {path.relative_to(ROOT)}") from exc
    if not isinstance(value, dict):
        raise PublicContractError(f"public JSON must be an object: {path.relative_to(ROOT)}")
    return value


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise PublicContractError(f"invalid public YAML: {path.relative_to(ROOT)}") from exc
    if not isinstance(value, dict):
        raise PublicContractError(f"public YAML must be an object: {path.relative_to(ROOT)}")
    return value


def _relative(value: str) -> str:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or "\\" in value or any(part in {"", ".", ".."} for part in path.parts):
        raise PublicContractError("all public paths must be normalized relative paths")
    return value


def _exact_keys(value: dict[str, Any], keys: set[str], label: str) -> None:
    if set(value) != keys:
        raise PublicContractError(f"{label} has the wrong public field set")


def _require_paths(paths: list[str]) -> None:
    missing = [path for path in paths if not (ROOT / path).is_file()]
    if missing:
        raise PublicContractError(f"required public files are missing: {', '.join(missing)}")


def _task_surface() -> list[dict[str, Any]]:
    value = _load_json(REQUIREMENTS / "change-surface.json")
    _exact_keys(value, {"schema_version", "tasks"}, "change surface")
    if value["schema_version"] != 1 or not isinstance(value["tasks"], list):
        raise PublicContractError("change surface version or tasks are invalid")
    return value["tasks"]


def check_r01() -> None:
    tasks = _task_surface()
    expected_paths: list[tuple[str, str]] = []
    for task in tasks:
        _exact_keys(task, {"task_id", "purpose", "write_paths"}, "change surface task")
        for raw_path in task["write_paths"]:
            expected_paths.append((_relative(raw_path), task["task_id"]))
    expected_paths.sort(key=lambda item: item[0].encode("utf-8"))

    inventory = _load_json(WORK / "source-inventory.json")
    _exact_keys(inventory, {"schema_version", "entries"}, "source inventory")
    entries = inventory["entries"]
    if inventory["schema_version"] != 1 or not isinstance(entries, list):
        raise PublicContractError("source inventory is not version 1")
    actual: list[tuple[str, str]] = []
    for entry in entries:
        _exact_keys(
            entry,
            {"path", "kind", "migration_action", "owner_task"},
            "source inventory entry",
        )
        path = _relative(entry["path"])
        if entry["kind"] != ("tree" if path.endswith("/**") else "file"):
            raise PublicContractError("source inventory path kind is inconsistent")
        if entry["migration_action"] not in {"add", "extend", "preserve"}:
            raise PublicContractError("source inventory migration action is invalid")
        actual.append((path, entry["owner_task"]))
    if actual != expected_paths:
        raise PublicContractError("source inventory does not exactly cover the public change surface")

    ledger = _load_json(WORK / "migration-ledger.json")
    _exact_keys(ledger, {"schema_version", "invariants"}, "migration ledger")
    invariants = ledger["invariants"]
    expected = {
        "legacy-stage-bytes": "preserve",
        "stage-discriminator": "extend",
        "plan-source-binding": "extend",
        "reserve-isolation": "extend",
        "lifecycle-reuse": "preserve",
        "export-roundtrip": "extend",
        "cross-checkout-repro": "preserve",
        "operator-contract": "extend",
    }
    if ledger["schema_version"] != 1 or not isinstance(invariants, list):
        raise PublicContractError("migration ledger is not version 1")
    observed: dict[str, str] = {}
    for item in invariants:
        _exact_keys(item, {"id", "status", "evidence_paths"}, "migration invariant")
        if not isinstance(item["evidence_paths"], list) or not item["evidence_paths"]:
            raise PublicContractError("each migration invariant needs public evidence paths")
        for path in item["evidence_paths"]:
            _relative(path)
        observed[item["id"]] = item["status"]
    if observed != expected:
        raise PublicContractError("migration ledger does not contain the exact public invariants")


def _import_runner_module(name: str):
    source = str(SOURCE_ROOT)
    if source not in sys.path:
        sys.path.insert(0, source)
    try:
        return importlib.import_module(f"benchmark_runner.{name}")
    except Exception as exc:
        raise PublicContractError(f"public module import failed: {name}") from exc


def check_r02() -> None:
    stage_schema = _load_json(ROOT / "benchmarks/suites/sdk-routing-v1/stage.schema.json")
    suite_schema = _load_json(ROOT / "benchmarks/suites/sdk-routing-v1/suite.schema.json")
    if "$defs" not in stage_schema or "$defs" not in suite_schema:
        raise PublicContractError("routing schemas must expose generated strict definitions")
    suite = _load_yaml(ROOT / "benchmarks/suites/sdk-routing-v1/suite.yaml")
    stages = suite.get("stages")
    if suite.get("design_revision") != 3 or suite.get("live_turn_ceiling_including_pilot") != 52:
        raise PublicContractError("suite additive revision or ceiling is wrong")
    if [item.get("stage_id") for item in stages or []] != ["s1-baseline", "s2-intermediate"]:
        raise PublicContractError("suite stage order is wrong")

    s1_path = ROOT / "benchmarks/suites/sdk-routing-v1/stages/s1-baseline.yaml"
    s2_path = ROOT / "benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml"
    s1_value = _load_yaml(s1_path)
    s2_value = _load_yaml(s2_path)
    if s2_value.get("stage_id") != "s2-intermediate" or s2_value.get("purpose") != "profile_routing":
        raise PublicContractError("S2 discriminator constants are wrong")
    if s2_value.get("base_live_model_turns") != 12 or s2_value.get("b1_retry_resume_reserve_turns") != 3 or s2_value.get("max_actual_live_model_turns") != 15:
        raise PublicContractError("S2 public budget constants are wrong")

    module = _import_runner_module("routing_suite")
    for name in ("RoutingS1StageManifest", "RoutingS2StageManifest", "RoutingStageManifest", "load_routing_stage"):
        if not hasattr(module, name):
            raise PublicContractError(f"stage-neutral parser API is missing: {name}")
    s1 = module.load_routing_stage(s1_path)
    s2 = module.load_routing_stage(s2_path)
    if type(s1).__name__ != "RoutingS1StageManifest" or type(s2).__name__ != "RoutingS2StageManifest":
        raise PublicContractError("stage discriminator selected the wrong branch")
    for model, value in ((module.RoutingS2StageManifest, s1_value), (module.RoutingS1StageManifest, s2_value)):
        try:
            model.model_validate(value)
        except Exception:
            pass
        else:
            raise PublicContractError("stage model accepted cross-branch bytes")


CONFIG_ROOT = "benchmarks/fixtures/routing-v1/intermediate/three-stage-config-migration"
INCIDENT_ROOT = "benchmarks/fixtures/routing-v1/intermediate/three-stage-incident-analysis"


def _fixture_contract(root: str, expected_tasks: list[str], expected_outputs: int) -> None:
    required = [
        f"{root}/.orchestrator/capabilities.yaml",
        f"{root}/.orchestrator/checks.yaml",
        f"{root}/.orchestrator/policies.yaml",
        f"{root}/.orchestrator/project.yaml",
        f"{root}/README.md",
        f"{root}/benchmark-run.yaml",
    ]
    _require_paths(required)
    run = _load_yaml(ROOT / root / "benchmark-run.yaml")
    tasks = run.get("tasks")
    if not isinstance(tasks, list) or [item.get("key") for item in tasks] != expected_tasks:
        raise PublicContractError(f"fixture Task order is wrong: {root}")
    if [item.get("depends_on") for item in tasks] != [[], [expected_tasks[0]], [expected_tasks[1]]]:
        raise PublicContractError(f"fixture dependency chain is wrong: {root}")
    outputs = {path for item in tasks for path in item.get("write_scope", [])}
    if len(outputs) != expected_outputs:
        raise PublicContractError(f"fixture output count is wrong: {root}")
    for item in tasks:
        if item.get("check_names", [])[-1:] != ["diff_check"]:
            raise PublicContractError(f"fixture Task is missing diff_check: {root}")


def check_r03() -> None:
    config_files = [
        "spec/config-contract.md", "inputs/current.json", "inputs/legacy.json",
        "benchmark_checks/__init__.py", "benchmark_checks/test_schema_contract.py",
        "benchmark_checks/test_migration_parse.py", "benchmark_checks/test_integration.py",
        "schema/__init__.py", "schema/model.py", "schema/errors.py",
        "migration/__init__.py", "migration/legacy.py", "runtime/__init__.py",
        "runtime/parser.py", "runtime/serializer.py", "cli/__init__.py", "cli/config_cli.py",
    ]
    incident_files = [
        "spec/report-contract.md", "catalog/topics.json", "sources/source-a.md",
        "sources/source-b.md", "sources/source-c.md", "benchmark_checks/__init__.py",
        "benchmark_checks/test_ledger_structure.py", "benchmark_checks/test_timeline_structure.py",
        "benchmark_checks/test_report_structure.py", "analysis/evidence-ledger.json",
        "analysis/uncertainties.json", "timeline/events.json", "timeline/hypotheses.json",
        "report/claims.json", "report/action-plan.json", "report/final-report.md",
    ]
    _require_paths([f"{CONFIG_ROOT}/{path}" for path in config_files])
    _require_paths([f"{INCIDENT_ROOT}/{path}" for path in incident_files])
    _fixture_contract(CONFIG_ROOT, ["T1", "T2", "T3"], 6)
    _fixture_contract(INCIDENT_ROOT, ["T1", "T2", "T3"], 7)
    manifest = _load_yaml(ROOT / "benchmarks/manifests/sdk-routing-s2-intermediate.yaml")
    if [item.get("id") for item in manifest.get("fixtures", [])] != [
        "three-stage-config-migration", "three-stage-incident-analysis"
    ]:
        raise PublicContractError("S2 fixture manifest order is wrong")
    if manifest.get("budgets", {}).get("max_actual_live_model_turns") != 15:
        raise PublicContractError("S2 fixture manifest budget is wrong")


def check_r04() -> None:
    module = _import_runner_module("routing_suite")
    for name in ("build_routing_s2_plan", "compute_fixture_complexity"):
        value = getattr(module, name, None)
        if value is None or not callable(value):
            raise PublicContractError(f"stage-neutral Plan API is missing: {name}")
    signature = inspect.signature(module.build_routing_s2_plan)
    for name in ("repository_root", "suite_path", "stage_path", "runner", "variants", "environment_fingerprint", "created_at"):
        if name not in signature.parameters:
            raise PublicContractError(f"S2 Plan identity input is missing: {name}")
    stage = _load_yaml(ROOT / "benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml")
    expected = ["cell_s2_a_1_c2", "cell_s2_a_1_b1", "cell_s2_b_1_b1", "cell_s2_b_1_c2"]
    if [cell.get("cell_id") for cell in stage.get("cells", [])] != expected:
        raise PublicContractError("S2 initial Plan order is wrong")
    for relative in (
        "tools/benchmark-runner/scripts/probe_sdk_routing_s1_plan.py",
        "tools/benchmark-runner/scripts/run_sdk_routing_s1.py",
    ):
        if "--stage" not in (ROOT / relative).read_text(encoding="utf-8"):
            raise PublicContractError(f"shared routing script is not stage-selectable: {relative}")
    if (ROOT / "tools/benchmark-runner/src/benchmark_runner/routing_s2_live.py").exists():
        raise PublicContractError("a duplicate S2 Controller is forbidden")


class _Identity:
    variant_id = "b1"


class _Metrics:
    def __init__(self, retry: int, resume: int) -> None:
        self.values = {"b1_retry_count": retry, "b1_resume_count": resume}


class _Measurement:
    def __init__(self, retry: int, resume: int) -> None:
        self.identity = _Identity()
        self.variant_metrics = _Metrics(retry, resume)


def check_r05() -> None:
    policy = _import_runner_module("s2_policy")
    for name in ("remaining_b1_retry_resume_reserve", "s2_b1_turn_cap", "derive_s2_routing_policy"):
        if not callable(getattr(policy, name, None)):
            raise PublicContractError(f"structured S2 policy API is missing: {name}")
    if policy.remaining_b1_retry_resume_reserve([]) != 3 or policy.s2_b1_turn_cap([]) != 6:
        raise PublicContractError("empty-history S2 reserve is wrong")
    history = [_Measurement(1, 0), _Measurement(0, 1)]
    if policy.remaining_b1_retry_resume_reserve(history) != 1 or policy.s2_b1_turn_cap(history) != 4:
        raise PublicContractError("S2 reserve reused or lost turns")
    _import_runner_module("routing_live")
    if (ROOT / "tools/benchmark-runner/src/benchmark_runner/routing_s2_live.py").exists():
        raise PublicContractError("S2 lifecycle must reuse the shared Controller")


def check_r06() -> None:
    routing = _import_runner_module("routing_suite")
    for name in (
        "routing_s2_nonlive_status",
        "export_routing_s2_nonlive",
        "verify_routing_s2_nonlive_export",
    ):
        if not callable(getattr(routing, name, None)):
            raise PublicContractError(f"shared S2 status/export API is missing: {name}")
    posthoc = _import_runner_module("s2_posthoc")
    expected = {
        "three-stage-config-migration": ("CFG-P1", "CFG-P2", "CFG-P3", "CFG-P4", "CFG-P5"),
        "three-stage-incident-analysis": ("INC-P1", "INC-P2", "INC-P3", "INC-P4", "INC-P5"),
    }
    if dict(posthoc.PROPERTY_IDS) != expected or not callable(posthoc.evaluate_posthoc):
        raise PublicContractError("public deterministic property catalog is wrong")
    # The property checker programs are Judge-only inputs and are deliberately
    # absent from the Worker snapshot.  The public Check validates the exported
    # API and frozen catalog; the independent Judge executes those programs.


def _test_functions(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as exc:
        raise PublicContractError(f"invalid regression source: {path.relative_to(ROOT)}") from exc
    return {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")}


def check_r07() -> None:
    s2_path = ROOT / "tools/benchmark-runner/tests/test_routing_s2.py"
    suite_path = ROOT / "tools/benchmark-runner/tests/test_routing_suite.py"
    judge_path = ROOT / "tools/benchmark-runner/tests/test_judge.py"
    _require_paths([str(path.relative_to(ROOT).as_posix()) for path in (s2_path, suite_path, judge_path)])
    names = _test_functions(s2_path)
    required = {
        "test_s2_stage_discriminator_rejects_cross_branch_bytes",
        "test_s2_retry_reserve_is_independent_and_never_recycles_early_turns",
        "test_s2_b1_preflight_canonicalizes_legacy_project_pack",
        "test_s2_fake_four_cell_plan_judge_property_seal_export",
    }
    posthoc_regression_names = {
        "test_s2_posthoc_fixture_outputs_and_label_parity",
        "test_s2_posthoc_pristine_golden_and_label_parity",
    }
    if not required <= names or not posthoc_regression_names & names:
        raise PublicContractError("the S2 public regression groups are incomplete")
    legacy_names = _test_functions(suite_path)
    required_legacy = {
        "test_complexity_profiles_are_recomputed_from_frozen_fixture_trees",
        "test_s1_plan_has_exact_eight_cell_order_and_calibration_only_policy",
        "test_model_free_runner_executes_exactly_one_next_cell_and_seals",
        "test_model_free_status_and_export_reject_an_incomplete_suite",
        "test_all_eight_model_free_cells_seal_export_and_detect_tampering",
    }
    if not required_legacy <= legacy_names:
        raise PublicContractError("the legacy S1 regression source surface is incomplete")
    public_regressions = [
        "test_s2_stage_discriminator_rejects_cross_branch_bytes",
        "test_s2_frozen_fixture_manifest_matches_live_model_controls",
        "test_s2_retry_reserve_is_independent_and_never_recycles_early_turns",
        "test_s2_b1_preflight_canonicalizes_legacy_project_pack",
    ]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            *(f"{s2_path}::{name}" for name in public_regressions),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    if result.returncode != 0:
        raise PublicContractError(
            "the public S2 routing regressions failed",
            public_feedback=_public_pytest_failure_feedback(result),
            failure_classification="UNKNOWN",
        )


def check_r08() -> None:
    contract = _load_json(WORK / "operator-contract.json")
    _exact_keys(contract, {"schema_version", "commands"}, "operator contract")
    if contract["schema_version"] != 1 or not isinstance(contract["commands"], list):
        raise PublicContractError("operator contract is not version 1")
    required_fields = {
        "command_id", "argv", "precondition", "success_exit_codes", "failure_map",
        "allowed_source_states", "allowed_terminal_states", "stop_before_next_dispatch",
        "implementation_symbol", "public_schema",
    }
    command_ids: list[str] = []
    for command in contract["commands"]:
        _exact_keys(command, required_fields, "operator command")
        command_ids.append(command["command_id"])
        if not command["argv"] or not command["success_exit_codes"] or not command["failure_map"]:
            raise PublicContractError("operator command relation is incomplete")
        schema_path = _relative(command["public_schema"])
        if not (ROOT / schema_path).is_file():
            raise PublicContractError("operator command references a missing public Schema")
        module_name, separator, symbol_name = command["implementation_symbol"].partition(":")
        if not separator or not hasattr(_import_runner_module(module_name), symbol_name):
            raise PublicContractError("operator command references a missing implementation symbol")
    expected = ["create", "status", "run-next", "export", "verify"]
    if command_ids != expected:
        raise PublicContractError("operator command order is wrong")
    readme = (ROOT / "tools/benchmark-runner/README.md").read_text(encoding="utf-8")
    if "<!-- profile-r-operator-contract:start -->" not in readme or "<!-- profile-r-operator-contract:end -->" not in readme:
        raise PublicContractError("operator README is not bound to the structured contract")
    for command_id in expected:
        if f"`{command_id}`" not in readme:
            raise PublicContractError("operator README omits a structured command ID")


CHECKS = {
    "R01": check_r01,
    "R02": check_r02,
    "R03": check_r03,
    "R04": check_r04,
    "R05": check_r05,
    "R06": check_r06,
    "R07": check_r07,
    "R08": check_r08,
}


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in CHECKS:
        print("PROFILE_R_PUBLIC_CONTRACT_FAILED:UNKNOWN_TASK")
        return 2
    task_id = argv[1]
    try:
        CHECKS[task_id]()
    except PublicContractError as exc:
        print(f"{task_id}_PUBLIC_CONTRACT_FAILED")
        print(f"{CHECK_FAILURE_CLASS_PREFIX}{exc.failure_classification}")
        if exc.public_feedback:
            for line in exc.public_feedback:
                print(f"{WORKER_FEEDBACK_PREFIX}{line}")
        return 1
    except (OSError, subprocess.SubprocessError):
        print(f"{task_id}_PUBLIC_CONTRACT_FAILED")
        print(f"{CHECK_FAILURE_CLASS_PREFIX}ENVIRONMENT")
        return 1
    print(f"{task_id}_PUBLIC_CONTRACT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
