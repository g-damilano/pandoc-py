"""LaTeX reader/writer — constrained slice."""
from __future__ import annotations

import re

from pandoc_py.ast import (
    Attr, BlockQuote, BulletList, CodeBlock, Document, Heading, OrderedList,
    Paragraph, ThematicBreak,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import block_text_paragraphs, inlines_to_plain, slugify_heading, text_to_inlines

_LATEX_HEADING_LEVELS = {
    'part': 0, 'chapter': 0, 'section': 1, 'subsection': 2,
    'subsubsection': 3, 'paragraph': 4, 'subparagraph': 5,
}
_LATEX_LEVEL_TO_NAME = ['section', 'subsection', 'subsubsection', 'paragraph', 'subparagraph', 'subparagraph']


def _read_latex(source: str) -> Document:
    """Constrained-slice LaTeX reader.

    Recognised:
      - ``\\section{Title}`` ... ``\\subparagraph{...}``, optionally
        followed by ``\\label{anchor}`` on the same or next line.
      - ``\\begin{itemize}`` / ``\\begin{enumerate}`` blocks with
        ``\\item`` content lines.
      - ``\\begin{quote}`` and ``\\begin{verbatim}`` blocks.
      - ``\\hrulefill`` / ``\\hrule`` thematic breaks.
      - Plain paragraphs separated by blank lines.
      - ``\\tightlist`` is silently dropped (pandoc emits it).
    """
    text = source.replace('\r\n', '\n').replace('\r', '\n')
    body_match = re.search(r'\\begin\{document\}(.*?)\\end\{document\}', text, re.DOTALL)
    if body_match:
        text = body_match.group(1)
    lines = text.split('\n')
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1; continue
        # Heading: \section{Heading}\label{heading} OR
        #          \section{Heading} on its own line followed by \label{...}
        m = re.match(r'^\\(part|chapter|section|subsection|subsubsection|paragraph|subparagraph)\*?\{(.*?)\}\s*(?:\\label\{([^}]+)\})?\s*$', line)
        if m:
            level = max(1, _LATEX_HEADING_LEVELS.get(m.group(1), 1))
            heading_text = m.group(2)
            anchor = m.group(3) or ''
            # Look at next line for orphan \label{..}
            if not anchor and i + 1 < len(lines):
                lm = re.match(r'^\\label\{([^}]+)\}\s*$', lines[i + 1].strip())
                if lm:
                    anchor = lm.group(1); i += 1
            attr = Attr(identifier=anchor) if anchor else Attr()
            blocks.append(Heading(level=level, inlines=text_to_inlines(heading_text), attr=attr))
            i += 1
            continue
        if line == r'\tightlist':
            i += 1; continue
        if line.startswith(r'\begin{itemize}'):
            items, j = [], i + 1
            while j < len(lines) and lines[j].strip() != r'\end{itemize}':
                ls = lines[j].strip()
                if ls == r'\tightlist' or not ls:
                    j += 1; continue
                im = re.match(r'^\\item\s*(.*)$', ls)
                if im:
                    item_buf = [im.group(1)]
                    j += 1
                    while j < len(lines):
                        nxt = lines[j].strip()
                        if nxt == r'\end{itemize}' or nxt.startswith(r'\item'):
                            break
                        if nxt:
                            item_buf.append(nxt)
                        j += 1
                    items.append([Paragraph(inlines=text_to_inlines(' '.join(s for s in item_buf if s)), is_plain=True)])
                else:
                    j += 1
            blocks.append(BulletList(items=items))
            i = j + 1; continue
        if line.startswith(r'\begin{enumerate}'):
            items, j = [], i + 1
            while j < len(lines) and lines[j].strip() != r'\end{enumerate}':
                ls = lines[j].strip()
                if ls == r'\tightlist' or not ls:
                    j += 1; continue
                im = re.match(r'^\\item\s*(.*)$', ls)
                if im:
                    item_buf = [im.group(1)]
                    j += 1
                    while j < len(lines):
                        nxt = lines[j].strip()
                        if nxt == r'\end{enumerate}' or nxt.startswith(r'\item'):
                            break
                        if nxt:
                            item_buf.append(nxt)
                        j += 1
                    items.append([Paragraph(inlines=text_to_inlines(' '.join(s for s in item_buf if s)), is_plain=True)])
                else:
                    j += 1
            blocks.append(OrderedList(items=items))
            i = j + 1; continue
        if line.startswith(r'\begin{quote}'):
            buf, j = [], i + 1
            while j < len(lines) and lines[j].strip() != r'\end{quote}':
                buf.append(lines[j]); j += 1
            blocks.append(BlockQuote(blocks=[Paragraph(inlines=text_to_inlines(' '.join(s.strip() for s in buf if s.strip())))]))
            i = j + 1; continue
        if line.startswith(r'\begin{verbatim}'):
            buf, j = [], i + 1
            while j < len(lines) and lines[j].strip() != r'\end{verbatim}':
                buf.append(lines[j]); j += 1
            blocks.append(CodeBlock(text='\n'.join(buf)))
            i = j + 1; continue
        if line in (r'\hrulefill', r'\hrule') or line.startswith(r'\rule{'):
            blocks.append(ThematicBreak()); i += 1; continue
        # Paragraph: collect contiguous non-empty, non-command-starting lines.
        buf = [line]; j = i + 1
        while j < len(lines) and lines[j].strip() and not lines[j].lstrip().startswith('\\'):
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
            text = inlines_to_plain(block.inlines)
            anchor = block.attr.identifier or slugify_heading(text)
            out.append(f'\\{cmd}{{{text}}}\\label{{{anchor}}}')
            out.append('')
        elif isinstance(block, Paragraph):
            out.append(inlines_to_plain(block.inlines)); out.append('')
        elif isinstance(block, BulletList):
            out.append(r'\begin{itemize}')
            out.append(r'\tightlist')
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out.append(r'\item')
                    out.append(f'  {sub}')
            out.append(r'\end{itemize}'); out.append('')
        elif isinstance(block, OrderedList):
            out.append(r'\begin{enumerate}')
            out.append(r'\tightlist')
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    out.append(r'\item')
                    out.append(f'  {sub}')
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
