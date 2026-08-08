from __future__ import annotations

import json
from collections.abc import Mapping

from migration.legacy import migrate
from schema.errors import InvalidTypeError


def parse(payload: Mapping[str, object] | str) -> dict[str, object]:
    if isinstance(payload, str):
        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise InvalidTypeError("payload") from exc
        if not isinstance(decoded, dict):
            raise InvalidTypeError("payload")
        payload = decoded
    if not isinstance(payload, Mapping):
        raise InvalidTypeError("payload")
    return migrate(payload)
