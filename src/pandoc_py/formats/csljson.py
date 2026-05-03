"""CSL JSON reader/writer — constrained slice."""
from __future__ import annotations

import json

from pandoc_py.ast import Document, Heading, Paragraph
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import inlines_to_plain, text_to_inlines


def _read_csljson(source: str) -> Document:
    """CSL-JSON reader.

    Pandoc treats CSL-JSON as bibliography input that becomes ``nocite``
    document metadata (Cite citationId="*") plus an empty body. Mirror
    that shape.
    """
    from pandoc_py.ast import Cite, Citation, MetaInlines
    try:
        entries = json.loads(source) if source.strip() else []
    except json.JSONDecodeError:
        entries = []
    if isinstance(entries, dict): entries = [entries]
    if not entries:
        return Document(blocks=[], source_format='csljson')
    citations = [Citation(citation_id='*', mode='NormalCitation', note_num=0)]
    cite = Cite(citations=citations, inlines=text_to_inlines('[@*]'))
    meta = {'nocite': MetaInlines(inlines=[cite])}
    return Document(blocks=[], meta=meta, source_format='csljson')


def _write_csljson(document: Document) -> str:
    entries = []
    cur: dict | None = None
    for block in document.blocks:
        if isinstance(block, Heading):
            if cur is not None: entries.append(cur)
            text = inlines_to_plain(block.inlines).strip()
            etype = 'misc'; eid = text
            if text.startswith('@'):
                rest = text[1:]
                if '{' in rest:
                    etype = rest.split('{', 1)[0]
                    eid = rest.split('{', 1)[1].rstrip('}')
            cur = {'id': eid, 'type': etype}
        elif isinstance(block, Paragraph) and cur is not None:
            text = inlines_to_plain(block.inlines).strip()
            if ':' in text:
                k, v = text.split(':', 1)
                cur[k.strip()] = v.strip()
    if cur is not None: entries.append(cur)
    return json.dumps(entries, indent=2, ensure_ascii=False) + '\n'


class CslJsonReader(Reader):
    format_name = 'csljson'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_csljson(source)

class CslJsonWriter(Writer):
    format_name = 'csljson'
    def write(self, document, options=None):
        return _write_csljson(document)

register_reader(CslJsonReader())
register_writer(CslJsonWriter())
