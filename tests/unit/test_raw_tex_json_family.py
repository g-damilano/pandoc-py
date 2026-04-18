from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.readers.markdown import read_markdown
from pandoc_py.writers.pandoc_json import document_to_pandoc_json_payload


def test_raw_tex_inline_command_flows_to_json() -> None:
    payload = document_to_pandoc_json_payload(read_markdown('before \\LaTeX{} after\n'))['blocks'][0]
    assert payload['t'] == 'Para'
    assert payload['c'][2] == {'t': 'RawInline', 'c': ['tex', '\\LaTeX{}']}


def test_raw_latex_inline_attribute_flows_to_json() -> None:
    payload = document_to_pandoc_json_payload(read_markdown('before `\\foo{bar}`{=latex} after\n'))['blocks'][0]
    assert payload['t'] == 'Para'
    assert payload['c'][2] == {'t': 'RawInline', 'c': ['latex', '\\foo{bar}']}


def test_raw_tex_command_block_flows_to_json() -> None:
    payload = document_to_pandoc_json_payload(read_markdown('\\foo{bar}\n'))['blocks'][0]
    assert payload == {'t': 'RawBlock', 'c': ['tex', '\\foo{bar}']}


def test_raw_tex_environment_block_flows_to_json() -> None:
    payload = document_to_pandoc_json_payload(read_markdown('\\begin{center}\nHello\n\\end{center}\n'))['blocks'][0]
    assert payload == {'t': 'RawBlock', 'c': ['tex', '\\begin{center}\nHello\n\\end{center}']}


def test_raw_tex_and_latex_fences_flow_to_json() -> None:
    tex_payload = document_to_pandoc_json_payload(read_markdown('```{=tex}\n\\foo{bar}\n```\n'))['blocks'][0]
    latex_payload = document_to_pandoc_json_payload(read_markdown('```{=latex}\n\\foo{bar}\n```\n'))['blocks'][0]
    assert tex_payload == {'t': 'RawBlock', 'c': ['tex', '\\foo{bar}']}
    assert latex_payload == {'t': 'RawBlock', 'c': ['latex', '\\foo{bar}']}
