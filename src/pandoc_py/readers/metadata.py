from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import yaml

from pandoc_py.ast import MetaBlocks, MetaBool, MetaInlines, MetaList, MetaMap, MetaString, MetaValue, Paragraph


class MetadataReaderError(ValueError):
    """Raised when YAML metadata or meta values fall outside the current supported slice."""


def split_yaml_front_matter(source: str) -> tuple[dict[str, MetaValue], str]:
    normalized = source.replace('\r\n', '\n').replace('\r', '\n')
    if not normalized.startswith('---\n'):
        return {}, source
    lines = normalized.split('\n')
    end_idx: int | None = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() in {'---', '...'}:
            end_idx = idx
            break
    if end_idx is None:
        return {}, source
    yaml_text = '\n'.join(lines[1:end_idx])
    rest = '\n'.join(lines[end_idx + 1:])
    if rest.startswith('\n'):
        rest = rest[1:]
    data = yaml.safe_load(yaml_text)
    if data is None:
        return {}, rest
    if not isinstance(data, Mapping):
        raise MetadataReaderError('YAML metadata front matter must decode to a mapping.')
    meta = {str(key): python_to_meta(value) for key, value in data.items()}
    return meta, rest


def python_to_meta(value: Any) -> MetaValue:
    if isinstance(value, bool):
        return MetaBool(value)
    if value is None:
        return MetaString('')
    if isinstance(value, (int, float)):
        return _string_to_meta(str(value))
    if isinstance(value, str):
        return _string_to_meta(value)
    if isinstance(value, Mapping):
        return MetaMap({str(key): python_to_meta(item) for key, item in value.items()})
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return MetaList([python_to_meta(item) for item in value])
    raise MetadataReaderError(f'Unsupported metadata value in current slice: {type(value).__name__}')


def _string_to_meta(text: str) -> MetaValue:
    from pandoc_py.readers.markdown import read_markdown

    if text == '':
        return MetaString('')
    document = read_markdown(text)
    if len(document.blocks) == 1 and isinstance(document.blocks[0], Paragraph):
        return MetaInlines(list(document.blocks[0].inlines))
    return MetaBlocks(list(document.blocks))


def meta_to_python(meta: MetaValue) -> Any:
    if isinstance(meta, MetaBool):
        return meta.value
    if isinstance(meta, MetaString):
        return meta.text
    if isinstance(meta, MetaInlines):
        return {'_meta_kind': 'inlines'}
    if isinstance(meta, MetaBlocks):
        return {'_meta_kind': 'blocks'}
    if isinstance(meta, MetaList):
        return [meta_to_python(item) for item in meta.items]
    if isinstance(meta, MetaMap):
        return {key: meta_to_python(value) for key, value in meta.mapping.items()}
    raise MetadataReaderError(f'Unsupported MetaValue in current slice: {type(meta).__name__}')
