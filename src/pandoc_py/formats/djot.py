"""Djot reader/writer — constrained slice."""
from __future__ import annotations

from pandoc_py.ast import (
    BlockQuote, BulletList, CodeBlock, Document, Heading, OrderedList,
    Paragraph, ThematicBreak,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import block_text_paragraphs, inlines_to_plain, parse_simple_blocks, slugify_heading


def _read_djot(source: str) -> Document:
    return Document(blocks=parse_simple_blocks(source), source_format='djot')


def _write_djot(document: Document) -> str:
    out: list[str] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            text = inlines_to_plain(block.inlines)
            anchor = block.attr.identifier or slugify_heading(text)
            out.append('{#' + anchor + '}')
            out.append('#' * max(1, min(block.level, 6)) + ' ' + text)
            out.append('')
        elif isinstance(block, Paragraph):
            out.append(inlines_to_plain(block.inlines)); out.append('')
        elif isinstance(block, BulletList):
            for item in block.items:
                for sub in block_text_paragraphs(item): out.append(f'- {sub}')
            out.append('')
        elif isinstance(block, OrderedList):
            n = block.start
            for item in block.items:
                for sub in block_text_paragraphs(item): out.append(f'{n}. {sub}'); n += 1
            out.append('')
        elif isinstance(block, BlockQuote):
            for sub in block_text_paragraphs(block.blocks): out.append(f'> {sub}')
            out.append('')
        elif isinstance(block, CodeBlock):
            out.append('```' + (block.info or '')); out.extend(block.text.split('\n')); out.append('```'); out.append('')
        elif isinstance(block, ThematicBreak):
            out.append('---'); out.append('')
    return '\n'.join(out).rstrip('\n') + '\n'


class DjotReader(Reader):
    format_name = 'djot'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_djot(source)

class DjotWriter(Writer):
    format_name = 'djot'
    def write(self, document, options=None):
        return _write_djot(document)

register_reader(DjotReader())
register_writer(DjotWriter())
