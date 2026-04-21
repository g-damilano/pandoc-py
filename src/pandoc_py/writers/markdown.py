from __future__ import annotations

from dataclasses import dataclass, field

from pandoc_py.ast import (
    Attr,
    BlockQuote,
    BulletList,
    Cite,
    Citation,
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
    LineBlock,
    Link,
    Math,
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
    Table,
    ThematicBreak,
    Underline,
)

THEMATIC_BREAK_RENDER = '-' * 72


class MarkdownWriterError(TypeError):
    """Raised when the writer receives a node outside the supported AST slice."""


InlineNode = Str | Space | SoftBreak | HardBreak | Emph | Strong | Strikeout | Subscript | Superscript | Underline | SmallCaps | Quoted | Math | Code | Span | Link | Image | RawInline | Note | Cite


@dataclass
class _MarkdownWriterContext:
    footnotes: list[str] = field(default_factory=list)


def _attr_is_empty(attr: Attr) -> bool:
    return not attr.identifier and not attr.classes and not attr.attributes


def _write_attr(attr: Attr) -> str:
    if _attr_is_empty(attr):
        return ''
    parts: list[str] = []
    if attr.identifier:
        parts.append(f'#{attr.identifier}')
    for cls in attr.classes:
        parts.append(f'.{cls}')
    for key, value in attr.attributes:
        parts.append(f'{key}="{value}"')
    return '{' + ' '.join(parts) + '}'


def _write_target_and_title(target: str, title: str) -> str:
    return f'{target} "{title}"' if title else target


def _merge_figure_attr(figure: Figure) -> Attr:
    return Attr(
        identifier=figure.attr.identifier,
        classes=list(figure.image.attr.classes),
        attributes=list(figure.image.attr.attributes),
    )


def _render_footnote_definition(number: int, body: str) -> str:
    lines = body.split('\n') if body else ['']
    rendered = [f'[^{number}]: {lines[0]}']
    for line in lines[1:]:
        rendered.append(('    ' + line) if line else '')
    return '\n'.join(rendered)


def _write_citation_suffix(inlines: list[InlineNode], ctx: _MarkdownWriterContext) -> str:
    return ''.join(_write_inline(inline, ctx) for inline in inlines)


def _write_single_citation(citation: Citation, ctx: _MarkdownWriterContext) -> str:
    head = '-@' if citation.mode == 'SuppressAuthor' else '@'
    suffix = _write_citation_suffix(citation.suffix, ctx)
    return f'{head}{citation.citation_id}{suffix}'


def _write_cite(inline: Cite, ctx: _MarkdownWriterContext) -> str:
    if not inline.citations:
        raise MarkdownWriterError('Empty citation groups are outside the current writer scope.')
    if len(inline.citations) == 1 and inline.citations[0].mode == 'AuthorInText':
        citation = inline.citations[0]
        suffix = _write_citation_suffix(citation.suffix, ctx)
        return f'@{citation.citation_id}' + (f' [{suffix}]' if suffix else '')
    rendered_items: list[str] = []
    for idx, citation in enumerate(inline.citations):
        piece = _write_single_citation(citation, ctx)
        if idx == 0 and citation.prefix:
            prefix = _write_inlines(citation.prefix, ctx)
            piece = f'{prefix} {piece}'
        rendered_items.append(piece)
    return '[' + '; '.join(rendered_items) + ']'


def _quote_marks(quote_type: str) -> tuple[str, str]:
    if quote_type == 'SingleQuote':
        return "'", "'"
    if quote_type == 'DoubleQuote':
        return '"', '"'
    raise MarkdownWriterError(f'Unsupported quote type in current markdown writer slice: {quote_type}')


def _write_inline(inline: InlineNode, ctx: _MarkdownWriterContext) -> str:
    if isinstance(inline, Str):
        return inline.text
    if isinstance(inline, Space):
        return ' '
    if isinstance(inline, SoftBreak):
        return ' '
    if isinstance(inline, HardBreak):
        return '\\' + '\n'
    if isinstance(inline, Emph):
        return f"*{_write_inlines(inline.inlines, ctx)}*"
    if isinstance(inline, Strong):
        return f"**{_write_inlines(inline.inlines, ctx)}**"
    if isinstance(inline, Strikeout):
        return f"~~{_write_inlines(inline.inlines, ctx)}~~"
    if isinstance(inline, Subscript):
        return f"~{_write_inlines(inline.inlines, ctx)}~"
    if isinstance(inline, Superscript):
        return f"^{_write_inlines(inline.inlines, ctx)}^"
    if isinstance(inline, Underline):
        return f'[{_write_inlines(inline.inlines, ctx)}]{{.underline}}'
    if isinstance(inline, SmallCaps):
        return f'[{_write_inlines(inline.inlines, ctx)}]{{.smallcaps}}'
    if isinstance(inline, Quoted):
        open_q, close_q = _quote_marks(inline.quote_type)
        return f'{open_q}{_write_inlines(inline.inlines, ctx)}{close_q}'
    if isinstance(inline, Math):
        delim = '$$' if inline.display else '$'
        return f'{delim}{inline.text}{delim}'
    if isinstance(inline, Code):
        return f'`{inline.text}`'
    if isinstance(inline, Span):
        return f'[{_write_inlines(inline.inlines, ctx)}]{_write_attr(inline.attr)}'
    if isinstance(inline, Link):
        if inline.autolink:
            if inline.target.startswith('mailto:'):
                core = f"<{inline.target[len('mailto:'):]}>"
            else:
                core = f'<{inline.target}>'
            return core + _write_attr(inline.attr)
        return f'[{_write_inlines(inline.inlines, ctx)}]({_write_target_and_title(inline.target, inline.title)}){_write_attr(inline.attr)}'
    if isinstance(inline, Image):
        return f'![{_write_inlines(inline.inlines, ctx)}]({_write_target_and_title(inline.target, inline.title)}){_write_attr(inline.attr)}'
    if isinstance(inline, RawInline):
        if inline.format not in {'html', 'tex', 'latex'}:
            raise MarkdownWriterError(f'Unsupported RawInline format in current writer slice: {inline.format}')
        if '`' in inline.text:
            raise MarkdownWriterError('Backticks inside RawInline are outside the current writer scope.')
        return f'`{inline.text}`{{={inline.format}}}'
    if isinstance(inline, Cite):
        return _write_cite(inline, ctx)
    if isinstance(inline, Note):
        if not inline.blocks:
            raise MarkdownWriterError('Empty notes are outside the current markdown writer scope.')
        body = _write_blocks(inline.blocks, ctx).rstrip('\n')
        number = len(ctx.footnotes) + 1
        ctx.footnotes.append(_render_footnote_definition(number, body))
        return f'[^{number}]'
    raise MarkdownWriterError(f'Unsupported inline node for markdown writer: {type(inline).__name__}')


def _write_inlines(inlines: list[InlineNode], ctx: _MarkdownWriterContext) -> str:
    return ''.join(_write_inline(inline, ctx) for inline in inlines).strip()


def _write_raw_inlines(inlines: list[InlineNode], ctx: _MarkdownWriterContext) -> str:
    return ''.join(_write_inline(inline, ctx) for inline in inlines)


def _write_paragraph(block: Paragraph, ctx: _MarkdownWriterContext) -> str:
    return _write_inlines(block.inlines, ctx)


def _write_line_block(block: LineBlock, ctx: _MarkdownWriterContext) -> str:
    rendered_lines: list[str] = []
    for line in block.lines:
        text = _write_raw_inlines(line, ctx)
        rendered_lines.append('| ' + text if text else '|')
    return '\n'.join(rendered_lines)


def _write_heading(block: Heading, ctx: _MarkdownWriterContext) -> str:
    if not 1 <= block.level <= 6:
        raise MarkdownWriterError(f'Unsupported heading level: {block.level}')
    suffix = _write_attr(block.attr) if not _attr_is_empty(block.attr) else ''
    body = _write_inlines(block.inlines, ctx)
    if suffix:
        return f"{'#' * block.level} {body} {suffix}"
    return f"{'#' * block.level} {body}"


def _write_thematic_break(_block: ThematicBreak) -> str:
    return THEMATIC_BREAK_RENDER


def _write_code_block(block: CodeBlock) -> str:
    classes = list(block.attr.classes)
    if block.info and block.info not in classes:
        classes.insert(0, block.info)
    attr = Attr(identifier=block.attr.identifier, classes=classes, attributes=list(block.attr.attributes))
    if not _attr_is_empty(block.attr):
        return f"```{_write_attr(attr)}\n{block.text}\n```"
    if block.info:
        return f"``` {block.info}\n{block.text}\n```"
    lines = block.text.split('\n') if block.text else ['']
    rendered: list[str] = []
    for line in lines:
        rendered.append(f'    {line}' if line else '')
    return '\n'.join(rendered)


def _write_raw_block(block: RawBlock) -> str:
    if block.format not in {'html', 'tex', 'latex'}:
        raise MarkdownWriterError(f'Unsupported RawBlock format in current writer slice: {block.format}')
    body = block.text[:-1] if block.text.endswith('\n') else block.text
    return f"```{{={block.format}}}\n{body}\n```"


def _write_block_quote(block: BlockQuote, ctx: _MarkdownWriterContext) -> str:
    if len(block.blocks) != 1 or not isinstance(block.blocks[0], Paragraph):
        raise MarkdownWriterError('Current markdown writer supports block quotes with one paragraph only.')
    paragraph = _write_paragraph(block.blocks[0], ctx)
    return '\n'.join(f'> {line}' for line in paragraph.split('\n'))


def _task_marker_and_rest(paragraph: Paragraph, ctx: _MarkdownWriterContext) -> str | None:
    if not paragraph.inlines or not isinstance(paragraph.inlines[0], Str):
        return None
    mark = paragraph.inlines[0].text
    if mark not in {'☐', '☒'}:
        return None
    rest_inlines = list(paragraph.inlines[1:])
    if rest_inlines and isinstance(rest_inlines[0], Space):
        rest_inlines = rest_inlines[1:]
    rendered_rest = _write_inlines(rest_inlines, ctx)
    prefix = '[x]' if mark == '☒' else '[ ]'
    return prefix if not rendered_rest else f'{prefix} {rendered_rest}'


def _indent_lines(text: str, count: int) -> str:
    prefix = ' ' * count
    return '\n'.join((prefix + line) if line else '' for line in text.split('\n'))


def _write_list_item(item: list[object], marker: str, ctx: _MarkdownWriterContext) -> str:
    if not item or not isinstance(item[0], Paragraph):
        raise MarkdownWriterError('Current markdown writer requires list items to start with a paragraph.')
    first = _task_marker_and_rest(item[0], ctx) or _write_paragraph(item[0], ctx)
    rendered = [f'{marker}{first}']
    indent = len(marker)
    for idx, block in enumerate(item[1:], start=1):
        block_text = _write_blocks([block], ctx).rstrip('\n')
        indented = _indent_lines(block_text, indent)
        if idx == 1 and isinstance(block, (BulletList, OrderedList)) and _paragraph_is_simple_list_head(item[0]):
            rendered.append(indented)
        else:
            rendered.append('')
            rendered.append(indented)
    return '\n'.join(rendered)


def _paragraph_is_simple_list_head(paragraph: Paragraph) -> bool:
    return all(not isinstance(inline, (SoftBreak, HardBreak, Note)) for inline in paragraph.inlines)


def _item_is_compact(item: list[object]) -> bool:
    return bool(item) and isinstance(item[0], Paragraph) and _paragraph_is_simple_list_head(item[0]) and all(isinstance(block, (BulletList, OrderedList)) for block in item[1:])


def _list_is_loose(items: list[list[object]]) -> bool:
    return any(not _item_is_compact(item) for item in items)


def _write_bullet_list(block: BulletList, ctx: _MarkdownWriterContext) -> str:
    separator = '\n\n' if _list_is_loose(block.items) else '\n'
    return separator.join(_write_list_item(item, '-   ', ctx) for item in block.items)


def _write_ordered_list(block: OrderedList, ctx: _MarkdownWriterContext) -> str:
    rendered_items: list[str] = []
    number = block.start
    for item in block.items:
        rendered_items.append(_write_list_item(item, f'{number}.  ', ctx))
        number += 1
    separator = '\n\n' if _list_is_loose(block.items) else '\n'
    return separator.join(rendered_items)


def _write_definition_list(block: DefinitionList, ctx: _MarkdownWriterContext) -> str:
    rendered_items: list[str] = []
    for term, definitions in block.items:
        if len(definitions) != 1 or len(definitions[0]) != 1 or not isinstance(definitions[0][0], Paragraph):
            raise MarkdownWriterError('Current markdown writer supports one paragraph per definition only.')
        rendered_items.append(f'{_write_inlines(term, ctx)}\n:   {_write_paragraph(definitions[0][0], ctx)}')
    return '\n\n'.join(rendered_items)


def _write_div(block: Div, ctx: _MarkdownWriterContext) -> str:
    inner = _write_blocks(block.blocks, ctx).rstrip('\n')
    if not _attr_is_empty(block.attr):
        return f":::{_write_attr(block.attr)}\n{inner}\n:::"
    return f":::\n{inner}\n:::"


def _write_figure(block: Figure, ctx: _MarkdownWriterContext) -> str:
    image = block.image
    merged_attr = _merge_figure_attr(block)
    return f'![{_write_inlines(image.inlines, ctx)}]({_write_target_and_title(image.target, image.title)}){_write_attr(merged_attr)}'


def _align_text(text: str, width: int, align: str, *, header: bool = False) -> str:
    if header or align == 'AlignLeft' or align == 'AlignDefault':
        return text.ljust(width)
    if align == 'AlignRight':
        return text.rjust(width)
    if align == 'AlignCenter':
        return text.center(width)
    raise MarkdownWriterError(f'Unsupported table alignment: {align}')


def _write_table(block: Table, ctx: _MarkdownWriterContext) -> str:
    if not block.headers or not block.aligns:
        raise MarkdownWriterError('Current markdown writer requires a header row and column alignments for tables.')
    column_count = len(block.headers)
    if column_count != len(block.aligns):
        raise MarkdownWriterError('Table header and alignment count mismatch.')
    header_texts = [_write_inlines(cell, ctx) for cell in block.headers]
    row_texts: list[list[str]] = []
    for row in block.rows:
        if len(row) != column_count:
            raise MarkdownWriterError('Current markdown writer requires rectangular table rows.')
        row_texts.append([_write_inlines(cell, ctx) for cell in row])
    widths = []
    for col in range(column_count):
        max_len = max([len(header_texts[col])] + [len(row[col]) for row in row_texts])
        widths.append(max_len + 2)
    header_line = '  ' + ' '.join(_align_text(text, widths[i], block.aligns[i], header=False) for i, text in enumerate(header_texts))
    rule_line = '  ' + ' '.join('-' * width for width in widths)
    body_lines = [
        '  ' + ' '.join(_align_text(text, widths[i], block.aligns[i]) for i, text in enumerate(row))
        for row in row_texts
    ]
    parts = [header_line.rstrip(), rule_line.rstrip(), *[line.rstrip() for line in body_lines]]
    if block.caption:
        parts.extend(['', '  : ' + _write_inlines(block.caption, ctx)])
    return '\n'.join(parts)


def _write_blocks(blocks: list[object], ctx: _MarkdownWriterContext) -> str:
    rendered_blocks: list[str] = []
    for block in blocks:
        if isinstance(block, Paragraph):
            rendered_blocks.append(_write_paragraph(block, ctx))
            continue
        if isinstance(block, LineBlock):
            rendered_blocks.append(_write_line_block(block, ctx))
            continue
        if isinstance(block, Null):
            continue
        if isinstance(block, Heading):
            rendered_blocks.append(_write_heading(block, ctx))
            continue
        if isinstance(block, ThematicBreak):
            rendered_blocks.append(_write_thematic_break(block))
            continue
        if isinstance(block, CodeBlock):
            rendered_blocks.append(_write_code_block(block))
            continue
        if isinstance(block, RawBlock):
            rendered_blocks.append(_write_raw_block(block))
            continue
        if isinstance(block, BlockQuote):
            rendered_blocks.append(_write_block_quote(block, ctx))
            continue
        if isinstance(block, BulletList):
            rendered_blocks.append(_write_bullet_list(block, ctx))
            continue
        if isinstance(block, OrderedList):
            rendered_blocks.append(_write_ordered_list(block, ctx))
            continue
        if isinstance(block, DefinitionList):
            rendered_blocks.append(_write_definition_list(block, ctx))
            continue
        if isinstance(block, Div):
            rendered_blocks.append(_write_div(block, ctx))
            continue
        if isinstance(block, Figure):
            rendered_blocks.append(_write_figure(block, ctx))
            continue
        if isinstance(block, Table):
            rendered_blocks.append(_write_table(block, ctx))
            continue
        raise MarkdownWriterError(f'Unsupported block node for markdown writer: {type(block).__name__}')
    if not rendered_blocks:
        return ''
    return '\n\n'.join(rendered_blocks) + '\n'


def write_markdown(document: Document) -> str:
    ctx = _MarkdownWriterContext()
    body = _write_blocks(document.blocks, ctx)
    if not ctx.footnotes:
        return body
    rendered_blocks = body.rstrip('\n')
    rendered_blocks += '\n\n' + '\n\n'.join(ctx.footnotes)
    return rendered_blocks + '\n'
