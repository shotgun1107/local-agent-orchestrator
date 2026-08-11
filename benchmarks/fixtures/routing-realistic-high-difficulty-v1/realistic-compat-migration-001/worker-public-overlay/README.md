# Repository-wide compatibility migration

Extend the existing single-stage routing implementation with the public S2
stage contract while preserving the S1 lifecycle, artifact, and export
meanings. Work through `benchmark-run.yaml` in dependency order.

Authoritative public requirements are under `profile-r/requirements/`.
`benchmark_checks/` and `.orchestrator/` are protected challenge files and
must not be modified. The checks intentionally cover only public contracts;
terminal evaluation uses a separate deterministic property checker.
