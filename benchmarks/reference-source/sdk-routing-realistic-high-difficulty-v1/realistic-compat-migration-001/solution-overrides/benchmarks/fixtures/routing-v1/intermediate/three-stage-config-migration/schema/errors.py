"""Stable public errors for the configuration fixture."""


class ConfigParseError(ValueError):
    """The serialized input is not strict UTF-8 JSON."""


class ConfigValidationError(ValueError):
    """A known configuration version violates its schema."""


class UnsupportedVersionError(ValueError):
    """The configuration has no supported version discriminator."""


class MigrationError(ValueError):
    """A valid legacy value cannot preserve the migration invariant."""


__all__ = [
    "ConfigParseError",
    "ConfigValidationError",
    "UnsupportedVersionError",
    "MigrationError",
]
