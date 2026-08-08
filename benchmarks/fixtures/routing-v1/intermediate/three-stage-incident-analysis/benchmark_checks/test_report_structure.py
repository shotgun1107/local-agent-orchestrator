from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReportStructureTest(unittest.TestCase):
    def test_report_documents_have_public_shape(self) -> None:
        claims = json.loads((ROOT / "report/claims.json").read_text(encoding="utf-8"))
        actions = json.loads((ROOT / "report/action-plan.json").read_text(encoding="utf-8"))
        report = (ROOT / "report/final-report.md").read_text(encoding="utf-8")
        self.assertEqual(set(claims), {"claims"})
        self.assertGreater(len(claims["claims"]), 0)
        for item in claims["claims"]:
            self.assertEqual(set(item), {"claim_id", "evidence_id", "status", "canonical_claim_text"})
            self.assertTrue(item["claim_id"].isascii() and item["claim_id"])
            self.assertIn(item["status"], {"confirmed", "conflicting"})
        self.assertEqual(set(actions), {"actions"})
        self.assertGreater(len(actions["actions"]), 0)
        for item in actions["actions"]:
            self.assertEqual(set(item), {"action_id", "action_type", "reference_ids"})
            self.assertTrue(item["action_id"].isascii() and item["action_id"])
            self.assertIn(item["action_type"], {"verify", "mitigate"})
            self.assertEqual(item["reference_ids"], sorted(item["reference_ids"]))
        self.assertEqual(
            [line[3:] for line in report.splitlines() if line.startswith("## ")],
            ["확인된 사실", "상충", "미확인", "권고"],
        )
        section = None
        for line in report.splitlines():
            if not line:
                continue
            if line.startswith("## "):
                section = line[3:]
                continue
            self.assertIsNotNone(section)
            pattern = (
                r"^- \[[^\]]+\] (verify|mitigate): [A-Za-z0-9,._-]+$"
                if section == "권고"
                else r"^- \[[^\]]+\] .+$"
            )
            self.assertIsNotNone(re.fullmatch(pattern, line))


if __name__ == "__main__":
    unittest.main()
