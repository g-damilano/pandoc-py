"""Tests for the CLI-flag → AST transforms.

Covers ``--number-sections``, ``--ascii``, ``--strip-comments``,
``--id-prefix``, and ``--epub-cover-image``. These are the flags that
have visible runtime effect via the document-level AST transform
pipeline in ``pandoc_py.cli.main._apply_ast_transforms``.
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
from pandoc_py.ast import Attr, Document, Heading, Paragraph, RawBlock, RawInline, Str  # noqa: E402
from pandoc_py.cli.main import (  # noqa: E402
    _apply_id_prefix,
    _ascii_only_output,
    _number_sections,
    _strip_html_comments,
    main as cli_main,
)


SIMPLE_MD = REPO_ROOT / 'tests' / 'fixtures' / 'format_families' / 'simple.md'


# ---- --number-sections ------------------------------------------------

def test_number_sections_prepends_hierarchical_numbers():
    doc = Document(blocks=[
        Heading(level=1, inlines=[Str('A')]),
        Heading(level=2, inlines=[Str('B')]),
        Heading(level=2, inlines=[Str('C')]),
        Heading(level=1, inlines=[Str('D')]),
    ])
    out = _number_sections(doc, ())
    flat = [b.inlines[0].text for b in out.blocks]
    assert flat == ['1.', '1.1.', '1.2.', '2.']


def test_number_sections_respects_unnumbered_class():
    doc = Document(blocks=[
        Heading(level=1, inlines=[Str('A')]),
        Heading(level=1, inlines=[Str('B')], attr=Attr(classes=['unnumbered'])),
        Heading(level=1, inlines=[Str('C')]),
    ])
    out = _number_sections(doc, ())
    flat = [b.inlines[0].text for b in out.blocks]
    assert flat == ['1.', 'B', '2.']


def test_number_sections_offset_starts_at_specified_index():
    doc = Document(blocks=[Heading(level=1, inlines=[Str('A')])])
    out = _number_sections(doc, (5,))
    assert out.blocks[0].inlines[0].text == '6.'


def test_number_sections_cli_round_trip_renders_in_html(tmp_path):
    out_path = tmp_path / 'out.html'
    rc = cli_main([
        str(SIMPLE_MD), '-f', 'markdown', '-t', 'html',
        '-N',
        '-o', str(out_path),
    ])
    assert rc == 0
    html = out_path.read_text(encoding='utf-8')
    assert '1.' in html  # at least one section number rendered


# ---- --ascii ----------------------------------------------------------

def test_ascii_only_output_replaces_non_ascii_in_text():
    assert _ascii_only_output('café') == 'caf&#xE9;'


def test_ascii_only_output_preserves_ascii():
    assert _ascii_only_output('hello') == 'hello'


def test_ascii_only_output_passes_bytes_unchanged():
    assert _ascii_only_output(b'\xc3\xa9') == b'\xc3\xa9'


def test_ascii_flag_cli_emits_numeric_refs(tmp_path):
    src = tmp_path / 'cafe.md'
    src.write_text('# café\n', encoding='utf-8')
    rc = cli_main([str(src), '-f', 'markdown', '-t', 'html',
                   '--ascii', '-o', str(tmp_path / 'out.html')])
    assert rc == 0
    html = (tmp_path / 'out.html').read_text(encoding='utf-8')
    assert 'caf&#xE9;' in html
    assert 'café' not in html


# ---- --strip-comments -------------------------------------------------

def test_strip_html_comments_drops_raw_html_comments():
    doc = Document(blocks=[
        RawBlock(format='html', text='<p>Hi</p><!-- secret -->'),
        Paragraph(inlines=[Str('keep')]),
    ])
    out = _strip_html_comments(doc)
    assert '<!--' not in out.blocks[0].text
    assert 'Hi' in out.blocks[0].text


def test_strip_html_comments_drops_inline_html_comment():
    doc = Document(blocks=[
        Paragraph(inlines=[
            Str('before'),
            RawInline(format='html', text='<!--gone-->'),
            Str('after'),
        ]),
    ])
    out = _strip_html_comments(doc)
    inlines = out.blocks[0].inlines
    assert inlines[1].text == ''  # comment stripped to empty raw inline


# ---- --id-prefix ------------------------------------------------------

def test_id_prefix_prepends_to_block_identifiers():
    doc = Document(blocks=[
        Heading(level=1, inlines=[Str('Hi')], attr=Attr(identifier='hi')),
        Paragraph(inlines=[Str('p')]),
    ])
    out = _apply_id_prefix(doc, 'ch1-')
    assert out.blocks[0].attr.identifier == 'ch1-hi'


def test_id_prefix_cli_through_html(tmp_path):
    out_path = tmp_path / 'out.html'
    rc = cli_main([
        str(SIMPLE_MD), '-f', 'markdown', '-t', 'html',
        '--id-prefix=ch1-',
        '-o', str(out_path),
    ])
    assert rc == 0
    html = out_path.read_text(encoding='utf-8')
    assert 'id="ch1-heading"' in html


# ---- --epub-cover-image ----------------------------------------------

def _write_tiny_png(path: Path) -> None:
    """Write a 1x1 transparent PNG."""
    path.write_bytes(
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01'
        b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )


def test_epub_cover_image_is_embedded_via_cli(tmp_path):
    cover = tmp_path / 'cover.png'
    _write_tiny_png(cover)
    out_path = tmp_path / 'book.epub'
    rc = cli_main([
        str(SIMPLE_MD), '-f', 'markdown', '-t', 'epub',
        '--epub-cover-image', str(cover),
        '-o', str(out_path),
    ])
    assert rc == 0
    with zipfile.ZipFile(out_path) as zf:
        names = set(zf.namelist())
        assert 'OEBPS/cover.png' in names
        assert 'OEBPS/cover.xhtml' in names
        opf = next(n for n in names if n.endswith('content.opf'))
        opf_text = zf.read(opf).decode('utf-8')
        assert 'cover-image' in opf_text
        assert 'idref="cover"' in opf_text


def test_epub_embed_font_is_included(tmp_path):
    font = tmp_path / 'DejaVu.ttf'
    font.write_bytes(b'\x00\x01\x00\x00')  # placeholder OpenType header
    out_path = tmp_path / 'book.epub'
    rc = cli_main([
        str(SIMPLE_MD), '-f', 'markdown', '-t', 'epub',
        '--epub-embed-font', str(font),
        '-o', str(out_path),
    ])
    assert rc == 0
    with zipfile.ZipFile(out_path) as zf:
        assert 'OEBPS/fonts/DejaVu.ttf' in zf.namelist()
