"""Dependency-free validation for configuration versions 1 and 2."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import urlsplit

from .errors import ConfigValidationError, UnsupportedVersionError


def _object(value: Any, label: str, keys: set[str]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ConfigValidationError(f"{label} must be an object")
    actual = set(value)
    if actual != keys:
        raise ConfigValidationError(f"{label} fields are invalid")
    return value


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigValidationError(f"{label} must be a non-empty string")
    return value


def _integer(value: Any, label: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ConfigValidationError(f"{label} must be an integer of at least {minimum}")
    return value


def _endpoint(value: Any) -> str:
    endpoint = _string(value, "endpoint")
    parsed = urlsplit(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ConfigValidationError("endpoint must be an absolute HTTP URL")
    return endpoint


def _features(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise ConfigValidationError("features must be a list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ConfigValidationError("features must contain non-empty strings")
    if len(set(value)) != len(value):
        raise ConfigValidationError("features must be unique")
    return sorted(value)


def validate_v1(value: Any) -> dict[str, Any]:
    """Validate and detach a version 1 configuration."""
    if not isinstance(value, Mapping):
        raise ConfigValidationError("configuration must be an object")
    if value.get("schema_version") != 1 or isinstance(value.get("schema_version"), bool):
        raise UnsupportedVersionError("schema_version must be 1")
    obj = _object(
        value,
        "configuration",
        {"schema_version", "service", "endpoint", "timeout", "retries", "features"},
    )
    return {
        "schema_version": 1,
        "service": _string(obj["service"], "service"),
        "endpoint": _endpoint(obj["endpoint"]),
        "timeout": _integer(obj["timeout"], "timeout", 1),
        "retries": _integer(obj["retries"], "retries", 0),
        "features": _features(obj["features"]),
    }


def validate_v2(value: Any) -> dict[str, Any]:
    """Validate and detach a version 2 configuration."""
    if not isinstance(value, Mapping):
        raise ConfigValidationError("configuration must be an object")
    if value.get("schema_version") != 2 or isinstance(value.get("schema_version"), bool):
        raise UnsupportedVersionError("schema_version must be 2")
    obj = _object(value, "configuration", {"schema_version", "service", "request", "features"})
    service = _object(obj["service"], "service", {"name", "endpoint"})
    request = _object(obj["request"], "request", {"timeout_seconds", "max_retries"})
    features = _object(obj["features"], "features", {"enabled"})
    return {
        "schema_version": 2,
        "service": {
            "name": _string(service["name"], "service.name"),
            "endpoint": _endpoint(service["endpoint"]),
        },
        "request": {
            "timeout_seconds": _integer(request["timeout_seconds"], "request.timeout_seconds", 1),
            "max_retries": _integer(request["max_retries"], "request.max_retries", 0),
        },
        "features": {"enabled": _features(features["enabled"])},
    }


def validate_config(value: Any) -> dict[str, Any]:
    """Validate a supported version without changing its version."""
    if not isinstance(value, Mapping):
        raise ConfigValidationError("configuration must be an object")
    version = value.get("schema_version")
    if isinstance(version, bool) or version not in (1, 2):
        raise UnsupportedVersionError("schema_version must be 1 or 2")
    return validate_v1(value) if version == 1 else validate_v2(value)


__all__ = ["validate_config", "validate_v1", "validate_v2"]
