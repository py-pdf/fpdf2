# pylint: disable=redefined-outer-name, no-self-use, protected-access
import pytest

from contextlib import contextmanager
import math
from pathlib import Path

# import fpdf
from fpdf.drawing import (
    Point,
    Transform,
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
    RoundedRectangle,
    Ellipse,
)

from fpdf.svg import (
    SVGSmoothCubicCurve,
    SVGRelativeSmoothCubicCurve,
    SVGSmoothQuadraticCurve,
    SVGRelativeSmoothQuadraticCurve,
)

SVG_SOURCE_DIR = Path(__file__).resolve().parent / "svg_sources"


@contextmanager
def no_error():
    yield


def svgfile(*names):
    return SVG_SOURCE_DIR.joinpath(*names)


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

Re = pointifier(RoundedRectangle)
El = pointifier(Ellipse)

test_svg_shape_tags = (
    pytest.param(
        '<rect x="20" y="20" width="60" height="60"/>',
        [M(0, 0), Re(20, 20, 60, 60, 0, 0)],
        no_error(),
        id="rect",
    ),
    pytest.param(
        '<rect x="20" y="20" width="60" height="60" rx="none" ry="none"/>',
        [M(0, 0), Re(20, 20, 60, 60, 0, 0)],
        no_error(),
        id="rect rx and ry none",
    ),
    pytest.param(
        '<rect x="20" y="20" width="60" height="60" rx="10" ry="none"/>',
        [M(0, 0), Re(20, 20, 60, 60, 10, 0)],
        no_error(),
        id="rect rx ry none",
    ),
    pytest.param(
        '<rect x="20" y="20" width="60" height="60" rx="10"/>',
        [M(0, 0), Re(20, 20, 60, 60, 10, 10)],
        no_error(),
        id="rect rx no ry",
    ),
    pytest.param(
        '<rect x="20" y="20" width="60" height="60" rx="10" ry="auto"/>',
        [M(0, 0), Re(20, 20, 60, 60, 10, 10)],
        no_error(),
        id="rect rx ry auto",
    ),
    pytest.param(
        '<rect x="20" y="20" width="60" height="60" ry="30"/>',
        [M(0, 0), Re(20, 20, 60, 60, 30, 30)],
        no_error(),
        id="rect ry no rx",
    ),
    pytest.param(
        '<rect x="20" y="20" width="60" height="60" rx="none" ry="30"/>',
        [M(0, 0), Re(20, 20, 60, 60, 0, 30)],
        no_error(),
        id="rect ry rx none",
    ),
    pytest.param(
        '<rect x="20" y="20" width="60" height="60" rx="auto" ry="30"/>',
        [M(0, 0), Re(20, 20, 60, 60, 30, 30)],
        no_error(),
        id="rect ry rx auto",
    ),
    pytest.param(
        '<rect x="20" y="20" width="500" height="60" rx="100" ry="10"/>',
        [M(0, 0), Re(20, 20, 500, 60, 100, 10)],
        no_error(),
        id="rect rx and ry",
    ),
    pytest.param(
        '<rect x="20" y="20" width="500" height="60" rx="-100" ry="10"/>',
        [],
        pytest.raises(ValueError),
        id="rect negative rx",
    ),
    pytest.param(
        '<rect x="20" y="20" width="-500" height="60" rx="100" ry="10"/>',
        [],
        pytest.raises(ValueError),
        id="rect negative width",
    ),
    pytest.param(
        '<circle r="10"/>',
        [M(0, 0), El(10, 10, 0, 0)],
        no_error(),
        id="circle no cx no cy",
    ),
    pytest.param(
        '<circle cx="10" r="10"/>',
        [M(0, 0), El(10, 10, 10, 0)],
        no_error(),
        id="circle cx no cy",
    ),
    pytest.param(
        '<circle cy="10" r="10"/>',
        [M(0, 0), El(10, 10, 0, 10)],
        no_error(),
        id="circle cy no cx",
    ),
    pytest.param(
        '<circle cx="10" cy="20" r="10"/>',
        [M(0, 0), El(10, 10, 10, 20)],
        no_error(),
        id="circle cy cx",
    ),
    pytest.param(
        '<circle r="-10"/>',
        [M(0, 0), El(-10, -10, 0, 0)],
        no_error(),
        id="circle negative r",
    ),
    pytest.param(
        '<circle cx="10" cy="10"/>', [], pytest.raises(KeyError), id="circle no r"
    ),
    pytest.param(
        '<ellipse rx="10"/>',
        [M(0, 0), El(10, 10, 0, 0)],
        no_error(),
        id="ellipse no cx no cy no ry",
    ),
    pytest.param(
        '<ellipse rx="10" ry="auto"/>',
        [M(0, 0), El(10, 10, 0, 0)],
        no_error(),
        id="ellipse no cx no cy ry auto",
    ),
    pytest.param(
        '<ellipse ry="10"/>',
        [M(0, 0), El(10, 10, 0, 0)],
        no_error(),
        id="ellipse no cx no cy no rx",
    ),
    pytest.param(
        '<ellipse rx="auto" ry="10"/>',
        [M(0, 0), El(10, 10, 0, 0)],
        no_error(),
        id="ellipse no cx no cy rx auto",
    ),
    pytest.param(
        "<ellipse/>",
        [],
        no_error(),
        id="ellipse empty",
    ),
    pytest.param(
        '<ellipse cx="10" rx="10"/>',
        [M(0, 0), El(10, 10, 10, 0)],
        no_error(),
        id="ellipse cx no cy",
    ),
    pytest.param(
        '<ellipse cy="10" rx="10"/>',
        [M(0, 0), El(10, 10, 0, 10)],
        no_error(),
        id="ellipse cy no cx",
    ),
    pytest.param(
        '<ellipse cx="10" cy="20" rx="10"/>',
        [M(0, 0), El(10, 10, 10, 20)],
        no_error(),
        id="ellipse cy cx",
    ),
    pytest.param(
        '<ellipse rx="-10"/>',
        [M(0, 0), El(-10, -10, 0, 0)],
        no_error(),
        id="ellipse negative r",
    ),
    pytest.param(
        '<ellipse rx="-10"/>',
        [M(0, 0), El(-10, -10, 0, 0)],
        no_error(),
        id="ellipse negative r",
    ),
    pytest.param(
        '<line x1="0" y1="0" x2="10" y2="10"/>',
        [M(0, 0), L(10, 10)],
        no_error(),
        id="line",
    ),
    pytest.param(
        '<line y1="0" x2="10" y2="10"/>',
        [],
        pytest.raises(KeyError),
        id="line no x1",
    ),
    pytest.param(
        '<polyline points="1, 0 10, 10, -20, -50"/>',
        [M(1, 0), L(10, 10), L(-20, -50)],
        no_error(),
        id="polyline",
    ),
    pytest.param(
        "<polyline/>",
        [],
        pytest.raises(KeyError),
        id="polyline no points",
    ),
    pytest.param(
        '<polygon points="1, 0 10, 10, -20, -50"/>',
        [M(1, 0), L(10, 10), L(-20, -50), Z()],
        no_error(),
        id="polygon",
    ),
    pytest.param(
        "<polygon/>",
        [],
        pytest.raises(KeyError),
        id="polygon no points",
    ),
)

test_svg_transforms = (
    pytest.param(
        "matrix(1,2,3,4,5,6)",
        Transform(1, 2, 3, 4, 5, 6),
        no_error(),
        id="matrix",
    ),
    pytest.param(
        "rotate(30)",
        Transform.rotation_d(30),
        no_error(),
        id="rotate",
    ),
    pytest.param(
        "rotate(30, 10, 10)",
        Transform.rotation_d(30).about(10, 10),
        no_error(),
        id="rotate about",
    ),
    pytest.param(
        "rotate(30, 10)",
        Transform.identity(),
        pytest.raises(ValueError),
        id="rotate bad syntax",
    ),
    pytest.param(
        "scale(2)",
        Transform.scaling(x=2, y=2),
        no_error(),
        id="scale combined",
    ),
    pytest.param(
        "scale(2, 1)",
        Transform.scaling(x=2, y=1),
        no_error(),
        id="scale x",
    ),
    pytest.param(
        "scale(1 2)",
        Transform.scaling(x=1, y=2),
        no_error(),
        id="scale y",
    ),
    pytest.param(
        "scale(1 2 3)",
        Transform.identity(),
        pytest.raises(ValueError),
        id="scale bad syntax",
    ),
    pytest.param(
        "scaleX(2)",
        Transform.scaling(x=2, y=1),
        no_error(),
        id="scaleX",
    ),
    pytest.param(
        "scaleY(2)",
        Transform.scaling(x=1, y=2),
        no_error(),
        id="scaleY",
    ),
    pytest.param(
        "skew(2)",
        Transform.shearing(x=math.tan(math.radians(2)), y=0),
        no_error(),
        id="skew x-only",
    ),
    pytest.param(
        "skew(2, 3)",
        Transform.shearing(x=math.tan(math.radians(2)), y=math.tan(math.radians(3))),
        no_error(),
        id="skew x and y",
    ),
    pytest.param(
        "skewX(2)",
        Transform.shearing(x=math.tan(math.radians(2)), y=0),
        no_error(),
        id="skewX",
    ),
    pytest.param(
        "skewY(2)",
        Transform.shearing(x=0, y=math.tan(math.radians(2))),
        no_error(),
        id="skewY",
    ),
    pytest.param(
        "translate(20)",
        Transform.translation(x=20, y=0),
        no_error(),
        id="translate x-only",
    ),
    pytest.param(
        "translate(20, 30)",
        Transform.translation(x=20, y=30),
        no_error(),
        id="translate x and y",
    ),
    pytest.param(
        "translateX(10)",
        Transform.translation(x=10, y=0),
        no_error(),
        id="translateX",
    ),
    pytest.param(
        "translateY(10)",
        Transform.translation(x=0, y=10),
        no_error(),
        id="translateY",
    ),
    pytest.param(
        "skewX(30) scale(1, 1.25) translate(200, 200) rotate(45) translate(-500, -500)",
        Transform.translation(-500, -500)
        .rotate_d(45)
        .translate(200, 200)
        .scale(1, 1.25)
        .shear(math.tan(math.radians(30)), 0),
        no_error(),
        id="multiple",
    ),
)

test_svg_transform_documents = (
    pytest.param(svgfile("transforms", "matrix.svg"), id="matrix"),
    pytest.param(svgfile("transforms", "rotate.svg"), id="rotate"),
    pytest.param(svgfile("transforms", "scale.svg"), id="scale"),
    pytest.param(svgfile("transforms", "skew.svg"), id="skew"),
    pytest.param(svgfile("transforms", "translate.svg"), id="translate"),
    pytest.param(svgfile("transforms", "multi.svg"), id="multiple"),
)

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
