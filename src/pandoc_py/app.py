from __future__ import annotations

from pandoc_py.readers.commonmark import CommonmarkScopeError, read_commonmark
from pandoc_py.readers.commonmark_x import read_commonmark_x
from pandoc_py.readers.html import HtmlReaderError, read_html
from pandoc_py.readers.markdown import MarkdownScopeError, read_markdown
from pandoc_py.readers.native import NativeReaderError, read_native
from pandoc_py.readers.pandoc_json import PandocJsonReaderError, read_pandoc_json
from pandoc_py.writers.commonmark import CommonmarkWriterError, write_commonmark
from pandoc_py.writers.commonmark_x import write_commonmark_x
from pandoc_py.writers.html import HtmlWriterError, write_html
from pandoc_py.writers.markdown import MarkdownWriterError, write_markdown
from pandoc_py.writers.native import NativeWriterError, write_native
from pandoc_py.writers.pandoc_json import PandocJsonWriterError, write_pandoc_json


class AppError(RuntimeError):
    """Raised when the requested conversion route is unsupported."""


SUPPORTED_INPUT_FORMATS = frozenset({'markdown', 'json', 'commonmark', 'commonmark_x', 'html', 'native'})
SUPPORTED_OUTPUT_FORMATS = frozenset({'markdown', 'json', 'html', 'native', 'commonmark', 'commonmark_x'})


def read_document(source: str, from_format: str):
    if from_format == 'markdown':
        return read_markdown(source)
    if from_format == 'json':
        return read_pandoc_json(source)
    if from_format == 'commonmark':
        return read_commonmark(source)
    if from_format == 'commonmark_x':
        return read_commonmark_x(source)
    if from_format == 'html':
        return read_html(source)
    if from_format == 'native':
        return read_native(source)
    raise AppError(f'Unsupported input format: {from_format}')


def write_document(document, to_format: str, *, standalone: bool = False) -> str:
    if to_format == 'markdown':
        return write_markdown(document)
    if to_format == 'json':
        return write_pandoc_json(document)
    if to_format == 'html':
        return write_html(document)
    if to_format == 'native':
        return write_native(document, standalone=standalone)
    if to_format == 'commonmark':
        return write_commonmark(document)
    if to_format == 'commonmark_x':
        return write_commonmark_x(document)
    raise AppError(f'Unsupported output format: {to_format}')


def convert_text(source: str, from_format: str, to_format: str, *, standalone: bool = False) -> str:
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
