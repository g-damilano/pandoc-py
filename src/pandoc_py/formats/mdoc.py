"""mdoc (BSD man-page) reader/writer — constrained slice (delegates to roff slice)."""
from __future__ import annotations

from pandoc_py.io import Reader, Writer, register_reader, register_writer
from .man import _read_man, _write_man


class MdocReader(Reader):
    format_name = 'mdoc'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_man(source)

class MdocWriter(Writer):
    format_name = 'mdoc'
    def write(self, document, options=None):
        return _write_man(document)

register_reader(MdocReader())
register_writer(MdocWriter())
