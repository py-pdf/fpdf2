# pylint: disable=redefined-outer-name, protected-access
import pytest

from decimal import Decimal
from contextlib import contextmanager

import fpdf


@contextmanager
def no_exception():
    yield


def exception(exc):
    def wrapper():
        return pytest.raises(exc)

    return wrapper


hex_colors = (
    pytest.param(
        "#CAB", fpdf.drawing.rgb8(r=0xCC, g=0xAA, b=0xBB, a=None), id="RGB hex 3"
    ),
    pytest.param(
        "#FADE", fpdf.drawing.rgb8(r=0xFF, g=0xAA, b=0xDD, a=0xEE), id="RGBA hex 4"
    ),
    pytest.param(
        "#C0FFEE", fpdf.drawing.rgb8(r=0xC0, g=0xFF, b=0xEE, a=None), id="RGB hex 6"
    ),
    pytest.param(
        "#0D06F00D", fpdf.drawing.rgb8(r=0x0D, g=0x06, b=0xF0, a=0x0D), id="RGBA hex 8"
    ),
    pytest.param("#asd", ValueError, id="bad characters"),
    pytest.param("asd", ValueError, id="bad characters missing hash"),
    pytest.param("#12345", ValueError, id="wrong length"),
    pytest.param("123456", ValueError, id="missing hash"),
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

r = fpdf.drawing.Raw


class CustomPrimitive:
    def pdf_repr(self):
        return "custom primitive"


pdf_primitives = (
    pytest.param(fpdf.drawing.Raw("raw output"), r("raw output"), id="raw"),
    pytest.param(CustomPrimitive(), r("custom primitive"), id="custom"),
    pytest.param(fpdf.drawing.Name("pdf_name"), r("/pdf_name"), id="name"),
    pytest.param(
        fpdf.drawing.Name("pdf#<name>"), r("/pdf#23#3Cname#3E"), id="escape name"
    ),
    pytest.param("string", r("(string)"), id="string"),
    pytest.param("\r()\\", r(r"""(\r\(\)\\)"""), id="escape string"),
    pytest.param(b"bytes", r("<6279746573>"), id="bytes"),
    pytest.param(123, r("123"), id="integer"),
    pytest.param(123.456, r("123.456"), id="float"),
    pytest.param(Decimal("1.1"), r("1.1"), id="decimal"),
    pytest.param(True, r("true"), id="True"),
    pytest.param(False, r("false"), id="False"),
    pytest.param(None, r("null"), id="None"),
    pytest.param(
        ["a", b"b", 0xC, fpdf.drawing.Name("d")], r("[(a) <62> 12 /d]"), id="list"
    ),
    pytest.param(
        ("a", b"b", 0xC, fpdf.drawing.Name("d")), r("[(a) <62> 12 /d]"), id="tuple"
    ),
    pytest.param(
        {fpdf.drawing.Name("key"): "value", fpdf.drawing.Name("k2"): True},
        r("<< /key (value)\n/k2 true >>"),
        id="dict",
    ),
)

T = fpdf.drawing.Transform
P = fpdf.drawing.Point

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
        fpdf.drawing.IntersectionRule,
        (fpdf.drawing.IntersectionRule.NONZERO, "NONZERO", "nonzero", "NONzero"),
        fpdf.drawing.IntersectionRule.NONZERO,
        no_exception,
        id="IntersectionRule.NONZERO",
    ),
    pytest.param(
        fpdf.drawing.IntersectionRule,
        (fpdf.drawing.IntersectionRule.EVENODD, "EVENODD", "evenodd", "EveNOdD"),
        fpdf.drawing.IntersectionRule.EVENODD,
        no_exception,
        id="IntersectionRule.EVENODD",
    ),
    pytest.param(
        fpdf.drawing.IntersectionRule,
        ("nonsense",),
        None,
        exception(ValueError),
        id="coerce bad string",
    ),
    pytest.param(
        fpdf.drawing.IntersectionRule,
        (1234,),
        None,
        exception(TypeError),
        id="coerce wrong type entirely",
    ),
    pytest.param(
        fpdf.drawing.PathPaintRule,
        (fpdf.drawing.PathPaintRule.STROKE, "stroke", "S"),
        fpdf.drawing.PathPaintRule.STROKE,
        no_exception,
        id="PathPaintRule.STROKE",
    ),
    pytest.param(
        fpdf.drawing.PathPaintRule,
        (fpdf.drawing.PathPaintRule.FILL_NONZERO, "fill_nonzero", "f"),
        fpdf.drawing.PathPaintRule.FILL_NONZERO,
        no_exception,
        id="PathPaintRule.FILL_NONZERO",
    ),
    pytest.param(
        fpdf.drawing.PathPaintRule,
        (fpdf.drawing.PathPaintRule.FILL_EVENODD, "fill_evenodd", "f*"),
        fpdf.drawing.PathPaintRule.FILL_EVENODD,
        no_exception,
        id="PathPaintRule.FILL_EVENODD",
    ),
    pytest.param(
        fpdf.drawing.PathPaintRule,
        (fpdf.drawing.PathPaintRule.STROKE_FILL_NONZERO, "stroke_fill_nonzero", "B"),
        fpdf.drawing.PathPaintRule.STROKE_FILL_NONZERO,
        no_exception,
        id="PathPaintRule.STROKE_FILL_NONZERO",
    ),
    pytest.param(
        fpdf.drawing.PathPaintRule,
        (fpdf.drawing.PathPaintRule.STROKE_FILL_EVENODD, "stroke_fill_evenodd", "B*"),
        fpdf.drawing.PathPaintRule.STROKE_FILL_EVENODD,
        no_exception,
        id="PathPaintRule.STROKE_FILL_EVENODD",
    ),
    pytest.param(
        fpdf.drawing.PathPaintRule,
        (fpdf.drawing.PathPaintRule.DONT_PAINT, "dont_paint", "n"),
        fpdf.drawing.PathPaintRule.DONT_PAINT,
        no_exception,
        id="PathPaintRule.DONT_PAINT",
    ),
    pytest.param(
        fpdf.drawing.PathPaintRule,
        (fpdf.drawing.PathPaintRule.AUTO, "auto"),
        fpdf.drawing.PathPaintRule.AUTO,
        no_exception,
        id="PathPaintRule.AUTO",
    ),
    pytest.param(
        fpdf.drawing.ClippingPathIntersectionRule,
        (fpdf.drawing.ClippingPathIntersectionRule.NONZERO, "nonzero", "W"),
        fpdf.drawing.ClippingPathIntersectionRule.NONZERO,
        no_exception,
        id="ClippingPathIntersectionRule.NONZERO",
    ),
    pytest.param(
        fpdf.drawing.ClippingPathIntersectionRule,
        (fpdf.drawing.ClippingPathIntersectionRule.EVENODD, "evenodd", "W*"),
        fpdf.drawing.ClippingPathIntersectionRule.EVENODD,
        no_exception,
        id="ClippingPathIntersectionRule.EVENODD",
    ),
    pytest.param(
        fpdf.drawing.StrokeCapStyle,
        (-1,),
        None,
        exception(ValueError),
        id="int coerce out of range",
    ),
    pytest.param(
        fpdf.drawing.StrokeCapStyle,
        ("nonsense",),
        None,
        exception(ValueError),
        id="int coerce bad key",
    ),
    pytest.param(
        fpdf.drawing.StrokeCapStyle,
        (1.0, object()),
        None,
        exception(TypeError),
        id="int coerce bad type",
    ),
    pytest.param(
        fpdf.drawing.StrokeCapStyle,
        (fpdf.drawing.StrokeCapStyle.BUTT, "butt", 0),
        fpdf.drawing.StrokeCapStyle.BUTT,
        no_exception,
        id="StrokeCapStyle.BUTT",
    ),
    pytest.param(
        fpdf.drawing.StrokeCapStyle,
        (fpdf.drawing.StrokeCapStyle.ROUND, "round", 1),
        fpdf.drawing.StrokeCapStyle.ROUND,
        no_exception,
        id="StrokeCapStyle.ROUND",
    ),
    pytest.param(
        fpdf.drawing.StrokeCapStyle,
        (fpdf.drawing.StrokeCapStyle.SQUARE, "square", 2),
        fpdf.drawing.StrokeCapStyle.SQUARE,
        no_exception,
        id="StrokeCapStyle.SQUARE",
    ),
    pytest.param(
        fpdf.drawing.StrokeJoinStyle,
        (fpdf.drawing.StrokeJoinStyle.MITER, "miter", 0),
        fpdf.drawing.StrokeJoinStyle.MITER,
        no_exception,
        id="StrokeJoinStyle.MITER",
    ),
    pytest.param(
        fpdf.drawing.StrokeJoinStyle,
        (fpdf.drawing.StrokeJoinStyle.ROUND, "round", 1),
        fpdf.drawing.StrokeJoinStyle.ROUND,
        no_exception,
        id="StrokeJoinStyle.ROUND",
    ),
    pytest.param(
        fpdf.drawing.StrokeJoinStyle,
        (fpdf.drawing.StrokeJoinStyle.BEVEL, "bevel", 2),
        fpdf.drawing.StrokeJoinStyle.BEVEL,
        no_exception,
        id="StrokeJoinStyle.BEVEL",
    ),
    pytest.param(
        fpdf.drawing.BlendMode,
        (fpdf.drawing.BlendMode.NORMAL, "normal"),
        fpdf.drawing.BlendMode.NORMAL,
        no_exception,
        id="BlendMode.NORMAL",
    ),
    pytest.param(
        fpdf.drawing.BlendMode,
        (fpdf.drawing.BlendMode.MULTIPLY, "multiply"),
        fpdf.drawing.BlendMode.MULTIPLY,
        no_exception,
        id="BlendMode.MULTIPLY",
    ),
    pytest.param(
        fpdf.drawing.BlendMode,
        (fpdf.drawing.BlendMode.SCREEN, "screen"),
        fpdf.drawing.BlendMode.SCREEN,
        no_exception,
        id="BlendMode.SCREEN",
    ),
    pytest.param(
        fpdf.drawing.BlendMode,
        (fpdf.drawing.BlendMode.OVERLAY, "overlay"),
        fpdf.drawing.BlendMode.OVERLAY,
        no_exception,
        id="BlendMode.OVERLAY",
    ),
    pytest.param(
        fpdf.drawing.BlendMode,
        (fpdf.drawing.BlendMode.DARKEN, "darken"),
        fpdf.drawing.BlendMode.DARKEN,
        no_exception,
        id="BlendMode.DARKEN",
    ),
    pytest.param(
        fpdf.drawing.BlendMode,
        (fpdf.drawing.BlendMode.LIGHTEN, "lighten"),
        fpdf.drawing.BlendMode.LIGHTEN,
        no_exception,
        id="BlendMode.LIGHTEN",
    ),
    pytest.param(
        fpdf.drawing.BlendMode,
        (fpdf.drawing.BlendMode.COLOR_DODGE, "color_dodge"),
        fpdf.drawing.BlendMode.COLOR_DODGE,
        no_exception,
        id="BlendMode.COLOR_DODGE",
    ),
    pytest.param(
        fpdf.drawing.BlendMode,
        (fpdf.drawing.BlendMode.COLOR_BURN, "color_burn"),
        fpdf.drawing.BlendMode.COLOR_BURN,
        no_exception,
        id="BlendMode.COLOR_BURN",
    ),
    pytest.param(
        fpdf.drawing.BlendMode,
        (fpdf.drawing.BlendMode.HARD_LIGHT, "hard_light"),
        fpdf.drawing.BlendMode.HARD_LIGHT,
        no_exception,
        id="BlendMode.HARD_LIGHT",
    ),
    pytest.param(
        fpdf.drawing.BlendMode,
        (fpdf.drawing.BlendMode.SOFT_LIGHT, "soft_light"),
        fpdf.drawing.BlendMode.SOFT_LIGHT,
        no_exception,
        id="BlendMode.SOFT_LIGHT",
    ),
    pytest.param(
        fpdf.drawing.BlendMode,
        (fpdf.drawing.BlendMode.DIFFERENCE, "difference"),
        fpdf.drawing.BlendMode.DIFFERENCE,
        no_exception,
        id="BlendMode.DIFFERENCE",
    ),
    pytest.param(
        fpdf.drawing.BlendMode,
        (fpdf.drawing.BlendMode.EXCLUSION, "exclusion"),
        fpdf.drawing.BlendMode.EXCLUSION,
        no_exception,
        id="BlendMode.EXCLUSION",
    ),
    pytest.param(
        fpdf.drawing.BlendMode,
        (fpdf.drawing.BlendMode.HUE, "hue"),
        fpdf.drawing.BlendMode.HUE,
        no_exception,
        id="BlendMode.HUE",
    ),
    pytest.param(
        fpdf.drawing.BlendMode,
        (fpdf.drawing.BlendMode.SATURATION, "saturation"),
        fpdf.drawing.BlendMode.SATURATION,
        no_exception,
        id="BlendMode.SATURATION",
    ),
    pytest.param(
        fpdf.drawing.BlendMode,
        (fpdf.drawing.BlendMode.COLOR, "color"),
        fpdf.drawing.BlendMode.COLOR,
        no_exception,
        id="BlendMode.COLOR",
    ),
    pytest.param(
        fpdf.drawing.BlendMode,
        (fpdf.drawing.BlendMode.LUMINOSITY, "luminosity"),
        fpdf.drawing.BlendMode.LUMINOSITY,
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
)


M = fpdf.drawing.Move
L = fpdf.drawing.Line
B = fpdf.drawing.BezierCurve

path_elements = (
    pytest.param(
        P(1, 1),
        fpdf.drawing.Move(P(1, 2)),
        "1 2 m",
        P(1, 2),
        fpdf.drawing.Move,
        id="move",
    ),
    pytest.param(
        P(1, 1),
        fpdf.drawing.RelativeMove(P(1, 2)),
        "2 3 m",
        P(2, 3),
        fpdf.drawing.Move,
        id="relative move",
    ),
    pytest.param(
        P(1, 1),
        fpdf.drawing.Line(P(1, 2)),
        "1 2 l",
        P(1, 2),
        fpdf.drawing.Line,
        id="line",
    ),
    pytest.param(
        P(1, 1),
        fpdf.drawing.RelativeLine(P(1, 2)),
        "2 3 l",
        P(2, 3),
        fpdf.drawing.Line,
        id="relative line",
    ),
    pytest.param(
        P(1, 1),
        fpdf.drawing.HorizontalLine(2),
        "2 1 l",
        P(2, 1),
        fpdf.drawing.Line,
        id="horizontal line",
    ),
    pytest.param(
        P(1, 1),
        fpdf.drawing.RelativeHorizontalLine(2),
        "3 1 l",
        P(3, 1),
        fpdf.drawing.Line,
        id="relative horizontal line",
    ),
    pytest.param(
        P(1, 1),
        fpdf.drawing.VerticalLine(2),
        "1 2 l",
        P(1, 2),
        fpdf.drawing.Line,
        id="vertical line",
    ),
    pytest.param(
        P(1, 1),
        fpdf.drawing.RelativeVerticalLine(2),
        "1 3 l",
        P(1, 3),
        fpdf.drawing.Line,
        id="relative vertical line",
    ),
    pytest.param(
        P(1, 1),
        fpdf.drawing.BezierCurve(P(1, 2), P(3, 4), P(5, 6)),
        "1 2 3 4 5 6 c",
        P(5, 6),
        fpdf.drawing.BezierCurve,
        id="cubic bezier curve",
    ),
    pytest.param(
        P(1, 1),
        fpdf.drawing.RelativeBezierCurve(P(1, 2), P(3, 4), P(5, 6)),
        "2 3 4 5 6 7 c",
        P(6, 7),
        fpdf.drawing.BezierCurve,
        id="relative cubic bezier curve",
    ),
    pytest.param(
        P(1, 1),
        fpdf.drawing.QuadraticBezierCurve(P(1, 2), P(3, 4)),
        "1 1.6667 1.6667 2.6667 3 4 c",
        P(3, 4),
        fpdf.drawing.QuadraticBezierCurve,
        id="quadratic bezier curve",
    ),
    pytest.param(
        P(1, 1),
        fpdf.drawing.RelativeQuadraticBezierCurve(P(1, 2), P(3, 4)),
        "1.6667 2.3333 2.6667 3.6667 4 5 c",
        P(4, 5),
        fpdf.drawing.QuadraticBezierCurve,
        id="relative quadratic bezier curve",
    ),
    pytest.param(
        P(1, 1),
        fpdf.drawing.Arc(P(1, 2), 0, True, True, P(3, 4)),
        "1.4142 -0.1046 2.1977 -0.3284 2.75 0.5 c 3.3023 1.3284 3.4142 2.8954 3 4 c",
        P(3, 4),
        fpdf.drawing.BezierCurve,
        id="arc",
    ),
    pytest.param(
        P(1, 1),
        fpdf.drawing.RelativeArc(P(1, 2), 0, True, True, P(3, 4)),
        "1.5523 -0.6569 2.6716 -1.1046 3.5 0 c 4.3284 1.1046 4.5523 3.3431 4 5 c",
        P(4, 5),
        fpdf.drawing.BezierCurve,
        id="relative arc",
    ),
    pytest.param(
        P(1, 1),
        fpdf.drawing.Rectangle(P(1, 2), P(3, 4)),
        "1 2 3 4 re",
        P(1, 2),
        fpdf.drawing.Line,
        id="rectangle",
    ),
    pytest.param(
        P(1, 1),
        fpdf.drawing.RoundedRectangle(P(1, 2), P(6, 6), P(1, 2)),
        "2 2 m 6 2 l 6.5523 2 7 2.8954 7 4 c 7 6 l 7 7.1046 6.5523 8 6 8 c 2 8 l "
        "1.4477 8 1 7.1046 1 6 c 1 4 l 1 2.8954 1.4477 2 2 2 c h",
        P(1, 2),
        fpdf.drawing.Line,
        id="rounded rectangle",
    ),
    pytest.param(
        P(1, 1),
        fpdf.drawing.Ellipse(P(1, 2), P(3, 4)),
        "4 4 m 4 5.1046 3.5523 6 3 6 c 2.4477 6 2 5.1046 2 4 c 2 2.8954 2.4477 2 3 2 c "
        "3.5523 2 4 2.8954 4 4 c h",
        P(3, 4),
        fpdf.drawing.Move,
        id="rounded rectangle",
    ),
    pytest.param(
        P(1, 1),
        fpdf.drawing.Ellipse(P(1, 2), P(3, 4)),
        "4 4 m 4 5.1046 3.5523 6 3 6 c 2.4477 6 2 5.1046 2 4 c 2 2.8954 2.4477 2 3 2 c "
        "3.5523 2 4 2.8954 4 4 c h",
        P(3, 4),
        fpdf.drawing.Move,
        id="ellipse",
    ),
    pytest.param(
        P(1, 1),
        fpdf.drawing.ImplicitClose(),
        "",
        P(1, 1),
        fpdf.drawing.Move,
        id="implicit close",
    ),
    pytest.param(
        P(1, 1),
        fpdf.drawing.Close(),
        "h",
        P(1, 1),
        fpdf.drawing.Move,
        id="close",
    ),
)

PP = fpdf.drawing.PaintedPath
d = fpdf.drawing

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
        [d.Move(P(0, 0)), d.RoundedRectangle(P(1, 2), P(3, 4), P(0, 0))],
        ("q 0 0 m 1 2 3 4 re B Q", "0 0 m 1 2 3 4 re W n"),
        id="rectangle",
    ),
    pytest.param(
        ((PP.circle, (1, 2, 3)),),
        [d.Move(P(0, 0)), d.Ellipse(center=P(1, 2), radii=P(3, 3))],
        (
            "q 0 0 m 4 2 m 4 3.6569 2.6569 5 1 5 c -0.6569 5 -2 3.6569 -2 2 c -2 0.3431 "
            "-0.6569 -1 1 -1 c 2.6569 -1 4 0.3431 4 2 c h B Q",
            "0 0 m 4 2 m 4 3.6569 2.6569 5 1 5 c -0.6569 5 -2 3.6569 -2 2 c -2 0.3431 "
            "-0.6569 -1 1 -1 c 2.6569 -1 4 0.3431 4 2 c h W n",
        ),
        id="circle",
    ),
    pytest.param(
        ((PP.ellipse, (1, 2, 3, 4)),),
        [d.Move(P(0, 0)), d.Ellipse(center=P(1, 2), radii=P(3, 4))],
        (
            "q 0 0 m 4 2 m 4 4.2091 2.6569 6 1 6 c -0.6569 6 -2 4.2091 -2 2 c -2 -0.2091 "
            "-0.6569 -2 1 -2 c 2.6569 -2 4 -0.2091 4 2 c h B Q",
            "0 0 m 4 2 m 4 4.2091 2.6569 6 1 6 c -0.6569 6 -2 4.2091 -2 2 c -2 -0.2091 "
            "-0.6569 -2 1 -2 c 2.6569 -2 4 -0.2091 4 2 c h W n",
        ),
        id="ellipse",
    ),
    pytest.param(
        ((PP.line_to, (2, 1)),),
        [d.Move(P(0, 0)), d.Line(P(2, 1))],
        ("q 0 0 m 2 1 l h B Q", "0 0 m 2 1 l W n"),
        id="line_to",
    ),
    pytest.param(
        ((PP.line_relative, (2, 1)),),
        [d.Move(P(0, 0)), d.RelativeLine(P(2, 1))],
        ("q 0 0 m 2 1 l h B Q", "0 0 m 2 1 l W n"),
        id="line_relative",
    ),
    pytest.param(
        ((PP.horizontal_line_to, (2,)),),
        [d.Move(P(0, 0)), d.HorizontalLine(2)],
        ("q 0 0 m 2 0 l h B Q", "0 0 m 2 0 l W n"),
        id="horizontal_line_to",
    ),
    pytest.param(
        ((PP.horizontal_line_relative, (2,)),),
        [d.Move(P(0, 0)), d.RelativeHorizontalLine(2)],
        ("q 0 0 m 2 0 l h B Q", "0 0 m 2 0 l W n"),
        id="horizontal_line_relative",
    ),
    pytest.param(
        ((PP.vertical_line_to, (2,)),),
        [d.Move(P(0, 0)), d.VerticalLine(2)],
        ("q 0 0 m 0 2 l h B Q", "0 0 m 0 2 l W n"),
        id="vertical_line_to",
    ),
    pytest.param(
        ((PP.vertical_line_relative, (2,)),),
        [d.Move(P(0, 0)), d.RelativeVerticalLine(2)],
        ("q 0 0 m 0 2 l h B Q", "0 0 m 0 2 l W n"),
        id="vertical_line_relative",
    ),
    pytest.param(
        ((PP.curve_to, (1, 2, 3, 4, 5, 6)),),
        [d.Move(P(0, 0)), d.BezierCurve(P(1, 2), P(3, 4), P(5, 6))],
        ("q 0 0 m 1 2 3 4 5 6 c h B Q", "0 0 m 1 2 3 4 5 6 c W n"),
        id="curve_to",
    ),
    pytest.param(
        ((PP.curve_relative, (1, 2, 3, 4, 5, 6)),),
        [d.Move(P(0, 0)), d.RelativeBezierCurve(P(1, 2), P(3, 4), P(5, 6))],
        ("q 0 0 m 1 2 3 4 5 6 c h B Q", "0 0 m 1 2 3 4 5 6 c W n"),
        id="curve_relative",
    ),
    pytest.param(
        ((PP.quadratic_curve_to, (1, 2, 3, 4)),),
        [d.Move(P(0, 0)), d.QuadraticBezierCurve(P(1, 2), P(3, 4))],
        (
            "q 0 0 m 0.6667 1.3333 1.6667 2.6667 3 4 c h B Q",
            "0 0 m 0.6667 1.3333 1.6667 2.6667 3 4 c W n",
        ),
        id="quadratic_curve_to",
    ),
    pytest.param(
        ((PP.quadratic_curve_relative, (1, 2, 3, 4)),),
        [d.Move(P(0, 0)), d.RelativeQuadraticBezierCurve(P(1, 2), P(3, 4))],
        (
            "q 0 0 m 0.6667 1.3333 1.6667 2.6667 3 4 c h B Q",
            "0 0 m 0.6667 1.3333 1.6667 2.6667 3 4 c W n",
        ),
        id="quadratic_curve_relative",
    ),
    pytest.param(
        ((PP.arc_to, (3, 3, 0, False, False, 1, 1)),),
        [d.Move(P(0, 0)), d.Arc(P(3, 3), 0, False, False, P(1, 1))],
        (
            "q 0 0 m 0.2489 0.4083 0.5917 0.7511 1 1 c h B Q",
            "0 0 m 0.2489 0.4083 0.5917 0.7511 1 1 c W n",
        ),
        id="arc_to",
    ),
    pytest.param(
        ((PP.arc_relative, (3, 3, 0, False, False, 1, 1)),),
        [d.Move(P(0, 0)), d.RelativeArc(P(3, 3), 0, False, False, P(1, 1))],
        (
            "q 0 0 m 0.2489 0.4083 0.5917 0.7511 1 1 c h B Q",
            "0 0 m 0.2489 0.4083 0.5917 0.7511 1 1 c W n",
        ),
        id="arc_relative",
    ),
    pytest.param(
        ((PP.close, ()),),
        [d.Move(P(0, 0)), d.Close()],
        ("q 0 0 m h B Q", "0 0 m h W n"),
        id="close",
    ),
)
