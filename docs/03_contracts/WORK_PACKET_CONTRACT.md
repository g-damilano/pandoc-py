# Work packet contract

Every implementation round must declare a work packet before broad edits begin.

## Required fields

- packet id
- date
- selected slice
- capability ids touched
- Haskell source anchors
- Python target modules
- fixtures added or reused
- comparator level
- acceptance rule
- exclusions and fail-closed boundaries
- expected tracker updates

## Admission rule

A packet may start only when:

- the slice is coherent
- the source anchors are known
- the verification method is declared
- the expected outputs of the round are named

## Completion rule

A packet is complete only when:

- implementation is present for the declared scope
- the declared verification runs were executed
- unresolved failures are logged in the divergence log
- the capability matrix reflects the actual state
- the next iteration brief is updated

## Forbidden packet patterns

- mixed unrelated subsystems in one packet
- format claims without comparator support
- broad parser or writer widening without narrowed acceptance criteria
- tracker-only completion claims with no executable evidence
