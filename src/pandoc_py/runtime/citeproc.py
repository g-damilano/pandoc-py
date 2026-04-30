"""Citeproc integration — constrained slice.

Walks Cite nodes and rewrites their inline content using the document's
metadata ``references`` map (CSL-JSON-style entries keyed by id).

Outside the slice: real CSL style processing, locale handling, and
bibliography rendering. Those require csl xml processing; this minimal
slice only renders ``[Author Year]`` text from the references map.
"""
from __future__ import annotations

from typing import Any

from pandoc_py.ast import (
    Block, Cite, Citation, Div, Document, Emph, Heading, Inline, Link,
    Note, Paragraph, Span, Str, Strong,
)


def _render_cite(citation: Citation, references: dict[str, dict[str, Any]]) -> str:
    ref = references.get(citation.citation_id)
    if not ref:
        return f'[@{citation.citation_id}]'
    author = ref.get('author', '')
    if isinstance(author, list) and author:
        author = author[0].get('family', '') if isinstance(author[0], dict) else str(author[0])
    year = ''
    issued = ref.get('issued')
    if isinstance(issued, dict):
        date_parts = issued.get('date-parts')
        if isinstance(date_parts, list) and date_parts and isinstance(date_parts[0], list) and date_parts[0]:
            year = str(date_parts[0][0])
    return f'[{author} {year}]'.strip()


def _walk_inlines(inlines: list[Inline], references: dict[str, dict[str, Any]]) -> list[Inline]:
    out: list[Inline] = []
    for inline in inlines:
        if isinstance(inline, Cite):
            text = ' '.join(_render_cite(c, references) for c in inline.citations)
            out.append(Str(text))
        elif isinstance(inline, (Emph, Strong, Span, Link)):
            children = _walk_inlines(inline.inlines, references)
            out.append(type(inline)(inlines=children, **{k: v for k, v in vars(inline).items() if k != 'inlines'}))
        elif isinstance(inline, Note):
            out.append(Note(blocks=_walk_blocks(inline.blocks, references)))
        else:
            out.append(inline)
    return out


def _walk_blocks(blocks: list[Block], references: dict[str, dict[str, Any]]) -> list[Block]:
    out: list[Block] = []
    for block in blocks:
        if isinstance(block, Paragraph):
            out.append(Paragraph(inlines=_walk_inlines(block.inlines, references), is_plain=block.is_plain))
        elif isinstance(block, Heading):
            out.append(Heading(level=block.level, inlines=_walk_inlines(block.inlines, references), attr=block.attr))
        elif isinstance(block, Div):
            out.append(Div(blocks=_walk_blocks(block.blocks, references), attr=block.attr))
        else:
            out.append(block)
    return out


def process_citations(document: Document) -> Document:
    refs = document.meta.get('references', {})
    if not isinstance(refs, dict):
        return document
    return Document(
        blocks=_walk_blocks(document.blocks, refs),
        meta=document.meta,
        source_format=document.source_format,
    )
