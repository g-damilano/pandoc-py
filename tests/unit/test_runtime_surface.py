"""Smoke tests for the runtime layer (state, filter, citeproc)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.app import convert_text
from pandoc_py.ast import Cite, Citation, Document, Paragraph, Str
from pandoc_py.readers.pandoc_json import read_pandoc_json
from pandoc_py.runtime import PandocState, apply_filter, process_citations


def test_pandoc_state_basics():
    state = PandocState()
    state.log('hello')
    assert 'hello' in state.trace


def test_apply_filter_callable_round_trip():
    def upper_filter(payload):
        for blk in payload.get('blocks', []):
            if blk.get('t') == 'Para':
                for c in blk.get('c', []):
                    if c.get('t') == 'Str':
                        c['c'] = c['c'].upper()
        return payload

    doc = read_pandoc_json(convert_text('hello world\n', 'markdown', 'json'))
    filtered = apply_filter(doc, upper_filter)
    assert filtered.blocks[0].inlines[0].text == 'HELLO'
    assert filtered.blocks[0].inlines[2].text == 'WORLD'


def test_process_citations_uses_references_metadata():
    doc = Document(
        blocks=[Paragraph(inlines=[Str('See'), Cite(citations=[Citation(citation_id='smith2020')], inlines=[])])],
        meta={'references': {'smith2020': {'author': [{'family': 'Smith'}], 'issued': {'date-parts': [[2020]]}}}},
    )
    out = process_citations(doc)
    flat = ' '.join(i.text for i in out.blocks[0].inlines if hasattr(i, 'text'))
    assert 'Smith 2020' in flat


def test_process_citations_falls_back_to_id_when_unknown():
    doc = Document(
        blocks=[Paragraph(inlines=[Cite(citations=[Citation(citation_id='unknown')], inlines=[])])],
        meta={'references': {}},
    )
    out = process_citations(doc)
    flat = ''.join(i.text for i in out.blocks[0].inlines if hasattr(i, 'text'))
    assert '[@unknown]' in flat


def test_process_citations_no_metadata_passthrough():
    doc = Document(blocks=[Paragraph(inlines=[Str('plain')])])
    out = process_citations(doc)
    assert out.blocks == doc.blocks
