# Public config contract

The implementation must expose exactly these callables:

- `schema.model.validate(mapping: Mapping[str, object]) -> dict[str, object]`
- `migration.legacy.migrate(mapping: Mapping[str, object]) -> dict[str, object]`
- `runtime.parser.parse(payload: Mapping[str, object] | str) -> dict[str, object]`
- `runtime.serializer.serialize(mapping: Mapping[str, object]) -> str`
- `cli.config_cli.main(argv: Sequence[str]) -> int`

`schema.errors` must expose four `ValueError` subclasses:

- `UnknownVersionError`: version is not 1 or 2
- `DuplicateKeyError`: two input keys are equal after trim/lower/hyphen normalization
- `UnknownKeyError`: a normalized key is outside the version contract
- `InvalidTypeError`: version, timeout/retry, or endpoint has the wrong type

Version 1 keys are `version`, `timeout`, `retries`, `endpoint`. Version 2 keys are
`version`, `timeout_seconds`, `max_retries`, `endpoint`. Migration maps v1 to v2,
accepts v2 idempotently, and never mutates its input. Parse accepts either a mapping
or JSON object text and returns a validated v2 mapping. Serialization uses UTF-8
JSON semantics, sorted keys, no insignificant whitespace, and no trailing newline.

CLI success: exit 0, one canonical v2 JSON line on stdout, empty stderr.
CLI contract failure: exit 2, `{"error":{"kind":"<ErrorClassName>"}}` as one
canonical JSON line on stdout, empty stderr.
