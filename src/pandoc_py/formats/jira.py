"""Jira/Confluence wiki reader/writer — constrained slice."""
from __future__ import annotations

from pandoc_py.ast import (
    BlockQuote, BulletList, CodeBlock, Document, Heading, OrderedList,
    Paragraph, ThematicBreak,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import block_text_paragraphs, inlines_to_plain, parse_simple_blocks, slugify_heading


def _read_jira(source: str) -> Document:
    return Document(blocks=parse_simple_blocks(source), source_format='jira')


def _write_jira(document: Document) -> str:
    out: list[str] = []
    blocks = document.blocks
    for idx, block in enumerate(blocks):
        if isinstance(block, Heading):
            text = inlines_to_plain(block.inlines)
            anchor = block.attr.identifier or slugify_heading(text)
            level = max(1, min(block.level, 6))
            out.append(f'h{level}. ' + '{anchor:' + anchor + '}' + text)
        elif isinstance(block, Paragraph):
            out.append(inlines_to_plain(block.inlines))
        elif isinstance(block, BulletList):
            for item in block.items:
                for sub in block_text_paragraphs(item): out.append(f'* {sub}')
        elif isinstance(block, OrderedList):
            n = block.start
            for item in block.items:
                for sub in block_text_paragraphs(item): out.append(f'# {sub}'); n += 1
        elif isinstance(block, BlockQuote):
            for sub in block_text_paragraphs(block.blocks): out.append(f'bq. {sub}')
        elif isinstance(block, CodeBlock):
            out.append('{noformat}')
            out.append(block.text + '{noformat}')
        elif isinstance(block, ThematicBreak):
            out.append('----')
        # Blank line between blocks unless previous was a heading (pandoc
        # joins heading immediately to following paragraph).
        if idx + 1 < len(blocks) and not isinstance(block, Heading):
            out.append('')
    return '\n'.join(out) + '\n'


class JiraReader(Reader):
    format_name = 'jira'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_jira(source)

class JiraWriter(Writer):
    format_name = 'jira'
    def write(self, document, options=None):
        return _write_jira(document)

register_reader(JiraReader())
register_writer(JiraWriter())
