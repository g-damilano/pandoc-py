"""``--pdf-engine`` support: render the document via an external engine.

When the user requests ``-t pdf`` (or ``-o foo.pdf``), we route the
document through an intermediate text writer (LaTeX by default; can be
HTML/ms/typst/context) and then invoke the engine on the result. The
resulting PDF bytes are returned.

If no engine is on the host's ``PATH``, ``run_pdf_engine`` returns
``None`` and the caller falls back to writer-only emit-success.

Engine routing matches the pandoc reference table:

* ``-t latex``  → ``pdflatex`` (alts: ``xelatex``, ``lualatex``,
  ``tectonic``, ``latexmk``)
* ``-t context`` → ``context``
* ``-t html``    → ``weasyprint`` (alts: ``prince``, ``wkhtmltopdf``,
  ``pagedjs-cli``)
* ``-t ms``      → ``groff`` (alt: ``pdfroff``)
* ``-t typst``   → ``typst``

The engine is taken from ``--pdf-engine`` if supplied, else the writer
default. Extra engine flags are taken from ``--pdf-engine-opt``.
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

_LOG = logging.getLogger('pandoc_py')


@dataclass(frozen=True)
class _EngineSpec:
    intermediate_format: str
    engine_default: str
    intermediate_extension: str
    invocation: str  # 'latex', 'wkhtmltopdf', 'groff', 'typst', 'context'


_PER_INTERMEDIATE: dict[str, _EngineSpec] = {
    'latex':   _EngineSpec('latex', 'pdflatex', '.tex', 'latex'),
    'beamer':  _EngineSpec('beamer', 'pdflatex', '.tex', 'latex'),
    'tex':     _EngineSpec('latex', 'pdflatex', '.tex', 'latex'),
    'context': _EngineSpec('context', 'context', '.tex', 'context'),
    'html':    _EngineSpec('html', 'weasyprint', '.html', 'wkhtmltopdf'),
    'html5':   _EngineSpec('html', 'weasyprint', '.html', 'wkhtmltopdf'),
    'ms':      _EngineSpec('ms', 'groff', '.ms', 'groff'),
    'typst':   _EngineSpec('typst', 'typst', '.typ', 'typst'),
}


def select_engine(intermediate_format: str | None, requested: str | None) -> tuple[_EngineSpec, str]:
    """Pick the (spec, engine) tuple based on the writer choice + flag.

    `intermediate_format` is the writer the caller chose (e.g. 'latex'); we
    use it to look up defaults. Falls back to LaTeX if unknown.
    """
    fmt = (intermediate_format or 'latex').lower()
    spec = _PER_INTERMEDIATE.get(fmt, _PER_INTERMEDIATE['latex'])
    engine = requested or spec.engine_default
    return spec, engine


def is_engine_available(engine: str) -> bool:
    return shutil.which(engine) is not None


def run_pdf_engine(
    intermediate_text: str,
    *,
    intermediate_format: str | None,
    engine: str | None = None,
    engine_opts: Iterable[str] = (),
    workdir: str | None = None,
) -> bytes | None:
    """Run the chosen PDF engine and return the resulting PDF bytes.

    Returns ``None`` if the engine is not available on the host. Raises
    ``RuntimeError`` if the engine is available but exits with a
    non-zero status, with the engine's stderr attached.
    """
    spec, engine_name = select_engine(intermediate_format, engine)
    if not is_engine_available(engine_name):
        _LOG.warning(
            'PDF engine %s not on PATH; cannot render PDF. '
            'Install %s or pass --pdf-engine to choose another.',
            engine_name, engine_name,
        )
        return None

    with tempfile.TemporaryDirectory(prefix='pandoc_py_pdf_') as tmp:
        base = Path(tmp) / 'doc'
        intermediate_path = base.with_suffix(spec.intermediate_extension)
        intermediate_path.write_text(intermediate_text, encoding='utf-8')
        pdf_path = base.with_suffix('.pdf')

        cmd = _build_command(spec, engine_name, intermediate_path, pdf_path, list(engine_opts))
        _LOG.info('Running PDF engine: %s', ' '.join(cmd))
        proc = subprocess.run(cmd, capture_output=True, cwd=tmp, text=True, check=False)
        if proc.returncode != 0:
            stderr = (proc.stderr or '').strip().splitlines()[-20:]
            raise RuntimeError(
                f'{engine_name} exited with {proc.returncode}: '
                + ('\n'.join(stderr) if stderr else '(no stderr)')
            )
        if not pdf_path.exists():
            # Some engines (e.g. groff -Tpdf) write to stdout; capture it.
            if proc.stdout:
                stdout_data = proc.stdout.encode('latin-1', errors='replace')
                if stdout_data.startswith(b'%PDF'):
                    return stdout_data
            raise RuntimeError(f'{engine_name} did not produce a PDF output file.')
        return pdf_path.read_bytes()


def _build_command(spec: _EngineSpec, engine: str, intermediate: Path, pdf: Path, opts: list[str]) -> list[str]:
    if spec.invocation == 'latex':
        cmd = [engine, '-interaction=nonstopmode', '-output-directory', str(intermediate.parent), str(intermediate)]
        return cmd + opts
    if spec.invocation == 'context':
        return [engine, *opts, str(intermediate)]
    if spec.invocation == 'wkhtmltopdf':
        # weasyprint: weasyprint INPUT OUTPUT
        # wkhtmltopdf:  wkhtmltopdf INPUT OUTPUT
        # prince:       prince INPUT -o OUTPUT
        # pagedjs-cli:  pagedjs-cli INPUT -o OUTPUT
        if engine == 'prince' or engine == 'pagedjs-cli':
            return [engine, str(intermediate), '-o', str(pdf), *opts]
        return [engine, *opts, str(intermediate), str(pdf)]
    if spec.invocation == 'groff':
        # groff -Tpdf -ms FILE > out.pdf  (we capture stdout)
        return [engine, '-Tpdf', '-ms', *opts, str(intermediate)]
    if spec.invocation == 'typst':
        return [engine, 'compile', *opts, str(intermediate), str(pdf)]
    return [engine, str(intermediate)]
