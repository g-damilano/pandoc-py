"""Jira/Confluence wiki reader/writer — constrained slice."""
from __future__ import annotations

from pandoc_py.ast import (
    BlockQuote, BulletList, CodeBlock, Document, Heading, OrderedList,
    Paragraph, ThematicBreak,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import block_text_paragraphs, inlines_to_plain, parse_simple_blocks, slugify_heading, text_to_inlines


def _read_jira(source: str) -> Document:
    """Jira reader admitting `hN. {anchor:id}Heading`, `* item`, `# item`,
    `bq. quote`, `{noformat}...{noformat}` code blocks.
    """
    import re as _re
    from pandoc_py.ast import Attr, BulletList, CodeBlock, OrderedList, ThematicBreak
    text = source.replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = _re.match(r'^h([1-6])\.\s*(?:\{anchor:([^}]+)\})?(.*)$', line)
        if m:
            level = int(m.group(1))
            anchor = m.group(2) or ''
            heading_text = m.group(3)
            attr = Attr(identifier=anchor) if anchor else Attr()
            blocks.append(Heading(level=level, inlines=text_to_inlines(heading_text), attr=attr))
            i += 1; continue
        if line.strip() == '{noformat}':
            buf, j = [], i + 1
            while j < len(lines) and not lines[j].endswith('{noformat}'):
                buf.append(lines[j]); j += 1
            if j < len(lines):
                tail = lines[j][:-len('{noformat}')]
                if tail: buf.append(tail)
            blocks.append(CodeBlock(text='\n'.join(buf)))
            i = j + 1; continue
        m = _re.match(r'^\*\s+(.*)$', line)
        if m:
            items = []
            while i < len(lines):
                im = _re.match(r'^\*\s+(.*)$', lines[i])
                if not im: break
                items.append([Paragraph(inlines=text_to_inlines(im.group(1)), is_plain=True)])
                i += 1
            blocks.append(BulletList(items=items)); continue
        m = _re.match(r'^#\s+(.*)$', line)
        if m:
            items = []
            while i < len(lines):
                im = _re.match(r'^#\s+(.*)$', lines[i])
                if not im: break
                items.append([Paragraph(inlines=text_to_inlines(im.group(1)), is_plain=True)])
                i += 1
            blocks.append(OrderedList(items=items)); continue
        m = _re.match(r'^bq\.\s+(.*)$', line)
        if m:
            blocks.append(BlockQuote(blocks=[Paragraph(inlines=text_to_inlines(m.group(1)))]))
            i += 1; continue
        if _re.match(r'^----+\s*$', line):
            blocks.append(ThematicBreak()); i += 1; continue
        if not line.strip():
            i += 1; continue
        buf = [line]; j = i + 1
        while j < len(lines) and lines[j].strip() and not (
            _re.match(r'^h[1-6]\.', lines[j]) or
            _re.match(r'^\*\s+', lines[j]) or
            _re.match(r'^#\s+', lines[j]) or
            _re.match(r'^bq\.\s+', lines[j]) or
            lines[j].strip() == '{noformat}'
        ):
            buf.append(lines[j]); j += 1
        blocks.append(Paragraph(inlines=text_to_inlines(' '.join(s.rstrip() for s in buf))))
        i = j
    return Document(blocks=blocks, source_format='jira')


def _write_jira(document: Document) -> str:
    out: list[str] = []
    blocks = document.blocks
    for idx, block in enumerate(blocks):
        if isinstance(block, Heading):
            text = inlines_to_plain(block.inlines)
            anchor = block.attr.identifier or slugify_heading(text)
            level = max(1, min(block.level, 6))
            out.append(f'h{level}. ' + '{anchor:' + anchor + '}' + text)
        elif isinstance(block, Paragraph):
            out.append(inlines_to_plain(block.inlines))
        elif isinstance(block, BulletList):
            for item in block.items:
                for sub in block_text_paragraphs(item): out.append(f'* {sub}')
        elif isinstance(block, OrderedList):
            n = block.start
            for item in block.items:
                for sub in block_text_paragraphs(item): out.append(f'# {sub}'); n += 1
        elif isinstance(block, BlockQuote):
            for sub in block_text_paragraphs(block.blocks): out.append(f'bq. {sub}')
        elif isinstance(block, CodeBlock):
            out.append('{noformat}')
            out.append(block.text + '{noformat}')
        elif isinstance(block, ThematicBreak):
            out.append('----')
        # Blank line between blocks unless previous was a heading (pandoc
        # joins heading immediately to following paragraph).
        if idx + 1 < len(blocks) and not isinstance(block, Heading):
            out.append('')
    return '\n'.join(out) + '\n'


class JiraReader(Reader):
    format_name = 'jira'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_jira(source)

class JiraWriter(Writer):
    format_name = 'jira'
    def write(self, document, options=None):
        return _write_jira(document)

register_reader(JiraReader())
register_writer(JiraWriter())
