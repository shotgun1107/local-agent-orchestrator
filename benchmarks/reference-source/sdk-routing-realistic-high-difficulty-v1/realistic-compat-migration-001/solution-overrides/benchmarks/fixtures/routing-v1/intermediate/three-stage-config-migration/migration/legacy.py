"""Idempotent version 1 to version 2 migration."""

from __future__ import annotations

from typing import Any

from schema.errors import MigrationError
from schema.model import validate_config, validate_v1, validate_v2


def migrate_v1_to_v2(value: Any) -> dict[str, Any]:
    """Convert a valid v1 value into the canonical v2 representation."""
    legacy = validate_v1(value)
    migrated = {
        "schema_version": 2,
        "service": {"name": legacy["service"], "endpoint": legacy["endpoint"]},
        "request": {
            "timeout_seconds": legacy["timeout"],
            "max_retries": legacy["retries"],
        },
        "features": {"enabled": legacy["features"]},
    }
    current = validate_v2(migrated)
    if (
        current["service"]["name"] != legacy["service"]
        or current["service"]["endpoint"] != legacy["endpoint"]
        or current["request"]["timeout_seconds"] != legacy["timeout"]
        or current["request"]["max_retries"] != legacy["retries"]
        or current["features"]["enabled"] != legacy["features"]
    ):
        raise MigrationError("migration did not preserve configuration values")
    return current


def migrate_config(value: Any) -> dict[str, Any]:
    """Return canonical v2 for either supported input version."""
    validated = validate_config(value)
    if validated["schema_version"] == 1:
        return migrate_v1_to_v2(validated)
    return validate_v2(validated)


__all__ = ["migrate_config", "migrate_v1_to_v2"]
