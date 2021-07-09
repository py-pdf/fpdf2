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
