from pathlib import Path

import pytest
from fpdf import FPDF, FPDFException
from test.conftest import assert_pdf_equal, LOREM_IPSUM

HERE = Path(__file__).resolve().parent
FONTS_DIR = HERE.parent / "fonts"
PNG_DIR = HERE.parent / "image/png_images"
SVG_DIR = HERE.parent / "svg/svg_sources"


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
    cols = pdf.text_columns(
        text=LOREM_IPSUM,
        text_align="J",
        img=SVG_DIR / "SVG_logo.svg",
        img_fill_width=True,
        ncols=3,
        gutter=5,
    )
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


def test_tcols_images(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 12)
    cols = pdf.text_columns(ncols=3, text_align="J")
    left, right = cols.current_x_extents(pdf.y, 0)
    pdf.line(left, pdf.t_margin, left, pdf.h - pdf.b_margin)
    pdf.line(right, pdf.t_margin, right, pdf.h - pdf.b_margin)
    with cols:
        cols.write(text="Images at Native Size\n(Raster 72 dpi, SVG 90 dpi)\n\n")
        cols.write(text=LOREM_IPSUM[:100])
        cols.image(PNG_DIR / "ac6343a98f8edabfcc6e536dd75aacb0.png")
        cols.write(text=LOREM_IPSUM[100:200])
        cols.image(SVG_DIR / "SVG_logo.svg")
        cols.write(text=LOREM_IPSUM[200:300])

        cols.new_column()
        cols.write(text="Images at Full Column Width\n\n")
        cols.write(text=LOREM_IPSUM[:100])
        cols.image(
            PNG_DIR / "ac6343a98f8edabfcc6e536dd75aacb0.png",
            fill_width=True,
        )
        cols.write(text=LOREM_IPSUM[100:200])
        cols.image(SVG_DIR / "SVG_logo.svg", fill_width=True)
        cols.write(text=LOREM_IPSUM[200:300])

        cols.new_column()
        cols.write(text="Images Aligned Right and Center\n\n")
        cols.write(text=LOREM_IPSUM[:100])
        cols.image(
            PNG_DIR / "ac6343a98f8edabfcc6e536dd75aacb0.png",
            align="RIGHT",
        )
        cols.write(text=LOREM_IPSUM[100:200])
        cols.image(SVG_DIR / "SVG_logo.svg", align="CENTER")
        cols.write(text=LOREM_IPSUM[200:300])

        cols.new_column()
        cols.write(text="Images at Size 50x20\ntop/bottom margin\n\n")
        cols.write(text=LOREM_IPSUM[:100])
        cols.image(
            PNG_DIR / "ac6343a98f8edabfcc6e536dd75aacb0.png",
            width=50,
            height=20,
            top_margin=10,
        )
        cols.write(text=LOREM_IPSUM[100:200])
        cols.image(
            SVG_DIR / "SVG_logo.svg",
            width=50,
            height=20,
            bottom_margin=10,
        )
        cols.write(text=LOREM_IPSUM[200:300])

        cols.new_column()
        cols.write(text="Images at Size 50x20 and keep_aspect_ratio=True\n\n")
        cols.write(text=LOREM_IPSUM[:100])
        cols.image(
            PNG_DIR / "ac6343a98f8edabfcc6e536dd75aacb0.png",
            width=50,
            height=20,
            keep_aspect_ratio=True,
        )
        cols.write(text=LOREM_IPSUM[100:200])
        cols.image(
            SVG_DIR / "SVG_logo.svg",
            width=50,
            height=20,
            keep_aspect_ratio=True,
        )
        cols.write(text=LOREM_IPSUM[200:300])

        cols.new_column()
        cols.write(text="Images at Size 20x50 and keep_aspect_ratio=True\n\n")
        cols.write(text=LOREM_IPSUM[:100])
        cols.image(
            PNG_DIR / "ac6343a98f8edabfcc6e536dd75aacb0.png",
            width=20,
            height=50,
            keep_aspect_ratio=True,
        )
        cols.write(text=LOREM_IPSUM[100:200])
        cols.image(
            SVG_DIR / "SVG_logo.svg",
            width=20,
            height=50,
            keep_aspect_ratio=True,
        )
        cols.write(text=LOREM_IPSUM[200:300])

        cols.new_column()
        cols.write(text="Column break by image\n\n")
        cols.write(text=LOREM_IPSUM[:100])
        cols.image(
            PNG_DIR / "ac6343a98f8edabfcc6e536dd75aacb0.png",
            fill_width=True,
        )
        cols.write(text=LOREM_IPSUM[100:200])
        cols.image(SVG_DIR / "SVG_logo.svg", fill_width=True)
        cols.write(text=LOREM_IPSUM[200:300])
        cols.image(
            PNG_DIR / "ac6343a98f8edabfcc6e536dd75aacb0.png",
            fill_width=True,
        )
        cols.image(SVG_DIR / "SVG_logo.svg", fill_width=True)

    assert_pdf_equal(pdf, HERE / "tcols_images.pdf", tmp_path)


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
    # invalid alignment values
    with pytest.raises(ValueError) as error:
        col = pdf.text_columns(text_align="X_CENTER")
    expected_msg = (
        "Text_align must be 'LEFT', 'CENTER', 'RIGHT', or 'JUSTIFY', not 'X_CENTER'."
    )
    assert str(error.value) == expected_msg
    with pytest.raises(ValueError) as error:
        with pdf.text_columns() as col:
            par = col.paragraph(text_align="X_CENTER")
    assert str(error.value) == expected_msg
    with pytest.raises(ValueError) as error:
        with pdf.text_columns() as col:
            col.image(name="foo", align="JUSTIFY")
    expected_msg = "Align must be 'LEFT', 'CENTER', or 'RIGHT', not 'JUSTIFY'."
    assert str(error.value) == expected_msg
    # Wrong call sequence for ImageParagraph.
    with pdf.text_columns() as col:
        col.image(name=PNG_DIR / "ac6343a98f8edabfcc6e536dd75aacb0.png")
        with pytest.raises(RuntimeError) as error:
            col._paragraphs[-1].render(1, 2, 3)  # pylint: disable=protected-access
    expected_msg = "ImageParagraph.build_line() must be called before render()."
    assert str(error.value) == expected_msg


def test_tcols_break_top_margin(tmp_path):  # regression test for #1214
    """Ensure that the top/bottom margins of a paragraph trigger
    a column break.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 14)
    pdf.set_top_margin(50)
    pdf.set_auto_page_break(True, 50)
    pdf.rect(pdf.l_margin, pdf.t_margin, pdf.epw, pdf.eph)

    with pdf.text_columns(text_align="J", ncols=2) as cols:
        for _ in range(3):
            with cols.paragraph(
                text_align="J",
                bottom_margin=pdf.font_size * 5,
                top_margin=pdf.font_size * 5,
            ) as par:
                par.write(text=LOREM_IPSUM)
    assert_pdf_equal(pdf, HERE / "tcols_break_top_margin.pdf", tmp_path)


def test_tcols_bullets_indent(tmp_path):
    """Ensure that the top/bottom margins work with indented/bulleted
    paragraphs.
    Ensure that indented paragraphs have a reduced total width.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 14)
    pdf.set_top_margin(50)
    pdf.set_auto_page_break(True, 50)
    pdf.rect(pdf.l_margin, pdf.t_margin, pdf.epw, pdf.eph)
    with pdf.text_columns(text_align="L", ncols=2) as cols:
        cols.write("Paragraphs with Top Margin\n\n")
        for _ in range(4):
            with cols.paragraph(
                text_align="J",
                top_margin=pdf.font_size * 4,
            ) as par:
                par.write(text=LOREM_IPSUM[:100])
        for _ in range(5):
            with cols.paragraph(
                text_align="J",
                top_margin=pdf.font_size * 4,
                indent=10,
                bullet_string="\x95",
            ) as par:
                par.write(text=LOREM_IPSUM[:100])
    pdf.add_page()
    pdf.rect(pdf.l_margin, pdf.t_margin, pdf.epw, pdf.eph)
    with pdf.text_columns(text_align="L", ncols=2) as cols:
        cols.write("Paragraphs with Bottom Margin\n\n")
        for _ in range(4):
            with cols.paragraph(
                text_align="J",
                bottom_margin=pdf.font_size * 4,
            ) as par:
                par.write(text=LOREM_IPSUM[:100])
        for _ in range(5):
            with cols.paragraph(
                text_align="J",
                bottom_margin=pdf.font_size * 4,
                indent=10,
                bullet_string="\x95",
            ) as par:
                par.write(text=LOREM_IPSUM[:100])
    pdf.add_page()
    pdf.rect(pdf.l_margin, pdf.t_margin, pdf.epw, pdf.eph)
    with pdf.text_columns(text_align="L", ncols=2) as cols:
        cols.write("Paragraphs with Top and Bottom Margin\n\n")
        for _ in range(4):
            with cols.paragraph(
                text_align="J",
                top_margin=pdf.font_size * 1.5,
                bottom_margin=pdf.font_size * 2.5,
            ) as par:
                par.write(text=LOREM_IPSUM[:100])
        for _ in range(5):
            with cols.paragraph(
                text_align="J",
                top_margin=pdf.font_size * 1.5,
                bottom_margin=pdf.font_size * 2.5,
                indent=10,
                bullet_string="\x95",
            ) as par:
                par.write(text=LOREM_IPSUM[:100])
    assert_pdf_equal(pdf, HERE / "tcols_bullets_indent.pdf", tmp_path)

