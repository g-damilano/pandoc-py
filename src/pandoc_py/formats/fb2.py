"""FictionBook 2 reader/writer — constrained slice."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from html import escape

from pandoc_py.ast import Document, Heading, Paragraph
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import inlines_to_plain, text_to_inlines


def _read_fb2(source: str) -> Document:
    root = ET.fromstring(source)
    blocks = []
    for el in root.iter():
        tag = el.tag.split('}')[-1]
        if tag == 'title':
            for p in el.iter():
                if p.tag.split('}')[-1] == 'p' and p.text:
                    blocks.append(Heading(level=1, inlines=text_to_inlines(p.text)))
        elif tag == 'p' and el.text:
            blocks.append(Paragraph(inlines=text_to_inlines(el.text)))
    return Document(blocks=blocks, source_format='fb2')


def _write_fb2(document: Document) -> str:
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0">',
             '<body><section>']
    for block in document.blocks:
        if isinstance(block, Heading):
            parts.append(f'<title><p>{escape(inlines_to_plain(block.inlines))}</p></title>')
        elif isinstance(block, Paragraph):
            parts.append(f'<p>{escape(inlines_to_plain(block.inlines))}</p>')
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
