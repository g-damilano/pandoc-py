"""JATS reader/writer — constrained slice (delegates structurally to DocBook)."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from html import escape

from pandoc_py.ast import (
    BulletList, CodeBlock, Document, Heading, OrderedList, Paragraph,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import block_text_paragraphs, inlines_to_plain, text_to_inlines


def _read_jats(source: str) -> Document:
    root = ET.fromstring(source)
    blocks = []
    for el in root.iter():
        tag = el.tag.split('}')[-1]
        if tag == 'title' and el.text:
            blocks.append(Heading(level=1, inlines=text_to_inlines(el.text)))
        elif tag == 'p' and el.text:
            blocks.append(Paragraph(inlines=text_to_inlines(el.text)))
    return Document(blocks=blocks, source_format='jats')


def _write_jats(document: Document) -> str:
    parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<article>', '<body>']
    for block in document.blocks:
        if isinstance(block, Heading):
            parts.append('<sec>')
            parts.append(f'<title>{escape(inlines_to_plain(block.inlines))}</title>')
            parts.append('</sec>')
        elif isinstance(block, Paragraph):
            parts.append(f'<p>{escape(inlines_to_plain(block.inlines))}</p>')
        elif isinstance(block, (BulletList, OrderedList)):
            list_type = 'bullet' if isinstance(block, BulletList) else 'order'
            parts.append(f'<list list-type="{list_type}">')
            for item in block.items:
                parts.append('<list-item>')
                for sub in block_text_paragraphs(item): parts.append(f'<p>{escape(sub)}</p>')
                parts.append('</list-item>')
            parts.append('</list>')
        elif isinstance(block, CodeBlock):
            parts.append(f'<preformat>{escape(block.text)}</preformat>')
    parts.append('</body></article>')
    return '\n'.join(parts) + '\n'


class JatsReader(Reader):
    format_name = 'jats'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_jats(source)

class JatsWriter(Writer):
    format_name = 'jats'
    aliases = ('jats_archiving', 'jats_articleauthoring', 'jats_publishing')
    def write(self, document, options=None):
        return _write_jats(document)

register_reader(JatsReader())
register_writer(JatsWriter())
