"""Vim help (vimdoc) writer — constrained slice.

Vim help files use a fixed-width plain-text layout with a few syntactic
markers:

* H1 sections are surrounded by horizontal rules of ``=`` characters.
* H2 sections use ``-`` characters.
* Bullet items are ``* item``.
* Code is enclosed in ``>`` / ``<`` markers and indented.

This is a writer-only format (Pandoc has no vimdoc reader).
"""
from __future__ import annotations

from pandoc_py.ast import (
    BlockQuote, BulletList, CodeBlock, Document, Heading, OrderedList,
    Paragraph, ThematicBreak,
)
from pandoc_py.io import Writer, register_writer
from ._common import block_text_paragraphs, inlines_to_plain


_RULE_WIDTH = 78


def _write_vimdoc(document: Document) -> str:
    out: list[str] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            text = inlines_to_plain(block.inlines)
            if block.level == 1:
                out.append('=' * _RULE_WIDTH)
                out.append(text)
            elif block.level == 2:
                out.append('-' * _RULE_WIDTH)
                out.append(text)
            else:
                out.append(text + ' ~')
            out.append('')
        elif isinstance(block, Paragraph):
            out.append(inlines_to_plain(block.inlines))
            out.append('')
        elif isinstance(block, BulletList):
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out.append(f'* {sub}')
            out.append('')
        elif isinstance(block, OrderedList):
            n = block.start
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out.append(f'{n}. {sub}')
                    n += 1
            out.append('')
        elif isinstance(block, BlockQuote):
            for sub in block_text_paragraphs(block.blocks):
                out.append(f'    {sub}')
            out.append('')
        elif isinstance(block, CodeBlock):
            out.append('>')
            for ln in block.text.split('\n'):
                out.append('    ' + ln)
            out.append('<')
            out.append('')
        elif isinstance(block, ThematicBreak):
            out.append('-' * _RULE_WIDTH)
            out.append('')
    return '\n'.join(out).rstrip('\n') + '\n'


class VimdocWriter(Writer):
    format_name = 'vimdoc'

    def write(self, document, options=None):
        return _write_vimdoc(document)


register_writer(VimdocWriter())
