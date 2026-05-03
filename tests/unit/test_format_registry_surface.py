"""Smoke tests for the OOP format registry and the new format families."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

import pytest

from pandoc_py import io as iolayer
from pandoc_py.app import convert_text


def test_registry_lists_core_formats():
    readers = set(iolayer.list_readers())
    writers = set(iolayer.list_writers())
    for f in ['markdown', 'json', 'html', 'native', 'commonmark', 'commonmark_x']:
        assert f in readers, f
        assert f in writers, f


def test_registry_includes_new_text_formats():
    readers = set(iolayer.list_readers())
    writers = set(iolayer.list_writers())
    for f in ['rst', 'org', 'latex', 'asciidoc', 'mediawiki', 'textile', 'djot',
              'dokuwiki', 'jira', 'creole', 'twiki', 'tikiwiki', 'vimwiki',
              'muse', 'haddock', 'txt2tags', 'typst', 'pod', 'man', 'mdoc']:
        assert f in readers, f
        assert f in writers, f


def test_registry_includes_structured_formats():
    readers = set(iolayer.list_readers())
    writers = set(iolayer.list_writers())
    for f in ['csv', 'opml', 'xml', 'docbook', 'jats', 'fb2',
              'bibtex', 'csljson', 'ris', 'endnotexml', 'rtf', 'ipynb']:
        assert f in readers, f
        assert f in writers, f


def test_registry_includes_binary_containers():
    readers = set(iolayer.list_readers())
    writers = set(iolayer.list_writers())
    for f in ['docx', 'odt', 'epub', 'pptx', 'xlsx']:
        assert f in writers, f
    # All except pdf are also readable
    for f in ['docx', 'odt', 'epub', 'pptx', 'xlsx']:
        assert f in readers, f


def test_registry_includes_writer_only_renderers():
    writers = set(iolayer.list_writers())
    for f in ['plain', 'context', 'texinfo', 'beamer', 'opendocument', 'tei',
              'icml', 'ms', 'ansi', 'bbcode', 'zimwiki', 'gfm', 'markdown_strict',
              'pdf']:
        assert f in writers, f


@pytest.mark.parametrize('to_format', [
    'rst', 'org', 'latex', 'asciidoc', 'mediawiki', 'textile', 'djot',
    'dokuwiki', 'jira', 'creole', 'twiki', 'tikiwiki', 'vimwiki', 'muse',
    'haddock', 'txt2tags', 'typst', 'pod', 'man', 'mdoc', 'context',
    'texinfo', 'opendocument', 'tei', 'plain', 'gfm', 'bbcode', 'zimwiki',
])
def test_markdown_to_format_round_trip_constrained_slice(to_format: str):
    out = convert_text('# Hello\n\nworld\n', 'markdown', to_format)
    assert isinstance(out, str)
    assert out.strip()  # non-empty output
    assert 'Hello' in out
    assert 'world' in out


@pytest.mark.parametrize('roundtrip_format', ['rst', 'org', 'asciidoc', 'mediawiki',
                                              'textile', 'djot', 'dokuwiki', 'jira',
                                              'pod', 'haddock'])
def test_round_trip_through_text_format(roundtrip_format: str):
    md = '# H\n\nbody.\n'
    out = convert_text(md, 'markdown', roundtrip_format)
    re_md = convert_text(out, roundtrip_format, 'markdown')
    assert 'H' in re_md
    assert 'body' in re_md


def test_csv_round_trip():
    csv_in = 'name,value\nalpha,1\nbeta,2\n'
    out_md = convert_text(csv_in, 'csv', 'markdown')
    assert 'alpha' in out_md and 'beta' in out_md


def test_ipynb_round_trip_includes_code_cell():
    md = '# Title\n\nexplanation\n\n```python\nprint(1)\n```\n'
    nb = convert_text(md, 'markdown', 'ipynb')
    assert '"cell_type"' in nb
    assert 'print(1)' in nb
    re_md = convert_text(nb, 'ipynb', 'markdown')
    assert 'Title' in re_md
    assert 'print(1)' in re_md


def test_docx_writer_emits_zip_with_document_xml():
    import io as _io
    import zipfile
    blob = convert_text('# H\n\nbody\n', 'markdown', 'docx')
    with zipfile.ZipFile(_io.BytesIO(blob)) as zf:
        assert 'word/document.xml' in zf.namelist()
        body = zf.read('word/document.xml').decode('utf-8')
        assert 'body' in body


def test_odt_writer_emits_zip_with_content_xml():
    import io as _io
    import zipfile
    blob = convert_text('# H\n\nbody\n', 'markdown', 'odt')
    with zipfile.ZipFile(_io.BytesIO(blob)) as zf:
        assert 'content.xml' in zf.namelist()
        assert 'mimetype' in zf.namelist()


def test_epub_writer_emits_valid_zip():
    import io as _io
    import zipfile
    blob = convert_text('# Chapter 1\n\nLorem ipsum.\n', 'markdown', 'epub')
    with zipfile.ZipFile(_io.BytesIO(blob)) as zf:
        names = zf.namelist()
        assert 'mimetype' in names
        assert 'META-INF/container.xml' in names
        assert 'OEBPS/content.opf' in names
        assert 'OEBPS/chapter.xhtml' in names


def test_pptx_writer_creates_one_slide_per_heading():
    import io as _io
    import zipfile
    md = '# Slide one\n\nbody\n\n# Slide two\n\nbody\n'
    blob = convert_text(md, 'markdown', 'pptx')
    with zipfile.ZipFile(_io.BytesIO(blob)) as zf:
        slides = [n for n in zf.namelist() if n.startswith('ppt/slides/slide')]
        assert len(slides) == 2


def test_xlsx_writer_emits_workbook():
    import io as _io
    import zipfile
    blob = convert_text('# Title\n\nrow content\n', 'markdown', 'xlsx')
    with zipfile.ZipFile(_io.BytesIO(blob)) as zf:
        assert 'xl/workbook.xml' in zf.namelist()
        assert 'xl/worksheets/sheet1.xml' in zf.namelist()


def test_bibtex_admits_bibliography_metadata_surface():
    """Pandoc reads BibTeX as nocite metadata + empty body. The reader
    must produce that shape."""
    from pandoc_py.formats.bibtex import _read_bibtex
    bib = '@article{smith2020, title = {The Title}, author = {Smith, J.}, year = {2020}}'
    doc = _read_bibtex(bib)
    assert doc.blocks == []
    assert 'nocite' in doc.meta


def test_csljson_admits_bibliography_metadata_surface():
    from pandoc_py.formats.csljson import _read_csljson
    csl = '[{"id": "smith2020", "type": "article", "title": "T", "author": "Smith"}]'
    doc = _read_csljson(csl)
    assert doc.blocks == []
    assert 'nocite' in doc.meta


def test_format_aliases_resolve_through_cli():
    out = convert_text('# H\n', 'markdown', 'pandoc-json')
    assert 'Header' in out
    out2 = convert_text('# H\n', 'markdown', 'commonmark-x')
    assert 'H' in out2
