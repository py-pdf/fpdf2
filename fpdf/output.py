"""
This module contains the serialization logic that produces a PDF document from a FPDF instance.
Most of the code in this module is used when FPDF.output() is called.

The contents of this module are internal to fpdf2, and not part of the public API.
They may change at any time without prior warning or any deprecation period,
in non-backward-compatible ways.
"""

# pylint: disable=protected-access
import logging
import re
from collections import OrderedDict, defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from html import escape as _html_escape
from io import BytesIO

from fontTools import subset as ftsubset

from .annotations import PDFAnnotation
from .drawing import PaintSoftMask, Transform
from .enums import OutputIntentSubType, PageLabelStyle, PDFResourceType, SignatureFlag
from .errors import FPDFException
from .fonts import CORE_FONTS, CoreFont, TTFFont
from .font_type_3 import Type3Font
from .image_datastructures import RasterImageInfo
from .line_break import TotalPagesSubstitutionFragment
from .outline import build_outline_objs
from .sign import Signature, sign_content
from .syntax import (
    Name,
    PDFArray,
    PDFContentStream,
    PDFDate,
    PDFObject,
    PDFString,
    build_obj_dict,
)
from .syntax import create_dictionary_string as pdf_dict
from .syntax import create_list_string as pdf_list
from .syntax import iobj_ref as pdf_ref
from .util import int2roman, int_to_letters

try:
    from endesive import signer
except ImportError:
    signer = None

from typing import TYPE_CHECKING, Dict, Optional, Union

if TYPE_CHECKING:
    from .fpdf import FPDF

LOGGER = logging.getLogger(__name__)

ZOOM_CONFIGS = {  # cf. section 8.2.1 "Destinations" of the 2006 PDF spec 1.7:
    "fullpage": ("/Fit",),
    "fullwidth": ("/FitH", "null"),
    "real": ("/XYZ", "null", "null", "1"),
}


class ContentWithoutID:
    def serialize(self, _security_handler=None):
        pass


class PDFHeader(ContentWithoutID):
    """
    Emit the PDF file header as required by ISO 32000-1, §7.5.2 “File header”.

    The header consists of:
      1) A line starting with the literal "%PDF-" followed by the file version
      2) If the file contains binary data an immediate second line that is a comment
         starting with "%" and containing at least four bytes with values ≥ 128 (non-ASCII).
         This helps file-transfer tools treat the content as binary rather than text.
    """

    def __init__(self, pdf_version):
        self.pdf_version = pdf_version

    # method override
    def serialize(self, _security_handler=None):
        return f"%PDF-{self.pdf_version}\n%éëñ¿"


class PDFFont(PDFObject):
    def __init__(self, subtype, base_font, encoding=None, d_w=None, w=None):
        super().__init__()
        self.type = Name("Font")
        self.subtype = Name(subtype)
        self.base_font = Name(base_font)
        self.encoding = Name(encoding) if encoding else None
        self.d_w = d_w
        self.w = w
        self.descendant_fonts = None
        self.to_unicode = None
        self.c_i_d_system_info = None
        self.font_descriptor = None
        self.c_i_d_to_g_i_d_map = None


class CIDSystemInfo(PDFObject):
    def __init__(self):
        super().__init__()
        self.registry = PDFString("Adobe", encrypt=True)
        self.ordering = PDFString("UCS", encrypt=True)
        self.supplement = 0


class PDFType3Font(PDFObject):
    def __init__(self, font3: "Type3Font"):
        super().__init__()
        self._font3 = font3
        self.type = Name("Font")
        self.name = Name(f"MPDFAA+{font3.base_font.name}")
        self.subtype = Name("Type3")
        self.font_b_box = (
            f"[{self._font3.base_font.ttfont['head'].xMin * self._font3.scale:.0f}"
            f" {self._font3.base_font.ttfont['head'].yMin * self._font3.scale:.0f}"
            f" {self._font3.base_font.ttfont['head'].xMax * self._font3.scale:.0f}"
            f" {self._font3.base_font.ttfont['head'].yMax * self._font3.scale:.0f}]"
        )
        self.font_matrix = "[0.001 0 0 0.001 0 0]"
        self.first_char = min(g.unicode for g in font3.glyphs)
        self.last_char = max(g.unicode for g in font3.glyphs)
        self.resources = None
        self.to_unicode = None

    @property
    def char_procs(self):
        return pdf_dict(
            {f"/{g.glyph_name}": f"{g.obj_id} 0 R" for g in self._font3.glyphs}
        )

    @property
    def encoding(self):
        return pdf_dict(
            {
                Name("/Type"): Name("/Encoding"),
                Name("/Differences"): self.differences_table(),
            }
        )

    @property
    def widths(self):
        sorted_glyphs = sorted(self._font3.glyphs, key=lambda glyph: glyph.unicode)
        # Find the range of unicode values
        min_unicode = sorted_glyphs[0].unicode
        max_unicode = sorted_glyphs[-1].unicode

        # Initialize widths array with zeros
        widths = [0] * (max_unicode + 1 - min_unicode)

        # Populate the widths array
        for glyph in sorted_glyphs:
            widths[glyph.unicode - min_unicode] = round(
                glyph.glyph_width * self._font3.scale + 0.001
            )
        return pdf_list([str(glyph_width) for glyph_width in widths])

    def generate_resources(
        self, img_objs_per_index, gfxstate_objs_per_name, pattern_objs_per_name
    ):
        resources = "<<"
        objects = " ".join(
            f"/I{img} {img_objs_per_index[img].id} 0 R"
            for img in self._font3.images_used
        )
        resources += f"/XObject <<{objects}>>" if len(objects) > 0 else ""

        ext_g_state = " ".join(
            f"/{name} {gfxstate_obj.id} 0 R"
            for name, gfxstate_obj in gfxstate_objs_per_name.items()
            if name in self._font3.graphics_style_used
        )
        resources += f"/ExtGState <<{ext_g_state}>>" if len(ext_g_state) > 0 else ""

        pattern = " ".join(
            f"/{name} {pattern.id} 0 R"
            for name, pattern in pattern_objs_per_name.items()
            if name in self._font3.patterns_used
        )
        resources += f"/Pattern <<{pattern}>>" if len(pattern) > 0 else ""

        resources += ">>"
        self.resources = resources

    def differences_table(self):
        sorted_glyphs = sorted(self._font3.glyphs, key=lambda glyph: glyph.unicode)
        return (
            "["
            + "\n".join(
                f"{glyph.unicode} /{glyph.glyph_name}" for glyph in sorted_glyphs
            )
            + "]"
        )


class PDFInfo(PDFObject):
    def __init__(
        self,
        title,
        subject,
        author,
        keywords,
        creator,
        producer,
        creation_date: PDFDate,
    ):
        super().__init__()
        self.title = PDFString(title, encrypt=True) if title else None
        self.subject = PDFString(subject, encrypt=True) if subject else None
        if author and isinstance(author, (list, tuple, set)):
            author = "; ".join(str(a) for a in author)
        self.author = PDFString(author, encrypt=True) if author else None
        if keywords and isinstance(keywords, (list, tuple, set)):
            keywords = ", ".join(str(keyword) for keyword in keywords)
        self.keywords = PDFString(keywords, encrypt=True) if keywords else None
        self.creator = PDFString(creator, encrypt=True) if creator else None
        self.producer = PDFString(producer, encrypt=True) if producer else None
        self.creation_date = creation_date


class AcroForm:
    def __init__(self, fields, sig_flags):
        self.fields = fields
        self.sig_flags = sig_flags

    def serialize(self, _security_handler=None, _obj_id=None):
        obj_dict = build_obj_dict(
            {key: getattr(self, key) for key in dir(self)},
            _security_handler=_security_handler,
            _obj_id=_obj_id,
        )
        return pdf_dict(obj_dict, field_join=" ")


class PDFCatalog(PDFObject):
    def __init__(
        self, lang=None, page_layout=None, page_mode=None, viewer_preferences=None
    ):
        super().__init__()
        self.type = Name("Catalog")
        self.lang = PDFString(lang) if lang else None
        self.page_layout = page_layout
        self.page_mode = page_mode
        self.viewer_preferences = viewer_preferences
        self.pages = None  # Required; shall be an indirect reference
        self.acro_form = None
        self.open_action = None
        self.mark_info = None
        self.metadata = None
        self.names = None
        self.outlines = None
        self.output_intents = None
        self.struct_tree_root = None


class PDFResources(PDFObject):
    def __init__(self, proc_set, font, x_object, ext_g_state, shading, pattern):
        super().__init__()
        self.proc_set = proc_set
        self.font = font
        self.x_object = x_object
        self.ext_g_state = ext_g_state
        self.shading = shading
        self.pattern = pattern


class PDFFontStream(PDFContentStream):
    def __init__(self, contents):
        super().__init__(contents=contents, compress=True)
        self.length1 = len(contents)


class PDFXmpMetadata(PDFContentStream):
    def __init__(self, contents):
        super().__init__(contents=contents.encode("utf-8"))
        self.type = Name("Metadata")
        self.subtype = Name("XML")


class PDFXObject(PDFContentStream):
    __slots__ = (  # RAM usage optimization
        "_id",
        "_contents",
        "filter",
        "length",
        "type",
        "subtype",
        "width",
        "height",
        "color_space",
        "bits_per_component",
        "decode",
        "decode_parms",
        "s_mask",
    )

    def __init__(
        self,
        contents,
        subtype,
        width,
        height,
        color_space,
        bits_per_component,
        img_filter=None,
        decode=None,
        decode_parms=None,
    ):
        super().__init__(contents=contents)
        self.type = Name("XObject")
        self.subtype = Name(subtype)
        self.width = width
        self.height = height
        self.color_space = color_space
        self.bits_per_component = bits_per_component
        self.filter = Name(img_filter)
        self.decode = decode
        self.decode_parms = decode_parms
        self.s_mask = None


class PDFICCProfile(PDFContentStream):
    """
    Holds values for ICC Profile Stream
    Args:
        contents (str): stream content
        n (int): [1|3|4], # the numbers for colors 1=Gray, 3=RGB, 4=CMYK
        alternate (str): ['DeviceGray'|'DeviceRGB'|'DeviceCMYK']
    """

    __slots__ = (  # RAM usage optimization
        "_id",
        "_contents",
        "filter",
        "length",
        "n",
        "alternate",
    )

    def __init__(
        self,
        contents,
        n,
        alternate,
    ):
        super().__init__(contents=contents, compress=True)
        self.n = n
        self.alternate = Name(alternate)


class PDFPageLabel:
    """
    This will be displayed by some PDF readers to identify pages.
    """

    __slots__ = ("_style", "_prefix", "st")  # RAM usage optimization

    def __init__(
        self, label_style: PageLabelStyle, label_prefix: str, label_start: int
    ):
        self._style: PageLabelStyle = label_style
        self._prefix: str = label_prefix
        self.st: int = label_start

    @property
    def s(self) -> Name:
        return Name(self._style.value) if self._style else None

    @property
    def p(self) -> PDFString:
        return PDFString(self._prefix) if self._prefix else None

    def __repr__(self):
        return f"PDFPageLabel({self._style}, {self._prefix}, {self.st})"

    def __str__(self):
        ret = self._prefix if self._prefix else ""
        if self._style:
            if self._style == PageLabelStyle.NUMBER:
                ret += str(self.st)
            elif self._style == PageLabelStyle.UPPER_ROMAN:
                ret += int2roman(self.st)
            elif self._style == PageLabelStyle.LOWER_ROMAN:
                ret += int2roman(self.st).lower()
            elif self._style == PageLabelStyle.UPPER_LETTER:
                ret += int_to_letters(self.st - 1)
            elif self._style == PageLabelStyle.LOWER_LETTER:
                ret += int_to_letters(self.st - 1).lower()
        return ret

    def serialize(self) -> dict:
        return build_obj_dict({key: getattr(self, key) for key in dir(self)})

    def get_style(self) -> PageLabelStyle:
        return self._style

    def get_prefix(self) -> str:
        return self._prefix

    def get_start(self) -> int:
        return self.st


class PDFPage(PDFObject):
    __slots__ = (  # RAM usage optimization
        "_id",
        "type",
        "contents",
        "dur",
        "trans",
        "annots",
        "group",
        "media_box",
        "struct_parents",
        "resources",
        "parent",
        "_index",
        "_width_pt",
        "_height_pt",
        "_page_label",
        "_text_substitution_fragments",
    )

    def __init__(
        self,
        duration,
        transition,
        contents,
        index,
    ):
        super().__init__()
        self.type = Name("Page")
        self.contents = contents
        self.dur = duration if duration else None
        self.trans = transition
        self.annots = PDFArray()  # list of PDFAnnotation
        self.group = None
        self.media_box = None
        self.struct_parents = None
        self.resources = None  # must always be set before calling .serialize()
        self.parent = None  # must always be set before calling .serialize()
        # Useful properties that will not be serialized in the final PDF document:
        self._index = index
        self._width_pt, self._height_pt = None, None
        self._page_label: PDFPageLabel = None
        self._text_substitution_fragments: list[TotalPagesSubstitutionFragment] = []

    def index(self):
        return self._index

    def set_index(self, i):
        self._index = i

    def dimensions(self):
        "Return a pair (width, height) in the unit specified to FPDF constructor"
        return self._width_pt, self._height_pt

    def set_dimensions(self, width_pt, height_pt):
        "Accepts a pair (width, height) in the unit specified to FPDF constructor"
        self._width_pt, self._height_pt = width_pt, height_pt

    def set_page_label(
        self, previous_page_label: PDFPageLabel, page_label: PDFPageLabel
    ):
        if (
            previous_page_label
            and page_label
            and page_label.get_style() == previous_page_label.get_style()
            and page_label.get_prefix() == previous_page_label.get_prefix()
            and not page_label.st
        ):
            page_label.st = previous_page_label.get_start() + 1

        if page_label:
            if not page_label.get_start():
                page_label.st = 1

        if previous_page_label and not page_label:
            page_label = PDFPageLabel(
                previous_page_label.get_style(),
                previous_page_label.get_prefix(),
                previous_page_label.get_start() + 1,
            )

        self._page_label = page_label

    def get_page_label(self) -> PDFPageLabel:
        return self._page_label

    def get_label(self) -> str:
        return str(self.index()) if not self._page_label else str(self._page_label)

    def get_text_substitutions(self):
        return self._text_substitution_fragments

    def add_text_substitution(self, fragment):
        self._text_substitution_fragments.append(fragment)


class PDFPagesRoot(PDFObject):
    def __init__(self, count, media_box):
        super().__init__()
        self.type = Name("Pages")
        self.count = count
        self.media_box = media_box
        self.kids = None  # must always be set before calling .serialize()


class PDFExtGState(PDFObject):
    def __init__(self, dict_as_str):
        super().__init__()
        self._dict_as_str = dict_as_str

    # method override
    def serialize(self, obj_dict=None, _security_handler=None):
        return f"{self.id} 0 obj\n{self._dict_as_str}\nendobj"


class PDFXrefAndTrailer(ContentWithoutID):
    "Cross-reference table & file trailer"

    def __init__(self, output_builder):
        self.output_builder = output_builder
        self.count = output_builder.obj_id + 1
        # Must be set before the call to serialize():
        self.catalog_obj = None
        self.info_obj = None
        self.encryption_obj = None

    def serialize(self, _security_handler=None):
        builder = self.output_builder
        startxref = str(len(builder.buffer))
        out = []
        out.append("xref")
        out.append(f"0 {self.count}")
        out.append("0000000000 65535 f ")
        for obj_id in range(1, self.count):
            out.append(f"{builder.offsets[obj_id]:010} 00000 n ")
        out.append("trailer")
        out.append("<<")
        out.append(f"/Size {self.count}")
        out.append(f"/Root {pdf_ref(self.catalog_obj.id)}")
        if self.info_obj:
            out.append(f"/Info {pdf_ref(self.info_obj.id)}")
        fpdf = builder.fpdf
        if self.encryption_obj:
            out.append(f"/Encrypt {pdf_ref(self.encryption_obj.id)}")
            file_id = fpdf._security_handler.file_id
        else:
            file_id = fpdf.file_id()
            if file_id == -1:
                file_id = fpdf._default_file_id(builder.buffer)
        if file_id:
            out.append(f"/ID [{file_id}]")
        out.append(">>")
        out.append("startxref")
        out.append(startxref)
        out.append("%%EOF")
        return "\n".join(out)


class OutputIntentDictionary:
    """
    The optional OutputIntents (PDF 1.4) entry in the document
    catalog dictionary holds an array of output intent dictionaries,
    each describing the colour reproduction characteristics of a possible
    output device.

    Args:
        subtype (OutputIntentSubType, required): PDFA, PDFX or ISOPDF
        output_condition_identifier (str, required): see the Name in
            https://www.color.org/registry.xalter
        output_condition (str, optional): see the Definition in
            https://www.color.org/registry.xalter
        registry_name (str, optional): "https://www.color.org"
        dest_output_profile (PDFICCProfile, required/optional):
            PDFICCProfile | None # (required if
            output_condition_identifier does not specify a standard
            production condition; optional otherwise)
        info (str, required/optional see dest_output_profile): human
            readable description of profile
    """

    __slots__ = (  # RAM usage optimization
        "type",
        "s",
        "output_condition_identifier",
        "output_condition",
        "registry_name",
        "dest_output_profile",
        "info",
    )

    def __init__(
        self,
        subtype: "OutputIntentSubType | str",
        output_condition_identifier: str,
        output_condition: str = None,
        registry_name: str = None,
        dest_output_profile: PDFICCProfile = None,
        info: str = None,
    ):
        self.type = Name("OutputIntent")
        self.s = Name(OutputIntentSubType.coerce(subtype).value)
        self.output_condition_identifier = (
            PDFString(output_condition_identifier)
            if output_condition_identifier
            else None
        )
        self.output_condition = (
            PDFString(output_condition) if output_condition else None
        )
        self.registry_name = PDFString(registry_name) if registry_name else None
        self.dest_output_profile = (
            dest_output_profile
            if dest_output_profile and isinstance(dest_output_profile, PDFICCProfile)
            else None
        )
        self.info = PDFString(info) if info else None

    def serialize(self, _security_handler=None, _obj_id=None):
        obj_dict = build_obj_dict(
            {key: getattr(self, key) for key in dir(self)},
            _security_handler=_security_handler,
            _obj_id=_obj_id,
        )
        return pdf_dict(obj_dict)


class ResourceCatalog:
    "Manage the indexing of resources and association to the pages they are used"

    GS_REGEX = re.compile(r"/(GS\d+) gs")
    IMG_REGEX = re.compile(r"/I(\d+) Do")
    PATTERN_FILL_REGEX = re.compile(r"/(P\d+)\s+scn")
    PATTERN_STROKE_REGEX = re.compile(r"/(P\d+)\s+SCN")
    FONT_REGEX = re.compile(r"/F(\d+)\s+[-+]?\d+(?:\.\d+)?\s+Tf")

    def __init__(self):
        self.resources = defaultdict(dict)
        self.resources_per_page = defaultdict(set)
        self.graphics_styles = OrderedDict()
        self.soft_mask_xobjects = []
        self.form_xobjects = []
        self.last_reserved_object_id = 0
        self.font_registry: Dict[str, Union[CoreFont, TTFFont]] = {}
        self.next_xobject_index = 1

    def add(self, resource_type: PDFResourceType, resource, page_number: Optional[int]):
        if resource_type in (PDFResourceType.PATTERN, PDFResourceType.SHADING):
            registry = self.resources[resource_type]
            prefix = self._get_prefix(resource_type)

            if resource not in registry:
                registry[resource] = f"{prefix}{len(registry) + 1}"
            if page_number is not None:
                self.resources_per_page[(page_number, resource_type)].add(
                    registry[resource]
                )
            return registry[resource]

        if (
            resource_type == PDFResourceType.X_OBJECT
            and isinstance(resource, int)
            and resource >= self.next_xobject_index
        ):
            self.next_xobject_index = resource + 1

        self.resources_per_page[(page_number, resource_type)].add(resource)
        return None

    def register_graphics_style(self, style):
        """
        Graphics style can be added without associating to a page number right away,
        like when rendering a svg image.
        The method that adds image to the page will call the add method for the page association.
        """
        style_dict = style.serialize()
        if not style_dict:  # empty style does not need an entry
            return None

        if style_dict not in self.graphics_styles:
            name = Name(
                f"{self._get_prefix(PDFResourceType.EXT_G_STATE)}{len(self.graphics_styles)}"
            )
            self.graphics_styles[style_dict] = name

        return self.graphics_styles[style_dict]

    def register_soft_mask(self, soft_mask: PaintSoftMask) -> int:
        """Register a soft mask xobject and return its object id"""
        self.last_reserved_object_id += 1
        xobject = soft_mask_path_to_xobject(soft_mask, self)
        xobject.id = self.last_reserved_object_id
        self.soft_mask_xobjects.append(xobject)
        return xobject.id

    def register_blend_form(self, blend_group) -> int:
        """Register a blend group Form XObject and return its resource index."""
        xobject = blend_group_to_xobject(blend_group, self)
        index = self.next_xobject_index
        self.next_xobject_index += 1
        self.form_xobjects.append((index, xobject))
        return index

    def scan_stream(self, rendered: str) -> list[tuple[PDFResourceType, str]]:
        """Parse a content stream and return discovered resources"""
        found = set()

        for m in self.GS_REGEX.finditer(rendered):
            found.add((PDFResourceType.EXT_G_STATE, m.group(1)))

        for m in self.IMG_REGEX.finditer(rendered):
            found.add((PDFResourceType.X_OBJECT, int(m.group(1))))

        for m in self.PATTERN_FILL_REGEX.finditer(rendered):
            found.add((PDFResourceType.PATTERN, m.group(1)))

        for m in self.PATTERN_STROKE_REGEX.finditer(rendered):
            found.add((PDFResourceType.PATTERN, m.group(1)))

        for m in self.FONT_REGEX.finditer(rendered):
            found.add((PDFResourceType.FONT, int(m.group(1))))

        return found

    def index_stream_resources(self, rendered: str, page_number: int) -> None:
        """
        Scan a rendered content stream and register resources used on the given page.
        Currently indexes:
          - ExtGState invocations: '/GSn gs'
          - Image XObjects: '/In Do'
        """
        for resource_type, resource in self.scan_stream(rendered):
            if resource_type == PDFResourceType.PATTERN:
                self.resources_per_page[(page_number, PDFResourceType.PATTERN)].add(
                    resource
                )
            else:
                self.add(resource_type, resource, page_number)

    def get_items(self, resource_type: PDFResourceType):
        return self.resources[resource_type].items()

    def get_resources_per_page(self, page_number: int, resource_type: PDFResourceType):
        return self.resources_per_page[(page_number, resource_type)]

    def get_used_resources(self, resource_type: PDFResourceType):
        unique = set()
        for (_, rtype), resource in self.resources_per_page.items():
            if rtype == resource_type:
                unique.update(resource)
        return unique

    @classmethod
    def _get_prefix(cls, resource_type: PDFResourceType):
        if resource_type == PDFResourceType.EXT_G_STATE:
            return "GS"
        if resource_type == PDFResourceType.PATTERN:
            return "P"
        if resource_type == PDFResourceType.SHADING:
            return "Sh"
        raise ValueError(f"No prefix for resource type {resource_type}")

    def get_font_from_family(
        self, font_family: str, font_style: str = ""
    ) -> Union["CoreFont", "TTFFont"]:
        """
        Resolve a family+style to a concrete font instance from the font registry.
        Behavior:
          - Exact match (family.lower() + style.upper()) in registry: return it
          - If `family` names a core font: add CoreFont to registry (if missing) and return it
          - If `family` is an alias/generic: translate to a core font, add to registry (if missing), and return it
          - Otherwise: raise KeyError

        Notes:
          - For Symbol/ZapfDingbats, style is forced to "" (they don't support B/I).
        """
        if not font_family:
            raise KeyError("Empty font family")

        style = "".join(sorted(font_style.upper()))

        alias = {
            # sans
            "sans-serif": "helvetica",
            "sans serif": "helvetica",
            "arial": "helvetica",
            "verdana": "helvetica",
            "tahoma": "helvetica",
            "segoe ui": "helvetica",
            # serif
            "serif": "times",
            "times": "times",
            "times new roman": "times",
            "georgia": "times",
            "cambria": "times",
            "garamond": "times",
            # mono
            "monospace": "courier",
            "courier": "courier",
            "courier new": "courier",
            "consolas": "courier",
            "monaco": "courier",
            # symbol
            "symbol": "symbol",
            "zapfdingbats": "zapfdingbats",
            "zapf dingbats": "zapfdingbats",
        }

        for candidate in font_family.strip().strip("'\"").split(","):
            family = candidate.strip().strip("'\"").lower()

            # 1) Exact match
            fontkey = f"{family}{style}"
            if fontkey in self.font_registry:
                return self.font_registry[fontkey]

            # 2) Core-family direct hit?
            if family in CORE_FONTS:
                core_style = "" if family in {"symbol", "zapfdingbats"} else style
                key = f"{family}{core_style}"
                if key not in self.font_registry:
                    i = len(self.font_registry) + 1
                    self.font_registry[key] = CoreFont(i, key, core_style)
                return self.font_registry[key]

            # 3) Alias / generic mapping to core font
            mapped = alias.get(family)
            if mapped:
                core_style = "" if mapped in {"symbol", "zapfdingbats"} else style
                key = f"{mapped}{core_style}"
                if key not in self.font_registry:
                    i = len(self.font_registry) + 1
                    self.font_registry[key] = CoreFont(i, key, core_style)
                return self.font_registry[key]

        # 4) Fail: do not return anything
        raise KeyError(f"No suitable font for family={font_family!r}, style={style!r}")


class OutputProducer:
    "Generates the final bytearray representing the PDF document, based on a FPDF instance."

    def __init__(self, fpdf: "FPDF"):
        self.fpdf = fpdf
        self.pdf_objs = []
        self.iccp_i_to_pdf_i = {}
        self.obj_id = (
            fpdf._resource_catalog.last_reserved_object_id
        )  # current PDF object number
        # array of PDF object offsets in self.buffer, used to build the xref table:
        self.offsets = {}
        self.trace_labels_per_obj_id = {}
        self.sections_size_per_trace_label = defaultdict(int)
        self.buffer = bytearray()  # resulting output buffer

    def bufferize(self):
        """
        This method alters the target FPDF instance
        by assigning IDs to all PDF objects,
        plus a few other properties on PDFPage instances
        """
        fpdf = self.fpdf

        # 1. Setup - Insert all PDF objects
        #    and assign unique consecutive numeric IDs to all of them

        if fpdf._security_handler:
            # get the file_id and generate passwords needed to encrypt streams and strings
            file_id = fpdf.file_id()
            if file_id == -1:
                # no custom file id - use default file id so encryption passwords can be generated
                file_id = fpdf._default_file_id(bytearray(0x00))
            fpdf._security_handler.generate_passwords(file_id)

        pdf_version = fpdf.pdf_version
        if (
            fpdf.viewer_preferences
            and fpdf.viewer_preferences._min_pdf_version > pdf_version
        ):
            pdf_version = fpdf.viewer_preferences._min_pdf_version
        self.pdf_objs.append(PDFHeader(pdf_version))
        pages_root_obj = self._add_pages_root()
        catalog_obj = self._add_catalog()
        page_objs = self._add_pages()
        sig_annotation_obj = self._add_annotations_as_objects()
        for embedded_file in fpdf.embedded_files:
            self._add_pdf_obj(embedded_file, "embedded_files")
            self._add_pdf_obj(embedded_file.file_spec(), "file_spec")
        self._insert_resources(page_objs)
        struct_tree_root_obj = self._add_structure_tree()
        outline_dict_obj, outline_items = self._add_document_outline()
        xmp_metadata_obj = self._add_xmp_metadata()
        info_obj = None
        if not fpdf._compliance:
            info_obj = self._add_info()
        encryption_obj = self._add_encryption()

        xref = PDFXrefAndTrailer(self)
        self.pdf_objs.append(xref)

        # 2. Plumbing - Inject all PDF object references required:
        pages_root_obj.kids = PDFArray(page_objs)
        self._finalize_catalog(
            catalog_obj,
            pages_root_obj=pages_root_obj,
            first_page_obj=page_objs[0],
            sig_annotation_obj=sig_annotation_obj,
            xmp_metadata_obj=xmp_metadata_obj,
            struct_tree_root_obj=struct_tree_root_obj,
            outline_dict_obj=outline_dict_obj,
        )
        dests = []
        for page_obj in page_objs:
            page_obj.parent = pages_root_obj
            for annot in page_obj.annots:
                page_dests = []
                if annot.dest:
                    # Only add to page_dests if it's a Destination object (not a string/PDFString)
                    if hasattr(annot.dest, "page_number"):
                        page_dests.append(annot.dest)
                if annot.a and hasattr(annot.a, "dest"):
                    # Only add to page_dests if it's a Destination object (not a string/PDFString)
                    if hasattr(annot.a.dest, "page_number"):
                        page_dests.append(annot.a.dest)
                for dest in page_dests:
                    if dest.page_number > len(page_objs):
                        raise ValueError(
                            f"Invalid reference to non-existing page {dest.page_number} present on page {page_obj.index()}: "
                        )
                dests.extend(page_dests)
            if not page_obj.annots:
                # Avoid serializing an empty PDFArray:
                page_obj.annots = None
        for outline_item in outline_items:
            dests.append(outline_item.dest)
        # Assigning the .page_ref property of all Destination objects:
        for dest in dests:
            dest.page_ref = pdf_ref(page_objs[dest.page_number - 1].id)
        for struct_elem in fpdf.struct_builder.doc_struct_elem.k:
            struct_elem.pg = page_objs[struct_elem.page_number() - 1]
        xref.catalog_obj = catalog_obj
        xref.info_obj = info_obj
        xref.encryption_obj = encryption_obj

        # 3. Serializing - Append all PDF objects to the buffer:
        assert (
            not self.buffer
        ), f"Nothing should have been appended to the .buffer at this stage: {self.buffer}"
        assert (
            not self.offsets
        ), f"No offset should have been set at this stage: {len(self.offsets)}"

        for pdf_obj in self.pdf_objs:
            if isinstance(pdf_obj, ContentWithoutID):
                # top header, xref table & trailer:
                trace_label = None
            else:
                self.offsets[pdf_obj.id] = len(self.buffer)
                trace_label = self.trace_labels_per_obj_id.get(pdf_obj.id)
            if trace_label:
                with self._trace_size(trace_label):
                    self._out(
                        pdf_obj.serialize(_security_handler=fpdf._security_handler)
                    )
            else:
                self._out(pdf_obj.serialize(_security_handler=fpdf._security_handler))
        self._log_final_sections_sizes()

        if fpdf._sign_key:
            self.buffer = sign_content(
                signer,
                self.buffer,
                fpdf._sign_key,
                fpdf._sign_cert,
                fpdf._sign_extra_certs,
                fpdf._sign_hashalgo,
                fpdf._sign_time,
            )
        return self.buffer

    def _out(self, data):
        "Append data to the buffer"
        if not isinstance(data, bytes):
            if not isinstance(data, str):
                data = str(data)
            data = data.encode("latin1")
        self.buffer += data + b"\n"

    def _add_pdf_obj(self, pdf_obj, trace_label=None):
        self.obj_id += 1
        pdf_obj.id = self.obj_id
        self.pdf_objs.append(pdf_obj)
        if trace_label:
            self.trace_labels_per_obj_id[self.obj_id] = trace_label
        return self.obj_id

    def _add_pages_root(self):
        fpdf = self.fpdf
        pages_root_obj = PDFPagesRoot(
            count=fpdf.pages_count,
            media_box=_dimensions_to_mediabox(fpdf.default_page_dimensions),
        )
        self._add_pdf_obj(pages_root_obj)
        return pages_root_obj

    def _iter_pages_in_order(self):
        for page_index in range(1, self.fpdf.pages_count + 1):
            page_obj = self.fpdf.pages[page_index]
            # Defensive check:
            assert (
                page_obj.index() == page_index
            ), f"{page_obj.index()=} != {page_index=}"
            yield page_obj

    def _add_pages(self, _slice=slice(0, None)):
        fpdf = self.fpdf
        page_objs = []
        for page_obj in list(self._iter_pages_in_order())[_slice]:
            if fpdf.pdf_version > "1.3" and fpdf.allow_images_transparency:
                page_obj.group = pdf_dict(
                    {"/Type": "/Group", "/S": "/Transparency", "/CS": "/DeviceRGB"},
                    field_join=" ",
                )
            if page_obj.dimensions() != fpdf.default_page_dimensions:
                page_obj.media_box = _dimensions_to_mediabox(page_obj.dimensions())
            self._add_pdf_obj(page_obj, "pages")
            page_objs.append(page_obj)

            # Extracting the page contents to insert it as a content stream:
            cs_obj = PDFContentStream(
                contents=page_obj.contents, compress=fpdf.compress
            )
            self._add_pdf_obj(cs_obj, "pages")
            page_obj.contents = cs_obj

        return page_objs

    def _add_annotations_as_objects(self):
        sig_annotation_obj = None
        for page_obj in self.fpdf.pages.values():
            for annot_obj in page_obj.annots:
                if isinstance(annot_obj, PDFAnnotation):  # distinct from AnnotationDict
                    self._add_pdf_obj(annot_obj)
                    if isinstance(annot_obj.v, Signature):
                        assert (
                            sig_annotation_obj is None
                        ), "A /Sig annotation is present on more than 1 page"
                        sig_annotation_obj = annot_obj
        return sig_annotation_obj

    def _add_fonts(
        self, image_objects_per_index, gfxstate_objs_per_name, pattern_objs_per_name
    ):
        font_objs_per_index = {}
        for font in sorted(self.fpdf.fonts.values(), key=lambda font: font.i):

            # type 3 font
            if font.type == "TTF" and font.color_font:
                if font.subset._next > 0xFF:
                    raise FPDFException(
                        "Type 3 fonts with color glyphs are not supported is more than 255 glyphs are rendered. "
                        "Set FPDF.render_color_fonts=False or use less color glyphs."
                    )
                for glyph in font.color_font.glyphs:
                    glyph.obj_id = self._add_pdf_obj(
                        PDFContentStream(
                            contents=glyph.glyph.encode("latin-1"),
                            compress=self.fpdf.compress,
                        ),
                        "fonts",
                    )
                bfChar = []

                for glyph, code_mapped in font.subset.items():
                    if len(glyph.unicode) == 0:
                        continue
                    bfChar.append(
                        f'<{code_mapped:02X}> <{"".join(chr(code).encode("utf-16-be").hex().upper() for code in glyph.unicode)}>\n'
                    )

                to_unicode_obj = PDFContentStream(
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
                    "<00> <FF>\n"
                    "endcodespacerange\n"
                    f"{len(bfChar)} beginbfchar\n"
                    f"{''.join(bfChar)}"
                    "endbfchar\n"
                    "endcmap\n"
                    "CMapName currentdict /CMap defineresource pop\n"
                    "end\n"
                    "end"
                )
                self._add_pdf_obj(to_unicode_obj, "fonts")

                t3_font_obj = PDFType3Font(font.color_font)
                t3_font_obj.to_unicode = pdf_ref(to_unicode_obj.id)
                t3_font_obj.generate_resources(
                    image_objects_per_index,
                    gfxstate_objs_per_name,
                    pattern_objs_per_name,
                )
                self._add_pdf_obj(t3_font_obj, "fonts")
                font_objs_per_index[font.i] = t3_font_obj
                continue

            # Standard font
            if font.type == "core":
                encoding = (
                    "WinAnsiEncoding"
                    if font.name not in ("Symbol", "ZapfDingbats")
                    else None
                )
                core_font_obj = PDFFont(
                    subtype="Type1", base_font=font.name, encoding=encoding
                )
                self._add_pdf_obj(core_font_obj, "fonts")
                font_objs_per_index[font.i] = core_font_obj
            elif font.type == "TTF":
                fontname = f"MPDFAA+{font.name}"

                # 1. get all glyphs in PDF
                glyph_names = font.subset.get_all_glyph_names()

                if len(font.missing_glyphs) > 0:
                    msg = ", ".join(
                        f"'{chr(x)}' ({chr(x).encode('unicode-escape').decode()})"
                        for x in font.missing_glyphs[:10]
                    )
                    if len(font.missing_glyphs) > 10:
                        msg += f", ... (and {len(font.missing_glyphs) - 10} others)"
                    LOGGER.warning(
                        "Font %s is missing the following glyphs: %s", fontname, msg
                    )

                # 2. make a subset
                # notdef_outline=True means that keeps the white box for the .notdef glyph
                # recommended_glyphs=True means that adds the .notdef, .null, CR, and space glyphs
                options = ftsubset.Options(notdef_outline=True, recommended_glyphs=True)
                # dropping some tables that currently not used:
                options.drop_tables += [
                    "FFTM",  # FontForge Timestamp table - cf. https://github.com/py-pdf/fpdf2/issues/600
                    "GDEF",  # Glyph Definition table = various glyph properties used in OpenType layout processing
                    "GPOS",  # Glyph Positioning table = precise control over glyph placement
                    #          for sophisticated text layout and rendering in each script and language system
                    "GSUB",  # Glyph Substitution table = data for substitution of glyphs for appropriate rendering of scripts
                    "MATH",  # Mathematical typesetting table = specific information necessary for math formula layout
                    "hdmx",  # Horizontal Device Metrics table, stores integer advance widths scaled to particular pixel sizes
                    #          for OpenType™ fonts with TrueType outlines
                    "meta",  # metadata table
                    "sbix",  # Apple's SBIX table, used for color bitmap glyphs
                    "CBDT",  # Color Bitmap Data Table
                    "CBLC",  # Color Bitmap Location Table
                    "EBDT",  # Embedded Bitmap Data Table
                    "EBLC",  # Embedded Bitmap Location Table
                    "EBSC",  # Embedded Bitmap Scaling Table
                    "SVG ",  # SVG table
                    "CPAL",  # Color Palette table
                    "COLR",  # Color table
                ]
                subsetter = ftsubset.Subsetter(options)
                subsetter.populate(glyphs=glyph_names)
                subsetter.subset(font.ttfont)

                # 3. make codeToGlyph
                # is a map Character_ID -> Glyph_ID
                # it's used for associating glyphs to new codes
                # this basically takes the old code of the character
                # take the glyph associated with it
                # and then associate to the new code the glyph associated with the old code

                code_to_glyph = {
                    char_id: font.ttfont.getGlyphID(glyph.glyph_name)
                    for glyph, char_id in font.subset.items()
                }

                # 4. return the ttfile
                output = BytesIO()
                font.ttfont.save(output)

                output.seek(0)
                ttfontstream = output.read()

                # A composite font - a font composed of other fonts,
                # organized hierarchically
                composite_font_obj = PDFFont(
                    subtype="Type0", base_font=fontname, encoding="Identity-H"
                )
                self._add_pdf_obj(composite_font_obj, "fonts")
                font_objs_per_index[font.i] = composite_font_obj

                # A CIDFont whose glyph descriptions are based on
                # TrueType font technology
                cid_font_obj = PDFFont(
                    subtype="CIDFontType2",
                    base_font=fontname,
                    d_w=font.desc.missing_width,
                    w=_tt_font_widths(font),
                )
                self._add_pdf_obj(cid_font_obj, "fonts")
                composite_font_obj.descendant_fonts = PDFArray([cid_font_obj])

                # bfChar
                # This table informs the PDF reader about the unicode
                # character that each used 16-bit code belongs to. It
                # allows searching the file and copying text from it.
                bfChar = []

                def format_code(unicode):
                    if unicode > 0xFFFF:
                        # Calculate surrogate pair
                        code_high = 0xD800 | (unicode - 0x10000) >> 10
                        code_low = 0xDC00 | (unicode & 0x3FF)
                        return f"{code_high:04X}{code_low:04X}"
                    return f"{unicode:04X}"

                for glyph, code_mapped in font.subset.items():
                    if len(glyph.unicode) == 0:
                        continue
                    bfChar.append(
                        f'<{code_mapped:04X}> <{"".join(format_code(code) for code in glyph.unicode)}>\n'
                    )

                to_unicode_obj = PDFContentStream(
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
                self._add_pdf_obj(to_unicode_obj, "fonts")
                composite_font_obj.to_unicode = to_unicode_obj

                cid_system_info_obj = CIDSystemInfo()
                self._add_pdf_obj(cid_system_info_obj, "fonts")
                cid_font_obj.c_i_d_system_info = cid_system_info_obj

                font_descriptor_obj = font.desc
                font_descriptor_obj.font_name = Name(fontname)
                self._add_pdf_obj(font_descriptor_obj, "fonts")
                cid_font_obj.font_descriptor = font_descriptor_obj

                # Embed CIDToGIDMap
                # A specification of the mapping from CIDs to glyph indices
                cid_to_gid_map = ["\x00"] * 256 * 256 * 2
                for cc, glyph in code_to_glyph.items():
                    cid_to_gid_map[cc * 2] = chr(glyph >> 8)
                    cid_to_gid_map[cc * 2 + 1] = chr(glyph & 0xFF)
                cid_to_gid_map = "".join(cid_to_gid_map)

                # manage binary data as latin1 until PEP461-like function is implemented
                cid_to_gid_map_obj = PDFContentStream(
                    contents=cid_to_gid_map.encode("latin1"), compress=True
                )
                self._add_pdf_obj(cid_to_gid_map_obj, "fonts")
                cid_font_obj.c_i_d_to_g_i_d_map = cid_to_gid_map_obj

                font_file_cs_obj = PDFFontStream(contents=ttfontstream)
                self._add_pdf_obj(font_file_cs_obj, "fonts")
                font_descriptor_obj.font_file2 = font_file_cs_obj

                font.subset.pick.cache_clear()
                font.subset.get_glyph.cache_clear()
                font.close()

        return font_objs_per_index

    def _add_images(self):
        img_objs_per_index = {}
        for img in sorted(
            self.fpdf.image_cache.images.values(), key=lambda img: img["i"]
        ):
            if img["usages"] > 0:
                img_objs_per_index[img["i"]] = self._add_image(img)
        return img_objs_per_index

    def _ensure_iccp(self, img_info):
        """
        Returns the PDF object of the ICC profile indexed iccp_i in the FPDF object.
        Adds it if not present.
        """
        iccp_i = img_info["iccp_i"]
        if iccp_i in self.iccp_i_to_pdf_i:
            return self.iccp_i_to_pdf_i[iccp_i]
        iccp_content = None
        for iccp_c, i in self.fpdf.image_cache.icc_profiles.items():
            if iccp_i == i:
                iccp_content = iccp_c
                break
        assert iccp_content is not None
        # Note: n should be 4 if the profile ColorSpace is CMYK
        iccp_obj = PDFICCProfile(
            contents=iccp_content, n=img_info["dpn"], alternate=img_info["cs"]
        )
        iccp_pdf_i = self._add_pdf_obj(iccp_obj, "iccp")
        self.iccp_i_to_pdf_i[iccp_i] = iccp_pdf_i
        return iccp_pdf_i

    def _add_image(self, info):
        color_space = Name(info["cs"])
        decode = None
        iccp_i = info.get("iccp_i")
        if color_space == "Indexed":
            color_space = PDFArray(
                ["/Indexed", "/DeviceRGB", f"{len(info['pal']) // 3 - 1}"]
            )
        elif iccp_i is not None:
            iccp_pdf_i = self._ensure_iccp(info)
            color_space = PDFArray(["/ICCBased", str(iccp_pdf_i), str("0"), "R"])
        elif color_space == "DeviceCMYK":
            if info["inverted"] is True:
                decode = "[1 0 1 0 1 0 1 0]"

        decode_parms = f"<<{info['dp']} /BitsPerComponent {info['bpc']}>>"
        img_obj = PDFXObject(
            subtype="Image",
            contents=info["data"],
            width=info["w"],
            height=info["h"],
            color_space=color_space,
            bits_per_component=info["bpc"],
            img_filter=info["f"],
            decode=decode,
            decode_parms=decode_parms,
        )
        info["obj_id"] = self._add_pdf_obj(img_obj, "images")

        # Soft mask
        if self.fpdf.allow_images_transparency and "smask" in info:
            dp = f"/Predictor 15 /Colors 1 /Columns {info['w']}"
            img_obj.s_mask = self._add_image(
                {
                    "w": info["w"],
                    "h": info["h"],
                    "cs": "DeviceGray",
                    "bpc": 8,
                    "f": info["f"],
                    "dp": dp,
                    "data": info["smask"],
                }
            )

        # Palette
        if "/Indexed" in color_space:
            pal_cs_obj = PDFContentStream(
                contents=info["pal"], compress=self.fpdf.compress
            )
            self._add_pdf_obj(pal_cs_obj, "images")
            img_obj.color_space.append(pdf_ref(pal_cs_obj.id))

        return img_obj

    def _add_gfxstates(self):
        gfxstate_objs_per_name = OrderedDict()
        for state_dict, name in self.fpdf._resource_catalog.graphics_styles.items():
            gfxstate_obj = PDFExtGState(state_dict)
            self._add_pdf_obj(gfxstate_obj, "gfxstate")
            gfxstate_objs_per_name[name] = gfxstate_obj
        return gfxstate_objs_per_name

    def _add_soft_masks(self, gfxstate_objs_per_name, pattern_objs_per_name):
        """Append soft-mask Form XObjects after patterns exist so we can resolve /Pattern ids."""
        for soft_mask in self.fpdf._resource_catalog.soft_mask_xobjects:
            soft_mask.resources = soft_mask._path.get_resource_dictionary(
                gfxstate_objs_per_name, pattern_objs_per_name
            )
            self.pdf_objs.append(soft_mask)

    def _register_form_xobject_placeholders(self, img_objs_per_index):
        """Ensure isolated blend forms are part of the XObject set before other resources rely on them."""
        for index, xobject in self.fpdf._resource_catalog.form_xobjects:
            if not getattr(xobject, "_registered", False):
                self._add_pdf_obj(xobject, "images")
                xobject._registered = True
            img_objs_per_index.setdefault(index, xobject)

    def _finalize_form_xobjects(
        self,
        img_objs_per_index,
        gfxstate_objs_per_name,
        pattern_objs_per_name,
        shading_objs_per_name,
        font_objs_per_index,
    ):
        """Populate resource dictionaries for isolated blend Form XObjects."""
        for _, xobject in self.fpdf._resource_catalog.form_xobjects:
            blend_group = getattr(xobject, "_blend_group", None)
            if blend_group is not None:
                xobject.resources = blend_group.get_resource_dictionary(
                    gfxstate_objs_per_name,
                    pattern_objs_per_name,
                    shading_objs_per_name,
                    font_objs_per_index,
                    img_objs_per_index,
                )

    def _add_shadings(self):
        shading_objs_per_name = OrderedDict()
        for shading, name in self.fpdf._resource_catalog.get_items(
            PDFResourceType.SHADING
        ):
            for function in shading.get_functions():
                self._add_pdf_obj(function, "function")
            shading_obj = shading.get_shading_object()
            self._add_pdf_obj(shading_obj, "shading")
            shading_objs_per_name[name] = shading_obj
        return shading_objs_per_name

    def _add_patterns(self):
        pattern_objs_per_name = OrderedDict()
        for pattern, name in self.fpdf._resource_catalog.get_items(
            PDFResourceType.PATTERN
        ):
            self._add_pdf_obj(pattern, "pattern")
            pattern_objs_per_name[name] = pattern
            if pattern.get_apply_page_ctm():
                pattern.set_matrix(
                    pattern.get_matrix()
                    @ Transform.translation(0, -self.fpdf.h)
                    .scale(x=1, y=-1)
                    .scale(self.fpdf.k)
                )

        return pattern_objs_per_name

    def _insert_resources(self, page_objs):
        img_objs_per_index = self._add_images()
        self._register_form_xobject_placeholders(img_objs_per_index)
        gfxstate_objs_per_name = self._add_gfxstates()
        pattern_objs_per_name = self._add_patterns()
        font_objs_per_index = self._add_fonts(
            img_objs_per_index, gfxstate_objs_per_name, pattern_objs_per_name
        )
        shading_objs_per_name = self._add_shadings()
        self._finalize_form_xobjects(
            img_objs_per_index,
            gfxstate_objs_per_name,
            pattern_objs_per_name,
            shading_objs_per_name,
            font_objs_per_index,
        )
        self._add_soft_masks(gfxstate_objs_per_name, pattern_objs_per_name)
        # Insert /Resources dicts:
        if self.fpdf.single_resources_object:
            resources_dict_obj = self._add_resources_dict(
                font_objs_per_index,
                img_objs_per_index,
                gfxstate_objs_per_name,
                shading_objs_per_name,
                pattern_objs_per_name,
            )
            for page_obj in page_objs:
                page_obj.resources = resources_dict_obj
        else:
            for page_number, page_obj in enumerate(page_objs, start=1):
                page_font_objs_per_index = {
                    font_id: font_objs_per_index[font_id]
                    for font_id in self.fpdf._resource_catalog.get_resources_per_page(
                        page_number, PDFResourceType.FONT
                    )
                }
                page_img_objs_per_index = {
                    img_id: img_objs_per_index[img_id]
                    for img_id in self.fpdf._resource_catalog.get_resources_per_page(
                        page_number, PDFResourceType.X_OBJECT
                    )
                }
                page_gfxstate_objs_per_name = {
                    gfx_name: gfx_state
                    for (gfx_name, gfx_state) in gfxstate_objs_per_name.items()
                    if gfx_name
                    in self.fpdf._resource_catalog.get_resources_per_page(
                        page_number, PDFResourceType.EXT_G_STATE
                    )
                }
                page_shading_objs_per_name = {
                    shading_name: shading_objs_per_name[shading_name]
                    for shading_name in self.fpdf._resource_catalog.get_resources_per_page(
                        page_number, PDFResourceType.SHADING
                    )
                }
                page_pattern_objs_per_name = {
                    pattern_name: pattern_objs_per_name[pattern_name]
                    for pattern_name in self.fpdf._resource_catalog.get_resources_per_page(
                        page_number, PDFResourceType.PATTERN
                    )
                }
                page_obj.resources = self._add_resources_dict(
                    page_font_objs_per_index,
                    page_img_objs_per_index,
                    page_gfxstate_objs_per_name,
                    page_shading_objs_per_name,
                    page_pattern_objs_per_name,
                )

    def _add_resources_dict(
        self,
        font_objs_per_index,
        img_objs_per_index,
        gfxstate_objs_per_name,
        shading_objs_per_name,
        pattern_objs_per_name,
    ):
        # From section 10.1, "Procedure Sets", of PDF 1.7 spec:
        # > Beginning with PDF 1.4, this feature is considered obsolete.
        # > For compatibility with existing consumer applications,
        # > PDF producer applications should continue to specify procedure sets
        # > (preferably, all of those listed in Table 10.1).
        proc_set = "[/PDF /Text /ImageB /ImageC /ImageI]"
        font, x_object, ext_g_state, shading, pattern = None, None, None, None, None

        if font_objs_per_index:
            font = pdf_dict(
                {
                    f"/F{index}": pdf_ref(font_obj.id)
                    for index, font_obj in sorted(font_objs_per_index.items())
                }
            )

        if img_objs_per_index:
            x_object = pdf_dict(
                {
                    f"/I{index}": pdf_ref(img_obj.id)
                    for index, img_obj in sorted(img_objs_per_index.items())
                }
            )

        if gfxstate_objs_per_name:
            ext_g_state = pdf_dict(
                {
                    f"/{name}": pdf_ref(gfxstate_obj.id)
                    for name, gfxstate_obj in gfxstate_objs_per_name.items()
                }
            )
        if shading_objs_per_name:
            shading = pdf_dict(
                {
                    f"/{name}": pdf_ref(shading_obj.id)
                    for name, shading_obj in sorted(shading_objs_per_name.items())
                }
            )

        if pattern_objs_per_name:
            pattern = pdf_dict(
                {
                    f"/{name}": pdf_ref(pattern_obj.id)
                    for name, pattern_obj in sorted(pattern_objs_per_name.items())
                }
            )

        resources_obj = PDFResources(
            proc_set=proc_set,
            font=font,
            x_object=x_object,
            ext_g_state=ext_g_state,
            shading=shading,
            pattern=pattern,
        )
        self._add_pdf_obj(resources_obj)
        return resources_obj

    def _add_structure_tree(self):
        "Builds a Structure Hierarchy, including image alternate descriptions"
        if self.fpdf.struct_builder.empty():
            return None
        struct_tree_root_obj = None
        for pdf_obj in self.fpdf.struct_builder:
            if struct_tree_root_obj is None:
                struct_tree_root_obj = pdf_obj
            self._add_pdf_obj(pdf_obj, "structure_tree")
        return struct_tree_root_obj

    def _add_document_outline(self):
        if not self.fpdf._outline:
            return None, ()
        outline_dict_obj, outline_items = None, []
        for pdf_obj in build_outline_objs(self.fpdf._outline):
            if outline_dict_obj is None:
                outline_dict_obj = pdf_obj
            else:
                outline_items.append(pdf_obj)
            self._add_pdf_obj(pdf_obj, "document_outline")
        return outline_dict_obj, outline_items

    def _add_xmp_metadata(self):
        # Prefer explicitly provided XMP (user-supplied inner <x:xmpmeta/> without xpacket):
        xmp_src = self.fpdf.xmp_metadata
        # If not provided but a PDF/A document is being created, synthesize it:
        if not xmp_src and self.fpdf._compliance:
            xmp_src = self._build_xmp_from_info()
        if not xmp_src:
            return None
        xpacket = f'<?xpacket begin="{chr(0xFEFF)}" id="W5M0MpCehiHzreSzNTczkc9d"?>\n{xmp_src}\n<?xpacket end="w"?>\n'
        pdf_obj = PDFXmpMetadata(xpacket)
        self._add_pdf_obj(pdf_obj)
        return pdf_obj

    def _build_xmp_from_info(self) -> str:
        title = getattr(self.fpdf, "title", None) or ""
        subject = getattr(self.fpdf, "subject", None) or ""
        author = getattr(self.fpdf, "author", None) or ""
        if author and isinstance(author, str):
            author = [author]
        keywords = getattr(self.fpdf, "keywords", None) or ""
        if keywords and isinstance(keywords, str):
            keywords = [keywords]
        creator_tool = getattr(self.fpdf, "creator", None) or ""
        producer = getattr(self.fpdf, "producer", None) or ""
        cdate = getattr(self.fpdf, "creation_date", None)
        creation_date_utc = None
        if isinstance(cdate, datetime):
            creation_date_utc = cdate if cdate.tzinfo else cdate.astimezone()
            creation_date_utc = creation_date_utc.astimezone(timezone.utc)
        pdfa = self.fpdf._compliance

        # Escape for XML attributes/PCDATA:
        def esc(s):
            """Return XML-escaped text suitable for XMP (attributes or text nodes)."""
            value = "" if s is None else _html_escape(str(s), quote=True)
            return value.replace("'", "&apos;")

        # XMP times are ISO 8601 (e.g., 2025-09-01T12:34:56+02:00):
        EPOCH = datetime(1969, 12, 31, 19, 0, 0, tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if creation_date_utc == EPOCH:
            xmp_create = EPOCH.isoformat(timespec="seconds")
            xmp_modify = EPOCH.isoformat(timespec="seconds")
        else:
            create_dt = creation_date_utc or now
            xmp_create = create_dt.isoformat(timespec="seconds")
            xmp_modify = now.isoformat(timespec="seconds")
        # Build a single Description that includes everything + pdfaid if requested:
        parts = [
            '<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="fpdf2">',
            "  <rdf:RDF",
            '    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"',
            '    xmlns:dc="http://purl.org/dc/elements/1.1/"',
            '    xmlns:xmp="http://ns.adobe.com/xap/1.0/"',
            '    xmlns:pdf="http://ns.adobe.com/pdf/1.3/"',
            '    xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/">',
            '    <rdf:Description rdf:about=""',
        ]
        # attributes block (xmp, pdf, pdfaid)
        if creator_tool:
            parts.append(f'        xmp:CreatorTool="{esc(creator_tool)}"')
        if xmp_create:
            parts.append(f'        xmp:CreateDate="{esc(xmp_create)}"')
            parts.append(f'        xmp:ModifyDate="{esc(xmp_modify)}"')
            parts.append(f'        xmp:MetadataDate="{esc(xmp_modify)}"')
        if producer:
            parts.append(f'        pdf:Producer="{esc(producer)}"')
        if keywords:
            keyword_list = ",".join(keywords)
            parts.append(f'        pdf:Keywords="{esc(keyword_list)}"')
        parts.append("      >")
        # nested elements (Lang Alt / Seqs)
        if pdfa:
            parts.append(f"      <pdfaid:part>{int(pdfa.part)}</pdfaid:part>")
            if pdfa.conformance:
                parts.append(
                    f"      <pdfaid:conformance>{esc(pdfa.conformance)}</pdfaid:conformance>"
                )
            if pdfa.part == 4:
                parts.append("      <pdfaid:rev>2020</pdfaid:rev>")
        if title:
            parts += [
                "      <dc:title><rdf:Alt>",
                '        <rdf:li xml:lang="x-default">' + esc(title) + "</rdf:li>",
                "      </rdf:Alt></dc:title>",
            ]
        if subject:
            parts += [
                "      <dc:description><rdf:Alt>",
                '        <rdf:li xml:lang="x-default">' + esc(subject) + "</rdf:li>",
                "      </rdf:Alt></dc:description>",
            ]
        if author:
            parts.append("      <dc:creator><rdf:Seq>")
            for a in author:
                parts.append(f"        <rdf:li>{esc(a)}</rdf:li>")
            parts.append("      </rdf:Seq></dc:creator>")
        parts += [
            "    </rdf:Description>",
            "  </rdf:RDF>",
            "</x:xmpmeta>",
        ]
        return "\n".join(parts)

    def _add_info(self):
        fpdf = self.fpdf
        creation_date = None
        if fpdf.creation_date:
            try:
                creation_date = PDFDate(fpdf.creation_date, with_tz=True, encrypt=True)
            except Exception as error:
                raise FPDFException(
                    f"Could not format date: {fpdf.creation_date}"
                ) from error
        info_obj = PDFInfo(
            title=fpdf.title,
            subject=getattr(fpdf, "subject", None),
            author=getattr(fpdf, "author", None),
            keywords=getattr(fpdf, "keywords", None),
            creator=getattr(fpdf, "creator", None),
            producer=getattr(fpdf, "producer", None),
            creation_date=creation_date,
        )
        self._add_pdf_obj(info_obj)
        return info_obj

    def _add_encryption(self):
        if self.fpdf._security_handler:
            encryption_handler = self.fpdf._security_handler
            pdf_obj = encryption_handler.get_encryption_obj()
            self._add_pdf_obj(pdf_obj)
            return pdf_obj
        return None

    def _add_output_intents(self):
        """should be added in _add_catalog"""
        output_intents = self.fpdf.output_intents
        if not output_intents:
            return None
        for output_intent in output_intents:
            if output_intent.dest_output_profile:
                self._add_pdf_obj(output_intent.dest_output_profile)
        return PDFArray(output_intents)

    def _add_catalog(self):
        fpdf = self.fpdf
        catalog_obj = PDFCatalog(
            lang=getattr(fpdf, "lang", None),
            page_layout=fpdf.page_layout,
            page_mode=fpdf.page_mode,
            viewer_preferences=fpdf.viewer_preferences,
        )
        catalog_obj.output_intents = self._add_output_intents()

        self._add_pdf_obj(catalog_obj)
        return catalog_obj

    def _finalize_catalog(
        self,
        catalog_obj,
        pages_root_obj,
        first_page_obj,
        sig_annotation_obj,
        xmp_metadata_obj,
        struct_tree_root_obj,
        outline_dict_obj,
    ):
        fpdf = self.fpdf
        catalog_obj.pages = pages_root_obj
        catalog_obj.struct_tree_root = struct_tree_root_obj
        catalog_obj.outlines = outline_dict_obj
        catalog_obj.metadata = xmp_metadata_obj
        if sig_annotation_obj:
            flags = SignatureFlag.SIGNATURES_EXIST + SignatureFlag.APPEND_ONLY
            catalog_obj.acro_form = AcroForm(
                fields=PDFArray([sig_annotation_obj]), sig_flags=flags
            )
        if fpdf.zoom_mode in ZOOM_CONFIGS:
            zoom_config = [
                pdf_ref(first_page_obj.id),
                *ZOOM_CONFIGS[fpdf.zoom_mode],
            ]
        else:  # zoom_mode is a number, not one of the allowed strings:
            zoom_config = [
                pdf_ref(first_page_obj.id),
                "/XYZ",
                "null",
                "null",
                str(fpdf.zoom_mode / 100),
            ]
        catalog_obj.open_action = pdf_list(zoom_config)
        if struct_tree_root_obj:
            catalog_obj.mark_info = pdf_dict({"/Marked": "true"})
        if fpdf.embedded_files or fpdf.named_destinations:
            names_dict_entries = {}

            if fpdf.embedded_files:
                file_spec_names = [
                    f"{PDFString(embedded_file.basename()).serialize()} {embedded_file.file_spec().ref}"
                    for embedded_file in fpdf.embedded_files
                    if embedded_file.globally_enclosed
                ]
                names_dict_entries["/EmbeddedFiles"] = pdf_dict(
                    {"/Names": pdf_list(file_spec_names)}
                )
                global_file_specs = [
                    pdf_ref(ef.file_spec().id)
                    for ef in self.fpdf.embedded_files
                    if ef.globally_enclosed()
                ]
                if global_file_specs:
                    catalog_obj.a_f = pdf_list(global_file_specs)

            if fpdf.named_destinations:
                # Create a list of name/destination pairs for the Dests name tree
                dests_names = []
                for name, dest in fpdf.named_destinations.items():
                    # Check if this is a placeholder destination (page 0)
                    if dest.page_number == 0:
                        raise FPDFException(
                            f"Named destination '{name}' was referenced but never set with set_link(name=...)"
                        )

                    # Ensure the destination's page_ref is set
                    if not hasattr(dest, "page_ref") or not dest.page_ref:
                        page_index = dest.page_number - 1
                        if 0 <= page_index < len(fpdf.pages):
                            dest.page_ref = pdf_ref(fpdf.pages[dest.page_number].id)

                    # Add name and destination to the Dests list
                    dests_names.append(
                        f"{PDFString(name, encrypt=True).serialize(_security_handler=fpdf._security_handler, _obj_id=catalog_obj.id)} {dest.serialize()}"
                    )

                if dests_names:
                    names_dict_entries["/Dests"] = pdf_dict(
                        {"/Names": pdf_list(sorted(dests_names))}
                    )

            catalog_obj.names = pdf_dict(names_dict_entries)

        page_labels = [
            f"{i} {pdf_dict(page.get_page_label().serialize())}"
            for i, page in enumerate(self._iter_pages_in_order())
            if page.get_page_label()
        ]
        if page_labels and not fpdf.pages[1].get_page_label():
            # If page labels are used, an entry for sequence 0 is mandatory
            page_labels.insert(0, "0 <<>>")
        if page_labels:
            catalog_obj.page_labels = pdf_dict(
                {"/Nums": PDFArray(page_labels).serialize()}
            )

    @contextmanager
    def _trace_size(self, label):
        prev_size = len(self.buffer)
        yield
        self.sections_size_per_trace_label[label] += len(self.buffer) - prev_size

    def _log_final_sections_sizes(self):
        LOGGER.debug("Final size summary of the biggest document sections:")
        for label, section_size in self.sections_size_per_trace_label.items():
            LOGGER.debug("- %s: %s", label, _sizeof_fmt(section_size))


def stream_content_for_raster_image(
    info: RasterImageInfo,
    x,
    y,
    w,
    h,
    keep_aspect_ratio=False,
    scale=1,
    pdf_height_to_flip=None,
):
    if keep_aspect_ratio:
        x, y, w, h = info.scale_inside_box(x, y, w, h)
    if pdf_height_to_flip:
        stream_h = h
        stream_y = pdf_height_to_flip - h - y
    else:
        stream_h = -h
        stream_y = y + h
    return (
        f"q {w * scale:.2f} 0 0 {stream_h * scale:.2f}"
        f" {x * scale:.2f} {stream_y * scale:.2f} cm"
        f" /I{info['i']} Do Q"
    )


def _tt_font_widths(font):
    rangeid = 0
    range_ = {}
    range_interval = {}
    prevcid = -2
    prevwidth = -1
    interval = False

    # Glyphs sorted by mapped character id
    glyphs = dict(sorted(font.subset.items(), key=lambda item: item[1]))

    for glyph in glyphs:
        cid_mapped = glyphs[glyph]
        if cid_mapped == (prevcid + 1):
            if glyph.glyph_width == prevwidth:
                if glyph.glyph_width == range_[rangeid][0]:
                    range_.setdefault(rangeid, []).append(glyph.glyph_width)
                else:
                    range_[rangeid].pop()
                    # new range
                    rangeid = prevcid
                    range_[rangeid] = [prevwidth, glyph.glyph_width]
                interval = True
                range_interval[rangeid] = True
            else:
                if interval:
                    # new range
                    rangeid = cid_mapped
                    range_[rangeid] = [glyph.glyph_width]
                else:
                    range_[rangeid].append(glyph.glyph_width)
                interval = False
        else:
            rangeid = cid_mapped
            range_[rangeid] = [glyph.glyph_width]
            interval = False
        prevcid = cid_mapped
        prevwidth = glyph.glyph_width
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
    return f"[{''.join(w)}]"


def _dimensions_to_mediabox(dimensions):
    width_pt, height_pt = dimensions
    return f"[0 0 {width_pt:.2f} {height_pt:.2f}]"


def _sizeof_fmt(num, suffix="B"):
    # Recipe from: https://stackoverflow.com/a/1094933/636849
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024
    return f"{num:.1f}Yi{suffix}"


def soft_mask_path_to_xobject(path, resource_catalog: ResourceCatalog):
    """Converts a PaintedSoftMask into a PDF XObject Form suitable for use as a soft mask."""
    xobject = PDFContentStream(contents=path.render(resource_catalog))
    xobject._path = path
    xobject.type = Name("XObject")
    xobject.subtype = Name("Form")
    xobject.b_box = PDFArray(path.get_bounding_box())
    xobject.group = "<</S /Transparency /CS /DeviceGray /I true /K false>>"
    return xobject


def blend_group_to_xobject(group, resource_catalog: ResourceCatalog):
    """Convert a blend group into a Form XObject with an isolated transparency group."""
    stream = group.render(resource_catalog)
    xobject = PDFContentStream(contents=stream)
    xobject._blend_group = group
    xobject._registered = False
    xobject.type = Name("XObject")
    xobject.subtype = Name("Form")
    bbox = group.get_bounding_box()
    xobject.b_box = PDFArray(bbox)
    xobject.group = "<</S /Transparency /CS /DeviceRGB /I true>>"
    return xobject
