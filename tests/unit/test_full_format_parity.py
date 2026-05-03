"""Full-format-parity audit.

Asserts that:

1. Every input format pandoc supports is registered as a pandoc_py
   reader (or alias).
2. Every output format pandoc supports is registered as a pandoc_py
   writer (or alias).
3. Each registered writer produces non-empty output for the canonical
   ``simple.md`` fixture (or, for binary writers, non-empty bytes).
4. Each text-format registered reader can round-trip its own writer's
   output back into a non-empty Document.

These tests pin "functional parity" for every document family.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.app import convert_text  # noqa: E402
from pandoc_py.io import (  # noqa: E402
    get_reader, get_writer, list_aliases, list_readers, list_writers,
)


SIMPLE_MARKDOWN = (REPO_ROOT / 'tests' / 'fixtures' / 'format_families' / 'simple.md').read_text(encoding='utf-8')


def _normalize(name: str) -> str:
    return name.replace('-', '_').lower()


def _pandoc_format_set(flag: str) -> set[str]:
    bin_path = (
        Path('/usr/bin/pandoc') if Path('/usr/bin/pandoc').exists()
        else Path(r'C:\Program Files\Pandoc\pandoc.exe')
        if Path(r'C:\Program Files\Pandoc\pandoc.exe').exists()
        else None
    )
    if bin_path is None:
        bin_path = shutil.which('pandoc')
    if bin_path is None:
        return set()
    return set(subprocess.run([str(bin_path), flag], capture_output=True, text=True).stdout.split())


def _registered_names(side: str) -> set[str]:
    canonical = list_readers() if side == 'reader' else list_writers()
    aliases = list_aliases()
    out: set[str] = set()
    for c in canonical:
        out.add(_normalize(c))
    for canon, al in aliases.items():
        for a in al:
            out.add(_normalize(a))
    return out


@pytest.mark.parametrize('flag,side', [
    ('--list-input-formats', 'reader'),
    ('--list-output-formats', 'writer'),
])
def test_pandoc_py_covers_every_pandoc_format(flag, side):
    expected = _pandoc_format_set(flag)
    if not expected:
        pytest.skip('Pandoc not available on this host.')
    actual = _registered_names(side)
    missing = {_normalize(f) for f in expected} - actual
    assert not missing, f'pandoc_py is missing {side}s for: {sorted(missing)}'


@pytest.mark.parametrize('writer_name', sorted(list_writers()))
def test_every_writer_emits_non_empty_output(writer_name):
    out = convert_text(SIMPLE_MARKDOWN, 'markdown', writer_name)
    assert out, f'Writer {writer_name!r} returned empty output.'
    if isinstance(out, bytes):
        assert len(out) > 0
    else:
        assert out.strip()


_TEXT_BINARY_SKIP_READERS = {
    # PDF is a write-only target (no reader, deliberately).
    'pdf',
}


@pytest.mark.parametrize('reader_name', sorted(list_readers()))
def test_every_text_reader_self_round_trips(reader_name):
    if reader_name in _TEXT_BINARY_SKIP_READERS:
        pytest.skip(f'{reader_name} has no reader by design.')
    reader = get_reader(reader_name)
    if reader.binary:
        # Binary readers are exercised by their own per-family audit module.
        pytest.skip(f'{reader_name} is a binary reader; covered by binary-audit module.')
    try:
        writer = get_writer(reader_name)
    except KeyError:
        pytest.skip(f'No writer registered for {reader_name}; reader-only format.')
    intermediate = convert_text(SIMPLE_MARKDOWN, 'markdown', reader_name)
    if isinstance(intermediate, bytes):
        intermediate = intermediate.decode('utf-8', errors='replace')
    if not intermediate.strip():
        pytest.skip(f'{reader_name} writer emitted empty output.')
    doc = reader.read(intermediate)
    # Ensure the reader produced *some* structured content.
    assert doc.blocks or doc.meta, (
        f'{reader_name} reader produced an empty document from non-empty input.'
    )
