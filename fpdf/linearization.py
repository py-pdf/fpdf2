# pylint: disable=fixme,protected-access
"""
This module is in work-in-progress state.
Hint tables / hint streams have not been implemented yet,
and there are a few "TODO" comment remaining.
cf. https://github.com/py-pdf/fpdf2/issues/62
"""
from .output import ContentWithoutID, OutputProducer, PDFHeader
from .sign import sign_content
from .syntax import PDFArray, PDFContentStream, PDFObject
from .syntax import iobj_ref as pdf_ref
from .util import buffer_subst

try:
    from endesive import signer
except ImportError:
    signer = None

HINT_STREAM_OFFSET_LENGTH_PLACEHOLDER = "0%1%2%3%4%5%6%7%8%9%a%b%c%d"
FIRST_PAGE_END_OFFSET_PLACEHOLDER = "1%2%3%4%5%6%"
MAIN_XREF_1ST_ENTRY_OFFSET_PLACEHOLDER = "2%3%4%5%6%7%"
FILE_LENGTH_PLACEHOLDER = "3%4%5%6%7%8%"


class PDFLinearization(PDFObject):
    def __init__(self, pages_count):
        super().__init__()
        self.linearized = "1"  # Version
        self.n = pages_count
        # Primary hint stream offset and length (part 5):
        self.h = HINT_STREAM_OFFSET_LENGTH_PLACEHOLDER
        self.o = None  # Object number of first page’s page object (part 6)
        self.e = FIRST_PAGE_END_OFFSET_PLACEHOLDER  # Offset of end of first page
        # Offset of first entry in main cross-reference table (part 11):
        self.t = MAIN_XREF_1ST_ENTRY_OFFSET_PLACEHOLDER
        self.l = FILE_LENGTH_PLACEHOLDER  # The length of the entire file in bytes


class PDFXrefAndTrailer(ContentWithoutID):
    PREV_MAIN_XREF_START_PLACEHOLDER = "0%1*2+3-2/1^"

    def __init__(self, output_builder):
        self.output_builder = output_builder
        self.count = output_builder.obj_id + 1
        self.start_obj_id = 1
        # Must be set before the call to serialize():
        self.catalog_obj = None
        self.info_obj = None
        self.first_xref = None
        self.main_xref = None
        # Computed at serialize() time based on output_builder.buffer size:
        self.startxref = None

    @property
    def is_first_xref(self):
        return bool(self.main_xref)

    @property
    def is_main_xref(self):
        return bool(self.first_xref)

    def serialize(self, _security_handler=None):
        builder = self.output_builder
        out = []
        self.startxref = str(len(builder.buffer))
        if self.is_main_xref:
            builder.buffer = buffer_subst(
                builder.buffer,
                self.PREV_MAIN_XREF_START_PLACEHOLDER,
                self.startxref.rjust(12, " "),
            )
        out.append("xref")
        out.append(f"{0 if self.start_obj_id == 1 else self.start_obj_id} {self.count}")
        if not self.is_first_xref:
            out.append("0000000000 65535 f ")
        assert (
            len(builder.offsets) > 1
        ), "TODO: how to know the offsets in the 1st xref at this stage?"
        for obj_id in range(self.start_obj_id, self.start_obj_id + self.count):
            out.append(f"{builder.offsets[obj_id]:010} 00000 n ")
        out.append("trailer")
        out.append("<<")
        if self.is_main_xref:
            out.append(f"/Size {self.count - self.first_xref.count}")
        else:
            if self.is_first_xref:
                out.append(f"/Size {self.main_xref.count}")
                out.append(f"/Prev {self.PREV_MAIN_XREF_START_PLACEHOLDER}")
            else:
                out.append(f"/Size {self.count}")
            out.append(f"/Root {pdf_ref(self.catalog_obj.id)}")
            out.append(f"/Info {pdf_ref(self.info_obj.id)}")
            fpdf = builder.fpdf
            file_id = fpdf.file_id()
            if file_id == -1:
                file_id = fpdf._default_file_id(builder.buffer)
            if file_id:
                out.append(f"/ID [{file_id}]")
        out.append(">>")
        out.append("startxref")
        startxref = self.startxref
        if self.is_main_xref:
            startxref = self.first_xref.startxref
        if self.is_first_xref:
            startxref = "0"
        out.append(startxref)
        out.append("%%EOF")
        return "\n".join(out)


class PDFHintStream(PDFContentStream):
    def __init__(self, contents, compress=False):
        super().__init__(contents=contents, compress=compress)
        self.s = None  # (Required) Shared object hint table
        self.t = None  # (Present only if thumbnail images exist) Thumbnail hint table
        self.o = None  # (Present only if a document outline exists) Outline hint table
        self.a = None  # (Present only if article threads exist) Thread information hint table
        self.e = None  # (Present only if named destinations exist) Named destination hint table
        self.v = None  # (Present only if an interactive form dictionary exists) Interactive form hint table
        self.i = None  # (Present only if a document information dictionary exists) Information dictionary hint table
        self.c = None  # (Present only if a logical structure hierarchy exists; PDF 1.3) Logical structure hint table
        self.l = None  # (PDF 1.3) Page label hint table
        self.r = None  # (Present only if a renditions name tree exists; PDF 1.5) Renditions name tree hint table
        self.b = None  # (Present only if embedded file streams exist; PDF 1.5) Embedded file stream hint table


class LinearizedOutputProducer(OutputProducer):
    def bufferize(self):
        fpdf = self.fpdf

        # 1. Setup - Insert all PDF objects
        #    (in the order required to build a linearized PDF),
        #    and assign unique consecutive numeric IDs to all of them

        # Part 1: Header
        self.pdf_objs.append(PDFHeader(fpdf.pdf_version))
        # Part 2: Linearization parameter dictionary
        linearization_obj = PDFLinearization(fpdf.pages_count)
        self._add_pdf_obj(linearization_obj)
        # Part 3: First-page cross-reference table and trailer
        first_xref = PDFXrefAndTrailer(self)
        self.pdf_objs.append(first_xref)
        # Part 4: Document catalogue and other required document-level objects
        catalog_obj = self._add_catalog()
        # Part 5: Primary hint stream (may precede or follow part 6)
        hint_stream_obj = PDFHintStream("")  # TODO
        self.pdf_objs.append(hint_stream_obj)
        # Part 6: First-page section (may precede or follow part 5)
        page_objs = self._add_pages(slice(0, 1))
        # The following objects shall be contained in the first-page section:
        #   + This page object shall explicitly specify all required attributes, e.g. Resources, MediaBox
        #   + The entire outline hierarchy, if the PageMode entry in the catalogue is UseOutlines
        #   + All objects that the page object refers to [including] Contents, Resources, Annots
        # TODO

        first_xref.count = self.obj_id + 1
        first_xref_pdf_objs = list(self.pdf_objs)
        self.obj_id = 0

        # Part 7: Remaining pages
        page_objs.extend(self._add_pages(slice(1, None)))
        # Part 8: Shared objects for all pages except the first
        # = resources, that are referenced from more than one page but [not] from the first page
        pages_root_obj = self._add_pages_root()
        sig_annotation_obj = self._add_annotations_as_objects()
        font_objs_per_index = self._add_fonts()
        img_objs_per_index = self._add_images()
        gfxstate_objs_per_name = self._add_gfxstates()
        shading_objs_per_name = self._add_shadings()
        pattern_objs_per_name = self._add_patterns()
        resources_dict_obj = self._add_resources_dict(
            font_objs_per_index,
            img_objs_per_index,
            gfxstate_objs_per_name,
            shading_objs_per_name,
            pattern_objs_per_name,
        )
        # Part 9: Objects not associated with pages, if any
        for embedded_file in fpdf.embedded_files:
            self._add_pdf_obj(embedded_file, "embedded_files")
        struct_tree_root_obj = self._add_structure_tree()
        outline_dict_obj, outline_items = self._add_document_outline()
        xmp_metadata_obj = self._add_xmp_metadata()
        info_obj = self._add_info()
        # Part 11: Main cross-reference table and trailer
        main_xref = PDFXrefAndTrailer(self)
        self.pdf_objs.append(main_xref)

        # Re-assigning IDs of all PDF objects in the 1st xref table:
        first_xref.start_obj_id = self.obj_id + 1
        for pdf_obj in first_xref_pdf_objs:
            if (
                not isinstance(pdf_obj, ContentWithoutID)
                and pdf_obj is not hint_stream_obj
            ):
                self.obj_id += 1
                pdf_obj.obj_id = self.obj_id
        # The hint streams shall be assigned the last object numbers in the file:
        self.obj_id += 1
        hint_stream_obj.id = self.obj_id

        # 2. Plumbing - Inject all PDF object references required:
        linearization_obj.o = page_objs[0].id
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
            page_obj.resources = resources_dict_obj
            for annot in page_obj.annots:
                if annot.dest:
                    dests.append(annot.dest)
                if annot.a and hasattr(annot.a, "dest"):
                    dests.append(annot.a.dest)
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
        main_xref.first_xref = first_xref
        first_xref.main_xref = main_xref
        for xref in [main_xref, first_xref]:
            xref.catalog_obj = catalog_obj
            xref.info_obj = info_obj

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
                    self._out(pdf_obj.serialize())
            else:
                self._out(pdf_obj.serialize())
        self._log_final_sections_sizes()

        # Now that the file size & all the offsets are known,
        # substitute the values of the Linearization properties:
        hs1_offset = self.offsets[hint_stream_obj.id]
        hs1_length = len(hint_stream_obj.serialize())
        self.buffer = buffer_subst(
            self.buffer,
            HINT_STREAM_OFFSET_LENGTH_PLACEHOLDER,
            f"[{hs1_offset: 12d} {hs1_length: 12d}]",
        )
        self.buffer = buffer_subst(
            self.buffer,
            FIRST_PAGE_END_OFFSET_PLACEHOLDER,
            f"{self.offsets[page_objs[0].id + 1]: 12d}",
        )
        self.buffer = buffer_subst(
            self.buffer,
            MAIN_XREF_1ST_ENTRY_OFFSET_PLACEHOLDER,
            f"{self.offsets[main_xref.start_obj_id]: 12d}",
        )
        self.buffer = buffer_subst(
            self.buffer,
            FILE_LENGTH_PLACEHOLDER,
            f"{len(self.buffer): 12d}",
        )

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
