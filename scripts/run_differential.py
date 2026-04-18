from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from lxml import etree, html

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
ORACLE = '/usr/bin/pandoc'


def _run(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, cwd=str(cwd), env=env, check=False)


def _version(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    text = (proc.stdout or proc.stderr).strip()
    return text.splitlines()[0] if text else 'unknown'


def _normalize_text(text: str | None, *, preserve: bool = False) -> str:
    if not text:
        return ''
    text = text.replace('\r\n', '\n').replace('\r', '\n').replace('\xa0', ' ')
    if preserve:
        return text
    return re.sub(r'\s+', ' ', text).strip()


def _html_fragments(text: str) -> list[object]:
    if not text.strip():
        return []
    return html.fragments_fromstring(text)


def _html_node_repr(node: object, *, preserve: bool = False) -> tuple:
    if isinstance(node, str):
        return ('text', _normalize_text(node, preserve=preserve))
    if isinstance(node, etree._Comment):
        return ('comment', _normalize_text(node.text), _normalize_text(node.tail))
    if not isinstance(node, etree._Element):
        return ('other', repr(node))
    tag = str(node.tag).lower()
    preserve_here = preserve or tag in {'pre', 'code'}
    attrs = tuple(sorted((str(k), str(v)) for k, v in node.attrib.items()))
    children: list[tuple] = []
    for child in node:
        children.append((_html_node_repr(child, preserve=preserve_here), _normalize_text(child.tail, preserve=preserve_here)))
    return ('elem', tag, attrs, _normalize_text(node.text, preserve=preserve_here), tuple(children))


def _normalized_html_repr(text: str) -> tuple:
    return tuple(_html_node_repr(node) for node in _html_fragments(text))


def _oracle_extra_args(to_format: str) -> list[str]:
    if to_format == 'html':
        return ['--mathjax', '--no-highlight', '--wrap=none']
    if to_format == 'native':
        return ['--wrap=none']
    if to_format in {'commonmark', 'commonmark_x'}:
        return ['--wrap=none']
    return []


def _parse_text_to_json(text: str, *, input_format: str, cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run([ORACLE, '-f', input_format, '-t', 'json', '--wrap=none'], input=text, text=True, capture_output=True, cwd=str(cwd), check=False)
    return proc.returncode, proc.stdout, proc.stderr


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('fixture')
    parser.add_argument('--from', dest='from_format', required=True)
    parser.add_argument('--to', dest='to_format', required=True)
    parser.add_argument('--report-id', required=True)
    parser.add_argument('--report-dir', default=str(REPO_ROOT / 'tests' / 'differential' / 'reports' / 'smoke'))
    args = parser.parse_args(argv)

    fixture = Path(args.fixture).resolve()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    py_env = dict(os.environ)
    py_env['PYTHONPATH'] = str(SRC_ROOT) + (os.pathsep + py_env['PYTHONPATH'] if py_env.get('PYTHONPATH') else '')

    oracle_cmd = [ORACLE, str(fixture), '-f', args.from_format, '-t', args.to_format, *_oracle_extra_args(args.to_format)]
    python_cmd = [sys.executable, str(REPO_ROOT / 'scripts' / 'run_python_cli.py'), str(fixture), '--from', args.from_format, '--to', args.to_format]

    oracle = _run(oracle_cmd, cwd=REPO_ROOT)
    python = _run(python_cmd, cwd=REPO_ROOT, env=py_env)

    oracle_out = report_dir / f'{args.report_id}.oracle.out'
    python_out = report_dir / f'{args.report_id}.python.out'
    oracle_err = report_dir / f'{args.report_id}.oracle.err'
    python_err = report_dir / f'{args.report_id}.python.err'
    oracle_out.write_text(oracle.stdout, encoding='utf-8')
    python_out.write_text(python.stdout, encoding='utf-8')
    oracle_err.write_text(oracle.stderr, encoding='utf-8')
    python_err.write_text(python.stderr, encoding='utf-8')

    native_reparse = None
    if oracle.returncode != 0 or python.returncode != 0:
        status = 'fail'
        summary = 'Non-zero exit code.'
        comparison_level = 'execution'
    elif args.to_format == 'json':
        comparison_level = 'structured_json'
        status = 'pass' if json.loads(oracle.stdout) == json.loads(python.stdout) else 'fail'
        summary = 'Structured JSON match.' if status == 'pass' else 'Structured JSON mismatch.'
    elif args.to_format == 'html':
        comparison_level = 'normalized_html'
        status = 'pass' if _normalized_html_repr(oracle.stdout) == _normalized_html_repr(python.stdout) else 'fail'
        summary = 'Normalized HTML match.' if status == 'pass' else 'Normalized HTML mismatch.'
    elif args.to_format == 'native':
        comparison_level = 'roundtrip_native_json'
        oracle_native_rc, oracle_native_json, oracle_native_err = _parse_text_to_json(oracle.stdout, input_format='native', cwd=REPO_ROOT)
        python_native_rc, python_native_json, python_native_err = _parse_text_to_json(python.stdout, input_format='native', cwd=REPO_ROOT)
        native_reparse = {
            'oracle_native_reparse_exit_code': oracle_native_rc,
            'python_native_reparse_exit_code': python_native_rc,
            'oracle_native_reparse_error': oracle_native_err,
            'python_native_reparse_error': python_native_err,
        }
        if oracle_native_rc != 0 or python_native_rc != 0:
            status = 'fail'
            summary = 'Native output failed to reparse through oracle parser.'
        else:
            status = 'pass' if json.loads(oracle_native_json) == json.loads(python_native_json) else 'fail'
            summary = 'Native round-trip JSON match.' if status == 'pass' else 'Native round-trip JSON mismatch.'
    elif args.to_format == 'markdown':
        comparison_level = 'roundtrip_markdown_json'
        oracle_md_rc, oracle_md_json, oracle_md_err = _parse_text_to_json(oracle.stdout, input_format='markdown', cwd=REPO_ROOT)
        python_md_rc, python_md_json, python_md_err = _parse_text_to_json(python.stdout, input_format='markdown', cwd=REPO_ROOT)
        native_reparse = {
            'oracle_markdown_reparse_exit_code': oracle_md_rc,
            'python_markdown_reparse_exit_code': python_md_rc,
            'oracle_markdown_reparse_error': oracle_md_err,
            'python_markdown_reparse_error': python_md_err,
        }
        if oracle_md_rc != 0 or python_md_rc != 0:
            status = 'fail'
            summary = 'Markdown output failed to reparse through oracle parser.'
        else:
            status = 'pass' if json.loads(oracle_md_json) == json.loads(python_md_json) else 'fail'
            summary = 'Markdown round-trip JSON match.' if status == 'pass' else 'Markdown round-trip JSON mismatch.'
    elif args.to_format in {'commonmark', 'commonmark_x'}:
        comparison_level = 'roundtrip_commonmark_json' if args.to_format == 'commonmark' else 'roundtrip_commonmark_x_json'
        reparse_format = args.to_format
        oracle_cm_rc, oracle_cm_json, oracle_cm_err = _parse_text_to_json(oracle.stdout, input_format=reparse_format, cwd=REPO_ROOT)
        python_cm_rc, python_cm_json, python_cm_err = _parse_text_to_json(python.stdout, input_format=reparse_format, cwd=REPO_ROOT)
        native_reparse = {
            'oracle_commonmark_reparse_exit_code': oracle_cm_rc,
            'python_commonmark_reparse_exit_code': python_cm_rc,
            'oracle_commonmark_reparse_error': oracle_cm_err,
            'python_commonmark_reparse_error': python_cm_err,
        }
        if oracle_cm_rc != 0 or python_cm_rc != 0:
            status = 'fail'
            summary = f'{args.to_format} output failed to reparse through oracle parser.'
        else:
            status = 'pass' if json.loads(oracle_cm_json) == json.loads(python_cm_json) else 'fail'
            summary = f'{args.to_format} round-trip JSON match.' if status == 'pass' else f'{args.to_format} round-trip JSON mismatch.'
    else:
        comparison_level = 'byte'
        status = 'pass' if oracle.stdout == python.stdout else 'fail'
        summary = 'Byte-for-byte match.' if status == 'pass' else 'Byte mismatch.'

    report = {
        'fixture_id': args.report_id,
        'input_format': args.from_format,
        'output_format': args.to_format,
        'comparison_level': comparison_level,
        'oracle_command': oracle_cmd,
        'python_command': python_cmd,
        'oracle_version': _version([ORACLE, '--version']),
        'python_version': _version([sys.executable, str(REPO_ROOT / 'scripts' / 'run_python_cli.py'), '--version', '-']),
        'oracle_exit_code': oracle.returncode,
        'python_exit_code': python.returncode,
        'status': status,
        'summary': summary,
        'oracle_stdout_path': str(oracle_out),
        'python_stdout_path': str(python_out),
        'oracle_stderr_path': str(oracle_err),
        'python_stderr_path': str(python_err),
    }
    if native_reparse is not None:
        report.update(native_reparse)
    (report_dir / f'{args.report_id}.report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if status == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
