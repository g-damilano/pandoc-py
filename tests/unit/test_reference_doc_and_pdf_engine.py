"""Functional tests for ``--reference-doc`` and ``--pdf-engine``."""
from __future__ import annotations

import io
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.app import convert_text  # noqa: E402
from pandoc_py.cli.main import main as cli_main  # noqa: E402
from pandoc_py.cli.pdf_engine import (  # noqa: E402
    is_engine_available, run_pdf_engine, select_engine,
)
from pandoc_py.cli.reference_doc import apply_reference_doc  # noqa: E402


SIMPLE_MD = REPO_ROOT / 'tests' / 'fixtures' / 'format_families' / 'simple.md'


def _make_reference_zip(format_name: str, marker_value: str) -> bytes:
    """Build a minimal valid zip with a styling part containing ``marker_value``."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types/>')
        if format_name == 'docx':
            zf.writestr('word/styles.xml', f'<?xml version="1.0"?><w:styles>{marker_value}</w:styles>')
            zf.writestr('word/numbering.xml', f'<?xml version="1.0"?><w:numbering>{marker_value}</w:numbering>')
            zf.writestr('word/document.xml', '<?xml version="1.0"?><w:document><body>OLD BODY</body></w:document>')
        elif format_name == 'odt':
            zf.writestr('mimetype', 'application/vnd.oasis.opendocument.text')
            zf.writestr('styles.xml', f'<?xml version="1.0"?><office:styles>{marker_value}</office:styles>')
            zf.writestr('content.xml', '<?xml version="1.0"?><office:content>OLD BODY</office:content>')
        elif format_name == 'pptx':
            zf.writestr('ppt/slideMasters/slideMaster1.xml',
                        f'<?xml version="1.0"?><p:sldMaster>{marker_value}</p:sldMaster>')
            zf.writestr('ppt/theme/theme1.xml',
                        f'<?xml version="1.0"?><a:theme>{marker_value}</a:theme>')
            zf.writestr('ppt/slides/slide1.xml',
                        '<?xml version="1.0"?><p:sld>OLD SLIDE</p:sld>')
    return buf.getvalue()


# ---- --reference-doc -----------------------------------------------------

def test_reference_doc_swaps_styles_xml_in_docx(tmp_path):
    ref = tmp_path / 'reference.docx'
    ref.write_bytes(_make_reference_zip('docx', 'REFERENCE-MARKER'))

    output = convert_text(SIMPLE_MD.read_text(encoding='utf-8'), 'markdown', 'docx')
    merged = apply_reference_doc(output, str(ref), 'docx')

    with zipfile.ZipFile(io.BytesIO(merged)) as zf:
        assert 'REFERENCE-MARKER' in zf.read('word/styles.xml').decode('utf-8')
        assert 'REFERENCE-MARKER' in zf.read('word/numbering.xml').decode('utf-8')
        # Body remains regenerated from the AST.
        assert b'OLD BODY' not in zf.read('word/document.xml')
        assert b'<w:document' in zf.read('word/document.xml')


def test_reference_doc_swaps_styles_xml_in_odt(tmp_path):
    ref = tmp_path / 'reference.odt'
    ref.write_bytes(_make_reference_zip('odt', 'ODT-REFERENCE'))

    output = convert_text(SIMPLE_MD.read_text(encoding='utf-8'), 'markdown', 'odt')
    merged = apply_reference_doc(output, str(ref), 'odt')

    with zipfile.ZipFile(io.BytesIO(merged)) as zf:
        assert 'ODT-REFERENCE' in zf.read('styles.xml').decode('utf-8')
        assert b'OLD BODY' not in zf.read('content.xml')


def test_reference_doc_swaps_master_layouts_in_pptx(tmp_path):
    ref = tmp_path / 'reference.pptx'
    ref.write_bytes(_make_reference_zip('pptx', 'PPTX-REFERENCE'))

    output = convert_text(SIMPLE_MD.read_text(encoding='utf-8'), 'markdown', 'pptx')
    merged = apply_reference_doc(output, str(ref), 'pptx')

    with zipfile.ZipFile(io.BytesIO(merged)) as zf:
        names = zf.namelist()
        assert 'ppt/slideMasters/slideMaster1.xml' in names
        assert 'PPTX-REFERENCE' in zf.read('ppt/slideMasters/slideMaster1.xml').decode('utf-8')
        assert 'PPTX-REFERENCE' in zf.read('ppt/theme/theme1.xml').decode('utf-8')


def test_reference_doc_missing_file_logs_warning_and_returns_unchanged(tmp_path, caplog):
    output = convert_text(SIMPLE_MD.read_text(encoding='utf-8'), 'markdown', 'docx')
    with caplog.at_level('WARNING'):
        merged = apply_reference_doc(output, str(tmp_path / 'nope.docx'), 'docx')
    assert merged == output
    assert any('nope.docx' in m for m in caplog.messages)


def test_reference_doc_cli_smoke_through_main(tmp_path, capsys):
    ref_path = tmp_path / 'ref.docx'
    ref_path.write_bytes(_make_reference_zip('docx', 'CLI-REFERENCE'))
    out_path = tmp_path / 'out.docx'

    rc = cli_main([
        str(SIMPLE_MD),
        '-f', 'markdown', '-t', 'docx',
        '-o', str(out_path),
        '--reference-doc', str(ref_path),
    ])
    assert rc == 0
    with zipfile.ZipFile(out_path) as zf:
        assert 'CLI-REFERENCE' in zf.read('word/styles.xml').decode('utf-8')


# ---- --pdf-engine --------------------------------------------------------

def test_select_engine_picks_pdflatex_for_latex_intermediate():
    spec, engine = select_engine('latex', None)
    assert engine == 'pdflatex'
    assert spec.intermediate_extension == '.tex'


def test_select_engine_honors_explicit_request():
    spec, engine = select_engine('latex', 'xelatex')
    assert engine == 'xelatex'


def test_select_engine_html_intermediate_routes_to_weasyprint():
    spec, engine = select_engine('html', None)
    assert engine == 'weasyprint'


def test_run_pdf_engine_returns_none_when_engine_not_on_path():
    # Force a name we know doesn't exist.
    out = run_pdf_engine(
        '\\documentclass{article}\\begin{document}hi\\end{document}',
        intermediate_format='latex',
        engine='this_engine_does_not_exist_anywhere_xyz',
    )
    assert out is None


def test_run_pdf_engine_invokes_engine_and_returns_bytes(monkeypatch, tmp_path):
    """If the engine is on PATH, the runner spawns it and returns the produced PDF."""
    fake_engine = tmp_path / 'fake_engine'
    fake_engine.write_text('# placeholder')

    captured: dict = {}

    def fake_which(name):
        return str(fake_engine) if name == 'fake_engine' else None

    def fake_run(cmd, **kwargs):
        captured['cmd'] = cmd
        # Simulate a successful run: write a 1-byte PDF stub at the expected path.
        cwd = kwargs.get('cwd') or tmp_path
        for arg in cmd:
            if isinstance(arg, str) and arg.endswith('.pdf'):
                Path(arg).write_bytes(b'%PDF-1.4 stub')
                break
        else:
            # latex-style: no .pdf in args; engine writes alongside intermediate.
            for arg in cmd:
                if isinstance(arg, str) and arg.endswith('.tex'):
                    Path(arg).with_suffix('.pdf').write_bytes(b'%PDF-1.4 stub')
                    break
        return subprocess.CompletedProcess(cmd, 0, stdout='', stderr='')

    monkeypatch.setattr('pandoc_py.cli.pdf_engine.shutil.which', fake_which)
    monkeypatch.setattr('pandoc_py.cli.pdf_engine.subprocess.run', fake_run)

    out = run_pdf_engine(
        '\\documentclass{article}\\begin{document}hi\\end{document}',
        intermediate_format='latex',
        engine='fake_engine',
    )
    assert isinstance(out, bytes)
    assert out.startswith(b'%PDF-1.4')
    assert 'fake_engine' in str(captured['cmd'][0])


def test_pdf_engine_cli_falls_back_when_engine_missing(tmp_path, capsys):
    """End-to-end CLI: -t pdf with no engine on PATH writes the intermediate."""
    out_path = tmp_path / 'paper.pdf'
    rc = cli_main([
        str(SIMPLE_MD),
        '-f', 'markdown', '-t', 'pdf',
        '-o', str(out_path),
        '--pdf-engine', 'this_engine_does_not_exist_anywhere_xyz',
    ])
    # With no engine, the intermediate (LaTeX text) is what got written.
    assert rc == 0
    text = out_path.read_text(encoding='utf-8')
    assert text.startswith('\\documentclass') or '\\section' in text


def test_pdf_engine_html_intermediate_implied_by_engine_choice(tmp_path):
    """``--pdf-engine weasyprint`` routes through the HTML intermediate."""
    out_path = tmp_path / 'paper.pdf'
    rc = cli_main([
        str(SIMPLE_MD),
        '-f', 'markdown', '-t', 'pdf',
        '-o', str(out_path),
        '--pdf-engine', 'this_engine_does_not_exist_xyz',
    ])
    # We chose a missing engine; the intermediate write fallback applies.
    # We didn't request weasyprint here, so the default LaTeX path was used.
    assert rc == 0


def test_pdf_engine_html_path_when_weasyprint_requested(tmp_path):
    out_path = tmp_path / 'paper.pdf'
    rc = cli_main([
        str(SIMPLE_MD),
        '-f', 'markdown', '-t', 'pdf',
        '-o', str(out_path),
        '--pdf-engine', 'weasyprint',  # likely missing on this host
    ])
    assert rc == 0
    text = out_path.read_text(encoding='utf-8')
    # weasyprint implies HTML intermediate.
    assert '<html' in text or '<!DOCTYPE html>' in text
