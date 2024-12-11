from pathlib import Path

from fpdf import FPDF
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent
FONTS_DIR = HERE.parent / "fonts"


def test_color_fonts(tmp_path):
    pdf = FPDF()
    # pdf.set_page_background((252,212,255))
    # pdf.set_text_shaping(False)

    pdf.add_font("NotoCBDT", "", HERE / "NotoColorEmoji-CBDT.ttf")
    pdf.add_font("TwitterEmoji", "", FONTS_DIR / "TwitterEmoji.ttf")
    pdf.add_font("BungeeSBIX", "", HERE / "BungeeColor-Regular_sbix_MacOS.ttf")

    pdf.add_page()

    test_text = "😂❤🤣👍😭🙏😘🥰😍😊"

    pdf.set_font("helvetica", "", 24)
    pdf.cell(text="Noto Color Emoji (CBDT)", new_x="lmargin", new_y="next")
    pdf.cell(text="Top 10 emojis:", new_x="right", new_y="top")
    pdf.set_font("NotoCBDT", "", 24)
    pdf.cell(text=test_text, new_x="lmargin", new_y="next")
    pdf.ln()
    pdf.set_font("helvetica", "", 24)
    pdf.cell(text="Twitter Emoji (SVG)", new_x="lmargin", new_y="next")
    pdf.set_font("TwitterEmoji", "", 24)
    pdf.cell(text=test_text, new_x="lmargin", new_y="next")
    pdf.ln()
    pdf.set_font("helvetica", "", 24)
    pdf.cell(text="Bungee color (sbix)", new_x="lmargin", new_y="next")
    pdf.set_font("BungeeSBIX", "", 24)
    pdf.cell(text="BUNGEE COLOR SBIX", new_x="lmargin", new_y="next")

    assert_pdf_equal(pdf, HERE / "color_font_basic.pdf", tmp_path)
