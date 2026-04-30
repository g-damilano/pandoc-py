# Next iteration

The widened native oracle packet was executed and closed on 2026-04-30 (8/8 reports passed against pandoc 3.8.2; 13 supplement rows promoted to `verified_smoke`).

The next governed program is to translate the **88 mapped-only inventory rows** into implemented translations. These are entire format families with no Python implementation yet. Work is being broken into governed packets:

1. **OOP consolidation packet** — introduce abstract base classes for `Reader` and `Writer`, plus a `format_registry` so new formats slot in cleanly. Existing readers/writers wrapped to conform. Goal: minimize per-format-family per-iteration overhead.
2. **Text-based reader/writer packets** (parallel-safe, can be batched in supplement matrices):
   - RST, Org, LaTeX, AsciiDoc, MediaWiki, Textile, Djot, DokuWiki, Jira, Typst, Muse, Creole, TWiki, Vimwiki, Haddock, Man/Mdoc/Roff, Pod, Txt2Tags, TikiWiki
3. **Structured-data format packets**:
   - CSV, OPML, XML, FB2, JATS, DocBook
4. **Bibliography format packets**:
   - BibTeX, CslJson, RIS, EndNote
5. **Binary-container format packets** (each is its own larger packet because of zip/OOXML handling):
   - IPYNB (JSON-based, fastest), EPUB, DOCX, ODT, PPTX, XLSX, RTF
6. **Runtime/filter/citeproc inventory packets**:
   - Common runtime/monad/state, JSON filter integration, citeproc

Promotion rule for each new format packet: each row may be admitted as `implemented_unverified` once a constrained slice is implemented and unit-tested. Promotion to `verified_smoke` requires a passing oracle-backed differential report at the declared comparator level.

Comparator-baseline policy is governed by `trackers/NATIVE_WIDENED_ORACLE_PACKET_EVIDENCE.md` "Comparator-baseline policy (admitted 2026-04-30)" — each report records its own oracle version; mixed-version evidence is allowed.
