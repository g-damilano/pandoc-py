
from __future__ import annotations

import json
from typing import Any

from pandoc_py.ast import (
    Attr,
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


class PandocJsonReaderError(ValueError):
    """Raised when a Pandoc JSON payload falls outside the current reader slice."""


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise PandocJsonReaderError(message)


def _attr_from_payload(payload: Any) -> Attr:
    _expect(isinstance(payload, list) and len(payload) == 3, 'Attr payload must be [id, classes, kvs].')
    identifier, classes, kvs = payload
    _expect(isinstance(identifier, str), 'Attr identifier must be a string.')
    _expect(isinstance(classes, list) and all(isinstance(v, str) for v in classes), 'Attr classes must be a list of strings.')
    _expect(isinstance(kvs, list), 'Attr attributes must be a list.')
    attrs: list[tuple[str, str]] = []
    for item in kvs:
        _expect(isinstance(item, list) and len(item) == 2, 'Attr key/value entries must be [key, value].')
        key, value = item
        _expect(isinstance(key, str) and isinstance(value, str), 'Attr key/value entries must contain strings.')
        attrs.append((key, value))
    return Attr(identifier=identifier, classes=list(classes), attributes=attrs)


def _citation_mode_from_payload(payload: Any) -> str:
    if isinstance(payload, dict):
        mode = payload.get('t')
    else:
        mode = payload
    _expect(mode in {'NormalCitation', 'AuthorInText', 'SuppressAuthor'}, f'Unsupported citation mode: {mode!r}')
    return str(mode)


def _inlines_from_payload(payload: Any) -> list:
    _expect(isinstance(payload, list), 'Inline list payload must be a list.')
    return [_inline_from_payload(item) for item in payload]


def _blocks_from_payload(payload: Any) -> list:
    _expect(isinstance(payload, list), 'Block list payload must be a list.')
    return [_block_from_payload(item) for item in payload]


def _inline_from_payload(payload: Any):
    _expect(isinstance(payload, dict) and 't' in payload, 'Inline payload must be an object with tag "t".')
    tag = payload['t']
    content = payload.get('c')
    if tag == 'Str':
        _expect(isinstance(content, str), 'Str payload must contain text.')
        return Str(content)
    if tag == 'Space':
        return Space()
    if tag == 'SoftBreak':
        return SoftBreak()
    if tag == 'LineBreak':
        return HardBreak()
    if tag == 'Emph':
        return Emph(_inlines_from_payload(content))
    if tag == 'Strong':
        return Strong(_inlines_from_payload(content))
    if tag == 'Strikeout':
        return Strikeout(_inlines_from_payload(content))
    if tag == 'Subscript':
        return Subscript(_inlines_from_payload(content))
    if tag == 'Superscript':
        return Superscript(_inlines_from_payload(content))
    if tag == 'Underline':
        return Underline(_inlines_from_payload(content))
    if tag == 'SmallCaps':
        return SmallCaps(_inlines_from_payload(content))
    if tag == 'Quoted':
        _expect(isinstance(content, list) and len(content) == 2, 'Quoted payload must be [quoteType, inlines].')
        quote_payload, inlines_payload = content
        quote_type = quote_payload.get('t') if isinstance(quote_payload, dict) else quote_payload
        _expect(quote_type in {'SingleQuote', 'DoubleQuote'}, f'Unsupported quote type: {quote_type!r}')
        return Quoted(inlines=_inlines_from_payload(inlines_payload), quote_type=str(quote_type))
    if tag == 'Math':
        _expect(isinstance(content, list) and len(content) == 2, 'Math payload must be [mode, text].')
        mode, text = content
        mode_tag = mode.get('t') if isinstance(mode, dict) else mode
        _expect(mode_tag in {'InlineMath', 'DisplayMath'}, f'Unsupported math mode: {mode_tag!r}')
        _expect(isinstance(text, str), 'Math text must be a string.')
        return Math(text=text, display=(mode_tag == 'DisplayMath'))
    if tag == 'Code':
        _expect(isinstance(content, list) and len(content) == 2, 'Code payload must be [attr, text].')
        _, text = content
        _expect(isinstance(text, str), 'Code text must be a string.')
        return Code(text)
    if tag == 'Span':
        _expect(isinstance(content, list) and len(content) == 2, 'Span payload must be [attr, inlines].')
        return Span(inlines=_inlines_from_payload(content[1]), attr=_attr_from_payload(content[0]))
    if tag == 'Link':
        _expect(isinstance(content, list) and len(content) == 3, 'Link payload must be [attr, inlines, target].')
        attr = _attr_from_payload(content[0])
        inlines = _inlines_from_payload(content[1])
        target_payload = content[2]
        _expect(isinstance(target_payload, list) and len(target_payload) == 2, 'Link target must be [url, title].')
        target, title = target_payload
        _expect(isinstance(target, str) and isinstance(title, str), 'Link target and title must be strings.')
        autolink = (not attr.identifier and not attr.attributes and attr.classes in (['uri'], ['email']))
        return Link(inlines=inlines, target=target, title=title, autolink=autolink, attr=attr if not autolink else Attr())
    if tag == 'Image':
        _expect(isinstance(content, list) and len(content) == 3, 'Image payload must be [attr, inlines, target].')
        attr = _attr_from_payload(content[0])
        inlines = _inlines_from_payload(content[1])
        target_payload = content[2]
        _expect(isinstance(target_payload, list) and len(target_payload) == 2, 'Image target must be [url, title].')
        target, title = target_payload
        _expect(isinstance(target, str) and isinstance(title, str), 'Image target and title must be strings.')
        return Image(inlines=inlines, target=target, title=title, attr=attr)
    if tag == 'RawInline':
        _expect(isinstance(content, list) and len(content) == 2, 'RawInline payload must be [format, text].')
        fmt, text = content
        _expect(isinstance(fmt, str) and isinstance(text, str), 'RawInline format and text must be strings.')
        return RawInline(format=fmt, text=text)
    if tag == 'Note':
        return Note(blocks=_blocks_from_payload(content))
    if tag == 'Cite':
        _expect(isinstance(content, list) and len(content) == 2, 'Cite payload must be [citations, inlines].')
        citations_payload, inlines_payload = content
        _expect(isinstance(citations_payload, list), 'Cite citations payload must be a list.')
        citations: list[Citation] = []
        for item in citations_payload:
            _expect(isinstance(item, dict), 'Citation entries must be objects.')
            citations.append(
                Citation(
                    citation_id=str(item.get('citationId', '')),
                    prefix=_inlines_from_payload(item.get('citationPrefix', [])),
                    suffix=_inlines_from_payload(item.get('citationSuffix', [])),
                    mode=_citation_mode_from_payload(item.get('citationMode')),
                    note_num=int(item.get('citationNoteNum', 0)),
                    hash=int(item.get('citationHash', 0)),
                )
            )
        return Cite(citations=citations, inlines=_inlines_from_payload(inlines_payload))
    raise PandocJsonReaderError(f'Unsupported inline tag for current reader slice: {tag}')


def _plain_or_para_inlines(block_payload: Any) -> list:
    _expect(isinstance(block_payload, dict) and block_payload.get('t') in {'Plain', 'Para'}, 'Expected Plain or Para block.')
    return _inlines_from_payload(block_payload.get('c', []))


def _caption_inlines_from_payload(payload: Any) -> list:
    _expect(isinstance(payload, list) and len(payload) == 2, 'Caption payload must be [short, blocks].')
    blocks = payload[1]
    if not blocks:
        return []
    first = blocks[0]
    return _plain_or_para_inlines(first)


def _table_cell_inlines(cell_payload: Any) -> list:
    _expect(isinstance(cell_payload, list) and len(cell_payload) == 5, 'Table cell payload must be [attr, align, rowspan, colspan, blocks].')
    _, _, rowspan, colspan, blocks = cell_payload
    _expect(int(rowspan) == 1 and int(colspan) == 1, 'Only rowspan=1 and colspan=1 are supported in current table slice.')
    if not blocks:
        return []
    return _plain_or_para_inlines(blocks[0])


def _table_aligns_from_payload(payload: Any) -> list[str]:
    _expect(isinstance(payload, list), 'Table colspec payload must be a list.')
    aligns: list[str] = []
    for item in payload:
        _expect(isinstance(item, list) and len(item) == 2, 'Colspec entries must be [align, width].')
        align_payload = item[0]
        align = align_payload.get('t') if isinstance(align_payload, dict) else align_payload
        _expect(isinstance(align, str), 'Table align tag must be a string.')
        aligns.append(align)
    return aligns


def _table_headers_from_payload(payload: Any) -> tuple[list[list], Attr]:
    _expect(isinstance(payload, list) and len(payload) == 2, 'Table head payload must be [attr, rows].')
    rows = payload[1]
    if not rows:
        return [], Attr()
    first_row = rows[0]
    _expect(isinstance(first_row, list) and len(first_row) == 2, 'Header row payload must be [attr, cells].')
    return [_table_cell_inlines(cell) for cell in first_row[1]], _attr_from_payload(first_row[0])


def _table_rows_from_payload(payload: Any) -> tuple[list[list[list]], list[Attr]]:
    _expect(isinstance(payload, list), 'Table body payload must be a list.')
    rows: list[list[list]] = []
    row_attrs: list[Attr] = []
    for body in payload:
        _expect(isinstance(body, list) and len(body) == 4, 'Table body payload must be [attr, row_head_cols, intermediate, rows].')
        body_rows = body[3]
        _expect(isinstance(body_rows, list), 'Table body rows must be a list.')
        for row in body_rows:
            _expect(isinstance(row, list) and len(row) == 2, 'Table row payload must be [attr, cells].')
            row_attrs.append(_attr_from_payload(row[0]))
            rows.append([_table_cell_inlines(cell) for cell in row[1]])
    return rows, row_attrs


def _figure_from_payload(content: Any) -> Figure:
    _expect(isinstance(content, list) and len(content) == 3, 'Figure payload must be [attr, caption, blocks].')
    attr = _attr_from_payload(content[0])
    blocks = content[2]
    _expect(isinstance(blocks, list) and len(blocks) == 1, 'Current figure reader slice expects one body block.')
    body = blocks[0]
    body_inlines = _plain_or_para_inlines(body)
    _expect(len(body_inlines) == 1 and isinstance(body_inlines[0], Image), 'Current figure reader slice expects a single Image in the body.')
    image = body_inlines[0]
    return Figure(
        image=Image(
            inlines=list(image.inlines),
            target=image.target,
            title=image.title,
            attr=image.attr,
        ),
        attr=attr,
    )


def _list_item_from_payload(payload: Any) -> list:
    _expect(isinstance(payload, list), 'List item payload must be a list.')
    blocks = []
    for item in payload:
        block = _block_from_payload(item)
        if isinstance(block, Paragraph) and item.get('t') == 'Plain':
            blocks.append(Paragraph(list(block.inlines)))
        else:
            blocks.append(block)
    return blocks


def _definition_items_from_payload(payload: Any) -> list:
    _expect(isinstance(payload, list), 'Definition list payload must be a list.')
    items = []
    for item in payload:
        _expect(isinstance(item, list) and len(item) == 2, 'Definition list items must be [term, defs].')
        term_payload, defs_payload = item
        _expect(isinstance(defs_payload, list), 'Definition list defs must be a list.')
        definitions = []
        for definition_blocks_payload in defs_payload:
            definitions.append(_blocks_from_payload(definition_blocks_payload))
        items.append((_inlines_from_payload(term_payload), definitions))
    return items


def _block_from_payload(payload: Any):
    _expect(isinstance(payload, dict) and 't' in payload, 'Block payload must be an object with tag "t".')
    tag = payload['t']
    content = payload.get('c')
    if tag in {'Para', 'Plain'}:
        return Paragraph(_inlines_from_payload(content))
    if tag == 'Null':
        return Null()
    if tag == 'Header':
        _expect(isinstance(content, list) and len(content) == 3, 'Header payload must be [level, attr, inlines].')
        level, attr_payload, inlines_payload = content
        return Heading(level=int(level), attr=_attr_from_payload(attr_payload), inlines=_inlines_from_payload(inlines_payload))
    if tag == 'HorizontalRule':
        return ThematicBreak()
    if tag == 'CodeBlock':
        _expect(isinstance(content, list) and len(content) == 2, 'CodeBlock payload must be [attr, text].')
        attr = _attr_from_payload(content[0])
        text = content[1]
        _expect(isinstance(text, str), 'CodeBlock text must be a string.')
        classes = list(attr.classes)
        info = classes[0] if classes else ''
        rest_classes = classes[1:] if classes else []
        return CodeBlock(text=text, info=info, attr=Attr(identifier=attr.identifier, classes=rest_classes, attributes=list(attr.attributes)))
    if tag == 'RawBlock':
        _expect(isinstance(content, list) and len(content) == 2, 'RawBlock payload must be [format, text].')
        fmt, text = content
        _expect(isinstance(fmt, str) and isinstance(text, str), 'RawBlock format and text must be strings.')
        return RawBlock(format=fmt, text=text)
    if tag == 'LineBlock':
        _expect(isinstance(content, list), 'LineBlock payload must be a list of inline lists.')
        return LineBlock(lines=[_inlines_from_payload(line) for line in content])
    if tag == 'BlockQuote':
        return BlockQuote(blocks=_blocks_from_payload(content))
    if tag == 'BulletList':
        return BulletList(items=[_list_item_from_payload(item) for item in content])
    if tag == 'OrderedList':
        _expect(isinstance(content, list) and len(content) == 2, 'OrderedList payload must be [attrs, items].')
        attrs_payload, items_payload = content
        _expect(isinstance(attrs_payload, list) and len(attrs_payload) == 3, 'OrderedList attrs must be [start, style, delim].')
        start = int(attrs_payload[0])
        style = attrs_payload[1].get('t') if isinstance(attrs_payload[1], dict) else 'Decimal'
        delim = attrs_payload[2].get('t') if isinstance(attrs_payload[2], dict) else 'Period'
        return OrderedList(start=start, style=style, delimiter=delim, items=[_list_item_from_payload(item) for item in items_payload])
    if tag == 'DefinitionList':
        return DefinitionList(items=_definition_items_from_payload(content))
    if tag == 'Div':
        _expect(isinstance(content, list) and len(content) == 2, 'Div payload must be [attr, blocks].')
        return Div(attr=_attr_from_payload(content[0]), blocks=_blocks_from_payload(content[1]))
    if tag == 'Figure':
        return _figure_from_payload(content)
    if tag == 'Table':
        _expect(isinstance(content, list) and len(content) == 6, 'Table payload must have 6 fields in current API slice.')
        _, caption_payload, colspecs_payload, head_payload, bodies_payload, _ = content
        headers, header_row_attr = _table_headers_from_payload(head_payload)
        rows, row_attrs = _table_rows_from_payload(bodies_payload)
        return Table(
            caption=_caption_inlines_from_payload(caption_payload),
            aligns=_table_aligns_from_payload(colspecs_payload),
            headers=headers,
            rows=rows,
            header_row_attr=header_row_attr,
            row_attrs=row_attrs,
        )
    raise PandocJsonReaderError(f'Unsupported block tag for current reader slice: {tag}')



def _meta_from_payload(payload: Any):
    _expect(isinstance(payload, dict) and 't' in payload, 'Meta payload must be an object with tag "t".')
    tag = payload['t']
    content = payload.get('c')
    if tag == 'MetaBool':
        _expect(isinstance(content, bool), 'MetaBool payload must be a bool.')
        return MetaBool(content)
    if tag == 'MetaString':
        _expect(isinstance(content, str), 'MetaString payload must be a string.')
        return MetaString(content)
    if tag == 'MetaInlines':
        return MetaInlines(_inlines_from_payload(content))
    if tag == 'MetaBlocks':
        return MetaBlocks(_blocks_from_payload(content))
    if tag == 'MetaList':
        _expect(isinstance(content, list), 'MetaList payload must be a list.')
        return MetaList([_meta_from_payload(item) for item in content])
    if tag == 'MetaMap':
        _expect(isinstance(content, dict), 'MetaMap payload must be an object.')
        return MetaMap({str(key): _meta_from_payload(value) for key, value in content.items()})
    raise PandocJsonReaderError(f'Unsupported meta tag for current reader slice: {tag}')


def _meta_map_from_payload(payload: Any) -> dict[str, MetaValue]:
    _expect(isinstance(payload, dict), 'Pandoc JSON meta payload must be an object.')
    return {str(key): _meta_from_payload(value) for key, value in payload.items()}

def document_from_pandoc_json_payload(payload: Any) -> Document:
    _expect(isinstance(payload, dict), 'Pandoc JSON payload must be an object.')
    _expect(isinstance(payload.get('blocks'), list), 'Pandoc JSON payload must contain a blocks list.')
    meta_payload = payload.get('meta', {})
    return Document(blocks=_blocks_from_payload(payload['blocks']), meta=_meta_map_from_payload(meta_payload))


def read_pandoc_json(source: str) -> Document:
    try:
        payload = json.loads(source)
    except json.JSONDecodeError as exc:
        raise PandocJsonReaderError(f'Invalid JSON input: {exc.msg}') from exc
    return document_from_pandoc_json_payload(payload)
