import pytest

from os import devnull
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from fpdf.errors import FPDFException
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_fallback_font(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(family="Roboto", fname=HERE / "Roboto-Regular.ttf")
    pdf.add_font(family="Roboto", style="B", fname=HERE / "Roboto-Bold.ttf")
    pdf.add_font(family="DejaVuSans", fname=HERE / "DejaVuSans.ttf")
    pdf.set_font("Roboto", size=15)
    pdf.write(txt="WITHOUT FALLBACK FONT:\n")
    write_strings(pdf)

    pdf.ln(10)
    pdf.write(txt="WITH FALLBACK FONT:\n")
    pdf.set_fallback_fonts(["DejaVuSans"])
    write_strings(pdf)

    assert_pdf_equal(
        pdf,
        HERE / "fallback_font.pdf",
        tmp_path,
    )


def write_strings(pdf):
    pdf.write(txt="write() 😄 😁 😆 😅 ✌")
    pdf.ln()
    pdf.cell(
        txt="cell() without markdown 😄 😁**bold** 😆 😅 ✌",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.cell(
        txt="cell() with markdown 😄 😁**bold** 😆 😅 ✌",
        markdown=True,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.multi_cell(
        txt="multi_cell() 😄 😁 😆 😅 ✌",
        w=50,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )


def test_fallback_font_no_warning(caplog):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(family="Roboto", fname=HERE / "Roboto-Regular.ttf")
    pdf.add_font(family="Roboto", style="B", fname=HERE / "Roboto-Bold.ttf")
    pdf.add_font(family="DejaVuSans", fname=HERE / "DejaVuSans.ttf")
    pdf.set_font("Roboto", size=15)
    pdf.set_fallback_fonts(["DejaVuSans"])
    write_strings(pdf)
    pdf.output()
    assert len(caplog.text) == 0


def test_fallback_font_ignore_style(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(family="Roboto", fname=HERE / "Roboto-Regular.ttf")
    pdf.add_font(family="Roboto", style="B", fname=HERE / "Roboto-Bold.ttf")
    pdf.add_font(family="DejaVuSans", fname=HERE / "DejaVuSans.ttf")
    pdf.set_font("Roboto", size=20)
    pdf.set_fallback_fonts(["DejaVuSans"])
    pdf.cell(
        txt="cell() with markdown and strict style match: **[😄 😁]** 😆 😅 ✌",
        markdown=True,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.ln()
    pdf.set_fallback_fonts(["DejaVuSans"], ignore_style=True)
    pdf.cell(
        txt="cell() with markdown and ignore style match: **[😄 😁]** 😆 😅 ✌",
        markdown=True,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    assert_pdf_equal(
        pdf,
        HERE / "fallback_font_ignore_style.pdf",
        tmp_path,
    )


def test_invalid_fallback_font():
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(family="Roboto", fname=HERE / "Roboto-Regular.ttf")
    pdf.add_font(family="Waree", fname=HERE / "Waree.ttf")
    pdf.set_font("Roboto", size=15)
    with pytest.raises(FPDFException) as error:
        pdf.set_fallback_fonts(["Waree", "Invalid"])
    assert (
        str(error.value)
        == "Undefined fallback font: Invalid - Use FPDF.add_font() beforehand"
    )


def test_glyph_not_on_any_font(caplog):
    """
    Similar to fonts\\test_add_font\\test_font_missing_glyphs,
    but resulting is less missing glyphs because the fallback font provided some of them
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(family="Roboto", fname=HERE / "Roboto-Regular.ttf")
    pdf.add_font(family="DejaVuSans", fname=HERE / "DejaVuSans.ttf")
    pdf.set_font("Roboto")
    pdf.set_fallback_fonts(["DejaVuSans"])
    pdf.cell(txt="Test 𝕥𝕖𝕤𝕥 🆃🅴🆂🆃 😲")
    pdf.output(devnull)
    assert "Roboto is missing the following glyphs: 🆃, 🅴, 🆂" in caplog.text
