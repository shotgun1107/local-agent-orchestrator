from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TimelineStructureTest(unittest.TestCase):
    def test_timeline_documents_have_public_shape(self) -> None:
        events = json.loads((ROOT / "timeline/events.json").read_text(encoding="utf-8"))
        hypotheses = json.loads((ROOT / "timeline/hypotheses.json").read_text(encoding="utf-8"))
        self.assertEqual(set(events), {"events"})
        self.assertGreater(len(events["events"]), 0)
        for item in events["events"]:
            self.assertEqual(set(item), {"event_id", "status", "evidence_ids", "uncertainty_ids"})
            self.assertTrue(item["event_id"].isascii() and item["event_id"])
            self.assertIn(item["status"], {"confirmed", "conflicting", "uncertain"})
            self.assertEqual(item["evidence_ids"], sorted(item["evidence_ids"]))
            self.assertEqual(item["uncertainty_ids"], sorted(item["uncertainty_ids"]))
        self.assertEqual(set(hypotheses), {"hypotheses"})
        self.assertGreater(len(hypotheses["hypotheses"]), 0)
        for item in hypotheses["hypotheses"]:
            self.assertEqual(set(item), {"hypothesis_id", "status", "evidence_ids", "uncertainty_ids"})
            self.assertTrue(item["hypothesis_id"].isascii() and item["hypothesis_id"])
            self.assertEqual(item["status"], "candidate")
            self.assertEqual(item["evidence_ids"], sorted(item["evidence_ids"]))
            self.assertEqual(item["uncertainty_ids"], sorted(item["uncertainty_ids"]))


if __name__ == "__main__":
    unittest.main()
