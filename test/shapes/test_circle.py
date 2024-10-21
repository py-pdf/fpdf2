from pathlib import Path

from fpdf import FPDF
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent

RADIUS = 25
MARGIN = 10


def next_row(pdf):
    pdf.ln()
    pdf.set_xy(pdf.l_margin + RADIUS, pdf.y + 2 * RADIUS + MARGIN)


def test_circle_style(tmp_path):
    pdf = FPDF(unit="mm")
    pdf.add_page()

    pdf.set_xy(pdf.l_margin + RADIUS, pdf.y + RADIUS)
    for counter, style in enumerate(["", "F", "FD", "DF", None]):
        pdf.circle(x=pdf.x, y=pdf.y, radius=RADIUS, style=style)
        pdf.set_x(pdf.x + 2 * RADIUS + MARGIN)
        if counter % 3 == 2:
            next_row(pdf)

    assert_pdf_equal(pdf, HERE / "circle_style.pdf", tmp_path)


def test_circle_line_width(tmp_path):
    pdf = FPDF(unit="mm")
    pdf.add_page()

    pdf.set_xy(pdf.l_margin + RADIUS, pdf.y + RADIUS)
    for line_width in [1, 2, 3]:
        pdf.set_line_width(line_width)
        pdf.circle(x=pdf.x, y=pdf.y, radius=RADIUS, style=None)
        pdf.set_x(pdf.x + 2 * RADIUS + MARGIN)
    next_row(pdf)
    for line_width in [4, 5, 6]:
        pdf.set_line_width(line_width)
        pdf.circle(x=pdf.x, y=pdf.y, radius=RADIUS, style=None)
        pdf.set_x(pdf.x + 2 * RADIUS + MARGIN)
    pdf.set_line_width(0.2)  # reset

    assert_pdf_equal(pdf, HERE / "circle_line_width.pdf", tmp_path)


def test_circle_draw_color(tmp_path):
    pdf = FPDF(unit="mm")
    pdf.add_page()

    pdf.set_line_width(0.5)
    pdf.set_xy(pdf.l_margin + RADIUS, pdf.y + RADIUS)
    for gray in [70, 140, 210]:
        pdf.set_draw_color(gray)
        pdf.circle(x=pdf.x, y=pdf.y, radius=RADIUS, style=None)
        pdf.set_x(pdf.x + 2 * RADIUS + MARGIN)

    assert_pdf_equal(pdf, HERE / "circle_draw_color.pdf", tmp_path)


def test_circle_fill_color(tmp_path):
    pdf = FPDF(unit="mm")
    pdf.add_page()

    pdf.set_fill_color(240)
    pdf.set_xy(pdf.l_margin + RADIUS, pdf.y + RADIUS)
    for color in [[230, 30, 180], [30, 180, 30], [30, 30, 70]]:
        pdf.set_draw_color(*color)
        pdf.circle(x=pdf.x, y=pdf.y, radius=RADIUS, style="FD")
        pdf.set_x(pdf.x + 2 * RADIUS + MARGIN)
    next_row(pdf)

    assert_pdf_equal(pdf, HERE / "circle_fill_color.pdf", tmp_path)
