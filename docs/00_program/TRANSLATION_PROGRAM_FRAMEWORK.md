# Translation program framework

This document defines the operating scaffold for a disciplined Haskell → Python translation program.

It is intentionally process-heavy: the goal is reproducible, auditable equivalence—not ad hoc conversion speed.

## 1) Program architecture

The program runs on six connected layers:

1. **Roadmap layer**: declares milestones and tranche order (`docs/00_program/ROADMAP.md`).
2. **Backlog layer**: enumerates capability rows and their current maturity (`trackers/CAPABILITY_MATRIX.csv`, `docs/02_tracking/BACKLOG.md`).
3. **Execution layer**: limits each iteration to one coherent work packet (`trackers/NEXT_ITERATION.md`, `trackers/WORK_PACKET_TEMPLATE.md`).
4. **Implementation history layer**: logs what landed and why (`trackers/IMPLEMENTATION_LOG.md`, `docs/02_tracking/DECISION_LOG.md`).
5. **Verification layer**: compares Python outputs against the Haskell oracle (`docs/03_contracts/VERIFICATION_CONTRACT.md`, `scripts/run_differential.py`).
6. **Control/index layer**: exposes current truth to humans and AI before any edits (`INDEX.md`, `PORT_INDEX.yaml`, `trackers/ITERATION_INDEX.yaml`).

## 2) Completion contract (non-negotiable)

A feature is complete only when all of the following are true:

- Python implementation exists and is mapped to a capability row.
- Equivalent behavior exists in the Haskell reference scope.
- Both implementations ran on identical inputs.
- Outputs were compared with a declared comparator level.
- Any mismatch was either fixed in-round or logged as divergence/blocker.

If any bullet is missing, the row must stay below verified states.

## 3) Capability state taxonomy

Use these status classes across planning and reporting:

- **Missing**: `not_started`, `mapped_only`
- **Partially developed**: `skeleton_only`, `partially_implemented`
- **Pending verification**: `implemented_unverified`
- **Verified**: `verified_smoke`, `verified_standard`, `verified_extended`, `done`
- **Constrained**: `known_divergence`, `blocked`, `deferred`
- **Needs refinement**: explicit row note `refinement_required` with owner + exit criteria

`refinement_required` is a control note, not a terminal state.

## 4) Verification and validation system

### 4.1 Required run shape

Each verification packet must declare and archive:

- input fixture source
- oracle invocation (Pandoc/Haskell-backed route)
- Python invocation
- comparator profile
- normalization profile (if non-byte compare)
- report artifact path
- pass/fail outcome and tracker links

### 4.2 Comparator policy

- Prefer strict byte comparison when output is canonical.
- Use structured equality for JSON/native-like outputs.
- Use semantic normalization only when justified and documented.
- For markdown/commonmark writers, use reparse-to-JSON semantic compare where canonical text is unstable.

### 4.3 Failure handling

Failing comparisons must end in one of two outcomes only:

1. fixed and rerun in the same iteration, or
2. explicit entry in `docs/02_tracking/DIVERGENCE_LOG.md` with bounded scope and next action.

## 5) Iteration workflow (AI-safe)

At the start of every iteration:

1. Read `trackers/ITERATION_INDEX.yaml`.
2. Confirm current packet in `trackers/NEXT_ITERATION.md`.
3. Execute only one coherent packet unless explicitly widened.

During execution:

4. Implement with fail-closed scope boundaries.
5. Run declared verification rails.
6. Log divergences/risks/decisions immediately.

Before close:

7. Update capability rows and status counts.
8. Update implementation + verification logs.
9. Refresh `trackers/ITERATION_INDEX.yaml` and run `python scripts/validate_control_plane.py`.

## 6) Auditable deliverables per iteration

Every completed packet should leave a trace bundle containing:

- changed code
- admitted capability rows
- evidence report references
- implementation log entry
- verification status update
- next packet declaration
- divergence entries (if any)
- control-plane validation result

This is the minimum record required for cumulative, non-random progress.
