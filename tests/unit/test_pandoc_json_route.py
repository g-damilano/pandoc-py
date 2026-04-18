from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.ast import BlockQuote, BulletList, Code, CodeBlock, Document, Emph, HardBreak, Heading, Image, Link, Math, OrderedList, Paragraph, RawBlock, RawInline, SoftBreak, Space, Str, Strikeout, Strong, Subscript, Superscript, Table, ThematicBreak
from pandoc_py.writers.pandoc_json import document_to_pandoc_json_payload


def test_write_paragraph_to_pandoc_json_payload() -> None:
    document = Document(blocks=[Paragraph(inlines=[Str('alpha'), Space(), Str('beta')])])
    assert document_to_pandoc_json_payload(document) == {
        'pandoc-api-version': [1, 23, 1],
        'meta': {},
        'blocks': [{'t': 'Para', 'c': [{'t': 'Str', 'c': 'alpha'}, {'t': 'Space'}, {'t': 'Str', 'c': 'beta'}]}],
    }


def test_write_heading_to_pandoc_json_payload() -> None:
    document = Document(blocks=[Heading(level=1, inlines=[Str('Alpha'), Space(), Emph(inlines=[Str('beta')]), Space(), Strong(inlines=[Str('gamma')])])])
    assert document_to_pandoc_json_payload(document) == {
        'pandoc-api-version': [1, 23, 1],
        'meta': {},
        'blocks': [
            {'t': 'Header', 'c': [1, ['alpha-beta-gamma', [], []], [
                {'t': 'Str', 'c': 'Alpha'},
                {'t': 'Space'},
                {'t': 'Emph', 'c': [{'t': 'Str', 'c': 'beta'}]},
                {'t': 'Space'},
                {'t': 'Strong', 'c': [{'t': 'Str', 'c': 'gamma'}]},
            ]]}
        ],
    }


def test_heading_identifiers_are_stably_disambiguated() -> None:
    document = Document(blocks=[Heading(level=1, inlines=[Str('Repeat')]), Heading(level=2, inlines=[Str('Repeat')])])
    payload = document_to_pandoc_json_payload(document)
    assert payload['blocks'][0]['c'][1][0] == 'repeat'
    assert payload['blocks'][1]['c'][1][0] == 'repeat-2'


def test_write_softbreak_to_pandoc_json_payload() -> None:
    document = Document(blocks=[Paragraph(inlines=[Str('alpha'), SoftBreak(), Str('beta')])])
    assert document_to_pandoc_json_payload(document)['blocks'][0]['c'] == [{'t': 'Str', 'c': 'alpha'}, {'t': 'SoftBreak'}, {'t': 'Str', 'c': 'beta'}]


def test_write_code_span_to_pandoc_json_payload() -> None:
    document = Document(blocks=[Paragraph(inlines=[Str('alpha'), Space(), Code('beta gamma')])])
    assert document_to_pandoc_json_payload(document)['blocks'][0]['c'] == [
        {'t': 'Str', 'c': 'alpha'},
        {'t': 'Space'},
        {'t': 'Code', 'c': [['', [], []], 'beta gamma']},
    ]


def test_write_link_to_pandoc_json_payload() -> None:
    document = Document(blocks=[Paragraph(inlines=[Str('alpha'), Space(), Link(inlines=[Str('beta'), Space(), Str('gamma')], target='https://example.com')])])
    assert document_to_pandoc_json_payload(document)['blocks'][0]['c'] == [
        {'t': 'Str', 'c': 'alpha'},
        {'t': 'Space'},
        {'t': 'Link', 'c': [['', [], []], [{'t': 'Str', 'c': 'beta'}, {'t': 'Space'}, {'t': 'Str', 'c': 'gamma'}], ['https://example.com', '']]},
    ]


def test_write_autolink_to_pandoc_json_payload() -> None:
    document = Document(blocks=[Paragraph(inlines=[Str('alpha'), Space(), Link(inlines=[Str('https://example.com')], target='https://example.com', autolink=True)])])
    assert document_to_pandoc_json_payload(document)['blocks'][0]['c'] == [
        {'t': 'Str', 'c': 'alpha'},
        {'t': 'Space'},
        {'t': 'Link', 'c': [['', ['uri'], []], [{'t': 'Str', 'c': 'https://example.com'}], ['https://example.com', '']]},
    ]


def test_write_block_quote_to_pandoc_json_payload() -> None:
    document = Document(blocks=[BlockQuote(blocks=[Paragraph(inlines=[Str('alpha'), Space(), Code('beta'), SoftBreak(), Str('gamma')])])])
    assert document_to_pandoc_json_payload(document)['blocks'][0] == {
        't': 'BlockQuote',
        'c': [
            {'t': 'Para', 'c': [
                {'t': 'Str', 'c': 'alpha'},
                {'t': 'Space'},
                {'t': 'Code', 'c': [['', [], []], 'beta']},
                {'t': 'SoftBreak'},
                {'t': 'Str', 'c': 'gamma'},
            ]}
        ],
    }


def test_write_bullet_list_to_pandoc_json_payload() -> None:
    document = Document(blocks=[BulletList(items=[[Paragraph(inlines=[Str('alpha')])], [Paragraph(inlines=[Str('beta'), Space(), Code('gamma')])]])])
    assert document_to_pandoc_json_payload(document)['blocks'][0] == {
        't': 'BulletList',
        'c': [
            [{'t': 'Plain', 'c': [{'t': 'Str', 'c': 'alpha'}]}],
            [{'t': 'Plain', 'c': [{'t': 'Str', 'c': 'beta'}, {'t': 'Space'}, {'t': 'Code', 'c': [['', [], []], 'gamma']}]}],
        ],
    }


def test_write_ordered_list_to_pandoc_json_payload() -> None:
    document = Document(blocks=[OrderedList(start=3, items=[[Paragraph(inlines=[Str('alpha')])], [Paragraph(inlines=[Str('beta'), Space(), Code('gamma')])]])])
    assert document_to_pandoc_json_payload(document)['blocks'][0] == {
        't': 'OrderedList',
        'c': [
            [3, {'t': 'Decimal'}, {'t': 'Period'}],
            [
                [{'t': 'Plain', 'c': [{'t': 'Str', 'c': 'alpha'}]}],
                [{'t': 'Plain', 'c': [{'t': 'Str', 'c': 'beta'}, {'t': 'Space'}, {'t': 'Code', 'c': [['', [], []], 'gamma']}]}],
            ],
        ],
    }


def test_cli_markdown_to_json_matches_pandoc_for_supported_slice() -> None:
    fixture = (
        '# Alpha *beta* **gamma** [delta](https://example.com)\n\n'
        '> quote line one\n> quote line two\n\n'
        '- first line\n- second `code`\n\n'
        '3. numbered one\n7. numbered two\n\n'
        'alpha `code span` beta\n'
    )
    env = dict(os.environ)
    env['PYTHONPATH'] = str(SRC_ROOT) + (os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    py = subprocess.run(
        [sys.executable, str(REPO_ROOT / 'scripts' / 'run_python_cli.py'), '-', '--from', 'markdown', '--to', 'json'],
        input=fixture,
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
        env=env,
        check=False,
    )
    oracle = subprocess.run(
        ['/usr/bin/pandoc', '-', '-f', 'markdown', '-t', 'json'],
        input=fixture,
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
        check=False,
    )
    assert py.returncode == 0, py.stderr
    assert oracle.returncode == 0, oracle.stderr
    assert json.loads(py.stdout) == json.loads(oracle.stdout)


def test_write_thematic_break_to_pandoc_json_payload() -> None:
    document = Document(blocks=[ThematicBreak()])
    assert document_to_pandoc_json_payload(document)['blocks'][0] == {'t': 'HorizontalRule'}



def test_setext_headings_flow_to_same_json_heading_payload() -> None:
    from pandoc_py.readers.markdown import read_markdown

    document = read_markdown("""Alpha beta
==========

Gamma delta
----------
""")
    assert document_to_pandoc_json_payload(document)['blocks'] == [
        {'t': 'Header', 'c': [1, ['alpha-beta', [], []], [{'t': 'Str', 'c': 'Alpha'}, {'t': 'Space'}, {'t': 'Str', 'c': 'beta'}]]},
        {'t': 'Header', 'c': [2, ['gamma-delta', [], []], [{'t': 'Str', 'c': 'Gamma'}, {'t': 'Space'}, {'t': 'Str', 'c': 'delta'}]]},
    ]


def test_write_code_block_to_pandoc_json_payload() -> None:
    document = Document(blocks=[CodeBlock(text="print('x')\nprint('y')", info='python')])
    assert document_to_pandoc_json_payload(document)['blocks'][0] == {
        't': 'CodeBlock',
        'c': [['', ['python'], []], "print('x')\nprint('y')"],
    }


def test_indented_code_block_flows_to_same_json_codeblock_payload() -> None:
    from pandoc_py.readers.markdown import read_markdown

    document = read_markdown("""    alpha
    beta
""")
    assert document_to_pandoc_json_payload(document)['blocks'][0] == {
        't': 'CodeBlock',
        'c': [['', [], []], 'alpha\nbeta'],
    }


def test_write_email_autolink_to_pandoc_json_payload() -> None:
    document = Document(blocks=[Paragraph(inlines=[Str('alpha'), Space(), Link(inlines=[Str('team@example.com')], target='mailto:team@example.com', autolink=True)])])
    assert document_to_pandoc_json_payload(document)['blocks'][0]['c'] == [
        {'t': 'Str', 'c': 'alpha'},
        {'t': 'Space'},
        {'t': 'Link', 'c': [['', ['email'], []], [{'t': 'Str', 'c': 'team@example.com'}], ['mailto:team@example.com', '']]},
    ]


def test_write_hardbreak_to_pandoc_json_payload() -> None:
    document = Document(blocks=[Paragraph(inlines=[Str('alpha'), HardBreak(), Str('beta')])])
    assert document_to_pandoc_json_payload(document)['blocks'][0]['c'] == [
        {'t': 'Str', 'c': 'alpha'},
        {'t': 'LineBreak'},
        {'t': 'Str', 'c': 'beta'},
    ]



def test_write_image_to_pandoc_json_payload() -> None:
    document = Document(blocks=[Paragraph(inlines=[Str('alpha'), Space(), Image(inlines=[Str('beta'), Space(), Str('gamma')], target='https://example.com/img.png')])])
    assert document_to_pandoc_json_payload(document)['blocks'][0]['c'] == [
        {'t': 'Str', 'c': 'alpha'},
        {'t': 'Space'},
        {'t': 'Image', 'c': [['', [], []], [{'t': 'Str', 'c': 'beta'}, {'t': 'Space'}, {'t': 'Str', 'c': 'gamma'}], ['https://example.com/img.png', '']]},
    ]



def test_write_link_with_title_to_pandoc_json_payload() -> None:
    document = Document(blocks=[Paragraph(inlines=[Link(inlines=[Str('beta')], target='https://example.com', title='Title')])])
    assert document_to_pandoc_json_payload(document)['blocks'][0]['c'] == [
        {'t': 'Link', 'c': [['', [], []], [{'t': 'Str', 'c': 'beta'}], ['https://example.com', 'Title']]},
    ]


def test_write_image_with_title_to_pandoc_json_payload() -> None:
    document = Document(blocks=[Paragraph(inlines=[Image(inlines=[Str('alt')], target='img.png', title='Title')])])
    payload = document_to_pandoc_json_payload(document)['blocks'][0]
    assert payload['t'] == 'Figure'
    assert payload['c'][2][0]['c'][0]['c'][2] == ['img.png', 'Title']

def test_reference_links_flow_to_same_json_link_payload() -> None:
    from pandoc_py.readers.markdown import read_markdown

    document = read_markdown("""[beta][ref]

[ref]: https://example.com "Title"
""")
    assert document_to_pandoc_json_payload(document)['blocks'][0]['c'] == [
        {'t': 'Link', 'c': [['', [], []], [{'t': 'Str', 'c': 'beta'}], ['https://example.com', 'Title']]},
    ]


def test_reference_images_flow_to_same_json_image_payload() -> None:
    from pandoc_py.readers.markdown import read_markdown

    document = read_markdown("""![alt][img]

[img]: img.png "Title"
""")
    payload = document_to_pandoc_json_payload(document)['blocks'][0]
    assert payload['t'] == 'Figure'
    assert payload['c'][2][0]['c'][0]['c'][2] == ['img.png', 'Title']

def test_write_inline_math_to_pandoc_json_payload() -> None:
    document = Document(blocks=[Paragraph(inlines=[Str('alpha'), Space(), Math('x+y'), Space(), Str('beta')])])
    assert document_to_pandoc_json_payload(document)['blocks'][0]['c'] == [
        {'t': 'Str', 'c': 'alpha'},
        {'t': 'Space'},
        {'t': 'Math', 'c': [{'t': 'InlineMath'}, 'x+y']},
        {'t': 'Space'},
        {'t': 'Str', 'c': 'beta'},
    ]


def test_write_display_math_to_pandoc_json_payload() -> None:
    document = Document(blocks=[Paragraph(inlines=[Math('\nx+y\n', display=True)])])
    assert document_to_pandoc_json_payload(document)['blocks'][0]['c'] == [
        {'t': 'Math', 'c': [{'t': 'DisplayMath'}, '\nx+y\n']},
    ]


def test_write_strikeout_to_pandoc_json_payload() -> None:
    document = Document(blocks=[Paragraph(inlines=[Strikeout(inlines=[Str('gone')])])])
    assert document_to_pandoc_json_payload(document)['blocks'][0]['c'] == [
        {'t': 'Strikeout', 'c': [{'t': 'Str', 'c': 'gone'}]},
    ]


def test_write_subscript_and_superscript_to_pandoc_json_payload() -> None:
    document = Document(blocks=[Paragraph(inlines=[Str('H'), Subscript(inlines=[Str('2')]), Str('O'), Space(), Str('2'), Superscript(inlines=[Str('10')])])])
    assert document_to_pandoc_json_payload(document)['blocks'][0]['c'] == [
        {'t': 'Str', 'c': 'H'},
        {'t': 'Subscript', 'c': [{'t': 'Str', 'c': '2'}]},
        {'t': 'Str', 'c': 'O'},
        {'t': 'Space'},
        {'t': 'Str', 'c': '2'},
        {'t': 'Superscript', 'c': [{'t': 'Str', 'c': '10'}]},
    ]


def test_write_raw_html_inline_to_pandoc_json_payload() -> None:
    document = Document(blocks=[Paragraph(inlines=[Str('alpha'), Space(), RawInline(format='html', text='<!-- note -->'), Space(), Str('gamma')])])
    assert document_to_pandoc_json_payload(document)['blocks'][0]['c'] == [
        {'t': 'Str', 'c': 'alpha'},
        {'t': 'Space'},
        {'t': 'RawInline', 'c': ['html', '<!-- note -->']},
        {'t': 'Space'},
        {'t': 'Str', 'c': 'gamma'},
    ]


def test_write_raw_html_block_to_pandoc_json_payload() -> None:
    document = Document(blocks=[RawBlock(format='html', text='<!-- note -->')])
    assert document_to_pandoc_json_payload(document)['blocks'][0] == {
        't': 'RawBlock',
        'c': ['html', '<!-- note -->'],
    }


def test_heading_slug_ignores_raw_html_inline() -> None:
    document = Document(blocks=[Heading(level=1, inlines=[Str('alpha'), Space(), RawInline(format='html', text='<!-- note -->'), Space(), Str('beta')])])
    payload = document_to_pandoc_json_payload(document)
    assert payload['blocks'][0]['c'][1] == ['alpha-beta', [], []]


def test_read_raw_html_attribute_forms_flow_to_same_json_payload() -> None:
    from pandoc_py.readers.markdown import read_markdown

    inline_document = read_markdown('alpha `<custom />`{=html} gamma\n')
    assert inline_document.blocks[0].inlines[2] == RawInline(format='html', text='<custom />')

    block_document = read_markdown('```{=html}\n<!-- note -->\n```\n')
    assert document_to_pandoc_json_payload(block_document)['blocks'][0] == {
        't': 'RawBlock',
        'c': ['html', '<!-- note -->'],
    }


def test_write_simple_table_to_pandoc_json_payload() -> None:
    document = Document(blocks=[Table(caption=[], aligns=['AlignDefault', 'AlignDefault'], headers=[[Str('A')], [Str('B')]], rows=[[[Str('1')], [Str('2')]]])])
    table = document_to_pandoc_json_payload(document)['blocks'][0]
    assert table['t'] == 'Table'
    assert table['c'][2] == [[{'t': 'AlignDefault'}, {'t': 'ColWidthDefault'}], [{'t': 'AlignDefault'}, {'t': 'ColWidthDefault'}]]
    assert table['c'][3][1][0][1][0][4] == [{'t': 'Plain', 'c': [{'t': 'Str', 'c': 'A'}]}]
    assert table['c'][4][0][3][0][1][0][4] == [{'t': 'Plain', 'c': [{'t': 'Str', 'c': '1'}]}]


def test_write_aligned_table_with_caption_to_pandoc_json_payload() -> None:
    document = Document(blocks=[Table(caption=[Str('Cap')], aligns=['AlignLeft', 'AlignRight'], headers=[[Str('Left')], [Str('Right')]], rows=[[[Emph(inlines=[Str('a')])], [Link(inlines=[Str('b')], target='https://e.com')]]])])
    table = document_to_pandoc_json_payload(document)['blocks'][0]
    assert table['c'][1] == [None, [{'t': 'Plain', 'c': [{'t': 'Str', 'c': 'Cap'}]}]]
    assert table['c'][2] == [[{'t': 'AlignLeft'}, {'t': 'ColWidthDefault'}], [{'t': 'AlignRight'}, {'t': 'ColWidthDefault'}]]
    assert table['c'][4][0][3][0][1][0][4] == [{'t': 'Plain', 'c': [{'t': 'Emph', 'c': [{'t': 'Str', 'c': 'a'}]}]}]


def test_read_pipe_table_flows_to_same_json_payload_as_writer() -> None:
    from pandoc_py.readers.markdown import read_markdown

    document = read_markdown('| A | B |\n|---|---|\n| 1 | 2 |\n\n: Cap')
    table = document_to_pandoc_json_payload(document)['blocks'][0]
    assert table['t'] == 'Table'
    assert table['c'][1] == [None, [{'t': 'Plain', 'c': [{'t': 'Str', 'c': 'Cap'}]}]]
