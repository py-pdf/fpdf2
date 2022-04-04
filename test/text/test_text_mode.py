from pathlib import Path

from fpdf import FPDF, TextMode
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def test_set_text_mode(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=100)
    with pdf.set_text_mode(TextMode.STROKE):
        pdf.cell(txt="Hello world")
    pdf.ln()
    pdf.line_width = 1
    with pdf.set_text_mode(TextMode.STROKE):
        pdf.cell(txt="Hello world")
    pdf.ln()
    with pdf.set_text_mode(TextMode.STROKE, width=2):
        pdf.cell(txt="Hello world")
    assert_pdf_equal(pdf, HERE / "set_text_mode.pdf", tmp_path)
