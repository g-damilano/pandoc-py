"""Top-level conversion entry points.

This module dispatches read and write requests through the
``pandoc_py.io`` registry. Every shipping format family — markdown, json,
html, native, commonmark/_x, plus all formats under ``pandoc_py.formats``
— self-registers at import time, so adding a new format requires no edits
here.

The legacy callable entry points (``read_markdown``, ``write_html``, …)
remain available from their original modules; the dispatcher just looks
them up via the registry.
"""

from __future__ import annotations

# Import side-effect: register every reader/writer with the registry.
from pandoc_py import io as _io  # noqa: F401  (triggers package init)
from pandoc_py import formats as _formats  # noqa: F401

from pandoc_py.ast import Document
from pandoc_py.io import (
    Reader,
    Writer,
    WriteOptions,
    get_reader,
    get_writer,
    list_readers,
    list_writers,
)
from pandoc_py.io.registry import _GLOBAL  # for SUPPORTED_* derivation
from pandoc_py.readers.commonmark import CommonmarkScopeError
from pandoc_py.readers.html import HtmlReaderError
from pandoc_py.readers.markdown import MarkdownScopeError
from pandoc_py.readers.native import NativeReaderError
from pandoc_py.readers.pandoc_json import PandocJsonReaderError
from pandoc_py.writers.commonmark import CommonmarkWriterError
from pandoc_py.writers.html import HtmlWriterError
from pandoc_py.writers.markdown import MarkdownWriterError
from pandoc_py.writers.native import NativeWriterError
from pandoc_py.writers.pandoc_json import PandocJsonWriterError


class AppError(RuntimeError):
    """Raised when the requested conversion route is unsupported."""


def _supported_readers() -> frozenset[str]:
    names = set(_GLOBAL.list_readers())
    names.update(_GLOBAL._reader_aliases.keys())
    return frozenset(names)


def _supported_writers() -> frozenset[str]:
    names = set(_GLOBAL.list_writers())
    names.update(_GLOBAL._writer_aliases.keys())
    return frozenset(names)


SUPPORTED_INPUT_FORMATS = _supported_readers()
SUPPORTED_OUTPUT_FORMATS = _supported_writers()


def read_document(source, from_format: str) -> Document:
    try:
        reader: Reader = get_reader(from_format)
    except KeyError as exc:
        raise AppError(f'Unsupported input format: {from_format}') from exc
    return reader.read(source)


def write_document(document: Document, to_format: str, *, standalone: bool = False):
    try:
        writer: Writer = get_writer(to_format)
    except KeyError as exc:
        raise AppError(f'Unsupported output format: {to_format}') from exc
    return writer.write(document, options=WriteOptions(standalone=standalone))


def convert_text(source, from_format: str, to_format: str, *, standalone: bool = False):
    document = read_document(source, from_format)
    return write_document(document, to_format, standalone=standalone)


CONVERSION_EXCEPTIONS = (
    OSError,
    CommonmarkScopeError,
    MarkdownScopeError,
    PandocJsonReaderError,
    NativeReaderError,
    MarkdownWriterError,
    PandocJsonWriterError,
    HtmlWriterError,
    HtmlReaderError,
    NativeWriterError,
    CommonmarkWriterError,
    AppError,
)
