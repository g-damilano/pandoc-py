from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.readers.markdown import read_markdown
from pandoc_py.writers.pandoc_json import document_to_pandoc_json_payload


def test_heading_attributes_flow_to_json() -> None:
    payload = document_to_pandoc_json_payload(read_markdown('# Head {#x .c key=val}\n'))['blocks'][0]
    assert payload['t'] == 'Header'
    assert payload['c'][1] == ['x', ['c'], [['key', 'val']]]


def test_span_attributes_flow_to_json() -> None:
    payload = document_to_pandoc_json_payload(read_markdown('[alpha]{#x .c key=val}\n'))['blocks'][0]
    assert payload['t'] == 'Para'
    assert payload['c'][0]['t'] == 'Span'
    assert payload['c'][0]['c'][0] == ['x', ['c'], [['key', 'val']]]


def test_div_attributes_flow_to_json() -> None:
    payload = document_to_pandoc_json_payload(read_markdown('::: {.note #x key=val}\npara\n:::\n'))['blocks'][0]
    assert payload['t'] == 'Div'
    assert payload['c'][0] == ['x', ['note'], [['key', 'val']]]


def test_fenced_code_attributes_flow_to_json() -> None:
    payload = document_to_pandoc_json_payload(read_markdown('``` {.python #x key=val}\nprint(1)\n```\n'))['blocks'][0]
    assert payload['t'] == 'CodeBlock'
    assert payload['c'][0] == ['x', ['python'], [['key', 'val']]]


def test_link_attributes_flow_to_json() -> None:
    payload = document_to_pandoc_json_payload(read_markdown('[a](https://e.com){#x .c key=val}\n'))['blocks'][0]
    assert payload['t'] == 'Para'
    assert payload['c'][0]['t'] == 'Link'
    assert payload['c'][0]['c'][0] == ['x', ['c'], [['key', 'val']]]


def test_standalone_image_attributes_flow_to_figure_json() -> None:
    payload = document_to_pandoc_json_payload(read_markdown('![a](img.png){#x .c key=val}\n'))['blocks'][0]
    assert payload['t'] == 'Figure'
    assert payload['c'][0] == ['x', [], []]
    assert payload['c'][2][0]['c'][0]['c'][0] == ['', ['c'], [['key', 'val']]]
