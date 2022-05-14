from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal

import pytest


HERE = Path(__file__).resolve().parent


def test_star(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()

    # no fill with line test
    y = 20
    pdf.star(15, y, 5, 15, 3, style="D")
    pdf.star(45, y, 5, 15, 4, style="D")
    pdf.star(75, y, 5, 15, 5, style="D")
    pdf.star(105, y, 5, 15, 6, style="D")
    pdf.star(135, y, 5, 15, 7, style="D")
    pdf.star(165, y, 5, 15, 8, style="D")
    pdf.star(195, y, 5, 15, 9, style="D")

    # fill and color test
    y += 40
    pdf.set_fill_color(134, 200, 15)
    pdf.star(15, y, 5, 15, 3, style="DF")
    pdf.star(45, y, 5, 15, 4, style="DF")
    pdf.star(75, y, 5, 15, 5, style="DF")
    pdf.star(105, y, 5, 15, 6, style="DF")
    pdf.star(135, y, 5, 15, 7, style="DF")
    pdf.star(165, y, 5, 15, 8, style="DF")
    pdf.star(195, y, 5, 15, 9, style="DF")

    # draw color test
    y += 40
    pdf.set_fill_color(0, 0, 0)
    pdf.set_draw_color(204, 0, 204)
    pdf.star(15, y, 5, 15, 3, style="D")
    pdf.star(45, y, 5, 15, 4, style="D")
    pdf.star(75, y, 5, 15, 5, style="D")
    pdf.star(105, y, 5, 15, 6, style="D")
    pdf.star(135, y, 5, 15, 7, style="D")
    pdf.star(165, y, 5, 15, 8, style="D")
    pdf.star(195, y, 5, 15, 9, style="D")

    # line width test
    y += 40
    pdf.set_line_width(1)
    pdf.star(15, y, 5, 15, 3, style="D")
    pdf.star(45, y, 5, 15, 4, style="D")
    pdf.star(75, y, 5, 15, 5, style="D")
    pdf.star(105, y, 5, 15, 6, style="D")
    pdf.star(135, y, 5, 15, 7, style="D")
    pdf.star(165, y, 5, 15, 8, style="D")
    pdf.star(195, y, 5, 15, 9, style="D")

    # line color and fill color
    y += 40
    pdf.set_fill_color(3, 190, 252)
    pdf.star(15, y, 5, 15, 3, style="DF")
    pdf.star(45, y, 5, 15, 4, style="DF")
    pdf.star(75, y, 5, 15, 5, style="DF")
    pdf.star(105, y, 5, 15, 6, style="DF")
    pdf.star(135, y, 5, 15, 7, style="DF")
    pdf.star(165, y, 5, 15, 8, style="DF")
    pdf.star(195, y, 5, 15, 9, style="DF")

    # fill only
    y += 40
    pdf.set_draw_color(0, 0, 255)
    pdf.star(15, y, 5, 15, 3, style="F")
    pdf.star(45, y, 5, 15, 4, style="F")
    pdf.star(75, y, 5, 15, 5, style="F")
    pdf.star(105, y, 5, 15, 6, style="F")
    pdf.star(135, y, 5, 15, 7, style="F")
    pdf.star(165, y, 5, 15, 8, style="F")
    pdf.star(195, y, 5, 15, 9, style="F")

    # rotation test
    y += 40
    pdf.set_draw_color(0, 0, 255)
    pdf.star(15, y, 5, 15, 3, rotateDegrees=0, style="DF")
    pdf.star(45, y, 5, 15, 4, rotateDegrees=35, style="DF")
    pdf.star(75, y, 5, 15, 5, rotateDegrees=45, style="DF")
    pdf.star(105, y, 5, 15, 6, rotateDegrees=200, style="DF")
    pdf.star(135, y, 5, 15, 7, rotateDegrees=13, style="DF")
    pdf.star(165, y, 5, 15, 8, rotateDegrees=22.5, style="DF")
    pdf.star(195, y, 5, 15, 9, rotateDegrees=77.3, style="DF")

    assert_pdf_equal(pdf, HERE / "regular_star.pdf", tmp_path)


def test_star_invalid_style():
    pdf = fpdf.FPDF()
    pdf.add_page()

    with pytest.raises(ValueError):
        pdf.star(15, 15, 5, 15, 3, rotateDegrees=0, style="N")
