"""Haddock reader/writer — constrained slice."""
from __future__ import annotations

from pandoc_py.ast import (
    BlockQuote, BulletList, CodeBlock, Document, Heading, OrderedList,
    Paragraph, ThematicBreak,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import block_text_paragraphs, inlines_to_plain, parse_simple_blocks, slugify_heading


def _read_haddock(source: str) -> Document:
    return Document(blocks=parse_simple_blocks(source), source_format='haddock')


def _write_haddock(document: Document) -> str:
    out: list[str] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            text = inlines_to_plain(block.inlines)
            anchor = block.attr.identifier or slugify_heading(text)
            out.append('=' * max(1, min(block.level, 6)) + ' ' + text)
            out.append(f'#{anchor}#')
            out.append('')
        elif isinstance(block, Paragraph):
            out.append(inlines_to_plain(block.inlines)); out.append('')
        elif isinstance(block, BulletList):
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out.append(f'-   {sub}')
            out.append('')
        elif isinstance(block, OrderedList):
            n = block.start
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out.append(f'{n}.  {sub}')
                n += 1
            out.append('')
        elif isinstance(block, BlockQuote):
            for sub in block_text_paragraphs(block.blocks):
                out.append(f'> {sub}')
            out.append('')
        elif isinstance(block, CodeBlock):
            for ln in block.text.split('\n'):
                out.append(f'> {ln}')
            out.append('')
        elif isinstance(block, ThematicBreak):
            out.append('---'); out.append('')
    return '\n'.join(out).rstrip('\n') + '\n'


class HaddockReader(Reader):
    format_name = 'haddock'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_haddock(source)

class HaddockWriter(Writer):
    format_name = 'haddock'
    def write(self, document, options=None):
        return _write_haddock(document)

register_reader(HaddockReader())
register_writer(HaddockWriter())
