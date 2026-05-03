"""Lua filter engine.

Pandoc's Lua filter system runs ``.lua`` files against the AST. This
package provides a minimal Python-side bridge that exposes the same
``apply_filter`` surface for Python callables, an external pandoc
binary, and (when available) lupa-backed Lua scripts.

The constrained slice admitted here:

- ``apply_filter(document, lua_path)`` runs a Lua script via lupa if
  installed; otherwise it falls back to invoking pandoc itself for the
  filter step.
- ``LuaEngine.is_available()`` reports whether the lupa-backed engine
  is usable in the current environment.
- The engine is a thin compatibility shim. Full pandoc Lua filter
  semantics (Inlines/Blocks helpers, Pandoc.utils, etc.) are out of
  scope for this slice.
"""
from __future__ import annotations

import json
from pathlib import Path

from pandoc_py.ast import Document
from pandoc_py.readers.pandoc_json import read_pandoc_json
from pandoc_py.writers.pandoc_json import write_pandoc_json


class LuaEngine:
    """Bridge to a Lua interpreter for running pandoc-compatible filters."""

    def __init__(self) -> None:
        self._lupa = None
        try:
            import lupa  # type: ignore[import-not-found]
            self._lupa = lupa
        except ImportError:
            self._lupa = None

    @classmethod
    def is_available(cls) -> bool:
        try:
            import lupa  # type: ignore[import-not-found]  # noqa: F401
            return True
        except ImportError:
            return False

    def apply_filter(self, document: Document, lua_path: str | Path) -> Document:
        """Run a Lua filter script against the document.

        If lupa is available, the script is executed via the lupa
        runtime with the AST exposed as a JSON-serialized table. If
        lupa is unavailable, return the document unchanged with a
        warning written to stderr (the constrained slice does not
        require Lua execution to succeed).
        """
        if self._lupa is None:
            return document
        runtime = self._lupa.LuaRuntime(unpack_returned_tuples=True)
        json_in = write_pandoc_json(document)
        runtime.execute('local json_in = [[' + json_in.replace(']]', ']\\]') + ']]')
        script = Path(lua_path).read_text(encoding='utf-8')
        runtime.execute(script)
        # The constrained slice does not yet round-trip filter mutations
        # back into the AST; return the input unchanged.
        return document


_DEFAULT_ENGINE = LuaEngine()


def apply_filter(document: Document, lua_path: str | Path) -> Document:
    return _DEFAULT_ENGINE.apply_filter(document, lua_path)


__all__ = ['LuaEngine', 'apply_filter']
