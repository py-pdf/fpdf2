from pathlib import Path

import pytest

from fpdf import FPDF
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def add_cell_page(pdf, cell_text):
    """Add a page with with some text to the PDF"""
    pdf.set_font("Helvetica")
    pdf.add_page()
    pdf.cell(w=10, h=10, txt=str(cell_text))


def test_unit_default(tmp_path):
    """Test creating a PDF with no unit"""
    pdf = FPDF()
    add_cell_page(pdf, "default")
    assert_pdf_equal(pdf, HERE / "unit_default.pdf", tmp_path)


@pytest.mark.parametrize("unit", ["pt", "mm", "cm", "in"])
def test_unit_str(tmp_path, unit):
    """Test all of the unit strings"""
    pdf = FPDF(unit=unit)
    add_cell_page(pdf, unit)
    assert_pdf_equal(pdf, HERE / "unit_{}.pdf".format(unit), tmp_path)


def test_unit_int(tmp_path):
    """Test creating a PDF with an int unit"""
    pdf = FPDF(unit=144)
    add_cell_page(pdf, "int = 2 in")
    assert_pdf_equal(pdf, HERE / "unit_int.pdf", tmp_path)


def test_unit_float(tmp_path):
    """Test creating a PDF with a float unit  (same as "in"), and that it is created exactly the same"""
    pdf = FPDF(unit=0.072)
    add_cell_page(pdf, "float = 1 thou")
    assert_pdf_equal(pdf, HERE / "unit_float.pdf", tmp_path)


def test_unit_int_matches_float_and_str(tmp_path):
    """Pdfs created with `unit=<float>` or `unit=<int>` should match those created with the associated string"""
    int_pdf = FPDF(unit=72)
    add_cell_page(int_pdf, "in")
    float_pdf = FPDF(unit=72.0)
    add_cell_page(float_pdf, "in")
    pdf_str = FPDF(unit="in")
    add_cell_page(pdf_str, "in")
    assert_pdf_equal(int_pdf, float_pdf, tmp_path)
    assert_pdf_equal(int_pdf, pdf_str, tmp_path)
    assert_pdf_equal(float_pdf, pdf_str, tmp_path)
