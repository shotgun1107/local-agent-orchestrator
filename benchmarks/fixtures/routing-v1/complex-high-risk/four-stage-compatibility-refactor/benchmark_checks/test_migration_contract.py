import json
import unittest
from pathlib import Path

from migration.upgrade import migrate


ROOT = Path(__file__).resolve().parents[1]


class MigrationContractTest(unittest.TestCase):
    def test_cases_and_idempotence(self):
        cases = json.loads((ROOT / "contract/compatibility-cases.json").read_text(encoding="utf-8"))["cases"]
        for case in cases:
            original = dict(case["old_payload"])
            once = migrate(original)
            self.assertEqual(once, case["canonical"])
            self.assertEqual(migrate(once), once)
            self.assertEqual(original, case["old_payload"])


if __name__ == "__main__":
    unittest.main()
