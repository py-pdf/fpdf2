import pytest

from decimal import Decimal
from contextlib import contextmanager

from fpdf.drawing import (
    Arc,
    BezierCurve,
    Close,
    Ellipse,
    HorizontalLine,
    ImplicitClose,
    Line,
    Move,
    PaintedPath,
    QuadraticBezierCurve,
    Rectangle,
    RelativeArc,
    RelativeBezierCurve,
    RelativeHorizontalLine,
    RelativeLine,
    RelativeMove,
    RelativeQuadraticBezierCurve,
    RelativeVerticalLine,
    RoundedRectangle,
    VerticalLine,
)
from fpdf.drawing_primitives import Point, Transform, rgb8
from fpdf.enums import (
    BlendMode,
    ClippingPathIntersectionRule,
    IntersectionRule,
    PathPaintRule,
    StrokeCapStyle,
    StrokeJoinStyle,
)
from fpdf.syntax import Name, Raw


@contextmanager
def no_exception():
    yield


def exception(exc):
    def wrapper():
        return pytest.raises(exc)

    return wrapper


hex_colors = (
    pytest.param("#CAB", rgb8(r=0xCC, g=0xAA, b=0xBB, a=None), id="RGB hex 3"),
    pytest.param("#FADE", rgb8(r=0xFF, g=0xAA, b=0xDD, a=0xEE), id="RGBA hex 4"),
    pytest.param("#C0FFEE", rgb8(r=0xC0, g=0xFF, b=0xEE, a=None), id="RGB hex 6"),
    pytest.param("#0D06F00D", rgb8(r=0x0D, g=0x06, b=0xF0, a=0x0D), id="RGBA hex 8"),
    pytest.param(
        "#0d06f00d",
        rgb8(r=0x0D, g=0x06, b=0xF0, a=0x0D),
        id="RGBA hex 9, case insensitive",
    ),
    pytest.param("#asd", ValueError, id="bad characters"),
    pytest.param("asd", ValueError, id="bad characters missing hash"),
    pytest.param("#12345", ValueError, id="wrong length"),
    pytest.param("123456", ValueError, id="missing hash"),
    pytest.param(123, TypeError, id="bad type integer"),
)

rgb_colors = (
    pytest.param("rgb(204, 170, 187)", rgb8(r=204, g=170, b=187, a=None), id="RGB"),
    pytest.param("rgb(13, 6, 240, 5)", rgb8(r=13, g=6, b=240, a=5), id="RGBA"),
    pytest.param(
        "rgb( 192,  255 ,  238 )",
        rgb8(r=192, g=255, b=238, a=None),
        id="rgb with extra spaces",
    ),
    pytest.param("rgb(a, s, d)", ValueError, id="bad characters"),
    pytest.param("(240, 170, 187)", ValueError, id="missing rgb"),
    pytest.param("rgb(10, 10, 10", ValueError, id="missing )"),
    pytest.param("rgb(13, 6, 240, 5, 200)", ValueError, id="wrong length"),
    pytest.param("rgba(13, 6, 240, 5)", ValueError, id="rgba instead of rgb"),
    pytest.param(123, TypeError, id="bad type integer"),
)

numbers = (
    pytest.param(100, "100", id="integer"),
    pytest.param(Decimal("1.1"), "1.1", id="Decimal"),
    pytest.param(Decimal("0.000008"), "0", id="truncated Decimal"),
    pytest.param(1.05, "1.05", id="float"),
    pytest.param(10.00001, "10", id="truncated float"),
    pytest.param(-1.12345, "-1.1235", id="rounded float"),
    pytest.param(-0.00004, "-0", id="negative zero"),
)

r = Raw


class CustomPrimitive:
    # pylint: disable=no-self-use
    def serialize(self):
        return "custom primitive"


pdf_primitives = (
    pytest.param(Raw("raw output"), r("raw output"), id="raw"),
    pytest.param(CustomPrimitive(), r("custom primitive"), id="custom"),
    pytest.param(Name("pdf_name"), r("/pdf_name"), id="name"),
    pytest.param(Name("pdf#<name>"), r("/pdf#23#3Cname#3E"), id="escape name"),
    pytest.param("string", r("(string)"), id="string"),
    pytest.param("\r()\\", r(r"""(\r\(\)\\)"""), id="escape string"),
    pytest.param(b"bytes", r("<6279746573>"), id="bytes"),
    pytest.param(123, r("123"), id="integer"),
    pytest.param(123.456, r("123.456"), id="float"),
    pytest.param(Decimal("1.1"), r("1.1"), id="decimal"),
    pytest.param(True, r("true"), id="True"),
    pytest.param(False, r("false"), id="False"),
    pytest.param(None, r("null"), id="None"),
    pytest.param(["a", b"b", 0xC, Name("d")], r("[(a) <62> 12 /d]"), id="list"),
    pytest.param(("a", b"b", 0xC, Name("d")), r("[(a) <62> 12 /d]"), id="tuple"),
    pytest.param(
        {Name("key"): "value", Name("k2"): True},
        r("<< /key (value)\n/k2 true >>"),
        id="dict",
    ),
)

pdf_bad_primitives = (
    pytest.param(type("EmptyClass", (), {}), TypeError, id="Class without bdf_repr"),
    pytest.param({"element", 1, 2.0}, TypeError, id="unsupported (set)"),
    pytest.param({"key": "value", "k2": True}, ValueError, id="dict with bad keys"),
)

T = Transform
P = Point

transforms = (
    pytest.param(T.identity(), P(1, 1), P(1, 1), id="identity"),
    pytest.param(T.translation(x=1, y=1), P(1, 1), P(2, 2), id="translation"),
    pytest.param(T.scaling(x=2, y=3), P(1, 1), P(2, 3), id="scaling x-y"),
    pytest.param(T.scaling(2), P(1, 1), P(2, 2), id="scaling"),
    pytest.param(T.rotation(1.5707963267948966), P(1, 0), P(0, 1.0), id="rotation"),
    pytest.param(T.rotation_d(90), P(1, 0), P(0, 1.0), id="rotation_d"),
    pytest.param(T.shearing(1, 0), P(1, 1), P(2, 1), id="shearing"),
)

coercive_enums = (
    pytest.param(
        IntersectionRule,
        (IntersectionRule.NONZERO, "NONZERO", "nonzero", "NONzero"),
        IntersectionRule.NONZERO,
        no_exception,
        id="IntersectionRule.NONZERO",
    ),
    pytest.param(
        IntersectionRule,
        (IntersectionRule.EVENODD, "EVENODD", "evenodd", "EveNOdD"),
        IntersectionRule.EVENODD,
        no_exception,
        id="IntersectionRule.EVENODD",
    ),
    pytest.param(
        IntersectionRule,
        ("nonsense",),
        None,
        exception(ValueError),
        id="coerce bad string",
    ),
    pytest.param(
        IntersectionRule,
        (1234,),
        None,
        exception(TypeError),
        id="coerce wrong type entirely",
    ),
    pytest.param(
        PathPaintRule,
        (PathPaintRule.STROKE, "stroke", "S"),
        PathPaintRule.STROKE,
        no_exception,
        id="PathPaintRule.STROKE",
    ),
    pytest.param(
        PathPaintRule,
        (PathPaintRule.FILL_NONZERO, "fill_nonzero", "f"),
        PathPaintRule.FILL_NONZERO,
        no_exception,
        id="PathPaintRule.FILL_NONZERO",
    ),
    pytest.param(
        PathPaintRule,
        (PathPaintRule.FILL_EVENODD, "fill_evenodd", "f*"),
        PathPaintRule.FILL_EVENODD,
        no_exception,
        id="PathPaintRule.FILL_EVENODD",
    ),
    pytest.param(
        PathPaintRule,
        (PathPaintRule.STROKE_FILL_NONZERO, "stroke_fill_nonzero", "B"),
        PathPaintRule.STROKE_FILL_NONZERO,
        no_exception,
        id="PathPaintRule.STROKE_FILL_NONZERO",
    ),
    pytest.param(
        PathPaintRule,
        (PathPaintRule.STROKE_FILL_EVENODD, "stroke_fill_evenodd", "B*"),
        PathPaintRule.STROKE_FILL_EVENODD,
        no_exception,
        id="PathPaintRule.STROKE_FILL_EVENODD",
    ),
    pytest.param(
        PathPaintRule,
        (PathPaintRule.DONT_PAINT, "dont_paint", "n"),
        PathPaintRule.DONT_PAINT,
        no_exception,
        id="PathPaintRule.DONT_PAINT",
    ),
    pytest.param(
        PathPaintRule,
        (PathPaintRule.AUTO, "auto"),
        PathPaintRule.AUTO,
        no_exception,
        id="PathPaintRule.AUTO",
    ),
    pytest.param(
        ClippingPathIntersectionRule,
        (ClippingPathIntersectionRule.NONZERO, "nonzero", "W"),
        ClippingPathIntersectionRule.NONZERO,
        no_exception,
        id="ClippingPathIntersectionRule.NONZERO",
    ),
    pytest.param(
        ClippingPathIntersectionRule,
        (ClippingPathIntersectionRule.EVENODD, "evenodd", "W*"),
        ClippingPathIntersectionRule.EVENODD,
        no_exception,
        id="ClippingPathIntersectionRule.EVENODD",
    ),
    pytest.param(
        StrokeCapStyle,
        (-1,),
        None,
        exception(ValueError),
        id="int coerce out of range",
    ),
    pytest.param(
        StrokeCapStyle,
        ("nonsense",),
        None,
        exception(ValueError),
        id="int coerce bad key",
    ),
    pytest.param(
        StrokeCapStyle,
        (1.0, object()),
        None,
        exception(TypeError),
        id="int coerce bad type",
    ),
    pytest.param(
        StrokeCapStyle,
        (StrokeCapStyle.BUTT, "butt", 0),
        StrokeCapStyle.BUTT,
        no_exception,
        id="StrokeCapStyle.BUTT",
    ),
    pytest.param(
        StrokeCapStyle,
        (StrokeCapStyle.ROUND, "round", 1),
        StrokeCapStyle.ROUND,
        no_exception,
        id="StrokeCapStyle.ROUND",
    ),
    pytest.param(
        StrokeCapStyle,
        (StrokeCapStyle.SQUARE, "square", 2),
        StrokeCapStyle.SQUARE,
        no_exception,
        id="StrokeCapStyle.SQUARE",
    ),
    pytest.param(
        StrokeJoinStyle,
        (StrokeJoinStyle.MITER, "miter", 0),
        StrokeJoinStyle.MITER,
        no_exception,
        id="StrokeJoinStyle.MITER",
    ),
    pytest.param(
        StrokeJoinStyle,
        (StrokeJoinStyle.ROUND, "round", 1),
        StrokeJoinStyle.ROUND,
        no_exception,
        id="StrokeJoinStyle.ROUND",
    ),
    pytest.param(
        StrokeJoinStyle,
        (StrokeJoinStyle.BEVEL, "bevel", 2),
        StrokeJoinStyle.BEVEL,
        no_exception,
        id="StrokeJoinStyle.BEVEL",
    ),
    pytest.param(
        BlendMode,
        (BlendMode.NORMAL, "normal"),
        BlendMode.NORMAL,
        no_exception,
        id="BlendMode.NORMAL",
    ),
    pytest.param(
        BlendMode,
        (BlendMode.MULTIPLY, "multiply"),
        BlendMode.MULTIPLY,
        no_exception,
        id="BlendMode.MULTIPLY",
    ),
    pytest.param(
        BlendMode,
        (BlendMode.SCREEN, "screen"),
        BlendMode.SCREEN,
        no_exception,
        id="BlendMode.SCREEN",
    ),
    pytest.param(
        BlendMode,
        (BlendMode.OVERLAY, "overlay"),
        BlendMode.OVERLAY,
        no_exception,
        id="BlendMode.OVERLAY",
    ),
    pytest.param(
        BlendMode,
        (BlendMode.DARKEN, "darken"),
        BlendMode.DARKEN,
        no_exception,
        id="BlendMode.DARKEN",
    ),
    pytest.param(
        BlendMode,
        (BlendMode.LIGHTEN, "lighten"),
        BlendMode.LIGHTEN,
        no_exception,
        id="BlendMode.LIGHTEN",
    ),
    pytest.param(
        BlendMode,
        (BlendMode.COLOR_DODGE, "color_dodge"),
        BlendMode.COLOR_DODGE,
        no_exception,
        id="BlendMode.COLOR_DODGE",
    ),
    pytest.param(
        BlendMode,
        (BlendMode.COLOR_BURN, "color_burn"),
        BlendMode.COLOR_BURN,
        no_exception,
        id="BlendMode.COLOR_BURN",
    ),
    pytest.param(
        BlendMode,
        (BlendMode.HARD_LIGHT, "hard_light"),
        BlendMode.HARD_LIGHT,
        no_exception,
        id="BlendMode.HARD_LIGHT",
    ),
    pytest.param(
        BlendMode,
        (BlendMode.SOFT_LIGHT, "soft_light"),
        BlendMode.SOFT_LIGHT,
        no_exception,
        id="BlendMode.SOFT_LIGHT",
    ),
    pytest.param(
        BlendMode,
        (BlendMode.DIFFERENCE, "difference"),
        BlendMode.DIFFERENCE,
        no_exception,
        id="BlendMode.DIFFERENCE",
    ),
    pytest.param(
        BlendMode,
        (BlendMode.EXCLUSION, "exclusion"),
        BlendMode.EXCLUSION,
        no_exception,
        id="BlendMode.EXCLUSION",
    ),
    pytest.param(
        BlendMode,
        (BlendMode.HUE, "hue"),
        BlendMode.HUE,
        no_exception,
        id="BlendMode.HUE",
    ),
    pytest.param(
        BlendMode,
        (BlendMode.SATURATION, "saturation"),
        BlendMode.SATURATION,
        no_exception,
        id="BlendMode.SATURATION",
    ),
    pytest.param(
        BlendMode,
        (BlendMode.COLOR, "color"),
        BlendMode.COLOR,
        no_exception,
        id="BlendMode.COLOR",
    ),
    pytest.param(
        BlendMode,
        (BlendMode.LUMINOSITY, "luminosity"),
        BlendMode.LUMINOSITY,
        no_exception,
        id="BlendMode.LUMINOSITY",
    ),
)


style_attributes = (
    pytest.param("auto_close", True, id="auto close"),
    pytest.param("intersection_rule", "evenodd", id="intersection rule"),
    pytest.param("fill_color", None, id="no fill color"),
    pytest.param("fill_color", "#00F", id="RGB 3 fill color"),
    pytest.param("fill_color", "#00FC", id="RGBA 4 fill color"),
    pytest.param("fill_color", "#00FF00", id="RGB 6 fill color"),
    pytest.param("fill_color", "#00FF007F", id="RGBA 8 fill color"),
    pytest.param("fill_opacity", None, id="no fill opacity"),
    pytest.param("fill_opacity", 0.5, id="half fill opacity"),
    pytest.param("stroke_color", None, id="no stroke color"),
    pytest.param("stroke_color", "#00F", id="RGB 3 stroke color"),
    pytest.param("stroke_color", "#00FC", id="RGBA 4 stroke color"),
    pytest.param("stroke_color", "#00FF00", id="RGB 6 stroke color"),
    pytest.param("stroke_color", "#00FF007F", id="RGBA 8 stroke color"),
    pytest.param("stroke_opacity", None, id="no stroke opacity"),
    pytest.param("stroke_opacity", 0.5, id="half stroke opacity"),
    pytest.param("stroke_width", None, id="no stroke width"),
    pytest.param("stroke_width", 0, id="0 stroke width"),
    pytest.param("stroke_width", 2, id="2 stroke width"),
    pytest.param("stroke_join_style", "miter", id="miter stroke join"),
    pytest.param("stroke_join_style", "bevel", id="bevel stroke join"),
    pytest.param("stroke_cap_style", "butt", id="butt stroke cap"),
    pytest.param("stroke_cap_style", "square", id="square stroke cap"),
    pytest.param("stroke_dash_pattern", 0.5, id="numeric stroke dash pattern"),
    pytest.param("stroke_dash_pattern", [0.5, 0.5], id="50-50 stroke dash pattern"),
    pytest.param("stroke_dash_pattern", [1, 2, 3, 1], id="complex stroke dash pattern"),
)

blend_modes = (
    pytest.param("normal"),
    pytest.param("multiply"),
    pytest.param("screen"),
    pytest.param("overlay"),
    pytest.param("darken"),
    pytest.param("lighten"),
    pytest.param("color_dodge"),
    pytest.param("color_burn"),
    pytest.param("hard_light"),
    pytest.param("soft_light"),
    pytest.param("difference"),
    pytest.param("exclusion"),
    pytest.param("hue"),
    pytest.param("saturation"),
    pytest.param("color"),
    pytest.param("luminosity"),
)

invalid_styles = (
    pytest.param("auto_close", 2, TypeError, id="invalid auto_close"),
    pytest.param("paint_rule", 123, TypeError, id="invalid numeric paint_rule"),
    pytest.param("paint_rule", "asdasd", ValueError, id="invalid string paint_rule"),
    pytest.param(
        "intersection_rule", 123, TypeError, id="invalid numeric intersection_rule"
    ),
    pytest.param(
        "intersection_rule", "asdasd", ValueError, id="invalid string intersection_rule"
    ),
    pytest.param("fill_color", "123", ValueError, id="invalid string fill_color"),
    pytest.param("fill_color", 2, TypeError, id="invalid numeric fill_color"),
    pytest.param("fill_opacity", "123123", TypeError, id="invalid string fill_opacity"),
    pytest.param("fill_opacity", 2, ValueError, id="invalid numeric fill_opacity"),
    pytest.param("stroke_color", [2], TypeError, id="invalid stroke_color"),
    pytest.param(
        "stroke_dash_pattern", "123", TypeError, id="invalid string stroke_dash_pattern"
    ),
    pytest.param(
        "stroke_dash_pattern",
        [0.5, "0.5"],
        TypeError,
        id="invalid string in stroke_dash_pattern",
    ),
    pytest.param(
        "stroke_dash_phase", "123", TypeError, id="invalid string stroke_dash_phase"
    ),
    pytest.param(
        "stroke_miter_limit", "123", TypeError, id="invalid string stroke_miter_limit"
    ),
    pytest.param("stroke_width", [2], TypeError, id="invalid stroke_width"),
    pytest.param("invalid_style_name", 2, AttributeError, id="invalid style name"),
)


M = Move
L = Line
B = BezierCurve

path_elements = (
    pytest.param(
        P(1, 1),
        Move(P(1, 2)),
        "1 2 m",
        P(1, 2),
        Move,
        id="move",
    ),
    pytest.param(
        P(1, 1),
        RelativeMove(P(1, 2)),
        "2 3 m",
        P(2, 3),
        Move,
        id="relative move",
    ),
    pytest.param(
        P(1, 1),
        Line(P(1, 2)),
        "1 2 l",
        P(1, 2),
        Line,
        id="line",
    ),
    pytest.param(
        P(1, 1),
        RelativeLine(P(1, 2)),
        "2 3 l",
        P(2, 3),
        Line,
        id="relative line",
    ),
    pytest.param(
        P(1, 1),
        HorizontalLine(2),
        "2 1 l",
        P(2, 1),
        Line,
        id="horizontal line",
    ),
    pytest.param(
        P(1, 1),
        RelativeHorizontalLine(2),
        "3 1 l",
        P(3, 1),
        Line,
        id="relative horizontal line",
    ),
    pytest.param(
        P(1, 1),
        VerticalLine(2),
        "1 2 l",
        P(1, 2),
        Line,
        id="vertical line",
    ),
    pytest.param(
        P(1, 1),
        RelativeVerticalLine(2),
        "1 3 l",
        P(1, 3),
        Line,
        id="relative vertical line",
    ),
    pytest.param(
        P(1, 1),
        BezierCurve(P(1, 2), P(3, 4), P(5, 6)),
        "1 2 3 4 5 6 c",
        P(5, 6),
        BezierCurve,
        id="cubic bezier curve",
    ),
    pytest.param(
        P(1, 1),
        RelativeBezierCurve(P(1, 2), P(3, 4), P(5, 6)),
        "2 3 4 5 6 7 c",
        P(6, 7),
        BezierCurve,
        id="relative cubic bezier curve",
    ),
    pytest.param(
        P(1, 1),
        QuadraticBezierCurve(P(1, 2), P(3, 4)),
        "1 1.6667 1.6667 2.6667 3 4 c",
        P(3, 4),
        QuadraticBezierCurve,
        id="quadratic bezier curve",
    ),
    pytest.param(
        P(1, 1),
        RelativeQuadraticBezierCurve(P(1, 2), P(3, 4)),
        "1.6667 2.3333 2.6667 3.6667 4 5 c",
        P(4, 5),
        QuadraticBezierCurve,
        id="relative quadratic bezier curve",
    ),
    pytest.param(
        P(1, 1),
        Arc(P(1, 2), 0, True, True, P(3, 4)),
        "1.4142 -0.1046 2.1977 -0.3284 2.75 0.5 c 3.3023 1.3284 3.4142 2.8954 3 4 c",
        P(3, 4),
        BezierCurve,
        id="arc",
    ),
    pytest.param(
        P(1, 1),
        RelativeArc(P(1, 2), 0, True, True, P(3, 4)),
        "1.5523 -0.6569 2.6716 -1.1046 3.5 0 c 4.3284 1.1046 4.5523 3.3431 4 5 c",
        P(4, 5),
        BezierCurve,
        id="relative arc",
    ),
    pytest.param(
        P(1, 1),
        Rectangle(P(1, 2), P(3, 4)),
        "1 2 3 4 re",
        P(1, 2),
        Line,
        id="rectangle",
    ),
    pytest.param(
        P(1, 1),
        RoundedRectangle(P(1, 2), P(6, 6), P(1, 2)),
        (
            "2 2 m 6 2 l 6.5523 2 7 2.8954 7 4 c 7 6 l 7 7.1046 6.5523 8 6 8 c 2 8 l "
            "1.4477 8 1 7.1046 1 6 c 1 4 l 1 2.8954 1.4477 2 2 2 c h"
        ),
        P(1, 2),
        Line,
        id="rounded rectangle",
    ),
    pytest.param(
        P(1, 1),
        Ellipse(P(1, 2), P(3, 4)),
        (
            "4 4 m 4 5.1046 3.5523 6 3 6 c 2.4477 6 2 5.1046 2 4 c 2 2.8954 2.4477 2 3 2 c "
            "3.5523 2 4 2.8954 4 4 c h"
        ),
        P(3, 4),
        Move,
        id="rounded rectangle",
    ),
    pytest.param(
        P(1, 1),
        Ellipse(P(1, 2), P(3, 4)),
        (
            "4 4 m 4 5.1046 3.5523 6 3 6 c 2.4477 6 2 5.1046 2 4 c 2 2.8954 2.4477 2 3 2 c "
            "3.5523 2 4 2.8954 4 4 c h"
        ),
        P(3, 4),
        Move,
        id="ellipse",
    ),
    pytest.param(
        P(1, 1),
        ImplicitClose(),
        "",
        P(1, 1),
        Move,
        id="implicit close",
    ),
    pytest.param(
        P(1, 1),
        Close(),
        "h",
        P(1, 1),
        Move,
        id="close",
    ),
)

PP = PaintedPath

paint_rules = (
    pytest.param(PathPaintRule.STROKE, PathPaintRule.STROKE, id="Enum"),
    pytest.param("FILL_EVENODD", PathPaintRule.FILL_EVENODD, id="matching string"),
    pytest.param(
        "stroke_fill_nonzero",
        PathPaintRule.STROKE_FILL_NONZERO,
        id="matching string after uppercasing",
    ),
    pytest.param(None, PathPaintRule.DONT_PAINT, id="None"),
)

clipping_path_result = (
    pytest.param(
        (
            "q 1 1 m 9 1 l 9 9 l 1 9 l h W n 0 0 m 10 0 l 5 10 l h B Q",
            "1 1 m 9 1 l 9 9 l 1 9 l h W n 0 0 m 10 0 l 5 10 l h W n",
        ),
        id="test",
    ),
)

painted_path_elements = (
    # circle, ellipse, rectangle
    pytest.param(
        ((PP.rectangle, (1, 2, 3, 4)),),
        [Move(P(0, 0)), RoundedRectangle(P(1, 2), P(3, 4), P(0, 0))],
        ("q 0 0 m 1 2 3 4 re B Q", "0 0 m 1 2 3 4 re W n"),
        id="rectangle",
    ),
    pytest.param(
        ((PP.circle, (1, 2, 3)),),
        [Move(P(0, 0)), Ellipse(center=P(1, 2), radii=P(3, 3))],
        (
            (
                "q 0 0 m 4 2 m 4 3.6569 2.6569 5 1 5 c -0.6569 5 -2 3.6569 -2 2 c -2 0.3431 "
                "-0.6569 -1 1 -1 c 2.6569 -1 4 0.3431 4 2 c h B Q"
            ),
            (
                "0 0 m 4 2 m 4 3.6569 2.6569 5 1 5 c -0.6569 5 -2 3.6569 -2 2 c -2 0.3431 "
                "-0.6569 -1 1 -1 c 2.6569 -1 4 0.3431 4 2 c h W n"
            ),
        ),
        id="circle",
    ),
    pytest.param(
        ((PP.ellipse, (1, 2, 3, 4)),),
        [Move(P(0, 0)), Ellipse(center=P(1, 2), radii=P(3, 4))],
        (
            (
                "q 0 0 m 4 2 m 4 4.2091 2.6569 6 1 6 c -0.6569 6 -2 4.2091 -2 2 c -2 -0.2091 "
                "-0.6569 -2 1 -2 c 2.6569 -2 4 -0.2091 4 2 c h B Q"
            ),
            (
                "0 0 m 4 2 m 4 4.2091 2.6569 6 1 6 c -0.6569 6 -2 4.2091 -2 2 c -2 -0.2091 "
                "-0.6569 -2 1 -2 c 2.6569 -2 4 -0.2091 4 2 c h W n"
            ),
        ),
        id="ellipse",
    ),
    pytest.param(
        ((PP.line_to, (2, 1)),),
        [Move(P(0, 0)), Line(P(2, 1))],
        ("q 0 0 m 2 1 l h B Q", "0 0 m 2 1 l W n"),
        id="line_to",
    ),
    pytest.param(
        ((PP.line_relative, (2, 1)),),
        [Move(P(0, 0)), RelativeLine(P(2, 1))],
        ("q 0 0 m 2 1 l h B Q", "0 0 m 2 1 l W n"),
        id="line_relative",
    ),
    pytest.param(
        ((PP.horizontal_line_to, (2,)),),
        [Move(P(0, 0)), HorizontalLine(2)],
        ("q 0 0 m 2 0 l h B Q", "0 0 m 2 0 l W n"),
        id="horizontal_line_to",
    ),
    pytest.param(
        ((PP.horizontal_line_relative, (2,)),),
        [Move(P(0, 0)), RelativeHorizontalLine(2)],
        ("q 0 0 m 2 0 l h B Q", "0 0 m 2 0 l W n"),
        id="horizontal_line_relative",
    ),
    pytest.param(
        ((PP.vertical_line_to, (2,)),),
        [Move(P(0, 0)), VerticalLine(2)],
        ("q 0 0 m 0 2 l h B Q", "0 0 m 0 2 l W n"),
        id="vertical_line_to",
    ),
    pytest.param(
        ((PP.vertical_line_relative, (2,)),),
        [Move(P(0, 0)), RelativeVerticalLine(2)],
        ("q 0 0 m 0 2 l h B Q", "0 0 m 0 2 l W n"),
        id="vertical_line_relative",
    ),
    pytest.param(
        ((PP.curve_to, (1, 2, 3, 4, 5, 6)),),
        [Move(P(0, 0)), BezierCurve(P(1, 2), P(3, 4), P(5, 6))],
        ("q 0 0 m 1 2 3 4 5 6 c h B Q", "0 0 m 1 2 3 4 5 6 c W n"),
        id="curve_to",
    ),
    pytest.param(
        ((PP.curve_relative, (1, 2, 3, 4, 5, 6)),),
        [Move(P(0, 0)), RelativeBezierCurve(P(1, 2), P(3, 4), P(5, 6))],
        ("q 0 0 m 1 2 3 4 5 6 c h B Q", "0 0 m 1 2 3 4 5 6 c W n"),
        id="curve_relative",
    ),
    pytest.param(
        ((PP.quadratic_curve_to, (1, 2, 3, 4)),),
        [Move(P(0, 0)), QuadraticBezierCurve(P(1, 2), P(3, 4))],
        (
            "q 0 0 m 0.6667 1.3333 1.6667 2.6667 3 4 c h B Q",
            "0 0 m 0.6667 1.3333 1.6667 2.6667 3 4 c W n",
        ),
        id="quadratic_curve_to",
    ),
    pytest.param(
        ((PP.quadratic_curve_relative, (1, 2, 3, 4)),),
        [Move(P(0, 0)), RelativeQuadraticBezierCurve(P(1, 2), P(3, 4))],
        (
            "q 0 0 m 0.6667 1.3333 1.6667 2.6667 3 4 c h B Q",
            "0 0 m 0.6667 1.3333 1.6667 2.6667 3 4 c W n",
        ),
        id="quadratic_curve_relative",
    ),
    pytest.param(
        ((PP.arc_to, (3, 3, 0, False, False, 1, 1)),),
        [Move(P(0, 0)), Arc(P(3, 3), 0, False, False, P(1, 1))],
        (
            "q 0 0 m 0.2489 0.4083 0.5917 0.7511 1 1 c h B Q",
            "0 0 m 0.2489 0.4083 0.5917 0.7511 1 1 c W n",
        ),
        id="arc_to",
    ),
    pytest.param(
        ((PP.arc_relative, (3, 3, 0, False, False, 1, 1)),),
        [Move(P(0, 0)), RelativeArc(P(3, 3), 0, False, False, P(1, 1))],
        (
            "q 0 0 m 0.2489 0.4083 0.5917 0.7511 1 1 c h B Q",
            "0 0 m 0.2489 0.4083 0.5917 0.7511 1 1 c W n",
        ),
        id="arc_relative",
    ),
    pytest.param(
        ((PP.close, ()),),
        [Move(P(0, 0)), Close()],
        ("q 0 0 m h B Q", "0 0 m h W n"),
        id="close",
    ),
)
