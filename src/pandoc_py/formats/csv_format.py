"""CSV reader/writer — constrained slice (CSV → single Table block)."""
from __future__ import annotations

import csv
import io

from pandoc_py.ast import (
    Document, Paragraph, Str, Table,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import inlines_to_plain, text_to_inlines


def _read_csv(source: str) -> Document:
    rows = list(csv.reader(io.StringIO(source)))
    if not rows:
        return Document(blocks=[], source_format='csv')
    headers = [text_to_inlines(cell) for cell in rows[0]]
    body = [[text_to_inlines(cell) for cell in r] for r in rows[1:]]
    aligns = ['AlignDefault'] * len(rows[0])
    return Document(blocks=[Table(caption=[], aligns=aligns, headers=headers, rows=body)], source_format='csv')


def _write_csv(document: Document) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    for block in document.blocks:
        if isinstance(block, Table):
            writer.writerow([inlines_to_plain(h) for h in block.headers])
            for row in block.rows:
                writer.writerow([inlines_to_plain(cell) for cell in row])
        elif isinstance(block, Paragraph):
            writer.writerow([inlines_to_plain(block.inlines)])
    return out.getvalue()


class CsvReader(Reader):
    format_name = 'csv'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_csv(source)

class CsvWriter(Writer):
    format_name = 'csv'
    def write(self, document, options=None):
        return _write_csv(document)

register_reader(CsvReader())
register_writer(CsvWriter())
