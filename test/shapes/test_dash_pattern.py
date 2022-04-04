from pathlib import Path
from pytest import raises

import fpdf
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_dash_pattern(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "", 10)

    def draw_stuff(x, y):
        pdf.line(x, y, x + 50, y + 50)
        pdf.polyline(((x, y), (x + 40, y + 20), (x + 10, y + 30), (x + 50, y + 50)))
        pdf.polygon(((x + 5, y + 20), (x + 25, y + 45), (x + 40, y + 10)))
        pdf.rect(x, y, 50, 50)
        pdf.ellipse(x, y, 50, 50)
        pdf.set_xy(x, y + 55)
        pdf.cell(w=50, h=5, txt="cell", border=1)

    # solid line
    draw_stuff(20, 20)
    # simple dash
    pdf.set_dash_pattern(3)
    draw_stuff(100, 20)
    # dashdot by overlap
    pdf.set_dash_pattern(4, 6)
    draw_stuff(20, 100)
    pdf.set_dash_pattern(0.5, 9.5, 3.25)
    # coverage: repeating the same pattern should not add it again
    pdf.set_dash_pattern(0.5, 9.5, 3.25)
    draw_stuff(20, 100)
    # reset to solid
    pdf.set_dash_pattern()
    draw_stuff(100, 100)

    assert_pdf_equal(pdf, HERE / "dash_pattern.pdf", tmp_path)


def test_dash_pattern_badinput():
    pdf = fpdf.FPDF()
    pdf.add_page()
    with raises(ValueError):
        pdf.set_dash_pattern(dash=-1)
    with raises(ValueError):
        pdf.set_dash_pattern(gap=-1)
    with raises(ValueError):
        pdf.set_dash_pattern(phase=-1)
    with raises(ValueError):
        pdf.set_dash_pattern(dash="yo")
    with raises(ValueError):
        pdf.set_dash_pattern(gap="hu")
    with raises(ValueError):
        pdf.set_dash_pattern(phase=None)
