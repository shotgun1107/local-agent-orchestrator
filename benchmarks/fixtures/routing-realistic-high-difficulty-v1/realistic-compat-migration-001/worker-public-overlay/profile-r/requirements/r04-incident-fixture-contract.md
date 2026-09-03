# R04 incident fixture contract

This file is the normative R04 contract. It is part of the initial Worker input,
is outside R04's write scope, and cannot be replaced by fixture-local documentation
or Worker-authored developer tests.

The incident fixture uses plural reference arrays throughout.

- Every claim has a non-empty, unique `evidence_ids` array. There is no singular
  `evidence_id` claim field.
- Event and hypothesis references use `evidence_ids` and `uncertainty_ids` arrays.
- Claim `event_ids` and `uncertainty_ids`, and action `claim_ids` and
  `uncertainty_ids`, refer only to declared public IDs.
- References preserve provenance transitively from sources through evidence,
  timeline, claims, actions, and the deterministic final report.
- The final report has exactly the ordered sections `확인된 사실`, `상충`, `미확인`,
  and `권고` and projects stored claims and actions without extra narrative.

The fixed public `r04_contract` checker directly validates these relationships.
Files under the fixture's `benchmark_checks/` directory are supplemental developer
tests and are never the sole evidence for R04 success.
