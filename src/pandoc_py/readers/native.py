from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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
    RawBlock,
    RawInline,
    SoftBreak,
    Space,
    Span,
    Str,
    Strikeout,
    Strong,
    Subscript,
    Superscript,
    Table,
    ThematicBreak,
)


class NativeReaderError(ValueError):
    """Raised when Pandoc native input falls outside the current supported slice."""


@dataclass(frozen=True)
class _Ident:
    name: str


@dataclass(frozen=True)
class _App:
    tag: str
    args: list[Any]


@dataclass(frozen=True)
class _Record:
    tag: str
    fields: dict[str, Any]


def _decode_haskell_string(raw: str) -> str:
    out: list[str] = []
    idx = 0
    while idx < len(raw):
        char = raw[idx]
        if char != '\\':
            out.append(char)
            idx += 1
            continue
        idx += 1
        if idx >= len(raw):
            out.append('\\')
            break
        escaped = raw[idx]
        if escaped in {'\\', '"', "'"}:
            out.append(escaped)
            idx += 1
            continue
        if escaped == 'n':
            out.append('\n')
            idx += 1
            continue
        if escaped == 'r':
            out.append('\r')
            idx += 1
            continue
        if escaped == 't':
            out.append('\t')
            idx += 1
            continue
        if escaped == 'b':
            out.append('\b')
            idx += 1
            continue
        if escaped == 'f':
            out.append('\f')
            idx += 1
            continue
        if escaped == '&':
            idx += 1
            continue
        if escaped.isdigit():
            end = idx
            while end < len(raw) and raw[end].isdigit():
                end += 1
            out.append(chr(int(raw[idx:end])))
            idx = end
            continue
        out.append(escaped)
        idx += 1
    return ''.join(out)


def _tokenize(source: str) -> list[Any]:
    tokens: list[Any] = []
    idx = 0
    while idx < len(source):
        char = source[idx]
        if char.isspace():
            idx += 1
            continue
        if char in '[](){},=':
            tokens.append(char)
            idx += 1
            continue
        if char == '"':
            idx += 1
            raw_chars: list[str] = []
            while idx < len(source):
                if source[idx] == '"':
                    break
                if source[idx] == '\\':
                    raw_chars.append(source[idx])
                    idx += 1
                    if idx < len(source):
                        raw_chars.append(source[idx])
                        idx += 1
                    continue
                raw_chars.append(source[idx])
                idx += 1
            if idx >= len(source) or source[idx] != '"':
                raise NativeReaderError('Unterminated string in native input.')
            idx += 1
            tokens.append(('STRING', _decode_haskell_string(''.join(raw_chars))))
            continue
        if char.isdigit() or (char == '-' and idx + 1 < len(source) and source[idx + 1].isdigit()):
            end = idx + 1
            while end < len(source) and source[end].isdigit():
                end += 1
            tokens.append(('NUMBER', int(source[idx:end])))
            idx = end
            continue
        if char.isalpha() or char == '_':
            end = idx + 1
            while end < len(source) and (source[end].isalnum() or source[end] in "._'-"):
                end += 1
            tokens.append(('IDENT', source[idx:end]))
            idx = end
            continue
        raise NativeReaderError(f'Unsupported character in native input: {char!r}')
    return tokens


class _Parser:
    def __init__(self, tokens: list[Any]):
        self.tokens = tokens
        self.index = 0

    def _peek(self) -> Any | None:
        if self.index >= len(self.tokens):
            return None
        return self.tokens[self.index]

    def _eat(self, token: Any | None = None, token_type: str | None = None) -> Any:
        current = self._peek()
        if current is None:
            raise NativeReaderError('Unexpected end of native input.')
        if token is not None and current != token:
            raise NativeReaderError(f'Expected {token!r}, found {current!r}.')
        if token_type is not None:
            if not isinstance(current, tuple) or current[0] != token_type:
                raise NativeReaderError(f'Expected token type {token_type!r}, found {current!r}.')
        self.index += 1
        return current

    def parse(self) -> Any:
        value = self._parse_term(stop_tokens=set())
        if self._peek() is not None:
            raise NativeReaderError(f'Unexpected trailing token: {self._peek()!r}')
        return value

    def _parse_term(self, stop_tokens: set[Any]) -> Any:
        atoms: list[Any] = []
        while True:
            current = self._peek()
            if current is None or current in stop_tokens:
                break
            atoms.append(self._parse_atom())
            current = self._peek()
            if current is None or current in stop_tokens:
                break
        if not atoms:
            raise NativeReaderError('Expected an expression in native input.')
        if len(atoms) == 1:
            return atoms[0]
        first = atoms[0]
        if isinstance(first, _Ident):
            return _App(first.name, atoms[1:])
        raise NativeReaderError('Only constructor applications are supported in the current native reader slice.')

    def _parse_atom(self) -> Any:
        current = self._peek()
        if current == '[':
            return self._parse_list()
        if current == '(':
            return self._parse_parens()
        if isinstance(current, tuple) and current[0] == 'STRING':
            self.index += 1
            return current[1]
        if isinstance(current, tuple) and current[0] == 'NUMBER':
            self.index += 1
            return current[1]
        if isinstance(current, tuple) and current[0] == 'IDENT':
            name = current[1]
            self.index += 1
            if self._peek() == '{':
                return self._parse_record(name)
            return _Ident(name)
        raise NativeReaderError(f'Unsupported native atom: {current!r}')

    def _parse_list(self) -> list[Any]:
        self._eat('[')
        items: list[Any] = []
        while self._peek() != ']':
            items.append(self._parse_term(stop_tokens={',', ']'}))
            if self._peek() == ',':
                self._eat(',')
        self._eat(']')
        return items

    def _parse_parens(self) -> Any:
        self._eat('(')
        if self._peek() == ')':
            self._eat(')')
            return tuple()
        items = [self._parse_term(stop_tokens={',', ')'})]
        saw_comma = False
        while self._peek() == ',':
            saw_comma = True
            self._eat(',')
            items.append(self._parse_term(stop_tokens={',', ')'}))
        self._eat(')')
        if saw_comma:
            return tuple(items)
        return items[0]

    def _parse_record(self, tag: str) -> _Record:
        self._eat('{')
        fields: dict[str, Any] = {}
        while self._peek() != '}':
            name = self._eat(token_type='IDENT')[1]
            self._eat('=')
            fields[name] = self._parse_term(stop_tokens={',', '}'})
            if self._peek() == ',':
                self._eat(',')
        self._eat('}')
        return _Record(tag, fields)


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise NativeReaderError(message)


def _parse_native_tree(source: str) -> Any:
    return _Parser(_tokenize(source)).parse()


def _ident_name(value: Any) -> str:
    _expect(isinstance(value, _Ident), f'Expected an identifier, got {type(value).__name__}.')
    return value.name


def _expect_app(value: Any, tag: str | None = None) -> _App:
    _expect(isinstance(value, _App), f'Expected constructor application, got {type(value).__name__}.')
    app = value
    if tag is not None:
        _expect(app.tag == tag, f'Expected native tag {tag!r}, found {app.tag!r}.')
    return app


def _parse_attr(value: Any) -> Attr:
    _expect(isinstance(value, tuple) and len(value) == 3, 'Attr payload must be a three-tuple.')
    identifier, classes, attributes = value
    _expect(isinstance(identifier, str), 'Attr identifier must be a string.')
    _expect(isinstance(classes, list) and all(isinstance(item, str) for item in classes), 'Attr classes must be a list of strings.')
    _expect(isinstance(attributes, list), 'Attr key/value pairs must be a list.')
    parsed_attributes: list[tuple[str, str]] = []
    for item in attributes:
        _expect(isinstance(item, tuple) and len(item) == 2, 'Attr key/value entries must be tuples of length 2.')
        key, raw_value = item
        _expect(isinstance(key, str) and isinstance(raw_value, str), 'Attr key/value entries must contain strings.')
        parsed_attributes.append((key, raw_value))
    return Attr(identifier=identifier, classes=list(classes), attributes=parsed_attributes)


def _parse_format(value: Any) -> str:
    if isinstance(value, str):
        return value
    app = _expect_app(value, 'Format')
    _expect(len(app.args) == 1 and isinstance(app.args[0], str), 'Format payload must wrap one string.')
    return app.args[0]


def _parse_inlines(value: Any) -> list[Any]:
    _expect(isinstance(value, list), 'Inline payload must be a list.')
    return [_parse_inline(item) for item in value]


def _parse_blocks(value: Any) -> list[Any]:
    _expect(isinstance(value, list), 'Block payload must be a list.')
    return [_parse_block(item) for item in value]


def _parse_citation(value: Any) -> Citation:
    _expect(isinstance(value, _Record) and value.tag == 'Citation', 'Citation payload must be a Citation record.')
    return Citation(
        citation_id=str(value.fields.get('citationId', '')),
        prefix=_parse_inlines(value.fields.get('citationPrefix', [])),
        suffix=_parse_inlines(value.fields.get('citationSuffix', [])),
        mode=_ident_name(value.fields.get('citationMode', _Ident('NormalCitation'))),
        note_num=int(value.fields.get('citationNoteNum', 0)),
        hash=int(value.fields.get('citationHash', 0)),
    )


def _parse_inline(value: Any) -> Any:
    if isinstance(value, _Ident):
        if value.name == 'Space':
            return Space()
        if value.name == 'SoftBreak':
            return SoftBreak()
        if value.name == 'LineBreak':
            return HardBreak()
        raise NativeReaderError(f'Unsupported bare inline tag in current native reader slice: {value.name}')
    app = _expect_app(value)
    if app.tag == 'Str':
        _expect(len(app.args) == 1 and isinstance(app.args[0], str), 'Str payload must wrap one string.')
        return Str(app.args[0])
    if app.tag == 'Emph':
        return Emph(_parse_inlines(app.args[0]))
    if app.tag == 'Strong':
        return Strong(_parse_inlines(app.args[0]))
    if app.tag == 'Strikeout':
        return Strikeout(_parse_inlines(app.args[0]))
    if app.tag == 'Subscript':
        return Subscript(_parse_inlines(app.args[0]))
    if app.tag == 'Superscript':
        return Superscript(_parse_inlines(app.args[0]))
    if app.tag == 'Math':
        _expect(len(app.args) == 2 and isinstance(app.args[1], str), 'Math payload must be [mode, text].')
        return Math(text=app.args[1], display=(_ident_name(app.args[0]) == 'DisplayMath'))
    if app.tag == 'Code':
        _expect(len(app.args) == 2 and isinstance(app.args[1], str), 'Code payload must be [attr, text].')
        return Code(app.args[1])
    if app.tag == 'Span':
        _expect(len(app.args) == 2, 'Span payload must be [attr, inlines].')
        return Span(inlines=_parse_inlines(app.args[1]), attr=_parse_attr(app.args[0]))
    if app.tag == 'Link':
        _expect(len(app.args) == 3, 'Link payload must be [attr, inlines, target].')
        attr = _parse_attr(app.args[0])
        target_payload = app.args[2]
        _expect(isinstance(target_payload, tuple) and len(target_payload) == 2, 'Link target must be (url, title).')
        target, title = target_payload
        _expect(isinstance(target, str) and isinstance(title, str), 'Link target values must be strings.')
        autolink = (not attr.identifier and not attr.attributes and attr.classes in (['uri'], ['email']))
        return Link(
            inlines=_parse_inlines(app.args[1]),
            target=target,
            title=title,
            autolink=autolink,
            attr=Attr() if autolink else attr,
        )
    if app.tag == 'Image':
        _expect(len(app.args) == 3, 'Image payload must be [attr, inlines, target].')
        target_payload = app.args[2]
        _expect(isinstance(target_payload, tuple) and len(target_payload) == 2, 'Image target must be (url, title).')
        target, title = target_payload
        _expect(isinstance(target, str) and isinstance(title, str), 'Image target values must be strings.')
        return Image(
            inlines=_parse_inlines(app.args[1]),
            target=target,
            title=title,
            attr=_parse_attr(app.args[0]),
        )
    if app.tag == 'RawInline':
        _expect(len(app.args) == 2 and isinstance(app.args[1], str), 'RawInline payload must be [format, text].')
        return RawInline(format=_parse_format(app.args[0]), text=app.args[1])
    if app.tag == 'Note':
        _expect(len(app.args) == 1, 'Note payload must wrap a block list.')
        return Note(blocks=_parse_blocks(app.args[0]))
    if app.tag == 'Cite':
        _expect(len(app.args) == 2, 'Cite payload must be [citations, inlines].')
        _expect(isinstance(app.args[0], list), 'Cite citations payload must be a list.')
        return Cite(
            citations=[_parse_citation(item) for item in app.args[0]],
            inlines=_parse_inlines(app.args[1]),
        )
    raise NativeReaderError(f'Unsupported inline tag for current native reader slice: {app.tag}')


def _parse_plain_or_para_inlines(value: Any) -> list[Any]:
    app = _expect_app(value)
    _expect(app.tag in {'Plain', 'Para'}, f'Expected Plain or Para block, found {app.tag!r}.')
    _expect(len(app.args) == 1, f'{app.tag} payload must wrap one inline list.')
    return _parse_inlines(app.args[0])


def _parse_table_cell(value: Any) -> list[Any]:
    app = _expect_app(value, 'Cell')
    _expect(len(app.args) == 5, 'Cell payload must be [attr, align, rowspan, colspan, blocks].')
    row_span = _expect_app(app.args[2], 'RowSpan')
    col_span = _expect_app(app.args[3], 'ColSpan')
    _expect(row_span.args == [1] and col_span.args == [1], 'Only rowspan=1 and colspan=1 are supported in the current table slice.')
    blocks = app.args[4]
    _expect(isinstance(blocks, list), 'Cell blocks payload must be a list.')
    if not blocks:
        return []
    return _parse_plain_or_para_inlines(blocks[0])


def _parse_table_row(value: Any) -> tuple[Attr, list[list[Any]]]:
    app = _expect_app(value, 'Row')
    _expect(len(app.args) == 2 and isinstance(app.args[1], list), 'Row payload must be [attr, cells].')
    return _parse_attr(app.args[0]), [_parse_table_cell(cell) for cell in app.args[1]]


def _parse_table(value: _App) -> Table:
    _expect(len(value.args) == 6, 'Table payload must have six fields in the current slice.')
    caption_app = _expect_app(value.args[1], 'Caption')
    _expect(len(caption_app.args) == 2, 'Caption payload must be [short, blocks].')
    caption_blocks = caption_app.args[1]
    caption: list[Any] = []
    if caption_blocks:
        caption = _parse_plain_or_para_inlines(caption_blocks[0])

    colspecs = value.args[2]
    _expect(isinstance(colspecs, list), 'Table colspecs payload must be a list.')
    aligns: list[str] = []
    for item in colspecs:
        _expect(isinstance(item, tuple) and len(item) == 2, 'Colspec entries must be tuples of length 2.')
        aligns.append(_ident_name(item[0]))

    head = _expect_app(value.args[3], 'TableHead')
    _expect(len(head.args) == 2 and isinstance(head.args[1], list), 'Table head payload must be [attr, rows].')
    header_row_attr = Attr()
    headers: list[list[Any]] = []
    if head.args[1]:
        header_row_attr, headers = _parse_table_row(head.args[1][0])

    bodies = value.args[4]
    _expect(isinstance(bodies, list), 'Table bodies payload must be a list.')
    rows: list[list[list[Any]]] = []
    row_attrs: list[Attr] = []
    for body in bodies:
        body_app = _expect_app(body, 'TableBody')
        _expect(len(body_app.args) == 4 and isinstance(body_app.args[3], list), 'TableBody payload must be [attr, rowHeadCols, intermediate, rows].')
        for row in body_app.args[3]:
            row_attr, cells = _parse_table_row(row)
            row_attrs.append(row_attr)
            rows.append(cells)

    return Table(
        caption=caption,
        aligns=aligns,
        headers=headers,
        rows=rows,
        header_row_attr=header_row_attr,
        row_attrs=row_attrs,
    )


def _parse_figure(value: _App) -> Figure:
    _expect(len(value.args) == 3, 'Figure payload must be [attr, caption, blocks].')
    blocks = value.args[2]
    _expect(isinstance(blocks, list) and len(blocks) == 1, 'Current figure slice expects one body block.')
    body = _expect_app(blocks[0], 'Plain')
    _expect(len(body.args) == 1 and len(body.args[0]) == 1, 'Current figure slice expects one Image inside Plain.')
    image = _parse_inline(body.args[0][0])
    _expect(isinstance(image, Image), 'Current figure slice expects one Image inside the body.')
    return Figure(
        image=Image(
            inlines=list(image.inlines),
            target=image.target,
            title=image.title,
            attr=image.attr,
        ),
        attr=_parse_attr(value.args[0]),
    )


def _parse_definition_list(value: _App) -> DefinitionList:
    _expect(len(value.args) == 1 and isinstance(value.args[0], list), 'DefinitionList payload must wrap one list.')
    items: list[tuple[list[Any], list[list[Any]]]] = []
    for item in value.args[0]:
        _expect(isinstance(item, tuple) and len(item) == 2, 'Definition list items must be (term, defs).')
        term_payload, defs_payload = item
        _expect(isinstance(defs_payload, list), 'Definition list defs must be a list.')
        items.append((_parse_inlines(term_payload), [_parse_blocks(definition) for definition in defs_payload]))
    return DefinitionList(items=items)


def _parse_block(value: Any) -> Any:
    if isinstance(value, _Ident):
        if value.name == 'HorizontalRule':
            return ThematicBreak()
        raise NativeReaderError(f'Unsupported bare block tag in current native reader slice: {value.name}')
    app = _expect_app(value)
    if app.tag in {'Para', 'Plain'}:
        _expect(len(app.args) == 1, f'{app.tag} payload must wrap one inline list.')
        return Paragraph(_parse_inlines(app.args[0]))
    if app.tag == 'Header':
        _expect(len(app.args) == 3, 'Header payload must be [level, attr, inlines].')
        return Heading(level=int(app.args[0]), attr=_parse_attr(app.args[1]), inlines=_parse_inlines(app.args[2]))
    if app.tag == 'CodeBlock':
        _expect(len(app.args) == 2 and isinstance(app.args[1], str), 'CodeBlock payload must be [attr, text].')
        attr = _parse_attr(app.args[0])
        classes = list(attr.classes)
        info = classes[0] if classes else ''
        rest_classes = classes[1:] if classes else []
        return CodeBlock(
            text=app.args[1],
            info=info,
            attr=Attr(identifier=attr.identifier, classes=rest_classes, attributes=list(attr.attributes)),
        )
    if app.tag == 'RawBlock':
        _expect(len(app.args) == 2 and isinstance(app.args[1], str), 'RawBlock payload must be [format, text].')
        return RawBlock(format=_parse_format(app.args[0]), text=app.args[1])
    if app.tag == 'BlockQuote':
        _expect(len(app.args) == 1, 'BlockQuote payload must wrap one block list.')
        return BlockQuote(blocks=_parse_blocks(app.args[0]))
    if app.tag == 'BulletList':
        _expect(len(app.args) == 1 and isinstance(app.args[0], list), 'BulletList payload must wrap one item list.')
        return BulletList(items=[_parse_blocks(item) for item in app.args[0]])
    if app.tag == 'OrderedList':
        _expect(len(app.args) == 2, 'OrderedList payload must be [attrs, items].')
        attrs = app.args[0]
        _expect(isinstance(attrs, tuple) and len(attrs) == 3, 'OrderedList attrs must be (start, style, delim).')
        return OrderedList(
            start=int(attrs[0]),
            style=_ident_name(attrs[1]),
            delimiter=_ident_name(attrs[2]),
            items=[_parse_blocks(item) for item in app.args[1]],
        )
    if app.tag == 'DefinitionList':
        return _parse_definition_list(app)
    if app.tag == 'Div':
        _expect(len(app.args) == 2, 'Div payload must be [attr, blocks].')
        return Div(attr=_parse_attr(app.args[0]), blocks=_parse_blocks(app.args[1]))
    if app.tag == 'Figure':
        return _parse_figure(app)
    if app.tag == 'Table':
        return _parse_table(app)
    raise NativeReaderError(f'Unsupported block tag for current native reader slice: {app.tag}')


def read_native(source: str) -> Document:
    tree = _parse_native_tree(source)
    if isinstance(tree, _App) and tree.tag == 'Pandoc':
        raise NativeReaderError(
            'Pandoc-wrapper native input with top-level metadata is outside the current admitted native reader slice.'
        )
    _expect(isinstance(tree, list), 'Current native reader slice expects the block-list native surface.')
    return Document(blocks=_parse_blocks(tree), source_format='native')
