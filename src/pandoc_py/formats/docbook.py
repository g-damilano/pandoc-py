"""DocBook reader/writer — constrained slice."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from html import escape

from pandoc_py.ast import (
    BulletList, CodeBlock, Document, Heading, OrderedList, Paragraph,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import block_text_paragraphs, inlines_to_plain, text_to_inlines


def _read_docbook(source: str) -> Document:
    # very forgiving parser: walk all <para>, <title>, <programlisting>
    root = ET.fromstring(source)
    blocks = []
    depth = 0
    def walk(el, depth):
        tag = el.tag.split('}')[-1]
        if tag in {'sect1', 'sect2', 'sect3', 'sect4', 'sect5', 'section'}:
            title = el.find('title')
            if title is not None and title.text:
                level = int(tag[-1]) if tag != 'section' else min(depth + 1, 6)
                blocks.append(Heading(level=level, inlines=text_to_inlines(title.text)))
        if tag == 'title' and (el.getparent() if hasattr(el, 'getparent') else None) is None:
            pass
        if tag == 'para' and el.text:
            blocks.append(Paragraph(inlines=text_to_inlines(el.text)))
        if tag == 'programlisting' and el.text:
            blocks.append(CodeBlock(text=el.text))
        for child in el:
            walk(child, depth + 1)
    walk(root, 0)
    return Document(blocks=blocks, source_format='docbook')


def _write_docbook(document: Document) -> str:
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<article xmlns="http://docbook.org/ns/docbook" version="5.0">']
    section_open = 0
    for block in document.blocks:
        if isinstance(block, Heading):
            while section_open >= block.level:
                parts.append('</section>'); section_open -= 1
            parts.append('<section>')
            parts.append(f'<title>{escape(inlines_to_plain(block.inlines))}</title>')
            section_open = block.level
        elif isinstance(block, Paragraph):
            parts.append(f'<para>{escape(inlines_to_plain(block.inlines))}</para>')
        elif isinstance(block, (BulletList, OrderedList)):
            tag = 'itemizedlist' if isinstance(block, BulletList) else 'orderedlist'
            parts.append(f'<{tag}>')
            for item in block.items:
                parts.append('<listitem>')
                for sub in block_text_paragraphs(item): parts.append(f'<para>{escape(sub)}</para>')
                parts.append('</listitem>')
            parts.append(f'</{tag}>')
        elif isinstance(block, CodeBlock):
            parts.append(f'<programlisting>{escape(block.text)}</programlisting>')
    while section_open > 0:
        parts.append('</section>'); section_open -= 1
    parts.append('</article>')
    return '\n'.join(parts) + '\n'


class DocbookReader(Reader):
    format_name = 'docbook'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_docbook(source)

class DocbookWriter(Writer):
    format_name = 'docbook'
    aliases = ('docbook4', 'docbook5')
    def write(self, document, options=None):
        return _write_docbook(document)

register_reader(DocbookReader())
register_writer(DocbookWriter())
