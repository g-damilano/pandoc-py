from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pandoc_py.app import convert_text
from pandoc_py.ast import Document, LineBlock, Null, Paragraph, Quoted, SmallCaps, Space, Str, Underline
from pandoc_py.writers.html import write_html
from pandoc_py.writers.markdown import write_markdown


def test_markdown_writer_supports_widened_native_inline_slice() -> None:
    document = Document(
        blocks=[
            Paragraph(
                [
                    Underline([Str('Underline')]),
                    Space(),
                    SmallCaps([Str('Small'), Space(), Str('caps')]),
                    Space(),
                    Quoted([Str('quoted')], quote_type='DoubleQuote'),
                ]
            )
        ],
        source_format='native_pandoc',
    )
    assert write_markdown(document) == '[Underline]{.underline} [Small caps]{.smallcaps} "quoted"\n'


def test_markdown_writer_supports_line_blocks_and_null_blocks() -> None:
    document = Document(
        blocks=[
            LineBlock([[Str('one')], [], [Str('two')]]),
            Null(),
        ],
        source_format='native_pandoc',
    )
    assert write_markdown(document) == '| one\n|\n| two\n'


def test_html_writer_supports_widened_native_inline_slice() -> None:
    document = Document(
        blocks=[
            Paragraph(
                [
                    Underline([Str('Underline')]),
                    Space(),
                    SmallCaps([Str('Small'), Space(), Str('caps')]),
                    Space(),
                    Quoted([Str('quoted')], quote_type='DoubleQuote'),
                ]
            )
        ],
        source_format='native_pandoc',
    )
    assert write_html(document) == '<p><span class="underline">Underline</span> <span class="smallcaps">Small caps</span> “quoted”</p>\n'


def test_html_writer_supports_line_blocks_and_null_blocks() -> None:
    document = Document(
        blocks=[
            LineBlock([[Str('one')], [], [Str('two')]]),
            Null(),
        ],
        source_format='native_pandoc',
    )
    assert write_html(document) == '<div class="line-block">\n<div class="line">one</div>\n<div class="line"><br /></div>\n<div class="line">two</div>\n</div>\n'


def test_convert_text_accepts_native_wrapper_on_markdown_and_html_routes() -> None:
    native_text = '''Pandoc
  (Meta { unMeta = fromList [] })
  [ Para [ Underline [ Str "Underline" ]
         , Space
         , SmallCaps [ Str "Small" , Space , Str "caps" ]
         , Space
         , Quoted DoubleQuote [ Str "quoted" ]
         ]
  , LineBlock [ [ Str "one" ] , [] , [ Str "two" ] ]
  , Null
  ]
'''
    markdown = convert_text(native_text, 'native', 'markdown')
    html = convert_text(native_text, 'native', 'html')
    assert '[Underline]{.underline}' in markdown
    assert '[Small caps]{.smallcaps}' in markdown
    assert '"quoted"' in markdown
    assert '| one' in markdown and '| two' in markdown
    assert '<span class="underline">Underline</span>' in html
    assert '<span class="smallcaps">Small caps</span>' in html
    assert '“quoted”' in html
    assert '<div class="line-block">' in html
