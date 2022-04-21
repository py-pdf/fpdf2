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
import pickle
import re
import sys
import warnings
import zlib
from collections import defaultdict, OrderedDict
from collections.abc import Sequence
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Callable, NamedTuple, Optional, Union, List

from PIL import Image

from . import drawing
from .actions import Action
from .deprecation import WarnOnDeprecatedModuleAttributes
from .enums import DocumentState, PathPaintRule, TextMode, XPos, YPos
from .errors import FPDFException, FPDFPageFormatException
from .fonts import fpdf_charwidths
from .graphics_state import GraphicsStateMixin
from .image_parsing import get_img_info, load_image, SUPPORTED_IMAGE_FILTERS
from .line_break import Fragment, TextLine, MultiLineBreak
from .outline import serialize_outline, OutlineSection
from .recorder import FPDFRecorder
from .structure_tree import MarkedContent, StructureTreeBuilder
from .svg import Percent, SVGObject
from .syntax import (
    create_dictionary_string as pdf_d,
    create_list_string as pdf_l,
    create_stream as pdf_stream,
    iobj_ref as pdf_ref,
    DestinationXYZ,
)
from .ttfonts import TTFontFile
from .util import (
    enclose_in_parens,
    escape_parens,
    substr,
    get_scale_factor,
)


LOGGER = logging.getLogger(__name__)
HERE = Path(__file__).resolve().parent

# Global variables
FPDF_VERSION = "2.5.2"
FPDF_FONT_DIR = HERE / "font"

PAGE_FORMATS = {
    "a3": (841.89, 1190.55),
    "a4": (595.28, 841.89),
    "a5": (420.94, 595.28),
    "letter": (612, 792),
    "legal": (612, 1008),
}
LAYOUT_NAMES = {
    "single": "/SinglePage",
    "continuous": "/OneColumn",
    "two": "/TwoColumnLeft",
}
ZOOM_CONFIGS = {  # cf. section 8.2.1 "Destinations" of the 2006 PDF spec 1.7:
    "fullpage": ("/Fit",),
    "fullwidth": ("/FitH", "null"),
    "real": ("/XYZ", "null", "null", "1"),
}


class Annotation(NamedTuple):
    type: str
    x: int
    y: int
    width: int
    height: int
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

    def serialize(self, fpdf):
        "Convert this object dictionnary to a string"
        rect = (
            f"{self.x:.2f} {self.y:.2f} "
            f"{self.x + self.width:.2f} {self.y - self.height:.2f}"
        )

        out = (
            f"<</Type /Annot /Subtype /{self.type}"
            f" /Rect [{rect}] /Border [0 0 {self.border_width}]"
            # Flag "Print" (bit position 3) specifies to print
            # the annotation when the page is printed.
            # cf. https://docs.verapdf.org/validation/pdfa-part1/#rule-653-2
            f" /F 4"
        )

        if self.contents:
            out += f" /Contents {enclose_in_parens(self.contents)}"

        if self.action:
            out += f" /A <<{self.action.dict_as_string()}>>"

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
            out += f" /M (D:{self.modification_time:%Y%m%d%H%M%S})"

        if self.quad_points:
            # pylint: disable=not-an-iterable
            quad_points = " ".join(
                f"{quad_point:.2f}" for quad_point in self.quad_points
            )
            out += f" /QuadPoints [{quad_points}]"

        if self.page:
            # Same logic as FPDF._current_page_object_id:
            out += f" /P {pdf_ref(2 * self.page + 1)}"

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
    added by adding fields to the `fpdf.fpdf.PAGE_FORMATS` dictionary with a
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
            font_cache_dir (Path or str): [**DEPRECATED**] unused
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
        self.annots = defaultdict(list)  # map page numbers to arrays of Annotations
        self.links = {}  # array of Destination
        self.in_footer = 0  # flag set when processing footer
        self.lasth = 0  # height of last cell printed
        self.current_font = {}  # current font
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
        self.font_size_pt = 12  # current font size in points
        self.font_size = self.font_size_pt / self.k
        self.font_stretching = 100  # current font stretching
        self.underline = 0  # underlining flag
        self.draw_color = self.DEFAULT_DRAW_COLOR
        self.fill_color = self.DEFAULT_FILL_COLOR
        self.text_color = self.DEFAULT_TEXT_COLOR
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
        self.compress = True  # Enable compression by default
        self.pdf_version = "1.3"  # Set default PDF version No.
        self._current_draw_context = None

        self._drawing_graphics_state_registry = drawing.GraphicsStateDictRegistry()
        self._graphics_state_obj_refs = OrderedDict()

        self.record_text_quad_points = False
        self.text_quad_points = defaultdict(
            list
        )  # page number -> array of 8 × n numbers

    def _set_min_pdf_version(self, version):
        self.pdf_version = max(self.pdf_version, version)

    @property
    def unifontsubset(self):
        return self.current_font.get("type") == "TTF"

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

        It allows to set tje zoom level: pages can be displayed entirely on screen,
        occupy the full width of the window, use the real size,
        be scaled by a specific zooming factor or use the viewer default (configured in its Preferences menu).

        The page layout can also be specified: single page at a time, continuous display, two columns or viewer default.

        Args:
            zoom: either "fullpage", "fullwidth", "real", "default",
                or a number indicating the zooming factor to use, interpreted as a percentage.
                The zoom level set by default is "default".
            layout (str): either "single", "continuous", "two" or "default",
                meaning to use the viewer default mode.
                The layout set by default is "default",
                and this method default value is "continuous".
        """
        if zoom in ZOOM_CONFIGS or not isinstance(zoom, str):
            self.zoom_mode = zoom
        elif zoom != "default":
            raise FPDFException(f"Incorrect zoom display mode: {zoom}")

        if layout in LAYOUT_NAMES:
            self.layout_mode = layout
        elif layout != "default":
            raise FPDFException(f"Incorrect layout display mode: {layout}")

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
        self.creation_date = datetime.now() if date is None else date

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
            Simply set the `core_fonts_encoding` property as a replacement.
        """
        warnings.warn(
            "set_doc_option() is deprecated. "
            "Simply set the `core_fonts_encoding` property as a replacement.",
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

        This substitution can be disabled for performances reasons, by caling `alias_nb_pages(None)`.

        Args:
            alias (str): the alias. Defaults to "{nb}".

        Notes
        -----

        When using this feature with the `cell` / `multicell` methods,
        or the `underline` attribute of `FPDF` class,
        the width of the text rendered will take into account the alias length,
        not the length of the "actual number of pages" string,
        which can causes slight positioning differences.
        """
        self.str_alias_nb_pages = alias

    def open(self):
        """
        Starts the generation of the PDF document.
        It is not necessary to call it explicitly because `add_page()` does it automatically.

        Notes
        -----

        This method does not add any page.
        """
        self.state = DocumentState.READY

    def close(self):
        """
        Terminates the PDF document.

        It is not necessary to call this method explicitly because `output()` does it automatically.
        If the document contains no page, `add_page()` is called to prevent from generating an invalid document.
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
        If a page is already present, the `footer()` method is called first.
        Then the page  is added, the current position is set to the top-left corner,
        with respect to the left and top margins, and the `header()` method is called.

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
                Can be configured globally through the `page_duration` FPDF property.
                As of june 2021, onored by Adobe Acrobat reader, but ignored by Sumatra PDF reader.
            transition (Transition child class): optional visual transition to use when moving
                from another page to the given page during a presentation.
                Can be configured globally through the `page_transition` FPDF property.
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

        This is automatically called by `add_page()`
        and should not be called directly by the user application.
        The default implementation performs nothing: you have to override this method
        in a subclass to implement your own rendering logic.
        """

    def footer(self):
        """
        Footer to be implemented in your own inherited class.

        This is automatically called by `add_page()` and `close()`
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
    def polyline(self, point_list, fill=False, polygon=False):
        """
        Draws lines between two or more points.

        Args:
            point_list (list of tuples): List of Abscissa and Ordinate of
                                        segments that should be drawn
            fill (bool): If true then polyline should be filled
            polygon (bool): If true, close path before stroking
        """
        operator = "m"
        for point in point_list:
            self._out(
                f"{point[0] * self.k:.2f} {(self.h - point[1]) * self.k:.2f} {operator}"
            )
            operator = "l"
        if polygon:
            self._out(" h ")
        if fill:
            self._out(" B ")
        else:
            self._out(" S ")

    @check_page
    def polygon(self, point_list, fill=False):
        """
        Outputs a polygon defined by three or more points.

        Args:
            point_list (list of tuples): List of Abscissa and Ordinate of
                                        polygon that should be drawn
            fill (bool): If true polygon will be filled
        """
        self.polyline(point_list, fill=fill, polygon=True)

    @check_page
    def dashed_line(self, x1, y1, x2, y2, dash_length=1, space_length=1):
        """
        Draw a dashed line between two points.
        **DEPRECATED** 2.4.6
        - use set_dash_pattern() and the normal drawing operations instead

        Args:
            x1 (float): Abscissa of first point
            y1 (float): Ordinate of first point
            x2 (float): Abscissa of second point
            y2 (float): Ordinate of second point
            dash_length (float): Length of the dash
            space_length (float): Length of the space between 2 dashes
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
    def rect(self, x, y, w, h, style=None):
        """
        Outputs a rectangle.
        It can be drawn (border only), filled (with no border) or both.

        Args:
            x (float): Abscissa of upper-left bounging box.
            y (float): Ordinate of upper-left bounging box.
            w (float): Width.
            h (float): Height.
            style (str): Style of rendering. Possible values are:
                * `D` or empty string: draw border. This is the default value.
                * `F`: fill
                * `DF` or `FD`: draw and fill
        """
        op = _style_to_operator(style)
        self._out(
            f"{x * self.k:.2f} {(self.h - y) * self.k:.2f} {w * self.k:.2f} "
            f"{-h * self.k:.2f} re {op}"
        )

    @check_page
    def ellipse(self, x, y, w, h, style=None):
        """
        Outputs an ellipse.
        It can be drawn (border only), filled (with no border) or both.

        Args:
            x (float): Abscissa of upper-left bounging box.
            y (float): Ordinate of upper-left bounging box.
            w (float): Width.
            h (float): Height.
            style (str): Style of rendering. Possible values are:
                * `D` or empty string: draw border. This is the default value.
                * `F`: fill
                * `DF` or `FD`: draw and fill
        """
        op = _style_to_operator(style)

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
                f"{(cx + rx) * self.k:.2f} {(self.h - cy) * self.k:.2f} c {op}"
            )
        )

    @check_page
    def circle(self, x, y, r, style=None):
        """
        Outputs a circle.
        It can be drawn (border only), filled (with no border) or both.

        Args:
            x (float): Abscissa of upper-left bounging box.
            y (float): Ordinate of upper-left bounging box.
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
            polyWidth (float): width of the polygon.
            rotateDegrees (float): degree amount to rotate polygon. (can be left blank)
            style (str): Style of rendering. Possible values are: (can be left blank)
                * `D` or None: draw border. This is the default value.
                * `F`: fill
                * `DF` or `FD`: draw and fill

        """
        radius = polyWidth / 2
        centerX = x + radius
        centerY = y - radius
        # center point is (centerX, centerY)
        points = []
        i = 1
        for i in range(1, numSides + 1):
            point = centerX + radius * math.cos(
                math.radians((360 / numSides) * i) + math.radians(rotateDegrees)
            ), centerY + radius * math.sin(
                math.radians((360 / numSides) * i) + math.radians(rotateDegrees)
            )
            points.append(point)
            i += 1
        # creates list of touples containing cordinate points of vertices

        self.polygon(points, style)
        # passes points through polygon function

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
            a (float): Semi-major axis diameter.
            b (float): Semi-minor axis diameter, if None, equals to a (default: None).
            start_angle (float): Start angle of the arc (in degrees).
            end_angle (float): End angle of the arc (in degrees).
            inclination (float): Inclination of the arc in respect of the x-axis (default: 0).
            clockwise (bool): Way of drawing the arc (True: clockwise, False: counterclockwise) (default: False).
            start_from_center (bool): Start drawing from the center of the circle (default: False).
            end_at_center (bool): End drawing at the center of the circle (default: False).
            style (str): Style of rendering. Possible values are:
                * `D` or None: draw border. This is the default value.
                * `F`: fill
                * `DF` or `FD`: draw and fill
        """
        op = _style_to_operator(style)

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
                end = f" {op}"

            self._out(
                (
                    f"{control_point_1[0] * self.k:.2f} {(self.h - control_point_1[1]) * self.k:.2f} "
                    f"{control_point_2[0] * self.k:.2f} {(self.h - control_point_2[1]) * self.k:.2f} "
                    f"{p2[0] * self.k:.2f} {(self.h - p2[1]) * self.k:.2f} c" + end
                )
            )

        if end_at_center:
            self._out(f"{cx * self.k:.2f} {(self.h - cy) * self.k:.2f} l {op}")

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
            x (float): Abscissa of upper-left bounging box.
            y (float): Ordinate of upper-left bounging box.
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
        for later calls to the `set_font()` method.

        **Warning:** there is partial support for Type1 and legacy fonts in .pkl font definition files,
        generated by the `MakeFont` utility, but this feature is getting deprecated in favour of TrueType Unicode font support
        (whose fonts are automatically processed with the included `ttfonts.py` module).

        You will find more information on the "Unicode" documentation page.

        Args:
            family (str): font family. Used as a reference for `set_font()`
            style (str): font style. "B" for bold, "I" for italic.
            fname (str): font file name. You can specify a relative or full path.
                If the file is not found, it will be searched in `FPDF_FONT_DIR`.
            uni (bool): [**DEPRECATED**] unused
        """
        if uni != "DEPRECATED":
            warnings.warn(
                '"uni" parameter is deprecated, unused and will soon be removed',
                DeprecationWarning,
                stacklevel=2,
            )
        else:
            uni = str(fname).endswith(".ttf")
        if not fname:
            raise ValueError('"fname" parameter is required')
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
        if uni:
            for parent in (".", FPDF_FONT_DIR):
                if not parent:
                    continue
                if (Path(parent) / fname).exists():
                    ttffilename = Path(parent) / fname
                    break
            else:
                raise FileNotFoundError(f"TTF Font file not found: {fname}")

            # include numbers in the subset! (if alias present)
            # ensure that alias is mapped 1-by-1 additionally (must be replaceable)
            sbarr = "\x00 "
            if self.str_alias_nb_pages:
                sbarr += "0123456789"
                sbarr += self.str_alias_nb_pages

            ttf = TTFontFile()
            ttf.getMetrics(ttffilename)
            desc = {
                "Ascent": round(ttf.ascent),
                "Descent": round(ttf.descent),
                "CapHeight": round(ttf.capHeight),
                "Flags": ttf.flags,
                "FontBBox": (
                    f"[{ttf.bbox[0]:.0f} {ttf.bbox[1]:.0f}"
                    f" {ttf.bbox[2]:.0f} {ttf.bbox[3]:.0f}]"
                ),
                "ItalicAngle": int(ttf.italicAngle),
                "StemV": round(ttf.stemV),
                "MissingWidth": round(ttf.defaultWidth),
            }

            # Generate metrics .pkl file
            font_dict = {
                "type": "TTF",
                "name": re.sub("[ ()]", "", ttf.fullName),
                "desc": desc,
                "up": round(ttf.underlinePosition),
                "ut": round(ttf.underlineThickness),
                "ttffile": ttffilename,
                "fontkey": fontkey,
                "originalsize": os.stat(ttffilename).st_size,
                "cw": ttf.charWidths,
            }

            self.fonts[fontkey] = {
                "i": len(self.fonts) + 1,
                "type": font_dict["type"],
                "name": font_dict["name"],
                "desc": font_dict["desc"],
                "up": font_dict["up"],
                "ut": font_dict["ut"],
                "cw": font_dict["cw"],
                "ttffile": font_dict["ttffile"],
                "fontkey": fontkey,
                "subset": SubsetMap(map(ord, sbarr)),
            }
            self.font_files[fontkey] = {
                "length1": font_dict["originalsize"],
                "type": "TTF",
                "ttffile": ttffilename,
            }
        else:
            warnings.warn(
                "Support for .pkl font files definition is deprecated, and will be removed from fpdf2 soon."
                " If you require this feature, please report your need on fpdf2 GitHub project.",
                DeprecationWarning,
                stacklevel=2,
            )
            font_dict = pickle.loads(Path(fname).read_bytes())
            font_dict["i"] = len(self.fonts) + 1
            self.fonts[fontkey] = font_dict
            diff = font_dict.get("diff")
            if diff:
                # Search existing encodings
                nb = len(self.diffs)
                for i in range(1, nb + 1):
                    if self.diffs[i] == diff:
                        d = i
                        break
                else:
                    d = nb + 1
                    self.diffs[d] = diff
                self.fonts[fontkey]["diff"] = d
            filename = font_dict.get("filename")
            if filename:
                if font_dict["type"] == "TrueType":
                    originalsize = font_dict["originalsize"]
                    self.font_files[filename] = {"length1": originalsize}
                else:
                    self.font_files[filename] = {
                        "length1": font_dict["size1"],
                        "length2": font_dict["size2"],
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
            and self.font_size_pt == size
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
        self.font_size = size / self.k
        self.current_font = self.fonts[fontkey]
        if self.page > 0:
            self._out(f"BT /F{self.current_font['i']} {self.font_size_pt:.2f} Tf ET")

    def set_font_size(self, size):
        """
        Configure the font size in points

        Args:
            size (float): font size in points
        """
        if self.font_size_pt == size:
            return
        self.font_size_pt = size
        self.font_size = size / self.k
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

        The identifier can then be passed to the `cell()`, `write()`, `image()` or `link()` methods.
        The destination must be defined using `set_link()`.
        """
        n = len(self.links) + 1
        self.links[n] = DestinationXYZ(page=1)
        return n

    def set_link(self, link, y=0, x=0, page=-1, zoom="null"):
        """
        Defines the page and position a link points to.

        Args:
            link (int): a link identifier returned by `add_link`.
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
        Text or image links are generally put via [cell](#fpdf.FPDF.cell),
        [write](#fpdf.FPDF.write) or [image](#fpdf.FPDF.image),
        but this method can be useful for instance to define a clickable area inside an image.

        Args:
            x (float): horizontal position (from the left) to the left side of the link rectangle
            y (float): vertical position (from the top) to the bottom side of the link rectangle
            w (float): width of the link rectangle
            h (float): width of the link rectangle
            link: either an URL or a integer returned by `add_link`, defining an internal link to a page
            alt_text (str): optional textual description of the link, for accessibility purposes
            border_width (int): thickness of an optional black border surrounding the link.
                Not all PDF readers honor this: Acrobat renders it but not Sumatra.
        """
        self.annots[self.page].append(
            Annotation(
                "Link",
                x=x * self.k,
                y=self.h_pt - y * self.k,
                width=w * self.k,
                height=h * self.k,
                link=link,
                alt_text=alt_text,
                border_width=border_width,
            )
        )

    @check_page
    def text_annotation(self, x, y, text, w=1, h=1):
        """
        Puts a text annotation on a rectangular area of the page.

        Args:
            x (float): horizontal position (from the left) to the left side of the link rectangle
            y (float): vertical position (from the top) to the bottom side of the link rectangle
            w (float): width of the link rectangle
            h (float): width of the link rectangle
            text (str): text to display
        """
        self.annots[self.page].append(
            Annotation(
                "Text",
                x * self.k,
                self.h_pt - y * self.k,
                w * self.k,
                h * self.k,
                contents=text,
            )
        )

    @check_page
    def add_action(self, action, x, y, w, h):
        """
        Puts an Action annotation on a rectangular area of the page.

        Args:
            action (fpdf.actions.Action): the action to add
            x (float): horizontal position (from the left) to the left side of the link rectangle
            y (float): vertical position (from the top) to the bottom side of the link rectangle
            w (float): width of the link rectangle
            h (float): width of the link rectangle
        """
        self.annots[self.page].append(
            Annotation(
                "Action",
                x * self.k,
                self.h_pt - y * self.k,
                w * self.k,
                h * self.k,
                action=action,
            )
        )

    @contextmanager
    def add_highlight(self, text, title="", color=(1, 1, 0), modification_time=None):
        """
        Context manager that adds a single highlight annotation based on the text lines inserted
        inside its indented block.

        Args:
            text (str): text of the annotation
            title (str): the text label that shall be displayed in the title bar of the annotation’s
                pop-up window when open and active. This entry shall identify the user who added the annotation.
            color (tuple): a tuple of numbers in the range 0.0 to 1.0, representing a colour used for
                the title bar of the annotation’s pop-up window
            modification_time (datetime): date and time when the annotation was most recently modified
        """
        if self.record_text_quad_points:
            raise FPDFException("add_highlight() cannot be nested")
        self.record_text_quad_points = True
        yield
        for page, quad_points in self.text_quad_points.items():
            self.add_text_markup_annotation(
                "Highlight",
                text,
                quad_points=quad_points,
                title=title,
                color=color,
                modification_time=modification_time,
                page=page,
            )
            self.text_quad_points = defaultdict(list)
        self.record_text_quad_points = False

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
            type (str): "Highlight", "Underline", "Squiggly" or "StrikeOut"
            text (str): text of the annotation
            quad_points (tuple): array of 8 × n numbers specifying the coordinates of n quadrilaterals
                in default user space that comprise the region in which the link should be activated.
                The coordinates for each quadrilateral are given in the order: x1 y1 x2 y2 x3 y3 x4 y4
                specifying the four vertices of the quadrilateral in counterclockwise order
            title (str): the text label that shall be displayed in the title bar of the annotation’s
                pop-up window when open and active. This entry shall identify the user who added the annotation.
            color (tuple): a tuple of numbers in the range 0.0 to 1.0, representing a colour used for
                the title bar of the annotation’s pop-up window
            modification_time (datetime): date and time when the annotation was most recently modified
            page (int): index of the page where this annotation is added
        """
        if type not in ("Highlight", "Underline", "Squiggly", "StrikeOut"):
            raise ValueError(f"Invalid text markup annotation subtype: {type}")
        if modification_time is None:
            modification_time = datetime.now()
        if page is None:
            page = self.page
        x_min = min(quad_points[0::2])
        y_min = min(quad_points[1::2])
        x_max = max(quad_points[0::2])
        y_max = max(quad_points[1::2])
        self.annots[page].append(
            Annotation(
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
        )

    @check_page
    def text(self, x, y, txt=""):
        """
        Prints a character string. The origin is on the left of the first character,
        on the baseline. This method allows placing a string precisely on the page,
        but it is usually easier to use the `cell()`, `multi_cell() or `write()` methods.

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
            unscaled_width = self.get_normalized_string_width_with_style(
                txt, self.font_style
            )
            if self.font_stretching != 100:
                unscaled_width *= self.font_stretching / 100
            w = unscaled_width * self.font_size / 1000
            h = self.font_size
            self.text_quad_points[self.page].extend(
                [
                    x * self.k,
                    (self.h - y) * self.k,
                    (x + w) * self.k,
                    (self.h - y) * self.k,
                    x * self.k,
                    (self.h - y + h) * self.k,
                    (x + w) * self.k,
                    (self.h - y + h) * self.k,
                ]
            )

    @check_page
    def rotate(self, angle, x=None, y=None):
        """
        .. deprecated:: 2.1.0
          Use `rotation` instead.
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

        Only the rendering is altered. The `get_x()` and `get_y()` methods are
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
        # All the folling calls to .set*() methods invoke .out() and write to the stream buffer:
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

        The default implementation returns a value according to the mode selected by `set_auto_page_break()`.
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
        new_x=XPos.RIGHT,
        new_y=YPos.TOP,
        ln="DEPRECATED",
        align="",
        fill=False,
        link="",
        center="DEPRECATED",
        markdown=False,
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
            new_x (Enum XPos): New current position in x after the call. Default: RIGHT
            new_y (Enum YPos): New current position in y after the call. Default: TOP
            ln (int): **DEPRECATED** 2.5.1: Use new_x and new_y instead.
            align (str): Allows to center or align the text inside the cell.
                Possible values are: `L` or empty string: left align (default value) ;
                `C`: center ; `R`: right align
            fill (bool): Indicates if the cell background must be painted (`True`)
                or transparent (`False`). Default value: False.
            link (str): optional link to add on the cell, internal
                (identifier returned by `add_link`) or external URL.
            center (bool): **DEPRECATED** 2.5.1: Use align="C" instead.
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
        if not isinstance(new_x, XPos):
            raise ValueError(
                f'Invalid value for parameter "new_x" ({new_x}),'
                "must be instance of Enum XPos"
            )
        if not isinstance(new_y, YPos):
            raise ValueError(
                f'Invalid value for parameter "new_y" ({new_y}),'
                "must be instance of Enum YPos"
            )
        if center == "DEPRECATED":
            center = False
        else:
            warnings.warn(
                ('The parameter "center" is deprecated.' ' Use align="C" instead.'),
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
        # Font styles preloading must be performed before any call to FPDF.get_string_width:
        txt = self.normalize_text(txt)
        styled_txt_frags = self._preload_font_styles(txt, markdown)
        return self._render_styled_text_line(
            TextLine(
                styled_txt_frags,
                text_width=0.0,
                number_of_spaces_between_words=0,
                justify=False,
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
        align: str = "",
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
            new_x (Enum XPos): New current position in x after the call.
            new_y (Enum YPos): New current position in y after the call.
            align (str): Allows to align the text inside the cell.
                Possible values are: `L` or empty string: left align (default value);
                `C`: center; `R`: right align; `J`: justify (if more than one word)
            fill (bool): Indicates if the cell background must be painted (`True`)
                or transparent (`False`). Default value: False.
            link (str): optional link to add on the cell, internal
                (identifier returned by `add_link`) or external URL.
            center (bool): **DEPRECATED** 2.5.1: Use align="C" instead.
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
            if align == "R":
                dx = w - self.c_margin - styled_txt_width
            elif align == "C":
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
        align="J",
        fill=False,
        split_only=False,
        link="",
        new_x=XPos.RIGHT,
        new_y=YPos.NEXT,
        ln="DEPRECATED",
        max_line_height=None,
        markdown=False,
        print_sh=False,
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
            align (str): Allows to center or align the text. Possible values are:
                `J`: justify (default value); `L` or empty string: left align ;
                `C`: center ; `R`: right align
            fill (bool): Indicates if the cell background must be painted (`True`)
                or transparent (`False`). Default value: False.
            split_only (bool): if `True`, does not output anything, only perform
                word-wrapping and return the resulting multi-lines array of strings.
            link (str): optional link to add on the cell, internal
                (identifier returned by `add_link`) or external URL.
            new_x (Enum XPos): New current position in x after the call. Default: RIGHT
            new_y (Enum YPos): New current position in y after the call. Default: NEXT
            ln (int): **DEPRECATED** 2.5.1: Use new_x and new_y instead.
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
        if not isinstance(new_x, XPos):
            raise ValueError(
                f'Invalid value for parameter "new_x" ({new_x}),'
                "must be instance of Enum XPos"
            )
        if not isinstance(new_y, YPos):
            raise ValueError(
                f'Invalid value for parameter "new_y" ({new_y}),'
                "must be instance of Enum YPos"
            )
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
            justify=(align == "J"),
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
                )
            ]
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
                # align="L" if (align == "J" and is_last_line) else align,
                align="L" if (align == "J" and is_last_line) else align,
                fill=fill,
                link=link,
            )
            if is_last_line and new_page and new_y == YPos.TOP:
                # When a page jump is performed and the requested y is TOP,
                # pretend we started at the top of the text block on the new page.
                # cf. test_multi_cell_table_with_automatic_page_break
                prev_y = self.y
            page_break_triggered = page_break_triggered or new_page

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
                (identifier returned by `add_link`) or external URL.
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
        text_line = multi_line_break.get_line_of_given_width(
            first_emwidth, wordsplit=False
        )
        # remaining lines fill between margins
        full_width = self.w - self.l_margin - self.r_margin
        full_emwidth = (full_width - 2 * self.c_margin) * 1000 / self.font_size
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
                align="L",
                fill=False,
                link=link,
            )
            page_break_triggered = page_break_triggered or new_page

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
            type (str): [**DEPRECATED**] unused, will be removed in a later version.
            link (str): optional link to add on the image, internal
                (identifier returned by `add_link`) or external URL.
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
        elif isinstance(name, Image.Image):
            bytes = name.tobytes()
            # disabling bandit rule as we just build a cache key, this is secure
            name, img = hashlib.md5(bytes).hexdigest(), name  # nosec B303 B324
        elif isinstance(name, io.BytesIO):
            if _is_xml(name):
                return self._vector_image(name, x, y, w, h, link, title, alt_text)
            bytes = name.getvalue()
            # disabling bandit rule as we just build a cache key, this is secure
            name, img = hashlib.md5(bytes).hexdigest(), name  # nosec B303 B324
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
        page_object_id = self._current_page_object_id()
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

    def _current_page_object_id(self):
        # Predictable given that _putpages is invoked first in _enddoc:
        return 2 * self.page + 1

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

        By default the bytearray buffer is returned.
        If a `name` is given, the PDF is written to a new file.

        Args:
            name (str): optional File object or file path where to save the PDF under
            dest (str): [**DEPRECATED**] unused, will be removed in a later version
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
            return txt.encode(self.core_fonts_encoding).decode("latin-1")
        return txt

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

            page_annots = self.annots[n]
            if page_annots:  # Annotations, e.g. links:
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
                self._out(f"/Annots [{annots}]")
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
        self._out("/Kids [" + " ".join(pdf_ref(3 + 2 * i) for i in range(nb)) + "]")
        self._out(f"/Count {nb}")
        self._out(f"/MediaBox [0 0 {dw_pt:.2f} {dh_pt:.2f}]")
        self._out(">>")
        self._out("endobj")

    def _substitute_page_number(self):
        nb = self.pages_count  # total number of pages
        substituted = False
        # Replace number of pages in fonts using subsets (unicode)
        alias = self.str_alias_nb_pages.encode("utf-16-be")
        encoded_nb = str(nb).encode("utf-16-be")
        for n in range(1, nb + 1):
            page = self.pages[n]
            new_content = page["content"].replace(alias, encoded_nb)
            substituted |= page["content"] != new_content
            page["content"] = new_content
        # Now repeat for no pages in non-subset fonts
        alias = self.str_alias_nb_pages.encode("latin-1")
        encoded_nb = str(nb).encode("latin-1")
        for n in range(1, nb + 1):
            page = self.pages[n]
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
                ttf = TTFontFile()
                fontname = f"MPDFAA+{font['name']}"
                subset = font["subset"].dict()
                del subset[0]
                ttfontstream = ttf.makeSubset(font["ttffile"], subset)
                ttfontsize = len(ttfontstream)
                fontstream = zlib.compress(ttfontstream)
                codeToGlyph = ttf.codeToGlyph
                # del codeToGlyph[0]

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
                self._putTTfontwidths(font, ttf.maxUni)
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
                cidtogidmap = ["\x00"] * 256 * 256 * 2
                for cc, glyph in codeToGlyph.items():
                    cidtogidmap[cc * 2] = chr(glyph >> 8)
                    cidtogidmap[cc * 2 + 1] = chr(glyph & 0xFF)
                cidtogidmap = "".join(cidtogidmap)
                # manage binary data as latin1 until PEP461-like function is implemented
                cidtogidmap = zlib.compress(cidtogidmap.encode("latin1"))
                self._newobj()
                self._out(f"<</Length {len(cidtogidmap)}")
                self._out("/Filter /FlateDecode")
                self._out(">>")
                self._out(pdf_stream(cidtogidmap))
                self._out("endobj")

                # Font file
                self._newobj()
                self._out(f"<</Length {len(fontstream)}")
                self._out("/Filter /FlateDecode")
                self._out(f"/Length1 {ttfontsize}")
                self._out(">>")
                self._out(pdf_stream(fontstream))
                self._out("endobj")
                del ttf
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
            if img_info["usages"] == 0:
                continue
            self._putimage(img_info)
            del img_info["data"]
            if "smask" in img_info:
                del img_info["smask"]

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
            self._out(
                f"/ColorSpace [/Indexed /DeviceRGB "
                f"{len(info['pal']) // 3 - 1} {pdf_ref(self.n + 1)}]"
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
            filter, pal = (
                ("/Filter /FlateDecode ", zlib.compress(info["pal"]))
                if self.compress
                else ("", info["pal"])
            )
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

        if hasattr(self, "creation_date"):
            try:
                creation_date = self.creation_date
                date_string = f"{creation_date:%Y%m%d%H%M%S}"
            except Exception as error:
                raise FPDFException(
                    f"Could not format date: {creation_date}"
                ) from error
        else:
            date_string = f"{datetime.now():%Y%m%d%H%M%S}"
        info_d["/CreationDate"] = enclose_in_parens(f"D:{date_string}")

        self._out(pdf_d(info_d, open_dict="", close_dict="", has_empty_fields=True))

    def _putcatalog(self):
        catalog_d = {
            "/Type": "/Catalog",
            # Pages is always the 1st object of the document, cf. the end of _putpages:
            "/Pages": pdf_ref(1),
        }
        lang = enclose_in_parens(getattr(self, "lang", None))
        if lang:
            catalog_d["/Lang"] = lang

        if self.zoom_mode in ZOOM_CONFIGS:
            zoom_config = [
                pdf_ref(3),  # reference to object ID of the 1st page
                *ZOOM_CONFIGS[self.zoom_mode],
            ]
        else:  # zoom_mode is a number, not one of the allowed strings:
            zoom_config = ["/XYZ", "null", "null", str(self.zoom_mode / 100)]
        catalog_d["/OpenAction"] = pdf_l(zoom_config)

        if self.layout_mode in LAYOUT_NAMES:
            catalog_d["/PageLayout"] = LAYOUT_NAMES[self.layout_mode]
        if self._xmp_metadata_obj_id:
            catalog_d["/Metadata"] = pdf_ref(self._xmp_metadata_obj_id)
        if self._struct_tree_root_obj_id:
            catalog_d["/MarkInfo"] = pdf_d({"/Marked": "true"})
            catalog_d["/StructTreeRoot"] = pdf_ref(self._struct_tree_root_obj_id)
        if self._outlines_obj_id:
            catalog_d["/Outlines"] = pdf_ref(self._outlines_obj_id)

        self._out(pdf_d(catalog_d, open_dict="", close_dict=""))

    def _putheader(self):
        self._out(f"%PDF-{self.pdf_version}")

    def _puttrailer(self):
        self._out(f"/Size {self.n + 1}")
        self._out(f"/Root {pdf_ref(self.n)}")  # Catalog object index
        self._out(f"/Info {pdf_ref(self.n - 1)}")  # Info object index

    def _enddoc(self):
        LOGGER.debug("Final doc sections size summary:")
        with self._trace_size("header"):
            self._putheader()
        with self._trace_size("pages"):
            self._putpages()
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
            self._putcatalog()
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
        up = self.current_font["up"]
        ut = self.current_font["ut"]
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
        self._out(
            (
                f"q {x * self.k:.2f} {(self.h - y - h) * self.k:.2f} {w * self.k:.2f} "
                f"{h * self.k:.2f} re W n"
            )
        )
        yield
        self._out("Q")

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
        After calling this method, calls to `start_section` will render section names visually.

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


def _style_to_operator(style):
    style_to_operators = {"F": "f", "FD": "B", "DF": "B", "D": "S"}
    if not style:
        style = "D"
    if style not in style_to_operators:
        raise ValueError(
            f"Invalid value for style: '{style}'. Allowed values: {'/'.join(style_to_operators.keys())}"
        )
    return style_to_operators[style]


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


def _is_xml(img: io.BytesIO):
    bytes = img.getvalue()
    return bytes.startswith(b"<?xml ") or bytes.startswith(b"<svg ")


sys.modules[__name__].__class__ = WarnOnDeprecatedModuleAttributes


__all__ = [
    "FPDF",
    "XPos",
    "YPos",
    "get_page_format",
    "TextMode",
    "TitleStyle",
    "PAGE_FORMATS",
]
