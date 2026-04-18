from __future__ import annotations

from pandoc_py.ast import (
    Attr,
    BlockQuote,
    BulletList,
    Code,
    CodeBlock,
    Document,
    Emph,
    HardBreak,
    Heading,
    Image,
    Link,
    OrderedList,
    Paragraph,
    RawBlock,
    RawInline,
    SoftBreak,
    Space,
    Str,
    Strong,
    ThematicBreak,
)
from pandoc_py.writers.markdown import MarkdownWriterError, write_markdown


class CommonmarkWriterError(TypeError):
    """Raised when the current AST slice cannot be rendered to CommonMark."""


def _ensure_attr_empty(attr: Attr, *, context: str) -> None:
    if attr.identifier or attr.classes or attr.attributes:
        raise CommonmarkWriterError(f'{context} attributes are outside the current CommonMark writer slice.')


def _ensure_inline_supported(inline) -> None:
    if isinstance(inline, (Str, Space, SoftBreak, HardBreak, Code, Emph, Strong)):
        return
    if isinstance(inline, Link):
        _ensure_attr_empty(inline.attr, context='Link')
        for child in inline.inlines:
            _ensure_inline_supported(child)
        return
    if isinstance(inline, Image):
        _ensure_attr_empty(inline.attr, context='Image')
        for child in inline.inlines:
            _ensure_inline_supported(child)
        return
    if isinstance(inline, RawInline):
        if inline.format != 'html':
            raise CommonmarkWriterError('Only raw HTML inlines are inside the current CommonMark writer slice.')
        return
    raise CommonmarkWriterError(f'Unsupported inline node for current CommonMark writer slice: {type(inline).__name__}')


def _ensure_block_supported(block) -> None:
    if isinstance(block, Paragraph):
        for inline in block.inlines:
            _ensure_inline_supported(inline)
        return
    if isinstance(block, Heading):
        _ensure_attr_empty(block.attr, context='Heading')
        for inline in block.inlines:
            _ensure_inline_supported(inline)
        return
    if isinstance(block, ThematicBreak):
        return
    if isinstance(block, CodeBlock):
        _ensure_attr_empty(block.attr, context='CodeBlock')
        return
    if isinstance(block, RawBlock):
        if block.format != 'html':
            raise CommonmarkWriterError('Only raw HTML blocks are inside the current CommonMark writer slice.')
        return
    if isinstance(block, BlockQuote):
        for child in block.blocks:
            _ensure_block_supported(child)
        return
    if isinstance(block, BulletList):
        for item in block.items:
            for child in item:
                _ensure_block_supported(child)
        return
    if isinstance(block, OrderedList):
        for item in block.items:
            for child in item:
                _ensure_block_supported(child)
        return
    raise CommonmarkWriterError(f'Unsupported block node for current CommonMark writer slice: {type(block).__name__}')


def write_commonmark(document: Document) -> str:
    for block in document.blocks:
        _ensure_block_supported(block)
    try:
        return write_markdown(Document(blocks=list(document.blocks), source_format=document.source_format))
    except MarkdownWriterError as exc:
        raise CommonmarkWriterError(str(exc)) from exc
