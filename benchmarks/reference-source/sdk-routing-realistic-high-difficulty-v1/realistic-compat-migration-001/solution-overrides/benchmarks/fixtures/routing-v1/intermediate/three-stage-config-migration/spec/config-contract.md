# Public configuration contract

## Versions

A configuration is a JSON object with integer `schema_version`.  Version 1 has
exactly `schema_version`, `service`, `endpoint`, `timeout`, `retries`, and
`features`.  Version 2 has exactly `schema_version`, `service`, `request`, and
`features`.  Booleans never count as integers.  Unknown fields are rejected.

For v1, `service` and `endpoint` are non-empty strings, `endpoint` is an
absolute `http` or `https` URL, `timeout` is a positive integer, `retries` is a
non-negative integer, and `features` is a list of unique non-empty strings.
For v2, `service` contains exactly `name` and `endpoint`; `request` contains
exactly `timeout_seconds` and `max_retries`; and `features` contains exactly
`enabled`.  Their leaf constraints are the same as v1.

`validate_v1`, `validate_v2`, and `validate_config` return a detached,
canonical dictionary and never mutate their input.  Canonical feature names
are sorted lexicographically.  `validate_config` dispatches only versions 1
and 2.

## Errors

The four public errors are `ConfigParseError`, `ConfigValidationError`,
`UnsupportedVersionError`, and `MigrationError`.  Each is a direct
`ValueError` subclass.  Validation failures use `ConfigValidationError`;
missing or unsupported version discriminators use `UnsupportedVersionError`;
invalid JSON/text inputs use `ConfigParseError`; and a migration invariant
failure uses `MigrationError`.  Public error messages are stable and contain
no paths or exception reprs.

## Migration and runtime

`migrate_config` accepts either valid version.  It maps v1 to v2 and
canonicalizes v2, returning a fresh object.  Applying it repeatedly is
idempotent.  `migrate_v1_to_v2` is the strict v1 entry point.

`parse_config` accepts UTF-8 `str`, `bytes`, or `bytearray` JSON and returns a
canonical v2 dictionary.  JSON constants such as NaN and duplicate object keys
are rejected.  `serialize_config` accepts either version and emits canonical
UTF-8 JSON text: sorted keys, compact separators, no ASCII escaping, and one
trailing newline.  Therefore parsing and serialization are stable under
round trips.

## CLI

`python -m cli.config_cli INPUT` reads INPUT, or `-` for standard input.  It
writes exactly one compact, sorted JSON object plus a newline.  Success exits
0 with `{"config":...,"ok":true}`.  A public configuration error exits 2
with `{"error":{"code":ERROR_CLASS_NAME,"message":MESSAGE},"ok":false}`.
Unexpected I/O errors exit 3 with the fixed code and message
`InputError` / `could not read input`.  Errors are written to stdout so every
invocation has one machine-readable result stream.
