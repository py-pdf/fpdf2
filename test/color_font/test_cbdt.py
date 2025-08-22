from pathlib import Path

from fpdf import FPDF
from test.conftest import assert_pdf_equal, EMOJI_TEST_TEXT

HERE = Path(__file__).resolve().parent
FONTS_DIR = HERE.parent / "fonts"


def test_noto_color_emoji(tmp_path):
    pdf = FPDF()
    pdf.add_font("NotoCBDT", "", HERE / "NotoColorEmoji-CBDT.ttf")
    pdf.add_page()
    test_text = "😂❤🤣👍😭🙏😘🥰😍😊"
    pdf.set_font("helvetica", "", 24)
    pdf.cell(text="Noto Color Emoji (CBDT)", new_x="lmargin", new_y="next")
    pdf.cell(text="Top 10 emojis:", new_x="right", new_y="top")
    pdf.set_font("NotoCBDT", "", 24)
    pdf.cell(text=test_text, new_x="lmargin", new_y="next")
    assert_pdf_equal(pdf, HERE / "cbdt_noto_color_emoji.pdf", tmp_path)


def test_noto_emoji_shaping(tmp_path):
    pdf = FPDF()
    pdf.add_font("NotoCBDT", "", HERE / "NotoColorEmoji-CBDT.ttf")
    pdf.add_page()
    combined_emojis = "🇫🇷 🇺🇸 🇨🇦 🧑 🧑🏽 🧑🏿"
    pdf.set_font("helvetica", "", 24)
    pdf.cell(text="Emojis without text shaping:", new_x="lmargin", new_y="next")
    pdf.set_font("NotoCBDT", "", 24)
    pdf.multi_cell(w=pdf.epw, text=combined_emojis, new_x="lmargin", new_y="next")
    pdf.ln()
    pdf.set_font("helvetica", "", 24)
    pdf.cell(text="Emojis with text shaping:", new_x="lmargin", new_y="next")
    pdf.set_font("NotoCBDT", "", 24)
    pdf.set_text_shaping(True)
    pdf.multi_cell(w=pdf.epw, text=combined_emojis, new_x="lmargin", new_y="next")
    assert_pdf_equal(pdf, HERE / "cbdt_noto_color_emoji_shaping.pdf", tmp_path)


def test_noto_emoji_text(tmp_path):
    text = EMOJI_TEST_TEXT
    pdf = FPDF()
    pdf.add_font("Roboto", "", FONTS_DIR / "Roboto-Regular.ttf")
    pdf.add_font("NotoCBDT", "", HERE / "NotoColorEmoji-CBDT.ttf")
    pdf.set_font("Roboto", "", 24)
    pdf.set_fallback_fonts(["NotoCBDT"])
    pdf.add_page()
    pdf.multi_cell(w=pdf.epw, text=text)
    assert_pdf_equal(pdf, HERE / "cbdt_noto_emoji_text.pdf", tmp_path)
