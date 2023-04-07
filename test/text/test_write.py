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
    pdf.add_font(fname=FONTS_DIR / "DroidSansFallback.ttf")
    pdf.set_font("DroidSansFallback", "", 8)
    pdf.write(txt=LOREM_IPSUM[:100])
    pdf.ln()
    pdf.ln()
    pdf.set_stretching(150)
    pdf.write(txt=LOREM_IPSUM[:100])
    # for reference, in lieu of a colored background
    pdf.line(pdf.l_margin, 10, pdf.l_margin, 100)
    pdf.line(right_boundary, 10, right_boundary, 100)
    assert_pdf_equal(pdf, HERE / "write_font_stretching.pdf", tmp_path)


def test_write_superscript(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 20)

    def write_this():
        pdf.write(txt="2")
        pdf.char_vpos = "SUP"
        pdf.write(txt="56")
        pdf.char_vpos = "LINE"
        pdf.write(txt=" more line text")
        pdf.char_vpos = "SUB"
        pdf.write(txt="(idx)")
        pdf.char_vpos = "LINE"
        pdf.write(txt=" end")
        pdf.ln()
        pdf.ln()
        pdf.write(txt="1234 + ")
        pdf.char_vpos = "NOM"
        pdf.write(txt="5")
        pdf.char_vpos = "LINE"
        pdf.write(txt="/")
        pdf.char_vpos = "DENOM"
        pdf.write(txt="16")
        pdf.char_vpos = "LINE"
        pdf.write(txt=" + 987 = x")
        pdf.ln()
        pdf.ln()
        pdf.ln()

    write_this()
    pdf.sub_scale = 0.5
    pdf.sup_scale = 0.5
    pdf.nom_scale = 0.5
    pdf.denom_scale = 0.5
    write_this()
    pdf.sub_lift = 0.0
    pdf.sup_lift = 0.0
    pdf.nom_lift = 0.0
    pdf.denom_lift = 0.0
    write_this()
    pdf.sub_lift = 1.0
    pdf.sup_lift = 1.0
    pdf.nom_lift = 1.0
    pdf.denom_lift = 1.0
    write_this()
    assert_pdf_equal(pdf, HERE / "write_superscript.pdf", tmp_path)


def test_write_char_wrap(tmp_path):  # issue #649
    right_boundary = 50
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_right_margin(pdf.w - right_boundary)
    pdf.set_font("Helvetica", "", 10)
    pdf.write(txt=LOREM_IPSUM[:200])
    pdf.ln()
    pdf.ln()
    pdf.write(txt=LOREM_IPSUM[:200], wrapmode="CHAR")
    pdf.ln()
    pdf.ln()
    pdf.set_font("Courier", "", 10)
    txt = "     " + "abcdefghijklmnopqrstuvwxyz" * 3
    pdf.write(txt=txt)
    pdf.ln()
    pdf.ln()
    pdf.write(txt=txt, wrapmode="CHAR")
    pdf.line(pdf.l_margin, 10, pdf.l_margin, 130)
    pdf.line(right_boundary, 10, right_boundary, 130)
    assert_pdf_equal(pdf, HERE / "write_char_wrap.pdf", tmp_path)
