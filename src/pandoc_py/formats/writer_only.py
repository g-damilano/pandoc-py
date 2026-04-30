"""Writer-only formats inventoried by Pandoc.

For each: a Writer that emits a constrained-slice rendering of the document.
Most of these are markdown-flavor or HTML-flavor presentations; we render
the same admitted slice with a format-specific surface tweak.
"""
from __future__ import annotations

from pandoc_py.ast import (
    BlockQuote, BulletList, CodeBlock, Document, Heading, OrderedList,
    Paragraph, ThematicBreak,
)
from pandoc_py.io import Writer, register_writer
from pandoc_py.writers.html import write_html
from pandoc_py.writers.markdown import write_markdown
from pandoc_py.writers.pandoc_json import write_pandoc_json
from ._common import block_text_paragraphs, inlines_to_plain


def _plain(document: Document) -> str:
    out: list[str] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            out.append(inlines_to_plain(block.inlines)); out.append('')
        elif isinstance(block, Paragraph):
            out.append(inlines_to_plain(block.inlines)); out.append('')
        elif isinstance(block, BlockQuote):
            for sub in block_text_paragraphs(block.blocks): out.append(sub)
            out.append('')
        elif isinstance(block, BulletList):
            for item in block.items:
                for sub in block_text_paragraphs(item): out.append(sub)
            out.append('')
        elif isinstance(block, OrderedList):
            n = block.start
            for item in block.items:
                for sub in block_text_paragraphs(item): out.append(f'{n}. {sub}'); n += 1
            out.append('')
        elif isinstance(block, CodeBlock):
            out.append(block.text); out.append('')
        elif isinstance(block, ThematicBreak):
            out.append('-' * 32); out.append('')
    return '\n'.join(out).rstrip('\n') + '\n'


class _PlainWriter(Writer):
    format_name = 'plain'
    def write(self, document, options=None): return _plain(document)


def _make_html_variant(name: str, aliases: tuple[str, ...] = ()) -> Writer:
    class _W(Writer):
        format_name = name
        aliases = ()
        def write(self, document, options=None):
            return write_html(document)
    _W.aliases = aliases
    _W.__name__ = f'{name.capitalize()}Writer'
    return _W()


def _make_md_variant(name: str, aliases: tuple[str, ...] = ()) -> Writer:
    class _W(Writer):
        format_name = name
        aliases = ()
        def write(self, document, options=None):
            return write_markdown(document)
    _W.aliases = aliases
    _W.__name__ = f'{name.capitalize()}Writer'
    return _W()


# Plain text
register_writer(_PlainWriter())

# HTML-family writer-only renderers (slide systems, chunked HTML, etc.)
for nm, al in [
    ('chunkedhtml', ()), ('dzslides', ()), ('s5', ()), ('slideous', ()),
    ('slidy', ()), ('revealjs', ('reveal_js',)),
]:
    register_writer(_make_html_variant(nm, al))

# Markdown-family writer-only renderers
for nm, al in [
    ('gfm', ()), ('markua', ()), ('markdown_strict', ()),
    ('markdown_phpextra', ()), ('markdown_mmd', ()),
    ('markdown_github', ()),
]:
    register_writer(_make_md_variant(nm, al))


# ConTeXt — a LaTeX-flavor writer; map blocks to a minimal ConTeXt surface
class _ContextWriter(Writer):
    format_name = 'context'
    def write(self, document, options=None):
        out: list[str] = []
        for block in document.blocks:
            if isinstance(block, Heading):
                lvl = max(1, min(block.level, 6))
                cmd = ['chapter', 'section', 'subsection', 'subsubsection', 'subsubsubsection', 'subsubsubsubsection'][lvl - 1]
                out.append(f'\\{cmd}{{{inlines_to_plain(block.inlines)}}}'); out.append('')
            elif isinstance(block, Paragraph):
                out.append(inlines_to_plain(block.inlines)); out.append('')
            elif isinstance(block, BulletList):
                out.append(r'\startitemize')
                for item in block.items:
                    for sub in block_text_paragraphs(item):
                        out.append(f'\\item {sub}')
                out.append(r'\stopitemize'); out.append('')
            elif isinstance(block, OrderedList):
                out.append(r'\startitemize[n]')
                for item in block.items:
                    for sub in block_text_paragraphs(item):
                        out.append(f'\\item {sub}')
                out.append(r'\stopitemize'); out.append('')
            elif isinstance(block, CodeBlock):
                out.append(r'\starttyping')
                for ln in block.text.split('\n'): out.append(ln)
                out.append(r'\stoptyping'); out.append('')
            elif isinstance(block, ThematicBreak):
                out.append(r'\thinrule'); out.append('')
        return '\n'.join(out).rstrip('\n') + '\n'

register_writer(_ContextWriter())


# Texinfo
class _TexinfoWriter(Writer):
    format_name = 'texinfo'
    def write(self, document, options=None):
        out: list[str] = [r'\input texinfo', '@settitle pandoc_py']
        for block in document.blocks:
            if isinstance(block, Heading):
                out.append(f'@chapter {inlines_to_plain(block.inlines)}')
            elif isinstance(block, Paragraph):
                out.append(inlines_to_plain(block.inlines)); out.append('')
            elif isinstance(block, BulletList):
                out.append('@itemize @bullet')
                for item in block.items:
                    for sub in block_text_paragraphs(item):
                        out.append(f'@item {sub}')
                out.append('@end itemize')
            elif isinstance(block, OrderedList):
                out.append('@enumerate')
                for item in block.items:
                    for sub in block_text_paragraphs(item):
                        out.append(f'@item {sub}')
                out.append('@end enumerate')
            elif isinstance(block, CodeBlock):
                out.append('@example')
                for ln in block.text.split('\n'): out.append(ln)
                out.append('@end example')
        out.append('@bye')
        return '\n'.join(out) + '\n'

register_writer(_TexinfoWriter())


# Beamer slides — emit LaTeX-beamer minimal frames
class _BeamerWriter(Writer):
    format_name = 'beamer'
    def write(self, document, options=None):
        out: list[str] = [r'\documentclass{beamer}', r'\begin{document}']
        in_frame = False
        for block in document.blocks:
            if isinstance(block, Heading):
                if in_frame: out.append(r'\end{frame}')
                out.append(f'\\begin{{frame}}{{{inlines_to_plain(block.inlines)}}}')
                in_frame = True
            elif isinstance(block, Paragraph):
                if not in_frame:
                    out.append(r'\begin{frame}{}'); in_frame = True
                out.append(inlines_to_plain(block.inlines))
            elif isinstance(block, BulletList):
                if not in_frame:
                    out.append(r'\begin{frame}{}'); in_frame = True
                out.append(r'\begin{itemize}')
                for item in block.items:
                    for sub in block_text_paragraphs(item): out.append(f'\\item {sub}')
                out.append(r'\end{itemize}')
        if in_frame: out.append(r'\end{frame}')
        out.append(r'\end{document}')
        return '\n'.join(out) + '\n'

register_writer(_BeamerWriter())


# OpenDocument FODT (XML body, single-file flat ODT). Real ODT is a zip — we
# emit just the content.xml-style flat body for the constrained slice.
class _OpenDocumentWriter(Writer):
    format_name = 'opendocument'
    def write(self, document, options=None):
        from html import escape
        out = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
               'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">',
               '<office:body><office:text>']
        for block in document.blocks:
            if isinstance(block, Heading):
                out.append(f'<text:h text:outline-level="{max(1, min(block.level, 6))}">'
                           f'{escape(inlines_to_plain(block.inlines))}</text:h>')
            elif isinstance(block, Paragraph):
                out.append(f'<text:p>{escape(inlines_to_plain(block.inlines))}</text:p>')
            elif isinstance(block, BulletList):
                out.append('<text:list>')
                for item in block.items:
                    out.append('<text:list-item>')
                    for sub in block_text_paragraphs(item):
                        out.append(f'<text:p>{escape(sub)}</text:p>')
                    out.append('</text:list-item>')
                out.append('</text:list>')
            elif isinstance(block, CodeBlock):
                out.append(f'<text:p text:style-name="Preformatted">{escape(block.text)}</text:p>')
        out.append('</office:text></office:body></office:document-content>')
        return '\n'.join(out) + '\n'

register_writer(_OpenDocumentWriter())


# TEI (Text Encoding Initiative)
class _TeiWriter(Writer):
    format_name = 'tei'
    def write(self, document, options=None):
        from html import escape
        out = ['<?xml version="1.0" encoding="UTF-8"?>', '<TEI xmlns="http://www.tei-c.org/ns/1.0">',
               '<text><body>']
        for block in document.blocks:
            if isinstance(block, Heading):
                out.append(f'<head>{escape(inlines_to_plain(block.inlines))}</head>')
            elif isinstance(block, Paragraph):
                out.append(f'<p>{escape(inlines_to_plain(block.inlines))}</p>')
            elif isinstance(block, CodeBlock):
                out.append(f'<code>{escape(block.text)}</code>')
        out.append('</body></text></TEI>')
        return '\n'.join(out) + '\n'

register_writer(_TeiWriter())


# Icml (InCopy ICML — InDesign)
class _IcmlWriter(Writer):
    format_name = 'icml'
    def write(self, document, options=None):
        from html import escape
        out = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<Document>',
               '<Story Self="story1">']
        for block in document.blocks:
            text = inlines_to_plain(getattr(block, 'inlines', getattr(block, 'text', '')) if not hasattr(block, 'text') else block.text) if hasattr(block, 'text') and not getattr(block, 'inlines', None) else inlines_to_plain(getattr(block, 'inlines', []))
            if isinstance(block, (Heading, Paragraph)):
                out.append(f'<ParagraphStyleRange><CharacterStyleRange><Content>{escape(inlines_to_plain(block.inlines))}</Content></CharacterStyleRange></ParagraphStyleRange>')
            elif isinstance(block, CodeBlock):
                out.append(f'<ParagraphStyleRange AppliedParagraphStyle="Code"><CharacterStyleRange><Content>{escape(block.text)}</Content></CharacterStyleRange></ParagraphStyleRange>')
        out.append('</Story></Document>')
        return '\n'.join(out) + '\n'

register_writer(_IcmlWriter())


# ms (groff -ms)
class _MsWriter(Writer):
    format_name = 'ms'
    def write(self, document, options=None):
        out: list[str] = []
        for block in document.blocks:
            if isinstance(block, Heading):
                out.append(f'.NH {max(1, min(block.level, 5))}')
                out.append(inlines_to_plain(block.inlines))
            elif isinstance(block, Paragraph):
                out.append('.LP'); out.append(inlines_to_plain(block.inlines))
            elif isinstance(block, BulletList):
                for item in block.items:
                    for sub in block_text_paragraphs(item):
                        out.append('.IP \\(bu'); out.append(sub)
            elif isinstance(block, CodeBlock):
                out.append('.DS L')
                for ln in block.text.split('\n'): out.append(ln)
                out.append('.DE')
        return '\n'.join(out) + '\n'

register_writer(_MsWriter())


# ANSI text writer (drops ANSI escape decoration since slice is plain)
class _AnsiWriter(Writer):
    format_name = 'ansi'
    def write(self, document, options=None):
        return _plain(document)

register_writer(_AnsiWriter())


# BBCode
class _BbCodeWriter(Writer):
    format_name = 'bbcode'
    def write(self, document, options=None):
        out: list[str] = []
        for block in document.blocks:
            if isinstance(block, Heading):
                out.append(f'[h{max(1, min(block.level, 6))}]{inlines_to_plain(block.inlines)}[/h{max(1, min(block.level, 6))}]')
            elif isinstance(block, Paragraph):
                out.append(inlines_to_plain(block.inlines)); out.append('')
            elif isinstance(block, BulletList):
                out.append('[list]')
                for item in block.items:
                    for sub in block_text_paragraphs(item): out.append(f'[*]{sub}')
                out.append('[/list]')
            elif isinstance(block, OrderedList):
                out.append('[list=1]')
                for item in block.items:
                    for sub in block_text_paragraphs(item): out.append(f'[*]{sub}')
                out.append('[/list]')
            elif isinstance(block, CodeBlock):
                out.append('[code]'); out.append(block.text); out.append('[/code]')
        return '\n'.join(out) + '\n'

register_writer(_BbCodeWriter())


# ZimWiki
class _ZimWikiWriter(Writer):
    format_name = 'zimwiki'
    def write(self, document, options=None):
        out: list[str] = []
        for block in document.blocks:
            if isinstance(block, Heading):
                eq = '=' * (7 - max(1, min(block.level, 6)))
                out.append(f'{eq} {inlines_to_plain(block.inlines)} {eq}')
            elif isinstance(block, Paragraph):
                out.append(inlines_to_plain(block.inlines)); out.append('')
            elif isinstance(block, BulletList):
                for item in block.items:
                    for sub in block_text_paragraphs(item): out.append(f'* {sub}')
            elif isinstance(block, OrderedList):
                n = block.start
                for item in block.items:
                    for sub in block_text_paragraphs(item):
                        out.append(f'{n}. {sub}'); n += 1
            elif isinstance(block, CodeBlock):
                out.append("'''"); out.append(block.text); out.append("'''")
        return '\n'.join(out) + '\n'

register_writer(_ZimWikiWriter())


# AnnotatedTable / Blaze: degenerate to native JSON or HTML
class _AnnotatedTableWriter(Writer):
    format_name = 'annotated_table'
    def write(self, document, options=None):
        return write_pandoc_json(document)

register_writer(_AnnotatedTableWriter())


class _BlazeWriter(Writer):
    format_name = 'blaze'
    def write(self, document, options=None):
        return write_html(document)

register_writer(_BlazeWriter())
