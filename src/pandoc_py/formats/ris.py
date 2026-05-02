"""RIS reader/writer — constrained slice."""
from __future__ import annotations

import re

from pandoc_py.ast import Document, Heading, Paragraph
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import inlines_to_plain, text_to_inlines


def _read_ris(source: str) -> Document:
    """RIS reader.

    Pandoc treats RIS input as bibliography metadata: entries collapse
    into a single ``nocite`` ``MetaInlines`` containing a Cite with
    ``citationId="*"``. Mirror that shape so reader-side differential
    reports compare apples-to-apples.
    """
    from pandoc_py.ast import Cite, Citation, MetaInlines
    has_entry = bool(re.search(r'^TY\s+-', source, re.MULTILINE))
    if not has_entry:
        return Document(blocks=[], source_format='ris')
    citations = [Citation(citation_id='*', mode='NormalCitation', note_num=0)]
    cite = Cite(citations=citations, inlines=text_to_inlines('[@*]'))
    meta = {'nocite': MetaInlines(inlines=[cite])}
    return Document(blocks=[], meta=meta, source_format='ris')


def _write_ris(document: Document) -> str:
    out: list[str] = []
    started = False
    for block in document.blocks:
        # Only blocks with `inlines` (Heading, Paragraph) carry text we can
        # reflect into RIS tag/value pairs. Skip lists, code blocks, etc.
        inlines = getattr(block, 'inlines', None)
        if inlines is None:
            continue
        text = inlines_to_plain(inlines).strip()
        m = re.match(r'^([A-Z][A-Z0-9]):\s*(.*)$', text)
        if not m: continue
        tag, val = m.group(1), m.group(2)
        if tag == 'TY':
            if started: out.append('ER  - ')
            out.append(f'TY  - {val}')
            started = True
        else:
            out.append(f'{tag}  - {val}')
    if started: out.append('ER  - ')
    return '\n'.join(out) + '\n'


class RisReader(Reader):
    format_name = 'ris'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_ris(source)

class RisWriter(Writer):
    format_name = 'ris'
    def write(self, document, options=None):
        return _write_ris(document)

register_reader(RisReader())
register_writer(RisWriter())
