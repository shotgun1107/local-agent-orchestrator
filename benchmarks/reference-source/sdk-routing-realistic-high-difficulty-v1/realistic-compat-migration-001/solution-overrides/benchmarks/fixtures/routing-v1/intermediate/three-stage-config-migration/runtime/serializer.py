"""Canonical JSON serialization."""

from __future__ import annotations

import json
from typing import Any

from migration.legacy import migrate_config


def serialize_config(value: Any) -> str:
    """Validate/migrate a value and emit canonical JSON plus one newline."""
    current = migrate_config(value)
    return json.dumps(
        current,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ) + "\n"


__all__ = ["serialize_config"]
