from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.ast import MetaBlocks, MetaBool, MetaInlines, MetaList, MetaMap, MetaString, Paragraph, Space, Str
from pandoc_py.readers.native import read_native
from pandoc_py.writers.native import write_native


def test_write_native_keeps_block_list_surface_without_meta() -> None:
    text = write_native(read_native('[ Para [ Str "alpha" ] ]\n'))
    assert text == '[Para [Str "alpha"]]\n'


def test_write_native_emits_pandoc_wrapper_when_meta_present() -> None:
    document = read_native('Pandoc nullMeta [ Para [ Str "alpha" ] ]\n')
    document = document.__class__(blocks=document.blocks, meta={'flag': MetaBool(True)}, source_format=document.source_format)
    rendered = write_native(document)
    assert rendered.startswith('Pandoc Meta { unMeta = fromList [(')
    assert '("flag",MetaBool True)' in rendered
    assert rendered.endswith('[Para [Str "alpha"]]\n')


def test_write_native_preserves_wrapper_surface_for_native_pandoc_source() -> None:
    document = read_native('Pandoc nullMeta [ Para [ Str "alpha" ] ]\n')
    rendered = write_native(document)
    assert rendered == 'Pandoc nullMeta [Para [Str "alpha"]]\n'


def test_write_native_standalone_wraps_without_meta() -> None:
    document = read_native('[ Para [ Str "alpha" ] ]\n')
    rendered = write_native(document, standalone=True)
    assert rendered == 'Pandoc nullMeta [Para [Str "alpha"]]\n'


def test_write_native_roundtrips_supported_meta_value_family() -> None:
    source = (
        'Pandoc (Meta { unMeta = fromList [('
        '"flag", MetaBool True),('
        '"title", MetaInlines [Str "Alpha"]),('
        '"subtitle", MetaString "Beta"),('
        '"tags", MetaList [MetaString "x",MetaString "y"]),('
        '"nested", MetaMap [("inner", MetaString "z")]),('
        '"abstract", MetaBlocks [Para [Str "Doc"]])'
        '] }) [ Para [ Str "body" , Space , Str "text" ] ]\n'
    )
    document = read_native(source)
    rendered = write_native(document)
    reparsed = read_native(rendered)

    assert isinstance(reparsed.meta.get('flag'), MetaBool)
    assert isinstance(reparsed.meta.get('title'), MetaInlines)
    assert isinstance(reparsed.meta.get('subtitle'), MetaString)
    assert isinstance(reparsed.meta.get('tags'), MetaList)
    assert isinstance(reparsed.meta.get('nested'), MetaMap)
    assert isinstance(reparsed.meta.get('abstract'), MetaBlocks)
    assert reparsed.blocks == [Paragraph([Str('body'), Space(), Str('text')])]
