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
    data = _coerce_bytes(source)
    xml = _zip_load_text(data, 'word/document.xml')
    root = ET.fromstring(xml)
    blocks = []
    for p in root.iter(_DOCX_W + 'p'):
        text_parts = [t.text or '' for t in p.iter(_DOCX_W + 't')]
        text = ''.join(text_parts).strip()
        if not text:
            continue
        style = ''
        for ps in p.iter(_DOCX_W + 'pStyle'):
            style = ps.attrib.get(_DOCX_W + 'val', '')
            break
        m = re.match(r'^Heading(\d)$', style or '')
        if m:
            blocks.append(Heading(level=int(m.group(1)), inlines=text_to_inlines(text)))
        else:
            blocks.append(Paragraph(inlines=text_to_inlines(text)))
    return Document(blocks=blocks, source_format='docx')


def _docx_paragraph(text: str, style: str | None = None) -> str:
    s = ''
    if style:
        s = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>'
    return f'<w:p>{s}<w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'


def _write_docx(document: Document) -> bytes:
    body_parts: list[str] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            body_parts.append(_docx_paragraph(inlines_to_plain(block.inlines), f'Heading{max(1, min(block.level, 6))}'))
        elif isinstance(block, Paragraph):
            body_parts.append(_docx_paragraph(inlines_to_plain(block.inlines)))
        elif isinstance(block, (BulletList, OrderedList)):
            for item in block.items:
                for sub in block_text_paragraphs(item):
                    body_parts.append(_docx_paragraph(('• ' if isinstance(block, BulletList) else '1. ') + sub, 'ListParagraph'))
        elif isinstance(block, CodeBlock):
            for ln in block.text.split('\n'):
                body_parts.append(_docx_paragraph(ln, 'Code'))

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
        '</Types>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/></Relationships>'
    )
    return _zip_save({
        '[Content_Types].xml': content_types.encode('utf-8'),
        '_rels/.rels': rels.encode('utf-8'),
        'word/document.xml': document_xml.encode('utf-8'),
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
    data = _coerce_bytes(source)
    xml = _zip_load_text(data, 'content.xml')
    root = ET.fromstring(xml)
    blocks = []
    for el in root.iter():
        tag = el.tag.split('}')[-1]
        text = ''.join(el.itertext()).strip()
        if not text:
            continue
        if tag == 'h':
            level = int(el.attrib.get('{urn:oasis:names:tc:opendocument:xmlns:text:1.0}outline-level', '1'))
            blocks.append(Heading(level=level, inlines=text_to_inlines(text)))
        elif tag == 'p':
            blocks.append(Paragraph(inlines=text_to_inlines(text)))
    return Document(blocks=blocks, source_format='odt')


def _write_odt(document: Document) -> bytes:
    body: list[str] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            body.append(f'<text:h text:outline-level="{max(1, min(block.level, 6))}">'
                        f'{escape(inlines_to_plain(block.inlines))}</text:h>')
        elif isinstance(block, Paragraph):
            body.append(f'<text:p>{escape(inlines_to_plain(block.inlines))}</text:p>')
    content_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<office:document-content '
        'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
        'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">'
        '<office:body><office:text>' + ''.join(body) + '</office:text></office:body>'
        '</office:document-content>'
    )
    mimetype = 'application/vnd.oasis.opendocument.text'
    manifest = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<manifest:manifest '
        'xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0">'
        '<manifest:file-entry manifest:media-type="application/vnd.oasis.opendocument.text" '
        'manifest:full-path="/"/>'
        '<manifest:file-entry manifest:media-type="text/xml" manifest:full-path="content.xml"/>'
        '</manifest:manifest>'
    )
    return _zip_save({
        'mimetype': mimetype.encode('ascii'),
        'content.xml': content_xml.encode('utf-8'),
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
    data = _coerce_bytes(source)
    blocks = []
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for name in sorted(zf.namelist()):
            if name.startswith('ppt/slides/slide') and name.endswith('.xml'):
                xml = zf.read(name).decode('utf-8')
                root = ET.fromstring(xml)
                texts = [(t.text or '') for t in root.iter() if t.tag.split('}')[-1] == 't']
                texts = [t for t in texts if t.strip()]
                if texts:
                    blocks.append(Heading(level=1, inlines=text_to_inlines(texts[0])))
                    for body in texts[1:]:
                        blocks.append(Paragraph(inlines=text_to_inlines(body)))
    return Document(blocks=blocks, source_format='pptx')


class PptxReader(Reader):
    format_name = 'pptx'
    binary = True
    def read(self, source, options=None):
        return _read_pptx(source)

register_reader(PptxReader())


# ----- XLSX ---------------------------------------------------------------

def _write_xlsx(document: Document) -> bytes:
    # Each Heading / Paragraph becomes a row in Sheet1.
    rows: list[str] = []
    for idx, block in enumerate(document.blocks):
        text = inlines_to_plain(getattr(block, 'inlines', [])) or getattr(block, 'text', '')
        rows.append(f'<row r="{idx + 1}"><c r="A{idx + 1}" t="inlineStr"><is><t>{escape(text)}</t></is></c></row>')
    sheet_xml = ('<?xml version="1.0"?>'
                 '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                 '<sheetData>' + ''.join(rows) + '</sheetData></worksheet>')
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
    data = _coerce_bytes(source)
    blocks = []
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for name in sorted(zf.namelist()):
            if name.endswith('.xhtml') or name.endswith('.html'):
                xml = zf.read(name).decode('utf-8', errors='replace')
                # crude tag stripping
                m = re.findall(r'<(h[1-6])[^>]*>(.*?)</\1>', xml, re.DOTALL | re.IGNORECASE)
                for tag, text in m:
                    blocks.append(Heading(level=int(tag[1]), inlines=text_to_inlines(re.sub(r'<[^>]+>', '', text).strip())))
                m = re.findall(r'<p[^>]*>(.*?)</p>', xml, re.DOTALL | re.IGNORECASE)
                for text in m:
                    plain = re.sub(r'<[^>]+>', '', text).strip()
                    if plain:
                        blocks.append(Paragraph(inlines=text_to_inlines(plain)))
    return Document(blocks=blocks, source_format='epub')


def _write_epub(document: Document) -> bytes:
    body_parts: list[str] = []
    for block in document.blocks:
        if isinstance(block, Heading):
            body_parts.append(f'<h{block.level}>{escape(inlines_to_plain(block.inlines))}</h{block.level}>')
        elif isinstance(block, Paragraph):
            body_parts.append(f'<p>{escape(inlines_to_plain(block.inlines))}</p>')
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
        return _write_epub(document)

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
