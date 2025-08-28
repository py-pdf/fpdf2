from pathlib import Path

from fpdf import FPDF
from test.conftest import LOREM_IPSUM, assert_pdf_equal, EMOJI_TEST_TEXT

HERE = Path(__file__).resolve().parent
FONTS_DIR = HERE.parent / "fonts"


def test_twemoji(tmp_path):
    # Twemoji - Mozilla build of the Twitter emojis on COLR format
    # Apache 2.0 license
    # https://github.com/mozilla/twemoji-colr
    pdf = FPDF()
    pdf.add_font("Twemoji", "", HERE / "Twemoji.Mozilla.ttf")
    pdf.add_page()
    test_text = "😂❤🤣👍😭🙏😘🥰😍😊"
    pdf.set_font("helvetica", "", 24)
    pdf.cell(text="Twemoi (COLRv0)", new_x="lmargin", new_y="next")
    pdf.cell(text="Top 10 emojis:", new_x="right", new_y="top")
    pdf.set_font("Twemoji", "", 24)
    pdf.cell(text=test_text, new_x="lmargin", new_y="next")
    assert_pdf_equal(pdf, HERE / "colrv0-twemoji.pdf", tmp_path)


def test_twemoji_shaping(tmp_path):
    pdf = FPDF()
    pdf.add_font("Twemoji", "", HERE / "Twemoji.Mozilla.ttf")
    pdf.add_page()
    combined_emojis = "🇫🇷 🇺🇸 🇨🇦 🧑 🧑🏽 🧑🏿"
    pdf.set_font("helvetica", "", 24)
    pdf.cell(text="Emojis without text shaping:", new_x="lmargin", new_y="next")
    pdf.set_font("Twemoji", "", 24)
    pdf.multi_cell(w=pdf.epw, text=combined_emojis, new_x="lmargin", new_y="next")
    pdf.ln()
    pdf.set_font("helvetica", "", 24)
    pdf.cell(text="Emojis with text shaping:", new_x="lmargin", new_y="next")
    pdf.set_font("Twemoji", "", 24)
    pdf.set_text_shaping(True)
    pdf.multi_cell(w=pdf.epw, text=combined_emojis, new_x="lmargin", new_y="next")
    assert_pdf_equal(pdf, HERE / "colrv0-twemoji_shaping.pdf", tmp_path)


def test_twemoji_text(tmp_path):
    text = EMOJI_TEST_TEXT
    pdf = FPDF()
    pdf.add_font("Roboto", "", FONTS_DIR / "Roboto-Regular.ttf")
    pdf.add_font("Twemoji", "", HERE / "Twemoji.Mozilla.ttf")
    pdf.set_font("Roboto", "", 24)
    pdf.set_fallback_fonts(["Twemoji"])
    pdf.add_page()
    pdf.multi_cell(w=pdf.epw, text=text)
    assert_pdf_equal(pdf, HERE / "colrv0-twemoji_text.pdf", tmp_path)


def test_noto_colrv1(tmp_path):
    # Twemoji - Mozilla build of the Twitter emojis on COLR format
    # Apache 2.0 license
    # https://github.com/mozilla/twemoji-colr
    pdf = FPDF()
    pdf.add_font("NotoColrv1", "", HERE / "colrv1-NotoColorEmoji.ttf")
    pdf.add_page()
    test_text = "😂❤🤣👍😭🙏😘🥰😍😊"
    pdf.set_font("helvetica", "", 24)
    pdf.cell(text="NotoColor (COLRv1)", new_x="lmargin", new_y="next")
    pdf.cell(text="Top 10 emojis:", new_x="right", new_y="top")
    pdf.set_font("NotoColrv1", "", 24)
    pdf.cell(text=test_text, new_x="lmargin", new_y="next")
    assert_pdf_equal(pdf, HERE / "colrv1-noto-color-emoji.pdf", tmp_path)


def test_noto_colrv1_shaping(tmp_path):
    pdf = FPDF()
    pdf.add_font("NotoColrv1", "", HERE / "colrv1-NotoColorEmoji.ttf")
    pdf.add_page()
    combined_emojis = "🇫🇷 🇺🇸 🇨🇦 🧑 🧑🏽 🧑🏿"
    pdf.set_font("helvetica", "", 24)
    pdf.cell(text="Emojis without text shaping:", new_x="lmargin", new_y="next")
    pdf.set_font("NotoColrv1", "", 24)
    pdf.multi_cell(w=pdf.epw, text=combined_emojis, new_x="lmargin", new_y="next")
    pdf.ln()
    pdf.set_font("helvetica", "", 24)
    pdf.cell(text="Emojis with text shaping:", new_x="lmargin", new_y="next")
    pdf.set_font("NotoColrv1", "", 24)
    pdf.set_text_shaping(True)
    pdf.multi_cell(w=pdf.epw, text=combined_emojis, new_x="lmargin", new_y="next")
    assert_pdf_equal(pdf, HERE / "colrv1-noto-color-emoji_shaping.pdf", tmp_path)


def test_noto_colrv1_text(tmp_path):
    text = EMOJI_TEST_TEXT
    pdf = FPDF()
    pdf.add_font("Roboto", "", FONTS_DIR / "Roboto-Regular.ttf")
    pdf.add_font("NotoColrv1", "", HERE / "colrv1-NotoColorEmoji.ttf")
    pdf.set_font("Roboto", "", 24)
    pdf.set_fallback_fonts(["NotoColrv1"])
    pdf.add_page()
    pdf.multi_cell(w=pdf.epw, text=text)
    assert_pdf_equal(pdf, HERE / "colrv1-noto-color-emoji_text.pdf", tmp_path)


def test_colrv1_bungee(tmp_path):
    # Bungee Color - OFL license
    # https://github.com/djrrb/Bungee

    pdf = FPDF()
    pdf.add_font("Bungee", "", HERE / "BungeeSpice-Regular-COLRv1.ttf")

    pdf.add_page()
    pdf.set_font("Bungee", size=16)
    pdf.multi_cell(w=pdf.epw, text=LOREM_IPSUM.upper(), align="L")
    pdf.ln()
    pdf.multi_cell(w=pdf.epw, text=LOREM_IPSUM.upper(), align="R")
    pdf.ln()
    pdf.multi_cell(w=pdf.epw, text=LOREM_IPSUM.upper(), align="J")

    assert_pdf_equal(pdf, HERE / "colrv1_bungee.pdf", tmp_path)


def test_colrv1_nabla(tmp_path):
    pdf = FPDF()
    pdf.add_font("Nabla", "", HERE / "Nabla-Regular-COLRv1-VariableFont_EDPT,EHLT.ttf")

    pdf.add_page()
    pdf.set_font("Nabla", size=16)
    pdf.multi_cell(w=pdf.epw, text=LOREM_IPSUM.upper(), align="L")
    pdf.ln()
    pdf.multi_cell(w=pdf.epw, text=LOREM_IPSUM.upper(), align="R")
    pdf.ln()
    pdf.multi_cell(w=pdf.epw, text=LOREM_IPSUM.upper(), align="J")

    assert_pdf_equal(pdf, HERE / "colrv1_nabla.pdf", tmp_path)
