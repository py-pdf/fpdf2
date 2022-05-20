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


def test_round_corners_rect(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()

    # no fill diferent sizes test
    y = 10
    pdf.rect(10, y, 15, 20, round_corners=True, style="D")
    pdf.rect(30, y, 20, 15, round_corners=True, style="D")
    pdf.rect(60, y, 33, 28, round_corners=True, style="D")
    pdf.rect(100, y, 50, 10, round_corners=True, style="D")
    pdf.rect(160, y, 10, 10, round_corners=True, style="D")

    # no fill different corners
    y += 35
    pdf.rect(10, y, 15, 20, round_corners=("TOP_LEFT"), style="D")
    pdf.rect(30, y, 20, 15, round_corners=("TOP_RIGHT"), style="D")
    pdf.rect(60, y, 33, 28, round_corners=("BOTTOM_LEFT"), style="D")
    pdf.rect(100, y, 50, 10, round_corners=("BOTTOM_RIGHT"), style="D")
    pdf.rect(160, y, 10, 10, round_corners=("TOP_LEFT"), style="D")

    # no fill multiple corners
    y += 35
    pdf.rect(10, y, 15, 20, round_corners=("TOP_LEFT", "BOTTOM_RIGHT"), style="D")
    pdf.rect(30, y, 20, 15, round_corners=("TOP_RIGHT", "TOP_LEFT"), style="D")
    pdf.rect(
        60,
        y,
        33,
        28,
        round_corners=("BOTTOM_LEFT", "BOTTOM_RIGHT", "TOP_LEFT"),
        style="D",
    )
    pdf.rect(
        100,
        y,
        50,
        10,
        round_corners=("BOTTOM_RIGHT", "TOP_RIGHT", "TOP_LEFT"),
        style="D",
    )
    pdf.rect(160, y, 10, 10, round_corners=("TOP_LEFT", "BOTTOM_LEFT"), style="D")

    # fill color diferent sizes test
    pdf.set_fill_color(0, 255, 0)
    y += 35
    pdf.rect(10, y, 15, 20, round_corners=True, style="DF")
    pdf.rect(30, y, 20, 15, round_corners=True, style="DF")
    pdf.rect(60, y, 33, 28, round_corners=True, style="DF")
    pdf.rect(100, y, 50, 10, round_corners=True, style="DF")
    pdf.rect(160, y, 10, 10, round_corners=True, style="DF")

    # fill different corners
    y += 35
    pdf.rect(10, y, 15, 20, round_corners=("TOP_LEFT"), style="DF")
    pdf.rect(30, y, 20, 15, round_corners=("TOP_RIGHT"), style="DF")
    pdf.rect(60, y, 33, 28, round_corners=("BOTTOM_LEFT"), style="DF")
    pdf.rect(100, y, 50, 10, round_corners=("BOTTOM_RIGHT"), style="DF")
    pdf.rect(160, y, 10, 10, round_corners=("TOP_LEFT"), style="DF")

    # fill multiple corners
    y += 35
    pdf.rect(10, y, 15, 20, round_corners=("TOP_LEFT", "BOTTOM_RIGHT"), style="DF")
    pdf.rect(30, y, 20, 15, round_corners=("TOP_RIGHT", "TOP_LEFT"), style="DF")
    pdf.rect(
        60,
        y,
        33,
        28,
        round_corners=("BOTTOM_LEFT", "BOTTOM_RIGHT", "TOP_LEFT"),
        style="DF",
    )
    pdf.rect(
        100,
        y,
        50,
        10,
        round_corners=("BOTTOM_RIGHT", "TOP_RIGHT", "TOP_LEFT"),
        style="DF",
    )
    pdf.rect(160, y, 10, 10, round_corners=("TOP_LEFT", "BOTTOM_LEFT"), style="DF")

    # fill only different corners
    pdf.set_fill_color(255, 255, 0)
    y += 35
    pdf.rect(10, y, 15, 20, round_corners=("TOP_LEFT"), style="F")
    pdf.rect(30, y, 20, 15, round_corners=("TOP_RIGHT"), style="F")
    pdf.rect(60, y, 33, 28, round_corners=("BOTTOM_LEFT"), style="F")
    pdf.rect(100, y, 50, 10, round_corners=("BOTTOM_RIGHT"), style="F")
    pdf.rect(160, y, 10, 10, round_corners=("TOP_LEFT"), style="F")

    # fill only multiple corners
    y += 35
    pdf.rect(10, y, 15, 20, round_corners=("TOP_LEFT", "BOTTOM_RIGHT"), style="F")
    pdf.rect(30, y, 20, 15, round_corners=("TOP_RIGHT", "TOP_LEFT"), style="F")
    pdf.rect(
        60,
        y,
        33,
        28,
        round_corners=("BOTTOM_LEFT", "BOTTOM_RIGHT", "TOP_LEFT"),
        style="F",
    )
    pdf.rect(
        100,
        y,
        50,
        10,
        round_corners=("BOTTOM_RIGHT", "TOP_RIGHT", "TOP_LEFT"),
        style="F",
    )
    pdf.rect(160, y, 10, 10, round_corners=("TOP_LEFT", "BOTTOM_LEFT"), style="F")

    assert_pdf_equal(pdf, HERE / "class_round_corners_rect.pdf", tmp_path)
