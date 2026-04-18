# Capability contract

Every capability admitted into the port program must satisfy this contract.

## Mandatory fields

- capability id
- subsystem area
- Haskell source anchor
- Python target module(s)
- user-visible behavior
- status
- verification level
- declared scope boundaries
- known exclusions

## Admission rule

A capability may enter active development only when:
- the source anchor is known
- the Python target is chosen
- acceptance criteria are written
- verification method is named

## Completion rule

A capability may move to a verified state only when:
- implementation exists for the declared scope
- differential or equivalent verification has passed for that scope
- remaining exclusions are explicit
- no hidden failures remain outside divergence tracking
