__version__ = '0.0.58'

# Eagerly bootstrap the format registry so `pandoc_py.io.get_reader/get_writer`
# resolves every shipping format without requiring callers to import every
# module separately.
from . import io as _io  # noqa: F401
from .io import bootstrap as _bootstrap  # noqa: F401
from . import formats as _formats  # noqa: F401
