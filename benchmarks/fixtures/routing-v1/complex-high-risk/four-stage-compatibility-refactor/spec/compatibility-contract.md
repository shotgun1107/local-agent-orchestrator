# Compatibility contract

The canonical v2 object has exactly `endpoint`, `max_retries`, `timeout_seconds`, `mode`, and `version` in that order. `version` is the integer `2`; retries and timeout are non-negative integers; mode is `safe` or `fast`.

The aliases in `contract/deprecation-policy.json` are accepted only when the matching canonical field is absent. Unknown fields, type coercion, and alias/canonical collisions fail with the public error codes. Migration does not mutate its input and is idempotent. Parsing old or new payloads yields the canonical object, serialization emits the canonical object, and the full migration/parse/serialize pipeline is idempotent.

The legacy API and CLI preserve the same success value. CLI failures are `{"ok": false, "error_code": CODE}`.
