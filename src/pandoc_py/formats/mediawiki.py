"""MediaWiki reader/writer — constrained slice."""
from __future__ import annotations

from pandoc_py.ast import (
    BlockQuote, BulletList, CodeBlock, Document, Heading, OrderedList,
    Paragraph, ThematicBreak,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import block_text_paragraphs, inlines_to_plain, parse_simple_blocks, slugify_heading


def _read_mediawiki(source: str) -> Document:
    return Document(blocks=parse_simple_blocks(source), source_format='mediawiki')


def _write_mediawiki(document: Document) -> str:
    out: list[str] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            text = inlines_to_plain(block.inlines)
            anchor = block.attr.identifier or slugify_heading(text)
            level = max(1, min(block.level, 6))
            out.append(f'<span id="{anchor}"></span>')
            out.append(f'{"=" * level} {text} {"=" * level}')
            out.append('')
        elif isinstance(block, Paragraph):
            out.append(inlines_to_plain(block.inlines)); out.append('')
        elif isinstance(block, BulletList):
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out.append(f'* {sub}')
            out.append('')
        elif isinstance(block, OrderedList):
            n = block.start
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out.append(f'# {sub}')
                n += 1
            out.append('')
        elif isinstance(block, BlockQuote):
            for sub in block_text_paragraphs(block.blocks): out.append(f'> {sub}')
            out.append('')
        elif isinstance(block, CodeBlock):
            out.append(f'<pre>{block.text}</pre>'); out.append('')
        elif isinstance(block, ThematicBreak):
            out.append('----'); out.append('')
    return '\n'.join(out).rstrip('\n') + '\n'


class MediawikiReader(Reader):
    format_name = 'mediawiki'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_mediawiki(source)

class MediawikiWriter(Writer):
    format_name = 'mediawiki'
    def write(self, document, options=None):
        return _write_mediawiki(document)

register_reader(MediawikiReader())
register_writer(MediawikiWriter())
