# Three-stage configuration migration fixture

This self-contained fixture models a serial migration from a legacy version 1
JSON configuration to the canonical version 2 representation.  The public
contract lives in `spec/config-contract.md`; `inputs/` contains one valid value
for each version, and `benchmark_checks/` contains the executable semantic
contract.

The three Tasks are deliberately ordered: T1 defines validation and the four
public errors, T2 adds an idempotent migration and canonical parser, and T3
adds serialization and a deterministic JSON CLI.  Their six implementation
outputs are `schema/errors.py`, `schema/model.py`, `migration/legacy.py`,
`runtime/parser.py`, `runtime/serializer.py`, and `cli/config_cli.py`.

Run all developer checks from this directory with:

```text
python -m pytest -q -p no:cacheprovider benchmark_checks
```
