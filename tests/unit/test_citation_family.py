from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.ast import Cite, Citation, Paragraph, Space, Str
from pandoc_py.readers.markdown import read_markdown
from pandoc_py.writers.markdown import write_markdown


def test_bracketed_citation_parses_with_prefix_and_locator_suffix() -> None:
    block = read_markdown('[see @doe, p. 3]\n').blocks[0]
    assert isinstance(block, Paragraph)
    assert len(block.inlines) == 1
    cite = block.inlines[0]
    assert isinstance(cite, Cite)
    assert cite.inlines == [Str('[see'), Space(), Str('@doe,'), Space(), Str('p.'), Space(), Str('3]')]
    assert cite.citations == [
        Citation(
            citation_id='doe',
            prefix=[Str('see')],
            suffix=[Str(','), Space(), Str('p.\xa03')],
            mode='NormalCitation',
        )
    ]


def test_multi_citation_group_parses() -> None:
    block = read_markdown('[@doe; @roe]\n').blocks[0]
    cite = block.inlines[0]
    assert isinstance(cite, Cite)
    assert [citation.citation_id for citation in cite.citations] == ['doe', 'roe']
    assert all(citation.mode == 'NormalCitation' for citation in cite.citations)


def test_author_in_text_citation_with_suffix_parses() -> None:
    block = read_markdown('@doe [p. 3]\n').blocks[0]
    cite = block.inlines[0]
    assert isinstance(cite, Cite)
    assert cite.citations == [
        Citation(
            citation_id='doe',
            prefix=[],
            suffix=[Str('p.\xa03')],
            mode='AuthorInText',
        )
    ]
    assert write_markdown(read_markdown('@doe [p. 3]\n')) == '@doe [p.\xa03]\n'


def test_suppress_author_citation_roundtrips_markdown() -> None:
    source = '[see -@doe]\n'
    assert write_markdown(read_markdown(source)) == source
