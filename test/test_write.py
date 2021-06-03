from pathlib import Path

from fpdf import FPDF
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_write_markdown(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=24)
    pdf.write(txt="**Lorem** __Ipsum__", markdown=True)
    assert_pdf_equal(pdf, HERE / "write_markdown.pdf", tmp_path)
