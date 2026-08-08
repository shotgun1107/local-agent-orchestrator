import json
import unittest
from pathlib import Path

from cli.config_cli import run
from compat.legacy_api import load
from compat.roundtrip import roundtrip


ROOT = Path(__file__).resolve().parents[1]


class BackwardCompatibilityTest(unittest.TestCase):
    def test_success_and_failure_meanings(self):
        payload = json.loads((ROOT / "contract/compatibility-cases.json").read_text(encoding="utf-8"))
        for case in payload["cases"]:
            self.assertEqual(load(case["old_payload"]), case["canonical"])
            self.assertEqual(roundtrip(case["old_payload"]), case["serialization"])
            self.assertEqual(run(case["old_payload"]), {"ok": True, "value": case["canonical"]})
        for case in payload["invalid_cases"]:
            self.assertEqual(run(case["payload"]), {"ok": False, "error_code": case["error_code"]})


if __name__ == "__main__":
    unittest.main()
