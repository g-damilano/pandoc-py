# Metadata / front-matter tranche evidence

Admitted in v41.

## Scope admitted

- YAML metadata blocks on markdown input
- scalar/bool/list/map/block metadata coercion into the active AST slice
- Pandoc JSON meta payload read/write parity
- dedicated metadata reader module surface tests

## Differential evidence

### Markdown with front matter -> JSON

- `SMOKE-META-MD-JSON-001` `meta_basic.md`
- `SMOKE-META-MD-JSON-002` `meta_nested.md`
- `SMOKE-META-MD-JSON-003` `meta_blocks.md`

Result: **3/3 passing** on structured JSON equality.

### JSON with meta -> JSON

- `SMOKE-META-JSON-JSON-001` `meta_basic.json`
- `SMOKE-META-JSON-JSON-002` `meta_nested.json`
- `SMOKE-META-JSON-JSON-003` `meta_blocks.json`

Result: **3/3 passing** on structured JSON equality.

## Unit evidence

- `tests/unit/test_metadata_surface.py`

Result: **5/5 passing**.

## Explicit non-admissions

- CommonMark metadata remains outside the admitted tranche until `commonmark_x` is separated from strict `commonmark` in the user-facing format layer.
- Markdown/CommonMark writer-side metadata emission is not admitted in this tranche.
