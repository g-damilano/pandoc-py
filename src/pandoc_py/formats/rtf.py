"""RTF reader/writer — constrained slice (text-level RTF only)."""
from __future__ import annotations

import re

from pandoc_py.ast import (
    BulletList, Document, Heading, OrderedList, Paragraph,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import block_text_paragraphs, inlines_to_plain, text_to_inlines


_RTF_CONTROL = re.compile(r'\\[a-zA-Z]+-?\d* ?')


def _strip_rtf(s: str) -> str:
    s = re.sub(r'\\\\', '\\\\', s)
    s = _RTF_CONTROL.sub(' ', s)
    s = s.replace('{', '').replace('}', '')
    return re.sub(r'\s+', ' ', s).strip()


def _read_rtf(source: str) -> Document:
    blocks: list = []
    body = source
    if r'\par' in body:
        for chunk in body.split(r'\par'):
            text = _strip_rtf(chunk)
            if text:
                blocks.append(Paragraph(inlines=text_to_inlines(text)))
    else:
        text = _strip_rtf(body)
        if text:
            blocks.append(Paragraph(inlines=text_to_inlines(text)))
    return Document(blocks=blocks, source_format='rtf')


def _rtf_escape(text: str) -> str:
    return text.replace('\\', r'\\').replace('{', r'\{').replace('}', r'\}')


def _write_rtf(document: Document) -> str:
    out = [r'{\rtf1\ansi\deff0']
    for block in document.blocks:
        if isinstance(block, Heading):
            out.append(r'\b ' + _rtf_escape(inlines_to_plain(block.inlines)) + r'\b0\par')
        elif isinstance(block, Paragraph):
            out.append(_rtf_escape(inlines_to_plain(block.inlines)) + r'\par')
        elif isinstance(block, (BulletList, OrderedList)):
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out.append(r'\bullet ' + _rtf_escape(sub) + r'\par')
    out.append('}')
    return '\n'.join(out) + '\n'


class RtfReader(Reader):
    format_name = 'rtf'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8', errors='replace')
        return _read_rtf(source)

class RtfWriter(Writer):
    format_name = 'rtf'
    def write(self, document, options=None):
        return _write_rtf(document)

register_reader(RtfReader())
register_writer(RtfWriter())
