# Public incident report contract

## Identity and provenance

All artifacts use `schema_version` 1 and incident ID
`INC-2025-02-14-CHECKOUT`. Source IDs, evidence IDs, uncertainty IDs, event
IDs, hypothesis IDs, claim IDs, and action IDs are stable public identities.
Every evidence item names one source path and one bracketed marker that occurs
exactly once in that source. Its statement must reproduce the source text
following the marker exactly. Derived artifacts may refer only to declared
IDs; references are non-empty, unique, and preserve provenance transitively.

The topic catalog declares whether a topic is `fact`, `conflict`, or
`uncertainty`. A conflict retains at least two disagreeing evidence items from
different sources. An uncertainty remains open and retains all evidence IDs
that motivate it. Conflicts and open questions must never be silently promoted
to confirmed facts.

## Evidence and timeline

`analysis/evidence-ledger.json` contains `evidence`; each item has `evidence_id`,
`topic_id`, `source_id`, `source_path`, `source_marker`, `statement`, and
`recorded_at`. `analysis/uncertainties.json` contains open questions with
`uncertainty_id`, `topic_id`, `question`, `reason`, `status`, and
`evidence_ids`.

`timeline/events.json` contains chronological `events`. Each has `event_id`,
`occurred_at`, `summary`, `status`, and `evidence_ids`; disputed events also
name `uncertainty_ids`. `timeline/hypotheses.json` contains hypotheses with a
non-confirmed `status`, distinct supporting and conflicting evidence lists,
and the open uncertainty IDs that prevent a causal conclusion.

## Report

`report/claims.json` stores claims for the first three report sections. Each
claim has `claim_id`, `section`, `text`, `evidence_ids`, `event_ids`, and
`uncertainty_ids`. Confirmed-fact claims have no uncertainty references;
conflict and unconfirmed claims have at least one. `report/action-plan.json`
stores ordered actions with `action_id`, `priority`, `text`, `claim_ids`, and
`uncertainty_ids`.

`report/final-report.md` is a deterministic projection, not an independent
narrative. It starts with `# INC-2025-02-14-CHECKOUT`, then contains exactly
the four level-two sections `확인된 사실`, `상충`, `미확인`, and `권고` in that
order. Claims appear in stored order as `- [CLAIM_ID] TEXT`; actions appear in
priority order as `- [ACTION_ID] TEXT`. No other prose is permitted.
