from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def next_row(pdf):
    pdf.ln()
    pdf.set_y(pdf.get_y() + SIZE + MARGIN)


SIZE = 50
MARGIN = 10


def test_circle_style(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    for counter, style in enumerate(["", "F", "FD", "DF", None]):
        pdf.circle(x=pdf.get_x(), y=pdf.get_y(), r=SIZE, style=style)
        pdf.set_x(pdf.get_x() + SIZE + MARGIN)
        if counter % 3 == 2:
            next_row(pdf)

    assert_pdf_equal(pdf, HERE / "class_circle_style.pdf", tmp_path)


def test_circle_line_width(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    for line_width in [1, 2, 3]:
        pdf.set_line_width(line_width)
        pdf.circle(x=pdf.get_x(), y=pdf.get_y(), r=SIZE, style=None)
        pdf.set_x(pdf.get_x() + SIZE + MARGIN)
    next_row(pdf)
    for line_width in [4, 5, 6]:
        pdf.set_line_width(line_width)
        pdf.circle(x=pdf.get_x(), y=pdf.get_y(), r=SIZE, style=None)
        pdf.set_x(pdf.get_x() + SIZE + MARGIN)
    pdf.set_line_width(0.2)  # reset

    assert_pdf_equal(pdf, HERE / "class_circle_line_width.pdf", tmp_path)


def test_circle_draw_color(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    pdf.set_line_width(0.5)
    for gray in [70, 140, 210]:
        pdf.set_draw_color(gray)
        pdf.circle(x=pdf.get_x(), y=pdf.get_y(), r=SIZE, style=None)
        pdf.set_x(pdf.get_x() + SIZE + MARGIN)

    assert_pdf_equal(pdf, HERE / "class_circle_draw_color.pdf", tmp_path)


def test_circle_fill_color(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    pdf.set_fill_color(240)
    for color in [[230, 30, 180], [30, 180, 30], [30, 30, 70]]:
        pdf.set_draw_color(*color)
        pdf.circle(x=pdf.get_x(), y=pdf.get_y(), r=SIZE, style="FD")
        pdf.set_x(pdf.get_x() + SIZE + MARGIN)
    next_row(pdf)

    assert_pdf_equal(pdf, HERE / "class_circle_fill_color.pdf", tmp_path)
