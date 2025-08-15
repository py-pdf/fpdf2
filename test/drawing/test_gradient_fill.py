import math
from pathlib import Path

import pytest
from fpdf import FPDF
from fpdf.pattern import LinearGradient, RadialGradient
from fpdf.drawing import PaintedPath, Transform, GradientPaint, ClippingPath

from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def _new_pdf():
    pdf = FPDF(unit="pt", format="A4")
    pdf.add_page()
    return pdf


def _rect(x, y, w, h):
    return PaintedPath().rectangle(x, y, w, h)

def _circle(cx, cy, r):
    p = PaintedPath().move_to(cx + r, cy)
    p.circle(cx, cy, r)
    return p

def test_linear_gradient_fill_rotated_vs_user_space(tmp_path):
    pdf = _new_pdf()

    # Path A with objectBoundingBox + rotation
    path = _rect(10, 20, 100, 50)
    grad = LinearGradient(0, 0, 1, 0, colors=["#FF0000", "#0000FF"], extend_before=True, extend_after=True)
    M_rot = Transform.rotation(math.radians(30))
    paint = GradientPaint(grad, units="objectBoundingBox", gradient_transform=M_rot)
    path.style.fill_color = paint
    path.style.stroke_color = None

    # Path B with userSpaceOnUse (absolute coords) - rendered as DeviceGray
    path2 = _rect(10, 90, 100, 50)
    grad2 = LinearGradient(10, 0, 110, 0, colors=["#ffffff", "#000000"], extend_before=True, extend_after=True)
    paint2 = GradientPaint(grad2, units="userSpaceOnUse")
    path2.style.fill_color = paint2
    path2.style.stroke_color = None

    with pdf.drawing_context() as dc:
        dc.add_item(path)
        dc.add_item(path2)

    assert_pdf_equal(pdf, HERE / "generated_pdf" / "gradient_linear_rotated_vs_user_space.pdf", tmp_path)


def test_linear_gradient_objbox_scale_translate(tmp_path: Path):
    pdf = _new_pdf()

    p = _rect(150, 40, 180, 90)  # non-uniform aspect
    lg = LinearGradient(0, 0, 1, 1, colors=["#0000FF", "#FFFFFF", "#FF0000"], extend_after=True)
    M = Transform.scaling(1.2, 0.6) @ Transform.translation(0.15, -0.1)  # in gradient space
    p.style.fill_color = GradientPaint(lg, units="objectBoundingBox", gradient_transform=M)
    p.style.stroke_color = None

    with pdf.drawing_context() as dc:
        dc.add_item(p)

    assert_pdf_equal(pdf, HERE / "generated_pdf" / "gradient_linear_scale_translate.pdf", tmp_path)

def test_linear_gradient_userspace_custom_pivot(tmp_path: Path):
    pdf = _new_pdf()

    p = _rect(40, 160, 220, 60)
    pivot_x, pivot_y = 150, 190
    M = (Transform.translation(-pivot_x, -pivot_y) @
         Transform.rotation(math.radians(-25)) @
         Transform.translation(pivot_x, pivot_y))

    lg = LinearGradient(40, 160, 260, 220, colors=["#222222", "#DDDDDD"])
    p.style.fill_color = GradientPaint(lg, units="userSpaceOnUse", gradient_transform=M)
    p.style.stroke_color = None

    with pdf.drawing_context() as dc:
        dc.add_item(p)

    assert_pdf_equal(pdf, HERE / "generated_pdf" / "gradient_userspace_pivot.pdf", tmp_path)

@pytest.mark.parametrize("extend_before,extend_after,basename", [
    (False, False, "stops_no_extend"),
    (True,  False, "stops_extend_before"),
    (False, True,  "stops_extend_after"),
    (True,  True,  "stops_extend_both"),
])
def test_linear_gradient_color_stops_extends(extend_before, extend_after, basename, tmp_path):
    pdf = _new_pdf()

    p = _rect(30, 30, 260, 40)
    p.style.stroke_color = "#000000"
    p.style.stroke_width = 2
    lg = LinearGradient(50, 0, 270, 0, colors=[
        "#0000FF",
        "#00FFFF",
        "#00FF00",
        "#FFFF00",
        "#FF0000"],
        bounds=[0.25, 0.50, 0.75],
        extend_before=extend_before,
        extend_after=extend_after,
    )
    paint = GradientPaint(lg, units="userSpaceOnUse")
    p.style.fill_color = paint
    

    with pdf.drawing_context() as dc:
        dc.add_item(p)

    assert_pdf_equal(pdf, HERE / "generated_pdf" / f"gradient_linear_{basename}.pdf", tmp_path, generate=True)


def test_radial_gradient_objbox_vs_userspace(tmp_path: Path):
    pdf = _new_pdf()

    # Top: objectBoundingBox
    p1 = _circle(140, 420, 50)
    rg1 = RadialGradient(0.5, 0.5, 0.0, 0.5, 0.5, 0.5, colors=["#FFFFFF", "#0000AA"])
    p1.style.fill_color = GradientPaint(rg1, units="objectBoundingBox")
    p1.style.stroke_color = None

    # Bottom: userSpaceOnUse
    p2 = _circle(340, 420, 50)
    rg2 = RadialGradient(340, 420, 0, 340, 420, 60, colors=["#FFFFFF", "#AA0000"])
    p2.style.fill_color = GradientPaint(rg2, units="userSpaceOnUse")
    p2.style.stroke_color = None

    with pdf.drawing_context() as dc:
        dc.add_item(p1)
        dc.add_item(p2)

    assert_pdf_equal(pdf, HERE / "generated_pdf" / "gradient_radial_objbox_userspace.pdf", tmp_path, generate=True)


def test_radial_gradient_focal_offset_extend(tmp_path: Path):
    pdf = _new_pdf()

    p = _rect(40, 480, 260, 120)
    # Circle center at (0.6, 0.5), focal at (0.3, 0.45), radius 0.7 (object bbox units)
    rg = RadialGradient(0.6, 0.5, 0.7, 0.3, 0.45, 0.0,
                        colors=["#FFFFFF", "#00AA00", "#003300"],
                        bounds=[0.6],
                        extend_before=True, extend_after=True)
    p.style.fill_color = GradientPaint(rg, units="objectBoundingBox")
    p.style.stroke_color = None

    with pdf.drawing_context() as dc:
        dc.add_item(p)

    assert_pdf_equal(pdf, HERE / "generated_pdf" / "gradient_radial_focal_extend.pdf", tmp_path, generate=True)

def test_shared_gradient_instance(tmp_path: Path):
    pdf = _new_pdf()

    lg = LinearGradient(0, 0, 1, 0, colors=["#FF0000", "#0000FF"])

    p1 = _rect(40, 40, 100, 40)
    p1.style.fill_color = GradientPaint(lg, units="objectBoundingBox")

    p2 = _rect(160, 40, 100, 40)
    # Different gradientTransform but same LinearGradient object
    p2.style.fill_color = GradientPaint(lg, units="objectBoundingBox",
                                        gradient_transform=Transform.rotation(math.radians(45)))

    with pdf.drawing_context() as dc:
        dc.add_item(p1)
        dc.add_item(p2)

    assert_pdf_equal(pdf, HERE / "generated_pdf" / "gradient_shared.pdf", tmp_path, generate=True)


def test_gradient_fill_with_solid_stroke(tmp_path: Path):
    pdf = _new_pdf()

    p = _rect(300, 20, 120, 50)
    lg = LinearGradient(0, 0, 1, 0, colors=["#FFFFFF", "#000000"])
    p.style.fill_color = GradientPaint(lg, units="objectBoundingBox")
    p.style.stroke_color = "#FF00FF"
    p.style.stroke_width = 3.0

    with pdf.drawing_context() as dc:
        dc.add_item(p)

    assert_pdf_equal(pdf, HERE / "generated_pdf" / "gradient_with_stroke.pdf", tmp_path, generate=True)


# --- 12) Two pages: same content, confirm resource reuse (XObject/Pattern reuse) ----

def test_gradients_across_pages_resource_reuse(tmp_path: Path):
    pdf = FPDF(unit="pt", format="A4")
    pdf.set_compression(False)

    # Page 1
    pdf.add_page()
    p1 = _rect(60, 100, 220, 70)
    lg = LinearGradient(0, 0, 1, 0, colors=["#222222", "#EEEEEE"])
    p1.style.fill_color = GradientPaint(lg, units="objectBoundingBox")
    p1.style.stroke_color = None
    with pdf.drawing_context() as dc:
        dc.add_item(p1)

    # Page 2 (same gradient again)
    pdf.add_page()
    p2 = _rect(60, 100, 220, 70)
    p2.style.fill_color = GradientPaint(lg, units="objectBoundingBox")
    p2.style.stroke_color = None
    with pdf.drawing_context() as dc:
        dc.add_item(p2)

    assert_pdf_equal(pdf, HERE / "generated_pdf" / "gradient_linear_different_pages.pdf", tmp_path, generate=True)
    