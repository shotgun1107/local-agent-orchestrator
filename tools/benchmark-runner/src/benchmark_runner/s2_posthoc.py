"""Deterministic post-hoc property checks for SDK routing S2 fixtures."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import subprocess
import sys
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any


CONFIG_FIXTURE_ID = "three-stage-config-migration"
INCIDENT_FIXTURE_ID = "three-stage-incident-analysis"
PROPERTY_IDS = {
    CONFIG_FIXTURE_ID: ("CFG-P1", "CFG-P2", "CFG-P3", "CFG-P4", "CFG-P5"),
    INCIDENT_FIXTURE_ID: ("INC-P1", "INC-P2", "INC-P3", "INC-P4", "INC-P5"),
}
_REPORT_HEADINGS = ("확인된 사실", "상충", "미확인", "권고")
_CLAIM_LINE = re.compile(r"^- \[([^\]]+)\] (.+)$")
_ACTION_LINE = re.compile(r"^- \[([^\]]+)\] (verify|mitigate): (.+)$")


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def checker_sha256(fixture_id: str) -> str:
    if fixture_id not in PROPERTY_IDS:
        raise ValueError(f"unsupported S2 fixture: {fixture_id}")
    repository_root = Path(__file__).resolve().parents[4]
    wrapper_name = "check_config.py" if fixture_id == CONFIG_FIXTURE_ID else "check_incident.py"
    paths = (
        Path(__file__).resolve(),
        repository_root
        / "benchmarks"
        / "posthoc-checks"
        / "sdk-routing-v1"
        / "s2"
        / "checkers"
        / wrapper_name,
    )
    digest = hashlib.sha256()
    for path in paths:
        data = path.read_bytes()
        relative = path.relative_to(repository_root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


@contextmanager
def _workspace_imports(workspace: Path):
    inserted = str(workspace.resolve())
    sys.path.insert(0, inserted)
    before = set(sys.modules)
    try:
        yield
    finally:
        sys.path.remove(inserted)
        for name in set(sys.modules) - before:
            module = sys.modules.get(name)
            origin = getattr(module, "__file__", None)
            if origin is not None and Path(origin).resolve().is_relative_to(workspace.resolve()):
                sys.modules.pop(name, None)


def _property_result(property_id: str, passed: bool, refs: list[str]) -> dict[str, object]:
    return {
        "property_id": property_id,
        "status": "pass" if passed else "fail",
        "evidence_refs": sorted(refs),
    }


def _run_properties(
    fixture_id: str,
    checks: Mapping[str, tuple[Callable[[], bool], list[str]]],
) -> dict[str, object]:
    results: list[dict[str, object]] = []
    for property_id in PROPERTY_IDS[fixture_id]:
        function, refs = checks[property_id]
        try:
            passed = function() is True
        except Exception:
            passed = False
        results.append(_property_result(property_id, passed, refs))
    return {
        "fixture_id": fixture_id,
        "checker_sha256": checker_sha256(fixture_id),
        "property_status": (
            "pass" if all(item["status"] == "pass" for item in results) else "fail"
        ),
        "properties": results,
    }


def _config_checks(workspace: Path) -> dict[str, object]:
    with _workspace_imports(workspace):
        model = importlib.import_module("schema.model")
        errors = importlib.import_module("schema.errors")
        migration = importlib.import_module("migration.legacy")
        parser = importlib.import_module("runtime.parser")
        serializer = importlib.import_module("runtime.serializer")

        legacy = json.loads((workspace / "inputs" / "legacy.json").read_text(encoding="utf-8"))
        current = json.loads((workspace / "inputs" / "current.json").read_text(encoding="utf-8"))

        def cfg_p1() -> bool:
            migrated = migration.migrate(legacy)
            validated = model.validate(migrated)
            return validated == {
                "endpoint": legacy["endpoint"],
                "max_retries": legacy["retries"],
                "timeout_seconds": legacy["timeout"],
                "version": 2,
            }

        def cfg_p2() -> bool:
            parsed = parser.parse(current)
            return parser.parse(serializer.serialize(parsed)) == parsed

        def cfg_p3() -> bool:
            once = migration.migrate(legacy)
            return migration.migrate(once) == once and migration.migrate(current) == current

        def cfg_p4() -> bool:
            cases = (
                ({**current, "version": 9}, errors.UnknownVersionError),
                (
                    {"version": 2, " timeout_seconds ": 1, "timeout_seconds": 2},
                    errors.DuplicateKeyError,
                ),
                ({**current, "unexpected": True}, errors.UnknownKeyError),
                ({**current, "timeout_seconds": "slow"}, errors.InvalidTypeError),
            )
            for payload, expected in cases:
                try:
                    parser.parse(payload)
                except expected:
                    continue
                except Exception:
                    return False
                return False
            return True

        def cfg_p5() -> bool:
            legacy_copy = json.loads(_canonical_json(legacy))
            current_copy = json.loads(_canonical_json(current))
            before = (_sha256_json(legacy_copy), _sha256_json(current_copy))
            migration.migrate(legacy_copy)
            parser.parse(current_copy)
            model.validate(current_copy)
            return before == (_sha256_json(legacy_copy), _sha256_json(current_copy))

        return _run_properties(
            CONFIG_FIXTURE_ID,
            {
                "CFG-P1": (cfg_p1, ["inputs/legacy.json"]),
                "CFG-P2": (cfg_p2, ["inputs/current.json"]),
                "CFG-P3": (cfg_p3, ["inputs/legacy.json", "inputs/current.json"]),
                "CFG-P4": (cfg_p4, ["spec/config-contract.md"]),
                "CFG-P5": (cfg_p5, ["inputs/legacy.json", "inputs/current.json"]),
            },
        )


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _parse_report(path: Path) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {name: {} for name in _REPORT_HEADINGS}
    current: str | None = None
    seen: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw:
            continue
        if raw.startswith("## "):
            current = raw[3:]
            if current not in sections or current in seen:
                raise ValueError("report heading differs")
            seen.append(current)
            continue
        if current is None:
            raise ValueError("report text appears outside a section")
        pattern = _ACTION_LINE if current == "권고" else _CLAIM_LINE
        match = pattern.fullmatch(raw)
        if match is None:
            raise ValueError("report line grammar differs")
        identifier = match.group(1)
        if identifier in sections[current]:
            raise ValueError("report identifier is duplicated")
        sections[current][identifier] = raw
    if tuple(seen) != _REPORT_HEADINGS:
        raise ValueError("report headings differ")
    return sections


def _incident_checks(workspace: Path) -> dict[str, object]:
    catalog = _load_object(workspace / "catalog" / "topics.json")
    ledger = _load_object(workspace / "analysis" / "evidence-ledger.json")
    uncertainties_payload = _load_object(workspace / "analysis" / "uncertainties.json")
    events_payload = _load_object(workspace / "timeline" / "events.json")
    hypotheses_payload = _load_object(workspace / "timeline" / "hypotheses.json")
    claims_payload = _load_object(workspace / "report" / "claims.json")
    actions_payload = _load_object(workspace / "report" / "action-plan.json")
    report = _parse_report(workspace / "report" / "final-report.md")

    sources = {item["source_id"]: item["path"] for item in catalog["sources"]}
    topics = {item["topic_id"]: item for item in catalog["topics"]}
    evidence = {item["evidence_id"]: item for item in ledger["evidence"]}
    uncertainties = {
        item["uncertainty_id"]: item for item in uncertainties_payload["uncertainties"]
    }
    events = {item["event_id"]: item for item in events_payload["events"]}
    hypotheses = {
        item["hypothesis_id"]: item for item in hypotheses_payload["hypotheses"]
    }
    claims = {item["claim_id"]: item for item in claims_payload["claims"]}
    actions = {item["action_id"]: item for item in actions_payload["actions"]}

    def inc_p1() -> bool:
        for item in evidence.values():
            source_path = workspace / sources[item["source_id"]]
            lines = source_path.read_text(encoding="utf-8").splitlines()
            locator = item["locator"]
            start = locator["line_start"]
            end = locator["line_end"]
            if not (isinstance(start, int) and isinstance(end, int) and 1 <= start <= end <= len(lines)):
                return False
            if "\n".join(lines[start - 1 : end]) != item["exact_excerpt"]:
                return False
        return True

    def inc_p2() -> bool:
        for topic_id, topic in topics.items():
            if topic["conflicting"] is not True:
                continue
            entries = [item for item in evidence.values() if item["topic_id"] == topic_id]
            if len({item["source_id"] for item in entries}) < topic["expected_distinct_source_count"]:
                return False
            entry_ids = {item["evidence_id"] for item in entries}
            conflicting_events = [
                item for item in events.values() if item["status"] == "conflicting"
            ]
            if not any(entry_ids.issubset(set(item["evidence_ids"])) for item in conflicting_events):
                return False
            conflicting_claim_evidence = {
                item["evidence_id"]
                for item in claims.values()
                if item["status"] == "conflicting"
            }
            if not entry_ids.issubset(conflicting_claim_evidence):
                return False
        return True

    def inc_p3() -> bool:
        evidence_ids = set(evidence)
        uncertainty_ids = set(uncertainties)
        for item in [*events.values(), *hypotheses.values()]:
            if not set(item["evidence_ids"]).issubset(evidence_ids):
                return False
            if not set(item["uncertainty_ids"]).issubset(uncertainty_ids):
                return False
        if any(item["evidence_id"] not in evidence_ids for item in claims.values()):
            return False
        valid_refs = evidence_ids | uncertainty_ids
        return all(set(item["reference_ids"]).issubset(valid_refs) for item in actions.values())

    def inc_p4() -> bool:
        for claim_id, item in claims.items():
            ledger_item = evidence[item["evidence_id"]]
            if item["canonical_claim_text"] != ledger_item["canonical_claim_text"]:
                return False
            section = "확인된 사실" if item["status"] == "confirmed" else "상충"
            expected = f"- [{claim_id}] {item['canonical_claim_text']}"
            if report[section].get(claim_id) != expected:
                return False
            other = "상충" if section == "확인된 사실" else "확인된 사실"
            if claim_id in report[other]:
                return False
        return set(report["확인된 사실"]) | set(report["상충"]) == set(claims)

    def inc_p5() -> bool:
        if any(identifier in report["확인된 사실"] for identifier in uncertainties):
            return False
        for uncertainty_id, item in uncertainties.items():
            expected = f"- [{uncertainty_id}] {item['next_action']}"
            if report["미확인"].get(uncertainty_id) != expected:
                return False
        if set(report["미확인"]) != set(uncertainties):
            return False
        for action_id, item in actions.items():
            refs = ",".join(item["reference_ids"])
            expected = f"- [{action_id}] {item['action_type']}: {refs}"
            if report["권고"].get(action_id) != expected:
                return False
        return set(report["권고"]) == set(actions)

    refs = [
        "catalog/topics.json",
        "analysis/evidence-ledger.json",
        "analysis/uncertainties.json",
        "timeline/events.json",
        "timeline/hypotheses.json",
        "report/claims.json",
        "report/action-plan.json",
        "report/final-report.md",
    ]
    return _run_properties(
        INCIDENT_FIXTURE_ID,
        {
            "INC-P1": (inc_p1, ["catalog/topics.json", "analysis/evidence-ledger.json"]),
            "INC-P2": (inc_p2, refs),
            "INC-P3": (inc_p3, refs),
            "INC-P4": (inc_p4, refs),
            "INC-P5": (inc_p5, refs),
        },
    )


def evaluate_posthoc(fixture_id: str, workspace: Path) -> dict[str, object]:
    workspace = workspace.resolve()
    try:
        if fixture_id == CONFIG_FIXTURE_ID:
            return _config_checks(workspace)
        if fixture_id == INCIDENT_FIXTURE_ID:
            return _incident_checks(workspace)
        raise ValueError(f"unsupported S2 fixture: {fixture_id}")
    except Exception:
        results = [
            _property_result(property_id, False, [])
            for property_id in PROPERTY_IDS.get(fixture_id, ())
        ]
        return {
            "fixture_id": fixture_id,
            "checker_sha256": checker_sha256(fixture_id),
            "property_status": "fail",
            "properties": results,
        }


def run_posthoc_subprocess(
    *,
    repository_root: Path,
    benchmark_python: Path,
    fixture_id: str,
    workspace: Path,
    timeout_seconds: float = 120.0,
) -> dict[str, object]:
    """Run one S2 checker in an isolated process and validate its public result."""

    checker_repository_root = Path(__file__).resolve().parents[4]
    wrapper = (
        checker_repository_root
        / "benchmarks"
        / "posthoc-checks"
        / "sdk-routing-v1"
        / "s2"
        / "checkers"
        / ("check_config.py" if fixture_id == CONFIG_FIXTURE_ID else "check_incident.py")
    )
    expected_sha256 = checker_sha256(fixture_id)

    def workspace_fingerprint() -> str:
        digest = hashlib.sha256()
        for path in sorted(
            (
                item
                for item in workspace.resolve().rglob("*")
                if item.is_file() and ".git" not in item.relative_to(workspace.resolve()).parts
            ),
            key=lambda item: item.relative_to(workspace.resolve()).as_posix(),
        ):
            relative = path.relative_to(workspace.resolve()).as_posix().encode("utf-8")
            data = path.read_bytes()
            digest.update(len(relative).to_bytes(8, "big"))
            digest.update(relative)
            digest.update(len(data).to_bytes(8, "big"))
            digest.update(data)
        return digest.hexdigest()

    before = workspace_fingerprint()
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
        }
    )
    try:
        result = subprocess.run(
            [
                str(benchmark_python.resolve()),
                "-P",
                str(wrapper),
                "--workspace",
                str(workspace.resolve()),
            ],
            cwd=repository_root.resolve(),
            env=environment,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        result = None
    if result is None or workspace_fingerprint() != before:
        return {
            "fixture_id": fixture_id,
            "checker_sha256": expected_sha256,
            "property_status": "checker_error",
            "properties": [],
        }
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError:
        value = None
    expected_keys = {"fixture_id", "checker_sha256", "property_status", "properties"}
    if (
        result.returncode not in {0, 2}
        or not isinstance(value, dict)
        or set(value) != expected_keys
        or value.get("fixture_id") != fixture_id
        or value.get("checker_sha256") != expected_sha256
        or value.get("property_status") not in {"pass", "fail", "checker_error"}
        or not isinstance(value.get("properties"), list)
    ):
        return {
            "fixture_id": fixture_id,
            "checker_sha256": expected_sha256,
            "property_status": "checker_error",
            "properties": [],
        }
    property_items = value["properties"]
    property_ids = [
        item.get("property_id") for item in property_items if isinstance(item, dict)
    ]
    property_contract_ok = all(
        isinstance(item, dict)
        and set(item) == {"property_id", "status", "evidence_refs"}
        and item.get("status") in {"pass", "fail"}
        and isinstance(item.get("evidence_refs"), list)
        and item["evidence_refs"] == sorted(set(item["evidence_refs"]))
        and all(isinstance(ref, str) and ref for ref in item["evidence_refs"])
        for item in property_items
    )
    status_matches = (
        value["property_status"] == "pass"
        and all(item["status"] == "pass" for item in property_items)
        and result.returncode == 0
    ) or (
        value["property_status"] == "fail"
        and any(item["status"] == "fail" for item in property_items)
        and result.returncode == 0
    ) or (
        value["property_status"] == "checker_error"
        and property_items == []
        and result.returncode == 2
    )
    if (
        (
            value["property_status"] != "checker_error"
            and property_ids != list(PROPERTY_IDS[fixture_id])
        )
        or not property_contract_ok
        or not status_matches
    ):
        return {
            "fixture_id": fixture_id,
            "checker_sha256": expected_sha256,
            "property_status": "checker_error",
            "properties": [],
        }
    return value
