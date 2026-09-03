from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INCIDENT_ID = "INC-2025-02-14-CHECKOUT"


def _json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _unique(items: list[dict], key: str) -> dict[str, dict]:
    values = [item[key] for item in items]
    assert len(values) == len(set(values))
    return {item[key]: item for item in items}


def test_evidence_is_an_exact_projection_of_source_markers() -> None:
    ledger = _json("analysis/evidence-ledger.json")
    assert set(ledger) == {"schema_version", "incident_id", "evidence"}
    assert ledger["schema_version"] == 1 and ledger["incident_id"] == INCIDENT_ID
    evidence = _unique(ledger["evidence"], "evidence_id")

    source_markers: dict[str, tuple[str, str, str]] = {}
    for path in sorted((ROOT / "sources").glob("source-*.md")):
        source = path.read_text(encoding="utf-8")
        source_id = re.search(r"Source ID: `([^`]+)`", source)
        assert source_id is not None
        for marker, statement in re.findall(r"^- \[([^]]+)] (.+)$", source, re.MULTILINE):
            assert marker not in source_markers
            source_markers[marker] = (source_id.group(1), path.relative_to(ROOT).as_posix(), statement)

    assert set(evidence) == set(source_markers)
    expected_keys = {
        "evidence_id", "topic_id", "source_id", "source_path",
        "source_marker", "statement", "recorded_at",
    }
    for evidence_id, item in evidence.items():
        assert set(item) == expected_keys
        source_id, source_path, statement = source_markers[evidence_id]
        assert item["source_marker"] == evidence_id
        assert (item["source_id"], item["source_path"], item["statement"]) == (
            source_id, source_path, statement
        )
        assert datetime.fromisoformat(item["recorded_at"].replace("Z", "+00:00")).tzinfo


def test_topics_classify_conflict_and_uncertainty_without_orphans() -> None:
    catalog = _json("catalog/topics.json")
    ledger = _json("analysis/evidence-ledger.json")
    uncertainties = _json("analysis/uncertainties.json")
    assert catalog["schema_version"] == uncertainties["schema_version"] == 1
    assert catalog["incident_id"] == uncertainties["incident_id"] == INCIDENT_ID

    topics = _unique(catalog["topics"], "topic_id")
    assert {item["kind"] for item in topics.values()} == {"fact", "conflict", "uncertainty"}
    evidence = _unique(ledger["evidence"], "evidence_id")
    assert {item["topic_id"] for item in evidence.values()} == set(topics)

    for topic_id, topic in topics.items():
        members = [item for item in evidence.values() if item["topic_id"] == topic_id]
        assert members
        if topic["kind"] == "conflict":
            assert len({item["source_id"] for item in members}) >= 2
            assert len({item["statement"] for item in members}) >= 2

    questions = _unique(uncertainties["uncertainties"], "uncertainty_id")
    expected_keys = {
        "uncertainty_id", "topic_id", "question", "reason", "status", "evidence_ids"
    }
    assert questions
    for item in questions.values():
        assert set(item) == expected_keys and item["status"] == "open"
        assert item["question"] and item["reason"]
        assert item["evidence_ids"] and len(item["evidence_ids"]) == len(set(item["evidence_ids"]))
        assert set(item["evidence_ids"]) <= set(evidence)
        assert item["topic_id"] in topics
        assert topics[item["topic_id"]]["kind"] in {"conflict", "uncertainty"}


def test_every_non_fact_topic_remains_explicitly_open() -> None:
    catalog = _json("catalog/topics.json")
    uncertainties = _json("analysis/uncertainties.json")["uncertainties"]
    open_topics = {item["topic_id"] for item in uncertainties if item["status"] == "open"}
    expected = {item["topic_id"] for item in catalog["topics"] if item["kind"] != "fact"}
    assert open_topics == expected
