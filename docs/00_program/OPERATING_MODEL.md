# Operating model

This repository is managed as a **verification-first translation program**.

The purpose of the operating model is to keep the port controlled even when many iterations are performed by different contributors or by AI across multiple rounds.

## The four rails

### 1. Traceability rail
Every capability must point back to one or more Haskell source anchors and forward to one or more Python target modules.

### 2. Capability rail
Work is governed by user-visible behavior, not by translated file count.

### 3. Verification rail
A slice is not complete until it has passed the declared comparator against the pinned Pandoc oracle.

### 4. Control rail
Every round must leave the repository more observable than it found it: trackers updated, divergences visible, and the next packet clear.

## State machine for a capability row

A capability should move through these states:

- `not_started`
- `mapped_only`
- `skeleton_only`
- `partially_implemented`
- `implemented_unverified`
- `verified_smoke`
- `verified_standard`
- `verified_extended`
- `known_divergence`
- `blocked`
- `deferred`
- `done`

Do not jump directly from `mapped_only` to `done`.

## Mandatory iteration lifecycle

1. Read the index and current trackers.
2. Select one coherent slice.
3. Declare the work packet before broad edits.
4. Implement fail-closed.
5. Verify with the declared comparator.
6. Log every unresolved mismatch.
7. Update trackers and publish the next packet.

## What counts as a coherent slice

A slice is coherent when it:

- belongs to one capability family or one tightly-linked vertical path
- has clear Haskell source anchors
- has a credible comparator already available or can add one in the same round
- can be handed off without hidden assumptions

Good slices:

- markdown citation parsing + AST support + JSON parity + smoke verification
- native writer + CLI route + round-trip oracle verification
- metadata reader + AST meta values + JSON parity + fixtures

Bad slices:

- scattered tiny fixes across unrelated readers and writers
- new syntax without a declared comparator
- new format claims without updated matrix rows

## Release logic

A release-worthy bundle must satisfy all of the following:

- the control plane validates cleanly
- the active capability matrix is internally consistent
- version identifiers are consistent across package and status trackers
- differential evidence exists for every newly admitted verified slice
- open divergences are explicit and bounded

## Anti-randomness rules

- No undocumented scope widening.
- No silent normalization changes.
- No tracker debt left for a future round.
- No progress claim based only on code presence.
- No admission of binary/container-format debt ahead of core semantics unless explicitly authorized.
