from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal, LOREM_IPSUM

HERE = Path(__file__).resolve().parent


def test_write_page_break(tmp_path):
    doc = fpdf.FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=24)
    doc.y = 20
    doc.write(txt=LOREM_IPSUM)
    doc.write(txt=LOREM_IPSUM)
    assert_pdf_equal(doc, HERE / "write_page_break.pdf", tmp_path)


def test_write_soft_hyphen(tmp_path):
    s = "Donau\u00addamp\u00adfschiff\u00adfahrts\u00adgesellschafts\u00adkapitäns\u00admützen\u00adstreifen. "
    doc = fpdf.FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=24)
    doc.y = 20
    doc.write(txt=s)
    doc.set_font("helvetica", size=24, style="B")
    doc.write(txt=s)
    doc.set_font("helvetica", size=24, style="I")
    doc.write(txt=s)
    doc.set_font("helvetica", size=24)
    doc.write(txt=s)
    doc.set_font("helvetica", size=24, style="B")
    doc.write(txt=s)
    doc.set_font("helvetica", size=24, style="I")
    doc.write(txt=s)
    doc.set_font("helvetica", size=24)
    doc.write(txt=s)
    assert_pdf_equal(doc, HERE / "write_soft_hyphen.pdf", tmp_path)


def test_write_trailing_nl(tmp_path):  # issue #455
    """Each item in lines triggers a line break at the end."""
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    lines = ["Hello\n", "Sweet\n", "World\n"]
    for line in lines:
        pdf.write(txt=line)
    pdf.write(txt="end_mmc")
    assert_pdf_equal(pdf, HERE / "write_trailing_nl.pdf", tmp_path)
