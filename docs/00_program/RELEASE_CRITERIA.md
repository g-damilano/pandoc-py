# Release criteria

A milestone is accepted only when all of the following are true:

1. The targeted capability rows exist and are up to date.
2. The Python implementation exists for the declared scope.
3. Verification exists for the declared scope.
4. Smoke verification passes for the declared scope.
5. Standard or extended corpus thresholds are met when required by the milestone.
6. Remaining mismatches are explicitly logged as divergences.
7. No silent failures remain outside the trackers.

## Milestone classes

### Slice-complete
- feature family implemented
- smoke verified
- divergences logged

### Track-complete
- capability family implemented
- standard corpus verified
- no high-severity open divergence inside the declared boundary

### Release-candidate
- release scope frozen
- release criteria file checked
- verification dashboard updated
- risk register reviewed
- decision log reviewed for open architectural debt
