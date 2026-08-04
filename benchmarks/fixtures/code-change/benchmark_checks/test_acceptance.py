import unittest

from src.config import parse_config


class ConfigAcceptanceTest(unittest.TestCase):
    def test_unknown_top_level_key_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_config({"name": "ok", "unknown": True})


if __name__ == "__main__":
    unittest.main()
