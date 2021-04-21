from pathlib import Path

from fpdf import FPDF
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_simple_text_annotation(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=24)
    text = "A few words forming a sentence."
    pdf.text(x=50, y=150, txt=text)
    width = pdf.get_string_width(text)
    pdf.text_annotation(
        x=50,
        y=150 - pdf.font_size,
        w=width,
        h=pdf.font_size,
        text="The quick brown fox ate the lazy mouse . ",
    )
    assert_pdf_equal(pdf, HERE / "simple_text_annotation.pdf", tmp_path)
