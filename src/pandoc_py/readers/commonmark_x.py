from __future__ import annotations

import re
from dataclasses import replace

from pandoc_py.ast import (
    BlockQuote,
    BulletList,
    DefinitionList,
    Div,
    Document,
    Heading,
    Note,
    OrderedList,
    Paragraph,
    RawBlock,
    Str,
    Space,
)
from pandoc_py.readers.markdown import read_markdown

_INLINE_NOTE_RE = re.compile(r'\^\[([^\]\n]+)\]')
_INLINE_NOTE_OPEN = 'PANDOCPYINLINEFOOTNOTEOPEN'
_INLINE_NOTE_CLOSE = 'PANDOCPYINLINEFOOTNOTECLOSE'


def _protect_inline_notes(source: str) -> str:
    return _INLINE_NOTE_RE.sub(lambda match: f'{_INLINE_NOTE_OPEN}{match.group(1)}{_INLINE_NOTE_CLOSE}', source)


def _restore_literal_text(text: str) -> str:
    return text.replace(_INLINE_NOTE_OPEN, '^[').replace(_INLINE_NOTE_CLOSE, ']')


def _restore_task_marker_inlines(inlines: list[object]) -> list[object]:
    if not inlines or not isinstance(inlines[0], Str):
        return list(inlines)
    marker = inlines[0].text
    if marker == '☐':
        restored: list[object] = [Str('['), Space(), Str(']')]
    elif marker == '☒':
        restored = [Str('[x]')]
    else:
        return list(inlines)
    tail = list(inlines[1:])
    if tail and isinstance(tail[0], Space):
        restored.append(Space())
        tail = tail[1:]
    restored.extend(tail)
    return restored


def _normalize_block(block):
    if isinstance(block, Paragraph):
        return Paragraph(inlines=_normalize_inlines(block.inlines))
    if isinstance(block, Heading):
        return Heading(level=block.level, inlines=_normalize_inlines(block.inlines), attr=block.attr)
    if isinstance(block, BulletList):
        return BulletList(items=[[_normalize_block(child) for child in item] for item in block.items])
    if isinstance(block, OrderedList):
        return OrderedList(start=block.start, style=block.style, delimiter=block.delimiter, items=[[_normalize_block(child) for child in item] for item in block.items])
    if isinstance(block, BlockQuote):
        return BlockQuote(blocks=[_normalize_block(child) for child in block.blocks])
    if isinstance(block, DefinitionList):
        return DefinitionList(
            items=[
                (_normalize_inlines(term), [[_normalize_block(child) for child in definition] for definition in definitions])
                for term, definitions in block.items
            ]
        )
    if isinstance(block, Div):
        return Div(blocks=[_normalize_block(child) for child in block.blocks], attr=block.attr)
    if isinstance(block, RawBlock) and block.format == 'html' and not block.text.endswith('\n'):
        return RawBlock(format=block.format, text=block.text + '\n')
    return block


def _normalize_inlines(inlines: list[object]) -> list[object]:
    restored = [_normalize_inline(inline) for inline in inlines]
    if restored and isinstance(restored[0], Str) and restored[0].text in {'☐', '☒'}:
        return _restore_task_marker_inlines(restored)
    return restored


def _normalize_inline(inline):
    if isinstance(inline, Str):
        return Str(_restore_literal_text(inline.text))
    if isinstance(inline, Note):
        # Inline-note syntax is not admitted on the governed commonmark_x surface yet.
        # Protected placeholders keep it literal, so any remaining Note nodes must come
        # from reference-style footnotes and should be preserved.
        return Note(blocks=[_normalize_block(block) for block in inline.blocks])
    return inline


def read_commonmark_x(source: str) -> Document:
    protected = _protect_inline_notes(source)
    document = read_markdown(protected)
    return Document(
        blocks=[_normalize_block(block) for block in document.blocks],
        meta=dict(document.meta),
        source_format='commonmark_x',
    )
