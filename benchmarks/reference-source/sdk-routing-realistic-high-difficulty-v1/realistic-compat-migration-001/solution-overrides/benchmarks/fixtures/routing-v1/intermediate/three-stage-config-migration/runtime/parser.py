"""Strict JSON parsing into the canonical v2 model."""

from __future__ import annotations

import json
from typing import Any

from migration.legacy import migrate_config
from schema.errors import ConfigParseError


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ConfigParseError("JSON object keys must be unique")
        result[key] = value
    return result


def _invalid_constant(_value: str) -> None:
    raise ConfigParseError("JSON numeric constants are not supported")


def parse_config(source: str | bytes | bytearray) -> dict[str, Any]:
    """Parse strict JSON and return a detached canonical v2 dictionary."""
    if not isinstance(source, (str, bytes, bytearray)):
        raise ConfigParseError("configuration input must be JSON text")
    try:
        text = bytes(source).decode("utf-8") if isinstance(source, (bytes, bytearray)) else source
    except UnicodeDecodeError as exc:
        raise ConfigParseError("configuration input must be UTF-8") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_invalid_constant,
        )
    except ConfigParseError:
        raise
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ConfigParseError("configuration input must be valid JSON") from exc
    return migrate_config(value)


__all__ = ["parse_config"]
