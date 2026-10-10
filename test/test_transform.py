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


def test_transform_tilted_title(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    pdf.text(20, 20, "Normal title")

    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.2)
    pdf.line(15, 30, 180, 30)

    title_anchor_x, title_anchor_y = 90, 30
    title_transform = Transform.rotation_d(12).about(title_anchor_x, title_anchor_y)
    with pdf.transform(title_transform):
        pdf.set_font("Times", style="B", size=20)
        pdf.set_text_color(30, 30, 120)
        pdf.text(60, 30, "Tilted Title")

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=9)
    pdf.text(20, 45, "Baseline at y=30")

    assert_pdf_equal(pdf, HERE / "transform_title.pdf", tmp_path)


def test_transform_mirrored_text(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)

    pdf.text(20, 50, "Left block")
    lines = ["Mirror me", "Line two", "Line three"]
    y_pos = 60
    for line in lines:
        pdf.text(20, y_pos, line)
        y_pos += 6

    axis_x = 105
    pdf.set_draw_color(160, 0, 0)
    pdf.set_line_width(0.2)
    pdf.line(axis_x, 40, axis_x, 110)
    pdf.set_text_color(120, 0, 0)
    pdf.text(axis_x + 2, 45, "mirror axis")

    mirror = Transform.scaling(-1, 1).about(axis_x, 0)
    with pdf.transform(mirror):
        pdf.set_text_color(0, 0, 120)
        pdf.text(20, 50, "Right block (mirrored)")
        y_pos = 60
        for line in lines:
            pdf.text(20, y_pos, line)
            y_pos += 6

    pdf.set_text_color(0, 0, 0)

    assert_pdf_equal(pdf, HERE / "transform_mirror.pdf", tmp_path)
