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
    LineBlock,
    Math,
    MetaBlocks,
    MetaBool,
    MetaInlines,
    MetaList,
    MetaMap,
    MetaString,
    MetaValue,
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

PANDOC_API_VERSION = (1, 23, 1)
DEFAULT_ORDERED_LIST_STYLE = 'Decimal'
DEFAULT_ORDERED_LIST_DELIM = 'Period'
URI_AUTOLINK_ATTR = ['', ['uri'], []]
EMAIL_AUTOLINK_ATTR = ['', ['email'], []]


class PandocJsonWriterError(TypeError):
    """Raised when the writer receives a node outside the supported AST slice."""


@dataclass
class _JsonWriterContext:
    slug_counts: Counter[str] = field(default_factory=Counter)
    citation_note_num: int = 1
    source_format: str = ''


InlineNode = Str | Space | SoftBreak | HardBreak | Emph | Strong | Strikeout | Subscript | Superscript | Underline | SmallCaps | Quoted | Math | Code | Span | Link | Image | RawInline | Note | Cite
BlockNode = Paragraph | LineBlock | Null | Heading | ThematicBreak | CodeBlock | RawBlock | BlockQuote | BulletList | OrderedList | DefinitionList | Div | Figure | Table


def _attr_payload(attr: Attr) -> list[object]:
    return [attr.identifier, list(attr.classes), [[k, v] for k, v in attr.attributes]]


def _link_attr(inline: Link, ctx: _JsonWriterContext) -> list[object]:
    if inline.autolink and not inline.attr.identifier and not inline.attr.classes and not inline.attr.attributes:
        if ctx.source_format in {'commonmark', 'commonmark_x'}:
            return _attr_payload(Attr())
        if inline.target.startswith('mailto:'):
            return list(EMAIL_AUTOLINK_ATTR)
        return list(URI_AUTOLINK_ATTR)
    return _attr_payload(inline.attr)


def _citation_mode_payload(mode: str) -> dict[str, str]:
    allowed = {'NormalCitation', 'AuthorInText', 'SuppressAuthor'}
    if mode not in allowed:
        raise PandocJsonWriterError(f'Unsupported citation mode in current writer slice: {mode}')
    return {'t': mode}


def _citation_payload(citation: Citation, ctx: _JsonWriterContext, note_num: int) -> dict[str, object]:
    return {
        'citationId': citation.citation_id,
        'citationPrefix': [_inline_to_payload(i, ctx) for i in citation.prefix],
        'citationSuffix': [_inline_to_payload(i, ctx) for i in citation.suffix],
        'citationMode': _citation_mode_payload(citation.mode),
        'citationNoteNum': note_num,
        'citationHash': citation.hash,
    }


def _inline_to_payload(inline: InlineNode, ctx: _JsonWriterContext) -> dict[str, object]:
    if isinstance(inline, Str):
        return {'t': 'Str', 'c': inline.text}
    if isinstance(inline, Space):
        return {'t': 'Space'}
    if isinstance(inline, SoftBreak):
        return {'t': 'SoftBreak'}
    if isinstance(inline, HardBreak):
        return {'t': 'LineBreak'}
    if isinstance(inline, Emph):
        return {'t': 'Emph', 'c': [_inline_to_payload(i, ctx) for i in inline.inlines]}
    if isinstance(inline, Strong):
        return {'t': 'Strong', 'c': [_inline_to_payload(i, ctx) for i in inline.inlines]}
    if isinstance(inline, Strikeout):
        return {'t': 'Strikeout', 'c': [_inline_to_payload(i, ctx) for i in inline.inlines]}
    if isinstance(inline, Subscript):
        return {'t': 'Subscript', 'c': [_inline_to_payload(i, ctx) for i in inline.inlines]}
    if isinstance(inline, Superscript):
        return {'t': 'Superscript', 'c': [_inline_to_payload(i, ctx) for i in inline.inlines]}
    if isinstance(inline, Underline):
        return {'t': 'Underline', 'c': [_inline_to_payload(i, ctx) for i in inline.inlines]}
    if isinstance(inline, SmallCaps):
        return {'t': 'SmallCaps', 'c': [_inline_to_payload(i, ctx) for i in inline.inlines]}
    if isinstance(inline, Quoted):
        if inline.quote_type not in {'SingleQuote', 'DoubleQuote'}:
            raise PandocJsonWriterError(f'Unsupported quote type in current pandoc JSON writer slice: {inline.quote_type}')
        return {'t': 'Quoted', 'c': [{'t': inline.quote_type}, [_inline_to_payload(i, ctx) for i in inline.inlines]]}
    if isinstance(inline, Math):
        return {'t': 'Math', 'c': [{'t': 'DisplayMath' if inline.display else 'InlineMath'}, inline.text]}
    if isinstance(inline, Code):
        return {'t': 'Code', 'c': [_attr_payload(Attr()), inline.text]}
    if isinstance(inline, Span):
        return {'t': 'Span', 'c': [_attr_payload(inline.attr), [_inline_to_payload(i, ctx) for i in inline.inlines]]}
    if isinstance(inline, Link):
        return {
            't': 'Link',
            'c': [
                _link_attr(inline, ctx),
                [_inline_to_payload(i, ctx) for i in inline.inlines],
                [inline.target, inline.title],
            ],
        }
    if isinstance(inline, Image):
        return {
            't': 'Image',
            'c': [
                _attr_payload(inline.attr),
                [_inline_to_payload(i, ctx) for i in inline.inlines],
                [inline.target, inline.title],
            ],
        }
    if isinstance(inline, RawInline):
        return {'t': 'RawInline', 'c': [inline.format, inline.text]}
    if isinstance(inline, Cite):
        note_num = ctx.citation_note_num
        ctx.citation_note_num += 1
        return {
            't': 'Cite',
            'c': [
                [_citation_payload(citation, ctx, note_num) for citation in inline.citations],
                [_inline_to_payload(i, ctx) for i in inline.inlines],
            ],
        }
    if isinstance(inline, Note):
        return {'t': 'Note', 'c': [_block_to_payload(block, ctx) for block in inline.blocks]}
    raise PandocJsonWriterError(f'Unsupported inline node for pandoc JSON writer: {type(inline).__name__}')


def _flatten_inline_text(inlines: list[InlineNode]) -> str:
    parts: list[str] = []
    for inline in inlines:
        if isinstance(inline, Str):
            parts.append(inline.text)
            continue
        if isinstance(inline, (Space, SoftBreak, HardBreak)):
            parts.append(' ')
            continue
        if isinstance(inline, (Emph, Strong, Strikeout, Subscript, Superscript, Underline, SmallCaps, Quoted, Span, Link, Image, Cite)):
            parts.append(_flatten_inline_text(inline.inlines))
            continue
        if isinstance(inline, (Code, Math)):
            parts.append(inline.text)
            continue
        if isinstance(inline, RawInline):
            continue
        if isinstance(inline, Note):
            continue
        raise PandocJsonWriterError(f'Unsupported inline node for heading identifier generation: {type(inline).__name__}')
    return ''.join(parts)


def _slugify_heading_text(text: str) -> str:
    normalized = unicodedata.normalize('NFKD', text)
    ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
    lowered = ascii_text.lower()
    slug = re.sub(r'[^a-z0-9.]+', '-', lowered).strip('-')
    if '://' in lowered:
        slug = slug.replace('-', '')
    return slug or 'section'


def _build_heading_identifier(block: Heading, ctx: _JsonWriterContext) -> str:
    if block.attr.identifier:
        return block.attr.identifier
    base = _slugify_heading_text(_flatten_inline_text(block.inlines))
    seen = ctx.slug_counts[base]
    ctx.slug_counts[base] += 1
    return base if seen == 0 else f'{base}-{seen + 1}'


def _heading_attr_payload(block: Heading, ctx: _JsonWriterContext) -> list[object]:
    if ctx.source_format == 'commonmark' and not block.attr.identifier and not block.attr.classes and not block.attr.attributes:
        return _attr_payload(Attr())
    identifier = _build_heading_identifier(block, ctx)
    return [identifier, list(block.attr.classes), [[k, v] for k, v in block.attr.attributes]]


def _paragraph_image_to_figure(block: Paragraph, source_format: str = '') -> Figure | None:
    if source_format in {'commonmark', 'commonmark_x'}:
        return None
    if len(block.inlines) != 1 or not isinstance(block.inlines[0], Image):
        return None
    image = block.inlines[0]
    figure_attr = Attr(identifier=image.attr.identifier)
    image_attr = Attr(classes=list(image.attr.classes), attributes=list(image.attr.attributes))
    return Figure(
        image=Image(inlines=image.inlines, target=image.target, title=image.title, attr=image_attr),
        attr=figure_attr,
    )


def _paragraph_like_payload(block: Paragraph, ctx: _JsonWriterContext, plain: bool) -> dict[str, object]:
    tag = 'Plain' if plain else 'Para'
    return {'t': tag, 'c': [_inline_to_payload(i, ctx) for i in block.inlines]}


def _code_block_payload(block: CodeBlock) -> dict[str, object]:
    classes = list(block.attr.classes)
    if block.info and block.info not in classes:
        classes.insert(0, block.info)
    attr = Attr(identifier=block.attr.identifier, classes=classes, attributes=list(block.attr.attributes))
    return {'t': 'CodeBlock', 'c': [_attr_payload(attr), block.text]}


def _figure_payload(block: Figure, ctx: _JsonWriterContext) -> dict[str, object]:
    figure_attr = _attr_payload(block.attr)
    caption_plain = {'t': 'Plain', 'c': [_inline_to_payload(i, ctx) for i in block.image.inlines]}
    image_payload = {
        't': 'Image',
        'c': [
            _attr_payload(block.image.attr),
            [_inline_to_payload(i, ctx) for i in block.image.inlines],
            [block.image.target, block.image.title],
        ],
    }
    return {
        't': 'Figure',
        'c': [
            figure_attr,
            [None, [caption_plain]],
            [{'t': 'Plain', 'c': [image_payload]}],
        ],
    }


def _plain_blocks_from_inlines(inlines: list[InlineNode], ctx: _JsonWriterContext) -> list[dict[str, object]]:
    return [{'t': 'Plain', 'c': [_inline_to_payload(i, ctx) for i in inlines]}]


def _table_cell_payload(inlines: list[InlineNode], align: str, ctx: _JsonWriterContext) -> list[object]:
    return [_attr_payload(Attr()), {'t': align}, 1, 1, _plain_blocks_from_inlines(inlines, ctx)]


def _table_payload(block: Table, ctx: _JsonWriterContext) -> dict[str, object]:
    colspecs = [[{'t': align}, {'t': 'ColWidthDefault'}] for align in block.aligns]
    head_row = [_table_cell_payload(cell, 'AlignDefault', ctx) for cell in block.headers]
    body_rows = [[_attr_payload(block.row_attrs[idx] if idx < len(block.row_attrs) else Attr()), [_table_cell_payload(cell, 'AlignDefault', ctx) for cell in row]] for idx, row in enumerate(block.rows)]
    caption_blocks = [] if not block.caption else _plain_blocks_from_inlines(block.caption, ctx)
    return {
        't': 'Table',
        'c': [
            _attr_payload(Attr()),
            [None, caption_blocks],
            colspecs,
            [_attr_payload(Attr()), [[_attr_payload(block.header_row_attr), head_row]]],
            [[_attr_payload(Attr()), 0, [], body_rows]],
            [_attr_payload(Attr()), []],
        ],
    }


def _item_is_compact(item: list[BlockNode | Block]) -> bool:
    return bool(item) and isinstance(item[0], Paragraph) and all(not isinstance(inline, (SoftBreak, HardBreak, Note)) for inline in item[0].inlines) and all(isinstance(block, (BulletList, OrderedList)) for block in item[1:])


def _list_item_payload(item: list[BlockNode | Block], ctx: _JsonWriterContext, loose: bool) -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = []
    first_plain = (not loose) and _item_is_compact(item)
    for idx, subblock in enumerate(item):
        payloads.append(_block_to_payload(subblock, ctx, plain_in_list=(idx == 0 and first_plain)))
    return payloads


def _definition_list_payload(block: DefinitionList, ctx: _JsonWriterContext) -> dict[str, object]:
    items_payload: list[list[object]] = []
    for term_inlines, definitions in block.items:
        defs_payload: list[list[dict[str, object]]] = []
        for definition_blocks in definitions:
            defs_payload.append([_block_to_payload(subblock, ctx, plain_in_list=True) for subblock in definition_blocks])
        items_payload.append([[_inline_to_payload(i, ctx) for i in term_inlines], defs_payload])
    return {'t': 'DefinitionList', 'c': items_payload}


def _block_to_payload(block: BlockNode | Block, ctx: _JsonWriterContext, plain_in_list: bool = False) -> dict[str, object]:
    if isinstance(block, Paragraph):
        figure = None if plain_in_list else _paragraph_image_to_figure(block, ctx.source_format)
        if figure is not None:
            return _figure_payload(figure, ctx)
        return _paragraph_like_payload(block, ctx, plain_in_list)
    if isinstance(block, Null):
        return {'t': 'Null'}
    if isinstance(block, LineBlock):
        return {'t': 'LineBlock', 'c': [[_inline_to_payload(i, ctx) for i in line] for line in block.lines]}
    if isinstance(block, Heading):
        return {
            't': 'Header',
            'c': [block.level, _heading_attr_payload(block, ctx), [_inline_to_payload(i, ctx) for i in block.inlines]],
        }
    if isinstance(block, ThematicBreak):
        return {'t': 'HorizontalRule'}
    if isinstance(block, CodeBlock):
        return _code_block_payload(block)
    if isinstance(block, RawBlock):
        return {'t': 'RawBlock', 'c': [block.format, block.text]}
    if isinstance(block, BlockQuote):
        return {'t': 'BlockQuote', 'c': [_block_to_payload(subblock, ctx) for subblock in block.blocks]}
    if isinstance(block, BulletList):
        items_payload: list[list[dict[str, object]]] = []
        loose = any(not _item_is_compact(item) for item in block.items)
        for item in block.items:
            items_payload.append(_list_item_payload(item, ctx, loose))
        return {'t': 'BulletList', 'c': items_payload}
    if isinstance(block, OrderedList):
        items_payload: list[list[dict[str, object]]] = []
        loose = any(not _item_is_compact(item) for item in block.items)
        for item in block.items:
            items_payload.append(_list_item_payload(item, ctx, loose))
        return {'t': 'OrderedList', 'c': [[block.start, {'t': block.style or DEFAULT_ORDERED_LIST_STYLE}, {'t': block.delimiter or DEFAULT_ORDERED_LIST_DELIM}], items_payload]}
    if isinstance(block, DefinitionList):
        return _definition_list_payload(block, ctx)
    if isinstance(block, Div):
        return {'t': 'Div', 'c': [_attr_payload(block.attr), [_block_to_payload(subblock, ctx) for subblock in block.blocks]]}
    if isinstance(block, Figure):
        return _figure_payload(block, ctx)
    if isinstance(block, Table):
        return _table_payload(block, ctx)
    raise PandocJsonWriterError(f'Unsupported block node for pandoc JSON writer: {type(block).__name__}')



def _meta_to_payload(meta: MetaValue, ctx: _JsonWriterContext) -> dict[str, object]:
    if isinstance(meta, MetaBool):
        return {'t': 'MetaBool', 'c': meta.value}
    if isinstance(meta, MetaString):
        return {'t': 'MetaString', 'c': meta.text}
    if isinstance(meta, MetaInlines):
        return {'t': 'MetaInlines', 'c': [_inline_to_payload(i, ctx) for i in meta.inlines]}
    if isinstance(meta, MetaBlocks):
        return {'t': 'MetaBlocks', 'c': [_block_to_payload(block, ctx) for block in meta.blocks]}
    if isinstance(meta, MetaList):
        return {'t': 'MetaList', 'c': [_meta_to_payload(item, ctx) for item in meta.items]}
    if isinstance(meta, MetaMap):
        return {'t': 'MetaMap', 'c': {key: _meta_to_payload(value, ctx) for key, value in meta.mapping.items()}}
    raise PandocJsonWriterError(f'Unsupported metadata value for pandoc JSON writer: {type(meta).__name__}')


def _meta_payload(document: Document, ctx: _JsonWriterContext) -> dict[str, object]:
    return {key: _meta_to_payload(value, ctx) for key, value in document.meta.items()}

def document_to_pandoc_json_payload(document: Document) -> dict[str, object]:
    ctx = _JsonWriterContext(source_format=document.source_format)
    return {
        'pandoc-api-version': list(PANDOC_API_VERSION),
        'meta': _meta_payload(document, ctx),
        'blocks': [_block_to_payload(block, ctx) for block in document.blocks],
    }


def write_pandoc_json(document: Document) -> str:
    return json.dumps(document_to_pandoc_json_payload(document), ensure_ascii=False) + '\n'
