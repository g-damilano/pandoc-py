from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.ast import DefinitionList, Document, Note, Paragraph, SoftBreak, Space, Str
from pandoc_py.readers.markdown import read_markdown
from pandoc_py.writers.markdown import write_markdown


def test_read_definition_list_into_ast() -> None:
    document = read_markdown('Term 1\n: Definition 1\n\nTerm 2\n: Definition 2\n')
    assert document == Document(
        blocks=[
            DefinitionList(
                items=[
                    ([Str('Term'), Space(), Str('1')], [[Paragraph(inlines=[Str('Definition'), Space(), Str('1')])]]),
                    ([Str('Term'), Space(), Str('2')], [[Paragraph(inlines=[Str('Definition'), Space(), Str('2')])]]),
                ]
            )
        ]
    )


def test_read_definition_list_continuation_into_ast() -> None:
    document = read_markdown('Term\n: First line\n    second line\n')
    assert document == Document(
        blocks=[
            DefinitionList(
                items=[
                    ([Str('Term')], [[Paragraph(inlines=[Str('First'), Space(), Str('line'), SoftBreak(), Str('second'), Space(), Str('line')])]])
                ]
            )
        ]
    )


def test_read_reference_footnote_into_ast() -> None:
    document = read_markdown('Alpha[^1].\n\n[^1]: Note text\n')
    assert document == Document(
        blocks=[
            Paragraph(inlines=[Str('Alpha'), Note(blocks=[Paragraph(inlines=[Str('Note'), Space(), Str('text')])]), Str('.')])
        ]
    )


def test_write_inline_note_normalizes_to_reference_footnote() -> None:
    document = Document(
        blocks=[
            Paragraph(inlines=[Str('Alpha'), Note(blocks=[Paragraph(inlines=[Str('Note'), Space(), Str('text')])]), Str('.')])
        ]
    )
    assert write_markdown(document) == 'Alpha[^1].\n\n[^1]: Note text\n'


def test_write_definition_list() -> None:
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
    assert write_markdown(document) == 'Term\n:   Definition\n\nOther\n:   Another definition\n'
