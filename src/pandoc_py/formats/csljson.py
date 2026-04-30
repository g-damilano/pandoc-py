"""CSL JSON reader/writer — constrained slice."""
from __future__ import annotations

import json

from pandoc_py.ast import Document, Heading, Paragraph
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import inlines_to_plain, text_to_inlines


def _read_csljson(source: str) -> Document:
    entries = json.loads(source)
    if isinstance(entries, dict): entries = [entries]
    blocks = []
    for entry in entries:
        eid = entry.get('id', '?')
        etype = entry.get('type', 'misc')
        blocks.append(Heading(level=1, inlines=text_to_inlines(f'@{etype}{{{eid}}}')))
        for k, v in entry.items():
            if k in {'id', 'type'}: continue
            blocks.append(Paragraph(inlines=text_to_inlines(f'{k}: {v}')))
    return Document(blocks=blocks, source_format='csljson')


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
