"""OPML reader/writer — constrained slice."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from html import escape

from pandoc_py.ast import (
    BulletList, CodeBlock, Document, Heading, OrderedList, Paragraph, ThematicBreak,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from pandoc_py.writers.markdown import write_markdown
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


def _attr_escape(text: str) -> str:
    return (text.replace('&', '&amp;')
                .replace('"', '&quot;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('\n', '&#10;'))


def _write_opml(document: Document) -> str:
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<opml version="2.0">',
             '<head><title></title></head>',
             '<body>']
    blocks = list(document.blocks)
    i = 0
    while i < len(blocks):
        block = blocks[i]
        if isinstance(block, Heading):
            text = inlines_to_plain(block.inlines)
            j = i + 1
            body_blocks = []
            while j < len(blocks) and not isinstance(blocks[j], Heading):
                body_blocks.append(blocks[j])
                j += 1
            note_md = write_markdown(Document(blocks=body_blocks)) if body_blocks else ''
            note_md = note_md.rstrip('\n')
            attrs = f'text="{_attr_escape(text)}"'
            if note_md:
                attrs += f' _note="{_attr_escape(note_md)}"'
            parts.append(f'<outline {attrs}>')
            parts.append('</outline>')
            i = j
        else:
            i += 1
    parts.append('</body>')
    parts.append('</opml>')
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
