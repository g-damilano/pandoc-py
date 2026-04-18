# Verification status

- Active matrix: 589 rows.
- Smoke-verified-or-better rows: 500/589 (84.9%).
- Implemented-or-better rows: 500/589 (84.9%).
- v54 json-input markdown semantic packet: the governed JSON-input corpus now passes on the semantic markdown round-trip rail, with 58 oracle-generated fixtures admitted after heading-attribute spacing in the markdown writer was corrected.
- JSON-input markdown semantic evidence: `trackers/JSON_INPUT_MARKDOWN_SEMANTIC_PACKET_EVIDENCE.md` documents 58/58 passing semantic markdown differential reports plus 127/127 targeted regression tests.
- v53 json-input screen-closure packet remains intact: the remaining fifteen oracle-generated JSON screen fixtures are now admitted on json/html/native rails, covering author-in-text and locator citations, context-bound fenced and indented code blocks, continuation footnotes, loose ordered-list nesting, aligned and simple pipe tables, fenced/raw TeX and LaTeX block forms, raw inline TeX/LaTeX forms, and thematic breaks in surrounding context.
- JSON-input screen-closure evidence: `trackers/JSON_INPUT_SCREEN_CLOSURE_EVIDENCE.md` documents 45/45 passing differential reports plus targeted JSON-route regression coverage.
- v52 json-input continuation packet remains intact: 21 additional oracle-generated JSON fixtures are now admitted on json/html/native rails, covering block quotes, span attributes, inline and loose bullet-list forms, emphasis/plain/strong/two-paragraph documents, heading attribute/code/link/emphasis+strong forms, indented code blocks, inline and titled links, ordered lists, reference-style links, Setext heading forms, soft breaks, and thematic breaks.
- JSON-input continuation evidence: `trackers/JSON_INPUT_CONTINUATION_PACKET_EVIDENCE.md` documents 63/63 passing differential reports plus targeted JSON-route regression coverage.
- v51 json-input breadth packet remains intact: 22 oracle-generated JSON fixtures are now admitted on json/html/native rails, covering ATX headings, URI and email autolinks, inline block quotes, bullet and inline ordered lists, simple and multi-citation paragraphs, code spans, simple definition lists, display math, fenced code attrs, fenced divs, inline and reference footnotes, standalone image attrs, image paragraphs, titled image paragraphs, pipe-table captions, reference images, strikeout, and subscript/superscript.
- JSON-input breadth evidence: `trackers/JSON_INPUT_BREADTH_PACKET_EVIDENCE.md` documents 66/66 passing differential reports.
- Existing markdown/json/html/native/CommonMark route verification remains intact for the previously admitted slice.
- Package version: pandoc_py 0.0.54.
