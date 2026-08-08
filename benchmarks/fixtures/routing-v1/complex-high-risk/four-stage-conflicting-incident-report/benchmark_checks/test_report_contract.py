import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReportContractTest(unittest.TestCase):
    def test_claim_status_and_action_references(self):
        evidence = {item["evidence_id"]: item for item in json.loads((ROOT / "analysis/evidence-ledger.json").read_text(encoding="utf-8"))["evidence"]}
        uncertainties = {item["uncertainty_id"] for item in json.loads((ROOT / "analysis/uncertainties.json").read_text(encoding="utf-8"))["uncertainties"]}
        claims = json.loads((ROOT / "report/claims.json").read_text(encoding="utf-8"))["claims"]
        actions = json.loads((ROOT / "report/action-plan.json").read_text(encoding="utf-8"))["actions"]
        report = (ROOT / "report/final-report.md").read_text(encoding="utf-8")
        for claim in claims:
            self.assertEqual(claim["status"], evidence[claim["evidence_id"]]["status"])
            self.assertIn(f"- [{claim['claim_id']}] {claim['canonical_claim_text']}", report)
        valid_refs = set(evidence) | uncertainties
        for action in actions:
            self.assertTrue(set(action["reference_ids"]).issubset(valid_refs))
            self.assertIn(f"- [{action['action_id']}] {action['action_type']}: {','.join(action['reference_ids'])}", report)


if __name__ == "__main__":
    unittest.main()
