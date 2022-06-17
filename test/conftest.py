import datetime as dt
import hashlib
import pathlib
import shutil
import sys
import warnings
from subprocess import check_output, CalledProcessError, PIPE

from fpdf.template import Template

QPDF_AVAILABLE = bool(shutil.which("qpdf"))
if not QPDF_AVAILABLE:
    warnings.warn(
        "qpdf command not available on the $PATH, falling back to hash-based "
        "comparisons in tests"
    )

EPOCH = dt.datetime(1969, 12, 31, 19, 00, 00)

LOREM_IPSUM = (
    "Lorem ipsum Ut nostrud irure reprehenderit anim nostrud dolore sed "
    "ut Excepteur dolore ut sunt irure consectetur tempor eu tempor "
    "nostrud dolore sint exercitation aliquip velit ullamco esse dolore "
    "mollit ea sed voluptate commodo amet eiusmod incididunt Excepteur "
    "Excepteur officia est ea dolore sed id in cillum incididunt quis ex "
    "id aliqua ullamco reprehenderit cupidatat in quis pariatur ex et "
    "veniam consectetur et minim minim nulla ea in quis Ut in "
    "consectetur cillum aliquip pariatur qui quis sint reprehenderit "
    "anim incididunt laborum dolor dolor est dolor fugiat ut officia do "
    "dolore deserunt nulla voluptate officia mollit elit consequat ad "
    "aliquip non nulla dolor nisi magna consectetur anim sint officia "
    "sit tempor anim do laboris ea culpa eu veniam sed cupidatat in anim "
    "fugiat culpa enim Ut cillum in exercitation magna nostrud aute "
    "proident laboris est ullamco nulla occaecat nulla proident "
    "consequat in ut labore non sit id cillum ut ea quis est ut dolore "
    "nisi aliquip aute pariatur ullamco ut cillum Duis nisi elit sit "
    "cupidatat do Ut aliqua irure sunt sunt proident sit aliqua in "
    "dolore Ut in sint sunt exercitation aliquip elit velit dolor nisi "
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
    if (
        actual_pdf.creation_date is True
    ):  # default value, meaning we are not testing .creation_date behaviour:
        actual_pdf.set_creation_date(EPOCH)
    if generate:
        assert isinstance(expected, pathlib.Path), (
            "When passing `True` to `generate`"
            "a pathlib.Path must be provided as the `expected` parameter"
        )
        actual_pdf.output(expected.open("wb"))
        return
    if isinstance(expected, pathlib.Path):
        expected_pdf_path = expected
    else:
        expected_pdf_path = tmp_path / "expected.pdf"
        with expected_pdf_path.open("wb") as pdf_file:
            if isinstance(expected, (bytes, bytearray)):
                pdf_file.write(expected)
            else:
                expected.set_creation_date(EPOCH)
                expected.output(pdf_file)
    actual_pdf_path = tmp_path / "actual.pdf"
    with actual_pdf_path.open("wb") as pdf_file:
        actual_pdf.output(pdf_file)
    if QPDF_AVAILABLE:  # Favor qpdf-based comparison, as it helps a lot debugging:
        actual_qpdf = _qpdf(actual_pdf_path)
        expected_qpdf = _qpdf(expected_pdf_path)
        (tmp_path / "actual_qpdf.pdf").write_bytes(actual_qpdf)
        (tmp_path / "expected_qpdf.pdf").write_bytes(expected_qpdf)
        actual_lines = actual_qpdf.splitlines()
        expected_lines = expected_qpdf.splitlines()
        if actual_lines != expected_lines:
            # It is important to reduce the size of both list of bytes here,
            # to avoid .assertSequenceEqual to take forever to finish, that itself calls difflib.ndiff,
            # that has cubic complexity from this comment by Tim Peters: https://bugs.python.org/issue6931#msg223459
            actual_lines = subst_streams_with_hashes(actual_lines)
            expected_lines = subst_streams_with_hashes(expected_lines)
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
                if not (b"\0" in line or b"\xff" in line):
                    # It's likely to be text! No need to compact stream
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


def _qpdf(input_pdf_filepath):
    if sys.platform == "cygwin":
        # Lucas (2021/01/06) : this conversion of UNIX file paths to Windows ones is only needed
        # for my development environment: Cygwin, a UNIX system, with a qpdf Windows binary. Sorry for the kludge!
        input_pdf_filepath = (
            check_output(["cygpath", "-w", str(input_pdf_filepath)]).decode().strip()
        )
    try:
        return check_output(
            ["qpdf", "--deterministic-id", "--qdf", str(input_pdf_filepath), "-"],
            stderr=PIPE,
        )
    except CalledProcessError as error:
        print(f"\nqpdf STDERR: {error.stderr.decode().strip()}")
        raise
