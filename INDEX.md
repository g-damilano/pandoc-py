# Pandoc Python Port — Control Tower Index

This repository is run as a **verification-first porting program**.

Do not treat it as an open-ended rewrite. Treat it as a controlled system with four mandatory rails:

1. **Traceability rail** — every Python change maps back to a Haskell source area.
2. **Capability rail** — work is tracked by user-visible capability, not by translated file count.
3. **Verification rail** — every implemented slice must be checked against pinned Pandoc behavior.
4. **Control rail** — every iteration must update the trackers so the program remains observable.

## Start here

For a human or AI starting a work cycle, read these in order:

1. `PORT_INDEX.yaml`
2. `docs/00_program/AI_START_HERE.md`
3. `docs/00_program/ITERATION_PROTOCOL.md`
4. `docs/00_program/OPERATING_MODEL.md`
5. `docs/00_program/TRANSLATION_PROGRAM_FRAMEWORK.md`
6. `trackers/ITERATION_INDEX.yaml`
7. `trackers/NEXT_ITERATION.md`
8. `trackers/CAPABILITY_MATRIX.csv`
9. `trackers/IMPLEMENTATION_LOG.md`
10. `trackers/VERIFICATION_STATUS.md`
11. `docs/03_contracts/VERIFICATION_CONTRACT.md`
12. `trackers/ITERATION_STATE.yaml`
13. `trackers/WORK_PACKET_TEMPLATE.md`

## Current program truth

- Program roadmap: `docs/00_program/ROADMAP.md`
- Capability source of truth: `trackers/CAPABILITY_MATRIX.csv`
- Iteration AI index: `trackers/ITERATION_INDEX.yaml`
- Immediate work packet: `trackers/NEXT_ITERATION.md`
- Chronological execution record: `trackers/IMPLEMENTATION_LOG.md`
- Verification health: `trackers/VERIFICATION_STATUS.md`
- Divergence control: `docs/02_tracking/DIVERGENCE_LOG.md`
- Risk control: `docs/02_tracking/RISK_REGISTER.md`
- Architecture decisions: `docs/02_tracking/DECISION_LOG.md`

## Non-negotiable rules

- No capability is "done" without oracle-backed verification.
- No large translation sweep without tracker updates.
- No hidden divergence: every mismatch must be logged.
- No uncontrolled broadening of grammar: each slice must stay fail-closed.
- No verification laundering through over-aggressive normalization.

## Iteration output contract

Every iteration must leave behind:

- code changes, if any
- updated capability rows
- updated implementation log
- updated verification status
- updated next-iteration brief
- divergence entries for every unresolved mismatch
- decision log entry if an architectural choice changed

## Suggested near-term focus

The current scaffold now includes a landed CommonMark_X honesty packet. The next large coherent engineering slice should widen that dedicated commonmark_x surface or close the next constrained verification gap, not reopen reporting-only work.


## M1 inventory assets

- Haskell repo inventory: `docs/01_architecture/HASKELL_REPO_INVENTORY.md`
- Scope gaps and external references: `docs/01_architecture/HASKELL_REPO_SCOPE_GAPS.md`
- Seeded mapping bridge: `docs/01_architecture/HASKELL_TO_PYTHON_MAPPING.md`
- Haskell module inventory CSV: `trackers/HASKELL_MODULE_INVENTORY.csv`
- Haskell capability seed CSV: `trackers/HASKELL_CAPABILITY_SEED.csv`
- Machine summary: `trackers/HASKELL_REPO_SUMMARY.json`
- Inventory extractor: `scripts/extract_haskell_inventory.py`


## Control-plane validation

Run `python scripts/validate_control_plane.py` before calling a bundle release structurally sound.
