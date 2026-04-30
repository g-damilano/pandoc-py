"""Template for lightweight text-format readers/writers.

Many formats have a small admitted slice that boils down to:
  read: parse plain markdown-like text into Heading/Paragraph/List/CodeBlock/Quote/HR
  write: serialize the same slice into a format-specific surface

``LightFormat`` builds a Reader/Writer pair from a small per-format
configuration of inline emphasis markers, heading prefix style, and code
fence style. Format modules instantiate it with their flavor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from pandoc_py.ast import (
    BlockQuote, BulletList, CodeBlock, Document, Heading, OrderedList,
    Paragraph, ThematicBreak,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import block_text_paragraphs, inlines_to_plain, parse_simple_blocks


@dataclass(frozen=True)
class FormatConfig:
    name: str
    aliases: tuple[str, ...] = ()
    heading: Callable[[int, str], str] = lambda lvl, text: '#' * lvl + ' ' + text
    bullet_prefix: str = '- '
    ordered_prefix: Callable[[int], str] = lambda n: f'{n}. '
    quote_prefix: str = '> '
    code_block: Callable[[str, str], list[str]] = lambda info, body: [f'```{info}'.rstrip(), *body.split('\n'), '```']
    thematic: str = '---'
    paragraph_blank: bool = True


def make_reader(config: FormatConfig) -> Reader:
    class _Reader(Reader):
        format_name = config.name
        aliases = config.aliases
        def read(self, source, options=None):
            if isinstance(source, bytes): source = source.decode('utf-8')
            return Document(blocks=parse_simple_blocks(source), source_format=config.name)
    _Reader.__name__ = f'{config.name.capitalize()}Reader'
    return _Reader()


def make_writer(config: FormatConfig) -> Writer:
    cfg = config

    def render(document: Document) -> str:
        out: list[str] = []
        for block in document.blocks:
            if isinstance(block, Heading):
                out.append(cfg.heading(max(1, block.level), inlines_to_plain(block.inlines)))
                if cfg.paragraph_blank: out.append('')
            elif isinstance(block, Paragraph):
                out.append(inlines_to_plain(block.inlines))
                if cfg.paragraph_blank: out.append('')
            elif isinstance(block, BulletList):
                for item in block.items:
                    for sub in block_text_paragraphs(item):
                        out.append(cfg.bullet_prefix + sub)
                if cfg.paragraph_blank: out.append('')
            elif isinstance(block, OrderedList):
                n = block.start
                for item in block.items:
                    for sub in block_text_paragraphs(item):
                        out.append(cfg.ordered_prefix(n) + sub)
                    n += 1
                if cfg.paragraph_blank: out.append('')
            elif isinstance(block, BlockQuote):
                for sub in block_text_paragraphs(block.blocks):
                    out.append(cfg.quote_prefix + sub)
                if cfg.paragraph_blank: out.append('')
            elif isinstance(block, CodeBlock):
                out.extend(cfg.code_block(block.info, block.text))
                if cfg.paragraph_blank: out.append('')
            elif isinstance(block, ThematicBreak):
                out.append(cfg.thematic)
                if cfg.paragraph_blank: out.append('')
        return '\n'.join(out).rstrip('\n') + '\n'

    class _Writer(Writer):
        format_name = cfg.name
        aliases = cfg.aliases
        def write(self, document, options=None):
            return render(document)
    _Writer.__name__ = f'{cfg.name.capitalize()}Writer'
    return _Writer()


def register(config: FormatConfig) -> None:
    register_reader(make_reader(config))
    register_writer(make_writer(config))
