from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.ast import MetaBlocks, MetaBool, MetaInlines, MetaList, MetaMap, MetaString, Paragraph, Space, Str
from pandoc_py.readers.commonmark import CommonmarkScopeError, read_commonmark
from pandoc_py.readers.markdown import read_markdown
from pandoc_py.readers.pandoc_json import read_pandoc_json
from pandoc_py.writers.pandoc_json import document_to_pandoc_json_payload


def test_markdown_reads_yaml_front_matter_into_document_meta() -> None:
    source = '---\ntitle: My Title\nauthor:\n  - Alice\n  - Bob\ndraft: true\n---\n\n# Hello\n'
    document = read_markdown(source)
    assert isinstance(document.meta['title'], MetaInlines)
    assert document.meta['title'].inlines == [Str('My'), Space(), Str('Title')]
    assert document.meta['author'] == MetaList([MetaInlines([Str('Alice')]), MetaInlines([Str('Bob')])])
    assert document.meta['draft'] == MetaBool(True)


def test_markdown_reads_block_scalar_metadata_as_metablocks() -> None:
    source = '---\nabstract: |\n  First para.\n\n  Second para.\n---\n\nBody\n'
    document = read_markdown(source)
    abstract = document.meta['abstract']
    assert isinstance(abstract, MetaBlocks)
    assert abstract.blocks == [
        Paragraph([Str('First'), Space(), Str('para.')]),
        Paragraph([Str('Second'), Space(), Str('para.')]),
    ]


def test_pandoc_json_reader_preserves_meta_map() -> None:
    payload = {
        'pandoc-api-version': [1, 23, 1],
        'meta': {
            'title': {'t': 'MetaInlines', 'c': [{'t': 'Str', 'c': 'Hello'}]},
            'draft': {'t': 'MetaBool', 'c': True},
            'params': {'t': 'MetaMap', 'c': {'status': {'t': 'MetaString', 'c': 'final'}}},
        },
        'blocks': [],
    }
    document = read_pandoc_json(json.dumps(payload))
    assert document.meta['title'] == MetaInlines([Str('Hello')])
    assert document.meta['draft'] == MetaBool(True)
    assert document.meta['params'] == MetaMap({'status': MetaString('final')})


def test_pandoc_json_writer_emits_meta_payload() -> None:
    source = '---\ntitle: Hi\nflags:\n  reviewed: true\n---\n\nBody\n'
    document = read_markdown(source)
    payload = document_to_pandoc_json_payload(document)
    assert payload['meta']['title']['t'] == 'MetaInlines'
    assert payload['meta']['flags']['t'] == 'MetaMap'
    assert payload['meta']['flags']['c']['reviewed'] == {'t': 'MetaBool', 'c': True}


def test_commonmark_rejects_yaml_metadata_block() -> None:
    source = '---\ntitle: Nope\n---\n\n# Hello\n'
    try:
        read_commonmark(source)
    except CommonmarkScopeError as exc:
        assert 'YAML metadata' in str(exc)
    else:
        raise AssertionError('Expected CommonmarkScopeError for YAML metadata block.')
