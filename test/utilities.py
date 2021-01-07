import hashlib
import inspect
import os
import pathlib
import shutil
import sys
import tempfile
import warnings
from datetime import datetime
from subprocess import check_call, check_output

from fpdf.template import Template


QPDF_AVAILABLE = bool(shutil.which("qpdf"))
if not QPDF_AVAILABLE:
    warnings.warn(
        "qpdf command not available on the $PATH, falling-back to hash-based comparisons in tests"
    )


class TempFile:
    """docstring for TempFile"""

    def __init__(self, name, handle):
        super(TempFile, self).__init__()
        self.name = name
        self.handle = handle

    def read_whole_file(self):
        while True:
            if not self.handle.read(10):
                break
        return self.handle.read()

    def rwf(self):
        return self.read_whole_file()

    def close(self):
        self.handle.close()


class TempFileCtx:
    """docstring for TempFileCtxs"""

    def __init__(self, prefix, delete, suffix):
        super(TempFileCtx, self).__init__()
        self.prefix = prefix
        self.delete = delete
        self.suffix = suffix

    def random(self):
        return os.urandom(24).hex()

    def get_os_tmp(self):
        return tempfile.gettempdir()

    def get_tmp_file_name_base(self):
        return self.prefix + self.random() + self.suffix

    def get_tmp_file_name(self):
        name = self.get_tmp_file_name_base()
        return os.path.join(self.get_os_tmp(), name)

    def __enter__(self):
        self.abs_name = self.get_tmp_file_name()
        pathlib.Path(self.abs_name).touch()
        tmp_file = TempFile(self.abs_name, open(self.abs_name, "rb"))
        self.tmp_file = tmp_file
        return tmp_file

    def __exit__(self, type, value, traceback):
        self.tmp_file.close()
        if self.delete:
            os.remove(self.abs_name)


def assert_pdf_equal(test, pdf_or_tmpl, rel_expected_pdf_filepath, delete=True):
    """
    Args:
        test (unittest.TestCase)
        pdf_or_tmpl: instance of `FPDF` or `Template`. The `output` or `render` method will be called on it.
        rel_expected_pdf_filepath (str): relative file path to a PDF file matching the expected output
        delete (bool): clean up temporary PDF files after performing test
    """
    if isinstance(pdf_or_tmpl, Template):
        pdf_or_tmpl.render()
        pdf = pdf_or_tmpl.pdf
    else:
        pdf = pdf_or_tmpl
    set_doc_date_0(pdf)  # Ensure PDFs CreationDate is always the same
    expected_pdf_filepath = relative_path_to(rel_expected_pdf_filepath, depth=2)
    with TempFileCtx(
        prefix="pyfpdf-test-", delete=delete, suffix="-actual.pdf"
    ) as actual_pdf_file:
        pdf.output(actual_pdf_file.name, "F")
        if not delete:
            print("Temporary file will not be deleted:", actual_pdf_file.name)
        if QPDF_AVAILABLE:  # Favor qpdf-based comparison, as it helps a lot debugging:
            with TempFileCtx(
                prefix="pyfpdf-test-", delete=delete, suffix="-actual-qpdf.pdf"
            ) as actual_qpdf_file, TempFileCtx(
                prefix="pyfpdf-test-", delete=delete, suffix="-expected-qpdf.pdf"
            ) as expected_qpdf_file:
                _qpdf(actual_pdf_file.name, actual_qpdf_file.name)
                _qpdf(expected_pdf_filepath, expected_qpdf_file.name)
                if not delete:
                    print(
                        "Temporary files will not be deleted:",
                        actual_qpdf_file.name,
                        expected_qpdf_file.name,
                    )
                test.assertSequenceEqual(
                    actual_qpdf_file.rwf(), expected_qpdf_file.rwf()
                )
        else:  # Fallback to hash comparison
            actual_hash = calculate_hash_of_file(actual_pdf_file.name)
            expected_hash = calculate_hash_of_file(expected_pdf_filepath)
            test.assertEqual(actual_hash, expected_hash)


def _qpdf(input_pdf_filepath, output_pdf_filepath):
    if sys.platform == "cygwin":
        # Lucas (2020/01/06) : this conversion of UNIX file paths to Windows ones is only needed
        # for my development environment: Cygwin, a UNIX system, with a qpdf Windows binary. Sorry for the kludge!
        input_pdf_filepath = (
            check_output(["cygpath", "-w", input_pdf_filepath]).decode().strip()
        )
        output_pdf_filepath = (
            check_output(["cygpath", "-w", output_pdf_filepath]).decode().strip()
        )
    check_call(
        ["qpdf", "--deterministic-id", input_pdf_filepath, output_pdf_filepath],
        stderr=sys.stderr,
        stdout=sys.stdout,
    )


def set_doc_date_0(doc):
    """
    Sets the document date to unix epoch start.
    Useful so that the generated PDFs CreationDate is always identical.
    """
    # 1969-12-31 19:00:00
    time_tuple = (1969, 12, 31, 19, 00, 00)
    doc.set_creation_date(datetime(*time_tuple))


def calculate_hash_of_file(full_path):
    """Finds md5 hash of a file given an abs path, reading in whole file."""
    with open(full_path, "rb") as file:
        data = file.read()
    return hashlib.md5(data).hexdigest()


def relative_path_to(place, depth=1):
    """Finds Relative Path to a place

    Works by getting the file of the caller module, then joining the directory
    of that absolute path and the place in the argument.
    """
    # pylint: disable=protected-access
    caller_file = inspect.getfile(sys._getframe(depth))
    return os.path.join(os.path.dirname(os.path.abspath(caller_file)), place)
