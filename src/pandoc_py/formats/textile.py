"""Textile reader/writer — constrained slice."""
from __future__ import annotations

import re

from pandoc_py.ast import (
    Attr, BulletList, CodeBlock, Document, Heading, OrderedList,
    Paragraph, ThematicBreak,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import block_text_paragraphs, inlines_to_plain, parse_simple_blocks, slugify_heading, text_to_inlines


def _read_textile(source: str) -> Document:
    """Textile reader admitting `hN(#anchor). text` heading-attr syntax."""
    text = source.replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^h([1-6])(?:\(#([^)]+)\))?\.\s+(.*)$', line)
        if m:
            level = int(m.group(1))
            anchor = m.group(2) or ''
            heading_text = m.group(3)
            attr = Attr(identifier=anchor) if anchor else Attr()
            blocks.append(Heading(level=level, inlines=text_to_inlines(heading_text), attr=attr))
            i += 1
            continue
        m = re.match(r'^bc\.\s*(.*)$', line)
        if m:
            blocks.append(CodeBlock(text=m.group(1)))
            i += 1
            continue
        m = re.match(r'^\*\s+(.*)$', line)
        if m:
            items = []
            while i < len(lines):
                im = re.match(r'^\*\s+(.*)$', lines[i])
                if not im: break
                items.append([Paragraph(inlines=text_to_inlines(im.group(1)), is_plain=True)])
                i += 1
            blocks.append(BulletList(items=items)); continue
        m = re.match(r'^#\s+(.*)$', line)
        if m:
            items = []
            while i < len(lines):
                im = re.match(r'^#\s+(.*)$', lines[i])
                if not im: break
                items.append([Paragraph(inlines=text_to_inlines(im.group(1)), is_plain=True)])
                i += 1
            blocks.append(OrderedList(items=items)); continue
        if not line.strip():
            i += 1; continue
        buf = [line]; j = i + 1
        while j < len(lines) and lines[j].strip() and not re.match(r'^h[1-6]', lines[j]) and not lines[j].startswith('bc.'):
            buf.append(lines[j]); j += 1
        blocks.append(Paragraph(inlines=text_to_inlines(' '.join(s.rstrip() for s in buf))))
        i = j
    return Document(blocks=blocks, source_format='textile')


def _write_textile(document: Document) -> str:
    out: list[str] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            text = inlines_to_plain(block.inlines)
            anchor = block.attr.identifier or slugify_heading(text)
            level = max(1, min(block.level, 6))
            out.append(f'h{level}(#{anchor}). {text}')
            out.append('')
        elif isinstance(block, Paragraph):
            out.append(inlines_to_plain(block.inlines)); out.append('')
        elif isinstance(block, BulletList):
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out.append(f'* {sub}')
            out.append('')
        elif isinstance(block, OrderedList):
            n = block.start
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out.append(f'# {sub}')
                n += 1
            out.append('')
        elif isinstance(block, CodeBlock):
            out.append(f'bc. {block.text}'); out.append('')
        elif isinstance(block, ThematicBreak):
            out.append('---'); out.append('')
    return '\n'.join(out).rstrip('\n') + '\n'


class TextileReader(Reader):
    format_name = 'textile'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_textile(source)

class TextileWriter(Writer):
    format_name = 'textile'
    def write(self, document, options=None):
        return _write_textile(document)

register_reader(TextileReader())
register_writer(TextileWriter())
