"""Binary container formats — DOCX, PPTX, XLSX, ODT, EPUB.

These formats are zip containers wrapping XML payloads. The constrained
slice for each:

- Reader: open the zip, find the canonical content XML, parse it as a flat
  sequence of headings and paragraphs (other shapes degrade to paragraphs).
- Writer: build a minimal zip whose payload contains a Pandoc-style flat
  rendering of the AST. Each output passes a basic 'open in target tool'
  smoke check, which is the admitted slice.

For oracle differential testing each format requires a binary comparator.
The reports are deferred until the binary-comparator policy is admitted in
a follow-up packet.
"""
from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
import zipfile
from html import escape
from pathlib import Path

from pandoc_py.ast import (
    BulletList, CodeBlock, Document, Heading, OrderedList, Paragraph,
)
from pandoc_py.io import Reader, Writer, register_reader, register_writer
from ._common import block_text_paragraphs, inlines_to_plain, text_to_inlines


# ----- shared zip helpers --------------------------------------------------

def _zip_load_text(data: bytes, member: str) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        with zf.open(member) as f:
            return f.read().decode('utf-8')


def _zip_save(members: dict[str, bytes]) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, content in members.items():
            zf.writestr(name, content)
    return out.getvalue()


def _coerce_bytes(source) -> bytes:
    if isinstance(source, str):
        return source.encode('latin-1', errors='ignore')
    return source


# ----- DOCX ----------------------------------------------------------------

_DOCX_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
_DOCX_W = '{' + _DOCX_NS + '}'


def _read_docx(source) -> Document:
    """DOCX reader admitting Heading, Paragraph, BulletList, OrderedList,
    and CodeBlock from the basic OOXML surface.

    A paragraph with `w:numPr/w:numId` becomes a list item (collapsed
    into BulletList or OrderedList based on the `w:abstractNum`'s
    numFmt). Paragraphs styled `Heading{N}` become Heading nodes.
    Paragraphs styled `SourceCode` are joined into a single CodeBlock.
    """
    data = _coerce_bytes(source)
    xml = _zip_load_text(data, 'word/document.xml')
    root = ET.fromstring(xml)
    # Resolve numId → numFmt via numbering.xml when available.
    num_kind: dict[str, str] = {}
    try:
        num_xml = _zip_load_text(data, 'word/numbering.xml')
        num_root = ET.fromstring(num_xml)
        abstract_kind: dict[str, str] = {}
        for an in num_root.iter(_DOCX_W + 'abstractNum'):
            an_id = an.attrib.get(_DOCX_W + 'abstractNumId', '')
            for fmt_el in an.iter(_DOCX_W + 'numFmt'):
                abstract_kind[an_id] = fmt_el.attrib.get(_DOCX_W + 'val', 'bullet')
                break
        for n in num_root.iter(_DOCX_W + 'num'):
            n_id = n.attrib.get(_DOCX_W + 'numId', '')
            for ref in n.iter(_DOCX_W + 'abstractNumId'):
                num_kind[n_id] = abstract_kind.get(ref.attrib.get(_DOCX_W + 'val', ''), 'bullet')
                break
    except KeyError:
        pass

    blocks: list = []
    pending_bullet: list[str] | None = None
    pending_ordered: list[str] | None = None
    pending_code: list[str] | None = None

    def flush_pending():
        nonlocal pending_bullet, pending_ordered, pending_code
        if pending_bullet is not None:
            blocks.append(BulletList(items=[
                [Paragraph(inlines=text_to_inlines(t), is_plain=True)] for t in pending_bullet
            ]))
            pending_bullet = None
        if pending_ordered is not None:
            blocks.append(OrderedList(items=[
                [Paragraph(inlines=text_to_inlines(t), is_plain=True)] for t in pending_ordered
            ]))
            pending_ordered = None
        if pending_code is not None:
            blocks.append(CodeBlock(text='\n'.join(pending_code)))
            pending_code = None

    for p in root.iter(_DOCX_W + 'p'):
        text_parts = [t.text or '' for t in p.iter(_DOCX_W + 't')]
        text = ''.join(text_parts).strip()
        # numPr → list item
        num_id = ''
        for ni in p.iter(_DOCX_W + 'numId'):
            num_id = ni.attrib.get(_DOCX_W + 'val', '')
            break
        if num_id:
            kind = num_kind.get(num_id, 'bullet')
            if kind == 'bullet':
                if pending_ordered is not None or pending_code is not None:
                    flush_pending()
                if pending_bullet is None:
                    pending_bullet = []
                pending_bullet.append(text)
            else:
                if pending_bullet is not None or pending_code is not None:
                    flush_pending()
                if pending_ordered is None:
                    pending_ordered = []
                pending_ordered.append(text)
            continue
        style = ''
        for ps in p.iter(_DOCX_W + 'pStyle'):
            style = ps.attrib.get(_DOCX_W + 'val', '')
            break
        if style == 'SourceCode':
            if pending_bullet is not None or pending_ordered is not None:
                flush_pending()
            if pending_code is None:
                pending_code = []
            pending_code.append(text)
            continue
        flush_pending()
        if not text:
            continue
        m = re.match(r'^Heading(\d)$', style or '')
        if m:
            blocks.append(Heading(level=int(m.group(1)), inlines=text_to_inlines(text)))
        else:
            blocks.append(Paragraph(inlines=text_to_inlines(text)))
    flush_pending()
    return Document(blocks=blocks, source_format='docx')


def _docx_paragraph(text: str, style: str | None = None) -> str:
    s = ''
    if style:
        s = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>'
    return f'<w:p>{s}<w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'


def _docx_list_paragraph(text: str, *, ordered: bool) -> str:
    num_id = '2' if ordered else '1'
    return (
        '<w:p>'
        '<w:pPr>'
        f'<w:pStyle w:val="ListParagraph"/>'
        '<w:numPr>'
        '<w:ilvl w:val="0"/>'
        f'<w:numId w:val="{num_id}"/>'
        '</w:numPr>'
        '</w:pPr>'
        f'<w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r>'
        '</w:p>'
    )


def _write_docx(document: Document) -> bytes:
    body_parts: list[str] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            body_parts.append(_docx_paragraph(inlines_to_plain(block.inlines), f'Heading{max(1, min(block.level, 6))}'))
        elif isinstance(block, Paragraph):
            body_parts.append(_docx_paragraph(inlines_to_plain(block.inlines)))
        elif isinstance(block, BulletList):
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    body_parts.append(_docx_list_paragraph(sub, ordered=False))
        elif isinstance(block, OrderedList):
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    body_parts.append(_docx_list_paragraph(sub, ordered=True))
        elif isinstance(block, CodeBlock):
            for ln in block.text.split('\n'):
                body_parts.append(_docx_paragraph(ln, 'SourceCode'))

    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{_DOCX_NS}">'
        '<w:body>' + ''.join(body_parts) + '</w:body></w:document>'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        '<Override PartName="/word/numbering.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
        '</Types>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/></Relationships>'
    )
    document_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId10" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
        'Target="styles.xml"/>'
        '<Relationship Id="rId11" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" '
        'Target="numbering.xml"/>'
        '</Relationships>'
    )
    style_entries = []
    for level in range(1, 7):
        style_entries.append(
            f'<w:style w:type="paragraph" w:styleId="Heading{level}">'
            f'<w:name w:val="heading {level}"/>'
            f'<w:pPr><w:outlineLvl w:val="{level - 1}"/></w:pPr>'
            '</w:style>'
        )
    style_entries.append(
        '<w:style w:type="paragraph" w:styleId="ListParagraph">'
        '<w:name w:val="List Paragraph"/></w:style>'
    )
    style_entries.append(
        '<w:style w:type="paragraph" w:styleId="SourceCode">'
        '<w:name w:val="Source Code"/></w:style>'
    )
    styles_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:styles xmlns:w="{_DOCX_NS}">' + ''.join(style_entries) + '</w:styles>'
    )
    numbering_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:numbering xmlns:w="{_DOCX_NS}">'
        '<w:abstractNum w:abstractNumId="0">'
        '<w:lvl w:ilvl="0"><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/></w:lvl>'
        '</w:abstractNum>'
        '<w:abstractNum w:abstractNumId="1">'
        '<w:lvl w:ilvl="0"><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/></w:lvl>'
        '</w:abstractNum>'
        '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>'
        '<w:num w:numId="2"><w:abstractNumId w:val="1"/></w:num>'
        '</w:numbering>'
    )
    return _zip_save({
        '[Content_Types].xml': content_types.encode('utf-8'),
        '_rels/.rels': rels.encode('utf-8'),
        'word/_rels/document.xml.rels': document_rels.encode('utf-8'),
        'word/document.xml': document_xml.encode('utf-8'),
        'word/styles.xml': styles_xml.encode('utf-8'),
        'word/numbering.xml': numbering_xml.encode('utf-8'),
    })


class DocxReader(Reader):
    format_name = 'docx'
    binary = True
    def read(self, source, options=None):
        return _read_docx(source)

class DocxWriter(Writer):
    format_name = 'docx'
    binary = True
    def write(self, document, options=None):
        return _write_docx(document)

register_reader(DocxReader())
register_writer(DocxWriter())


# ----- ODT -----------------------------------------------------------------

def _read_odt(source) -> Document:
    """ODT reader admitting Heading, Paragraph, BulletList, OrderedList.

    A ``text:list`` element becomes BulletList (default) or OrderedList
    (if its style declares a list-level-style-number); each immediate
    ``text:list-item`` contributes one item.
    """
    _ODT_TEXT = 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'
    _ODT_T = '{' + _ODT_TEXT + '}'
    data = _coerce_bytes(source)
    xml = _zip_load_text(data, 'content.xml')
    root = ET.fromstring(xml)
    # Resolve list-style names to bullet/ordered.
    list_kind: dict[str, str] = {}
    try:
        styles_xml = _zip_load_text(data, 'styles.xml')
        for ls in ET.fromstring(styles_xml).iter():
            if ls.tag.split('}')[-1] == 'list-style':
                name = ls.attrib.get('{urn:oasis:names:tc:opendocument:xmlns:style:1.0}name')
                if not name: continue
                kind = 'bullet'
                for child in ls:
                    if child.tag.split('}')[-1] == 'list-level-style-number':
                        kind = 'ordered'; break
                list_kind[name] = kind
    except KeyError:
        pass
    # Also check content.xml automatic-styles for inline list styles.
    for ls in root.iter():
        if ls.tag.split('}')[-1] == 'list-style':
            name = ls.attrib.get('{urn:oasis:names:tc:opendocument:xmlns:style:1.0}name')
            if not name: continue
            kind = 'bullet'
            for child in ls:
                if child.tag.split('}')[-1] == 'list-level-style-number':
                    kind = 'ordered'; break
            list_kind[name] = kind

    blocks: list = []

    def walk(el, depth):
        for child in el:
            tag = child.tag.split('}')[-1]
            if tag == 'h':
                level = int(child.attrib.get(_ODT_T + 'outline-level', '1'))
                text = ''.join(child.itertext()).strip()
                if text:
                    blocks.append(Heading(level=level, inlines=text_to_inlines(text)))
            elif tag == 'p':
                text = ''.join(child.itertext()).strip()
                if text:
                    blocks.append(Paragraph(inlines=text_to_inlines(text)))
            elif tag == 'list':
                style_name = child.attrib.get(_ODT_T + 'style-name', '')
                kind = list_kind.get(style_name, 'bullet')
                items = []
                for li in child:
                    if li.tag.split('}')[-1] == 'list-item':
                        item_text = ''.join(li.itertext()).strip()
                        items.append([Paragraph(inlines=text_to_inlines(item_text), is_plain=True)])
                if items:
                    blocks.append(OrderedList(items=items) if kind == 'ordered' else BulletList(items=items))
            else:
                walk(child, depth + 1)

    walk(root, 0)
    return Document(blocks=blocks, source_format='odt')


def _write_odt(document: Document) -> bytes:
    body: list[str] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            body.append(f'<text:h text:outline-level="{max(1, min(block.level, 6))}">'
                        f'{escape(inlines_to_plain(block.inlines))}</text:h>')
        elif isinstance(block, Paragraph):
            body.append(f'<text:p>{escape(inlines_to_plain(block.inlines))}</text:p>')
        elif isinstance(block, BulletList):
            body.append('<text:list text:style-name="ListBullet">')
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    body.append(f'<text:list-item><text:p>{escape(sub)}</text:p></text:list-item>')
            body.append('</text:list>')
        elif isinstance(block, OrderedList):
            body.append('<text:list text:style-name="ListNumber">')
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    body.append(f'<text:list-item><text:p>{escape(sub)}</text:p></text:list-item>')
            body.append('</text:list>')
        elif isinstance(block, CodeBlock):
            for ln in block.text.split('\n'):
                body.append(f'<text:p>{escape(ln)}</text:p>')
    content_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<office:document-content '
        'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
        'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
        'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0">'
        '<office:automatic-styles>'
        '<text:list-style style:name="ListBullet">'
        '<text:list-level-style-bullet text:level="1" text:bullet-char="•"/>'
        '</text:list-style>'
        '<text:list-style style:name="ListNumber">'
        '<text:list-level-style-number text:level="1" style:num-format="1" style:num-suffix="."/>'
        '</text:list-style>'
        '</office:automatic-styles>'
        '<office:body><office:text>' + ''.join(body) + '</office:text></office:body>'
        '</office:document-content>'
    )
    mimetype = 'application/vnd.oasis.opendocument.text'
    styles_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<office:document-styles '
        'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
        'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">'
        '<office:styles>'
        '<text:list-style style:name="ListBullet" '
        'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0">'
        '<text:list-level-style-bullet text:level="1" text:bullet-char="•"/>'
        '</text:list-style>'
        '<text:list-style style:name="ListNumber" '
        'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0">'
        '<text:list-level-style-number text:level="1" style:num-format="1" style:num-suffix="."/>'
        '</text:list-style>'
        '</office:styles>'
        '</office:document-styles>'
    )
    manifest = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<manifest:manifest '
        'xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0">'
        '<manifest:file-entry manifest:media-type="application/vnd.oasis.opendocument.text" '
        'manifest:full-path="/"/>'
        '<manifest:file-entry manifest:media-type="text/xml" manifest:full-path="content.xml"/>'
        '<manifest:file-entry manifest:media-type="text/xml" manifest:full-path="styles.xml"/>'
        '</manifest:manifest>'
    )
    return _zip_save({
        'mimetype': mimetype.encode('ascii'),
        'content.xml': content_xml.encode('utf-8'),
        'styles.xml': styles_xml.encode('utf-8'),
        'META-INF/manifest.xml': manifest.encode('utf-8'),
    })


class OdtReader(Reader):
    format_name = 'odt'
    binary = True
    def read(self, source, options=None):
        return _read_odt(source)

class OdtWriter(Writer):
    format_name = 'odt'
    binary = True
    def write(self, document, options=None):
        return _write_odt(document)

register_reader(OdtReader())
register_writer(OdtWriter())


# ----- PPTX (writer-only — readers map slides to headings + paragraphs) ----

def _write_pptx(document: Document) -> bytes:
    # A minimal PPTX with one slide per Heading.
    slides_xml: list[str] = []
    current_title = ''
    current_body: list[str] = []
    slides: list[tuple[str, list[str]]] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            if current_title or current_body:
                slides.append((current_title, current_body))
            current_title = inlines_to_plain(block.inlines)
            current_body = []
        elif isinstance(block, Paragraph):
            current_body.append(inlines_to_plain(block.inlines))
    if current_title or current_body:
        slides.append((current_title, current_body))

    members: dict[str, bytes] = {}
    members['[Content_Types].xml'] = (
        '<?xml version="1.0"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Override PartName="/ppt/presentation.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
        '</Types>'
    ).encode('utf-8')
    members['_rels/.rels'] = (
        '<?xml version="1.0"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="ppt/presentation.xml"/></Relationships>'
    ).encode('utf-8')
    pres_xml = ('<?xml version="1.0"?>'
                '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
                '<p:sldIdLst>'
                + ''.join(f'<p:sldId id="{256 + i}" r:id="rId{10 + i}" '
                          f'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>'
                          for i in range(len(slides)))
                + '</p:sldIdLst></p:presentation>')
    members['ppt/presentation.xml'] = pres_xml.encode('utf-8')
    for idx, (title, paras) in enumerate(slides):
        body_xml = ''.join(
            f'<p:sp><p:txBody><a:p xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            f'<a:r><a:t>{escape(p)}</a:t></a:r></a:p></p:txBody></p:sp>'
            for p in [title, *paras]
        )
        members[f'ppt/slides/slide{idx + 1}.xml'] = (
            '<?xml version="1.0"?>'
            '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            '<p:cSld><p:spTree>' + body_xml + '</p:spTree></p:cSld></p:sld>'
        ).encode('utf-8')
    return _zip_save(members)


class PptxWriter(Writer):
    format_name = 'pptx'
    binary = True
    def write(self, document, options=None):
        return _write_pptx(document)

register_writer(PptxWriter())


# Pptx reader — best-effort: pick text out of slide XML files.
def _read_pptx(source) -> Document:
    """PPTX reader.

    Each ``ppt/slides/slide*.xml`` becomes one slide. The first text
    shape on a slide is captured as a Heading (level 1, the slide
    title). Subsequent shapes are walked paragraph-by-paragraph; an
    ``<a:p>`` whose ``<a:pPr>`` carries ``<a:buChar>`` is collected as
    a bullet-list item; ``<a:buAutoNum>`` triggers an OrderedList; an
    ``<a:p>`` without a bullet marker is a Paragraph. Consecutive
    bullet items collapse into a single BulletList/OrderedList block.
    """
    data = _coerce_bytes(source)
    blocks: list = []
    a_ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'
    a_t = '{' + a_ns + '}'
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for name in sorted(zf.namelist()):
            if not (name.startswith('ppt/slides/slide') and name.endswith('.xml')):
                continue
            xml = zf.read(name).decode('utf-8')
            root = ET.fromstring(xml)
            shape_paragraphs: list[tuple[str, str]] = []  # (kind, text)
            for sp in root.iter():
                if sp.tag.split('}')[-1] != 'sp':
                    continue
                for p in sp.iter(a_t + 'p'):
                    text = ''.join((t.text or '') for t in p.iter(a_t + 't')).strip()
                    if not text:
                        continue
                    kind = 'para'
                    pPr = p.find(a_t + 'pPr')
                    if pPr is not None:
                        if pPr.find(a_t + 'buChar') is not None:
                            kind = 'bullet'
                        elif pPr.find(a_t + 'buAutoNum') is not None:
                            kind = 'ordered'
                    shape_paragraphs.append((kind, text))
            if not shape_paragraphs:
                continue
            # Title is the first non-bullet, non-ordered paragraph.
            title_idx = next((i for i, (k, _) in enumerate(shape_paragraphs) if k == 'para'), None)
            if title_idx is not None:
                blocks.append(Heading(level=1, inlines=text_to_inlines(shape_paragraphs[title_idx][1])))
                rest = shape_paragraphs[:title_idx] + shape_paragraphs[title_idx + 1:]
            else:
                rest = list(shape_paragraphs)
            i = 0
            while i < len(rest):
                kind, text = rest[i]
                if kind in {'bullet', 'ordered'}:
                    items = []
                    target_kind = kind
                    while i < len(rest) and rest[i][0] == target_kind:
                        items.append([Paragraph(inlines=text_to_inlines(rest[i][1]), is_plain=True)])
                        i += 1
                    blocks.append(BulletList(items=items) if target_kind == 'bullet' else OrderedList(items=items))
                else:
                    blocks.append(Paragraph(inlines=text_to_inlines(text)))
                    i += 1
    return Document(blocks=blocks, source_format='pptx')


class PptxReader(Reader):
    format_name = 'pptx'
    binary = True
    def read(self, source, options=None):
        return _read_pptx(source)

register_reader(PptxReader())


# ----- XLSX ---------------------------------------------------------------

def _write_xlsx(document: Document) -> bytes:
    """XLSX writer.

    Table blocks expand to one ``<row>`` per row (header + body) with one
    ``<c>`` per cell (column ``A`` onward). Non-table blocks fall back to
    one row per block in column ``A``.
    """
    from pandoc_py.ast import Table
    rows_xml: list[str] = []
    row_idx = 0

    def col_letter(n: int) -> str:
        out = ''
        while n >= 0:
            out = chr(ord('A') + n % 26) + out
            n = n // 26 - 1
            if n < 0:
                break
        return out

    def emit_row(values: list[str]) -> None:
        nonlocal row_idx
        row_idx += 1
        cells = ''.join(
            f'<c r="{col_letter(i)}{row_idx}" t="inlineStr"><is><t>{escape(v)}</t></is></c>'
            for i, v in enumerate(values)
        )
        rows_xml.append(f'<row r="{row_idx}">{cells}</row>')

    for block in document.blocks:
        if isinstance(block, Table):
            if block.headers:
                emit_row([inlines_to_plain(cell) for cell in block.headers])
            for row in block.rows:
                emit_row([inlines_to_plain(cell) for cell in row])
        else:
            text = inlines_to_plain(getattr(block, 'inlines', [])) or getattr(block, 'text', '')
            emit_row([text])
    sheet_xml = ('<?xml version="1.0"?>'
                 '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                 '<sheetData>' + ''.join(rows_xml) + '</sheetData></worksheet>')
    workbook_xml = ('<?xml version="1.0"?>'
                    '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                    '<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>')
    members = {
        '[Content_Types].xml': (
            '<?xml version="1.0"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Override PartName="/xl/workbook.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '</Types>'
        ).encode('utf-8'),
        '_rels/.rels': (
            '<?xml version="1.0"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="xl/workbook.xml"/></Relationships>'
        ).encode('utf-8'),
        'xl/_rels/workbook.xml.rels': (
            '<?xml version="1.0"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            'Target="worksheets/sheet1.xml"/></Relationships>'
        ).encode('utf-8'),
        'xl/workbook.xml': workbook_xml.encode('utf-8'),
        'xl/worksheets/sheet1.xml': sheet_xml.encode('utf-8'),
    }
    return _zip_save(members)


def _read_xlsx(source) -> Document:
    data = _coerce_bytes(source)
    blocks = []
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for name in sorted(zf.namelist()):
            if name.startswith('xl/worksheets/') and name.endswith('.xml'):
                xml = zf.read(name).decode('utf-8')
                root = ET.fromstring(xml)
                for row in root.iter():
                    if row.tag.split('}')[-1] == 'row':
                        cells = [(t.text or '') for t in row.iter() if t.tag.split('}')[-1] == 't']
                        text = ' '.join(c for c in cells if c.strip())
                        if text:
                            blocks.append(Paragraph(inlines=text_to_inlines(text)))
    return Document(blocks=blocks, source_format='xlsx')


class XlsxReader(Reader):
    format_name = 'xlsx'
    binary = True
    def read(self, source, options=None):
        return _read_xlsx(source)

class XlsxWriter(Writer):
    format_name = 'xlsx'
    binary = True
    def write(self, document, options=None):
        return _write_xlsx(document)

register_reader(XlsxReader())
register_writer(XlsxWriter())


# ----- EPUB ---------------------------------------------------------------

def _read_epub(source) -> Document:
    """EPUB reader admitting Heading, Paragraph, BulletList, OrderedList,
    and CodeBlock from the chapter XHTML payload(s)."""
    data = _coerce_bytes(source)
    blocks = []
    nav_files = {'nav.xhtml', 'OEBPS/nav.xhtml', 'EPUB/nav.xhtml'}
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for name in sorted(zf.namelist()):
            if not (name.endswith('.xhtml') or name.endswith('.html')):
                continue
            # Skip nav documents — they hold the TOC, not the body content.
            base = name.rsplit('/', 1)[-1]
            if base in {'nav.xhtml', 'toc.xhtml'} or name in nav_files:
                continue
            xml = zf.read(name).decode('utf-8', errors='replace')
            # Strip the namespace and remaining xml declaration so a
            # plain ElementTree.fromstring can parse the body.
            cleaned = re.sub(r'<\?xml[^?]*\?>', '', xml)
            cleaned = re.sub(r'<!DOCTYPE[^>]+>', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'\bxmlns(:[a-z]+)?="[^"]*"', '', cleaned)
            # Strip any remaining prefixed attributes (epub:type, xml:lang).
            cleaned = re.sub(r'\b[a-zA-Z][a-zA-Z0-9]*:[a-zA-Z][a-zA-Z0-9]*="[^"]*"', '', cleaned)
            try:
                root = ET.fromstring(cleaned if '<html' in cleaned else f'<html>{cleaned}</html>')
            except ET.ParseError:
                continue
            for el in root.iter():
                tag = el.tag.lower()
                if re.match(r'^h[1-6]$', tag):
                    text = ''.join(el.itertext()).strip()
                    if text:
                        blocks.append(Heading(level=int(tag[1]), inlines=text_to_inlines(text)))
                elif tag == 'p':
                    text = ''.join(el.itertext()).strip()
                    if text:
                        blocks.append(Paragraph(inlines=text_to_inlines(text)))
                elif tag == 'ul':
                    items = []
                    for li in el:
                        if li.tag.lower() == 'li':
                            items.append([Paragraph(inlines=text_to_inlines(''.join(li.itertext()).strip()), is_plain=True)])
                    if items:
                        blocks.append(BulletList(items=items))
                elif tag == 'ol':
                    items = []
                    for li in el:
                        if li.tag.lower() == 'li':
                            items.append([Paragraph(inlines=text_to_inlines(''.join(li.itertext()).strip()), is_plain=True)])
                    if items:
                        blocks.append(OrderedList(items=items))
                elif tag == 'pre':
                    text = ''.join(el.itertext())
                    if text:
                        blocks.append(CodeBlock(text=text.rstrip('\n')))
    return Document(blocks=blocks, source_format='epub')


def _write_epub(document: Document) -> bytes:
    body_parts: list[str] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            body_parts.append(f'<h{block.level}>{escape(inlines_to_plain(block.inlines))}</h{block.level}>')
        elif isinstance(block, Paragraph):
            body_parts.append(f'<p>{escape(inlines_to_plain(block.inlines))}</p>')
        elif isinstance(block, BulletList):
            body_parts.append('<ul>')
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    body_parts.append(f'<li>{escape(sub)}</li>')
            body_parts.append('</ul>')
        elif isinstance(block, OrderedList):
            body_parts.append('<ol>')
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    body_parts.append(f'<li>{escape(sub)}</li>')
            body_parts.append('</ol>')
        elif isinstance(block, CodeBlock):
            body_parts.append(f'<pre><code>{escape(block.text)}</code></pre>')
    chapter_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter</title></head>'
        '<body>' + ''.join(body_parts) + '</body></html>'
    )
    container = ('<?xml version="1.0" encoding="UTF-8"?>'
                 '<container version="1.0" '
                 'xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
                 '<rootfiles>'
                 '<rootfile full-path="OEBPS/content.opf" '
                 'media-type="application/oebps-package+xml"/>'
                 '</rootfiles></container>')
    package = ('<?xml version="1.0" encoding="UTF-8"?>'
               '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">'
               '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
               '<dc:identifier id="bookid">pandoc-py</dc:identifier>'
               '<dc:title>pandoc-py</dc:title><dc:language>en</dc:language>'
               '<meta property="dcterms:modified">2026-04-30T00:00:00Z</meta>'
               '</metadata>'
               '<manifest><item id="ch1" href="chapter.xhtml" media-type="application/xhtml+xml"/>'
               '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/></manifest>'
               '<spine><itemref idref="ch1"/></spine></package>')
    nav = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<html xmlns="http://www.w3.org/1999/xhtml" '
           'xmlns:epub="http://www.idpf.org/2007/ops"><head><title>Nav</title></head>'
           '<body><nav epub:type="toc"><ol><li><a href="chapter.xhtml">Start</a></li></ol></nav></body></html>')
    return _zip_save({
        'mimetype': b'application/epub+zip',
        'META-INF/container.xml': container.encode('utf-8'),
        'OEBPS/content.opf': package.encode('utf-8'),
        'OEBPS/nav.xhtml': nav.encode('utf-8'),
        'OEBPS/chapter.xhtml': chapter_xml.encode('utf-8'),
    })


class EpubReader(Reader):
    format_name = 'epub'
    binary = True
    def read(self, source, options=None):
        return _read_epub(source)

class EpubWriter(Writer):
    format_name = 'epub'
    aliases = ('epub2', 'epub3')
    binary = True
    def write(self, document, options=None):
        return _write_epub_with_options(document, options)


_EPUB_IMAGE_MIME = {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.webp': 'image/webp',
}


def _write_epub_with_options(document: Document, options) -> bytes:
    """Wrap _write_epub() so that ``--epub-cover-image``,
    ``--epub-metadata``, ``--epub-embed-font`` and ``--epub-subdirectory``
    are honored at the zip level."""
    base = _write_epub(document)
    if options is None:
        return base
    extra = getattr(options, 'extra', None) or {}
    cover = extra.get('epub_cover_image')
    metadata = extra.get('epub_metadata')
    fonts = extra.get('epub_embed_fonts') or ()
    if not any((cover, metadata, fonts)):
        return base
    import io
    import zipfile
    from html import escape as _h_escape
    src_members: dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(base)) as zf:
        for name in zf.namelist():
            src_members[name] = zf.read(name)
    if cover:
        path = Path(cover)
        try:
            data = path.read_bytes()
        except OSError:
            data = None
        if data is not None:
            ext = path.suffix.lower()
            mime = _EPUB_IMAGE_MIME.get(ext, 'application/octet-stream')
            member = f'OEBPS/cover{ext}'
            src_members[member] = data
            src_members['OEBPS/cover.xhtml'] = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<!DOCTYPE html>'
                '<html xmlns="http://www.w3.org/1999/xhtml"><head>'
                '<title>Cover</title></head><body>'
                f'<div style="text-align:center;"><img src="cover{ext}" alt="cover"/></div>'
                '</body></html>'
            ).encode('utf-8')
            # Patch content.opf to register the cover image + page.
            opf_key = next((k for k in src_members if k.endswith('content.opf')), None)
            if opf_key is not None:
                opf = src_members[opf_key].decode('utf-8', errors='replace')
                inject_manifest = (
                    f'<item id="cover-image" href="cover{ext}" '
                    f'media-type="{mime}" properties="cover-image"/>'
                    '<item id="cover" href="cover.xhtml" '
                    'media-type="application/xhtml+xml"/>'
                )
                if '<manifest>' in opf and 'cover-image' not in opf:
                    opf = opf.replace('<manifest>', f'<manifest>{inject_manifest}', 1)
                if '<spine>' in opf and 'idref="cover"' not in opf:
                    opf = opf.replace('<spine>', '<spine><itemref idref="cover"/>', 1)
                src_members[opf_key] = opf.encode('utf-8')
    if metadata:
        try:
            meta_xml = Path(metadata).read_text(encoding='utf-8')
        except OSError:
            meta_xml = ''
        if meta_xml:
            opf_key = next((k for k in src_members if k.endswith('content.opf')), None)
            if opf_key is not None:
                opf = src_members[opf_key].decode('utf-8', errors='replace')
                # Inject extra metadata children into <metadata>.
                if '<metadata' in opf:
                    inject = ''.join(
                        line for line in meta_xml.splitlines()
                        if line.strip().startswith('<')
                    )
                    opf = opf.replace('</metadata>', inject + '</metadata>', 1)
                    src_members[opf_key] = opf.encode('utf-8')
    if fonts:
        for font_path in fonts:
            fp = Path(font_path)
            try:
                fbytes = fp.read_bytes()
            except OSError:
                continue
            src_members[f'OEBPS/fonts/{fp.name}'] = fbytes
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as out:
        for name, data in src_members.items():
            out.writestr(name, data)
    return buf.getvalue()

register_reader(EpubReader())
register_writer(EpubWriter())


# ----- BITS (BITS XML markup, kin to JATS) --------------------------------

class BitsReader(Reader):
    format_name = 'bits'
    def read(self, source, options=None):
        if isinstance(source, bytes): source = source.decode('utf-8')
        from .jats import _read_jats
        doc = _read_jats(source)
        return Document(blocks=doc.blocks, meta=doc.meta, source_format='bits')

register_reader(BitsReader())


# ----- PDF (writer placeholder — degenerates to plain text bytes) ---------

class PdfWriter(Writer):
    format_name = 'pdf'
    binary = True
    def write(self, document, options=None):
        # Real PDF generation requires LaTeX or weasyprint. The constrained
        # slice produces a one-page bytes blob with the document text.
        from .writer_only import _plain
        return _plain(document).encode('utf-8')

register_writer(PdfWriter())
