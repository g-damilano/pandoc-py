from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.ast import BlockQuote, BulletList, Code, CodeBlock, Document, Emph, HardBreak, Heading, Image, Link, Math, OrderedList, Paragraph, RawBlock, RawInline, SoftBreak, Space, Str, Strikeout, Strong, Subscript, Superscript, Table, ThematicBreak
from pandoc_py.readers.markdown import MarkdownScopeError, read_markdown
from pandoc_py.writers.markdown import write_markdown


def test_read_plain_paragraph_into_ast() -> None:
    document = read_markdown('alpha beta gamma\n')
    assert document == Document(blocks=[Paragraph(inlines=[Str('alpha'), Space(), Str('beta'), Space(), Str('gamma')])])


def test_read_softbreak_paragraph_into_ast() -> None:
    document = read_markdown('alpha beta\nsecond line\n')
    assert document == Document(
        blocks=[
            Paragraph(inlines=[Str('alpha'), Space(), Str('beta'), SoftBreak(), Str('second'), Space(), Str('line')])
        ]
    )


def test_read_heading_into_ast() -> None:
    document = read_markdown('# Heading\n')
    assert document == Document(blocks=[Heading(level=1, inlines=[Str('Heading')])])


def test_read_emphasis_into_ast() -> None:
    document = read_markdown('alpha *beta gamma* delta\n')
    assert document == Document(
        blocks=[
            Paragraph(
                inlines=[
                    Str('alpha'),
                    Space(),
                    Emph(inlines=[Str('beta'), Space(), Str('gamma')]),
                    Space(),
                    Str('delta'),
                ]
            )
        ]
    )


def test_read_strong_into_ast() -> None:
    document = read_markdown('alpha **beta gamma** delta\n')
    assert document == Document(
        blocks=[
            Paragraph(
                inlines=[
                    Str('alpha'),
                    Space(),
                    Strong(inlines=[Str('beta'), Space(), Str('gamma')]),
                    Space(),
                    Str('delta'),
                ]
            )
        ]
    )


def test_read_code_span_into_ast() -> None:
    document = read_markdown('alpha `beta gamma` delta\n')
    assert document == Document(
        blocks=[Paragraph(inlines=[Str('alpha'), Space(), Code('beta gamma'), Space(), Str('delta')])]
    )


def test_read_link_into_ast() -> None:
    document = read_markdown('alpha [beta gamma](https://example.com) delta\n')
    assert document == Document(
        blocks=[
            Paragraph(
                inlines=[
                    Str('alpha'),
                    Space(),
                    Link(inlines=[Str('beta'), Space(), Str('gamma')], target='https://example.com'),
                    Space(),
                    Str('delta'),
                ]
            )
        ]
    )


def test_read_autolink_into_ast() -> None:
    document = read_markdown('alpha <https://example.com> delta\n')
    assert document == Document(
        blocks=[
            Paragraph(
                inlines=[
                    Str('alpha'),
                    Space(),
                    Link(inlines=[Str('https://example.com')], target='https://example.com', autolink=True),
                    Space(),
                    Str('delta'),
                ]
            )
        ]
    )


def test_read_block_quote_into_ast() -> None:
    document = read_markdown('> alpha beta\n> gamma *delta*\n')
    assert document == Document(
        blocks=[
            BlockQuote(
                blocks=[
                    Paragraph(
                        inlines=[
                            Str('alpha'),
                            Space(),
                            Str('beta'),
                            SoftBreak(),
                            Str('gamma'),
                            Space(),
                            Emph(inlines=[Str('delta')]),
                        ]
                    )
                ]
            )
        ]
    )


def test_read_bullet_list_into_ast() -> None:
    document = read_markdown('- alpha beta\n- gamma *delta*\n')
    assert document == Document(
        blocks=[
            BulletList(
                items=[
                    [Paragraph(inlines=[Str('alpha'), Space(), Str('beta')])],
                    [Paragraph(inlines=[Str('gamma'), Space(), Emph(inlines=[Str('delta')])])],
                ]
            )
        ]
    )


def test_read_ordered_list_into_ast() -> None:
    document = read_markdown('3. alpha beta\n7. gamma `delta`\n')
    assert document == Document(
        blocks=[
            OrderedList(
                start=3,
                items=[
                    [Paragraph(inlines=[Str('alpha'), Space(), Str('beta')])],
                    [Paragraph(inlines=[Str('gamma'), Space(), Code('delta')])],
                ],
            )
        ]
    )


def test_write_heading_and_paragraph() -> None:
    document = Document(
        blocks=[Heading(level=2, inlines=[Str('Section')]), Paragraph(inlines=[Str('Alpha'), Space(), Str('beta')])]
    )
    assert write_markdown(document) == '## Section\n\nAlpha beta\n'


def test_write_emphasis_and_strong() -> None:
    document = Document(
        blocks=[
            Paragraph(inlines=[Str('alpha'), Space(), Emph(inlines=[Str('beta')]), Space(), Strong(inlines=[Str('gamma')])])
        ]
    )
    assert write_markdown(document) == 'alpha *beta* **gamma**\n'


def test_write_code_span() -> None:
    document = Document(blocks=[Paragraph(inlines=[Str('alpha'), Space(), Code('beta gamma'), Space(), Str('delta')])])
    assert write_markdown(document) == 'alpha `beta gamma` delta\n'


def test_write_link() -> None:
    document = Document(
        blocks=[
            Paragraph(
                inlines=[
                    Str('alpha'),
                    Space(),
                    Link(inlines=[Str('beta'), Space(), Str('gamma')], target='https://example.com'),
                    Space(),
                    Str('delta'),
                ]
            )
        ]
    )
    assert write_markdown(document) == 'alpha [beta gamma](https://example.com) delta\n'


def test_write_autolink() -> None:
    document = Document(
        blocks=[
            Paragraph(
                inlines=[
                    Str('alpha'),
                    Space(),
                    Link(inlines=[Str('https://example.com')], target='https://example.com', autolink=True),
                    Space(),
                    Str('delta'),
                ]
            )
        ]
    )
    assert write_markdown(document) == 'alpha <https://example.com> delta\n'


def test_write_block_quote() -> None:
    document = Document(
        blocks=[
            BlockQuote(blocks=[Paragraph(inlines=[Str('alpha'), Space(), Code('beta'), SoftBreak(), Str('gamma')])])
        ]
    )
    assert write_markdown(document) == '> alpha `beta` gamma\n'


def test_write_bullet_list() -> None:
    document = Document(
        blocks=[
            BulletList(items=[[Paragraph(inlines=[Str('alpha')])], [Paragraph(inlines=[Str('beta'), Space(), Code('gamma')])]])
        ]
    )
    assert write_markdown(document) == '-   alpha\n-   beta `gamma`\n'


def test_write_ordered_list() -> None:
    document = Document(
        blocks=[
            OrderedList(start=3, items=[[Paragraph(inlines=[Str('alpha')])], [Paragraph(inlines=[Str('beta'), Space(), Code('gamma')])]])
        ]
    )
    assert write_markdown(document) == '3.  alpha\n4.  beta `gamma`\n'


def test_softbreak_writes_as_space_for_markdown_parity() -> None:
    document = Document(blocks=[Paragraph(inlines=[Str('alpha'), Space(), Str('beta'), SoftBreak(), Str('second')])])
    assert write_markdown(document) == 'alpha beta second\n'


def test_read_nested_bullet_list_into_ast() -> None:
    document = read_markdown('- alpha\n  - beta\n')
    assert document == Document(
        blocks=[
            BulletList(items=[[Paragraph(inlines=[Str('alpha')]), BulletList(items=[[Paragraph(inlines=[Str('beta')])]])]])
        ]
    )


def test_reject_star_list_scope_boundary() -> None:
    try:
        read_markdown('* alpha\n')
    except MarkdownScopeError:
        pass
    else:
        raise AssertionError('Expected star-bullet lists to remain outside the current minimal scope.')


def test_read_nested_ordered_list_into_ast() -> None:
    document = read_markdown('1. alpha\n   1. beta\n')
    assert document == Document(
        blocks=[
            OrderedList(start=1, items=[[Paragraph(inlines=[Str('alpha')]), OrderedList(start=1, items=[[Paragraph(inlines=[Str('beta')])]])]])
        ]
    )


def test_reject_nested_block_quote_scope_boundary() -> None:
    try:
        read_markdown('> > beta\n')
    except MarkdownScopeError:
        pass
    else:
        raise AssertionError('Expected nested block quotes to remain outside the current minimal scope.')


def test_reject_list_inside_block_quote_scope_boundary() -> None:
    try:
        read_markdown('> - beta\n')
    except MarkdownScopeError:
        pass
    else:
        raise AssertionError('Expected lists inside block quotes to remain outside the current minimal scope.')


def test_reject_nested_star_scope_boundary() -> None:
    try:
        read_markdown('*alpha **beta** gamma*\n')
    except MarkdownScopeError:
        pass
    else:
        raise AssertionError('Expected nested star-delimited emphasis to remain outside current scope.')


def test_reject_unclosed_emphasis_scope_boundary() -> None:
    try:
        read_markdown('*emph\n')
    except MarkdownScopeError:
        pass
    else:
        raise AssertionError('Expected unclosed emphasis to remain outside the current minimal scope.')


def test_reject_multi_backtick_code_scope_boundary() -> None:
    try:
        read_markdown('``code``\n')
    except MarkdownScopeError:
        pass
    else:
        raise AssertionError('Expected multi-backtick code spans to remain outside the current minimal scope.')


def test_reject_unclosed_code_span_scope_boundary() -> None:
    try:
        read_markdown('`code\n')
    except MarkdownScopeError:
        pass
    else:
        raise AssertionError('Expected unclosed code spans to remain outside the current minimal scope.')


def test_reject_undefined_reference_link_scope_boundary() -> None:
    try:
        read_markdown('[alpha][beta]\n')
    except MarkdownScopeError:
        pass
    else:
        raise AssertionError('Expected undefined reference links to remain outside the current minimal scope.')


def test_read_link_title_scope_is_now_supported() -> None:
    document = read_markdown('[alpha](https://example.com \"title\")\n')
    assert document == Document(blocks=[Paragraph(inlines=[Link(inlines=[Str('alpha')], target='https://example.com', title='title')])])


def test_read_thematic_break_into_ast() -> None:
    document = read_markdown('---\n')
    assert document == Document(blocks=[ThematicBreak()])


def test_write_thematic_break() -> None:
    document = Document(blocks=[ThematicBreak()])
    assert write_markdown(document) == ('-' * 72) + '\n'


def test_reject_asterisk_thematic_break_scope_boundary() -> None:
    try:
        read_markdown('***\n')
    except MarkdownScopeError:
        pass
    else:
        raise AssertionError('Expected asterisk thematic breaks to remain outside the current minimal scope.')



def test_read_setext_heading_level_1_into_ast() -> None:
    document = read_markdown("""Alpha beta
==========
""")
    assert document == Document(blocks=[Heading(level=1, inlines=[Str('Alpha'), Space(), Str('beta')])])


def test_read_setext_heading_level_2_into_ast() -> None:
    document = read_markdown("""Gamma delta
----------
""")
    assert document == Document(blocks=[Heading(level=2, inlines=[Str('Gamma'), Space(), Str('delta')])])


def test_read_setext_heading_with_inline_code_into_ast() -> None:
    document = read_markdown("""Alpha `beta`
==========
""")
    assert document == Document(blocks=[Heading(level=1, inlines=[Str('Alpha'), Space(), Code('beta')])])


def test_read_fenced_code_block_with_info_into_ast() -> None:
    document = read_markdown("""``` python
print('x')
print('y')
```
""")
    assert document == Document(blocks=[CodeBlock(text="print('x')\nprint('y')", info='python')])


def test_write_fenced_code_block_with_info() -> None:
    document = Document(blocks=[CodeBlock(text="print('x')\nprint('y')", info='python')])
    assert write_markdown(document) == """``` python
print('x')
print('y')
```
"""


def test_write_fenced_code_block_without_info_normalizes_to_indented_code() -> None:
    document = Document(blocks=[CodeBlock(text='alpha\n\nbeta')])
    assert write_markdown(document) == """    alpha

    beta
"""


def test_reject_unclosed_fenced_code_block_scope_boundary() -> None:
    try:
        read_markdown("""``` python
print('x')
""")
    except MarkdownScopeError:
        pass
    else:
        raise AssertionError('Expected unclosed fenced code blocks to remain outside the current minimal scope.')


def test_read_indented_code_block_into_ast() -> None:
    document = read_markdown("""    alpha
    beta
""")
    assert document == Document(blocks=[CodeBlock(text='alpha\nbeta')])


def test_read_indented_code_block_with_literal_markdown_chars_into_ast() -> None:
    document = read_markdown("""    # not a heading
    - not a list
""")
    assert document == Document(blocks=[CodeBlock(text='# not a heading\n- not a list')])


def test_read_indented_code_block_in_document_context() -> None:
    document = read_markdown("""Alpha beta

    gamma
    delta
""")
    assert document == Document(blocks=[Paragraph(inlines=[Str('Alpha'), Space(), Str('beta')]), CodeBlock(text='gamma\ndelta')])


def test_read_email_autolink_into_ast() -> None:
    document = read_markdown('alpha <team@example.com> delta\n')
    assert document == Document(
        blocks=[
            Paragraph(
                inlines=[
                    Str('alpha'),
                    Space(),
                    Link(inlines=[Str('team@example.com')], target='mailto:team@example.com', autolink=True),
                    Space(),
                    Str('delta'),
                ]
            )
        ]
    )


def test_write_email_autolink() -> None:
    document = Document(
        blocks=[
            Paragraph(
                inlines=[
                    Str('alpha'),
                    Space(),
                    Link(inlines=[Str('team@example.com')], target='mailto:team@example.com', autolink=True),
                    Space(),
                    Str('delta'),
                ]
            )
        ]
    )
    assert write_markdown(document) == 'alpha <team@example.com> delta\n'


def test_read_backslash_hardbreak_into_ast() -> None:
    document = read_markdown("alpha\\\nbeta\n")
    assert document == Document(
        blocks=[Paragraph(inlines=[Str('alpha'), HardBreak(), Str('beta')])]
    )


def test_read_two_space_hardbreak_into_ast() -> None:
    document = read_markdown("alpha  \nbeta\n")
    assert document == Document(
        blocks=[Paragraph(inlines=[Str('alpha'), HardBreak(), Str('beta')])]
    )


def test_write_hardbreak_canonicalizes_to_backslash() -> None:
    document = Document(blocks=[Paragraph(inlines=[Str('alpha'), HardBreak(), Str('beta')])])
    assert write_markdown(document) == "alpha\\\nbeta\n"


def test_write_block_quote_with_hardbreak() -> None:
    document = Document(blocks=[BlockQuote(blocks=[Paragraph(inlines=[Str('alpha'), HardBreak(), Str('beta')])])])
    assert write_markdown(document) == "> alpha\\\n> beta\n"



def test_read_inline_image_into_ast() -> None:
    document = read_markdown('alpha ![beta gamma](https://example.com/img.png) delta\n')
    assert document == Document(
        blocks=[
            Paragraph(
                inlines=[
                    Str('alpha'),
                    Space(),
                    Image(inlines=[Str('beta'), Space(), Str('gamma')], target='https://example.com/img.png'),
                    Space(),
                    Str('delta'),
                ]
            )
        ]
    )


def test_write_inline_image() -> None:
    document = Document(
        blocks=[
            Paragraph(
                inlines=[
                    Str('alpha'),
                    Space(),
                    Image(inlines=[Str('beta'), Space(), Str('gamma')], target='https://example.com/img.png'),
                    Space(),
                    Str('delta'),
                ]
            )
        ]
    )
    assert write_markdown(document) == 'alpha ![beta gamma](https://example.com/img.png) delta\n'


def test_reject_nested_inline_syntax_in_image_label() -> None:
    try:
        read_markdown('![*beta*](https://example.com/img.png)\n')
    except MarkdownScopeError as exc:
        assert 'image labels' in str(exc)
    else:
        raise AssertionError('Expected MarkdownScopeError for nested inline syntax in image label')


def test_read_link_with_title_into_ast() -> None:
    document = read_markdown("""alpha [beta](https://example.com "Title") delta
""")
    assert document == Document(
        blocks=[
            Paragraph(
                inlines=[
                    Str('alpha'),
                    Space(),
                    Link(inlines=[Str('beta')], target='https://example.com', title='Title'),
                    Space(),
                    Str('delta'),
                ]
            )
        ]
    )


def test_read_image_with_title_into_ast() -> None:
    document = read_markdown("""alpha ![beta gamma](img.png "Image Title") delta
""")
    assert document == Document(
        blocks=[
            Paragraph(
                inlines=[
                    Str('alpha'),
                    Space(),
                    Image(inlines=[Str('beta'), Space(), Str('gamma')], target='img.png', title='Image Title'),
                    Space(),
                    Str('delta'),
                ]
            )
        ]
    )


def test_read_reference_link_variants_into_ast() -> None:
    document = read_markdown("""[beta][ref]

[ref][]

[ref]

[ref]: https://example.com "Ref Title"
""")
    explicit = Link(inlines=[Str('beta')], target='https://example.com', title='Ref Title')
    collapsed = Link(inlines=[Str('ref')], target='https://example.com', title='Ref Title')
    shortcut = Link(inlines=[Str('ref')], target='https://example.com', title='Ref Title')
    assert document == Document(
        blocks=[
            Paragraph(inlines=[explicit]),
            Paragraph(inlines=[collapsed]),
            Paragraph(inlines=[shortcut]),
        ]
    )


def test_read_reference_image_into_ast() -> None:
    document = read_markdown("""![alt text][img]

[img]: img.png "Img Title"
""")
    assert document == Document(
        blocks=[Paragraph(inlines=[Image(inlines=[Str('alt'), Space(), Str('text')], target='img.png', title='Img Title')])]
    )


def test_write_link_with_title() -> None:
    document = Document(blocks=[Paragraph(inlines=[Link(inlines=[Str('beta')], target='https://example.com', title='Title')])])
    assert write_markdown(document) == '[beta](https://example.com \"Title\")\n'


def test_write_image_with_title() -> None:
    document = Document(blocks=[Paragraph(inlines=[Image(inlines=[Str('alt')], target='img.png', title='Title')])])
    assert write_markdown(document) == '![alt](img.png \"Title\")\n'


def test_reject_undefined_reference_scope_boundary() -> None:
    try:
        read_markdown("""[beta][missing]
""")
    except MarkdownScopeError:
        pass
    else:
        raise AssertionError('Expected undefined reference labels to remain outside the current minimal scope.')


def test_read_inline_math_into_ast() -> None:
    document = read_markdown('alpha $x+y$ beta\n')
    assert document == Document(
        blocks=[Paragraph(inlines=[Str('alpha'), Space(), Math('x+y'), Space(), Str('beta')])]
    )


def test_read_display_math_block_into_ast() -> None:
    document = read_markdown('$$\nx+y\n$$\n')
    assert document == Document(blocks=[Paragraph(inlines=[Math('\nx+y\n', display=True)])])


def test_read_strikeout_into_ast() -> None:
    document = read_markdown('alpha ~~beta gamma~~ delta\n')
    assert document == Document(
        blocks=[Paragraph(inlines=[Str('alpha'), Space(), Strikeout(inlines=[Str('beta'), Space(), Str('gamma')]), Space(), Str('delta')])]
    )


def test_read_subscript_and_superscript_into_ast() -> None:
    document = read_markdown('H~2~O 2^10^\n')
    assert document == Document(
        blocks=[Paragraph(inlines=[Str('H'), Subscript(inlines=[Str('2')]), Str('O'), Space(), Str('2'), Superscript(inlines=[Str('10')])])]
    )


def test_write_inline_math_and_display_math() -> None:
    document = Document(blocks=[
        Paragraph(inlines=[Str('alpha'), Space(), Math('x+y'), Space(), Str('beta')]),
        Paragraph(inlines=[Math('\nx+y\n', display=True)]),
    ])
    assert write_markdown(document) == 'alpha $x+y$ beta\n\n$$\nx+y\n$$\n'


def test_write_strikeout_subscript_and_superscript() -> None:
    document = Document(blocks=[Paragraph(inlines=[Strikeout(inlines=[Str('gone')]), Space(), Str('H'), Subscript(inlines=[Str('2')]), Str('O'), Space(), Str('2'), Superscript(inlines=[Str('10')])])])
    assert write_markdown(document) == '~~gone~~ H~2~O 2^10^\n'


def test_read_inline_raw_html_comment_into_ast() -> None:
    document = read_markdown('alpha <!-- note --> gamma\n')
    assert document == Document(
        blocks=[Paragraph(inlines=[Str('alpha'), Space(), RawInline(format='html', text='<!-- note -->'), Space(), Str('gamma')])]
    )


def test_read_inline_raw_html_tag_into_ast() -> None:
    document = read_markdown('alpha <br /> gamma\n')
    assert document == Document(
        blocks=[Paragraph(inlines=[Str('alpha'), Space(), RawInline(format='html', text='<br />'), Space(), Str('gamma')])]
    )


def test_read_inline_raw_html_attribute_syntax_into_ast() -> None:
    document = read_markdown('alpha `<custom />`{=html} gamma\n')
    assert document == Document(
        blocks=[Paragraph(inlines=[Str('alpha'), Space(), RawInline(format='html', text='<custom />'), Space(), Str('gamma')])]
    )


def test_read_raw_html_comment_block_into_ast() -> None:
    document = read_markdown('<!-- note -->\n')
    assert document == Document(blocks=[RawBlock(format='html', text='<!-- note -->')])


def test_read_raw_html_hr_block_into_ast() -> None:
    document = read_markdown('<hr />\n')
    assert document == Document(blocks=[RawBlock(format='html', text='<hr />')])


def test_read_raw_html_named_block_into_ast() -> None:
    document = read_markdown('<script>\nalert(1)\n</script>\n')
    assert document == Document(blocks=[RawBlock(format='html', text='<script>\nalert(1)\n</script>')])


def test_read_raw_html_fence_into_ast() -> None:
    document = read_markdown('```{=html}\n<!-- note -->\n```\n')
    assert document == Document(blocks=[RawBlock(format='html', text='<!-- note -->')])


def test_write_raw_html_inline_and_block() -> None:
    document = Document(
        blocks=[
            Paragraph(inlines=[Str('alpha'), Space(), RawInline(format='html', text='<!-- note -->'), Space(), Str('gamma')]),
            RawBlock(format='html', text='<!-- note -->'),
        ]
    )
    assert write_markdown(document) == 'alpha `<!-- note -->`{=html} gamma\n\n```{=html}\n<!-- note -->\n```\n'


def test_read_simple_pipe_table_into_ast() -> None:
    document = read_markdown('| A | B |\n|---|---|\n| 1 | 2 |\n')
    assert document == Document(blocks=[Table(caption=[], aligns=['AlignDefault', 'AlignDefault'], headers=[[Str('A')], [Str('B')]], rows=[[[Str('1')], [Str('2')]]])])


def test_read_aligned_pipe_table_with_inline_cells_into_ast() -> None:
    document = read_markdown('| Left | Right |\n|:-----|------:|\n| *a* | [b](https://e.com) |\n')
    assert document == Document(blocks=[Table(caption=[], aligns=['AlignLeft', 'AlignRight'], headers=[[Str('Left')], [Str('Right')]], rows=[[[Emph(inlines=[Str('a')])], [Link(inlines=[Str('b')], target='https://e.com')]]])])


def test_read_pipe_table_with_caption_after_into_ast() -> None:
    document = read_markdown('| A | B |\n|---|---|\n| 1 | 2 |\n\n: Cap')
    assert document == Document(blocks=[Table(caption=[Str('Cap')], aligns=['AlignDefault', 'AlignDefault'], headers=[[Str('A')], [Str('B')]], rows=[[[Str('1')], [Str('2')]]])])


def test_read_pipe_table_with_caption_before_into_ast() -> None:
    document = read_markdown(': Cap\n\n| A | B |\n|---|---|\n| 1 | 2 |\n')
    assert document == Document(blocks=[Table(caption=[Str('Cap')], aligns=['AlignDefault', 'AlignDefault'], headers=[[Str('A')], [Str('B')]], rows=[[[Str('1')], [Str('2')]]])])


def test_write_simple_table_to_markdown() -> None:
    document = Document(blocks=[Table(caption=[], aligns=['AlignDefault', 'AlignDefault'], headers=[[Str('A')], [Str('B')]], rows=[[[Str('1')], [Str('2')]], [[Str('3')], [Str('4')]]])])
    assert write_markdown(document) == '  A   B\n  --- ---\n  1   2\n  3   4\n'


def test_write_aligned_table_with_caption_to_markdown() -> None:
    document = Document(blocks=[Table(caption=[Str('Cap')], aligns=['AlignLeft', 'AlignRight'], headers=[[Str('Left')], [Str('Right')]], rows=[[[Str('alpha')], [Str('2')]]])])
    assert write_markdown(document) == '  Left      Right\n  ------- -------\n  alpha         2\n\n  : Cap\n'
