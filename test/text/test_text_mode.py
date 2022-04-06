from pathlib import Path

from fpdf import FPDF, TextMode
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def test_text_mode_stroke(tmp_path):
    pdf = FPDF(orientation="landscape")
    pdf.add_page()
    pdf.set_font("Helvetica", size=80)
    with pdf.local_context(text_mode=TextMode.STROKE, line_width=2):
        pdf.cell(txt="STROKE text mode")
    pdf.ln()
    pdf.cell(txt="FILL text mode")
    pdf.ln()
    pdf.text_mode = TextMode.STROKE
    pdf.cell(txt="STROKE text mode")
    assert_pdf_equal(pdf, HERE / "text_mode_stroke.pdf", tmp_path)


def test_text_mode_clip(tmp_path):
    pdf = FPDF(orientation="landscape")
    pdf.add_page()
    pdf.set_font("Helvetica", size=80)
    with pdf.local_context(text_mode=TextMode.CLIP):
        pdf.cell(txt="CLIP text mode")
        for r in range(0, 200, 2):
            pdf.circle(x=110 - r / 2, y=30 - r / 2, r=r)
    assert_pdf_equal(pdf, HERE / "text_mode_clip.pdf", tmp_path)
