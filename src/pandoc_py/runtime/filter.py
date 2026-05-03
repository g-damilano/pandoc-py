"""JSON filter integration — constrained slice.

Matches the Haskell `pandoc --filter` contract on the JSON surface:

  Document (in pandoc JSON) -> filter binary or callable -> Document (in pandoc JSON)

Two filter shapes are accepted:

  1. A Python callable ``filter(payload: dict) -> dict`` returning the
     transformed Pandoc JSON payload.
  2. A path to an executable: it receives the JSON payload on stdin and is
     expected to write the transformed payload to stdout.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Callable

from pandoc_py.ast import Document
from pandoc_py.readers.pandoc_json import read_pandoc_json
from pandoc_py.writers.pandoc_json import document_to_pandoc_json_payload


FilterCallable = Callable[[dict[str, Any]], dict[str, Any]]


def apply_filter(document: Document, filter_target: FilterCallable | str | Path) -> Document:
    payload = document_to_pandoc_json_payload(document)
    if callable(filter_target):
        new_payload = filter_target(payload)
    else:
        proc = subprocess.run(
            [str(filter_target)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=True,
            encoding='utf-8',
            errors='replace',
        )
        new_payload = json.loads(proc.stdout)
    return read_pandoc_json(json.dumps(new_payload))
