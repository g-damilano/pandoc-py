# CommonMark_X packet evidence

This tranche closes the strict `commonmark` vs `commonmark_x` honesty gap by admitting a dedicated `commonmark_x` reader/writer surface and verifying it against pinned Pandoc behavior.

## Scope admitted in v44

- dedicated CLI/app canonicalization for `commonmark_x`
- dedicated reader surface with `source_format=commonmark_x`
- metadata-bearing `commonmark_x` input
- attribute-bearing `commonmark_x` input
- downstream JSON/HTML/native semantics with generated heading ids preserved and autolink classes suppressed
- dedicated `commonmark_x` writer surface
- commonmark_x heading-attribute spacing parity
- standalone-image paragraph -> HTML figure parity on the admitted writer slice

## Oracle-backed report counts

### `commonmark_x` input rails

10 fixtures passed on each of 3 rails:

- JSON: 10/10
- HTML: 10/10
- native: 10/10

Fixtures:

- `atx_heading`
- `autolink_paragraph`
- `block_quote`
- `bracketed_span`
- `bullet_list`
- `fenced_code_attrs`
- `heading_attrs`
- `image_attrs_standalone`
- `link_attrs`
- `meta_basic`

### `commonmark_x` output rail

8 markdown-input fixtures passed on the `markdown -> commonmark_x` round-trip comparator:

- `atx_heading`
- `autolink_paragraph`
- `bracketed_span`
- `bullet_list`
- `fenced_code_attrs`
- `heading_attrs`
- `image_attrs_standalone`
- `link_attrs`

## Total differential evidence

- **38/38** oracle-backed differential reports passing

All reports live under `tests/differential/reports/smoke_commonmark_x/`.
