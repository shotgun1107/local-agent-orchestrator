from __future__ import annotations

from collections.abc import Mapping

from schema.model import validate


def migrate(mapping: Mapping[str, object]) -> dict[str, object]:
    validated = validate(mapping)
    if validated["version"] == 2:
        return dict(validated)
    return {
        "endpoint": validated["endpoint"],
        "max_retries": validated["retries"],
        "timeout_seconds": validated["timeout"],
        "version": 2,
    }
