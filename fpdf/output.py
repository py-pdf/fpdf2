# pylint: disable=protected-access
import logging
from collections import OrderedDict
from contextlib import contextmanager
from io import BytesIO

from .enums import SignatureFlag
from .errors import FPDFException
from .drawing import render_pdf_primitive
from .outline import serialize_outline
from .sign import Signature, sign_content
from .syntax import Name, PDFArray, PDFContentStream, PDFObject
from .syntax import create_dictionary_string as pdf_dict
from .syntax import create_list_string as pdf_list
from .syntax import create_stream as pdf_stream
from .syntax import iobj_ref as pdf_ref
from .util import (
    enclose_in_parens,
    format_date,
    object_id_for_page,
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
        _ = float("inf")  # unknown value
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


class PDFFontStream(PDFContentStream):
    def __init__(self, contents, **kwargs):
        super().__init__(contents=contents, compress=True, **kwargs)
        self.length1 = len(contents)


class PDFXObject(PDFContentStream):
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


class PageObject(PDFObject):
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


class PagesRoot(PDFObject):
    def __init__(self, kids, count, media_box, **kwargs):
        super().__init__(**kwargs)
        self.type = Name("Pages")
        self.kids = kids
        self.count = count
        self.media_box = media_box


class OutputProducer:
    "Generates the final bytearray representing the PDF document, based on a FPDF instance."

    def __init__(self, fpdf):
        self.fpdf = fpdf
        self.buffer = bytearray()  # resulting output buffer
        self._pdf_objs = []
        self._trace_labels_per_obj_id = {}
        # array of PDF object offsets in self.buffer, used to build the xref table:
        self.offsets = {}
        self.n = PERMANENT_INITIAL_OBJ_IDS_COUNT  # current PDF object number - TODO: initialize this to 0 & rename it
        self._graphics_state_obj_refs = None
        # Truthy only if a Structure Tree is added to the document:
        self._struct_tree_root_obj_id = None
        # Truthy only if an Outline is added to the document:
        self._outlines_obj_id = None
        # Truthy only if XMP metadata is added to the document:
        self._xmp_metadata_obj_id = None

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
        #     pages_count=self.fpdf.pages_count,
        #     first_page_obj_id=object_id_for_page(1),
        # ))
        page_objs = self._add_pages(resources_dict_obj_id)
        pages_root_obj_id = self._add_pages_root(page_objs)  # TODO: move this before
        assert pages_root_obj_id == 1  # TODO: remove this temporary assertion
        sig_annotation_obj_id = self._add_annotations_as_objects()
        for embedded_file in self.fpdf.embedded_files:
            self._add_pdf_obj(embedded_file, "embedded_files")
        font_objs_per_index = self._add_fonts()
        img_objs_per_index = self._add_images()

        # 2. Inject all PDF object references required:
        for page_obj in page_objs:
            page_obj.parent = pdf_ref(pages_root_obj_id)

        # 3. Serializing - appending all PDF objects to the buffer:
        assert (
            not self.buffer
        ), f"Nothing should have been appended to the .buffer at this stage: {self.buffer}"
        assert (
            not self.offsets
        ), f"No offset should have been set at this stage: {len(self.offsets)}"
        self._out(f"%PDF-{fpdf.pdf_version}")
        for pdf_obj in self._pdf_objs:
            self.offsets[pdf_obj.id] = len(self.buffer)
            trace_label = self._trace_labels_per_obj_id.get(pdf_obj.id)
            if trace_label:
                with self._trace_size(trace_label):
                    self._out(pdf_obj.serialize())
            else:
                self._out(pdf_obj.serialize())

        # self._add_xref_and_trailer(page=1)
        # pages_root_obj_id = self._add_pages_root(page_objs)
        # catalog_obj_id = self._add_catalog(pages_root_obj_id)
        # resources_dict_obj_id = self._add_resources_dict()
        # self._add_primary_hint_stream()

        # Legacy code being refactored (WIP):
        with self._trace_size("gfxstate"):
            self._put_graphics_state_dicts()
        resources_dict_obj_id = self._put_resources_dict(
            font_objs_per_index, img_objs_per_index
        )  # TODO: move this before
        if not fpdf.struct_builder.empty():
            with self._trace_size("structure_tree"):
                self._put_structure_tree()
        else:
            self._struct_tree_root_obj_id = False
        if fpdf._outline:
            with self._trace_size("document_outline"):
                self._put_document_outline()
        else:
            self._outlines_obj_id = False
        if fpdf.xmp_metadata:
            self._put_xmp_metadata()
        else:
            self._xmp_metadata_obj_id = False
        info_obj_id = self._put_info()
        catalog_obj_id = self._put_catalog(
            pages_root_obj_id, sig_annotation_obj_id
        )  # TODO: move this before
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

    def _newobj(self):
        "Begin a new PDF object"  # TODO: remove this method in the end
        self.n += 1
        self.offsets[self.n] = len(self.buffer)
        self._out(f"{self.n} 0 obj")
        return self.n

    def _add_pdf_obj(self, pdf_obj, trace_label=None):
        self.n += 1
        pdf_obj.id = self.n
        self._pdf_objs.append(pdf_obj)
        if trace_label:
            self._trace_labels_per_obj_id[self.n] = trace_label
        return self.n

    def _add_pages_root(self, page_objs):
        fpdf = self.fpdf
        if fpdf.def_orientation == "P":
            dw_pt = fpdf.dw_pt
            dh_pt = fpdf.dh_pt
        else:
            dw_pt = fpdf.dh_pt
            dh_pt = fpdf.dw_pt
        pages_root_obj = PagesRoot(
            kids=PDFArray(page_objs),
            count=fpdf.pages_count,
            media_box=f"[0 0 {dw_pt:.2f} {dh_pt:.2f}]",
        )
        pages_root_obj.id = 1
        self._pdf_objs.append(pages_root_obj)
        # self._add_pdf_obj(pages_root_obj)  # TODO: uncomment this and remove the 2 lines above
        return pages_root_obj.id

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
            assert page_obj_id == object_id_for_page(page_number)
            # TODO: FPDF.add_page could directly store PageObject intances in .pages,
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
            page_obj = PageObject(
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
            cs_id = self._add_pdf_obj(cs_obj, "pages")
            page_obj.contents = pdf_ref(cs_id)

        return page_objs

    def _add_annotations_as_objects(self):
        sig_annotation_obj_id = None
        for page_annots_as_obj in self.fpdf.annots_as_obj.values():
            for annot_obj in page_annots_as_obj:
                obj_id = self._add_pdf_obj(annot_obj, "annotations_objects")
                if isinstance(annot_obj.v, Signature):
                    assert (
                        sig_annotation_obj_id is None
                    ), "A /Sig annotation is present on more than 1 page"
                    sig_annotation_obj_id = obj_id
        return sig_annotation_obj_id

    def _add_fonts(self):
        fpdf = self.fpdf
        font_objs_per_index = {}
        for font in sorted(fpdf.fonts.values(), key=lambda font: font["i"]):
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
                composite_font_obj.to_unicode = pdf_ref(to_unicode_obj.id)

                cid_system_info_obj = CIDSystemInfo(
                    registry="Adobe", ordering="UCS", supplement=0
                )
                self._add_pdf_obj(cid_system_info_obj, "fonts")
                cid_font_obj.c_i_d_system_info = pdf_ref(cid_system_info_obj.id)

                font_descriptor_obj = font["desc"]
                font_descriptor_obj.font_name = Name(fontname)
                self._add_pdf_obj(font_descriptor_obj, "fonts")
                cid_font_obj.font_descriptor = pdf_ref(font_descriptor_obj.id)

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
                cid_font_obj.c_i_d_to_g_i_d_map = pdf_ref(cid_to_gid_map_obj.id)

                font_file_cs_obj = PDFFontStream(contents=ttfontstream)
                self._add_pdf_obj(font_file_cs_obj, "fonts")
                font_descriptor_obj.font_file2 = pdf_ref(font_file_cs_obj.id)

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
            smask_obj = self._add_image(
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
            img_obj.s_mask = pdf_ref(smask_obj.id)

        # Palette
        if "/Indexed" in color_space:
            pal_cs_obj = PDFContentStream(
                contents=info["pal"], compress=self.fpdf.compress
            )
            self._add_pdf_obj(pal_cs_obj, "images")
            img_obj.color_space.append(pdf_ref(pal_cs_obj.id))

        return img_obj

    def _put_graphics_state_dicts(self):
        self._graphics_state_obj_refs = OrderedDict()
        for state_dict, name in self.fpdf._drawing_graphics_state_registry.items():
            self._newobj()
            self._graphics_state_obj_refs[name] = self.n
            self._out(state_dict)
            self._out("endobj")

    def _put_resources_dict(self, font_objs_per_index, img_objs_per_index):
        # obj_id = self._newobj()  # TODO: uncomment this an remove the next 3 lines
        obj_id = 2
        self.offsets[obj_id] = len(self.buffer)
        self._out(f"{obj_id} 0 obj")
        self._out("<<")

        # From section 10.1, "Procedure Sets", of PDF 1.7 spec:
        # > Beginning with PDF 1.4, this feature is considered obsolete.
        # > For compatibility with existing consumer applications,
        # > PDF producer applications should continue to specify procedure sets
        # > (preferably, all of those listed in Table 10.1).
        self._out("/ProcSet [/PDF /Text /ImageB /ImageC /ImageI]")
        self._out("/Font <<")
        for index, font_obj in sorted(font_objs_per_index.items()):
            self._out(f"/F{index} {pdf_ref(font_obj.id)}")
        self._out(">>")

        # if self.fpdf.images:  # TODO: restore this IF
        self._out("/XObject <<")
        for index, img_obj in sorted(img_objs_per_index.items()):
            self._out(f"/I{index} {pdf_ref(img_obj.id)}")
        self._out(">>")

        if self.fpdf._drawing_graphics_state_registry:
            self._put_graphics_state_refs()

        self._out(">>")
        self._out("endobj")
        return obj_id

    def _put_graphics_state_refs(self):
        assert (
            self._graphics_state_obj_refs is not None
        ), "Graphics state objects refs must have been generated"
        self._out("/ExtGState <<")
        for name, obj_id in self._graphics_state_obj_refs.items():
            self._out(f"{render_pdf_primitive(name)} {pdf_ref(obj_id)}")
        self._out(">>")

    def _put_structure_tree(self):
        "Builds a Structure Hierarchy, including image alternate descriptions"
        # This property is later used by _put_catalog to insert a reference to the StructTreeRoot:
        self._struct_tree_root_obj_id = self.n + 1
        self.fpdf.struct_builder.serialize(
            first_object_id=self._struct_tree_root_obj_id, output_producer=self
        )

    def _put_document_outline(self):
        # This property is later used by _put_catalog to insert a reference to the Outlines:
        self._outlines_obj_id = self.n + 1
        serialize_outline(
            self.fpdf._outline,
            first_object_id=self._outlines_obj_id,
            output_producer=self,
        )

    def _put_xmp_metadata(self):
        xpacket = f'<?xpacket begin="ï»¿" id="W5M0MpCehiHzreSzNTczkc9d"?>\n{self.fpdf.xmp_metadata}\n<?xpacket end="w"?>\n'
        self._newobj()
        self._out(f"<</Type /Metadata /Subtype /XML /Length {len(xpacket)}>>")
        self._out(pdf_stream(xpacket))
        self._out("endobj")
        self._xmp_metadata_obj_id = self.n

    def _put_info(self):
        fpdf = self.fpdf
        info_d = {
            "/Title": enclose_in_parens(getattr(fpdf, "title", None)),
            "/Subject": enclose_in_parens(getattr(fpdf, "subject", None)),
            "/Author": enclose_in_parens(getattr(fpdf, "author", None)),
            "/Keywords": enclose_in_parens(getattr(fpdf, "keywords", None)),
            "/Creator": enclose_in_parens(getattr(fpdf, "creator", None)),
            "/Producer": enclose_in_parens(getattr(fpdf, "producer", None)),
        }
        if fpdf.creation_date:
            try:
                info_d["/CreationDate"] = format_date(fpdf.creation_date, with_tz=True)
            except Exception as error:
                raise FPDFException(
                    f"Could not format date: {fpdf.creation_date}"
                ) from error
        obj_id = self._newobj()
        self._out("<<")
        self._out(pdf_dict(info_d, open_dict="", close_dict="", has_empty_fields=True))
        self._out(">>")
        self._out("endobj")
        return obj_id

    def _put_catalog(self, pages_root_obj_id, sig_annotation_obj_id):
        fpdf = self.fpdf
        obj_id = self._newobj()
        self._out("<<")

        catalog_d = {
            "/Type": "/Catalog",
            "/Pages": pdf_ref(pages_root_obj_id),
        }
        lang = enclose_in_parens(getattr(fpdf, "lang", None))
        if lang:
            catalog_d["/Lang"] = lang
        if sig_annotation_obj_id:
            flags = SignatureFlag.SIGNATURES_EXIST + SignatureFlag.APPEND_ONLY
            self._out(
                f"/AcroForm <</Fields [{sig_annotation_obj_id} 0 R] /SigFlags {flags}>>"
            )

        if fpdf.zoom_mode in ZOOM_CONFIGS:
            zoom_config = [
                pdf_ref(
                    object_id_for_page(1)
                ),  # reference to object ID of the 1st page
                *ZOOM_CONFIGS[fpdf.zoom_mode],
            ]
        else:  # zoom_mode is a number, not one of the allowed strings:
            zoom_config = ["/XYZ", "null", "null", str(fpdf.zoom_mode / 100)]
        catalog_d["/OpenAction"] = pdf_list(zoom_config)

        if fpdf.page_layout:
            catalog_d["/PageLayout"] = fpdf.page_layout.value.pdf_repr()
        if fpdf.page_mode:
            catalog_d["/PageMode"] = fpdf.page_mode.value.pdf_repr()
        if fpdf.viewer_preferences:
            catalog_d["/ViewerPreferences"] = fpdf.viewer_preferences.serialize()
        # assert (
        # self._xmp_metadata_obj_id is not None
        # ), "ID of XMP metadata PDF object must be known"
        if self._xmp_metadata_obj_id:
            catalog_d["/Metadata"] = pdf_ref(self._xmp_metadata_obj_id)
        # assert (
        # self._struct_tree_root_obj_id is not None
        # ), "ID of root PDF object of the Structure Tree must be known"
        if self._struct_tree_root_obj_id:
            catalog_d["/MarkInfo"] = pdf_dict({"/Marked": "true"})
            catalog_d["/StructTreeRoot"] = pdf_ref(self._struct_tree_root_obj_id)
        # assert (
        # self._outlines_obj_id is not None
        # ), "ID of Outlines PDF object must be known"
        if self._outlines_obj_id:
            catalog_d["/Outlines"] = pdf_ref(self._outlines_obj_id)
        if self.fpdf.embedded_files:
            file_spec_names = [
                f"{enclose_in_parens(embedded_file.basename())} {embedded_file.file_spec().serialize()}"
                for embedded_file in self.fpdf.embedded_files
            ]
            catalog_d["/Names"] = pdf_dict(
                {"/EmbeddedFiles": pdf_dict({"/Names": pdf_list(file_spec_names)})}
            )

        self._out(pdf_dict(catalog_d, open_dict="", close_dict=""))
        self._out(">>")
        self._out("endobj")
        return obj_id

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
