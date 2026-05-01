"""Haddock reader/writer — constrained slice."""
from __future__ import annotations

import re

from pandoc_py.ast import (
    Attr, BlockQuote, BulletList, CodeBlock, Document, Heading, OrderedList,
    Paragraph, ThematicBreak,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import block_text_paragraphs, inlines_to_plain, slugify_heading, text_to_inlines


def _read_haddock(source: str) -> Document:
    """Haddock reader admitting `= text` headings, `> ` code blocks,
    `-   ` bullets, `1.  ` ordered, and `#anchor#` heading-anchor lines.
    """
    text = source.replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^(=+)\s+(.*)$', line)
        if m:
            level = max(1, min(len(m.group(1)), 6))
            heading_text = m.group(2)
            # Optional anchor on next line: #anchor#
            anchor = ''
            if i + 1 < len(lines):
                am = re.match(r'^#([^\s#]+)#\s*$', lines[i + 1].strip())
                if am:
                    anchor = am.group(1)
            attr = Attr(identifier=anchor) if anchor else Attr()
            blocks.append(Heading(level=level, inlines=text_to_inlines(heading_text), attr=attr))
            i += 2 if anchor else 1
            continue
        if line.startswith('> '):
            buf = []
            j = i
            while j < len(lines) and lines[j].startswith('> '):
                buf.append(lines[j][2:]); j += 1
            blocks.append(CodeBlock(text='\n'.join(buf)))
            i = j; continue
        m = re.match(r'^-\s+(.*)$', line)
        if m:
            items = []
            while i < len(lines):
                im = re.match(r'^-\s+(.*)$', lines[i])
                if not im: break
                items.append([Paragraph(inlines=text_to_inlines(im.group(1)), is_plain=True)])
                i += 1
            blocks.append(BulletList(items=items)); continue
        m = re.match(r'^\d+\.\s+(.*)$', line)
        if m:
            items = []
            while i < len(lines):
                im = re.match(r'^\d+\.\s+(.*)$', lines[i])
                if not im: break
                items.append([Paragraph(inlines=text_to_inlines(im.group(1)), is_plain=True)])
                i += 1
            blocks.append(OrderedList(items=items)); continue
        if re.match(r'^---+\s*$', line):
            blocks.append(ThematicBreak()); i += 1; continue
        if not line.strip():
            i += 1; continue
        buf = [line]; j = i + 1
        while j < len(lines) and lines[j].strip() and not (
            re.match(r'^=+\s', lines[j]) or
            re.match(r'^-\s+', lines[j]) or
            re.match(r'^\d+\.\s+', lines[j]) or
            lines[j].startswith('> ') or
            re.match(r'^#[^\s#]+#\s*$', lines[j].strip())
        ):
            buf.append(lines[j]); j += 1
        blocks.append(Paragraph(inlines=text_to_inlines(' '.join(s.rstrip() for s in buf))))
        i = j
    return Document(blocks=blocks, source_format='haddock')


def _write_haddock(document: Document) -> str:
    out: list[str] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            text = inlines_to_plain(block.inlines)
            anchor = block.attr.identifier or slugify_heading(text)
            out.append('=' * max(1, min(block.level, 6)) + ' ' + text)
            out.append(f'#{anchor}#')
            out.append('')
        elif isinstance(block, Paragraph):
            out.append(inlines_to_plain(block.inlines)); out.append('')
        elif isinstance(block, BulletList):
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out.append(f'-   {sub}')
            out.append('')
        elif isinstance(block, OrderedList):
            n = block.start
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out.append(f'{n}.  {sub}')
                n += 1
            out.append('')
        elif isinstance(block, BlockQuote):
            for sub in block_text_paragraphs(block.blocks):
                out.append(f'> {sub}')
            out.append('')
        elif isinstance(block, CodeBlock):
            for ln in block.text.split('\n'):
                out.append(f'> {ln}')
            out.append('')
        elif isinstance(block, ThematicBreak):
            out.append('---'); out.append('')
    return '\n'.join(out).rstrip('\n') + '\n'


class HaddockReader(Reader):
    format_name = 'haddock'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_haddock(source)


class HaddockWriter(Writer):
    format_name = 'haddock'
    def write(self, document, options=None):
        return _write_haddock(document)


register_reader(HaddockReader())
register_writer(HaddockWriter())
