# Native input packet — implementation status

## Status

Implemented in code, not yet formally admitted into the governed capability matrix.

## Landed code surface

- `src/pandoc_py/readers/native.py`
- `src/pandoc_py/app.py`
- `src/pandoc_py/readers/__init__.py`
- `src/pandoc_py/__init__.py` (`0.0.55`)
- `tests/unit/test_native_reader_surface.py`

## Current admitted scope of the implementation

The native reader currently accepts the block-list native surface and parses the existing active AST slice for:

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

## Explicit fail-closed boundary

Top-level `Pandoc ...` wrapper input carrying metadata remains outside the currently admitted native reader slice and should stay fail-closed until the comparator and metadata contract are declared explicitly.

## Recommended matrix-admission rows for the next formal tracker update

- `INV-RD-NATIVE-001` -> `implemented_unverified`
- `RD-NATIVE-CORE-001`
- `RD-NATIVE-INLINE-001`
- `RD-NATIVE-ATTR-001`
- `RD-NATIVE-BLOCKS-001`
- `RD-NATIVE-TABLE-FIGURE-001`
- `RD-NATIVE-NOTE-CITE-MATH-001`
- `CLI-NATIVE-INPUT-001`
- `VER-NATIVE-READER-SURFACE-001`

## Working percentage impact once admitted as implemented-unverified

Starting from the published governed state of `500 / 589`, admitting the native-input tranche above would move the implemented-or-better count to approximately `509 / 597` = `85.3%`.

This is a working estimate only until the capability matrix and progress report are regenerated from the repository state.
