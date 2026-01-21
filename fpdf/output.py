"""
This module contains the serialization logic that produces a PDF document from a FPDF instance.
Most of the code in this module is used when FPDF.output() is called.

The contents of this module are internal to fpdf2, and not part of the public API.
They may change at any time without prior warning or any deprecation period,
in non-backward-compatible ways.
"""

# pyright: reportAttributeAccessIssue=false, reportUnknownMemberType=false, reportPrivateUsage=false

import logging
import re

# pylint: disable=protected-access
from abc import ABC, abstractmethod
from collections import OrderedDict, defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from html import escape as _html_escape
from io import BytesIO

from fontTools import subset as ftsubset

from .annotations import AnnotationDict, PDFAnnotation
from .drawing import ImageSoftMask, PaintSoftMask
from .drawing_primitives import Transform
from .enums import OutputIntentSubType, PageLabelStyle, PDFResourceType, SignatureFlag
from .errors import FPDFException
from .font_type_3 import Type3Font
from .fonts import CORE_FONTS, CoreFont, TTFFont
from .image_datastructures import ImageXObjectInfo, RasterImageInfo, scale_inside_box
from .line_break import TotalPagesSubstitutionFragment
from .outline import OutlineDictionary, OutlineItemDictionary, build_outline_objs
from .pattern import Gradient, MeshShading, Pattern, Shading
from .sign import Signature, sign_content
from .syntax import (
    DestinationXYZ,
    Name,
    PDFArray,
    PDFContentStream,
    PDFDate,
    PDFObject,
    PDFString,
    Raw,
    build_obj_dict,
    create_dictionary_string as pdf_dict,
    create_list_string as pdf_list,
    iobj_ref as pdf_ref,
)
from .util import int2roman, int_to_letters

try:
    from endesive import signer
except ImportError:
    signer = None

from typing import (
    TYPE_CHECKING,
    Any,
    ItemsView,
    Iterator,
    Literal,
    Optional,
    Sequence,
    Union,
    cast,
)

if TYPE_CHECKING:
    from .drawing import BlendGroup, GraphicsStyle
    from .encryption import EncryptionDictionary, StandardSecurityHandler
    from .enums import PageLayout, PageMode
    from .fonts import PDFFontDescriptor
    from .fpdf import FPDF
    from .prefs import ViewerPreferences
    from .transitions import Transition


LOGGER = logging.getLogger(__name__)

ZOOM_CONFIGS = {  # cf. section 8.2.1 "Destinations" of the 2006 PDF spec 1.7:
    "fullpage": ("/Fit",),
    "fullwidth": ("/FitH", "null"),
    "real": ("/XYZ", "null", "null", "1"),
}


class ContentWithoutID(ABC):

    @abstractmethod
    def serialize(
        self, _security_handler: Optional["StandardSecurityHandler"] = None
    ) -> str:
        raise NotImplementedError


class PDFHeader(ContentWithoutID):
    """
    Emit the PDF file header as required by ISO 32000-1, §7.5.2 “File header”.

    The header consists of:
      1) A line starting with the literal "%PDF-" followed by the file version
      2) If the file contains binary data an immediate second line that is a comment
         starting with "%" and containing at least four bytes with values ≥ 128 (non-ASCII).
         This helps file-transfer tools treat the content as binary rather than text.
    """

    def __init__(self, pdf_version: str) -> None:
        self.pdf_version = pdf_version

    def serialize(
        self, _security_handler: Optional["StandardSecurityHandler"] = None
    ) -> str:
        return f"%PDF-{self.pdf_version}\n%éëñ¿"


class PDFFont(PDFObject):
    def __init__(
        self,
        subtype: str,
        base_font: str,
        encoding: Optional[str] = None,
        d_w: Optional[float] = None,
        w: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.type = Name("Font")
        self.subtype = Name(subtype)
        self.base_font = Name(base_font)
        self.encoding = Name(encoding) if encoding else None
        self.d_w = d_w  # default glyph width
        self.w = w  # widths list
        self.descendant_fonts: Optional[PDFArray] = None
        self.to_unicode: Optional[PDFContentStream] = None
        self.c_i_d_system_info: Optional[CIDSystemInfo] = None
        self.font_descriptor: Optional["PDFFontDescriptor"] = None
        self.c_i_d_to_g_i_d_map: Optional[PDFContentStream] = None


class CIDSystemInfo(PDFObject):
    def __init__(self) -> None:
        super().__init__()
        self.registry = PDFString("Adobe", encrypt=True)
        self.ordering = PDFString("UCS", encrypt=True)
        self.supplement = 0


class PDFType3Font(PDFObject):
    def __init__(self, font3: "Type3Font") -> None:
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
        self.resources: Optional[str] = None
        self.to_unicode: Optional[str] = None

    @property
    def char_procs(self) -> str:
        return pdf_dict(
            {f"/{g.glyph_name}": f"{g.obj_id} 0 R" for g in self._font3.glyphs}
        )

    @property
    def encoding(self) -> str:
        return pdf_dict(
            {
                Name("/Type"): Name("/Encoding"),
                Name("/Differences"): self.differences_table(),
            }
        )

    @property
    def widths(self) -> str:
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
        self,
        img_objs_per_index: dict[int, "PDFXObject"],
        gfxstate_objs_per_name: dict[str, "PDFExtGState"],
        pattern_objs_per_name: dict[str, "Pattern"],
    ) -> None:
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

    def differences_table(self) -> str:
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
        title: Optional[str],
        subject: Optional[str],
        author: Optional[str],
        keywords: Optional[str],
        creator: Optional[str],
        producer: Optional[str],
        creation_date: PDFDate,
    ) -> None:
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
    def __init__(self, fields: PDFArray, sig_flags: int):
        self.fields = fields
        self.sig_flags = sig_flags

    def serialize(
        self,
        _security_handler: Optional["StandardSecurityHandler"] = None,
        _obj_id: Optional[int] = None,
    ) -> str:
        obj_dict = build_obj_dict(
            {key: getattr(self, key) for key in dir(self)},
            _security_handler=_security_handler,
            _obj_id=_obj_id,
        )
        return pdf_dict(obj_dict, field_join=" ")


class PDFCatalog(PDFObject):
    def __init__(
        self,
        lang: Optional[str] = None,
        page_layout: Optional["PageLayout"] = None,
        page_mode: Optional["PageMode"] = None,
        viewer_preferences: Optional["ViewerPreferences"] = None,
    ) -> None:
        super().__init__()
        self.type = Name("Catalog")
        self.lang = PDFString(lang) if lang else None
        self.page_layout = page_layout
        self.page_mode = page_mode
        self.viewer_preferences = viewer_preferences
        self.pages: Optional[PDFPagesRoot] = (
            None  # Required; shall be an indirect reference
        )
        self.acro_form: Optional[AcroForm] = None
        self.open_action: Optional[str] = None
        self.mark_info: Optional[str] = None
        self.metadata: Optional[PDFXmpMetadata] = None
        self.names: Optional[str] = None
        self.outlines: Optional[OutlineDictionary] = None
        self.output_intents: Optional[PDFArray] = None
        self.struct_tree_root: Optional[PDFObject] = None
        self.a_f: Optional[str] = None
        self.page_labels: Optional[str] = None


class PDFResources(PDFObject):
    def __init__(
        self,
        proc_set: Optional[str],
        font: Optional[str],
        x_object: Optional[str],
        ext_g_state: Optional[str],
        shading: Optional[str],
        pattern: Optional[str],
    ) -> None:
        super().__init__()
        self.proc_set = proc_set
        self.font = font
        self.x_object = x_object
        self.ext_g_state = ext_g_state
        self.shading = shading
        self.pattern = pattern


class PDFFontStream(PDFContentStream):
    def __init__(self, contents: bytes) -> None:
        super().__init__(contents=contents, compress=True)
        self.length1 = len(contents)


class PDFXmpMetadata(PDFContentStream):
    def __init__(self, contents: str) -> None:
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
        "image_mask",
    )

    def __init__(
        self,
        contents: bytes,
        subtype: str,
        width: float,
        height: float,
        color_space: PDFArray | Name | None,
        bits_per_component: int,
        img_filter: Optional[str] = None,
        decode: Optional[str] = None,
        decode_parms: Optional[str] = None,
        image_mask: bool = False,
    ) -> None:
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
        self.s_mask: Optional[PDFXObject] = None
        self.image_mask = True if image_mask else None


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
        contents: bytes,
        n: int,
        alternate: str,
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
        self,
        label_style: Optional[PageLabelStyle],
        label_prefix: Optional[str],
        label_start: Optional[int],
    ) -> None:
        self._style: Optional[PageLabelStyle] = label_style
        self._prefix: Optional[str] = label_prefix
        self.st: Optional[int] = label_start

    @property
    def s(self) -> Optional[Name]:
        return Name(self._style.value) if self._style else None

    @property
    def p(self) -> Optional[PDFString]:
        return PDFString(self._prefix) if self._prefix else None

    def __repr__(self) -> str:
        return f"PDFPageLabel({self._style}, {self._prefix}, {self.st})"

    def __str__(self) -> str:
        ret = self._prefix if self._prefix else ""
        if self._style:
            if self._style == PageLabelStyle.NUMBER:
                ret += str(self.st)
            elif self._style == PageLabelStyle.UPPER_ROMAN:
                ret += int2roman(self.st or 1)
            elif self._style == PageLabelStyle.LOWER_ROMAN:
                ret += int2roman(self.st or 1).lower()
            elif self._style == PageLabelStyle.UPPER_LETTER:
                start = (self.st or 1) - 1
                ret += int_to_letters(start)
            elif self._style == PageLabelStyle.LOWER_LETTER:
                start = (self.st or 1) - 1
                ret += int_to_letters(start).lower()
        return ret

    def serialize(self) -> dict[str, Any]:
        return build_obj_dict({key: getattr(self, key) for key in dir(self)})

    def get_style(self) -> Optional[PageLabelStyle]:
        return self._style

    def get_prefix(self) -> str:
        return self._prefix or ""

    def get_start(self) -> int:
        return self.st or 1


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
        duration: Optional[float],
        transition: Optional["Transition"],
        contents: bytearray | PDFContentStream,
        index: int,
    ):
        super().__init__()
        self.type = Name("Page")
        self.contents = contents
        self.dur = duration if duration else None
        self.trans = transition
        self.annots: Optional[PDFArray] = PDFArray()  # list of PDFAnnotation
        self.group: Optional[str] = None
        self.media_box: Optional[str] = None
        self.struct_parents: Optional[int] = None
        self.resources: Optional[PDFResources] = (
            None  # must always be set before calling .serialize()
        )
        self.parent: Optional[PDFPagesRoot] = (
            None  # must always be set before calling .serialize()
        )
        # Useful properties that will not be serialized in the final PDF document:
        self._index = index
        self._width_pt: Optional[float] = None
        self._height_pt: Optional[float] = None
        self._page_label: Optional[PDFPageLabel] = None
        self._text_substitution_fragments: list[TotalPagesSubstitutionFragment] = []

    def index(self) -> int:
        return self._index

    def set_index(self, i: int) -> None:
        self._index = i

    def dimensions(self) -> tuple[float, float]:
        "Return a pair (width, height) in the unit specified to FPDF constructor"
        if self._width_pt is None or self._height_pt is None:
            raise ValueError("Page dimensions are null")
        return self._width_pt, self._height_pt

    def set_dimensions(self, width_pt: float, height_pt: float) -> None:
        "Accepts a pair (width, height) in the unit specified to FPDF constructor"
        self._width_pt, self._height_pt = width_pt, height_pt

    def set_page_label(
        self,
        previous_page_label: Optional[PDFPageLabel],
        page_label: Optional[PDFPageLabel],
    ) -> None:
        if (
            previous_page_label
            and page_label
            and page_label.get_style() == previous_page_label.get_style()
            and page_label.get_prefix() == previous_page_label.get_prefix()
            and not page_label.st
        ):
            page_label.st = previous_page_label.get_start() + 1

        if page_label:
            if page_label.st is None or page_label.st == 0:
                page_label.st = 1

        if previous_page_label and not page_label:
            page_label = PDFPageLabel(
                previous_page_label.get_style(),
                previous_page_label.get_prefix(),
                previous_page_label.get_start() + 1,
            )

        self._page_label = page_label

    def get_page_label(self) -> Optional[PDFPageLabel]:
        return self._page_label

    def get_label(self) -> str:
        return str(self.index()) if not self._page_label else str(self._page_label)

    def get_text_substitutions(self) -> Sequence[TotalPagesSubstitutionFragment]:
        return self._text_substitution_fragments

    def add_text_substitution(self, fragment: TotalPagesSubstitutionFragment) -> None:
        self._text_substitution_fragments.append(fragment)

    def add_annotation(self, annotation: AnnotationDict | PDFAnnotation) -> None:
        if self.annots is None:
            self.annots = PDFArray()
        self.annots.append(annotation)


class PDFPagesRoot(PDFObject):
    def __init__(self, count: int, media_box: str) -> None:
        super().__init__()
        self.type = Name("Pages")
        self.count = count
        self.media_box = media_box
        self.kids: Optional[PDFArray] = (
            None  # must always be set before calling .serialize()
        )


class PDFExtGState(PDFObject):
    def __init__(self, dict_as_str: str) -> None:
        super().__init__()
        self._dict_as_str = dict_as_str

    # method override
    def serialize(
        self,
        obj_dict: Optional[dict[str, Any]] = None,
        _security_handler: Optional["StandardSecurityHandler"] = None,
    ) -> str:
        return f"{self.id} 0 obj\n{self._dict_as_str}\nendobj"


class PDFXrefAndTrailer(ContentWithoutID):
    "Cross-reference table & file trailer"

    def __init__(self, output_builder: "OutputProducer") -> None:
        self.output_builder = output_builder
        self.count = output_builder.obj_id + 1
        # Must be set before the call to serialize():
        self.catalog_obj: Optional[PDFCatalog] = None
        self.info_obj: Optional[PDFInfo] = None
        self.encryption_obj: Optional["EncryptionDictionary"] = None

    def serialize(
        self, _security_handler: Optional["StandardSecurityHandler"] = None
    ) -> str:
        if self.catalog_obj is None:
            raise FPDFException("Invalid state for XREF production.")
        builder = self.output_builder
        startxref = str(len(builder.buffer))
        out: list[str] = []
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
            assert fpdf._security_handler is not None
            file_id: Optional[str | Literal[-1]] = fpdf._security_handler.file_id
        else:
            file_id = fpdf.file_id()
            if file_id == -1:
                file_id = fpdf._default_file_id(builder.buffer)
        if file_id is not None:
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
        output_condition_identifier: Optional[str],
        output_condition: Optional[str] = None,
        registry_name: Optional[str] = None,
        dest_output_profile: Optional[PDFICCProfile] = None,
        info: Optional[str] = None,
    ) -> None:
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

    def serialize(
        self,
        _security_handler: Optional["StandardSecurityHandler"] = None,
        _obj_id: Optional[int] = None,
    ) -> str:
        obj_dict = build_obj_dict(
            {key: getattr(self, key) for key in dir(self)},
            _security_handler=_security_handler,
            _obj_id=_obj_id,
        )
        return pdf_dict(obj_dict)


ResourceTypes = Union[str, int, Name, "Gradient", "Pattern", "Shading", "MeshShading"]


class ResourceCatalog:
    "Manage the indexing of resources and association to the pages they are used"

    GS_REGEX = re.compile(r"/(GS\d+) gs")
    IMG_REGEX = re.compile(r"/I(\d+) Do")
    PATTERN_FILL_REGEX = re.compile(r"/(P\d+)\s+scn")
    PATTERN_STROKE_REGEX = re.compile(r"/(P\d+)\s+SCN")
    FONT_REGEX = re.compile(r"/F(\d+)\s+[-+]?\d+(?:\.\d+)?\s+Tf")

    def __init__(self) -> None:
        self.resources: dict[PDFResourceType, dict[ResourceTypes, str]] = defaultdict(
            dict
        )
        self.resources_per_page: dict[
            tuple[int, PDFResourceType], set[ResourceTypes]
        ] = defaultdict(set)
        self.graphics_styles: dict[str, Name] = OrderedDict()
        self.soft_mask_xobjects: list[PDFContentStream] = []
        self.form_xobjects: list[tuple[int, PDFContentStream]] = []
        self.last_reserved_object_id: int = 0
        self.font_registry: dict[str, CoreFont | TTFFont] = {}
        self.next_xobject_index: int = 1

    def add(
        self,
        resource_type: PDFResourceType,
        resource: ResourceTypes,
        page_number: Optional[int],
    ) -> Optional[str]:
        if resource_type in (PDFResourceType.PATTERN, PDFResourceType.SHADING):
            registry = self.resources[resource_type]
            prefix = self._get_prefix(resource_type)

            if resource not in registry:
                registry[resource] = f"{prefix}{len(registry) + 1}"
            if page_number is not None:
                self.resources_per_page[(page_number, resource_type)].add(
                    registry[resource]
                )
            return str(registry[resource])

        if (
            resource_type == PDFResourceType.X_OBJECT
            and isinstance(resource, int)
            and resource >= self.next_xobject_index
        ):
            self.next_xobject_index = resource + 1

        if TYPE_CHECKING:
            assert page_number is not None
        self.resources_per_page[(page_number, resource_type)].add(resource)
        return None

    def register_graphics_style(self, style: "GraphicsStyle") -> Optional[Name]:
        """
        Graphics style can be added without associating to a page number right away,
        like when rendering a svg image.
        The method that adds image to the page will call the add method for the page association.
        """
        style_dict: Optional[Raw] = style.serialize()
        if style_dict is None:  # empty style does not need an entry
            return None
        style_str = str(style_dict)

        if style_str not in self.graphics_styles:
            name = Name(
                f"{self._get_prefix(PDFResourceType.EXT_G_STATE)}{len(self.graphics_styles)}"
            )
            self.graphics_styles[style_str] = name

        return self.graphics_styles[style_str]

    def register_soft_mask(self, soft_mask: PaintSoftMask | ImageSoftMask) -> int:
        """Register a soft mask xobject and return its object id"""
        self.last_reserved_object_id += 1
        xobject = soft_mask_path_to_xobject(soft_mask, self)
        xobject.id = self.last_reserved_object_id
        self.soft_mask_xobjects.append(xobject)
        return xobject.id

    def register_blend_form(self, blend_group: "BlendGroup") -> int:
        """Register a blend group Form XObject and return its resource index."""
        xobject = blend_group_to_xobject(blend_group, self)
        index = self.next_xobject_index
        self.next_xobject_index += 1
        self.form_xobjects.append((index, xobject))
        return index

    def scan_stream(self, rendered: str) -> set[tuple[PDFResourceType, str]]:
        """Parse a content stream and return discovered resources"""
        found: set[tuple[PDFResourceType, str]] = set()

        for m in self.GS_REGEX.finditer(rendered):
            found.add((PDFResourceType.EXT_G_STATE, m.group(1)))

        for m in self.IMG_REGEX.finditer(rendered):
            found.add((PDFResourceType.X_OBJECT, m.group(1)))

        for m in self.PATTERN_FILL_REGEX.finditer(rendered):
            found.add((PDFResourceType.PATTERN, m.group(1)))

        for m in self.PATTERN_STROKE_REGEX.finditer(rendered):
            found.add((PDFResourceType.PATTERN, m.group(1)))

        for m in self.FONT_REGEX.finditer(rendered):
            found.add((PDFResourceType.FONT, m.group(1)))

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

    def get_items(
        self, resource_type: PDFResourceType
    ) -> ItemsView[ResourceTypes, str]:
        return self.resources[resource_type].items()

    def get_resources_per_page(
        self, page_number: int, resource_type: PDFResourceType
    ) -> set[ResourceTypes]:
        return self.resources_per_page[(page_number, resource_type)]

    def get_used_resources(self, resource_type: PDFResourceType) -> set[ResourceTypes]:
        unique: set[ResourceTypes] = set()
        for (_, rtype), resource in self.resources_per_page.items():
            if rtype == resource_type:
                unique.update(resource)
        return unique

    @classmethod
    def _get_prefix(cls, resource_type: PDFResourceType) -> str:
        if resource_type == PDFResourceType.EXT_G_STATE:
            return "GS"
        if resource_type == PDFResourceType.PATTERN:
            return "P"
        if resource_type == PDFResourceType.SHADING:
            return "Sh"
        raise ValueError(f"No prefix for resource type {resource_type}")

    def get_font_from_family(
        self, font_family: str, font_style: str = ""
    ) -> CoreFont | TTFFont:
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

    def __init__(self, fpdf: "FPDF") -> None:
        self.fpdf = fpdf
        self.pdf_objs: list[PDFObject | ContentWithoutID] = []
        self.iccp_i_to_pdf_i: dict[int, int] = {}
        self.obj_id: int = (
            fpdf._resource_catalog.last_reserved_object_id
        )  # current PDF object number
        # array of PDF object offsets in self.buffer, used to build the xref table:
        self.offsets: dict[int, int] = {}
        self.trace_labels_per_obj_id: dict[int, str] = {}
        self.sections_size_per_trace_label: dict[str, int] = defaultdict(int)
        self.buffer: bytearray = bytearray()  # resulting output buffer

    def bufferize(self) -> bytearray:
        """
        This method alters the target FPDF instance
        by assigning IDs to all PDF objects,
        plus a few other properties on PDFPage instances
        """
        fpdf = self.fpdf

        # 1. setup - Insert all PDF objects
        #    and assign unique consecutive numeric IDs to all of them

        if fpdf._security_handler is not None:
            # get the file_id and generate passwords needed to encrypt streams and strings
            file_id: Optional[str | Literal[-1]] = fpdf.file_id()
            if file_id == -1:
                # no custom file id - use default file id so encryption passwords can be generated
                file_id = fpdf._default_file_id(bytearray(0x00))
            fpdf._security_handler.generate_passwords(str(file_id))

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
        dests: list[DestinationXYZ] = []
        for page_obj in page_objs:
            page_obj.parent = pages_root_obj
            assert isinstance(page_obj.annots, PDFArray)
            for annot in page_obj.annots:
                page_dests: list[DestinationXYZ] = []
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
            if outline_item.dest is not None:
                dests.append(outline_item.dest)
        # Assigning the .page_ref property of all Destination objects:
        for dest in dests:
            dest.page_ref = pdf_ref(
                page_objs[
                    dest.page_number - 1
                ].id  # pyright: ignore[reportUnknownArgumentType]
            )
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
                signer,  # pyright: ignore[reportArgumentType]
                self.buffer,
                fpdf._sign_key,
                fpdf._sign_cert,
                fpdf._sign_extra_certs,
                fpdf._sign_hashalgo,
                fpdf._sign_time,
            )
        return self.buffer

    def _out(self, data: bytes | bytearray | str) -> None:
        "Append data to the buffer"
        if not isinstance(data, bytes):
            if not isinstance(data, str):
                data = str(data)
            data = data.encode("latin1")
        self.buffer += data + b"\n"

    def _add_pdf_obj(
        self, pdf_obj: PDFObject, trace_label: Optional[str] = None
    ) -> int:
        self.obj_id += 1
        pdf_obj.id = self.obj_id
        self.pdf_objs.append(pdf_obj)
        if trace_label:
            self.trace_labels_per_obj_id[self.obj_id] = trace_label
        return self.obj_id

    def _add_pages_root(self) -> PDFPagesRoot:
        fpdf = self.fpdf
        pages_root_obj = PDFPagesRoot(
            count=fpdf.pages_count,
            media_box=_dimensions_to_mediabox(fpdf.default_page_dimensions),
        )
        self._add_pdf_obj(pages_root_obj)
        return pages_root_obj

    def _iter_pages_in_order(self) -> Iterator[PDFPage]:
        for page_index in range(1, self.fpdf.pages_count + 1):
            page_obj = self.fpdf.pages[page_index]
            # Defensive check:
            assert (
                page_obj.index() == page_index
            ), f"{page_obj.index()=} != {page_index=}"
            yield page_obj

    def _add_pages(self, _slice: slice = slice(0, None)) -> list[PDFPage]:
        fpdf = self.fpdf
        page_objs: list[PDFPage] = []
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
            assert isinstance(page_obj.contents, bytearray)
            cs_obj = PDFContentStream(
                contents=page_obj.contents, compress=fpdf.compress
            )
            self._add_pdf_obj(cs_obj, "pages")
            page_obj.contents = cs_obj

        return page_objs

    def _add_annotations_as_objects(self) -> Optional[PDFAnnotation]:
        sig_annotation_obj = None
        for page_obj in self.fpdf.pages.values():
            assert isinstance(page_obj.annots, PDFArray)
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
        self,
        image_objects_per_index: dict[int, PDFXObject],
        gfxstate_objs_per_name: dict[str, PDFExtGState],
        pattern_objs_per_name: dict[str, "Pattern"],
    ) -> dict[int, PDFFont | PDFType3Font]:
        font_objs_per_index: dict[int, PDFFont | PDFType3Font] = {}
        for font in sorted(self.fpdf.fonts.values(), key=lambda font: font.i):

            # type 3 font
            if isinstance(font, TTFFont) and font.color_font:
                if font.subset._next > 0xFF:
                    raise FPDFException(
                        "Type 3 fonts with color glyphs are not supported is more than 255 glyphs are rendered. "
                        "set FPDF.render_color_fonts=False or use less color glyphs."
                    )
                for color_glyph in font.color_font.glyphs:
                    color_glyph.obj_id = self._add_pdf_obj(
                        PDFContentStream(
                            contents=color_glyph.glyph.encode("latin-1"),
                            compress=self.fpdf.compress,
                        ),
                        "fonts",
                    )
                bfChar: list[str] = []

                for glyph, code_mapped in font.subset.items():
                    if (
                        glyph is None
                        or not isinstance(glyph.unicode, tuple)
                        or len(glyph.unicode) == 0
                    ):
                        continue
                    bfChar.append(
                        f'<{code_mapped:02X}> <{"".join(chr(code).encode("utf-16-be").hex().upper() for code in glyph.unicode)}>\n'
                    )

                to_unicode_obj = PDFContentStream(
                    (
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
                    ).encode("latin-1")
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
            if isinstance(font, CoreFont):
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
            elif isinstance(font, TTFFont):
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

                code_to_glyph: dict[int, int] = {
                    char_id: font.ttfont.getGlyphID(glyph.glyph_name)
                    for glyph, char_id in font.subset.items()
                    if glyph is not None
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

                # A CIDFont whose glyph descriptions are based on TrueType or CFF technology
                is_cff_cid = font.is_cff and font.is_cid_keyed
                code_to_cid: Optional[dict[int, int]] = None
                cid_widths: Optional[dict[int, int]] = None
                if is_cff_cid:
                    code_to_cid = {}
                    cid_widths = {}
                    for glyph, code_mapped in font.subset.items():
                        if glyph is None:
                            continue
                        if (
                            glyph.glyph_name.startswith("cid")
                            and glyph.glyph_name[3:].isdigit()
                        ):
                            cid = int(glyph.glyph_name[3:])
                        else:
                            cid = glyph.glyph_id
                        if cid > 0xFFFF:
                            LOGGER.warning(
                                "Glyph CID %s exceeds 0xFFFF and cannot be encoded in a 2-byte CID font: %s",
                                cid,
                                font.fontkey,
                            )
                            continue
                        code_to_cid[code_mapped] = cid
                        cid_widths[cid] = glyph.glyph_width
                cid_font_obj = PDFFont(
                    subtype="CIDFontType0" if is_cff_cid else "CIDFontType2",
                    base_font=fontname,
                    d_w=font.desc.missing_width,
                    w=(
                        _cid_font_widths(cid_widths)
                        if is_cff_cid and cid_widths
                        else _tt_font_widths(font)
                    ),
                )
                self._add_pdf_obj(cid_font_obj, "fonts")
                composite_font_obj.descendant_fonts = PDFArray([cid_font_obj])

                # bfChar
                # This table informs the PDF reader about the unicode
                # character that each used 16-bit code belongs to. It
                # allows searching the file and copying text from it.
                bfChar = []

                def format_code(unicode: int) -> str:
                    if unicode > 0xFFFF:
                        # Calculate surrogate pair
                        code_high = 0xD800 | (unicode - 0x10000) >> 10
                        code_low = 0xDC00 | (unicode & 0x3FF)
                        return f"{code_high:04X}{code_low:04X}"
                    return f"{unicode:04X}"

                for glyph, code_mapped in font.subset.items():
                    if (
                        glyph is None
                        or not isinstance(glyph.unicode, tuple)
                        or len(glyph.unicode) == 0
                    ):
                        continue
                    bfChar.append(
                        f'<{code_mapped:04X}> <{"".join(format_code(code) for code in glyph.unicode)}>\n'
                    )

                to_unicode_obj = PDFContentStream(
                    (
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
                    ).encode("latin-1")
                )
                self._add_pdf_obj(to_unicode_obj, "fonts")
                composite_font_obj.to_unicode = to_unicode_obj

                if is_cff_cid and code_to_cid:
                    registry = "Adobe"
                    ordering = "Identity"
                    supplement = 0
                    if font.cff_ros:
                        registry, ordering, supplement = font.cff_ros
                    cid_mapping = [
                        f"<{code:04X}> {cid}\n"
                        for code, cid in sorted(code_to_cid.items())
                    ]
                    encoding_cmap_obj = PDFContentStream(
                        (
                            "/CIDInit /ProcSet findresource begin\n"
                            "12 dict begin\n"
                            "begincmap\n"
                            "/CIDSystemInfo\n"
                            f"<</Registry ({registry})\n"
                            f"/Ordering ({ordering})\n"
                            f"/Supplement {supplement}\n"
                            ">> def\n"
                            f"/CMapName /{registry}-{ordering}-UCS def\n"
                            "/CMapType 2 def\n"
                            "1 begincodespacerange\n"
                            "<0000> <FFFF>\n"
                            "endcodespacerange\n"
                            f"{len(cid_mapping)} begincidchar\n"
                            f"{''.join(cid_mapping)}"
                            "endcidchar\n"
                            "endcmap\n"
                            "CMapName currentdict /CMap defineresource pop\n"
                            "end\n"
                            "end"
                        ).encode("latin-1")
                    )
                    encoding_cmap_obj.type = Name("CMap")  # type: ignore[attr-defined]
                    encoding_cmap_obj.c_map_name = Name(  # type: ignore[attr-defined]
                        f"{registry}-{ordering}-UCS"
                    )
                    encoding_cmap_obj.c_i_d_system_info = Raw(  # type: ignore[attr-defined]
                        f"<< /Registry ({registry}) /Ordering ({ordering}) /Supplement {supplement} >>"
                    )
                    self._add_pdf_obj(encoding_cmap_obj, "fonts")
                    composite_font_obj.encoding = encoding_cmap_obj  # type: ignore[assignment]

                cid_system_info_obj = CIDSystemInfo()
                if is_cff_cid and font.cff_ros:
                    registry, ordering, supplement = font.cff_ros
                    cid_system_info_obj.registry = PDFString(registry, encrypt=True)
                    cid_system_info_obj.ordering = PDFString(ordering, encrypt=True)
                    cid_system_info_obj.supplement = supplement
                self._add_pdf_obj(cid_system_info_obj, "fonts")
                cid_font_obj.c_i_d_system_info = cid_system_info_obj

                font_descriptor_obj = font.desc
                font_descriptor_obj.font_name = Name(fontname)
                self._add_pdf_obj(font_descriptor_obj, "fonts")
                cid_font_obj.font_descriptor = font_descriptor_obj

                if not is_cff_cid:
                    # Embed CIDToGIDMap
                    # A specification of the mapping from CIDs to glyph indices
                    cid_to_gid_list = ["\x00"] * 256 * 256 * 2
                    for cc, glyph_i in code_to_glyph.items():
                        cid_to_gid_list[cc * 2] = chr(glyph_i >> 8)
                        cid_to_gid_list[cc * 2 + 1] = chr(glyph_i & 0xFF)
                    cid_to_gid_map = "".join(cid_to_gid_list)

                    # manage binary data as latin1 until PEP461-like function is implemented
                    cid_to_gid_map_obj = PDFContentStream(
                        contents=cid_to_gid_map.encode("latin1"), compress=True
                    )
                    self._add_pdf_obj(cid_to_gid_map_obj, "fonts")
                    cid_font_obj.c_i_d_to_g_i_d_map = cid_to_gid_map_obj

                font_file_cs_obj = PDFFontStream(contents=ttfontstream)
                if is_cff_cid:
                    font_file_cs_obj.subtype = Name("CIDFontType0C")  # type: ignore[attr-defined]
                self._add_pdf_obj(font_file_cs_obj, "fonts")
                if is_cff_cid:
                    font_descriptor_obj.font_file3 = font_file_cs_obj  # type: ignore[attr-defined]
                else:
                    font_descriptor_obj.font_file2 = font_file_cs_obj  # type: ignore[attr-defined]

                font.subset.pick.cache_clear()
                font.subset.get_glyph.cache_clear()
                font.close()

        return font_objs_per_index

    def _add_images(self) -> dict[int, PDFXObject]:
        img_objs_per_index: dict[int, PDFXObject] = {}
        for raster_img in sorted(
            self.fpdf.image_cache.images.values(),
            key=lambda img: img["i"],
        ):
            if raster_img["usages"] > 0:
                img_objs_per_index[raster_img["i"]] = self._add_image(
                    cast(ImageXObjectInfo, raster_img)
                )
        return img_objs_per_index

    def _ensure_iccp(self, img_info: RasterImageInfo) -> int:
        """
        Returns the PDF object of the ICC profile indexed iccp_i in the FPDF object.
        Adds it if not present.
        """
        iccp_i = img_info.get("iccp_i")
        assert iccp_i is not None
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
            contents=iccp_content,
            n=img_info["dpn"],
            alternate=img_info["cs"],
        )
        iccp_pdf_i = self._add_pdf_obj(iccp_obj, "iccp")
        self.iccp_i_to_pdf_i[iccp_i] = iccp_pdf_i
        return iccp_pdf_i

    def _add_image(self, info: ImageXObjectInfo) -> PDFXObject:
        image_mask = bool(info.get("image_mask"))
        color_space: Name | PDFArray | None = None if image_mask else Name(info["cs"])
        decode = None
        iccp_i = None if image_mask else info.get("iccp_i")
        if color_space == "Indexed":
            color_space = PDFArray(
                ["/Indexed", "/DeviceRGB", f"{len(info['pal']) // 3 - 1}"]  # type: ignore[arg-type]
            )
        elif iccp_i is not None:
            iccp_pdf_i = self._ensure_iccp(cast(RasterImageInfo, info))
            color_space = PDFArray(["/ICCBased", str(iccp_pdf_i), str("0"), "R"])
        elif color_space == "DeviceCMYK":
            if info.get("inverted") is True:
                decode = "[1 0 1 0 1 0 1 0]"
        if "decode" in info:
            decode = info["decode"]

        decode_parms = f"<<{info['dp']} /BitsPerComponent {info['bpc']}>>"
        img_obj = PDFXObject(
            subtype="Image",
            contents=info["data"],
            width=int(info["w"]),
            height=int(info["h"]),
            color_space=color_space,
            bits_per_component=info["bpc"],
            img_filter=info["f"],
            decode=decode,
            decode_parms=decode_parms,
            image_mask=image_mask,
        )
        info["obj_id"] = self._add_pdf_obj(img_obj, "images")

        # Soft mask
        if self.fpdf.allow_images_transparency and "smask" in info and not image_mask:
            dp = f"/Predictor 15 /Colors 1 /Columns {info['w']}"
            smask = info["smask"]
            assert smask is not None
            img_obj.s_mask = self._add_image(
                {
                    "w": info["w"],
                    "h": info["h"],
                    "cs": "DeviceGray",
                    "bpc": 8,
                    "f": info["f"],
                    "dp": dp,
                    "data": smask,
                }
            )

        # Palette
        if isinstance(color_space, PDFArray) and "/Indexed" in color_space:
            assert isinstance(img_obj.color_space, PDFArray)
            pal = info.get("pal")
            assert pal is not None
            pal_cs_obj = PDFContentStream(contents=pal, compress=self.fpdf.compress)
            self._add_pdf_obj(pal_cs_obj, "images")
            img_obj.color_space.append(pdf_ref(pal_cs_obj.id))

        return img_obj

    def _add_gfxstates(self) -> dict[str, PDFExtGState]:
        gfxstate_objs_per_name: dict[str, PDFExtGState] = OrderedDict()
        for state_dict, name in self.fpdf._resource_catalog.graphics_styles.items():
            gfxstate_obj = PDFExtGState(state_dict)
            self._add_pdf_obj(gfxstate_obj, "gfxstate")
            gfxstate_objs_per_name[name] = gfxstate_obj
        return gfxstate_objs_per_name

    def _add_soft_masks(
        self,
        gfxstate_objs_per_name: dict[str, PDFExtGState],
        pattern_objs_per_name: dict[str, "Pattern"],
        img_objs_per_index: dict[int, PDFXObject],
    ) -> None:
        """Append soft-mask Form XObjects after patterns exist so we can resolve /Pattern ids."""
        for soft_mask in self.fpdf._resource_catalog.soft_mask_xobjects:
            soft_mask.resources = soft_mask._path.get_resource_dictionary(  # type: ignore[attr-defined]
                gfxstate_objs_per_name, pattern_objs_per_name, img_objs_per_index
            )
            self.pdf_objs.append(soft_mask)

    def _register_form_xobject_placeholders(
        self, img_objs_per_index: dict[int, PDFXObject]
    ) -> None:
        """Ensure isolated blend forms are part of the XObject set before other resources rely on them."""
        for index, xobject in self.fpdf._resource_catalog.form_xobjects:
            if not getattr(xobject, "_registered", False):
                self._add_pdf_obj(xobject, "images")
                xobject._registered = True  # type: ignore[attr-defined]
            img_objs_per_index.setdefault(index, xobject)  # type: ignore[arg-type]

    def _finalize_form_xobjects(
        self,
        img_objs_per_index: dict[int, PDFXObject],
        gfxstate_objs_per_name: dict[str, PDFExtGState],
        pattern_objs_per_name: dict[str, Pattern],
        shading_objs_per_name: dict[str, Shading | MeshShading],
        font_objs_per_index: dict[int, PDFFont | PDFType3Font],
    ) -> None:
        """Populate resource dictionaries for isolated blend Form XObjects."""
        for _, xobject in self.fpdf._resource_catalog.form_xobjects:
            blend_group = getattr(xobject, "_blend_group", None)
            if blend_group is not None:
                xobject.resources = blend_group.get_resource_dictionary(  # type: ignore[attr-defined]
                    gfxstate_objs_per_name,
                    pattern_objs_per_name,
                    shading_objs_per_name,
                    font_objs_per_index,
                    img_objs_per_index,
                )

    def _add_shadings(self) -> dict[str, Shading | MeshShading]:
        shading_objs_per_name: dict[str, Shading | MeshShading] = OrderedDict()
        for shading, name in self.fpdf._resource_catalog.get_items(
            PDFResourceType.SHADING
        ):
            assert isinstance(shading, (Gradient, Shading, MeshShading))
            for function in shading.get_functions():
                self._add_pdf_obj(function, "function")
            shading_obj: Shading | MeshShading = shading.get_shading_object()
            self._add_pdf_obj(shading_obj, "shading")
            shading_objs_per_name[name] = shading_obj
        return shading_objs_per_name

    def _add_patterns(self) -> dict[str, Pattern]:
        pattern_objs_per_name: dict[str, Pattern] = OrderedDict()
        for pattern, name in self.fpdf._resource_catalog.get_items(
            PDFResourceType.PATTERN
        ):
            assert isinstance(pattern, Pattern)
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

    def _insert_resources(self, page_objs: list[PDFPage]) -> None:
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
        self._add_soft_masks(
            gfxstate_objs_per_name, pattern_objs_per_name, img_objs_per_index
        )
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
                    int(font_id): font_objs_per_index[int(font_id)]  # type: ignore[arg-type]
                    for font_id in self.fpdf._resource_catalog.get_resources_per_page(
                        page_number, PDFResourceType.FONT
                    )
                }
                page_img_objs_per_index = {
                    int(img_id): img_objs_per_index[int(img_id)]  # type: ignore[arg-type]
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
                    str(shading_name): shading_objs_per_name[str(shading_name)]
                    for shading_name in self.fpdf._resource_catalog.get_resources_per_page(
                        page_number, PDFResourceType.SHADING
                    )
                }
                page_pattern_objs_per_name = {
                    str(pattern_name): pattern_objs_per_name[str(pattern_name)]
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
        font_objs_per_index: dict[int, PDFFont | PDFType3Font],
        img_objs_per_index: dict[int, PDFXObject],
        gfxstate_objs_per_name: dict[str, PDFExtGState],
        shading_objs_per_name: dict[str, Shading | MeshShading],
        pattern_objs_per_name: dict[str, Pattern],
    ) -> PDFResources:
        # From section 10.1, "Procedure sets", of PDF 1.7 spec:
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

    def _add_structure_tree(self) -> Optional[PDFObject]:
        "Builds a Structure Hierarchy, including image alternate descriptions"
        if self.fpdf.struct_builder.empty():
            return None
        struct_tree_root_obj = None
        for pdf_obj in self.fpdf.struct_builder:
            if struct_tree_root_obj is None:
                struct_tree_root_obj = pdf_obj
            self._add_pdf_obj(pdf_obj, "structure_tree")
        return struct_tree_root_obj

    def _add_document_outline(
        self,
    ) -> tuple[Optional[OutlineDictionary], Sequence[OutlineItemDictionary]]:
        if not self.fpdf._outline:
            return None, ()
        outline_dict_obj: Optional[OutlineDictionary] = None
        outline_items: list[OutlineItemDictionary] = []
        for pdf_obj in build_outline_objs(self.fpdf._outline):
            if isinstance(pdf_obj, OutlineDictionary):
                outline_dict_obj = pdf_obj
            else:
                outline_items.append(pdf_obj)
            self._add_pdf_obj(pdf_obj, "document_outline")
        return outline_dict_obj, outline_items

    def _add_xmp_metadata(self) -> Optional[PDFXmpMetadata]:
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
        def esc(s: str) -> str:
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

    def _add_info(self) -> PDFInfo:
        fpdf = self.fpdf
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

    def _add_encryption(self) -> Optional["EncryptionDictionary"]:
        if self.fpdf._security_handler:
            encryption_handler = self.fpdf._security_handler
            pdf_obj = encryption_handler.get_encryption_obj()
            self._add_pdf_obj(pdf_obj)
            return pdf_obj
        return None

    def _add_output_intents(self) -> Optional[PDFArray]:
        """should be added in _add_catalog"""
        output_intents = self.fpdf.output_intents
        if not output_intents:
            return None
        for output_intent in output_intents:
            if output_intent.dest_output_profile:
                self._add_pdf_obj(output_intent.dest_output_profile)
        return PDFArray(output_intents)

    def _add_catalog(self) -> PDFCatalog:
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
        catalog_obj: PDFCatalog,
        pages_root_obj: PDFPagesRoot,
        first_page_obj: PDFPage,
        sig_annotation_obj: Optional[PDFAnnotation],
        xmp_metadata_obj: Optional[PDFXmpMetadata],
        struct_tree_root_obj: Optional[PDFObject],
        outline_dict_obj: Optional[OutlineDictionary],
    ) -> None:
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
                *ZOOM_CONFIGS[fpdf.zoom_mode],  # type: ignore[index]
            ]
        else:  # zoom_mode is a number, not one of the allowed strings:
            zoom_config = [
                pdf_ref(first_page_obj.id),
                "/XYZ",
                "null",
                "null",
                str(cast(float, fpdf.zoom_mode) / 100),
            ]
        catalog_obj.open_action = pdf_list(zoom_config)
        if struct_tree_root_obj:
            catalog_obj.mark_info = pdf_dict({"/Marked": "true"})
        if fpdf.embedded_files or fpdf.named_destinations:
            names_dict_entries: dict[str, str] = {}

            if fpdf.embedded_files:
                file_spec_names = [
                    f"{PDFString(embedded_file.basename()).serialize()} {embedded_file.file_spec().ref}"
                    for embedded_file in fpdf.embedded_files
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
                dests_names: list[str] = []
                for name, dest in fpdf.named_destinations.items():
                    # Check if this is a placeholder destination (page 0)
                    if dest.page_number == 0:
                        raise FPDFException(
                            f"Named destination '{name}' was referenced but never set with set_link(name=...)"
                        )

                    # Ensure the destination's page_ref is set
                    if not hasattr(dest, "page_ref") or not dest.page_ref:
                        assert dest.page_number is not None
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
            f"{i} {pdf_dict(label.serialize())}"
            for i, page in enumerate(self._iter_pages_in_order())
            if (label := page.get_page_label()) is not None
        ]
        if page_labels and not fpdf.pages[1].get_page_label():
            # If page labels are used, an entry for sequence 0 is mandatory
            page_labels.insert(0, "0 <<>>")
        if page_labels:
            catalog_obj.page_labels = pdf_dict(
                {"/Nums": PDFArray(page_labels).serialize()}
            )

    @contextmanager
    def _trace_size(self, label: str) -> Iterator[None]:
        prev_size = len(self.buffer)
        yield
        self.sections_size_per_trace_label[label] += len(self.buffer) - prev_size

    def _log_final_sections_sizes(self) -> None:
        LOGGER.debug("Final size summary of the biggest document sections:")
        for label, section_size in self.sections_size_per_trace_label.items():
            LOGGER.debug("- %s: %s", label, _sizeof_fmt(section_size))


def stream_content_for_raster_image(
    info: RasterImageInfo,
    x: float,
    y: float,
    w: float,
    h: float,
    keep_aspect_ratio: bool = False,
    scale: float = 1,
    pdf_height_to_flip: Optional[float] = None,
) -> str:
    if keep_aspect_ratio:
        x, y, w, h = scale_inside_box(info, x, y, w, h)
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


def _tt_font_widths(font: TTFFont) -> str:
    rangeid: int = 0
    range_: dict[int, list[int]] = {}
    range_interval: dict[int, bool] = {}
    prevcid: int = -2
    prevwidth: int = -1
    interval: bool = False

    # Glyphs sorted by mapped character id
    glyphs = dict(sorted(font.subset.items(), key=lambda item: item[1]))

    for glyph in glyphs:
        assert glyph is not None
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
    w: list[str] = []
    for k, ws in sorted(range_.items()):
        if len(set(ws)) == 1:
            w.append(f" {k} {k + len(ws) - 1} {ws[0]}")
        else:
            w.append(f" {k} [ {' '.join(str(int(h)) for h in ws)} ]\n")
    return f"[{''.join(w)}]"


def _cid_font_widths(cid_widths: dict[int, int]) -> str:
    rangeid: int = 0
    range_: dict[int, list[int]] = {}
    range_interval: dict[int, bool] = {}
    prevcid: int = -2
    prevwidth: int = -1
    interval: bool = False

    for cid, width in sorted(cid_widths.items()):
        if cid == (prevcid + 1):
            if width == prevwidth:
                if width == range_[rangeid][0]:
                    range_.setdefault(rangeid, []).append(width)
                else:
                    range_[rangeid].pop()
                    rangeid = prevcid
                    range_[rangeid] = [prevwidth, width]
                interval = True
                range_interval[rangeid] = True
            else:
                if interval:
                    rangeid = cid
                    range_[rangeid] = [width]
                else:
                    range_[rangeid].append(width)
                interval = False
        else:
            rangeid = cid
            range_[rangeid] = [width]
            interval = False
        prevcid = cid
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
    w: list[str] = []
    for k, ws in sorted(range_.items()):
        if len(set(ws)) == 1:
            w.append(f" {k} {k + len(ws) - 1} {ws[0]}")
        else:
            w.append(f" {k} [ {' '.join(str(int(h)) for h in ws)} ]\n")
    return f"[{''.join(w)}]"


def _dimensions_to_mediabox(dimensions: tuple[float, float]) -> str:
    width_pt, height_pt = dimensions
    return f"[0 0 {width_pt:.2f} {height_pt:.2f}]"


def _sizeof_fmt(num: float, suffix: str = "B") -> str:
    # Recipe from: https://stackoverflow.com/a/1094933/636849
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024
    return f"{num:.1f}Yi{suffix}"


def soft_mask_path_to_xobject(
    path: PaintSoftMask | ImageSoftMask, resource_catalog: ResourceCatalog
) -> PDFContentStream:
    """Converts a PaintedSoftMask into a PDF XObject Form suitable for use as a soft mask."""
    xobject = PDFContentStream(contents=path.render(resource_catalog).encode("latin-1"))
    xobject._path = path  # type: ignore[attr-defined]
    xobject.type = Name("XObject")  # type: ignore[attr-defined]
    xobject.subtype = Name("Form")  # type: ignore[attr-defined]
    xobject.b_box = PDFArray(path.get_bounding_box())  # type: ignore[attr-defined]
    xobject.group = "<</S /Transparency /CS /DeviceGray /I true /K false>>"  # type: ignore[attr-defined]
    return xobject


def blend_group_to_xobject(
    group: "BlendGroup", resource_catalog: ResourceCatalog
) -> PDFContentStream:
    """Convert a blend group into a Form XObject with an isolated transparency group."""
    stream = group.render(resource_catalog)
    xobject = PDFContentStream(contents=stream.encode("latin-1"))
    xobject._blend_group = group  # type: ignore[attr-defined]
    xobject._registered = False  # type: ignore[attr-defined]
    xobject.type = Name("XObject")  # type: ignore[attr-defined]
    xobject.subtype = Name("Form")  # type: ignore[attr-defined]
    bbox = group.get_bounding_box()
    xobject.b_box = PDFArray(bbox)  # type: ignore[attr-defined]
    xobject.group = "<</S /Transparency /CS /DeviceRGB /I true>>"  # type: ignore[attr-defined]
    return xobject
