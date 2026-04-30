"""Generic XML pseudo-format — round-trips paragraphs/headings as a flat XML body."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from html import escape

from pandoc_py.ast import Document, Heading, Paragraph
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import inlines_to_plain, text_to_inlines


def _read_xml(source: str) -> Document:
    root = ET.fromstring(source)
    blocks = []
    for el in root.iter():
        tag = el.tag.split('}')[-1]
        text = (el.text or '').strip()
        if not text:
            continue
        if tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
            blocks.append(Heading(level=int(tag[1]), inlines=text_to_inlines(text)))
        elif tag in {'p', 'para'}:
            blocks.append(Paragraph(inlines=text_to_inlines(text)))
    return Document(blocks=blocks, source_format='xml')


def _write_xml(document: Document) -> str:
    parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<document>']
    for block in document.blocks:
        if isinstance(block, Heading):
            tag = f'h{max(1, min(block.level, 6))}'
            parts.append(f'<{tag}>{escape(inlines_to_plain(block.inlines))}</{tag}>')
        elif isinstance(block, Paragraph):
            parts.append(f'<p>{escape(inlines_to_plain(block.inlines))}</p>')
    parts.append('</document>')
    return '\n'.join(parts) + '\n'


class XmlReader(Reader):
    format_name = 'xml'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_xml(source)

class XmlWriter(Writer):
    format_name = 'xml'
    def write(self, document, options=None):
        return _write_xml(document)

register_reader(XmlReader())
register_writer(XmlWriter())
