from pathlib import Path

from fpdf import FPDF, TextMode

import pytest

from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def test_text_modes(tmp_path):
    pdf = FPDF(format=(350, 150))
    pdf.add_page()
    pdf.set_font("Helvetica", size=80)
    with pdf.local_context(fill_color=(255, 128, 0)):
        pdf.cell(txt="FILL default")
    with pdf.local_context(text_color=(0, 128, 255)):
        pdf.cell(txt=" text mode")
    pdf.ln()
    with pdf.local_context(text_mode=TextMode.STROKE, line_width=2):
        pdf.cell(txt="STROKE text mode")
    pdf.ln()
    pdf.text_mode = TextMode.FILL_STROKE
    pdf.line_width = 4
    pdf.set_draw_color(255, 0, 255)
    pdf.cell(txt="FILL_STROKE text mode")
    pdf.ln()
    with pdf.local_context():
        pdf.text_mode = "INVISIBLE"  # testing TextMode.coerce
        pdf.cell(txt="INVISIBLE text mode")
    assert_pdf_equal(pdf, HERE / "text_modes.pdf", tmp_path)


def test_clip_text_modes(tmp_path):
    pdf = FPDF(format=(420, 150))
    pdf.add_page()
    pdf.set_font("Helvetica", size=80)
    pdf.line_width = 1
    with pdf.local_context(text_mode=TextMode.FILL_CLIP, text_color=(0, 255, 255)):
        pdf.cell(txt="FILL_CLIP text mode")
        for r in range(0, 200, 2):
            pdf.circle(x=110 - r / 2, y=22 - r / 2, r=r)
    pdf.ln()
    with pdf.local_context(text_mode=TextMode.STROKE_CLIP):
        pdf.cell(txt="STROKE_CLIP text mode")
        for r in range(0, 200, 2):
            pdf.circle(x=110 - r / 2, y=50 - r / 2, r=r)
    pdf.ln()
    with pdf.local_context(
        text_mode=TextMode.FILL_STROKE_CLIP, text_color=(0, 255, 255)
    ):
        pdf.cell(txt="FILL_STROKE_CLIP text mode")
        for r in range(0, 200, 2):
            pdf.circle(x=110 - r / 2, y=78 - r / 2, r=r)
    pdf.ln()
    with pdf.local_context(text_mode=TextMode.CLIP):
        pdf.cell(txt="CLIP text mode")
        for r in range(0, 200, 2):
            pdf.circle(x=110 - r / 2, y=106 - r / 2, r=r)
    pdf.ln()
    assert_pdf_equal(pdf, HERE / "clip_text_modes.pdf", tmp_path)


def test_invalid_text_mode():
    pdf = FPDF()
    with pytest.raises(ValueError):
        pdf.text_mode = "DUMMY"
