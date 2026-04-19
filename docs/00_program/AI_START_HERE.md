# AI start here

This file is the entrypoint for any new iteration.

## Mission

Port Pandoc from Haskell to Python **without losing behavioral traceability** and **without allowing implementation to outrun verification**.

## What you must preserve

- Pandoc remains the behavioral oracle.
- Progress is measured by verified capability slices.
- Every change must remain auditable.
- Every mismatch must become visible.

## What you should read before touching code

1. `INDEX.md`
2. `PORT_INDEX.yaml`
3. `docs/00_program/ROADMAP.md`
4. `docs/00_program/ITERATION_PROTOCOL.md`
5. `docs/00_program/OPERATING_MODEL.md`
6. `docs/00_program/TRANSLATION_PROGRAM_FRAMEWORK.md`
7. `trackers/ITERATION_INDEX.yaml`
8. `docs/03_contracts/CAPABILITY_CONTRACT.md`
9. `docs/03_contracts/VERIFICATION_CONTRACT.md`
10. `docs/03_contracts/WORK_PACKET_CONTRACT.md`
11. `trackers/ITERATION_STATE.yaml`
12. `trackers/WORK_PACKET_TEMPLATE.md`
13. `trackers/NEXT_ITERATION.md`
14. `trackers/CAPABILITY_MATRIX.csv`
15. `trackers/IMPLEMENTATION_LOG.md`
16. `trackers/VERIFICATION_STATUS.md`

## How to choose work

Select **one large coherent family** per round whenever possible.

Good examples:
- citation primitives + markdown citation parsing + JSON payload parity + smoke fixtures
- one self-contained attribute family across AST, reader, writer, JSON, tests, and trackers

Bad examples:
- editing unrelated tiny features across multiple subsystems in one sweep
- broadening grammar faster than comparator support

## Required outputs of a successful round

- changed code only inside the justified scope
- updated capability rows
- updated implementation log entry
- updated verification status entry
- updated next-iteration brief
- divergence entries for every unresolved mismatch
- decision log update for architecture-level choices

## Failure discipline

If verification fails, do not hide it. Either:

- fix the issue in the same round, or
- record it explicitly as a divergence/blocker and narrow the scope.


## Required inventory context

Before selecting a new slice, review `docs/01_architecture/HASKELL_REPO_INVENTORY.md` and `docs/01_architecture/HASKELL_REPO_SCOPE_GAPS.md`. Do not assume the current archive is the full AST source of truth.


## Structural health check

Before closing a round, run `python scripts/validate_control_plane.py` and do not claim the control bundle is sound if it fails.
