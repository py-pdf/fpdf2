from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def test_regular_polygon(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()

    # no fill with line
    pdf.regular_polygon(x=10, y=35, num_sides=3, poly_width=25)
    pdf.regular_polygon(x=40, y=35, num_sides=4, poly_width=25)
    pdf.regular_polygon(x=70, y=35, num_sides=5, poly_width=25)
    pdf.regular_polygon(x=100, y=35, num_sides=6, poly_width=25)
    pdf.regular_polygon(x=130, y=35, num_sides=7, poly_width=25)
    pdf.regular_polygon(x=160, y=35, num_sides=8, poly_width=25)

    # fill and color test
    pdf.set_fill_color(r=134, g=200, b=15)
    pdf.regular_polygon(x=10, y=75, num_sides=3, poly_width=25, style="df")
    pdf.regular_polygon(x=40, y=75, num_sides=4, poly_width=25, style="df")
    pdf.regular_polygon(x=70, y=75, num_sides=5, poly_width=25, style="df")
    pdf.regular_polygon(x=100, y=75, num_sides=6, poly_width=25, style="df")
    pdf.regular_polygon(x=130, y=75, num_sides=7, poly_width=25, style="df")
    pdf.regular_polygon(x=160, y=75, num_sides=8, poly_width=25, style="df")

    # draw color test
    pdf.set_fill_color(r=0, g=0, b=0)
    pdf.set_draw_color(r=204, g=0, b=204)
    pdf.regular_polygon(x=10, y=115, num_sides=3, poly_width=25)
    pdf.regular_polygon(x=40, y=115, num_sides=4, poly_width=25)
    pdf.regular_polygon(x=70, y=115, num_sides=5, poly_width=25)
    pdf.regular_polygon(x=100, y=115, num_sides=6, poly_width=25)
    pdf.regular_polygon(x=130, y=115, num_sides=7, poly_width=25)
    pdf.regular_polygon(x=160, y=115, num_sides=8, poly_width=25)

    # line width test
    pdf.set_line_width(1)
    pdf.regular_polygon(x=10, y=155, num_sides=3, poly_width=25)
    pdf.regular_polygon(x=40, y=155, num_sides=4, poly_width=25)
    pdf.regular_polygon(x=70, y=155, num_sides=5, poly_width=25)
    pdf.regular_polygon(x=100, y=155, num_sides=6, poly_width=25)
    pdf.regular_polygon(x=130, y=155, num_sides=7, poly_width=25)
    pdf.regular_polygon(x=160, y=155, num_sides=8, poly_width=25)

    # line color and fill color
    pdf.set_fill_color(r=3, g=190, b=252)
    pdf.regular_polygon(x=10, y=195, num_sides=3, poly_width=25, style="df")
    pdf.regular_polygon(x=40, y=195, num_sides=4, poly_width=25, style="df")
    pdf.regular_polygon(x=70, y=195, num_sides=5, poly_width=25, style="df")
    pdf.regular_polygon(x=100, y=195, num_sides=6, poly_width=25, style="df")
    pdf.regular_polygon(x=130, y=195, num_sides=7, poly_width=25, style="df")
    pdf.regular_polygon(x=160, y=195, num_sides=8, poly_width=25, style="df")

    # rotation test
    pdf.set_draw_color(r=0, g=0, b=255)
    pdf.regular_polygon(x=10, y=235, num_sides=3, poly_width=25, rotate_degrees=30)
    pdf.regular_polygon(x=40, y=235, num_sides=4, poly_width=25, rotate_degrees=45)
    pdf.regular_polygon(x=70, y=235, num_sides=5, poly_width=25, rotate_degrees=200)
    pdf.regular_polygon(x=100, y=235, num_sides=6, poly_width=25, rotate_degrees=0)
    pdf.regular_polygon(x=130, y=235, num_sides=7, poly_width=25, rotate_degrees=13)
    pdf.regular_polygon(x=160, y=235, num_sides=8, poly_width=25, rotate_degrees=22.5)

    # fill only
    pdf.regular_polygon(x=10, y=275, num_sides=3, poly_width=25, style="f")
    pdf.regular_polygon(x=40, y=275, num_sides=4, poly_width=25, style="f")
    pdf.regular_polygon(x=70, y=275, num_sides=5, poly_width=25, style="f")
    pdf.regular_polygon(x=100, y=275, num_sides=6, poly_width=25, style="f")
    pdf.regular_polygon(x=130, y=275, num_sides=7, poly_width=25, style="f")
    pdf.regular_polygon(x=160, y=275, num_sides=8, poly_width=25, style="f")

    assert_pdf_equal(pdf, HERE / "regular_polygon.pdf", tmp_path)
