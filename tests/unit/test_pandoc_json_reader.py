
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.ast import (
    Attr,
    Cite,
    CodeBlock,
    Document,
    Figure,
    Heading,
    Image,
    Link,
    Paragraph,
    Space,
    Str,
    Table,
)
from pandoc_py.readers.pandoc_json import document_from_pandoc_json_payload, read_pandoc_json


def test_read_simple_paragraph_from_pandoc_json() -> None:
    document = read_pandoc_json(json.dumps({
        'pandoc-api-version': [1, 23, 1],
        'meta': {},
        'blocks': [{'t': 'Para', 'c': [{'t': 'Str', 'c': 'alpha'}, {'t': 'Space'}, {'t': 'Str', 'c': 'beta'}]}],
    }))
    assert document == Document(blocks=[Paragraph(inlines=[Str('alpha'), Space(), Str('beta')])])


def test_read_heading_link_and_autolink_from_pandoc_json() -> None:
    payload = {
        'pandoc-api-version': [1, 23, 1],
        'meta': {},
        'blocks': [{
            't': 'Header',
            'c': [2, ['sec', ['x'], [['k', 'v']]], [
                {'t': 'Str', 'c': 'see'},
                {'t': 'Space'},
                {'t': 'Link', 'c': [['', ['uri'], []], [{'t': 'Str', 'c': 'https://example.com'}], ['https://example.com', '']]},
            ]],
        }],
    }
    document = document_from_pandoc_json_payload(payload)
    assert document == Document(blocks=[
        Heading(
            level=2,
            attr=Attr(identifier='sec', classes=['x'], attributes=[('k', 'v')]),
            inlines=[Str('see'), Space(), Link(inlines=[Str('https://example.com')], target='https://example.com', autolink=True)],
        )
    ])


def test_read_codeblock_info_from_pandoc_json() -> None:
    payload = {
        'pandoc-api-version': [1, 23, 1],
        'meta': {},
        'blocks': [{
            't': 'CodeBlock',
            'c': [['x', ['python', 'extra'], [['k', 'v']]], 'print(1)'],
        }],
    }
    document = document_from_pandoc_json_payload(payload)
    assert document == Document(blocks=[
        CodeBlock(text='print(1)', info='python', attr=Attr(identifier='x', classes=['extra'], attributes=[('k', 'v')]))
    ])


def test_read_cite_from_pandoc_json() -> None:
    payload = {
        'pandoc-api-version': [1, 23, 1],
        'meta': {},
        'blocks': [{
            't': 'Para',
            'c': [{
                't': 'Cite',
                'c': [[{
                    'citationId': 'doe2020',
                    'citationPrefix': [{'t': 'Str', 'c': 'see'}],
                    'citationSuffix': [{'t': 'Str', 'c': 'p.'}, {'t': 'Space'}, {'t': 'Str', 'c': '3'}],
                    'citationMode': {'t': 'NormalCitation'},
                    'citationNoteNum': 2,
                    'citationHash': 0,
                }], [{'t': 'Str', 'c': '[@doe2020, p. 3]'}]],
            }],
        }],
    }
    document = document_from_pandoc_json_payload(payload)
    para = document.blocks[0]
    assert isinstance(para, Paragraph)
    assert isinstance(para.inlines[0], Cite)
    assert para.inlines[0].citations[0].citation_id == 'doe2020'
    assert para.inlines[0].citations[0].note_num == 2



def test_read_table_from_pandoc_json() -> None:
    payload = {
        'pandoc-api-version': [1, 23, 1],
        'meta': {},
        'blocks': [{
            't': 'Table',
            'c': [
                ['', [], []],
                [None, [{'t': 'Plain', 'c': [{'t': 'Str', 'c': 'Cap'}]}]],
                [[{'t': 'AlignLeft'}, {'t': 'ColWidthDefault'}], [{'t': 'AlignRight'}, {'t': 'ColWidthDefault'}]],
                [['', [], []], [
                    [['', [], []], [
                        [['', [], []], {'t': 'AlignLeft'}, 1, 1, [{'t': 'Plain', 'c': [{'t': 'Str', 'c': 'A'}]}]],
                        [['', [], []], {'t': 'AlignRight'}, 1, 1, [{'t': 'Plain', 'c': [{'t': 'Str', 'c': 'B'}]}]],
                    ]]
                ]],
                [[['', [], []], 0, [], [
                    [['', [], []], [
                        [['', [], []], {'t': 'AlignLeft'}, 1, 1, [{'t': 'Plain', 'c': [{'t': 'Str', 'c': '1'}]}]],
                        [['', [], []], {'t': 'AlignRight'}, 1, 1, [{'t': 'Plain', 'c': [{'t': 'Str', 'c': '2'}]}]],
                    ]]
                ]]],
                [['', [], []], []],
            ],
        }],
    }
    document = document_from_pandoc_json_payload(payload)
    assert document == Document(blocks=[
        Table(
            caption=[Str('Cap')],
            aligns=['AlignLeft', 'AlignRight'],
            headers=[[Str('A')], [Str('B')]],
            rows=[[[Str('1')], [Str('2')]]],
            row_attrs=[Attr()],
        )
    ])


def test_read_figure_from_pandoc_json() -> None:
    payload = {
        'pandoc-api-version': [1, 23, 1],
        'meta': {},
        'blocks': [{
            't': 'Figure',
            'c': [
                ['fig-x', [], []],
                [None, [{'t': 'Plain', 'c': [{'t': 'Str', 'c': 'caption'}]}]],
                [{
                    't': 'Plain',
                    'c': [{
                        't': 'Image',
                        'c': [['', ['cls'], [['k', 'v']]], [{'t': 'Str', 'c': 'caption'}], ['img.png', '']],
                    }],
                }],
            ],
        }],
    }
    document = document_from_pandoc_json_payload(payload)
    assert document == Document(blocks=[
        Figure(
            image=Image(
                inlines=[Str('caption')],
                target='img.png',
                title='',
                attr=Attr(classes=['cls'], attributes=[('k', 'v')]),
            ),
            attr=Attr(identifier='fig-x'),
        )
    ])
