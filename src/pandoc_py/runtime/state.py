"""PandocState — minimal substitute for the Haskell PandocMonad envelope."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PandocState:
    cwd: Path = field(default_factory=Path.cwd)
    reader_options: dict[str, Any] = field(default_factory=dict)
    writer_options: dict[str, Any] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def log(self, message: str) -> None:
        self.trace.append(message)
