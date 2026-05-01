"""Typst reader/writer — constrained slice."""
from __future__ import annotations

from pandoc_py.ast import (
    BlockQuote, BulletList, CodeBlock, Document, Heading, OrderedList,
    Paragraph, ThematicBreak,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import block_text_paragraphs, inlines_to_plain, parse_simple_blocks, slugify_heading


def _read_typst(source: str) -> Document:
    return Document(blocks=parse_simple_blocks(source), source_format='typst')


def _write_typst(document: Document) -> str:
    out: list[str] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            text = inlines_to_plain(block.inlines)
            anchor = block.attr.identifier or slugify_heading(text)
            out.append('=' * max(1, min(block.level, 6)) + ' ' + text)
            out.append(f'<{anchor}>')
        elif isinstance(block, Paragraph):
            out.append(inlines_to_plain(block.inlines))
        elif isinstance(block, BulletList):
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out.append(f'- {sub}')
        elif isinstance(block, OrderedList):
            n = block.start
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out.append(f'+ {sub}')
                n += 1
        elif isinstance(block, BlockQuote):
            for sub in block_text_paragraphs(block.blocks):
                out.append(f'#quote[{sub}]')
        elif isinstance(block, CodeBlock):
            out.append('```' + (block.info or ''))
            out.extend(block.text.split('\n'))
            out.append('```')
        elif isinstance(block, ThematicBreak):
            out.append('#line(length: 100%)')
    return '\n'.join(out) + '\n'


class TypstReader(Reader):
    format_name = 'typst'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_typst(source)

class TypstWriter(Writer):
    format_name = 'typst'
    def write(self, document, options=None):
        return _write_typst(document)

register_reader(TypstReader())
register_writer(TypstWriter())
