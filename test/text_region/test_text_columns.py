from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal, LOREM_IPSUM

HERE = Path(__file__).resolve().parent
FONTS_DIR = HERE.parent / "fonts"


def test_tcols_align(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 12)
    cols = pdf.text_column()
    with cols:
        cols.write(txt=LOREM_IPSUM[:100])
        pdf.set_font("Times", "", 12)
        cols.write(txt=LOREM_IPSUM[100:200])
        pdf.set_font("Courier", "", 12)
        cols.write(txt=LOREM_IPSUM[200:300])

    pdf.ln()
    pdf.ln()
    pdf.set_font("Helvetica", "I", 12)
    with cols:
        with cols.paragraph(align="J") as par:
            par.write(txt=LOREM_IPSUM[:100])
            pdf.set_font("Times", "I", 12)
            par.write(txt=LOREM_IPSUM[100:200])
            pdf.set_font("Courier", "I", 12)
            par.write(txt=LOREM_IPSUM[200:300])

    pdf.ln()
    pdf.ln()
    pdf.set_font("Helvetica", "B", 12)
    with cols:
        with cols.paragraph(align="R") as par:
            par.write(txt=LOREM_IPSUM[:100])
            pdf.set_font("Times", "B", 12)
            par.write(txt=LOREM_IPSUM[100:200])
            pdf.set_font("Courier", "B", 12)
            par.write(txt=LOREM_IPSUM[200:300])

    pdf.ln()
    pdf.ln()
    pdf.set_font("Helvetica", "BI", 12)
    with cols:
        with cols.paragraph(align="C") as par:
            par.write(txt=LOREM_IPSUM[:100])
            pdf.set_font("Times", "BI", 12)
            par.write(txt=LOREM_IPSUM[100:200])
            pdf.set_font("Courier", "BI", 12)
            par.write(txt=LOREM_IPSUM[200:300])

    assert_pdf_equal(pdf, HERE / "tcols_align.pdf", tmp_path)


def test_tcols_2cols(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.t_margin = 50
    pdf.set_auto_page_break(True, 100)
    pdf.set_font("Helvetica", "", 6)
    cols = pdf.text_columns(align="J", ncols=3, gap_width=5)
    with cols:
        cols.write(txt=LOREM_IPSUM)
        pdf.set_font("Times", "", 8)
        cols.write(txt=LOREM_IPSUM)
        pdf.set_font("Courier", "", 10)
        cols.write(txt=LOREM_IPSUM)
        pdf.set_font("Helvetica", "", 12)
        cols.write(txt=LOREM_IPSUM)
        pdf.set_font("Times", "", 14)
        cols.write(txt=LOREM_IPSUM)
        pdf.set_font("Courier", "", 16)
        cols.write(txt=LOREM_IPSUM)

    assert_pdf_equal(pdf, HERE / "tcols_2cols.pdf", tmp_path)
