from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
import re
import unicodedata

from pandoc_py.ast import (
    Attr,
    Block,
    BlockQuote,
    BulletList,
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
    Note,
    OrderedList,
    Paragraph,
    RawBlock,
    RawInline,
    SoftBreak,
    Space,
    Span,
    Str,
    Strikeout,
    Strong,
    Subscript,
    Superscript,
    Table,
    ThematicBreak,
)


class HtmlWriterError(TypeError):
    """Raised when the writer receives a node outside the supported HTML slice."""


TASK_BOX_UNCHECKED = '☐'
TASK_BOX_CHECKED = '☒'
InlineNode = Str | Space | SoftBreak | HardBreak | Emph | Strong | Strikeout | Subscript | Superscript | Math | Code | Span | Link | Image | RawInline | Note | Cite


@dataclass
class _HtmlWriterContext:
    footnotes: list[list[Block]] = field(default_factory=list)
    source_format: str = ''


def _escape_text(text: str) -> str:
    return escape(text, quote=False)


def _escape_attr(text: str) -> str:
    return escape(text, quote=True)


def _slugify_heading_text(text: str) -> str:
    normalized = unicodedata.normalize('NFKD', text)
    ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
    lowered = ascii_text.lower()
    slug = re.sub(r'[^a-z0-9.]+', '-', lowered).strip('-')
    if '://' in lowered:
        slug = slug.replace('-', '')
    return slug or 'section'


def _attr_items(attr: Attr, *, include_id: bool = True, include_class: bool = True) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    if include_id and attr.identifier:
        items.append(('id', attr.identifier))
    if include_class and attr.classes:
        items.append(('class', ' '.join(attr.classes)))
    for key, value in attr.attributes:
        html_key = key if key.startswith('data-') else f'data-{key}'
        items.append((html_key, value))
    return items


def _attrs_to_html(items: list[tuple[str, str]]) -> str:
    if not items:
        return ''
    return ''.join(f' {key}="{_escape_attr(value)}"' for key, value in items)


def _is_simple_paragraph(paragraph: Paragraph) -> bool:
    return all(not isinstance(i, (SoftBreak, HardBreak, Note)) for i in paragraph.inlines)


def _task_state(paragraph: Paragraph) -> tuple[bool, bool, list[InlineNode]]:
    if not paragraph.inlines or not isinstance(paragraph.inlines[0], Str):
        return False, False, list(paragraph.inlines)
    mark = paragraph.inlines[0].text
    if mark not in {TASK_BOX_UNCHECKED, TASK_BOX_CHECKED}:
        return False, False, list(paragraph.inlines)
    rest = list(paragraph.inlines[1:])
    if rest and isinstance(rest[0], Space):
        rest = rest[1:]
    return True, mark == TASK_BOX_CHECKED, rest


def _plain_inline_text(inline: InlineNode) -> str:
    if isinstance(inline, Str):
        return inline.text
    if isinstance(inline, Space):
        return ' '
    if isinstance(inline, (SoftBreak, HardBreak)):
        return '\n'
    if isinstance(inline, (Emph, Strong, Strikeout, Subscript, Superscript, Span, Link, Image)):
        return ''.join(_plain_inline_text(i) for i in inline.inlines)
    if isinstance(inline, Math):
        return inline.text
    if isinstance(inline, Code):
        return inline.text
    if isinstance(inline, RawInline):
        return inline.text if inline.format == 'html' else ''
    if isinstance(inline, Note):
        return ''
    if isinstance(inline, Cite):
        return _render_citation_source(inline)
    raise HtmlWriterError(f'Unsupported inline node for text extraction: {type(inline).__name__}')


def _render_citation_source(inline: Cite) -> str:
    def render_suffix(inlines: list[InlineNode]) -> str:
        return ''.join(_plain_inline_text(i) for i in inlines)

    if not inline.citations:
        raise HtmlWriterError('Empty citation groups are outside the current HTML writer scope.')
    if len(inline.citations) == 1 and inline.citations[0].mode == 'AuthorInText':
        citation = inline.citations[0]
        suffix = render_suffix(citation.suffix)
        return f'@{citation.citation_id}' + (f' [{suffix}]' if suffix else '')
    rendered_items: list[str] = []
    for idx, citation in enumerate(inline.citations):
        head = '-@' if citation.mode == 'SuppressAuthor' else '@'
        piece = f'{head}{citation.citation_id}{render_suffix(citation.suffix)}'
        if idx == 0 and citation.prefix:
            prefix = ''.join(_plain_inline_text(i) for i in citation.prefix)
            piece = f'{prefix} {piece}'
        rendered_items.append(piece)
    return '[' + '; '.join(rendered_items) + ']'


def _render_inline(inline: InlineNode, ctx: _HtmlWriterContext) -> str:
    if isinstance(inline, Str):
        return _escape_text(inline.text)
    if isinstance(inline, Space):
        return ' '
    if isinstance(inline, SoftBreak):
        return '\n'
    if isinstance(inline, HardBreak):
        return '<br />\n'
    if isinstance(inline, Emph):
        return f'<em>{_render_inlines(inline.inlines, ctx)}</em>'
    if isinstance(inline, Strong):
        return f'<strong>{_render_inlines(inline.inlines, ctx)}</strong>'
    if isinstance(inline, Strikeout):
        return f'<del>{_render_inlines(inline.inlines, ctx)}</del>'
    if isinstance(inline, Subscript):
        return f'<sub>{_render_inlines(inline.inlines, ctx)}</sub>'
    if isinstance(inline, Superscript):
        return f'<sup>{_render_inlines(inline.inlines, ctx)}</sup>'
    if isinstance(inline, Math):
        cls = 'display' if inline.display else 'inline'
        delimiters = ('\\[\n', '\n\\]') if inline.display else ('\\(', '\\)')
        return f'<span class="math {cls}">{_escape_text(delimiters[0] + inline.text + delimiters[1])}</span>'
    if isinstance(inline, Code):
        return f'<code>{_escape_text(inline.text)}</code>'
    if isinstance(inline, Span):
        return f'<span{_attrs_to_html(_attr_items(inline.attr))}>{_render_inlines(inline.inlines, ctx)}</span>'
    if isinstance(inline, Link):
        attrs = [('href', inline.target)]
        if inline.autolink and not inline.attr.identifier and not inline.attr.classes and not inline.attr.attributes and ctx.source_format not in {'commonmark', 'commonmark_x'}:
            attrs.append(('class', 'email' if inline.target.startswith('mailto:') else 'uri'))
        attrs += _attr_items(inline.attr)
        if inline.title:
            attrs.append(('title', inline.title))
        return f'<a{_attrs_to_html(attrs)}>{_render_inlines(inline.inlines, ctx)}</a>'
    if isinstance(inline, Image):
        attrs = [('src', inline.target)] + _attr_items(inline.attr)
        attrs.append(('alt', ''.join(_plain_inline_text(i) for i in inline.inlines)))
        if inline.title:
            attrs.append(('title', inline.title))
        return f'<img{_attrs_to_html(attrs)} />'
    if isinstance(inline, RawInline):
        if inline.format == 'html':
            return inline.text
        if inline.format in {'tex', 'latex'}:
            return ''
        raise HtmlWriterError(f'Unsupported RawInline format in current HTML writer slice: {inline.format}')
    if isinstance(inline, Note):
        if not inline.blocks:
            raise HtmlWriterError('Empty notes are outside the current HTML writer scope.')
        number = len(ctx.footnotes) + 1
        ctx.footnotes.append(list(inline.blocks))
        return f'<a href="#fn{number}" class="footnote-ref" id="fnref{number}" role="doc-noteref"><sup>{number}</sup></a>'
    if isinstance(inline, Cite):
        cites = ' '.join(c.citation_id for c in inline.citations)
        return f'<span class="citation" data-cites="{_escape_attr(cites)}">{_escape_text(_render_citation_source(inline))}</span>'
    raise HtmlWriterError(f'Unsupported inline node for HTML writer: {type(inline).__name__}')


def _render_inlines(inlines: list[InlineNode], ctx: _HtmlWriterContext) -> str:
    return ''.join(_render_inline(inline, ctx) for inline in inlines)


def _heading_attr(block: Heading, ctx: _HtmlWriterContext) -> Attr:
    if block.attr.identifier:
        return block.attr
    if ctx.source_format == 'commonmark' and not block.attr.classes and not block.attr.attributes:
        return block.attr
    return Attr(identifier=_slugify_heading_text(''.join(_plain_inline_text(i) for i in block.inlines)), classes=list(block.attr.classes), attributes=list(block.attr.attributes))


def _paragraph_as_figure(block: Paragraph, source_format: str = '') -> Figure | None:
    if source_format in {'commonmark', 'commonmark_x'}:
        return None
    if len(block.inlines) != 1 or not isinstance(block.inlines[0], Image):
        return None
    image = block.inlines[0]
    return Figure(
        image=Image(inlines=image.inlines, target=image.target, title=image.title, attr=Attr(classes=list(image.attr.classes), attributes=list(image.attr.attributes))),
        attr=Attr(identifier=image.attr.identifier),
    )


def _render_paragraph(block: Paragraph, ctx: _HtmlWriterContext) -> str:
    maybe_figure = _paragraph_as_figure(block, ctx.source_format)
    if maybe_figure is not None:
        return _render_figure(maybe_figure, ctx)
    return f'<p>{_render_inlines(block.inlines, ctx)}</p>'


def _render_heading(block: Heading, ctx: _HtmlWriterContext) -> str:
    attr = _heading_attr(block, ctx)
    return f'<h{block.level}{_attrs_to_html(_attr_items(attr))}>{_render_inlines(block.inlines, ctx)}</h{block.level}>'


def _render_thematic_break(_block: ThematicBreak) -> str:
    return '<hr />'


def _render_code_block(block: CodeBlock) -> str:
    classes = list(block.attr.classes)
    if block.info and block.info not in classes:
        classes.insert(0, block.info)
    pre_attr = Attr(identifier=block.attr.identifier, classes=classes, attributes=list(block.attr.attributes))
    return f'<pre{_attrs_to_html(_attr_items(pre_attr))}><code>{_escape_text(block.text)}</code></pre>'


def _render_raw_block(block: RawBlock) -> str:
    if block.format == 'html':
        return block.text
    if block.format in {'tex', 'latex'}:
        return ''
    raise HtmlWriterError(f'Unsupported RawBlock format in current HTML writer slice: {block.format}')


def _render_block_quote(block: BlockQuote, ctx: _HtmlWriterContext) -> str:
    return f'<blockquote>\n{_render_blocks(block.blocks, ctx)}\n</blockquote>'




def _item_is_compact(item: list[Block]) -> bool:
    return bool(item) and isinstance(item[0], Paragraph) and _is_simple_paragraph(item[0]) and all(isinstance(block, (BulletList, OrderedList)) for block in item[1:])


def _list_is_loose(items: list[list[Block]]) -> bool:
    return any(not _item_is_compact(item) for item in items)

def _render_list_item(item: list[Block], ctx: _HtmlWriterContext, *, force_paragraph: bool = False) -> str:
    if not item or not isinstance(item[0], Paragraph):
        raise HtmlWriterError('Current HTML writer requires list items to start with a paragraph.')
    first = item[0]
    is_task, checked, task_rest = _task_state(first)
    if not force_paragraph and len(item) == 1 and _is_simple_paragraph(first):
        if is_task:
            checkbox = '<input type="checkbox" checked="" />' if checked else '<input type="checkbox" />'
            return f'<li><label>{checkbox}{_render_inlines(task_rest, ctx)}</label></li>'
        return f'<li>{_render_inlines(first.inlines, ctx)}</li>'
    pieces: list[str] = []
    if not force_paragraph and _is_simple_paragraph(first) and all(isinstance(block, (BulletList, OrderedList)) for block in item[1:]):
        if is_task:
            checkbox = '<input type="checkbox" checked="" />' if checked else '<input type="checkbox" />'
            pieces.append(f'<label>{checkbox}{_render_inlines(task_rest, ctx)}</label>')
        else:
            pieces.append(_render_inlines(first.inlines, ctx))
    elif is_task and _is_simple_paragraph(first):
        checkbox = '<input type="checkbox" checked="" />' if checked else '<input type="checkbox" />'
        pieces.append(f'<p><label>{checkbox}{_render_inlines(task_rest, ctx)}</label></p>')
    else:
        pieces.append(_render_paragraph(first, ctx))
    for block in item[1:]:
        pieces.append(_render_block(block, ctx))
    return '<li>\n' + '\n'.join(piece for piece in pieces if piece) + '\n</li>'


def _render_bullet_list(block: BulletList, ctx: _HtmlWriterContext) -> str:
    is_task_list = bool(block.items) and all(item and isinstance(item[0], Paragraph) and _task_state(item[0])[0] for item in block.items)
    attr = ' class="task-list"' if is_task_list else ''
    force_paragraph = _list_is_loose(block.items)
    items = '\n'.join(_render_list_item(item, ctx, force_paragraph=force_paragraph) for item in block.items)
    return f'<ul{attr}>\n{items}\n</ul>'


def _render_ordered_list(block: OrderedList, ctx: _HtmlWriterContext) -> str:
    attrs: list[tuple[str, str]] = [('type', '1')]
    if block.start != 1:
        attrs.insert(0, ('start', str(block.start)))
    force_paragraph = _list_is_loose(block.items)
    items = '\n'.join(_render_list_item(item, ctx, force_paragraph=force_paragraph) for item in block.items)
    return f'<ol{_attrs_to_html(attrs)}>\n{items}\n</ol>'


def _render_definition_list(block: DefinitionList, ctx: _HtmlWriterContext) -> str:
    lines = ['<dl>']
    for term, definitions in block.items:
        lines.append(f'<dt>{_render_inlines(term, ctx)}</dt>')
        for definition_blocks in definitions:
            lines.append('<dd>')
            if len(definition_blocks) == 1 and isinstance(definition_blocks[0], Paragraph):
                lines.append(_render_inlines(definition_blocks[0].inlines, ctx))
            else:
                lines.append(_render_blocks(definition_blocks, ctx))
            lines.append('</dd>')
    lines.append('</dl>')
    return '\n'.join(lines)


def _render_div(block: Div, ctx: _HtmlWriterContext) -> str:
    return f'<div{_attrs_to_html(_attr_items(block.attr))}>\n{_render_blocks(block.blocks, ctx)}\n</div>'


def _render_figure(block: Figure, ctx: _HtmlWriterContext) -> str:
    figure_attrs = _attrs_to_html(_attr_items(block.attr, include_class=False))
    image_attrs = [('src', block.image.target)] + _attr_items(block.image.attr) + [('alt', ''.join(_plain_inline_text(i) for i in block.image.inlines))]
    if block.image.title:
        image_attrs.append(('title', block.image.title))
    caption = _render_inlines(block.image.inlines, ctx)
    return f'<figure{figure_attrs}>\n<img{_attrs_to_html(image_attrs)} />\n<figcaption aria-hidden="true">{caption}</figcaption>\n</figure>'


def _align_style(align: str) -> str | None:
    return {
        'AlignDefault': None,
        'AlignLeft': 'left',
        'AlignCenter': 'center',
        'AlignRight': 'right',
    }[align]


def _render_table_cell(tag: str, inlines: list[InlineNode], align: str, ctx: _HtmlWriterContext) -> str:
    attrs: list[tuple[str, str]] = []
    style = _align_style(align)
    if style is not None:
        attrs.append(('style', f'text-align: {style};'))
    return f'<{tag}{_attrs_to_html(attrs)}>{_render_inlines(inlines, ctx)}</{tag}>'


def _render_table(block: Table, ctx: _HtmlWriterContext) -> str:
    lines = ['<table>']
    if block.caption:
        lines.append(f'<caption>{_render_inlines(block.caption, ctx)}</caption>')
    lines.extend(['<thead>', '<tr class="header">'])
    for idx, cell in enumerate(block.headers):
        lines.append(_render_table_cell('th', cell, block.aligns[idx], ctx))
    lines.extend(['</tr>', '</thead>', '<tbody>'])
    for row_idx, row in enumerate(block.rows):
        lines.append(f'<tr class="{"odd" if row_idx % 2 == 0 else "even"}">')
        for col_idx, cell in enumerate(row):
            lines.append(_render_table_cell('td', cell, block.aligns[col_idx], ctx))
        lines.append('</tr>')
    lines.extend(['</tbody>', '</table>'])
    return '\n'.join(lines)


def _render_block(block: Block, ctx: _HtmlWriterContext) -> str:
    if isinstance(block, Paragraph):
        return _render_paragraph(block, ctx)
    if isinstance(block, Heading):
        return _render_heading(block, ctx)
    if isinstance(block, ThematicBreak):
        return _render_thematic_break(block)
    if isinstance(block, CodeBlock):
        return _render_code_block(block)
    if isinstance(block, RawBlock):
        return _render_raw_block(block)
    if isinstance(block, BlockQuote):
        return _render_block_quote(block, ctx)
    if isinstance(block, BulletList):
        return _render_bullet_list(block, ctx)
    if isinstance(block, OrderedList):
        return _render_ordered_list(block, ctx)
    if isinstance(block, DefinitionList):
        return _render_definition_list(block, ctx)
    if isinstance(block, Div):
        return _render_div(block, ctx)
    if isinstance(block, Figure):
        return _render_figure(block, ctx)
    if isinstance(block, Table):
        return _render_table(block, ctx)
    raise HtmlWriterError(f'Unsupported block node for HTML writer: {type(block).__name__}')


def _render_blocks(blocks: list[Block], ctx: _HtmlWriterContext) -> str:
    rendered = [_render_block(block, ctx) for block in blocks]
    return '\n'.join(part for part in rendered if part)


def _render_footnotes(ctx: _HtmlWriterContext) -> str:
    if not ctx.footnotes:
        return ''
    lines = [
        '<section id="footnotes" class="footnotes footnotes-end-of-document" role="doc-endnotes">',
        '<hr />',
        '<ol>',
    ]
    for idx, blocks in enumerate(ctx.footnotes, start=1):
        rendered = _render_blocks(blocks, ctx)
        backlink = f'<a href="#fnref{idx}" class="footnote-back" role="doc-backlink">↩︎</a>'
        if rendered.endswith('</p>'):
            rendered = rendered[:-4] + backlink + '</p>'
        else:
            rendered += backlink
        lines.append(f'<li id="fn{idx}">{rendered}</li>')
    lines.extend(['</ol>', '</section>'])
    return '\n'.join(lines)


def write_html(document: Document) -> str:
    ctx = _HtmlWriterContext(source_format=document.source_format)
    body = _render_blocks(document.blocks, ctx)
    footnotes = _render_footnotes(ctx)
    if footnotes:
        body = body + ('\n' if body else '') + footnotes
    return body + ('\n' if body else '')
