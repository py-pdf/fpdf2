# pylint: disable=redefined-outer-name, no-self-use, protected-access
import pytest

from pathlib import Path

# import fpdf
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
    Arc as A,
    RelativeArc as a,
    ImplicitClose,
    Close,
)

from fpdf.svg import (
    SVGSmoothCubicCurve,
    SVGRelativeSmoothCubicCurve,
    SVGSmoothQuadraticCurve,
    SVGRelativeSmoothQuadraticCurve,
)

SVG_SOURCE_DIR = Path(__file__).resolve().parent / "svg_sources"


def svgfile(name):
    return SVG_SOURCE_DIR / name


def P(x, y):
    return Point(float(x), float(y))


def pointifier(source_fn):
    def wrapper(*args):
        return source_fn(*(P(arg1, arg2) for arg1, arg2 in zip(args[::2], args[1::2])))

    return wrapper


M = pointifier(Move)
m = pointifier(RelativeMove)
L = pointifier(Line)
l = pointifier(RelativeLine)
H = lambda arg: HorizontalLine(float(arg))
h = lambda arg: RelativeHorizontalLine(float(arg))
V = lambda arg: VerticalLine(float(arg))
v = lambda arg: RelativeVerticalLine(float(arg))
C = pointifier(BezierCurve)
c = pointifier(RelativeBezierCurve)
Q = pointifier(QuadraticBezierCurve)
q = pointifier(RelativeQuadraticBezierCurve)
S = pointifier(SVGSmoothCubicCurve)
s = pointifier(SVGRelativeSmoothCubicCurve)
T = pointifier(SVGSmoothQuadraticCurve)
t = pointifier(SVGRelativeSmoothQuadraticCurve)
iz = pointifier(ImplicitClose)
Z = pointifier(Close)

test_svg_sources = (
    pytest.param(svgfile("arcs01.svg"), id="SVG spec arcs01"),
    pytest.param(svgfile("arcs02.svg"), id="SVG spec arcs02"),
    pytest.param(svgfile("circle01.svg"), id="SVG spec circle01"),
    pytest.param(svgfile("cubic01.svg"), id="SVG spec cubic01 (modified)"),
    pytest.param(svgfile("cubic02.svg"), id="SVG spec cubic02 (modified)"),
    pytest.param(svgfile("ellipse01.svg"), id="SVG spec ellipse01"),
    pytest.param(svgfile("line01.svg"), id="SVG spec line01"),
    pytest.param(svgfile("polygon01.svg"), id="SVG spec polygon01"),
    pytest.param(svgfile("polyline01.svg"), id="SVG spec polyline01"),
    pytest.param(svgfile("quad01.svg"), id="SVG spec quad01"),
    pytest.param(svgfile("rect01.svg"), id="SVG spec rect01"),
    pytest.param(svgfile("rect02.svg"), id="SVG spec rect02"),
    pytest.param(svgfile("triangle01.svg"), id="SVG spec triangle01"),
    pytest.param(svgfile("SVG_logo.svg"), id="SVG logo from wikipedia"),
)

svg_path_edge_cases = (
    pytest.param(
        "M0 1L2 3z", [M(0, 1), L(2, 3), Z()], id="no whitespace around commands"
    ),
    pytest.param(
        " M    0   1  L  2   3 z  ", [M(0, 1), L(2, 3), Z()], id="extra whitespace"
    ),
    pytest.param("M0,1l2,3", [M(0, 1), L(2, 3)], id="comma separation"),
    pytest.param("M 0 , 1 L 2 , 3", [M(0, 1), L(2, 3)], id="commas and spaces"),
    pytest.param("M 0,1 L-2-3", [M(0, 1), L(-2, -3)], id="negative number separation"),
    pytest.param("M 0,1 L+2+3", [M(0, 1), L(2, 3)], id="unary plus number separation"),
    pytest.param("M 0 1 2 3 4 5", [M(0, 1), L(2, 3), L(4, 5)], id="implicit L"),
    pytest.param("m 0 1 2 3 4 5", [m(0, 1), l(2, 3), l(4, 5)], id="implicit l"),
    pytest.param(
        "m 0. .1 L 2.2 3.3", [m(0, 0.1), L(2.2, 3.3)], id="floating point numbers"
    ),
    pytest.param("M0..1L.2.3.4.5", [M(0.0, 0.1), L(0.2, 0.3), L(0.4, 0.5)], id="why"),
)

svg_path_directives = (
    pytest.param("M 0 1 L 2 3", [M(0, 1), L(2, 3)], id="line"),
    pytest.param("m 0 1 l 2 3", [M(0, 1), l(2, 3)], id="relative line"),
    pytest.param("M 0 1 H 2", [M(0, 1), H(2)], id="horizontal line"),
    pytest.param("M 0 1 h 2", [M(0, 1), h(2)], id="relative horizontal line"),
    pytest.param("M 0 1 V 2", [M(0, 1), V(2)], id="vertical line"),
    pytest.param("M 0 1 v 2", [M(0, 1), v(2)], id="relative vertical line"),
    pytest.param(
        "M 0 1 C 2 3 4 5 6 7", [M(0, 1), C(2, 3, 4, 5, 6, 7)], id="cubic bezier"
    ),
    pytest.param(
        "M 0 1 c 2 3 4 5 6 7",
        [M(0, 1), c(2, 3, 4, 5, 6, 7)],
        id="relative cubic bezier",
    ),
    pytest.param("M 0 1 Q 2 3 4 5", [M(0, 1), Q(2, 3, 4, 5)], id="quadratic bezier"),
    pytest.param(
        "M 0 1 q 2 3 4 5", [M(0, 1), q(2, 3, 4, 5)], id="relative quadratic bezier"
    ),
    pytest.param(
        "M 0 1 A 2 3 0 1 0 4 5",
        [M(0, 1), A(P(2, 3), 0, True, False, P(4, 5))],
        id="arc",
    ),
    pytest.param(
        "M 0 1 a 2 3 0 1 0 4 5",
        [M(0, 1), a(P(2, 3), 0, True, False, P(4, 5))],
        id="relative arc",
    ),
    pytest.param(
        "M 0 1 C 2 3 4 5 6 7 S 8 9 10 11",
        [M(0, 1), C(2, 3, 4, 5, 6, 7), S(8, 9, 10, 11)],
        id="smooth cubic bezier",
    ),
    pytest.param(
        "M 0 1 C 2 3 4 5 6 7 s 8 9 10 11",
        [M(0, 1), C(2, 3, 4, 5, 6, 7), s(8, 9, 10, 11)],
        id="relative smooth cubic bezier",
    ),
    pytest.param(
        "M 0 1 Q 2 3 4 5 T 6 7",
        [M(0, 1), Q(2, 3, 4, 5), T(6, 7)],
        id="smooth quadratic bezier",
    ),
    pytest.param(
        "M 0 1 Q 2 3 4 5 t 6 7",
        [M(0, 1), Q(2, 3, 4, 5), t(6, 7)],
        id="relative smooth quadratic bezier",
    ),
    pytest.param("M 0 1 z", [M(0, 1), Z()], id="close"),
    pytest.param(
        "M 0 1 L 2 3 M 3 4 L 5 6",
        [M(0, 1), L(2, 3), iz(), M(3, 4), L(5, 6)],
        id="implicit close",
    ),
)

svg_path_implicit_directives = ...
