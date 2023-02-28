import pytest

from os import devnull
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from fpdf.errors import FPDFException
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_fallback_font(tmp_path):
    def write_strings():
        pdf.ln()
        pdf.write(txt="write 😄 😁 😆 😅 ✌")
        pdf.ln()
        pdf.cell(
            txt="cell with **markdown 😄 😁** 😆 😅 ✌",
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.cell(
            txt="cell without **markdown 😄 😁** 😆 😅 ✌",
            markdown=False,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.multi_cell(
            txt="multi cell 😄 😁 😆 😅 ✌",
            w=50,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(family="Roboto", fname=HERE / "Roboto-Regular.ttf")
    pdf.add_font(family="Roboto", style="B", fname=HERE / "Roboto-Bold.ttf")
    pdf.add_font(family="DejaVuSans", fname=HERE / "DejaVuSans.ttf")
    pdf.set_font("Roboto", size=15)
    pdf.write(txt="No fallback font:")
    write_strings()
    pdf.set_fallback_fonts(["DejaVuSans"])
    pdf.ln(2)
    pdf.write(txt="With fallback font:")
    write_strings()

    assert_pdf_equal(
        pdf,
        HERE / "font_fallback.pdf",
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
