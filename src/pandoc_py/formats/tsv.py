"""TSV (tab-separated values) reader/writer — constrained slice.

Mirrors the CSV reader/writer but uses TAB as the field separator.
"""
from __future__ import annotations

import csv
import io

from pandoc_py.ast import Document, Paragraph, Table
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import inlines_to_plain, text_to_inlines


def _read_tsv(source: str) -> Document:
    rows = list(csv.reader(io.StringIO(source), delimiter='\t'))
    if not rows:
        return Document(blocks=[], source_format='tsv')
    headers = [text_to_inlines(cell) for cell in rows[0]]
    body = [[text_to_inlines(cell) for cell in r] for r in rows[1:]]
    aligns = ['AlignDefault'] * len(rows[0])
    return Document(
        blocks=[Table(caption=[], aligns=aligns, headers=headers, rows=body)],
        source_format='tsv',
    )


def _write_tsv(document: Document) -> str:
    out = io.StringIO()
    writer = csv.writer(out, delimiter='\t', lineterminator='\n')
    for block in document.blocks:
        if isinstance(block, Table):
            writer.writerow([inlines_to_plain(h) for h in block.headers])
            for row in block.rows:
                writer.writerow([inlines_to_plain(cell) for cell in row])
        elif isinstance(block, Paragraph):
            writer.writerow([inlines_to_plain(block.inlines)])
    return out.getvalue()


class TsvReader(Reader):
    format_name = 'tsv'

    def read(self, source, options=None):
        if isinstance(source, bytes):
            source = source.decode('utf-8')
        return _read_tsv(source)


class TsvWriter(Writer):
    format_name = 'tsv'

    def write(self, document, options=None):
        return _write_tsv(document)


register_reader(TsvReader())
register_writer(TsvWriter())
