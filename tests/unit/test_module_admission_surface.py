from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from pandoc_py.cli.options import format_version_banner, normalize_format
from pandoc_py.readers.commonmark import read_commonmark
from pandoc_py.readers.commonmark_x import read_commonmark_x
from pandoc_py.readers.html import read_html
from pandoc_py.readers.markdown import read_markdown
from pandoc_py.writers.commonmark import write_commonmark
from pandoc_py.writers.commonmark_x import write_commonmark_x
from pandoc_py.writers.html import write_html
from pandoc_py.writers.markdown import write_markdown
from pandoc_py.writers.native import write_native


def test_seed_module_aliases_resolve_current_supported_formats() -> None:
    assert normalize_format('markdown', role='input') == 'markdown'
    assert normalize_format('markdown', role='output') == 'markdown'
    assert normalize_format('commonmark_x', role='input') == 'commonmark_x'
    assert normalize_format('html5', role='input') == 'html'
    assert normalize_format('native', role='output') == 'native'


def test_seed_module_readers_return_documents() -> None:
    assert read_markdown('# Heading\n').blocks
    assert read_commonmark('# Heading\n').blocks
    assert read_commonmark_x('# Heading\n').blocks
    assert read_html('<p>Hello</p>').blocks


def test_seed_module_writers_emit_current_surface() -> None:
    document = read_markdown('# Heading\n\nParagraph\n')
    assert '# Heading' in write_markdown(document)
    assert '<h1' in write_html(document)
    assert 'Header 1' in write_native(document)
    assert '# Heading' in write_commonmark(document)
    assert '# Heading' in write_commonmark_x(document)


def test_package_cli_main_module_runs_version_banner() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    env['PYTHONPATH'] = str(repo_root / 'src') + ((os.pathsep + env['PYTHONPATH']) if env.get('PYTHONPATH') else '')
    proc = subprocess.run(
        [sys.executable, '-m', 'pandoc_py.cli', '--version'],
        text=True,
        capture_output=True,
        cwd=repo_root,
        env=env,
        check=False,
    )
    assert proc.returncode == 0
    assert proc.stdout == format_version_banner()
