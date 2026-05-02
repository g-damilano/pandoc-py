"""RTF reader/writer — constrained slice (text-level RTF only)."""
from __future__ import annotations

import re

from pandoc_py.ast import (
    BulletList, CodeBlock, Document, Heading, OrderedList, Paragraph,
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
    """Pandoc-aligned RTF surface.

    Each block is wrapped in ``{\\pard ... \\par}`` with the same control
    words pandoc emits, so pandoc's RTF reader recognises the structure
    rather than treating boldface as Strong inside Para.
    """
    out = [r'{\rtf1\ansi\deff0']
    for block in document.blocks:
        if isinstance(block, Heading):
            level = max(1, min(block.level, 6)) - 1
            text = _rtf_escape(inlines_to_plain(block.inlines))
            out.append(r'{\pard \ql \f0 \sa180 \li0 \fi0 '
                       f'\\outlinelevel{level} \\b \\fs36 {text}\\par}}')
        elif isinstance(block, Paragraph):
            text = _rtf_escape(inlines_to_plain(block.inlines))
            out.append(r'{\pard \ql \f0 \sa180 \li0 \fi0 ' + text + r'\par}')
        elif isinstance(block, BulletList):
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out.append(r'{\pard \ql \f0 \sa0 \li360 \fi-360 \bullet \tx360\tab '
                               + _rtf_escape(sub) + r'\par}')
        elif isinstance(block, OrderedList):
            n = block.start
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out.append(r'{\pard \ql \f0 \sa0 \li360 \fi-360 '
                               + str(n) + r'.\tx360\tab '
                               + _rtf_escape(sub) + r'\par}')
                    n += 1
        elif isinstance(block, CodeBlock):
            for ln in block.text.split('\n'):
                out.append(r'{\pard \ql \f0 \sa0 \f1 ' + _rtf_escape(ln) + r'\par}')
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
