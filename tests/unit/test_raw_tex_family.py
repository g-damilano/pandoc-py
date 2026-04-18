from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.ast import Paragraph, RawBlock, RawInline, Space, Str
from pandoc_py.readers.markdown import read_markdown
from pandoc_py.writers.markdown import write_markdown


def test_read_raw_tex_inline_command() -> None:
    document = read_markdown('before \\LaTeX{} after\n')
    assert document.blocks == [Paragraph(inlines=[Str('before'), Space(), RawInline(format='tex', text='\\LaTeX{}'), Space(), Str('after')])]


def test_read_raw_latex_inline_attribute() -> None:
    document = read_markdown('before `\\foo{bar}`{=latex} after\n')
    assert document.blocks == [Paragraph(inlines=[Str('before'), Space(), RawInline(format='latex', text='\\foo{bar}'), Space(), Str('after')])]


def test_read_raw_tex_command_block() -> None:
    document = read_markdown('\\foo{bar}\n')
    assert document.blocks == [RawBlock(format='tex', text='\\foo{bar}')]


def test_read_raw_tex_environment_block() -> None:
    document = read_markdown('\\begin{center}\nHello\n\\end{center}\n')
    assert document.blocks == [RawBlock(format='tex', text='\\begin{center}\nHello\n\\end{center}')]


def test_read_raw_tex_and_latex_fences() -> None:
    tex_doc = read_markdown('```{=tex}\n\\foo{bar}\n```\n')
    latex_doc = read_markdown('```{=latex}\n\\foo{bar}\n```\n')
    assert tex_doc.blocks == [RawBlock(format='tex', text='\\foo{bar}')]
    assert latex_doc.blocks == [RawBlock(format='latex', text='\\foo{bar}')]


def test_write_markdown_for_raw_tex_family() -> None:
    inline_doc = read_markdown('before \\LaTeX{} after\n')
    block_doc = read_markdown('\\foo{bar}\n')
    latex_doc = read_markdown('```{=latex}\n\\foo{bar}\n```\n')
    assert write_markdown(inline_doc) == 'before `\\LaTeX{}`{=tex} after\n'
    assert write_markdown(block_doc) == '```{=tex}\n\\foo{bar}\n```\n'
    assert write_markdown(latex_doc) == '```{=latex}\n\\foo{bar}\n```\n'
