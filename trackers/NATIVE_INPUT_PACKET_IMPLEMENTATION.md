# Native input packet — implementation status

## Status

Implemented in code, widened beyond the initial block-list-only tranche, but not yet formally admitted into the governed capability matrix.

## Landed code surface

- `src/pandoc_py/readers/native.py`
- `src/pandoc_py/app.py`
- `src/pandoc_py/readers/__init__.py`
- `src/pandoc_py/__init__.py` (`0.0.56`)
- `tests/unit/test_native_reader_surface.py`

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

## Remaining fail-closed boundary

The code is landed, but the wrapper + metadata tranche is not yet formally governed on oracle-backed differential rails. The next honest step is evidence and matrix admission, not opening a new broad format family.

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
- `CLI-NATIVE-INPUT-001`
- `VER-NATIVE-READER-SURFACE-001`

## Working percentage impact once admitted as implemented-unverified

Starting from the published governed state of `500 / 589`, admitting the widened native-input tranche above would move the implemented-or-better count to approximately `511 / 599` = `85.3%`.

This is still a working estimate only until the capability matrix and progress report are regenerated from the repository state.
