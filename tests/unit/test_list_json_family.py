from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.ast import BulletList, Document, OrderedList, Paragraph, SoftBreak, Space, Str
from pandoc_py.writers.pandoc_json import document_to_pandoc_json_payload


def test_task_bullet_list_json_payload_uses_checkbox_glyphs() -> None:
    document = Document(
        blocks=[
            BulletList(
                items=[
                    [Paragraph(inlines=[Str('☐'), Space(), Str('one')])],
                    [Paragraph(inlines=[Str('☒'), Space(), Str('two')])],
                ]
            )
        ]
    )
    assert document_to_pandoc_json_payload(document)['blocks'][0] == {
        't': 'BulletList',
        'c': [
            [{'t': 'Plain', 'c': [{'t': 'Str', 'c': '☐'}, {'t': 'Space'}, {'t': 'Str', 'c': 'one'}]}],
            [{'t': 'Plain', 'c': [{'t': 'Str', 'c': '☒'}, {'t': 'Space'}, {'t': 'Str', 'c': 'two'}]}],
        ],
    }


def test_compact_nested_ordered_list_keeps_plain_first_blocks_in_json_payload() -> None:
    document = Document(
        blocks=[
            OrderedList(
                start=1,
                items=[
                    [
                        Paragraph(inlines=[Str('outer')]),
                        BulletList(items=[[Paragraph(inlines=[Str('inner'), Space(), Str('a')])]]),
                    ],
                    [Paragraph(inlines=[Str('done')])],
                ],
            )
        ]
    )
    assert document_to_pandoc_json_payload(document)['blocks'][0] == {
        't': 'OrderedList',
        'c': [
            [1, {'t': 'Decimal'}, {'t': 'Period'}],
            [
                [
                    {'t': 'Plain', 'c': [{'t': 'Str', 'c': 'outer'}]},
                    {'t': 'BulletList', 'c': [[{'t': 'Plain', 'c': [{'t': 'Str', 'c': 'inner'}, {'t': 'Space'}, {'t': 'Str', 'c': 'a'}]}]]},
                ],
                [
                    {'t': 'Plain', 'c': [{'t': 'Str', 'c': 'done'}]},
                ],
            ],
        ],
    }


def test_loose_ordered_list_uses_para_for_all_sibling_items_in_json_payload() -> None:
    document = Document(
        blocks=[
            OrderedList(
                start=1,
                items=[
                    [
                        Paragraph(inlines=[Str('first'), SoftBreak(), Str('continued')]),
                        OrderedList(start=1, items=[[Paragraph(inlines=[Str('inner')])]]),
                    ],
                    [Paragraph(inlines=[Str('second')])],
                ],
            )
        ]
    )
    assert document_to_pandoc_json_payload(document)['blocks'][0] == {
        't': 'OrderedList',
        'c': [
            [1, {'t': 'Decimal'}, {'t': 'Period'}],
            [
                [
                    {'t': 'Para', 'c': [{'t': 'Str', 'c': 'first'}, {'t': 'SoftBreak'}, {'t': 'Str', 'c': 'continued'}]},
                    {'t': 'OrderedList', 'c': [[1, {'t': 'Decimal'}, {'t': 'Period'}], [[{'t': 'Plain', 'c': [{'t': 'Str', 'c': 'inner'}]}]]]},
                ],
                [
                    {'t': 'Para', 'c': [{'t': 'Str', 'c': 'second'}]},
                ],
            ],
        ],
    }
