"""OPML reader/writer — constrained slice."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from html import escape

from pandoc_py.ast import Document, Heading, Paragraph
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import inlines_to_plain, text_to_inlines


def _read_opml(source: str) -> Document:
    root = ET.fromstring(source)
    blocks = []

    def walk(node, depth):
        for outline in node.findall('outline'):
            text = outline.attrib.get('text', '') or outline.attrib.get('title', '')
            blocks.append(Heading(level=min(depth, 6), inlines=text_to_inlines(text)))
            note = outline.attrib.get('_note')
            if note:
                blocks.append(Paragraph(inlines=text_to_inlines(note)))
            walk(outline, depth + 1)

    body = root.find('body')
    if body is not None:
        walk(body, 1)
    return Document(blocks=blocks, source_format='opml')


def _write_opml(document: Document) -> str:
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<opml version="2.0">',
             '<head><title>pandoc_py</title></head>',
             '<body>']
    depth = 0
    last_level = 0
    for block in document.blocks:
        if isinstance(block, Heading):
            while last_level >= block.level and depth > 0:
                parts.append('</outline>')
                depth -= 1; last_level -= 1
            parts.append(f'<outline text="{escape(inlines_to_plain(block.inlines), quote=True)}">')
            depth += 1; last_level = block.level
        elif isinstance(block, Paragraph):
            parts.append(f'<outline text="{escape(inlines_to_plain(block.inlines), quote=True)}"/>')
    while depth > 0:
        parts.append('</outline>'); depth -= 1
    parts.append('</body></opml>')
    return '\n'.join(parts) + '\n'


class OpmlReader(Reader):
    format_name = 'opml'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_opml(source)

class OpmlWriter(Writer):
    format_name = 'opml'
    def write(self, document, options=None):
        return _write_opml(document)

register_reader(OpmlReader())
register_writer(OpmlWriter())
