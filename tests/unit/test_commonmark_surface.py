from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from pandoc_py.app import convert_text
from pandoc_py.ast import Attr, Document, Heading, Link, Paragraph, Str
from pandoc_py.cli.options import normalize_format
from pandoc_py.readers.commonmark import CommonmarkScopeError, read_commonmark
from pandoc_py.writers.commonmark import CommonmarkWriterError, write_commonmark


def test_normalize_format_accepts_commonmark_aliases() -> None:
    assert normalize_format('commonmark', role='input') == 'commonmark'
    assert normalize_format('commonmark_x', role='output') == 'commonmark_x'


def test_read_commonmark_marks_source_format() -> None:
    document = read_commonmark('# Heading\n')
    assert document == Document(blocks=[Heading(level=1, inlines=[Str('Heading')])], source_format='commonmark')


def test_read_commonmark_rejects_heading_attributes() -> None:
    with pytest.raises(CommonmarkScopeError):
        read_commonmark('# Heading {#sec}\n')


def test_write_commonmark_rejects_heading_attributes() -> None:
    with pytest.raises(CommonmarkWriterError):
        write_commonmark(Document(blocks=[Heading(level=1, inlines=[Str('Heading')], attr=Attr(identifier='sec'))]))


def test_commonmark_input_to_json_suppresses_generated_heading_identifier() -> None:
    payload = convert_text('# Heading\n', 'commonmark', 'json')
    assert '"Header"' in payload
    assert '"heading"' not in payload


def test_commonmark_input_to_html_suppresses_heading_id_and_autolink_class() -> None:
    html = convert_text('# Heading\n\n<https://example.com>\n', 'commonmark', 'html')
    assert '<h1>Heading</h1>' in html
    assert 'class="uri"' not in html
    assert 'id="heading"' not in html


def test_commonmark_input_to_native_suppresses_generated_heading_identifier_and_autolink_class() -> None:
    native = convert_text('# Heading\n\n<https://example.com>\n', 'commonmark', 'native')
    assert 'Header 1 ("",[],[])' in native
    assert '("",["uri"],[])' not in native


def test_write_commonmark_autolink_round_trips() -> None:
    doc = Document(blocks=[Paragraph(inlines=[Link(inlines=[Str('https://example.com')], target='https://example.com', autolink=True)])])
    assert write_commonmark(doc) == '<https://example.com>\n'


def test_package_main_module_runs(tmp_path: Path) -> None:
    source = tmp_path / 'input.md'
    source.write_text('# Heading\n', encoding='utf-8')
    repo_root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    env['PYTHONPATH'] = str(repo_root / 'src') + ((os.pathsep + env['PYTHONPATH']) if env.get('PYTHONPATH') else '')
    proc = subprocess.run(
        [sys.executable, '-m', 'pandoc_py', str(source), '-f', 'markdown', '-t', 'commonmark'],
        text=True,
        capture_output=True,
        cwd=repo_root,
        env=env,
        check=False,
    )
    assert proc.returncode == 0
    assert '# Heading' in proc.stdout
