from __future__ import annotations

from pandoc_py.ast import (
    Attr,
    BlockQuote,
    BulletList,
    Code,
    CodeBlock,
    Document,
    Emph,
    Figure,
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
from pandoc_py.readers.markdown import MarkdownScopeError, read_markdown


class CommonmarkScopeError(ValueError):
    """Raised when the input falls outside the current CommonMark slice."""


def _ensure_attr_empty(attr: Attr, *, context: str) -> None:
    if attr.identifier or attr.classes or attr.attributes:
        raise CommonmarkScopeError(f'{context} attributes are outside the current CommonMark slice.')


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
            raise CommonmarkScopeError('Only raw HTML inlines are inside the current CommonMark slice.')
        return
    raise CommonmarkScopeError(f'Unsupported inline node for current CommonMark slice: {type(inline).__name__}')


def _ensure_paragraph_supported(block: Paragraph) -> None:
    for inline in block.inlines:
        _ensure_inline_supported(inline)


def _ensure_block_supported(block) -> None:
    if isinstance(block, Paragraph):
        _ensure_paragraph_supported(block)
        return
    if isinstance(block, Heading):
        _ensure_attr_empty(block.attr, context='Heading')
        for inline in block.inlines:
            _ensure_inline_supported(inline)
        return
    if isinstance(block, ThematicBreak):
        return
    if isinstance(block, CodeBlock):
        _ensure_attr_empty(Attr(identifier=block.attr.identifier, classes=block.attr.classes, attributes=block.attr.attributes), context='CodeBlock')
        return
    if isinstance(block, RawBlock):
        if block.format != 'html':
            raise CommonmarkScopeError('Only raw HTML blocks are inside the current CommonMark slice.')
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
    if isinstance(block, Figure):
        raise CommonmarkScopeError('Figure blocks are outside the current CommonMark slice.')
    raise CommonmarkScopeError(f'Unsupported block node for current CommonMark slice: {type(block).__name__}')


def read_commonmark(source: str) -> Document:
    try:
        document = read_markdown(source)
    except MarkdownScopeError as exc:
        raise CommonmarkScopeError(str(exc)) from exc
    if document.meta:
        raise CommonmarkScopeError('YAML metadata blocks are outside the current CommonMark slice.')
    for block in document.blocks:
        _ensure_block_supported(block)
    return Document(blocks=list(document.blocks), meta=dict(document.meta), source_format='commonmark')
