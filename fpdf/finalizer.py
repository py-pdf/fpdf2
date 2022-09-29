# pylint: disable=protected-access
import hashlib, logging, zlib
from contextlib import contextmanager

from .sign import Signature
from .syntax import create_dictionary_string as pdf_dict
from .syntax import create_stream as pdf_stream
from .syntax import iobj_ref as pdf_ref
from .util import format_date, object_id_for_page


LOGGER = logging.getLogger(__name__)


class OutputProducer:
    "Generates the final bytearray representing the PDF document, based on a FPDF instance."

    def __init__(self, fpdf):
        self.fpdf = fpdf
        self.buffer = bytearray()  # resulting output buffer
        # array of PDF object offsets in self.buffer, used to build the xref table:
        self.offsets = {}
        self.n = 2  # current PDF object number
        self._embedded_files_per_pdf_ref = None

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
        with self._trace_size("header"):
            self._out(f"%PDF-{self.fpdf._final_pdf_version()}")
        self._build_embedded_files_per_pdf_ref()
        # It is important that pages are the first PDF objects inserted in the document,
        # followed immediately by annotations: some parts of fpdf2 currently rely on that
        # order of insertion (e.g. util.object_id_for_page):
        with self._trace_size("pages"):
            self._putpages()
        with self._trace_size("annotations_objects"):
            sig_annotation_obj_id = self._put_annotations_as_objects()
        with self._trace_size("embedded_files"):
            self._put_embedded_files()
        return self.buffer, sig_annotation_obj_id

    def _out(self, s):
        if not isinstance(s, bytes):
            if not isinstance(s, str):
                s = str(s)
            s = s.encode("latin1")
        self.buffer += s + b"\n"

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

    def _putpages(self):
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
                annots += annot.serialize(fpdf, self._embedded_files_per_pdf_ref)
                if annot.quad_points:
                    # This won't alter the PDF header, that has already been rendered,
                    # but can trigger the insertion of a /Page /Group by _putpages:
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
                self._out(annot.serialize(fpdf, self._embedded_files_per_pdf_ref))
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

    def _newobj(self):
        "Begin a new PDF object"
        self.n += 1
        self.offsets[self.n] = len(self.buffer)
        self._out(f"{self.n} 0 obj")
        return self.n

    @contextmanager
    def _trace_size(self, label):
        prev_size = len(self.buffer)
        yield
        LOGGER.debug("- %s.size: %s", label, _sizeof_fmt(len(self.buffer) - prev_size))


def _sizeof_fmt(num, suffix="B"):
    # Recipe from: https://stackoverflow.com/a/1094933/636849
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024
    return f"{num:.1f}Yi{suffix}"
