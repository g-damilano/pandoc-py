# Native input packet — implementation status

## Status

Implemented in code, widened beyond the initial block-list-only tranche, and now extended through the markdown and HTML writers for the newly admitted native-only nodes. It is still not yet formally admitted into the governed capability matrix.

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

## Remaining fail-closed boundary

The code is landed, but the widened native packet is not yet formally governed on oracle-backed differential rails. The next honest step is evidence and matrix admission, not opening a new broad format family.

## Recommended matrix-admission rows for the next formal tracker update

- `INV-RD-NATIVE-001` -> `implemented_unverified`
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

## Working percentage impact once admitted as implemented-unverified

Starting from the published governed state of `500 / 589`, admitting the widened native packet above would move the implemented-or-better count to approximately `514 / 602` = `85.4%`.

This is still a working estimate only until the capability matrix and progress report are regenerated from the repository state.
