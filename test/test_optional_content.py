from pathlib import Path

from fpdf import FPDF
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_optional_content(tmp_path):  # issue 441
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=24)
    with pdf.optional_content(on_print=False):
        pdf.text(20, 30, "Visible on screen only")
    with pdf.optional_content(on_view=False):
        pdf.text(20, 50, "Printed only")
    pdf.text(20, 70, "Always visible")
    assert_pdf_equal(pdf, HERE / "optional_content.pdf", tmp_path)
