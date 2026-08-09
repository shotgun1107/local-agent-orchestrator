import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AlternativeContractTest(unittest.TestCase):
    def test_fan_in_is_preserved(self):
        groups = {item["group_id"] for item in json.loads((ROOT / "timeline/conflict-groups.json").read_text(encoding="utf-8"))["groups"]}
        uncertainties = {item["uncertainty_id"] for item in json.loads((ROOT / "analysis/uncertainties.json").read_text(encoding="utf-8"))["uncertainties"]}
        hypotheses = json.loads((ROOT / "analysis/hypotheses.json").read_text(encoding="utf-8"))["hypotheses"]
        alternatives = json.loads((ROOT / "analysis/alternative-matrix.json").read_text(encoding="utf-8"))["alternatives"]
        self.assertEqual(set().union(*(set(item["conflict_group_ids"]) for item in hypotheses)), groups)
        self.assertEqual(set().union(*(set(item["uncertainty_ids"]) for item in hypotheses)), uncertainties)
        hypothesis_ids = {item["hypothesis_id"] for item in hypotheses}
        self.assertEqual(set().union(*(set(item["hypothesis_ids"]) for item in alternatives)), hypothesis_ids)


if __name__ == "__main__":
    unittest.main()
