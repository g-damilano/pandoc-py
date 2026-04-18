from __future__ import annotations

from html import escape

from pandoc_py.ast import Document, Heading, Image, Paragraph
from pandoc_py.writers.html import _attr_items, _attrs_to_html, _plain_inline_text
from pandoc_py.writers.markdown import (
    _MarkdownWriterContext,
    _attr_is_empty,
    _write_attr,
    _write_blocks,
    _write_inlines,
    _write_target_and_title,
)


def _write_heading_commonmark_x(block: Heading, ctx: _MarkdownWriterContext) -> str:
    suffix = '' if _attr_is_empty(block.attr) else f' {_write_attr(block.attr)}'
    return f"{'#' * block.level} {_write_inlines(block.inlines, ctx)}{suffix}"


def _render_figure_html_from_paragraph(block: Paragraph, ctx: _MarkdownWriterContext) -> str | None:
    if len(block.inlines) != 1 or not isinstance(block.inlines[0], Image):
        return None
    image = block.inlines[0]
    figure_attr = []
    if image.attr.identifier:
        figure_attr.append(('id', image.attr.identifier))
    image_attr = _attr_items(image.attr, include_id=False)
    image_attr.insert(0, ('src', image.target))
    image_attr.append(('alt', ''.join(_plain_inline_text(i) for i in image.inlines)))
    if image.title:
        image_attr.append(('title', image.title))
    caption = _write_inlines(image.inlines, ctx)
    lines = [f'<figure{_attrs_to_html(figure_attr)}>', f'<img{_attrs_to_html(image_attr)} />']
    if caption:
        lines.append(f'<figcaption aria-hidden="true">{escape(caption, quote=False)}</figcaption>')
    lines.append('</figure>')
    return '\n'.join(lines)


def write_commonmark_x(document: Document) -> str:
    ctx = _MarkdownWriterContext()
    rendered_blocks: list[str] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            rendered_blocks.append(_write_heading_commonmark_x(block, ctx))
            continue
        if isinstance(block, Paragraph):
            maybe_figure = _render_figure_html_from_paragraph(block, ctx)
            if maybe_figure is not None:
                rendered_blocks.append(maybe_figure)
                continue
        rendered_blocks.append(_write_blocks([block], ctx).rstrip('\n'))
    body = '' if not rendered_blocks else '\n\n'.join(rendered_blocks) + '\n'
    if not ctx.footnotes:
        return body
    rendered = body.rstrip('\n')
    rendered += '\n\n' + '\n\n'.join(ctx.footnotes)
    return rendered + '\n'
