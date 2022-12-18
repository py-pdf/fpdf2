from pathlib import Path
from pytest import warns

import fpdf
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def next_row(pdf):
    pdf.ln()
    pdf.set_y(pdf.get_y() + size + margin)


size = 50
margin = 10


def test_line(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    def draw_diagonal_line(pdf, x, y):
        pdf.line(x, y, x + size, y + size / 2)

    for width in [0.71, 1, 2]:
        pdf.set_line_width(width)
        draw_diagonal_line(pdf, pdf.get_x(), pdf.get_y())
        pdf.set_x(pdf.get_x() + size + margin)
    next_row(pdf)

    for color in [70, 140, 200]:
        pdf.set_draw_color(color)
        draw_diagonal_line(pdf, pdf.get_x(), pdf.get_y())
        pdf.set_x(pdf.get_x() + size + margin)
    next_row(pdf)

    assert_pdf_equal(pdf, HERE / "class_line.pdf", tmp_path)


def test_dash(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    def draw_diagonal_dash(pdf, x, y, *a, **k):
        with warns(DeprecationWarning):
            pdf.dashed_line(x, y, x + size, y + size / 2, *a, **k)

    for width in [0.71, 1, 2]:
        pdf.set_line_width(width)
        draw_diagonal_dash(pdf, pdf.get_x(), pdf.get_y(), margin, margin / 2)
        pdf.set_x(pdf.get_x() + size + margin)
    next_row(pdf)

    for color in [70, 140, 200]:
        pdf.set_draw_color(color)
        draw_diagonal_dash(pdf, pdf.get_x(), pdf.get_y(), margin, margin / 2)
        pdf.set_x(pdf.get_x() + size + margin)
    next_row(pdf)

    pdf.set_draw_color(0)
    pdf.set_line_width(0.2)
    draw_diagonal_dash(pdf, pdf.get_x(), pdf.get_y(), margin, margin)

    pdf.set_x(pdf.get_x() + size + margin)
    draw_diagonal_dash(pdf, pdf.get_x(), pdf.get_y(), margin / 2, margin)

    next_row(pdf)
    pdf.set_line_width(1)
    with warns(DeprecationWarning):
        x, y = pdf.get_x(), pdf.get_y()
        pdf.dashed_line(x, y, x + 100, y + 80, 10, 3)
        pdf.set_x(pdf.get_x() + 20)
        x, y = pdf.get_x(), pdf.get_y()
        pdf.dashed_line(x, y, x + 100, y + 80, 3, 20)
        pdf.set_x(pdf.get_x() + 20)
        x, y = pdf.get_x(), pdf.get_y()
        pdf.dashed_line(x, y, x + 100, y + 80, 6, 17)

    assert_pdf_equal(pdf, HERE / "class_dash.pdf", tmp_path)
