from __future__ import annotations

import contextlib
import io
import inspect
import json
import tempfile
import unittest
from pathlib import Path


class IntegrationTest(unittest.TestCase):
    def test_round_trip_and_cli(self) -> None:
        from cli.config_cli import main
        from runtime.parser import parse
        from runtime.serializer import serialize

        current = json.loads(Path("inputs/current.json").read_text(encoding="utf-8"))
        self.assertEqual(parse(serialize(parse(current))), current)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(["inputs/current.json"])
        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue(), serialize(current) + "\n")
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(list(inspect.signature(serialize).parameters), ["mapping"])
        self.assertEqual(list(inspect.signature(main).parameters), ["argv"])

    def test_cli_contract_error_and_exact_implementation_files(self) -> None:
        from cli.config_cli import main

        with tempfile.TemporaryDirectory() as directory:
            invalid = Path(directory) / "invalid.json"
            invalid.write_text('{"version":9}', encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = main([str(invalid)])
        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), '{"error":{"kind":"UnknownVersionError"}}\n')
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(
            sorted(
                str(path).replace("\\", "/")
                for pattern in ("schema/*.py", "migration/*.py", "runtime/*.py", "cli/*.py")
                for path in Path(".").glob(pattern)
                if path.name != "__init__.py"
            ),
            [
                "cli/config_cli.py",
                "migration/legacy.py",
                "runtime/parser.py",
                "runtime/serializer.py",
                "schema/errors.py",
                "schema/model.py",
            ],
        )


if __name__ == "__main__":
    unittest.main()
