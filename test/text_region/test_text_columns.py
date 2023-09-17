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
        cols.write(text=LOREM_IPSUM[:100])
        pdf.set_font("Times", "", 12)
        cols.write(text=LOREM_IPSUM[100:200])
        pdf.set_font("Courier", "", 12)
        cols.write(text=LOREM_IPSUM[200:300])

    pdf.ln()
    pdf.ln()
    pdf.set_font("Helvetica", "I", 12)
    with cols:
        with cols.paragraph(align="J") as par:
            par.write(text=LOREM_IPSUM[:100])
            pdf.set_font("Times", "I", 12)
            par.write(text=LOREM_IPSUM[100:200])
            pdf.set_font("Courier", "I", 12)
            par.write(text=LOREM_IPSUM[200:300])

    pdf.ln()
    pdf.ln()
    pdf.set_font("Helvetica", "B", 12)
    with cols:
        with cols.paragraph(align="R") as par:
            par.write(text=LOREM_IPSUM[:100])
            pdf.set_font("Times", "B", 12)
            par.write(text=LOREM_IPSUM[100:200])
            pdf.set_font("Courier", "B", 12)
            par.write(text=LOREM_IPSUM[200:300])

    pdf.ln()
    pdf.ln()
    pdf.set_font("Helvetica", "BI", 12)
    with cols:
        with cols.paragraph(align="C") as par:
            par.write(text=LOREM_IPSUM[:100])
            pdf.set_font("Times", "BI", 12)
            par.write(text=LOREM_IPSUM[100:200])
            pdf.set_font("Courier", "BI", 12)
            par.write(text=LOREM_IPSUM[200:300])

    assert_pdf_equal(pdf, HERE / "tcols_align.pdf", tmp_path)


def test_tcols_3cols(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.t_margin = 50
    pdf.set_auto_page_break(True, 100)
    pdf.set_font("Helvetica", "", 6)
    cols = pdf.text_columns(text=LOREM_IPSUM, align="J", ncols=3, gutter=5)
    with cols:
        pdf.set_font("Times", "", 8)
        cols.write(text=LOREM_IPSUM)
        pdf.set_font("Courier", "", 10)
        cols.write(text=LOREM_IPSUM)
        pdf.set_font("Helvetica", "", 12)
        cols.write(text=LOREM_IPSUM)
        pdf.set_font("Times", "", 14)
        cols.write(text=LOREM_IPSUM)
        pdf.set_font("Courier", "", 16)
        cols.write(text=LOREM_IPSUM)
    assert_pdf_equal(pdf, HERE / "tcols_2cols.pdf", tmp_path)


def test_tcols_balance(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(True, 100)
    pdf.set_font("Helvetica", "", 6)
    cols_2 = pdf.text_columns(align="J", ncols=2, gutter=10, balance=True)
    cols_3 = pdf.text_columns(align="J", ncols=3, gutter=5, balance=True)
    with cols_2:
        pdf.set_font("Times", "", 8)
        cols_2.write(text=LOREM_IPSUM[:300])
    with cols_3:
        pdf.set_font("Courier", "", 10)
        cols_3.write(text=LOREM_IPSUM[300:600])
    with cols_2:
        pdf.set_font("Helvetica", "", 12)
        cols_2.write(text=LOREM_IPSUM[600:900])
    with cols_3:
        pdf.set_font("Times", "", 14)
        cols_3.write(text=LOREM_IPSUM[:300])
    assert_pdf_equal(pdf, HERE / "tcols_balance.pdf", tmp_path)


def xest_tcols_text_shaping(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.t_margin = 50
    pdf.set_text_shaping(True)
    pdf.set_font("Helvetica", "", 6)
    tsfontpath = HERE / ".." / "text_shaping"
    pdf.add_font(
        family="KFGQPC", fname=tsfontpath / "KFGQPC Uthmanic Script HAFS Regular.otf"
    )
    pdf.add_font(family="Mangal", fname=tsfontpath / "Mangal 400.ttf")
    cols = pdf.text_columns(align="L", ncols=3, gutter=20)
    with cols:
        #        pdf.set_font("Times", "", 12)
        #        cols.write(text=LOREM_IPSUM[:101])
        pdf.set_font("KFGQPC", size=12)
        cols.write(text=" مثال على اللغة العربية. محاذاة لليمين.")
        pdf.set_font("Mangal", size=12)
        cols.write(text="इण्टरनेट पर हिन्दी के साधन")
    #        pdf.set_font("Helvetica", "", 12)
    #        pdf.set_font("Times", "", 14)
    #        cols.write(text=LOREM_IPSUM)
    #        pdf.set_font("Courier", "", 16)
    #        cols.write(text=LOREM_IPSUM)

    assert_pdf_equal(pdf, HERE / "tcols_text_shaping.pdf", tmp_path)
