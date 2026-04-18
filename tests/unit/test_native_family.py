from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pandoc_py.ast import Document, Heading, Paragraph, Space, Str
from pandoc_py.readers.markdown import read_markdown
from pandoc_py.writers.native import write_native


def _reparse_native_to_json(native_text: str) -> dict[str, object]:
    proc = subprocess.run(
        ['/usr/bin/pandoc', '-f', 'native', '-t', 'json', '--wrap=none'],
        input=native_text,
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _oracle_json_from_markdown(markdown_text: str) -> dict[str, object]:
    proc = subprocess.run(
        ['/usr/bin/pandoc', '-f', 'markdown', '-t', 'json', '--wrap=none'],
        input=markdown_text,
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_write_basic_native_blocks() -> None:
    document = Document(blocks=[Heading(level=1, inlines=[Str('Heading')]), Paragraph(inlines=[Str('alpha'), Space(), Str('beta')])])
    reparsed = _reparse_native_to_json(write_native(document))
    oracle = _oracle_json_from_markdown('# Heading\n\nalpha beta\n')
    assert reparsed == oracle


def test_native_route_matches_curated_smoke_corpus() -> None:
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
    fixtures_dir = REPO_ROOT / 'tests' / 'fixtures' / 'smoke'
    for fixture_name in fixtures:
        source = (fixtures_dir / fixture_name).read_text(encoding='utf-8')
        native = write_native(read_markdown(source))
        assert _reparse_native_to_json(native) == _oracle_json_from_markdown(source), fixture_name
