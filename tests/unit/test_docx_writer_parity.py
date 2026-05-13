"""Comprehensive OOXML structure tests for ``pandoc_py.formats.docx_writer``.

Every Pandoc inline and block should land in the correct OOXML container
with the right run-properties (``w:rPr``) or paragraph-properties
(``w:pPr``). These tests assert on the raw document.xml extracted from the
DOCX zip so we don't drift quietly from pandoc's structural conventions.
"""
from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.app import convert_text  # noqa: E402
from pandoc_py.ast import (  # noqa: E402
    Attr, BlockQuote, BulletList, Code, CodeBlock, DefinitionList, Div,
    Document, Emph, HardBreak, Heading, Image, LineBlock, Link, Math, Note,
    OrderedList, Paragraph, Quoted, RawBlock, RawInline, SmallCaps,
    SoftBreak, Space, Span, Str, Strikeout, Strong, Subscript, Superscript,
    Table, ThematicBreak, Underline,
)
from pandoc_py.formats.docx_writer import write_docx  # noqa: E402


# ---- shared helpers --------------------------------------------------

def _docx_parts(blocks: list) -> dict[str, str]:
    """Render ``Document(blocks=...)`` to docx bytes and return parts as
    text where applicable.
    """
    data = write_docx(Document(blocks=blocks))
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        return {n: zf.read(n).decode('utf-8', errors='replace')
                for n in zf.namelist()
                if n.endswith(('.xml', '.rels'))}


def _doc_xml(blocks: list) -> str:
    return _docx_parts(blocks)['word/document.xml']


# ---- inlines ---------------------------------------------------------

def test_str_and_space_become_w_t_runs():
    xml = _doc_xml([Paragraph(inlines=[Str('hello'), Space(), Str('world')])])
    assert '<w:r><w:t xml:space="preserve">hello</w:t></w:r>' in xml
    assert '<w:r><w:t xml:space="preserve"> </w:t></w:r>' in xml
    assert '<w:r><w:t xml:space="preserve">world</w:t></w:r>' in xml


def test_softbreak_becomes_space_run():
    xml = _doc_xml([Paragraph(inlines=[Str('a'), SoftBreak(), Str('b')])])
    assert '<w:t xml:space="preserve"> </w:t>' in xml


def test_hardbreak_emits_w_br():
    xml = _doc_xml([Paragraph(inlines=[Str('a'), HardBreak(), Str('b')])])
    assert '<w:r><w:br/></w:r>' in xml


def test_emph_emits_w_i_rpr():
    xml = _doc_xml([Paragraph(inlines=[Emph(inlines=[Str('emph')])])])
    assert '<w:rPr><w:i/></w:rPr>' in xml
    assert '>emph</w:t>' in xml


def test_strong_emits_w_b_rpr():
    xml = _doc_xml([Paragraph(inlines=[Strong(inlines=[Str('bold')])])])
    assert '<w:rPr><w:b/></w:rPr>' in xml


def test_strikeout_emits_w_strike():
    xml = _doc_xml([Paragraph(inlines=[Strikeout(inlines=[Str('x')])])])
    assert '<w:strike/>' in xml


def test_underline_emits_w_u_single():
    xml = _doc_xml([Paragraph(inlines=[Underline(inlines=[Str('u')])])])
    assert '<w:u w:val="single"/>' in xml


def test_smallcaps_emits_w_smallcaps():
    xml = _doc_xml([Paragraph(inlines=[SmallCaps(inlines=[Str('s')])])])
    assert '<w:smallCaps/>' in xml


def test_subscript_and_superscript():
    sub = _doc_xml([Paragraph(inlines=[Subscript(inlines=[Str('x')])])])
    sup = _doc_xml([Paragraph(inlines=[Superscript(inlines=[Str('x')])])])
    assert '<w:vertAlign w:val="subscript"/>' in sub
    assert '<w:vertAlign w:val="superscript"/>' in sup


def test_code_uses_verbatim_char_style():
    xml = _doc_xml([Paragraph(inlines=[Code(text='print(1)')])])
    assert '<w:rStyle w:val="VerbatimChar"/>' in xml
    assert '>print(1)</w:t>' in xml


def test_math_inline_and_display_render_with_delimiters():
    inline_xml = _doc_xml([Paragraph(inlines=[Math(text='a+b', display=False)])])
    display_xml = _doc_xml([Paragraph(inlines=[Math(text='a+b', display=True)])])
    assert '<w:rStyle w:val="Equation"/>' in inline_xml
    assert r'\(a+b\)' in inline_xml
    assert r'\[a+b\]' in display_xml


def test_quoted_wraps_inlines_in_curly_quotes():
    xml = _doc_xml([Paragraph(inlines=[
        Quoted(inlines=[Str('x')], quote_type='DoubleQuote'),
    ])])
    assert '“' in xml  # left double quote
    assert '”' in xml


def test_nested_emph_strong_keeps_both_properties():
    xml = _doc_xml([Paragraph(inlines=[
        Strong(inlines=[Emph(inlines=[Str('both')])]),
    ])])
    # The inner run should carry both bold and italic.
    assert '<w:rPr><w:b/><w:i/></w:rPr>' in xml or '<w:rPr><w:i/><w:b/></w:rPr>' in xml


def test_span_is_transparent():
    xml = _doc_xml([Paragraph(inlines=[
        Span(inlines=[Str('inside')], attr=Attr(identifier='x')),
    ])])
    assert '>inside</w:t>' in xml


def test_link_emits_hyperlink_with_rid_and_relationship():
    parts = _docx_parts([Paragraph(inlines=[
        Link(inlines=[Str('site')], target='https://example.com'),
    ])])
    doc = parts['word/document.xml']
    rels = parts['word/_rels/document.xml.rels']
    assert '<w:hyperlink r:id="rId' in doc
    assert '<w:rStyle w:val="Hyperlink"/>' in doc
    assert 'Target="https://example.com"' in rels
    assert 'TargetMode="External"' in rels


def test_image_emits_drawing_and_media_entry(tmp_path):
    img = tmp_path / 'tiny.png'
    img.write_bytes(
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01'
        b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    data = write_docx(Document(blocks=[
        Paragraph(inlines=[Image(target=str(img), inlines=[Str('alt')])]),
    ]))
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        doc = zf.read('word/document.xml').decode()
        rels = zf.read('word/_rels/document.xml.rels').decode()
        names = zf.namelist()
        assert '<w:drawing>' in doc
        assert '<wp:inline' in doc
        assert any(n.startswith('word/media/image') and n.endswith('.png') for n in names)
        assert 'Target="media/image1.png"' in rels


def test_image_missing_file_falls_back_to_1x1_png():
    data = write_docx(Document(blocks=[
        Paragraph(inlines=[Image(target='/nonexistent/whatever.png')]),
    ]))
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        assert 'word/media/image1.png' in zf.namelist()
        png = zf.read('word/media/image1.png')
        assert png.startswith(b'\x89PNG')


def test_note_emits_footnote_reference_and_footnotes_xml():
    data = write_docx(Document(blocks=[
        Paragraph(inlines=[
            Str('see'), Note(blocks=[Paragraph(inlines=[Str('fn')])]),
        ]),
    ]))
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = set(zf.namelist())
        doc = zf.read('word/document.xml').decode()
        assert 'word/footnotes.xml' in names
        assert '<w:footnoteReference w:id="2"/>' in doc
        notes = zf.read('word/footnotes.xml').decode()
        # Sentinel notes plus our actual footnote at id="2".
        assert 'w:id="-1"' in notes
        assert 'w:id="0"' in notes
        assert 'w:id="2"' in notes


def test_rawinline_openxml_passthrough():
    xml = _doc_xml([Paragraph(inlines=[
        RawInline(format='openxml', text='<w:r><w:t>raw</w:t></w:r>'),
    ])])
    assert '<w:r><w:t>raw</w:t></w:r>' in xml


# ---- blocks ----------------------------------------------------------

def test_heading_emits_heading_n_style_and_bookmark():
    xml = _doc_xml([Heading(level=2, inlines=[Str('Title')],
                            attr=Attr(identifier='title'))])
    assert '<w:pStyle w:val="Heading2"/>' in xml
    assert '<w:bookmarkStart' in xml
    assert 'w:name="title"' in xml
    assert '<w:bookmarkEnd' in xml


def test_heading_levels_are_clamped_to_1_6():
    high = _doc_xml([Heading(level=9, inlines=[Str('x')])])
    assert '<w:pStyle w:val="Heading6"/>' in high
    low = _doc_xml([Heading(level=0, inlines=[Str('x')])])
    assert '<w:pStyle w:val="Heading1"/>' in low


def test_paragraph_is_plain_w_p():
    xml = _doc_xml([Paragraph(inlines=[Str('p')])])
    assert '<w:p>' in xml
    assert '>p</w:t>' in xml


def test_blockquote_applies_blocktext_style_to_inner_paragraph():
    xml = _doc_xml([BlockQuote(blocks=[Paragraph(inlines=[Str('q')])])])
    assert '<w:pStyle w:val="BlockText"/>' in xml
    assert '>q</w:t>' in xml


def test_bullet_list_uses_numid_1():
    xml = _doc_xml([BulletList(items=[
        [Paragraph(inlines=[Str('a')])],
        [Paragraph(inlines=[Str('b')])],
    ])])
    assert '<w:numId w:val="1"/>' in xml
    assert '<w:pStyle w:val="ListParagraph"/>' in xml
    # Both items must appear.
    assert '>a</w:t>' in xml and '>b</w:t>' in xml


def test_ordered_list_uses_numid_2():
    xml = _doc_xml([OrderedList(items=[[Paragraph(inlines=[Str('first')])]])])
    assert '<w:numId w:val="2"/>' in xml


def test_definition_list_uses_term_and_definition_styles():
    xml = _doc_xml([DefinitionList(items=[
        ([Str('term')], [[Paragraph(inlines=[Str('def')])]])
    ])])
    assert '<w:pStyle w:val="DefinitionTerm"/>' in xml
    assert '<w:pStyle w:val="Definition"/>' in xml


def test_codeblock_uses_sourcecode_style_per_line():
    xml = _doc_xml([CodeBlock(text='line1\nline2')])
    # One paragraph per line, each styled SourceCode.
    assert xml.count('<w:pStyle w:val="SourceCode"/>') == 2
    assert '>line1</w:t>' in xml
    assert '>line2</w:t>' in xml


def test_thematic_break_emits_pbdr_bottom():
    xml = _doc_xml([ThematicBreak()])
    assert '<w:pBdr>' in xml
    assert '<w:bottom' in xml


def test_lineblock_renders_one_paragraph_with_br_separator():
    xml = _doc_xml([LineBlock(lines=[[Str('a')], [Str('b')]])])
    assert '<w:pStyle w:val="LineBlock"/>' in xml
    assert '<w:r><w:br/></w:r>' in xml


def test_div_is_transparent():
    xml = _doc_xml([Div(blocks=[Paragraph(inlines=[Str('inside')])])])
    assert '>inside</w:t>' in xml


def test_rawblock_openxml_passthrough():
    xml = _doc_xml([RawBlock(format='openxml', text='<w:p><w:r><w:t>raw</w:t></w:r></w:p>')])
    assert '<w:p><w:r><w:t>raw</w:t></w:r></w:p>' in xml


def test_rawblock_other_formats_dropped():
    xml = _doc_xml([RawBlock(format='html', text='<p>dropped</p>')])
    assert 'dropped' not in xml


def test_table_renders_w_tbl_with_header_and_rows():
    xml = _doc_xml([Table(
        caption=[Str('cap')],
        aligns=['AlignLeft', 'AlignRight'],
        headers=[[Str('H1')], [Str('H2')]],
        rows=[[[Str('a')], [Str('b')]], [[Str('c')], [Str('d')]]],
    )])
    assert '<w:tbl>' in xml
    assert '<w:tblHeader/>' in xml
    assert '<w:jc w:val="left"/>' in xml
    assert '<w:jc w:val="right"/>' in xml
    assert '<w:pStyle w:val="Caption"/>' in xml
    for token in ('H1', 'H2', 'a', 'b', 'c', 'd'):
        assert f'>{token}</w:t>' in xml


# ---- container parts -------------------------------------------------

def test_content_types_registers_word_document():
    parts = _docx_parts([Paragraph(inlines=[Str('hi')])])
    ct = parts['[Content_Types].xml']
    assert 'PartName="/word/document.xml"' in ct
    assert 'wordprocessingml.document.main+xml' in ct


def test_content_types_adds_image_default_when_image_present(tmp_path):
    img = tmp_path / 'tiny.png'
    img.write_bytes(
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01'
        b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    data = write_docx(Document(blocks=[
        Paragraph(inlines=[Image(target=str(img))]),
    ]))
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        ct = zf.read('[Content_Types].xml').decode()
        assert 'Extension="png"' in ct


def test_styles_xml_defines_all_referenced_styles():
    parts = _docx_parts([Paragraph(inlines=[Str('hi')])])
    styles = parts['word/styles.xml']
    for sid in ('Heading1', 'Heading2', 'Heading6', 'Normal', 'ListParagraph',
                'SourceCode', 'BlockText', 'LineBlock', 'Caption',
                'DefinitionTerm', 'Definition', 'VerbatimChar', 'Hyperlink',
                'FootnoteReference', 'Equation', 'Table'):
        assert f'w:styleId="{sid}"' in styles, sid


def test_numbering_xml_defines_both_lists():
    parts = _docx_parts([Paragraph(inlines=[Str('hi')])])
    numbering = parts['word/numbering.xml']
    assert 'w:numId="1"' in numbering
    assert 'w:numId="2"' in numbering
    assert 'w:val="bullet"' in numbering
    assert 'w:val="decimal"' in numbering


def test_document_rels_links_styles_and_numbering():
    parts = _docx_parts([Paragraph(inlines=[Str('hi')])])
    rels = parts['word/_rels/document.xml.rels']
    assert 'Target="styles.xml"' in rels
    assert 'Target="numbering.xml"' in rels


def test_document_rels_includes_footnotes_only_when_present():
    plain = _docx_parts([Paragraph(inlines=[Str('hi')])])
    assert 'Target="footnotes.xml"' not in plain['word/_rels/document.xml.rels']
    with_note = _docx_parts([Paragraph(inlines=[
        Str('x'),
        Note(blocks=[Paragraph(inlines=[Str('fn')])]),
    ])])
    assert 'Target="footnotes.xml"' in with_note['word/_rels/document.xml.rels']


# ---- end-to-end md → docx ------------------------------------------

def _convert_md(md: str) -> bytes:
    return convert_text(md, from_format='markdown', to_format='docx')


def test_md_emph_strong_strike_round_trip_appear_in_ooxml():
    body = _convert_md('*em* and **bold** and ~~strike~~\n')
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        doc = zf.read('word/document.xml').decode()
    assert '<w:i/>' in doc
    assert '<w:b/>' in doc
    assert '<w:strike/>' in doc


def test_md_inline_code_uses_verbatimchar():
    body = _convert_md('Use `printf` here.\n')
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        doc = zf.read('word/document.xml').decode()
    assert 'VerbatimChar' in doc
    assert '>printf</w:t>' in doc


def test_md_link_creates_hyperlink_relationship():
    body = _convert_md('[home](https://example.com)\n')
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        rels = zf.read('word/_rels/document.xml.rels').decode()
        doc = zf.read('word/document.xml').decode()
    assert 'Target="https://example.com"' in rels
    assert '<w:hyperlink r:id="rId' in doc


def test_md_headings_get_correct_levels():
    body = _convert_md('# h1\n\n## h2\n\n### h3\n')
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        doc = zf.read('word/document.xml').decode()
    assert '<w:pStyle w:val="Heading1"/>' in doc
    assert '<w:pStyle w:val="Heading2"/>' in doc
    assert '<w:pStyle w:val="Heading3"/>' in doc


def test_md_bullet_and_ordered_lists_use_distinct_numids():
    body = _convert_md('- a\n- b\n\n1. one\n2. two\n')
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        doc = zf.read('word/document.xml').decode()
    assert '<w:numId w:val="1"/>' in doc
    assert '<w:numId w:val="2"/>' in doc


def test_md_codeblock_yields_sourcecode_paragraphs():
    body = _convert_md('```\nline1\nline2\n```\n')
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        doc = zf.read('word/document.xml').decode()
    assert doc.count('<w:pStyle w:val="SourceCode"/>') >= 2


def test_md_blockquote_applies_blocktext():
    body = _convert_md('> quoted\n')
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        doc = zf.read('word/document.xml').decode()
    assert '<w:pStyle w:val="BlockText"/>' in doc


def test_md_thematic_break_emits_pbdr():
    body = _convert_md('para\n\n---\n\nmore\n')
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        doc = zf.read('word/document.xml').decode()
    assert '<w:pBdr>' in doc


def test_md_to_docx_zip_is_valid_and_readable_by_reader():
    """The docx we emit must be readable by our own docx reader.
    Validates the OOXML stays structurally consistent end-to-end.
    """
    body = _convert_md('# Heading\n\nThis is *emph* and **strong**.\n\n- a\n- b\n')
    # Must be a valid zip with the canonical members.
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        names = set(zf.namelist())
        assert '[Content_Types].xml' in names
        assert 'word/document.xml' in names
        assert 'word/styles.xml' in names
        assert '_rels/.rels' in names
        assert 'word/_rels/document.xml.rels' in names
    # And our reader must accept it.
    re_text = convert_text(body, from_format='docx', to_format='markdown')
    assert 'Heading' in re_text
    # Content survives the round-trip even if formatting hints are reapproximated.
    assert 'emph' in re_text
    assert 'strong' in re_text
