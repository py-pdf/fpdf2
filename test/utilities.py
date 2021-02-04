import datetime as dt
import hashlib
import pathlib
import subprocess
import shutil
import warnings

from fpdf.template import Template

QPDF_AVAILABLE = bool(shutil.which("qpdf"))
if not QPDF_AVAILABLE:
    warnings.warn(
        "qpdf command not available on the $PATH, falling back to hash-based "
        "comparisons in tests"
    )


def assert_pdf_equal(actual, expected, tmp_path, generate=False):
    """
    This compare the output of a `FPDF` instance (or `Template` instance),
    with the provided PDF file.

    The `CreationDate` of the newly generated PDF is fixed, so that it never triggers
    a diff.

    If the `qpdf` command is available on the `$PATH`, it will be used to perform the
    comparison, as it greatly helps debugging diffs. Otherwise, a hash-based comparison
    logic is used as a fallback.

    Args:
        actual: instance of `FPDF` or `Template`. The `output` or `render` method
          will be called on it.
        expected: instance of `FPDF`, `bytearray` or file path to a PDF file
          matching the expected output
        tmp_path (Path): temporary directory provided by pytest individually to the
          caller test function
        generate (bool): only generate `pdf` output to `rel_expected_pdf_filepath`
          and return. Useful to create new tests.
    """
    if isinstance(actual, Template):
        actual.render()
        actual_pdf = actual.pdf
    else:
        actual_pdf = actual
    actual_pdf.set_creation_date(dt.datetime.fromtimestamp(0, dt.timezone.utc))
    if generate:
        assert isinstance(expected, pathlib.Path), (
            "When passing `True` to `generate`"
            "a pathlib.Path must be provided as the `expected` parameter"
        )
        actual_pdf.output(expected.open("wb"))
        return
    if not isinstance(expected, (bytes, bytearray)):
        # Convert FPDF instance or file path to bytes:
        if isinstance(expected, pathlib.Path):
            expected_pdf_path = expected
        else:
            expected_pdf_path = tmp_path / "expected.pdf"
            expected.output(expected_pdf_path.open("wb"))
        expected = expected_pdf_path.read_bytes()
    actual_pdf_path = tmp_path / "actual.pdf"
    actual_pdf.output(actual_pdf_path.open("wb"))
    if QPDF_AVAILABLE:  # Favor qpdf-based comparison, as it helps a lot debugging:
        actual_qpdf = _qpdf(actual_pdf_path.read_bytes())
        expected_qpdf = _qpdf(expected)
        (tmp_path / "actual_qpdf.pdf").write_bytes(actual_qpdf)
        (tmp_path / "expected_qpdf.pdf").write_bytes(expected_qpdf)
        actual_lines = actual_qpdf.splitlines()
        expected_lines = expected_qpdf.splitlines()
        if actual_lines != expected_lines:
            expected_lines = subst_streams_with_hashes(expected_lines)
            actual_lines = subst_streams_with_hashes(actual_lines)
        assert actual_lines == expected_lines
    else:  # Fallback to hash comparison
        actual_hash = hashlib.md5(actual_pdf_path.read_bytes()).hexdigest()
        expected_hash = hashlib.md5(expected_pdf_path.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, f"{actual_hash} != {expected_hash}"


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
            stream_hash = hashlib.md5(stream).hexdigest()
            out_lines.append(f"<stream with MD5 hash: {stream_hash}>\n".encode())
            stream = None
    return out_lines


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
