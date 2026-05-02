"""JATS reader/writer — constrained slice."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from html import escape

from pandoc_py.ast import (
    Attr, BulletList, CodeBlock, Document, Heading, OrderedList, Paragraph,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import block_text_paragraphs, inlines_to_plain, text_to_inlines


def _ltag(el):
    return el.tag.split('}')[-1] if isinstance(el.tag, str) else ''


def _read_jats(source: str) -> Document:
    """JATS reader: walk <sec>/<title>/<p>/<list>/<code>."""
    root = ET.fromstring(source)
    blocks: list = []

    def walk(el, depth):
        tag = _ltag(el)
        if tag == 'sec':
            title = None
            for child in el:
                if _ltag(child) == 'title':
                    title = child; break
            if title is not None and title.text:
                anchor = el.attrib.get('id', '')
                attr = Attr(identifier=anchor) if anchor else Attr()
                blocks.append(Heading(level=min(depth + 1, 6), inlines=text_to_inlines(title.text), attr=attr))
            for child in el:
                if _ltag(child) != 'title':
                    walk(child, depth + 1)
        elif tag == 'p':
            text = ''.join(el.itertext()).strip()
            if text:
                blocks.append(Paragraph(inlines=text_to_inlines(text)))
        elif tag == 'list':
            list_type = el.attrib.get('list-type', 'bullet')
            items = []
            for li in el:
                if _ltag(li) == 'list-item':
                    text = ''.join(li.itertext()).strip()
                    items.append([Paragraph(inlines=text_to_inlines(text), is_plain=True)])
            blocks.append(BulletList(items=items) if list_type == 'bullet' else OrderedList(items=items))
        elif tag in {'preformat', 'code'} and el.text:
            blocks.append(CodeBlock(text=el.text))
        else:
            for child in el:
                walk(child, depth + 1)

    # Start at depth=-2 so the first <sec> inside <article><body> produces
    # an H1 (matches pandoc's JATS reader convention).
    walk(root, -2)
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
