# pylint: disable=protected-access
import hashlib, logging, zlib
from collections import OrderedDict
from contextlib import contextmanager
from io import BytesIO

from .enums import SignatureFlag
from .errors import FPDFException
from .drawing import render_pdf_primitive
from .outline import serialize_outline
from .sign import Signature, sign_content
from .syntax import create_dictionary_string as pdf_dict
from .syntax import create_list_string as pdf_list
from .syntax import create_stream as pdf_stream
from .syntax import iobj_ref as pdf_ref
from .util import enclose_in_parens, escape_parens, format_date, object_id_for_page

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


class OutputProducer:
    "Generates the final bytearray representing the PDF document, based on a FPDF instance."

    def __init__(self, fpdf):
        self.fpdf = fpdf
        self.buffer = bytearray()  # resulting output buffer
        # array of PDF object offsets in self.buffer, used to build the xref table:
        self.offsets = {}
        self.n = 2  # current PDF object number
        self._graphics_state_obj_refs = None
        self._embedded_files_per_pdf_ref = None
        # Truthy only if a Structure Tree is added to the document:
        self._struct_tree_root_obj_id = None
        # Truthy only if an Outline is added to the document:
        self._outlines_obj_id = None
        # Truthy only if XMP metadata is added to the document:
        self._xmp_metadata_obj_id = None

    def bufferize(self):
        """
        This operation alters the target FPDF instance
        through calls to ._insert_table_of_contents(), ._substitute_page_number(),
        _set_min_pdf_version() & _final_pdf_version()
        """
        # * PDF object 1 is always the pages root
        # * PDF object 2 is always the resources dictionary
        # Those objects are not inserted first in the document though
        LOGGER.debug("Final doc sections size summary:")
        fpdf = self.fpdf
        with self._trace_size("header"):
            self._out(f"%PDF-{fpdf._final_pdf_version()}")
        self._build_embedded_files_per_pdf_ref()
        # It is important that pages are the first PDF objects inserted in the document,
        # followed immediately by annotations: some parts of fpdf2 currently rely on that
        # order of insertion (e.g. util.object_id_for_page):
        with self._trace_size("pages"):
            self._put_pages()
        with self._trace_size("annotations_objects"):
            sig_annotation_obj_id = self._put_annotations_as_objects()
        with self._trace_size("embedded_files"):
            self._put_embedded_files()
        self._put_resources()  # trace_size is performed inside
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
        with self._trace_size("info"):
            info_obj_id = self._put_info()
        with self._trace_size("catalog"):
            catalog_obj_id = self._put_catalog(sig_annotation_obj_id)
        with self._trace_size("xref"):  #  cross-reference table
            startxref = len(self.buffer)
            self._out("xref")
            self._out(f"0 {self.n + 1}")
            self._out("0000000000 65535 f ")
            for i in range(1, self.n + 1):
                self._out(f"{self.offsets[i]:010} 00000 n ")
        with self._trace_size("trailer"):
            self._put_trailer(info_obj_id, catalog_obj_id, startxref)
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

    def _out(self, s):
        if not isinstance(s, bytes):
            if not isinstance(s, str):
                s = str(s)
            s = s.encode("latin1")
        self.buffer += s + b"\n"

    def _newobj(self):
        "Begin a new PDF object"
        self.n += 1
        self.offsets[self.n] = len(self.buffer)
        self._out(f"{self.n} 0 obj")
        return self.n

    def _build_embedded_files_per_pdf_ref(self):
        assert self._embedded_files_per_pdf_ref is None
        fpdf = self.fpdf
        self._embedded_files_per_pdf_ref = {}
        first_annot_obj_id = object_id_for_page(fpdf.pages_count) + 2
        annotations_count = sum(
            len(page_annots_as_obj)
            for page_annots_as_obj in fpdf.annots_as_obj.values()
        )
        for n, embedd_file in enumerate(
            fpdf.embedded_files, start=first_annot_obj_id + annotations_count
        ):
            self._embedded_files_per_pdf_ref[pdf_ref(n)] = embedd_file

    def _put_pages(self):
        fpdf = self.fpdf
        if fpdf._toc_placeholder:
            fpdf._insert_table_of_contents()
        if fpdf.str_alias_nb_pages:
            fpdf._substitute_page_number()
        if fpdf.def_orientation == "P":
            dw_pt = fpdf.dw_pt
            dh_pt = fpdf.dh_pt
        else:
            dw_pt = fpdf.dh_pt
            dh_pt = fpdf.dw_pt
        compression_filter = "/Filter /FlateDecode " if fpdf.compress else ""

        # The Annotations embedded as PDF objects
        # are added to the document just after all the pages,
        # hence we can deduce their object IDs:
        annot_obj_id = object_id_for_page(fpdf.pages_count) + 2

        for n in range(1, fpdf.pages_count + 1):
            # Page
            self._newobj()
            self._out("<</Type /Page")
            self._out(f"/Parent {pdf_ref(1)}")
            page = fpdf.pages[n]
            if page["duration"]:
                self._out(f"/Dur {page['duration']}")
            if page["transition"]:
                self._out(f"/Trans {page['transition'].dict_as_string()}")
            w_pt, h_pt = page["w_pt"], page["h_pt"]
            if w_pt != dw_pt or h_pt != dh_pt:
                self._out(f"/MediaBox [0 0 {w_pt:.2f} {h_pt:.2f}]")
            self._out(f"/Resources {pdf_ref(2)}")
            annot_obj_id = self._put_page_annotations(n, annot_obj_id)
            if fpdf.pdf_version > "1.3":
                self._out("/Group <</Type /Group /S /Transparency /CS /DeviceRGB>>")
            spid = fpdf._struct_parents_id_per_page.get(self.n)
            if spid is not None:
                self._out(f"/StructParents {spid}")
            self._out(f"/Contents {pdf_ref(self.n + 1)}>>")
            self._out("endobj")

            # Page content
            content = page["content"]
            p = zlib.compress(content) if fpdf.compress else content
            self._newobj()
            self._out(f"<<{compression_filter}/Length {len(p)}>>")
            self._out(pdf_stream(p))
            self._out("endobj")
        # Pages root
        self.offsets[1] = len(self.buffer)
        self._out("1 0 obj")
        self._out("<</Type /Pages")
        self._out(
            "/Kids ["
            + " ".join(
                pdf_ref(object_id_for_page(page))
                for page in range(1, fpdf.pages_count + 1)
            )
            + "]"
        )
        self._out(f"/Count {fpdf.pages_count}")
        self._out(f"/MediaBox [0 0 {dw_pt:.2f} {dh_pt:.2f}]")
        self._out(">>")
        self._out("endobj")

    def _put_page_annotations(self, page_number, annot_obj_id):
        fpdf = self.fpdf
        page_annots = fpdf.annots[page_number]
        page_annots_as_obj = fpdf.annots_as_obj[page_number]
        if page_annots or page_annots_as_obj:
            # Annotations, e.g. links:
            annots = ""
            for annot in page_annots:
                annots += serialize_annot(annot, fpdf, self._embedded_files_per_pdf_ref)
                if annot.quad_points:
                    # This won't alter the PDF header, that has already been rendered,
                    # but can trigger the insertion of a /Page /Group by _put_pages:
                    fpdf._set_min_pdf_version("1.6")
            if page_annots and page_annots_as_obj:
                annots += " "
            annots += " ".join(
                f"{annot_obj_id + i} 0 R" for i in range(len(page_annots_as_obj))
            )
            annot_obj_id += len(page_annots_as_obj)
            self._out(f"/Annots [{annots}]")
        return annot_obj_id

    def _put_annotations_as_objects(self):
        fpdf = self.fpdf
        sig_annotation_obj_id = None
        # The following code inserts annotations in the order
        # they have been inserted in the pages / .annots_as_obj dict;
        # this relies on a property of Python dicts since v3.7:
        for page_annots_as_obj in fpdf.annots_as_obj.values():
            for annot in page_annots_as_obj:
                self._newobj()
                self._out(
                    serialize_annot(annot, fpdf, self._embedded_files_per_pdf_ref)
                )
                self._out("endobj")
                if isinstance(annot.value, Signature):
                    sig_annotation_obj_id = self.n
        return sig_annotation_obj_id

    def _put_embedded_files(self):
        for embedd_file in self.fpdf.embedded_files:
            stream_dict = {
                "/Type": "/EmbeddedFile",
            }
            stream_content = embedd_file.bytes
            if embedd_file.compress:
                stream_dict["/Filter"] = "/FlateDecode"
                stream_content = zlib.compress(stream_content)
            stream_dict["/Length"] = len(stream_content)
            params = {
                "/Size": len(embedd_file.bytes),
            }
            if embedd_file.creation_date:
                params["/CreationDate"] = format_date(
                    embedd_file.creation_date, with_tz=True
                )
            if embedd_file.modification_date:
                params["/ModDate"] = format_date(
                    embedd_file.modification_date, with_tz=True
                )
            if embedd_file.checksum:
                file_hash = hashlib.new("md5", usedforsecurity=False)
                file_hash.update(stream_content)
                hash_hex = file_hash.hexdigest()
                params["/CheckSum"] = f"<{hash_hex}>"
            stream_dict["/Params"] = pdf_dict(params)
            self._newobj()
            self._out(pdf_dict(stream_dict))
            self._out(pdf_stream(stream_content))
            self._out("endobj")
            assert self._embedded_files_per_pdf_ref[pdf_ref(self.n)] == embedd_file

    def _put_resources(self):
        with self._trace_size("resources.fonts"):
            self._put_fonts()
        with self._trace_size("resources.images"):
            self._put_images()
        with self._trace_size("resources.gfxstate"):
            self._put_graphics_state_dicts()

        # Resource dictionary
        with self._trace_size("resources.dict"):
            self._put_resource_dict()

    def _put_fonts(self):
        fpdf = self.fpdf
        flist = [(x[1]["i"], x[0], x[1]) for x in fpdf.fonts.items()]
        flist.sort()
        for _, font_name, font in flist:
            fpdf.fonts[font_name]["n"] = self.n + 1
            # Standard font
            if font["type"] == "core":
                self._newobj()
                self._out("<</Type /Font")
                self._out(f"/BaseFont /{font['name']}")
                self._out("/Subtype /Type1")
                if font["name"] not in ("Symbol", "ZapfDingbats"):
                    self._out("/Encoding /WinAnsiEncoding")
                self._out(">>")
                self._out("endobj")
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
                self._out(_put_TT_font_widths(font, max(uni_to_new_code_char)))
                self._out(f"/CIDToGIDMap {pdf_ref(self.n + 4)}")
                self._out(">>")
                self._out("endobj")

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
                for key, value in font["desc"].items():
                    self._out(f" /{key} {value}")
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

    def _put_images(self):
        for img_info in sorted(
            self.fpdf.images.values(), key=lambda img_info: img_info["i"]
        ):
            if img_info["usages"] > 0:
                self._put_image(img_info)

    def _put_image(self, info):
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
                if self.fpdf.allow_images_transparency and "smask" in info
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

        if self.fpdf.allow_images_transparency and "smask" in info:
            self._out(f"/SMask {pdf_ref(self.n + 1)}")

        self._out(f"/Length {len(info['data'])}>>")
        self._out(pdf_stream(info["data"]))
        self._out("endobj")

        # Soft mask
        if self.fpdf.allow_images_transparency and "smask" in info:
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
            self._put_image(smask)

        # Palette
        if info["cs"] == "Indexed":
            self._newobj()
            if self.fpdf.compress:
                pal_filter, pal_data = (
                    "/Filter /FlateDecode ",
                    zlib.compress(info["pal"]),
                )
            else:
                pal_filter, pal_data = ("", info["pal"])
            self._out(f"<<{pal_filter}/Length {len(pal_data)}>>")
            self._out(pdf_stream(pal_data))
            self._out("endobj")

    def _put_graphics_state_dicts(self):
        self._graphics_state_obj_refs = OrderedDict()
        for state_dict, name in self.fpdf._drawing_graphics_state_registry.items():
            self._newobj()
            self._graphics_state_obj_refs[name] = self.n
            self._out(state_dict)
            self._out("endobj")

    def _put_resource_dict(self):
        self.offsets[2] = len(self.buffer)
        self._out("2 0 obj")
        self._out("<<")

        # From section 10.1, "Procedure Sets", of PDF 1.7 spec:
        # > Beginning with PDF 1.4, this feature is considered obsolete.
        # > For compatibility with existing consumer applications,
        # > PDF producer applications should continue to specify procedure sets
        # > (preferably, all of those listed in Table 10.1).
        self._out("/ProcSet [/PDF /Text /ImageB /ImageC /ImageI]")
        self._out("/Font <<")
        font_ids = [(x["i"], x["n"]) for x in self.fpdf.fonts.values()]
        font_ids.sort()
        for idx, n in font_ids:
            self._out(f"/F{idx} {pdf_ref(n)}")
        self._out(">>")

        # if self.images: [TODO] uncomment this & indent the next 3 lines in order to save 15 bytes / page without image
        self._put_xobjects()

        if self.fpdf._drawing_graphics_state_registry:
            self._put_graphics_state_refs()

        self._out(">>")
        self._out("endobj")

    def _put_xobjects(self):
        self._out("/XObject <<")
        img_ids = [
            (img_info["i"], img_info["n"])
            for img_info in self.fpdf.images.values()
            if img_info["usages"]
        ]
        img_ids.sort()
        for idx, n in img_ids:
            self._out(f"/I{idx} {pdf_ref(n)}")
        self._out(">>")

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

    def _put_catalog(self, sig_annotation_obj_id=None):
        fpdf = self.fpdf
        obj_id = self._newobj()
        self._out("<<")

        catalog_d = {
            "/Type": "/Catalog",
            # Pages is always the 1st object of the document, cf. _put_pages:
            "/Pages": pdf_ref(1),
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
                pdf_ref(3),  # reference to object ID of the 1st page
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
        assert (
            self._xmp_metadata_obj_id is not None
        ), "ID of XMP metadata PDF object must be known"
        if self._xmp_metadata_obj_id:
            catalog_d["/Metadata"] = pdf_ref(self._xmp_metadata_obj_id)
        assert (
            self._struct_tree_root_obj_id is not None
        ), "ID of root PDF object of the Structure Tree must be known"
        if self._struct_tree_root_obj_id:
            catalog_d["/MarkInfo"] = pdf_dict({"/Marked": "true"})
            catalog_d["/StructTreeRoot"] = pdf_ref(self._struct_tree_root_obj_id)
        assert (
            self._outlines_obj_id is not None
        ), "ID of Outlines PDF object must be known"
        if self._outlines_obj_id:
            catalog_d["/Outlines"] = pdf_ref(self._outlines_obj_id)
        assert (
            self._embedded_files_per_pdf_ref is not None
        ), "ID of Embedded files must be known"
        if self._embedded_files_per_pdf_ref:
            file_spec_names = [
                f"{enclose_in_parens(file.basename)} {file.file_spec(pdf_ref)}"
                for pdf_ref, file in self._embedded_files_per_pdf_ref.items()
            ]
            catalog_d["/Names"] = pdf_dict(
                {"/EmbeddedFiles": pdf_dict({"/Names": pdf_list(file_spec_names)})}
            )

        self._out(pdf_dict(catalog_d, open_dict="", close_dict=""))
        self._out(">>")
        self._out("endobj")
        return obj_id

    def _put_trailer(self, info_obj_id, catalog_obj_id, startxref):
        self._out("trailer")
        self._out("<<")
        self._out(f"/Size {self.n + 1}")
        self._out(f"/Root {pdf_ref(catalog_obj_id)}")
        self._out(f"/Info {pdf_ref(info_obj_id)}")
        file_id = self.fpdf.file_id(self.buffer, self.fpdf.creation_date)
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


def serialize_annot(annot, fpdf, embedded_files_per_pdf_ref=None):
    "Convert this object dictionnary to a string"
    rect = (
        f"{annot.x:.2f} {annot.y:.2f} "
        f"{annot.x + annot.width:.2f} {annot.y - annot.height:.2f}"
    )

    out = (
        f"<</Type /Annot /Subtype /{annot.type}"
        f" /Rect [{rect}] /Border [0 0 {annot.border_width}]"
    )

    if annot.field_type:
        out += f" /FT /{annot.field_type}"

    if annot.value:
        out += f" /V {annot.value.serialize()}"

    if annot.flags:
        out += f" /F {sum(annot.flags)}"

    if annot.contents:
        out += f" /Contents {enclose_in_parens(annot.contents)}"

    if annot.action:
        out += f" /A {annot.action.dict_as_string()}"

    if annot.link:
        if isinstance(annot.link, str):
            out += f" /A <</S /URI /URI {enclose_in_parens(annot.link)}>>"
        else:  # Dest type ending of annotation entry
            assert (
                annot.link in fpdf.links
            ), f"Link with an invalid index: {annot.link} (doc #links={len(fpdf.links)})"
            out += f" /Dest {fpdf.links[annot.link].as_str(fpdf)}"

    if annot.color:
        # pylint: disable=unsubscriptable-object
        out += f" /C [{annot.color[0]} {annot.color[1]} {annot.color[2]}]"

    if annot.title:
        out += f" /T ({escape_parens(annot.title)})"

    if annot.modification_time:
        out += f" /M {format_date(annot.modification_time)}"

    if annot.quad_points:
        # pylint: disable=not-an-iterable
        quad_points = pdf_list(f"{quad_point:.2f}" for quad_point in annot.quad_points)
        out += f" /QuadPoints {quad_points}"

    if annot.page:
        out += f" /P {pdf_ref(object_id_for_page(annot.page))}"

    if annot.name:
        out += f" /Name {annot.name.value.pdf_repr()}"

    if annot.ink_list:
        ink_list = pdf_list(f"{coord:.2f}" for coord in annot.ink_list)
        out += f" /InkList [{ink_list}]"

    if annot.embedded_file_name:
        # pylint: disable=protected-access
        assert (
            embedded_files_per_pdf_ref
        ), "_build_embedded_files_per_pdf_ref() must be called beforehand to know PDF IDs of /EmbeddedFile objects"
        embedded_file_ref, embedded_file = next(
            (file_ref, file)
            for file_ref, file in embedded_files_per_pdf_ref.items()
            if file.basename == annot.embedded_file_name
        )
        out += f" /FS {embedded_file.file_spec(embedded_file_ref)}"

    return out + ">>"


def _put_TT_font_widths(font, maxUni):
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
    return f"/W [{''.join(w)}]"


def _sizeof_fmt(num, suffix="B"):
    # Recipe from: https://stackoverflow.com/a/1094933/636849
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024
    return f"{num:.1f}Yi{suffix}"
