from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def draw_points(pdf, point_lists):
    for pl in point_lists:
        for p in pl:
            pdf.circle(x=p[0] + 0.5, y=p[1] + 0.5, radius=0.5, style="FD")


def test_quadratic_beziers(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    pl1 = [(20, 40), (40, 20), (60, 40)]
    pl2 = [(20, 80), (50, 100), (60, 80)]
    pl3 = [(20, 120), (40, 110), (60, 120)]
    pl4 = [(20, 170), (40, 160), (60, 170)]
    pl5 = [[20, 230], (40, 280), (60, 250)]

    pdf.set_fill_color(r=255, g=0, b=0)
    pdf.bezier(pl1, style="DF")
    pdf.set_fill_color(r=0, g=255, b=0)
    pdf.bezier(pl2, style="DF")
    pdf.set_fill_color(r=0, g=0, b=255)
    pdf.bezier(pl3, style="DF", closed=True)
    pdf.bezier(pl4, style="F")
    pdf.bezier(pl5, style="D")

    draw_points(pdf, [pl1, pl2, pl3, pl4, pl5])

    assert_pdf_equal(pdf, HERE / "quadratic_bezier_curve.pdf", tmp_path)


def test_cubic_beziers(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    pl1 = [(120, 40), (140, 30), (160, 49), (180, 50)]
    pl2 = [(120, 80), (150, 100), (160, 80), (180, 80)]
    pl3 = [(120, 120), (140, 130), (160, 140), (180, 120)]
    pl4 = [(20, 20), (40, 10), (60, 20)]
    pl5 = [[20, 80], (40, 90), (60, 80)]

    pdf.set_fill_color(r=255, g=0, b=0)
    pdf.bezier(pl1, style="DF")
    pdf.set_fill_color(r=0, g=255, b=0)
    pdf.bezier(pl2, style="DF")
    pdf.set_fill_color(r=0, g=0, b=255)
    pdf.bezier(pl3, style="DF", closed=True)
    pdf.bezier(pl4, style="F")
    pdf.bezier(pl5, style="D")

    draw_points(pdf, [pl1, pl2, pl3, pl4, pl5])

    assert_pdf_equal(pdf, HERE / "cubic_bezier_curve.pdf", tmp_path)


def test_bezier_line_settings(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    pl1 = [(120, 40), (140, 30), (160, 49), (180, 50)]
    pl2 = [(20, 80), (50, 100), (60, 80)]

    pdf.set_fill_color(r=255, g=0, b=0)
    pdf.set_dash_pattern(dash=2, gap=3)
    pdf.bezier(pl1, style="DF")

    pdf.set_fill_color(r=0, g=255, b=0)
    pdf.set_dash_pattern(dash=4, gap=6)
    pdf.set_line_width(2)
    pdf.bezier(pl2, style="DF")

    # Reset for drawing points
    pdf.set_line_width(0.2)
    pdf.set_dash_pattern(0, 0, 0)

    draw_points(pdf, [pl1, pl2])

    assert_pdf_equal(pdf, HERE / "bezier_curve_line_settings.pdf", tmp_path)


def test_bezier_chaining(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    pdf.x, pdf.y = 20, pdf.h / 4 - 30
    pdf.cell(text="Chaining cubic curves:")
    for i in range(4):
        shift = 20 if i % 2 else -20
        x1, y1 = (3 * i + 1) * pdf.w / 14, pdf.h / 4
        x2, y2 = (3 * i + 2) * pdf.w / 14, pdf.h / 4 + shift
        x3, y3 = (3 * i + 3) * pdf.w / 14, pdf.h / 4 + shift
        x4, y4 = (3 * i + 4) * pdf.w / 14, pdf.h / 4
        pdf.set_draw_color(
            {
                0: "#000",
                1: "#f00",
                2: "#0f0",
                3: "#00f",
            }[i % 4]
        )
        pdf.circle(x=x1, y=y1, radius=0.5)
        pdf.circle(x=x2, y=y2, radius=0.5)
        pdf.circle(x=x3, y=y3, radius=0.5)
        pdf.circle(x=x4, y=y4, radius=0.5)
        pdf.bezier(((x1, y1), (x2, y2), (x3, y3), (x4, y4)))

    pdf.x, pdf.y = 20, pdf.h / 2 - 30
    pdf.cell(text="Chaining quadratic curves:")
    for i in range(4):
        shift = 20 if i % 2 else -20
        x1, y1 = (2 * i + 1) * pdf.w / 10, pdf.h / 2
        x2, y2 = (2 * i + 2) * pdf.w / 10, pdf.h / 2 + shift
        x3, y3 = (2 * i + 3) * pdf.w / 10, pdf.h / 2
        pdf.set_draw_color(
            {
                0: "#f00",
                1: "#0f0",
                2: "#00f",
            }[i % 3]
        )
        pdf.circle(x=x1, y=y1, radius=0.5)
        pdf.circle(x=x2, y=y2, radius=0.5)
        pdf.circle(x=x3, y=y3, radius=0.5)
        pdf.bezier(((x1, y1), (x2, y2), (x3, y3)))

    assert_pdf_equal(pdf, HERE / "bezier_chaining.pdf", tmp_path)
