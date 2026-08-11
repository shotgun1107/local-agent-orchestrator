# Public S1 to S2 migration contract

## Preservation boundary

- Keep the existing S1 stage ID, cell order, 12-turn ceiling, route-decision
  prohibition, Measurement meaning, seal verification, and export kind strings.
- Extend the shared suite and lifecycle. Do not create an S2-only Controller,
  state machine, Measurement, seal, Judge, runtime, or adapter implementation.
- The stage discriminator must reject S1 bytes as S2 and S2 bytes as S1.
- Every source, fixture, stage, order, and budget identity used by a Plan must
  remain bound through status, export, and verification.

## S2 public constants

- stage ID: `s2-intermediate`
- purpose: `profile_routing`
- variants: `c2`, `b1`
- profiles: `three-stage-config-migration`, `three-stage-incident-analysis`
- initial cell order: config C2, config B1, incident B1, incident C2
- base turns: 12; B1 retry/resume reserve: 3; absolute maximum: 15
- route decisions are allowed only for S2 and only through structured policy.

## Fixture contracts

The config fixture has three serial Tasks and exactly six implementation
outputs across `schema`, `migration`, `runtime`, and `cli`. It exposes v1/v2
validation, idempotent migration, canonical parsing/serialization, four public
`ValueError` subclasses, and deterministic CLI success/error JSON.

The incident fixture has three serial Tasks and exactly seven outputs across
`analysis`, `timeline`, and `report`. Source conflicts and uncertainty must be
preserved through IDs. Its report has the four ordered sections `확인된 사실`,
`상충`, `미확인`, and `권고`; claims and actions are rendered only from the
structured artifacts.

## Lifecycle and export

- Reuse create/status/run-next, Judge, seal, and export paths for both stages.
- B1 retry and resume consume an independent three-turn reserve; unused or
  early-terminated base turns are never recycled into that reserve.
- A normal Task failure is preserved and the paired Variant still runs.
  Identity, scope, secret, seal, or infrastructure failure stops before the
  next model turn.
- Export and verification must bind the exact stage discriminator and preserve
  the old S1 bytes and meanings.

## Operator contract

`profile-r/work/operator-contract.json` is the machine-readable authority for
commands, argv, preconditions, allowed source/terminal states, success and
failure codes, stop rules, implementation symbols, and public schemas. README
prose may explain it but may not define a different relation.
