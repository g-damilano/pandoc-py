"""Adapters that wrap the existing functional readers/writers as Reader/Writer instances.

These adapters preserve every existing entry point (`read_markdown`,
`write_html`, etc.) — the callable layer is unchanged — while making each
format-family accessible through the OOP `FormatRegistry`. New format
families plug into the registry via the same Reader/Writer ABCs without
touching the dispatch in ``app.py``.
"""

from __future__ import annotations

from pandoc_py.ast import Document

from .base import Reader, ReadOptions, Writer, WriteOptions


class _CallableReader(Reader):
    """Wrap a `(source: str) -> Document` callable as a Reader."""

    def __init__(self, format_name: str, fn, aliases: tuple[str, ...] = ()) -> None:
        self.format_name = format_name
        self.aliases = aliases
        self._fn = fn

    def read(self, source: str | bytes, options: ReadOptions | None = None) -> Document:
        if isinstance(source, bytes):
            source = source.decode('utf-8')
        return self._fn(source)


class _CallableWriter(Writer):
    """Wrap a `(document, **kw) -> str` callable as a Writer.

    If the callable accepts a ``standalone`` keyword argument, the adapter
    forwards ``options.standalone``.
    """

    def __init__(self, format_name: str, fn, *, accepts_standalone: bool = False, aliases: tuple[str, ...] = ()) -> None:
        self.format_name = format_name
        self.aliases = aliases
        self._fn = fn
        self._accepts_standalone = accepts_standalone

    def write(self, document: Document, options: WriteOptions | None = None) -> str | bytes:
        opts = options or WriteOptions()
        if self._accepts_standalone:
            return self._fn(document, standalone=opts.standalone)
        return self._fn(document)
