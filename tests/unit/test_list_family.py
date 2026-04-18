from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.ast import BulletList, Document, OrderedList, Paragraph, SoftBreak, Space, Str
from pandoc_py.readers.markdown import read_markdown
from pandoc_py.writers.markdown import write_markdown


def test_read_task_bullet_list_into_ast() -> None:
    document = read_markdown('- [ ] one\n- [x] two\n')
    assert document == Document(
        blocks=[
            BulletList(
                items=[
                    [[Paragraph(inlines=[Str('☐'), Space(), Str('one')])][0]],
                    [[Paragraph(inlines=[Str('☒'), Space(), Str('two')])][0]],
                ]
            )
        ]
    )


def test_read_loose_bullet_list_with_nested_list_into_ast() -> None:
    document = read_markdown('- alpha\n\n  beta\n\n  - nested one\n  - nested two\n- gamma\n')
    assert document == Document(
        blocks=[
            BulletList(
                items=[
                    [
                        Paragraph(inlines=[Str('alpha')]),
                        Paragraph(inlines=[Str('beta')]),
                        BulletList(
                            items=[
                                [Paragraph(inlines=[Str('nested'), Space(), Str('one')])],
                                [Paragraph(inlines=[Str('nested'), Space(), Str('two')])],
                            ]
                        ),
                    ],
                    [Paragraph(inlines=[Str('gamma')])],
                ]
            )
        ]
    )


def test_read_ordered_list_continuation_and_nested_list_into_ast() -> None:
    document = read_markdown('1. first\n   continued\n\n   1. inner\n2. second\n')
    assert document == Document(
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


def test_write_compact_ordered_list_with_nested_bullet_list() -> None:
    document = Document(
        blocks=[
            OrderedList(
                start=1,
                items=[
                    [
                        Paragraph(inlines=[Str('outer')]),
                        BulletList(
                            items=[
                                [Paragraph(inlines=[Str('inner'), Space(), Str('a')])],
                                [Paragraph(inlines=[Str('inner'), Space(), Str('b')])],
                            ]
                        ),
                    ],
                    [Paragraph(inlines=[Str('done')])],
                ],
            )
        ]
    )
    assert write_markdown(document) == '1.  outer\n    -   inner a\n    -   inner b\n2.  done\n'


def test_write_loose_ordered_list_with_continuation_and_nested_ordered_list() -> None:
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
    assert write_markdown(document) == '1.  first continued\n\n    1.  inner\n\n2.  second\n'
