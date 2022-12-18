#!/usr/bin/env python
import sys

from .enums import TextMode, XPos, YPos
from .fpdf import (
    FPDF,
    FPDFException,
    TitleStyle,
    FPDF_FONT_DIR as _FPDF_FONT_DIR,
    FPDF_VERSION as _FPDF_VERSION,
)
from .html import HTMLMixin, HTML2FPDF
from .prefs import ViewerPreferences
from .template import Template, FlexTemplate
from . import svg
from .deprecation import WarnOnDeprecatedModuleAttributes

FPDF_VERSION = _FPDF_VERSION
"Current FPDF Version, also available via `__version__`"

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
    "XPos",
    "YPos",
    "Template",
    "FlexTemplate",
    "TitleStyle",
    "ViewerPreferences",
    "HTMLMixin",
    "HTML2FPDF",
    # FPDF Constants
    "FPDF_VERSION",
    "FPDF_FONT_DIR",
]
