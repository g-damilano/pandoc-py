# Widened native oracle packet evidence

This packet is the **oracle-backed verification bundle** for the widened native supplement rows admitted in `trackers/CAPABILITY_MATRIX_NATIVE_SUPPLEMENT.csv`.

It is intentionally split into two states:

1. **verification bundle prepared** — fixtures, report IDs, comparator policy, and target rows are declared in-repo
2. **verification bundle executed** — oracle-backed differential reports are archived and the supplement rows are upgraded from `implemented_unverified` to verified states

At present, this document settles state **(1)** only. It does **not** claim that the widened native oracle reports have already been executed.

## Target rows

- `RD-NATIVE-CORE-001`
- `RD-NATIVE-INLINE-001`
- `RD-NATIVE-ATTR-001`
- `RD-NATIVE-BLOCKS-001`
- `RD-NATIVE-TABLE-FIGURE-001`
- `RD-NATIVE-NOTE-CITE-MATH-001`
- `RD-NATIVE-META-001`
- `RD-NATIVE-WRAPPER-001`
- `WR-MD-NATIVE-WIDENED-001`
- `WR-HTML-NATIVE-WIDENED-001`
- `CLI-NATIVE-INPUT-001`
- `VER-NATIVE-READER-SURFACE-001`
- `VER-NATIVE-WIDENED-OUTPUT-SURFACE-001`

## Comparator policy

### `native -> json`
- comparison level: `structured_json`
- oracle output: `pandoc -f native -t json`
- python output: `pandoc_py --from native --to json`
- pass condition: exact structured JSON equality

### `native -> html`
- comparison level: `normalized_html`
- oracle output: `pandoc -f native -t html --mathjax --no-highlight --wrap=none`
- python output: `pandoc_py --from native --to html`
- pass condition: normalized HTML fragment equality

### `native -> native`
- comparison level: `roundtrip_native_json`
- oracle output: `pandoc -f native -t native --wrap=none`
- python output: `pandoc_py --from native --to native`
- pass condition: both native outputs reparse through the oracle native parser to identical structured JSON

### `native -> markdown`
- comparison level: `roundtrip_markdown_json`
- oracle output: `pandoc -f native -t markdown --wrap=none`
- python output: `pandoc_py --from native --to markdown`
- pass condition: both markdown outputs reparse through the oracle markdown parser to identical structured JSON

## Fixtures admitted into the verification bundle

- `tests/fixtures/smoke_native_input_widened/native_widened_wrapper.native`
- `tests/fixtures/smoke_native_input_widened/native_widened_blocks.native`

## Planned report IDs

### wrapper fixture
- `SMOKE-NATIVEW-JSON-001`
- `SMOKE-NATIVEW-HTML-001`
- `SMOKE-NATIVEW-NATIVE-001`
- `SMOKE-NATIVEW-MD-001`

### block-list fixture
- `SMOKE-NATIVEW-JSON-002`
- `SMOKE-NATIVEW-HTML-002`
- `SMOKE-NATIVEW-NATIVE-002`
- `SMOKE-NATIVEW-MD-002`

## Runbook

From the repository root, execute:

```bash
python scripts/run_differential.py tests/fixtures/smoke_native_input_widened/native_widened_wrapper.native --from native --to json --report-id SMOKE-NATIVEW-JSON-001 --report-dir tests/differential/reports/smoke_native_input_widened
python scripts/run_differential.py tests/fixtures/smoke_native_input_widened/native_widened_wrapper.native --from native --to html --report-id SMOKE-NATIVEW-HTML-001 --report-dir tests/differential/reports/smoke_native_input_widened
python scripts/run_differential.py tests/fixtures/smoke_native_input_widened/native_widened_wrapper.native --from native --to native --report-id SMOKE-NATIVEW-NATIVE-001 --report-dir tests/differential/reports/smoke_native_input_widened
python scripts/run_differential.py tests/fixtures/smoke_native_input_widened/native_widened_wrapper.native --from native --to markdown --report-id SMOKE-NATIVEW-MD-001 --report-dir tests/differential/reports/smoke_native_input_widened
python scripts/run_differential.py tests/fixtures/smoke_native_input_widened/native_widened_blocks.native --from native --to json --report-id SMOKE-NATIVEW-JSON-002 --report-dir tests/differential/reports/smoke_native_input_widened
python scripts/run_differential.py tests/fixtures/smoke_native_input_widened/native_widened_blocks.native --from native --to html --report-id SMOKE-NATIVEW-HTML-002 --report-dir tests/differential/reports/smoke_native_input_widened
python scripts/run_differential.py tests/fixtures/smoke_native_input_widened/native_widened_blocks.native --from native --to native --report-id SMOKE-NATIVEW-NATIVE-002 --report-dir tests/differential/reports/smoke_native_input_widened
python scripts/run_differential.py tests/fixtures/smoke_native_input_widened/native_widened_blocks.native --from native --to markdown --report-id SMOKE-NATIVEW-MD-002 --report-dir tests/differential/reports/smoke_native_input_widened
```

## Promotion rule

Only after all admitted reports above pass and are archived under `tests/differential/reports/smoke_native_input_widened/` may the supplement rows be upgraded from `implemented_unverified` to `verified_smoke`.

## Current honest status

- verification bundle prepared: **yes**
- oracle-backed reports archived: **no claim yet**
- supplement rows promoted to `verified_smoke`: **not yet**
