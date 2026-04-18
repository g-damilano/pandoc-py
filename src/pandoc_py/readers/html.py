from __future__ import annotations

import re
from typing import Iterable

from lxml import etree, html

from pandoc_py.ast import (
    Attr,
    BlockQuote,
    BulletList,
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
    OrderedList,
    Paragraph,
    Space,
    Span,
    Str,
    SoftBreak,
    Strikeout,
    Strong,
    Subscript,
    Superscript,
    Table,
    ThematicBreak,
)


class HtmlReaderError(ValueError):
    """Raised when HTML input falls outside the current reader slice."""


_WHITESPACE_RE = re.compile(r'\s+')
_INLINE_BLOCK_TAGS = {'p', 'div', 'blockquote', 'ul', 'ol', 'dl', 'table', 'figure', 'pre', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr'}
_INLINE_TAGS = {'em', 'i', 'strong', 'b', 'del', 's', 'strike', 'sub', 'sup', 'code', 'a', 'img', 'span', 'br'}


def _normalize_attr_name(name: str) -> str:
    name = name.lower()
    return name[5:] if name.startswith('data-') else name


def _attr_from_element(element: etree._Element, *, skip: set[str] | None = None) -> Attr:
    skip = skip or set()
    identifier = ''
    classes: list[str] = []
    attrs: list[tuple[str, str]] = []
    for key, value in element.attrib.items():
        key = str(key)
        value = str(value)
        if key in skip:
            continue
        if key == 'id':
            identifier = value
            continue
        if key == 'class':
            classes = [part for part in value.split() if part]
            continue
        attrs.append((_normalize_attr_name(key), value))
    return Attr(identifier=identifier, classes=classes, attributes=attrs)


def _append_text_inlines(target: list, text: str | None, *, preserve_newlines: bool = False) -> None:
    if not text:
        return
    normalized = text.replace('\r\n', '\n').replace('\r', '\n').replace('\xa0', ' ')
    if preserve_newlines:
        for segment in re.split(r'(\n+)', normalized):
            if not segment:
                continue
            if segment.startswith('\n'):
                if target and not isinstance(target[-1], (SoftBreak, HardBreak)):
                    target.append(SoftBreak())
                continue
            for part in re.split(r'([ \t\f\v]+)', segment):
                if not part:
                    continue
                if part.isspace():
                    if target and not isinstance(target[-1], (Space, HardBreak, SoftBreak)):
                        target.append(Space())
                else:
                    target.append(Str(part))
        return
    for part in re.split(r'(\s+)', normalized):
        if not part:
            continue
        if part.isspace():
            if target and not isinstance(target[-1], (Space, HardBreak)):
                target.append(Space())
        else:
            target.append(Str(part))


def _cleanup_inlines(inlines: Iterable) -> list:
    cleaned: list = []
    for inline in inlines:
        if isinstance(inline, Space):
            if not cleaned or isinstance(cleaned[-1], (Space, HardBreak)):
                continue
            cleaned.append(inline)
            continue
        if isinstance(inline, HardBreak):
            if cleaned and isinstance(cleaned[-1], Space):
                cleaned.pop()
            cleaned.append(inline)
            continue
        cleaned.append(inline)
    while cleaned and isinstance(cleaned[0], Space):
        cleaned.pop(0)
    while cleaned and isinstance(cleaned[-1], Space):
        cleaned.pop()
    normalized: list = []
    for inline in cleaned:
        if normalized and isinstance(normalized[-1], HardBreak) and isinstance(inline, Space):
            continue
        normalized.append(inline)
    return normalized


def _element_text(element: etree._Element) -> str:
    return ''.join(element.itertext())


def _parse_inline_children(element: etree._Element, *, preserve_newlines: bool = False) -> list:
    inlines: list = []
    _append_text_inlines(inlines, element.text, preserve_newlines=preserve_newlines)
    for child in element:
        inlines.extend(_inline_from_node(child))
        _append_text_inlines(inlines, child.tail, preserve_newlines=preserve_newlines)
    return _cleanup_inlines(inlines)


def _text_as_inlines(text: str) -> list:
    inlines: list = []
    _append_text_inlines(inlines, text)
    return _cleanup_inlines(inlines)


def _is_inline_element(node: etree._Element) -> bool:
    return isinstance(node.tag, str) and node.tag.lower() in _INLINE_TAGS


def _is_block_element(node: etree._Element) -> bool:
    return isinstance(node.tag, str) and node.tag.lower() in _INLINE_BLOCK_TAGS


def _inline_from_node(node: object) -> list:
    if isinstance(node, etree._Comment):
        return []
    if not isinstance(node, etree._Element) or not isinstance(node.tag, str):
        raise HtmlReaderError(f'Unsupported inline node: {node!r}')
    tag = node.tag.lower()
    if tag in {'em', 'i'}:
        return [Emph(_parse_inline_children(node))]
    if tag in {'strong', 'b'}:
        return [Strong(_parse_inline_children(node))]
    if tag in {'del', 's', 'strike'}:
        return [Strikeout(_parse_inline_children(node))]
    if tag == 'sub':
        return [Subscript(_parse_inline_children(node))]
    if tag == 'sup':
        return [Superscript(_parse_inline_children(node))]
    if tag == 'code':
        return [Code(_element_text(node))]
    if tag == 'a':
        attr = _attr_from_element(node, skip={'href', 'title'})
        return [Link(inlines=_parse_inline_children(node), target=node.attrib.get('href', ''), title=node.attrib.get('title', ''), autolink=False, attr=attr)]
    if tag == 'img':
        attr = _attr_from_element(node, skip={'src', 'title', 'alt'})
        return [Image(inlines=_text_as_inlines(node.attrib.get('alt', '')), target=node.attrib.get('src', ''), title=node.attrib.get('title', ''), attr=attr)]
    if tag == 'span':
        classes = set((node.attrib.get('class') or '').split())
        preserve_newlines = {'math', 'display'}.issubset(classes)
        return [Span(inlines=_parse_inline_children(node, preserve_newlines=preserve_newlines), attr=_attr_from_element(node))]
    if tag == 'br':
        return [HardBreak()]
    raise HtmlReaderError(f'Unsupported inline tag for current HTML reader slice: {tag}')


def _maybe_task_item(node: etree._Element):
    children = [child for child in node if isinstance(child.tag, str)]
    if len(children) != 1 or children[0].tag.lower() != 'label':
        return None
    label = children[0]
    label_children = [child for child in label if isinstance(child.tag, str)]
    if len(label_children) != 1 or label_children[0].tag.lower() != 'input':
        return None
    checkbox = label_children[0]
    if checkbox.attrib.get('type', '').lower() != 'checkbox':
        return None
    mark = '☒' if 'checked' in checkbox.attrib else '☐'
    text = ''.join(label.itertext())
    text = text.replace('\xa0', ' ').strip()
    inlines = [Str(mark)]
    suffix = _text_as_inlines(text)
    if suffix:
        inlines.append(Space())
        inlines.extend(suffix)
    return [Paragraph(inlines=_cleanup_inlines(inlines))]


def _inline_blocks_from_mixed_content(element: etree._Element) -> list:
    inlines = _parse_inline_children(element)
    return [Paragraph(inlines=inlines)] if inlines else []


def _blocks_from_children(element: etree._Element) -> list:
    blocks: list = []
    leading = _text_as_inlines(element.text or '')
    if leading:
        blocks.append(Paragraph(inlines=leading))
    for child in element:
        if isinstance(child, etree._Comment):
            if child.tail and child.tail.strip():
                blocks.append(Paragraph(inlines=_text_as_inlines(child.tail)))
            continue
        if not isinstance(child, etree._Element) or not isinstance(child.tag, str):
            continue
        if _is_block_element(child):
            blocks.extend(_block_from_node(child))
        elif _is_inline_element(child):
            blocks.extend(_inline_blocks_from_mixed_content(element))
            return blocks
        else:
            raise HtmlReaderError(f'Unsupported block child tag for current HTML reader slice: {child.tag.lower()}')
        tail = _text_as_inlines(child.tail or '')
        if tail:
            blocks.append(Paragraph(inlines=tail))
    return blocks


def _list_item_blocks(node: etree._Element) -> list:
    task = _maybe_task_item(node)
    if task is not None:
        return task
    blocks = _blocks_from_children(node)
    return blocks or [Paragraph(inlines=[])]


def _parse_list(node: etree._Element):
    items = [_list_item_blocks(child) for child in node if isinstance(child.tag, str) and child.tag.lower() == 'li']
    if node.tag.lower() == 'ul':
        return BulletList(items=items)
    start = int(node.attrib.get('start', '1')) if node.attrib.get('start', '1').isdigit() else 1
    style_map = {'1': 'Decimal', 'A': 'UpperAlpha', 'a': 'LowerAlpha', 'I': 'UpperRoman', 'i': 'LowerRoman'}
    style = style_map.get(node.attrib.get('type', '1'), 'Decimal')
    return OrderedList(start=start, style=style, delimiter='DefaultDelim', items=items)


def _parse_definition_list(node: etree._Element) -> DefinitionList:
    items: list[tuple[list, list[list]]] = []
    pending_term: list | None = None
    pending_defs: list[list] = []
    for child in node:
        if not isinstance(child.tag, str):
            continue
        tag = child.tag.lower()
        if tag == 'dt':
            if pending_term is not None:
                items.append((pending_term, pending_defs or [[Paragraph(inlines=[])] ]))
            pending_term = _parse_inline_children(child)
            pending_defs = []
        elif tag == 'dd':
            pending_defs.append(_blocks_from_children(child) or [Paragraph(inlines=_parse_inline_children(child))])
        else:
            raise HtmlReaderError(f'Unsupported definition list child tag: {tag}')
    if pending_term is not None:
        items.append((pending_term, pending_defs or [[Paragraph(inlines=[])] ]))
    return DefinitionList(items=items)


def _parse_alignment(style: str | None) -> str:
    if not style:
        return 'AlignDefault'
    style = style.lower()
    if 'text-align:' not in style:
        return 'AlignDefault'
    value = style.split('text-align:', 1)[1].split(';', 1)[0].strip()
    return {
        'left': 'AlignLeft',
        'center': 'AlignCenter',
        'right': 'AlignRight',
    }.get(value, 'AlignDefault')


def _cell_inlines(node: etree._Element) -> list:
    if any(_is_block_element(child) for child in node if isinstance(child.tag, str)):
        blocks = _blocks_from_children(node)
        if len(blocks) == 1 and isinstance(blocks[0], Paragraph):
            return blocks[0].inlines
        raise HtmlReaderError('Only single-paragraph table cells are inside the current HTML reader slice.')
    return _parse_inline_children(node)


def _parse_table(node: etree._Element) -> Table:
    caption: list = []
    aligns: list[str] = []
    headers: list[list] = []
    rows: list[list[list]] = []
    header_row_attr = Attr()
    row_attrs: list[Attr] = []
    for child in node:
        if not isinstance(child.tag, str):
            continue
        tag = child.tag.lower()
        if tag == 'caption':
            caption = _parse_inline_children(child)
        elif tag == 'thead':
            row_nodes = [r for r in child if isinstance(r.tag, str) and r.tag.lower() == 'tr']
            if row_nodes:
                header_cells = [c for c in row_nodes[0] if isinstance(c.tag, str) and c.tag.lower() in {'th', 'td'}]
                headers = [_cell_inlines(c) for c in header_cells]
                aligns = [_parse_alignment(c.attrib.get('style')) for c in header_cells]
                header_row_attr = _attr_from_element(row_nodes[0])
        elif tag == 'tbody':
            for row in child:
                if not isinstance(row.tag, str) or row.tag.lower() != 'tr':
                    continue
                cells = [c for c in row if isinstance(c.tag, str) and c.tag.lower() in {'th', 'td'}]
                rows.append([_cell_inlines(c) for c in cells])
                row_attrs.append(_attr_from_element(row))
        elif tag == 'tr':
            cells = [c for c in child if isinstance(c.tag, str) and c.tag.lower() in {'th', 'td'}]
            if not headers:
                headers = [_cell_inlines(c) for c in cells]
                aligns = [_parse_alignment(c.attrib.get('style')) for c in cells]
            else:
                rows.append([_cell_inlines(c) for c in cells])
        else:
            raise HtmlReaderError(f'Unsupported table child tag for current HTML reader slice: {tag}')
    return Table(caption=caption, aligns=aligns or ['AlignDefault'] * len(headers), headers=headers, rows=rows, header_row_attr=header_row_attr, row_attrs=row_attrs)


def _parse_figure(node: etree._Element) -> Figure:
    img_node = None
    caption: list = []
    for child in node:
        if not isinstance(child.tag, str):
            continue
        tag = child.tag.lower()
        if tag == 'img':
            img_node = child
        elif tag == 'figcaption':
            caption = _parse_inline_children(child)
    if img_node is None:
        raise HtmlReaderError('Figure without img is outside the current HTML reader slice.')
    image = _inline_from_node(img_node)[0]
    if not isinstance(image, Image):
        raise HtmlReaderError('Figure body did not parse to Image.')
    image = Image(inlines=caption or image.inlines, target=image.target, title=image.title, attr=image.attr)
    return Figure(image=image, attr=_attr_from_element(node, skip={'class'}))


def _block_from_node(node: object) -> list:
    if isinstance(node, etree._Comment):
        return []
    if not isinstance(node, etree._Element) or not isinstance(node.tag, str):
        raise HtmlReaderError(f'Unsupported block node: {node!r}')
    tag = node.tag.lower()
    if tag == 'p':
        return [Paragraph(inlines=_parse_inline_children(node))]
    if tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
        return [Heading(level=int(tag[1]), inlines=_parse_inline_children(node), attr=_attr_from_element(node))]
    if tag == 'blockquote':
        return [BlockQuote(blocks=_blocks_from_children(node))]
    if tag in {'ul', 'ol'}:
        return [_parse_list(node)]
    if tag == 'hr':
        return [ThematicBreak()]
    if tag == 'pre':
        children = [child for child in node if isinstance(child.tag, str)]
        if len(children) == 1 and children[0].tag.lower() == 'code':
            return [CodeBlock(text=_element_text(children[0]), attr=_attr_from_element(node), info='')]
        return [CodeBlock(text=_element_text(node), attr=_attr_from_element(node), info='')]
    if tag == 'div':
        return [Div(blocks=_blocks_from_children(node), attr=_attr_from_element(node))]
    if tag == 'dl':
        return [_parse_definition_list(node)]
    if tag == 'figure':
        return [_parse_figure(node)]
    if tag == 'table':
        return [_parse_table(node)]
    if tag in _INLINE_TAGS:
        return [Paragraph(inlines=_inline_from_node(node))]
    if tag in {'script', 'style'}:
        return []
    raise HtmlReaderError(f'Unsupported block tag for current HTML reader slice: {tag}')


def read_html(source: str) -> Document:
    try:
        fragments = html.fragments_fromstring(source)
    except etree.ParserError as exc:
        raise HtmlReaderError(str(exc)) from exc
    blocks: list = []
    for fragment in fragments:
        if isinstance(fragment, str):
            inlines = _text_as_inlines(fragment)
            if inlines:
                blocks.append(Paragraph(inlines=inlines))
            continue
        blocks.extend(_block_from_node(fragment))
    return Document(blocks=blocks, source_format='html')
