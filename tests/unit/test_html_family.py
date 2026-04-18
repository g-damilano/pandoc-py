from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pandoc_py.ast import BlockQuote, BulletList, CodeBlock, Document, Heading, Image, Link, Paragraph, Space, Str, Table
from pandoc_py.writers.html import write_html
from scripts.run_differential import _normalized_html_repr


def test_write_basic_html_blocks() -> None:
    document = Document(
        blocks=[
            Heading(level=1, inlines=[Str('Heading')]),
            Paragraph(inlines=[Str('alpha'), Space(), Link(inlines=[Str('beta')], target='https://example.com')]),
            BlockQuote(blocks=[Paragraph(inlines=[Str('quoted')])]),
        ]
    )
    assert write_html(document) == (
        '<h1 id="heading">Heading</h1>\n'
        '<p>alpha <a href="https://example.com">beta</a></p>\n'
        '<blockquote>\n<p>quoted</p>\n</blockquote>\n'
    )


def test_write_figure_and_table_html() -> None:
    document = Document(
        blocks=[
            Paragraph(inlines=[Image(inlines=[Str('cap')], target='img.png')]),
            Table(
                caption=[Str('Cap')],
                aligns=['AlignLeft', 'AlignRight'],
                headers=[[Str('A')], [Str('B')]],
                rows=[[[Str('1')], [Str('2')]]],
            ),
        ]
    )
    html = write_html(document)
    assert '<figure>' in html
    assert '<figcaption aria-hidden="true">cap</figcaption>' in html
    assert '<caption>Cap</caption>' in html
    assert '<td style="text-align: right;">2</td>' in html


def test_write_bullet_list_with_compact_nested_list_html() -> None:
    document = Document(
        blocks=[
            BulletList(
                items=[
                    [Paragraph(inlines=[Str('outer')]), BulletList(items=[[Paragraph(inlines=[Str('inner')])]])],
                    [Paragraph(inlines=[Str('done')])],
                ]
            )
        ]
    )
    assert write_html(document) == (
        '<ul>\n'
        '<li>\nouter\n<ul>\n<li>inner</li>\n</ul>\n</li>\n'
        '<li>done</li>\n'
        '</ul>\n'
    )


def _run_python_html(fixture: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env['PYTHONPATH'] = str(SRC_ROOT) + (os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / 'scripts' / 'run_python_cli.py'), str(fixture), '--from', 'markdown', '--to', 'html'],
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
        env=env,
        check=False,
    )


def _run_oracle_html(fixture: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ['/usr/bin/pandoc', str(fixture), '-f', 'markdown', '-t', 'html', '--mathjax', '--no-highlight', '--wrap=none'],
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
        check=False,
    )


def _assert_html_route_matches(fixture_name: str) -> None:
    fixture = REPO_ROOT / 'tests' / 'fixtures' / 'smoke' / fixture_name
    py = _run_python_html(fixture)
    oracle = _run_oracle_html(fixture)
    assert py.returncode == 0, py.stderr
    assert oracle.returncode == 0, oracle.stderr
    assert _normalized_html_repr(py.stdout) == _normalized_html_repr(oracle.stdout)


def test_html_route_matches_curated_smoke_corpus() -> None:
    fixtures = [
        'plain_paragraph.md',
        'atx_heading.md',
        'autolink_paragraph.md',
        'email_autolink_paragraph.md',
        'heading_attrs.md',
        'link_attrs.md',
        'image_attrs_standalone.md',
        'fenced_code_attrs.md',
        'block_quote_inline.md',
        'bullet_list_loose_nested.md',
        'ordered_list_compact_nested.md',
        'pipe_table_inline_cells.md',
        'definition_list_continuation.md',
        'footnote_reference.md',
        'citation_multi.md',
        'display_math_block.md',
        'raw_inline_tag.md',
        'raw_block_script.md',
        'task_list_bullet.md',
        'raw_block_tex_fence.md',
    ]
    for fixture_name in fixtures:
        _assert_html_route_matches(fixture_name)
