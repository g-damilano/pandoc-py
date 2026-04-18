from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.readers.markdown import read_markdown
from pandoc_py.writers.pandoc_json import document_to_pandoc_json_payload


def _oracle_payload(source: str) -> dict[str, object]:
    proc = subprocess.run(
        ['pandoc', '-f', 'markdown', '-t', 'json'],
        input=source.encode('utf-8'),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return json.loads(proc.stdout)


def test_simple_citation_matches_pandoc_json() -> None:
    source = '[@doe]\n\n[@roe]\n'
    assert document_to_pandoc_json_payload(read_markdown(source)) == _oracle_payload(source)


def test_prefixed_locator_citation_matches_pandoc_json() -> None:
    source = '[see @doe, p. 3]\n'
    assert document_to_pandoc_json_payload(read_markdown(source)) == _oracle_payload(source)


def test_author_in_text_citation_matches_pandoc_json() -> None:
    source = '@doe [p. 3]\n'
    assert document_to_pandoc_json_payload(read_markdown(source)) == _oracle_payload(source)


def test_multi_citation_group_matches_pandoc_json() -> None:
    source = '[@doe; @roe, pp. 1-3]\n'
    assert document_to_pandoc_json_payload(read_markdown(source)) == _oracle_payload(source)
