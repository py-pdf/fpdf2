# pylint: disable=import-outside-toplevel
from contextlib import contextmanager
from datetime import datetime, timezone
from time import perf_counter
from timeit import timeit
from types import SimpleNamespace
import functools
import gc
import hashlib
import linecache
import os
import pathlib
import shutil
import tracemalloc
import warnings

from subprocess import check_output, CalledProcessError, PIPE

import pytest

from fpdf.util import get_process_rss_as_mib, print_mem_usage
from fpdf.template import Template

QPDF_AVAILABLE = bool(shutil.which("qpdf"))
if not QPDF_AVAILABLE:
    warnings.warn(
        # pylint: disable=implicit-str-concat
        "qpdf command not available on the $PATH, falling back to hash-based "
        "comparisons in tests"
    )

EPOCH = datetime(1969, 12, 31, 19, 00, 00).replace(tzinfo=timezone.utc)

LOREM_IPSUM = (
    # pylint: disable=implicit-str-concat
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


def assert_pdf_equal(
    actual,
    expected,
    tmp_path,
    linearize=False,
    at_epoch=True,
    generate=False,
    ignore_id_changes=False,
    ignore_original_obj_ids=False,
    ignore_xref_offets=False,
):
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
    if at_epoch:
        actual_pdf.creation_date = EPOCH
    if generate:
        assert isinstance(expected, pathlib.Path), (
            "When passing `True` to `generate`"
            "a pathlib.Path must be provided as the `expected` parameter"
        )
        actual_pdf.output(expected.open("wb"), linearize=linearize)
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
                expected.output(pdf_file, linearize=linearize)
    actual_pdf_path = tmp_path / "actual.pdf"
    with actual_pdf_path.open("wb") as pdf_file:
        actual_pdf.output(pdf_file, linearize=linearize)
    if QPDF_AVAILABLE:  # Favor qpdf-based comparison, as it helps a lot debugging:
        actual_qpdf = _qpdf(actual_pdf_path)
        expected_qpdf = _qpdf(expected_pdf_path)
        (tmp_path / "actual_qpdf.pdf").write_bytes(actual_qpdf)
        (tmp_path / "expected_qpdf.pdf").write_bytes(expected_qpdf)
        actual_lines = actual_qpdf.splitlines()
        expected_lines = expected_qpdf.splitlines()
        if ignore_id_changes:
            actual_lines = filter_out_doc_id(actual_lines)
            expected_lines = filter_out_doc_id(expected_lines)
        if ignore_original_obj_ids:
            actual_lines = filter_out_original_obj_ids(actual_lines)
            expected_lines = filter_out_original_obj_ids(expected_lines)
        if ignore_xref_offets:
            actual_lines = filter_out_xref_offets(actual_lines)
            expected_lines = filter_out_xref_offets(expected_lines)
        if actual_lines != expected_lines:
            # It is important to reduce the size of both list of bytes here,
            # to avoid .assertSequenceEqual to take forever to finish, that itself calls difflib.ndiff,
            # that has cubic complexity from this comment by Tim Peters: https://bugs.python.org/issue6931#msg223459
            actual_lines = subst_streams_with_hashes(actual_lines)
            expected_lines = subst_streams_with_hashes(expected_lines)
        assert actual_lines == expected_lines
        if linearize:
            _run_cmd("qpdf", "--check-linearization", str(actual_pdf_path))
    else:  # Fallback to hash comparison
        actual_hash = hashlib.md5(actual_pdf_path.read_bytes()).hexdigest()
        expected_hash = hashlib.md5(expected_pdf_path.read_bytes()).hexdigest()

        # trick to open both files in explorer if they are different
        # if actual_hash != expected_hash:
        #     # open both
        #     import subprocess
        #     subprocess.Popen(f'explorer "{actual_pdf_path}"')
        #     subprocess.Popen(f'explorer "{expected_pdf_path}"')

        assert actual_hash == expected_hash, f"{actual_hash} != {expected_hash}"


def filter_out_doc_id(lines):
    return [line for line in lines if not line.startswith(b"  /ID [<")]


def filter_out_original_obj_ids(lines):
    return [line for line in lines if not line.startswith(b"%% Original object ID: ")]


def filter_out_xref_offets(lines):
    return [line for line in lines if not line.endswith(b" 00000 n ")]


def check_signature(pdf, trusted_cert_paths, linearize=False):
    # pylint: disable=import-outside-toplevel
    from endesive import pdf as endesive_pdf

    trusted_certs = []
    for cert_filepath in trusted_cert_paths:
        with open(cert_filepath, "rb") as cert_file:
            trusted_certs.append(cert_file.read())
    results = endesive_pdf.verify(pdf.output(linearize=linearize), trusted_certs)
    for hash_ok, signature_ok, cert_ok in results:
        assert signature_ok
        assert hash_ok
        assert cert_ok


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
    return _run_cmd(
        "qpdf",
        "--deterministic-id",
        "--password=fpdf2",
        "--qdf",
        str(input_pdf_filepath),
        "-",
    )


def _run_cmd(*args):
    try:
        return check_output(args, stderr=PIPE)
    except CalledProcessError as error:
        print(f"\nqpdf STDERR: {error.stderr.decode().strip()}")
        raise


@contextmanager
def time_execution():
    """
    Usage:

        with time_execution() as duration:
            ...
        assert duration.seconds < 10
    """
    ctx = SimpleNamespace()
    start = perf_counter()
    yield ctx
    ctx.seconds = perf_counter() - start


def ensure_exec_time_below(seconds, repeats=10):
    """
    Unit test decorator using the standard timeit module
    to check that average duration of the target test
    does not get over the limit provided.

    Those checks are only enabled if $CHECK_EXEC_TIME is set.

    This decorator replaced pytest-timeout, and is a better fit:
    * because it allows to know how much above the threshold the test ran
    * because it does not cause a global PyTest interruption
    * because it computes an average, and is hence more stable
    """

    def actual_decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            def func_with_args():
                test_func(*args, **kwargs)

            if not os.environ.get("CHECK_EXEC_TIME"):
                func_with_args()
                return

            total_elapsed_in_secs = timeit(func_with_args, number=repeats)
            # Compute average:
            avg_duration_in_secs = total_elapsed_in_secs / repeats
            assert avg_duration_in_secs < seconds

        return wrapper

    return actual_decorator


def ensure_rss_memory_below(mib):
    """
    Ensure there is no unexpected / significant increase between
    the process RSS memory BEFORE executing the test, and AFTER.

    Those checks are only enabled if $CHECK_RSS_MEMORY is set.

    This decorator replaced memunit, and is a better fit:
    * because it takes in consideration a difference of RSS values,
      not an absolute memory amount, and hence better checks
      the memory usage of a single test, with more isolation to other tests
    * because it does not suffer from some memory_profiler issues:
        + https://github.com/py-pdf/fpdf2/issues/641#issuecomment-1465730884
        + hanging MemTimer child process sometimes preventing PyTest finalization,
          blocking in multiprocessing.util._exit_function() :
          https://github.com/python/cpython/blob/3.11/Lib/multiprocessing/util.py#L355

    Sadly, we cannot use the same approach as ensure_exec_time_below()
    of using averages, as RSS measures are made on the same process and are not independent.
    """

    def actual_decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            if not os.environ.get("CHECK_RSS_MEMORY"):
                test_func(*args, **kwargs)
                return
            start_rss_in_mib = get_process_rss_as_mib()
            test_func(*args, **kwargs)
            if not start_rss_in_mib:
                return  # not available under Windows
            end_rss_in_mib = get_process_rss_as_mib()
            assert end_rss_in_mib - start_rss_in_mib < mib

        return wrapper

    return actual_decorator


# Enabling this check creates an increase in memory usage,
# so we require an opt-in through a CLI argument:
def pytest_addoption(parser):
    parser.addoption(
        "--trace-memory-usage",
        action="store_true",
        help="Trace the memory usage during tests execution",
    )
    parser.addoption(
        "--pympler-summary",
        action="store_true",
        help="At the end of the tests execution, display a summary of objects allocated in memory",
    )
    parser.addoption(
        "--trace-malloc",
        action="store_true",
        help="Trace main memory allocations differences during the whole execution",
    )


@pytest.fixture(scope="module", autouse=True)
def module_memory_usage(request):
    start_rss_in_mib = None
    if request.config.getoption("trace_memory_usage"):
        start_rss_in_mib = get_process_rss_as_mib()
    yield
    if not start_rss_in_mib:
        return  # not available under Windows
    gc.collect()
    end_rss_in_mib = get_process_rss_as_mib()
    sign = "+" if end_rss_in_mib > start_rss_in_mib else ""
    capmanager = request.config.pluginmanager.getplugin("capturemanager")
    with capmanager.global_and_fixture_disabled():
        print("\n")
        print(
            f"Memory bump for {request.node.name.split('/')[-1]}: {sign}{end_rss_in_mib-start_rss_in_mib:.1f} MiB"
        )


@pytest.fixture(scope="session", autouse=True)
def final_memory_usage(request):
    yield
    if request.config.getoption("trace_memory_usage"):
        gc.collect()
        capmanager = request.config.pluginmanager.getplugin("capturemanager")
        with capmanager.global_and_fixture_disabled():
            print("\n")
            print_mem_usage("Final memory usage:")


@pytest.fixture(scope="session", autouse=True)
def pympler_summary(request):
    yield
    if request.config.getoption("pympler_summary"):
        # pylint: disable=import-error
        from pympler.muppy import get_objects
        from pympler.summary import print_, summarize

        gc.collect()
        all_objects = get_objects()
        capmanager = request.config.pluginmanager.getplugin("capturemanager")
        with capmanager.global_and_fixture_disabled():
            print("\n[pympler/muppy] biggest objects summary:")
            print_(summarize(all_objects))


@pytest.fixture(scope="session", autouse=True)
def trace_malloc(request):
    if not request.config.getoption("trace_malloc"):
        yield
        return
    gc.collect()
    # Top-10 recipe from: https://docs.python.org/3/library/tracemalloc.html#display-the-top-10
    tracemalloc.start()
    snapshot1 = tracemalloc.take_snapshot().filter_traces(
        (
            tracemalloc.Filter(False, linecache.__file__),
            tracemalloc.Filter(False, tracemalloc.__file__),
        )
    )
    yield
    gc.collect()
    snapshot2 = tracemalloc.take_snapshot().filter_traces(
        (
            tracemalloc.Filter(False, linecache.__file__),
            tracemalloc.Filter(False, tracemalloc.__file__),
        )
    )
    top_stats = snapshot2.compare_to(snapshot1, "lineno")
    capmanager = request.config.pluginmanager.getplugin("capturemanager")
    with capmanager.global_and_fixture_disabled():
        print("[tracemalloc] Top 10 differences:")
        for stat in top_stats[:10]:
            print(stat)
