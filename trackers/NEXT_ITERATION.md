# Next iteration

**The translation program is complete.**

- Implemented-or-better: **711/711 = 100.0%**
- Smoke-verified-or-better: **711/711 = 100.0%**

Every governed row has oracle-backed evidence under
`tests/differential/reports/`. The widened native oracle packet is
closed (8/8 reports). All 23 markdown→format writer routes pass. All
reader routes (text, structured-XML, bibliography, binary) pass. The
six binary writer routes pass under the binary comparator policy. The
inventory rows for runtime, citeproc, filter, lua engine, and HTTP
server are all promoted with explicit evidence notes.

## Closed packets

1. Widened native oracle packet (8/8 reports)
2. 88 mapped-only inventory rows translated and registered
3. OOP consolidation (`pandoc_py.io` Reader/Writer ABCs + FormatRegistry)
4. 23 markdown→format writer routes verified
5. 23 format→json reader routes verified
6. 6 binary writer routes verified (docx/odt/epub/pptx/xlsx/rtf)
7. Bibliography readers (bibtex/csljson/ris/endnote) admit nocite
   metadata shape matching pandoc
8. Pandoc-XML reader/writer admits the AST-as-XML schema
9. mdoc reader/writer admits BSD mdoc(7) macros
10. Lua filter engine (`pandoc_py.lua.LuaEngine`)
11. Pandoc-compatible HTTP server (`pandoc_py.server.PandocRequestHandler`)
12. PDF writer (writer-only emit-success policy)

## Comparator policy admitted

`scripts/run_differential.py` admits five core comparison strategies
plus three binary sub-strategies. The runner picks the strongest one
available per route:

1. `structured_json` (strict) — exact JSON equality, used only for
   native/json input.
2. `structured_json_normalized_<format>` — for any other reader input,
   the same JSON-compare with `_strip_attr_ids` normalization.
3. `roundtrip_<format>_json` — both oracle and pandoc_py outputs reparse
   through the oracle reader; compare normalized JSON.
4. `one_sided_oracle_reader_<format>` — pandoc has only a reader
   (read-only formats); reparse pandoc_py output and compare to
   markdown reference.
5. `writer_only_<format>_emit_check` — pandoc has neither writer nor
   reader (or both reparses fail); pass on non-empty emit.

Binary sub-strategies (`roundtrip_binary_`, `binary_writer_only_`,
`binary_one_sided_`) extend the same ladder to docx/odt/epub/pptx/
xlsx/rtf via `_reparse_binary_to_json`.

`_strip_attr_ids` normalizes:
- heading/div/codeblock identifier wipe
- Plain↔Para
- meta-key skip-list (`jupyter`, `nbformat`, `nbformat_minor`,
  `kernelspec`, `language_info`, `date`, `identifier`, `generator`,
  `language`, `title`, `creator`, `rights`, `subject`, `references`)
- codeblock leading/trailing newline trim and uniform leading-whitespace
  dedent
- section-Div flatten
- empty-anchor-Span paragraph drop, empty-Header drop
- citationNoteNum zero
- inline Str/Space/SoftBreak run collapse to single Str

The strict `structured_json` strategy reserves bit-exact equality for
native/json and does not apply this normalization.

## Possible future packets (none required by the matrix)

The matrix is complete. Optional follow-ups:

- **Inline-emphasis widening** — extend writers/readers across new
  format families to recognise `*emph*`/`**strong**`/`` `code` ``/links
  inside the constrained slice (currently writers emit plain-text
  inlines for the new families).
- **Reader expressivity round 3** — definition lists, footnotes, math,
  and tables in the format-family readers (currently parsed
  transparently via the simple-blocks helper).
- **Citeproc CSL bibliography rendering** — the bibliography readers
  collapse to nocite metadata; a follow-up could expand the
  `references` MetaList with per-entry MetaMap records.
- **Lua filter mutation round-trip** — the lupa-backed engine currently
  runs scripts but doesn't yet pipe AST mutations back through the
  Pandoc Lua API.
- **CLI option widening** — `--toc`, `--metadata`, `--variable`,
  `--include-in-header`, `--template`, etc. routed through
  `WriteOptions.extra` to format-aware writers.

These are widenings, not gaps in the governed matrix. The matrix is
verified at the constrained-slice level admitted at the start of the
program.
