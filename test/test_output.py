from filecmp import cmp

import fpdf
import pytest

from test.conftest import assert_same_file


def test_repeated_calls_to_output(tmp_path):
    pdf = fpdf.FPDF()
    pdf.output(tmp_path / "empty.pdf")
    pdf.output(tmp_path / "empty2.pdf")
    assert cmp(tmp_path / "empty.pdf", tmp_path / "empty2.pdf")


def test_deprecation_warning(tmp_path):
    pdf = fpdf.FPDF()
    with pytest.warns(DeprecationWarning) as record:
        # pylint: disable=unexpected-keyword-arg
        pdf.output(name=tmp_path / "empty.pdf", dest="F")
    assert len(record) == 1
    assert_same_file(record[0].filename, __file__)


def test_save_to_absolute_path(tmp_path):
    pdf = fpdf.FPDF()
    pdf.output((tmp_path / "empty.pdf").absolute())


def test_page_dimensions_trailing_zeros_preserve_rounding():
    pdf = fpdf.FPDF(unit="pt", format=(100.0, 200.1234))
    pdf.add_page()
    assert b"/MediaBox [0 0 100 200.12]" in pdf.output()
