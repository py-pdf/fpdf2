from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def test_add_page_format(tmp_path):
    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica")
    for i in range(9):
        pdf.add_page(format=(210 * (1 - i / 10), 297 * (1 - i / 10)))
        pdf.cell(w=10, h=10, txt=str(i))
    pdf.add_page(same=True)
    pdf.cell(w=10, h=10, txt="9")
    assert_pdf_equal(pdf, HERE / "add_page_format.pdf", tmp_path)


def test_add_page_duration(tmp_path):
    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica", size=120)
    pdf.add_page(duration=3)
    pdf.cell(txt="Page 1")
    pdf.page_duration = 0.5
    pdf.add_page()
    pdf.cell(txt="Page 2")
    pdf.add_page()
    pdf.cell(txt="Page 3")
    assert_pdf_equal(pdf, HERE / "add_page_duration.pdf", tmp_path)
