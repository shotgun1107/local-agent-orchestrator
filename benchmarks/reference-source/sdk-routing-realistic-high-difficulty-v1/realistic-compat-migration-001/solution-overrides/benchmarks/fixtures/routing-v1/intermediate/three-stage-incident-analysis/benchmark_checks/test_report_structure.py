from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INCIDENT_ID = "INC-2025-02-14-CHECKOUT"
SECTIONS = ["확인된 사실", "상충", "미확인", "권고"]


def _json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _mapping(path: str, collection: str, key: str) -> dict[str, dict]:
    items = _json(path)[collection]
    assert len(items) == len({item[key] for item in items})
    return {item[key]: item for item in items}


def _render(claims: list[dict], actions: list[dict]) -> str:
    lines = [f"# {INCIDENT_ID}", ""]
    for section in SECTIONS:
        lines.extend([f"## {section}", ""])
        if section == "권고":
            items = sorted(actions, key=lambda item: item["priority"])
            lines.extend(f'- [{item["action_id"]}] {item["text"]}' for item in items)
        else:
            items = [item for item in claims if item["section"] == section]
            lines.extend(f'- [{item["claim_id"]}] {item["text"]}' for item in items)
        lines.append("")
    return "\n".join(lines)


def test_claims_keep_complete_transitive_lineage() -> None:
    claims_document = _json("report/claims.json")
    assert set(claims_document) == {"schema_version", "incident_id", "claims"}
    assert claims_document["schema_version"] == 1 and claims_document["incident_id"] == INCIDENT_ID
    evidence = _mapping("analysis/evidence-ledger.json", "evidence", "evidence_id")
    events = _mapping("timeline/events.json", "events", "event_id")
    uncertainties = _mapping("analysis/uncertainties.json", "uncertainties", "uncertainty_id")
    claims = claims_document["claims"]
    assert len(claims) == len({item["claim_id"] for item in claims})
    assert [item["section"] for item in claims] == sorted(
        (item["section"] for item in claims), key=["확인된 사실", "상충", "미확인"].index
    )
    expected_keys = {
        "claim_id", "section", "text", "evidence_ids", "event_ids", "uncertainty_ids"
    }
    for claim in claims:
        assert set(claim) == expected_keys and claim["text"]
        assert claim["section"] in SECTIONS[:-1]
        assert claim["evidence_ids"] and claim["event_ids"]
        assert set(claim["evidence_ids"]) <= set(evidence)
        assert set(claim["event_ids"]) <= set(events)
        assert set(claim["uncertainty_ids"]) <= set(uncertainties)
        for field in ("evidence_ids", "event_ids", "uncertainty_ids"):
            assert len(claim[field]) == len(set(claim[field]))
        if claim["section"] == "확인된 사실":
            assert claim["uncertainty_ids"] == []
            assert all(events[event_id]["status"] == "confirmed" for event_id in claim["event_ids"])
        else:
            assert claim["uncertainty_ids"]
            assert all(uncertainties[item]["status"] == "open" for item in claim["uncertainty_ids"])


def test_actions_are_ordered_and_address_open_questions() -> None:
    claims = _mapping("report/claims.json", "claims", "claim_id")
    uncertainties = _mapping("analysis/uncertainties.json", "uncertainties", "uncertainty_id")
    document = _json("report/action-plan.json")
    assert set(document) == {"schema_version", "incident_id", "actions"}
    assert document["schema_version"] == 1 and document["incident_id"] == INCIDENT_ID
    actions = document["actions"]
    assert len(actions) == len({item["action_id"] for item in actions})
    assert [item["priority"] for item in actions] == list(range(1, len(actions) + 1))
    for action in actions:
        assert set(action) == {"action_id", "priority", "text", "claim_ids", "uncertainty_ids"}
        assert action["text"] and action["claim_ids"] and action["uncertainty_ids"]
        assert set(action["claim_ids"]) <= set(claims)
        assert set(action["uncertainty_ids"]) <= set(uncertainties)
        assert all(uncertainties[item]["status"] == "open" for item in action["uncertainty_ids"])
    addressed = {item for action in actions for item in action["uncertainty_ids"]}
    assert addressed == set(uncertainties)


def test_final_report_is_only_the_structured_projection() -> None:
    claims = _json("report/claims.json")["claims"]
    actions = _json("report/action-plan.json")["actions"]
    report = (ROOT / "report/final-report.md").read_text(encoding="utf-8")
    assert report == _render(claims, actions)
    assert re.findall(r"^## (.+)$", report, re.MULTILINE) == SECTIONS
    rendered_ids = re.findall(r"^- \[([^]]+)]", report, re.MULTILINE)
    assert rendered_ids == [item["claim_id"] for item in claims] + [
        item["action_id"] for item in sorted(actions, key=lambda item: item["priority"])
    ]
