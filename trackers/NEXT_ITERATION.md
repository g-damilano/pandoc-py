# Next iteration

Work on one of these packets, in this order of preference:

1. **Native-wrapper oracle admission packet** — now that `read_native` accepts top-level `Pandoc` wrappers with metadata (`nullMeta`, `Meta { unMeta = fromList ... }`, and `Meta*` values), run oracle-backed differential evidence for native -> json/html/native rails and upgrade `INV-RD-NATIVE-001` from `implemented_unverified` only after comparator reports are archived.
2. **Native metadata edge-policy packet** — declare and verify bounded policy for native metadata edge forms not yet admitted (if any), including explicit divergence logging for unsupported constructors or map encodings.
3. **Non-JSON markdown-output admission beyond JSON input** — widen semantic markdown round-trip verification beyond JSON input only after source-format-specific heading-id and metadata policy is declared explicitly.

Do not open DOCX, PPTX, ODT, EPUB, Lua breadth, citeproc breadth, or broad writer-option work in the next round. Native wrapper verification should be governed before another broad frontier is opened.
