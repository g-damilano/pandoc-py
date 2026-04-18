# Next iteration

Work on one of these packets, in this order of preference:

1. **Metadata/native input packet** — add the next constrained metadata-emission or native-input route only if its comparator and non-oracle implementation contract are declared before implementation and the acceptance rows are added to the matrix first.
2. **Targeted raw/TeX writer closure** — only if needed for the metadata/native packet, tighten raw/TeX writer semantics under existing comparators without opening broad writer-option scope.
3. **Non-JSON markdown-output admission** — widen semantic markdown round-trip verification beyond JSON input only after source-format-specific heading-id and metadata policy is declared explicitly.

Do not open DOCX, PPTX, ODT, EPUB, Lua breadth, citeproc breadth, or broad writer-option work in the next round. The `json -> markdown` route is now governed; the next packet should change frontier, not simply relabel the same writer rail.
