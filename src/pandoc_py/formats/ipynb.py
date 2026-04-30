"""Jupyter Notebook (IPYNB) reader/writer — constrained slice.

Each notebook cell becomes either:
  * markdown cell  → its parsed markdown blocks merged into the document
  * code cell      → a CodeBlock with `info` set to the cell language
  * raw cell       → a Paragraph in the admitted slice
"""
from __future__ import annotations

import json

from pandoc_py.ast import (
    CodeBlock, Document, Paragraph,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from pandoc_py.readers.markdown import read_markdown
from pandoc_py.writers.markdown import write_markdown
from ._common import inlines_to_plain, text_to_inlines


def _read_ipynb(source: str) -> Document:
    nb = json.loads(source)
    lang = nb.get('metadata', {}).get('language_info', {}).get('name', 'python')
    blocks = []
    for cell in nb.get('cells', []):
        ctype = cell.get('cell_type')
        src = cell.get('source', '')
        if isinstance(src, list): src = ''.join(src)
        if ctype == 'markdown':
            inner = read_markdown(src)
            blocks.extend(inner.blocks)
        elif ctype == 'code':
            blocks.append(CodeBlock(text=src.rstrip('\n'), info=lang))
        elif ctype == 'raw':
            blocks.append(Paragraph(inlines=text_to_inlines(src)))
    return Document(blocks=blocks, meta=nb.get('metadata', {}).get('pandoc', {}), source_format='ipynb')


def _write_ipynb(document: Document) -> str:
    cells = []
    md_buf: list = []

    def flush_md():
        nonlocal md_buf
        if md_buf:
            sub_doc = Document(blocks=list(md_buf))
            md_text = write_markdown(sub_doc)
            cells.append({'cell_type': 'markdown', 'metadata': {}, 'source': md_text.splitlines(keepends=True)})
            md_buf = []

    for block in document.blocks:
        if isinstance(block, CodeBlock):
            flush_md()
            cells.append({
                'cell_type': 'code',
                'metadata': {}, 'execution_count': None,
                'source': [ln + '\n' for ln in block.text.split('\n')] if block.text else [],
                'outputs': [],
            })
        else:
            md_buf.append(block)
    flush_md()
    nb = {
        'cells': cells,
        'metadata': {'language_info': {'name': 'python'}, 'kernelspec': {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'}},
        'nbformat': 4,
        'nbformat_minor': 5,
    }
    return json.dumps(nb, indent=1, ensure_ascii=False) + '\n'


class IpynbReader(Reader):
    format_name = 'ipynb'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_ipynb(source)

class IpynbWriter(Writer):
    format_name = 'ipynb'
    def write(self, document, options=None):
        return _write_ipynb(document)

register_reader(IpynbReader())
register_writer(IpynbWriter())
