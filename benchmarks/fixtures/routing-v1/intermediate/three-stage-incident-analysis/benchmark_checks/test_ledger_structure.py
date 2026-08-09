from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LedgerStructureTest(unittest.TestCase):
    def test_ledger_and_uncertainties_have_public_shape(self) -> None:
        ledger = json.loads((ROOT / "analysis/evidence-ledger.json").read_text(encoding="utf-8"))
        uncertainties = json.loads((ROOT / "analysis/uncertainties.json").read_text(encoding="utf-8"))
        self.assertEqual(set(ledger), {"evidence"})
        self.assertGreater(len(ledger["evidence"]), 0)
        for item in ledger["evidence"]:
            self.assertEqual(
                set(item),
                {"evidence_id", "source_id", "locator", "exact_excerpt", "topic_id", "observation_status", "canonical_claim_text"},
            )
            self.assertTrue(item["evidence_id"].isascii() and item["evidence_id"])
            self.assertEqual(set(item["locator"]), {"line_start", "line_end"})
            self.assertIn(item["observation_status"], {"observed", "reported", "derived"})
        self.assertEqual(set(uncertainties), {"uncertainties"})
        self.assertGreater(len(uncertainties["uncertainties"]), 0)
        for item in uncertainties["uncertainties"]:
            self.assertEqual(set(item), {"uncertainty_id", "evidence_ids", "source_ids", "next_action"})
            self.assertTrue(item["uncertainty_id"].isascii() and item["uncertainty_id"])
            self.assertEqual(item["evidence_ids"], sorted(item["evidence_ids"]))
            self.assertEqual(item["source_ids"], sorted(item["source_ids"]))


if __name__ == "__main__":
    unittest.main()
