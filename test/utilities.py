import hashlib
import inspect
import os
import shutil
import sys
import warnings
from binascii import hexlify
from contextlib import contextmanager
from datetime import datetime
from subprocess import check_call, check_output
from tempfile import NamedTemporaryFile

from fpdf.template import Template

QPDF_AVAILABLE = bool(shutil.which("qpdf"))
if not QPDF_AVAILABLE:
    warnings.warn(
        "qpdf command not available on the $PATH, falling back to hash-based comparisons in tests"
    )


def assert_pdf_equal(
    test, pdf_or_tmpl, rel_expected_pdf_filepath, delete=True, generate=False
):
    """
    This compare the output of a `FPDF` instance (or `Template` instance),
    with the provided PDF file.

    The `CreationDate` of the newly generated PDF is fixed, so that it never triggers a diff.

    If the `qpdf` command is available on the `$PATH`, it will be used to perform the comparison,
    as it greatly helps debugging diffs. Otherwise, a hash-based comparison logic is used as a fallback.

    Args:
        test (unittest.TestCase)
        pdf_or_tmpl: instance of `FPDF` or `Template`. The `output` or `render` method will be called on it.
        rel_expected_pdf_filepath (str): relative file path to a PDF file matching the expected output
        delete (bool): clean up temporary PDF files after performing test
        generate (bool): only generate `pdf` output to `rel_expected_pdf_filepath` and return. Useful to create new tests.
    """
    if isinstance(pdf_or_tmpl, Template):
        pdf_or_tmpl.render()
        pdf = pdf_or_tmpl.pdf
    else:
        pdf = pdf_or_tmpl
    set_doc_date_0(pdf)
    expected_pdf_filepath = relative_path_to(rel_expected_pdf_filepath, depth=2)
    if generate:
        pdf.output(expected_pdf_filepath)
        return
    with tmp_file(
        prefix="pyfpdf-test-", delete=delete, suffix="-actual.pdf"
    ) as actual_pdf_file:
        pdf.output(actual_pdf_file.name)
        if not delete:
            print("Temporary file will not be deleted:", actual_pdf_file.name)
        if QPDF_AVAILABLE:  # Favor qpdf-based comparison, as it helps a lot debugging:
            with tmp_file(
                prefix="pyfpdf-test-", delete=delete, suffix="-actual-qpdf.pdf"
            ) as actual_qpdf_file, tmp_file(
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
                expected_lines = expected_qpdf_file.read().splitlines()
                actual_lines = actual_qpdf_file.read().splitlines()
                if actual_lines == expected_lines:
                    test.assertTrue(actual_lines == expected_lines)
                    return
                # It is very important to reduce the size of both list of bytes here,
                # or the call to .assertEqual will take forever to finish.
                # Under the hood it calls .assertSequenceEqual, that itself calls difflib.ndiff,
                # that has cubic complexity from this comment by Tim Peters: https://bugs.python.org/issue6931#msg223459
                expected_lines = subst_streams_with_hashes(expected_lines)
                actual_lines = subst_streams_with_hashes(actual_lines)
                test.assertEqual(actual_lines, expected_lines)
        else:  # Fallback to hash comparison
            actual_hash = calculate_hash_of_file(actual_pdf_file.name)
            expected_hash = calculate_hash_of_file(expected_pdf_filepath)
            test.assertEqual(actual_hash, expected_hash)


def subst_streams_with_hashes(in_lines):
    """
    This utility function reduce the length of `in_lines`, a list of bytes,
    by replacing multi-lines streams looking like this:

        stream
        {non-printable-binary-data}endstream

    by a single line with this format:

        <stream with MD5 hash: abcdef0123456789>
    """
    out_lines, stream = [], None
    for line in in_lines:
        if line == b"stream":
            assert stream is None
            stream = bytearray()
        elif stream == b"stream":
            # First line of stream, we check if it is binary or not:
            try:
                line.decode("latin-1")
                if b"\0" not in line:
                    # It's text! No need to compact stream
                    stream = None
            except UnicodeDecodeError:
                pass
        if stream is None:
            out_lines.append(line)
        else:
            stream += line
        if line.endswith(b"endstream") and stream:
            stream_hash = hashlib.md5(stream).digest()
            out_lines.append(b"<stream with MD5 hash: " + hexlify(stream_hash) + b">\n")
            stream = None
    return out_lines


@contextmanager
def tmp_file(*args, delete=True, **kwargs):
    # Always passing delete=False to NamedTemporaryFile in order to avoid permission errors on Windows:
    with NamedTemporaryFile(*args, delete=False, **kwargs) as ntf:
        try:
            yield ntf
        finally:
            if delete:
                ntf.close()
                os.remove(ntf.name)


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
        [
            "qpdf",
            "--deterministic-id",
            "--qdf",
            input_pdf_filepath,
            output_pdf_filepath,
        ],
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
    return os.path.abspath(os.path.join(os.path.dirname(caller_file), place))
