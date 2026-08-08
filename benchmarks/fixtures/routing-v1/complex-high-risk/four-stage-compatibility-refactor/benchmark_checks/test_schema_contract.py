import json
import unittest
from pathlib import Path

from schema import errors, model


ROOT = Path(__file__).resolve().parents[1]


class SchemaContractTest(unittest.TestCase):
    def test_public_identity(self):
        api = json.loads((ROOT / "contract/public-api.json").read_text(encoding="utf-8"))
        policy = json.loads((ROOT / "contract/deprecation-policy.json").read_text(encoding="utf-8"))
        self.assertEqual(list(model.PUBLIC_FIELDS), api["canonical_fields"])
        self.assertEqual(model.ALIASES, policy["allowed_aliases"])
        self.assertEqual(errors.ERROR_CODES, api["error_codes"])


if __name__ == "__main__":
    unittest.main()
