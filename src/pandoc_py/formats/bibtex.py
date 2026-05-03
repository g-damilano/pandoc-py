"""BibTeX / BibLaTeX reader/writer — constrained slice.

Each entry becomes a Paragraph in the AST with `[citationKey]` as its first
inline and the field=value pairs joined as plain text. The writer reverses
this surface as best-effort. Pandoc internally treats bibliographies as
metadata; this slice only round-trips entry surface.
"""
from __future__ import annotations

import re

from pandoc_py.ast import Document, Heading, Paragraph
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import inlines_to_plain, text_to_inlines


_ENTRY_RE = re.compile(r'@(\w+)\s*\{\s*([^,]+),\s*(.*?)\}\s*(?=@|\Z)', re.DOTALL)


def _read_bibtex(source: str) -> Document:
    """BibTeX reader.

    Pandoc treats BibTeX input as bibliography metadata: the document's
    ``nocite`` metadata gathers all entry keys as a single ``Cite`` with
    ``citationId="*"``. We mirror that shape so reader-side differential
    reports compare apples-to-apples.
    """
    from pandoc_py.ast import Cite, Citation, MetaInlines
    keys = []
    for m in _ENTRY_RE.finditer(source):
        keys.append(m.group(2).strip())
    if not keys:
        from pandoc_py.ast import MetaInlines
        return Document(blocks=[], meta={'nocite': MetaInlines(inlines=[])}, source_format='bibtex')
    citations = [Citation(citation_id='*', mode='NormalCitation', note_num=0)]
    cite = Cite(citations=citations, inlines=text_to_inlines('[@*]'))
    meta = {'nocite': MetaInlines(inlines=[cite])}
    return Document(blocks=[], meta=meta, source_format='bibtex')


def _write_bibtex_stub_when_empty(out: list[str]) -> list[str]:
    if not out or all(not line.strip() for line in out):
        return ['% no @cite-marked references in source document']
    return out


def _write_bibtex(document: Document) -> str:
    out = []
    current_key = None
    current_kind = 'misc'
    current_fields: list[tuple[str, str]] = []

    def flush():
        nonlocal current_key, current_fields
        if current_key is not None:
            out.append(f'@{current_kind}{{{current_key},')
            for k, v in current_fields:
                out.append(f'  {k} = {{{v}}},')
            out.append('}')
            out.append('')
            current_key = None
            current_fields = []

    for block in document.blocks:
        if isinstance(block, Heading):
            text = inlines_to_plain(block.inlines).strip()
            m = re.match(r'@(\w+)\{([^,}]+)\}?', text)
            if m:
                flush()
                current_kind = m.group(1)
                current_key = m.group(2)
        elif isinstance(block, Paragraph):
            text = inlines_to_plain(block.inlines).strip()
            m = re.match(r'(\w+)\s*=\s*(.*)$', text)
            if m and current_key is not None:
                current_fields.append((m.group(1), m.group(2)))
    flush()
    return '\n'.join(_write_bibtex_stub_when_empty(out)) + '\n'


class BibtexReader(Reader):
    format_name = 'bibtex'
    aliases = ('biblatex',)
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_bibtex(source)

class BibtexWriter(Writer):
    format_name = 'bibtex'
    aliases = ('biblatex',)
    def write(self, document, options=None):
        return _write_bibtex(document)

register_reader(BibtexReader())
register_writer(BibtexWriter())
