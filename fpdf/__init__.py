"""
Root module.
Gives direct access to some classes defined in submodules:

* `fpdf.fpdf.FPDF`
* `fpdf.enums.Align`
* `fpdf.enums.TextMode`
* `fpdf.enums.XPos`
* `fpdf.enums.YPos`
* `fpdf.errors.FPDFException`
* `fpdf.fonts.FontFace`
* `fpdf.fonts.TextStyle`
* `fpdf.prefs.ViewerPreferences`
* `fpdf.template.Template`
* `fpdf.template.FlexTemplate`
"""

import warnings, sys

from .deprecation import WarnOnDeprecatedModuleAttributes
from .enums import Align, TextMode, XPos, YPos
from .errors import FPDFException
from .fonts import FontFace, TextStyle
from .fpdf import (
    FPDF,
    TitleStyle,
    FPDF_FONT_DIR as _FPDF_FONT_DIR,
    FPDF_VERSION as _FPDF_VERSION,
)
from .html import HTMLMixin, HTML2FPDF
from .prefs import ViewerPreferences
from .template import Template, FlexTemplate
from .util import get_scale_factor

try:
    # This module only exists in PyFPDF, it has been removed in fpdf2 since v2.5.7:
    # pylint: disable=import-self
    from . import ttfonts

    warnings.warn(
        "You have both PyFPDF & fpdf2 installed. "
        "Both packages cannot be installed at the same time as they share the same module namespace. "
        "To only keep fpdf2, run: pip uninstall --yes pypdf && pip install --upgrade fpdf2"
    )
except ImportError:
    pass  # no PyFPDF installation detected

FPDF_VERSION = _FPDF_VERSION
"Current fpdf2 version, also available as `__version__`"

FPDF_FONT_DIR = _FPDF_FONT_DIR
"Extra filesystem folder where fpdf2 looks for fonts files, after the current directory"

# Pattern from sir Guido Von Rossum: https://stackoverflow.com/a/72911884/636849
# > a module can define a class with the desired functionality, and then at
# > the end, replace itself in sys.modules with an instance of that class
sys.modules[__name__].__class__ = WarnOnDeprecatedModuleAttributes

__license__ = "LGPL 3.0"

__version__ = FPDF_VERSION

__all__ = [
    # Metadata:
    "__version__",
    "__license__",
    # Classes:
    "FPDF",
    "FPDFException",
    "FontFace",
    "Align",
    "TextMode",
    "XPos",
    "YPos",
    "Template",
    "FlexTemplate",
    "TitleStyle",
    "TextStyle",
    "ViewerPreferences",
    # Deprecated classes:
    "HTMLMixin",
    "HTML2FPDF",
    # FPDF constants:
    "FPDF_VERSION",
    "FPDF_FONT_DIR",
    # Utility functions:
    "get_scale_factor",
]

__pdoc__ = {name: name.startswith("FPDF_") for name in __all__}
