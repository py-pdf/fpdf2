from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def draw_points(pdf, pl1, pl2, pl3, pl4, pl5):
    for p1, p2, p3, p4, p5 in zip(pl1, pl2, pl3, pl4, pl5):
        pdf.circle(x=p1[0], y=p1[1], r=1, style="FD")
        pdf.circle(x=p2[0], y=p2[1], r=1, style="FD")
        pdf.circle(x=p3[0], y=p3[1], r=1, style="FD")
        pdf.circle(x=p4[0], y=p4[1], r=1, style="FD")
        pdf.circle(x=p5[0], y=p5[1], r=1, style="FD")


def test_quadratic_beziers(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    pl1 = [(20, 40), (40, 20), (60, 40)]
    pl2 = [(20, 80), (50, 100), (60, 80)]
    pl3 = [(20, 120), (40, 110), (60, 120)]
    pl4 = [(20, 170), (40, 160), (60, 170)]
    pl5 = [[20, 230], (40, 280), (60, 250)]

    pdf.set_fill_color(r=255, g=0, b=0)
    pdf.bezier(pl1)
    pdf.set_fill_color(r=0, g=255, b=0)
    pdf.bezier(pl2)
    pdf.set_fill_color(r=0, g=0, b=255)
    pdf.bezier(pl3, closed=True)
    pdf.bezier(pl4, style="F")
    pdf.bezier(pl5, style="D")

    draw_points(pdf, pl1, pl2, pl3, pl4, pl5)

    assert_pdf_equal(pdf, HERE / "quadratic_bezier_curve.pdf", tmp_path, generate=True)


def test_cubic_beziers(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    pl1 = [(120, 40), (140, 30), (160, 49), (180, 50)]
    pl2 = [(120, 80), (150, 100), (160, 80), (180, 80)]
    pl3 = [(120, 120), (140, 130), (160, 140), (180, 120)]
    pl4 = [(20, 20), (40, 10), (60, 20)]
    pl5 = [[20, 80], (40, 90), (60, 80)]

    pdf.set_fill_color(r=255, g=0, b=0)
    pdf.bezier(pl1)
    pdf.set_fill_color(r=0, g=255, b=0)
    pdf.bezier(pl2)
    pdf.set_fill_color(r=0, g=0, b=255)
    pdf.bezier(pl3, closed=True)
    pdf.bezier(pl4, style="F")
    pdf.bezier(pl5, style="D")

    draw_points(pdf, pl1, pl2, pl3, pl4, pl5)

    assert_pdf_equal(pdf, HERE / "cubic_bezier_curve.pdf", tmp_path, generate=True)
