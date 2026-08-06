from __future__ import annotations

import unittest


class NormalizeKeyTests(unittest.TestCase):
    def test_normalizes_supported_spelling(self) -> None:
        from src.normalization import normalize_key

        self.assertEqual(normalize_key("  MAX-Retries "), "max_retries")
        self.assertEqual(normalize_key("timeout_seconds"), "timeout_seconds")

    def test_rejects_empty_and_non_string_values(self) -> None:
        from src.normalization import normalize_key

        for value in ("   ", None, 3):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_key(value)


if __name__ == "__main__":
    unittest.main()
