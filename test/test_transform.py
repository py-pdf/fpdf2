import math
from fpdf import FPDF
from fpdf.drawing_primitives import Transform
from pathlib import Path
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_transform_isolation(tmp_path):
    """
    Verifies that the transformation is strictly isolated to the 'with' block
    and does not leak to subsequent drawings.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)

    w, h = 30, 20
    y_pos = 50

    pdf.set_draw_color(0, 0, 0)  # Black
    pdf.set_line_width(0.5)
    pdf.text(20, y_pos - 5, "1. Before (Normal)")
    pdf.rect(20, y_pos, w, h)

    x_center = 80

    cx, cy = x_center + w / 2, y_pos + h / 2

    t_complex = (
        Transform.translation(cx, cy)
        @ Transform.rotation(math.radians(20))
        @ Transform.shearing(x=math.radians(10), y=0)
        @ Transform.translation(-cx, -cy)
    )

    pdf.set_draw_color(220, 50, 50)  # Red

    with pdf.transform(t_complex):
        pdf.text(x_center, y_pos - 5, "2. Inside (Transformed)")
        pdf.rect(x_center, y_pos, w, h)
    pdf.set_draw_color(0, 0, 0)
    x_right = 140

    pdf.text(x_right, y_pos - 5, "3. After (Normal)")
    pdf.rect(x_right, y_pos, w, h)

    assert_pdf_equal(pdf, HERE / "transform.pdf", tmp_path)
