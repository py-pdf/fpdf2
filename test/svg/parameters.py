# pylint: disable=redefined-outer-name, protected-access, unnecessary-lambda-assignment
import pytest

from contextlib import contextmanager
import math
from pathlib import Path

# import fpdf
from fpdf.drawing import (
    Point,
    Transform,
    IntersectionRule,
    GraphicsStyle,
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
    resolve_length,
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


def Gs(**kwargs):
    style = GraphicsStyle()
    # this is set on all stylables by the SVG machinery
    style.auto_close = False
    for name, val in kwargs.items():
        setattr(style, name, val)

    return style


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
        '<rect x="20" y="20" width="0" height="60" rx="10" ry="10"/>',
        [],
        no_error(),
        id="rect width 0",
    ),
    pytest.param(
        '<rect x="20" y="20" width="60" height="60" rx="60" ry="60"/>',
        [M(0, 0), Re(20, 20, 60, 60, 30, 30)],
        no_error(),
        id="rect overlarge rx and ry",
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
        "skew(2, 3, 4, 5, 6)",
        None,
        pytest.raises(ValueError),
        id="skew too many args",
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
        "translate(20, 30, 45)",
        None,
        pytest.raises(ValueError),
        id="translate too many args",
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

test_svg_attribute_conversion = (
    pytest.param(
        '<path fill="none"/>',
        Gs(fill_color=None),
        no_error(),
        id="fill color none",
    ),
    pytest.param(
        '<path fill="inherit"/>',
        Gs(fill_color=GraphicsStyle.INHERIT),
        no_error(),
        id="fill color inherit",
    ),
    pytest.param(
        '<path fill="black"/>',
        Gs(fill_color="#000"),
        no_error(),
        id="fill color name",
    ),
    pytest.param(
        '<path fill="#0007"/>',
        Gs(fill_color="#0007", fill_opacity=0x77 / 0xFF),
        no_error(),
        id="fill color rgba",
    ),
    pytest.param(
        '<path fill="1"/>',
        Gs(),
        pytest.raises(ValueError),
        id="fill color invalid",
    ),
    pytest.param(
        '<path fill-rule="inherit"/>',
        Gs(intersection_rule=GraphicsStyle.INHERIT),
        no_error(),
        id="fill-rule inherit",
    ),
    pytest.param(
        '<path fill-rule="nonzero"/>',
        Gs(intersection_rule=IntersectionRule.NONZERO),
        no_error(),
        id="fill-rule nonzero",
    ),
    pytest.param(
        '<path fill-rule="evenodd"/>',
        Gs(intersection_rule=IntersectionRule.EVENODD),
        no_error(),
        id="fill-rule evenodd",
    ),
    pytest.param(
        '<path fill-rule="none"/>',
        Gs(),
        pytest.raises(ValueError),
        id="fill-rule invalid",
    ),
    pytest.param(
        '<path fill-opacity="0.5"/>',
        Gs(fill_opacity=0.5),
        no_error(),
        id="fill-opacity 0.5",
    ),
    pytest.param(
        '<path fill-opacity="-2"/>',
        Gs(fill_opacity=0.0),
        no_error(),
        id="fill-opacity too small",
    ),
    pytest.param(
        '<path fill-opacity="5"/>',
        Gs(fill_opacity=1.0),
        no_error(),
        id="fill-opacity too big",
    ),
    pytest.param(
        '<path fill-opacity="inherit"/>',
        Gs(fill_opacity=GraphicsStyle.INHERIT),
        no_error(),
        id="fill-opacity inherit",
    ),
    pytest.param(
        '<path fill-opacity="none"/>',
        Gs(),
        pytest.raises(ValueError),
        id="fill-opacity invalid",
    ),
    pytest.param(
        '<path stroke="none"/>',
        Gs(stroke_color=None),
        no_error(),
        id="stroke color none",
    ),
    pytest.param(
        '<path stroke="inherit"/>',
        Gs(stroke_color=GraphicsStyle.INHERIT),
        no_error(),
        id="stroke color inherit",
    ),
    pytest.param(
        '<path stroke="black"/>',
        Gs(stroke_color="#000"),
        no_error(),
        id="stroke color name",
    ),
    pytest.param(
        '<path stroke="#0007"/>',
        Gs(stroke_color="#0007", stroke_opacity=0x77 / 0xFF),
        no_error(),
        id="stroke color rgba",
    ),
    pytest.param(
        '<path stroke="1"/>',
        Gs(),
        pytest.raises(ValueError),
        id="stroke color invalid",
    ),
    pytest.param(
        '<path stroke-width="0"/>',
        Gs(stroke_width=None),
        no_error(),
        id="stroke-width 0",
    ),
    pytest.param(
        '<path stroke-width="2"/>',
        Gs(stroke_width=2),
        no_error(),
        id="stroke-width number",
    ),
    pytest.param(
        '<path stroke-width="inherit"/>',
        Gs(),
        no_error(),
        id="stroke-width inherit",
    ),
    pytest.param(
        '<path stroke-width="-2"/>',
        Gs(),
        pytest.raises(ValueError),
        id="stroke-width negative",
    ),
    pytest.param(
        '<path stroke-width="bad"/>',
        Gs(),
        pytest.raises(ValueError),
        id="stroke-width number",
    ),
    pytest.param(
        '<path stroke-dasharray="1 2 3 4 5"/>',
        Gs(stroke_dash_pattern=[1, 2, 3, 4, 5]),
        no_error(),
        id="stroke-dasharray list",
    ),
    pytest.param(
        '<path stroke-dasharray="1"/>',
        Gs(stroke_dash_pattern=[1]),
        no_error(),
        id="stroke-dasharray single value",
    ),
    pytest.param(
        '<path stroke-dasharray="inherit"/>',
        Gs(),
        no_error(),
        id="stroke-dasharray inherit",
    ),
    pytest.param(
        '<path stroke-dasharray="bad"/>',
        Gs(),
        pytest.raises(ValueError),
        id="stroke-dasharray invalid",
    ),
    pytest.param(
        '<path stroke-dasharray="1" stroke-dashoffset="1"/>',
        Gs(stroke_dash_pattern=[1], stroke_dash_phase=1),
        no_error(),
        id="stroke-dashoffset",
    ),
    pytest.param(
        '<path stroke-linecap="butt"/>',
        Gs(stroke_cap_style="butt"),
        no_error(),
        id="stroke-linecap butt",
    ),
    pytest.param(
        '<path stroke-linecap="round"/>',
        Gs(stroke_cap_style="round"),
        no_error(),
        id="stroke-linecap round",
    ),
    pytest.param(
        '<path stroke-linecap="square"/>',
        Gs(stroke_cap_style="square"),
        no_error(),
        id="stroke-linecap square",
    ),
    pytest.param(
        '<path stroke-linecap="inherit"/>',
        Gs(stroke_cap_style=GraphicsStyle.INHERIT),
        no_error(),
        id="stroke-linecap inherit",
    ),
    pytest.param(
        '<path stroke-linecap="bad"/>',
        Gs(),
        pytest.raises(ValueError),
        id="stroke-linecap invalid",
    ),
    pytest.param(
        '<path stroke-linejoin="miter"/>',
        Gs(stroke_join_style="miter"),
        no_error(),
        id="stroke-linejoin miter",
    ),
    pytest.param(
        '<path stroke-linejoin="round"/>',
        Gs(stroke_join_style="round"),
        no_error(),
        id="stroke-linejoin round",
    ),
    pytest.param(
        '<path stroke-linejoin="bevel"/>',
        Gs(stroke_join_style="bevel"),
        no_error(),
        id="stroke-linejoin bevel",
    ),
    pytest.param(
        '<path stroke-linejoin="inherit"/>',
        Gs(stroke_join_style=GraphicsStyle.INHERIT),
        no_error(),
        id="stroke-linejoin inherit",
    ),
    pytest.param(
        '<path stroke-linejoin="bad"/>',
        Gs(),
        pytest.raises(ValueError),
        id="stroke-linejoin invalid",
    ),
    pytest.param(
        '<path stroke-miterlimit="2"/>',
        Gs(stroke_miter_limit=2),
        no_error(),
        id="stroke-miterlimit",
    ),
    pytest.param(
        '<path stroke-miterlimit="inherit"/>',
        Gs(stroke_miter_limit=GraphicsStyle.INHERIT),
        no_error(),
        id="stroke-miterlimit inherit",
    ),
    pytest.param(
        '<path stroke-miterlimit="0.5"/>',
        Gs(),
        pytest.raises(ValueError),
        id="stroke-miterlimit too small",
    ),
    pytest.param(
        '<path stroke-miterlimit="bad"/>',
        Gs(),
        pytest.raises(ValueError),
        id="stroke-miterlimit invalid",
    ),
    pytest.param(
        '<path stroke-opacity="0.5"/>',
        Gs(stroke_opacity=0.5),
        no_error(),
        id="stroke-opacity 0.5",
    ),
    pytest.param(
        '<path stroke-opacity="-2"/>',
        Gs(stroke_opacity=0.0),
        no_error(),
        id="stroke-opacity too small",
    ),
    pytest.param(
        '<path stroke-opacity="5"/>',
        Gs(stroke_opacity=1.0),
        no_error(),
        id="stroke-opacity too big",
    ),
    pytest.param(
        '<path stroke-opacity="inherit"/>',
        Gs(stroke_opacity=GraphicsStyle.INHERIT),
        no_error(),
        id="stroke-opacity inherit",
    ),
    pytest.param(
        '<path stroke-opacity="none"/>',
        Gs(),
        pytest.raises(ValueError),
        id="stroke-opacity invalid",
    ),
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
    pytest.param(svgfile("viewbox.svg"), id="weird viewbox"),
    pytest.param(svgfile("search.svg"), id="search icon"),  # issue 356
    # discovered while investigatin issue 358:
    pytest.param(svgfile("issue_358b.svg"), id="repeated relative move"),
    pytest.param(svgfile("issue_358.svg"), id="arc start & initial point"),  # issue 358
    pytest.param(svgfile("Ghostscript_colorcircle.svg"), id="ghostscript colorcircle"),
    pytest.param(svgfile("Ghostscript_escher.svg"), id="ghostscript escher"),
    pytest.param(svgfile("use-xlink-href.svg"), id="use xlink:href - issue #446"),
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
    pytest.param(
        "m 0 1 2 3 4 5", [M(0, 0), m(0, 1), l(2, 3), l(4, 5)], id="implicit l"
    ),
    pytest.param(
        "m 0. .1 L 2.2 3.3",
        [M(0, 0), m(0, 0.1), L(2.2, 3.3)],
        id="floating point numbers",
    ),
    pytest.param("M0..1L.2.3.4.5", [M(0.0, 0.1), L(0.2, 0.3), L(0.4, 0.5)], id="why"),
)

svg_path_directives = (
    pytest.param("M 0 1 L 2 3", [M(0, 1), L(2, 3)], id="line"),
    pytest.param("m 0 1 l 2 3", [M(0, 0), m(0, 1), l(2, 3)], id="relative line"),
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
    pytest.param(
        "M 0 1 c -7e-5 -4e-5 -8.8492 -3.1382 -8.8493 -3.1383",
        [M(0, 1), c(-7e-5, -4e-5, -8.8492, -3.1382, -8.8493, -3.1383)],
        id="exponentiated numbers",  # cf. issue #376
    ),
)

svg_path_render_tests = (
    pytest.param(
        "M 0 1 C 2 3 4 5 6 7 S 8 9 10 11",
        "q 0 1 m 2 3 4 5 6 7 c 8 9 8 9 10 11 c h B Q",
        id="smooth cubic bezier",
    ),
    pytest.param(
        "M 0 1 S 8 9 10 11",
        "q 0 1 m 0 1 8 9 10 11 c h B Q",
        id="smooth cubic bezier unchained",
    ),
    pytest.param(
        "M 0 1 C 2 3 4 5 6 7 s 8 9 10 11",
        "q 0 1 m 2 3 4 5 6 7 c 8 9 14 16 16 18 c h B Q",
        id="relative smooth cubic bezier",
    ),
    pytest.param(
        "M 0 1 s 8 9 10 11",
        "q 0 1 m 0 1 8 10 10 12 c h B Q",
        id="relative smooth cubic bezier unchained",
    ),
    pytest.param(
        "M 0 1 Q 2 3 4 5 T 6 7",
        "q 0 1 m 1.3333 2.3333 2.6667 3.6667 4 5 c 5.3333 6.3333 6 7 6 7 c h B Q",
        id="smooth quadratic bezier",
    ),
    pytest.param(
        "M 0 1 T 6 7",
        "q 0 1 m 0 1 2 3 6 7 c h B Q",
        id="smooth quadratic bezier unchained",
    ),
    pytest.param(
        "M 0 1 Q 2 3 4 5 t 6 7",
        "q 0 1 m 1.3333 2.3333 2.6667 3.6667 4 5 c 5.3333 6.3333 7.3333 8.6667 10 12 c h B Q",
        id="relative smooth quadratic bezier",
    ),
    pytest.param(
        "M 0 1 t 6 7",
        "q 0 1 m 0 1 2 3.3333 6 8 c h B Q",
        id="relative smooth quadratic bezier unchained",
    ),
)

svg_path_implicit_directives = (
    pytest.param("M 0 1 L 2 3 4 5", [M(0, 1), L(2, 3), L(4, 5)], id="line"),
    pytest.param(
        "m 0 1 l 2 3 4 5", [M(0, 0), m(0, 1), l(2, 3), l(4, 5)], id="relative line"
    ),
    pytest.param("M 0 1 H 2 3", [M(0, 1), H(2), H(3)], id="horizontal line"),
    pytest.param("M 0 1 h 2 3", [M(0, 1), h(2), h(3)], id="relative horizontal line"),
    pytest.param("M 0 1 V 2 3", [M(0, 1), V(2), V(3)], id="vertical line"),
    pytest.param("M 0 1 v 2 3", [M(0, 1), v(2), v(3)], id="relative vertical line"),
    pytest.param(
        "M 0 1 C 2 3 4 5 6 7 8 9 10 11 12 13",
        [M(0, 1), C(2, 3, 4, 5, 6, 7), C(8, 9, 10, 11, 12, 13)],
        id="cubic bezier",
    ),
    pytest.param(
        "M 0 1 c 2 3 4 5 6 7 8 9 10 11 12 13",
        [M(0, 1), c(2, 3, 4, 5, 6, 7), c(8, 9, 10, 11, 12, 13)],
        id="relative cubic bezier",
    ),
    pytest.param(
        "M 0 1 Q 2 3 4 5 6 7 8 9",
        [M(0, 1), Q(2, 3, 4, 5), Q(6, 7, 8, 9)],
        id="quadratic bezier",
    ),
    pytest.param(
        "M 0 1 q 2 3 4 5 6 7 8 9",
        [M(0, 1), q(2, 3, 4, 5), q(6, 7, 8, 9)],
        id="relative quadratic bezier",
    ),
    pytest.param(
        "M 0 1 A 2 3 0 1 0 4 5 6 7 0 1 0 8 9",
        [
            M(0, 1),
            A(P(2, 3), 0, True, False, P(4, 5)),
            A(P(6, 7), 0, True, False, P(8, 9)),
        ],
        id="arc",
    ),
    pytest.param(
        "M 0 1 a 2 3 0 1 0 4 5 6 7 0 1 0 8 9",
        [
            M(0, 1),
            a(P(2, 3), 0, True, False, P(4, 5)),
            a(P(6, 7), 0, True, False, P(8, 9)),
        ],
        id="relative arc",
    ),
    pytest.param(
        "M 0 1 C 2 3 4 5 6 7 S 8 9 10 11 12 13 14 15",
        [M(0, 1), C(2, 3, 4, 5, 6, 7), S(8, 9, 10, 11), S(12, 13, 14, 15)],
        id="smooth cubic bezier",
    ),
    pytest.param(
        "M 0 1 C 2 3 4 5 6 7 s 8 9 10 11 12 13 14 15",
        [M(0, 1), C(2, 3, 4, 5, 6, 7), s(8, 9, 10, 11), s(12, 13, 14, 15)],
        id="relative smooth cubic bezier",
    ),
    pytest.param(
        "M 0 1 Q 2 3 4 5 T 6 7 8 9",
        [M(0, 1), Q(2, 3, 4, 5), T(6, 7), T(8, 9)],
        id="smooth quadratic bezier",
    ),
    pytest.param(
        "M 0 1 Q 2 3 4 5 t 6 7 8 9",
        [M(0, 1), Q(2, 3, 4, 5), t(6, 7), t(8, 9)],
        id="relative smooth quadratic bezier",
    ),
)


def svg_snippet(width="", height="", viewbox="", aspect=True):
    if width:
        width = f'width="{width}"'
    if height:
        height = f'height="{height}"'
    if viewbox:
        viewbox = f'viewBox="{viewbox}"'
    if aspect:
        aspect = 'preserveAspectRatio="xMidYMid"'
    else:
        aspect = 'preserveAspectRatio="none"'

    return f"""<?xml version="1.0" standalone="no"?>
        <svg {width} {height} {viewbox} {aspect} xmlns="http://www.w3.org/2000/svg" version="1.1">
        </svg>
        """


# test "renders" these onto a 10pt by 10pt page.
svg_shape_info_tests = (
    pytest.param(
        svg_snippet(width="10mm"),
        (resolve_length("10mm"), 10),
        Transform.identity(),
        no_error(),
        id="width only",
    ),
    pytest.param(
        svg_snippet(height="10mm"),
        (10, resolve_length("10mm")),
        Transform.identity(),
        no_error(),
        id="height only",
    ),
    pytest.param(
        svg_snippet(width="100%", height="100%"),
        (10, 10),
        Transform.identity(),
        no_error(),
        id="fit percent",
    ),
    pytest.param(
        svg_snippet(width="50%", height="50%"),
        (5, 5),
        Transform.identity(),
        no_error(),
        id="small percent",
    ),
    pytest.param(
        svg_snippet(width="10mm", height="10mm"),
        (resolve_length("10mm"),) * 2,
        Transform.identity(),
        no_error(),
        id="same shape",
    ),
    pytest.param(
        svg_snippet(width="11mm", height="9mm"),
        (resolve_length("11mm"), resolve_length("9mm")),
        Transform.identity(),
        no_error(),
        id="different shape",
    ),
    pytest.param(
        svg_snippet(width="110%", height="90%"),
        (11, 9),
        Transform.identity(),
        no_error(),
        id="different shape, percent",
    ),
    pytest.param(
        svg_snippet(viewbox="0 0 100 100"),
        (10, 10),
        Transform.scaling(0.1),
        no_error(),
        id="viewbox 100",
    ),
    pytest.param(
        svg_snippet(width="5mm", height="6mm", viewbox="0 0 100 100"),
        (resolve_length("5mm"), resolve_length("6mm")),
        Transform.scaling(resolve_length("5mm") / 100).translate(
            x=0, y=10 * resolve_length("5mm") / 100
        ),
        no_error(),
        id="fixed size, viewbox 100",
    ),
    pytest.param(
        svg_snippet(viewbox="0 0 110 90"),
        (10, 10),
        Transform.scaling(10 / 110).translate(x=0, y=10 * 10 / 110),
        no_error(),
        id="viewbox wide",
    ),
    pytest.param(
        svg_snippet(viewbox="0 0 90 110"),
        (10, 10),
        Transform.scaling(10 / 110).translate(x=10 * 10 / 110, y=0),
        no_error(),
        id="viewbox tall",
    ),
    pytest.param(
        svg_snippet(viewbox="0 0 110 90", aspect=False),
        (10, 10),
        Transform.scaling(10 / 110, 10 / 90),
        no_error(),
        id="viewbox wide, no aspect preservation",
    ),
    pytest.param(
        svg_snippet(viewbox="0 0 90 110", aspect=False),
        (10, 10),
        Transform.scaling(10 / 90, 10 / 110),
        no_error(),
        id="viewbox tall, no aspect preservation",
    ),
    pytest.param(
        svg_snippet(viewbox="45 55 90 110"),
        (10, 10),
        Transform.scaling(10 / 110, 10 / 110).translate(-35 / 11, -5),
        no_error(),
        id="viewbox tall and shifted",
    ),
    pytest.param(
        svg_snippet(viewbox="45 55 90 110", aspect=False),
        (10, 10),
        Transform.scaling(10 / 90, 10 / 110).translate(-5, -5),
        no_error(),
        id="viewbox tall and shifted, no aspect preservation",
    ),
    pytest.param(
        svg_snippet(viewbox="0 0 -90 110", aspect=False),
        (10, 10),
        None,
        pytest.raises(ValueError),
        id="invalid viewbox",
    ),
)
