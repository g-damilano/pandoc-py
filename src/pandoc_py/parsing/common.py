from __future__ import annotations

import re

from pandoc_py.ast import Attr, Space, Str


class ParsingError(ValueError):
    """Raised when shared parsing helpers receive unsupported input."""


InlineTextNode = Str | Space


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def parse_plain_segment(text: str) -> list[InlineTextNode]:
    inlines: list[InlineTextNode] = []
    for token in re.findall(r'[^ ]+| +', text):
        if token.isspace():
            inlines.append(Space())
        else:
            inlines.append(Str(token))
    return inlines


def normalize_citation_suffix_text(text: str) -> str:
    return re.sub(r'\b(pp?\.) (?=\d)', lambda match: f"{match.group(1)}\xa0", text)


def citation_suffix_inlines(text: str) -> list[InlineTextNode]:
    return parse_plain_segment(normalize_citation_suffix_text(text))


def normalize_reference_label(label: str) -> str:
    collapsed = ' '.join(label.strip().split())
    if not collapsed:
        raise ParsingError('Empty reference labels are outside the current reader scope.')
    return collapsed.casefold()


def parse_attr_string(raw: str) -> Attr:
    raw = raw.strip()
    if not (raw.startswith('{') and raw.endswith('}')):
        raise ParsingError('Malformed attribute list is outside the current reader scope.')
    body = raw[1:-1].strip()
    if not body:
        raise ParsingError('Empty attribute lists are outside the current reader scope.')
    tokens = re.findall(r'"[^"]*"|\S+', body)
    identifier = ''
    classes: list[str] = []
    attributes: list[tuple[str, str]] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.startswith('#'):
            if identifier:
                raise ParsingError('Multiple identifiers in one attribute list are outside the current reader scope.')
            identifier = token[1:]
            if not identifier:
                raise ParsingError('Empty identifiers are outside the current reader scope.')
            i += 1
            continue
        if token.startswith('.'):
            cls = token[1:]
            if not cls:
                raise ParsingError('Empty classes are outside the current reader scope.')
            classes.append(cls)
            i += 1
            continue
        if '=' in token:
            key, value = token.split('=', 1)
            if not key:
                raise ParsingError('Empty attribute keys are outside the current reader scope.')
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            attributes.append((key, value))
            i += 1
            continue
        if i + 2 < len(tokens) and tokens[i + 1] == '=':
            key = token
            value = tokens[i + 2]
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            attributes.append((key, value))
            i += 3
            continue
        raise ParsingError('Unsupported attribute token is outside the current reader scope.')
    return Attr(identifier=identifier, classes=classes, attributes=attributes)


def split_trailing_attr(text: str) -> tuple[str, Attr]:
    stripped = text.rstrip()
    if not stripped.endswith('}'):
        return text.strip(), Attr()
    start = stripped.rfind('{')
    if start == -1:
        return text.strip(), Attr()
    if start > 0 and stripped[start - 1] not in {' ', '\t'}:
        return text.strip(), Attr()
    return stripped[:start].rstrip(), parse_attr_string(stripped[start:])


def attr_is_empty(attr: Attr) -> bool:
    return not attr.identifier and not attr.classes and not attr.attributes
