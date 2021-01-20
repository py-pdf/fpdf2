#!/usr/bin/env python
from .fpdf import (
    FPDF,
    FPDF_CACHE_DIR as _FPDF_CACHE_DIR,
    FPDF_CACHE_MODE as _FPDF_CACHE_MODE,
    FPDF_FONT_DIR as _FPDF_FONT_DIR,
    FPDF_VERSION as _FPDF_VERSION,
    SYSTEM_TTFONTS as _SYSTEM_TTFONTS,
)
from .html import HTMLMixin
from .template import Template

FPDF_VERSION = _FPDF_VERSION
"""Current FPDF Version, also available via `__version__` (which is read by `setup.py`):

<pre>
>>> import fpdf
>>> fpdf.__version__
'2.2.0'
</pre>
"""

FPDF_CACHE_MODE = _FPDF_CACHE_MODE

FPDF_CACHE_DIR = _FPDF_CACHE_DIR
"""This is the directory where pickle files for TTF font files are kept
containing meta-data and stuffs.
"""

FPDF_FONT_DIR = _FPDF_FONT_DIR
"""This is the location of where to look for fonts."""

SYSTEM_TTFONTS = _SYSTEM_TTFONTS
"""This is the directory searched for fonts when a font file path is not given.
"""

__license__ = "LGPL 3.0"

__version__ = FPDF_VERSION


__all__ = [
    # metadata
    "__version__",
    "__license__",
    # Classes
    "FPDF",
    "Template",
    "HTMLMixin",
    # FPDF Constants
    "FPDF_VERSION",
    "FPDF_CACHE_MODE",
    "FPDF_CACHE_DIR",
    "FPDF_FONT_DIR",
    "SYSTEM_TTFONTS",
]
