from collections.abc import Mapping

from schema.errors import AliasConflictError, UnknownFieldError
from schema.model import ALIASES, validate


def migrate(payload):
    if not isinstance(payload, Mapping):
        raise UnknownFieldError("payload must be a mapping")
    value = dict(payload)
    for alias, canonical in ALIASES.items():
        if alias in value and canonical in value:
            raise AliasConflictError(alias)
        if alias in value:
            value[canonical] = value.pop(alias)
    value.setdefault("version", 2)
    return validate(value)
