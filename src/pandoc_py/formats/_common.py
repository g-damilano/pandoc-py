"""Shared helpers for the constrained-slice readers and writers.

Each format module reuses these helpers so the per-format code stays minimal
and the slice they admit is consistent.
"""

from __future__ import annotations

import re
from typing import Iterable

from pandoc_py.ast import (
    Block,
    BlockQuote,
    BulletList,
    Code,
    CodeBlock,
    Document,
    Emph,
    HardBreak,
    Heading,
    Inline,
    Link,
    OrderedList,
    Paragraph,
    SoftBreak,
    Space,
    Str,
    Strong,
    ThematicBreak,
)


# --- Inline tokenizer ------------------------------------------------------

def text_to_inlines(text: str) -> list[Inline]:
    """Tokenize a single-line snippet into Str/Space inlines.

    No format-specific markup. Caller layers on top.
    """
    out: list[Inline] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i].isspace():
            out.append(Space())
            i += 1
            while i < n and text[i].isspace():
                i += 1
            continue
        j = i
        while j < n and not text[j].isspace():
            j += 1
        out.append(Str(text[i:j]))
        i = j
    return out


def join_paragraph_lines(lines: list[str]) -> list[Inline]:
    """Join multi-line paragraph text with SoftBreak between lines."""
    out: list[Inline] = []
    for idx, line in enumerate(lines):
        if idx > 0:
            out.append(SoftBreak())
        out.extend(text_to_inlines(line.rstrip()))
    return out


# --- Inline writer (Pandoc-canonical plain rendering) ----------------------

def inlines_to_plain(inlines: Iterable[Inline]) -> str:
    """Flatten inlines to plain text, used by formats whose writer surface
    only supports plain-text inline content."""
    parts: list[str] = []
    for inline in inlines:
        if isinstance(inline, Str):
            parts.append(inline.text)
        elif isinstance(inline, Space):
            parts.append(' ')
        elif isinstance(inline, SoftBreak):
            parts.append(' ')
        elif isinstance(inline, HardBreak):
            parts.append('\n')
        elif isinstance(inline, (Emph, Strong)):
            parts.append(inlines_to_plain(inline.inlines))
        elif isinstance(inline, Code):
            parts.append(inline.text)
        elif isinstance(inline, Link):
            parts.append(inlines_to_plain(inline.inlines))
        else:
            # Best-effort: any other inline drops to its inline children if it
            # has them, otherwise to empty string.
            children = getattr(inline, 'inlines', None)
            if children is not None:
                parts.append(inlines_to_plain(children))
    return ''.join(parts)


# --- Block-level slice writer helpers --------------------------------------

def block_text_paragraphs(blocks: list[Block]) -> list[str]:
    """Render the admitted block slice as a list of plain-text paragraph
    strings. Used by the simplest writers (one paragraph -> one block of
    text). Headings, lists, code blocks and quotes degrade to plain text.
    """
    out: list[str] = []
    for block in blocks:
        if isinstance(block, Paragraph):
            out.append(inlines_to_plain(block.inlines))
        elif isinstance(block, Heading):
            out.append(inlines_to_plain(block.inlines))
        elif isinstance(block, BlockQuote):
            for sub in block_text_paragraphs(block.blocks):
                out.append('> ' + sub)
        elif isinstance(block, (BulletList, OrderedList)):
            marker_idx = 0
            for item in block.items:
                marker_idx += 1
                marker = '- ' if isinstance(block, BulletList) else f'{marker_idx}. '
                for sub in block_text_paragraphs(item):
                    out.append(marker + sub)
        elif isinstance(block, CodeBlock):
            out.append(block.text)
        elif isinstance(block, ThematicBreak):
            out.append('---')
    return out


# --- Light line-format reader skeleton -------------------------------------

ATX_HEADING = re.compile(r'^(#{1,6})\s+(.*?)\s*#*\s*$')
SETEXT_LEVEL_1 = re.compile(r'^=+\s*$')
SETEXT_LEVEL_2 = re.compile(r'^-+\s*$')
BULLET_ITEM = re.compile(r'^[-*+]\s+(.*)$')
NUMBERED_ITEM = re.compile(r'^(\d+)[.)]\s+(.*)$')
BLOCK_QUOTE_LINE = re.compile(r'^>\s?(.*)$')
THEMATIC = re.compile(r'^([-*_])\1{2,}\s*$')
FENCE_OPEN = re.compile(r'^(```+|~~~+)\s*([\w-]*)\s*$')


def parse_simple_blocks(text: str, *, atx_only: bool = False) -> list[Block]:
    """A constrained block-level parser shared by lightweight format readers.

    Recognised constructs in this slice:
      * ATX headings ``#``..``######``
      * Bullet lists ``- item`` (single-paragraph items)
      * Ordered lists ``1. item``
      * Block quotes ``> line``
      * Thematic breaks (``---``, ``***``, ``___``)
      * Fenced code blocks (```` ```lang ```` or ``~~~lang``)
      * Plain paragraphs separated by blank lines

    Format-specific inline syntax (``*emph*``, ``[link](...)``, etc.) is
    expected to be applied by the caller via a post-processing pass.
    """
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    if lines and lines[-1] == '':
        lines.pop()

    out: list[Block] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if THEMATIC.match(line):
            out.append(ThematicBreak())
            i += 1
            continue
        m = ATX_HEADING.match(line)
        if m:
            level = len(m.group(1))
            out.append(Heading(level=level, inlines=text_to_inlines(m.group(2))))
            i += 1
            continue
        m = FENCE_OPEN.match(line)
        if m:
            fence = m.group(1)
            info = m.group(2)
            buf: list[str] = []
            j = i + 1
            close = re.compile(r'^' + re.escape(fence[0]) + r'{' + str(len(fence)) + r',}\s*$')
            while j < len(lines) and not close.match(lines[j]):
                buf.append(lines[j])
                j += 1
            text_block = '\n'.join(buf)
            out.append(CodeBlock(text=text_block, info=info))
            i = j + 1
            continue
        m = BULLET_ITEM.match(line)
        if m:
            items: list[list[Block]] = []
            while i < len(lines):
                im = BULLET_ITEM.match(lines[i])
                if not im:
                    break
                items.append([Paragraph(inlines=text_to_inlines(im.group(1)), is_plain=True)])
                i += 1
            out.append(BulletList(items=items))
            continue
        m = NUMBERED_ITEM.match(line)
        if m:
            items = []
            start = int(m.group(1))
            while i < len(lines):
                im = NUMBERED_ITEM.match(lines[i])
                if not im:
                    break
                items.append([Paragraph(inlines=text_to_inlines(im.group(2)), is_plain=True)])
                i += 1
            out.append(OrderedList(start=start, items=items))
            continue
        m = BLOCK_QUOTE_LINE.match(line)
        if m:
            buf = [m.group(1)]
            j = i + 1
            while j < len(lines):
                qm = BLOCK_QUOTE_LINE.match(lines[j])
                if not qm:
                    break
                buf.append(qm.group(1))
                j += 1
            out.append(BlockQuote(blocks=[Paragraph(inlines=join_paragraph_lines(buf))]))
            i = j
            continue
        if not atx_only:
            # Setext heading?
            if i + 1 < len(lines):
                if SETEXT_LEVEL_1.match(lines[i + 1].strip()) and lines[i].strip():
                    out.append(Heading(level=1, inlines=text_to_inlines(lines[i].strip())))
                    i += 2
                    continue
                if SETEXT_LEVEL_2.match(lines[i + 1].strip()) and lines[i].strip():
                    out.append(Heading(level=2, inlines=text_to_inlines(lines[i].strip())))
                    i += 2
                    continue
        # Paragraph — collect until blank or block-starter
        buf = [line]
        j = i + 1
        while j < len(lines) and lines[j].strip() and not (
            ATX_HEADING.match(lines[j])
            or BULLET_ITEM.match(lines[j])
            or NUMBERED_ITEM.match(lines[j])
            or BLOCK_QUOTE_LINE.match(lines[j])
            or FENCE_OPEN.match(lines[j])
            or THEMATIC.match(lines[j])
        ):
            buf.append(lines[j])
            j += 1
        out.append(Paragraph(inlines=join_paragraph_lines(buf)))
        i = j
    return out


# --- Common Document constructor ------------------------------------------

def text_document(text: str, source_format: str, *, atx_only: bool = False) -> Document:
    return Document(blocks=parse_simple_blocks(text, atx_only=atx_only), source_format=source_format)
