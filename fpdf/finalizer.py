import logging
from contextlib import contextmanager

from .syntax import iobj_ref as pdf_ref
from .util import object_id_for_page


LOGGER = logging.getLogger(__name__)


class OutputProducer:
    """
    Generates the final bytearray representing the PDF document,
    based on a FPDF intance.
    """

    def __init__(self, fpdf):
        self.fpdf = fpdf
        self.buffer = bytearray()  # resulting output buffer
        # array of PDF object offsets in self.buffer, used to build the xref table:
        self.offsets = {}
        self.n = 2  # current PDF object number
        self._embedded_files_per_pdf_ref = None

    def bufferize(self):
        # * PDF object 1 is always the pages root
        # * PDF object 2 is always the resources dictionary
        # Those objects are not inserted first in the document though
        LOGGER.debug("Final doc sections size summary:")
        with self._trace_size("header"):
            self._out(f"%PDF-{self.fpdf._final_pdf_version()}")
        self._build_embedded_files_per_pdf_ref()
        return self.buffer

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
