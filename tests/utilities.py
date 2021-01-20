import datetime as dt
import hashlib
import subprocess
import shutil
import warnings
from pathlib import Path

QPDF_AVAILABLE = bool(shutil.which("qpdf"))
if not QPDF_AVAILABLE:
    warnings.warn(
        "qpdf command not available on the $PATH, "
        "falling back to hash-based comparisons in tests"
    )


def assert_pdf_equal(pdf, expected_path, tmp_path):
    """
    This compare the output of a `FPDF` instance with the provided PDF file.

    The `CreationDate` of the newly generated PDF is fixed, so that it never
     triggers a diff.

    If the `qpdf` command is available on the `$PATH`, it will be used
    to perform the comparison, as it greatly helps debugging diffs.
    Otherwise, a hash-based comparison logic is used as a fallback.

    Args:
        pdf: instance of `FPDF`
        expected_path (Path): path to a PDF file matching the expected output
        tmp_path (Path): pytest's fixture for the current temporary directory
    """
    pdf.set_creation_date(dt.datetime.fromtimestamp(0, dt.timezone.utc))
    actual_path = tmp_path / f"pyfpdf-test-actual.pdf"
    pdf.output(actual_path.open("wb"))
    if QPDF_AVAILABLE:  # Favor qpdf-based comparison for better debugging:
        expected_lines = _qpdf(expected_path.read_bytes()).splitlines()
        actual_lines = _qpdf(actual_path.read_bytes()).splitlines()
        if actual_lines != expected_lines:
            expected_lines = list(subst_streams_with_hashes(expected_lines))
            actual_lines = list(subst_streams_with_hashes(actual_lines))
        assert actual_lines == expected_lines
    else:  # Fallback to hash comparison
        actual_hash = hashlib.md5(actual_path.read_bytes()).hexdigest()
        expected_hash = hashlib.md5(expected_path.read_bytes()).hexdigest()
        assert actual_hash == expected_hash


def _qpdf(pdf_data):
    """
    Processes the input pdf_data and returns the output.
    No files are written on disk.
    """
    proc = subprocess.Popen(
        ["qpdf", "--deterministic-id", "--qdf", "-", "-"],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.communicate(input=pdf_data)[0]


def subst_streams_with_hashes(in_lines):
    """
    This utility function reduce the length of `in_lines`, a list of bytes,
    by replacing multi-lines streams looking like this:

        stream
        {non-printable-binary-data}endstream

    by a single line with this format:

        <stream with MD5 hash: abcdef0123456789>

    and it yields each resulting line
    """
    stream = None
    for line in in_lines:
        if line == b"stream":
            assert stream is None
            stream = bytearray()
        elif stream == b"stream":
            # First line of stream, we check if it is binary or not:
            try:
                line.decode("latin-1")
            except UnicodeDecodeError:
                pass
            else:
                if b"\0" not in line:
                    # It's text! No need to compact stream
                    stream = None
        if stream is None:
            yield line
        else:
            stream += line
        if line.endswith(b"endstream") and stream:
            stream_hash = hashlib.md5(stream).hexdigest()
            yield f"<stream with MD5 hash: {stream_hash}>\n".encode()
            stream = None
