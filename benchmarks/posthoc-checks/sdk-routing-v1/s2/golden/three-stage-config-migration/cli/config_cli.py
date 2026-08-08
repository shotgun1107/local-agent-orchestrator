from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from runtime.parser import parse
from runtime.serializer import serialize
from schema.errors import DuplicateKeyError, InvalidTypeError, UnknownKeyError, UnknownVersionError


CONTRACT_ERRORS = (UnknownVersionError, DuplicateKeyError, UnknownKeyError, InvalidTypeError)


def main(argv: Sequence[str]) -> int:
    try:
        if len(argv) != 1:
            raise InvalidTypeError("one input path is required")
        payload = Path(argv[0]).read_text(encoding="utf-8")
        print(serialize(parse(payload)))
        return 0
    except CONTRACT_ERRORS as exc:
        print(json.dumps({"error": {"kind": type(exc).__name__}}, sort_keys=True, separators=(",", ":")))
        return 2
