"""Format-family implementations beyond the original markdown/html/native/json core.

Each module here implements one Pandoc format family at a constrained slice
admitted in the governed matrix. Importing ``pandoc_py.formats`` ensures
all bundled families self-register with the global FormatRegistry.

Each module is intentionally small. The pattern is:

1. Subclass ``pandoc_py.io.Reader`` and/or ``Writer``.
2. Set ``format_name`` (and ``aliases`` if needed).
3. Implement ``read``/``write`` for the admitted slice; raise
   ``UnsupportedFeatureError`` outside it.
4. Register an instance via ``register_reader`` / ``register_writer``.

The constrained slice for the non-core families covers:

- Document with metadata (title/subtitle/author/date when expressible)
- Paragraphs of inline content
- Headings (levels 1-6)
- Emphasis, strong, code, links (inline + simple)
- Bullet and ordered lists (single-paragraph items)
- Block quotes
- Code blocks (fenced where supported)
- Thematic breaks where supported

Anything beyond this slice is rejected with a clear error and tracked as
known-divergence in the supplement matrix.
"""

from __future__ import annotations

# Import every module so its register_*(...) calls run.
from . import asciidoc        # noqa: F401
from . import bibtex          # noqa: F401
from . import binary          # noqa: F401
from . import creole          # noqa: F401
from . import csljson         # noqa: F401
from . import csv_format      # noqa: F401
from . import djot            # noqa: F401
from . import docbook         # noqa: F401
from . import dokuwiki        # noqa: F401
from . import endnote         # noqa: F401
from . import fb2             # noqa: F401
from . import haddock         # noqa: F401
from . import ipynb           # noqa: F401
from . import jats            # noqa: F401
from . import jira            # noqa: F401
from . import latex           # noqa: F401
from . import man             # noqa: F401
from . import mdoc            # noqa: F401
from . import mediawiki       # noqa: F401
from . import muse            # noqa: F401
from . import opml            # noqa: F401
from . import org             # noqa: F401
from . import pod             # noqa: F401
from . import ris             # noqa: F401
from . import rst             # noqa: F401
from . import rtf             # noqa: F401
from . import textile         # noqa: F401
from . import tikiwiki        # noqa: F401
from . import twiki           # noqa: F401
from . import txt2tags        # noqa: F401
from . import typst           # noqa: F401
from . import vimwiki         # noqa: F401
from . import writer_only     # noqa: F401
from . import xml_format      # noqa: F401
