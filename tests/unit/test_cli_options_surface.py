from __future__ import annotations

import io
from pathlib import Path

import pytest

from pandoc_py import __version__
from pandoc_py.app import AppError, convert_text
from pandoc_py.cli.main import main
from pandoc_py.cli.options import CliOptions, OptionError, format_version_banner, normalize_format, parse_cli_options
from pandoc_py.parsing.common import (
    ParsingError,
    attr_is_empty,
    citation_suffix_inlines,
    normalize_newlines,
    normalize_reference_label,
    parse_attr_string,
    parse_plain_segment,
    split_trailing_attr,
)


def test_parse_cli_options_supports_short_flags_and_output() -> None:
    options = parse_cli_options(['input.md', '-f', 'markdown', '-t', 'html', '-o', 'out.html'])
    assert options == CliOptions(input_path='input.md', from_format='markdown', to_format='html', output_path='out.html', standalone=False, version=False)


def test_parse_cli_options_supports_standalone_flag() -> None:
    options = parse_cli_options(['input.md', '-f', 'markdown', '-t', 'native', '--standalone'])
    assert options.standalone is True


def test_parse_cli_options_supports_version_without_input() -> None:
    options = parse_cli_options(['--version'])
    assert options.version is True
    assert options.input_path == '-'


def test_normalize_format_accepts_surface_aliases() -> None:
    assert normalize_format('pandoc-json', role='input') == 'json'
    assert normalize_format('html5', role='output') == 'html'


@pytest.mark.parametrize('role,value', [('input', 'docx'), ('output', 'latex')])
def test_normalize_format_rejects_unsupported_values(role: str, value: str) -> None:
    with pytest.raises(OptionError):
        normalize_format(value, role=role)


def test_format_version_banner_uses_current_version() -> None:
    assert format_version_banner() == f'pandoc_py {__version__}\n'


def test_main_reads_stdin_when_input_path_is_dash(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr('sys.stdin', io.StringIO('# Heading\n'))
    rc = main(['-', '-f', 'markdown', '-t', 'json'])
    assert rc == 0
    out = capsys.readouterr().out
    assert 'Header' in out


def test_main_writes_output_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = tmp_path / 'input.md'
    source.write_text('# Heading\n', encoding='utf-8')
    target = tmp_path / 'output.html'
    rc = main([str(source), '-f', 'markdown', '-t', 'html', '-o', str(target)])
    assert rc == 0
    assert capsys.readouterr().out == ''
    assert '<h1' in target.read_text(encoding='utf-8')


def test_main_returns_error_for_unsupported_route(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(['-', '-f', 'docx', '-t', 'html'])
    assert rc == 2
    assert 'Unsupported input format' in capsys.readouterr().err


def test_app_convert_text_runs_current_json_route() -> None:
    json_source = '{"pandoc-api-version":[1,23,1],"meta":{},"blocks":[{"t":"Para","c":[{"t":"Str","c":"Hello"}]}]}'
    html = convert_text(json_source, 'json', 'html')
    assert '<p>Hello</p>' in html


def test_app_convert_text_native_standalone_wraps_output() -> None:
    native = convert_text('# Heading\n', 'markdown', 'native', standalone=True)
    assert native.startswith('Pandoc nullMeta ')


def test_app_convert_text_rejects_unknown_route() -> None:
    with pytest.raises(AppError):
        convert_text('Hello', 'docx', 'html')


def test_parsing_common_normalizes_newlines_and_reference_labels() -> None:
    assert normalize_newlines('a\r\nb\rc') == 'a\nb\nc'
    assert normalize_reference_label('  Alpha   Beta ') == 'alpha beta'


def test_parsing_common_parse_plain_segment_and_citation_suffix() -> None:
    assert [type(node).__name__ for node in parse_plain_segment('a  b')] == ['Str', 'Space', 'Str']
    suffix = citation_suffix_inlines('pp. 3-4')
    assert ''.join(getattr(node, 'text', ' ') for node in suffix).replace(' ', '') == 'pp.\xa03-4'


def test_parsing_common_attribute_helpers() -> None:
    attr = parse_attr_string('{#sec .x key="value"}')
    assert attr.identifier == 'sec'
    assert attr.classes == ['x']
    assert attr.attributes == [('key', 'value')]
    body, trailing = split_trailing_attr('Title {#sec .x}')
    assert body == 'Title'
    assert trailing.identifier == 'sec'
    assert attr_is_empty(parse_attr_string('{.x}')) is False


def test_parsing_common_rejects_empty_reference_label() -> None:
    with pytest.raises(ParsingError):
        normalize_reference_label('   ')
