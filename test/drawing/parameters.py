import pytest

from decimal import Decimal

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

numbers = (
    pytest.param(100, "100", id="integer"),
    pytest.param(Decimal("1.1"), "1.1", id="Decimal"),
    pytest.param(Decimal("0.000008"), "0", id="truncated Decimal"),
    pytest.param(1.05, "1.05", id="float"),
    pytest.param(10.00001, "10", id="truncated float"),
    pytest.param(-1.12345, "-1.1235", id="rounded float"),
    pytest.param(-0.00004, "-0", id="negative zero"),
)
