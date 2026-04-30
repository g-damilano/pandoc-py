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
- oracle-backed reports archived: **yes** (8/8 passed on 2026-04-30 against pandoc 3.8.2 on a Windows runner)
- supplement rows promoted to `verified_smoke`: **yes** (all 13 target rows in `trackers/CAPABILITY_MATRIX_NATIVE_SUPPLEMENT.csv`)

## Execution environment requirement

The runbook above must satisfy:

1. The oracle binary is reachable. As of the 2026-04-30 runner-portability infrastructure update, `scripts/run_differential.py` now resolves the oracle in this order: `PANDOC_ORACLE` env var, then `/usr/bin/pandoc`, then `C:\Program Files\Pandoc\pandoc.exe`, then `which pandoc`. Each report records the resolved oracle path and version.
2. The oracle pandoc version is recorded in every archived report. Historical reports were produced with `pandoc 3.1.11.1`. Newer reports may be produced with later 3.x releases (for example `pandoc 3.8.2`); the report file itself is the source of truth for which version was used. A passing report at version `Y` is honest evidence that pandoc_py output matches pandoc `Y`'s output at the comparator level declared. It is **not** evidence about other versions.

### Comparator-baseline policy (admitted 2026-04-30)

- Each report records `oracle_version` directly. That string is authoritative for that report.
- A row may be promoted from `implemented_unverified` to `verified_smoke` once at least one passing oracle-backed report exists for the row's comparator policy. The oracle version of that report becomes part of the row's evidence trail.
- If a later run on a different oracle version produces a divergent result for the same fixture, that divergence must be archived alongside the previous report; it does not retroactively invalidate the earlier promotion but does add a known-divergence note to the supplement matrix.
- The runner is therefore free to use any pandoc 3.x oracle that resolves on the host. Promotion remains gated only on a passing report at the declared comparator level.

## Execution attempts

### 2026-04-30 (Windows worktree, pandoc 3.8.2)

- ran on a Windows worktree against `pandoc 3.8.2` at `C:\Program Files\Pandoc\pandoc.exe`
- `scripts/run_differential.py` was updated to resolve the oracle via `PANDOC_ORACLE` env var → `/usr/bin/pandoc` → Windows default → `which pandoc`
- fixtures revised to remove `Null` block (pandoc-types 1.23+ dropped it from the native parser); test for nullMeta alias also adjusted
- HTML writer aligned to oracle 3.x output: `<u>` for Underline, flat `<br />`-separated line-block, no `class="header"`/`class="odd"` table row classes
- native writer aligned to oracle: non-standalone mode emits block list only (drops meta), standalone emits Pandoc wrapper
- Para vs Plain distinction added to AST as `Paragraph.is_plain: bool | None` for round-trip fidelity
- all 8 reports passed; archived under `tests/differential/reports/smoke_native_input_widened/`
- 13 supplement rows promoted from `implemented_unverified` to `verified_smoke`
