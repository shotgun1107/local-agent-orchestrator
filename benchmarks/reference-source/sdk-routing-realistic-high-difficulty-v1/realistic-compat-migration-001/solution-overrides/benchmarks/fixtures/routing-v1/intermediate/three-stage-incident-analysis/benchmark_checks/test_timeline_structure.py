from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INCIDENT_ID = "INC-2025-02-14-CHECKOUT"


def _json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _ids(items: list[dict], key: str) -> set[str]:
    values = [item[key] for item in items]
    assert len(values) == len(set(values))
    return set(values)


def test_events_are_chronological_sourced_and_uncertainty_safe() -> None:
    evidence = _json("analysis/evidence-ledger.json")["evidence"]
    uncertainties = _json("analysis/uncertainties.json")["uncertainties"]
    timeline = _json("timeline/events.json")
    assert set(timeline) == {"schema_version", "incident_id", "events"}
    assert timeline["schema_version"] == 1 and timeline["incident_id"] == INCIDENT_ID
    evidence_ids = _ids(evidence, "evidence_id")
    uncertainty_ids = _ids(uncertainties, "uncertainty_id")
    open_ids = {item["uncertainty_id"] for item in uncertainties if item["status"] == "open"}
    events = timeline["events"]
    _ids(events, "event_id")
    stamps = [datetime.fromisoformat(item["occurred_at"].replace("Z", "+00:00")) for item in events]
    assert stamps == sorted(stamps)

    expected_keys = {
        "event_id", "occurred_at", "summary", "status", "evidence_ids", "uncertainty_ids"
    }
    for event in events:
        assert set(event) == expected_keys and event["summary"]
        assert event["status"] in {"confirmed", "disputed"}
        assert event["evidence_ids"] and len(event["evidence_ids"]) == len(set(event["evidence_ids"]))
        assert set(event["evidence_ids"]) <= evidence_ids
        assert set(event["uncertainty_ids"]) <= uncertainty_ids
        if event["status"] == "confirmed":
            assert event["uncertainty_ids"] == []
        else:
            assert event["uncertainty_ids"] and set(event["uncertainty_ids"]) <= open_ids
            assert len({next(item["source_id"] for item in evidence if item["evidence_id"] == ref)
                        for ref in event["evidence_ids"]}) >= 2


def test_hypotheses_never_turn_correlation_into_fact() -> None:
    evidence_ids = _ids(_json("analysis/evidence-ledger.json")["evidence"], "evidence_id")
    open_ids = {
        item["uncertainty_id"]
        for item in _json("analysis/uncertainties.json")["uncertainties"]
        if item["status"] == "open"
    }
    document = _json("timeline/hypotheses.json")
    assert set(document) == {"schema_version", "incident_id", "hypotheses"}
    assert document["schema_version"] == 1 and document["incident_id"] == INCIDENT_ID
    hypotheses = document["hypotheses"]
    _ids(hypotheses, "hypothesis_id")
    expected_keys = {
        "hypothesis_id", "statement", "status", "supporting_evidence_ids",
        "conflicting_evidence_ids", "uncertainty_ids",
    }
    for hypothesis in hypotheses:
        assert set(hypothesis) == expected_keys and hypothesis["statement"]
        assert hypothesis["status"] in {"unconfirmed", "rejected"}
        supporting = hypothesis["supporting_evidence_ids"]
        conflicting = hypothesis["conflicting_evidence_ids"]
        assert supporting and conflicting and set(supporting).isdisjoint(conflicting)
        assert len(supporting) == len(set(supporting)) and len(conflicting) == len(set(conflicting))
        assert set(supporting + conflicting) <= evidence_ids
        assert hypothesis["uncertainty_ids"] and set(hypothesis["uncertainty_ids"]) <= open_ids


def test_disputed_evidence_is_not_lost_from_the_timeline() -> None:
    disputed_evidence = {
        evidence_id
        for item in _json("analysis/uncertainties.json")["uncertainties"]
        if item["topic_id"] == "TOP-001"
        for evidence_id in item["evidence_ids"]
    }
    represented = {
        evidence_id
        for event in _json("timeline/events.json")["events"]
        if event["status"] == "disputed"
        for evidence_id in event["evidence_ids"]
    }
    assert disputed_evidence == represented
