# JSON-input continuation packet evidence

This packet admits **21 additional oracle-generated JSON fixtures** on the governed JSON-input rails:

- `json -> json`
- `json -> html`
- `json -> native`

The admitted fixtures are:

- `block_quote`
- `bracketed_span`
- `bullet_list_inline`
- `bullet_list_loose_nested`
- `emphasis_paragraph`
- `heading_attrs`
- `heading_code_span`
- `heading_emphasis_strong`
- `heading_link`
- `indented_code_block`
- `link_paragraph`
- `link_title_paragraph`
- `ordered_list`
- `plain_paragraph`
- `reference_links`
- `setext_heading_inline`
- `setext_headings`
- `softbreak_paragraph`
- `strong_paragraph`
- `thematic_break`
- `two_paragraphs`

Evidence location:

- reports: `tests/differential/reports/json_input_v52/`
- fixtures: `tests/fixtures/json_input_v52/`

Result summary:

- **63/63** oracle-backed differential reports passed
- comparator levels used:
  - structured JSON
  - normalized HTML
  - native round-trip JSON

Targeted regression coverage retained during the packet:

- `tests/unit/test_pandoc_json_route.py`
- `tests/unit/test_list_json_family.py`
- `tests/unit/test_attribute_json_family.py`
- `tests/unit/test_citation_json_family.py`
- `tests/unit/test_definition_footnote_json_family.py`

This packet is intentionally **no-code**: it converts already-implemented Pandoc-JSON reader behavior into governed verified progress rather than claiming new parser capability.
