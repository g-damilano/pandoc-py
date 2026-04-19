from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.app import convert_text
from pandoc_py.ast import LineBlock, Null, Space, Str
from pandoc_py.readers.native import read_native
from pandoc_py.readers.pandoc_json import read_pandoc_json
from pandoc_py.writers.native import write_native
from pandoc_py.writers.pandoc_json import document_to_pandoc_json_payload


def test_pandoc_json_reader_accepts_null_and_lineblock() -> None:
    payload = {
        'pandoc-api-version': [1, 23, 1],
        'meta': {},
        'blocks': [
            {'t': 'Null'},
            {'t': 'LineBlock', 'c': [[{'t': 'Str', 'c': 'alpha'}], [{'t': 'Str', 'c': 'beta'}, {'t': 'Space'}, {'t': 'Str', 'c': 'gamma'}]]},
        ],
    }
    document = read_pandoc_json(json.dumps(payload))
    assert document.blocks == [
        Null(),
        LineBlock(lines=[[Str('alpha')], [Str('beta'), Space(), Str('gamma')]]),
    ]


def test_pandoc_json_writer_emits_null_and_lineblock() -> None:
    document = read_native('[ Null , LineBlock [ [ Str "alpha" ] , [ Str "beta" , Space , Str "gamma" ] ] ]\n')
    payload = document_to_pandoc_json_payload(document)
    assert payload['blocks'] == [
        {'t': 'Null'},
        {'t': 'LineBlock', 'c': [[{'t': 'Str', 'c': 'alpha'}], [{'t': 'Str', 'c': 'beta'}, {'t': 'Space'}, {'t': 'Str', 'c': 'gamma'}]]},
    ]


def test_native_reader_and_writer_support_null_and_lineblock() -> None:
    source = '[ Null , LineBlock [ [ Str "alpha" ] , [ Str "beta" , Space , Str "gamma" ] ] ]\n'
    document = read_native(source)
    assert document.blocks == [
        Null(),
        LineBlock(lines=[[Str('alpha')], [Str('beta'), Space(), Str('gamma')]]),
    ]
    rendered = write_native(document)
    assert rendered.startswith('[Null,LineBlock [[')


def test_convert_json_native_json_roundtrips_null_and_lineblock() -> None:
    payload = {
        'pandoc-api-version': [1, 23, 1],
        'meta': {},
        'blocks': [
            {'t': 'Null'},
            {'t': 'LineBlock', 'c': [[{'t': 'Str', 'c': 'alpha'}], [{'t': 'Str', 'c': 'beta'}, {'t': 'Space'}, {'t': 'Str', 'c': 'gamma'}]]},
        ],
    }
    native_text = convert_text(json.dumps(payload), 'json', 'native')
    reparsed = json.loads(convert_text(native_text, 'native', 'json'))
    assert reparsed['blocks'] == payload['blocks']
