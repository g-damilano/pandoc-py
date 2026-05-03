"""XWiki markup writer — constrained slice.

XWiki uses ``=`` for headings (``= H1 =``, ``== H2 ==`` etc.), ``*`` for
bullet items, ``1.`` for ordered items, and ``{{{ ... }}}`` for inline
code. This is a writer-only format in Pandoc.
"""
from __future__ import annotations

from pandoc_py.ast import (
    BlockQuote, BulletList, CodeBlock, Document, Heading, OrderedList,
    Paragraph, ThematicBreak,
)
from pandoc_py.io import Writer, register_writer
from ._common import block_text_paragraphs, inlines_to_plain


def _write_xwiki(document: Document) -> str:
    out: list[str] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            mark = '=' * max(1, min(block.level, 6))
            text = inlines_to_plain(block.inlines)
            out.append(f'{mark} {text} {mark}')
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
                    out.append(f'1. {sub}')
                    n += 1
            out.append('')
        elif isinstance(block, BlockQuote):
            for sub in block_text_paragraphs(block.blocks):
                out.append(f'> {sub}')
            out.append('')
        elif isinstance(block, CodeBlock):
            info = block.info or ''
            header = '{{code' + (f' language="{info}"' if info else '') + '}}'
            out.append(header)
            out.extend(block.text.split('\n'))
            out.append('{{/code}}')
            out.append('')
        elif isinstance(block, ThematicBreak):
            out.append('----')
            out.append('')
    return '\n'.join(out).rstrip('\n') + '\n'


class XwikiWriter(Writer):
    format_name = 'xwiki'

    def write(self, document, options=None):
        return _write_xwiki(document)


register_writer(XwikiWriter())
