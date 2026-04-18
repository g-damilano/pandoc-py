# pandoc-types source anchor

This file closes the earlier inventory blind spot around the canonical Pandoc AST definitions.

## What is now anchored

The repository now carries a local structural source anchor at:

- `third_party/pandoc-types/src/Text/Pandoc/Definition.hs`

That file is used to ground the current Python AST slice against the external `pandoc-types` definition source rather than pretending `pandoc-main.zip` already contained the whole AST oracle.

## What this anchor is for

- constructor and type-name traceability
- AST coverage mapping for the current Python slice
- more honest completion claims for AST-core tracker rows
- future widening of the denominator from bootstrap scope toward repo scope

## What this anchor is not

- not a full vendored `pandoc-types` package yet
- not a substitute for behavioral verification through the pinned `pandoc` oracle
- not permission to open citeproc or other downstream families without explicit admission

## Generated assets

- `trackers/PANDOC_TYPES_SYMBOLS.csv`
- `trackers/AST_SOURCE_COVERAGE.csv`
- `scripts/extract_pandoc_types_symbols.py`

## Operational rule

Any future AST-family expansion should update the generated coverage assets before claiming parity at the AST layer.
