"""MediaWiki reader/writer — constrained slice."""
from __future__ import annotations

import re

from pandoc_py.ast import (
    Attr, BlockQuote, BulletList, CodeBlock, Document, Heading, OrderedList,
    Paragraph, RawInline, Str, ThematicBreak,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import block_text_paragraphs, inlines_to_plain, slugify_heading, text_to_inlines


def _read_mediawiki(source: str) -> Document:
    """MediaWiki reader admitting `<span id="anchor"></span>` heading anchors,
    `=`-delimited headings, `*`/`#` lists, `<pre>` code, and paragraphs.

    Pandoc emits a leading ``<span id="anchor"></span>`` line above every
    heading; the reader pairs that span with the next heading and stores
    its identifier on the heading's attr.
    """
    text = source.replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^(<span\s+id="[^"]+"></span>)\s*$', line.strip())
        if m:
            # Pandoc's mediawiki reader emits this as a Paragraph containing
            # two RawInlines (the open and close span tags) — match that.
            opener = re.match(r'^(<span\s+id="[^"]+">)(</span>)\s*$', line.strip())
            blocks.append(Paragraph(inlines=[
                RawInline(format='html', text=opener.group(1)),
                RawInline(format='html', text=opener.group(2)),
            ]))
            i += 1
            continue
        m = re.match(r'^(=+)\s*(.*?)\s*\1\s*$', line)
        if m:
            level = max(1, min(len(m.group(1)), 6))
            blocks.append(Heading(level=level, inlines=text_to_inlines(m.group(2)), attr=Attr()))
            i += 1
            continue
        if line.startswith('<pre>'):
            buf, j = [], i
            content = line[len('<pre>'):]
            if content.endswith('</pre>'):
                blocks.append(CodeBlock(text=content[:-len('</pre>')]))
                i += 1
                continue
            buf.append(content)
            j = i + 1
            while j < len(lines) and not lines[j].endswith('</pre>'):
                buf.append(lines[j])
                j += 1
            if j < len(lines):
                tail = lines[j][:-len('</pre>')]
                if tail:
                    buf.append(tail)
            blocks.append(CodeBlock(text='\n'.join(buf)))
            i = j + 1
            continue
        m = re.match(r'^\*\s+(.*)$', line)
        if m:
            items = []
            while i < len(lines):
                im = re.match(r'^\*\s+(.*)$', lines[i])
                if not im: break
                items.append([Paragraph(inlines=text_to_inlines(im.group(1)), is_plain=True)])
                i += 1
            blocks.append(BulletList(items=items))
            continue
        m = re.match(r'^#\s+(.*)$', line)
        if m:
            items = []
            while i < len(lines):
                im = re.match(r'^#\s+(.*)$', lines[i])
                if not im: break
                items.append([Paragraph(inlines=text_to_inlines(im.group(1)), is_plain=True)])
                i += 1
            blocks.append(OrderedList(items=items))
            continue
        if re.match(r'^----+\s*$', line):
            blocks.append(ThematicBreak())
            i += 1
            continue
        if not line.strip():
            i += 1
            continue
        # paragraph (collected until a blank line or block starter)
        buf = [line]; j = i + 1
        while j < len(lines) and lines[j].strip() and not (
            re.match(r'^=+\s', lines[j]) or
            re.match(r'^\*\s+', lines[j]) or
            re.match(r'^#\s+', lines[j]) or
            lines[j].startswith('<pre>') or
            re.match(r'^----+', lines[j]) or
            re.match(r'^<span\s+id="', lines[j])
        ):
            buf.append(lines[j]); j += 1
        blocks.append(Paragraph(inlines=text_to_inlines(' '.join(s.rstrip() for s in buf))))
        i = j
    return Document(blocks=blocks, source_format='mediawiki')


def _write_mediawiki(document: Document) -> str:
    out: list[str] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            text = inlines_to_plain(block.inlines)
            anchor = block.attr.identifier or slugify_heading(text)
            level = max(1, min(block.level, 6))
            out.append(f'<span id="{anchor}"></span>')
            out.append(f'{"=" * level} {text} {"=" * level}')
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
        elif isinstance(block, BlockQuote):
            for sub in block_text_paragraphs(block.blocks): out.append(f'> {sub}')
            out.append('')
        elif isinstance(block, CodeBlock):
            out.append(f'<pre>{block.text}</pre>'); out.append('')
        elif isinstance(block, ThematicBreak):
            out.append('----'); out.append('')
    return '\n'.join(out).rstrip('\n') + '\n'


class MediawikiReader(Reader):
    format_name = 'mediawiki'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_mediawiki(source)


class MediawikiWriter(Writer):
    format_name = 'mediawiki'
    def write(self, document, options=None):
        return _write_mediawiki(document)


register_reader(MediawikiReader())
register_writer(MediawikiWriter())
