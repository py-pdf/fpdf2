import math
from pathlib import Path

import pytest
from fpdf import FPDF
from fpdf.pattern import (
    LinearGradient,
    RadialGradient,
    shape_linear_gradient,
    shape_radial_gradient,
)
from fpdf.drawing import PaintedPath, Transform, GradientPaint

from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def _new_pdf():
    pdf = FPDF(unit="pt", format="A4")
    pdf.add_page()
    return pdf


def _rect(x, y, w, h):
    return PaintedPath().rectangle(x, y, w, h)


def _circle(cx, cy, r):
    circle = PaintedPath().move_to(cx + r, cy)
    circle.circle(cx, cy, r)
    return circle


def test_linear_gradient_fill_rotated_vs_user_space(tmp_path):
    pdf = _new_pdf()

    # Path A with objectBoundingBox + rotation
    path = _rect(10, 20, 100, 50)
    gradient = LinearGradient(
        0, 0, 1, 0, colors=["#FF0000", "#0000FF"], extend_before=True, extend_after=True
    )
    matrix_rotation = Transform.rotation(math.radians(30))
    paint = GradientPaint(
        gradient, units="objectBoundingBox", gradient_transform=matrix_rotation
    )
    path.style.fill_color = paint
    path.style.stroke_color = None

    # Path B with userSpaceOnUse (absolute coords) - rendered as DeviceGray
    path2 = _rect(10, 90, 100, 50)
    gradient2 = LinearGradient(
        10,
        0,
        110,
        0,
        colors=["#ffffff", "#000000"],
        extend_before=True,
        extend_after=True,
    )
    paint2 = GradientPaint(gradient2, units="userSpaceOnUse")
    path2.style.fill_color = paint2
    path2.style.stroke_color = None

    with pdf.drawing_context() as dc:
        dc.add_item(path)
        dc.add_item(path2)

    assert_pdf_equal(
        pdf,
        HERE / "generated_pdf" / "gradient_linear_rotated_vs_user_space.pdf",
        tmp_path,
    )


def test_linear_gradient_objbox_scale_translate(tmp_path: Path):
    pdf = _new_pdf()

    path = _rect(150, 40, 180, 90)  # non-uniform aspect
    lg = LinearGradient(
        0, 0, 1, 1, colors=["#0000FF", "#FFFFFF", "#FF0000"], extend_after=True
    )
    M = Transform.scaling(1.2, 0.6) @ Transform.translation(
        0.15, -0.1
    )  # in gradient space
    path.style.fill_color = GradientPaint(
        lg, units="objectBoundingBox", gradient_transform=M
    )
    path.style.stroke_color = None

    with pdf.drawing_context() as dc:
        dc.add_item(path)

    assert_pdf_equal(
        pdf, HERE / "generated_pdf" / "gradient_linear_scale_translate.pdf", tmp_path
    )


def test_linear_gradient_userspace_custom_pivot(tmp_path: Path):
    pdf = _new_pdf()

    path = _rect(40, 160, 220, 60)
    gradient = LinearGradient(40, 160, 260, 220, colors=["#222222", "#DDDDDD"])
    path.style.fill_color = GradientPaint(
        gradient,
        units="userSpaceOnUse",
        gradient_transform=Transform.translation(-150, -190)
        .rotate(math.radians(-25))
        .translate(150, 190),
    )
    path.style.stroke_color = None

    with pdf.drawing_context() as dc:
        dc.add_item(path)

    assert_pdf_equal(
        pdf, HERE / "generated_pdf" / "gradient_userspace_pivot.pdf", tmp_path
    )


@pytest.mark.parametrize(
    "extend_before,extend_after,basename",
    [
        (False, False, "stops_no_extend"),
        (True, False, "stops_extend_before"),
        (False, True, "stops_extend_after"),
        (True, True, "stops_extend_both"),
    ],
)
def test_linear_gradient_color_stops_extends(
    extend_before, extend_after, basename, tmp_path
):
    pdf = _new_pdf()

    path = _rect(30, 30, 260, 40)
    path.style.stroke_color = "#000000"
    path.style.stroke_width = 2
    gradient = LinearGradient(
        50,
        0,
        270,
        0,
        colors=["#0000FF", "#00FFFF", "#00FF00", "#FFFF00", "#FF0000"],
        bounds=[0.25, 0.50, 0.75],
        extend_before=extend_before,
        extend_after=extend_after,
    )
    paint = GradientPaint(gradient, units="userSpaceOnUse")
    path.style.fill_color = paint

    with pdf.drawing_context() as dc:
        dc.add_item(path)

    assert_pdf_equal(
        pdf,
        HERE / "generated_pdf" / f"gradient_linear_{basename}.pdf",
        tmp_path,
    )


def test_radial_gradient_objbox_vs_userspace(tmp_path: Path):
    pdf = _new_pdf()

    path1 = _circle(140, 100, 50)
    gradient1 = RadialGradient(
        0.5, 0.5, 0.0, 0.5, 0.5, 0.5, colors=["#FFFFFF", "#0000AA"]
    )
    path1.style.fill_color = GradientPaint(gradient1, units="objectBoundingBox")
    path1.style.stroke_color = None

    path2 = _circle(340, 100, 50)
    gradient2 = RadialGradient(340, 100, 0, 340, 100, 60, colors=["#FFFFFF", "#AA0000"])
    path2.style.fill_color = GradientPaint(gradient2, units="userSpaceOnUse")
    path2.style.stroke_color = None

    with pdf.drawing_context() as dc:
        dc.add_item(path1)
        dc.add_item(path2)

    assert_pdf_equal(
        pdf,
        HERE / "generated_pdf" / "gradient_radial_objbox_userspace.pdf",
        tmp_path,
    )


def test_radial_gradient_focal_offset_extend(tmp_path: Path):
    pdf = _new_pdf()

    path = _rect(40, 100, 260, 120)
    # Circle center at (0.6, 0.5), focal at (0.3, 0.45), radius 0.7 (object bbox units)
    gradient = RadialGradient(
        0.6,
        0.5,
        0.7,
        0.3,
        0.45,
        0.0,
        colors=["#FFFFFF", "#00AA00", "#003300"],
        bounds=[0.6],
        extend_before=True,
        extend_after=True,
    )
    path.style.fill_color = GradientPaint(gradient, units="objectBoundingBox")
    path.style.stroke_color = None

    with pdf.drawing_context() as dc:
        dc.add_item(path)

    assert_pdf_equal(
        pdf,
        HERE / "generated_pdf" / "gradient_radial_focal_extend.pdf",
        tmp_path,
    )


def test_shared_gradient_instance(tmp_path: Path):
    pdf = _new_pdf()

    gradient = LinearGradient(0, 0, 1, 0, colors=["#FF0000", "#0000FF"])

    path1 = _rect(40, 40, 100, 40)
    path1.style.fill_color = GradientPaint(gradient, units="objectBoundingBox")

    path2 = _rect(160, 40, 100, 40)

    # Different gradient transform but same LinearGradient object
    path2.style.fill_color = GradientPaint(
        gradient,
        units="objectBoundingBox",
        gradient_transform=Transform.translation(-0.5, -0.5)
        .rotate(math.radians(180))
        .translate(0.5, 0.5),
    )

    with pdf.drawing_context() as dc:
        dc.add_item(path1)
        dc.add_item(path2)

    assert_pdf_equal(pdf, HERE / "generated_pdf" / "gradient_shared.pdf", tmp_path)


def test_gradient_fill_with_solid_stroke(tmp_path: Path):
    pdf = _new_pdf()

    gradient = LinearGradient(0, 0, 1, 0, colors=["#FFFFFF", "#000000"])

    path1 = _rect(50, 20, 120, 50)
    path1.style.fill_color = GradientPaint(gradient, units="objectBoundingBox")
    path1.style.stroke_color = "#0000FF"
    path1.style.stroke_width = 3.0

    path2 = _rect(200, 20, 120, 50)
    path2.style.fill_color = "#0000FF"
    path2.style.stroke_color = GradientPaint(gradient, units="objectBoundingBox")
    path2.style.stroke_width = 3.0

    path3 = _rect(350, 20, 120, 50)
    path3.style.fill_color = GradientPaint(gradient, units="objectBoundingBox")
    path3.style.stroke_color = GradientPaint(gradient, units="objectBoundingBox")
    path3.style.stroke_width = 3.0

    with pdf.drawing_context() as dc:
        dc.add_item(path1)
        dc.add_item(path2)
        dc.add_item(path3)

    assert_pdf_equal(
        pdf,
        HERE / "generated_pdf" / "gradient_with_stroke.pdf",
        tmp_path,
    )


def test_gradients_across_pages_resource_reuse(tmp_path: Path):
    pdf = FPDF(unit="pt", format="A4")
    pdf.set_compression(False)

    # Page 1
    pdf.add_page()
    path1 = _rect(60, 100, 220, 70)
    gradient = LinearGradient(0, 0, 1, 0, colors=["#222222", "#EEEEEE"])
    path1.style.fill_color = GradientPaint(gradient, units="objectBoundingBox")
    path1.style.stroke_color = None
    with pdf.drawing_context() as dc:
        dc.add_item(path1)

    # Page 2 (same gradient)
    pdf.add_page()
    path2 = _rect(60, 100, 220, 70)
    path2.style.fill_color = GradientPaint(gradient, units="objectBoundingBox")
    path2.style.stroke_color = None
    with pdf.drawing_context() as dc:
        dc.add_item(path2)

    assert_pdf_equal(
        pdf,
        HERE / "generated_pdf" / "gradient_linear_different_pages.pdf",
        tmp_path,
    )


def test_gradient_shape_linear(tmp_path: Path):
    pdf = _new_pdf()

    # SVG-like stops
    stops = [
        (0.00, "#000000"),
        (0.50, "#ff0000"),
        (1.00, "#00ff00"),
    ]

    gradient = shape_linear_gradient(0, 0, 1, 0, stops)

    r1 = _rect(40, 100, 120, 60)
    r1.style.fill_color = GradientPaint(gradient, units="objectBoundingBox")
    r1.style.stroke_color = "#000000"
    r1.style.stroke_width = 1.0

    r2 = _rect(180, 100, 120, 60)
    r2.style.fill_color = GradientPaint(
        gradient,
        units="objectBoundingBox",
        gradient_transform=Transform.translation(-0.5, -0.5)
        .rotate(math.radians(180))
        .translate(0.5, 0.5),
    )
    r2.style.stroke_color = "#000000"
    r2.style.stroke_width = 1.0

    r3 = _rect(320, 100, 120, 60)
    r3.style.fill_color = GradientPaint(
        gradient,
        units="objectBoundingBox",
        gradient_transform=Transform.scaling(0.4, 1.0).translate(0.3, 0.0),
    )
    r3.style.stroke_color = "#000000"
    r3.style.stroke_width = 1.0

    with pdf.drawing_context() as dc:
        dc.add_item(r1)
        dc.add_item(r2)
        dc.add_item(r3)

    assert_pdf_equal(
        pdf,
        HERE / "generated_pdf" / "gradient_shape_linear.pdf",
        tmp_path,
    )


def test_gradient_shape_radial(tmp_path: Path):
    pdf = _new_pdf()

    # Stops from white center to blue edge
    stops = [
        (0.00, "#ffffff"),
        (0.75, "#66aaff"),
        (1.00, "#002266"),
    ]

    rg_center = shape_radial_gradient(cx=0.5, cy=0.5, r=0.5, stops=stops)

    c1 = _circle(110, 150, 50)
    c1.style.fill_color = GradientPaint(rg_center, units="objectBoundingBox")
    c1.style.stroke_color = None

    rg_focal = shape_radial_gradient(
        cx=0.5, cy=0.5, r=0.5, stops=stops, fx=0.3, fy=0.4, fr=0.0
    )

    c2 = _circle(260, 150, 50)
    c2.style.fill_color = GradientPaint(rg_focal, units="objectBoundingBox")
    c2.style.stroke_color = None

    rg_rect = shape_radial_gradient(
        cx=0.5, cy=0.5, r=0.7, stops=stops, fx=0.35, fy=0.45, fr=0.0
    )

    r = _rect(320, 100, 120, 120)
    r.style.fill_color = GradientPaint(rg_rect, units="objectBoundingBox")
    r.style.stroke_color = "#000000"
    r.style.stroke_width = 0.8

    with pdf.drawing_context() as dc:
        dc.add_item(c1)
        dc.add_item(c2)
        dc.add_item(r)

    assert_pdf_equal(
        pdf,
        HERE / "generated_pdf" / "gradient_shape_radial.pdf",
        tmp_path,
    )
