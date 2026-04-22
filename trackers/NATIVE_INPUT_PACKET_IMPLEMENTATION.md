# Native input packet — implementation status

## Status

Implemented in code, widened beyond the initial block-list-only tranche, extended through the markdown and HTML writers for the newly admitted native-only nodes, and now admitted into the governed tracker via a native supplement matrix. It is not yet smoke-verified on oracle-backed differential rails for the widened packet.

## Landed code surface

- `src/pandoc_py/readers/native.py`
- `src/pandoc_py/app.py`
- `src/pandoc_py/readers/__init__.py`
- `src/pandoc_py/writers/pandoc_json.py`
- `src/pandoc_py/writers/native.py`
- `src/pandoc_py/writers/markdown.py`
- `src/pandoc_py/writers/html.py`
- `src/pandoc_py/__init__.py` (`0.0.57`)
- `tests/unit/test_native_reader_surface.py`
- `tests/unit/test_native_widened_output_surface.py`
- `trackers/CAPABILITY_MATRIX_NATIVE_SUPPLEMENT.csv`

## Current implemented scope

The native reader now accepts all of the following current-slice native surfaces:

- top-level `Pandoc (...) [...]` wrapper
- `nullMeta` and `Meta {unMeta = ...}` metadata payloads
- block-list native surface
- single-block payloads
- inline-list payloads coerced to a paragraph
- single-inline payloads coerced to a paragraph

Across those entry shapes, the active AST slice now covers:

- paragraphs and headings
- attrs
- links and images
- block quotes
- bullet and ordered lists
- definition lists
- figures
- simple tables
- notes
- citations
- math
- raw HTML
- raw TeX / LaTeX
- metadata values in the admitted AST family: `MetaBool`, `MetaString`, `MetaInlines`, `MetaBlocks`, `MetaList`, and `MetaMap`
- widened native-only nodes flowing through end-to-end output rails: `Underline`, `SmallCaps`, `Quoted`, `LineBlock`, and `Null`

## Remaining boundary

The widened native packet is now governed for implemented progress, but it is not yet formally smoke-verified on oracle-backed differential rails. The next honest step is evidence and row upgrades from `implemented_unverified` to verified states.

## Admitted supplement rows

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

## Published progress impact after tracker catch-up

After admitting the native supplement matrix into the governed progress script, the published implemented-or-better count moves from `500 / 589` to `513 / 602` = `85.2%`.

The smoke-verified-or-better count remains `500 / 602` = `83.1%` until oracle-backed widened-native evidence is archived and the corresponding rows are upgraded.
