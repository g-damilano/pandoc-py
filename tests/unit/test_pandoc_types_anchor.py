from __future__ import annotations

import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_pandoc_types_definition_anchor_exists() -> None:
    path = REPO_ROOT / 'third_party' / 'pandoc-types' / 'src' / 'Text' / 'Pandoc' / 'Definition.hs'
    text = path.read_text(encoding='utf-8')
    assert 'module Text.Pandoc.Definition' in text
    assert 'data Pandoc = Pandoc Meta [Block]' in text
    assert 'data Inline' in text
    assert 'data Block' in text


def test_current_python_ast_symbols_are_anchored() -> None:
    path = REPO_ROOT / 'trackers' / 'AST_SOURCE_COVERAGE.csv'
    rows = list(csv.DictReader(path.open(encoding='utf-8')) )
    assert rows
    assert all(row['Coverage status'] == 'anchored' for row in rows)
    lookup = {row['Python AST symbol']: row['Haskell anchor symbol'] for row in rows}
    assert lookup['Document'] == 'Pandoc'
    assert lookup['Paragraph'] == 'Para'
    assert lookup['Heading'] == 'Header'
    assert lookup['HardBreak'] == 'LineBreak'
