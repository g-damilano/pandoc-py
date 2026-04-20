from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.app import convert_text
from pandoc_py.ast import Paragraph, Quoted, SmallCaps, Space, Str, Underline
from pandoc_py.readers.native import read_native
from pandoc_py.readers.pandoc_json import read_pandoc_json
from pandoc_py.writers.native import write_native
from pandoc_py.writers.pandoc_json import document_to_pandoc_json_payload


def test_pandoc_json_reader_accepts_underline_smallcaps_quoted() -> None:
    payload = {
        'pandoc-api-version': [1, 23, 1],
        'meta': {},
        'blocks': [
            {
                't': 'Para',
                'c': [
                    {'t': 'Underline', 'c': [{'t': 'Str', 'c': 'alpha'}]},
                    {'t': 'Space'},
                    {'t': 'SmallCaps', 'c': [{'t': 'Str', 'c': 'beta'}]},
                    {'t': 'Space'},
                    {'t': 'Quoted', 'c': [{'t': 'SingleQuote'}, [{'t': 'Str', 'c': 'gamma'}]]},
                ],
            }
        ],
    }
    document = read_pandoc_json(json.dumps(payload))
    assert document.blocks == [
        Paragraph([
            Underline([Str('alpha')]),
            Space(),
            SmallCaps([Str('beta')]),
            Space(),
            Quoted([Str('gamma')], quote_type='SingleQuote'),
        ])
    ]


def test_pandoc_json_writer_emits_underline_smallcaps_quoted() -> None:
    document = read_native('Para [ Underline [ Str "alpha" ] , Space , SmallCaps [ Str "beta" ] , Space , Quoted DoubleQuote [ Str "gamma" ] ]\n')
    payload = document_to_pandoc_json_payload(document)
    assert payload['blocks'][0]['c'] == [
        {'t': 'Underline', 'c': [{'t': 'Str', 'c': 'alpha'}]},
        {'t': 'Space'},
        {'t': 'SmallCaps', 'c': [{'t': 'Str', 'c': 'beta'}]},
        {'t': 'Space'},
        {'t': 'Quoted', 'c': [{'t': 'DoubleQuote'}, [{'t': 'Str', 'c': 'gamma'}]]},
    ]


def test_native_reader_and_writer_support_underline_smallcaps_quoted() -> None:
    source = 'Para [ Underline [ Str "alpha" ] , Space , SmallCaps [ Str "beta" ] , Space , Quoted SingleQuote [ Str "gamma" ] ]\n'
    document = read_native(source)
    assert document.blocks == [
        Paragraph([
            Underline([Str('alpha')]),
            Space(),
            SmallCaps([Str('beta')]),
            Space(),
            Quoted([Str('gamma')], quote_type='SingleQuote'),
        ])
    ]
    rendered = write_native(document)
    assert 'Underline [Str "alpha"]' in rendered
    assert 'SmallCaps [Str "beta"]' in rendered
    assert 'Quoted SingleQuote [Str "gamma"]' in rendered


def test_convert_json_native_json_roundtrips_underline_smallcaps_quoted() -> None:
    payload = {
        'pandoc-api-version': [1, 23, 1],
        'meta': {},
        'blocks': [
            {
                't': 'Para',
                'c': [
                    {'t': 'Underline', 'c': [{'t': 'Str', 'c': 'alpha'}]},
                    {'t': 'Space'},
                    {'t': 'SmallCaps', 'c': [{'t': 'Str', 'c': 'beta'}]},
                    {'t': 'Space'},
                    {'t': 'Quoted', 'c': [{'t': 'DoubleQuote'}, [{'t': 'Str', 'c': 'gamma'}]]},
                ],
            }
        ],
    }
    native_text = convert_text(json.dumps(payload), 'json', 'native')
    reparsed = json.loads(convert_text(native_text, 'native', 'json'))
    assert reparsed['blocks'] == payload['blocks']
