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
    pdf.star(x=15, y=y, r_in=5, r_out=15, corners=3, style="D")
    pdf.star(x=45, y=y, r_in=5, r_out=15, corners=4, style="D")
    pdf.star(x=75, y=y, r_in=5, r_out=15, corners=5, style="D")
    pdf.star(x=105, y=y, r_in=5, r_out=15, corners=6, style="D")
    pdf.star(x=135, y=y, r_in=5, r_out=15, corners=7, style="D")
    pdf.star(x=165, y=y, r_in=5, r_out=15, corners=8, style="D")
    pdf.star(x=195, y=y, r_in=5, r_out=15, corners=9, style="D")

    # fill and color test
    y += 40
    pdf.set_fill_color(r=134, g=200, b=15)
    pdf.star(x=15, y=y, r_in=5, r_out=15, corners=3, style="DF")
    pdf.star(x=45, y=y, r_in=5, r_out=15, corners=4, style="DF")
    pdf.star(x=75, y=y, r_in=5, r_out=15, corners=5, style="DF")
    pdf.star(x=105, y=y, r_in=5, r_out=15, corners=6, style="DF")
    pdf.star(x=135, y=y, r_in=5, r_out=15, corners=7, style="DF")
    pdf.star(x=165, y=y, r_in=5, r_out=15, corners=8, style="DF")
    pdf.star(x=195, y=y, r_in=5, r_out=15, corners=9, style="DF")

    # draw color test
    y += 40
    pdf.set_fill_color(r=0, g=0, b=0)
    pdf.set_draw_color(r=204, g=0, b=204)
    pdf.star(x=15, y=y, r_in=5, r_out=15, corners=3, style="D")
    pdf.star(x=45, y=y, r_in=5, r_out=15, corners=4, style="D")
    pdf.star(x=75, y=y, r_in=5, r_out=15, corners=5, style="D")
    pdf.star(x=105, y=y, r_in=5, r_out=15, corners=6, style="D")
    pdf.star(x=135, y=y, r_in=5, r_out=15, corners=7, style="D")
    pdf.star(x=165, y=y, r_in=5, r_out=15, corners=8, style="D")
    pdf.star(x=195, y=y, r_in=5, r_out=15, corners=9, style="D")

    # line width test
    y += 40
    pdf.set_line_width(1)
    pdf.star(x=15, y=y, r_in=5, r_out=15, corners=3, style="D")
    pdf.star(x=45, y=y, r_in=5, r_out=15, corners=4, style="D")
    pdf.star(x=75, y=y, r_in=5, r_out=15, corners=5, style="D")
    pdf.star(x=105, y=y, r_in=5, r_out=15, corners=6, style="D")
    pdf.star(x=135, y=y, r_in=5, r_out=15, corners=7, style="D")
    pdf.star(x=165, y=y, r_in=5, r_out=15, corners=8, style="D")
    pdf.star(x=195, y=y, r_in=5, r_out=15, corners=9, style="D")

    # line color and fill color
    y += 40
    pdf.set_fill_color(r=3, g=190, b=252)
    pdf.star(x=15, y=y, r_in=5, r_out=15, corners=3, style="DF")
    pdf.star(x=45, y=y, r_in=5, r_out=15, corners=4, style="DF")
    pdf.star(x=75, y=y, r_in=5, r_out=15, corners=5, style="DF")
    pdf.star(x=105, y=y, r_in=5, r_out=15, corners=6, style="DF")
    pdf.star(x=135, y=y, r_in=5, r_out=15, corners=7, style="DF")
    pdf.star(x=165, y=y, r_in=5, r_out=15, corners=8, style="DF")
    pdf.star(x=195, y=y, r_in=5, r_out=15, corners=9, style="DF")

    # fill only
    y += 40
    pdf.set_draw_color(r=0, g=0, b=255)
    pdf.star(x=15, y=y, r_in=5, r_out=15, corners=3, style="F")
    pdf.star(x=45, y=y, r_in=5, r_out=15, corners=4, style="F")
    pdf.star(x=75, y=y, r_in=5, r_out=15, corners=5, style="F")
    pdf.star(x=105, y=y, r_in=5, r_out=15, corners=6, style="F")
    pdf.star(x=135, y=y, r_in=5, r_out=15, corners=7, style="F")
    pdf.star(x=165, y=y, r_in=5, r_out=15, corners=8, style="F")
    pdf.star(x=195, y=y, r_in=5, r_out=15, corners=9, style="F")

    # rotation test
    y += 40
    pdf.set_draw_color(r=0, g=0, b=255)
    pdf.star(x=15, y=y, r_in=5, r_out=15, corners=3, rotate_degrees=0, style="DF")
    pdf.star(x=45, y=y, r_in=5, r_out=15, corners=4, rotate_degrees=35, style="DF")
    pdf.star(x=75, y=y, r_in=5, r_out=15, corners=5, rotate_degrees=45, style="DF")
    pdf.star(x=105, y=y, r_in=5, r_out=15, corners=6, rotate_degrees=200, style="DF")
    pdf.star(x=135, y=y, r_in=5, r_out=15, corners=7, rotate_degrees=13, style="DF")
    pdf.star(x=165, y=y, r_in=5, r_out=15, corners=8, rotate_degrees=22.5, style="DF")
    pdf.star(x=195, y=y, r_in=5, r_out=15, corners=9, rotate_degrees=77.3, style="DF")

    assert_pdf_equal(pdf, HERE / "regular_star.pdf", tmp_path)


def test_star_invalid_style():
    pdf = fpdf.FPDF()
    pdf.add_page()

    with pytest.raises(ValueError):
        pdf.star(x=15, y=15, r_in=5, r_out=15, corners=3, rotate_degrees=0, style="N")
