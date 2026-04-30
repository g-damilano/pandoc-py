"""LaTeX reader/writer — constrained slice."""
from __future__ import annotations

import re
from pandoc_py.ast import (
    BlockQuote, BulletList, CodeBlock, Document, Heading, OrderedList,
    Paragraph, ThematicBreak,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import block_text_paragraphs, inlines_to_plain, text_to_inlines

_LATEX_HEADING_LEVELS = {
    'part': 0, 'chapter': 0, 'section': 1, 'subsection': 2,
    'subsubsection': 3, 'paragraph': 4, 'subparagraph': 5,
}
_LATEX_LEVEL_TO_NAME = ['section', 'subsection', 'subsubsection', 'paragraph', 'subparagraph', 'subparagraph']


def _read_latex(source: str) -> Document:
    text = source.replace('\r\n', '\n').replace('\r', '\n')
    # Strip LaTeX preamble down to body if \begin{document} is present.
    m = re.search(r'\\begin\{document\}(.*?)\\end\{document\}', text, re.DOTALL)
    if m:
        text = m.group(1)
    lines = text.split('\n')
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1; continue
        m = re.match(r'^\\(part|chapter|section|subsection|subsubsection|paragraph|subparagraph)\*?\{(.*)\}\s*$', line)
        if m:
            level = max(1, _LATEX_HEADING_LEVELS.get(m.group(1), 1))
            blocks.append(Heading(level=level, inlines=text_to_inlines(m.group(2))))
            i += 1; continue
        if line.startswith(r'\begin{itemize}'):
            items, j = [], i + 1
            while j < len(lines) and not lines[j].strip().startswith(r'\end{itemize}'):
                im = re.match(r'^\s*\\item\s*(.*)$', lines[j])
                if im:
                    items.append([Paragraph(inlines=text_to_inlines(im.group(1)), is_plain=True)])
                j += 1
            blocks.append(BulletList(items=items))
            i = j + 1; continue
        if line.startswith(r'\begin{enumerate}'):
            items, j = [], i + 1
            while j < len(lines) and not lines[j].strip().startswith(r'\end{enumerate}'):
                im = re.match(r'^\s*\\item\s*(.*)$', lines[j])
                if im:
                    items.append([Paragraph(inlines=text_to_inlines(im.group(1)), is_plain=True)])
                j += 1
            blocks.append(OrderedList(items=items))
            i = j + 1; continue
        if line.startswith(r'\begin{quote}'):
            buf, j = [], i + 1
            while j < len(lines) and not lines[j].strip().startswith(r'\end{quote}'):
                buf.append(lines[j]); j += 1
            blocks.append(BlockQuote(blocks=[Paragraph(inlines=text_to_inlines(' '.join(s.strip() for s in buf if s.strip())))]))
            i = j + 1; continue
        if line.startswith(r'\begin{verbatim}'):
            buf, j = [], i + 1
            while j < len(lines) and not lines[j].strip().startswith(r'\end{verbatim}'):
                buf.append(lines[j]); j += 1
            blocks.append(CodeBlock(text='\n'.join(buf)))
            i = j + 1; continue
        if line in (r'\hrulefill', r'\rule{\linewidth}{0.4pt}', r'\hrule'):
            blocks.append(ThematicBreak()); i += 1; continue
        # Paragraph until blank
        buf = [line]; j = i + 1
        while j < len(lines) and lines[j].strip() and not lines[j].strip().startswith('\\'):
            buf.append(lines[j].strip()); j += 1
        blocks.append(Paragraph(inlines=text_to_inlines(' '.join(buf))))
        i = j
    return Document(blocks=blocks, source_format='latex')


def _write_latex(document: Document) -> str:
    out: list[str] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            level = max(1, min(block.level, 6))
            cmd = _LATEX_LEVEL_TO_NAME[level - 1]
            out.append(f'\\{cmd}{{{inlines_to_plain(block.inlines)}}}')
            out.append('')
        elif isinstance(block, Paragraph):
            out.append(inlines_to_plain(block.inlines)); out.append('')
        elif isinstance(block, BulletList):
            out.append(r'\begin{itemize}')
            for item in block.items:
                for sub in block_text_paragraphs(item): out.append(f'\\item {sub}')
            out.append(r'\end{itemize}'); out.append('')
        elif isinstance(block, OrderedList):
            out.append(r'\begin{enumerate}')
            for item in block.items:
                for sub in block_text_paragraphs(item): out.append(f'\\item {sub}')
            out.append(r'\end{enumerate}'); out.append('')
        elif isinstance(block, BlockQuote):
            out.append(r'\begin{quote}')
            for sub in block_text_paragraphs(block.blocks): out.append(sub)
            out.append(r'\end{quote}'); out.append('')
        elif isinstance(block, CodeBlock):
            out.append(r'\begin{verbatim}')
            for ln in block.text.split('\n'): out.append(ln)
            out.append(r'\end{verbatim}'); out.append('')
        elif isinstance(block, ThematicBreak):
            out.append(r'\hrulefill'); out.append('')
    return '\n'.join(out).rstrip('\n') + '\n'


class LatexReader(Reader):
    format_name = 'latex'
    aliases = ('tex',)
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        return _read_latex(source)


class LatexWriter(Writer):
    format_name = 'latex'
    aliases = ('tex',)
    def write(self, document, options=None):
        return _write_latex(document)


register_reader(LatexReader())
register_writer(LatexWriter())
