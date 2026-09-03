# Three-stage incident analysis fixture

This self-contained fixture turns three partially conflicting incident sources
into an evidence ledger, a timeline, and a report without erasing uncertainty.
The public contract is in `spec/report-contract.md`; stable markers in the
source documents are the authority for each evidence record.

The three Tasks are serial. T1 creates the evidence and uncertainty ledgers,
T2 derives sourced events and hypotheses, and T3 creates structured claims and
actions before rendering the final report. Their seven implementation outputs
are `analysis/evidence-ledger.json`, `analysis/uncertainties.json`,
`timeline/events.json`, `timeline/hypotheses.json`, `report/claims.json`,
`report/action-plan.json`, and `report/final-report.md`.

Run all developer checks from this directory with:

```text
python -m pytest -q -p no:cacheprovider benchmark_checks
```
