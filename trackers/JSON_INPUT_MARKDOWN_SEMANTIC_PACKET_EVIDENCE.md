# JSON-input markdown semantic packet evidence

This packet settles the `json -> markdown` verification policy by using **semantic markdown round-trip comparison**: both the oracle markdown output and the Python markdown output are reparsed through the oracle markdown parser and compared as structured Pandoc JSON.

## Admitted scope

The packet admits **58 oracle-generated JSON fixtures** on the `json -> markdown` rail:

- v51 breadth packet: **22/22** fixtures passed
- v52 continuation packet: **21/21** fixtures passed
- v53 screen-closure packet: **15/15** fixtures passed

Total: **58/58** semantic markdown differential reports passed.

## Comparator policy

- output route under test: `json -> markdown`
- comparison level: `roundtrip_markdown_json`
- oracle markdown output is reparsed with `pandoc -f markdown -t json`
- Python markdown output is reparsed with `pandoc -f markdown -t json`
- the reparsed JSON payloads must match exactly

This resolves `DIV-0033`: byte comparison for markdown reserialization was too brittle, but semantic round-trip comparison is strict enough for the currently admitted writer slice.

## Code changes needed for closure

One real writer defect had to be fixed before the packet could be admitted:

- heading attribute blocks now render **after a separating space** in the markdown writer, so heading attributes attach to the heading instead of being parsed as inline-code or inline-link attributes.

## Targeted regression

- **127/127** targeted unit tests passed across:
  - `tests/unit/test_markdown_writer_surface.py`
  - `tests/unit/test_pandoc_json_route.py`
  - `tests/unit/test_pandoc_json_reader.py`
  - `tests/unit/test_metadata_surface.py`
  - `tests/unit/test_minimal_markdown_slice.py`

## Fixture groups admitted

### v51 breadth packet

`atx_heading`, `autolink_paragraph`, `block_quote_inline`, `bullet_list`, `citation_multi`, `citation_simple`, `code_span_paragraph`, `definition_list_simple`, `display_math_block`, `email_autolink_paragraph`, `fenced_code_attrs`, `fenced_div`, `footnote_inline`, `footnote_reference`, `image_attrs_standalone`, `image_paragraph`, `image_title_paragraph`, `ordered_list_inline`, `pipe_table_caption`, `reference_image`, `strikeout_paragraph`, `subscript_superscript_paragraph`

### v52 continuation packet

`block_quote`, `bracketed_span`, `bullet_list_inline`, `bullet_list_loose_nested`, `emphasis_paragraph`, `heading_attrs`, `heading_code_span`, `heading_emphasis_strong`, `heading_link`, `indented_code_block`, `link_paragraph`, `link_title_paragraph`, `ordered_list`, `plain_paragraph`, `reference_links`, `setext_heading_inline`, `setext_headings`, `softbreak_paragraph`, `strong_paragraph`, `thematic_break`, `two_paragraphs`

### v53 screen-closure packet

`citation_author_in_text`, `citation_prefix_locator`, `fenced_code_block_context`, `footnote_continuation`, `indented_code_block_context`, `ordered_list_loose_nested`, `pipe_table_aligned`, `pipe_table_simple`, `raw_block_latex_fence`, `raw_block_tex_command`, `raw_block_tex_env`, `raw_block_tex_fence`, `raw_inline_latex_attr`, `raw_inline_tex_command`, `thematic_break_context`
