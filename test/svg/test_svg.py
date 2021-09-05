from pathlib import Path
import re

import fpdf
from test.conftest import assert_pdf_equal

import pytest

from fpdf.drawing import (
    Point,
    Move,
    RelativeMove,
    Line,
    RelativeLine,
    HorizontalLine,
    RelativeHorizontalLine,
    VerticalLine,
    RelativeVerticalLine,
    BezierCurve,
    RelativeBezierCurve,
    QuadraticBezierCurve,
    RelativeQuadraticBezierCurve,
    Arc,
    RelativeArc,
    ImplicitClose,
    Close,
)

from fpdf.svg import (
    SVGSmoothCubicCurve,
    SVGRelativeSmoothCubicCurve,
    SVGSmoothQuadraticCurve,
    SVGRelativeSmoothQuadraticCurve,
)

HERE = Path(__file__).resolve().parent


@pytest.fixture(
    params=[
        "arcs01.svg",
        "arcs02.svg",
        "circle01.svg",
        "cubic01.svg",
        "cubic02.svg",
        "ellipse01.svg",
        "line01.svg",
        "polygon01.svg",
        "polyline01.svg",
        "quad01.svg",
        "rect01.svg",
        "rect02.svg",
        "triangle01.svg",
        "SVG_logo.svg",
    ],
    ids=lambda param: param,
)
def svg_file(request):
    return HERE / "svg_sources" / request.param


def test_svg_conversion(tmp_path, svg_file):
    svg = fpdf.svg.SVGObject.from_file(svg_file)

    pdf = fpdf.FPDF(unit="pt", format=(svg.width, svg.height))
    pdf.add_page()

    svg.draw_to_page(pdf)

    assert_pdf_equal(pdf, HERE / "generated_pdf" / f"{svg_file.stem}.pdf", tmp_path)


def test_svg_path_parsing(svg_paths):
    svg_path, result = svg_paths

    pdf_path = fpdf.drawing.PaintedPath()

    fpdf.svg.svg_path_converter(pdf_path, svg_path)

    assert result == pdf_path._root_graphics_context.path_items


@pytest.fixture(
    params=[
        (
            "M 100 100 L 300 100 L 200 300 z",
            [
                Move(Point(100.0, 100.0)),
                Line(Point(300.0, 100.0)),
                Line(Point(200.0, 300.0)),
                Close(),
            ],
        ),
        (
            "M 0 0 L 50 20 M 100 100 L 300 100 L 200 300 z",
            [
                Move(Point(0.0, 0.0)),
                Line(Point(50.0, 20.0)),
                ImplicitClose(),
                Move(Point(100.0, 100.0)),
                Line(Point(300.0, 100.0)),
                Line(Point(200.0, 300.0)),
                Close(),
            ],
        ),
        (
            "M100,200 C100,100 250,100 250,200 S400,300 400,200",
            [
                Move(Point(100.0, 200.0)),
                BezierCurve(
                    Point(100.0, 100.0), Point(250.0, 100.0), Point(250.0, 200.0)
                ),
                SVGSmoothCubicCurve(Point(400.0, 300.0), Point(400.0, 200.0)),
            ],
        ),
        (
            "M100,200 C100,100 400,100 400,200",
            [
                Move(Point(100.0, 200.0)),
                BezierCurve(
                    Point(100.0, 100.0), Point(400.0, 100.0), Point(400.0, 200.0)
                ),
            ],
        ),
        (
            "M100,500 C25,400 475,400 400,500",
            [
                Move(Point(100.0, 500.0)),
                BezierCurve(
                    Point(25.0, 400.0), Point(475.0, 400.0), Point(400.0, 500.0)
                ),
            ],
        ),
        (
            "M100,800 C175,700 325,700 400,800",
            [
                Move(Point(100.0, 800.0)),
                BezierCurve(
                    Point(175.0, 700.0), Point(325.0, 700.0), Point(400.0, 800.0)
                ),
            ],
        ),
        (
            "M600,200 C675,100 975,100 900,200",
            [
                Move(Point(600.0, 200.0)),
                BezierCurve(
                    Point(675.0, 100.0), Point(975.0, 100.0), Point(900.0, 200.0)
                ),
            ],
        ),
        (
            "M600,500 C600,350 900,650 900,500",
            [
                Move(Point(600.0, 500.0)),
                BezierCurve(
                    Point(600.0, 350.0), Point(900.0, 650.0), Point(900.0, 500.0)
                ),
            ],
        ),
        (
            "M600,800 C625,700 725,700 750,800 S875,900 900,800",
            [
                Move(Point(600.0, 800.0)),
                BezierCurve(
                    Point(625.0, 700.0), Point(725.0, 700.0), Point(750.0, 800.0)
                ),
                SVGSmoothCubicCurve(Point(875.0, 900.0), Point(900.0, 800.0)),
            ],
        ),
        (
            "M200,300 Q400,50 600,300 T1000,300",
            [
                Move(Point(200.0, 300.0)),
                QuadraticBezierCurve(Point(400.0, 50.0), Point(600.0, 300.0)),
                SVGSmoothQuadraticCurve(Point(1000.0, 300.0)),
            ],
        ),
        (
            "M 0 0 L 50 20 m 50 80 L 300 100 L 200 300 z",
            [
                Move(Point(0.0, 0.0)),
                Line(Point(50.0, 20.0)),
                ImplicitClose(),
                RelativeMove(Point(50.0, 80.0)),
                Line(Point(300.0, 100.0)),
                Line(Point(200.0, 300.0)),
                Close(),
            ],
        ),
        (
            "M100,200 s 150,-100 150,0",
            [
                Move(Point(100.0, 200.0)),
                SVGRelativeSmoothCubicCurve(Point(150.0, -100.0), Point(150.0, 0.0)),
            ],
        ),
    ],
    ids=lambda param: param[0],
)
def svg_paths(request):
    return request.param
