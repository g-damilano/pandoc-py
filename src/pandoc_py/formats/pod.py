"""Perl POD reader/writer — constrained slice."""
from __future__ import annotations

import re
from pandoc_py.ast import (
    BulletList, CodeBlock, Document, Heading, OrderedList, Paragraph,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import block_text_paragraphs, inlines_to_plain, text_to_inlines


def _read_pod(source: str) -> Document:
    text = source.replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^=head([1-6])\s+(.*)$', line)
        if m:
            blocks.append(Heading(level=int(m.group(1)), inlines=text_to_inlines(m.group(2))))
            i += 1; continue
        if line.startswith('=over'):
            items, j = [], i + 1
            while j < len(lines) and not lines[j].startswith('=back'):
                im = re.match(r'^=item\s+\*?\s*(.*)$', lines[j])
                if im:
                    items.append([Paragraph(inlines=text_to_inlines(im.group(1)), is_plain=True)])
                j += 1
            blocks.append(BulletList(items=items))
            i = j + 1; continue
        if line.startswith('=cut') or line.startswith('=pod'):
            i += 1; continue
        if line.startswith(' ') or line.startswith('\t'):
            buf, j = [line.lstrip()], i + 1
            while j < len(lines) and (lines[j].startswith(' ') or lines[j].startswith('\t')):
                buf.append(lines[j].lstrip()); j += 1
            blocks.append(CodeBlock(text='\n'.join(buf)))
            i = j; continue
        if not line.strip():
            i += 1; continue
        buf, j = [line], i + 1
        while j < len(lines) and lines[j].strip() and not lines[j].startswith('='):
            buf.append(lines[j]); j += 1
        blocks.append(Paragraph(inlines=text_to_inlines(' '.join(s.rstrip() for s in buf))))
        i = j
    return Document(blocks=blocks, source_format='pod')


def _write_pod(document: Document) -> str:
    out: list[str] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            out.append(f'=head{max(1, min(block.level, 6))} {inlines_to_plain(block.inlines)}'); out.append('')
        elif isinstance(block, Paragraph):
            out.append(inlines_to_plain(block.inlines)); out.append('')
        elif isinstance(block, (BulletList, OrderedList)):
            out.append('=over')
            out.append('')
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out.append(f'=item *')
                    out.append('')
                    out.append(sub)
                    out.append('')
            out.append('=back')
            out.append('')
        elif isinstance(block, CodeBlock):
            for ln in block.text.split('\n'): out.append(' ' + ln)
            out.append('')
    out.append('=cut')
    return '\n'.join(out) + '\n'


class PodReader(Reader):
    format_name = 'pod'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_pod(source)

class PodWriter(Writer):
    format_name = 'pod'
    def write(self, document, options=None):
        return _write_pod(document)

register_reader(PodReader())
register_writer(PodWriter())
