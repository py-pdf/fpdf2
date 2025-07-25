from pathlib import Path
from test.conftest import assert_pdf_equal

import pytest

from fpdf import FPDF
from fpdf.drawing import (
    Arc,
    BezierCurve,
    BoundingBox,
    Ellipse,
    HorizontalLine,
    Line,
    PaintedPath,
    Point,
    QuadraticBezierCurve,
    Rectangle,
    RelativeArc,
    RelativeBezierCurve,
    RelativeHorizontalLine,
    RelativeLine,
    RelativeQuadraticBezierCurve,
    RelativeVerticalLine,
    RoundedRectangle,
    Transform,
    VerticalLine,
)
from fpdf.enums import PathPaintRule

HERE = Path(__file__).resolve().parent


def rotate_around_center(bbox: BoundingBox) -> Transform:
    """
    Create a transformation that rotates the bounding box around its center.
    """
    center_x = (bbox.x0 + bbox.x1) / 2
    center_y = (bbox.y0 + bbox.y1) / 2
    return (
        Transform.translation(center_x, center_y)
        .rotate(45)
        .translate(-center_x + 150, -center_y)
    )


TRANSFORMS = {
    "identity": Transform.identity(),
    "scaled": Transform.scaling(2, 3),
    "rotated": rotate_around_center,
    "translated": Transform.translation(50, 100),
}


@pytest.mark.parametrize(
    "shape, start, expected_bbox",
    [
        (
            Line(pt=Point(50, 20)),
            Point(10, 20),
            BoundingBox(10, 20, 50, 20),
        ),
        (
            Line(pt=Point(30, 80)),
            Point(30, 10),
            BoundingBox(30, 10, 30, 80),
        ),
        (
            Line(pt=Point(100, 100)),
            Point(50, 50),
            BoundingBox(50, 50, 100, 100),
        ),
        (
            Line(pt=Point(50, 50)),
            Point(100, 100),
            BoundingBox(50, 50, 100, 100),
        ),
        (
            Line(pt=Point(5, 5)),
            Point(-10, -5),
            BoundingBox(-10, -5, 5, 5),
        ),
        (Line(pt=Point(42, 42)), Point(42, 42), BoundingBox(42, 42, 42, 42)),
        (
            RelativeLine(pt=Point(40, 0)),
            Point(10, 20),
            BoundingBox(10, 20, 50, 20),
        ),
        (
            RelativeLine(pt=Point(0, 60)),
            Point(30, 10),
            BoundingBox(30, 10, 30, 70),
        ),
        (
            RelativeLine(pt=Point(100, 100)),
            Point(0, 0),
            BoundingBox(0, 0, 100, 100),
        ),
        (
            RelativeLine(pt=Point(-100, -100)),
            Point(100, 100),
            BoundingBox(0, 0, 100, 100),
        ),
        (
            RelativeLine(pt=Point(15, 10)),
            Point(-10, -5),
            BoundingBox(-10, -5, 5, 5),
        ),
        (
            RelativeLine(pt=Point(0, 0)),
            Point(42, 42),
            BoundingBox(42, 42, 42, 42),
        ),
        (HorizontalLine(x=50), Point(10, 20), BoundingBox(10, 20, 50, 20)),
        (HorizontalLine(x=20), Point(50, 15), BoundingBox(20, 15, 50, 15)),
        (
            HorizontalLine(x=42),
            Point(42, 42),
            BoundingBox(42, 42, 42, 42),
        ),
        (
            RelativeHorizontalLine(x=40),
            Point(10, 20),
            BoundingBox(10, 20, 50, 20),
        ),
        (
            RelativeHorizontalLine(x=-30),
            Point(20, 15),
            BoundingBox(-10, 15, 20, 15),
        ),
        (
            RelativeHorizontalLine(x=0),
            Point(42, 42),
            BoundingBox(42, 42, 42, 42),
        ),
        (VerticalLine(y=80), Point(30, 10), BoundingBox(30, 10, 30, 80)),
        (VerticalLine(y=20), Point(20, 50), BoundingBox(20, 20, 20, 50)),
        (VerticalLine(y=42), Point(42, 42), BoundingBox(42, 42, 42, 42)),
        (RelativeVerticalLine(y=50), Point(30, 10), BoundingBox(30, 10, 30, 60)),
        (
            RelativeVerticalLine(y=-30),
            Point(20, 50),
            BoundingBox(20, 20, 20, 50),
        ),
        (
            RelativeVerticalLine(y=0),
            Point(42, 42),
            BoundingBox(42, 42, 42, 42),
        ),
        (
            BezierCurve(c1=Point(30, 0), c2=Point(70, 0), end=Point(100, 0)),
            Point(0, 0),
            BoundingBox(0, 0, 100, 0),
        ),
        (
            BezierCurve(c1=Point(0, 30), c2=Point(0, 70), end=Point(0, 100)),
            Point(0, 0),
            BoundingBox(0, 0, 0, 100),
        ),
        (
            BezierCurve(c1=Point(100, 0), c2=Point(0, 100), end=Point(100, 100)),
            Point(0, 0),
            BoundingBox(0, 0, 100, 100),
        ),
        (
            BezierCurve(c1=Point(70, 100), c2=Point(30, 100), end=Point(0, 100)),
            Point(100, 100),
            BoundingBox(0, 100, 100, 100),
        ),
        (
            BezierCurve(c1=Point(150, 0), c2=Point(-150, 100), end=Point(100, 100)),
            Point(0, 0),
            BoundingBox(-3.808522398518157, 0.0, 100.0, 100.0),
        ),
        (
            BezierCurve(c1=Point(25, 25), c2=Point(50, 50), end=Point(75, 75)),
            Point(0, 0),
            BoundingBox(0, 0, 75, 75),
        ),
        (
            BezierCurve(c1=Point(42, 42), c2=Point(42, 42), end=Point(42, 42)),
            Point(42, 42),
            BoundingBox(42, 42, 42, 42),
        ),
        (
            RelativeBezierCurve(
                c1=Point(30, 60), c2=Point(60, 90), end=Point(100, 100)
            ),
            Point(0, 0),
            BoundingBox(0, 0, 100, 100),
        ),
        (
            RelativeBezierCurve(
                c1=Point(20, -20), c2=Point(-30, 30), end=Point(-50, -50)
            ),
            Point(25, 25),
            BoundingBox(-25.0, -25.0, 29.63395588138013, 25.0),
        ),
        (
            RelativeBezierCurve(c1=Point(0, 0), c2=Point(0, 0), end=Point(50, 50)),
            Point(0, 0),
            BoundingBox(0, 0, 50, 50),
        ),
        (
            RelativeBezierCurve(c1=Point(0, 0), c2=Point(0, 0), end=Point(0, 0)),
            Point(10, 10),
            BoundingBox(10, 10, 10, 10),
        ),
        (
            RelativeBezierCurve(c1=Point(50, 1), c2=Point(100, 2), end=Point(150, 1)),
            Point(0, 0),
            BoundingBox(0.0, 0.0, 150.0, 1.4142135623730951),
        ),
        (
            RelativeBezierCurve(c1=Point(1, 50), c2=Point(2, 100), end=Point(1, 150)),
            Point(0, 0),
            BoundingBox(0.0, 0.0, 1.4142135623730951, 150.0),
        ),
        (
            QuadraticBezierCurve(ctrl=Point(50, 100), end=Point(100, 0)),
            Point(0, 0),
            BoundingBox(0, 0, 100, 50),
        ),
        (
            QuadraticBezierCurve(ctrl=Point(50, 100), end=Point(100, 0)),
            Point(0, 0),
            BoundingBox(0, 0, 100, 50),
        ),
        (
            QuadraticBezierCurve(ctrl=Point(50, 0), end=Point(100, 0)),
            Point(0, 0),
            BoundingBox(0, 0, 100, 0),
        ),
        (
            QuadraticBezierCurve(ctrl=Point(50, 50), end=Point(100, 100)),
            Point(0, 0),
            BoundingBox(0, 0, 100, 100),
        ),
        (
            QuadraticBezierCurve(ctrl=Point(25, -100), end=Point(50, 0)),
            Point(0, 0),
            BoundingBox(0, -50, 50, 0),
        ),
        (
            QuadraticBezierCurve(ctrl=Point(42, 42), end=Point(42, 42)),
            Point(42, 42),
            BoundingBox(42, 42, 42, 42),
        ),
        (
            RelativeQuadraticBezierCurve(ctrl=Point(50, 100), end=Point(100, 0)),
            Point(0, 0),
            BoundingBox(0, 0, 100, 50),
        ),
        (
            RelativeQuadraticBezierCurve(ctrl=Point(50, 0), end=Point(100, 0)),
            Point(0, 0),
            BoundingBox(0, 0, 100, 0),
        ),
        (
            RelativeQuadraticBezierCurve(ctrl=Point(50, 50), end=Point(100, 100)),
            Point(0, 0),
            BoundingBox(0, 0, 100, 100),
        ),
        (
            RelativeQuadraticBezierCurve(ctrl=Point(25, -100), end=Point(50, 0)),
            Point(0, 0),
            BoundingBox(0, -50, 50, 0),
        ),
        (
            RelativeQuadraticBezierCurve(ctrl=Point(0, 0), end=Point(0, 0)),
            Point(42, 42),
            BoundingBox(42, 42, 42, 42),
        ),
        (
            RelativeQuadraticBezierCurve(ctrl=Point(-25, 25), end=Point(-50, -50)),
            Point(100, 100),
            BoundingBox(50, 50, 100, 106.25),
        ),
        (
            Arc(
                radii=Point(50, 50),
                rotation=0,
                large=False,
                sweep=True,
                end=Point(50, 50),
            ),
            Point(0, 0),
            BoundingBox(0, 0, 50, 50),
        ),
        (
            Arc(
                radii=Point(50, 50),
                rotation=0,
                large=True,
                sweep=False,
                end=Point(-50, 0),
            ),
            Point(50, 0),
            BoundingBox(-50, -50, 50, 0),
        ),
        (
            Arc(
                radii=Point(50, 30),
                rotation=45,
                large=False,
                sweep=True,
                end=Point(100, 0),
            ),
            Point(0, 0),
            BoundingBox(-5.405509724430832, -68.61529643011123, 99.99999989849465, 0),
        ),
        (
            Arc(
                radii=Point(0.1, 0.1),
                rotation=0,
                large=False,
                sweep=True,
                end=Point(0.1, 0),
            ),
            Point(0, 0),
            BoundingBox(0, -0.013397459621556158, 0.1, 0),
        ),
        (
            Arc(
                radii=Point(25, 40),
                rotation=0,
                large=False,
                sweep=False,
                end=Point(-40, 25),
            ),
            Point(0, 0),
            BoundingBox(
                -39.99999998902608, -8.416886842006127, 0.0, 24.999999894774596
            ),
        ),
        (
            RelativeArc(
                radii=Point(50, 50),
                rotation=0,
                large=False,
                sweep=True,
                end=Point(50, 50),
            ),
            Point(0, 0),
            BoundingBox(0, 0, 50, 50),
        ),
        (
            RelativeArc(
                radii=Point(50, 50),
                rotation=0,
                large=True,
                sweep=False,
                end=Point(-100, 0),
            ),
            Point(50, 0),
            BoundingBox(-50.0, -50.0, 50.0, 0.0),
        ),
        (
            RelativeArc(
                radii=Point(50, 30),
                rotation=45,
                large=False,
                sweep=True,
                end=Point(100, 0),
            ),
            Point(0, 0),
            BoundingBox(-5.405509724430832, -68.61529643011123, 99.99999989849465, 0),
        ),
        (
            RelativeArc(
                radii=Point(0.1, 0.1),
                rotation=0,
                large=False,
                sweep=True,
                end=Point(0.1, 0),
            ),
            Point(0, 0),
            BoundingBox(0, -0.013397459621556158, 0.1, 0),
        ),
        (
            RelativeArc(
                radii=Point(25, 40),
                rotation=0,
                large=False,
                sweep=False,
                end=Point(-40, 25),
            ),
            Point(0, 0),
            BoundingBox(-39.99999998902608, -8.416886842006127, 0, 24.999999894774596),
        ),
        (
            Rectangle(org=Point(10, 20), size=Point(80, 60)),
            None,
            BoundingBox(10, 20, 90, 80),
        ),
        (
            Rectangle(org=Point(0, 0), size=Point(100, 100)),
            None,
            BoundingBox(0, 0, 100, 100),
        ),
        (
            Rectangle(org=Point(-50, -25), size=Point(30, 45)),
            None,
            BoundingBox(-50, -25, -20, 20),
        ),
        (
            Rectangle(org=Point(42, 42), size=Point(0, 0)),
            None,
            BoundingBox(42, 42, 42, 42),
        ),
        (
            Rectangle(org=Point(5, 10), size=Point(100, 0.1)),
            None,
            BoundingBox(5, 10, 105, 10.1),
        ),
        (
            Rectangle(org=Point(5, 10), size=Point(0.1, 100)),
            None,
            BoundingBox(5, 10, 5.1, 110),
        ),
        (
            RoundedRectangle(
                org=Point(0, 0), size=Point(100, 50), corner_radii=Point(10, 10)
            ),
            None,
            BoundingBox(0, 0, 100, 50),
        ),
        (
            RoundedRectangle(
                org=Point(10, 20), size=Point(30, 40), corner_radii=Point(0, 0)
            ),
            None,
            BoundingBox(10, 20, 40, 60),
        ),
        (
            RoundedRectangle(
                org=Point(50, 50), size=Point(-30, -20), corner_radii=Point(5, 5)
            ),
            None,
            BoundingBox(20, 30, 50, 50),
        ),
        (
            RoundedRectangle(
                org=Point(0, 0), size=Point(20, 10), corner_radii=Point(30, 30)
            ),
            None,
            BoundingBox(0, 0, 20, 10),
        ),
        (
            RoundedRectangle(
                org=Point(0, 0), size=Point(0, 50), corner_radii=Point(10, 10)
            ),
            None,
            BoundingBox(0, 0, 0, 50),
        ),
        (
            RoundedRectangle(
                org=Point(0, 0), size=Point(80, 0), corner_radii=Point(10, 10)
            ),
            None,
            BoundingBox(0, 0, 80, 0),
        ),
        (
            RoundedRectangle(
                org=Point(30, 30), size=Point(-10, -10), corner_radii=Point(0, 0)
            ),
            None,
            BoundingBox(20, 20, 30, 30),
        ),
        (
            Ellipse(radii=Point(10, 10), center=Point(0, 0)),
            None,
            BoundingBox(-10, -10, 10, 10),
        ),
        (
            Ellipse(radii=Point(10, 10), center=Point(100, 200)),
            None,
            BoundingBox(90, 190, 110, 210),
        ),
        (
            Ellipse(radii=Point(25, 10), center=Point(50, 75)),
            None,
            BoundingBox(25, 65, 75, 85),
        ),
        (
            Ellipse(radii=Point(0, 20), center=Point(50, 50)),
            None,
            BoundingBox.empty(),
        ),
        (
            Ellipse(radii=Point(15, 0), center=Point(0, 0)),
            None,
            BoundingBox.empty(),
        ),
    ],
)
def test_shape_bounding_box(shape, start, expected_bbox):
    bbox, _ = shape.bounding_box(start)
    if not bbox.is_valid():
        assert not expected_bbox.is_valid()
    else:
        assert bbox == expected_bbox

    for _, tf in TRANSFORMS.items():
        transform = tf(expected_bbox) if callable(tf) else tf

        start = start if start else Point(0, 0)
        path = PaintedPath()
        path.move_to(start.x, start.y)
        path.add_path_element(shape)
        path.style.stroke_color = "#000000"
        path.style.paint_rule = PathPaintRule.FILL_NONZERO
        path.transform = transform

        bbox, _ = path.bounding_box(start=start)

        expected_scaled_bbox = expected_bbox.transformed(transform)
        if not bbox.is_valid():
            assert not expected_scaled_bbox.is_valid()
            return
        assert bbox == expected_scaled_bbox


def simple_path_absolute_relative():
    path = PaintedPath()
    path.move_to(10, 10)
    path.line_to(100, 10)
    path.line_relative(0, 40)
    path.line_to(10, 50)
    path.close()
    return path


def circle_and_rectangle():
    path = PaintedPath()
    path.circle(60, 60, 30)
    path.rectangle(20, 20, 40, 40)
    return path


def mixed_curves_and_lines():
    path = PaintedPath()
    path.move_to(0, 0)
    path.curve_to(30, 60, 60, 90, 100, 100)
    path.quadratic_curve_relative(20, -100, 50, 0)
    path.line_to(0, 0)
    path.close()
    return path


def arc_and_line():
    path = PaintedPath()
    path.move_to(50, 50)
    path.arc_relative(25, 25, 0, False, True, 50, 50)
    path.line_to(25, 75)
    return path


def rect_base():
    p = PaintedPath()
    p.style.fill_color = "#88aaee"
    p.rectangle(10, 10, 90, 40)  # bbox: (10,10)-(100,50)
    return p


def fill_only_rect_nonzero():
    p = rect_base()
    p.style.fill_color = "#88aaee"
    p.style.stroke_color = None
    p.style.paint_rule = PathPaintRule.FILL_NONZERO
    return p  # FILL_NONZERO, no stroke expansion


def stroke_only_rect_w4():
    p = rect_base()
    p.style.fill_color = None
    p.style.stroke_color = "#000000"
    p.style.stroke_width = 4  # expand by 2 in x/y
    return p  # STROKE


def stroke_fill_rect_w2():
    p = rect_base()
    p.style.fill_color = "#cccccc"
    p.style.stroke_color = "#000000"
    p.style.stroke_width = 2  # expand by 1 in x/y
    p.style.paint_rule = PathPaintRule.STROKE_FILL_NONZERO
    return p  # STROKE_FILL_NONZERO


def evenodd_fill_with_hole():
    p = PaintedPath()
    # outer rect (20,20)-(90,90)
    p.rectangle(20, 20, 70, 70)
    # inner rect (40,40)-(70,70) => hole
    p.rectangle(40, 40, 30, 30)
    p.style.fill_color = "#88aaee"
    p.style.stroke_color = None
    p.style.paint_rule = PathPaintRule.FILL_EVENODD
    return p  # FILL_EVENODD, bbox is outer rect only


def scaled_stroke_rect_w2():
    p = rect_base()
    p.transform = Transform.scaling(2.0, 0.5)
    p.style.fill_color = None
    p.style.stroke_color = "#000000"
    p.style.stroke_width = 2
    p.style.paint_rule = PathPaintRule.STROKE
    return p
    # Geom scales to (20,5)-(200,25); row_norms=(2,0.5); pad=(2,0.5)


def translated_fill_only():
    p = rect_base()
    p.transform = Transform.translation(15, -5)
    p.style.fill_color = "#88aaee"
    p.style.stroke_color = None
    p.style.paint_rule = PathPaintRule.FILL_NONZERO
    return p  # FILL_NONZERO, just shifted


def nested_scaled_circle_stroke2():
    p = PaintedPath()
    p.transform = Transform.scaling(1.5, 1.5)
    p.circle(20, 20, 10)  # base bbox (10,10)-(30,30) -> scaled to (15,15)-(45,45)
    p.style.fill_color = None
    p.style.stroke_color = "#000000"
    p.style.stroke_width = 2  # row_norms ~ (1.5,1.5); pad=(1.5,1.5)
    return p


def hairline_stroke_rect():
    p = rect_base()
    p.style.fill_color = None
    p.style.stroke_color = "#000000"
    p.style.stroke_width = 0  # hairline: no bbox expansion in user space
    return p


def zero_opacity_stroke_rect():
    p = rect_base()
    p.style.fill_color = None
    p.style.stroke_color = "#000000"
    p.style.stroke_width = 6
    p.style.stroke_opacity = 0.0  # invisible stroke => no expansion
    return p


def dont_paint_rect():
    p = rect_base()
    p.style.paint_rule = PathPaintRule.DONT_PAINT
    # bbox should remain purely geometric
    return p


@pytest.mark.parametrize(
    "test_id, path_builder, expected_bbox",
    [
        (
            "simple_path_absolute_relative",
            simple_path_absolute_relative,
            BoundingBox(9.5, 9.5, 100.5, 50.5),
        ),
        (
            "circle_and_rectangle",
            circle_and_rectangle,
            BoundingBox(19.5, 19.5, 90.5, 90.5),
        ),
        (
            "mixed_curves_and_lines",
            mixed_curves_and_lines,
            BoundingBox(-0.5, -0.5, 150.5, 100.5),
        ),
        (
            "arc_and_line",
            arc_and_line,
            BoundingBox(
                24.5, 39.14466094591647, 110.85533905932736, 100.50000004195078
            ),
        ),
        # paint-rule variations (no transforms)
        (
            "fill_only_nonzero",
            fill_only_rect_nonzero,
            BoundingBox(10.0, 10.0, 100.0, 50.0),
        ),
        ("stroke_only_w4", stroke_only_rect_w4, BoundingBox(8.0, 8.0, 102.0, 52.0)),
        ("stroke_fill_w2", stroke_fill_rect_w2, BoundingBox(9.0, 9.0, 101.0, 51.0)),
        (
            "evenodd_fill_with_hole",
            evenodd_fill_with_hole,
            BoundingBox(20.0, 20.0, 90.0, 90.0),
        ),
        # transforms
        (
            "scaled_stroke_rect_w2",
            scaled_stroke_rect_w2,
            BoundingBox(18.0, 4.5, 202.0, 25.5),
        ),
        (
            "translated_fill_only",
            translated_fill_only,
            BoundingBox(25.0, 5.0, 115.0, 45.0),
        ),
        (
            "nested_scaled_circle_stroke2",
            nested_scaled_circle_stroke2,
            BoundingBox(13.5, 13.5, 46.5, 46.5),
        ),
        # special stroke cases
        (
            "hairline_stroke_rect",
            hairline_stroke_rect,
            BoundingBox(10.0, 10.0, 100.0, 50.0),
        ),
        (
            "zero_opacity_stroke_rect",
            zero_opacity_stroke_rect,
            BoundingBox(10.0, 10.0, 100.0, 50.0),
        ),
        # explicit DONT_PAINT (no stroke expansion)
        ("dont_paint_rect", dont_paint_rect, BoundingBox(10.0, 10.0, 100.0, 50.0)),
    ],
)
def test_composite_painted_path(test_id, path_builder, expected_bbox, tmp_path):
    path = path_builder()
    bbox, _ = path.bounding_box(Point(0, 0))
    print(bbox, expected_bbox)
    assert bbox == expected_bbox

    pdf = FPDF()
    pdf.add_page()

    with pdf.drawing_context() as gc:
        gc.add_item(path)

    with pdf.drawing_context() as gc:
        # Draw bounding box in red
        bbox_path = PaintedPath()
        bbox_path.rectangle(bbox.x0, bbox.y0, bbox.x1 - bbox.x0, bbox.y1 - bbox.y0)
        bbox_path.style.stroke_color = "#ff0000"
        bbox_path.style.stroke_width = 0.1
        bbox_path.style.fill_color = None
        gc.add_item(bbox_path)

    assert_pdf_equal(
        pdf,
        HERE / f"generated_pdf/bounding_box_painted_path_{test_id}.pdf",
        tmp_path,
    )
