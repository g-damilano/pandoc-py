# Next iteration

The translation program reached **98.6% implemented / 73.8% verified** on 711 governed rows. All 88 previously `mapped_only` inventory rows now have Python implementations under `src/pandoc_py/formats/` plugged into the OOP `FormatRegistry`. 5 of the new writer rails are oracle-backed; the rest are admitted as `implemented_unverified` pending widened comparator policy and per-format calibration.

The next governed packets, in order:

1. **Oracle-comparator widening packet for new format families.** Build per-format reparse comparators for org, asciidoc, mediawiki, textile, djot, jira, creole, vimwiki, twiki, tikiwiki, haddock, txt2tags, typst, pod, csv, opml, docbook, jats, fb2, rtf, ipynb. For each, calibrate the writer surface (heading delimiters, code-fence form, list markers) to match what `pandoc -f <fmt>` reparses cleanly. Promote each row only when its dedicated `FAMILIES-MD2<FMT>-NNN` report passes.
2. **Reader oracle packets**, parallel to (1). Hand-craft per-format input fixtures, run `<fmt>→json` through both pandoc_py and the oracle, compare structured JSON. Promote `RD-<FMT>-001` rows on pass.
3. **Binary-comparator policy admission packet.** Define how DOCX/ODT/EPUB/PPTX/XLSX outputs are oracle-compared: zip member set + per-member XML structural comparison. Once admitted, run reports against pandoc 3.x and promote `WR-DOCX-001`, `WR-ODT-001`, etc.
4. **Inline-emphasis widening packet.** Several format readers/writers admit only plain-text inlines today; widen to support `*emph*` / `**strong**` / `` `code` `` / inline links across the families.
5. **Citeproc bibliography packet.** Today's citeproc is a constrained slice that renders `[Author Year]`; widen to handle CSL style files and bibliography sections.
6. **Lua filter packet.** `apply_filter` accepts callables and external executables; add a Lua interpreter shim.
7. **CLI option widening packet.** New CLI flags pandoc accepts (--toc, --metadata, --variable, --include-in-header, etc.) routed through `WriteOptions.extra`.

Comparator-baseline policy remains as admitted in `trackers/NATIVE_WIDENED_ORACLE_PACKET_EVIDENCE.md` — per-report `oracle_version` is authoritative and mixed-version evidence is allowed.
