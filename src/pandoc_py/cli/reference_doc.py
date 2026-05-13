"""``--reference-doc`` support for docx / odt / pptx output.

When ``--reference-doc <path>`` is supplied, pandoc replaces the styles
and document properties of the generated zip with those from the
reference file. The user's body content (regenerated from the AST)
remains, but inherits the look of the reference.

This module performs the same operation post-hoc: we generate the zip
through the normal writer, then walk the reference zip and copy each
"styling" part into the output, leaving the content parts untouched.

The selection of which parts are styling vs. content uses the same
heuristic pandoc itself uses:

* DOCX  — replace ``word/styles.xml``, ``word/numbering.xml``,
  ``word/theme/theme1.xml``, ``word/settings.xml``, and any
  ``word/header*.xml`` / ``word/footer*.xml``. Keep
  ``word/document.xml`` from the regenerated output.
* ODT   — replace ``styles.xml`` and any media under ``Pictures/``.
  Keep ``content.xml`` from the regenerated output.
* PPTX  — replace ``ppt/slideMasters/*``, ``ppt/slideLayouts/*``,
  ``ppt/theme/*``, ``ppt/presentation.xml`` rels.
  Keep ``ppt/slides/*`` from the regenerated output.

If the reference doc is missing or unreadable a warning is logged and
the original output is returned unchanged.
"""
from __future__ import annotations

import io
import logging
import zipfile
from pathlib import Path

_LOG = logging.getLogger('pandoc_py')


_DOCX_STYLE_PARTS = {
    'word/styles.xml',
    'word/numbering.xml',
    'word/settings.xml',
    'word/fontTable.xml',
    'word/webSettings.xml',
    'word/theme/theme1.xml',
}


_ODT_STYLE_PARTS = {
    'styles.xml',
    'meta.xml',
    'settings.xml',
}


_PPTX_STYLE_PREFIXES = (
    'ppt/slideMasters/',
    'ppt/slideLayouts/',
    'ppt/theme/',
    'ppt/notesSlides/',
)


def apply_reference_doc(output_bytes: bytes, reference_path: str, format_name: str) -> bytes:
    """Return a new zip with the styling parts of `reference_path` swapped in.

    `output_bytes` is the bytes of the writer-produced zip; `format_name`
    selects which parts are considered "styling".
    """
    try:
        ref_data = Path(reference_path).read_bytes()
    except OSError as exc:
        _LOG.warning('Could not read --reference-doc %s: %s', reference_path, exc)
        return output_bytes

    try:
        ref_members = _load_members(ref_data)
    except zipfile.BadZipFile:
        _LOG.warning('--reference-doc %s is not a valid zip; ignoring.', reference_path)
        return output_bytes

    if format_name == 'docx':
        return _merge_zip(output_bytes, ref_members, lambda name: name in _DOCX_STYLE_PARTS
                          or name.startswith('word/header')
                          or name.startswith('word/footer')
                          or name.startswith('word/_rels/header')
                          or name.startswith('word/_rels/footer'))
    if format_name == 'odt':
        return _merge_zip(output_bytes, ref_members, lambda name: name in _ODT_STYLE_PARTS
                          or name.startswith('Pictures/'))
    if format_name == 'pptx':
        return _merge_zip(output_bytes, ref_members, lambda name: name.startswith(_PPTX_STYLE_PREFIXES))
    # Other formats — return output unchanged.
    _LOG.warning('--reference-doc not supported for format %s; ignoring.', format_name)
    return output_bytes


def _load_members(data: bytes) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for name in zf.namelist():
            out[name] = zf.read(name)
    return out


def _merge_zip(output_bytes: bytes, ref_members: dict[str, bytes], should_replace) -> bytes:
    out_members = _load_members(output_bytes)
    # Replace styling parts from reference.
    for name, content in ref_members.items():
        if should_replace(name):
            out_members[name] = content
    # Add styling parts that exist in reference but not in output (e.g.
    # header/footer files our writer doesn't emit by default).
    for name, content in ref_members.items():
        if should_replace(name) and name not in out_members:
            out_members[name] = content
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, content in out_members.items():
            zf.writestr(name, content)
    return buf.getvalue()
