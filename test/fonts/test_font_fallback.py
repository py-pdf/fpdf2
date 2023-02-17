from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_fallback_font(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(family="Roboto", fname=HERE / "Roboto-Regular.ttf")
    pdf.add_font(family="EmojiOne", fname=HERE / "EmojiOneColor-SVGinOT.ttf")
    pdf.set_font("Roboto")
    pdf.set_fallback_fonts(["EmojiOne"])
    pdf.cell(
        txt="hello **world 😄 😁** 😆 😅 ✌ 🤞 🌭 🍔 🍟 🍕",
        markdown=True,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.cell(
        txt="hello world 😄 😁 😆 😅 ✌ 🤞 🌭 🍔 🍟 🍕",
        markdown=False,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.multi_cell(
        txt="hello world 😄 😁 😆 😅 ✌ 🤞 🌭 🍔 🍟 🍕", w=50, new_x=XPos.LMARGIN, new_y=YPos.NEXT
    )
    pdf.write(txt="hello world 😄 😁 😆 😅 ✌ 🤞 🌭 🍔 🍟 🍕")
    assert_pdf_equal(pdf, HERE / "font_fallback.pdf", tmp_path)


# test - set fallback a font that has not been added
# test - glyph not on any font
