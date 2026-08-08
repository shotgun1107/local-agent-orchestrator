"""Deterministic post-hoc property checks for SDK routing S3 fixtures."""

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

import yaml


COMPATIBILITY_FIXTURE_ID = "four-stage-compatibility-refactor"
INCIDENT_FIXTURE_ID = "four-stage-conflicting-incident-report"
PROPERTY_IDS = {
    COMPATIBILITY_FIXTURE_ID: (
        "HCR-P1",
        "HCR-P2",
        "HCR-P3",
        "HCR-P4",
        "HCR-P5a",
        "HCR-P5b",
        "HCR-P6",
    ),
    INCIDENT_FIXTURE_ID: (
        "HCI-P1",
        "HCI-P2",
        "HCI-P3",
        "HCI-P4",
        "HCI-P5",
        "HCI-P6",
    ),
}
_REPORT_HEADINGS = ("확인된 사실", "상충", "미확인", "권고")
_CLAIM_LINE = re.compile(r"^- \[([^\]]+)\] (.+)$")
_ACTION_LINE = re.compile(r"^- \[([^\]]+)\] (verify|mitigate): (.+)$")


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def checker_sha256(fixture_id: str) -> str:
    if fixture_id not in PROPERTY_IDS:
        raise ValueError(f"unsupported S3 fixture: {fixture_id}")
    repository_root = Path(__file__).resolve().parents[4]
    wrapper_name = (
        "check_compatibility.py"
        if fixture_id == COMPATIBILITY_FIXTURE_ID
        else "check_incident.py"
    )
    paths = (
        Path(__file__).resolve(),
        repository_root
        / "benchmarks"
        / "posthoc-checks"
        / "sdk-routing-v1"
        / "s3"
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


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _property_result(property_id: str, passed: bool, refs: list[str]) -> dict[str, object]:
    return {
        "property_id": property_id,
        "status": "pass" if passed else "fail",
        "evidence_refs": sorted(set(refs)),
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


def _compatibility_checks(workspace: Path) -> dict[str, object]:
    public_api = _load_object(workspace / "contract" / "public-api.json")
    cases_payload = _load_object(workspace / "contract" / "compatibility-cases.json")
    deprecation = _load_object(workspace / "contract" / "deprecation-policy.json")
    protected = _load_object(workspace / "contract" / "protected-files.json")
    cases = cases_payload["cases"]
    invalid_cases = cases_payload["invalid_cases"]

    with _workspace_imports(workspace):
        model = importlib.import_module("schema.model")
        errors = importlib.import_module("schema.errors")
        migration = importlib.import_module("migration.upgrade")
        parser = importlib.import_module("runtime.parser")
        serializer = importlib.import_module("runtime.serializer")
        adapter = importlib.import_module("integration.adapter")
        legacy_api = importlib.import_module("compat.legacy_api")
        roundtrip = importlib.import_module("compat.roundtrip")
        config_cli = importlib.import_module("cli.config_cli")

        def hcr_p1() -> bool:
            return bool(
                list(model.PUBLIC_FIELDS) == public_api["canonical_fields"]
                and model.ALIASES == deprecation["allowed_aliases"]
                and errors.ERROR_CODES == public_api["error_codes"]
            )

        def hcr_p2() -> bool:
            return all(
                migration.migrate(json.loads(_canonical_json(item["old_payload"])))
                == item["canonical"]
                for item in cases
            )

        def hcr_p3() -> bool:
            return all(
                parser.parse(item["old_payload"]) == item["canonical"]
                and parser.parse(item["new_payload"]) == item["canonical"]
                and serializer.serialize(item["canonical"]) == item["serialization"]
                and adapter.normalize(item["old_payload"]) == item["canonical"]
                for item in cases
            )

        def hcr_p4() -> bool:
            for item in cases:
                canonical = item["canonical"]
                if legacy_api.load(item["old_payload"]) != canonical:
                    return False
                if roundtrip.roundtrip(item["old_payload"]) != item["serialization"]:
                    return False
                if config_cli.run(item["old_payload"]) != {"ok": True, "value": canonical}:
                    return False
            for item in invalid_cases:
                result = config_cli.run(item["payload"])
                if result != {"ok": False, "error_code": item["error_code"]}:
                    return False
            return True

        def hcr_p5a() -> bool:
            for item in cases:
                once = migration.migrate(item["old_payload"])
                if migration.migrate(once) != once:
                    return False
            return True

        def pipeline(payload: object) -> dict[str, object]:
            canonical = parser.parse(migration.migrate(payload))
            return parser.parse(serializer.serialize(canonical))

        def hcr_p5b() -> bool:
            return all(
                pipeline(item["old_payload"]) == item["canonical"]
                and pipeline(pipeline(item["old_payload"])) == item["canonical"]
                for item in cases
            )

        def hcr_p6() -> bool:
            run = yaml.safe_load((workspace / "benchmark-run.yaml").read_text(encoding="utf-8"))
            writes = {
                path
                for task in run["tasks"]
                for path in task["write_scope"]
            }
            protected_paths = set(protected["protected_paths"])
            if writes != set(protected["allowed_write_paths"]) or writes & protected_paths:
                return False
            overlaps = {
                f"{left['key']}->{right['key']}:{path}"
                for index, left in enumerate(run["tasks"])
                for right in run["tasks"][index + 1 :]
                for path in set(left["write_scope"]) & set(right["write_scope"])
            }
            return overlaps == set(protected["allowed_overlap_edges"])

        refs = [
            "contract/public-api.json",
            "contract/compatibility-cases.json",
            "contract/deprecation-policy.json",
            "spec/compatibility-contract.md",
        ]
        return _run_properties(
            COMPATIBILITY_FIXTURE_ID,
            {
                "HCR-P1": (hcr_p1, refs[:3]),
                "HCR-P2": (hcr_p2, [refs[1]]),
                "HCR-P3": (hcr_p3, refs),
                "HCR-P4": (hcr_p4, refs),
                "HCR-P5a": (hcr_p5a, [refs[1]]),
                "HCR-P5b": (hcr_p5b, refs),
                "HCR-P6": (
                    hcr_p6,
                    ["benchmark-run.yaml", "contract/protected-files.json"],
                ),
            },
        )


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
    sources_payload = _load_object(workspace / "catalog" / "sources.json")
    topics_payload = _load_object(workspace / "catalog" / "topics.json")
    groups_payload = _load_object(workspace / "catalog" / "conflict-groups.json")
    ledger_payload = _load_object(workspace / "analysis" / "evidence-ledger.json")
    uncertainties_payload = _load_object(workspace / "analysis" / "uncertainties.json")
    events_payload = _load_object(workspace / "timeline" / "events.json")
    timeline_groups_payload = _load_object(workspace / "timeline" / "conflict-groups.json")
    hypotheses_payload = _load_object(workspace / "analysis" / "hypotheses.json")
    alternatives_payload = _load_object(workspace / "analysis" / "alternative-matrix.json")
    claims_payload = _load_object(workspace / "report" / "claims.json")
    actions_payload = _load_object(workspace / "report" / "action-plan.json")
    report = _parse_report(workspace / "report" / "final-report.md")

    sources = {item["source_id"]: item["path"] for item in sources_payload["sources"]}
    topics = {item["topic_id"]: item for item in topics_payload["topics"]}
    catalog_groups = {item["group_id"]: item for item in groups_payload["groups"]}
    evidence = {item["evidence_id"]: item for item in ledger_payload["evidence"]}
    uncertainties = {
        item["uncertainty_id"]: item for item in uncertainties_payload["uncertainties"]
    }
    events = {item["event_id"]: item for item in events_payload["events"]}
    timeline_groups = {
        item["group_id"]: item for item in timeline_groups_payload["groups"]
    }
    hypotheses = {
        item["hypothesis_id"]: item for item in hypotheses_payload["hypotheses"]
    }
    alternatives = {
        item["alternative_id"]: item for item in alternatives_payload["alternatives"]
    }
    claims = {item["claim_id"]: item for item in claims_payload["claims"]}
    actions = {item["action_id"]: item for item in actions_payload["actions"]}

    def hci_p1() -> bool:
        for item in evidence.values():
            source_path = workspace / sources[item["source_id"]]
            lines = source_path.read_text(encoding="utf-8").splitlines()
            locator = item["locator"]
            start, end = locator["line_start"], locator["line_end"]
            if not (
                isinstance(start, int)
                and isinstance(end, int)
                and 1 <= start <= end <= len(lines)
                and "\n".join(lines[start - 1 : end]) == item["exact_excerpt"]
            ):
                return False
        return bool(evidence)

    def hci_p2() -> bool:
        for topic_id, topic in topics.items():
            entries = [item for item in evidence.values() if item["topic_id"] == topic_id]
            if len({item["source_id"] for item in entries}) < topic["required_distinct_sources"]:
                return False
        return {item["topic_id"] for item in evidence.values()} == set(topics)

    def hci_p3() -> bool:
        for group_id, catalog_group in catalog_groups.items():
            actual = timeline_groups.get(group_id)
            if actual is None or set(actual["topic_ids"]) != set(catalog_group["topic_ids"]):
                return False
            group_evidence = {
                item["evidence_id"]
                for item in evidence.values()
                if item["topic_id"] in catalog_group["topic_ids"]
            }
            if not group_evidence.issubset(set(actual["evidence_ids"])):
                return False
            if not any(
                event["status"] == "conflicting"
                and group_evidence.issubset(set(event["evidence_ids"]))
                for event in events.values()
            ):
                return False
        return set(timeline_groups) == set(catalog_groups)

    def hci_p4() -> bool:
        for group_id in catalog_groups:
            if not any(group_id in item["conflict_group_ids"] for item in hypotheses.values()):
                return False
        for uncertainty_id in uncertainties:
            if not any(uncertainty_id in item["uncertainty_ids"] for item in hypotheses.values()):
                return False
        hypothesis_ids = set(hypotheses)
        if not alternatives or any(
            not set(item["hypothesis_ids"]).issubset(hypothesis_ids)
            or not item["hypothesis_ids"]
            for item in alternatives.values()
        ):
            return False
        return all(
            any(hypothesis_id in item["hypothesis_ids"] for item in alternatives.values())
            for hypothesis_id in hypothesis_ids
        )

    def hci_p5() -> bool:
        evidence_ids = set(evidence)
        for claim_id, claim in claims.items():
            evidence_item = evidence.get(claim["evidence_id"])
            if evidence_item is None or claim["status"] != evidence_item["status"]:
                return False
            section = {
                "confirmed": "확인된 사실",
                "conflicting": "상충",
                "uncertain": "미확인",
            }[claim["status"]]
            expected = f"- [{claim_id}] {claim['canonical_claim_text']}"
            if report[section].get(claim_id) != expected:
                return False
        report_claim_ids = set().union(
            set(report["확인된 사실"]), set(report["상충"]), set(report["미확인"])
        )
        return set(claims) == report_claim_ids and {
            item["evidence_id"] for item in claims.values()
        }.issubset(evidence_ids)

    def hci_p6() -> bool:
        valid_refs = set(evidence) | set(uncertainties)
        for action_id, action in actions.items():
            if not action["reference_ids"] or not set(action["reference_ids"]).issubset(valid_refs):
                return False
            refs = ",".join(action["reference_ids"])
            expected = f"- [{action_id}] {action['action_type']}: {refs}"
            if report["권고"].get(action_id) != expected:
                return False
        return set(report["권고"]) == set(actions)

    refs = [
        "catalog/sources.json",
        "catalog/topics.json",
        "catalog/conflict-groups.json",
        "analysis/evidence-ledger.json",
        "analysis/uncertainties.json",
        "timeline/events.json",
        "timeline/conflict-groups.json",
        "analysis/hypotheses.json",
        "analysis/alternative-matrix.json",
        "report/claims.json",
        "report/action-plan.json",
        "report/final-report.md",
    ]
    return _run_properties(
        INCIDENT_FIXTURE_ID,
        {
            "HCI-P1": (hci_p1, refs[:4]),
            "HCI-P2": (hci_p2, refs[:5]),
            "HCI-P3": (hci_p3, refs[:7]),
            "HCI-P4": (hci_p4, refs[4:9]),
            "HCI-P5": (hci_p5, refs[3:11]),
            "HCI-P6": (hci_p6, refs[3:]),
        },
    )


def evaluate_posthoc(fixture_id: str, workspace: Path) -> dict[str, object]:
    workspace = workspace.resolve()
    try:
        if fixture_id == COMPATIBILITY_FIXTURE_ID:
            return _compatibility_checks(workspace)
        if fixture_id == INCIDENT_FIXTURE_ID:
            return _incident_checks(workspace)
        raise ValueError(f"unsupported S3 fixture: {fixture_id}")
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
    """Run one S3 checker in an isolated process and validate its public result."""

    checker_repository_root = Path(__file__).resolve().parents[4]
    wrapper = (
        checker_repository_root
        / "benchmarks"
        / "posthoc-checks"
        / "sdk-routing-v1"
        / "s3"
        / "checkers"
        / (
            "check_compatibility.py"
            if fixture_id == COMPATIBILITY_FIXTURE_ID
            else "check_incident.py"
        )
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
