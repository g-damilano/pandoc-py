from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MetaValue:
    """Base type for document metadata values in the current AST slice."""


@dataclass(frozen=True)
class Attr:
    identifier: str = ''
    classes: list[str] = field(default_factory=list)
    attributes: list[tuple[str, str]] = field(default_factory=list)


@dataclass(frozen=True)
class Inline:
    """Base type for inline nodes in the current AST slice."""


@dataclass(frozen=True)
class Str(Inline):
    text: str


@dataclass(frozen=True)
class Space(Inline):
    """A semantic space between inline tokens."""


@dataclass(frozen=True)
class SoftBreak(Inline):
    """A semantic soft line break inside a paragraph or heading."""


@dataclass(frozen=True)
class HardBreak(Inline):
    """A semantic hard line break inside a paragraph-like block."""


@dataclass(frozen=True)
class Emph(Inline):
    inlines: list[Inline] = field(default_factory=list)


@dataclass(frozen=True)
class Strong(Inline):
    inlines: list[Inline] = field(default_factory=list)


@dataclass(frozen=True)
class Strikeout(Inline):
    inlines: list[Inline] = field(default_factory=list)


@dataclass(frozen=True)
class Subscript(Inline):
    inlines: list[Inline] = field(default_factory=list)


@dataclass(frozen=True)
class Superscript(Inline):
    inlines: list[Inline] = field(default_factory=list)


@dataclass(frozen=True)
class Underline(Inline):
    inlines: list[Inline] = field(default_factory=list)


@dataclass(frozen=True)
class SmallCaps(Inline):
    inlines: list[Inline] = field(default_factory=list)


@dataclass(frozen=True)
class Quoted(Inline):
    inlines: list[Inline] = field(default_factory=list)
    quote_type: str = 'DoubleQuote'


@dataclass(frozen=True)
class Math(Inline):
    text: str
    display: bool = False


@dataclass(frozen=True)
class Code(Inline):
    text: str


@dataclass(frozen=True)
class Span(Inline):
    inlines: list[Inline] = field(default_factory=list)
    attr: Attr = field(default_factory=Attr)


@dataclass(frozen=True)
class Link(Inline):
    inlines: list[Inline] = field(default_factory=list)
    target: str = ''
    title: str = ''
    autolink: bool = False
    attr: Attr = field(default_factory=Attr)


@dataclass(frozen=True)
class Image(Inline):
    inlines: list[Inline] = field(default_factory=list)
    target: str = ''
    title: str = ''
    attr: Attr = field(default_factory=Attr)


@dataclass(frozen=True)
class RawInline(Inline):
    format: str = 'html'
    text: str = ''


@dataclass(frozen=True)
class Note(Inline):
    blocks: list['Block'] = field(default_factory=list)


@dataclass(frozen=True)
class Citation:
    citation_id: str
    prefix: list[Inline] = field(default_factory=list)
    suffix: list[Inline] = field(default_factory=list)
    mode: str = 'NormalCitation'
    note_num: int = 0
    hash: int = 0


@dataclass(frozen=True)
class Cite(Inline):
    citations: list[Citation] = field(default_factory=list)
    inlines: list[Inline] = field(default_factory=list)


@dataclass(frozen=True)
class Block:
    """Base type for block nodes in the current AST slice."""


@dataclass(frozen=True)
class Paragraph(Block):
    inlines: list[Inline] = field(default_factory=list)


@dataclass(frozen=True)
class LineBlock(Block):
    lines: list[list[Inline]] = field(default_factory=list)


@dataclass(frozen=True)
class Null(Block):
    """A null block placeholder in Pandoc AST."""


@dataclass(frozen=True)
class Heading(Block):
    level: int
    inlines: list[Inline] = field(default_factory=list)
    attr: Attr = field(default_factory=Attr)


@dataclass(frozen=True)
class BulletList(Block):
    items: list[list[Block]] = field(default_factory=list)


@dataclass(frozen=True)
class OrderedList(Block):
    start: int = 1
    style: str = 'Decimal'
    delimiter: str = 'Period'
    items: list[list[Block]] = field(default_factory=list)


@dataclass(frozen=True)
class BlockQuote(Block):
    blocks: list[Block] = field(default_factory=list)


@dataclass(frozen=True)
class ThematicBreak(Block):
    """A thematic break / horizontal rule block."""


@dataclass(frozen=True)
class CodeBlock(Block):
    text: str
    info: str = ''
    attr: Attr = field(default_factory=Attr)


@dataclass(frozen=True)
class RawBlock(Block):
    format: str = 'html'
    text: str = ''


@dataclass(frozen=True)
class Div(Block):
    blocks: list[Block] = field(default_factory=list)
    attr: Attr = field(default_factory=Attr)


@dataclass(frozen=True)
class DefinitionList(Block):
    items: list[tuple[list[Inline], list[list[Block]]]] = field(default_factory=list)


@dataclass(frozen=True)
class Figure(Block):
    image: Image
    attr: Attr = field(default_factory=Attr)


@dataclass(frozen=True)
class Table(Block):
    caption: list[Inline] = field(default_factory=list)
    aligns: list[str] = field(default_factory=list)
    headers: list[list[Inline]] = field(default_factory=list)
    rows: list[list[list[Inline]]] = field(default_factory=list)
    header_row_attr: Attr = field(default_factory=Attr)
    row_attrs: list[Attr] = field(default_factory=list)




@dataclass(frozen=True)
class MetaBool(MetaValue):
    value: bool


@dataclass(frozen=True)
class MetaString(MetaValue):
    text: str


@dataclass(frozen=True)
class MetaInlines(MetaValue):
    inlines: list[Inline] = field(default_factory=list)


@dataclass(frozen=True)
class MetaBlocks(MetaValue):
    blocks: list['Block'] = field(default_factory=list)


@dataclass(frozen=True)
class MetaList(MetaValue):
    items: list[MetaValue] = field(default_factory=list)


@dataclass(frozen=True)
class MetaMap(MetaValue):
    mapping: dict[str, MetaValue] = field(default_factory=dict)


@dataclass(frozen=True)
class Document:
    blocks: list[Block] = field(default_factory=list)
    meta: dict[str, MetaValue] = field(default_factory=dict)
    source_format: str = ''


__all__ = [
    'Attr',
    'Block',
    'BlockQuote',
    'BulletList',
    'Citation',
    'Cite',
    'Code',
    'CodeBlock',
    'DefinitionList',
    'Div',
    'Document',
    'Emph',
    'Figure',
    'HardBreak',
    'Heading',
    'Image',
    'Inline',
    'Link',
    'LineBlock',
    'Math',
    'MetaBlocks',
    'MetaBool',
    'MetaInlines',
    'MetaList',
    'MetaMap',
    'MetaString',
    'MetaValue',
    'Note',
    'Null',
    'OrderedList',
    'Paragraph',
    'RawBlock',
    'RawInline',
    'SoftBreak',
    'Space',
    'Span',
    'Str',
    'Strikeout',
    'Strong',
    'Subscript',
    'Superscript',
    'Underline',
    'SmallCaps',
    'Quoted',
    'Table',
    'ThematicBreak',
]
