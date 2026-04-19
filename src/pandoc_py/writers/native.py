from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field

from pandoc_py.ast import (
    Attr,
    Block,
    BlockQuote,
    BulletList,
    Citation,
    Cite,
    Code,
    CodeBlock,
    DefinitionList,
    Div,
    Document,
    Emph,
    Figure,
    HardBreak,
    Heading,
    Image,
    Link,
    Math,
    MetaBlocks,
    MetaBool,
    MetaInlines,
    MetaList,
    MetaMap,
    MetaString,
    MetaValue,
    LineBlock,
    Note,
    Null,
    OrderedList,
    Paragraph,
    Quoted,
    RawBlock,
    RawInline,
    SmallCaps,
    SoftBreak,
    Space,
    Span,
    Str,
    Strikeout,
    Strong,
    Subscript,
    Superscript,
    Underline,
    Table,
    ThematicBreak,
)


class NativeWriterError(TypeError):
    """Raised when the current AST slice cannot be rendered to Pandoc native."""


@dataclass
class _NativeWriterContext:
    slug_counts: Counter[str] = field(default_factory=Counter)
    citation_note_num: int = 1
    source_format: str = ''


InlineNode = Str | Space | SoftBreak | HardBreak | Emph | Strong | Strikeout | Subscript | Superscript | Underline | SmallCaps | Quoted | Math | Code | Span | Link | Image | RawInline | Note | Cite
BlockNode = Paragraph | LineBlock | Null | Heading | ThematicBreak | CodeBlock | RawBlock | BlockQuote | BulletList | OrderedList | DefinitionList | Div | Figure | Table

URI_AUTOLINK_ATTR = Attr(classes=['uri'])
EMAIL_AUTOLINK_ATTR = Attr(classes=['email'])


def _quoted(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)


def _attr_repr(attr: Attr) -> str:
    classes = '[' + ','.join(_quoted(c) for c in attr.classes) + ']'
    attributes = '[' + ','.join(f'({_quoted(k)},{_quoted(v)})' for k, v in attr.attributes) + ']'
    return f'({_quoted(attr.identifier)},{classes},{attributes})'


def _flatten_inline_text(inlines: list[InlineNode]) -> str:
    parts: list[str] = []
    for inline in inlines:
        if isinstance(inline, Str):
            parts.append(inline.text)
        elif isinstance(inline, (Space, SoftBreak, HardBreak)):
            parts.append(' ')
        elif isinstance(inline, (Emph, Strong, Strikeout, Subscript, Superscript, Underline, SmallCaps, Quoted, Span, Link, Image, Cite)):
            parts.append(_flatten_inline_text(inline.inlines))
        elif isinstance(inline, (Code, Math)):
            parts.append(inline.text)
        elif isinstance(inline, (RawInline, Note)):
            continue
        else:
            raise NativeWriterError(f'Unsupported inline node for heading identifier generation: {type(inline).__name__}')
    return ''.join(parts)


def _slugify_heading_text(text: str) -> str:
    normalized = unicodedata.normalize('NFKD', text)
    ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
    lowered = ascii_text.lower()
    slug = re.sub(r'[^a-z0-9.]+', '-', lowered).strip('-')
    if '://' in lowered:
        slug = slug.replace('-', '')
    return slug or 'section'


def _heading_attr(block: Heading, ctx: _NativeWriterContext) -> Attr:
    if block.attr.identifier:
        return block.attr
    if ctx.source_format == 'commonmark' and not block.attr.classes and not block.attr.attributes:
        return block.attr
    base = _slugify_heading_text(_flatten_inline_text(block.inlines))
    seen = ctx.slug_counts[base]
    ctx.slug_counts[base] += 1
    identifier = base if seen == 0 else f'{base}-{seen + 1}'
    return Attr(identifier=identifier, classes=list(block.attr.classes), attributes=list(block.attr.attributes))


def _link_attr(inline: Link, ctx: _NativeWriterContext) -> Attr:
    if inline.autolink and not inline.attr.identifier and not inline.attr.classes and not inline.attr.attributes:
        if ctx.source_format in {'commonmark', 'commonmark_x'}:
            return Attr()
        return EMAIL_AUTOLINK_ATTR if inline.target.startswith('mailto:') else URI_AUTOLINK_ATTR
    return inline.attr


def _paragraph_image_to_figure(block: Paragraph, source_format: str = '') -> Figure | None:
    if source_format in {'commonmark', 'commonmark_x'}:
        return None
    if len(block.inlines) != 1 or not isinstance(block.inlines[0], Image):
        return None
    image = block.inlines[0]
    return Figure(
        image=Image(
            inlines=image.inlines,
            target=image.target,
            title=image.title,
            attr=Attr(classes=list(image.attr.classes), attributes=list(image.attr.attributes)),
        ),
        attr=Attr(identifier=image.attr.identifier),
    )


def _item_is_compact(item: list[BlockNode | Block]) -> bool:
    return bool(item) and isinstance(item[0], Paragraph) and all(not isinstance(inline, (SoftBreak, HardBreak, Note)) for inline in item[0].inlines) and all(isinstance(block, (BulletList, OrderedList)) for block in item[1:])


def _citation_mode(mode: str) -> str:
    allowed = {'NormalCitation', 'AuthorInText', 'SuppressAuthor'}
    if mode not in allowed:
        raise NativeWriterError(f'Unsupported citation mode in current native writer slice: {mode}')
    return mode


def _inline_list(inlines: list[InlineNode], ctx: _NativeWriterContext) -> str:
    return '[' + ','.join(_inline_repr(inline, ctx) for inline in inlines) + ']'


def _block_list(blocks: list[BlockNode | Block], ctx: _NativeWriterContext, plain_in_list: bool = False) -> str:
    return '[' + ','.join(_block_repr(block, ctx, plain_in_list=plain_in_list) for block in blocks) + ']'


def _meta_value_repr(value: MetaValue, ctx: _NativeWriterContext) -> str:
    if isinstance(value, MetaBool):
        return f'MetaBool {"True" if value.value else "False"}'
    if isinstance(value, MetaString):
        return f'MetaString {_quoted(value.text)}'
    if isinstance(value, MetaInlines):
        return f'MetaInlines {_inline_list(value.inlines, ctx)}'
    if isinstance(value, MetaBlocks):
        return f'MetaBlocks {_block_list(value.blocks, ctx)}'
    if isinstance(value, MetaList):
        return 'MetaList [' + ','.join(_meta_value_repr(item, ctx) for item in value.items) + ']'
    if isinstance(value, MetaMap):
        entries = ','.join(f'({_quoted(key)},{_meta_value_repr(item, ctx)})' for key, item in value.mapping.items())
        return 'MetaMap [' + entries + ']'
    raise NativeWriterError(f'Unsupported metadata value for native writer: {type(value).__name__}')


def _meta_repr(meta: dict[str, MetaValue], ctx: _NativeWriterContext) -> str:
    if not meta:
        return 'nullMeta'
    entries = ','.join(f'({_quoted(key)},{_meta_value_repr(value, ctx)})' for key, value in meta.items())
    return 'Meta { unMeta = fromList [' + entries + '] }'


def _plain_para(inlines: list[InlineNode], ctx: _NativeWriterContext) -> str:
    return f'Plain {_inline_list(inlines, ctx)}'


def _plain_blocks(inlines: list[InlineNode], ctx: _NativeWriterContext) -> str:
    return '[' + _plain_para(inlines, ctx) + ']'


def _citation_repr(citation: Citation, ctx: _NativeWriterContext, note_num: int) -> str:
    return (
        'Citation '
        '{ citationId = ' + _quoted(citation.citation_id)
        + ', citationPrefix = ' + _inline_list(citation.prefix, ctx)
        + ', citationSuffix = ' + _inline_list(citation.suffix, ctx)
        + ', citationMode = ' + _citation_mode(citation.mode)
        + ', citationNoteNum = ' + str(note_num)
        + ', citationHash = ' + str(citation.hash)
        + ' }'
    )


def _inline_repr(inline: InlineNode, ctx: _NativeWriterContext) -> str:
    if isinstance(inline, Str):
        return f'Str {_quoted(inline.text)}'
    if isinstance(inline, Space):
        return 'Space'
    if isinstance(inline, SoftBreak):
        return 'SoftBreak'
    if isinstance(inline, HardBreak):
        return 'LineBreak'
    if isinstance(inline, Emph):
        return f'Emph {_inline_list(inline.inlines, ctx)}'
    if isinstance(inline, Strong):
        return f'Strong {_inline_list(inline.inlines, ctx)}'
    if isinstance(inline, Strikeout):
        return f'Strikeout {_inline_list(inline.inlines, ctx)}'
    if isinstance(inline, Subscript):
        return f'Subscript {_inline_list(inline.inlines, ctx)}'
    if isinstance(inline, Superscript):
        return f'Superscript {_inline_list(inline.inlines, ctx)}'
    if isinstance(inline, Underline):
        return f'Underline {_inline_list(inline.inlines, ctx)}'
    if isinstance(inline, SmallCaps):
        return f'SmallCaps {_inline_list(inline.inlines, ctx)}'
    if isinstance(inline, Quoted):
        if inline.quote_type not in {'SingleQuote', 'DoubleQuote'}:
            raise NativeWriterError(f'Unsupported quote type in current native writer slice: {inline.quote_type}')
        return f'Quoted {inline.quote_type} {_inline_list(inline.inlines, ctx)}'
    if isinstance(inline, Math):
        return f'Math {"DisplayMath" if inline.display else "InlineMath"} {_quoted(inline.text)}'
    if isinstance(inline, Code):
        return f'Code {_attr_repr(Attr())} {_quoted(inline.text)}'
    if isinstance(inline, Span):
        return f'Span {_attr_repr(inline.attr)} {_inline_list(inline.inlines, ctx)}'
    if isinstance(inline, Link):
        return f'Link {_attr_repr(_link_attr(inline, ctx))} {_inline_list(inline.inlines, ctx)} ({_quoted(inline.target)},{_quoted(inline.title)})'
    if isinstance(inline, Image):
        return f'Image {_attr_repr(inline.attr)} {_inline_list(inline.inlines, ctx)} ({_quoted(inline.target)},{_quoted(inline.title)})'
    if isinstance(inline, RawInline):
        return f'RawInline (Format {_quoted(inline.format)}) {_quoted(inline.text)}'
    if isinstance(inline, Note):
        return f'Note {_block_list(inline.blocks, ctx)}'
    if isinstance(inline, Cite):
        note_num = ctx.citation_note_num
        ctx.citation_note_num += 1
        citations = '[' + ','.join(_citation_repr(c, ctx, note_num) for c in inline.citations) + ']'
        return f'Cite {citations} {_inline_list(inline.inlines, ctx)}'
    raise NativeWriterError(f'Unsupported inline node for native writer: {type(inline).__name__}')


def _list_item_repr(item: list[BlockNode | Block], ctx: _NativeWriterContext, loose: bool) -> str:
    first_plain = (not loose) and _item_is_compact(item)
    parts = []
    for idx, subblock in enumerate(item):
        parts.append(_block_repr(subblock, ctx, plain_in_list=(idx == 0 and first_plain)))
    return '[' + ','.join(parts) + ']'


def _cell_repr(inlines: list[InlineNode], align: str, ctx: _NativeWriterContext) -> str:
    return f'Cell {_attr_repr(Attr())} {align} (RowSpan 1) (ColSpan 1) {_plain_blocks(inlines, ctx)}'


def _colspec_repr(align: str) -> str:
    if align not in {'AlignDefault', 'AlignLeft', 'AlignCenter', 'AlignRight'}:
        raise NativeWriterError(f'Unsupported column alignment in current native writer slice: {align}')
    return f'({align},ColWidthDefault)'


def _table_repr(block: Table, ctx: _NativeWriterContext) -> str:
    caption = f'(Caption Nothing {_plain_blocks(block.caption, ctx) if block.caption else "[]"})'
    colspecs = '[' + ','.join(_colspec_repr(align) for align in block.aligns) + ']'
    head_cells = '[' + ','.join(_cell_repr(cell, 'AlignDefault', ctx) for cell in block.headers) + ']'
    table_head = f'(TableHead {_attr_repr(Attr())} [Row {_attr_repr(block.header_row_attr)} {head_cells}])'
    body_rows = []
    for row_idx, row in enumerate(block.rows):
        cells = '[' + ','.join(_cell_repr(cell, 'AlignDefault', ctx) for cell in row) + ']'
        row_attr = block.row_attrs[row_idx] if row_idx < len(block.row_attrs) else Attr()
        body_rows.append(f'Row {_attr_repr(row_attr)} {cells}')
    bodies = '[TableBody ' + _attr_repr(Attr()) + ' (RowHeadColumns 0) [] [' + ','.join(body_rows) + ']]'
    foot = f'(TableFoot {_attr_repr(Attr())} [])'
    return f'Table {_attr_repr(Attr())} {caption} {colspecs} {table_head} {bodies} {foot}'


def _block_repr(block: BlockNode | Block, ctx: _NativeWriterContext, plain_in_list: bool = False) -> str:
    if isinstance(block, Paragraph):
        if not plain_in_list:
            figure = _paragraph_image_to_figure(block, ctx.source_format)
            if figure is not None:
                return _block_repr(figure, ctx)
        return f'{"Plain" if plain_in_list else "Para"} {_inline_list(block.inlines, ctx)}'
    if isinstance(block, Heading):
        return f'Header {block.level} {_attr_repr(_heading_attr(block, ctx))} {_inline_list(block.inlines, ctx)}'
    if isinstance(block, ThematicBreak):
        return 'HorizontalRule'
    if isinstance(block, Null):
        return 'Null'
    if isinstance(block, CodeBlock):
        classes = list(block.attr.classes)
        if block.info and block.info not in classes:
            classes.insert(0, block.info)
        attr = Attr(identifier=block.attr.identifier, classes=classes, attributes=list(block.attr.attributes))
        return f'CodeBlock {_attr_repr(attr)} {_quoted(block.text)}'
    if isinstance(block, RawBlock):
        return f'RawBlock (Format {_quoted(block.format)}) {_quoted(block.text)}'
    if isinstance(block, LineBlock):
        lines = '[' + ','.join(_inline_list(line, ctx) for line in block.lines) + ']'
        return f'LineBlock {lines}'
    if isinstance(block, BlockQuote):
        return f'BlockQuote {_block_list(block.blocks, ctx)}'
    if isinstance(block, BulletList):
        loose = any(not _item_is_compact(item) for item in block.items)
        return 'BulletList [' + ','.join(_list_item_repr(item, ctx, loose) for item in block.items) + ']'
    if isinstance(block, OrderedList):
        loose = any(not _item_is_compact(item) for item in block.items)
        return 'OrderedList (' + str(block.start) + ',' + (block.style or 'Decimal') + ',' + (block.delimiter or 'Period') + ') [' + ','.join(_list_item_repr(item, ctx, loose) for item in block.items) + ']'
    if isinstance(block, DefinitionList):
        items = []
        for term_inlines, definitions in block.items:
            defs = '[' + ','.join(_block_list(definition_blocks, ctx, plain_in_list=True) for definition_blocks in definitions) + ']'
            items.append(f'({_inline_list(term_inlines, ctx)},{defs})')
        return 'DefinitionList [' + ','.join(items) + ']'
    if isinstance(block, Div):
        return f'Div {_attr_repr(block.attr)} {_block_list(block.blocks, ctx)}'
    if isinstance(block, Figure):
        caption = f'(Caption Nothing {_plain_blocks(block.image.inlines, ctx)})'
        body = '[' + _plain_para([block.image], ctx) + ']'
        return f'Figure {_attr_repr(block.attr)} {caption} {body}'
    if isinstance(block, Table):
        return _table_repr(block, ctx)
    raise NativeWriterError(f'Unsupported block node for native writer: {type(block).__name__}')


def write_native(document: Document, *, standalone: bool = False) -> str:
    ctx = _NativeWriterContext(source_format=document.source_format)
    blocks = _block_list(document.blocks, ctx)
    if standalone or document.meta or document.source_format == 'native_pandoc':
        return f'Pandoc {_meta_repr(document.meta, ctx)} {blocks}\n'
    return blocks + '\n'
