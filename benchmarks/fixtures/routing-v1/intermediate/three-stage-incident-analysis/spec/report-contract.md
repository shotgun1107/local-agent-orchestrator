# Public incident report contract

All JSON documents are objects with one top-level array named after their record
type. Records must use exactly the fields below. Every ID is a non-empty ASCII
string, and every ID array is sorted lexicographically.

- `analysis/evidence-ledger.json`: `evidence_id`, `source_id`, `locator`,
  `exact_excerpt`, `topic_id`, `observation_status`, `canonical_claim_text`.
  `locator` has integer `line_start` and `line_end`. Status is one of
  `observed`, `reported`, or `derived`.
- `analysis/uncertainties.json`: `uncertainty_id`, `evidence_ids`, `source_ids`,
  `next_action`.
- `timeline/events.json`: `event_id`, `status`, `evidence_ids`,
  `uncertainty_ids`. Status is `confirmed`, `conflicting`, or `uncertain`.
- `timeline/hypotheses.json`: `hypothesis_id`, `status`, `evidence_ids`,
  `uncertainty_ids`. Status is exactly `candidate`.
- `report/claims.json`: `claim_id`, `evidence_id`, `status`,
  `canonical_claim_text`. Status is `confirmed` or `conflicting`.
- `report/action-plan.json`: `action_id`, `action_type`, `reference_ids`.
  Action type is `verify` or `mitigate`.

The final report contains exactly these headings in this order: `확인된 사실`,
`상충`, `미확인`, `권고`. There is no prose outside the sections.

- confirmed/conflicting: `- [<claim_id>] <canonical_claim_text>`
- uncertainty: `- [<uncertainty_id>] <next_action>`
- action: `- [<action_id>] <verify|mitigate>: <comma-separated-reference_ids>`

The public catalog is the complete topic universe. A conflicting topic must
retain the declared number of distinct sources through the ledger, timeline, and
claim index. The post-hoc checker validates relationships and source locators; it
does not compare the output to a hidden answer string.
