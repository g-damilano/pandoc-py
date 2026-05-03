"""Muse reader/writer — constrained slice."""
from __future__ import annotations

import re

from pandoc_py.ast import (
    BlockQuote, BulletList, CodeBlock, Document, Heading, OrderedList, Paragraph, ThematicBreak,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import block_text_paragraphs, inlines_to_plain, text_to_inlines


def _read_muse(source: str) -> Document:
    text = source.replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^(\*+)\s+(.*)$', line)
        if m:
            level = max(1, min(len(m.group(1)), 5))
            blocks.append(Heading(level=level, inlines=text_to_inlines(m.group(2))))
            i += 1; continue
        if line.lstrip().startswith('<example>'):
            buf, j = [], i + 1
            while j < len(lines) and not lines[j].lstrip().startswith('</example>'):
                buf.append(lines[j]); j += 1
            blocks.append(CodeBlock(text='\n'.join(buf)))
            i = j + 1; continue
        m = re.match(r'^\s*-\s+(.*)$', line)
        if m:
            items = []
            while i < len(lines):
                im = re.match(r'^\s*-\s+(.*)$', lines[i])
                if not im: break
                items.append([Paragraph(inlines=text_to_inlines(im.group(1)), is_plain=True)])
                i += 1
            blocks.append(BulletList(items=items)); continue
        m = re.match(r'^\s*\d+\.\s+(.*)$', line)
        if m:
            items = []
            while i < len(lines):
                im = re.match(r'^\s*\d+\.\s+(.*)$', lines[i])
                if not im: break
                items.append([Paragraph(inlines=text_to_inlines(im.group(1)), is_plain=True)])
                i += 1
            blocks.append(OrderedList(items=items)); continue
        if re.match(r'^----+\s*$', line):
            blocks.append(ThematicBreak()); i += 1; continue
        if not line.strip():
            i += 1; continue
        buf = [line]; j = i + 1
        while j < len(lines) and lines[j].strip() and not (
            re.match(r'^\*+\s+', lines[j]) or
            re.match(r'^\s*[-*]\s+', lines[j]) or
            re.match(r'^\s*\d+\.\s+', lines[j]) or
            lines[j].lstrip().startswith('<example>')
        ):
            buf.append(lines[j]); j += 1
        blocks.append(Paragraph(inlines=text_to_inlines(' '.join(s.rstrip() for s in buf))))
        i = j
    return Document(blocks=blocks, source_format='muse')


def _write_muse(document: Document) -> str:
    out: list[str] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            out.append('*' * max(1, min(block.level, 5)) + ' ' + inlines_to_plain(block.inlines))
            out.append('')
        elif isinstance(block, Paragraph):
            out.append(inlines_to_plain(block.inlines)); out.append('')
        elif isinstance(block, BulletList):
            for item in block.items:
                for sub in block_text_paragraphs(item): out.append(f' - {sub}')
            out.append('')
        elif isinstance(block, OrderedList):
            n = block.start
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out.append(f' {n}. {sub}')
                n += 1
            out.append('')
        elif isinstance(block, BlockQuote):
            for sub in block_text_paragraphs(block.blocks): out.append(f' {sub}')
            out.append('')
        elif isinstance(block, CodeBlock):
            out.append('<example>'); out.extend(block.text.split('\n')); out.append('</example>'); out.append('')
        elif isinstance(block, ThematicBreak):
            out.append('----'); out.append('')
    return '\n'.join(out).rstrip('\n') + '\n'


class MuseReader(Reader):
    format_name = 'muse'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_muse(source)

class MuseWriter(Writer):
    format_name = 'muse'
    def write(self, document, options=None):
        return _write_muse(document)

register_reader(MuseReader())
register_writer(MuseWriter())
