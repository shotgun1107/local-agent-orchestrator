# Public runtime-boundary repair contract

The Worker may rely only on the base source, the fourteen public observations,
and this contract. Observation order is not proof of a cause.

Required invariants:

1. The selected named permission profile is proven by direction-aware SDK
   request, response, and notification evidence. Legacy sandbox arguments are
   absent and model-turn request count remains zero.
2. Effective configuration, readiness, runtime identity, and every helper
   command are recomputed from recorded evidence rather than trusted booleans.
3. Declared workspace positive read/write behavior remains available and is
   bound to the identity that actually executes the helper command.
4. Worker reads and writes to both logical Controller-only roots fail in all
   public direct, parent, child, and link/path cases. Protected root identity
   remains unchanged before and after execution.
5. Child processes preserve the same access boundary. Protected content is not
   exposed through stdout, stderr, environment, arguments, or enumeration.
6. Temporary link/path entries and frozen command identity are unchanged after
   each probe, whether a protected target is readable or not.
7. A blocked state operation returns only fields and value ranges allowed by
   the public typed Schema. Controller-only preconditions and postconditions
   remain the authority for protected state identity.
8. The verifier recomputes all probe results and exact four-file bundle
   identity. Structured incident claims may be confirmed or excluded only when
   their cited public observations permit that transition.

For Tasks I02 through I08, record chosen implementation symbols, regression
test names, changed paths, and public evidence IDs in
`profile-i/work/task-contracts.json`. These declarations are public milestones,
not terminal proof.
