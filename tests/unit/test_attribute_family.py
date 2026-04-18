from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.ast import Attr, CodeBlock, Div, Heading, Image, Link, Paragraph, Space, Span, Str
from pandoc_py.readers.markdown import read_markdown
from pandoc_py.writers.markdown import write_markdown


def test_read_heading_with_attributes() -> None:
    document = read_markdown('# Head {#x .c key=val}\n')
    assert document.blocks == [Heading(level=1, inlines=[Str('Head')], attr=Attr(identifier='x', classes=['c'], attributes=[('key', 'val')]))]


def test_read_bracketed_span_with_attributes() -> None:
    document = read_markdown('[alpha]{#x .c key=val}\n')
    assert document.blocks == [Paragraph(inlines=[Span(inlines=[Str('alpha')], attr=Attr(identifier='x', classes=['c'], attributes=[('key', 'val')]))])]


def test_read_fenced_div_with_attributes() -> None:
    document = read_markdown('::: {.note #x key=val}\npara\n:::\n')
    assert document.blocks == [Div(blocks=[Paragraph(inlines=[Str('para')])], attr=Attr(identifier='x', classes=['note'], attributes=[('key', 'val')]))]


def test_read_fenced_code_block_with_attributes() -> None:
    document = read_markdown('``` {.python #x key=val}\nprint(1)\n```\n')
    assert document.blocks == [CodeBlock(text='print(1)', info='python', attr=Attr(identifier='x', classes=[], attributes=[('key', 'val')]))]


def test_read_link_with_attributes() -> None:
    document = read_markdown('[a](https://e.com){#x .c key=val}\n')
    assert document.blocks == [Paragraph(inlines=[Link(inlines=[Str('a')], target='https://e.com', attr=Attr(identifier='x', classes=['c'], attributes=[('key', 'val')]))])]


def test_read_inline_image_with_attributes() -> None:
    document = read_markdown('text ![a](img.png){#x .c key=val} more\n')
    assert document.blocks == [
        Paragraph(
            inlines=[
                Str('text'),
                Space(),
                Image(inlines=[Str('a')], target='img.png', attr=Attr(identifier='x', classes=['c'], attributes=[('key', 'val')])),
                Space(),
                Str('more'),
            ]
        )
    ]


def test_write_markdown_for_attribute_family() -> None:
    heading = read_markdown('# Head {#h .hh k=v}\n')
    div = read_markdown('::: {.note #x key=val}\npara\n:::\n')
    link = read_markdown('[a](https://e.com){#l .c key=val}\n')
    assert '# Head{#h .hh k="v"}' in write_markdown(heading)
    assert ':::{#x .note key="val"}' in write_markdown(div)
    assert '[a](https://e.com){#l .c key="val"}' in write_markdown(link)
