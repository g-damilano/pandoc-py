"""FictionBook 2 reader/writer — constrained slice."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from html import escape

from pandoc_py.ast import Document, Heading, Paragraph
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import inlines_to_plain, text_to_inlines


def _read_fb2(source: str) -> Document:
    """FB2 reader: walk body/section/title/p preserving section depth.

    pandoc emits each section's title at level=section-depth+1; e.g. a
    title in a top-level section becomes H2 (because the body itself
    counts as the implicit H1 root).
    """
    root = ET.fromstring(source)
    blocks: list = []

    def walk(el, depth):
        tag = el.tag.split('}')[-1]
        if tag == 'section':
            new_depth = depth + 1
            for child in el:
                ctag = child.tag.split('}')[-1]
                if ctag == 'title':
                    for p in child:
                        if p.tag.split('}')[-1] == 'p' and p.text:
                            blocks.append(Heading(level=min(new_depth, 6), inlines=text_to_inlines(p.text)))
                else:
                    walk(child, new_depth)
            return
        if tag == 'p' and el.text:
            blocks.append(Paragraph(inlines=text_to_inlines(el.text)))
            return
        for child in el:
            walk(child, depth)

    # Start at depth=1 because <body> itself counts as the document root,
    # so the first <section>/title inside body becomes H2.
    walk(root, 1)
    return Document(blocks=blocks, source_format='fb2')


def _write_fb2(document: Document) -> str:
    from pandoc_py.ast import BulletList, OrderedList, CodeBlock, ThematicBreak
    from ._common import block_text_paragraphs
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0">',
             '<body><section>']
    for block in document.blocks:
        if isinstance(block, Heading):
            parts.append(f'<title><p>{escape(inlines_to_plain(block.inlines))}</p></title>')
        elif isinstance(block, Paragraph):
            parts.append(f'<p>{escape(inlines_to_plain(block.inlines))}</p>')
        elif isinstance(block, BulletList):
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    parts.append(f'<p>• {escape(sub)}</p>')
        elif isinstance(block, OrderedList):
            n = block.start
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    parts.append(f'<p>{n}. {escape(sub)}</p>')
                    n += 1
        elif isinstance(block, CodeBlock):
            parts.append('<empty-line/>')
            for ln in block.text.split('\n'):
                parts.append(f'<p><code>{escape(ln)}</code></p>')
            parts.append('<empty-line/>')
        elif isinstance(block, ThematicBreak):
            parts.append('<empty-line/>')
    parts.append('</section></body></FictionBook>')
    return '\n'.join(parts) + '\n'


class Fb2Reader(Reader):
    format_name = 'fb2'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_fb2(source)

class Fb2Writer(Writer):
    format_name = 'fb2'
    def write(self, document, options=None):
        return _write_fb2(document)

register_reader(Fb2Reader())
register_writer(Fb2Writer())
