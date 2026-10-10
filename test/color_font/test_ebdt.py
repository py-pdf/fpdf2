from pathlib import Path

from fpdf import FPDF
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_ebdt_cozette(tmp_path):
    """
    Cozette is a bitmat font with MIT license.
    See https://github.com/the-moonwitch/Cozette
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Cozette", "", str(HERE / "ebdt_cozette.otb"))
    pdf.set_font("Cozette", "", 40)
    pdf.cell(text="Hello World!", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 255)
    pdf.cell(text="Hello Blue World!", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 255, 0)
    pdf.cell(text="Hello Green World!", new_x="LMARGIN", new_y="NEXT")

    assert_pdf_equal(pdf, HERE / "ebdt_cozette.pdf", tmp_path)


def test_ebdt_terminus(tmp_path):
    """
    Terminus is a bitmat font with SIL open font license.
    See https://files.ax86.net/terminus-ttf/
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Terminus", "", str(HERE / "ebdt_TerminusTTF-4.49.3.ttf"))
    pdf.set_font("Terminus", "", 40)
    pdf.cell(text="Hello World!", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 255)
    pdf.cell(text="Hello Blue World!", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 255, 0)
    pdf.cell(text="Hello Green World!", new_x="LMARGIN", new_y="NEXT")

    assert_pdf_equal(pdf, HERE / "ebdt_terminus.pdf", tmp_path)
