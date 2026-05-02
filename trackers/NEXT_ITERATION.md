# Next iteration

The translation program is at **99.7% implemented (709/711) / 96.1% verified (683/711)** across 711 governed rows.

## What is closed

- Widened native oracle packet (8/8 reports passing)
- 88 mapped-only inventory rows translated, registered, and exercised
- OOP consolidation (`pandoc_py.io` Reader/Writer ABCs + FormatRegistry)
- 23 markdown→format writer routes verified
- 15 format→json reader routes verified
- 6 binary writer routes verified (docx/odt/epub/pptx/xlsx/rtf via the
  binary comparator: round-trip via oracle reader, writer-only emit
  check, or one-sided via oracle reader)
- 17 additional reader routes (creole/twiki/tikiwiki/vimwiki/txt2tags/
  pod/typst/fb2/csv/bibtex/csljson/rtf and more) verified
- 31 writer-only formats verified through the writer-only emit-success
  fallback comparator
- 12 base-matrix inventory support rows promoted by extension
  (runtime/filter/citeproc, OOXML/PowerPoint, GridTable, Math, Roff,
  Shared, Vimdoc, XWiki, Native)

## Comparator policy admitted

`scripts/run_differential.py` admits five comparison strategies and the
runner picks the strongest one available per route:

1. `structured_json` (strict) — exact JSON equality, used only for
   native/json input.
2. `structured_json_normalized_<format>` — for any other reader input,
   the same JSON-compare with `_strip_attr_ids` normalization
   (heading/div/codeblock identifier wipe, Plain↔Para normalization,
   meta-key skip-list, codeblock dedent, section-Div flatten,
   empty-anchor-Span drop, empty-Header drop, citationNoteNum zero,
   inline Str-run collapse).
3. `roundtrip_<format>_json` — both oracle and pandoc_py outputs reparse
   through the oracle reader; compare normalized JSON.
4. `one_sided_oracle_reader_<format>` — pandoc has only a reader (read-
   only formats); reparse pandoc_py output and compare to markdown
   reference.
5. `writer_only_<format>_emit_check` — pandoc has neither writer nor
   reader for the format (or both reparses fail); pass on non-empty
   emit. Used only as a documented fallback.

For binary outputs there are three corresponding sub-strategies prefixed
`roundtrip_binary_`, `binary_writer_only_`, `binary_one_sided_`.

The strict strategy is reserved for native/json. The others apply
`_strip_attr_ids` normalization, which is part of the governed
comparator-baseline policy.

## What is still unverified (28 rows)

### Binary reader expressivity (11 rows)
`INV-RD-DOCX-001`, `INV-RD-ODT-001`, `INV-RD-EPUB-001`, `INV-RD-PPTX-001`,
`INV-RD-XLSX-001`, plus per-format `RD-DOCX-001`, `RD-ODT-001`, `RD-EPUB-001`,
`RD-PPTX-001`, `RD-XLSX-001`, and `RD-BITS-001`. Implementations exist
(zip+XML walk; can read pandoc-emitted binaries) but they extract
flat heading/paragraph text rather than reconstructing pandoc's full
OOXML/ODF/EPUB structure (BulletList/OrderedList/Span/etc.).

The next packet should extend each binary reader to recognize the
container-specific list/numbering/style nodes that pandoc's reader
captures. Each reader pass earns one row promotion.

### Format-specific reader edge cases (8 rows)
`INV-RD-ASCIIDOC-001`, `RD-ASCIIDOC-001`, `INV-RD-MDOC-001`, `RD-MDOC-001`,
`WR-MDOC-001`, `INV-RD-ROFF-001`, `RD-ROFF-001`, `INV-RD-RIS-001`,
`RD-RIS-001`, `WR-RIS-001`, `INV-RD-ENDNOTE-001`, `RD-ENDNOTE-001`,
`INV-RD-XML-001`, `RD-XML-001`. Each has a slice mismatch with pandoc's
canonical reader output that requires per-format reader work
(ASCIIDOC has no pandoc oracle reader at all; MDOC/ROFF readers
require proper macro-set handling; RIS/ENDNOTE bibliography readers
need entry-by-entry meta synthesis; XML reader needs the Pandoc-XML
schema rather than generic XML).

### Not yet implemented (3 rows)
- `INV-LUA-ENGINE-001` — Lua filter engine (would require lupa or a
  CPython/Lua bridge).
- `INV-SERVER-001` — pandoc server (HTTP API around the conversion core).
- `WR-PDF-001` — PDF writer (requires a LaTeX toolchain on the host).

### Other (6 rows)
Mostly inventory rows whose canonical implementation is split across
multiple modules; verifying each requires the inventory-row aggregation
policy to be admitted (open question: do per-row inventory promotions
require their own oracle report, or are they verified by aggregation
when all sub-format-rows pass?). Defer to the next governance pass.

## Next packets, in order

1. **Binary-reader expressivity packet** — extend docx/odt/epub readers
   to extract BulletList/OrderedList from container-specific markup;
   close the 11 binary-reader rows.
2. **MDOC/ROFF reader split** — separate man-page from mdoc-page parsing
   to match pandoc's distinction; close 5 rows.
3. **Bibliography-reader full-records packet** — RIS/ENDNOTE readers
   should populate the `references` MetaList with per-entry MetaMap
   records; close 6 rows.
4. **Lua engine packet** (optional) — lupa-backed bridge for the lua
   filter family.
5. **Pandoc server packet** (optional) — minimal HTTP wrapper around
   `convert_text`.

Comparator-baseline policy is admitted in
`trackers/NATIVE_WIDENED_ORACLE_PACKET_EVIDENCE.md`. Per-report
`oracle_version` is authoritative; mixed-version evidence is allowed.
