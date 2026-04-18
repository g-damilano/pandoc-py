# Iteration protocol

Each cycle must follow this sequence.

## 1. Intake

Read the current state:
- `trackers/NEXT_ITERATION.md`
- `trackers/CAPABILITY_MATRIX.csv`
- `trackers/IMPLEMENTATION_LOG.md`
- `trackers/VERIFICATION_STATUS.md`
- open divergences affecting the selected area

## 2. Slice selection

Pick the largest coherent slice that:
- has clear Haskell source anchors
- fits current comparator coverage
- can be verified inside the round
- does not require uncontrolled parser or writer broadening

## 3. Work packet declaration

Use `trackers/WORK_PACKET_TEMPLATE.md`. Before implementation, define:
- capability IDs to touch
- Haskell source modules
- Python target modules
- fixtures to add or reuse
- comparator level to use
- pass/fail acceptance rule

## 4. Implementation

Implement fail-closed:
- prefer constrained behavior over over-broad half-correct behavior
- do not add silent fallback semantics
- keep grammar narrow unless verification expands with it

## 5. Verification

Run, as applicable:
- unit tests
- golden tests
- differential smoke tests
- structured JSON/native comparison
- normalized semantic comparison
- container-aware comparison for archive formats

## 6. Divergence handling

For every unresolved mismatch create or update a divergence entry with:
- capability
- input/fixture
- oracle result
- Python result
- severity
- suspected cause
- planned resolution

## 7. Tracker updates

At minimum update:
- `trackers/CAPABILITY_MATRIX.csv`
- `trackers/IMPLEMENTATION_LOG.md`
- `trackers/VERIFICATION_STATUS.md`
- `trackers/NEXT_ITERATION.md`
- `docs/02_tracking/DIVERGENCE_LOG.md` if anything remains open

## 8. Handoff

Leave a concise handoff note covering:
- what changed
- what passed
- what failed
- what remains highest value next

## 9. Control-plane validation

Run `python scripts/validate_control_plane.py` after tracker updates. Treat a failing control-plane check as a real repository defect, not as paperwork.
