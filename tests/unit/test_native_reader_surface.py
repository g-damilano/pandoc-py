from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pandoc_py.app import convert_text
from pandoc_py.ast import MetaBlocks, MetaBool, MetaInlines, MetaList, MetaMap, MetaString, Paragraph, Space, Str
from pandoc_py.readers.native import read_native
from pandoc_py.writers.pandoc_json import document_to_pandoc_json_payload

PANDOC_BIN = shutil.which('pandoc')


def _oracle_json_from_native(native_text: str) -> dict[str, object]:
    if PANDOC_BIN is None:
        pytest.skip('pandoc binary not available in environment')
    proc = subprocess.run(
        [PANDOC_BIN, '-f', 'native', '-t', 'json', '--wrap=none'],
        input=native_text,
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _python_json_from_native(native_text: str) -> dict[str, object]:
    return document_to_pandoc_json_payload(read_native(native_text))


def test_read_native_basic_structures_match_oracle_json() -> None:
    native_text = '''[ Header
    1 ( "x" , [ "c" ] , [ ( "key" , "val" ) ] ) [ Str "Head" ]
, Para [ Str "alpha" , Space , Str "beta" ]
, CodeBlock ( "code-id" , [ "python" , "extra" ] , [ ( "k" , "v" ) ] ) "print(1)"
, RawBlock (Format "html") "<script>\nalert(1)\n</script>"
]
'''
    document = read_native(native_text)
    assert document.source_format == 'native'
    assert _python_json_from_native(native_text) == _oracle_json_from_native(native_text)


def test_read_native_lists_notes_and_citations_match_oracle_json() -> None:
    native_text = '''[ BulletList
    [ [ Plain [ Str "\\9744" , Space , Str "one" ] ]
    , [ Plain [ Str "\\9746" , Space , Str "two" ] ]
    ]
, OrderedList
    (3,Decimal,Period)
    [ [ Para [ Str "alpha" ] ]
    , [ Para [ Str "beta" ] ]
    ]
, Para
    [ Str "Alpha"
    , Note [ Para [ Str "Note" , Space , Str "text" ] ]
    , Str "."
    ]
, Para
    [ Cite
        [ Citation
            { citationId = "doe"
            , citationPrefix = []
            , citationSuffix = []
            , citationMode = NormalCitation
            , citationNoteNum = 1
            , citationHash = 0
            }
        , Citation
            { citationId = "roe"
            , citationPrefix = []
            , citationSuffix = [ Str "," , Space , Str "pp.\\160\\&1-3" ]
            , citationMode = NormalCitation
            , citationNoteNum = 1
            , citationHash = 0
            }
        ]
        [ Str "[@doe;"
        , Space
        , Str "@roe,"
        , Space
        , Str "pp."
        , Space
        , Str "1-3]"
        ]
    ]
, Para [ Math DisplayMath "\\nx+y\\n" ]
]
'''
    assert _python_json_from_native(native_text) == _oracle_json_from_native(native_text)


def test_read_native_figures_tables_and_raw_tex_match_oracle_json() -> None:
    native_text = '''[ Figure
    ( "x" , [] , [] )
    (Caption Nothing [ Plain [ Str "a" ] ])
    [ Plain
        [ Image
            ( "" , [ "c" ] , [ ( "key" , "val" ) ] )
            [ Str "a" ]
            ( "img.png" , "" )
        ]
    ]
, Table
    ( "" , [] , [] )
    (Caption Nothing [])
    [ ( AlignLeft , ColWidthDefault )
    , ( AlignRight , ColWidthDefault )
    ]
    (TableHead
       ( "" , [] , [] )
       [ Row
           ( "" , [] , [] )
           [ Cell
               ( "" , [] , [] )
               AlignDefault
               (RowSpan 1)
               (ColSpan 1)
               [ Plain [ Str "Emph" ] ]
           , Cell
               ( "" , [] , [] )
               AlignDefault
               (RowSpan 1)
               (ColSpan 1)
               [ Plain [ Str "Link" ] ]
           ]
       ])
    [ TableBody
        ( "" , [] , [] )
        (RowHeadColumns 0)
        []
        [ Row
            ( "" , [] , [] )
            [ Cell
                ( "" , [] , [] )
                AlignDefault
                (RowSpan 1)
                (ColSpan 1)
                [ Plain [ Emph [ Str "a" ] ] ]
            , Cell
                ( "" , [] , [] )
                AlignDefault
                (RowSpan 1)
                (ColSpan 1)
                [ Plain
                    [ Link
                        ( "" , [] , [] )
                        [ Str "b" ]
                        ( "https://example.com" , "" )
                    ]
                ]
            ]
        ]
    ]
    (TableFoot ( "" , [] , [] ) [])
, RawBlock (Format "tex") "\\foo{bar}"
]
'''
    assert _python_json_from_native(native_text) == _oracle_json_from_native(native_text)


def test_convert_text_accepts_native_input_on_json_route() -> None:
    native_text = '[ Para [ Str "alpha" , Space , Str "beta" ] ]\n'
    assert json.loads(convert_text(native_text, 'native', 'json')) == _oracle_json_from_native(native_text)


def test_native_reader_accepts_top_level_pandoc_wrapper_with_null_meta() -> None:
    native_text = 'Pandoc nullMeta [ Para [ Str "alpha" ] ]\n'
    document = read_native(native_text)
    assert document.meta == {}
    assert document.source_format == 'native_pandoc'
    assert _python_json_from_native(native_text) == _oracle_json_from_native(native_text)


def test_native_reader_pandoc_wrapper_metadata_matches_oracle_json() -> None:
    native_text = '''Pandoc
  (Meta
    { unMeta =
      fromList
        [ ("flag", MetaBool True)
        , ("title", MetaInlines [Str "Alpha"])
        , ("subtitle", MetaString "Beta")
        , ("tags", MetaList [MetaString "x", MetaString "y"])
        , ("nested", MetaMap [("inner", MetaString "z")])
        , ("abstract", MetaBlocks [Para [Str "Doc"]])
        ]
    })
  [ Para [ Str "body" ] ]
'''
    document = read_native(native_text)
    assert isinstance(document.meta.get('flag'), MetaBool)
    assert isinstance(document.meta.get('title'), MetaInlines)
    assert isinstance(document.meta.get('subtitle'), MetaString)
    assert isinstance(document.meta.get('tags'), MetaList)
    assert isinstance(document.meta.get('nested'), MetaMap)
    assert isinstance(document.meta.get('abstract'), MetaBlocks)
    assert _python_json_from_native(native_text) == _oracle_json_from_native(native_text)


def test_native_reader_accepts_single_block_payload() -> None:
    document = read_native('Para [ Str "alpha" ]\n')
    assert document.blocks == [Paragraph([Str('alpha')])]
    assert document.meta == {}
    assert document.source_format == 'native'


def test_native_reader_accepts_inline_list_payload() -> None:
    document = read_native('[ Str "alpha" , Space , Str "beta" ]\n')
    assert document.blocks == [Paragraph([Str('alpha'), Space(), Str('beta')])]
    assert document.meta == {}
    assert document.source_format == 'native'


def test_native_reader_accepts_single_inline_payload() -> None:
    document = read_native('Str "alpha"\n')
    assert document.blocks == [Paragraph([Str('alpha')])]
    assert document.meta == {}
    assert document.source_format == 'native'
