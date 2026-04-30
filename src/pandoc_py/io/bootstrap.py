"""Register every shipping reader and writer with the global FormatRegistry.

Importing ``pandoc_py.io.bootstrap`` is idempotent: it ensures every format
that has a callable ``read_*`` / ``write_*`` entry point in ``readers/``
or ``writers/`` is also reachable via ``get_reader(name)`` / ``get_writer(name)``.

New format families register themselves here. The dispatcher in ``app.py``
asks the registry, so adding a format is a one-liner here plus the
implementation file — no edits to the dispatcher.
"""

from __future__ import annotations

from pandoc_py.readers.commonmark import read_commonmark
from pandoc_py.readers.commonmark_x import read_commonmark_x
from pandoc_py.readers.html import read_html
from pandoc_py.readers.markdown import read_markdown
from pandoc_py.readers.native import read_native
from pandoc_py.readers.pandoc_json import read_pandoc_json
from pandoc_py.writers.commonmark import write_commonmark
from pandoc_py.writers.commonmark_x import write_commonmark_x
from pandoc_py.writers.html import write_html
from pandoc_py.writers.markdown import write_markdown
from pandoc_py.writers.native import write_native
from pandoc_py.writers.pandoc_json import write_pandoc_json

from .adapters import _CallableReader, _CallableWriter
from .registry import register_reader, register_writer

_BOOTSTRAPPED = False


def bootstrap() -> None:
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return
    _BOOTSTRAPPED = True

    # Readers
    register_reader(_CallableReader('markdown', read_markdown))
    register_reader(_CallableReader('json', read_pandoc_json, aliases=('pandoc-json',)))
    register_reader(_CallableReader('commonmark', read_commonmark))
    register_reader(_CallableReader('commonmark_x', read_commonmark_x, aliases=('commonmark-x',)))
    register_reader(_CallableReader('html', read_html, aliases=('html5', 'xhtml')))
    register_reader(_CallableReader('native', read_native))

    # Writers
    register_writer(_CallableWriter('markdown', write_markdown))
    register_writer(_CallableWriter('json', write_pandoc_json, aliases=('pandoc-json',)))
    register_writer(_CallableWriter('html', write_html, aliases=('html5', 'xhtml')))
    register_writer(_CallableWriter('native', write_native, accepts_standalone=True))
    register_writer(_CallableWriter('commonmark', write_commonmark))
    register_writer(_CallableWriter('commonmark_x', write_commonmark_x, aliases=('commonmark-x',)))


bootstrap()
