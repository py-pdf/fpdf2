from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal

import pytest

HERE = Path(__file__).resolve().parent


def test_multi_cell_markdown(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Times", "", 32)
    text = (  # Some text where styling occur over line breaks:
        "Lorem ipsum dolor amet, **consectetur adipiscing** elit,"
        " sed do eiusmod __tempor incididunt__ ut labore et dolore --magna aliqua--."
    )
    pdf.multi_cell(
        w=pdf.epw, txt=text, markdown=True
    )  # This is tricky to get working well
    pdf.ln()
    pdf.multi_cell(w=pdf.epw, txt=text, markdown=True, align="L")
    assert_pdf_equal(pdf, HERE / "multi_cell_markdown.pdf", tmp_path)


def test_multi_cell_markdown_with_ttf_fonts(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.add_font("Roboto", "", HERE / "../fonts/Roboto-Regular.ttf")
    pdf.add_font("Roboto", "B", HERE / "../fonts/Roboto-Bold.ttf")
    pdf.add_font("Roboto", "I", HERE / "../fonts/Roboto-Italic.ttf")
    pdf.set_font("Roboto", size=32)
    text = (  # Some text where styling occur over line breaks:
        "Lorem ipsum dolor, **consectetur adipiscing** elit,"
        " eiusmod __tempor incididunt__ ut labore et dolore --magna aliqua--."
    )
    pdf.multi_cell(
        w=pdf.epw, txt=text, markdown=True
    )  # This is tricky to get working well
    pdf.ln()
    pdf.multi_cell(w=pdf.epw, txt=text, markdown=True, align="L")
    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_with_ttf_fonts.pdf", tmp_path)


def test_multi_cell_markdown_missing_ttf_font():
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.add_font("Roboto", fname=HERE / "../fonts/Roboto-Regular.ttf")
    pdf.set_font("Roboto", size=60)
    with pytest.raises(fpdf.FPDFException) as error:
        pdf.multi_cell(w=pdf.epw, txt="**Lorem Ipsum**", markdown=True)
    expected_msg = (
        "Undefined font: robotoB - Use built-in fonts or FPDF.add_font() beforehand"
    )
    assert str(error.value) == expected_msg


def test_multi_cell_markdown_with_fill_color(tmp_path):  # issue 348
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=10)
    pdf.set_fill_color(255, 0, 0)
    pdf.multi_cell(
        50, markdown=True, txt="aa bb cc **dd ee dd ee dd ee dd ee dd ee dd ee**"
    )
    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_with_fill_color.pdf", tmp_path)


def test_multi_cell_markdown_justified(tmp_path):  # issue 327
    pdf = fpdf.FPDF()
    pdf.add_page()
    for font in ("Helvetica", "Courier"):
        pdf.set_font(family=font, size=12)
        pdf.set_y(pdf.y + 3)
        pdf.multi_cell(
            190,
            markdown=True,
            align="J",
            txt=(
                "Lorem **ipsum** dolor sit amet, **consectetur** adipiscing elit, "
                "sed do eiusmod tempor incididunt ut labore et dolore magna "
                "aliqua. Ut enim ad minim veniam, __quis__ nostrud exercitation "
                "ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis "
                "aute irure dolor in reprehenderit in voluptate velit esse cillum "
                "dolore eu fugiat nulla pariatur. Excepteur sint occaecat "
                "cupidatat non proident, sunt in culpa qui officia deserunt "
                "mollit anim id est laborum."
            ),
        )
        pdf.set_x(10)
        pdf.set_y(pdf.y + 5)
    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_justified.pdf", tmp_path)
