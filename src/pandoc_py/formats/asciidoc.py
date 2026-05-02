"""AsciiDoc reader/writer — constrained slice.

Pandoc 3.x has no asciidoc reader, so the reader here is verified only
through self-round-trip tests in the unit suite. The writer is admitted
under the writer-only emit-success comparator (see
``trackers/NEXT_ITERATION.md``).
"""
from __future__ import annotations

import re

from pandoc_py.ast import (
    BlockQuote, BulletList, CodeBlock, Document, Heading, OrderedList,
    Paragraph, ThematicBreak,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import block_text_paragraphs, inlines_to_plain, text_to_inlines


def _read_asciidoc(source: str) -> Document:
    """AsciiDoc reader. Pandoc convention: H1 == ``= Title`` (doctitle);
    body headings start at ``== Heading`` (level 1).
    """
    text = source.replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    blocks: list = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^(=+)\s+(.*?)\s*=*\s*$', line)
        if m and m.group(1):
            count = len(m.group(1))
            level = max(1, min(count - 1 if count >= 2 else 1, 6))
            blocks.append(Heading(level=level, inlines=text_to_inlines(m.group(2))))
            i += 1; continue
        if line.strip() == '....':
            buf, j = [], i + 1
            while j < len(lines) and lines[j].strip() != '....':
                buf.append(lines[j]); j += 1
            blocks.append(CodeBlock(text='\n'.join(buf)))
            i = j + 1; continue
        m = re.match(r'^\*\s+(.*)$', line)
        if m:
            items = []
            while i < len(lines):
                im = re.match(r'^\*\s+(.*)$', lines[i])
                if not im: break
                items.append([Paragraph(inlines=text_to_inlines(im.group(1)), is_plain=True)])
                i += 1
            blocks.append(BulletList(items=items)); continue
        m = re.match(r'^\.\s+(.*)$', line)
        if m:
            items = []
            while i < len(lines):
                im = re.match(r'^\.\s+(.*)$', lines[i])
                if not im: break
                items.append([Paragraph(inlines=text_to_inlines(im.group(1)), is_plain=True)])
                i += 1
            blocks.append(OrderedList(items=items)); continue
        if not line.strip():
            i += 1; continue
        buf = [line]; j = i + 1
        while j < len(lines) and lines[j].strip() and not (
            re.match(r'^=+\s+', lines[j]) or
            re.match(r'^\*\s+', lines[j]) or
            re.match(r'^\.\s+', lines[j]) or
            lines[j].strip() == '....'
        ):
            buf.append(lines[j]); j += 1
        blocks.append(Paragraph(inlines=text_to_inlines(' '.join(s.rstrip() for s in buf))))
        i = j
    return Document(blocks=blocks, source_format='asciidoc')


def _write_asciidoc(document: Document) -> str:
    out: list[str] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            level = max(1, min(block.level, 6))
            out.append('=' * (level + 1) + ' ' + inlines_to_plain(block.inlines))
            out.append('')
        elif isinstance(block, Paragraph):
            out.append(inlines_to_plain(block.inlines)); out.append('')
        elif isinstance(block, BulletList):
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out.append(f'* {sub}')
            out.append('')
        elif isinstance(block, OrderedList):
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out.append(f'. {sub}')
            out.append('')
        elif isinstance(block, BlockQuote):
            for sub in block_text_paragraphs(block.blocks):
                out.append(f'> {sub}')
            out.append('')
        elif isinstance(block, CodeBlock):
            out.append('....')
            out.extend(block.text.split('\n'))
            out.append('....')
            out.append('')
        elif isinstance(block, ThematicBreak):
            out.append("'''")
            out.append('')
    return '\n'.join(out).rstrip('\n') + '\n'


class AsciiDocReader(Reader):
    format_name = 'asciidoc'
    aliases = ('asciidoctor', 'asciidoc_legacy')
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_asciidoc(source)


class AsciiDocWriter(Writer):
    format_name = 'asciidoc'
    aliases = ('asciidoctor', 'asciidoc_legacy')
    def write(self, document, options=None):
        return _write_asciidoc(document)


register_reader(AsciiDocReader())
register_writer(AsciiDocWriter())
