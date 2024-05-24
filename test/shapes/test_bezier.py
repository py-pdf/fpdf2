from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def draw_points(pdf, point_list1, point_list2, point_list3):
    for p1, p2, p3 in zip(point_list1, point_list2, point_list3):
        pdf.circle(x=p1[0], y=p1[1], r=1, style="FD")
        pdf.circle(x=p2[0], y=p2[1], r=1, style="FD")
        pdf.circle(x=p3[0], y=p3[1], r=1, style="FD")


def test_three_quadratic_beziers(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    point_list1 = [(20, 40), (40, 20), (60, 40)]
    point_list2 = [(20, 80), (50, 100), (60, 80)]
    point_list3 = [(20, 120), (40, 110), (60, 120)]

    pdf.set_fill_color(r=255, g=0, b=0)
    pdf.bezier(point_list1)
    pdf.set_fill_color(r=0, g=255, b=0)
    pdf.bezier(point_list2)
    pdf.set_fill_color(r=0, g=0, b=255)
    pdf.bezier(point_list3, closed=True)

    draw_points(pdf, point_list1, point_list2, point_list3)

    assert_pdf_equal(pdf, HERE / "quadratic_bezier_curve.pdf", tmp_path)


def test_three_cubic_beziers(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    point_list1 = [(120, 40), (140, 30), (160, 49), (180, 50)]
    point_list2 = [(120, 80), (150, 100), (160, 80), (180, 80)]
    point_list3 = [(120, 120), (140, 130), (160, 140), (180, 120)]

    pdf.set_fill_color(r=255, g=0, b=0)
    pdf.bezier(point_list1)
    pdf.set_fill_color(r=0, g=255, b=0)
    pdf.bezier(point_list2)
    pdf.set_fill_color(r=0, g=0, b=255)
    pdf.bezier(point_list3, closed=True)

    draw_points(pdf, point_list1, point_list2, point_list3)

    assert_pdf_equal(pdf, HERE / "cubic_bezier_curve.pdf", tmp_path)