# R03 configuration fixture contract

This file is the normative R03 contract. It is part of the initial Worker input,
is outside R03's write scope, and cannot be replaced by fixture-local documentation
or Worker-authored developer tests.

The configuration fixture must implement the following public behavior.

- `runtime.parser.parse_config` accepts UTF-8 `str`, `bytes`, or `bytearray`,
  rejects duplicate keys and non-standard numeric constants, and returns a detached
  canonical version-2 dictionary.
- `runtime.serializer.serialize_config` accepts either supported version and emits
  sorted compact UTF-8 JSON with exactly one trailing newline.
- Parsing and serialization are stable under round trips.
- `cli.config_cli.main([INPUT])` exits 0 and emits exactly one sorted compact JSON
  object `{"config": CANONICAL_CONFIG, "ok": true}` followed by one newline.
- Public configuration failures emit one stable JSON error object and exit 2.
- Input I/O failure emits `InputError` / `could not read input` and exits 3.

The fixed public `r03_contract` checker directly executes these behaviors. Files
under the fixture's `benchmark_checks/` directory are supplemental developer tests
and are never the sole evidence for R03 success.
