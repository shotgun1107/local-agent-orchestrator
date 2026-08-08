import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ConflictContractTest(unittest.TestCase):
    def test_conflicts_are_preserved(self):
        expected = {item["group_id"]: item for item in json.loads((ROOT / "catalog/conflict-groups.json").read_text(encoding="utf-8"))["groups"]}
        actual = {item["group_id"]: item for item in json.loads((ROOT / "timeline/conflict-groups.json").read_text(encoding="utf-8"))["groups"]}
        events = json.loads((ROOT / "timeline/events.json").read_text(encoding="utf-8"))["events"]
        self.assertEqual(set(actual), set(expected))
        for group_id, group in expected.items():
            self.assertEqual(set(actual[group_id]["topic_ids"]), set(group["topic_ids"]))
            self.assertTrue(any(event["status"] == "conflicting" and set(actual[group_id]["evidence_ids"]).issubset(event["evidence_ids"]) for event in events))


if __name__ == "__main__":
    unittest.main()
