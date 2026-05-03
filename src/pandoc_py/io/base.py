"""Base classes for pandoc_py readers and writers.

Every format family conforms to the ``Reader`` / ``Writer`` ABCs so that:

* the ``app`` and ``cli`` layers can dispatch by format name without
  format-specific imports;
* the differential harness can iterate the registry to know which routes are
  available;
* new format families can be added by subclassing one ABC each, with no
  changes to the dispatcher.

This is the OOP backbone of the consolidated repository structure. It is
intentionally narrow: each reader/writer subclass owns format-specific logic
and plugs into the registry via ``register_reader`` / ``register_writer``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from pandoc_py.ast import Document


class ReaderError(RuntimeError):
    """Raised when a reader cannot decode its input."""


class WriterError(RuntimeError):
    """Raised when a writer cannot encode the document."""


class UnsupportedFeatureError(ReaderError):
    """Raised when an input form is outside the current admitted slice."""


@dataclass(frozen=True)
class ReadOptions:
    """Per-call reader options. Reserved for future expansion.

    Currently empty by design. Format-specific options should live on the
    concrete Reader subclass, not here, so callers can stay format-agnostic.
    """

    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WriteOptions:
    """Per-call writer options shared by all formats."""

    standalone: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


class Reader(ABC):
    """Abstract base for all format readers.

    Subclasses set the class attribute ``format_name`` and (optionally)
    ``aliases`` and ``binary``.

    A reader produces a ``Document`` from the input source.
    Text-based readers receive a ``str``; binary-container readers receive
    raw ``bytes``.
    """

    format_name: str = ''
    aliases: tuple[str, ...] = ()
    binary: bool = False

    @abstractmethod
    def read(self, source: str | bytes, options: ReadOptions | None = None) -> Document:
        ...

    def __repr__(self) -> str:
        return f'<Reader format={self.format_name!r}>'


class Writer(ABC):
    """Abstract base for all format writers.

    Subclasses set the class attribute ``format_name`` and (optionally)
    ``aliases`` and ``binary``.
    """

    format_name: str = ''
    aliases: tuple[str, ...] = ()
    binary: bool = False

    @abstractmethod
    def write(self, document: Document, options: WriteOptions | None = None) -> str | bytes:
        ...

    def __repr__(self) -> str:
        return f'<Writer format={self.format_name!r}>'
