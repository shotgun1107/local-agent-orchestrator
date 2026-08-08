from __future__ import annotations

from collections.abc import Mapping

from .errors import DuplicateKeyError, InvalidTypeError, UnknownKeyError, UnknownVersionError


def _normalize(mapping: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(mapping, Mapping):
        raise InvalidTypeError("configuration must be a mapping")
    normalized: dict[str, object] = {}
    for key, value in mapping.items():
        if not isinstance(key, str):
            raise InvalidTypeError("configuration keys must be strings")
        canonical = key.strip().lower().replace("-", "_")
        if canonical in normalized:
            raise DuplicateKeyError(canonical)
        normalized[canonical] = value
    return normalized


def _integer(value: object, name: str) -> int:
    if type(value) is not int or value < 0:
        raise InvalidTypeError(name)
    return value


def validate(mapping: Mapping[str, object]) -> dict[str, object]:
    normalized = _normalize(mapping)
    version = normalized.get("version")
    if type(version) is not int:
        raise InvalidTypeError("version")
    if version not in {1, 2}:
        raise UnknownVersionError(str(version))
    allowed = (
        {"version", "timeout", "retries", "endpoint"}
        if version == 1
        else {"version", "timeout_seconds", "max_retries", "endpoint"}
    )
    unknown = set(normalized) - allowed
    if unknown:
        raise UnknownKeyError(sorted(unknown)[0])
    if set(normalized) != allowed:
        raise InvalidTypeError("missing required key")
    endpoint = normalized["endpoint"]
    if not isinstance(endpoint, str):
        raise InvalidTypeError("endpoint")
    if version == 1:
        return {
            "endpoint": endpoint,
            "retries": _integer(normalized["retries"], "retries"),
            "timeout": _integer(normalized["timeout"], "timeout"),
            "version": 1,
        }
    return {
        "endpoint": endpoint,
        "max_retries": _integer(normalized["max_retries"], "max_retries"),
        "timeout_seconds": _integer(normalized["timeout_seconds"], "timeout_seconds"),
        "version": 2,
    }
