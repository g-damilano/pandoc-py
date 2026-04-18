# Verification status

- Active matrix: 287 rows, all smoke-verified or better.
- v39 HTML-input closure tranche: the previously excluded ordered-list, table, and display-math HTML-input cases are now admitted on JSON/HTML/native rails.
- Targeted unit regressions across HTML reader surface, Pandoc JSON reader table coverage, HTML writer, native writer, and CLI versioning are green.
- HTML-input closure corpus: 9/9 oracle-backed reports passing across 3 fixtures on 3 rails.
- Curated HTML-input corpus: 48/48 oracle-backed reports passing across 16 fixtures on JSON/HTML/native rails.
- Curated CommonMark-safe HTML corpus: 5/5 oracle-backed reports passing on the CommonMark round-trip rail.
- Package version: pandoc_py 0.0.39.
- Existing markdown/json/html/native/CommonMark route verification remains intact for the active slice.


- v40 module-admission tranche tied module-family seed rows to existing smoke corpora and executable entrypoint tests.

- v40 targeted module evidence: 34 unit tests passed; 6 new oracle-backed module_tranche reports passed (markdown, commonmark, html writer/input, native writer, cli entry surface).
