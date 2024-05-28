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
    pdf.write(text="WITHOUT FALLBACK FONT:\n")
    write_strings(pdf)

    pdf.ln(10)
    pdf.write(text="WITH FALLBACK FONT:\n")
    pdf.set_fallback_fonts(["DejaVuSans"])
    write_strings(pdf)

    assert_pdf_equal(
        pdf,
        HERE / "fallback_font.pdf",
        tmp_path,
    )


def write_strings(pdf):
    pdf.write(text="write() 😄 😁 😆 😅 ✌")
    pdf.ln()
    pdf.cell(
        text="cell() without markdown 😄 😁**bold** 😆 😅 ✌",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.cell(
        text="cell() with markdown 😄 😁**bold** 😆 😅 ✌",
        markdown=True,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.multi_cell(
        text="multi_cell() 😄 😁 😆 😅 ✌",
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

    pdf.set_fallback_fonts(["DejaVuSans"], exact_match=True)
    pdf.cell(
        text="cell() with markdown + exact_match=True: **[😄 😁]** 😆 😅 ✌",
        markdown=True,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.ln()

    pdf.set_fallback_fonts(["DejaVuSans"], exact_match=False)
    pdf.cell(
        text="cell() with markdown + exact_match=False: **[😄 😁]** 😆 😅 ✌",
        markdown=True,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.ln()

    pdf.add_font(family="DejaVuSans", style="B", fname=HERE / "DejaVuSans-Bold.ttf")
    pdf.cell(
        text="cell() with markdown + matching font style: **[😄 😁]** 😆 😅 ✌",
        markdown=True,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.ln()

    pdf.add_font(family="Roboto", style="I", fname=HERE / "Roboto-Italic.ttf")
    pdf.add_font(family="Roboto", style="BI", fname=HERE / "Roboto-BoldItalic.TTF")
    pdf.add_font(family="DejaVuSans", style="I", fname=HERE / "DejaVuSans-Oblique.ttf")
    pdf.add_font(
        family="DejaVuSans", style="IB", fname=HERE / "DejaVuSans-BoldOblique.ttf"
    )
    pdf.cell(
        text="cell() with markdown + bold-italics: __{**[😄 😁]** 😆 😅}__ ✌",
        markdown=True,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.ln()

    assert_pdf_equal(
        pdf,
        HERE / "fallback_font_ignore_style.pdf",
        tmp_path,
    )


def test_fallback_font_with_overriden_get_fallback_font(tmp_path):
    class PDF(FPDF):
        def get_fallback_font(self, char, style=""):
            fonts_with_char = [
                font_id
                for font_id in self._fallback_font_ids
                if ord(char) in self.fonts[font_id].cmap
            ]
            if not fonts_with_char:
                return None
            if len(fonts_with_char) == 1:
                return fonts_with_char[0]
            if self.font_family == "quicksand" and "dejavusans" in fonts_with_char:
                return "dejavusans"
            if self.font_family == "roboto" and "twitteremoji" in fonts_with_char:
                return "twitteremoji"
            raise NotImplementedError

    pdf = PDF()
    pdf.add_page()
    pdf.add_font(family="Quicksand", fname=HERE / "Quicksand-Regular.otf")
    pdf.add_font(family="Roboto", fname=HERE / "Roboto-Regular.ttf")
    pdf.add_font(fname=HERE / "DejaVuSans.ttf")
    pdf.add_font(fname=HERE / "TwitterEmoji.ttf")
    pdf.add_font(fname=HERE / "Waree.ttf")
    text = "Hello world / สวัสดีชาวโลก ทดสอบฟอนต์, 😄 😁 😆 😅 ✌"
    pdf.set_fallback_fonts(["DejaVuSans", "TwitterEmoji", "Waree"])
    pdf.set_font("Quicksand", size=20)
    pdf.cell(
        text=text,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.ln()
    pdf.set_font("Roboto", size=20)
    pdf.cell(
        text=text,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    assert_pdf_equal(
        pdf,
        HERE / "fallback_font_with_overriden_get_fallback_font.pdf",
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
    pdf.cell(text="Test 𝕥𝕖𝕤𝕥 🆃🅴🆂🆃 😲")
    pdf.output(devnull)
    assert (
        "Roboto is missing the following glyphs: "
        "'🆃' (\\U0001f183), '🅴' (\\U0001f174), '🆂' (\\U0001f182)" in caplog.text
    )
