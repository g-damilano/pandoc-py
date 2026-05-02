# Next iteration

The translation program is at **98.6% implemented / 84.7% verified** across 711 governed rows. The widened-native, format-family translation, writer-calibration, reader-calibration, and binary-comparator packets are all closed.

**Binary comparator policy admitted (2026-05-02):** see `scripts/run_differential.py` `_BINARY_FORMATS` and the binary comparator branch. The runner supports three sub-comparators for binary outputs:

1. **Round-trip via oracle reader** — both pandoc and pandoc_py emit binary; reparse both via `pandoc -f <format> -t json` and compare normalized JSON. Used for docx, odt, epub, rtf.
2. **Writer-only emit-success** — pandoc has a writer but no reader (e.g. pptx); both writers emit non-empty bytes. The pass criterion is "both binaries are non-empty".
3. **One-sided via oracle reader** — pandoc has a reader but no writer; pandoc_py emits binary, pandoc reparses to JSON, compared against markdown→json reference. Falls back to writer-only emit-success when oracle has neither writer nor reader (e.g. xlsx in 3.x).

The next packets, in order:

1. **Reader-calibration packet (closed)** — all 15 admitted readers verify against pandoc 3.8.2 reference (rst, org, latex, mediawiki, textile, djot, dokuwiki, jira, muse, haddock, man, opml, docbook, jats, ipynb).
2. **Inline-emphasis widening packet** — current readers/writers admit only plain-text inlines for the new format families. Widen to support `*emph*` / `**strong**` / `` `code` `` / inline links across families.
3. **Citeproc bibliography packet** — render proper CSL-style citations and bibliography section.
4. **Lua filter packet** — add a lupa-backed Lua interpreter so `apply_filter` can run pandoc-compatible Lua filters in addition to Python callables and external executables.
5. **CLI option widening packet** — wire `--toc`, `--metadata`, `--variable`, `--include-in-header`, etc. through `WriteOptions.extra` to format-aware writers.
6. **Reader expressivity round-2** — extend the constrained-slice readers to handle additional structures (definition lists, tables, footnotes, math) per pandoc surface.

Comparator-baseline policy is admitted in `trackers/NATIVE_WIDENED_ORACLE_PACKET_EVIDENCE.md` — per-report `oracle_version` is authoritative, mixed-version evidence allowed. The `_strip_attr_ids` normalization applied to one-sided / reparse-based / binary comparators is governed: it strips identifier slots, normalizes Plain↔Para, drops auto-injected meta keys (`jupyter`, `nbformat`, `kernelspec`, `language_info`, `date`, `identifier`, `generator`, `language`, `title`, `creator`, `rights`, `subject`), uniformly dedents CodeBlock content, flattens "section" Divs, drops empty-content anchor Span paragraphs, and collapses inline runs of Str/Space/SoftBreak. The strict `structured_json` comparator (native/json input) does NOT apply this normalization.
