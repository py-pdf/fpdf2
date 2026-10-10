from pathlib import Path

from fpdf import FPDF
from test.conftest import LOREM_IPSUM, assert_pdf_equal

HERE = Path(__file__).resolve().parent
FONTS_DIR = HERE.parent / "fonts"


def test_sbix_compyx(tmp_path):
    # Compyx - OFL license
    # https://github.com/RoelN/Compyx

    pdf = FPDF()
    pdf.add_font("Compyx", "", HERE / "Compyx-Regular-SBIX.ttf")

    pdf.add_page()
    pdf.set_font("Compyx", size=16)
    pdf.multi_cell(w=pdf.epw, text=LOREM_IPSUM.lower(), align="L")
    pdf.ln()
    pdf.multi_cell(w=pdf.epw, text=LOREM_IPSUM.lower(), align="R")
    pdf.ln()
    pdf.multi_cell(w=pdf.epw, text=LOREM_IPSUM.lower(), align="J")

    assert_pdf_equal(pdf, HERE / "sbix_compyx.pdf", tmp_path)


def test_sbix_bungee(tmp_path):
    # Bungee Color - OFL license
    # https://github.com/djrrb/Bungee

    pdf = FPDF()
    pdf.add_font("Bungee", "", HERE / "BungeeColor-Regular_sbix_MacOS.ttf")

    pdf.add_page()
    pdf.set_font("Bungee", size=16)
    pdf.multi_cell(w=pdf.epw, text=LOREM_IPSUM.upper(), align="L")
    pdf.ln()
    pdf.multi_cell(w=pdf.epw, text=LOREM_IPSUM.upper(), align="R")
    pdf.ln()
    pdf.multi_cell(w=pdf.epw, text=LOREM_IPSUM.upper(), align="J")

    assert_pdf_equal(pdf, HERE / "sbix_bungee.pdf", tmp_path)
