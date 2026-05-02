"""Audit tests for the binary / container / office format families.

Each test exercises both the writer and the reader for one family and
asserts that:

* the writer emits a non-empty container of the expected zip / text
  shape;
* the reader can read its own writer's output back into a Document
  with the heading/paragraph/list structure the markdown source
  expressed (a self-round-trip);
* where possible, pandoc's own reader for the same format extracts
  matching structure (oracle-backed self-round-trip).

These tests complement the differential reports under
``tests/differential/reports/binary*`` and pin the binary container
families to a structural contract.
"""
from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(REPO_ROOT / 'tests') not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / 'tests'))

from _oracle import resolve_oracle  # noqa: E402

from pandoc_py.app import convert_text  # noqa: E402
from pandoc_py.ast import (  # noqa: E402
    BulletList, CodeBlock, Document, Heading, OrderedList, Paragraph,
)
from pandoc_py.io import get_reader, get_writer  # noqa: E402

SIMPLE_MARKDOWN = (REPO_ROOT / 'tests' / 'fixtures' / 'format_families' / 'simple.md').read_text(encoding='utf-8')


# ---- DOCX ---------------------------------------------------------------

def test_docx_writer_emits_valid_ooxml_zip():
    raw = convert_text(SIMPLE_MARKDOWN, 'markdown', 'docx')
    assert isinstance(raw, bytes) and len(raw) > 0
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        names = set(zf.namelist())
    # Required OOXML parts.
    assert '[Content_Types].xml' in names
    assert '_rels/.rels' in names
    assert 'word/document.xml' in names
    assert 'word/styles.xml' in names
    assert 'word/numbering.xml' in names


def test_docx_reader_self_round_trips_the_writer():
    raw = convert_text(SIMPLE_MARKDOWN, 'markdown', 'docx')
    reader = get_reader('docx')
    doc = reader.read(raw)
    assert any(isinstance(b, Heading) for b in doc.blocks)
    assert any(isinstance(b, BulletList) for b in doc.blocks)
    assert any(isinstance(b, CodeBlock) for b in doc.blocks)


# ---- ODT ----------------------------------------------------------------

def test_odt_writer_emits_valid_opendocument_zip():
    raw = convert_text(SIMPLE_MARKDOWN, 'markdown', 'odt')
    assert isinstance(raw, bytes) and len(raw) > 0
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        names = set(zf.namelist())
        assert zf.read('mimetype') == b'application/vnd.oasis.opendocument.text'
    assert 'content.xml' in names
    assert 'styles.xml' in names
    assert 'META-INF/manifest.xml' in names


def test_odt_reader_self_round_trips_the_writer():
    raw = convert_text(SIMPLE_MARKDOWN, 'markdown', 'odt')
    doc = get_reader('odt').read(raw)
    assert any(isinstance(b, Heading) for b in doc.blocks)
    assert any(isinstance(b, BulletList) for b in doc.blocks)


# ---- EPUB ---------------------------------------------------------------

def test_epub_writer_emits_valid_epub_zip():
    raw = convert_text(SIMPLE_MARKDOWN, 'markdown', 'epub')
    assert isinstance(raw, bytes) and len(raw) > 0
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        names = set(zf.namelist())
        assert zf.read('mimetype').startswith(b'application/epub+zip')
    assert 'META-INF/container.xml' in names
    assert any(n.endswith('.opf') for n in names)
    assert any(n.endswith('.xhtml') for n in names)


def test_epub_reader_self_round_trips_the_writer():
    raw = convert_text(SIMPLE_MARKDOWN, 'markdown', 'epub')
    doc = get_reader('epub').read(raw)
    assert any(isinstance(b, Heading) for b in doc.blocks)
    assert any(isinstance(b, BulletList) for b in doc.blocks)
    assert any(isinstance(b, CodeBlock) for b in doc.blocks)


# ---- PPTX ---------------------------------------------------------------

def test_pptx_writer_emits_valid_powerpoint_zip():
    raw = convert_text(SIMPLE_MARKDOWN, 'markdown', 'pptx')
    assert isinstance(raw, bytes) and len(raw) > 0
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        names = set(zf.namelist())
    assert '[Content_Types].xml' in names
    assert 'ppt/presentation.xml' in names
    assert any(n.startswith('ppt/slides/slide') and n.endswith('.xml') for n in names)


def test_pptx_reader_self_round_trips_the_writer():
    raw = convert_text(SIMPLE_MARKDOWN, 'markdown', 'pptx')
    doc = get_reader('pptx').read(raw)
    assert any(isinstance(b, Heading) for b in doc.blocks)


def test_pptx_reader_handles_pandoc_emitted_pptx(tmp_path):
    """Pandoc has a PPTX writer (no PPTX reader) — verify our reader can
    consume pandoc's emission and produce a non-empty document."""
    oracle = resolve_oracle()
    if oracle is None:
        pytest.skip('No pandoc oracle available.')
    import subprocess
    fixture = REPO_ROOT / 'tests' / 'fixtures' / 'format_families' / 'simple.md'
    out_path = tmp_path / 'sample.pptx'
    subprocess.run(
        [oracle, str(fixture), '-f', 'markdown', '-t', 'pptx', '-o', str(out_path)],
        check=True,
    )
    doc = get_reader('pptx').read(out_path.read_bytes())
    assert any(isinstance(b, Heading) for b in doc.blocks)
    assert any(isinstance(b, Paragraph) for b in doc.blocks)


# ---- XLSX ---------------------------------------------------------------

def test_xlsx_writer_emits_valid_workbook_zip():
    raw = convert_text((REPO_ROOT / 'tests' / 'fixtures' / 'format_families' / 'table.csv').read_text(encoding='utf-8'),
                       'csv', 'xlsx')
    assert isinstance(raw, bytes) and len(raw) > 0
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        names = set(zf.namelist())
    assert '[Content_Types].xml' in names
    assert 'xl/workbook.xml' in names
    assert 'xl/worksheets/sheet1.xml' in names


def test_xlsx_reader_self_round_trips_the_writer():
    csv_text = (REPO_ROOT / 'tests' / 'fixtures' / 'format_families' / 'table.csv').read_text(encoding='utf-8')
    raw = convert_text(csv_text, 'csv', 'xlsx')
    doc = get_reader('xlsx').read(raw)
    # Each spreadsheet row should produce at least one block (paragraph).
    assert any(isinstance(b, Paragraph) for b in doc.blocks)


# ---- IPYNB --------------------------------------------------------------

def test_ipynb_writer_emits_valid_notebook_json():
    raw = convert_text(SIMPLE_MARKDOWN, 'markdown', 'ipynb')
    assert isinstance(raw, str) and raw.strip().startswith('{')
    nb = json.loads(raw)
    assert nb.get('nbformat') == 4
    assert isinstance(nb.get('cells'), list) and nb['cells']


def test_ipynb_reader_round_trips_through_self():
    raw = convert_text(SIMPLE_MARKDOWN, 'markdown', 'ipynb')
    doc = get_reader('ipynb').read(raw)
    # Cells become Divs with class "cell".
    from pandoc_py.ast import Div
    assert any(isinstance(b, Div) and 'cell' in b.attr.classes for b in doc.blocks)


# ---- RTF ----------------------------------------------------------------

def test_rtf_writer_emits_pandoc_aligned_pard_groups():
    raw = convert_text(SIMPLE_MARKDOWN, 'markdown', 'rtf')
    assert isinstance(raw, str)
    assert raw.lstrip().startswith(r'{\rtf1')
    assert r'{\pard' in raw
    assert r'\par}' in raw
    assert r'\outlinelevel' in raw  # heading marker
    assert r'\bullet' in raw  # list marker


def test_rtf_reader_round_trips_through_self():
    raw = convert_text(SIMPLE_MARKDOWN, 'markdown', 'rtf')
    doc = get_reader('rtf').read(raw)
    assert any(isinstance(b, Heading) for b in doc.blocks)
    assert any(isinstance(b, Paragraph) for b in doc.blocks)
