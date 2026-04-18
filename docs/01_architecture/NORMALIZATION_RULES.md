# Normalization rules

Normalization exists to remove non-semantic noise, not to manufacture passing results.

## Allowed

- line ending normalization
- trailing whitespace trimming
- stable object key ordering
- attribute ordering normalization when order is not semantically meaningful
- removal of known generated metadata that is explicitly declared non-semantic

## Disallowed

- removing semantic nodes
- collapsing distinct block or inline types into shared text
- stripping identifiers, classes, captions, citations, raw blocks, or links to force equivalence
- silently mutating content to satisfy weak comparisons

## Comparator ladder

1. byte equality
2. structured equality
3. semantic normalized equality
4. container-aware equivalence
5. round-trip AST equivalence

Use the strictest valid level for the capability under test.

## Approved semantic comparator for the current markdown rail

- `json -> markdown` may be governed with **markdown round-trip JSON equivalence** when both oracle and Python markdown outputs are reparsed through the oracle markdown parser and the resulting JSON payloads match exactly
- this comparator is approved for the current JSON-input markdown route only; broader markdown-output use still needs explicit source-format policy
