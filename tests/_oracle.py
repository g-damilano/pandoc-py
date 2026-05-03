from __future__ import annotations

import os
import shutil
from pathlib import Path


def resolve_oracle() -> str | None:
    env_oracle = os.environ.get('PANDOC_ORACLE')
    if env_oracle:
        return env_oracle
    if Path('/usr/bin/pandoc').exists():
        return '/usr/bin/pandoc'
    win_default = Path(r'C:\Program Files\Pandoc\pandoc.exe')
    if win_default.exists():
        return str(win_default)
    return shutil.which('pandoc')


def oracle_or_skip():
    import pytest
    oracle = resolve_oracle()
    if oracle is None:
        pytest.skip('No pandoc oracle available on this host (set PANDOC_ORACLE or install pandoc).')
    return oracle
