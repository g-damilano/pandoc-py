"""Smoke-tests for the expanded pandoc-compatible CLI surface."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.cli.main import main as cli_main  # noqa: E402
from pandoc_py.cli.options import parse_cli_options  # noqa: E402
from pandoc_py.cli.templates import render_template, get_default_template  # noqa: E402


SIMPLE_MD = REPO_ROOT / 'tests' / 'fixtures' / 'format_families' / 'simple.md'


def _run(argv, capsys, *, stdin: str | None = None):
    if stdin is not None:
        # argparse reads from sys.stdin via _read_input_one when path == '-'
        import io
        sys.stdin = io.StringIO(stdin)
    rc = cli_main(argv)
    out, err = capsys.readouterr()
    return rc, out, err


def test_list_input_formats_emits_one_per_line(capsys):
    rc, out, _ = _run(['--list-input-formats'], capsys)
    assert rc == 0
    lines = out.strip().splitlines()
    assert 'markdown' in lines and 'docx' in lines and 'native' in lines


def test_list_output_formats_emits_one_per_line(capsys):
    rc, out, _ = _run(['--list-output-formats'], capsys)
    assert rc == 0
    lines = out.strip().splitlines()
    assert 'pdf' in lines and 'html' in lines and 'pptx' in lines


def test_list_extensions_emits_known_extensions(capsys):
    rc, out, _ = _run(['--list-extensions'], capsys)
    assert rc == 0
    assert '+smart' in out.splitlines() and '+footnotes' in out.splitlines()


def test_print_default_template_html(capsys):
    rc, out, _ = _run(['--print-default-template', 'html'], capsys)
    assert rc == 0
    assert '<!DOCTYPE html>' in out and '$body$' in out


def test_metadata_and_variable_round_trip_into_template(capsys):
    rc, out, _ = _run([
        str(SIMPLE_MD),
        '--from', 'markdown', '--to', 'html', '-s',
        '-V', 'title=My Title',
        '-V', 'lang=en',
        '-V', 'css=style.css',
    ], capsys)
    assert rc == 0
    assert '<title>My Title</title>' in out
    assert 'lang="en"' in out
    assert 'href="style.css"' in out
    assert '<h1 id="heading">Heading</h1>' in out


def test_shift_heading_level_by_increases_levels(capsys):
    rc, out, _ = _run([
        '-', '--from', 'markdown', '--to', 'markdown',
        '--shift-heading-level-by=1',
    ], capsys, stdin='# Top\n')
    assert rc == 0
    assert out.strip().startswith('## Top')


def test_filename_extension_drives_format_detection(capsys, tmp_path):
    src = tmp_path / 'sample.md'
    src.write_text('# Hi\n', encoding='utf-8')
    out_path = tmp_path / 'out.html'
    rc, _, _ = _run([str(src), '-o', str(out_path)], capsys)
    assert rc == 0
    assert out_path.read_text(encoding='utf-8').startswith('<h1')


def test_extension_suffix_does_not_break_format_resolution():
    options = parse_cli_options(['--from', 'markdown+smart-tex_math_dollars',
                                  '--to', 'html'])
    assert options.from_format == 'markdown'
    assert '+smart' not in options.to_extensions
    assert 'smart' in options.from_extensions


def test_template_default_round_trip_basic_html():
    template = get_default_template('html')
    assert template is not None
    rendered = render_template(template, {
        'body': '<p>hi</p>', 'lang': 'en', 'title-meta': 'T',
    })
    assert '<p>hi</p>' in rendered
    assert '<title>T</title>' in rendered


def test_template_iteration_and_separator():
    out = render_template('$for(items)$$it$$sep$, $endfor$', {'items': ['a', 'b', 'c']})
    assert out == 'a, b, c'


def test_template_conditional_with_else():
    out = render_template('$if(toc)$YES$else$NO$endif$', {'toc': True})
    assert out == 'YES'
    out = render_template('$if(toc)$YES$else$NO$endif$', {'toc': False})
    assert out == 'NO'


def test_template_pipe_uppercase():
    out = render_template('$name/uppercase$', {'name': 'hello'})
    assert out == 'HELLO'


def test_unsupported_format_returns_exit_code_2(capsys):
    rc, _, err = _run(['-f', 'xyzzy_unknown', '-t', 'html'], capsys)
    assert rc == 2
    assert 'Unsupported' in err


def test_version_flag(capsys):
    rc, out, _ = _run(['--version'], capsys)
    assert rc == 0
    assert out.startswith('pandoc_py ')
