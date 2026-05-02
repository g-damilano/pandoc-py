"""EndNote XML reader/writer — constrained slice."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from html import escape

from pandoc_py.ast import Document, Heading, Paragraph
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import inlines_to_plain, text_to_inlines


def _read_endnote(source: str) -> Document:
    root = ET.fromstring(source)
    blocks = []
    for record in root.iter('record'):
        ref_type = record.find('ref-type')
        if ref_type is not None and ref_type.text:
            blocks.append(Heading(level=1, inlines=text_to_inlines(f'ref-type: {ref_type.text}')))
        titles = record.find('titles')
        if titles is not None:
            for title in titles.iter('title'):
                if title.text:
                    blocks.append(Paragraph(inlines=text_to_inlines(f'title: {title.text}')))
        for tag in ('contributors', 'dates', 'periodical'):
            element = record.find(tag)
            if element is not None:
                for sub in element.iter():
                    if sub.text and sub.text.strip():
                        blocks.append(Paragraph(inlines=text_to_inlines(f'{sub.tag}: {sub.text.strip()}')))
    return Document(blocks=blocks, source_format='endnotexml')


def _write_endnote(document: Document) -> str:
    parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<xml><records>']
    record_open = False
    for block in document.blocks:
        inlines = getattr(block, 'inlines', None)
        if inlines is None:
            continue
        text = inlines_to_plain(inlines).strip()
        if isinstance(block, Heading) and text.startswith('ref-type:'):
            if record_open: parts.append('</record>')
            parts.append('<record>')
            parts.append(f'<ref-type>{escape(text.split(":", 1)[1].strip())}</ref-type>')
            record_open = True
        elif isinstance(block, Paragraph) and ':' in text and record_open:
            tag, val = text.split(':', 1)
            tag = tag.strip(); val = val.strip()
            parts.append(f'<{tag}>{escape(val)}</{tag}>')
    if record_open: parts.append('</record>')
    parts.append('</records></xml>')
    return '\n'.join(parts) + '\n'


class EndnoteReader(Reader):
    format_name = 'endnotexml'
    aliases = ('endnote',)
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_endnote(source)

class EndnoteWriter(Writer):
    format_name = 'endnotexml'
    aliases = ('endnote',)
    def write(self, document, options=None):
        return _write_endnote(document)

register_reader(EndnoteReader())
register_writer(EndnoteWriter())
