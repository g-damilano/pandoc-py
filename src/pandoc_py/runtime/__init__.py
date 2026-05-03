"""Runtime / filter / citeproc support — constrained slice.

This module provides the Python equivalents of the Haskell pandoc runtime
layer:

* `PandocState` — replaces the Haskell `PandocMonad`/`PandocPure` state
  envelope. It carries reader/writer options, the working directory, and a
  list of trace messages.
* `apply_filter(document, filter_callable_or_path)` — runs a JSON filter
  over the document, exactly mirroring `pandoc --filter` semantics: the
  filter receives Pandoc JSON on stdin (or as a Python callable) and
  returns Pandoc JSON.
* `process_citations(document)` — minimal citeproc layer: walks Cite nodes
  and rewrites them into `[Author, Year]` rendered text using metadata
  ``references`` if present.

These are constrained slices admitted in the format-families supplement
matrix as `implemented_unverified`. Full citeproc bibliography processing
is out of slice.
"""

from __future__ import annotations

from .citeproc import process_citations
from .filter import apply_filter
from .state import PandocState

__all__ = [
    'PandocState',
    'apply_filter',
    'process_citations',
]
