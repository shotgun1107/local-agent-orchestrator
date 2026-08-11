from __future__ import annotations

import unittest

from src.config import parse_config


class ParseConfigAcceptanceTests(unittest.TestCase):
    def test_normalizes_keys_without_mutating_input(self) -> None:
        raw = {" Timeout-Seconds ": 30, "MAX-RETRIES": 2}

        parsed = parse_config(raw)

        self.assertEqual(parsed, {"timeout_seconds": 30, "max_retries": 2})
        self.assertEqual(raw, {" Timeout-Seconds ": 30, "MAX-RETRIES": 2})
        self.assertIsNot(parsed, raw)

    def test_rejects_unknown_key_after_normalization(self) -> None:
        with self.assertRaises(ValueError):
            parse_config({"timeout-seconds": 30, "debug-mode": True})

    def test_rejects_duplicate_key_after_normalization(self) -> None:
        with self.assertRaises(ValueError):
            parse_config({"MAX-RETRIES": 1, "max_retries": 2})


if __name__ == "__main__":
    unittest.main()
