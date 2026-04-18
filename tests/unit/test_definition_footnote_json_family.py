from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.ast import DefinitionList, Document, Note, Paragraph, SoftBreak, Space, Str
from pandoc_py.writers.pandoc_json import document_to_pandoc_json_payload


def test_write_definition_list_to_pandoc_json_payload() -> None:
    document = Document(
        blocks=[
            DefinitionList(
                items=[
                    ([Str('Term')], [[Paragraph(inlines=[Str('Definition')])]]),
                    ([Str('Other')], [[Paragraph(inlines=[Str('Another'), Space(), Str('definition')])]]),
                ]
            )
        ]
    )
    assert document_to_pandoc_json_payload(document)['blocks'][0] == {
        't': 'DefinitionList',
        'c': [
            [[{'t': 'Str', 'c': 'Term'}], [[{'t': 'Plain', 'c': [{'t': 'Str', 'c': 'Definition'}]}]]],
            [[{'t': 'Str', 'c': 'Other'}], [[{'t': 'Plain', 'c': [{'t': 'Str', 'c': 'Another'}, {'t': 'Space'}, {'t': 'Str', 'c': 'definition'}]}]]],
        ],
    }


def test_write_note_to_pandoc_json_payload() -> None:
    document = Document(
        blocks=[
            Paragraph(inlines=[Str('Alpha'), Note(blocks=[Paragraph(inlines=[Str('Note'), Space(), Str('text')])]), Str('.')])
        ]
    )
    assert document_to_pandoc_json_payload(document)['blocks'][0]['c'] == [
        {'t': 'Str', 'c': 'Alpha'},
        {'t': 'Note', 'c': [{'t': 'Para', 'c': [{'t': 'Str', 'c': 'Note'}, {'t': 'Space'}, {'t': 'Str', 'c': 'text'}]}]},
        {'t': 'Str', 'c': '.'},
    ]


def test_definition_list_continuation_uses_softbreak_in_json_payload() -> None:
    document = Document(
        blocks=[
            DefinitionList(
                items=[
                    ([Str('Term')], [[Paragraph(inlines=[Str('First'), Space(), Str('line'), SoftBreak(), Str('second'), Space(), Str('line')])]])
                ]
            )
        ]
    )
    assert document_to_pandoc_json_payload(document)['blocks'][0] == {
        't': 'DefinitionList',
        'c': [
            [[{'t': 'Str', 'c': 'Term'}], [[{'t': 'Plain', 'c': [
                {'t': 'Str', 'c': 'First'},
                {'t': 'Space'},
                {'t': 'Str', 'c': 'line'},
                {'t': 'SoftBreak'},
                {'t': 'Str', 'c': 'second'},
                {'t': 'Space'},
                {'t': 'Str', 'c': 'line'},
            ]}]]],
        ],
    }
