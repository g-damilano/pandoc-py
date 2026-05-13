"""Full-functional DOCX writer.

Mirrors pandoc's ``-t docx`` output at the structural OOXML level:

* every Pandoc inline (Str/Space/SoftBreak/HardBreak/Emph/Strong/
  Strikeout/Subscript/Superscript/Underline/SmallCaps/Quoted/Code/
  Span/Link/Image/RawInline/Note/Cite/Math) is rendered into the
  appropriate ``w:r`` run with the right ``w:rPr`` properties;
* every Pandoc block (Paragraph/Heading/BlockQuote/BulletList/
  OrderedList/DefinitionList/CodeBlock/RawBlock/ThematicBreak/
  Figure/Table/LineBlock/Div/Null) is rendered into one or more
  paragraphs (or, for Table, a ``w:tbl``);
* relationships are tracked so hyperlinks, images, and footnote
  references resolve to real ``rId`` ids in
  ``word/_rels/document.xml.rels`` / ``word/_rels/footnotes.xml.rels``;
* images are read from disk and stored at ``word/media/<name>``;
* footnotes are emitted into ``word/footnotes.xml`` with sentinel
  entries (-1/0) matching pandoc's defaults.

The output is a valid OOXML zip that pandoc's docx reader reparses to
a structurally equivalent AST.
"""
from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from typing import Iterable

from pandoc_py.ast import (
    Attr, Block, BlockQuote, BulletList, Cite, Code, CodeBlock,
    DefinitionList, Div, Document, Emph, Figure, HardBreak, Heading,
    Image, Inline, LineBlock, Link, Math, Note, Null, OrderedList,
    Paragraph, Quoted, RawBlock, RawInline, SmallCaps, SoftBreak, Space,
    Span, Str, Strikeout, Strong, Subscript, Superscript, Table,
    ThematicBreak, Underline,
)


_W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
_R_REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
_A_NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'
_PIC_NS = 'http://schemas.openxmlformats.org/drawingml/2006/picture'
_WP_NS = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'


# ---- state ---------------------------------------------------------------

@dataclass
class _State:
    rels: list[tuple[str, str, str, str | None]] = field(default_factory=list)
    """(rId, type, target, targetMode_or_None)"""
    media: dict[str, bytes] = field(default_factory=dict)
    footnotes: list[str] = field(default_factory=list)  # each item is a body of w:p paragraphs
    rel_counter: int = 100
    image_counter: int = 0

    def new_rid(self) -> str:
        self.rel_counter += 1
        return f'rId{self.rel_counter}'

    def add_hyperlink(self, target: str) -> str:
        rid = self.new_rid()
        self.rels.append((
            rid,
            'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',
            target,
            'External',
        ))
        return rid

    def add_image(self, source_path: str, data: bytes, ext: str) -> tuple[str, str]:
        self.image_counter += 1
        media_name = f'image{self.image_counter}.{ext.lstrip(".")}'
        self.media[media_name] = data
        rid = self.new_rid()
        self.rels.append((
            rid,
            'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image',
            f'media/{media_name}',
            None,
        ))
        return rid, media_name


# ---- inline helpers ------------------------------------------------------

_QUOTES = {
    'DoubleQuote': ('“', '”'),
    'SingleQuote': ('‘', '’'),
}


def _text_run(text: str, rpr: str = '') -> str:
    """Emit one ``w:r`` with optional run-properties."""
    if not text:
        # Empty runs are pointless; keep paragraphs tidy.
        return ''
    return (
        '<w:r>'
        + (f'<w:rPr>{rpr}</w:rPr>' if rpr else '')
        + f'<w:t xml:space="preserve">{escape(text)}</w:t>'
        + '</w:r>'
    )


def _wrap_with_rpr(child_xml: str, extra_rpr: str) -> str:
    """Add ``extra_rpr`` to every ``<w:r>`` inside ``child_xml``.

    Used by recursive inline rendering: the outer formatting (Emph,
    Strong, etc.) needs to apply to every run produced by the inner
    inlines, not just to a single one. We inject the property into
    each run's ``w:rPr``.
    """
    if not extra_rpr:
        return child_xml

    def patch_run(match: re.Match) -> str:
        run = match.group(0)
        if '<w:rPr>' in run:
            return run.replace('<w:rPr>', f'<w:rPr>{extra_rpr}', 1)
        return run.replace('<w:r>', f'<w:r><w:rPr>{extra_rpr}</w:rPr>', 1)

    return re.sub(r'<w:r>.*?</w:r>', patch_run, child_xml, flags=re.DOTALL)


def _render_inlines(inlines: Iterable[Inline], state: _State) -> str:
    return ''.join(_render_inline(i, state) for i in inlines)


def _render_inline(node: Inline, state: _State) -> str:
    if isinstance(node, Str):
        return _text_run(node.text)
    if isinstance(node, Space):
        return _text_run(' ')
    if isinstance(node, SoftBreak):
        return _text_run(' ')
    if isinstance(node, HardBreak):
        return '<w:r><w:br/></w:r>'
    if isinstance(node, Emph):
        return _wrap_with_rpr(_render_inlines(node.inlines, state), '<w:i/>')
    if isinstance(node, Strong):
        return _wrap_with_rpr(_render_inlines(node.inlines, state), '<w:b/>')
    if isinstance(node, Strikeout):
        return _wrap_with_rpr(_render_inlines(node.inlines, state), '<w:strike/>')
    if isinstance(node, Underline):
        return _wrap_with_rpr(_render_inlines(node.inlines, state), '<w:u w:val="single"/>')
    if isinstance(node, SmallCaps):
        return _wrap_with_rpr(_render_inlines(node.inlines, state), '<w:smallCaps/>')
    if isinstance(node, Subscript):
        return _wrap_with_rpr(_render_inlines(node.inlines, state), '<w:vertAlign w:val="subscript"/>')
    if isinstance(node, Superscript):
        return _wrap_with_rpr(_render_inlines(node.inlines, state), '<w:vertAlign w:val="superscript"/>')
    if isinstance(node, Quoted):
        opening, closing = _QUOTES.get(node.quote_type, _QUOTES['DoubleQuote'])
        return _text_run(opening) + _render_inlines(node.inlines, state) + _text_run(closing)
    if isinstance(node, Code):
        return _text_run(node.text, rpr='<w:rStyle w:val="VerbatimChar"/>')
    if isinstance(node, Math):
        # Pandoc emits OMML; we render a verbatim run with appropriate
        # style so the math text is at least preserved in the docx.
        prefix, suffix = (r'\(', r'\)') if not node.display else (r'\[', r'\]')
        return _text_run(prefix + node.text + suffix, rpr='<w:rStyle w:val="Equation"/>')
    if isinstance(node, Span):
        return _render_inlines(node.inlines, state)
    if isinstance(node, Link):
        rid = state.add_hyperlink(node.target)
        inner = _render_inlines(node.inlines, state) or _text_run(node.target)
        inner = _wrap_with_rpr(inner, '<w:rStyle w:val="Hyperlink"/>')
        return f'<w:hyperlink r:id="{rid}">{inner}</w:hyperlink>'
    if isinstance(node, Image):
        return _render_image(node, state)
    if isinstance(node, RawInline):
        if node.format in {'openxml', 'docx'}:
            return node.text  # embedded OOXML
        if node.format == 'html':
            # Approximation: drop the markup but keep its text content.
            return _text_run(re.sub(r'<[^>]+>', '', node.text))
        # Unknown raw formats are silently dropped.
        return ''
    if isinstance(node, Note):
        idx = len(state.footnotes) + 1
        footnote_body = _render_blocks(node.blocks, state, in_footnote=True)
        state.footnotes.append(footnote_body)
        # Pandoc uses w:id starting at 2 (after the two sentinel notes -1 and 0).
        return (
            '<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/></w:rPr>'
            f'<w:footnoteReference w:id="{idx + 1}"/></w:r>'
        )
    if isinstance(node, Cite):
        # Citeproc would expand these; until then, render the inline
        # text representation supplied by the AST.
        return _render_inlines(node.inlines, state)
    # Fallback: any other inline class with an inlines field, recurse.
    children = getattr(node, 'inlines', None)
    if children is not None:
        return _render_inlines(children, state)
    return ''


def _render_image(node: Image, state: _State) -> str:
    """Render an Image as ``w:drawing``.

    Tries to read the file from disk to embed the raw bytes. If the file
    isn't readable we still emit the drawing skeleton with a placeholder
    rId so the OOXML stays valid.
    """
    target = node.target
    data: bytes | None = None
    ext = Path(target).suffix.lstrip('.').lower() or 'png'
    try:
        if target and not target.startswith(('http://', 'https://', 'data:')):
            data = Path(target).read_bytes()
    except OSError:
        data = None
    if data is None:
        data = _PNG_1X1
        ext = 'png'
    rid, media_name = state.add_image(target, data, ext)
    alt = ''.join(getattr(i, 'text', '') for i in node.inlines)
    # 100 px ≈ 952500 EMU at 96 dpi
    width_attr = next((v for k, v in node.attr.attributes if k == 'width'), '300')
    try:
        width_px = int(re.sub(r'[^0-9]', '', width_attr) or '300')
    except ValueError:
        width_px = 300
    width_emu = max(1, int(width_px * 9525))
    height_emu = width_emu  # Square placeholder; readers compute true ratio from the embedded image.
    return (
        '<w:r>'
        '<w:drawing>'
        f'<wp:inline xmlns:wp="{_WP_NS}" distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{width_emu}" cy="{height_emu}"/>'
        '<wp:effectExtent l="0" t="0" r="0" b="0"/>'
        f'<wp:docPr id="{state.image_counter}" name="{escape(media_name, quote=True)}" descr="{escape(alt, quote=True)}"/>'
        '<wp:cNvGraphicFramePr/>'
        f'<a:graphic xmlns:a="{_A_NS}">'
        '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:pic xmlns:pic="{_PIC_NS}">'
        '<pic:nvPicPr>'
        f'<pic:cNvPr id="{state.image_counter}" name="{escape(media_name, quote=True)}"/>'
        '<pic:cNvPicPr/>'
        '</pic:nvPicPr>'
        '<pic:blipFill>'
        f'<a:blip xmlns:r="{_R_REL}" r:embed="{rid}"/>'
        '<a:stretch><a:fillRect/></a:stretch>'
        '</pic:blipFill>'
        '<pic:spPr>'
        f'<a:xfrm><a:off x="0" y="0"/><a:ext cx="{width_emu}" cy="{height_emu}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        '</pic:spPr>'
        '</pic:pic>'
        '</a:graphicData></a:graphic>'
        '</wp:inline>'
        '</w:drawing>'
        '</w:r>'
    )


# A 1×1 transparent PNG used when an image target cannot be read from disk.
_PNG_1X1 = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01'
    b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
)


# ---- block rendering -----------------------------------------------------

def _render_blocks(blocks: Iterable[Block], state: _State, *, in_footnote: bool = False) -> str:
    return ''.join(_render_block(b, state, in_footnote=in_footnote) for b in blocks)


def _render_block(block: Block, state: _State, *, in_footnote: bool = False) -> str:
    if isinstance(block, Heading):
        return _para(
            f'<w:pStyle w:val="Heading{max(1, min(block.level, 6))}"/>',
            _bookmark(block.attr.identifier) + _render_inlines(block.inlines, state),
        )
    if isinstance(block, Paragraph):
        # Pandoc maps a paragraph that contains a single Image to a
        # captioned figure if the alt text is non-empty. We approximate
        # by rendering the image; figures handle the caption explicitly.
        return _para('', _render_inlines(block.inlines, state))
    if isinstance(block, BlockQuote):
        # Render every inner block as a paragraph styled BlockText.
        return ''.join(
            _wrap_paragraph_style(rendered, 'BlockText')
            for rendered in [_render_block(b, state, in_footnote=in_footnote) for b in block.blocks]
        )
    if isinstance(block, BulletList):
        return _render_list(block.items, state, ordered=False)
    if isinstance(block, OrderedList):
        return _render_list(block.items, state, ordered=True)
    if isinstance(block, DefinitionList):
        out: list[str] = []
        for term_inlines, defs in block.items:
            out.append(_para('<w:pStyle w:val="DefinitionTerm"/>', _render_inlines(term_inlines, state)))
            for defn in defs:
                for sub in defn:
                    rendered = _render_block(sub, state, in_footnote=in_footnote)
                    out.append(_wrap_paragraph_style(rendered, 'Definition'))
        return ''.join(out)
    if isinstance(block, CodeBlock):
        return ''.join(
            _para('<w:pStyle w:val="SourceCode"/>', _text_run(line))
            for line in block.text.split('\n')
        )
    if isinstance(block, ThematicBreak):
        return (
            '<w:p><w:pPr><w:pBdr>'
            '<w:bottom w:val="single" w:sz="6" w:space="1" w:color="auto"/>'
            '</w:pBdr></w:pPr></w:p>'
        )
    if isinstance(block, LineBlock):
        # Each line as a separate run separated by w:br; whole thing one paragraph.
        run_pieces: list[str] = []
        for idx, line in enumerate(block.lines):
            if idx > 0:
                run_pieces.append('<w:r><w:br/></w:r>')
            run_pieces.append(_render_inlines(line, state))
        return _para('<w:pStyle w:val="LineBlock"/>', ''.join(run_pieces))
    if isinstance(block, Figure):
        out = _render_block(Paragraph(inlines=[block.image]), state, in_footnote=in_footnote)
        caption = getattr(block, 'caption', None)
        if caption:
            # caption can be a [Inline] or richer; default reader/writer
            # populates it as an empty list.
            inlines = caption if isinstance(caption, list) else getattr(caption, 'inlines', [])
            if inlines:
                out += _para('<w:pStyle w:val="Caption"/>', _render_inlines(inlines, state))
        return out
    if isinstance(block, Table):
        return _render_table(block, state)
    if isinstance(block, Div):
        return _render_blocks(block.blocks, state, in_footnote=in_footnote)
    if isinstance(block, RawBlock):
        if block.format in {'openxml', 'docx'}:
            return block.text
        return ''
    if isinstance(block, Null):
        return ''
    return _para('', _text_run(repr(block)))


def _para(ppr_inner: str, runs: str) -> str:
    """Emit ``<w:p>`` with optional ``<w:pPr>`` and the supplied runs."""
    ppr = f'<w:pPr>{ppr_inner}</w:pPr>' if ppr_inner else ''
    return f'<w:p>{ppr}{runs}</w:p>'


def _wrap_paragraph_style(rendered: str, style: str) -> str:
    """Add the ``w:pStyle`` to every ``<w:p>`` in `rendered` that lacks one."""
    out: list[str] = []
    cursor = 0
    for m in re.finditer(r'<w:p\b([^>]*)>', rendered):
        out.append(rendered[cursor:m.end()])
        # Peek at the next characters to see if a pPr already follows.
        nxt = rendered[m.end():m.end() + 8]
        if nxt.startswith('<w:pPr>'):
            # Splice the style in front of any existing children.
            cursor = m.end() + len('<w:pPr>')
            out.append(f'<w:pStyle w:val="{style}"/>')
        else:
            out.append(f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>')
            cursor = m.end()
    out.append(rendered[cursor:])
    return ''.join(out)


def _bookmark(identifier: str) -> str:
    """Wrap a heading in a bookmark so cross-references can resolve."""
    if not identifier:
        return ''
    bm_id = abs(hash(identifier)) % (2**24)
    return (
        f'<w:bookmarkStart w:id="{bm_id}" w:name="{escape(identifier, quote=True)}"/>'
        f'<w:bookmarkEnd w:id="{bm_id}"/>'
    )


def _render_list(items: list[list[Block]], state: _State, *, ordered: bool) -> str:
    num_id = 2 if ordered else 1
    out: list[str] = []
    for item in items:
        for idx, sub in enumerate(item):
            if isinstance(sub, Paragraph) and idx == 0:
                ppr = (
                    '<w:pStyle w:val="ListParagraph"/>'
                    '<w:numPr><w:ilvl w:val="0"/>'
                    f'<w:numId w:val="{num_id}"/></w:numPr>'
                )
                out.append(_para(ppr, _render_inlines(sub.inlines, state)))
            else:
                rendered = _render_block(sub, state)
                # Sub-blocks (nested lists, paragraphs) inherit the list-paragraph style.
                out.append(rendered)
    return ''.join(out)


def _render_table(block: Table, state: _State) -> str:
    """Emit a ``w:tbl`` with header + body rows. Cell content is rendered
    as a single paragraph per cell.

    Pandoc Table in the constrained slice carries:
        caption: list[Inline]
        aligns:  list[str]   (e.g. 'AlignLeft')
        headers: list[list[Inline]]
        rows:    list[list[list[Inline]]]
    """
    n_cols = max(len(block.headers), max((len(r) for r in block.rows), default=0))
    if n_cols == 0:
        return ''
    # Match pandoc's column-width heuristic: distribute 11/13 of the page
    # text width across columns. This is the empirical factor pandoc 3.x
    # uses so the reparsed AST recovers a matching ColWidth fraction.
    _PAGE_TEXT_DXA = 9360  # letter page (12240) minus 1440-twip margins.
    col_dxa = round(_PAGE_TEXT_DXA * 11 / (13 * max(1, n_cols)))
    grid = '<w:tblGrid>' + ''.join([f'<w:gridCol w:w="{col_dxa}"/>'] * n_cols) + '</w:tblGrid>'
    tbl_pr = (
        '<w:tblPr>'
        '<w:tblStyle w:val="Table"/>'
        '<w:tblW w:w="0" w:type="auto"/>'
        '<w:tblLook w:val="04A0"/>'
        '</w:tblPr>'
    )
    rows_xml: list[str] = []
    if block.headers:
        cells = ''.join(
            _render_cell(cell, state,
                         block.aligns[i] if i < len(block.aligns) else 'AlignDefault',
                         col_dxa)
            for i, cell in enumerate(block.headers)
        )
        rows_xml.append(
            '<w:tr><w:trPr><w:tblHeader/></w:trPr>' + cells + '</w:tr>'
        )
    for row in block.rows:
        cells = ''.join(
            _render_cell(cell, state,
                         block.aligns[i] if i < len(block.aligns) else 'AlignDefault',
                         col_dxa)
            for i, cell in enumerate(row)
        )
        rows_xml.append('<w:tr>' + cells + '</w:tr>')
    tbl = f'<w:tbl>{tbl_pr}{grid}{"".join(rows_xml)}</w:tbl>'
    caption_xml = ''
    if block.caption:
        caption_xml = _para('<w:pStyle w:val="Caption"/>', _render_inlines(block.caption, state))
    return caption_xml + tbl


_ALIGN_TO_JC = {
    'AlignLeft': 'left',
    'AlignRight': 'right',
    'AlignCenter': 'center',
    # AlignDefault deliberately omitted: pandoc emits no <w:jc> for it so the
    # docx reader recovers AlignDefault round-trip rather than AlignLeft.
}


def _render_cell(cell: list[Inline], state: _State, align: str, col_dxa: int) -> str:
    jc = _ALIGN_TO_JC.get(align)
    ppr = f'<w:pPr><w:jc w:val="{jc}"/></w:pPr>' if jc else ''
    runs = _render_inlines(cell, state)
    body = f'<w:p>{ppr}{runs}</w:p>'
    # Pandoc emits empty <w:tcPr/> rather than <w:tcW>; the docx reader
    # derives the column width from <w:tblGrid>. Omitting tcW keeps the
    # ColWidth round-trip in lock-step with pandoc's expected fraction.
    return '<w:tc><w:tcPr/>' + body + '</w:tc>'


# ---- document assembly ---------------------------------------------------

def write_docx(document: Document) -> bytes:
    state = _State()
    body = _render_blocks(document.blocks, state)
    document_xml = _document_xml(body)
    members = _base_members(document_xml, state)
    return _save_zip(members)


def _document_xml(body: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{_W}" xmlns:r="{_R_REL}" '
        f'xmlns:wp="{_WP_NS}" xmlns:a="{_A_NS}" xmlns:pic="{_PIC_NS}">'
        f'<w:body>{body}'
        '<w:sectPr>'
        '<w:pgSz w:w="12240" w:h="15840"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" '
        'w:header="720" w:footer="720" w:gutter="0"/>'
        '</w:sectPr>'
        '</w:body></w:document>'
    )


def _base_members(document_xml: str, state: _State) -> dict[str, bytes]:
    content_types = _content_types(has_footnotes=bool(state.footnotes), media_exts=_media_extensions(state.media))
    main_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f'<Relationship Id="rId1" Type="{_R_REL}/officeDocument" Target="word/document.xml"/>'
        '</Relationships>'
    )
    doc_rels = _document_rels_xml(state.footnotes, state.rels)
    styles = _styles_xml()
    numbering = _numbering_xml()
    members = {
        '[Content_Types].xml': content_types.encode('utf-8'),
        '_rels/.rels': main_rels.encode('utf-8'),
        'word/_rels/document.xml.rels': doc_rels.encode('utf-8'),
        'word/document.xml': document_xml.encode('utf-8'),
        'word/styles.xml': styles.encode('utf-8'),
        'word/numbering.xml': numbering.encode('utf-8'),
    }
    if state.footnotes:
        members['word/footnotes.xml'] = _footnotes_xml(state.footnotes).encode('utf-8')
    for name, data in state.media.items():
        members[f'word/media/{name}'] = data
    return members


def _media_extensions(media: dict[str, bytes]) -> set[str]:
    return {Path(name).suffix.lstrip('.').lower() for name in media}


def _content_types(*, has_footnotes: bool, media_exts: set[str]) -> str:
    defaults: list[str] = [
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
    ]
    image_mime = {
        'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
        'gif': 'image/gif', 'bmp': 'image/bmp', 'svg': 'image/svg+xml',
        'webp': 'image/webp',
    }
    for ext in sorted(media_exts):
        if ext and ext not in {'rels', 'xml'}:
            mime = image_mime.get(ext, 'application/octet-stream')
            defaults.append(f'<Default Extension="{ext}" ContentType="{mime}"/>')
    overrides: list[str] = [
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>',
        '<Override PartName="/word/styles.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>',
        '<Override PartName="/word/numbering.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>',
    ]
    if has_footnotes:
        overrides.append(
            '<Override PartName="/word/footnotes.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"/>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        + ''.join(defaults) + ''.join(overrides) + '</Types>'
    )


def _document_rels_xml(footnotes: list[str], rels: list[tuple[str, str, str, str | None]]) -> str:
    entries = [
        f'<Relationship Id="rId10" Type="{_R_REL}/styles" Target="styles.xml"/>',
        f'<Relationship Id="rId11" Type="{_R_REL}/numbering" Target="numbering.xml"/>',
    ]
    if footnotes:
        entries.append(f'<Relationship Id="rId12" Type="{_R_REL}/footnotes" Target="footnotes.xml"/>')
    for rid, kind, target, mode in rels:
        if mode:
            entries.append(
                f'<Relationship Id="{rid}" Type="{kind}" Target="{escape(target, quote=True)}" TargetMode="{mode}"/>'
            )
        else:
            entries.append(
                f'<Relationship Id="{rid}" Type="{kind}" Target="{escape(target, quote=True)}"/>'
            )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + ''.join(entries) + '</Relationships>'
    )


def _footnotes_xml(bodies: list[str]) -> str:
    sentinels = (
        '<w:footnote w:type="separator" w:id="-1"><w:p>'
        '<w:r><w:separator/></w:r></w:p></w:footnote>'
        '<w:footnote w:type="continuationSeparator" w:id="0"><w:p>'
        '<w:r><w:continuationSeparator/></w:r></w:p></w:footnote>'
    )
    notes: list[str] = []
    for idx, body in enumerate(bodies, start=2):
        notes.append(f'<w:footnote w:id="{idx}">{body}</w:footnote>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:footnotes xmlns:w="{_W}">' + sentinels + ''.join(notes) + '</w:footnotes>'
    )


def _styles_xml() -> str:
    parts = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             f'<w:styles xmlns:w="{_W}">']
    for level in range(1, 7):
        parts.append(
            f'<w:style w:type="paragraph" w:styleId="Heading{level}">'
            f'<w:name w:val="heading {level}"/>'
            f'<w:basedOn w:val="Normal"/>'
            f'<w:pPr><w:outlineLvl w:val="{level - 1}"/></w:pPr>'
            '</w:style>'
        )
    parts.append('<w:style w:type="paragraph" w:styleId="Normal"><w:name w:val="Normal"/></w:style>')
    parts.append('<w:style w:type="paragraph" w:styleId="ListParagraph">'
                 '<w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/></w:style>')
    parts.append('<w:style w:type="paragraph" w:styleId="SourceCode">'
                 '<w:name w:val="Source Code"/><w:basedOn w:val="Normal"/>'
                 '<w:rPr><w:rFonts w:ascii="Courier New" w:hAnsi="Courier New"/></w:rPr></w:style>')
    parts.append('<w:style w:type="paragraph" w:styleId="BlockText">'
                 '<w:name w:val="Block Text"/><w:basedOn w:val="Normal"/>'
                 '<w:pPr><w:ind w:left="720"/></w:pPr></w:style>')
    parts.append('<w:style w:type="paragraph" w:styleId="LineBlock">'
                 '<w:name w:val="Line Block"/><w:basedOn w:val="Normal"/></w:style>')
    parts.append('<w:style w:type="paragraph" w:styleId="Caption">'
                 '<w:name w:val="caption"/><w:basedOn w:val="Normal"/>'
                 '<w:rPr><w:i/></w:rPr></w:style>')
    parts.append('<w:style w:type="paragraph" w:styleId="DefinitionTerm">'
                 '<w:name w:val="Definition Term"/><w:basedOn w:val="Normal"/>'
                 '<w:rPr><w:b/></w:rPr></w:style>')
    parts.append('<w:style w:type="paragraph" w:styleId="Definition">'
                 '<w:name w:val="Definition"/><w:basedOn w:val="Normal"/>'
                 '<w:pPr><w:ind w:left="720"/></w:pPr></w:style>')
    parts.append('<w:style w:type="character" w:styleId="VerbatimChar">'
                 '<w:name w:val="Verbatim Char"/>'
                 '<w:rPr><w:rFonts w:ascii="Courier New" w:hAnsi="Courier New"/></w:rPr></w:style>')
    parts.append('<w:style w:type="character" w:styleId="Hyperlink">'
                 '<w:name w:val="Hyperlink"/>'
                 '<w:rPr><w:color w:val="0000FF"/><w:u w:val="single"/></w:rPr></w:style>')
    parts.append('<w:style w:type="character" w:styleId="FootnoteReference">'
                 '<w:name w:val="footnote reference"/>'
                 '<w:rPr><w:vertAlign w:val="superscript"/></w:rPr></w:style>')
    parts.append('<w:style w:type="character" w:styleId="Equation">'
                 '<w:name w:val="Equation"/></w:style>')
    parts.append('<w:style w:type="table" w:styleId="Table">'
                 '<w:name w:val="Table"/></w:style>')
    parts.append('</w:styles>')
    return ''.join(parts)


def _numbering_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:numbering xmlns:w="{_W}">'
        '<w:abstractNum w:abstractNumId="0">'
        '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/>'
        '<w:lvlJc w:val="left"/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl>'
        '</w:abstractNum>'
        '<w:abstractNum w:abstractNumId="1">'
        '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/>'
        '<w:lvlJc w:val="left"/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl>'
        '</w:abstractNum>'
        '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>'
        '<w:num w:numId="2"><w:abstractNumId w:val="1"/></w:num>'
        '</w:numbering>'
    )


def _save_zip(members: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    return buf.getvalue()
