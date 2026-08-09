import json
import unittest
from pathlib import Path

from integration.adapter import normalize
from runtime.parser import parse
from runtime.serializer import serialize


ROOT = Path(__file__).resolve().parents[1]


class IntegrationContractTest(unittest.TestCase):
    def test_parse_serialize_and_adapter(self):
        cases = json.loads((ROOT / "contract/compatibility-cases.json").read_text(encoding="utf-8"))["cases"]
        for case in cases:
            self.assertEqual(parse(case["old_payload"]), case["canonical"])
            self.assertEqual(parse(case["new_payload"]), case["canonical"])
            self.assertEqual(serialize(case["canonical"]), case["serialization"])
            self.assertEqual(normalize(case["old_payload"]), case["canonical"])


if __name__ == "__main__":
    unittest.main()
