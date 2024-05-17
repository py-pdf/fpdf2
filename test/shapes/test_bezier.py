from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent

'''
import fpdf
import test.conftest
pdf = fpdf.FPDF()
pdf.add_page()
b1= [(20, 40), (40, 20), (60, 40)]
b2 = [(20, 80), (50, 100), (60, 80)]
b3 = [(20, 120), (40, 110), (60, 120)]
pdf.set_fill_color(r=255, g=0, b=0)
pdf.bezier(b1)
pdf.set_fill_color(r=0, g=255, b=0)
pdf.bezier(b2)
pdf.set_fill_color(r=0, g=0, b=255)
pdf.bezier(b3)
assert_pdf_equal(pdf, 
    HERE / "cubic_bezier_curve.pdf", 
    tmp_path,
    generate=True
)

'''
point_list1 = [(20, 40), (40, 20), (60, 40)]
point_list2 = [(20, 80), (50, 100), (60, 80)]
point_list3 = [(20, 120), (40, 110), (60, 120)]


def test_three_cubic_beziers(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    pdf.set_fill_color(r=255, g=0, b=0)
    pdf.bezier(point_list1)
    pdf.set_fill_color(r=0, g=255, b=0)
    pdf.bezier(point_list2)
    pdf.set_fill_color(r=0, g=0, b=255)
    pdf.bezier(point_list3)

    assert_pdf_equal(pdf, HERE / "cubic_bezier_curve.pdf", tmp_path)

