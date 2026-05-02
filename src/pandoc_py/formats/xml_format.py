"""Pandoc-XML reader/writer.

Pandoc's XML format is a serialization of the Pandoc AST as XML
(``<Pandoc><blocks><Header>...</Header><Para>...</Para>...</blocks></Pandoc>``).
This module implements the constrained slice of that schema.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from html import escape

from pandoc_py.ast import (
    Attr, BlockQuote, BulletList, CodeBlock, Document, Heading, OrderedList,
    Paragraph, ThematicBreak,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import block_text_paragraphs, inlines_to_plain, text_to_inlines


def _read_xml(source: str) -> Document:
    root = ET.fromstring(source)
    blocks: list = []

    def parse_inlines_text(el):
        return ''.join(el.itertext()).strip()

    def parse_block(el):
        tag = el.tag.split('}')[-1]
        if tag == 'Header':
            level = int(el.attrib.get('level', '1'))
            anchor = el.attrib.get('id', '')
            attr = Attr(identifier=anchor) if anchor else Attr()
            blocks.append(Heading(level=level, inlines=text_to_inlines(parse_inlines_text(el)), attr=attr))
        elif tag in {'Para', 'Plain'}:
            text = parse_inlines_text(el)
            if text:
                blocks.append(Paragraph(inlines=text_to_inlines(text), is_plain=(tag == 'Plain')))
        elif tag == 'BulletList':
            items = []
            for it in el:
                if it.tag.split('}')[-1] == 'item':
                    items.append([Paragraph(inlines=text_to_inlines(parse_inlines_text(it)), is_plain=True)])
            blocks.append(BulletList(items=items))
        elif tag == 'OrderedList':
            items = []
            for it in el:
                if it.tag.split('}')[-1] == 'item':
                    items.append([Paragraph(inlines=text_to_inlines(parse_inlines_text(it)), is_plain=True)])
            blocks.append(OrderedList(items=items))
        elif tag == 'BlockQuote':
            text = parse_inlines_text(el)
            blocks.append(BlockQuote(blocks=[Paragraph(inlines=text_to_inlines(text))]))
        elif tag == 'CodeBlock':
            blocks.append(CodeBlock(text=el.text or ''))
        elif tag in {'HorizontalRule', 'ThematicBreak'}:
            blocks.append(ThematicBreak())
        else:
            for child in el:
                parse_block(child)

    blocks_root = root.find('blocks')
    if blocks_root is not None:
        for child in blocks_root:
            parse_block(child)
    else:
        for child in root:
            parse_block(child)
    return Document(blocks=blocks, source_format='xml')


def _write_xml(document: Document) -> str:
    parts: list[str] = ["<?xml version='1.0' ?>"]
    parts.append('<Pandoc api-version="1,23,1">')
    parts.append('<meta />')
    parts.append('<blocks>')
    for block in document.blocks:
        if isinstance(block, Heading):
            anchor_attr = ''
            if block.attr.identifier:
                anchor_attr = f' id="{escape(block.attr.identifier, quote=True)}"'
            parts.append(f'<Header{anchor_attr} level="{max(1, min(block.level, 6))}">{escape(inlines_to_plain(block.inlines))}</Header>')
        elif isinstance(block, Paragraph):
            tag = 'Plain' if block.is_plain else 'Para'
            parts.append(f'<{tag}>{escape(inlines_to_plain(block.inlines))}</{tag}>')
        elif isinstance(block, BulletList):
            parts.append('<BulletList>')
            for item in block.items:
                parts.append('<item>')
                for sub in block_text_paragraphs(item):
                    parts.append(f'<Plain>{escape(sub)}</Plain>')
                parts.append('</item>')
            parts.append('</BulletList>')
        elif isinstance(block, OrderedList):
            parts.append('<OrderedList>')
            for item in block.items:
                parts.append('<item>')
                for sub in block_text_paragraphs(item):
                    parts.append(f'<Plain>{escape(sub)}</Plain>')
                parts.append('</item>')
            parts.append('</OrderedList>')
        elif isinstance(block, BlockQuote):
            parts.append('<BlockQuote>')
            for sub in block_text_paragraphs(block.blocks):
                parts.append(f'<Para>{escape(sub)}</Para>')
            parts.append('</BlockQuote>')
        elif isinstance(block, CodeBlock):
            parts.append(f'<CodeBlock>{escape(block.text)}</CodeBlock>')
        elif isinstance(block, ThematicBreak):
            parts.append('<HorizontalRule />')
    parts.append('</blocks>')
    parts.append('</Pandoc>')
    return '\n'.join(parts) + '\n'


class XmlReader(Reader):
    format_name = 'xml'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_xml(source)


class XmlWriter(Writer):
    format_name = 'xml'
    def write(self, document, options=None):
        return _write_xml(document)


register_reader(XmlReader())
register_writer(XmlWriter())
