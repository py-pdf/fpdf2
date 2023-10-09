from pathlib import Path

import pytest
from fpdf import FPDF, FPDFException
from test.conftest import assert_pdf_equal, LOREM_IPSUM

HERE = Path(__file__).resolve().parent
FONTS_DIR = HERE.parent / "fonts"


def test_tcols_align(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 12)
    col = pdf.text_columns()
    with col:
        col.write(text=LOREM_IPSUM[:100])
        pdf.set_font("Times", "", 12)
        col.write(text=LOREM_IPSUM[100:200])
        pdf.set_font("Courier", "", 12)
        col.write(text=LOREM_IPSUM[200:300])
    pdf.set_font("Helvetica", "I", 12)
    with col:
        with col.paragraph(text_align="J", top_margin=pdf.font_size * 2) as par:
            par.write(text=LOREM_IPSUM[:100])
            pdf.set_font("Times", "I", 12)
            par.write(text=LOREM_IPSUM[100:200])
            pdf.set_font("Courier", "I", 12)
            par.write(text=LOREM_IPSUM[200:300])
    pdf.set_font("Helvetica", "B", 12)
    with col:
        with col.paragraph(text_align="R", top_margin=pdf.font_size * 2) as par:
            par.write(text=LOREM_IPSUM[:100])
            pdf.set_font("Times", "B", 12)
            par.write(text=LOREM_IPSUM[100:200])
            pdf.set_font("Courier", "B", 12)
            par.write(text=LOREM_IPSUM[200:300])
    pdf.set_font("Helvetica", "BI", 12)
    with col:
        with col.paragraph(text_align="C", top_margin=pdf.font_size * 2) as par:
            par.write(text=LOREM_IPSUM[:100])
            pdf.set_font("Times", "BI", 12)
            par.write(text=LOREM_IPSUM[100:200])
            pdf.set_font("Courier", "BI", 12)
            par.write(text=LOREM_IPSUM[200:300])
    assert_pdf_equal(pdf, HERE / "tcols_align.pdf", tmp_path)


def test_tcols_3cols(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.t_margin = 50
    pdf.set_auto_page_break(True, 100)
    pdf.set_font("Helvetica", "", 6)
    cols = pdf.text_columns(text=LOREM_IPSUM, text_align="J", ncols=3, gutter=5)
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
    assert_pdf_equal(pdf, HERE / "tcols_3cols.pdf", tmp_path)


def test_tcols_balance(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(True, 100)
    pdf.set_font("Helvetica", "", 6)
    cols_2 = pdf.text_columns(text_align="J", ncols=2, gutter=10, balance=True)
    cols_3 = pdf.text_columns(text_align="J", ncols=3, gutter=5, balance=True)
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


def test_tcols_charwrap(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("courier", "", 16)
    col = pdf.text_columns(l_margin=50, r_margin=50)
    # wrapmode on paragraph
    with col.paragraph(wrapmode="CHAR", bottom_margin=pdf.font_size) as par:
        par.write(text=LOREM_IPSUM[:500])
    col.render()
    # wrapmode on column
    with pdf.text_columns(
        l_margin=50,
        r_margin=50,
        wrapmode="CHAR",
    ) as col:
        with col.paragraph() as par:
            par.write(text=LOREM_IPSUM[500:1000])
    assert_pdf_equal(pdf, HERE / "tcols_charwrap.pdf", tmp_path)


def test_tcols_no_font():
    pdf = FPDF()
    pdf.add_page()
    with pytest.raises(FPDFException) as error:
        col = pdf.text_columns()
        col.write("something")
    expected_msg = "No font set, you need to call set_font() beforehand"
    assert str(error.value) == expected_msg
    with pytest.raises(FPDFException) as error:
        col.ln()
    expected_msg = "No font set, you need to call set_font() beforehand"
    assert str(error.value) == expected_msg


def test_tcols_bad_uses():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("courier", "", 16)
    col = pdf.text_columns()
    # recursive text region context
    with col:
        col.write("something")
        with pytest.raises(FPDFException) as error:
            with col:
                pass
    expected_msg = "Unable to enter the same TextColumns context recursively."
    assert str(error.value) == expected_msg
    # recursive use of paragraph context
    with col.paragraph() as par:
        par.write("something")
        with pytest.raises(FPDFException) as error:
            col.paragraph()
    expected_msg = "Unable to nest paragraphs."
    assert str(error.value) == expected_msg
    # writing to column while we have an explicit paragraph active
    with col.paragraph() as par:
        par.write("something")
        with pytest.raises(FPDFException) as error:
            col.write("else")
    expected_msg = "Conflicts with active paragraph. Either close the current paragraph or write your text inside it."
    assert str(error.value) == expected_msg
    # ending a non-existent paragraph
    with pytest.raises(FPDFException) as error:
        col.end_paragraph()
    expected_msg = "No active paragraph to end."
    assert str(error.value) == expected_msg
    # column with negative width
    with pytest.raises(FPDFException) as error:
        col = pdf.text_columns(l_margin=150, r_margin=150)
    expected_msg = (
        "TextColumns(): Right limit (60.00155555555551) lower than left limit (150)."
    )
    assert str(error.value) == expected_msg


@pytest.mark.skip(reason="unfinished")
def test_tcols_text_shaping(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.t_margin = 50
    pdf.set_text_shaping(True)
    pdf.set_font("Helvetica", "", 6)
    tsfontpath = HERE / ".." / "text_shaping"
    pdf.add_font(
        family="KFGQPC", fname=tsfontpath / "KFGQPC Uthmanic Script HAFS Regular.otf"
    )
    pdf.add_font(family="Mangal", fname=tsfontpath / "Mangal 400.ttf")
    cols = pdf.text_columns(text_align="L", ncols=3, gutter=20)
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
