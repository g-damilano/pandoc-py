"""Emacs Org-mode reader/writer — constrained slice."""
from __future__ import annotations

import re
from pandoc_py.ast import (
    BlockQuote, BulletList, CodeBlock, Document, Heading, OrderedList,
    Paragraph, ThematicBreak,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import block_text_paragraphs, inlines_to_plain, text_to_inlines


def _read_org(source: str) -> Document:
    text = source.replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1; continue
        m = re.match(r'^(\*+)\s+(.*)$', line)
        if m:
            blocks.append(Heading(level=len(m.group(1)), inlines=text_to_inlines(m.group(2))))
            i += 1; continue
        if line.lstrip().lower().startswith('#+begin_src'):
            info = line.split(None, 1)
            lang = info[1] if len(info) > 1 else ''
            buf, j = [], i + 1
            while j < len(lines) and not lines[j].lstrip().lower().startswith('#+end_src'):
                buf.append(lines[j]); j += 1
            blocks.append(CodeBlock(text='\n'.join(buf), info=lang))
            i = j + 1; continue
        m = re.match(r'^[-+]\s+(.*)$', line)
        if m:
            items = []
            while i < len(lines):
                im = re.match(r'^[-+]\s+(.*)$', lines[i])
                if not im: break
                items.append([Paragraph(inlines=text_to_inlines(im.group(1)), is_plain=True)])
                i += 1
            blocks.append(BulletList(items=items)); continue
        m = re.match(r'^(\d+)[.)]\s+(.*)$', line)
        if m:
            items, start = [], int(m.group(1))
            while i < len(lines):
                im = re.match(r'^(\d+)[.)]\s+(.*)$', lines[i])
                if not im: break
                items.append([Paragraph(inlines=text_to_inlines(im.group(2)), is_plain=True)])
                i += 1
            blocks.append(OrderedList(start=start, items=items)); continue
        if re.match(r'^-{5,}\s*$', line):
            blocks.append(ThematicBreak()); i += 1; continue
        buf = [line]; j = i + 1
        while j < len(lines) and lines[j].strip() and not re.match(r'^(\*+)\s+', lines[j]) and not lines[j].lstrip().lower().startswith('#+begin_src'):
            buf.append(lines[j]); j += 1
        blocks.append(Paragraph(inlines=text_to_inlines(' '.join(s.rstrip() for s in buf))))
        i = j
    return Document(blocks=blocks, source_format='org')


def _write_org(document: Document) -> str:
    out: list[str] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            out.append('*' * max(1, block.level) + ' ' + inlines_to_plain(block.inlines)); out.append('')
        elif isinstance(block, Paragraph):
            out.append(inlines_to_plain(block.inlines)); out.append('')
        elif isinstance(block, BulletList):
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out.append(f'- {sub}')
            out.append('')
        elif isinstance(block, OrderedList):
            n = block.start
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out.append(f'{n}. {sub}')
                n += 1
            out.append('')
        elif isinstance(block, BlockQuote):
            out.append('#+begin_quote')
            for sub in block_text_paragraphs(block.blocks): out.append(sub)
            out.append('#+end_quote'); out.append('')
        elif isinstance(block, CodeBlock):
            out.append(f'#+begin_src {block.info}'.rstrip())
            for ln in block.text.split('\n'): out.append(ln)
            out.append('#+end_src'); out.append('')
        elif isinstance(block, ThematicBreak):
            out.append('-' * 32); out.append('')
    return '\n'.join(out).rstrip('\n') + '\n'


class OrgReader(Reader):
    format_name = 'org'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_org(source)

class OrgWriter(Writer):
    format_name = 'org'
    def write(self, document, options=None):
        return _write_org(document)

register_reader(OrgReader())
register_writer(OrgWriter())
