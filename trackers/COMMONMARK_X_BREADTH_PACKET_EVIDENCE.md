# CommonMark_X breadth packet evidence

This tranche widens the dedicated `commonmark_x` surface with additional markdown-safe behaviors that are already implemented in the shared markdown core and are now admitted under explicit oracle-backed `commonmark_x` evidence.

## Scope admitted in v45

- inline-bearing block quote paragraphs
- emphasis paragraphs
- strong-emphasis paragraphs
- plain single-paragraph documents
- two-paragraph documents
- thematic breaks

## Oracle-backed report counts

Each admitted fixture passed on all four `commonmark_x` verification rails:

- input -> JSON
- input -> HTML
- input -> native
- markdown -> commonmark_x output round-trip

Admitted fixtures:

- `block_quote_inline`
- `emphasis_paragraph`
- `strong_paragraph`
- `plain_paragraph`
- `two_paragraphs`
- `thematic_break`

## Total differential evidence

- **24/24** oracle-backed differential reports passing

All reports live under `tests/differential/reports/smoke_commonmark_x_breadth/`.
