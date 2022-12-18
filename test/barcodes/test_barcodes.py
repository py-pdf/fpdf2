from pathlib import Path

from fpdf import FPDF
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_code39(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.code39("*fpdf2*", x=30, y=50, w=4, h=20)
    pdf.set_font("courier", "B", size=36)
    pdf.text(x=70, y=80, txt="*fpdf2*")
    assert_pdf_equal(pdf, HERE / "barcodes_code39.pdf", tmp_path)


def test_interleaved2of5(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.interleaved2of5("1337", x=65, y=50, w=4, h=20)
    pdf.set_font("courier", "B", size=36)
    pdf.text(x=80, y=80, txt="1337")
    assert_pdf_equal(pdf, HERE / "barcodes_interleaved2of5.pdf", tmp_path)
