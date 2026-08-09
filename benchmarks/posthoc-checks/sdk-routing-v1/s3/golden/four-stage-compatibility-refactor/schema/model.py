from collections.abc import Mapping

from schema.errors import InvalidModeError, MissingFieldError, UnknownFieldError


PUBLIC_FIELDS = ("endpoint", "max_retries", "timeout_seconds", "mode", "version")
ALIASES = {"url": "endpoint", "retries": "max_retries", "timeout": "timeout_seconds"}


def validate(payload):
    if not isinstance(payload, Mapping):
        raise UnknownFieldError("payload must be a mapping")
    unknown = set(payload) - set(PUBLIC_FIELDS)
    if unknown:
        raise UnknownFieldError(sorted(unknown)[0])
    missing = set(PUBLIC_FIELDS) - set(payload)
    if missing:
        raise MissingFieldError(sorted(missing)[0])
    if payload["mode"] not in {"safe", "fast"}:
        raise InvalidModeError(str(payload["mode"]))
    if payload["version"] != 2:
        raise UnknownFieldError("version")
    for name in ("max_retries", "timeout_seconds"):
        value = payload[name]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise UnknownFieldError(name)
    if not isinstance(payload["endpoint"], str) or not payload["endpoint"]:
        raise MissingFieldError("endpoint")
    return {name: payload[name] for name in PUBLIC_FIELDS}
