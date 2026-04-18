from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.ast import Attr, BulletList, CodeBlock, Figure, Heading, OrderedList, Paragraph, SoftBreak, Space, Span, Str, Table
from pandoc_py.readers.html import read_html
from pandoc_py.writers.native import write_native
from pandoc_py.writers.pandoc_json import document_to_pandoc_json_payload


def test_read_html_heading_and_link_attrs() -> None:
    document = read_html('<h1 id="x" class="a" data-key="val">Heading</h1><p><a href="https://example.com" title="T" class="uri">https://example.com</a></p>')
    heading = document.blocks[0]
    assert isinstance(heading, Heading)
    assert heading.attr.identifier == 'x'
    assert heading.attr.classes == ['a']
    assert heading.attr.attributes == [('key', 'val')]
    paragraph = document.blocks[1]
    assert isinstance(paragraph, Paragraph)


def test_read_html_task_list_and_code_block() -> None:
    document = read_html('<ul class="task-list"><li><label><input type="checkbox" />one</label></li></ul><pre id="x" class="python"><code>print(1)</code></pre>')
    task_list = document.blocks[0]
    assert isinstance(task_list, BulletList)
    assert task_list.items[0][0] == Paragraph(inlines=[Str('☐'), Space(), Str('one')])
    code = document.blocks[1]
    assert isinstance(code, CodeBlock)
    assert code.attr.identifier == 'x'
    assert code.attr.classes == ['python']
    assert code.text == 'print(1)'


def test_read_html_figure_and_table() -> None:
    source = (
        '<figure id="f"><img src="img.png" class="c" data-key="val" alt="cap" />'
        '<figcaption aria-hidden="true">cap</figcaption></figure>'
        '<table><caption>Cap</caption><thead><tr><th style="text-align: left;">A</th><th style="text-align: right;">B</th></tr></thead>'
        '<tbody><tr><td><em>a</em></td><td><a href="https://example.com">b</a></td></tr></tbody></table>'
    )
    document = read_html(source)
    figure = document.blocks[0]
    table = document.blocks[1]
    assert isinstance(figure, Figure)
    assert figure.attr.identifier == 'f'
    assert figure.image.attr.classes == ['c']
    assert figure.image.attr.attributes == [('key', 'val')]
    assert isinstance(table, Table)
    assert table.caption == [Str('Cap')]
    assert table.aligns == ['AlignLeft', 'AlignRight']


def test_html_ordered_list_uses_default_delim_in_json_payload() -> None:
    document = read_html('<ol type="1"><li>one</li><li>two</li></ol>')
    ordered = document.blocks[0]
    assert isinstance(ordered, OrderedList)
    assert ordered.style == 'Decimal'
    assert ordered.delimiter == 'DefaultDelim'
    payload = document_to_pandoc_json_payload(document)
    assert payload['blocks'][0]['c'][0] == [1, {'t': 'Decimal'}, {'t': 'DefaultDelim'}]


def test_html_display_math_span_preserves_softbreaks() -> None:
    document = read_html('''<p><span class="math display">\\[
x+y
\\]</span></p>''')
    assert document.blocks == [
        Paragraph(
            inlines=[
                Span(
                    inlines=[Str('\\['), SoftBreak(), Str('x+y'), SoftBreak(), Str('\\]')],
                    attr=Attr(classes=['math', 'display']),
                )
            ]
        )
    ]


def test_html_table_row_attrs_and_alignments_roundtrip_survive_writers() -> None:
    document = read_html(
        '<table><thead><tr class="header"><th style="text-align: left;">A</th><th style="text-align: right;">B</th></tr></thead>'
        '<tbody><tr class="odd"><td style="text-align: left;">1</td><td style="text-align: right;">2</td></tr></tbody></table>'
    )
    table = document.blocks[0]
    assert isinstance(table, Table)
    assert table.header_row_attr == Attr(classes=['header'])
    assert table.row_attrs == [Attr(classes=['odd'])]
    payload = document_to_pandoc_json_payload(document)
    table_payload = payload['blocks'][0]['c']
    row = table_payload[3][1][0]
    assert row[0] == ['', ['header'], []]
    assert table_payload[2] == [[{'t': 'AlignLeft'}, {'t': 'ColWidthDefault'}], [{'t': 'AlignRight'}, {'t': 'ColWidthDefault'}]]
    assert row[1][0][1] == {'t': 'AlignDefault'}
    assert row[1][1][1] == {'t': 'AlignDefault'}
    assert 'Row ("",["odd"],[])' in write_native(document)
