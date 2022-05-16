from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def test_regular_polygon(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()

    # no fill with line
    pdf.regular_polygon(10, 35, 3, 25)
    pdf.regular_polygon(40, 35, 4, 25)
    pdf.regular_polygon(70, 35, 5, 25)
    pdf.regular_polygon(100, 35, 6, 25)
    pdf.regular_polygon(130, 35, 7, 25)
    pdf.regular_polygon(160, 35, 8, 25)

    # fill and color test
    pdf.set_fill_color(134, 200, 15)
    pdf.regular_polygon(10, 75, 3, 25, style="df")
    pdf.regular_polygon(40, 75, 4, 25, style="df")
    pdf.regular_polygon(70, 75, 5, 25, style="df")
    pdf.regular_polygon(100, 75, 6, 25, style="df")
    pdf.regular_polygon(130, 75, 7, 25, style="df")
    pdf.regular_polygon(160, 75, 8, 25, style="df")

    # draw color test
    pdf.set_fill_color(0, 0, 0)
    pdf.set_draw_color(204, 0, 204)
    pdf.regular_polygon(10, 115, 3, 25)
    pdf.regular_polygon(40, 115, 4, 25)
    pdf.regular_polygon(70, 115, 5, 25)
    pdf.regular_polygon(100, 115, 6, 25)
    pdf.regular_polygon(130, 115, 7, 25)
    pdf.regular_polygon(160, 115, 8, 25)

    # line width test
    pdf.set_line_width(1)
    pdf.regular_polygon(10, 155, 3, 25)
    pdf.regular_polygon(40, 155, 4, 25)
    pdf.regular_polygon(70, 155, 5, 25)
    pdf.regular_polygon(100, 155, 6, 25)
    pdf.regular_polygon(130, 155, 7, 25)
    pdf.regular_polygon(160, 155, 8, 25)

    # line color and fill color
    pdf.set_fill_color(3, 190, 252)
    pdf.regular_polygon(10, 195, 3, 25, style="df")
    pdf.regular_polygon(40, 195, 4, 25, style="df")
    pdf.regular_polygon(70, 195, 5, 25, style="df")
    pdf.regular_polygon(100, 195, 6, 25, style="df")
    pdf.regular_polygon(130, 195, 7, 25, style="df")
    pdf.regular_polygon(160, 195, 8, 25, style="df")

    # rotation test
    pdf.set_draw_color(0, 0, 255)
    pdf.regular_polygon(10, 235, 3, 25, 30)
    pdf.regular_polygon(40, 235, 4, 25, 45)
    pdf.regular_polygon(70, 235, 5, 25, 200)
    pdf.regular_polygon(100, 235, 6, 25, 0)
    pdf.regular_polygon(130, 235, 7, 25, 13)
    pdf.regular_polygon(160, 235, 8, 25, 22.5)

    # fill only
    pdf.regular_polygon(10, 275, 3, 25, style="f")
    pdf.regular_polygon(40, 275, 4, 25, style="f")
    pdf.regular_polygon(70, 275, 5, 25, style="f")
    pdf.regular_polygon(100, 275, 6, 25, style="f")
    pdf.regular_polygon(130, 275, 7, 25, style="f")
    pdf.regular_polygon(160, 275, 8, 25, style="f")

    assert_pdf_equal(pdf, HERE / "regular_polygon.pdf", tmp_path)
