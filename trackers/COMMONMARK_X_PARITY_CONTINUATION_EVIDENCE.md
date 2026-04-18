# CommonMark_X parity continuation evidence

This tranche closes the remaining backslash-line-ending parity defect and admits the next bounded set of already-implemented `commonmark_x` behaviors that now pass on all four governed rails.

## Scope admitted in v48

- doubled-backslash line-ending paragraphs (`hardbreak_paragraph`)
- raw inline HTML tags (`raw_inline_tag`)
- fenced code blocks (`fenced_code_block`)
- inline math paragraphs (`math_inline_paragraph`)
- display math blocks (`display_math_block`)
- reference-style links (`reference_links`)
- inline image attributes (`image_attrs_inline`)

## Oracle-backed report counts

Each admitted fixture passed on all four `commonmark_x` verification rails:

- input -> JSON
- input -> HTML
- input -> native
- markdown -> commonmark_x output round-trip

## Total differential evidence

- **28/28** oracle-backed differential reports passing

## Semantic fix landed

The reader now gives escaped punctuation precedence over the raw-TeX inline path and coalesces adjacent `Str` nodes, which closes the remaining `hardbreak_paragraph` mismatch where Pandoc expects a literal backslash plus `SoftBreak` rather than a hard break or raw TeX inline.
