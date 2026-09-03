"""Deterministic command-line adapter for configuration normalization."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TextIO

from runtime.parser import parse_config
from schema.errors import (
    ConfigParseError,
    ConfigValidationError,
    MigrationError,
    UnsupportedVersionError,
)

PUBLIC_ERRORS = (
    ConfigParseError,
    ConfigValidationError,
    UnsupportedVersionError,
    MigrationError,
)


def _write(payload: object, stream: TextIO) -> None:
    stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


def run(source: str | bytes | bytearray, stdout: TextIO = sys.stdout) -> int:
    """Normalize source and write one deterministic result object."""
    try:
        config = parse_config(source)
    except PUBLIC_ERRORS as exc:
        _write(
            {"error": {"code": type(exc).__name__, "message": str(exc)}, "ok": False},
            stdout,
        )
        return 2
    _write({"config": config, "ok": True}, stdout)
    return 0


def main(argv: list[str] | None = None, stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout) -> int:
    """Read one file (or stdin for '-') and produce one JSON result line."""
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        _write({"error": {"code": "UsageError", "message": "expected exactly one input"}, "ok": False}, stdout)
        return 2
    try:
        source = stdin.read() if args[0] == "-" else Path(args[0]).read_bytes()
    except OSError:
        _write({"error": {"code": "InputError", "message": "could not read input"}, "ok": False}, stdout)
        return 3
    return run(source, stdout)


if __name__ == "__main__":
    raise SystemExit(main())
