# pylint: disable=redefined-outer-name, no-self-use, protected-access
import pytest

from decimal import Decimal

import fpdf

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
    pytest.param("\n\r\t\b\f()\\", r(r"""(\n\r\t\b\f\(\)\\)"""), id="escape string"),
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
    pytest.param("auto_close", 2, ValueError, id="invalid auto_close"),
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
