from __future__ import annotations

import json
import inspect
import unittest
from pathlib import Path


class MigrationParseTest(unittest.TestCase):
    def test_legacy_migrates_and_current_parses(self) -> None:
        from migration.legacy import migrate
        from runtime.parser import parse

        legacy = json.loads(Path("inputs/legacy.json").read_text(encoding="utf-8"))
        current = json.loads(Path("inputs/current.json").read_text(encoding="utf-8"))
        self.assertEqual(migrate(legacy), current)
        self.assertEqual(parse(current), current)
        self.assertEqual(list(inspect.signature(migrate).parameters), ["mapping"])
        self.assertEqual(list(inspect.signature(parse).parameters), ["payload"])


if __name__ == "__main__":
    unittest.main()
