#!/usr/bin/env python
import sys

from .fpdf import (
    FPDF,
    FPDFException,
    TitleStyle,
    FPDF_FONT_DIR as _FPDF_FONT_DIR,
    FPDF_VERSION as _FPDF_VERSION,
)
from .html import HTMLMixin, HTML2FPDF
from .template import Template, FlexTemplate
from .deprecation import WarnOnDeprecatedModuleAttributes

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
    "FlexTemplate",
    "TitleStyle",
    "HTMLMixin",
    "HTML2FPDF",
    # FPDF Constants
    "FPDF_VERSION",
    "FPDF_FONT_DIR",
]
