"""Format registry for pandoc_py readers and writers.

The registry is a process-global lookup keyed by canonical format name.
``register_reader`` / ``register_writer`` accept a ``Reader`` / ``Writer``
*instance* and store it under its ``format_name`` plus all declared
``aliases``. ``get_reader`` / ``get_writer`` dispatch by name with alias
resolution.

The registry is the single point of truth that the ``app`` layer consults.
Adding a new format family is therefore: subclass ``Reader``/``Writer``,
construct an instance, call ``register_reader``/``register_writer``.
"""

from __future__ import annotations

from .base import Reader, Writer


class FormatRegistry:
    def __init__(self) -> None:
        self._readers: dict[str, Reader] = {}
        self._writers: dict[str, Writer] = {}
        self._reader_aliases: dict[str, str] = {}
        self._writer_aliases: dict[str, str] = {}

    def register_reader(self, reader: Reader) -> Reader:
        canonical = reader.format_name
        if not canonical:
            raise ValueError(f'Reader {reader!r} must declare a format_name.')
        self._readers[canonical] = reader
        for alias in reader.aliases:
            self._reader_aliases[alias] = canonical
        return reader

    def register_writer(self, writer: Writer) -> Writer:
        canonical = writer.format_name
        if not canonical:
            raise ValueError(f'Writer {writer!r} must declare a format_name.')
        self._writers[canonical] = writer
        for alias in writer.aliases:
            self._writer_aliases[alias] = canonical
        return writer

    def resolve_reader_name(self, name: str) -> str:
        if name in self._readers:
            return name
        return self._reader_aliases.get(name, name)

    def resolve_writer_name(self, name: str) -> str:
        if name in self._writers:
            return name
        return self._writer_aliases.get(name, name)

    def get_reader(self, name: str) -> Reader:
        canonical = self.resolve_reader_name(name)
        if canonical not in self._readers:
            available = ', '.join(sorted(self._readers))
            raise KeyError(f'No reader registered for format {name!r}. Available: {available}')
        return self._readers[canonical]

    def get_writer(self, name: str) -> Writer:
        canonical = self.resolve_writer_name(name)
        if canonical not in self._writers:
            available = ', '.join(sorted(self._writers))
            raise KeyError(f'No writer registered for format {name!r}. Available: {available}')
        return self._writers[canonical]

    def list_readers(self) -> list[str]:
        return sorted(self._readers)

    def list_writers(self) -> list[str]:
        return sorted(self._writers)

    def list_aliases(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {name: [] for name in self._readers}
        for alias, canonical in self._reader_aliases.items():
            out.setdefault(canonical, []).append(alias)
        for alias, canonical in self._writer_aliases.items():
            out.setdefault(canonical, []).append(alias)
        for name in out:
            out[name] = sorted(set(out[name]))
        return out


_GLOBAL = FormatRegistry()


def register_reader(reader: Reader) -> Reader:
    return _GLOBAL.register_reader(reader)


def register_writer(writer: Writer) -> Writer:
    return _GLOBAL.register_writer(writer)


def get_reader(name: str) -> Reader:
    return _GLOBAL.get_reader(name)


def get_writer(name: str) -> Writer:
    return _GLOBAL.get_writer(name)


def list_readers() -> list[str]:
    return _GLOBAL.list_readers()


def list_writers() -> list[str]:
    return _GLOBAL.list_writers()


def list_aliases() -> dict[str, list[str]]:
    return _GLOBAL.list_aliases()
