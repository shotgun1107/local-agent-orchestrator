from __future__ import annotations

import unittest
import inspect
from pathlib import Path


class SchemaContractTest(unittest.TestCase):
    def test_public_schema_and_errors(self) -> None:
        from schema import errors
        from schema.model import validate

        for name in (
            "UnknownVersionError",
            "DuplicateKeyError",
            "UnknownKeyError",
            "InvalidTypeError",
        ):
            self.assertTrue(issubclass(getattr(errors, name), ValueError))
        self.assertEqual(
            validate(
                {
                    "version": 2,
                    "timeout_seconds": 30,
                    "max_retries": 3,
                    "endpoint": "https://service.invalid",
                }
            )["version"],
            2,
        )
        self.assertEqual(list(inspect.signature(validate).parameters), ["mapping"])
        self.assertEqual(
            sorted(
                path.as_posix()
                for path in Path("schema").glob("*.py")
                if path.name != "__init__.py"
            ),
            ["schema/errors.py", "schema/model.py"],
        )


if __name__ == "__main__":
    unittest.main()
