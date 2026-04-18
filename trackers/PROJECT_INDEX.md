# Project index

Operational quick links:

- Master index: `INDEX.md`
- AI entrypoint: `docs/00_program/AI_START_HERE.md`
- Iteration protocol: `docs/00_program/ITERATION_PROTOCOL.md`
- Operating model: `docs/00_program/OPERATING_MODEL.md`
- Haskell repo inventory: `docs/01_architecture/HASKELL_REPO_INVENTORY.md`
- Scope gaps: `docs/01_architecture/HASKELL_REPO_SCOPE_GAPS.md`
- Capability contract: `docs/03_contracts/CAPABILITY_CONTRACT.md`
- Verification contract: `docs/03_contracts/VERIFICATION_CONTRACT.md`
- Current work packet: `trackers/NEXT_ITERATION.md`
- Active execution matrix: `trackers/CAPABILITY_MATRIX.csv`
- Repo-scope Haskell seed: `trackers/HASKELL_CAPABILITY_SEED.csv`
- Haskell module inventory: `trackers/HASKELL_MODULE_INVENTORY.csv`
- Implementation log: `trackers/IMPLEMENTATION_LOG.md`
- Verification status: `trackers/VERIFICATION_STATUS.md`
- Iteration state: `trackers/ITERATION_STATE.yaml`
- Work packet template: `trackers/WORK_PACKET_TEMPLATE.md`
- Control-plane status: `trackers/CONTROL_PLANE_STATUS.md`

## Latest milestone

- Pandoc JSON reader family landed across the current AST slice and is verified on JSON-input differential rails for structured JSON, normalized HTML, and round-trip native output.
- External AST source anchoring is now structurally mitigated through a local `pandoc-types` definition-source anchor; the next structural move is to pin package-version provenance and start merging repo-scope rows more honestly.

- v36: admitted first repo-scope control tranche (app/options/parsing + external AST dependency) into the governed denominator.

- v38: admitted first HTML-input reader tranche with structured JSON, normalized HTML, native round-trip, and CommonMark-safe rails.
- v39: closed the first HTML-input divergence tranche (ordered-list delimiter, table structural fidelity, display-math line breaks) and admitted those cases into the governed matrix.

- v40: module-admission tranche widened the governed denominator by admitting already-implemented markdown/commonmark/html/native module-family seed rows and CLI bin entrypoint.

- v41: admitted the metadata/front-matter tranche with explicit metadata AST values, markdown YAML front-matter ingestion, and Pandoc JSON meta parity on structured JSON rails.


- v42: hardened the control plane with an operating model, work-packet contract, machine-readable iteration state, and a validator that checks structural consistency and version drift.

- v43: widened the active governed denominator by admitting all remaining coarse repo-scope Haskell inventory rows, so conversion progress now reflects mapped-but-unimplemented families instead of hiding them outside the matrix.

- v44: landed the CommonMark_X honesty packet with a dedicated commonmark_x reader/writer surface, source-aware downstream parity rules, and 38 oracle-backed commonmark_x differential reports.

- v45: widened commonmark_x breadth with six additional oracle-backed markdown-safe behaviors (inline block quotes, emphasis, strong, plain paragraph, two paragraphs, thematic break) via 24 new differential reports.

- v46: widened commonmark_x breadth with thirteen additional oracle-backed markdown-safe behaviors (code-span/link/softbreak paragraphs, ATX headings, list-safe cases, heading-inline cases, and URI/email autolinks) via 52 new differential reports.

- v47: widened commonmark_x structural breadth with Setext headings, bracketed spans, heading/link attribute blocks, and trailing-two-space hard-break paragraphs.

- v48: closed the remaining doubled-backslash parity gap and widened commonmark_x breadth with raw inline HTML tags, fenced code blocks, inline/display math, reference-style links, and inline image attributes via 28 new differential reports.

- v49: widened commonmark_x breadth with fourteen additional oracle-backed behaviors (definition lists, fenced div/code-attrs, reference footnotes/images, raw inline comment/attr syntax, strikeout/subscript-superscript, indented code, and titled image/link variants) via 56 new differential reports.

- v50: closed the next bounded commonmark_x divergence packet: task-list markers now stay literal on the dedicated surface, inline footnote syntax stays literal, and raw HTML comment/fenced/script/hr blocks preserve terminal newlines without double-newline round-trip drift.

- v51: opened the JSON-input breadth frontier with 22 oracle-generated JSON fixtures admitted on json/html/native rails.

- v52: continued JSON-input breadth with 21 additional oracle-generated fixtures, including heading-inline, link, list, and context-safe paragraph forms.

- v53: closed the current JSON-input screen corpus by admitting the remaining 15 oracle-generated fixtures, including author/locator citations, code-context cases, continuation footnotes, loose ordered nesting, aligned/simple tables, raw TeX/LaTeX forms, and contextual thematic breaks.
- v54: settled the `json -> markdown` semantic comparator, fixed heading-attribute spacing in the markdown writer, and admitted 58 JSON-input behaviors on the markdown round-trip rail.
