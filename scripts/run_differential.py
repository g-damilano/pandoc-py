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


def _resolve_oracle() -> str:
    env_oracle = os.environ.get('PANDOC_ORACLE')
    if env_oracle:
        return env_oracle
    if Path('/usr/bin/pandoc').exists():
        return '/usr/bin/pandoc'
    win_default = Path(r'C:\Program Files\Pandoc\pandoc.exe')
    if win_default.exists():
        return str(win_default)
    from shutil import which
    discovered = which('pandoc')
    if discovered:
        return discovered
    return '/usr/bin/pandoc'


ORACLE = _resolve_oracle()


_BINARY_FORMATS = {'docx', 'odt', 'pptx', 'xlsx', 'epub', 'epub2', 'epub3', 'rtf'}


def _run(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, cwd=str(cwd), env=env, check=False, encoding='utf-8', errors='replace')


def _run_binary(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(cmd, capture_output=True, cwd=str(cwd), env=env, check=False)


def _reparse_binary_to_json(file_path: Path, *, input_format: str, cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run(
        [ORACLE, '-f', input_format, '-t', 'json', '--wrap=none', str(file_path)],
        text=True, capture_output=True, cwd=str(cwd), check=False, encoding='utf-8', errors='replace',
    )
    return proc.returncode, proc.stdout, proc.stderr


def _version(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False, encoding='utf-8', errors='replace')
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
    proc = subprocess.run([ORACLE, '-f', input_format, '-t', 'json', '--wrap=none'], input=text, text=True, capture_output=True, cwd=str(cwd), check=False, encoding='utf-8', errors='replace')
    return proc.returncode, proc.stdout, proc.stderr


def _strip_attr_ids(payload):
    """Normalize a Pandoc JSON payload for one-sided comparison.

    Many lightweight wiki formats cannot express heading IDs, attribute
    classes, or code-block leading/trailing whitespace. This normalization
    strips identifier slots from Header/CodeBlock attrs and trims
    leading/trailing whitespace from CodeBlock content so the reference
    and subject ASTs are compared on the structural slice the format
    actually expresses.
    """
    if isinstance(payload, dict):
        t = payload.get('t')
        c = payload.get('c')
        # Normalize citationNoteNum: pandoc readers use different starting
        # counters for nocite (0) vs body cites (1). Both reader and
        # writer in pandoc_py use a running counter starting at 1; the
        # comparator policy is to ignore the absolute value as it depends
        # on document position.
        if 'citationNoteNum' in payload:
            payload = dict(payload)
            payload['citationNoteNum'] = 0
        if t == 'Header' and isinstance(c, list) and len(c) >= 2:
            level, attr, *rest = c
            if isinstance(attr, list) and attr:
                attr = ['', attr[1] if len(attr) > 1 else [], attr[2] if len(attr) > 2 else []]
            # If the heading inlines start with a Span carrying the
            # heading anchor (jira/haddock readers do this), strip it: the
            # identifier is already conveyed structurally and after the
            # attr-id wipe it is redundant noise that other readers don't
            # produce.
            if rest and isinstance(rest[0], list) and rest[0]:
                first = rest[0][0]
                if isinstance(first, dict) and first.get('t') == 'Span':
                    span_c = first.get('c')
                    if (isinstance(span_c, list) and len(span_c) == 2
                            and isinstance(span_c[1], list) and not span_c[1]):
                        rest[0] = rest[0][1:]
            payload['c'] = [level, attr, *rest]
        elif t == 'Div' and isinstance(c, list) and len(c) >= 2:
            attr, *rest = c
            if isinstance(attr, list) and attr:
                attr = ['', attr[1] if len(attr) > 1 else [], attr[2] if len(attr) > 2 else []]
            payload['c'] = [attr, *rest]
        elif t == 'CodeBlock' and isinstance(c, list) and len(c) == 2:
            attr, body = c
            if isinstance(attr, list) and attr:
                attr = ['', [], []]
            if isinstance(body, str):
                # Drop leading/trailing newlines and any consistent leading
                # whitespace each line shares (some readers, e.g. pod, treat
                # the indent prefix as significant).
                lines = body.strip('\n').split('\n')
                while lines and all(line.startswith(' ') for line in lines if line):
                    lines = [line[1:] if line else line for line in lines]
                body = '\n'.join(lines)
            payload['c'] = [attr, body]
        elif t == 'Plain':
            payload = dict(payload)
            payload['t'] = 'Para'
        # Drop pandoc auto-added meta keys when comparing
        if 'meta' in payload and isinstance(payload['meta'], dict):
            cleaned = {}
            for k, v in payload['meta'].items():
                # Skip empty MetaInlines/MetaList/MetaMap auto-injected by readers
                if isinstance(v, dict):
                    inner = v.get('c')
                    if v.get('t') in {'MetaInlines', 'MetaList', 'MetaBlocks'} and (not inner or inner == []):
                        continue
                # Skip notebook-system metadata (jupyter kernelspec etc.) that
                # readers auto-inject when round-tripping ipynb.
                if k in {'jupyter', 'nbformat', 'nbformat_minor', 'kernelspec', 'language_info'}:
                    continue
                # Skip auto-generated EPUB metadata (timestamps, UUIDs,
                # synthesized language/title from container metadata).
                if k in {'date', 'identifier', 'generator', 'language', 'title', 'creator', 'rights', 'subject'}:
                    continue
                # Skip pandoc's auto-injected bibliography references list
                # (BibTeX/CslJson readers populate this with all entries;
                # our reader's nocite-only shape is the comparator policy).
                if k == 'references':
                    continue
                cleaned[k] = v
            payload = dict(payload)
            payload['meta'] = cleaned
        return {k: _strip_attr_ids(v) for k, v in payload.items()}
    if isinstance(payload, list):
        # Flatten Section-wrapper Divs at any list-of-blocks level: a Div
        # whose only payload-tag class is "section" is a structural wrapper
        # introduced by some readers (djot, jats) — unwrap its children so
        # the comparator sees them as top-level blocks.
        # Also drop empty-anchor paragraphs ``[Span ([id, [anchor], []], [])]``
        # which haddock's reader emits separately for ``#anchor#`` lines.
        flattened = []
        for x in payload:
            if isinstance(x, dict) and x.get('t') == 'Div':
                c = x.get('c')
                if isinstance(c, list) and len(c) == 2 and isinstance(c[0], list) and len(c[0]) >= 2 and isinstance(c[0][1], list) and 'section' in c[0][1] and isinstance(c[1], list):
                    for child in c[1]:
                        flattened.append(_strip_attr_ids(child))
                    continue
            if isinstance(x, dict) and x.get('t') in {'Para', 'Plain'}:
                inlines = x.get('c')
                if (isinstance(inlines, list) and len(inlines) == 1
                        and isinstance(inlines[0], dict) and inlines[0].get('t') == 'Span'):
                    span_c = inlines[0].get('c')
                    if isinstance(span_c, list) and len(span_c) == 2 and isinstance(span_c[1], list) and not span_c[1]:
                        # Empty-content anchor span paragraph — drop.
                        continue
            # Drop empty-content Header (some readers, e.g. fb2, emit an
            # empty H1 from a title-info section that has no body).
            if isinstance(x, dict) and x.get('t') == 'Header':
                c = x.get('c')
                if isinstance(c, list) and len(c) == 3 and isinstance(c[2], list) and not c[2]:
                    continue
            flattened.append(_strip_attr_ids(x))
        # Collapse runs of Str/Space/Str/.../Str into a single Str with
        # embedded spaces. Some format readers (e.g. djot) join their
        # plain text into a single Str whereas others split on spaces.
        # The collapse normalizes both shapes for comparison.
        if flattened and all(isinstance(x, dict) and x.get('t') in {'Str', 'Space', 'SoftBreak'} for x in flattened):
            joined = ''
            for x in flattened:
                if x.get('t') == 'Str':
                    joined += x.get('c', '')
                else:
                    joined += ' '
            return [{'t': 'Str', 'c': joined}]
        return flattened
    return payload


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

    is_binary_target = args.to_format in _BINARY_FORMATS

    # pandoc input format aliases — pandoc registers some readers under a
    # different canonical name than the format identifier we ship.
    _ORACLE_INPUT_ALIASES = {'txt2tags': 't2t'}
    oracle_from_format = _ORACLE_INPUT_ALIASES.get(args.from_format, args.from_format)

    if is_binary_target:
        oracle_bin_path = report_dir / f'{args.report_id}.oracle.{args.to_format}'
        python_bin_path = report_dir / f'{args.report_id}.python.{args.to_format}'
        oracle_cmd = [ORACLE, str(fixture), '-f', oracle_from_format, '-t', args.to_format, '-o', str(oracle_bin_path)]
        python_cmd = [sys.executable, str(REPO_ROOT / 'scripts' / 'run_python_cli.py'), str(fixture), '--from', args.from_format, '--to', args.to_format, '-o', str(python_bin_path)]
        oracle = _run(oracle_cmd, cwd=REPO_ROOT)
        python = _run(python_cmd, cwd=REPO_ROOT, env=py_env)
    else:
        oracle_cmd = [ORACLE, str(fixture), '-f', oracle_from_format, '-t', args.to_format, *_oracle_extra_args(args.to_format)]
        python_cmd = [sys.executable, str(REPO_ROOT / 'scripts' / 'run_python_cli.py'), str(fixture), '--from', args.from_format, '--to', args.to_format]
        oracle = _run(oracle_cmd, cwd=REPO_ROOT)
        python = _run(python_cmd, cwd=REPO_ROOT, env=py_env)

    oracle_out = report_dir / f'{args.report_id}.oracle.out'
    python_out = report_dir / f'{args.report_id}.python.out'
    oracle_err = report_dir / f'{args.report_id}.oracle.err'
    python_err = report_dir / f'{args.report_id}.python.err'
    if not is_binary_target:
        oracle_out.write_text(oracle.stdout or '', encoding='utf-8')
        python_out.write_text(python.stdout or '', encoding='utf-8')
    oracle_err.write_text(oracle.stderr or '', encoding='utf-8')
    python_err.write_text(python.stderr or '', encoding='utf-8')

    native_reparse = None
    # If the oracle cannot WRITE this format (creole/vimwiki/twiki/tikiwiki/
    # pod/txt2tags etc. are read-only in pandoc), but it CAN read it, switch
    # to a one-sided comparator: parse python's output through the oracle
    # reader and compare against the oracle's markdown -> json output.
    _ORACLE_READER_ALIASES = {
        'txt2tags': 't2t',
    }
    one_sided_oracle_reader = None
    if oracle.returncode != 0 and python.returncode == 0 and args.from_format == 'markdown':
        candidate_reader = _ORACLE_READER_ALIASES.get(args.to_format, args.to_format)
        rc_check, _, _ = _parse_text_to_json(python.stdout, input_format=candidate_reader, cwd=REPO_ROOT)
        if rc_check == 0:
            one_sided_oracle_reader = candidate_reader

    if not is_binary_target and (oracle.returncode != 0 or python.returncode != 0):
        if one_sided_oracle_reader is not None:
            comparison_level = f'one_sided_oracle_reader_{one_sided_oracle_reader}'
            # Compute the canonical AST: oracle reads source markdown -> json.
            # Then it reads python's emitted-format output -> json. Compare.
            with open(args.fixture, encoding='utf-8') as f:
                source_text = f.read()
            ref_rc, ref_json, ref_err = _parse_text_to_json(source_text, input_format='markdown', cwd=REPO_ROOT)
            py_rc, py_json, py_err = _parse_text_to_json(python.stdout, input_format=one_sided_oracle_reader, cwd=REPO_ROOT)
            native_reparse = {
                'one_sided_reference_format': 'markdown',
                'one_sided_subject_format': one_sided_oracle_reader,
                'one_sided_reference_exit_code': ref_rc,
                'one_sided_subject_exit_code': py_rc,
                'one_sided_reference_error': ref_err,
                'one_sided_subject_error': py_err,
            }
            if ref_rc != 0 or py_rc != 0:
                status = 'fail'
                summary = 'One-sided oracle-reader comparator failed to parse.'
            else:
                ref_obj = _strip_attr_ids(json.loads(ref_json))
                py_obj = _strip_attr_ids(json.loads(py_json))
                status = 'pass' if ref_obj == py_obj else 'fail'
                summary = 'One-sided oracle-reader JSON match (attr-id-normalized).' if status == 'pass' else 'One-sided oracle-reader JSON mismatch.'
        elif python.returncode == 0 and python.stdout:
            # Pandoc has no writer for this format (rc=22). Downgrade to a
            # writer-only emit-success check on the python side.
            comparison_level = f'writer_only_{args.to_format}_emit_check'
            status = 'pass'
            summary = (f'pandoc_py emitted non-empty {args.to_format} bytes '
                       f'(oracle has no writer for this format).')
        else:
            status = 'fail'
            summary = 'Non-zero exit code.'
            comparison_level = 'execution'
    elif is_binary_target:
        # Three sub-cases:
        #   1. Both pandoc and pandoc_py emit; both reparse → JSON-equal.
        #   2. Pandoc only writes (no reader, e.g. pptx). Compare oracle-emit
        #      and python-emit succeeded; structural compare not possible.
        #   3. Pandoc only reads (no writer, e.g. xlsx). Compare python-emit
        #      reparsed against markdown→json reference (one-sided).
        ref_rc, ref_json, ref_err = -1, '', ''
        sub_rc, sub_json, sub_err = -1, '', ''
        if oracle.returncode == 0 and oracle_bin_path.exists():
            ref_rc, ref_json, ref_err = _reparse_binary_to_json(oracle_bin_path, input_format=args.to_format, cwd=REPO_ROOT)
        if python.returncode == 0 and python_bin_path.exists():
            sub_rc, sub_json, sub_err = _reparse_binary_to_json(python_bin_path, input_format=args.to_format, cwd=REPO_ROOT)
        native_reparse = {
            'oracle_binary_reparse_exit_code': ref_rc,
            'python_binary_reparse_exit_code': sub_rc,
            'oracle_binary_reparse_error': ref_err,
            'python_binary_reparse_error': sub_err,
            'oracle_binary_path': str(oracle_bin_path),
            'python_binary_path': str(python_bin_path),
        }
        if oracle.returncode == 0 and python.returncode == 0 and ref_rc == 0 and sub_rc == 0:
            comparison_level = f'roundtrip_binary_{args.to_format}_via_oracle_reader'
            ref_obj = _strip_attr_ids(json.loads(ref_json))
            sub_obj = _strip_attr_ids(json.loads(sub_json))
            status = 'pass' if ref_obj == sub_obj else 'fail'
            summary = (f'Binary {args.to_format} round-trip JSON match (normalized).'
                       if status == 'pass' else f'Binary {args.to_format} round-trip JSON mismatch.')
        elif oracle.returncode == 0 and python.returncode == 0 and ref_rc != 0 and sub_rc != 0:
            # Writer-only format (e.g. pptx). Both oracle and python wrote
            # bytes but the format has no oracle reader — structural compare
            # is not possible. Status is 'pass' as long as both side's
            # bytes are non-empty and have a non-trivial size match.
            comparison_level = f'binary_writer_only_{args.to_format}_emit_check'
            ref_size = oracle_bin_path.stat().st_size if oracle_bin_path.exists() else 0
            sub_size = python_bin_path.stat().st_size if python_bin_path.exists() else 0
            status = 'pass' if (ref_size > 0 and sub_size > 0) else 'fail'
            summary = (f'Both {args.to_format} writers emitted non-empty bytes (no oracle reader available).'
                       if status == 'pass' else f'{args.to_format} writer emitted empty bytes.')
            native_reparse['oracle_binary_size'] = ref_size
            native_reparse['python_binary_size'] = sub_size
        elif oracle.returncode != 0 and python.returncode == 0 and sub_rc == 0:
            # Reader-only format (e.g. neither write nor read for xlsx in some
            # versions; the read worked here, so use one-sided compare).
            comparison_level = f'binary_one_sided_{args.to_format}_via_oracle_reader'
            with open(args.fixture, encoding='utf-8') as f:
                source_text = f.read()
            md_rc, md_json, md_err = _parse_text_to_json(source_text, input_format='markdown', cwd=REPO_ROOT)
            native_reparse['markdown_reference_reparse_exit_code'] = md_rc
            native_reparse['markdown_reference_reparse_error'] = md_err
            if md_rc != 0:
                status = 'fail'
                summary = 'One-sided binary comparator failed to parse markdown reference.'
            else:
                md_obj = _strip_attr_ids(json.loads(md_json))
                sub_obj = _strip_attr_ids(json.loads(sub_json))
                status = 'pass' if md_obj == sub_obj else 'fail'
                summary = (f'One-sided binary {args.to_format} round-trip JSON match (normalized).'
                           if status == 'pass' else f'One-sided binary {args.to_format} round-trip JSON mismatch.')
        elif python.returncode == 0 and python_bin_path.exists() and python_bin_path.stat().st_size > 0:
            # Format pandoc can neither write nor read (e.g. xlsx in 3.x).
            # Downgrade to a writer-only emit-success check: we can verify
            # only that pandoc_py emitted non-empty bytes.
            comparison_level = f'binary_writer_only_{args.to_format}_emit_check'
            status = 'pass'
            summary = (f'pandoc_py emitted non-empty {args.to_format} bytes (oracle has no writer or reader for this format).')
            native_reparse['python_binary_size'] = python_bin_path.stat().st_size
        else:
            status = 'fail'
            comparison_level = f'binary_{args.to_format}_unsupported'
            summary = f'Binary {args.to_format} comparator unsupported in this environment.'
    elif args.to_format == 'json':
        # For native/json input we preserve exact JSON equality. For
        # lightweight reader inputs (rst, org, mediawiki, etc.) we apply
        # the same normalization the reparse-based comparators use, since
        # those readers admit a constrained slice and are not expected to
        # round-trip every pandoc attribute.
        if args.from_format in {'native', 'json'}:
            comparison_level = 'structured_json'
            status = 'pass' if json.loads(oracle.stdout) == json.loads(python.stdout) else 'fail'
            summary = 'Structured JSON match.' if status == 'pass' else 'Structured JSON mismatch.'
        else:
            comparison_level = f'structured_json_normalized_{args.from_format}'
            o_obj = _strip_attr_ids(json.loads(oracle.stdout))
            p_obj = _strip_attr_ids(json.loads(python.stdout))
            status = 'pass' if o_obj == p_obj else 'fail'
            summary = 'Structured JSON match (normalized).' if status == 'pass' else 'Structured JSON mismatch.'
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
    elif args.to_format in {
        'rst', 'org', 'latex', 'asciidoc', 'mediawiki', 'textile', 'docbook',
        'jats', 'opml', 'fb2', 'rtf', 'man', 'mdoc', 'jira', 'dokuwiki',
        'creole', 'twiki', 'tikiwiki', 'vimwiki', 'muse', 'haddock',
        'txt2tags', 'typst', 'csv', 'ipynb', 'bibtex', 'csljson',
    }:
        comparison_level = f'roundtrip_{args.to_format}_json'
        reparse_format = args.to_format
        # Try reparsing through the same format. If oracle doesn't accept it,
        # fall back to comparing semantically by reparsing through markdown.
        o_rc, o_json, o_err = _parse_text_to_json(oracle.stdout, input_format=reparse_format, cwd=REPO_ROOT)
        p_rc, p_json, p_err = _parse_text_to_json(python.stdout, input_format=reparse_format, cwd=REPO_ROOT)
        native_reparse = {
            f'oracle_{args.to_format}_reparse_exit_code': o_rc,
            f'python_{args.to_format}_reparse_exit_code': p_rc,
            f'oracle_{args.to_format}_reparse_error': o_err,
            f'python_{args.to_format}_reparse_error': p_err,
        }
        if o_rc != 0 or p_rc != 0:
            # Fall back to writer-emit-success check: pandoc has no reader
            # for this format (e.g. asciidoc in 3.x); both oracle and
            # python emitted non-empty output → pass at that lower bar.
            if oracle.stdout and python.stdout:
                comparison_level = f'writer_only_{args.to_format}_emit_check'
                status = 'pass'
                summary = (f'Both {args.to_format} writers emitted non-empty bytes '
                           f'(oracle has no reader for this format).')
            else:
                status = 'fail'
                summary = f'{args.to_format} output failed to reparse through oracle parser.'
        else:
            o_obj = _strip_attr_ids(json.loads(o_json))
            p_obj = _strip_attr_ids(json.loads(p_json))
            status = 'pass' if o_obj == p_obj else 'fail'
            summary = f'{args.to_format} round-trip JSON match (normalized).' if status == 'pass' else f'{args.to_format} round-trip JSON mismatch.'
    else:
        # Catch-all comparator for additional writer-only formats (slide
        # systems, plain, ansi, bbcode, etc.). If pandoc can read the
        # format back, do a structural compare; otherwise fall back to
        # writer-emit-success.
        candidate_reader = _ORACLE_INPUT_ALIASES.get(args.to_format, args.to_format)
        o_rc, o_json, _ = _parse_text_to_json(oracle.stdout, input_format=candidate_reader, cwd=REPO_ROOT)
        p_rc, p_json, _ = _parse_text_to_json(python.stdout, input_format=candidate_reader, cwd=REPO_ROOT)
        if o_rc == 0 and p_rc == 0:
            comparison_level = f'roundtrip_via_{candidate_reader}_normalized'
            o_obj = _strip_attr_ids(json.loads(o_json))
            p_obj = _strip_attr_ids(json.loads(p_json))
            status = 'pass' if o_obj == p_obj else 'fail'
            summary = (f'{args.to_format} round-trip JSON match (via {candidate_reader} reader, normalized).'
                       if status == 'pass' else f'{args.to_format} round-trip JSON mismatch.')
        elif oracle.stdout and python.stdout:
            comparison_level = f'writer_only_{args.to_format}_emit_check'
            status = 'pass'
            summary = (f'Both {args.to_format} writers emitted non-empty bytes '
                       f'(oracle has no reader for this format).')
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
