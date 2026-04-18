# Module admission evidence tranche (v40)

This tranche formally admits already-implemented module-family rows from the repo-scope seed into the governed matrix.

## Rows admitted
- INV-RD-MARKDOWN-001
- INV-WR-MARKDOWN-001
- INV-RD-COMMONMARK-001
- INV-WR-COMMONMARK-001
- INV-WR-HTML-001
- INV-WR-NATIVE-001
- INV-CLI-BIN-001

## New targeted evidence generated in v40
- `MOD-MD-MD-001` — markdown -> markdown byte match
- `MOD-MD-HTML-001` — markdown -> html normalized HTML match
- `MOD-MD-NATIVE-001` — markdown -> native round-trip JSON match
- `MOD-CM-JSON-001` — commonmark -> json structured JSON match
- `MOD-MD-CM-001` — markdown -> commonmark semantic round-trip match
- `MOD-HTMLIN-JSON-001` — html -> json structured JSON match

## Existing evidence anchors carried forward
- Existing markdown smoke reports in `tests/differential/reports/smoke/`
- Existing CommonMark smoke reports in `tests/differential/reports/smoke_commonmark/`
- Existing HTML-input and HTML-output smoke reports in `tests/differential/reports/smoke_html*`
- Existing native round-trip smoke reports in `tests/differential/reports/smoke_native/`
- `tests/unit/test_module_admission_surface.py`

## Admission rule
These rows are admitted because the code surface already exists in `src/pandoc_py`, and the bundle now contains both route-level differential evidence and direct module/entrypoint surface tests that exercise these module families under smoke coverage.
