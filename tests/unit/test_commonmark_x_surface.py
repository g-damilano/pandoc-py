from __future__ import annotations

from pandoc_py.app import convert_text
from pandoc_py.ast import Document, Heading, MetaInlines, Paragraph, Str
from pandoc_py.cli.options import normalize_format
from pandoc_py.readers.commonmark_x import read_commonmark_x
from pandoc_py.writers.commonmark_x import write_commonmark_x


def test_normalize_format_accepts_dedicated_commonmark_x_surface() -> None:
    assert normalize_format('commonmark_x', role='input') == 'commonmark_x'
    assert normalize_format('commonmark-x', role='output') == 'commonmark_x'


def test_read_commonmark_x_marks_source_format_and_keeps_metadata() -> None:
    document = read_commonmark_x('---\ntitle: Hi\n---\n\n# Heading\n')
    assert document.meta == {'title': MetaInlines([Str('Hi')])}
    assert document.source_format == 'commonmark_x'
    assert document.blocks == [Heading(level=1, inlines=[Str('Heading')])]


def test_commonmark_x_input_to_json_generates_heading_identifier_and_suppresses_autolink_class() -> None:
    payload = convert_text('# Heading\n\n<https://example.com>\n', 'commonmark_x', 'json')
    assert '"Header"' in payload
    assert '"heading"' in payload
    assert '"uri"' not in payload


def test_commonmark_x_input_to_html_generates_heading_id_and_suppresses_autolink_class() -> None:
    html = convert_text('# Heading\n\n<https://example.com>\n', 'commonmark_x', 'html')
    assert '<h1 id="heading">Heading</h1>' in html
    assert 'class="uri"' not in html


def test_commonmark_x_input_to_native_generates_heading_identifier_and_suppresses_autolink_class() -> None:
    native = convert_text('# Heading\n\n<https://example.com>\n', 'commonmark_x', 'native')
    assert 'Header 1 ("heading",[],[])' in native
    assert '("",["uri"],[])' not in native


def test_commonmark_x_standalone_image_remains_paragraph_on_html_and_json_routes() -> None:
    source = '![a](img.png){#x .c key="val"}\n'
    html = convert_text(source, 'commonmark_x', 'html')
    payload = convert_text(source, 'commonmark_x', 'json')
    assert '<p><img src="img.png" id="x" class="c" data-key="val" alt="a" /></p>' in html
    assert '"Figure"' not in payload
    assert '"Para"' in payload


def test_write_commonmark_x_uses_markdown_surface() -> None:
    doc = Document(blocks=[Paragraph(inlines=[Str('Hello')])])
    assert write_commonmark_x(doc) == 'Hello\n'


def test_commonmark_x_double_backslash_line_ending_stays_literal_backslash_plus_softbreak() -> None:
    native = convert_text('alpha\\\\\nbeta\n', 'commonmark_x', 'native')
    assert 'Str "alpha\\\\"' in native
    assert 'SoftBreak' in native


def test_commonmark_x_fenced_code_block_reaches_json_route() -> None:
    payload = convert_text('```\nalpha\n```\n', 'commonmark_x', 'json')
    assert '"CodeBlock"' in payload
    assert '"alpha"' in payload


def test_commonmark_x_display_math_block_reaches_html_route() -> None:
    html = convert_text('$$\na+b\n$$\n', 'commonmark_x', 'html')
    assert 'class="math display"' in html
    assert '\\[' in html



def test_commonmark_x_definition_list_reaches_json_route() -> None:
    payload = convert_text('Term\n: Definition\n', 'commonmark_x', 'json')
    assert '"DefinitionList"' in payload
    assert '"Definition"' in payload


def test_commonmark_x_reference_image_reaches_html_route() -> None:
    html = convert_text('alpha ![alt](img.png "Img Title") delta\n', 'commonmark_x', 'html')
    assert '<img src="img.png" alt="alt" title="Img Title" />' in html


def test_commonmark_x_raw_inline_comment_reaches_html_route() -> None:
    html = convert_text('alpha <!-- note --> gamma\n', 'commonmark_x', 'html')
    assert '<!-- note -->' in html


def test_commonmark_x_subscript_and_strikeout_reach_json_route() -> None:
    payload = convert_text('H~2~O and ~~gone~~\n', 'commonmark_x', 'json')
    assert '"Subscript"' in payload
    assert '"Strikeout"' in payload


def test_commonmark_x_task_lists_stay_literal_on_json_route() -> None:
    payload = convert_text('- [ ] one\n- [x] two\n', 'commonmark_x', 'json')
    assert '"☐"' not in payload
    assert '"☒"' not in payload
    assert '"[x]"' in payload


def test_commonmark_x_inline_footnote_stays_literal_on_json_route() -> None:
    payload = convert_text('Alpha^[Note text].\n', 'commonmark_x', 'json')
    assert '"Note"' not in payload
    assert 'Alpha^[Note' in payload
    assert 'text].' in payload


def test_commonmark_x_raw_html_blocks_preserve_terminal_newline_on_json_route() -> None:
    payload = convert_text('<!-- note -->\n', 'commonmark_x', 'json')
    assert '<!-- note -->\\n' in payload
