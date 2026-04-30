"""reStructuredText reader/writer — constrained slice."""
from __future__ import annotations

import re
from pandoc_py.ast import (
    BlockQuote, BulletList, CodeBlock, Document, Emph, Heading,
    Link, OrderedList, Paragraph, Str, Strong, ThematicBreak,
)
from pandoc_py.io import Reader, Writer, ReadOptions, WriteOptions, register_reader, register_writer
from ._common import block_text_paragraphs, inlines_to_plain, parse_simple_blocks, text_to_inlines

_RST_HEADING_UNDERLINE = re.compile(r'^([=\-`:.\'"~^_*+#])\1+\s*$')

# RST heading-character → level (per Pandoc canonical ordering)
_RST_LEVEL_BY_CHAR = {'=': 1, '-': 2, '~': 3, '^': 4, '"': 5, "'": 6}


def _read_rst(source: str) -> Document:
    text = source.replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        # RST heading: line followed by underline of equal-or-greater length
        if i + 1 < len(lines):
            under = lines[i + 1]
            m = _RST_HEADING_UNDERLINE.match(under)
            if m and len(under.strip()) >= len(line.strip()) and line.strip():
                ch = under.strip()[0]
                level = _RST_LEVEL_BY_CHAR.get(ch, 1)
                blocks.append(Heading(level=level, inlines=text_to_inlines(line.strip())))
                i += 2
                continue
        # bullet list
        m = re.match(r'^[-*+]\s+(.*)$', line)
        if m:
            items = []
            while i < len(lines):
                im = re.match(r'^[-*+]\s+(.*)$', lines[i])
                if not im:
                    break
                items.append([Paragraph(inlines=text_to_inlines(im.group(1)), is_plain=True)])
                i += 1
            blocks.append(BulletList(items=items))
            continue
        # numbered
        m = re.match(r'^(\d+)[.)]\s+(.*)$', line)
        if m:
            items = []
            start = int(m.group(1))
            while i < len(lines):
                im = re.match(r'^(\d+)[.)]\s+(.*)$', lines[i])
                if not im:
                    break
                items.append([Paragraph(inlines=text_to_inlines(im.group(2)), is_plain=True)])
                i += 1
            blocks.append(OrderedList(start=start, items=items))
            continue
        # thematic break (RST transition)
        if re.match(r'^([-=~_*])\1{3,}\s*$', line):
            blocks.append(ThematicBreak())
            i += 1
            continue
        # literal block introduced by ::
        if line.strip().endswith('::'):
            text_part = line.rstrip()[:-2].rstrip()
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            buf = []
            while j < len(lines) and (lines[j].startswith(' ') or lines[j].startswith('\t')):
                buf.append(lines[j].lstrip())
                j += 1
            if text_part:
                blocks.append(Paragraph(inlines=text_to_inlines(text_part)))
            blocks.append(CodeBlock(text='\n'.join(buf)))
            i = j
            continue
        # paragraph
        buf = [line]
        j = i + 1
        while j < len(lines) and lines[j].strip():
            if i + 2 < len(lines) and _RST_HEADING_UNDERLINE.match(lines[j]):
                break
            buf.append(lines[j])
            j += 1
        blocks.append(Paragraph(inlines=text_to_inlines(' '.join(s.rstrip() for s in buf))))
        i = j
    return Document(blocks=blocks, source_format='rst')


def _write_rst(document: Document) -> str:
    out_lines: list[str] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            text = inlines_to_plain(block.inlines)
            level = max(1, min(block.level, 6))
            ch = '=-~^"' "'"[level - 1] if level <= 5 else "'"
            out_lines.append(text)
            out_lines.append(ch * max(3, len(text)))
            out_lines.append('')
        elif isinstance(block, Paragraph):
            out_lines.append(inlines_to_plain(block.inlines))
            out_lines.append('')
        elif isinstance(block, BulletList):
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out_lines.append(f'- {sub}')
            out_lines.append('')
        elif isinstance(block, OrderedList):
            n = block.start
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out_lines.append(f'{n}. {sub}')
                n += 1
            out_lines.append('')
        elif isinstance(block, BlockQuote):
            for sub in block_text_paragraphs(block.blocks):
                out_lines.append(f'    {sub}')
            out_lines.append('')
        elif isinstance(block, CodeBlock):
            out_lines.append('::')
            out_lines.append('')
            for ln in block.text.split('\n'):
                out_lines.append(f'    {ln}')
            out_lines.append('')
        elif isinstance(block, ThematicBreak):
            out_lines.append('-' * 32)
            out_lines.append('')
    return '\n'.join(out_lines).rstrip('\n') + '\n'


class RstReader(Reader):
    format_name = 'rst'
    aliases = ('restructuredtext',)
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_rst(source)


class RstWriter(Writer):
    format_name = 'rst'
    aliases = ('restructuredtext',)
    def write(self, document, options=None):
        return _write_rst(document)


register_reader(RstReader())
register_writer(RstWriter())
