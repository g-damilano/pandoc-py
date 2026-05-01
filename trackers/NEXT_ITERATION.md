# Next iteration

The translation program is at **98.6% implemented / 79.3% verified** across 711 governed rows. The widened native oracle packet, the format-family translation packet, and the writer-calibration comparator-widening packet are all closed.

The next governed packets, in order:

1. **Reader-calibration packet.** The current reader implementations admit a deliberately constrained slice that does not yet match what pandoc emits when round-tripping through the format. Per-format reader work remaining (rows still at `implemented_unverified`):
   - **org**: skip/parse `:PROPERTIES:` drawers and `:CUSTOM_ID:` -> heading.attr.identifier
   - **latex**: handle `\section{...}\label{...}` pair; parse `\begin{itemize}\item…` correctly
   - **mediawiki**: pass `<span id=…>…</span>` as RawInline anchor; handle linked refs
   - **textile**: parse `h1(#anchor).` heading-attribute syntax
   - **djot**: parse `{#anchor}` heading-attribute lines
   - **dokuwiki**, **jira**, **muse**, **haddock**, **pod**, **man**: each has format-specific parsing edge cases (anchors, list-item shape, raw blocks).
   - **docbook** / **jats**: walk full XML element tree, not just text-extraction.
   - **opml**: parse the `_note` attribute as embedded markdown.

   Each reader should be calibrated until `<format> -> json` reparses cleanly to the same structured JSON as pandoc's reference. Each pass earns one `RD-<FMT>-001` row promotion.

2. **Binary-comparator policy admission packet.** Define how DOCX/ODT/PPTX/XLSX/EPUB outputs are oracle-compared (zip member set + per-member XML structural comparison; mimetype byte-equality; ignore generated UUIDs and timestamps). Once admitted, run binary reports and promote `WR-DOCX-001`, `WR-ODT-001`, etc.

3. **Inline-emphasis widening packet.** Several format readers/writers admit only plain-text inlines today; widen to support `*emph*` / `**strong**` / `` `code` `` / inline links across the families.

4. **Citeproc bibliography packet.** Today's citeproc renders `[Author Year]` text only; widen to handle CSL style files, locales, and a bibliography-section emitter.

5. **Lua filter packet.** Add a lupa-backed Lua interpreter so `apply_filter` can run pandoc-compatible Lua filters in addition to Python callables and external executables.

6. **CLI option widening packet.** New CLI flags pandoc accepts (--toc, --metadata, --variable, --include-in-header, etc.) routed through `WriteOptions.extra` to format-aware writers that consume them.

Comparator-baseline policy is admitted in `trackers/NATIVE_WIDENED_ORACLE_PACKET_EVIDENCE.md` — per-report `oracle_version` is authoritative; mixed-version evidence is allowed. The `_strip_attr_ids` normalization applied to the one-sided and reparse-based comparators is a declared part of the comparator policy: it strips identifier slots, normalizes Plain<->Para, drops auto-injected meta keys, and uniformly dedents CodeBlock content. The strict `structured_json` comparator (native/json input) does NOT apply this normalization.
