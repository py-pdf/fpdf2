from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal, LOREM_IPSUM

HERE = Path(__file__).resolve().parent
FONTS_DIR = HERE.parent / "fonts"


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


def test_write_font_stretching(tmp_path):  # issue #478
    right_boundary = 60
    pdf = fpdf.FPDF()
    pdf.add_page()
    # built-in font
    pdf.set_font("Helvetica", "", 8)
    pdf.set_fill_color(255, 255, 0)
    pdf.set_right_margin(pdf.w - right_boundary)
    pdf.write(txt=LOREM_IPSUM[:100])
    pdf.ln()
    pdf.ln()
    pdf.set_stretching(150)
    pdf.write(txt=LOREM_IPSUM[:100])
    pdf.ln()
    pdf.ln()
    # unicode font
    pdf.set_stretching(100)
    pdf.add_font("Droid", fname=FONTS_DIR / "DroidSansFallback.ttf")
    pdf.set_font("Droid", "", 8)
    pdf.set_fill_color(255, 255, 0)
    pdf.write(txt=LOREM_IPSUM[:100])
    pdf.ln()
    pdf.ln()
    pdf.set_stretching(150)
    pdf.write(txt=LOREM_IPSUM[:100])
    # for reference, in lieu of a colored background
    pdf.line(pdf.l_margin, 10, pdf.l_margin, 100)
    pdf.line(right_boundary, 10, right_boundary, 100)
    assert_pdf_equal(pdf, HERE / "write_font_stretching.pdf", tmp_path)
