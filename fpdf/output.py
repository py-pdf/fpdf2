# pylint: disable=protected-access
import logging
from collections import OrderedDict
from contextlib import contextmanager
from io import BytesIO

from .enums import SignatureFlag
from .errors import FPDFException
from .outline import build_outline_objs
from .sign import Signature, sign_content
from .syntax import build_obj_dict, Name, PDFArray, PDFContentStream, PDFObject
from .syntax import create_dictionary_string as pdf_dict
from .syntax import create_list_string as pdf_list
from .syntax import iobj_ref as pdf_ref
from .util import (
    enclose_in_parens,
    format_date,
    PERMANENT_INITIAL_OBJ_IDS_COUNT,
)

from fontTools import ttLib
from fontTools import subset as ftsubset

try:
    from endesive import signer
except ImportError:
    signer = None


LOGGER = logging.getLogger(__name__)

ZOOM_CONFIGS = {  # cf. section 8.2.1 "Destinations" of the 2006 PDF spec 1.7:
    "fullpage": ("/Fit",),
    "fullwidth": ("/FitH", "null"),
    "real": ("/XYZ", "null", "null", "1"),
}


class PDFLinearization(PDFObject):
    def __init__(self, file_length, pages_count, first_page_obj_id, **kwargs):
        super().__init__(**kwargs)
        _ = float("inf")  # TODO: unknown value
        self.linearized = "1.0"  # Version
        self.l = file_length
        self.h = [_]  # Primary hint stream offset and length (part 5)
        self.o = first_page_obj_id  # Object number of first page’s page object (part 6)
        self.e = _  # Offset of end of first page
        self.n = pages_count
        self.t = _  # Offset of first entry in main cross-reference table (part 11)


class PDFFont(PDFObject):
    def __init__(self, subtype, base_font, encoding=None, d_w=None, w=None, **kwargs):
        super().__init__(**kwargs)
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


class PDFFontDescriptor(PDFObject):
    def __init__(
        self,
        ascent,
        descent,
        cap_height,
        flags,
        font_b_box,
        italic_angle,
        stem_v,
        missing_width,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.type = Name("FontDescriptor")
        self.ascent = ascent
        self.descent = descent
        self.cap_height = cap_height
        self.flags = flags
        self.font_b_box = font_b_box
        self.italic_angle = italic_angle
        self.stem_v = stem_v
        self.missing_width = missing_width
        self.font_name = None


class CIDSystemInfo(PDFObject):
    def __init__(self, registry, ordering, supplement, **kwargs):
        super().__init__(**kwargs)
        self.registry = enclose_in_parens(registry)
        self.ordering = enclose_in_parens(ordering)
        self.supplement = supplement


class PDFInfo(PDFObject):
    def __init__(
        self,
        title,
        subject,
        author,
        keywords,
        creator,
        producer,
        creation_date,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.title = enclose_in_parens(title) if title else None
        self.subject = enclose_in_parens(subject) if subject else None
        self.author = enclose_in_parens(author) if author else None
        self.keywords = enclose_in_parens(keywords) if keywords else None
        self.creator = enclose_in_parens(creator) if creator else None
        self.producer = enclose_in_parens(producer) if producer else None
        self.creation_date = creation_date


class AcroForm:
    def __init__(self, fields, sig_flags):
        self.fields = fields
        self.sig_flags = sig_flags

    def serialize(self):
        obj_dict = build_obj_dict({key: getattr(self, key) for key in dir(self)})
        return pdf_dict(obj_dict, field_join=" ")


class PDFCatalog(PDFObject):
    def __init__(
        self,
        pages,
        lang,
        acro_form,
        open_action,
        page_layout,
        page_mode,
        viewer_preferences,
        metadata,
        mark_info,
        struct_tree_root,
        outlines,
        names,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.type = Name("Catalog")
        self.pages = pages
        self.lang = enclose_in_parens(lang) if lang else None
        self.acro_form = acro_form
        self.open_action = open_action
        self.page_layout = page_layout
        self.page_mode = page_mode
        self.viewer_preferences = viewer_preferences
        self.metadata = metadata
        self.mark_info = mark_info
        self.struct_tree_root = struct_tree_root
        self.outlines = outlines
        self.names = names


class PDFResources(PDFObject):
    def __init__(self, proc_set, font, x_object, ext_g_state, **kwargs):
        super().__init__(**kwargs)
        self.proc_set = proc_set
        self.font = font
        self.x_object = x_object
        self.ext_g_state = ext_g_state


class PDFFontStream(PDFContentStream):
    def __init__(self, contents, **kwargs):
        super().__init__(contents=contents, compress=True, **kwargs)
        self.length1 = len(contents)


class PDFXmpMetadata(PDFContentStream):
    def __init__(self, contents, **kwargs):
        super().__init__(contents=contents, **kwargs)
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
        "filter",
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
        **kwargs,
    ):
        super().__init__(contents=contents, **kwargs)
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


class PDFPage(PDFObject):
    __slots__ = (  # RAM usage optimization
        "_id",
        "type",
        "parent",
        "dur",
        "trans",
        "media_box",
        "resources",
        "annots",
        "group",
        "struct_parents",
        "contents",
    )

    def __init__(
        self,
        duration,
        transition,
        media_box,
        resources_dict_obj_id,
        annots,
        group,
        spid,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.type = Name("Page")
        self.parent = None  # must always be set before calling .serialize()
        self.dur = duration
        self.trans = transition
        self.media_box = media_box
        # TODO: insert a direct /Resource PDF object, with only images / fonts / graphics states used on the page
        self.resources = pdf_ref(resources_dict_obj_id)
        self.annots = annots
        self.group = group
        self.struct_parents = spid
        self.contents = None  # must always be set before calling .serialize()


class PDFPagesRoot(PDFObject):
    def __init__(self, kids, count, media_box, **kwargs):
        super().__init__(**kwargs)
        self.type = Name("Pages")
        self.kids = kids
        self.count = count
        self.media_box = media_box


class PDFExtGState(PDFObject):
    def __init__(self, dict_as_str, **kwargs):
        super().__init__(**kwargs)
        self._dict_as_str = dict_as_str

    # method override
    def serialize(self, obj_dict=None):
        return f"{self.id} 0 obj\n{self._dict_as_str}\nendobj"


class OutputProducer:
    "Generates the final bytearray representing the PDF document, based on a FPDF instance."

    def __init__(self, fpdf):
        self.fpdf = fpdf
        self.pdf_objs = []
        self.n = PERMANENT_INITIAL_OBJ_IDS_COUNT  # current PDF object number - TODO: initialize this to 0 & rename it
        # array of PDF object offsets in self.buffer, used to build the xref table:
        self.offsets = {}
        self.trace_labels_per_obj_id = {}
        self.buffer = bytearray()  # resulting output buffer

    def bufferize(self):
        "This method DOES NOT alter the target FPDF instance in any way"
        LOGGER.debug("Final doc sections size summary:")
        fpdf = self.fpdf
        # TODO: temporary, remove this line:
        resources_dict_obj_id = PERMANENT_INITIAL_OBJ_IDS_COUNT

        # 1. Insert all objects in the order required to build a linearized PDF,
        #    and assign IDs to those objects:
        # self._add_pdf_obj(PDFLinearization(
        #     file_length=len(self.buffer),
        #     pages_count=fpdf.pages_count,
        #     first_page_obj_id=page_objs[0].id,
        # ))
        page_objs = self._add_pages(resources_dict_obj_id)
        pages_root_obj = self._add_pages_root(page_objs)  # TODO: move this before
        sig_annotation_obj = self._add_annotations_as_objects()
        for embedded_file in fpdf.embedded_files:
            self._add_pdf_obj(embedded_file, "embedded_files")
        font_objs_per_index = self._add_fonts()
        img_objs_per_index = self._add_images()
        gfxstate_objs_per_name = self._add_gfxstates()
        self._add_resources_dict(
            font_objs_per_index, img_objs_per_index, gfxstate_objs_per_name
        )  # TODO: move this before
        struct_tree_root_obj = self._add_structure_tree()
        outline_dict_obj = self._add_document_outline(page_objs)
        xmp_metadata_obj = self._add_xmp_metadata()
        info_obj_id = self._add_info()
        catalog_obj_id = self._add_catalog(
            pages_root_obj,
            page_objs[0].id,
            sig_annotation_obj,
            xmp_metadata_obj,
            struct_tree_root_obj,
            outline_dict_obj,
        )  # TODO: move this before

        # 2. Inject all PDF object references required:
        for page_obj in page_objs:
            page_obj.parent = pdf_ref(pages_root_obj.id)

        # WIP: linearized order
        # self._add_xref_and_trailer(page=1)
        # pages_root_obj = self._add_pages_root(page_objs)
        # catalog_obj_id = self._add_catalog(pages_root_obj.id)
        # resources_dict_obj = self._add_resources_dict()
        # self._add_primary_hint_stream()

        # 3. Serializing - appending all PDF objects to the buffer:
        assert (
            not self.buffer
        ), f"Nothing should have been appended to the .buffer at this stage: {self.buffer}"
        assert (
            not self.offsets
        ), f"No offset should have been set at this stage: {len(self.offsets)}"
        self._out(f"%PDF-{fpdf.pdf_version}")
        for pdf_obj in self.pdf_objs:
            self.offsets[pdf_obj.id] = len(self.buffer)
            trace_label = self.trace_labels_per_obj_id.get(pdf_obj.id)
            if trace_label:
                with self._trace_size(trace_label):
                    self._out(pdf_obj.serialize())
            else:
                self._out(pdf_obj.serialize())
        self._put_xref_and_trailer(catalog_obj_id, info_obj_id)
        self._out("%%EOF")

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
        self.n += 1
        pdf_obj.id = self.n
        self.pdf_objs.append(pdf_obj)
        if trace_label:
            self.trace_labels_per_obj_id[self.n] = trace_label
        return self.n

    def _add_pages_root(self, page_objs):
        fpdf = self.fpdf
        if fpdf.def_orientation == "P":
            dw_pt = fpdf.dw_pt
            dh_pt = fpdf.dh_pt
        else:
            dw_pt = fpdf.dh_pt
            dh_pt = fpdf.dw_pt
        pages_root_obj = PDFPagesRoot(
            kids=PDFArray(page_objs),
            count=fpdf.pages_count,
            media_box=f"[0 0 {dw_pt:.2f} {dh_pt:.2f}]",
        )
        pages_root_obj.id = 1
        self.pdf_objs.append(pages_root_obj)
        # self._add_pdf_obj(pages_root_obj)  # TODO: uncomment this and remove the 2 lines above
        return pages_root_obj

    def _add_pages(self, resources_dict_obj_id):
        fpdf = self.fpdf
        if fpdf.def_orientation == "P":
            dw_pt = fpdf.dw_pt
            dh_pt = fpdf.dh_pt
        else:
            dw_pt = fpdf.dh_pt
            dh_pt = fpdf.dw_pt

        page_objs = []
        for page_number in range(1, fpdf.pages_count + 1):
            page_obj_id = self.n + 1
            # TODO: FPDF.add_page could directly store PDFPage intances in .pages,
            #       to limit Python object allocations in memory
            page = fpdf.pages[page_number]
            w_pt, h_pt = page["w_pt"], page["h_pt"]
            media_box = (
                f"[0 0 {w_pt:.2f} {h_pt:.2f}]"
                if w_pt != dw_pt or h_pt != dh_pt
                else None
            )
            group = (
                pdf_dict(
                    {"/Type": "/Group", "/S": "/Transparency", "/CS": "/DeviceRGB"},
                    field_join=" ",
                )
                if fpdf.pdf_version > "1.3"
                else None
            )
            annots = None
            page_annots = fpdf.annots[page_number]
            page_annots_as_obj = fpdf.annots_as_obj[page_number]
            if page_annots or page_annots_as_obj:
                annots = PDFArray(page_annots + page_annots_as_obj)
                for annot in annots:
                    if annot.dest:
                        annot.dest.page_ref = pdf_ref(page_obj_id)
            page_obj = PDFPage(
                media_box=media_box,
                duration=page["duration"] or None,
                transition=page["transition"] if page["transition"] else None,
                resources_dict_obj_id=resources_dict_obj_id,
                annots=annots,
                group=group,
                spid=fpdf._struct_parents_id_per_page.get(page_obj_id),
            )
            self._add_pdf_obj(page_obj, "pages")
            page_objs.append(page_obj)

            cs_obj = PDFContentStream(contents=page["content"], compress=fpdf.compress)
            self._add_pdf_obj(cs_obj, "pages")
            page_obj.contents = cs_obj

        # Assigning the page_ref property of all Destination objects in pages:
        dests = []
        for page_obj in page_objs:
            for annot in page_obj.annots or ():
                if annot.dest:
                    dests.append(annot.dest)
                if annot.a and hasattr(annot.a, "dest"):
                    dests.append(annot.a.dest)
        for dest in dests:
            dest.page_ref = pdf_ref(page_objs[dest.page_number - 1].id)

        return page_objs

    def _add_annotations_as_objects(self):
        sig_annotation_obj = None
        for page_annots_as_obj in self.fpdf.annots_as_obj.values():
            for annot_obj in page_annots_as_obj:
                self._add_pdf_obj(annot_obj, "annotations_objects")
                if isinstance(annot_obj.v, Signature):
                    assert (
                        sig_annotation_obj is None
                    ), "A /Sig annotation is present on more than 1 page"
                    sig_annotation_obj = annot_obj
        return sig_annotation_obj

    def _add_fonts(self):
        font_objs_per_index = {}
        for font in sorted(self.fpdf.fonts.values(), key=lambda font: font["i"]):
            # Standard font
            if font["type"] == "core":
                encoding = (
                    "WinAnsiEncoding"
                    if font["name"] not in ("Symbol", "ZapfDingbats")
                    else None
                )
                core_font_obj = PDFFont(
                    subtype="Type1", base_font=font["name"], encoding=encoding
                )
                self._add_pdf_obj(core_font_obj, "fonts")
                font_objs_per_index[font["i"]] = core_font_obj
            elif font["type"] == "TTF":
                fontname = f"MPDFAA+{font['name']}"

                # unicode_char -> new_code_char map for chars embedded in the PDF
                uni_to_new_code_char = font["subset"].dict()

                # why we delete 0-element?
                del uni_to_new_code_char[0]

                # ---- FONTTOOLS SUBSETTER ----
                # recalcTimestamp=False means that it doesn't modify the "modified" timestamp in head table
                # if we leave recalcTimestamp=True the tests will break every time
                fonttools_font = ttLib.TTFont(
                    file=font["ttffile"], recalcTimestamp=False
                )

                # 1. get all glyphs in PDF
                cmap = fonttools_font["cmap"].getBestCmap()
                glyph_names = [
                    cmap[unicode] for unicode in uni_to_new_code_char if unicode in cmap
                ]

                # 2. make a subset
                # notdef_outline=True means that keeps the white box for the .notdef glyph
                # recommended_glyphs=True means that adds the .notdef, .null, CR, and space glyphs
                options = ftsubset.Options(notdef_outline=True, recommended_glyphs=True)
                # dropping the tables previous dropped in the old ttfonts.py file #issue 418
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
                for code, new_code_mapped in uni_to_new_code_char.items():
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

                # 4. return the ttfile
                output = BytesIO()
                fonttools_font.save(output)

                output.seek(0)
                ttfontstream = output.read()

                # A composite font - a font composed of other fonts,
                # organized hierarchically
                composite_font_obj = PDFFont(
                    subtype="Type0", base_font=fontname, encoding="Identity-H"
                )
                self._add_pdf_obj(composite_font_obj, "fonts")
                font_objs_per_index[font["i"]] = composite_font_obj

                # A CIDFont whose glyph descriptions are based on
                # TrueType font technology
                cid_font_obj = PDFFont(
                    subtype="CIDFontType2",
                    base_font=fontname,
                    d_w=font["desc"].missing_width,
                    w=_tt_font_widths(font, max(uni_to_new_code_char)),
                )
                self._add_pdf_obj(cid_font_obj, "fonts")
                composite_font_obj.descendant_fonts = PDFArray([cid_font_obj])

                # bfChar
                # This table informs the PDF reader about the unicode
                # character that each used 16-bit code belongs to. It
                # allows searching the file and copying text from it.
                bfChar = []
                uni_to_new_code_char = font["subset"].dict()
                for code in uni_to_new_code_char:
                    code_mapped = uni_to_new_code_char.get(code)
                    if code > 0xFFFF:
                        # Calculate surrogate pair
                        code_high = 0xD800 | (code - 0x10000) >> 10
                        code_low = 0xDC00 | (code & 0x3FF)
                        bfChar.append(
                            f"<{code_mapped:04X}> <{code_high:04X}{code_low:04X}>\n"
                        )
                    else:
                        bfChar.append(f"<{code_mapped:04X}> <{code:04X}>\n")

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

                cid_system_info_obj = CIDSystemInfo(
                    registry="Adobe", ordering="UCS", supplement=0
                )
                self._add_pdf_obj(cid_system_info_obj, "fonts")
                cid_font_obj.c_i_d_system_info = cid_system_info_obj

                font_descriptor_obj = font["desc"]
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

        return font_objs_per_index

    def _add_images(self):
        img_objs_per_index = {}
        for img in sorted(self.fpdf.images.values(), key=lambda img: img["i"]):
            if img["usages"] > 0:
                img_objs_per_index[img["i"]] = self._add_image(img)
        return img_objs_per_index

    def _add_image(self, info):
        color_space = Name(info["cs"])
        decode = None
        if color_space == "Indexed":
            color_space = PDFArray(
                ["/Indexed", "/DeviceRGB", f"{len(info['pal']) // 3 - 1}"]
            )
        elif color_space == "DeviceCMYK":
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
        self._add_pdf_obj(img_obj, "images")

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
        for state_dict, name in self.fpdf._drawing_graphics_state_registry.items():
            gfxstate_obj = PDFExtGState(state_dict)
            self._add_pdf_obj(gfxstate_obj, "gfxstate")
            gfxstate_objs_per_name[name] = gfxstate_obj
        return gfxstate_objs_per_name

    def _add_resources_dict(
        self, font_objs_per_index, img_objs_per_index, gfxstate_objs_per_name
    ):
        # From section 10.1, "Procedure Sets", of PDF 1.7 spec:
        # > Beginning with PDF 1.4, this feature is considered obsolete.
        # > For compatibility with existing consumer applications,
        # > PDF producer applications should continue to specify procedure sets
        # > (preferably, all of those listed in Table 10.1).
        proc_set = "[/PDF /Text /ImageB /ImageC /ImageI]"

        # if font_objs_per_index:  # TODO: restore this IF
        font = pdf_dict(
            {
                f"/F{index}": pdf_ref(font_obj.id)
                for index, font_obj in sorted(font_objs_per_index.items())
            }
        )

        # if img_objs_per_index:  # TODO: restore this IF
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
        else:
            ext_g_state = None

        resources_obj = PDFResources(
            proc_set=proc_set, font=font, x_object=x_object, ext_g_state=ext_g_state
        )
        resources_obj.id = 2
        self.pdf_objs.append(resources_obj)
        # self._add_pdf_obj(resources_obj)  # TODO: uncomment this and remove the 2 lines above

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

    def _add_document_outline(self, page_objs):
        if not self.fpdf._outline:
            return None
        outline_dict_obj = None
        for pdf_obj in build_outline_objs(self.fpdf._outline, page_objs):
            if outline_dict_obj is None:
                outline_dict_obj = pdf_obj
            self._add_pdf_obj(pdf_obj, "document_outline")
        return outline_dict_obj

    def _add_xmp_metadata(self):
        if not self.fpdf.xmp_metadata:
            return None
        xpacket = f'<?xpacket begin="ï»¿" id="W5M0MpCehiHzreSzNTczkc9d"?>\n{self.fpdf.xmp_metadata}\n<?xpacket end="w"?>\n'
        pdf_obj = PDFXmpMetadata(xpacket)
        self._add_pdf_obj(pdf_obj)
        return pdf_obj

    def _add_info(self):
        fpdf = self.fpdf
        creation_date = None
        if fpdf.creation_date:
            try:
                creation_date = format_date(fpdf.creation_date, with_tz=True)
            except Exception as error:
                raise FPDFException(
                    f"Could not format date: {fpdf.creation_date}"
                ) from error
        info_obj = PDFInfo(
            title=getattr(fpdf, "title", None),
            subject=getattr(fpdf, "subject", None),
            author=getattr(fpdf, "author", None),
            keywords=getattr(fpdf, "keywords", None),
            creator=getattr(fpdf, "creator", None),
            producer=getattr(fpdf, "producer", None),
            creation_date=creation_date,
        )
        return self._add_pdf_obj(info_obj)

    def _add_catalog(
        self,
        pages_root_obj,
        first_page_obj_id,
        sig_annotation_obj,
        xmp_metadata_obj,
        struct_tree_root_obj,
        outline_dict_obj,
    ):
        fpdf = self.fpdf

        acro_form = None
        if sig_annotation_obj:
            flags = SignatureFlag.SIGNATURES_EXIST + SignatureFlag.APPEND_ONLY
            acro_form = AcroForm(fields=PDFArray([sig_annotation_obj]), sig_flags=flags)

        if fpdf.zoom_mode in ZOOM_CONFIGS:
            zoom_config = [
                pdf_ref(first_page_obj_id),
                *ZOOM_CONFIGS[fpdf.zoom_mode],
            ]
        else:  # zoom_mode is a number, not one of the allowed strings:
            zoom_config = ["/XYZ", "null", "null", str(fpdf.zoom_mode / 100)]

        mark_info = pdf_dict({"/Marked": "true"}) if struct_tree_root_obj else None
        names = None
        if fpdf.embedded_files:
            file_spec_names = [
                f"{enclose_in_parens(embedded_file.basename())} {embedded_file.file_spec().serialize()}"
                for embedded_file in fpdf.embedded_files
            ]
            names = pdf_dict(
                {"/EmbeddedFiles": pdf_dict({"/Names": pdf_list(file_spec_names)})}
            )

        catalog_obj = PDFCatalog(
            pages=pages_root_obj,
            lang=getattr(fpdf, "lang", None),
            acro_form=acro_form,
            open_action=pdf_list(zoom_config),
            page_layout=fpdf.page_layout,
            page_mode=fpdf.page_mode,
            viewer_preferences=fpdf.viewer_preferences,
            metadata=xmp_metadata_obj,
            mark_info=mark_info,
            struct_tree_root=struct_tree_root_obj,
            outlines=outline_dict_obj,
            names=names,
        )
        return self._add_pdf_obj(catalog_obj)

    def _put_xref_and_trailer(self, catalog_obj_id, info_obj_id):
        startxref = len(self.buffer)
        self._out("xref")
        self._out(f"0 {self.n + 1}")
        self._out("0000000000 65535 f ")
        for i in range(1, self.n + 1):
            self._out(f"{self.offsets[i]:010} 00000 n ")
        self._out("trailer")
        self._out("<<")
        self._out(f"/Size {self.n + 1}")
        self._out(f"/Root {pdf_ref(catalog_obj_id)}")
        self._out(f"/Info {pdf_ref(info_obj_id)}")
        file_id = self.fpdf.file_id()
        if file_id == -1:
            file_id = self.fpdf._default_file_id(self.buffer)
        if file_id:
            self._out(f"/ID [{file_id}]")
        self._out(">>")
        self._out("startxref")
        self._out(startxref)

    @contextmanager
    def _trace_size(self, label):
        prev_size = len(self.buffer)
        yield
        LOGGER.debug("- %s.size: %s", label, _sizeof_fmt(len(self.buffer) - prev_size))


def _tt_font_widths(font, maxUni):
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
        char_width = font["cw"][cid]
        if "dw" not in font or (font["dw"] and char_width != font["dw"]):
            cid_mapped = subset.get(cid)
            if cid_mapped is None:
                continue
            if cid_mapped == (prevcid + 1):
                if char_width == prevwidth:
                    if char_width == range_[rangeid][0]:
                        range_.setdefault(rangeid, []).append(char_width)
                    else:
                        range_[rangeid].pop()
                        # new range
                        rangeid = prevcid
                        range_[rangeid] = [prevwidth, char_width]
                    interval = True
                    range_interval[rangeid] = True
                else:
                    if interval:
                        # new range
                        rangeid = cid_mapped
                        range_[rangeid] = [char_width]
                    else:
                        range_[rangeid].append(char_width)
                    interval = False
            else:
                rangeid = cid_mapped
                range_[rangeid] = [char_width]
                interval = False
            prevcid = cid_mapped
            prevwidth = char_width
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


def _sizeof_fmt(num, suffix="B"):
    # Recipe from: https://stackoverflow.com/a/1094933/636849
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024
    return f"{num:.1f}Yi{suffix}"
