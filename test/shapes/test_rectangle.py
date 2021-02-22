from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def next_row(pdf):
    pdf.ln()
    pdf.set_y(pdf.get_y() + size + margin)


size = 50
margin = 10


def test_rect_not_square(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    for counter, style in enumerate(["", "F", "FD", "DF", None]):
        pdf.rect(x=pdf.get_x(), y=pdf.get_y(), w=size / 2, h=size, style=style)
        pdf.set_x(pdf.get_x() + (size / 2) + margin)
        if counter % 3 == 0:
            next_row(pdf)

    assert_pdf_equal(pdf, HERE / "class_rect_not_square.pdf", tmp_path)


def test_rect_style(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    for counter, style in enumerate(["", "F", "FD", "DF", None]):
        pdf.rect(x=pdf.get_x(), y=pdf.get_y(), w=size, h=size, style=style)
        pdf.set_x(pdf.get_x() + size + margin)
        if counter % 3 == 0:
            next_row(pdf)

    assert_pdf_equal(pdf, HERE / "class_rect_style.pdf", tmp_path)


def test_rect_line_width(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    for line_width in [1, 2, 3]:
        pdf.set_line_width(line_width)
        pdf.rect(x=pdf.get_x(), y=pdf.get_y(), w=size, h=size, style=None)
        pdf.set_x(pdf.get_x() + size + margin)
    next_row(pdf)
    for line_width in [4, 5, 6]:
        pdf.set_line_width(line_width)
        pdf.rect(x=pdf.get_x(), y=pdf.get_y(), w=size, h=size, style=None)
        pdf.set_x(pdf.get_x() + size + margin)
    pdf.set_line_width(0.2)  # reset

    assert_pdf_equal(pdf, HERE / "class_rect_line_width.pdf", tmp_path)


def test_rect_draw_color(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    # Colors
    pdf.set_line_width(0.5)
    for gray in [70, 140, 210]:
        pdf.set_draw_color(gray)
        pdf.rect(x=pdf.get_x(), y=pdf.get_y(), w=size, h=size, style=None)
        pdf.set_x(pdf.get_x() + size + margin)

    assert_pdf_equal(pdf, HERE / "class_rect_draw_color.pdf", tmp_path)


def test_rect_fill_color(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    pdf.set_fill_color(240)
    for color in [[230, 30, 180], [30, 180, 30], [30, 30, 70]]:
        pdf.set_draw_color(*color)
        pdf.rect(x=pdf.get_x(), y=pdf.get_y(), w=size, h=size, style="FD")
        pdf.set_x(pdf.get_x() + size + margin)

    next_row(pdf)

    assert_pdf_equal(pdf, HERE / "class_rect_fill_color.pdf", tmp_path)
