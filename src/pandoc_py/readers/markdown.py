from __future__ import annotations

import re

from pandoc_py.ast import (
    Attr,
    BlockQuote,
    BulletList,
    Citation,
    Cite,
    Code,
    CodeBlock,
    DefinitionList,
    Div,
    Document,
    Emph,
    Figure,
    HardBreak,
    Heading,
    Image,
    Link,
    Math,
    Note,
    OrderedList,
    Paragraph,
    Span,
    RawBlock,
    RawInline,
    SoftBreak,
    Space,
    Str,
    Strikeout,
    Strong,
    Subscript,
    Superscript,
    Table,
    ThematicBreak,
)

from pandoc_py.parsing.common import (
    attr_is_empty as _attr_is_empty,
    citation_suffix_inlines as _citation_suffix_inlines,
    normalize_newlines as _normalize_newlines,
    normalize_reference_label as _normalize_reference_label,
    parse_attr_string as _parse_attr_string,
    parse_plain_segment as _parse_plain_segment,
    split_trailing_attr as _split_trailing_attr,
)
from pandoc_py.readers.metadata import MetadataReaderError, split_yaml_front_matter

UNSUPPORTED_INLINE_PATTERNS = (
    r'_',
)
UNSUPPORTED_LINE_START = re.compile(r'^\s{0,3}([+*]\s|~~~)')
ATX_HEADING = re.compile(r'^\s{0,3}(#{1,6})[ \t]+(.*?)(?:[ \t]+#+[ \t]*)?$')
SETEXT_LEVEL_1 = re.compile(r'^\s{0,3}=+[ \t]*$')
SETEXT_LEVEL_2 = re.compile(r'^\s{0,3}-+[ \t]*$')
SIMPLE_BULLET_ITEM = re.compile(r'^\s{0,3}-[ \t]+(.*)$')
SIMPLE_ORDERED_ITEM = re.compile(r'^\s{0,3}([1-9][0-9]*)\.[ \t]+(.*)$')
TASK_MARKER = re.compile(r'^\[( |x|X)\](?:[ \t]+(.*))?$')
SIMPLE_BLOCK_QUOTE_LINE = re.compile(r'^\s{0,3}>[ \t]?(.*)$')
THEMATIC_BREAK = re.compile(r'^\s{0,3}-{3,}\s*$')
FENCE_OPEN = re.compile(r'^\s{0,3}```[ \t]*(.*?)?[ \t]*$')
FENCE_CLOSE = re.compile(r'^\s{0,3}```[ \t]*$')
RAW_FORMAT_FENCE_OPEN = re.compile(r'^\s{0,3}```\{=(html|tex|latex)\}[ \t]*$')
DIV_OPEN = re.compile(r'^\s{0,3}:::[ \t]*(\{[^}]*\})?[ \t]*$')
DIV_CLOSE = re.compile(r'^\s{0,3}:::[ \t]*$')
INDENTED_CODE_LINE = re.compile(r'^ {4}(.*)$')
REFERENCE_DEF_LINE = re.compile(r'^\s{0,3}\[([^\]]+)\]:[ \t]+(.*)$')
FOOTNOTE_DEF_LINE = re.compile(r'^\s{0,3}\[\^([^\]]+)\]:[ \t]+(.*)$')
DEFINITION_ITEM_LINE = re.compile(r'^\s{0,3}:[ \t]+(.*)$')
TABLE_CAPTION_LINE = re.compile(r'^\s{0,3}:[ \t]+(.*)$')
LINK_TARGET_PATTERN = re.compile(r'^[^\s()<>]+$')
AUTOLINK_TARGET_PATTERN = re.compile(r'^(?:https?|ftp)://[^\s<>]+$')
EMAIL_AUTOLINK_PATTERN = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$")
CITATION_ID_PATTERN = r'[A-Za-z0-9][A-Za-z0-9_:.#$%&+?<>~/\-]*'
BRACKETED_CITATION_SEGMENT = re.compile(rf'^(?P<prefix>.*?)(?P<marker>-?@)(?P<id>{CITATION_ID_PATTERN})(?P<suffix>.*)$')
AUTHOR_IN_TEXT_CITATION = re.compile(rf'@(?P<id>{CITATION_ID_PATTERN})')
RAW_HTML_BLOCK_TAG_OPEN = re.compile(r'^\s{0,3}<(script|style|pre)\b[^>]*>\s*$', re.IGNORECASE)
RAW_HTML_HR_BLOCK = re.compile(r'^\s{0,3}<hr\b[^>]*>\s*$', re.IGNORECASE)
RAW_TEX_ENV_OPEN = re.compile(r'^\s{0,3}\\begin\{([A-Za-z*@]+)\}\s*$')
RAW_TEX_COMMAND_BLOCK = re.compile(r'^\s{0,3}\\[A-Za-z@]+[*]?(?:\[[^\]\n]*\])*(?:\{[^{}\n]*\})*\s*$')
RAW_HTML_COMMENT_START = re.compile(r'^\s{0,3}<!--')
RAW_HTML_COMMENT_END = re.compile(r'-->\s*$')
RAW_HTML_INLINE_TAG = re.compile(r'</?[A-Za-z][A-Za-z0-9:-]*(?:\s+[^<>\n]*?)?\s*/?>')
UNSUPPORTED_INLINE = re.compile('|'.join(UNSUPPORTED_INLINE_PATTERNS))
BLOCK_HTML_TAGS = {
    'address', 'article', 'aside', 'blockquote', 'body', 'canvas', 'dd', 'details', 'div', 'dl', 'dt',
    'fieldset', 'figcaption', 'figure', 'footer', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header',
    'hr', 'html', 'iframe', 'li', 'main', 'nav', 'ol', 'p', 'pre', 'script', 'section', 'style', 'table',
    'tbody', 'td', 'textarea', 'tfoot', 'th', 'thead', 'tr', 'ul',
}


class MarkdownScopeError(ValueError):
    """Raised when the input falls outside the current markdown slice."""


InlineNode = Str | Space | SoftBreak | HardBreak | Emph | Strong | Strikeout | Subscript | Superscript | Math | Code | Span | Link | Image | RawInline | Note | Cite
ReferenceDef = tuple[str, str]
FootnoteDef = list[Paragraph]
TableCaption = list[InlineNode]


ESCAPABLE_PUNCTUATION = set("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")


def _parse_backslash_escape(text: str, index: int) -> tuple[Str | None, int]:
    if index + 1 >= len(text):
        return None, index
    escaped = text[index + 1]
    if escaped in ESCAPABLE_PUNCTUATION:
        return Str(escaped), index + 2
    return None, index


def _split_blocks(text: str) -> list[list[str]]:
    lines = _normalize_newlines(text).split('\n')
    blocks: list[list[str]] = []
    current: list[str] = []
    i = 0
    while i < len(lines):
        raw_line = lines[i]
        if raw_line.strip() == '':
            if current:
                blocks.append(current)
                current = []
            i += 1
            continue
        if FENCE_OPEN.match(raw_line):
            if current:
                blocks.append(current)
                current = []
            fenced = [raw_line]
            i += 1
            while i < len(lines):
                fenced.append(lines[i])
                if FENCE_CLOSE.match(lines[i]):
                    break
                i += 1
            else:
                raise MarkdownScopeError('Unclosed fenced code block is outside the current reader scope.')
            blocks.append(fenced)
            i += 1
            continue
        if RAW_FORMAT_FENCE_OPEN.match(raw_line):
            if current:
                blocks.append(current)
                current = []
            fenced = [raw_line]
            i += 1
            while i < len(lines):
                fenced.append(lines[i])
                if FENCE_CLOSE.match(lines[i]):
                    break
                i += 1
            else:
                raise MarkdownScopeError('Unclosed raw format fence is outside the current reader scope.')
            blocks.append(fenced)
            i += 1
            continue
        if DIV_OPEN.match(raw_line):
            if current:
                blocks.append(current)
                current = []
            div_lines = [raw_line]
            i += 1
            while i < len(lines):
                div_lines.append(lines[i])
                if DIV_CLOSE.match(lines[i]):
                    break
                i += 1
            else:
                raise MarkdownScopeError('Unclosed fenced div is outside the current reader scope.')
            blocks.append(div_lines)
            i += 1
            continue
        raw_block_open = RAW_HTML_BLOCK_TAG_OPEN.match(raw_line)
        if raw_block_open:
            if current:
                blocks.append(current)
                current = []
            tag = raw_block_open.group(1)
            block = [raw_line]
            i += 1
            close_re = re.compile(rf'^\s{{0,3}}</{tag}>\s*$', re.IGNORECASE)
            while i < len(lines):
                block.append(lines[i])
                if close_re.match(lines[i]):
                    break
                i += 1
            else:
                raise MarkdownScopeError('Unclosed raw html block is outside the current reader scope.')
            blocks.append(block)
            i += 1
            continue
        if RAW_HTML_COMMENT_START.match(raw_line):
            if current:
                blocks.append(current)
                current = []
            comment = [raw_line]
            i += 1
            if not RAW_HTML_COMMENT_END.search(raw_line):
                while i < len(lines):
                    comment.append(lines[i])
                    if RAW_HTML_COMMENT_END.search(lines[i]):
                        break
                    i += 1
                else:
                    raise MarkdownScopeError('Unclosed raw html comment block is outside the current reader scope.')
                i += 1
            blocks.append(comment)
            continue
        current.append(raw_line)
        i += 1
    if current:
        blocks.append(current)
    return blocks


def _reject_tabs(lines: list[str]) -> None:
    for line in lines:
        if '\t' in line:
            raise MarkdownScopeError('Tabs are outside the current minimal markdown scope.')


def _reject_unsupported_line_start(line: str) -> None:
    if UNSUPPORTED_LINE_START.search(line):
        raise MarkdownScopeError('Unsupported markdown block syntax for current reader scope.')


def _reject_unsupported_inline(text: str) -> None:
    if UNSUPPORTED_INLINE.search(text):
        raise MarkdownScopeError('Unsupported markdown inline syntax for current reader scope.')


def _parse_citation_segments(raw: str, *, default_mode: str) -> list[Citation] | None:
    segments = [segment.strip() for segment in raw.split(';')]
    if any(not segment for segment in segments):
        return None
    citations: list[Citation] = []
    for idx, segment in enumerate(segments):
        match = BRACKETED_CITATION_SEGMENT.fullmatch(segment)
        if match is None:
            return None
        prefix_text = match.group('prefix').rstrip()
        marker = match.group('marker')
        citation_id = match.group('id')
        suffix_text = match.group('suffix').strip()
        if idx > 0 and prefix_text:
            return None
        mode = 'SuppressAuthor' if marker == '-@' else default_mode
        citations.append(
            Citation(
                citation_id=citation_id,
                prefix=_parse_plain_segment(prefix_text) if prefix_text else [],
                suffix=_citation_suffix_inlines(suffix_text) if suffix_text else [],
                mode=mode,
            )
        )
    return citations


def _parse_bracketed_citation(text: str, index: int) -> tuple[Cite | None, int]:
    end = text.find(']', index + 1)
    if end == -1:
        return None, index
    if end + 1 < len(text) and text[end + 1] in '([':
        return None, index
    raw = text[index:end + 1]
    content = text[index + 1:end]
    if '@' not in content:
        return None, index
    citations = _parse_citation_segments(content, default_mode='NormalCitation')
    if citations is None:
        return None, index
    return Cite(citations=citations, inlines=_parse_plain_segment(raw)), end + 1


def _parse_author_in_text_citation(text: str, index: int) -> tuple[Cite | None, int]:
    if index > 0 and re.match(r'[A-Za-z0-9_]', text[index - 1]):
        return None, index
    match = AUTHOR_IN_TEXT_CITATION.match(text, index)
    if match is None:
        return None, index
    citation_id = match.group('id')
    end = match.end()
    raw = text[index:end]
    suffix: list[Str | Space] = []
    if text.startswith(' [', end):
        suffix_end = text.find(']', end + 2)
        if suffix_end == -1:
            raise MarkdownScopeError('Unclosed author-in-text citation suffix is outside the current reader scope.')
        suffix_text = text[end + 2:suffix_end].strip()
        raw = text[index:suffix_end + 1]
        end = suffix_end + 1
        suffix = _citation_suffix_inlines(suffix_text) if suffix_text else []
    citation = Citation(citation_id=citation_id, suffix=suffix, mode='AuthorInText')
    return Cite(citations=[citation], inlines=_parse_plain_segment(raw)), end


def _validate_plain_label(label: str, *, kind: str) -> None:
    if kind == 'link':
        if not label or label != label.strip():
            raise MarkdownScopeError('Empty or edge-spaced link labels are outside the current reader scope.')
        if any(ch in label for ch in '[]()*`<>~^$'):
            raise MarkdownScopeError('Nested inline syntax inside link labels is outside the current reader scope.')
    else:
        if label != label.strip():
            raise MarkdownScopeError('Edge-spaced image labels are outside the current reader scope.')
        if any(ch in label for ch in '[]()*`<>!~^$'):
            raise MarkdownScopeError('Nested inline syntax inside image labels is outside the current reader scope.')
    _reject_unsupported_inline(label)


def _parse_target_and_title(raw: str, *, kind: str) -> tuple[str, str]:
    raw = raw.strip()
    if not raw:
        raise MarkdownScopeError(f'Empty {kind} targets are outside the current reader scope.')
    title = ''
    match = re.fullmatch(r'([^\s()<>]+)[ \t]+"([^"]*)"', raw)
    if match:
        target, title = match.group(1), match.group(2)
    else:
        target = raw
    if not LINK_TARGET_PATTERN.fullmatch(target):
        raise MarkdownScopeError(f'Complex {kind} targets are outside the current reader scope.')
    return target, title


def _parse_brace_attr(text: str, index: int) -> tuple[Attr | None, int]:
    if index >= len(text) or text[index] != '{':
        return None, index
    end = text.find('}', index + 1)
    if end == -1:
        raise MarkdownScopeError('Unclosed attribute list is outside the current reader scope.')
    return _parse_attr_string(text[index:end + 1]), end + 1


def _parse_reference_definitions(blocks: list[list[str]]) -> tuple[dict[str, ReferenceDef], dict[str, list[str]], list[list[str]]]:
    definitions: dict[str, ReferenceDef] = {}
    footnotes_raw: dict[str, list[str]] = {}
    retained: list[list[str]] = []
    for lines in blocks:
        footnote_match = FOOTNOTE_DEF_LINE.match(lines[0]) if lines else None
        if footnote_match:
            label = footnote_match.group(1)
            content_lines = [footnote_match.group(2)]
            valid = True
            for line in lines[1:]:
                indented = INDENTED_CODE_LINE.match(line)
                if not indented:
                    valid = False
                    break
                content_lines.append(indented.group(1))
            if valid:
                footnotes_raw[_normalize_reference_label(label)] = content_lines
                continue

        parsed_block: list[tuple[str, str, str]] = []
        for line in lines:
            match = REFERENCE_DEF_LINE.match(line)
            if not match:
                parsed_block = []
                break
            label = match.group(1)
            raw_target = match.group(2)
            target, title = _parse_target_and_title(raw_target, kind='reference definition')
            parsed_block.append((label, target, title))
        if parsed_block and len(parsed_block) == len(lines):
            for label, target, title in parsed_block:
                definitions[_normalize_reference_label(label)] = (target, title)
            continue

        retained.append(lines)
    return definitions, footnotes_raw, retained


def _materialize_footnotes(footnotes_raw: dict[str, list[str]], definitions: dict[str, ReferenceDef]) -> dict[str, FootnoteDef]:
    return {
        label: [Paragraph(inlines=_parse_multiline_inlines(lines, definitions, {}))]
        for label, lines in footnotes_raw.items()
    }


def _parse_simple_delimited(text: str, index: int, delimiter: str, *, kind: str) -> tuple[str, int]:
    start = index + len(delimiter)
    end = text.find(delimiter, start)
    if end == -1:
        raise MarkdownScopeError(f'Unclosed {kind} delimiter is outside the current reader scope.')
    content = text[start:end]
    if not content or content != content.strip():
        raise MarkdownScopeError(f'Delimited {kind} with empty or edge-spaced content is outside the current reader scope.')
    if delimiter in content:
        raise MarkdownScopeError(f'Nested or repeated {kind} delimiters are outside the current reader scope.')
    if any(ch in content for ch in '[]()`<>!~^$'):
        raise MarkdownScopeError(f'Nested inline syntax inside {kind} is outside the current reader scope.')
    _reject_unsupported_inline(content)
    return content, end + len(delimiter)


def _parse_code_span(text: str, index: int) -> tuple[str, int]:
    if text.startswith('``', index):
        raise MarkdownScopeError('Multi-backtick code spans are outside the current reader scope.')
    end = text.find('`', index + 1)
    if end == -1:
        raise MarkdownScopeError('Unclosed code span delimiter is outside the current reader scope.')
    content = text[index + 1:end]
    if not content:
        raise MarkdownScopeError('Empty code spans are outside the current reader scope.')
    if content != content.strip():
        raise MarkdownScopeError('Edge-spaced code spans are outside the current reader scope.')
    if '\n' in content or '\r' in content:
        raise MarkdownScopeError('Multiline code spans are outside the current reader scope.')
    return content, end + 1


def _parse_math(text: str, index: int) -> tuple[Math, int]:
    if text.startswith('$$', index):
        delimiter = '$$'
        display = True
    else:
        delimiter = '$'
        display = False
    start = index + len(delimiter)
    end = text.find(delimiter, start)
    if end == -1:
        raise MarkdownScopeError('Unclosed math delimiter is outside the current reader scope.')
    content = text[start:end]
    if not content:
        raise MarkdownScopeError('Empty math spans are outside the current reader scope.')
    if not display and ('\n' in content or '\r' in content):
        raise MarkdownScopeError('Multiline inline math is outside the current reader scope.')
    if content != content.strip():
        raise MarkdownScopeError('Edge-spaced inline/display math is outside the current reader scope.')
    return Math(text=content, display=display), end + len(delimiter)


def _parse_raw_inline_attribute(text: str, index: int) -> tuple[RawInline | None, int]:
    end = text.find('`', index + 1)
    if end == -1:
        return None, index
    fmt_match = re.match(r'\{=(html|tex|latex)\}', text[end + 1:])
    if not fmt_match:
        return None, index
    content = text[index + 1:end]
    if not content or '\n' in content or '\r' in content:
        raise MarkdownScopeError('Only single-line raw inline attribute spans are supported in the current reader scope.')
    fmt = fmt_match.group(1)
    return RawInline(format=fmt, text=content), end + 1 + len(fmt_match.group(0))


def _parse_raw_tex_inline(text: str, index: int) -> tuple[RawInline | None, int]:
    if index + 1 >= len(text) or text[index + 1].isspace():
        return None, index
    if text[index + 1].isalpha() or text[index + 1] == '@':
        j = index + 2
        while j < len(text) and (text[j].isalpha() or text[j] == '@'):
            j += 1
        if j < len(text) and text[j] == '*':
            j += 1
    else:
        if text[index + 1] in '{}[]()<>':
            return None, index
        j = index + 2
    while j < len(text):
        if text[j] == '[':
            end = text.find(']', j + 1)
            if end == -1:
                raise MarkdownScopeError('Unclosed raw tex optional argument is outside the current reader scope.')
            j = end + 1
            continue
        if text[j] == '{':
            depth = 1
            k = j + 1
            while k < len(text) and depth > 0:
                if text[k] == '{':
                    depth += 1
                elif text[k] == '}':
                    depth -= 1
                k += 1
            if depth != 0:
                raise MarkdownScopeError('Unclosed raw tex braced argument is outside the current reader scope.')
            j = k
            continue
        break
    return RawInline(format='tex', text=text[index:j]), j

def _parse_raw_html_comment_inline(text: str, index: int) -> tuple[RawInline, int]:
    end = text.find('-->', index + 4)
    if end == -1:
        raise MarkdownScopeError('Unclosed raw html comment is outside the current reader scope.')
    content = text[index:end + 3]
    if '\n' in content or '\r' in content:
        raise MarkdownScopeError('Multiline raw html comments are outside the current inline reader scope.')
    return RawInline(format='html', text=content), end + 3


def _parse_raw_html_tag_inline(text: str, index: int) -> tuple[RawInline | None, int]:
    match = RAW_HTML_INLINE_TAG.match(text[index:])
    if not match:
        return None, index
    content = match.group(0)
    inner = content[2:] if content.startswith('</') else content[1:]
    tag_name = re.split(r'[\s>/]', inner, maxsplit=1)[0].lower()
    if tag_name in BLOCK_HTML_TAGS:
        raise MarkdownScopeError('Block-level raw html tags are outside the current inline reader scope.')
    return RawInline(format='html', text=content), index + len(content)


def _reference_lookup(raw_label: str, definitions: dict[str, ReferenceDef]) -> ReferenceDef:
    key = _normalize_reference_label(raw_label)
    if key not in definitions:
        raise MarkdownScopeError('Undefined reference label is outside the current reader scope.')
    return definitions[key]


def _parse_link(text: str, index: int, definitions: dict[str, ReferenceDef]) -> tuple[Link, int]:
    label_end = text.find(']', index + 1)
    if label_end == -1:
        raise MarkdownScopeError('Unclosed link label is outside the current reader scope.')
    label = text[index + 1:label_end]
    _validate_plain_label(label, kind='link')
    next_index = label_end + 1
    if next_index < len(text) and text[next_index] == '(':
        target_end = text.find(')', next_index + 1)
        if target_end == -1:
            raise MarkdownScopeError('Unclosed link target is outside the current reader scope.')
        target, title = _parse_target_and_title(text[next_index + 1:target_end], kind='link')
        attr, after_attr = _parse_brace_attr(text, target_end + 1)
        return Link(inlines=_parse_plain_segment(label), target=target, title=title, attr=attr or Attr()), after_attr
    if next_index < len(text) and text[next_index] == '[':
        ref_end = text.find(']', next_index + 1)
        if ref_end == -1:
            raise MarkdownScopeError('Unclosed reference label is outside the current reader scope.')
        raw_ref = text[next_index + 1:ref_end]
        target, title = _reference_lookup(label if raw_ref == '' else raw_ref, definitions)
        attr, after_attr = _parse_brace_attr(text, ref_end + 1)
        return Link(inlines=_parse_plain_segment(label), target=target, title=title, attr=attr or Attr()), after_attr
    target, title = _reference_lookup(label, definitions)
    attr, after_attr = _parse_brace_attr(text, next_index)
    return Link(inlines=_parse_plain_segment(label), target=target, title=title, attr=attr or Attr()), after_attr

def _parse_image(text: str, index: int, definitions: dict[str, ReferenceDef]) -> tuple[Image, int]:
    if index + 1 >= len(text) or text[index + 1] != '[':
        raise MarkdownScopeError('Unsupported markdown image syntax for current reader scope.')
    label_end = text.find(']', index + 2)
    if label_end == -1:
        raise MarkdownScopeError('Unclosed image label is outside the current reader scope.')
    label = text[index + 2:label_end]
    _validate_plain_label(label, kind='image')
    next_index = label_end + 1
    if next_index < len(text) and text[next_index] == '(':
        target_end = text.find(')', next_index + 1)
        if target_end == -1:
            raise MarkdownScopeError('Unclosed image target is outside the current reader scope.')
        target, title = _parse_target_and_title(text[next_index + 1:target_end], kind='image')
        attr, after_attr = _parse_brace_attr(text, target_end + 1)
        return Image(inlines=_parse_plain_segment(label), target=target, title=title, attr=attr or Attr()), after_attr
    if next_index < len(text) and text[next_index] == '[':
        ref_end = text.find(']', next_index + 1)
        if ref_end == -1:
            raise MarkdownScopeError('Unclosed image reference label is outside the current reader scope.')
        raw_ref = text[next_index + 1:ref_end]
        target, title = _reference_lookup(label if raw_ref == '' else raw_ref, definitions)
        attr, after_attr = _parse_brace_attr(text, ref_end + 1)
        return Image(inlines=_parse_plain_segment(label), target=target, title=title, attr=attr or Attr()), after_attr
    target, title = _reference_lookup(label, definitions)
    attr, after_attr = _parse_brace_attr(text, next_index)
    return Image(inlines=_parse_plain_segment(label), target=target, title=title, attr=attr or Attr()), after_attr


def _footnote_lookup(raw_label: str, footnotes: dict[str, FootnoteDef]) -> FootnoteDef:
    key = _normalize_reference_label(raw_label)
    if key not in footnotes:
        raise MarkdownScopeError('Undefined footnote label is outside the current reader scope.')
    return footnotes[key]


def _parse_footnote_reference(text: str, index: int, footnotes: dict[str, FootnoteDef]) -> tuple[Note, int]:
    end = text.find(']', index + 2)
    if end == -1:
        raise MarkdownScopeError('Unclosed footnote reference is outside the current reader scope.')
    label = text[index + 2:end]
    if not label.strip():
        raise MarkdownScopeError('Empty footnote references are outside the current reader scope.')
    return Note(blocks=list(_footnote_lookup(label, footnotes))), end + 1


def _parse_inline_note(text: str, index: int, definitions: dict[str, ReferenceDef], footnotes: dict[str, FootnoteDef]) -> tuple[Note, int]:
    end = text.find(']', index + 2)
    if end == -1:
        raise MarkdownScopeError('Unclosed inline note is outside the current reader scope.')
    content = text[index + 2:end]
    if not content or content != content.strip():
        raise MarkdownScopeError('Empty or edge-spaced inline notes are outside the current reader scope.')
    if '^[`' in content:
        raise MarkdownScopeError('Nested inline notes are outside the current reader scope.')
    return Note(blocks=[Paragraph(inlines=_parse_inline_text(content, definitions, footnotes))]), end + 1

def _parse_span(text: str, index: int) -> tuple[Span, int] | tuple[None, int]:
    label_end = text.find(']', index + 1)
    if label_end == -1 or label_end + 1 >= len(text) or text[label_end + 1] != '{':
        return None, index
    label = text[index + 1:label_end]
    if not label or label != label.strip():
        raise MarkdownScopeError('Empty or edge-spaced bracketed spans are outside the current reader scope.')
    if any(ch in label for ch in '![]()`<>~^$'):
        raise MarkdownScopeError('Nested inline syntax inside bracketed spans is outside the current reader scope.')
    _reject_unsupported_inline(label)
    attr, next_index = _parse_brace_attr(text, label_end + 1)
    if attr is None:
        return None, index
    return Span(inlines=_parse_plain_segment(label), attr=attr), next_index

def _parse_autolink(text: str, index: int) -> tuple[Link, int]:
    end = text.find('>', index + 1)
    if end == -1:
        raise MarkdownScopeError('Unclosed autolink is outside the current reader scope.')
    target = text[index + 1:end]
    if AUTOLINK_TARGET_PATTERN.fullmatch(target):
        return Link(inlines=[Str(target)], target=target, autolink=True), end + 1
    if EMAIL_AUTOLINK_PATTERN.fullmatch(target):
        return Link(inlines=[Str(target)], target=f'mailto:{target}', autolink=True), end + 1
    raise MarkdownScopeError('Only simple URI and email autolinks are supported in the current reader scope.')


def _parse_inline_text(text: str, definitions: dict[str, ReferenceDef], footnotes: dict[str, FootnoteDef]) -> list[InlineNode]:
    _reject_unsupported_inline(text)
    parsed: list[InlineNode] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == ' ':
            while i < n and text[i] == ' ':
                i += 1
            parsed.append(Space())
            continue
        if text.startswith('![', i):
            image, i = _parse_image(text, i, definitions)
            parsed.append(image)
            continue
        if text.startswith('[^', i):
            note, i = _parse_footnote_reference(text, i, footnotes)
            parsed.append(note)
            continue
        if text[i] == '[':
            cite, next_i = _parse_bracketed_citation(text, i)
            if cite is not None:
                parsed.append(cite)
                i = next_i
                continue
            span, next_i = _parse_span(text, i)
            if span is not None:
                parsed.append(span)
                i = next_i
                continue
            link, i = _parse_link(text, i, definitions)
            parsed.append(link)
            continue
        if text[i] == '@':
            cite, next_i = _parse_author_in_text_citation(text, i)
            if cite is not None:
                parsed.append(cite)
                i = next_i
                continue
        if text.startswith('<!--', i):
            raw_inline, i = _parse_raw_html_comment_inline(text, i)
            parsed.append(raw_inline)
            continue
        if text[i] == '<':
            raw_inline, next_i = _parse_raw_html_tag_inline(text, i)
            if raw_inline is not None:
                parsed.append(raw_inline)
                i = next_i
                continue
            link, i = _parse_autolink(text, i)
            parsed.append(link)
            continue
        if text[i] == '>':
            raise MarkdownScopeError('Raw > characters are outside the current reader scope.')
        if text[i] == '`':
            raw_inline, next_i = _parse_raw_inline_attribute(text, i)
            if raw_inline is not None:
                parsed.append(raw_inline)
                i = next_i
                continue
            content, i = _parse_code_span(text, i)
            parsed.append(Code(content))
            continue
        if text[i] == '\\':
            escaped, next_i = _parse_backslash_escape(text, i)
            if escaped is not None:
                parsed.append(escaped)
                i = next_i
                continue
            raw_tex, next_i = _parse_raw_tex_inline(text, i)
            if raw_tex is not None:
                parsed.append(raw_tex)
                i = next_i
                continue
        if text.startswith('$$', i) or text[i] == '$':
            math, i = _parse_math(text, i)
            parsed.append(math)
            continue
        if text.startswith('~~', i):
            content, i = _parse_simple_delimited(text, i, '~~', kind='strikeout')
            parsed.append(Strikeout(inlines=_parse_plain_segment(content)))
            continue
        if text.startswith('***', i):
            raise MarkdownScopeError('Triple-star emphasis is outside the current reader scope.')
        if text.startswith('**', i):
            content, i = _parse_simple_delimited(text, i, '**', kind='strong emphasis')
            parsed.append(Strong(inlines=_parse_plain_segment(content)))
            continue
        if text[i] == '*':
            content, i = _parse_simple_delimited(text, i, '*', kind='emphasis')
            parsed.append(Emph(inlines=_parse_plain_segment(content)))
            continue
        if text[i] == '~':
            content, i = _parse_simple_delimited(text, i, '~', kind='subscript')
            parsed.append(Subscript(inlines=_parse_plain_segment(content)))
            continue
        if text.startswith('^[', i):
            note, i = _parse_inline_note(text, i, definitions, footnotes)
            parsed.append(note)
            continue
        if text[i] == '^':
            content, i = _parse_simple_delimited(text, i, '^', kind='superscript')
            parsed.append(Superscript(inlines=_parse_plain_segment(content)))
            continue
        j = i
        while j < n and text[j] not in ' !*`[@<>~^$\\':
            j += 1
        if j == i:
            raise MarkdownScopeError('Unsupported markdown inline syntax for current reader scope.')
        parsed.append(Str(text[i:j]))
        i = j
    return _coalesce_inlines(parsed)


def _coalesce_inlines(inlines: list[InlineNode]) -> list[InlineNode]:
    merged: list[InlineNode] = []
    for inline in inlines:
        if isinstance(inline, Str) and merged and isinstance(merged[-1], Str):
            merged[-1] = Str(merged[-1].text + inline.text)
            continue
        merged.append(inline)
    return merged


def _strip_hardbreak_marker(line: str) -> tuple[str, bool]:
    if line.endswith('\\') and not line.endswith('\\\\'):
        return line[:-1], True
    match = re.search(r' {2,}$', line)
    if match:
        return line[:match.start()], True
    return line, False


def _parse_multiline_inlines(lines: list[str], definitions: dict[str, ReferenceDef], footnotes: dict[str, FootnoteDef]) -> list[InlineNode]:
    parsed: list[InlineNode] = []
    for idx, line in enumerate(lines):
        content = line
        hard_break = False
        if idx < len(lines) - 1:
            content, hard_break = _strip_hardbreak_marker(line)
        parsed.extend(_parse_inline_text(content.strip(), definitions, footnotes))
        if idx < len(lines) - 1:
            parsed.append(HardBreak() if hard_break else SoftBreak())
    return _coalesce_inlines(parsed)


def _display_math_block_from_lines(lines: list[str]) -> Paragraph | None:
    if len(lines) < 2:
        return None
    if lines[0].strip() != '$$' or lines[-1].strip() != '$$':
        return None
    body_lines = lines[1:-1]
    return Paragraph(inlines=[Math(text='\n' + '\n'.join(body_lines) + '\n', display=True)])


def _heading_from_lines(lines: list[str], definitions: dict[str, ReferenceDef], footnotes: dict[str, FootnoteDef]) -> Heading | None:
    if len(lines) != 1:
        return None
    match = ATX_HEADING.match(lines[0])
    if not match:
        return None
    level = len(match.group(1))
    body, attr = _split_trailing_attr(match.group(2))
    if not body:
        raise MarkdownScopeError('Empty ATX headings are outside the current reader scope.')
    return Heading(level=level, inlines=_parse_inline_text(body, definitions, footnotes), attr=attr)


def _setext_heading_from_lines(lines: list[str], definitions: dict[str, ReferenceDef], footnotes: dict[str, FootnoteDef]) -> Heading | None:
    if len(lines) != 2:
        return None
    body, attr = _split_trailing_attr(lines[0])
    underline = lines[1]
    if not body:
        raise MarkdownScopeError('Empty Setext headings are outside the current reader scope.')
    if ATX_HEADING.match(lines[0]):
        return None
    if SETEXT_LEVEL_1.match(underline):
        return Heading(level=1, inlines=_parse_inline_text(body, definitions, footnotes), attr=attr)
    if SETEXT_LEVEL_2.match(underline):
        return Heading(level=2, inlines=_parse_inline_text(body, definitions, footnotes), attr=attr)
    return None


def _thematic_break_from_lines(lines: list[str]) -> ThematicBreak | None:
    if len(lines) != 1:
        return None
    if THEMATIC_BREAK.match(lines[0]):
        return ThematicBreak()
    return None


def _raw_format_fenced_block_from_lines(lines: list[str]) -> RawBlock | None:
    if len(lines) < 2:
        return None
    opener = RAW_FORMAT_FENCE_OPEN.match(lines[0])
    if not opener:
        return None
    if not FENCE_CLOSE.match(lines[-1]):
        raise MarkdownScopeError('Unclosed raw format fence is outside the current reader scope.')
    return RawBlock(format=opener.group(1), text='\n'.join(lines[1:-1]))


def _strip_optional_block_indent(line: str) -> str:
    return re.sub(r'^ {0,3}', '', line, count=1)


def _raw_html_comment_block_from_lines(lines: list[str]) -> RawBlock | None:
    joined = '\n'.join(_strip_optional_block_indent(line) for line in lines)
    if joined.startswith('<!--') and joined.endswith('-->'):
        return RawBlock(format='html', text=joined)
    return None


def _raw_html_hr_block_from_lines(lines: list[str]) -> RawBlock | None:
    if len(lines) != 1:
        return None
    if RAW_HTML_HR_BLOCK.match(lines[0]):
        return RawBlock(format='html', text=_strip_optional_block_indent(lines[0]).strip())
    return None


def _raw_html_named_block_from_lines(lines: list[str]) -> RawBlock | None:
    if len(lines) < 2:
        return None
    opener = RAW_HTML_BLOCK_TAG_OPEN.match(lines[0])
    if not opener:
        return None
    tag = opener.group(1)
    if not re.match(rf'^\s{{0,3}}</{tag}>\s*$', lines[-1], re.IGNORECASE):
        raise MarkdownScopeError('Unclosed raw html block is outside the current reader scope.')
    return RawBlock(format='html', text='\n'.join(_strip_optional_block_indent(line) for line in lines))


def _raw_tex_environment_block_from_lines(lines: list[str]) -> RawBlock | None:
    if len(lines) < 2:
        return None
    opener = RAW_TEX_ENV_OPEN.match(lines[0])
    if not opener:
        return None
    env = opener.group(1)
    if not re.match(rf'^\s{{0,3}}\\end\{{{re.escape(env)}\}}\s*$', lines[-1]):
        raise MarkdownScopeError('Unclosed raw tex environment block is outside the current reader scope.')
    return RawBlock(format='tex', text='\n'.join(_strip_optional_block_indent(line) for line in lines))


def _raw_tex_command_block_from_lines(lines: list[str]) -> RawBlock | None:
    if len(lines) != 1:
        return None
    if RAW_TEX_COMMAND_BLOCK.match(lines[0]):
        return RawBlock(format='tex', text=_strip_optional_block_indent(lines[0]).strip())
    return None

def _code_block_from_lines(lines: list[str]) -> CodeBlock | None:
    if len(lines) < 2:
        return None
    opener = FENCE_OPEN.match(lines[0])
    if not opener:
        return None
    if not FENCE_CLOSE.match(lines[-1]):
        raise MarkdownScopeError('Unclosed fenced code block is outside the current reader scope.')
    opener_body = (opener.group(1) or '').strip()
    info = ''
    attr = Attr()
    if opener_body:
        if opener_body.startswith('{') and opener_body.endswith('}'):
            attr = _parse_attr_string(opener_body)
            classes = list(attr.classes)
            if classes:
                info = classes[0]
                attr = Attr(identifier=attr.identifier, classes=classes[1:], attributes=list(attr.attributes))
        else:
            info = opener_body
    body_lines = lines[1:-1]
    return CodeBlock(text='\n'.join(body_lines), info=info, attr=attr)


def _parse_pipe_table_row(line: str) -> list[str] | None:
    stripped = line.strip()
    if not (stripped.startswith('|') and stripped.endswith('|')):
        return None
    return [cell.strip() for cell in stripped[1:-1].split('|')]


def _parse_pipe_table_alignment(cell: str) -> str | None:
    token = cell.strip()
    if not token or any(ch not in ':-' for ch in token) or '-' not in token:
        return None
    if token.startswith(':') and token.endswith(':'):
        return 'AlignCenter'
    if token.startswith(':'):
        return 'AlignLeft'
    if token.endswith(':'):
        return 'AlignRight'
    return 'AlignDefault'


def _table_caption_from_lines(lines: list[str], definitions: dict[str, ReferenceDef], footnotes: dict[str, FootnoteDef]) -> TableCaption | None:
    if len(lines) != 1:
        return None
    match = TABLE_CAPTION_LINE.match(lines[0])
    if not match:
        return None
    caption = match.group(1).strip()
    if not caption:
        raise MarkdownScopeError('Empty table captions are outside the current reader scope.')
    return _parse_inline_text(caption, definitions, footnotes)


def _pipe_table_from_lines(lines: list[str], definitions: dict[str, ReferenceDef], footnotes: dict[str, FootnoteDef], caption: TableCaption | None = None) -> Table | None:
    if len(lines) < 2:
        return None
    header_cells = _parse_pipe_table_row(lines[0])
    delimiter_cells = _parse_pipe_table_row(lines[1])
    if header_cells is None or delimiter_cells is None or len(header_cells) != len(delimiter_cells) or len(header_cells) < 1:
        return None
    aligns: list[str] = []
    for cell in delimiter_cells:
        align = _parse_pipe_table_alignment(cell)
        if align is None:
            return None
        aligns.append(align)
    body_rows: list[list[list[InlineNode]]] = []
    for line in lines[2:]:
        row_cells = _parse_pipe_table_row(line)
        if row_cells is None or len(row_cells) != len(header_cells):
            return None
        body_rows.append([_parse_inline_text(cell, definitions, footnotes) if cell else [] for cell in row_cells])
    return Table(
        caption=list(caption or []),
        aligns=aligns,
        headers=[_parse_inline_text(cell, definitions, footnotes) if cell else [] for cell in header_cells],
        rows=body_rows,
    )


def _indented_code_block_from_lines(lines: list[str]) -> CodeBlock | None:
    if not lines:
        return None
    body_lines: list[str] = []
    for line in lines:
        match = INDENTED_CODE_LINE.match(line)
        if not match:
            return None
        body_lines.append(match.group(1))
    return CodeBlock(text='\n'.join(body_lines), info='')


def _definition_list_from_lines(lines: list[str], definitions: dict[str, ReferenceDef], footnotes: dict[str, FootnoteDef]) -> DefinitionList | None:
    if len(lines) < 2:
        return None
    items: list[tuple[list[InlineNode], list[list[Paragraph]]]] = []
    i = 0
    while i < len(lines):
        term_line = lines[i].strip()
        if not term_line:
            return None
        if i + 1 >= len(lines):
            return None
        j = i + 1
        defs_for_term: list[list[Paragraph]] = []
        while j < len(lines):
            match = DEFINITION_ITEM_LINE.match(lines[j])
            if not match:
                break
            content_lines = [match.group(1)]
            j += 1
            while j < len(lines):
                indented = INDENTED_CODE_LINE.match(lines[j])
                if not indented:
                    break
                content_lines.append(indented.group(1))
                j += 1
            defs_for_term.append([Paragraph(inlines=_parse_multiline_inlines(content_lines, definitions, footnotes))])
        if not defs_for_term:
            return None
        items.append((_parse_inline_text(term_line, definitions, footnotes), defs_for_term))
        i = j
    return DefinitionList(items=items)


def _paragraph_from_lines(lines: list[str], definitions: dict[str, ReferenceDef], footnotes: dict[str, FootnoteDef]) -> Paragraph:
    return Paragraph(inlines=_parse_multiline_inlines(lines, definitions, footnotes))


def _div_from_lines(lines: list[str], definitions: dict[str, ReferenceDef], footnotes: dict[str, FootnoteDef]) -> Div | None:
    if len(lines) < 2:
        return None
    opener = DIV_OPEN.match(lines[0])
    if not opener or not DIV_CLOSE.match(lines[-1]):
        return None
    attr_raw = opener.group(1) or '{}'
    attr = _parse_attr_string(attr_raw) if attr_raw != '{}' else Attr()
    inner_lines = lines[1:-1]
    for inner in inner_lines:
        if DIV_OPEN.match(inner):
            raise MarkdownScopeError('Nested fenced divs are outside the current reader scope.')
    inner_doc = read_markdown('\n'.join(inner_lines)) if inner_lines else Document(blocks=[])
    return Div(blocks=inner_doc.blocks, attr=attr)


def _block_quote_from_lines(lines: list[str], definitions: dict[str, ReferenceDef], footnotes: dict[str, FootnoteDef]) -> BlockQuote | None:
    quoted_lines: list[str] = []
    for line in lines:
        match = SIMPLE_BLOCK_QUOTE_LINE.match(line)
        if not match:
            return None
        content = match.group(1)
        if not content or content != content.strip():
            raise MarkdownScopeError('Empty or edge-spaced block-quote lines are outside the current reader scope.')
        if SIMPLE_BLOCK_QUOTE_LINE.match(content):
            raise MarkdownScopeError('Nested block quotes are outside the current reader scope.')
        if SIMPLE_BULLET_ITEM.match(content) or SIMPLE_ORDERED_ITEM.match(content):
            raise MarkdownScopeError('Lists inside block quotes are outside the current reader scope.')
        quoted_lines.append(content)
    return BlockQuote(blocks=[Paragraph(inlines=_parse_multiline_inlines(quoted_lines, definitions, footnotes))])


def _leading_spaces(line: str) -> int:
    return len(line) - len(line.lstrip(' '))


def _starts_list_kind(line: str, kind: str) -> bool:
    if kind == 'bullet':
        return SIMPLE_BULLET_ITEM.match(line) is not None and _leading_spaces(line) <= 3
    if kind == 'ordered':
        return SIMPLE_ORDERED_ITEM.match(line) is not None and _leading_spaces(line) <= 3
    raise ValueError(f'Unknown list kind: {kind}')


def _collect_list_region(blocks: list[list[str]], start: int, kind: str) -> tuple[list[str], int]:
    region_lines: list[str] = []
    i = start
    while i < len(blocks):
        first = blocks[i][0]
        if _starts_list_kind(first, kind) or _leading_spaces(first) >= 2:
            if region_lines:
                region_lines.append('')
            region_lines.extend(blocks[i])
            i += 1
            continue
        break
    return region_lines, i


def _strip_list_indent(line: str) -> str:
    if not line.strip():
        return ''
    indent = _leading_spaces(line)
    if indent < 2:
        raise MarkdownScopeError('List continuation lines are outside the current reader scope.')
    return line[indent:]


def _apply_task_marker(content: str) -> str:
    match = TASK_MARKER.match(content)
    if not match:
        return content
    mark = '☒' if match.group(1).lower() == 'x' else '☐'
    rest = (match.group(2) or '').strip()
    return mark if not rest else f'{mark} {rest}'


def _parse_list_item_blocks(first_content: str, tail_lines: list[str], definitions: dict[str, ReferenceDef], footnotes: dict[str, FootnoteDef]) -> list[object]:
    paragraph_lines = [_apply_task_marker(first_content)]
    i = 0
    while i < len(tail_lines):
        line = tail_lines[i]
        if not line.strip():
            break
        stripped = _strip_list_indent(line)
        if SIMPLE_BULLET_ITEM.match(stripped) or SIMPLE_ORDERED_ITEM.match(stripped):
            break
        paragraph_lines.append(stripped)
        i += 1
    blocks: list[object] = [Paragraph(inlines=_parse_multiline_inlines(paragraph_lines, definitions, footnotes))]
    remainder = tail_lines[i:]
    if remainder:
        dedented = '\n'.join(_strip_list_indent(line) if line.strip() else '' for line in remainder)
        if dedented.strip():
            nested_doc = read_markdown(dedented)
            blocks.extend(nested_doc.blocks)
    return blocks


def _bullet_list_from_lines(lines: list[str], definitions: dict[str, ReferenceDef], footnotes: dict[str, FootnoteDef]) -> BulletList | None:
    items: list[list[object]] = []
    i = 0
    while i < len(lines):
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i >= len(lines):
            break
        match = SIMPLE_BULLET_ITEM.match(lines[i])
        if not match:
            return None
        first_content = match.group(1)
        i += 1
        tail_lines: list[str] = []
        while i < len(lines):
            if lines[i].strip() and _leading_spaces(lines[i]) < 2 and _starts_list_kind(lines[i], 'bullet'):
                break
            tail_lines.append(lines[i])
            i += 1
        items.append(_parse_list_item_blocks(first_content, tail_lines, definitions, footnotes))
    return BulletList(items=items) if items else None


def _ordered_list_from_lines(lines: list[str], definitions: dict[str, ReferenceDef], footnotes: dict[str, FootnoteDef]) -> OrderedList | None:
    items: list[list[object]] = []
    start: int | None = None
    i = 0
    while i < len(lines):
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i >= len(lines):
            break
        match = SIMPLE_ORDERED_ITEM.match(lines[i])
        if not match:
            return None
        if start is None:
            start = int(match.group(1))
        first_content = match.group(2)
        i += 1
        tail_lines: list[str] = []
        while i < len(lines):
            if lines[i].strip() and _leading_spaces(lines[i]) < 2 and _starts_list_kind(lines[i], 'ordered'):
                break
            tail_lines.append(lines[i])
            i += 1
        items.append(_parse_list_item_blocks(first_content, tail_lines, definitions, footnotes))
    if not items or start is None:
        return None
    return OrderedList(start=start, items=items)


def read_markdown(text: str) -> Document:
    try:
        meta, body = split_yaml_front_matter(text)
    except MetadataReaderError as exc:
        raise MarkdownScopeError(str(exc)) from exc
    raw_blocks = _split_blocks(body)
    definitions, footnotes_raw, blocks_to_parse = _parse_reference_definitions(raw_blocks)
    footnotes = _materialize_footnotes(footnotes_raw, definitions)
    blocks = []
    i = 0
    while i < len(blocks_to_parse):
        lines = blocks_to_parse[i]
        caption_here = _table_caption_from_lines(lines, definitions, footnotes)
        if caption_here is not None and i + 1 < len(blocks_to_parse):
            table_after = _pipe_table_from_lines(blocks_to_parse[i + 1], definitions, footnotes, caption_here)
            if table_after is not None:
                blocks.append(table_after)
                i += 2
                continue
        caption_after = _table_caption_from_lines(blocks_to_parse[i + 1], definitions, footnotes) if i + 1 < len(blocks_to_parse) else None
        pipe_table = _pipe_table_from_lines(lines, definitions, footnotes, caption_after)
        if pipe_table is not None:
            blocks.append(pipe_table)
            i += 2 if caption_after is not None else 1
            continue
        _reject_tabs(lines)
        raw_format_fenced = _raw_format_fenced_block_from_lines(lines)
        if raw_format_fenced is not None:
            blocks.append(raw_format_fenced)
            i += 1
            continue
        div_block = _div_from_lines(lines, definitions, footnotes)
        if div_block is not None:
            blocks.append(div_block)
            i += 1
            continue
        raw_html_comment = _raw_html_comment_block_from_lines(lines)
        if raw_html_comment is not None:
            blocks.append(raw_html_comment)
            i += 1
            continue
        raw_html_hr = _raw_html_hr_block_from_lines(lines)
        if raw_html_hr is not None:
            blocks.append(raw_html_hr)
            i += 1
            continue
        raw_html_named = _raw_html_named_block_from_lines(lines)
        if raw_html_named is not None:
            blocks.append(raw_html_named)
            i += 1
            continue
        raw_tex_env = _raw_tex_environment_block_from_lines(lines)
        if raw_tex_env is not None:
            blocks.append(raw_tex_env)
            i += 1
            continue
        raw_tex_command = _raw_tex_command_block_from_lines(lines)
        if raw_tex_command is not None:
            blocks.append(raw_tex_command)
            i += 1
            continue
        display_math = _display_math_block_from_lines(lines)
        if display_math is not None:
            blocks.append(display_math)
            i += 1
            continue
        candidate = _heading_from_lines(lines, definitions, footnotes)
        if candidate is not None:
            blocks.append(candidate)
            i += 1
            continue
        setext_candidate = _setext_heading_from_lines(lines, definitions, footnotes)
        if setext_candidate is not None:
            blocks.append(setext_candidate)
            i += 1
            continue
        thematic_break = _thematic_break_from_lines(lines)
        if thematic_break is not None:
            blocks.append(thematic_break)
            i += 1
            continue
        code_block = _code_block_from_lines(lines)
        if code_block is not None:
            blocks.append(code_block)
            i += 1
            continue
        indented_code_block = _indented_code_block_from_lines(lines)
        if indented_code_block is not None:
            blocks.append(indented_code_block)
            i += 1
            continue
        block_quote = _block_quote_from_lines(lines, definitions, footnotes)
        if block_quote is not None:
            blocks.append(block_quote)
            i += 1
            continue
        if _starts_list_kind(lines[0], 'bullet'):
            list_region, next_i = _collect_list_region(blocks_to_parse, i, 'bullet')
            bullet_list = _bullet_list_from_lines(list_region, definitions, footnotes)
            if bullet_list is not None:
                blocks.append(bullet_list)
                i = next_i
                continue
        if _starts_list_kind(lines[0], 'ordered'):
            list_region, next_i = _collect_list_region(blocks_to_parse, i, 'ordered')
            ordered_list = _ordered_list_from_lines(list_region, definitions, footnotes)
            if ordered_list is not None:
                blocks.append(ordered_list)
                i = next_i
                continue
        definition_list = _definition_list_from_lines(lines, definitions, footnotes)
        if definition_list is not None:
            combined_items = list(definition_list.items)
            j = i + 1
            while j < len(blocks_to_parse):
                next_definition_list = _definition_list_from_lines(blocks_to_parse[j], definitions, footnotes)
                if next_definition_list is None:
                    break
                combined_items.extend(next_definition_list.items)
                j += 1
            blocks.append(DefinitionList(items=combined_items))
            i = j
            continue
        _reject_unsupported_line_start(lines[0])
        blocks.append(_paragraph_from_lines(lines, definitions, footnotes))
        i += 1
    return Document(blocks=blocks, meta=meta)
