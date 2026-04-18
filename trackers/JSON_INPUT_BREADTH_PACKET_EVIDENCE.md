# JSON-input breadth packet evidence

Admitted in v51.

## Scope admitted

- `atx_heading` admitted on JSON-input -> json/html/native rails
- `autolink_paragraph` admitted on JSON-input -> json/html/native rails
- `block_quote_inline` admitted on JSON-input -> json/html/native rails
- `bullet_list` admitted on JSON-input -> json/html/native rails
- `citation_multi` admitted on JSON-input -> json/html/native rails
- `citation_simple` admitted on JSON-input -> json/html/native rails
- `code_span_paragraph` admitted on JSON-input -> json/html/native rails
- `definition_list_simple` admitted on JSON-input -> json/html/native rails
- `display_math_block` admitted on JSON-input -> json/html/native rails
- `email_autolink_paragraph` admitted on JSON-input -> json/html/native rails
- `fenced_code_attrs` admitted on JSON-input -> json/html/native rails
- `fenced_div` admitted on JSON-input -> json/html/native rails
- `footnote_inline` admitted on JSON-input -> json/html/native rails
- `footnote_reference` admitted on JSON-input -> json/html/native rails
- `image_attrs_standalone` admitted on JSON-input -> json/html/native rails
- `image_paragraph` admitted on JSON-input -> json/html/native rails
- `image_title_paragraph` admitted on JSON-input -> json/html/native rails
- `ordered_list_inline` admitted on JSON-input -> json/html/native rails
- `pipe_table_caption` admitted on JSON-input -> json/html/native rails
- `reference_image` admitted on JSON-input -> json/html/native rails
- `strikeout_paragraph` admitted on JSON-input -> json/html/native rails
- `subscript_superscript_paragraph` admitted on JSON-input -> json/html/native rails

## Oracle-backed report counts

Each admitted fixture passed on all three governed JSON-input verification rails:

- json input -> JSON (structured equality)
- json input -> HTML (normalized HTML equality)
- json input -> native (oracle native round-trip JSON equality)

## Total differential evidence

- **66/66** oracle-backed differential reports passing

## Fixture corpus

- **22** oracle-generated JSON fixtures derived from the existing markdown smoke corpus

## Targeted regression coverage

- **62/62** targeted regression tests passed across `test_pandoc_json_reader.py`, `test_pandoc_json_route.py`, `test_attribute_json_family.py`, `test_list_json_family.py`, `test_definition_footnote_json_family.py`, `test_citation_json_family.py`, `test_native_family.py`, and `test_metadata_surface.py`.
