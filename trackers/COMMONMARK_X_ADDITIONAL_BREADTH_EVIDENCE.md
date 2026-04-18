# CommonMark_X additional breadth evidence

This packet widens the dedicated `commonmark_x` surface with already-implemented behaviors that were verified one by one on all four governed rails and only then admitted into the governed matrix.

## Scope admitted in v49

- simple definition lists (`definition_list_simple`)
- continuation-line definition lists (`definition_list_continuation`)
- fenced code blocks with attributes (`fenced_code_attrs`)
- fenced div blocks (`fenced_div`)
- reference footnotes (`footnote_reference`)
- raw inline HTML comments (`raw_inline_comment`)
- raw inline HTML attribute syntax (`raw_inline_attr`)
- reference-style images (`reference_image`)
- strikeout paragraphs (`strikeout_paragraph`)
- subscript/superscript paragraphs (`subscript_superscript_paragraph`)
- indented code blocks (`indented_code_block`)
- inline image paragraphs (`image_paragraph`)
- titled image paragraphs (`image_title_paragraph`)
- titled inline-link paragraphs (`link_title_paragraph`)

## Oracle-backed report counts

Each admitted fixture passed on all four `commonmark_x` verification rails:

- input -> JSON
- input -> HTML
- input -> native
- markdown -> commonmark_x output round-trip

## Total differential evidence

- **56/56** oracle-backed differential reports passing

## Admission rule kept intact

No new comparator was introduced for this packet. Every promoted behavior was already implemented and was admitted only after passing the existing four-rail `commonmark_x` differential harness.
