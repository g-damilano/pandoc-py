"""EndNote XML reader/writer — constrained slice."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from html import escape

from pandoc_py.ast import Document, Heading, Paragraph
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import inlines_to_plain, text_to_inlines


def _read_endnote(source: str) -> Document:
    """EndNote XML reader.

    Pandoc treats EndNote XML as bibliography input that becomes
    ``nocite`` document metadata plus an empty body. Mirror that shape.
    """
    from pandoc_py.ast import Cite, Citation, MetaInlines
    try:
        root = ET.fromstring(source)
        has_records = any(True for _ in root.iter('record'))
    except ET.ParseError:
        has_records = False
    if not has_records:
        return Document(blocks=[], source_format='endnotexml')
    citations = [Citation(citation_id='*', mode='NormalCitation', note_num=0)]
    cite = Cite(citations=citations, inlines=text_to_inlines('[@*]'))
    meta = {'nocite': MetaInlines(inlines=[cite])}
    return Document(blocks=[], meta=meta, source_format='endnotexml')


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
