#!/usr/bin/env python
import sys

from .fpdf import (
    FPDF,
    FPDF_FONT_DIR as _FPDF_FONT_DIR,
    FPDF_VERSION as _FPDF_VERSION,
    SYSTEM_TTFONTS as _SYSTEM_TTFONTS,
)
from .html import HTMLMixin
from .template import Template
from .util.deprecation import WarnOnDeprecatedModuleAttributes

FPDF_VERSION = _FPDF_VERSION
"""Current FPDF Version, also available via `__version__` (which is read by `setup.py`):

<pre>
>>> import fpdf
>>> fpdf.__version__
'2.2.0'
</pre>
"""

FPDF_FONT_DIR = _FPDF_FONT_DIR
"""This is the location of where to look for fonts."""

SYSTEM_TTFONTS = _SYSTEM_TTFONTS
"""This is the directory searched for fonts when a font file path is not given.
"""

sys.modules[__name__].__class__ = WarnOnDeprecatedModuleAttributes

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
    "FPDF_FONT_DIR",
    "SYSTEM_TTFONTS",
]
