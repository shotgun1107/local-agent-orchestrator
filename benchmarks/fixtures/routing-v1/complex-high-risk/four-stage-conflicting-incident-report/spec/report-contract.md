# Incident report contract

Evidence records contain `evidence_id`, `source_id`, `topic_id`, `status`, `locator`, `exact_excerpt`, and `canonical_claim_text`. Locators are one-based inclusive source line ranges and excerpts are byte-derived text. Status is `confirmed`, `conflicting`, or `uncertain`.

Every catalog topic must meet its distinct-source minimum. Conflict groups preserve the exact catalog topic set and all corresponding evidence. Every conflict group and uncertainty is referenced by at least one hypothesis; every hypothesis appears in an alternative row.

Claims preserve their evidence status. Actions use `verify` or `mitigate` and reference only evidence or uncertainty IDs. `final-report.md` has exactly these headings in this order: `확인된 사실`, `상충`, `미확인`, `권고`. Claim lines use `- [ID] canonical text`; action lines use `- [ID] TYPE: comma-separated-reference-ids`.
