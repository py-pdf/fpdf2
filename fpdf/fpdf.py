#!/usr/bin/env python
# ****************************************************************************
# * Software: FPDF for python                                                *
# * License:  LGPL v3.0+                                                     *
# *                                                                          *
# * Original Author (PHP):  Olivier PLATHEY 2004-12-31                       *
# * Ported to Python 2.4 by Max (maxpat78@yahoo.it) on 2006-05               *
# * Maintainer:  Mariano Reingart (reingart@gmail.com) et al since 2008 est. *
# * Maintainer:  David Alexander (daveankin@gmail.com) et al since 2017 est. *
# * Maintainer:  Lucas Cimon et al since 2021 est.                           *
# ****************************************************************************
"""fpdf module (in fpdf package housing FPDF class)

This module contains FPDF class inspiring this library.
"""

import hashlib
import io
import logging
import math
import os
import re
import sys
import warnings
import zlib
from collections import OrderedDict, defaultdict
from collections.abc import Sequence
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import wraps
from math import isclose
from os.path import splitext
from pathlib import Path
from typing import Callable, List, NamedTuple, Optional, Tuple, Union
from fontTools import ttLib
from fontTools import subset as ftsubset
from io import BytesIO

try:
    from PIL.Image import Image
except ImportError:
    warnings.warn(
        "Pillow could not be imported - fpdf2 will not be able to add any image"
    )

    class Image:
        pass


try:
    from endesive import signer
    from cryptography.hazmat.primitives.serialization import pkcs12
except ImportError:
    signer = False

from . import drawing
from .actions import Action
from .deprecation import WarnOnDeprecatedModuleAttributes
from .enums import (
    Align,
    AnnotationName,
    AnnotationFlag,
    DocumentState,
    PageLayout,
    PageMode,
    PathPaintRule,
    RenderStyle,
    SignatureFlag,
    TextMarkupType,
    TextMode,
    XPos,
    YPos,
    Corner,
    FontDescriptorFlags,
)
from .errors import FPDFException, FPDFPageFormatException, FPDFUnicodeEncodingException
from .fonts import fpdf_charwidths
from .graphics_state import GraphicsStateMixin
from .image_parsing import SUPPORTED_IMAGE_FILTERS, get_img_info, load_image
from .line_break import Fragment, MultiLineBreak, TextLine
from .outline import OutlineSection, serialize_outline
from .recorder import FPDFRecorder
from .structure_tree import MarkedContent, StructureTreeBuilder
from .sign import Signature, sign_content
from .svg import Percent, SVGObject
from .syntax import DestinationXYZ
from .syntax import create_dictionary_string as pdf_dict
from .syntax import create_list_string as pdf_list
from .syntax import create_stream as pdf_stream
from .syntax import iobj_ref as pdf_ref
from .util import (
    enclose_in_parens,
    escape_parens,
    format_date,
    get_scale_factor,
    object_id_for_page,
    substr,
)

# Public global variables:
FPDF_VERSION = "2.5.6"
PAGE_FORMATS = {
    "a3": (841.89, 1190.55),
    "a4": (595.28, 841.89),
    "a5": (420.94, 595.28),
    "letter": (612, 792),
    "legal": (612, 1008),
}
"Supported page format names & dimensions"

# Private global variables:
LOGGER = logging.getLogger(__name__)
HERE = Path(__file__).resolve().parent
FPDF_FONT_DIR = HERE / "font"
LAYOUT_ALIASES = {
    "default": None,
    "single": PageLayout.SINGLE_PAGE,
    "continuous": PageLayout.ONE_COLUMN,
    "two": PageLayout.TWO_COLUMN_LEFT,
}
ZOOM_CONFIGS = {  # cf. section 8.2.1 "Destinations" of the 2006 PDF spec 1.7:
    "fullpage": ("/Fit",),
    "fullwidth": ("/FitH", "null"),
    "real": ("/XYZ", "null", "null", "1"),
}

# cf. https://docs.verapdf.org/validation/pdfa-part1/#rule-653-2
DEFAULT_ANNOT_FLAGS = (AnnotationFlag.PRINT,)


class Annotation(NamedTuple):
    type: str
    x: int
    y: int
    width: int
    height: int
    flags: Tuple[AnnotationFlag] = DEFAULT_ANNOT_FLAGS
    contents: str = None
    link: Union[str, int] = None
    alt_text: Optional[str] = None
    action: Optional[Action] = None
    color: Optional[int] = None
    modification_time: Optional[datetime] = None
    title: Optional[str] = None
    quad_points: Optional[tuple] = None
    page: Optional[int] = None
    border_width: int = 0  # PDF readers support: displayed by Acrobat but not Sumatra
    name: Optional[AnnotationName] = None  # for text annotations
    ink_list: Tuple[int] = ()  # for ink annotations
    field_type: Optional[str] = None
    value: Optional[str] = None

    def serialize(self, fpdf):
        "Convert this object dictionnary to a string"
        rect = (
            f"{self.x:.2f} {self.y:.2f} "
            f"{self.x + self.width:.2f} {self.y - self.height:.2f}"
        )

        out = (
            f"<</Type /Annot /Subtype /{self.type}"
            f" /Rect [{rect}] /Border [0 0 {self.border_width}]"
        )

        if self.field_type:
            out += f" /FT /{self.field_type}"

        if self.value:
            out += f" /V {self.value.serialize()}"

        if self.flags:
            out += f" /F {sum(self.flags)}"

        if self.contents:
            out += f" /Contents {enclose_in_parens(self.contents)}"

        if self.action:
            out += f" /A {self.action.dict_as_string()}"

        if self.link:
            if isinstance(self.link, str):
                out += f" /A <</S /URI /URI {enclose_in_parens(self.link)}>>"
            else:  # Dest type ending of annotation entry
                assert (
                    self.link in fpdf.links
                ), f"Link with an invalid index: {self.link} (doc #links={len(fpdf.links)})"
                out += f" /Dest {fpdf.links[self.link].as_str(fpdf)}"

        if self.color:
            # pylint: disable=unsubscriptable-object
            out += f" /C [{self.color[0]} {self.color[1]} {self.color[2]}]"

        if self.title:
            out += f" /T ({escape_parens(self.title)})"

        if self.modification_time:
            out += f" /M {format_date(self.modification_time)}"

        if self.quad_points:
            # pylint: disable=not-an-iterable
            quad_points = pdf_list(
                f"{quad_point:.2f}" for quad_point in self.quad_points
            )
            out += f" /QuadPoints {quad_points}"

        if self.page:
            out += f" /P {pdf_ref(object_id_for_page(self.page))}"

        if self.name:
            out += f" /Name {self.name.value.pdf_repr()}"

        if self.ink_list:
            ink_list = pdf_list(f"{coord:.2f}" for coord in self.ink_list)
            out += f" /InkList [{ink_list}]"

        return out + ">>"


class TitleStyle(NamedTuple):
    font_family: Optional[str] = None
    font_style: Optional[str] = None
    font_size_pt: Optional[int] = None
    color: Union[int, tuple] = None  # grey scale or (red, green, blue)
    underline: bool = False
    t_margin: Optional[int] = None
    l_margin: Optional[int] = None
    b_margin: Optional[int] = None


class ToCPlaceholder(NamedTuple):
    render_function: Callable
    start_page: int
    y: int
    pages: int = 1


class SubsetMap:
    """Holds a mapping of used characters and their position in the font's subset

    Characters that must be mapped on their actual unicode must be part of the
    `identities` list during object instanciation. These non-negative values should
    only appear once in the list. `pick()` can be used to get the characters
    corresponding position in the subset. If it's not yet part of the object, a new
    position is acquired automatically. This implementation always tries to return
    the lowest possible representation.
    """

    def __init__(self, identities: List[int]):
        super().__init__()
        self._next = 0

        # sort list to ease deletion once _next
        # becomes higher than first reservation
        self._reserved = sorted(identities)

        # int(x) to ensure values are integers
        self._map = {x: int(x) for x in self._reserved}

    def pick(self, unicode: int):
        if not unicode in self._map:
            while self._next in self._reserved:
                self._next += 1
                if self._next > self._reserved[0]:
                    del self._reserved[0]

            self._map[unicode] = self._next
            self._next += 1

        return self._map.get(unicode)

    def dict(self):
        return self._map.copy()


# Disabling this check due to the "format" parameter below:
# pylint: disable=redefined-builtin
def get_page_format(format, k=None):
    """Return page width and height size in points.

    Throws FPDFPageFormatException

    `format` can be either a 2-tuple or one of 'a3', 'a4', 'a5', 'letter', or
    'legal'.

    If format is a tuple, then the return value is the tuple's values
    given in the units specified on this document in the constructor,
    multiplied by the corresponding scale factor `k`, taken from instance
    variable `self.k`.

    If format is a string, the (width, height) tuple returned is in points.
    For a width and height of 8.5 * 11, 72 dpi is assumed, so the value
    returned is (8.5 * 72, 11 * 72), or (612, 792). Additional formats can be
    added by adding fields to the `PAGE_FORMATS` dictionary with a
    case insensitive key (the name of the new format) and 2-tuple value of
    (width, height) in dots per inch with a 72 dpi resolution.
    """
    if isinstance(format, str):
        format = format.lower()
        if format in PAGE_FORMATS:
            return PAGE_FORMATS[format]
        raise FPDFPageFormatException(format, unknown=True)

    if k is None:
        raise FPDFPageFormatException(format, one=True)

    try:
        return format[0] * k, format[1] * k
    except Exception as e:
        args = f"{format}, {k}"
        raise FPDFPageFormatException(f"Arguments must be numbers: {args}") from e


def check_page(fn):
    """Decorator to protect drawing methods"""

    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        if not self.page and not kwargs.get("split_only"):
            raise FPDFException("No page open, you need to call add_page() first")
        return fn(self, *args, **kwargs)

    return wrapper


class FPDF(GraphicsStateMixin):
    "PDF Generation class"
    MARKDOWN_BOLD_MARKER = "**"
    MARKDOWN_ITALICS_MARKER = "__"
    MARKDOWN_UNDERLINE_MARKER = "--"

    def __init__(
        self,
        orientation="portrait",
        unit="mm",
        format="A4",
        font_cache_dir="DEPRECATED",
    ):
        """
        Args:
            orientation (str): possible values are "portrait" (can be abbreviated "P")
                or "landscape" (can be abbreviated "L"). Default to "portrait".
            unit (str, int, float): possible values are "pt", "mm", "cm", "in", or a number.
                A point equals 1/72 of an inch, that is to say about 0.35 mm (an inch being 2.54 cm).
                This is a very common unit in typography; font sizes are expressed in this unit.
                If given a number, then it will be treated as the number of points per unit.  (eg. 72 = 1 in)
                Default to "mm".
            format (str): possible values are "a3", "a4", "a5", "letter", "legal" or a tuple
                (width, height) expressed in the given unit. Default to "a4".
            font_cache_dir (Path or str): [**DEPRECATED since v2.5.1**] unused
        """
        if font_cache_dir != "DEPRECATED":
            warnings.warn(
                '"font_cache_dir" parameter is deprecated, unused and will soon be removed',
                DeprecationWarning,
                stacklevel=2,
            )
        super().__init__()
        # Initialization of instance attributes
        self.offsets = {}  # array of object offsets
        self.page = 0  # current page number
        self.n = 2  # current object number
        self.buffer = bytearray()  # buffer holding in-memory PDF
        # Associative array from page number to dicts containing pages and metadata:
        self.pages = {}
        self.state = DocumentState.UNINITIALIZED  # current document state
        self.fonts = {}  # array of used fonts
        self.font_files = {}  # array of font files
        self.diffs = {}  # array of encoding differences
        self.images = {}  # array of used images
        self.annots = defaultdict(
            list
        )  # map page numbers to a list of Annotations; they will be inlined in the Page object
        self.annots_as_obj = defaultdict(
            list
        )  # map page numbers to a list of pairs (Annotations, obj_id); they will be embedded in the doc as separated objects
        self.links = {}  # array of Destination
        self.in_footer = 0  # flag set when processing footer
        self.lasth = 0  # height of last cell printed
        self.str_alias_nb_pages = "{nb}"

        self.ws = 0  # word spacing
        self.angle = 0  # used by deprecated method: rotate()
        self.xmp_metadata = None
        self.image_filter = "AUTO"
        self.page_duration = 0  # optional pages display duration, cf. add_page()
        self.page_transition = None  # optional pages transition, cf. add_page()
        self.allow_images_transparency = True
        # Do nothing by default. Allowed values: 'WARN', 'DOWNSCALE':
        self.oversized_images = None
        self.oversized_images_ratio = 2  # number of pixels per UserSpace point
        # Only set if XMP metadata is added to the document:
        self._xmp_metadata_obj_id = None
        self.struct_builder = StructureTreeBuilder()
        self._struct_parents_id_per_page = {}  # {page_object_id -> StructParent(s) ID}
        # Only set if a Structure Tree is added to the document:
        self._struct_tree_root_obj_id = None
        self._outlines_obj_id = None
        self._toc_placeholder = None  # ToCPlaceholder
        self._outline = []  # list of OutlineSection
        self._sign_key = None
        self.section_title_styles = {}  # level -> TitleStyle

        # Standard fonts
        self.core_fonts = {
            "courier": "Courier",
            "courierB": "Courier-Bold",
            "courierI": "Courier-Oblique",
            "courierBI": "Courier-BoldOblique",
            "helvetica": "Helvetica",
            "helveticaB": "Helvetica-Bold",
            "helveticaI": "Helvetica-Oblique",
            "helveticaBI": "Helvetica-BoldOblique",
            "times": "Times-Roman",
            "timesB": "Times-Bold",
            "timesI": "Times-Italic",
            "timesBI": "Times-BoldItalic",
            "symbol": "Symbol",
            "zapfdingbats": "ZapfDingbats",
        }
        self.core_fonts_encoding = "latin-1"
        "Font encoding, Latin-1 by default"
        # Replace these fonts with these core fonts
        self.font_aliases = {
            "arial": "helvetica",
            "couriernew": "courier",
            "timesnewroman": "times",
        }
        # Scale factor
        self.k = get_scale_factor(unit)

        # Graphics state variables defined as properties by GraphicsStateMixin.
        # We set their default values here.
        self.font_family = ""  # current font family
        self.font_style = ""  # current font style
        self.font_size_pt = 12
        self.font_stretching = 100  # current font stretching
        self.underline = 0  # underlining flag
        self.current_font = {}  # current font
        self.draw_color = self.DEFAULT_DRAW_COLOR
        self.fill_color = self.DEFAULT_FILL_COLOR
        self.text_color = self.DEFAULT_TEXT_COLOR
        self.page_background = None
        self.dash_pattern = dict(dash=0, gap=0, phase=0)
        self.line_width = 0.567 / self.k  # line width (0.2 mm)
        self.text_mode = TextMode.FILL
        # end of grapics state variables

        self.dw_pt, self.dh_pt = get_page_format(format, self.k)
        self._set_orientation(orientation, self.dw_pt, self.dh_pt)
        self.def_orientation = self.cur_orientation
        # Page spacing
        # Page margins (1 cm)
        margin = (7200 / 254) / self.k
        self.x, self.y, self.l_margin, self.t_margin = 0, 0, 0, 0
        self.set_margins(margin, margin)
        self.x, self.y = self.l_margin, self.t_margin
        self.c_margin = margin / 10.0  # Interior cell margin (1 mm)
        # sets self.auto_page_break, self.b_margin & self.page_break_trigger:
        self.set_auto_page_break(True, 2 * margin)
        self.set_display_mode("fullwidth")  # Full width display mode
        self._page_mode = None
        self.viewer_preferences = None
        self.compress = True  # Enable compression by default
        self.pdf_version = "1.3"  # Set default PDF version No.
        self.creation_date = datetime.now(timezone.utc)

        self._current_draw_context = None
        self._drawing_graphics_state_registry = drawing.GraphicsStateDictRegistry()
        self._graphics_state_obj_refs = OrderedDict()

        self.record_text_quad_points = False
        # page number -> array of 8 × n numbers:
        self.text_quad_points = defaultdict(list)

    def _set_min_pdf_version(self, version):
        self.pdf_version = max(self.pdf_version, version)

    @property
    def unifontsubset(self):
        return self.current_font.get("type") == "TTF"

    @property
    def page_mode(self):
        return self._page_mode

    @page_mode.setter
    def page_mode(self, page_mode):
        self._page_mode = PageMode.coerce(page_mode)

    @property
    def epw(self):
        """
        Effective page width: the page width minus its horizontal margins.
        """
        return self.w - self.l_margin - self.r_margin

    @property
    def eph(self):
        """
        Effective page height: the page height minus its vertical margins.
        """
        return self.h - self.t_margin - self.b_margin

    @property
    def pages_count(self):
        """
        Returns the total pages of the document.
        """
        return len(self.pages)

    def set_margin(self, margin):
        """
        Sets the document right, left, top & bottom margins to the same value.

        Args:
            margin (float): margin in the unit specified to FPDF constructor
        """
        self.set_margins(margin, margin)
        self.set_auto_page_break(self.auto_page_break, margin)

    def set_margins(self, left, top, right=-1):
        """
        Sets the document left, top & optionaly right margins to the same value.
        By default, they equal 1 cm.
        Also sets the current FPDF.y on the page to this minimum vertical position.

        Args:
            left (float): left margin in the unit specified to FPDF constructor
            top (float): top margin in the unit specified to FPDF constructor
            right (float): optional right margin in the unit specified to FPDF constructor
        """
        self.set_left_margin(left)
        if self.y < top or self.y == self.t_margin:
            self.y = top
        self.t_margin = top
        if right == -1:
            right = left
        self.r_margin = right

    def set_left_margin(self, margin):
        """
        Sets the document left margin.
        Also sets the current FPDF.x on the page to this minimum horizontal position.

        Args:
            margin (float): margin in the unit specified to FPDF constructor
        """
        if self.x < margin or self.x == self.l_margin:
            self.x = margin
        self.l_margin = margin

    def set_top_margin(self, margin):
        """
        Sets the document top margin.

        Args:
            margin (float): margin in the unit specified to FPDF constructor
        """
        self.t_margin = margin

    def set_right_margin(self, margin):
        """
        Sets the document right margin.

        Args:
            margin (float): margin in the unit specified to FPDF constructor
        """
        self.r_margin = margin

    def set_auto_page_break(self, auto, margin=0):
        """
        Set auto page break mode and triggering bottom margin.
        By default, the mode is on and the bottom margin is 2 cm.

        Args:
            auto (bool): enable or disable this mode
            margin (float): optional bottom margin (distance from the bottom of the page)
                in the unit specified to FPDF constructor
        """
        self.auto_page_break = auto
        self.b_margin = margin
        self.page_break_trigger = self.h - self.b_margin

    def _set_orientation(self, orientation, page_width_pt, page_height_pt):
        orientation = orientation.lower()
        if orientation in ("p", "portrait"):
            self.cur_orientation = "P"
            self.w_pt = page_width_pt
            self.h_pt = page_height_pt
        elif orientation in ("l", "landscape"):
            self.cur_orientation = "L"
            self.w_pt = page_height_pt
            self.h_pt = page_width_pt
        else:
            raise FPDFException(f"Incorrect orientation: {orientation}")
        self.w = self.w_pt / self.k
        self.h = self.h_pt / self.k

    def set_display_mode(self, zoom, layout="continuous"):
        """
        Defines the way the document is to be displayed by the viewer.

        It allows to set the zoom level: pages can be displayed entirely on screen,
        occupy the full width of the window, use the real size,
        be scaled by a specific zooming factor or use the viewer default (configured in its Preferences menu).

        The page layout can also be specified: single page at a time, continuous display, two columns or viewer default.

        Args:
            zoom: either "fullpage", "fullwidth", "real", "default",
                or a number indicating the zooming factor to use, interpreted as a percentage.
                The zoom level set by default is "default".
            layout (fpdf.enums.PageLayout, str): allowed layout aliases are "single", "continuous", "two" or "default",
                meaning to use the viewer default mode.
                The layout set by default is "continuous".
        """
        if zoom in ZOOM_CONFIGS or not isinstance(zoom, str):
            self.zoom_mode = zoom
        elif zoom != "default":
            raise FPDFException(f"Incorrect zoom display mode: {zoom}")

        if layout in LAYOUT_ALIASES:
            self.page_layout = LAYOUT_ALIASES[layout]
        else:
            self.page_layout = PageLayout.coerce(layout)

    def set_compression(self, compress):
        """
        Activates or deactivates page compression.

        When activated, the internal representation of each page is compressed
        using the zlib/deflate method (FlateDecode), which leads to a compression ratio
        of about 2 for the resulting document.

        Page compression is enabled by default.

        Args:
            compress (bool): indicates if compression should be enabled
        """
        self.compress = compress

    def set_title(self, title):
        """
        Defines the title of the document.

        Args:
            title (str): the title
        """
        self.title = title

    def set_lang(self, lang):
        """
        A language identifier specifying the natural language for all text in the document
        except where overridden by language specifications for structure elements or marked content.
        A language identifier can either be the empty text string, to indicate that the language is unknown,
        or a Language-Tag as defined in RFC 3066, "Tags for the Identification of Languages".

        Args:
            lang (str): the document main language
        """
        self.lang = lang
        if lang:
            self._set_min_pdf_version("1.4")

    def set_subject(self, subject):
        """
        Defines the subject of the document.

        Args:
            subject (str): the document main subject
        """
        self.subject = subject

    def set_author(self, author):
        """
        Defines the author of the document.

        Args:
            author(str): the name of the author
        """
        self.author = author

    def set_keywords(self, keywords):
        """
        Associate keywords with the document

        Args:
            keywords (str): a space-separated list of words
        """
        self.keywords = keywords

    def set_creator(self, creator):
        """
        Defines the creator of the document.
        This is typically the name of the application that generates the PDF.

        Args:
            creator (str): name of the PDF creator
        """
        self.creator = creator

    def set_producer(self, producer):
        """Producer of document"""
        self.producer = producer

    def set_creation_date(self, date=None):
        """Sets Creation of Date time, or current time if None given."""
        if self._sign_key:
            raise FPDFException(
                ".set_creation_date() must always be called before .sign*() methods"
            )
        self.creation_date = date

    def set_xmp_metadata(self, xmp_metadata):
        if "<?xpacket" in xmp_metadata[:50]:
            raise ValueError(
                "fpdf2 already performs XMP metadata wrapping in a <?xpacket> tag"
            )
        self.xmp_metadata = xmp_metadata
        if xmp_metadata:
            self._set_min_pdf_version("1.4")

    def set_doc_option(self, opt, value):
        """
        Defines a document option.

        Args:
            opt (str): name of the option to set
            value (str) option value

        .. deprecated:: 2.4.0
            Simply set the `FPDF.core_fonts_encoding` property as a replacement.
        """
        warnings.warn(
            "set_doc_option() is deprecated. "
            "Simply set the `.core_fonts_encoding` property as a replacement.",
            DeprecationWarning,
            stacklevel=2,
        )
        if opt != "core_fonts_encoding":
            raise FPDFException(f'Unknown document option "{opt}"')
        self.core_fonts_encoding = value

    def set_image_filter(self, image_filter):
        """
        Args:
            image_filter (str): name of a support image filter or "AUTO",
                meaning to use the best image filter given the images provided.
        """
        if image_filter not in SUPPORTED_IMAGE_FILTERS:
            raise ValueError(
                f"'{image_filter}' is not a supported image filter: {''.join(SUPPORTED_IMAGE_FILTERS)}"
            )
        self.image_filter = image_filter
        if image_filter == "JPXDecode":
            self._set_min_pdf_version("1.5")

    def alias_nb_pages(self, alias="{nb}"):
        """
        Defines an alias for the total number of pages.
        It will be substituted as the document is closed.

        This is useful to insert the number of pages of the document
        at a time when this number is not known by the program.

        This substitution can be disabled for performances reasons, by calling `alias_nb_pages(None)`.

        Args:
            alias (str): the alias. Defaults to "{nb}".

        Notes
        -----

        When using this feature with the `FPDF.cell` / `FPDF.multi_cell` methods,
        or the `.underline` attribute of `FPDF` class,
        the width of the text rendered will take into account the alias length,
        not the length of the "actual number of pages" string,
        which can causes slight positioning differences.
        """
        self.str_alias_nb_pages = alias

    def open(self):
        """
        Starts the generation of the PDF document.
        It is not necessary to call it explicitly because `FPDF.add_page()` does it automatically.

        Notes
        -----

        This method does not add any page.
        """
        self.state = DocumentState.READY

    def close(self):
        """
        Terminates the PDF document.

        It is not necessary to call this method explicitly because `FPDF.output()` does it automatically.
        If the document contains no page, `FPDF.add_page()` is called to prevent from generating an invalid document.
        """
        if self.state == DocumentState.CLOSED:
            return
        if self.page == 0:
            self.add_page()

        # Page footer
        self.in_footer = 1
        self.footer()
        self.in_footer = 0

        self._endpage()  # close page
        self._enddoc()  # close document

    def add_page(
        self, orientation="", format="", same=False, duration=0, transition=None
    ):
        """
        Adds a new page to the document.
        If a page is already present, the `FPDF.footer()` method is called first.
        Then the page  is added, the current position is set to the top-left corner,
        with respect to the left and top margins, and the `FPDF.header()` method is called.

        Args:
            orientation (str): "portrait" (can be abbreviated "P")
                or "landscape" (can be abbreviated "L"). Default to "portrait".
            format (str): "a3", "a4", "a5", "letter", "legal" or a tuple
                (width, height). Default to "a4".
            same (bool): indicates to use the same page format as the previous page.
                Default to False.
            duration (float): optional page’s display duration, i.e. the maximum length of time,
                in seconds, that the page is displayed in presentation mode,
                before the viewer application automatically advances to the next page.
                Can be configured globally through the `.page_duration` FPDF property.
                As of june 2021, onored by Adobe Acrobat reader, but ignored by Sumatra PDF reader.
            transition (Transition child class): optional visual transition to use when moving
                from another page to the given page during a presentation.
                Can be configured globally through the `.page_transition` FPDF property.
                As of june 2021, onored by Adobe Acrobat reader, but ignored by Sumatra PDF reader.
        """
        if self.state == DocumentState.CLOSED:
            raise FPDFException(
                "A page cannot be added on a closed document, after calling output()"
            )
        if self.state == DocumentState.UNINITIALIZED:
            self.open()

        family = self.font_family
        style = f"{self.font_style}U" if self.underline else self.font_style
        size = self.font_size_pt
        lw = self.line_width
        dc = self.draw_color
        fc = self.fill_color
        tc = self.text_color
        stretching = self.font_stretching

        if self.page > 0:
            # Page footer
            self.in_footer = 1
            self.footer()
            self.in_footer = 0
            # close page
            self._endpage()

        # Start new page
        self._beginpage(
            orientation,
            format,
            same,
            duration or self.page_duration,
            transition or self.page_transition,
            new_page=not self._has_next_page(),
        )

        if self.page_background:
            if isinstance(self.page_background, tuple):
                self.set_fill_color(*self.page_background)
                self.rect(0, 0, self.w, self.h, style="F")
                self.set_fill_color(*(255 * v for v in fc.colors))
            else:
                self.image(self.page_background, 0, 0, self.w, self.h)

        self._out("2 J")  # Set line cap style to square
        self.line_width = lw  # Set line width
        self._out(f"{lw * self.k:.2f} w")

        # Set font
        if family:
            self.set_font(family, style, size)

        # Set colors
        self.draw_color = dc
        if dc != self.DEFAULT_DRAW_COLOR:
            self._out(dc.pdf_repr().upper())
        self.fill_color = fc
        if fc != self.DEFAULT_FILL_COLOR:
            self._out(fc.pdf_repr().lower())
        self.text_color = tc

        # BEGIN Page header
        self.header()

        if self.line_width != lw:  # Restore line width
            self.line_width = lw
            self._out(f"{lw * self.k:.2f} w")

        if family:
            self.set_font(family, style, size)  # Restore font

        if self.draw_color != dc:  # Restore colors
            self.draw_color = dc
            self._out(dc.pdf_repr().upper())
        if self.fill_color != fc:
            self.fill_color = fc
            self._out(fc.pdf_repr().lower())
        self.text_color = tc

        if stretching != 100:  # Restore stretching
            self.set_stretching(stretching)
        # END Page header

    def header(self):
        """
        Header to be implemented in your own inherited class

        This is automatically called by `FPDF.add_page()`
        and should not be called directly by the user application.
        The default implementation performs nothing: you have to override this method
        in a subclass to implement your own rendering logic.
        """

    def footer(self):
        """
        Footer to be implemented in your own inherited class.

        This is automatically called by `FPDF.add_page()` and `FPDF.close()`
        and should not be called directly by the user application.
        The default implementation performs nothing: you have to override this method
        in a subclass to implement your own rendering logic.
        """

    def page_no(self):
        """Get the current page number"""
        return self.page

    def set_draw_color(self, r, g=-1, b=-1):
        """
        Defines the color used for all stroking operations (lines, rectangles and cell borders).
        It can be expressed in RGB components or grey scale.
        The method can be called before the first page is created and the value is retained from page to page.

        Args:
            r (int): if `g` and `b` are given, this indicates the red component.
                Else, this indicates the grey level. The value must be between 0 and 255.
            g (int): green component (between 0 and 255)
            b (int): blue component (between 0 and 255)
        """
        if (r == 0 and g == 0 and b == 0) or g == -1:
            self.draw_color = drawing.DeviceGray(r / 255)
        else:
            self.draw_color = drawing.DeviceRGB(r / 255, g / 255, b / 255)
        if self.page > 0:
            self._out(self.draw_color.pdf_repr().upper())

    def set_fill_color(self, r, g=-1, b=-1):
        """
        Defines the color used for all filling operations (filled rectangles and cell backgrounds).
        It can be expressed in RGB components or grey scale.
        The method can be called before the first page is created and the value is retained from page to page.

        Args:
            r (int): if `g` and `b` are given, this indicates the red component.
                Else, this indicates the grey level. The value must be between 0 and 255.
            g (int): green component (between 0 and 255)
            b (int): blue component (between 0 and 255)
        """
        if (r == 0 and g == 0 and b == 0) or g == -1:
            self.fill_color = drawing.DeviceGray(r / 255)
        else:
            self.fill_color = drawing.DeviceRGB(r / 255, g / 255, b / 255)
        if self.page > 0:
            self._out(self.fill_color.pdf_repr().lower())

    def set_text_color(self, r, g=-1, b=-1):
        """
        Defines the color used for text.
        It can be expressed in RGB components or grey scale.
        The method can be called before the first page is created and the value is retained from page to page.

        Args:
            r (int): if `g` and `b` are given, this indicates the red component.
                Else, this indicates the grey level. The value must be between 0 and 255.
            g (int): green component (between 0 and 255)
            b (int): blue component (between 0 and 255)
        """
        if (r == 0 and g == 0 and b == 0) or g == -1:
            self.text_color = drawing.DeviceGray(r / 255)
        else:
            self.text_color = drawing.DeviceRGB(r / 255, g / 255, b / 255)

    def get_string_width(self, s, normalized=False, markdown=False):
        """
        Returns the length of a string in user unit. A font must be selected.
        The value is calculated with stretching and spacing.

        Args:
            s (str): the string whose length is to be computed.
            normalized (bool): whether normalization needs to be performed on the input string.
            markdown (bool): indicates if basic markdown support is enabled
        """
        # normalized is parameter for internal use
        s = s if normalized else self.normalize_text(s)
        w = 0
        for frag in (
            self._markdown_parse(s)
            if markdown
            else (Fragment.from_string(s, self.font_style, bool(self.underline)),)
        ):
            w += self.get_normalized_string_width_with_style(frag.string, frag.style)
        if self.font_stretching != 100:
            w *= self.font_stretching / 100
        return w * self.font_size / 1000

    def get_normalized_string_width_with_style(self, string, style):
        """
        Returns the length of a string with given style

        Args:
            string (str): the string whose length is to be computed.
            style (str) : the string representing the style
        """
        w = 0
        font = self.fonts[self.font_family + style]
        if self.unifontsubset:
            for char in string:
                w += _char_width(font, ord(char))
        else:
            w += sum(_char_width(font, char) for char in string)
        return w

    def set_line_width(self, width):
        """
        Defines the line width of all stroking operations (lines, rectangles and cell borders).
        By default, the value equals 0.2 mm.
        The method can be called before the first page is created and the value is retained from page to page.

        Args:
            width (float): the width in user unit
        """
        self.line_width = width
        if self.page > 0:
            self._out(f"{width * self.k:.2f} w")

    def set_page_background(self, background):
        """
        Sets a background color or image to be drawn every time `FPDF.add_page()` is called, or removes a previously set background.
        The method can be called before the first page is created and the value is retained from page to page.

        Args:
            background: either a string representing a file path or URL to an image,
                an io.BytesIO containg an image as bytes, an instance of `PIL.Image.Image`, drawing.DeviceRGB
                or a RGB tuple representing a color to fill the background with or `None` to remove the background
        """

        if isinstance(
            background, (str, io.BytesIO, Image, drawing.DeviceRGB, tuple, type(None))
        ):
            if isinstance(background, drawing.DeviceRGB):
                self.page_background = tuple(255 * v for v in background.colors)
            else:
                self.page_background = background
        else:
            raise TypeError(
                f"""background must be of type str, io.BytesIO, PIL.Image.Image, drawing.DeviceRGB, tuple or None
        got: {type(background)}"""
            )

    @contextmanager
    @check_page
    def drawing_context(self, debug_stream=None):
        """
        Create a context for drawing paths on the current page.

        If this context manager is called again inside of an active context, it will
        raise an exception, as base drawing contexts cannot be nested.

        Args:
            debug_stream (TextIO): print a pretty tree of all items to be rendered
                to the provided stream. To store the output in a string, use
                `io.StringIO`.
        """

        if self._current_draw_context is not None:
            raise FPDFException(
                "cannot create a drawing context while one is already open"
            )

        context = drawing.DrawingContext()
        self._current_draw_context = context
        try:
            yield context
        finally:
            self._current_draw_context = None

        starting_style = self._current_graphic_style()
        render_args = (
            self._drawing_graphics_state_registry,
            drawing.Point(self.x, self.y),
            self.k,
            self.h,
            starting_style,
        )

        if debug_stream:
            rendered = context.render_debug(*render_args, debug_stream)
        else:
            rendered = context.render(*render_args)

        self._out(rendered)
        # The drawing API makes use of features (notably transparency and blending modes) that were introduced in PDF 1.4:
        self._set_min_pdf_version("1.4")

    def _current_graphic_style(self):
        gs = drawing.GraphicsStyle()
        gs.allow_transparency = self.allow_images_transparency

        # This initial stroke_width is ignored when embedding SVGs,
        # as the value in SVGObject.convert_graphics() takes precedence,
        # so this probably creates an unnecessary PDF dict entry:
        gs.stroke_width = self.line_width

        if self.draw_color != self.DEFAULT_DRAW_COLOR:
            gs.stroke_color = self.draw_color
        if self.fill_color != self.DEFAULT_FILL_COLOR:
            gs.fill_color = self.fill_color

        dash_info = self.dash_pattern
        dash_pattern = (dash_info["dash"], dash_info["gap"])
        if (dash_pattern[0] == 0) or (dash_pattern[1] == 0):
            dash_pattern = None

        gs.stroke_dash_pattern = dash_pattern
        gs.stroke_dash_phase = dash_info["phase"]

        return gs

    @contextmanager
    def new_path(self, x=0, y=0, paint_rule=PathPaintRule.AUTO, debug_stream=None):
        """
        Create a path for appending lines and curves to.

        Args:
            x (float): Abscissa of the path starting point
            y (float): Ordinate of the path starting point
            paint_rule (PathPaintRule): Optional choice of how the path should
                be painted. The default (AUTO) automatically selects stroke/fill based
                on the path style settings.
            debug_stream (TextIO): print a pretty tree of all items to be rendered
                to the provided stream. To store the output in a string, use
                `io.StringIO`.

        """
        with self.drawing_context(debug_stream=debug_stream) as ctxt:
            path = drawing.PaintedPath(x=x, y=y)
            path.style.paint_rule = paint_rule
            yield path
            ctxt.add_item(path)

    def draw_path(self, path, debug_stream=None):
        """
        Add a pre-constructed path to the document.

        Args:
            path (drawing.PaintedPath): the path to be drawn.
            debug_stream (TextIO): print a pretty tree of all items to be rendered
                to the provided stream. To store the output in a string, use
                `io.StringIO`.
        """
        with self.drawing_context(debug_stream=debug_stream) as ctxt:
            ctxt.add_item(path)

    def set_dash_pattern(self, dash=0, gap=0, phase=0):
        """
        Set the current dash pattern for lines and curves.

        Args:
            dash (float >= 0):
                The length of the dashes in current units.

            gap (float >= 0):
                The length of the gaps between dashes in current units.
                If omitted, the dash length will be used.

            phase (float >= 0):
                Where in the sequence to start drawing.

        Omitting 'dash' (= 0) resets the pattern to a solid line.
        """
        if not (isinstance(dash, (int, float)) and dash >= 0):
            raise ValueError("Dash length must be zero or a positive number.")
        if not (isinstance(gap, (int, float)) and gap >= 0):
            raise ValueError("gap length must be zero or a positive number.")
        if not (isinstance(phase, (int, float)) and phase >= 0):
            raise ValueError("Phase must be zero or a positive number.")

        pattern = dict(dash=dash, gap=gap, phase=phase)

        if pattern != self.dash_pattern:
            self.dash_pattern = pattern

            if dash:
                if gap:
                    dstr = f"[{dash * self.k:.3f} {gap * self.k:.3f}] {phase *self.k:.3f} d"
                else:
                    dstr = f"[{dash * self.k:.3f}] {phase *self.k:.3f} d"
            else:
                dstr = "[] 0 d"

            self._out(dstr)

    @check_page
    def line(self, x1, y1, x2, y2):
        """
        Draw a line between two points.

        Args:
            x1 (float): Abscissa of first point
            y1 (float): Ordinate of first point
            x2 (float): Abscissa of second point
            y2 (float): Ordinate of second point
        """
        self._out(
            f"{x1 * self.k:.2f} {(self.h - y1) * self.k:.2f} m {x2 * self.k:.2f} "
            f"{(self.h - y2) * self.k:.2f} l S"
        )

    @check_page
    def polyline(self, point_list, fill=False, polygon=False, style=None):
        """
        Draws lines between two or more points.

        Args:
            point_list (list of tuples): List of Abscissa and Ordinate of
                                        segments that should be drawn
            fill (bool): [**DEPRECATED since v2.5.4**] Use `style="F"` or `style="DF"` instead
            polygon (bool): If true, close path before stroking, to fill the inside of the polyline
            style (fpdf.enums.RenderStyle, str): Optional style of rendering. Possible values are:

            * `D` or None: draw border. This is the default value.
            * `F`: fill
            * `DF` or `FD`: draw and fill
        """
        if fill:
            warnings.warn(
                '"fill" parameter is deprecated, use style="F" or style="DF" instead',
                DeprecationWarning,
                stacklevel=5 if polygon else 3,
            )
        if fill and style is None:
            style = RenderStyle.DF
        else:
            style = RenderStyle.coerce(style)
            if fill and style == RenderStyle.D:
                raise ValueError(
                    f"Conflicting values provided: fill={fill} & style={style}"
                )
        operator = "m"
        for point in point_list:
            self._out(
                f"{point[0] * self.k:.2f} {(self.h - point[1]) * self.k:.2f} {operator}"
            )
            operator = "l"
        if polygon:
            self._out(" h")
        self._out(f" {style.operator}")

    @check_page
    def polygon(self, point_list, fill=False, style=None):
        """
        Outputs a polygon defined by three or more points.

        Args:
            point_list (list of tuples): List of coordinates defining the polygon to draw
            fill (bool): [**DEPRECATED since v2.5.4**] Use `style="F"` or `style="DF"` instead
            style (fpdf.enums.RenderStyle, str): Optional style of rendering. Possible values are:

            * `D` or None: draw border. This is the default value.
            * `F`: fill
            * `DF` or `FD`: draw and fill
        """
        self.polyline(point_list, fill=fill, polygon=True, style=style)

    @check_page
    def dashed_line(self, x1, y1, x2, y2, dash_length=1, space_length=1):
        """
        Draw a dashed line between two points.

        Args:
            x1 (float): Abscissa of first point
            y1 (float): Ordinate of first point
            x2 (float): Abscissa of second point
            y2 (float): Ordinate of second point
            dash_length (float): Length of the dash
            space_length (float): Length of the space between 2 dashes

        .. deprecated:: 2.4.6
            Use `FPDF.set_dash_pattern()` and the normal drawing operations instead.
        """
        warnings.warn(
            "dashed_line() is deprecated, and will be removed in a future release. "
            "Use set_dash_pattern() and the normal drawing operations instead.",
            DeprecationWarning,
            stacklevel=3,
        )
        self.set_dash_pattern(dash_length, space_length)
        self.line(x1, y1, x2, y2)
        self.set_dash_pattern()

    @check_page
    def rect(self, x, y, w, h, style=None, round_corners=False, corner_radius=0):
        """
        Outputs a rectangle.
        It can be drawn (border only), filled (with no border) or both.

        Args:
            x (float): Abscissa of upper-left bounding box.
            y (float): Ordinate of upper-left bounding box.
            w (float): Width.
            h (float): Height.

            style (fpdf.enums.RenderStyle, str): Optional style of rendering. Possible values are:

            * `D` or empty string: draw border. This is the default value.
            * `F`: fill
            * `DF` or `FD`: draw and fill

            round_corners (tuple of str, tuple of fpdf.enums.Corner, bool): Optional draw a rectangle with round corners.
            Possible values are:

            *`TOP_LEFT`: a rectangle with round top left corner
            *`TOP_RIGHT`: a rectangle with round top right corner
            *`BOTTOM_LEFT`: a rectangle with round bottom left corner
            *`BOTTOM_RIGHT`: a rectangle with round bottom right corner
            *`True`: a rectangle with all round corners
            *`False`: a rectangle with no round corners

            corner_radius: Optional radius of the corners
        """

        style = RenderStyle.coerce(style)
        if round_corners is not False:
            self._draw_rounded_rect(x, y, w, h, style, round_corners, corner_radius)
        else:
            self._out(
                f"{x * self.k:.2f} {(self.h - y) * self.k:.2f} {w * self.k:.2f} "
                f"{-h * self.k:.2f} re {style.operator}"
            )

    def _draw_rounded_rect(self, x, y, w, h, style, round_corners, r):
        min = h
        if w < h:
            min = w

        if r == 0:
            r = min / 5

        if r >= min / 2:
            r /= min

        point_1 = point_8 = (x, y)
        point_2 = point_3 = (x + w, y)
        point_4 = point_5 = (x + w, y + h)
        point_6 = point_7 = (x, y + h)
        coor_x = [x, x + w, x, x + w]
        coor_y = [y, y, y + h, y + h]

        if round_corners is True:
            round_corners = [
                Corner.TOP_RIGHT.value,
                Corner.TOP_LEFT.value,
                Corner.BOTTOM_RIGHT.value,
                Corner.BOTTOM_LEFT.value,
            ]
        round_corners = tuple(Corner.coerce(rc) for rc in round_corners)

        if Corner.TOP_RIGHT in round_corners:
            self.arc(coor_x[0], coor_y[0], 2 * r, 180, 270, style=style)
            point_1 = (x + r, y)
            point_8 = (x, y + r)

        if Corner.TOP_LEFT in round_corners:
            self.arc(coor_x[1] - 2 * r, coor_y[1], 2 * r, 270, 0, style=style)
            point_2 = (x + w - r, y)
            point_3 = (x + w, y + r)

        if Corner.BOTTOM_LEFT in round_corners:
            self.arc(coor_x[3] - 2 * r, coor_y[3] - 2 * r, 2 * r, 0, 90, style=style)
            point_4 = (x + w, y + h - r)
            point_5 = (x + w - r, y + h)

        if Corner.BOTTOM_RIGHT in round_corners:
            self.arc(coor_x[2], coor_y[2] - 2 * r, 2 * r, 90, 180, style=style)
            point_6 = (x + r, y + h)
            point_7 = (x, y + h - r)

        if style.is_fill:

            self.polyline(
                [
                    point_1,
                    point_2,
                    point_3,
                    point_4,
                    point_5,
                    point_6,
                    point_7,
                    point_8,
                    point_1,
                ],
                style="F",
            )

        if style.is_draw:
            self.line(point_1[0], point_1[1], point_2[0], point_2[1])
            self.line(point_3[0], point_3[1], point_4[0], point_4[1])
            self.line(point_5[0], point_5[1], point_6[0], point_6[1])
            self.line(point_7[0], point_7[1], point_8[0], point_8[1])

    @check_page
    def ellipse(self, x, y, w, h, style=None):
        """
        Outputs an ellipse.
        It can be drawn (border only), filled (with no border) or both.

        Args:
            x (float): Abscissa of upper-left bounding box.
            y (float): Ordinate of upper-left bounding box.
            w (float): Width
            h (float): Height
            style (fpdf.enums.RenderStyle, str): Optional style of rendering. Possible values are:

            * `D` or empty string: draw border. This is the default value.
            * `F`: fill
            * `DF` or `FD`: draw and fill
        """
        style = RenderStyle.coerce(style)
        self._draw_ellipse(x, y, w, h, style.operator)

    def _draw_ellipse(self, x, y, w, h, operator):
        cx = x + w / 2
        cy = y + h / 2
        rx = w / 2
        ry = h / 2

        lx = 4 / 3 * (math.sqrt(2) - 1) * rx
        ly = 4 / 3 * (math.sqrt(2) - 1) * ry

        self._out(
            (
                f"{(cx + rx) * self.k:.2f} {(self.h - cy) * self.k:.2f} m "
                f"{(cx + rx) * self.k:.2f} {(self.h - cy + ly) * self.k:.2f} "
                f"{(cx + lx) * self.k:.2f} {(self.h - cy + ry) * self.k:.2f} "
                f"{cx * self.k:.2f} {(self.h - cy + ry) * self.k:.2f} c"
            )
        )
        self._out(
            (
                f"{(cx - lx) * self.k:.2f} {(self.h - cy + ry) * self.k:.2f} "
                f"{(cx - rx) * self.k:.2f} {(self.h - cy + ly) * self.k:.2f} "
                f"{(cx - rx) * self.k:.2f} {(self.h - cy) * self.k:.2f} c"
            )
        )
        self._out(
            (
                f"{(cx - rx) * self.k:.2f} {(self.h - cy - ly) * self.k:.2f} "
                f"{(cx - lx) * self.k:.2f} {(self.h - cy - ry) * self.k:.2f} "
                f"{cx * self.k:.2f} {(self.h - cy - ry) * self.k:.2f} c"
            )
        )
        self._out(
            (
                f"{(cx + lx) * self.k:.2f} {(self.h - cy - ry) * self.k:.2f} "
                f"{(cx + rx) * self.k:.2f} {(self.h - cy - ly) * self.k:.2f} "
                f"{(cx + rx) * self.k:.2f} {(self.h - cy) * self.k:.2f} c {operator}"
            )
        )

    @check_page
    def circle(self, x, y, r, style=None):
        """
        Outputs a circle.
        It can be drawn (border only), filled (with no border) or both.

        Args:
            x (float): Abscissa of upper-left bounding box.
            y (float): Ordinate of upper-left bounding box.
            r (float): Radius of the circle.
            style (str): Style of rendering. Possible values are:

            * `D` or None: draw border. This is the default value.
            * `F`: fill
            * `DF` or `FD`: draw and fill
        """
        self.ellipse(x, y, r, r, style)

    @check_page
    def regular_polygon(self, x, y, numSides, polyWidth, rotateDegrees=0, style=None):
        """
        Outputs a regular polygon with n sides
        It can be rotated
        Style can also be applied (fill, border...)

        Args:
            x (float): Abscissa of upper-left bounding box.
            y (float): Ordinate of upper-left bounding box.
            numSides (int): Number of sides for polygon.
            polyWidth (float): Width of the polygon.
            rotateDegrees (float): Optional degree amount to rotate polygon.
            style (fpdf.enums.RenderStyle, str): Optional style of rendering. Possible values are:

            * `D` or None: draw border. This is the default value.
            * `F`: fill
            * `DF` or `FD`: draw and fill
        """
        radius = polyWidth / 2
        centerX = x + radius
        centerY = y - radius
        # center point is (centerX, centerY)
        points = []
        for i in range(1, numSides + 1):
            point = centerX + radius * math.cos(
                math.radians((360 / numSides) * i) + math.radians(rotateDegrees)
            ), centerY + radius * math.sin(
                math.radians((360 / numSides) * i) + math.radians(rotateDegrees)
            )
            points.append(point)
        # creates list of touples containing cordinate points of vertices

        self.polygon(points, style=style)
        # passes points through polygon function

    @check_page
    def star(self, x, y, r_in, r_out, corners, rotate_degrees=0, style=None):
        """
        Outputs a regular star with n corners.
        It can be rotated.
        It can be drawn (border only), filled (with no border) or both.

        Args:
            x (float): Abscissa of star's centre.
            y (float): Ordinate of star's centre.
            r_in (float): radius of internal circle.
            r_out (float): radius of external circle.
            corners (int): number of star's corners.
            rotate_degrees (float): Optional degree amount to rotate star clockwise.

            style (fpdf.enums.RenderStyle, str): Optional style of rendering. Possible values are:
            * `D`: draw border. This is the default value.
            * `F`: fill.
            * `DF` or `FD`: draw and fill.
        """
        th = math.radians(rotate_degrees)
        point_list = []
        for i in range(0, (corners * 2) + 1):
            corner_x = x + (r_out if i % 2 == 0 else r_in) * math.sin(th)
            corner_y = y + (r_out if i % 2 == 0 else r_in) * math.cos(th)
            point_list.append((corner_x, corner_y))

            th += math.radians(180 / corners)

        self.polyline(point_list, polygon=True, style=style)

    def arc(
        self,
        x,
        y,
        a,
        start_angle,
        end_angle,
        b=None,
        inclination=0,
        clockwise=False,
        start_from_center=False,
        end_at_center=False,
        style=None,
    ):
        """
        Outputs an arc.
        It can be drawn (border only), filled (with no border) or both.

        Args:
            a (float): Semi-major axis diameter.
            b (float): Semi-minor axis diameter, if None, equals to a (default: None).
            start_angle (float): Start angle of the arc (in degrees).
            end_angle (float): End angle of the arc (in degrees).
            inclination (float): Inclination of the arc in respect of the x-axis (default: 0).
            clockwise (bool): Way of drawing the arc (True: clockwise, False: counterclockwise) (default: False).
            start_from_center (bool): Start drawing from the center of the circle (default: False).
            end_at_center (bool): End drawing at the center of the circle (default: False).
            style (fpdf.enums.RenderStyle, str): Optional style of rendering. Allowed values are:

            * `D` or None: draw border. This is the default value.
            * `F`: fill
            * `DF` or `FD`: draw and fill
        """
        style = RenderStyle.coerce(style)

        if b is None:
            b = a

        a /= 2
        b /= 2

        cx = x + a
        cy = y + b

        # Functions used only to construct other points of the bezier curve
        def deg_to_rad(deg):
            return deg * math.pi / 180

        def angle_to_param(angle):
            angle = deg_to_rad(angle % 360)
            eta = math.atan2(math.sin(angle) / b, math.cos(angle) / a)

            if eta < 0:
                eta += 2 * math.pi
            return eta

        theta = deg_to_rad(inclination)
        cos_theta = math.cos(theta)
        sin_theta = math.sin(theta)

        def evaluate(eta):
            a_cos_eta = a * math.cos(eta)
            b_sin_eta = b * math.sin(eta)

            return [
                cx + a_cos_eta * cos_theta - b_sin_eta * sin_theta,
                cy + a_cos_eta * sin_theta + b_sin_eta * cos_theta,
            ]

        def derivative_evaluate(eta):
            a_sin_eta = a * math.sin(eta)
            b_cos_eta = b * math.cos(eta)

            return [
                -a_sin_eta * cos_theta - b_cos_eta * sin_theta,
                -a_sin_eta * sin_theta + b_cos_eta * cos_theta,
            ]

        # Calculating start_eta and end_eta so that
        #   start_eta < end_eta   <= start_eta + 2*PI if counterclockwise
        #   end_eta   < start_eta <= end_eta + 2*PI   if clockwise
        start_eta = angle_to_param(start_angle)
        end_eta = angle_to_param(end_angle)

        if not clockwise and end_eta <= start_eta:
            end_eta += 2 * math.pi
        elif clockwise and end_eta >= start_eta:
            start_eta += 2 * math.pi

        start_point = evaluate(start_eta)

        # Move to the start point
        if start_from_center:
            self._out(f"{cx * self.k:.2f} {(self.h - cy) * self.k:.2f} m")
            self._out(
                f"{start_point[0] * self.k:.2f} {(self.h - start_point[1]) * self.k:.2f} l"
            )
        else:
            self._out(
                f"{start_point[0] * self.k:.2f} {(self.h - start_point[1]) * self.k:.2f} m"
            )

        # Number of curves to use, maximal segment angle is 2*PI/max_curves
        max_curves = 4
        n = min(
            max_curves, math.ceil(abs(end_eta - start_eta) / (2 * math.pi / max_curves))
        )
        d_eta = (end_eta - start_eta) / n

        alpha = math.sin(d_eta) * (math.sqrt(4 + 3 * math.tan(d_eta / 2) ** 2) - 1) / 3

        eta2 = start_eta
        p2 = evaluate(eta2)
        p2_prime = derivative_evaluate(eta2)

        for i in range(n):
            p1 = p2
            p1_prime = p2_prime

            eta2 += d_eta
            p2 = evaluate(eta2)
            p2_prime = derivative_evaluate(eta2)

            control_point_1 = [p1[0] + alpha * p1_prime[0], p1[1] + alpha * p1_prime[1]]
            control_point_2 = [p2[0] - alpha * p2_prime[0], p2[1] - alpha * p2_prime[1]]

            end = ""
            if i == n - 1 and not end_at_center:
                end = f" {style.operator}"

            self._out(
                (
                    f"{control_point_1[0] * self.k:.2f} {(self.h - control_point_1[1]) * self.k:.2f} "
                    f"{control_point_2[0] * self.k:.2f} {(self.h - control_point_2[1]) * self.k:.2f} "
                    f"{p2[0] * self.k:.2f} {(self.h - p2[1]) * self.k:.2f} c" + end
                )
            )

        if end_at_center:
            if start_from_center:
                self._out(f"h {style.operator}")
            else:
                self._out(
                    f"{cx * self.k:.2f} {(self.h - cy) * self.k:.2f} l {style.operator}"
                )

    @check_page
    def solid_arc(
        self,
        x,
        y,
        a,
        start_angle,
        end_angle,
        b=None,
        inclination=0,
        clockwise=False,
        style=None,
    ):
        """
        Outputs a solid arc. A solid arc combines an arc and a triangle to form a pie slice
        It can be drawn (border only), filled (with no border) or both.

        Args:
            x (float): Abscissa of upper-left bounding box.
            y (float): Ordinate of upper-left bounding box.
            a (float): Semi-major axis.
            b (float): Semi-minor axis, if None, equals to a (default: None).
            start_angle (float): Start angle of the arc (in degrees).
            end_angle (float): End angle of the arc (in degrees).
            inclination (float): Inclination of the arc in respect of the x-axis (default: 0).
            clockwise (bool): Way of drawing the arc (True: clockwise, False: counterclockwise) (default: False).
            style (str): Style of rendering. Possible values are:

            * `D` or None: draw border. This is the default value.
            * `F`: fill
            * `DF` or `FD`: draw and fill
        """
        self.arc(
            x,
            y,
            a,
            start_angle,
            end_angle,
            b,
            inclination,
            clockwise,
            True,
            True,
            style,
        )

    def add_font(self, family, style="", fname=None, uni="DEPRECATED"):
        """
        Imports a TrueType or OpenType font and makes it available
        for later calls to the `FPDF.set_font()` method.

        You will find more information on the "Unicode" documentation page.

        Args:
            family (str): font family. Used as a reference for `FPDF.set_font()`
            style (str): font style. "B" for bold, "I" for italic.
            fname (str): font file name. You can specify a relative or full path.
                If the file is not found, it will be searched in `FPDF_FONT_DIR`.
            uni (bool): [**DEPRECATED since 2.5.1**] unused
        """
        if not fname:
            raise ValueError('"fname" parameter is required')

        ext = splitext(str(fname))[1]
        if ext not in (".otf", ".otc", ".ttf", ".ttc"):
            raise ValueError(
                f"Unsupported font file extension: {ext}."
                " add_font() used to accept .pkl file as input, but for security reasons"
                " this feature is deprecated since v2.5.1 and has been removed in v2.5.3."
            )

        if uni != "DEPRECATED":
            warnings.warn(
                '"uni" parameter is deprecated, unused and will soon be removed',
                DeprecationWarning,
                stacklevel=2,
            )

        style = "".join(sorted(style.upper()))
        if any(letter not in "BI" for letter in style):
            raise ValueError(
                f"Unknown style provided (only B & I letters are allowed): {style}"
            )
        fontkey = f"{family.lower()}{style}"

        # Check if font already added or one of the core fonts
        if fontkey in self.fonts or fontkey in self.core_fonts:
            warnings.warn(f"Core font or font already added '{fontkey}': doing nothing")
            return

        for parent in (".", FPDF_FONT_DIR):
            if not parent:
                continue

            if (Path(parent) / fname).exists():
                ttffilename = Path(parent) / fname
                break
        else:
            raise FileNotFoundError(f"TTF Font file not found: {fname}")

        font = ttLib.TTFont(ttffilename)
        self.font_files[fontkey] = {
            "length1": os.stat(ttffilename).st_size,
            "type": "TTF",
            "ttffile": ttffilename,
        }

        scale = 1000 / font["head"].unitsPerEm
        default_width = scale * font["hmtx"].metrics[".notdef"][0]

        try:
            cap_height = font["OS/2"].sCapHeight
        except AttributeError:
            cap_height = font["hhea"].ascent

        # entry for the PDF font descriptor specifying various characteristics of the font
        flags = FontDescriptorFlags.SYMBOLIC
        if font["post"].isFixedPitch:
            flags |= FontDescriptorFlags.FIXED_PITCH
        if font["post"].italicAngle != 0:
            flags |= FontDescriptorFlags.ITALIC
        if font["OS/2"].usWeightClass >= 600:
            flags |= FontDescriptorFlags.FORCE_BOLD

        desc = {
            "Ascent": round(font["hhea"].ascent * scale),
            "Descent": round(font["hhea"].descent * scale),
            "CapHeight": round(cap_height * scale),
            "Flags": flags.value,
            "FontBBox": (
                f"[{font['head'].xMin * scale:.0f} {font['head'].yMin * scale:.0f}"
                f" {font['head'].xMax * scale:.0f} {font['head'].yMax * scale:.0f}]"
            ),
            "ItalicAngle": int(font["post"].italicAngle),
            "StemV": round(50 + int(pow((font["OS/2"].usWeightClass / 65), 2))),
            "MissingWidth": round(default_width),
        }

        # a map unicode_char -> char_width
        char_widths = defaultdict(lambda: default_width)
        for char in font.getBestCmap().keys():
            # take glyph associated to char
            glyph = font.getBestCmap()[char]

            # take width associated to glyph
            w = font["hmtx"].metrics[glyph][0]

            char_widths[char] = round(scale * w + 0.001)  # ROUND_HALF_UP

        # include numbers in the subset! (if alias present)
        # ensure that alias is mapped 1-by-1 additionally (must be replaceable)
        sbarr = "\x00 "
        if self.str_alias_nb_pages:
            sbarr += "0123456789"
            sbarr += self.str_alias_nb_pages

        self.fonts[fontkey] = {
            "i": len(self.fonts) + 1,
            "type": "TTF",
            "name": re.sub("[ ()]", "", font["name"].getBestFullName()),
            "desc": desc,
            "up": round(font["post"].underlinePosition * scale),
            "ut": round(font["post"].underlineThickness * scale),
            "cw": char_widths,
            "ttffile": ttffilename,
            "fontkey": fontkey,
            "subset": SubsetMap(map(ord, sbarr)),
        }

    def set_font(self, family=None, style="", size=0):
        """
        Sets the font used to print character strings.
        It is mandatory to call this method at least once before printing text.

        Default encoding is not specified, but all text writing methods accept only
        unicode for external fonts and one byte encoding for standard.

        Standard fonts use `Latin-1` encoding by default, but Windows
        encoding `cp1252` (Western Europe) can be used with
        `self.core_fonts_encoding = encoding`.

        The font specified is retained from page to page.
        The method can be called before the first page is created.

        Args:
            family (str): name of a font added with `FPDF.add_font`,
                or name of one of the 14 standard "PostScript" fonts:
                Courier (fixed-width), Helvetica (sans serif), Times (serif),
                Symbol (symbolic) or ZapfDingbats (symbolic)
                If an empty string is provided, the current family is retained.
            style (str): empty string (by default) or a combination
                of one or several letters among B (bold), I (italic) and U (underline).
                Bold and italic styles do not apply to Symbol and ZapfDingbats fonts.
            size (float): in points. The default value is the current size.
        """
        if not family:
            family = self.font_family

        family = family.lower()
        style = "".join(sorted(style.upper()))
        if any(letter not in "BIU" for letter in style):
            raise ValueError(
                f"Unknown style provided (only B/I/U letters are allowed): {style}"
            )
        if "U" in style:
            self.underline = True
            style = style.replace("U", "")
        else:
            self.underline = False

        if family in self.font_aliases and family + style not in self.fonts:
            warnings.warn(
                f"Substituting font {family} by core font "
                f"{self.font_aliases[family]}"
            )
            family = self.font_aliases[family]
        elif family in ("symbol", "zapfdingbats") and style:
            warnings.warn(
                f"Built-in font {family} only has a single 'style' and can't be bold "
                f"or italic"
            )
            style = ""

        if size == 0:
            size = self.font_size_pt

        # Test if font is already selected
        if (
            self.font_family == family
            and self.font_style == style
            and isclose(self.font_size_pt, size)
        ):
            return

        # Test if used for the first time
        fontkey = family + style
        if fontkey not in self.fonts:
            if fontkey not in self.core_fonts:
                raise FPDFException(
                    f"Undefined font: {fontkey} - "
                    f"Use built-in fonts or FPDF.add_font() beforehand"
                )
            # If it's one of the core fonts, add it to self.fonts
            self.fonts[fontkey] = {
                "i": len(self.fonts) + 1,
                "type": "core",
                "name": self.core_fonts[fontkey],
                "up": -100,
                "ut": 50,
                "cw": fpdf_charwidths[fontkey],
                "fontkey": fontkey,
            }

        # Select it
        self.font_family = family
        self.font_style = style
        self.font_size_pt = size
        self.current_font = self.fonts[fontkey]
        if self.page > 0:
            self._out(f"BT /F{self.current_font['i']} {self.font_size_pt:.2f} Tf ET")

    def set_font_size(self, size):
        """
        Configure the font size in points

        Args:
            size (float): font size in points
        """
        if isclose(self.font_size_pt, size):
            return
        self.font_size_pt = size
        if self.page > 0:
            if not self.current_font:
                raise FPDFException(
                    "Cannot set font size: a font must be selected first"
                )
            self._out(f"BT /F{self.current_font['i']} {self.font_size_pt:.2f} Tf ET")

    def set_stretching(self, stretching):
        """
        Sets horizontal font stretching.
        By default, no stretching is set (which is equivalent to a value of 100).

        Args:
            stretching (float): horizontal stretching (scaling) in percents.
        """
        if self.font_stretching == stretching:
            return
        self.font_stretching = stretching
        if self.page > 0:
            self._out(f"BT {self.font_stretching:.2f} Tz ET")

    def add_link(self):
        """
        Creates a new internal link and returns its identifier.
        An internal link is a clickable area which directs to another place within the document.

        The identifier can then be passed to the `FPDF.cell()`, `FPDF.write()`, `FPDF.image()`
        or `FPDF.link()` methods.
        The destination must be defined using `FPDF.set_link()`.
        """
        n = len(self.links) + 1
        self.links[n] = DestinationXYZ(page=1)
        return n

    def set_link(self, link, y=0, x=0, page=-1, zoom="null"):
        """
        Defines the page and position a link points to.

        Args:
            link (int): a link identifier returned by `FPDF.add_link()`.
            y (float): optional ordinate of target position.
                The default value is 0 (top of page).
            x (float): optional abscissa of target position.
                The default value is 0 (top of page).
            page (int): optional number of target page.
                -1 indicates the current page, which is the default value.
            zoom (float): optional new zoom level after following the link.
                Currently ignored by Sumatra PDF Reader, but observed by Adobe Acrobat reader.
        """
        self.links[link] = DestinationXYZ(
            self.page if page == -1 else page, x=x, y=y, zoom=zoom
        )

    @check_page
    def link(self, x, y, w, h, link, alt_text=None, border_width=0):
        """
        Puts a link annotation on a rectangular area of the page.
        Text or image links are generally put via `FPDF.cell`,
        `FPDF.write` or `FPDF.image`,
        but this method can be useful for instance to define a clickable area inside an image.

        Args:
            x (float): horizontal position (from the left) to the left side of the link rectangle
            y (float): vertical position (from the top) to the bottom side of the link rectangle
            w (float): width of the link rectangle
            h (float): height of the link rectangle
            link: either an URL or a integer returned by `FPDF.add_link`, defining an internal link to a page
            alt_text (str): optional textual description of the link, for accessibility purposes
            border_width (int): thickness of an optional black border surrounding the link.
                Not all PDF readers honor this: Acrobat renders it but not Sumatra.
        """
        link = Annotation(
            "Link",
            x=x * self.k,
            y=self.h_pt - y * self.k,
            width=w * self.k,
            height=h * self.k,
            link=link,
            alt_text=alt_text,
            border_width=border_width,
        )
        self.annots[self.page].append(link)
        return link

    @check_page
    def text_annotation(
        self, x, y, text, w=1, h=1, name=None, flags=DEFAULT_ANNOT_FLAGS
    ):
        """
        Puts a text annotation on a rectangular area of the page.

        Args:
            x (float): horizontal position (from the left) to the left side of the link rectangle
            y (float): vertical position (from the top) to the bottom side of the link rectangle
            text (str): text to display
            w (float): optional width of the link rectangle
            h (float): optional height of the link rectangle
            name (fpdf.enums.AnnotationName, str): optional icon that shall be used in displaying the annotation
            flags (Tuple[fpdf.enums.AnnotationFlag], Tuple[str]): optional list of flags defining annotation properties
        """
        annotation = Annotation(
            "Text",
            x * self.k,
            self.h_pt - y * self.k,
            w * self.k,
            h * self.k,
            contents=text,
            name=AnnotationName.coerce(name) if name else None,
            flags=tuple(AnnotationFlag.coerce(flag) for flag in flags),
        )
        self.annots[self.page].append(annotation)
        return annotation

    @check_page
    def add_action(self, action, x, y, w, h):
        """
        Puts an Action annotation on a rectangular area of the page.

        Args:
            action (fpdf.actions.Action): the action to add
            x (float): horizontal position (from the left) to the left side of the link rectangle
            y (float): vertical position (from the top) to the bottom side of the link rectangle
            w (float): width of the link rectangle
            h (float): height of the link rectangle
        """
        annotation = Annotation(
            "Action",
            x * self.k,
            self.h_pt - y * self.k,
            w * self.k,
            h * self.k,
            action=action,
        )
        self.annots[self.page].append(annotation)
        return annotation

    @contextmanager
    def highlight(
        self, text, title="", type="Highlight", color=(1, 1, 0), modification_time=None
    ):
        """
        Context manager that adds a single highlight annotation based on the text lines inserted
        inside its indented block.

        Args:
            text (str): text of the annotation
            title (str): the text label that shall be displayed in the title bar of the annotation’s
                pop-up window when open and active. This entry shall identify the user who added the annotation.
            type (fpdf.enums.TextMarkupType, str): "Highlight", "Underline", "Squiggly" or "StrikeOut".
            color (tuple): a tuple of numbers in the range 0.0 to 1.0, representing a colour used for
                the title bar of the annotation’s pop-up window. Defaults to yellow.
            modification_time (datetime): date and time when the annotation was most recently modified
        """
        if self.record_text_quad_points:
            raise FPDFException("highlight() cannot be nested")
        self.record_text_quad_points = True
        yield
        for page, quad_points in self.text_quad_points.items():
            self.add_text_markup_annotation(
                type,
                text,
                quad_points=quad_points,
                title=title,
                color=color,
                modification_time=modification_time,
                page=page,
            )
            self.text_quad_points = defaultdict(list)
        self.record_text_quad_points = False

    add_highlight = highlight  # For backward compatibilty

    @check_page
    def add_text_markup_annotation(
        self,
        type,
        text,
        quad_points,
        title="",
        color=(1, 1, 0),
        modification_time=None,
        page=None,
    ):
        """
        Adds a text markup annotation on some quadrilateral areas of the page.

        Args:
            type (fpdf.enums.TextMarkupType, str): "Highlight", "Underline", "Squiggly" or "StrikeOut"
            text (str): text of the annotation
            quad_points (tuple): array of 8 × n numbers specifying the coordinates of n quadrilaterals
                in default user space that comprise the region in which the link should be activated.
                The coordinates for each quadrilateral are given in the order: x1 y1 x2 y2 x3 y3 x4 y4
                specifying the four vertices of the quadrilateral in counterclockwise order
            title (str): the text label that shall be displayed in the title bar of the annotation’s
                pop-up window when open and active. This entry shall identify the user who added the annotation.
            color (tuple): a tuple of numbers in the range 0.0 to 1.0, representing a colour used for
                the title bar of the annotation’s pop-up window. Defaults to yellow.
            modification_time (datetime): date and time when the annotation was most recently modified
            page (int): index of the page where this annotation is added
        """
        type = TextMarkupType.coerce(type).value
        if modification_time is None:
            modification_time = self.creation_date
        if page is None:
            page = self.page
        x_min = min(quad_points[0::2])
        y_min = min(quad_points[1::2])
        x_max = max(quad_points[0::2])
        y_max = max(quad_points[1::2])
        annotation = Annotation(
            type,
            contents=text,
            x=y_min,
            y=y_max,
            width=x_max - x_min,
            height=y_max - y_min,
            color=color,
            modification_time=modification_time,
            title=title,
            quad_points=quad_points,
            page=page,
        )
        self.annots[page].append(annotation)
        return annotation

    @check_page
    def ink_annotation(
        self, coords, contents="", title="", color=(1, 1, 0), border_width=1
    ):
        """
        Adds add an ink annotation on the page.

        Args:
            coords (tuple): an iterable of coordinates (pairs of numbers) defining a path
            contents (str): textual description
            title (str): the text label that shall be displayed in the title bar of the annotation’s
                pop-up window when open and active. This entry shall identify the user who added the annotation.
            color (tuple): a tuple of numbers in the range 0.0 to 1.0, representing a colour used for
                the title bar of the annotation’s pop-up window. Defaults to yellow.
            border_width (int): thickness of the path stroke.
        """
        ink_list = sum(((x * self.k, (self.h - y) * self.k) for (x, y) in coords), ())
        x_min = min(ink_list[0::2])
        y_min = min(ink_list[1::2])
        x_max = max(ink_list[0::2])
        y_max = max(ink_list[1::2])
        annotation = Annotation(
            "Ink",
            x=y_min,
            y=y_max,
            width=x_max - x_min,
            height=y_max - y_min,
            ink_list=ink_list,
            color=color,
            border_width=border_width,
            page=self.page,
            contents=contents,
            title=title,
        )
        self.annots[self.page].append(annotation)
        return annotation

    @check_page
    def text(self, x, y, txt=""):
        """
        Prints a character string. The origin is on the left of the first character,
        on the baseline. This method allows placing a string precisely on the page,
        but it is usually easier to use the `FPDF.cell()`, `FPDF.multi_cell() or `FPDF.write()` methods.

        Args:
            x (float): abscissa of the origin
            y (float): ordinate of the origin
            txt (str): string to print
        """
        if not self.font_family:
            raise FPDFException("No font set, you need to call set_font() beforehand")
        txt = self.normalize_text(txt)
        if self.unifontsubset:
            txt_mapped = ""
            for char in txt:
                uni = ord(char)
                # Instead of adding the actual character to the stream its code is
                # mapped to a position in the font's subset
                txt_mapped += chr(self.current_font["subset"].pick(uni))
            txt2 = escape_parens(txt_mapped.encode("utf-16-be").decode("latin-1"))
        else:
            txt2 = escape_parens(txt)
        s = f"BT {x * self.k:.2f} {(self.h - y) * self.k:.2f} Td"
        if self.text_mode != TextMode.FILL:
            s += f" {self.text_mode} Tr {self.line_width:.2f} w"
        s += f" ({txt2}) Tj ET"
        if self.underline and txt != "":
            s += " " + self._do_underline(x, y, txt)
        if self.fill_color != self.text_color:
            s = f"q {self.text_color.pdf_repr().lower()} {s} Q"
        self._out(s)
        if self.record_text_quad_points:
            w = (
                self.get_normalized_string_width_with_style(txt, self.font_style)
                * self.font_stretching
                / 100
                * self.font_size
                / 1000
            )
            h = self.font_size
            y -= 0.8 * h  # same coefficient as in _render_styled_text_line()
            self.text_quad_points[self.page].extend(
                [
                    x * self.k,
                    (self.h - y) * self.k,
                    (x + w) * self.k,
                    (self.h - y) * self.k,
                    x * self.k,
                    (self.h - y - h) * self.k,
                    (x + w) * self.k,
                    (self.h - y - h) * self.k,
                ]
            )

    @check_page
    def rotate(self, angle, x=None, y=None):
        """
        .. deprecated:: 2.1.0
            Use `FPDF.rotation()` instead.
        """
        warnings.warn(
            "rotate() can produces malformed PDFs and is deprecated. "
            "Use the rotation() context manager instead.",
            DeprecationWarning,
            stacklevel=3,
        )
        if x is None:
            x = self.x
        if y is None:
            y = self.y

        if self.angle != 0:
            self._out("Q")
        self.angle = angle
        if angle != 0:
            angle *= math.pi / 180
            c = math.cos(angle)
            s = math.sin(angle)
            cx = x * self.k
            cy = (self.h - y) * self.k
            s = (
                f"q {c:.5F} {s:.5F} {-s:.5F} {c:.5F} {cx:.2F} {cy:.2F} cm "
                f"1 0 0 1 {-cx:.2F} {-cy:.2F} cm"
            )
            self._out(s)

    @check_page
    @contextmanager
    def rotation(self, angle, x=None, y=None):
        """
        This method allows to perform a rotation around a given center.
        It must be used as a context-manager using `with`:

            with rotation(angle=90, x=x, y=y):
                pdf.something()

        The rotation affects all elements which are printed inside the indented
        context (with the exception of clickable areas).

        Args:
            angle (float): angle in degrees
            x (float): abscissa of the center of the rotation
            y (float): ordinate of the center of the rotation

        Notes
        -----

        Only the rendering is altered. The `FPDF.get_x()` and `FPDF.get_y()` methods are
        not affected, nor the automatic page break mechanism.
        The rotation also establishes a local graphics state, so that any
        graphics state settings changed within will not affect the operations
        invoked after it has finished.
        """
        if x is None:
            x = self.x
        if y is None:
            y = self.y
        angle *= math.pi / 180
        c, s = math.cos(angle), math.sin(angle)
        cx, cy = x * self.k, (self.h - y) * self.k
        with self.local_context():
            self._out(
                f"{c:.5F} {s:.5F} {-s:.5F} {c:.5F} {cx:.2F} {cy:.2F} cm "
                f"1 0 0 1 {-cx:.2F} {-cy:.2F} cm"
            )
            yield

    @check_page
    @contextmanager
    def local_context(
        self,
        font_family=None,
        font_style=None,
        font_size=None,
        line_width=None,
        draw_color=None,
        fill_color=None,
        text_color=None,
        dash_pattern=None,
        **kwargs,
    ):
        """
        Creates a local graphics state, which won't affect the surrounding code.
        This method must be used as a context manager using `with`:

            with pdf.local_context():
                set_some_state()
                draw_some_stuff()

        The affected settings are those controlled by GraphicsStateMixin and drawing.GraphicsStyle:
            allow_transparency
            auto_close
            blend_mode
            dash_pattern
            draw_color
            fill_color
            fill_opacity
            font_family
            font_size
            font_style
            font_stretching
            intersection_rule
            line_width
            paint_rule
            stroke_cap_style
            stroke_join_style
            stroke_miter_limit
            stroke_opacity
            text_color
            text_mode
            underline

        Args:
            **kwargs: key-values settings to set at the beggining of this context.
        """
        self._push_local_stack()
        gs = None
        for key, value in kwargs.items():
            if key in (
                "stroke_color",
                "stroke_dash_phase",
                "stroke_dash_pattern",
                "stroke_width",
            ):
                raise ValueError(
                    f"Unsupported setting: {key} - This can be controlled through dash_pattern / draw_color / line_width"
                )
            if key in drawing.GraphicsStyle.MERGE_PROPERTIES:
                if gs is None:
                    gs = drawing.GraphicsStyle()
                setattr(gs, key, value)
                if key == "blend_mode":
                    self._set_min_pdf_version("1.4")
            elif key in ("font_stretching", "text_mode", "underline"):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unsupported setting: {key}")
        if gs:
            gs_name = self._drawing_graphics_state_registry.register_style(gs)
            self._out(f"q /{gs_name} gs")
        else:
            self._out("q")
        # All the following calls to .set*() methods invoke .out() and write to the stream buffer:
        if font_family is not None or font_style is not None or font_size is not None:
            self.set_font(
                font_family or self.font_family,
                font_style or self.font_style,
                font_size or self.font_size_pt,
            )
        if line_width is not None:
            self.set_line_width(line_width)
        if draw_color is not None:
            if isinstance(draw_color, Sequence):
                self.set_draw_color(*draw_color)
            else:
                self.set_draw_color(draw_color)
        if fill_color is not None:
            if isinstance(fill_color, Sequence):
                self.set_fill_color(*fill_color)
            else:
                self.set_fill_color(fill_color)
        if text_color is not None:
            if isinstance(text_color, Sequence):
                self.set_text_color(*text_color)
            else:
                self.set_text_color(text_color)
        if dash_pattern is not None:
            self.set_dash_pattern(**dash_pattern)
        yield
        self._out("Q")
        self._pop_local_stack()

    @property
    def accept_page_break(self):
        """
        Whenever a page break condition is met, this method is called,
        and the break is issued or not depending on the returned value.

        The default implementation returns a value according to the mode selected by `FPDF.set_auto_page_break()`.
        This method is called automatically and should not be called directly by the application.
        """
        return self.auto_page_break

    @check_page
    def cell(
        self,
        w=None,
        h=None,
        txt="",
        border=0,
        ln="DEPRECATED",
        align=Align.L,
        fill=False,
        link="",
        center="DEPRECATED",
        markdown=False,
        new_x=XPos.RIGHT,
        new_y=YPos.TOP,
    ):
        """
        Prints a cell (rectangular area) with optional borders, background color and
        character string. The upper-left corner of the cell corresponds to the current
        position. The text can be aligned or centered. After the call, the current
        position moves to the selected `new_x`/`new_y` position. It is possible to put a link
        on the text.

        If automatic page breaking is enabled and the cell goes beyond the limit, a
        page break is performed before outputting.

        Args:
            w (float): Cell width. Default value: None, meaning to fit text width.
                If 0, the cell extends up to the right margin.
            h (float): Cell height. Default value: None, meaning an height equal
                to the current font size.
            txt (str): String to print. Default value: empty string.
            border: Indicates if borders must be drawn around the cell.
                The value can be either a number (`0`: no border ; `1`: frame)
                or a string containing some or all of the following characters
                (in any order):
                `L`: left ; `T`: top ; `R`: right ; `B`: bottom. Default value: 0.
            new_x (fpdf.enums.XPos, str): New current position in x after the call. Default: RIGHT
            new_y (fpdf.enums.YPos, str): New current position in y after the call. Default: TOP
            ln (int): **DEPRECATED since 2.5.1**: Use `new_x` and `new_y` instead.
            align (fpdf.enums.Align, str): Allows to center or align the text inside the cell.
                Possible values are: `L` or empty string: left align (default value) ;
                `C`: center; `X`: center around current x; `R`: right align
            fill (bool): Indicates if the cell background must be painted (`True`)
                or transparent (`False`). Default value: False.
            link (str): optional link to add on the cell, internal
                (identifier returned by `FPDF.add_link`) or external URL.
            center (bool): **DEPRECATED** since 2.5.1:
                Use align="C" or align="X" instead.
            markdown (bool): enable minimal markdown-like markup to render part
                of text as bold / italics / underlined. Default to False.

        Returns: a boolean indicating if page break was triggered
        """
        if not self.font_family:
            raise FPDFException("No font set, you need to call set_font() beforehand")
        if isinstance(w, str) or isinstance(h, str):
            raise ValueError(
                "Parameter 'w' and 'h' must be numbers, not strings."
                " You can omit them by passing string content with txt="
            )
        if isinstance(border, int) and border not in (0, 1):
            warnings.warn(
                'Integer values for "border" parameter other than 1 are currently '
                "ignored"
            )
            border = 1
        new_x = XPos.coerce(new_x)
        new_y = YPos.coerce(new_y)
        if center == "DEPRECATED":
            center = False
        else:
            warnings.warn(
                'The parameter "center" is deprecated. Use align="C" or align="X" instead.',
                DeprecationWarning,
                stacklevel=3,
            )
        if ln != "DEPRECATED":
            # For backwards compatibility, if "ln" is used we overwrite "new_[xy]".
            if ln == 0:
                new_x = XPos.RIGHT
                new_y = YPos.TOP
            elif ln == 1:
                new_x = XPos.LMARGIN
                new_y = YPos.NEXT
            elif ln == 2:
                new_x = XPos.LEFT
                new_y = YPos.NEXT
            else:
                raise ValueError(
                    f'Invalid value for parameter "ln" ({ln}),'
                    " must be an int between 0 and 2."
                )
            warnings.warn(
                (
                    'The parameter "ln" is deprecated.'
                    f" Instead of ln={ln} use new_x=XPos.{new_x.name}, new_y=YPos.{new_y.name}."
                ),
                DeprecationWarning,
                stacklevel=3,
            )
        align = Align.coerce(align)
        if align == Align.J:
            raise ValueError(
                "cell() only produces one text line, justified alignment is not possible"
            )
        # Font styles preloading must be performed before any call to FPDF.get_string_width:
        txt = self.normalize_text(txt)
        styled_txt_frags = self._preload_font_styles(txt, markdown)
        return self._render_styled_text_line(
            TextLine(
                styled_txt_frags,
                text_width=0.0,
                number_of_spaces_between_words=0,
                justify=False,
                trailing_nl=False,
            ),
            w,
            h,
            border,
            new_x=new_x,
            new_y=new_y,
            align=align,
            fill=fill,
            link=link,
            center=center,
        )

    def _render_styled_text_line(
        self,
        text_line: TextLine,
        w: float = None,
        h: float = None,
        border: Union[str, int] = 0,
        new_x: XPos = XPos.RIGHT,
        new_y: YPos = YPos.TOP,
        align: Align = Align.L,
        fill: bool = False,
        link: str = "",
        center: bool = False,
    ):
        """
        Prints a cell (rectangular area) with optional borders, background color and
        character string. The upper-left corner of the cell corresponds to the current
        position. The text can be aligned, centered or justified. After the call, the
        current position moves to the requested new position. It is possible to put a
        link on the text.

        If automatic page breaking is enabled and the cell goes beyond the limit, a
        page break is performed before outputting.

        Args:
            text_line (TextLine instance): Contains the (possibly empty) tuple of
                fragments to render.
            w (float): Cell width. Default value: None, meaning to fit text width.
                If 0, the cell extends up to the right margin.
            h (float): Cell height. Default value: None, meaning an height equal
                to the current font size.
            border: Indicates if borders must be drawn around the cell.
                The value can be either a number (`0`: no border ; `1`: frame)
                or a string containing some or all of the following characters
                (in any order):
                `L`: left ; `T`: top ; `R`: right ; `B`: bottom. Default value: 0.
            new_x (fpdf.enums.XPos): New current position in x after the call.
            new_y (fpdf.enums.YPos): New current position in y after the call.
            align (fpdf.enums.Align): Allows to align the text inside the cell.
                Possible values are:
                `L` or empty string: left align (default value);
                `C`: center; `X`: center around current x; `R`: right align;
                `J`: justify (if more than one word)
            fill (bool): Indicates if the cell background must be painted (`True`)
                or transparent (`False`). Default value: False.
            link (str): optional link to add on the cell, internal
                (identifier returned by `FPDF.add_link`) or external URL.
            center (bool): **DEPRECATED since 2.5.1**: Use `align="C"` instead.
            markdown (bool): enable minimal markdown-like markup to render part
                of text as bold / italics / underlined. Default to False.

        Returns: a boolean indicating if page break was triggered
        """
        if not self.font_family:
            raise FPDFException("No font set, you need to call set_font() beforehand")
        if isinstance(border, int) and border not in (0, 1):
            warnings.warn(
                'Integer values for "border" parameter other than 1 are currently '
                "ignored"
            )
            border = 1
        styled_txt_width = text_line.text_width / 1000 * self.font_size
        if not styled_txt_width:
            for styled_txt_frag in text_line.fragments:
                unscaled_width = self.get_normalized_string_width_with_style(
                    styled_txt_frag.string, styled_txt_frag.style
                )
                if self.font_stretching != 100:
                    unscaled_width *= self.font_stretching / 100
                styled_txt_width += unscaled_width * self.font_size / 1000
        elif self.font_stretching != 100:
            styled_txt_width *= self.font_stretching / 100

        if w == 0:
            w = self.w - self.r_margin - self.x
        elif w is None:
            if not text_line.fragments:
                raise ValueError(
                    "A 'text_line' parameter with fragments must be provided if 'w' is None"
                )
            w = styled_txt_width + self.c_margin + self.c_margin
        if h is None:
            h = self.font_size
        if align == Align.X:
            self.x -= w / 2
        if center:
            self.x = self.l_margin + (self.epw - w) / 2
        page_break_triggered = self._perform_page_break_if_need_be(h)
        sl = []
        k = self.k
        # pylint: disable=invalid-unary-operand-type
        # "h" can't actually be None
        if fill:
            op = "B" if border == 1 else "f"
            sl.append(
                f"{self.x * k:.2f} {(self.h - self.y) * k:.2f} "
                f"{w * k:.2f} {-h * k:.2f} re {op}"
            )
        elif border == 1:
            sl.append(
                f"{self.x * k:.2f} {(self.h - self.y) * k:.2f} "
                f"{w * k:.2f} {-h * k:.2f} re S"
            )
        # pylint: enable=invalid-unary-operand-type

        if isinstance(border, str):
            x = self.x
            y = self.y
            if "L" in border:
                sl.append(
                    f"{x * k:.2f} {(self.h - y) * k:.2f} m "
                    f"{x * k:.2f} {(self.h - (y + h)) * k:.2f} l S"
                )
            if "T" in border:
                sl.append(
                    f"{x * k:.2f} {(self.h - y) * k:.2f} m "
                    f"{(x + w) * k:.2f} {(self.h - y) * k:.2f} l S"
                )
            if "R" in border:
                sl.append(
                    f"{(x + w) * k:.2f} {(self.h - y) * k:.2f} m "
                    f"{(x + w) * k:.2f} {(self.h - (y + h)) * k:.2f} l S"
                )
            if "B" in border:
                sl.append(
                    f"{x * k:.2f} {(self.h - (y + h)) * k:.2f} m "
                    f"{(x + w) * k:.2f} {(self.h - (y + h)) * k:.2f} l S"
                )

        if self.record_text_quad_points:
            x = self.x
            y = self.y
            self.text_quad_points[self.page].extend(
                [
                    x * self.k,
                    (self.h - y) * self.k,
                    (x + w) * self.k,
                    (self.h - y) * self.k,
                    x * self.k,
                    (self.h - y - h) * self.k,
                    (x + w) * self.k,
                    (self.h - y - h) * self.k,
                ]
            )

        s_start = self.x
        s_width, underlines = 0, []
        # We try to avoid modifying global settings for temporary changes.
        current_font_style = self.font_style
        current_font = self.current_font
        if text_line.fragments:
            if align == Align.R:
                dx = w - self.c_margin - styled_txt_width
            elif align in [Align.C, Align.X]:
                dx = (w - styled_txt_width) / 2
            else:
                dx = self.c_margin
            s_start += dx

            if self.fill_color != self.text_color:
                sl.append(self.text_color.pdf_repr().lower())

            sl.append(
                f"BT {(self.x + dx) * k:.2f} "
                f"{(self.h - self.y - 0.5 * h - 0.3 * self.font_size) * k:.2f} Td"
            )

            if self.text_mode != TextMode.FILL:
                sl.append(f"{self.text_mode} Tr {self.line_width:.2f} w")

            # precursor to self.ws, or manual spacing of unicode fonts/
            word_spacing = 0
            if text_line.justify:
                word_spacing = (
                    w - self.c_margin - self.c_margin - styled_txt_width
                ) / text_line.number_of_spaces_between_words
            if self.font_stretching != 100:
                # Space character is already stretched, extra spacing is absolute.
                word_spacing *= 100 / self.font_stretching
            if word_spacing and self.unifontsubset:
                # If multibyte, Tw has no effect - do word spacing using an
                # adjustment before each space
                space = escape_parens(" ".encode("utf-16-be").decode("latin-1"))
                if self.ws > 0:
                    sl.append("0 Tw")
                    self.ws = 0
                for frag in text_line.fragments:
                    if current_font_style != frag.style:
                        current_font_style = frag.style
                        current_font = self.fonts[self.font_family + current_font_style]
                        sl.append(f"/F{current_font['i']} {self.font_size_pt:.2f} Tf")
                    txt_frag_mapped = ""
                    for char in frag.string:
                        uni = ord(char)
                        txt_frag_mapped += chr(current_font["subset"].pick(uni))

                    # Determine the position of space (" ") in the current subset and
                    # split words whenever this mapping code is found
                    words = txt_frag_mapped.split(
                        chr(current_font["subset"].pick(ord(" ")))
                    )

                    words_strl = []
                    for i, word in enumerate(words):
                        word = escape_parens(word.encode("utf-16-be").decode("latin-1"))
                        if i == 0:
                            words_strl.append(f"({word})")
                        else:
                            adj = -(word_spacing * self.k) * 1000 / self.font_size_pt
                            words_strl.append(f"{adj:.3f}({space}{word})")
                    sl.append(f"[{' '.join(words_strl)}] TJ")
                    if frag.underline:
                        underlines.append((self.x + dx + s_width, frag.string))
                    frag_width = self.get_normalized_string_width_with_style(
                        frag.string, current_font_style
                    )
                    # /1000 for font space conversion, /100 for percentage -> *0.00001
                    frag_width *= self.font_stretching * self.font_size * 0.00001
                    s_width += frag_width + self.ws * frag.string.count(" ")
            else:
                if word_spacing and word_spacing != self.ws:
                    sl.append(f"{word_spacing * self.k:.3f} Tw")
                elif self.ws > 0:
                    sl.append("0 Tw")
                self.ws = word_spacing

                for frag in text_line.fragments:
                    if current_font_style != frag.style:
                        current_font_style = frag.style
                        current_font = self.fonts[self.font_family + current_font_style]
                        sl.append(f"/F{current_font['i']} {self.font_size_pt:.2f} Tf")
                    if self.unifontsubset:
                        txt_frag_mapped = ""
                        for char in frag.string:
                            uni = ord(char)
                            txt_frag_mapped += chr(current_font["subset"].pick(uni))
                        txt_frag_escaped = escape_parens(
                            txt_frag_mapped.encode("utf-16-be").decode("latin-1")
                        )
                    else:
                        txt_frag_escaped = escape_parens(frag.string)
                    sl.append(f"({txt_frag_escaped}) Tj")
                    if frag.underline:
                        underlines.append((self.x + dx + s_width, frag.string))
                    frag_width = self.get_normalized_string_width_with_style(
                        frag.string, current_font_style
                    )
                    # /1000 for font space conversion, /100 for percentage -> *0.00001
                    frag_width *= self.font_stretching * self.font_size * 0.00001
                    s_width += frag_width + self.ws * frag.string.count(" ")
            sl.append("ET")

            for start_x, txt_frag in underlines:
                sl.append(
                    self._do_underline(
                        start_x,
                        self.y + (0.5 * h) + (0.3 * self.font_size),
                        txt_frag,
                        current_font,
                    )
                )
            if link:
                self.link(
                    self.x + dx,
                    self.y + (0.5 * h) - (0.5 * self.font_size),
                    styled_txt_width,
                    self.font_size,
                    link,
                )
        if sl:
            # If any PDF settings have been left modified, wrap the line in a local context.
            if (
                current_font_style != self.font_style
                or self.fill_color != self.text_color
            ):
                s = f"q {' '.join(sl)} Q"
            else:
                s = " ".join(sl)
            self._out(s)
        self.lasth = h

        # XPos.LEFT -> self.x stays the same
        if new_x == XPos.RIGHT:
            self.x += w
        elif new_x == XPos.START:
            self.x = s_start
        elif new_x == XPos.END:
            self.x = s_start + s_width
        elif new_x == XPos.WCONT:
            self.x = s_start + s_width - self.c_margin
        elif new_x == XPos.CENTER:
            self.x = s_start + s_width / 2.0
        elif new_x == XPos.LMARGIN:
            self.x = self.l_margin
        elif new_x == XPos.RMARGIN:
            self.x = self.w - self.r_margin

        # YPos.TOP:  -> self.y stays the same
        # YPos.LAST: -> self.y stays the same (single line)
        if new_y == YPos.NEXT:
            self.y += h
        if new_y == YPos.TMARGIN:
            self.y = self.t_margin
        if new_y == YPos.BMARGIN:
            self.y = self.h - self.b_margin

        return page_break_triggered

    def _preload_font_styles(self, txt, markdown):
        """
        When Markdown styling is enabled, we require secondary fonts
        to ender text in bold & italics.
        This function ensure that those fonts are available.
        It needs to perform Markdown parsing,
        so we return the resulting `styled_txt_frags` tuple
        to avoid repeating this processing later on.
        """
        if not txt:
            return tuple()
        if not markdown:
            return tuple(
                [Fragment.from_string(txt, self.font_style, bool(self.underline))]
            )
        prev_font_style = self.font_style
        styled_txt_frags = tuple(self._markdown_parse(txt))
        page = self.page
        # We set the current to page to zero so that
        # set_font() does not produce any text object on the stream buffer:
        self.page = 0
        if any("B" in frag.style for frag in styled_txt_frags):
            # Ensuring bold font is supported:
            self.set_font(style="B")
        if any("I" in frag.style for frag in styled_txt_frags):
            # Ensuring italics font is supported:
            self.set_font(style="I")
        # Restoring initial style:
        self.set_font(style=prev_font_style)
        self.page = page
        return styled_txt_frags

    def _markdown_parse(self, txt):
        "Split some text into fragments based on styling: **bold**, __italics__, --underlined--"
        txt_frag, in_bold, in_italics, in_underline = (
            [],
            "B" in self.font_style,
            "I" in self.font_style,
            bool(self.underline),
        )
        while txt:
            is_marker = txt[:2] in (
                self.MARKDOWN_BOLD_MARKER,
                self.MARKDOWN_ITALICS_MARKER,
                self.MARKDOWN_UNDERLINE_MARKER,
            )
            half_marker = txt[0]
            # Check that previous & next characters are not identical to the marker:
            if (
                is_marker
                and (not txt_frag or txt_frag[0] != half_marker)
                and (len(txt) < 3 or txt[2] != half_marker)
            ):
                if txt_frag:
                    yield Fragment(
                        ("B" if in_bold else "") + ("I" if in_italics else ""),
                        in_underline,
                        txt_frag,
                    )
                if txt[:2] == self.MARKDOWN_BOLD_MARKER:
                    in_bold = not in_bold
                if txt[:2] == self.MARKDOWN_ITALICS_MARKER:
                    in_italics = not in_italics
                if txt[:2] == self.MARKDOWN_UNDERLINE_MARKER:
                    in_underline = not in_underline
                txt_frag = []
                txt = txt[2:]
            else:
                txt_frag.append(txt[0])
                txt = txt[1:]
        if txt_frag:
            yield Fragment(
                ("B" if in_bold else "") + ("I" if in_italics else ""),
                in_underline,
                txt_frag,
            )

    def will_page_break(self, height):
        """
        Let you know if adding an element will trigger a page break,
        based on its height and the current ordinate (`y` position).

        Args:
            height (float): height of the section that would be added, e.g. a cell

        Returns: a boolean indicating if a page break would occur
        """
        return (
            self.y + height > self.page_break_trigger
            and not self.in_footer
            and self.accept_page_break
        )

    def _perform_page_break_if_need_be(self, h):
        if self.will_page_break(h):
            LOGGER.debug(
                "Page break on page %d at y=%d for element of height %d > %d",
                self.page,
                self.y,
                h,
                self.page_break_trigger,
            )
            self._perform_page_break()
            return True
        return False

    def _perform_page_break(self):
        x, ws = self.x, self.ws
        # Reset word spacing
        # We want each page to start with the default value, so that splitting
        # the document between pages later doesn't cause any trouble.
        if ws > 0:
            self.ws = 0
            self._out("0 Tw")
        self.add_page(same=True)
        self.x = x  # restore x but not y after drawing header

    def _has_next_page(self):
        return self.pages_count > self.page

    @check_page
    def multi_cell(
        self,
        w,
        h=None,
        txt="",
        border=0,
        align=Align.J,
        fill=False,
        split_only=False,
        link="",
        ln="DEPRECATED",
        max_line_height=None,
        markdown=False,
        print_sh=False,
        new_x=XPos.RIGHT,
        new_y=YPos.NEXT,
    ):
        """
        This method allows printing text with line breaks. They can be automatic
        (breaking at the most recent space or soft-hyphen character) as soon as the text
        reaches the right border of the cell, or explicit (via the `\\n` character).
        As many cells as necessary are stacked, one below the other.
        Text can be aligned, centered or justified. The cell block can be framed and
        the background painted.

        Args:
            w (float): cell width. If 0, they extend up to the right margin of the page.
            h (float): cell height. Default value: None, meaning to use the current font size.
            txt (str): string to print.
            border: Indicates if borders must be drawn around the cell.
                The value can be either a number (`0`: no border ; `1`: frame)
                or a string containing some or all of the following characters
                (in any order):
                `L`: left ; `T`: top ; `R`: right ; `B`: bottom. Default value: 0.
            align (fpdf.enums.Align, str): Allows to center or align the text.
                Possible values are:
                `J`: justify (default value); `L` or empty string: left align;
                `C`: center; `X`: center around current x; `R`: right align
            fill (bool): Indicates if the cell background must be painted (`True`)
                or transparent (`False`). Default value: False.
            split_only (bool): if `True`, does not output anything, only perform
                word-wrapping and return the resulting multi-lines array of strings.
            link (str): optional link to add on the cell, internal
                (identifier returned by `add_link`) or external URL.
            new_x (fpdf.enums.XPos, str): New current position in x after the call. Default: RIGHT
            new_y (fpdf.enums.YPos, str): New current position in y after the call. Default: NEXT
            ln (int): **DEPRECATED since 2.5.1**: Use `new_x` and `new_y` instead.
            max_line_height (float): optional maximum height of each sub-cell generated
            markdown (bool): enable minimal markdown-like markup to render part
                of text as bold / italics / underlined. Default to False.
            print_sh (bool): Treat a soft-hyphen (\\u00ad) as a normal printable
                character, instead of a line breaking opportunity. Default value: False

        Using `new_x=XPos.RIGHT, new_y=XPos.TOP, maximum height=pdf.font_size` is
        useful to build tables with multiline text in cells.

        Returns: a boolean indicating if page break was triggered,
            or if `split_only == True`: `txt` splitted into lines in an array
        """
        if isinstance(w, str) or isinstance(h, str):
            raise ValueError(
                "Parameter 'w' and 'h' must be numbers, not strings."
                " You can omit them by passing string content with txt="
            )
        new_x = XPos.coerce(new_x)
        new_y = YPos.coerce(new_y)
        if ln != "DEPRECATED":
            # For backwards compatibility, if "ln" is used we overwrite "new_[xy]".
            if ln == 0:
                new_x = XPos.RIGHT
                new_y = YPos.NEXT
            elif ln == 1:
                new_x = XPos.LMARGIN
                new_y = YPos.NEXT
            elif ln == 2:
                new_x = XPos.LEFT
                new_y = YPos.NEXT
            elif ln == 3:
                new_x = XPos.RIGHT
                new_y = YPos.TOP
            else:
                raise ValueError(
                    f'Invalid value for parameter "ln" ({ln}),'
                    " must be an int between 0 and 3."
                )
            warnings.warn(
                (
                    'The parameter "ln" is deprecated.'
                    f" Instead of ln={ln} use new_x=XPos.{new_x.name}, new_y=YPos.{new_y.name}."
                ),
                DeprecationWarning,
                stacklevel=3,
            )
        align = Align.coerce(align)

        page_break_triggered = False
        if split_only:
            self._out = lambda *args, **kwargs: None
            self.add_page = lambda *args, **kwargs: None
            self._perform_page_break_if_need_be = lambda *args, **kwargs: None

        if h is None:
            h = self.font_size
        # If width is 0, set width to available width between margins
        if w == 0:
            w = self.w - self.r_margin - self.x
        maximum_allowed_emwidth = (w - 2 * self.c_margin) * 1000 / self.font_size
        if self.font_stretching != 100:
            maximum_allowed_emwidth *= 100 / self.font_stretching

        # Calculate text length
        txt = self.normalize_text(txt)
        normalized_string = txt.replace("\r", "")
        styled_text_fragments = self._preload_font_styles(normalized_string, markdown)

        prev_font_style, prev_underline = self.font_style, self.underline
        prev_x, prev_y = self.x, self.y

        if not border:
            border = ""
        elif border == 1:
            border = "LTRB"

        text_lines = []
        multi_line_break = MultiLineBreak(
            styled_text_fragments,
            self.get_normalized_string_width_with_style,
            justify=(align == Align.J),
            print_sh=print_sh,
        )
        text_line = multi_line_break.get_line_of_given_width(maximum_allowed_emwidth)
        while (text_line) is not None:
            text_lines.append(text_line)
            text_line = multi_line_break.get_line_of_given_width(
                maximum_allowed_emwidth
            )

        if not text_lines:  # ensure we display at least one cell - cf. issue #349
            text_lines = [
                TextLine(
                    "",
                    text_width=0,
                    number_of_spaces_between_words=0,
                    justify=False,
                    trailing_nl=False,
                )
            ]
        if align == Align.X:
            prev_x = self.x
        for text_line_index, text_line in enumerate(text_lines):
            is_last_line = text_line_index == len(text_lines) - 1
            if max_line_height is not None and h > max_line_height and not is_last_line:
                current_cell_height = max_line_height
                h -= current_cell_height
            else:
                current_cell_height = h

            new_page = self._render_styled_text_line(
                text_line,
                w,
                h=current_cell_height,
                border="".join(
                    (
                        "T" if "T" in border and text_line_index == 0 else "",
                        "L" if "L" in border else "",
                        "R" if "R" in border else "",
                        "B" if "B" in border and is_last_line else "",
                    )
                ),
                new_x=new_x if is_last_line else XPos.LEFT,
                new_y=new_y if is_last_line else YPos.NEXT,
                align=Align.L if (align == Align.J and is_last_line) else align,
                fill=fill,
                link=link,
            )
            if is_last_line and new_page and new_y == YPos.TOP:
                # When a page jump is performed and the requested y is TOP,
                # pretend we started at the top of the text block on the new page.
                # cf. test_multi_cell_table_with_automatic_page_break
                prev_y = self.y
            page_break_triggered = page_break_triggered or new_page
            if not is_last_line and align == Align.X:
                # prevent cumulative shift to the left
                self.x = prev_x
            if (
                is_last_line
                and text_line.trailing_nl
                and new_y in (YPos.LAST, YPos.NEXT)
            ):
                # The line renderer can't handle trailing newlines in the text.
                self.ln()

        if new_y == YPos.TOP:  # We may have jumped a few lines -> reset
            self.y = prev_y

        if split_only:
            # restore writing functions
            del self.add_page
            del self._out
            del self._perform_page_break_if_need_be
            self.set_xy(prev_x, prev_y)  # restore location
            result = []
            for text_line in text_lines:
                characters = []
                for frag in text_line.fragments:
                    characters.extend(frag.characters)
                result.append("".join(characters))
            return result
        if markdown:
            if self.font_style != prev_font_style:
                self.font_style = prev_font_style
                self.current_font = self.fonts[self.font_family + self.font_style]
            self.underline = prev_underline

        return page_break_triggered

    @check_page
    def write(
        self, h: float = None, txt: str = "", link: str = "", print_sh: bool = False
    ):
        """
        Prints text from the current position.
        When the right margin is reached, a line break occurs at the most recent
        space or soft-hyphen character, and text continues from the left margin.
        A manual break happens any time the \\n character is met,
        Upon method exit, the current position is left just at the end of the text.

        Args:
            h (float): line height. Default value: None, meaning to use the current font size.
            txt (str): text content
            link (str): optional link to add on the text, internal
                (identifier returned by `FPDF.add_link`) or external URL.
            print_sh (bool): Treat a soft-hyphen (\\u00ad) as a normal printable
                character, instead of a line breaking opportunity. Default value: False
        """
        if not self.font_family:
            raise FPDFException("No font set, you need to call set_font() beforehand")
        if isinstance(h, str):
            raise ValueError(
                "Parameter 'h' must be a number, not a string."
                " You can omit it by passing string content with txt="
            )
        if h is None:
            h = self.font_size

        page_break_triggered = False
        normalized_string = self.normalize_text(txt).replace("\r", "")
        styled_text_fragments = self._preload_font_styles(normalized_string, False)

        text_lines = []
        multi_line_break = MultiLineBreak(
            styled_text_fragments,
            self.get_normalized_string_width_with_style,
            print_sh=print_sh,
        )
        prev_x = self.x
        # first line from current x position to right margin
        first_width = self.w - prev_x - self.r_margin
        first_emwidth = (first_width - 2 * self.c_margin) * 1000 / self.font_size
        if self.font_stretching != 100:
            first_emwidth *= 100 / self.font_stretching
        text_line = multi_line_break.get_line_of_given_width(
            first_emwidth, wordsplit=False
        )
        # remaining lines fill between margins
        full_width = self.w - self.l_margin - self.r_margin
        full_emwidth = (full_width - 2 * self.c_margin) * 1000 / self.font_size
        if self.font_stretching != 100:
            full_emwidth *= 100 / self.font_stretching
        while (text_line) is not None:
            text_lines.append(text_line)
            text_line = multi_line_break.get_line_of_given_width(full_emwidth)
        if text_line:
            text_lines.append(text_line)
        if not text_lines:
            return False

        self.ws = 0  # currently only left aligned, so no word spacing
        for text_line_index, text_line in enumerate(text_lines):
            if text_line_index == 0:
                line_width = first_width
            else:
                line_width = full_width
                self.ln()
            new_page = self._render_styled_text_line(
                text_line,
                line_width,
                h=h,
                border=0,
                new_x=XPos.WCONT,
                new_y=YPos.TOP,
                align=Align.L,
                fill=False,
                link=link,
            )
            page_break_triggered = page_break_triggered or new_page
        if text_line.trailing_nl:
            # The line renderer can't handle trailing newlines in the text.
            self.ln()
        return page_break_triggered

    @check_page
    def image(
        self,
        name,
        x=None,
        y=None,
        w=0,
        h=0,
        type="",
        link="",
        title=None,
        alt_text=None,
    ):
        """
        Put an image on the page.

        The size of the image on the page can be specified in different ways:
        * explicit width and height (expressed in user units)
        * one explicit dimension, the other being calculated automatically
          in order to keep the original proportions
        * no explicit dimension, in which case the image is put at 72 dpi.

        **Remarks**:
        * if an image is used several times, only one copy is embedded in the file.
        * when using an animated GIF, only the first frame is used.

        Args:
            name: either a string representing a file path to an image, an URL to an image,
                an io.BytesIO, or a instance of `PIL.Image.Image`
            x (float): optional horizontal position where to put the image on the page.
                If not specified or equal to None, the current abscissa is used.
            y (float): optional vertical position where to put the image on the page.
                If not specified or equal to None, the current ordinate is used.
                After the call, the current ordinate is moved to the bottom of the image
            w (float): optional width of the image. If not specified or equal to zero,
                it is automatically calculated from the image size.
                Pass `pdf.epw` to scale horizontally to the full page width.
            h (float): optional height of the image. If not specified or equal to zero,
                it is automatically calculated from the image size.
                Pass `pdf.eph` to scale horizontally to the full page height.
            type (str): [**DEPRECATED since 2.2.0**] unused, will be removed in a later version.
            link (str): optional link to add on the image, internal
                (identifier returned by `FPDF.add_link`) or external URL.
            title (str): optional. Currently, never seem rendered by PDF readers.
            alt_text (str): optional alternative text describing the image,
                for accessibility purposes. Displayed by some PDF readers on hover.
        """
        if type:
            warnings.warn(
                '"type" parameter is deprecated, unused and will soon be removed',
                DeprecationWarning,
                stacklevel=3,
            )
        if str(name).endswith(".svg"):
            # Insert it as a PDF path:
            img = load_image(str(name))
            return self._vector_image(img, x, y, w, h, link, title, alt_text)
        if isinstance(name, str):
            img = None
        elif isinstance(name, Image):
            bytes = name.tobytes()
            img_hash = hashlib.new("md5", usedforsecurity=False)  # nosec B324
            img_hash.update(bytes)
            name, img = img_hash.hexdigest(), name
        elif isinstance(name, io.BytesIO):
            bytes = name.getvalue().strip()
            if _is_svg(bytes):
                return self._vector_image(name, x, y, w, h, link, title, alt_text)
            img_hash = hashlib.new("md5", usedforsecurity=False)  # nosec B324
            img_hash.update(bytes)
            name, img = img_hash.hexdigest(), name
        else:
            name, img = str(name), name
        info = self.images.get(name)
        if info:
            info["usages"] += 1
        else:
            if not img:
                img = load_image(name)
            info = get_img_info(img, self.image_filter)
            info["i"] = len(self.images) + 1
            info["usages"] = 1
            self.images[name] = info
        if "smask" in info:
            self._set_min_pdf_version("1.4")

        # Automatic width and height calculation if needed
        if w == 0 and h == 0:  # Put image at 72 dpi
            w = info["w"] / self.k
            h = info["h"] / self.k
        elif w == 0:
            w = h * info["w"] / info["h"]
        elif h == 0:
            h = w * info["h"] / info["w"]

        if self.oversized_images and info["usages"] == 1:
            info = self._downscale_image(name, img, info, w, h)

        # Flowing mode
        if y is None:
            self._perform_page_break_if_need_be(h)
            y = self.y
            self.y += h
        if x is None:
            x = self.x

        stream_content = (
            f"q {w * self.k:.2f} 0 0 {h * self.k:.2f} {x * self.k:.2f} "
            f"{(self.h - y - h) * self.k:.2f} cm /I{info['i']} Do Q"
        )
        if title or alt_text:
            with self._marked_sequence(title=title, alt_text=alt_text):
                self._out(stream_content)
        else:
            self._out(stream_content)
        if link:
            self.link(x, y, w, h, link)

        return info

    def _vector_image(
        self,
        img: io.BytesIO,
        x=None,
        y=None,
        w=0,
        h=0,
        link="",
        title=None,
        alt_text=None,
    ):
        svg = SVGObject(img.getvalue())
        if w == 0 and h == 0:
            if not svg.width or not svg.height:
                raise ValueError(
                    '<svg> has no "height" / "width": w= or h= must be provided to FPDF.image()'
                )
            w = (
                svg.width * self.epw / 100
                if isinstance(svg.width, Percent)
                else svg.width
            )
            h = (
                svg.height * self.eph / 100
                if isinstance(svg.height, Percent)
                else svg.height
            )
        else:
            _, _, vw, vh = svg.viewbox
            if w == 0:
                w = vw * h / vh
            elif h == 0:
                h = vh * w / vw

        # Flowing mode
        if y is None:
            self._perform_page_break_if_need_be(h)
            y = self.y
            self.y += h
        if x is None:
            x = self.x

        _, _, path = svg.transform_to_rect_viewport(
            scale=1, width=w, height=h, ignore_svg_top_attrs=True
        )
        path.transform = path.transform @ drawing.Transform.translation(x, y)

        old_x, old_y = self.x, self.y
        try:
            self.set_xy(0, 0)
            if title or alt_text:
                with self._marked_sequence(title=title, alt_text=alt_text):
                    self.draw_path(path)
            else:
                self.draw_path(path)
        finally:
            self.set_xy(old_x, old_y)
        if link:
            self.link(x, y, w, h, link)

    def _downscale_image(self, name, img, info, w, h):
        width_in_pt, height_in_pt = w * self.k, h * self.k
        lowres_name = f"lowres-{name}"
        lowres_info = self.images.get(lowres_name)
        if (
            info["w"] > width_in_pt * self.oversized_images_ratio
            and info["h"] > height_in_pt * self.oversized_images_ratio
        ):
            factor = (
                min(info["w"] / width_in_pt, info["h"] / height_in_pt)
                / self.oversized_images_ratio
            )
            if self.oversized_images.lower().startswith("warn"):
                LOGGER.warning(
                    "OVERSIZED: Image %s with size %.1fx%.1fpx is rendered at size %.1fx%.1fpt."
                    " Set pdf.oversized_images = 'DOWNSCALE' to reduce embedded image size by a factor %.1f",
                    name,
                    info["w"],
                    info["h"],
                    width_in_pt,
                    height_in_pt,
                    factor,
                )
            elif self.oversized_images.lower() == "downscale":
                dims = (
                    round(width_in_pt * self.oversized_images_ratio),
                    round(height_in_pt * self.oversized_images_ratio),
                )
                info["usages"] -= 1  # no need to embed the high-resolution image
                if lowres_info:  # Great, we've already done the job!
                    info = lowres_info
                    if info["w"] * info["h"] < dims[0] * dims[1]:
                        # The existing low-res image is too small, we need a bigger low-res image:
                        info.update(
                            get_img_info(
                                img or load_image(name), self.image_filter, dims
                            )
                        )
                        LOGGER.debug(
                            "OVERSIZED: Updated low-res image with name=%s id=%d to dims=%s",
                            lowres_name,
                            info["i"],
                            dims,
                        )
                    info["usages"] += 1
                else:
                    info = get_img_info(
                        img or load_image(name), self.image_filter, dims
                    )
                    info["i"] = len(self.images) + 1
                    info["usages"] = 1
                    self.images[lowres_name] = info
                    LOGGER.debug(
                        "OVERSIZED: Generated new low-res image with name=%s dims=%s id=%d",
                        lowres_name,
                        dims,
                        info["i"],
                    )
            else:
                raise ValueError(
                    f"Invalid value for attribute .oversized_images: {self.oversized_images}"
                )
        elif lowres_info:
            # Embedding the same image in high-res after inserting it in low-res:
            lowres_info.update(info)
            del self.images[name]
            info = lowres_info
        return info

    @contextmanager
    def _marked_sequence(self, **kwargs):
        """
        Can receive as named arguments any of the entries described in section 14.7.2 'Structure Hierarchy'
        of the PDF spec: iD, a, c, r, lang, e, actualText
        """
        page_object_id = object_id_for_page(self.page)
        mcid = self.struct_builder.next_mcid_for_page(page_object_id)
        marked_content = self._add_marked_content(
            page_object_id, struct_type="/Figure", mcid=mcid, **kwargs
        )
        start_page = self.page
        self._out(f"/P <</MCID {mcid}>> BDC")
        yield marked_content
        if self.page != start_page:
            raise FPDFException("A page jump occured inside a marked sequence")
        self._out("EMC")

    def _add_marked_content(self, page_object_id, **kwargs):
        """
        Can receive as named arguments any of the entries described in section 14.7.2 'Structure Hierarchy'
        of the PDF spec: iD, a, c, r, lang, e, actualText
        """
        struct_parents_id = self._struct_parents_id_per_page.get(page_object_id)
        if struct_parents_id is None:
            struct_parents_id = len(self._struct_parents_id_per_page)
            self._struct_parents_id_per_page[page_object_id] = struct_parents_id
        marked_content = MarkedContent(page_object_id, struct_parents_id, **kwargs)
        self.struct_builder.add_marked_content(marked_content)
        self._set_min_pdf_version("1.4")  # due to using /MarkInfo
        return marked_content

    @check_page
    def ln(self, h=None):
        """
        Line Feed.
        The current abscissa goes back to the left margin and the ordinate increases by
        the amount passed as parameter.

        Args:
            h (float): The height of the break.
                By default, the value equals the height of the last printed cell.
        """
        self.x = self.l_margin
        self.y += self.lasth if h is None else h

    def get_x(self):
        """Returns the abscissa of the current position."""
        return self.x

    def set_x(self, x):
        """
        Defines the abscissa of the current position.
        If the value provided is negative, it is relative to the right of the page.

        Args:
            x (float): the new current abscissa
        """
        self.x = x if x >= 0 else self.w + x

    def get_y(self):
        """Returns the ordinate of the current position."""
        return self.y

    def set_y(self, y):
        """
        Moves the current abscissa back to the left margin and sets the ordinate.
        If the value provided is negative, it is relative to the bottom of the page.

        Args:
            y (float): the new current ordinate
        """
        self.x = self.l_margin
        self.y = y if y >= 0 else self.h + y

    def set_xy(self, x, y):
        """
        Defines the abscissa and ordinate of the current position.
        If the values provided are negative, they are relative respectively to the right and bottom of the page.

        Args:
            x (float): the new current abscissa
            y (float): the new current ordinate
        """
        self.set_y(y)
        self.set_x(x)

    def output(self, name="", dest=""):
        """
        Output PDF to some destination.
        The method first calls [close](close.md) if necessary to terminate the document.
        After calling this method, content cannot be added to the document anymore.

        By default the bytearray buffer is returned.
        If a `name` is given, the PDF is written to a new file.

        Args:
            name (str): optional File object or file path where to save the PDF under
            dest (str): [**DEPRECATED since 2.3.0**] unused, will be removed in a later version
        """
        if dest:
            warnings.warn(
                '"dest" parameter is deprecated, unused and will soon be removed',
                DeprecationWarning,
                stacklevel=2,
            )
        # Finish document if necessary:
        if self.state < DocumentState.CLOSED:
            self.close()
        if name:
            if isinstance(name, os.PathLike):
                name.write_bytes(self.buffer)
            elif isinstance(name, str):
                Path(name).write_bytes(self.buffer)
            else:
                name.write(self.buffer)
            return None
        return self.buffer

    def normalize_text(self, txt):
        """Check that text input is in the correct format/encoding"""
        # - for TTF unicode fonts: unicode object (utf8 encoding)
        # - for built-in fonts: string instances (encoding: latin-1, cp1252)
        if not self.unifontsubset and self.core_fonts_encoding:
            try:
                return txt.encode(self.core_fonts_encoding).decode("latin-1")
            except UnicodeEncodeError as error:
                raise FPDFUnicodeEncodingException(
                    text_index=error.start,
                    character=txt[error.start],
                    font_name=self.font_family + self.font_style,
                ) from error
        return txt

    def sign_pkcs12(
        self,
        pkcs_filepath,
        password=None,
        hashalgo="sha256",
        contact_info=None,
        location=None,
        signing_time=None,
        reason=None,
        flags=(AnnotationFlag.PRINT, AnnotationFlag.LOCKED),
    ):
        """
        Args:
            pkcs_filepath (str): file path to a .pfx or .p12 PKCS12,
                in the binary format described by RFC 7292
            password (bytes-like): the password to use to decrypt the data.
                `None` if the PKCS12 is not encrypted.
            hashalgo (str): hashing algorithm used, passed to `hashlib.new`
            contact_info (str): optional information provided by the signer to enable
                a recipient to contact the signer to verify the signature
            location (str): optional CPU host name or physical location of the signing
            signing_time (datetime): optional time of signing
            reason (str): optional signing reason
            flags (Tuple[fpdf.enums.AnnotationFlag], Tuple[str]): optional list of flags defining annotation properties
        """
        if not signer:
            raise EnvironmentError(
                "endesive.signer not available - PDF cannot be signed - Try: pip install endesive"
            )
        with open(pkcs_filepath, "rb") as pkcs_file:
            key, cert, extra_certs = pkcs12.load_key_and_certificates(
                pkcs_file.read(), password
            )
        self.sign(
            key=key,
            cert=cert,
            extra_certs=extra_certs,
            hashalgo=hashalgo,
            contact_info=contact_info,
            location=location,
            signing_time=signing_time,
            reason=reason,
            flags=flags,
        )

    @check_page
    def sign(
        self,
        key,
        cert,
        extra_certs=(),
        hashalgo="sha256",
        contact_info=None,
        location=None,
        signing_time=None,
        reason=None,
        flags=(AnnotationFlag.PRINT, AnnotationFlag.LOCKED),
    ):
        """
        Args:
            key: certificate private key
            cert (cryptography.x509.Certificate): certificate
            extra_certs (list[cryptography.x509.Certificate]): list of additional PKCS12 certificates
            hashalgo (str): hashing algorithm used, passed to `hashlib.new`
            contact_info (str): optional information provided by the signer to enable
                a recipient to contact the signer to verify the signature
            location (str): optional CPU host name or physical location of the signing
            signing_time (datetime): optional time of signing
            reason (str): optional signing reason
            flags (Tuple[fpdf.enums.AnnotationFlag], Tuple[str]): optional list of flags defining annotation properties
        """
        if not signer:
            raise EnvironmentError(
                "endesive.signer not available - PDF cannot be signed - Try: pip install endesive"
            )
        if self._sign_key:
            raise FPDFException(".sign* methods should be called only once")

        self._sign_key = key
        self._sign_cert = cert
        self._sign_extra_certs = extra_certs
        self._sign_hashalgo = hashalgo
        self._sign_time = signing_time or self.creation_date

        annotation = Annotation(
            "Widget",
            field_type="Sig",
            x=0,
            y=0,
            width=0,
            height=0,
            flags=flags,
            title="signature",
            value=Signature(
                contact_info=contact_info,
                location=location,
                m=format_date(self._sign_time),
                reason=reason,
            ),
        )
        self.annots_as_obj[self.page].append(annotation)

    def _putpages(self):
        nb = self.pages_count  # total number of pages
        if self.str_alias_nb_pages:
            self._substitute_page_number()
        if self._toc_placeholder:
            self._insert_table_of_contents()
        if self.def_orientation == "P":
            dw_pt = self.dw_pt
            dh_pt = self.dh_pt
        else:
            dw_pt = self.dh_pt
            dh_pt = self.dw_pt
        filter = "/Filter /FlateDecode " if self.compress else ""

        # The Annotations embedded as PDF objects
        # are added to the document just after all the pages,
        # hence we can deduce their object IDs:
        annot_obj_id = object_id_for_page(nb) + 2

        for n in range(1, nb + 1):
            # Page
            self._newobj()
            self._out("<</Type /Page")
            self._out(f"/Parent {pdf_ref(1)}")
            page = self.pages[n]
            if page["duration"]:
                self._out(f"/Dur {page['duration']}")
            if page["transition"]:
                self._out(f"/Trans {page['transition'].dict_as_string()}")
            w_pt, h_pt = page["w_pt"], page["h_pt"]
            if w_pt != dw_pt or h_pt != dh_pt:
                self._out(f"/MediaBox [0 0 {w_pt:.2f} {h_pt:.2f}]")
            self._out(f"/Resources {pdf_ref(2)}")
            annot_obj_id = self._put_page_annotations(n, annot_obj_id)
            if self.pdf_version > "1.3":
                self._out("/Group <</Type /Group /S /Transparency /CS /DeviceRGB>>")
            spid = self._struct_parents_id_per_page.get(self.n)
            if spid is not None:
                self._out(f"/StructParents {spid}")
            self._out(f"/Contents {pdf_ref(self.n + 1)}>>")
            self._out("endobj")

            # Page content
            content = page["content"]
            p = zlib.compress(content) if self.compress else content
            self._newobj()
            self._out(f"<<{filter}/Length {len(p)}>>")
            self._out(pdf_stream(p))
            self._out("endobj")
        # Pages root
        self.offsets[1] = len(self.buffer)
        self._out("1 0 obj")
        self._out("<</Type /Pages")
        self._out(
            "/Kids ["
            + " ".join(pdf_ref(object_id_for_page(page)) for page in range(1, nb + 1))
            + "]"
        )
        self._out(f"/Count {nb}")
        self._out(f"/MediaBox [0 0 {dw_pt:.2f} {dh_pt:.2f}]")
        self._out(">>")
        self._out("endobj")

    def _put_page_annotations(self, page_number, annot_obj_id):
        page_annots = self.annots[page_number]
        page_annots_as_obj = self.annots_as_obj[page_number]
        if page_annots or page_annots_as_obj:
            # Annotations, e.g. links:
            annots = ""
            for annot in page_annots:
                annots += annot.serialize(self)
                if annot.alt_text is not None:
                    # Note: the spec indicates that a /StructParent could be added **inside* this /Annot,
                    # but tests with Adobe Acrobat Reader reveal that the page /StructParents inserted below
                    # is enough to link the marked content in the hierarchy tree with this annotation link.
                    self._add_marked_content(
                        self.n, struct_type="/Link", alt_text=annot.alt_text
                    )
                if annot.quad_points:
                    self._set_min_pdf_version("1.6")
            if page_annots and page_annots_as_obj:
                annots += " "
            annots += " ".join(
                f"{annot_obj_id + i} 0 R" for i in range(len(page_annots_as_obj))
            )
            annot_obj_id += len(page_annots_as_obj)
            self._out(f"/Annots [{annots}]")
        return annot_obj_id

    def _substitute_page_number(self):
        nb = self.pages_count  # total number of pages
        substituted = False
        # Replace number of pages in fonts using subsets (unicode)
        alias = self.str_alias_nb_pages.encode("utf-16-be")
        encoded_nb = str(nb).encode("utf-16-be")
        for page in self.pages.values():
            new_content = page["content"].replace(alias, encoded_nb)
            substituted |= page["content"] != new_content
            page["content"] = new_content
        # Now repeat for no pages in non-subset fonts
        alias = self.str_alias_nb_pages.encode("latin-1")
        encoded_nb = str(nb).encode("latin-1")
        for page in self.pages.values():
            new_content = page["content"].replace(alias, encoded_nb)
            substituted |= page["content"] != new_content
            page["content"] = new_content
        if substituted:
            LOGGER.debug(
                "Substitution of '%s' was performed in the document",
                self.str_alias_nb_pages,
            )

    def _insert_table_of_contents(self):
        prev_state = self.state
        tocp = self._toc_placeholder
        self.page = tocp.start_page
        # Doc has been closed but we want to write to self.pages[self.page] instead of self.buffer:
        self.state = DocumentState.GENERATING_PAGE
        self.y = tocp.y
        tocp.render_function(self, self._outline)
        expected_final_page = tocp.start_page + tocp.pages - 1
        if self.page != expected_final_page:
            too = "many" if self.page > expected_final_page else "few"
            error_msg = f"The rendering function passed to FPDF.insert_toc_placeholder triggered too {too} page breaks: "
            error_msg += f"ToC ended on page {self.page} while it was expected to span exactly {tocp.pages} pages"
            raise FPDFException(error_msg)
        self.state = prev_state

    def _putfonts(self):
        nf = self.n
        for diff in self.diffs.values():
            # Encodings
            self._newobj()
            self._out(
                "<</Type /Encoding /BaseEncoding /WinAnsiEncoding "
                + "/Differences ["
                + diff
                + "]>>"
            )
            self._out("endobj")

        for name, info in self.font_files.items():
            if "type" in info and info["type"] != "TTF":
                # Font file embedding
                self._newobj()
                info["n"] = self.n
                font = (FPDF_FONT_DIR / name).read_bytes()
                compressed = substr(name, -2) == ".z"
                if not compressed and "length2" in info:
                    header = ord(font[0]) == 128
                    if header:
                        # Strip first binary header
                        font = substr(font, 6)
                    if header and ord(font[info["length1"]]) == 128:
                        # Strip second binary header
                        font = substr(font, 0, info["length1"]) + substr(
                            font, info["length1"] + 6
                        )

                self._out(f"<</Length {len(font)}")
                if compressed:
                    self._out("/Filter /FlateDecode")
                self._out(f"/Length1 {info['length1']}")
                if "length2" in info:
                    self._out(f"/Length2 {info['length2']} /Length3 0")
                self._out(">>")
                self._out(pdf_stream(font))
                self._out("endobj")

        # Font objects
        flist = [(x[1]["i"], x[0], x[1]) for x in self.fonts.items()]
        flist.sort()
        for _, font_name, font in flist:
            self.fonts[font_name]["n"] = self.n + 1
            my_type = font["type"]
            name = font["name"]
            # Standard font
            if my_type == "core":
                self._newobj()
                self._out("<</Type /Font")
                self._out(f"/BaseFont /{name}")
                self._out("/Subtype /Type1")
                if name not in ("Symbol", "ZapfDingbats"):
                    self._out("/Encoding /WinAnsiEncoding")
                self._out(">>")
                self._out("endobj")

            # Additional Type1 or TrueType font
            elif my_type in ("Type1", "TrueType"):
                self._newobj()
                self._out("<</Type /Font")
                self._out(f"/BaseFont /{name}")
                self._out(f"/Subtype /{my_type}")
                self._out("/FirstChar 32 /LastChar 255")
                self._out(f"/Widths {pdf_ref(self.n + 1)}")
                self._out(f"/FontDescriptor {pdf_ref(self.n + 2)}")
                if font["enc"]:
                    if "diff" in font:
                        self._out(f"/Encoding {pdf_ref(nf + font['diff'])}")
                    else:
                        self._out("/Encoding /WinAnsiEncoding")
                self._out(">>")
                self._out("endobj")

                # Widths
                self._newobj()
                self._out(
                    "["
                    + " ".join(_char_width(font, chr(i)) for i in range(32, 256))
                    + "]"
                )
                self._out("endobj")

                # Descriptor
                self._newobj()
                s = f"<</Type /FontDescriptor /FontName /{name}"
                for k in (
                    "Ascent",
                    "Descent",
                    "CapHeight",
                    "Flags",
                    "FontBBox",
                    "ItalicAngle",
                    "StemV",
                    "MissingWidth",
                ):
                    s += f" /{k} {font['desc'][k]}"

                filename = font["file"]
                if filename:
                    s += " /FontFile"
                    if my_type != "Type1":
                        s += "2"
                    s += " " + pdf_ref(self.font_files[filename]["n"])
                self._out(f"{s}>>")
                self._out("endobj")
            elif my_type == "TTF":
                self.fonts[font_name]["n"] = self.n + 1
                fontname = f"MPDFAA+{font['name']}"
                subset = font["subset"].dict()

                # why we delete 0-element?
                del subset[0]

                # ---- FONTTOOLS SUBSETTER ----
                # recalcTimestamp=False means that it doesn't modify the "modified" timestamp in head table
                # if we leave recalcTimestamp=True the tests will break every time
                fonttools_font = ttLib.TTFont(
                    file=font["ttffile"], recalcTimestamp=False
                )

                # 1. get all glyphs in PDF
                cmap = fonttools_font["cmap"].getBestCmap()
                glyph_names = [cmap[code] for code in subset if code in cmap]

                # 2. make a subset
                # notdef_outline=True means that keeps the white box for the .notdef glyph
                # recommended_glyphs=True means that adds the .notdef, .null, CR, and space glyphs
                options = ftsubset.Options(notdef_outline=True, recommended_glyphs=True)
                options.drop_tables += ["GDEF", "GSUB", "GPOS", "MATH", "hdmx"]
                subsetter = ftsubset.Subsetter(options)
                subsetter.populate(glyphs=glyph_names)
                subsetter.subset(fonttools_font)

                # 3. make codeToGlyph
                # is a map Character_ID -> Glyph_ID
                # it's used for associating glyphs to new codes
                # this basically takes the old code of the character
                # take the glyph associated with it
                # and then associate to the new code the glyph associated with the old code
                code_to_glyph = {}
                for code, new_code_mapped in subset.items():
                    if code in cmap:
                        glyph_name = cmap[code]
                        code_to_glyph[new_code_mapped] = fonttools_font.getGlyphID(
                            glyph_name
                        )
                    else:
                        # notdef is associated if no glyph was associated to the old code
                        # it's not necessary to do this, it seems to be done by default
                        code_to_glyph[new_code_mapped] = fonttools_font.getGlyphID(
                            ".notdef"
                        )

                max_unicode = max(subset)

                # 4. return the ttfile
                output = BytesIO()
                fonttools_font.save(output)

                output.seek(0)
                ttfontstream = output.read()
                ttfontsize = len(ttfontstream)
                fontstream = zlib.compress(ttfontstream)

                # Type0 Font
                # A composite font - a font composed of other fonts,
                # organized hierarchically
                self._newobj()
                self._out("<</Type /Font")
                self._out("/Subtype /Type0")
                self._out(f"/BaseFont /{fontname}")
                self._out("/Encoding /Identity-H")
                self._out(f"/DescendantFonts [{pdf_ref(self.n + 1)}]")
                self._out(f"/ToUnicode {pdf_ref(self.n + 2)}")
                self._out(">>")
                self._out("endobj")

                # CIDFontType2
                # A CIDFont whose glyph descriptions are based on
                # TrueType font technology
                self._newobj()
                self._out("<</Type /Font")
                self._out("/Subtype /CIDFontType2")
                self._out(f"/BaseFont /{fontname}")
                self._out(f"/CIDSystemInfo {pdf_ref(self.n + 2)}")
                self._out(f"/FontDescriptor {pdf_ref(self.n + 3)}")
                if font["desc"].get("MissingWidth"):
                    self._out(f"/DW {font['desc']['MissingWidth']}")
                self._putTTfontwidths(font, max_unicode)
                self._out(f"/CIDToGIDMap {pdf_ref(self.n + 4)}")
                self._out(">>")
                self._out("endobj")

                # bfChar
                # This table informs the PDF reader about the unicode
                # character that each used 16-bit code belongs to. It
                # allows searching the file and copying text from it.
                bfChar = []
                subset = font["subset"].dict()
                for code in subset:
                    code_mapped = subset.get(code)
                    if code > 0xFFFF:
                        # Calculate surrogate pair
                        code_high = 0xD800 | (code - 0x10000) >> 10
                        code_low = 0xDC00 | (code & 0x3FF)
                        bfChar.append(
                            f"<{code_mapped:04X}> <{code_high:04X}{code_low:04X}>\n"
                        )
                    else:
                        bfChar.append(f"<{code_mapped:04X}> <{code:04X}>\n")

                # ToUnicode
                self._newobj()
                toUni = (
                    "/CIDInit /ProcSet findresource begin\n"
                    "12 dict begin\n"
                    "begincmap\n"
                    "/CIDSystemInfo\n"
                    "<</Registry (Adobe)\n"
                    "/Ordering (UCS)\n"
                    "/Supplement 0\n"
                    ">> def\n"
                    "/CMapName /Adobe-Identity-UCS def\n"
                    "/CMapType 2 def\n"
                    "1 begincodespacerange\n"
                    "<0000> <FFFF>\n"
                    "endcodespacerange\n"
                    f"{len(bfChar)} beginbfchar\n"
                    f"{''.join(bfChar)}"
                    "endbfchar\n"
                    "endcmap\n"
                    "CMapName currentdict /CMap defineresource pop\n"
                    "end\n"
                    "end"
                )
                self._out(f"<</Length {len(toUni)}>>")
                self._out(pdf_stream(toUni))
                self._out("endobj")

                # CIDSystemInfo dictionary
                self._newobj()
                self._out("<</Registry (Adobe)")
                self._out("/Ordering (UCS)")
                self._out("/Supplement 0")
                self._out(">>")
                self._out("endobj")

                # Font descriptor
                self._newobj()
                self._out("<</Type /FontDescriptor")
                self._out("/FontName /" + fontname)
                for kd in (
                    "Ascent",
                    "Descent",
                    "CapHeight",
                    "Flags",
                    "FontBBox",
                    "ItalicAngle",
                    "StemV",
                    "MissingWidth",
                ):
                    v = font["desc"][kd]
                    if kd == "Flags":
                        v = v | 4
                        v = v & ~32  # SYMBOLIC font flag
                    self._out(f" /{kd} {v}")
                self._out(f"/FontFile2 {pdf_ref(self.n + 2)}")
                self._out(">>")
                self._out("endobj")

                # Embed CIDToGIDMap
                # A specification of the mapping from CIDs to glyph indices
                cid_to_gid_map = ["\x00"] * 256 * 256 * 2
                for cc, glyph in code_to_glyph.items():
                    cid_to_gid_map[cc * 2] = chr(glyph >> 8)
                    cid_to_gid_map[cc * 2 + 1] = chr(glyph & 0xFF)
                cid_to_gid_map = "".join(cid_to_gid_map)

                # manage binary data as latin1 until PEP461-like function is implemented
                cid_to_gid_map = zlib.compress(cid_to_gid_map.encode("latin1"))

                self._newobj()
                self._out(f"<</Length {len(cid_to_gid_map)}")
                self._out("/Filter /FlateDecode")
                self._out(">>")
                self._out(pdf_stream(cid_to_gid_map))
                self._out("endobj")

                # Font file
                self._newobj()
                self._out(f"<</Length {len(fontstream)}")
                self._out("/Filter /FlateDecode")
                self._out(f"/Length1 {ttfontsize}")
                self._out(">>")
                self._out(pdf_stream(fontstream))
                self._out("endobj")
            else:
                # Allow for additional types
                mtd = f"_put{my_type.lower()}"
                # check if self has a attr mtd which is callable (method)
                if not callable(getattr(self, mtd, None)):
                    raise FPDFException(f"Unsupported font type: {my_type}")
                self.mtd(font)  # pylint: disable=no-member

    def _putTTfontwidths(self, font, maxUni):
        rangeid = 0
        range_ = {}
        range_interval = {}
        prevcid = -2
        prevwidth = -1
        interval = False
        startcid = 1
        cwlen = maxUni + 1

        # for each character
        subset = font["subset"].dict()
        for cid in range(startcid, cwlen):
            width = _char_width(font, cid)
            if "dw" not in font or (font["dw"] and width != font["dw"]):
                cid_mapped = subset.get(cid)
                if cid_mapped is None:
                    continue
                if cid_mapped == (prevcid + 1):
                    if width == prevwidth:
                        if width == range_[rangeid][0]:
                            range_.setdefault(rangeid, []).append(width)
                        else:
                            range_[rangeid].pop()
                            # new range
                            rangeid = prevcid
                            range_[rangeid] = [prevwidth, width]
                        interval = True
                        range_interval[rangeid] = True
                    else:
                        if interval:
                            # new range
                            rangeid = cid_mapped
                            range_[rangeid] = [width]
                        else:
                            range_[rangeid].append(width)
                        interval = False
                else:
                    rangeid = cid_mapped
                    range_[rangeid] = [width]
                    interval = False
                prevcid = cid_mapped
                prevwidth = width
        prevk = -1
        nextk = -1
        prevint = False

        ri = range_interval
        for k, ws in sorted(range_.items()):
            cws = len(ws)
            if k == nextk and not prevint and (k not in ri or cws < 3):
                if k in ri:
                    del ri[k]
                range_[prevk] = range_[prevk] + range_[k]
                del range_[k]
            else:
                prevk = k
            nextk = k + cws
            if k in ri:
                prevint = cws > 3
                del ri[k]
                nextk -= 1
            else:
                prevint = False
        w = []
        for k, ws in sorted(range_.items()):
            if len(set(ws)) == 1:
                w.append(f" {k} {k + len(ws) - 1} {ws[0]}")
            else:
                w.append(f" {k} [ {' '.join(str(int(h)) for h in ws)} ]\n")
        self._out(f"/W [{''.join(w)}]")

    def _putimages(self):
        for img_info in sorted(
            self.images.values(), key=lambda img_info: img_info["i"]
        ):
            if img_info["usages"] > 0:
                self._putimage(img_info)

    def _putimage(self, info):
        if "data" not in info:
            return
        self._newobj()
        info["n"] = self.n
        self._out("<</Type /XObject")
        self._out("/Subtype /Image")
        self._out(f"/Width {info['w']}")
        self._out(f"/Height {info['h']}")

        if info["cs"] == "Indexed":
            palette_ref = (
                pdf_ref(self.n + 2)
                if self.allow_images_transparency and "smask" in info
                else pdf_ref(self.n + 1)
            )
            self._out(
                f"/ColorSpace [/Indexed /DeviceRGB "
                f"{len(info['pal']) // 3 - 1} {palette_ref}]"
            )
        else:
            self._out(f"/ColorSpace /{info['cs']}")
            if info["cs"] == "DeviceCMYK":
                self._out("/Decode [1 0 1 0 1 0 1 0]")

        self._out(f"/BitsPerComponent {info['bpc']}")

        if "f" in info:
            self._out(f"/Filter /{info['f']}")
        if "dp" in info:
            self._out(f"/DecodeParms <<{info['dp']}>>")

        if "trns" in info and isinstance(info["trns"], list):
            trns = " ".join(f"{x} {x}" for x in info["trns"])
            self._out(f"/Mask [{trns}]")

        if self.allow_images_transparency and "smask" in info:
            self._out(f"/SMask {pdf_ref(self.n + 1)}")

        self._out(f"/Length {len(info['data'])}>>")
        self._out(pdf_stream(info["data"]))
        self._out("endobj")

        # Soft mask
        if self.allow_images_transparency and "smask" in info:
            dp = f"/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns {info['w']}"
            smask = {
                "w": info["w"],
                "h": info["h"],
                "cs": "DeviceGray",
                "bpc": 8,
                "f": info["f"],
                "dp": dp,
                "data": info["smask"],
            }
            self._putimage(smask)

        # Palette
        if info["cs"] == "Indexed":
            self._newobj()
            if self.compress:
                filter, pal = ("/Filter /FlateDecode ", zlib.compress(info["pal"]))
            else:
                filter, pal = ("", info["pal"])
            self._out(f"<<{filter}/Length {len(pal)}>>")
            self._out(pdf_stream(pal))
            self._out("endobj")

    def _putxobjectdict(self):
        img_ids = [
            (img_info["i"], img_info["n"])
            for img_info in self.images.values()
            if img_info["usages"]
        ]
        img_ids.sort()
        for idx, n in img_ids:
            self._out(f"/I{idx} {pdf_ref(n)}")

    def _put_graphics_state_dicts(self):
        for state_dict, name in self._drawing_graphics_state_registry.items():
            self._newobj()
            self._graphics_state_obj_refs[name] = self.n
            self._out(state_dict)
            self._out("endobj")

    def _put_graphics_state_refs(self):
        for name, obj_id in self._graphics_state_obj_refs.items():
            self._out(f"{drawing.render_pdf_primitive(name)} {pdf_ref(obj_id)}")

    def _putresourcedict(self):
        # From section 10.1, "Procedure Sets", of PDF 1.7 spec:
        # > Beginning with PDF 1.4, this feature is considered obsolete.
        # > For compatibility with existing consumer applications,
        # > PDF producer applications should continue to specify procedure sets
        # > (preferably, all of those listed in Table 10.1).
        self._out("/ProcSet [/PDF /Text /ImageB /ImageC /ImageI]")
        self._out("/Font <<")
        font_ids = [(x["i"], x["n"]) for x in self.fonts.values()]
        font_ids.sort()
        for idx, n in font_ids:
            self._out(f"/F{idx} {pdf_ref(n)}")
        self._out(">>")

        # if self.images: [TODO] uncomment this & indent the next 3 lines in order to save 15 bytes / page without image
        self._out("/XObject <<")
        self._putxobjectdict()
        self._out(">>")

        if self._drawing_graphics_state_registry:
            self._out("/ExtGState <<")
            self._put_graphics_state_refs()
            self._out(">>")

    def _putresources(self):
        with self._trace_size("resources.fonts"):
            self._putfonts()
        with self._trace_size("resources.images"):
            self._putimages()
        with self._trace_size("resources.gfxstate"):
            self._put_graphics_state_dicts()

        # Resource dictionary
        with self._trace_size("resources.dict"):
            self.offsets[2] = len(self.buffer)
            self._out("2 0 obj")
            self._out("<<")
            self._putresourcedict()
            self._out(">>")
            self._out("endobj")

    def _put_structure_tree(self):
        "Builds a Structure Hierarchy, including image alternate descriptions"
        # This property is later used by _putcatalog to insert a reference to the StructTreeRoot:
        self._struct_tree_root_obj_id = self.n + 1
        self.struct_builder.serialize(
            first_object_id=self._struct_tree_root_obj_id, fpdf=self
        )

    def _put_annotations_as_objects(self):
        sig_annotation_obj_id = None
        # The following code inserts annotations in the order
        # they have been inserted in the pages / .annots_as_obj dict;
        # this relies on a property of Python dicts since v3.7:
        for page_annots_as_obj in self.annots_as_obj.values():
            for annot in page_annots_as_obj:
                self._newobj()
                self._out(annot.serialize(self))
                self._out("endobj")
                if isinstance(annot.value, Signature):
                    sig_annotation_obj_id = self.n
        return sig_annotation_obj_id

    def _put_document_outline(self):
        # This property is later used by _putcatalog to insert a reference to the Outlines:
        self._outlines_obj_id = self.n + 1
        serialize_outline(
            self._outline, first_object_id=self._outlines_obj_id, fpdf=self
        )

    def _put_xmp_metadata(self):
        xpacket = f'<?xpacket begin="ï»¿" id="W5M0MpCehiHzreSzNTczkc9d"?>\n{self.xmp_metadata}\n<?xpacket end="w"?>\n'
        self._newobj()
        self._out(f"<</Type /Metadata /Subtype /XML /Length {len(xpacket)}>>")
        self._out(pdf_stream(xpacket))
        self._out("endobj")
        self._xmp_metadata_obj_id = self.n

    def _putinfo(self):
        info_d = {
            "/Title": enclose_in_parens(getattr(self, "title", None)),
            "/Subject": enclose_in_parens(getattr(self, "subject", None)),
            "/Author": enclose_in_parens(getattr(self, "author", None)),
            "/Keywords": enclose_in_parens(getattr(self, "keywords", None)),
            "/Creator": enclose_in_parens(getattr(self, "creator", None)),
            "/Producer": enclose_in_parens(getattr(self, "producer", None)),
        }

        if self.creation_date:
            try:
                info_d["/CreationDate"] = format_date(self.creation_date, with_tz=True)
            except Exception as error:
                raise FPDFException(
                    f"Could not format date: {self.creation_date}"
                ) from error

        self._out(pdf_dict(info_d, open_dict="", close_dict="", has_empty_fields=True))

    def _putcatalog(self, sig_annotation_obj_id=None):
        catalog_d = {
            "/Type": "/Catalog",
            # Pages is always the 1st object of the document, cf. the end of _putpages:
            "/Pages": pdf_ref(1),
        }
        lang = enclose_in_parens(getattr(self, "lang", None))
        if lang:
            catalog_d["/Lang"] = lang
        if sig_annotation_obj_id:
            flags = SignatureFlag.SIGNATURES_EXIST + SignatureFlag.APPEND_ONLY
            self._out(
                f"/AcroForm <</Fields [{sig_annotation_obj_id} 0 R] /SigFlags {flags}>>"
            )

        if self.zoom_mode in ZOOM_CONFIGS:
            zoom_config = [
                pdf_ref(3),  # reference to object ID of the 1st page
                *ZOOM_CONFIGS[self.zoom_mode],
            ]
        else:  # zoom_mode is a number, not one of the allowed strings:
            zoom_config = ["/XYZ", "null", "null", str(self.zoom_mode / 100)]
        catalog_d["/OpenAction"] = pdf_list(zoom_config)

        if self.page_layout:
            catalog_d["/PageLayout"] = self.page_layout.value.pdf_repr()
        if self.page_mode:
            catalog_d["/PageMode"] = self.page_mode.value.pdf_repr()
        if self.viewer_preferences:
            catalog_d["/ViewerPreferences"] = self.viewer_preferences.serialize()
        if self._xmp_metadata_obj_id:
            catalog_d["/Metadata"] = pdf_ref(self._xmp_metadata_obj_id)
        if self._struct_tree_root_obj_id:
            catalog_d["/MarkInfo"] = pdf_dict({"/Marked": "true"})
            catalog_d["/StructTreeRoot"] = pdf_ref(self._struct_tree_root_obj_id)
        if self._outlines_obj_id:
            catalog_d["/Outlines"] = pdf_ref(self._outlines_obj_id)

        self._out(pdf_dict(catalog_d, open_dict="", close_dict=""))

    def _putheader(self):
        if self.page_layout in (PageLayout.TWO_PAGE_LEFT, PageLayout.TWO_PAGE_RIGHT):
            self._set_min_pdf_version("1.5")
        if self.page_mode == PageMode.USE_OC:
            self._set_min_pdf_version("1.5")
        if self.page_mode == PageMode.USE_ATTACHMENTS:
            self._set_min_pdf_version("1.6")
        self._out(f"%PDF-{self.pdf_version}")

    def _puttrailer(self):
        self._out(f"/Size {self.n + 1}")
        self._out(f"/Root {pdf_ref(self.n)}")  # Catalog object index
        self._out(f"/Info {pdf_ref(self.n - 1)}")  # Info object index
        file_id = self.file_id()
        if file_id:
            self._out(f"/ID [{file_id}]")

    def file_id(self):
        """
        This method can be overridden in inherited classes
        in order to define a custom file identifier.
        Its output must have the format "<hex_string1><hex_string2>".
        If this method returns a falsy value (None, empty string),
        no /ID will be inserted in the generated PDF document.
        """
        # Quoting the PDF 1.7 spec, section 14.4 File Identifiers:
        # > The value of this entry shall be an array of two byte strings.
        # > The first byte string shall be a permanent identifier
        # > based on the contents of the file at the time it was originally created
        # > and shall not change when the file is incrementally updated.
        # > The second byte string shall be a changing identifier
        # > based on the file’s contents at the time it was last updated.
        # > When a file is first written, both identifiers shall be set to the same value.
        bytes = self.buffer + self.creation_date.strftime("%Y%m%d%H%M%S").encode("utf8")
        id_hash = hashlib.new("md5", usedforsecurity=False)  # nosec B324
        id_hash.update(bytes)
        hash_hex = id_hash.hexdigest().upper()
        return f"<{hash_hex}><{hash_hex}>"

    def _enddoc(self):
        LOGGER.debug("Final doc sections size summary:")
        with self._trace_size("header"):
            self._putheader()
        # It is important that pages are the first PDF objects inserted in the document,
        # followed immediately by annotations: some parts of fpdf2 currently relies on that
        # order of insertion (e.g. util.object_id_for_page):
        with self._trace_size("pages"):
            self._putpages()
        sig_annotation_obj_id = self._put_annotations_as_objects()
        self._putresources()  # trace_size is performed inside
        if not self.struct_builder.empty():
            with self._trace_size("structure_tree"):
                self._put_structure_tree()
        if self._outline:
            with self._trace_size("document_outline"):
                self._put_document_outline()
        if self.xmp_metadata:
            self._put_xmp_metadata()
        # Info
        with self._trace_size("info"):
            self._newobj()
            self._out("<<")
            self._putinfo()
            self._out(">>")
            self._out("endobj")
        # Catalog
        with self._trace_size("catalog"):
            self._newobj()
            self._out("<<")
            self._putcatalog(sig_annotation_obj_id)
            self._out(">>")
            self._out("endobj")
        # Cross-ref
        with self._trace_size("xref"):
            o = len(self.buffer)
            self._out("xref")
            self._out(f"0 {self.n + 1}")
            self._out("0000000000 65535 f ")
            for i in range(1, self.n + 1):
                self._out(f"{self.offsets[i]:010} 00000 n ")
        # Trailer
        with self._trace_size("trailer"):
            self._out("trailer")
            self._out("<<")
            self._puttrailer()
            self._out(">>")
            self._out("startxref")
            self._out(o)
        self._out("%%EOF")
        if self._sign_key:
            self.buffer = sign_content(
                signer,
                self.buffer,
                self._sign_key,
                self._sign_cert,
                self._sign_extra_certs,
                self._sign_hashalgo,
                self._sign_time,
            )
        self.state = DocumentState.CLOSED

    def _beginpage(
        self, orientation, format, same, duration, transition, new_page=True
    ):
        self.page += 1
        if new_page:
            page = {
                "content": bytearray(),
                "duration": duration,
                "transition": transition,
            }
            self.pages[self.page] = page
            if transition:
                self._set_min_pdf_version("1.5")
        else:
            page = self.pages[self.page]
        self.state = DocumentState.GENERATING_PAGE
        self.x = self.l_margin
        self.y = self.t_margin
        self.font_family = ""
        self.font_stretching = 100
        if same:
            if orientation or format:
                raise ValueError(
                    f"Inconsistent parameters: same={same} but orientation={orientation} format={format}"
                )
        else:
            # Set page format if provided, else use default value:
            page_width_pt, page_height_pt = (
                get_page_format(format, self.k) if format else (self.dw_pt, self.dh_pt)
            )
            self._set_orientation(
                orientation or self.def_orientation, page_width_pt, page_height_pt
            )
            self.page_break_trigger = self.h - self.b_margin
        page["w_pt"], page["h_pt"] = self.w_pt, self.h_pt

    def _endpage(self):
        # End of page contents
        self.state = DocumentState.READY

    def _newobj(self):
        # Begin a new object
        self.n += 1
        self.offsets[self.n] = len(self.buffer)
        self._out(f"{self.n} 0 obj")
        return self.n

    def _do_underline(self, x, y, txt, current_font=None):
        "Draw an horizontal line starting from (x, y) with a length equal to 'txt' width"
        if current_font is None:
            current_font = self.current_font
        up = current_font["up"]
        ut = current_font["ut"]
        w = self.get_string_width(txt, True) + self.ws * txt.count(" ")
        return (
            f"{x * self.k:.2f} "
            f"{(self.h - y + up / 1000 * self.font_size) * self.k:.2f} "
            f"{w * self.k:.2f} {-ut / 1000 * self.font_size_pt:.2f} re f"
        )

    def _out(self, s):
        if self.state == DocumentState.CLOSED:
            raise FPDFException(
                "Content cannot be added on a closed document, after calling output()"
            )
        if not isinstance(s, bytes):
            if not isinstance(s, str):
                s = str(s)
            s = s.encode("latin1")
        if self.state == DocumentState.GENERATING_PAGE:
            self.pages[self.page]["content"] += s + b"\n"
        else:
            self.buffer += s + b"\n"

    @check_page
    def interleaved2of5(self, txt, x, y, w=1, h=10):
        """Barcode I2of5 (numeric), adds a 0 if odd length"""
        narrow = w / 3
        wide = w

        # wide/narrow codes for the digits
        bar_char = {
            "0": "nnwwn",
            "1": "wnnnw",
            "2": "nwnnw",
            "3": "wwnnn",
            "4": "nnwnw",
            "5": "wnwnn",
            "6": "nwwnn",
            "7": "nnnww",
            "8": "wnnwn",
            "9": "nwnwn",
            "A": "nn",
            "Z": "wn",
        }
        # The caller should do this, or we can't rotate the thing.
        # self.set_fill_color(0)
        code = txt
        # add leading zero if code-length is odd
        if len(code) % 2 != 0:
            code = f"0{code}"

        # add start and stop codes
        code = f"AA{code.lower()}ZA"

        for i in range(0, len(code), 2):
            # choose next pair of digits
            char_bar = code[i]
            char_space = code[i + 1]
            # check whether it is a valid digit
            if char_bar not in bar_char:
                raise RuntimeError(f'Char "{char_bar}" invalid for I25:')
            if char_space not in bar_char:
                raise RuntimeError(f'Char "{char_space}" invalid for I25: ')

            # create a wide/narrow-seq (first digit=bars, second digit=spaces)
            seq = "".join(
                f"{cb}{cs}" for cb, cs in zip(bar_char[char_bar], bar_char[char_space])
            )

            for bar_index, char in enumerate(seq):
                # set line_width depending on value
                line_width = narrow if char == "n" else wide

                # draw every second value, the other is represented by space
                if bar_index % 2 == 0:
                    self.rect(x, y, line_width, h, "F")

                x += line_width

    @check_page
    def code39(self, txt, x, y, w=1.5, h=5):
        """Barcode 3of9"""
        dim = {"w": w, "n": w / 3}
        if not txt.startswith("*") or not txt.endswith("*"):
            warnings.warn(
                "Code 39 input must start and end with a '*' character to be valid."
                " This method does not insert it automatically."
            )
        chars = {
            "0": "nnnwwnwnn",
            "1": "wnnwnnnnw",
            "2": "nnwwnnnnw",
            "3": "wnwwnnnnn",
            "4": "nnnwwnnnw",
            "5": "wnnwwnnnn",
            "6": "nnwwwnnnn",
            "7": "nnnwnnwnw",
            "8": "wnnwnnwnn",
            "9": "nnwwnnwnn",
            "A": "wnnnnwnnw",
            "B": "nnwnnwnnw",
            "C": "wnwnnwnnn",
            "D": "nnnnwwnnw",
            "E": "wnnnwwnnn",
            "F": "nnwnwwnnn",
            "G": "nnnnnwwnw",
            "H": "wnnnnwwnn",
            "I": "nnwnnwwnn",
            "J": "nnnnwwwnn",
            "K": "wnnnnnnww",
            "L": "nnwnnnnww",
            "M": "wnwnnnnwn",
            "N": "nnnnwnnww",
            "O": "wnnnwnnwn",
            "P": "nnwnwnnwn",
            "Q": "nnnnnnwww",
            "R": "wnnnnnwwn",
            "S": "nnwnnnwwn",
            "T": "nnnnwnwwn",
            "U": "wwnnnnnnw",
            "V": "nwwnnnnnw",
            "W": "wwwnnnnnn",
            "X": "nwnnwnnnw",
            "Y": "wwnnwnnnn",
            "Z": "nwwnwnnnn",
            "-": "nwnnnnwnw",
            ".": "wwnnnnwnn",
            " ": "nwwnnnwnn",
            "*": "nwnnwnwnn",
            "$": "nwnwnwnnn",
            "/": "nwnwnnnwn",
            "+": "nwnnnwnwn",
            "%": "nnnwnwnwn",
        }
        # The caller should do this, or we can't rotate the thing.
        # self.set_fill_color(0)
        for c in txt.upper():
            if c not in chars:
                raise RuntimeError(f'Invalid char "{c}" for Code39')
            for i, d in enumerate(chars[c]):
                if i % 2 == 0:
                    self.rect(x, y, dim[d], h, "F")
                x += dim[d]
            x += dim["n"]

    @check_page
    @contextmanager
    def rect_clip(self, x, y, w, h):
        """
        Context manager that defines a rectangular crop zone,
        useful to render only part of an image.

        Args:
            x (float): abscissa of the clipping region top left corner
            y (float): ordinate of the clipping region top left corner
            w (float): width of the clipping region
            h (float): height of the clipping region
        """
        self._out(
            (
                f"q {x * self.k:.2f} {(self.h - y - h) * self.k:.2f} {w * self.k:.2f} "
                f"{h * self.k:.2f} re W n"
            )
        )
        yield
        self._out("Q")

    @check_page
    @contextmanager
    def elliptic_clip(self, x, y, w, h):
        """
        Context manager that defines an elliptic crop zone,
        useful to render only part of an image.

        Args:
            x (float): abscissa of the clipping region top left corner
            y (float): ordinate of the clipping region top left corner
            w (float): ellipse width
            h (float): ellipse height
        """
        self._out("q")
        self._draw_ellipse(x, y, w, h, "W n")
        yield
        self._out("Q")

    @check_page
    @contextmanager
    def round_clip(self, x, y, r):
        """
        Context manager that defines a circular crop zone,
        useful to render only part of an image.

        Args:
            x (float): abscissa of the clipping region top left corner
            y (float): ordinate of the clipping region top left corner
            r (float): radius of the clipping region
        """
        with self.elliptic_clip(x, y, r, r):
            yield

    @contextmanager
    def _trace_size(self, label):
        prev_size = len(self.buffer)
        yield
        LOGGER.debug("- %s.size: %s", label, _sizeof_fmt(len(self.buffer) - prev_size))

    @contextmanager
    def unbreakable(self):
        """
        Ensures that all rendering performed in this context appear on a single page
        by performing page break beforehand if need be.

        Notes
        -----

        Using this method means to duplicate the FPDF `bytearray` buffer:
        when generating large PDFs, doubling memory usage may be troublesome.
        """
        prev_page, prev_y = self.page, self.y
        recorder = FPDFRecorder(self, accept_page_break=False)
        recorder.page_break_triggered = False
        LOGGER.debug("Starting unbreakable block")
        yield recorder
        y_scroll = recorder.y - prev_y + (recorder.page - prev_page) * self.eph
        if prev_y + y_scroll > self.page_break_trigger or recorder.page > prev_page:
            LOGGER.debug("Performing page jump due to unbreakable height")
            recorder.rewind()
            # pylint: disable=protected-access
            # Performing this call through .pdf so that it does not get recorded & replayed:
            recorder.pdf._perform_page_break()
            recorder.replay()
            recorder.page_break_triggered = True
        LOGGER.debug("Ending unbreakable block")

    @contextmanager
    def offset_rendering(self):
        """
        All rendering performed in this context is made on a dummy FPDF object.
        This allows to test the results of some operations on the global layout
        before performing them "for real".
        """
        prev_page, prev_y = self.page, self.y
        recorder = FPDFRecorder(self, accept_page_break=False)
        recorder.page_break_triggered = False
        yield recorder
        y_scroll = recorder.y - prev_y + (recorder.page - prev_page) * self.eph
        if prev_y + y_scroll > self.page_break_trigger or recorder.page > prev_page:
            recorder.page_break_triggered = True
        recorder.rewind()

    @check_page
    def insert_toc_placeholder(self, render_toc_function, pages=1):
        """
        Configure Table Of Contents rendering at the end of the document generation,
        and reserve some vertical space right now in order to insert it.

        Args:
            render_toc_function (function): a function that will be invoked to render the ToC.
                This function will receive 2 parameters: `pdf`, an instance of FPDF, and `outline`,
                a list of `OutlineSection`.
            pages (int): the number of pages that the Table of Contents will span,
                including the current one that will. As many page breaks as the value of this argument
                will occur immediately after calling this method.
        """
        if not callable(render_toc_function):
            raise TypeError(
                f"The first argument must be a callable, got: {type(render_toc_function)}"
            )
        if self._toc_placeholder:
            raise FPDFException(
                "A placeholder for the table of contents has already been defined"
                f" on page {self._toc_placeholder.start_page}"
            )
        self._toc_placeholder = ToCPlaceholder(
            render_toc_function, self.page, self.y, pages
        )
        for _ in range(pages):
            self.add_page()

    def set_section_title_styles(
        self,
        level0,
        level1=None,
        level2=None,
        level3=None,
        level4=None,
        level5=None,
        level6=None,
    ):
        """
        Defines a style for section titles.
        After calling this method, calls to `FPDF.start_section` will render section names visually.

        Args:
            level0 (TitleStyle): style for the top level section titles
            level1 (TitleStyle): optional style for the level 1 section titles
            level2 (TitleStyle): optional style for the level 2 section titles
            level3 (TitleStyle): optional style for the level 3 section titles
            level4 (TitleStyle): optional style for the level 4 section titles
            level5 (TitleStyle): optional style for the level 5 section titles
            level6 (TitleStyle): optional style for the level 6 section titles
        """
        for level in (level0, level1, level2, level3, level4, level5, level6):
            if level and not isinstance(level, TitleStyle):
                raise TypeError(
                    f"Arguments must all be TitleStyle instances, got: {type(level)}"
                )
        self.section_title_styles = {
            0: level0,
            1: level1,
            2: level2,
            3: level3,
            4: level4,
            5: level5,
            6: level6,
        }

    @check_page
    def start_section(self, name, level=0):
        """
        Start a section in the document outline.
        If section_title_styles have been configured,
        render the section name visually as a title.

        Args:
            name (str): section name
            level (int): section level in the document outline. 0 means top-level.
        """
        if level < 0:
            raise ValueError('"level" mut be equal or greater than zero')
        if self._outline and level > self._outline[-1].level + 1:
            raise ValueError(
                f"Incoherent hierarchy: cannot start a level {level} section after a level {self._outline[-1].level} one"
            )
        dest = DestinationXYZ(self.page, y=self.y)
        struct_elem = None
        if self.section_title_styles:
            # We first check if adding this multi-cell will trigger a page break:
            with self.offset_rendering() as pdf:
                # pylint: disable=protected-access
                with pdf._apply_style(pdf.section_title_styles[level]):
                    pdf.multi_cell(
                        w=pdf.epw,
                        h=pdf.font_size,
                        txt=name,
                        new_x=XPos.LMARGIN,
                        new_y=YPos.NEXT,
                    )
            if pdf.page_break_triggered:
                # If so, we trigger a page break manually beforehand:
                self.add_page()
            with self._marked_sequence(title=name) as marked_content:
                struct_elem = self.struct_builder.struct_elem_per_mc[marked_content]
                with self._apply_style(self.section_title_styles[level]):
                    self.multi_cell(
                        w=self.epw,
                        h=self.font_size,
                        txt=name,
                        new_x=XPos.LMARGIN,
                        new_y=YPos.NEXT,
                    )
        self._outline.append(OutlineSection(name, level, self.page, dest, struct_elem))

    @contextmanager
    def _apply_style(self, title_style):
        prev_font = (self.font_family, self.font_style, self.font_size_pt)
        self.set_font(
            title_style.font_family, title_style.font_style, title_style.font_size_pt
        )
        prev_text_color = self.text_color
        if title_style.color is not None:
            if isinstance(title_style.color, Sequence):
                self.set_text_color(*title_style.color)
            else:
                self.set_text_color(title_style.color)
        prev_underline = self.underline
        self.underline = title_style.underline
        if title_style.t_margin:
            self.ln(title_style.t_margin)
        if title_style.l_margin:
            self.set_x(title_style.l_margin)
        yield
        if title_style.b_margin:
            self.ln(title_style.b_margin)
        self.set_font(*prev_font)
        self.text_color = prev_text_color
        self.underline = prev_underline


def _char_width(font, char):
    cw = font["cw"]
    try:
        width = cw[char]
    except (IndexError, KeyError):
        width = font.get("desc", {}).get("MissingWidth") or 500
    if width == 65535:
        width = 0
    return width


def _sizeof_fmt(num, suffix="B"):
    # Recipe from: https://stackoverflow.com/a/1094933/636849
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024
    return f"{num:.1f}Yi{suffix}"


def _is_svg(bytes):
    return bytes.startswith(b"<?xml ") or bytes.startswith(b"<svg ")


sys.modules[__name__].__class__ = WarnOnDeprecatedModuleAttributes


__pdoc__ = {"FPDF.add_highlight": False}  # Replaced by FPDF.highlight

__all__ = [
    "FPDF",
    "XPos",
    "YPos",
    "get_page_format",
    "TextMode",
    "TitleStyle",
    "PAGE_FORMATS",
]
