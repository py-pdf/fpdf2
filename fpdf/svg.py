"""
Utilities to parse SVG graphics into fpdf.drawing objects.

The contents of this module are internal to fpdf2, and not part of the public API.
They may change at any time without prior warning or any deprecation period,
in non-backward-compatible ways.

Usage documentation at: <https://py-pdf.github.io/fpdf2/SVG.html>
"""

import logging, math, re, warnings
from copy import deepcopy
from numbers import Number
from typing import NamedTuple, Optional, Tuple

from fontTools.svgLib.path import parse_path

from .enums import PathPaintRule

try:
    from defusedxml.ElementTree import fromstring as parse_xml_str
except ImportError:
    warnings.warn(
        "defusedxml could not be imported - fpdf2 will not be able to sanitize SVG images provided"
    )
    # nosemgrep: python.lang.security.use-defused-xml.use-defused-xml
    from xml.etree.ElementTree import fromstring as parse_xml_str  # nosec

from . import html
from .drawing_primitives import color_from_hex_string, color_from_rgb_string, Transform

from .drawing import (
    GraphicsContext,
    GraphicsStyle,
    PaintedPath,
    PathPen,
    ClippingPath,
    Text,
    TextRun,
)
from .image_datastructures import ImageCache, VectorImageInfo
from .output import stream_content_for_raster_image

LOGGER = logging.getLogger(__name__)

__pdoc__ = {"force_nodocument": False}


def force_nodocument(item):
    """A decorator that forces pdoc not to document the decorated item (class or method)"""
    __pdoc__[item.__qualname__] = False
    return item


# https://www.w3.org/TR/SVG/Overview.html

_HANDY_NAMESPACES = {
    "svg": "http://www.w3.org/2000/svg",
    "xlink": "http://www.w3.org/1999/xlink",
}

NUMBER_SPLIT = re.compile(r"(?:\s+,\s+|\s+,|,\s+|\s+|,)")
TRANSFORM_GETTER = re.compile(
    r"(matrix|rotate|scale|scaleX|scaleY|skew|skewX|skewY|translate|translateX|translateY)\(([\d\.,\s+-]+)\)"
)

CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
CSS_BLOCK_RE = re.compile(r"(?s)([^{}]+)\{([^{}]*)\}")


def _normalize_css_value(value):
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        return stripped
    return value


@force_nodocument
class Percent(float):
    """class to represent percentage values"""


unit_splitter = re.compile(r"\s*(?P<value>[-+]?[\d\.]+)\s*(?P<unit>%|[a-zA-Z]*)")

# none of these are supported right now
# https://www.w3.org/TR/css-values-4/#lengths
relative_length_units = {
    "%",  # (context sensitive, depends on which attribute it is applied to)
    "em",  # (current font size)
    "ex",  # (current font x-height)
    # CSS 3
    "ch",  # (advance measure of 0, U+0030 glyph)
    "rem",  # (font-size of the root element)
    "vw",  # (1% of viewport width)
    "vh",  # (1% of viewport height)
    "vmin",  # (smaller of vw or vh)
    "vmax",  # (larger of vw or vh)
    # CSS 4
    "cap",  # (font cap height)
    "ic",  # (advance measure of fullwidth U+6C34 glyph)
    "lh",  # (line height)
    "rlh",  # (root element line height)
    "vi",  # (1% of viewport size in root element's inline axis)
    "vb",  # (1% of viewport size in root element's block axis)
}

absolute_length_units = {
    "in": 72,  # (inches, 72 pt)
    "cm": 72 / 2.54,  # (centimeters, 72 / 2.54 pt)
    "mm": 72 / 25.4,  # (millimeters 72 / 25.4 pt)
    "pt": 1,  # (pdf canonical unit)
    "pc": 12,  # (pica, 12 pt)
    "px": 0.75,  # (reference pixel unit, 0.75 pt)
    # CSS 3
    "Q": 72 / 101.6,  # (quarter-millimeter, 72 / 101.6 pt)
}

angle_units = {
    "deg": math.tau / 360,
    "grad": math.tau / 400,
    "rad": 1,  # pdf canonical unit
    "turn": math.tau,
}


# in CSS the default length unit is px, but as far as I can tell, for SVG interpreting
# unitless numbers as being expressed in pt is more appropriate. Particularly, the
# scaling we do using viewBox attempts to scale so that 1 svg user unit = 1 pdf pt
# because this results in the output PDF having the correct physical dimensions (i.e. a
# feature with a 1cm size in SVG will actually end up being 1cm in size in the PDF).
@force_nodocument
def resolve_length(length_str, default_unit="pt"):
    """Convert a length unit to our canonical length unit, pt."""
    match = unit_splitter.match(length_str)
    if match is None:
        raise ValueError(f"Unable to parse '{length_str}' as a length") from None
    value, unit = match.groups()
    if not unit:
        unit = default_unit

    try:
        return float(value) * absolute_length_units[unit]
    except KeyError:
        if unit in relative_length_units:
            raise ValueError(
                f"{length_str} uses unsupported relative length {unit}"
            ) from None

        raise ValueError(f"{length_str} contains unrecognized unit {unit}") from None


@force_nodocument
def resolve_angle(angle_str, default_unit="deg"):
    """Convert an angle value to our canonical angle unit, radians"""
    value, unit = unit_splitter.match(angle_str).groups()
    if not unit:
        unit = default_unit

    try:
        return float(value) * angle_units[unit]
    except KeyError:
        raise ValueError(f"angle {angle_str} has unknown unit {unit}") from None


@force_nodocument
def xmlns(space, name):
    """Create an XML namespace string representation for the given tag name."""
    try:
        space = f"{{{_HANDY_NAMESPACES[space]}}}"
    except KeyError:
        space = ""

    return f"{space}{name}"


@force_nodocument
def xmlns_lookup(space, *names):
    """Create a lookup for the given name in the given XML namespace."""

    result = {}
    for name in names:
        result[xmlns(space, name)] = name
        result[name] = name

    return result


@force_nodocument
def without_ns(qualified_tag):
    """Remove the xmlns namespace from a qualified XML tag name"""
    i = qualified_tag.index("}")
    if i >= 0:
        return qualified_tag[i + 1 :]
    return qualified_tag


shape_tags = xmlns_lookup(
    "svg", "rect", "circle", "ellipse", "line", "polyline", "polygon"
)


@force_nodocument
def svgcolor(colorstr):
    try:
        colorstr = html.COLOR_DICT[colorstr]
    except KeyError:
        pass

    if colorstr.startswith("#"):
        return color_from_hex_string(colorstr)

    if colorstr.startswith("rgb"):
        return color_from_rgb_string(colorstr)

    raise ValueError(f"unsupported color specification {colorstr}")


@force_nodocument
def convert_stroke_width(incoming):
    val = resolve_length(incoming)
    if val < 0:
        raise ValueError(f"stroke width {incoming} cannot be negative")
    if val == 0:
        return None

    return val


@force_nodocument
def convert_miterlimit(incoming):
    val = float(incoming)
    if val < 1.0:
        raise ValueError(f"miter limit {incoming} cannot be less than 1")

    return val


@force_nodocument
def clamp_float(min_val, max_val):
    def converter(value):
        val = float(value)
        if val < min_val:
            return min_val
        if val > max_val:
            return max_val
        return val

    return converter


@force_nodocument
def inheritable(value, converter=lambda value: value):
    if value in ("inherit", "currentColor"):
        return GraphicsStyle.INHERIT

    return converter(value)


@force_nodocument
def optional(value, converter=lambda noop: noop):
    # Treat missing/empty/whitespace exactly like "not set"
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    if value == "none":
        return None

    return inheritable(value, converter)


# this is mostly SVG 1.1 stuff. SVG 2 changed some of this and the documentation is much
# harder to assemble into something coherently understandable
svg_attr_map = {
    # https://www.w3.org/TR/SVG11/painting.html#FillProperty
    "fill": lambda colorstr: ("fill_color", optional(colorstr, svgcolor)),
    # https://www.w3.org/TR/SVG11/painting.html#FillRuleProperty
    "fill-rule": lambda fillrulestr: ("intersection_rule", inheritable(fillrulestr)),
    # https://www.w3.org/TR/SVG11/painting.html#FillOpacityProperty
    "fill-opacity": lambda filopstr: (
        "fill_opacity",
        inheritable(filopstr, clamp_float(0.0, 1.0)),
    ),
    # https://www.w3.org/TR/SVG11/painting.html#StrokeProperty
    "stroke": lambda colorstr: ("stroke_color", optional(colorstr, svgcolor)),
    # https://www.w3.org/TR/SVG11/painting.html#StrokeWidthProperty
    "stroke-width": lambda valuestr: (
        "stroke_width",
        inheritable(valuestr, convert_stroke_width),
    ),
    # https://www.w3.org/TR/SVG11/painting.html#StrokeDasharrayProperty
    "stroke-dasharray": lambda dasharray: (
        "stroke_dash_pattern",
        optional(
            dasharray,
            lambda da: [float(item) for item in NUMBER_SPLIT.split(da) if item],
        ),
    ),
    # stroke-dashoffset may be a percentage, which we don't support currently
    # https://www.w3.org/TR/SVG11/painting.html#StrokeDashoffsetProperty
    "stroke-dashoffset": lambda dashoff: (
        "stroke_dash_phase",
        inheritable(dashoff, float),
    ),
    # https://www.w3.org/TR/SVG11/painting.html#StrokeLinecapProperty
    "stroke-linecap": lambda capstr: ("stroke_cap_style", inheritable(capstr)),
    # https://www.w3.org/TR/SVG11/painting.html#StrokeLinejoinProperty
    "stroke-linejoin": lambda joinstr: ("stroke_join_style", inheritable(joinstr)),
    # https://www.w3.org/TR/SVG11/painting.html#StrokeMiterlimitProperty
    "stroke-miterlimit": lambda limstr: (
        "stroke_miter_limit",
        inheritable(limstr, convert_miterlimit),
    ),
    # https://www.w3.org/TR/SVG11/painting.html#StrokeOpacityProperty
    "stroke-opacity": lambda stropstr: (
        "stroke_opacity",
        inheritable(stropstr, clamp_float(0.0, 1.0)),
    ),
}


@force_nodocument
def apply_styles(stylable, svg_element, computed_style=None):
    """Apply the known styles from `svg_element` to the pdf path/group `stylable`."""
    if computed_style is not None:
        style = computed_style
    else:
        style = {}
        for key, value in html.parse_css_style(
            svg_element.attrib.get("style", "")
        ).items():
            norm_value = _normalize_css_value(value)
            if norm_value is not None:
                style[key] = norm_value

    stylable.style.auto_close = False

    for attr_name, converter in svg_attr_map.items():
        value = _normalize_css_value(style.get(attr_name))
        if value is None:
            value = _normalize_css_value(svg_element.attrib.get(attr_name))
        if value is not None:
            setattr(stylable.style, *converter(value))

    # handle this separately for now
    opacity = _normalize_css_value(style.get("opacity"))
    if opacity is None:
        opacity = _normalize_css_value(svg_element.attrib.get("opacity"))
    if opacity is not None:
        opacity = float(opacity)
        stylable.style.fill_opacity = opacity
        stylable.style.stroke_opacity = opacity

    tfstr = svg_element.attrib.get("transform")
    if tfstr:
        stylable.transform = convert_transforms(tfstr)


def _preserve_ws(style_map: dict, tag) -> bool:
    # CSS ‘white-space’ wins; otherwise XML’s xml:space
    ws = (style_map.get("white-space") or "").strip()
    if ws in ("pre", "pre-wrap", "break-spaces"):
        return True
    xml_space = tag.attrib.get("{http://www.w3.org/XML/1998/namespace}space")
    return xml_space == "preserve"


def _collapse_ws(s: str, *, preserve: bool = False) -> str:
    """
    Collapse sequences of whitespace characters (spaces, tabs, etc.) to a single space
    In some cases, like with `pre` tags, whitespace should be preserved.
    """
    if s is None:
        return ""
    if preserve:
        return s  # keep all spaces/newlines
    return re.sub(r"\s+", " ", s)


def _svg_font_style_to_emphasis(font_style: str, font_weight: str) -> str:
    # Map CSS-like values to fpdf "B", "I", "BI", ""
    b = False
    i = False
    if font_weight:
        fw = font_weight.strip().lower()
        # numeric 600+ considered bold in CSS, also "bold", "bolder"
        b = fw in ("bold", "bolder") or (fw.isdigit() and int(fw) >= 600)
    if font_style:
        fs = font_style.strip().lower()
        i = fs in ("italic", "oblique")
    if b and i:
        return "BI"
    if b:
        return "B"
    if i:
        return "I"
    return ""


def _get_attr_or_style(
    tag, name: str, style_map: Optional[dict] = None
) -> Optional[str]:
    """Return the value for a given attribute, honoring computed style overrides."""
    if style_map is not None:
        value = _normalize_css_value(style_map.get(name))
        if value is not None:
            return value
    if style_map is None:
        inline = html.parse_css_style(tag.attrib.get("style", ""))
        value = _normalize_css_value(inline.get(name))
        if value is not None:
            return value
    return _normalize_css_value(tag.attrib.get(name))


def _parse_font_attrs(
    tag, style_map: Optional[dict] = None
) -> Tuple[Optional[str], str, Optional[float], str]:
    """Returns (font_family or None, font_style_emphasis, font_size_pt or None, text_anchor)"""
    family_value = _get_attr_or_style(tag, "font-family", style_map)
    if family_value:
        cleaned = []
        for item in family_value.split(","):
            stripped = item.strip().replace('"', "").replace("'", "")
            if stripped:
                cleaned.append(stripped)
        family = ",".join(cleaned) if cleaned else None
    else:
        family = None

    # style/weight -> B/I/BI/""
    font_style = _get_attr_or_style(tag, "font-style", style_map) or ""
    font_weight = _get_attr_or_style(tag, "font-weight", style_map) or ""
    emphasis = _svg_font_style_to_emphasis(font_style, font_weight)

    # font-size: default 16px (SVG/CSS); resolve_length defaults to pt; px=0.75pt defined above.
    fs = _get_attr_or_style(tag, "font-size", style_map)
    size_pt = (
        resolve_length(fs) if fs is not None else None
    )  # px handled in absolute_length_units

    # text-anchor: start|middle|end (default start)
    ta = (_get_attr_or_style(tag, "text-anchor", style_map) or "start").strip().lower()
    if ta not in ("start", "middle", "end"):
        ta = "start"

    return family, emphasis, float(size_pt) if size_pt is not None else None, ta


def _parse_xy_delta(
    tag,
    style_map: Optional[dict] = None,
    font_size: Optional[float] = None,
) -> Tuple[float, float, float, float]:
    """x,y (default 0,0) and optional dx,dy (default 0)"""

    # pylint: disable=too-many-return-statements
    def first_number(name: str, default: float = 0.0, resolver=resolve_length):
        attr = None
        if style_map is not None and name in style_map:
            attr = style_map[name]
        elif name in tag.attrib:
            attr = tag.attrib[name]
        if not attr:
            return default
        parts = NUMBER_SPLIT.split(attr.strip())
        if not parts or not parts[0]:
            return default
        token = parts[0]
        match = unit_splitter.fullmatch(token)
        if match:
            value_str = match.group("value")
            unit = (match.group("unit") or "").strip()
            if unit.lower() in {"em", "rem"}:
                if font_size is None:
                    LOGGER.warning(
                        "Ignoring relative %s length on <%s %s> because font size is unknown",
                        unit,
                        tag.tag,
                        name,
                    )
                    return default
                try:
                    return float(value_str) * font_size
                except (TypeError, ValueError):
                    return default
            if unit.lower() == "ex":
                if font_size is None:
                    LOGGER.warning(
                        "Ignoring relative ex length on <%s %s> because font size is unknown",
                        tag.tag,
                        name,
                    )
                    return default
                try:
                    return float(value_str) * font_size * 0.5
                except (TypeError, ValueError):
                    return default
        try:
            return float(resolver(token))
        except ValueError:
            LOGGER.warning(
                "Ignoring unsupported length '%s' on <%s %s>",
                token,
                tag.tag,
                name,
            )
            return default

    x = first_number("x", 0.0)
    y = first_number("y", 0.0)
    dx = first_number("dx", 0.0)
    dy = first_number("dy", 0.0)
    return x, y, dx, dy


def _extract_css_class_styles(css_text):
    styles = []
    if not css_text:
        return styles

    cleaned = CSS_COMMENT_RE.sub("", css_text)
    for selector_block, body in CSS_BLOCK_RE.findall(cleaned):
        declarations = html.parse_css_style(body)
        if not declarations:
            continue
        normalized = {}
        for key, value in declarations.items():
            norm_value = _normalize_css_value(value)
            if norm_value is not None:
                normalized[key] = norm_value
        if not normalized:
            continue
        selectors = [selector.strip() for selector in selector_block.split(",")]
        for selector in selectors:
            if not selector.startswith("."):
                continue
            class_name = selector[1:].split(":", 1)[0].strip()
            if not class_name:
                continue
            styles.append((class_name, dict(normalized)))
    return styles


@force_nodocument
class ShapeBuilder:
    """A namespace within which methods for converting basic shapes can be looked up."""

    @staticmethod
    def new_path(tag, clipping_path: bool = False):
        """Create a new path with the appropriate styles."""
        path = PaintedPath()
        if clipping_path:
            path = ClippingPath()
        apply_styles(path, tag)
        return path

    @classmethod
    def rect(cls, tag, clipping_path: bool = False):
        """Convert an SVG <rect> into a PDF path."""
        # svg rect is wound clockwise
        x = resolve_length(tag.attrib.get("x", "0"))
        y = resolve_length(tag.attrib.get("y", "0"))
        width = tag.attrib.get("width", "0")
        if width.endswith("%"):
            width = Percent(width[:-1])
        else:
            width = resolve_length(width)
        height = tag.attrib.get("height", "0")
        if height.endswith("%"):
            height = Percent(height[:-1])
        else:
            height = resolve_length(height)
        rx = tag.attrib.get("rx", "auto")
        ry = tag.attrib.get("ry", "auto")

        if rx == "none":
            rx = 0
        if ry == "none":
            ry = 0

        if rx == ry == "auto":
            rx = ry = 0
        elif rx == "auto":
            rx = ry = float(ry)
        elif ry == "auto":
            ry = rx = float(rx)
        else:
            rx = float(rx)
            ry = float(ry)

        if (width < 0) or (height < 0) or (rx < 0) or (ry < 0):
            raise ValueError(f"bad rect {tag}")

        if (width == 0) or (height == 0):
            return PaintedPath()

        if rx > (width / 2):
            rx = width / 2
        if ry > (height / 2):
            ry = height / 2

        path = cls.new_path(tag, clipping_path)
        path.rectangle(x, y, width, height, rx, ry)
        return path

    @classmethod
    def circle(cls, tag, clipping_path: bool = False):
        """Convert an SVG <circle> into a PDF path."""
        cx = float(tag.attrib.get("cx", 0))
        cy = float(tag.attrib.get("cy", 0))
        r = float(tag.attrib["r"])

        path = cls.new_path(tag, clipping_path)
        path.circle(cx, cy, r)
        return path

    @classmethod
    def ellipse(cls, tag, clipping_path: bool = False):
        """Convert an SVG <ellipse> into a PDF path."""
        cx = float(tag.attrib.get("cx", 0))
        cy = float(tag.attrib.get("cy", 0))

        rx = tag.attrib.get("rx", "auto")
        ry = tag.attrib.get("ry", "auto")

        path = cls.new_path(tag, clipping_path)

        if (rx == ry == "auto") or (rx == 0) or (ry == 0):
            return path

        if rx == "auto":
            rx = ry = float(ry)
        elif ry == "auto":
            rx = ry = float(rx)
        else:
            rx = float(rx)
            ry = float(ry)

        path.ellipse(cx, cy, rx, ry)
        return path

    @classmethod
    def line(cls, tag):
        """Convert an SVG <line> into a PDF path."""
        x1 = float(tag.attrib["x1"])
        y1 = float(tag.attrib["y1"])
        x2 = float(tag.attrib["x2"])
        y2 = float(tag.attrib["y2"])

        path = cls.new_path(tag)
        path.move_to(x1, y1)
        path.line_to(x2, y2)
        return path

    @classmethod
    def polyline(cls, tag):
        """Convert an SVG <polyline> into a PDF path."""
        path = cls.new_path(tag)
        points = "M" + tag.attrib["points"]
        svg_path_converter(path, points)
        return path

    @classmethod
    def polygon(cls, tag, clipping_path: bool = False):
        """Convert an SVG <polygon> into a PDF path."""
        path = cls.new_path(tag, clipping_path)
        points = "M" + tag.attrib["points"] + "Z"
        svg_path_converter(path, points)
        return path


@force_nodocument
def convert_transforms(tfstr):
    """Convert SVG/CSS transform functions into PDF transforms."""

    # SVG 2 uses CSS transforms. SVG 1.1 transforms are slightly different. I'm really
    # not sure if it is worth it to try to support SVG 2 because it is significantly
    # more entangled with The HTML Disaster than SVG 1.1, which makes it astronomically
    # harder to support.
    # https://drafts.csswg.org/css-transforms/#two-d-transform-functions
    parsed = TRANSFORM_GETTER.findall(tfstr)
    # pylint: disable=redefined-loop-name
    transform = Transform.identity()
    for tf_type, args in parsed:
        args = args.strip()
        if tf_type == "matrix":
            a, b, c, d, e, f = tuple(float(n) for n in NUMBER_SPLIT.split(args))
            transform = Transform(a, b, c, d, e, f) @ transform

        elif tf_type == "rotate":
            theta, *about = NUMBER_SPLIT.split(args)
            theta = resolve_angle(theta)
            rotation = Transform.rotation(theta=theta)
            if about:
                # this is an SVG 1.1 feature. SVG 2 uses the transform-origin property.
                # see: https://www.w3.org/TR/SVG11/coords.html#TransformAttribute
                if len(about) == 2:
                    rotation = rotation.about(float(about[0]), float(about[1]))
                else:
                    raise ValueError(
                        f"rotation transform {tf_type}({args}) is malformed"
                    )

            transform = rotation @ transform

        elif tf_type == "scale":
            # if sy is not provided, it takes a value equal to sx
            args = NUMBER_SPLIT.split(args)
            if len(args) == 2:
                sx = float(args[0])
                sy = float(args[1])
            elif len(args) == 1:
                sx = sy = float(args[0])
            else:
                raise ValueError(f"bad scale transform {tfstr}")

            transform = Transform.scaling(x=sx, y=sy) @ transform

        elif tf_type == "scaleX":  # SVG 2
            transform = Transform.scaling(x=float(args), y=1) @ transform

        elif tf_type == "scaleY":  # SVG 2
            transform = Transform.scaling(x=1, y=float(args)) @ transform

        elif tf_type == "skew":  # SVG 2, not the same as skewX@skewY
            # if sy is not provided, it takes a value equal to 0
            args = NUMBER_SPLIT.split(args)
            if len(args) == 2:
                sx = resolve_angle(args[0])
                sy = resolve_angle(args[1])
            elif len(args) == 1:
                sx = resolve_angle(args[0])
                sy = 0
            else:
                raise ValueError(f"bad skew transform {tfstr}")

            transform = Transform.shearing(x=math.tan(sx), y=math.tan(sy)) @ transform

        elif tf_type == "skewX":
            transform = (
                Transform.shearing(x=math.tan(resolve_angle(args)), y=0) @ transform
            )

        elif tf_type == "skewY":
            transform = (
                Transform.shearing(x=0, y=math.tan(resolve_angle(args))) @ transform
            )

        elif tf_type == "translate":
            # if y is not provided, it takes a value equal to 0
            args = NUMBER_SPLIT.split(args)
            if len(args) == 2:
                x = resolve_length(args[0])
                y = resolve_length(args[1])
            elif len(args) == 1:
                x = resolve_length(args[0])
                y = 0
            else:
                raise ValueError(f"bad translation transform {tfstr}")

            transform = Transform.translation(x=x, y=y) @ transform

        elif tf_type == "translateX":  # SVG 2
            transform = Transform.translation(x=resolve_length(args), y=0) @ transform

        elif tf_type == "translateY":  # SVG 2
            transform = Transform.translation(x=0, y=resolve_length(args)) @ transform

    return transform


@force_nodocument
def svg_path_converter(pdf_path, svg_path):
    pen = PathPen(pdf_path)
    parse_path(svg_path, pen)
    if not pen.first_is_move:
        raise ValueError("Path does not start with move item")


class SVGObject:
    """
    A representation of an SVG that has been converted to a PDF representation.
    """

    @classmethod
    def from_file(cls, filename, *args, encoding="utf-8", **kwargs):
        """
        Create an `SVGObject` from the contents of the file at `filename`.

        Args:
            filename (path-like): the path to a file containing SVG data.
            *args: forwarded directly to the SVGObject initializer. For subclass use.
            encoding (str): optional charset encoding to use when reading the file.
            **kwargs: forwarded directly to the SVGObject initializer. For subclass use.

        Returns:
            A converted `SVGObject`.
        """
        with open(filename, "r", encoding=encoding) as svgfile:
            return cls(svgfile.read(), *args, **kwargs)

    def __init__(self, svg_text, image_cache: ImageCache = None):
        self.image_cache = image_cache  # Needed to render images
        self.cross_references = {}
        self.css_class_styles = {}

        # disabling bandit rule as we use defusedxml:
        svg_tree = parse_xml_str(svg_text)  # nosec B314

        if svg_tree.tag not in xmlns_lookup("svg", "svg"):
            raise ValueError(f"root tag must be svg, not {svg_tree.tag}")

        self._collect_css_styles(svg_tree)
        self.extract_shape_info(svg_tree)
        self.convert_graphics(svg_tree)

    @force_nodocument
    def update_xref(self, key, referenced):
        if key:
            key = "#" + key if not key.startswith("#") else key
            self.cross_references[key] = referenced

    def _collect_css_styles(self, root_tag):
        for node in root_tag.iter():
            if node.tag in xmlns_lookup("svg", "style"):
                css_text = "".join(node.itertext() or [])
                for class_name, declarations in _extract_css_class_styles(css_text):
                    existing = self.css_class_styles.setdefault(class_name, {})
                    existing.update(declarations)

    def _style_map_for(self, tag):
        style_map = {}
        if self.css_class_styles:
            class_attr = tag.attrib.get("class")
            if class_attr:
                for class_name in class_attr.split():
                    class_styles = self.css_class_styles.get(class_name)
                    if class_styles:
                        style_map.update(class_styles)
        inline = html.parse_css_style(tag.attrib.get("style", ""))
        for key, value in inline.items():
            norm_value = _normalize_css_value(value)
            if norm_value is not None:
                style_map[key] = norm_value
            elif key in style_map:
                style_map.pop(key, None)
        inheritable_attrs = (
            "font-family",
            "font-size",
            "font-style",
            "font-weight",
            "text-anchor",
            "white-space",
        )
        for attr in inheritable_attrs:
            if attr in tag.attrib:
                norm_value = _normalize_css_value(tag.attrib.get(attr))
                if norm_value is not None:
                    style_map.setdefault(attr, norm_value)
        return style_map

    @force_nodocument
    def extract_shape_info(self, root_tag):
        """Collect shape info from the given SVG."""

        width = root_tag.get("width")
        height = root_tag.get("height")
        viewbox = root_tag.get("viewBox")
        # we don't fully support this, just check for its existence
        preserve_ar = root_tag.get("preserveAspectRatio", True)
        if preserve_ar == "none":
            self.preserve_ar = None
        else:
            self.preserve_ar = True

        self.width = None
        if width is not None:
            width.strip()
            if width.endswith("%"):
                self.width = Percent(width[:-1])
            else:
                self.width = resolve_length(width)

        self.height = None
        if height is not None:
            height.strip()
            if height.endswith("%"):
                self.height = Percent(height[:-1])
            else:
                self.height = resolve_length(height)

        if viewbox is None:
            self.viewbox = None
        else:
            viewbox = viewbox.strip()
            vx, vy, vw, vh = [float(num) for num in NUMBER_SPLIT.split(viewbox)]
            if (vw < 0) or (vh < 0):
                raise ValueError(f"invalid negative width/height in viewbox {viewbox}")

            self.viewbox = [vx, vy, vw, vh]

    @force_nodocument
    def convert_graphics(self, root_tag):
        """Convert the graphics contained in the SVG into the PDF representation."""
        base_group = GraphicsContext()
        base_group.style.stroke_width = None
        base_group.style.auto_close = False
        base_group.style.stroke_cap_style = "butt"

        self.build_group(root_tag, base_group)

        self.base_group = base_group

    def transform_to_page_viewport(self, pdf, align_viewbox=True):
        """
        Size the converted SVG paths to the page viewport.

        The SVG document size can be specified relative to the rendering viewport
        (e.g. width=50%). If the converted SVG sizes are relative units, then this
        computes the appropriate scale transform to size the SVG to the correct
        dimensions for a page in the current PDF document.

        If the SVG document size is specified in absolute units, then it is not scaled.

        Args:
            pdf (fpdf.fpdf.FPDF): the pdf to use the page size of.
            align_viewbox (bool): if True, mimic some of the SVG alignment rules if the
                viewbox aspect ratio does not match that of the viewport.

        Returns:
            The same thing as `SVGObject.transform_to_rect_viewport`.
        """

        return self.transform_to_rect_viewport(pdf.k, pdf.epw, pdf.eph, align_viewbox)

    def transform_to_rect_viewport(
        self, scale, width, height, align_viewbox=True, ignore_svg_top_attrs=False
    ):
        """
        Size the converted SVG paths to an arbitrarily sized viewport.

        The SVG document size can be specified relative to the rendering viewport
        (e.g. width=50%). If the converted SVG sizes are relative units, then this
        computes the appropriate scale transform to size the SVG to the correct
        dimensions for a page in the current PDF document.

        Args:
            scale (Number): the scale factor from document units to PDF points.
            width (Number): the width of the viewport to scale to in document units.
            height (Number): the height of the viewport to scale to in document units.
            align_viewbox (bool): if True, mimic some of the SVG alignment rules if the
                viewbox aspect ratio does not match that of the viewport.
            ignore_svg_top_attrs (bool): ignore <svg> top attributes like "width", "height"
                or "preserveAspectRatio" when figuring the image dimensions.
                Require width & height to be provided as parameters.

        Returns:
            A tuple of (width, height, `fpdf.drawing.GraphicsContext`), where width and
            height are the resolved width and height (they may be 0. If 0, the returned
            `fpdf.drawing.GraphicsContext` will be empty). The
            `fpdf.drawing.GraphicsContext` contains all of the paths that were
            converted from the SVG, scaled to the given viewport size.
        """

        if ignore_svg_top_attrs:
            vp_width = width
        elif isinstance(self.width, Percent):
            if not width:
                raise ValueError(
                    'SVG "width" is a percentage, hence a viewport width is required'
                )
            vp_width = self.width * width / 100
        else:
            vp_width = self.width or width

        if ignore_svg_top_attrs:
            vp_height = height
        elif isinstance(self.height, Percent):
            if not height:
                raise ValueError(
                    'SVG "height" is a percentage, hence a viewport height is required'
                )
            vp_height = self.height * height / 100
        else:
            vp_height = self.height or height

        if scale == 1:
            transform = Transform.identity()
        else:
            transform = Transform.scaling(1 / scale)

        if self.viewbox:
            vx, vy, vw, vh = self.viewbox

            if (vw == 0) or (vh == 0):
                return 0, 0, GraphicsContext()

            w_ratio = vp_width / vw
            h_ratio = vp_height / vh

            if not ignore_svg_top_attrs and self.preserve_ar and (w_ratio != h_ratio):
                w_ratio = h_ratio = min(w_ratio, h_ratio)

            transform = (
                transform
                @ Transform.translation(x=-vx, y=-vy)
                @ Transform.scaling(x=w_ratio, y=h_ratio)
            )

            if align_viewbox:
                transform = transform @ Transform.translation(
                    x=vp_width / 2 - (vw / 2) * w_ratio,
                    y=vp_height / 2 - (vh / 2) * h_ratio,
                )

        self.base_group.transform = transform

        return vp_width / scale, vp_height / scale, self.base_group

    def draw_to_page(self, pdf, x=None, y=None, debug_stream=None):
        """
        Directly draw the converted SVG to the given PDF's current page.

        The page viewport is used for sizing the SVG.

        Args:
            pdf (fpdf.fpdf.FPDF): the document to which the converted SVG is rendered.
            x (Number): abscissa of the converted SVG's top-left corner.
            y (Number): ordinate of the converted SVG's top-left corner.
            debug_stream (io.TextIO): the stream to which rendering debug info will be
                written.
        """
        self.image_cache = pdf.image_cache  # Needed to render images
        _, _, path = self.transform_to_page_viewport(pdf)

        old_x, old_y = pdf.x, pdf.y
        try:
            if x is not None and y is not None:
                pdf.set_xy(0, 0)
                path.transform = path.transform @ Transform.translation(x, y)

            pdf.draw_path(path, debug_stream)

        finally:
            pdf.set_xy(old_x, old_y)

    # defs paths are not drawn immediately but are added to xrefs and can be referenced
    # later to be drawn.
    @force_nodocument
    def handle_defs(self, defs):
        """Produce lookups for groups and paths inside the <defs> tag"""
        for child in defs:
            if child.tag in xmlns_lookup("svg", "g"):
                self.build_group(child)
            elif child.tag in xmlns_lookup("svg", "a"):
                # <a> tags aren't supported but we need to recurse into them to
                # render nested elements.
                LOGGER.warning(
                    "Ignoring unsupported SVG tag: <a> (contributions are welcome to add support for it)",
                )
                self.build_group(child)
            elif child.tag in xmlns_lookup("svg", "path"):
                self.build_path(child)
            elif child.tag in xmlns_lookup("svg", "image"):
                self.build_image(child)
            elif child.tag in shape_tags:
                self.build_shape(child)
            elif child.tag in xmlns_lookup("svg", "clipPath"):
                try:
                    clip_id = child.attrib["id"]
                except KeyError:
                    clip_id = None
                for child_ in child:
                    self.build_clipping_path(child_, clip_id)
            elif child.tag in xmlns_lookup("svg", "style"):
                # Styles handled globally during parsing
                continue
            else:
                LOGGER.warning(
                    "Ignoring unsupported SVG tag: <%s> (contributions are welcome to add support for it)",
                    without_ns(child.tag),
                )

    # this assumes xrefs only reference already-defined ids.
    # I don't know if this is required by the SVG spec.
    @force_nodocument
    def build_xref(self, xref):
        """Resolve a cross-reference to an already-seen SVG element by ID."""
        style_map = self._style_map_for(xref)
        pdf_group = GraphicsContext()
        apply_styles(pdf_group, xref, style_map)

        for candidate in xmlns_lookup("xlink", "href", "id"):
            try:
                ref = xref.attrib[candidate]
                break
            except KeyError:
                pass
        else:
            raise ValueError(f"use {xref} doesn't contain known xref attribute")

        try:
            pdf_group.add_item(self.cross_references[ref])
        except KeyError:
            raise ValueError(
                f"use {xref} references nonexistent ref id {ref}"
            ) from None

        if "x" in xref.attrib or "y" in xref.attrib:
            # Quoting the SVG spec - 5.6.2. Layout of re-used graphics:
            # > The x and y properties define an additional transformation translate(x,y)
            x, y = float(xref.attrib.get("x", 0)), float(xref.attrib.get("y", 0))
            pdf_group.transform = Transform.translation(x=x, y=y)
        # Note that we currently do not support "width" & "height" in <use>

        return pdf_group

    @force_nodocument
    def build_group(self, group, pdf_group=None, inherited_style=None):
        """Handle nested items within a group <g> tag."""
        local_style = self._style_map_for(group)
        merged_style = dict(inherited_style or {})
        merged_style.update(local_style)
        if pdf_group is None:
            pdf_group = GraphicsContext()
        apply_styles(pdf_group, group, merged_style)

        # handle defs before anything else
        for child in [
            child for child in group if child.tag in xmlns_lookup("svg", "defs")
        ]:
            self.handle_defs(child)

        for child in group:
            if child.tag in xmlns_lookup("svg", "defs"):
                self.handle_defs(child)
            elif child.tag in xmlns_lookup("svg", "style"):
                # Stylesheets already parsed globally.
                continue
            elif child.tag in xmlns_lookup("svg", "g"):
                pdf_group.add_item(self.build_group(child, None, merged_style), False)
            elif child.tag in xmlns_lookup("svg", "a"):
                # <a> tags aren't supported but we need to recurse into them to
                # render nested elements.
                LOGGER.warning(
                    "Ignoring unsupported SVG tag: <a> (contributions are welcome to add support for it)",
                )
                pdf_group.add_item(self.build_group(child, None, merged_style), False)
            elif child.tag in xmlns_lookup("svg", "path"):
                pdf_group.add_item(self.build_path(child), False)
            elif child.tag in shape_tags:
                pdf_group.add_item(self.build_shape(child), False)
            elif child.tag in xmlns_lookup("svg", "use"):
                pdf_group.add_item(self.build_xref(child), False)
            elif child.tag in xmlns_lookup("svg", "image"):
                pdf_group.add_item(self.build_image(child), False)
            elif child.tag in xmlns_lookup("svg", "text"):
                pdf_group.add_item(self.build_text(child, merged_style), False)
            else:
                LOGGER.warning(
                    "Ignoring unsupported SVG tag: <%s> (contributions are welcome to add support for it)",
                    without_ns(child.tag),
                )

        self.update_xref(group.attrib.get("id"), pdf_group)

        return pdf_group

    @force_nodocument
    def build_path(self, path):
        """Convert an SVG <path> tag into a PDF path object."""
        style_map = self._style_map_for(path)
        pdf_path = PaintedPath()
        apply_styles(pdf_path, path, style_map)
        self.apply_clipping_path(pdf_path, path, style_map)
        svg_path = path.attrib.get("d")
        if svg_path is not None:
            svg_path_converter(pdf_path, svg_path)
        self.update_xref(path.attrib.get("id"), pdf_path)
        return pdf_path

    @force_nodocument
    def build_shape(self, shape):
        """Convert an SVG shape tag into a PDF path object. Necessary to make xref (because ShapeBuilder doesn't have access to this object.)"""
        style_map = self._style_map_for(shape)
        shape_builder = getattr(ShapeBuilder, shape_tags[shape.tag])
        shape_path = shape_builder(shape)
        apply_styles(shape_path, shape, style_map)
        self.apply_clipping_path(shape_path, shape, style_map)
        self.update_xref(shape.attrib.get("id"), shape_path)
        return shape_path

    @force_nodocument
    def build_clipping_path(self, shape, clip_id):
        if shape.tag in shape_tags:
            style_map = self._style_map_for(shape)
            shape_builder = getattr(ShapeBuilder, shape_tags[shape.tag])
            clipping_path_shape = shape_builder(shape, True)
            apply_styles(clipping_path_shape, shape, style_map)
        elif shape.tag in xmlns_lookup("svg", "path"):
            style_map = self._style_map_for(shape)
            clipping_path_shape = PaintedPath()
            apply_styles(clipping_path_shape, shape, style_map)
            clipping_path_shape.paint_rule = PathPaintRule.DONT_PAINT
            svg_path = shape.attrib.get("d")
            if svg_path is not None:
                svg_path_converter(clipping_path_shape, svg_path)
        else:
            LOGGER.warning(
                "Ignoring unsupported <clipPath> child tag: <%s> (contributions are welcome to add support for it)",
                without_ns(shape.tag),
            )
            return
        self.update_xref(clip_id, clipping_path_shape)

    @force_nodocument
    def apply_clipping_path(self, stylable, svg_element, style_map=None):
        clip_value = None
        if style_map and "clip-path" in style_map:
            clip_value = style_map["clip-path"]
        if clip_value is None:
            clip_value = svg_element.attrib.get("clip-path")
        if clip_value:
            clipping_path_id = re.search(r"url\((\#\w+)\)", clip_value)
            stylable.clipping_path = self.cross_references[clipping_path_id[1]]

    @force_nodocument
    def build_image(self, image):
        href = None
        for key in xmlns_lookup("xlink", "href"):
            if key in image.attrib:
                href = image.attrib[key]
                break
        if not href:
            raise ValueError("<image> is missing a href attribute")
        width = float(image.attrib.get("width", 0))
        height = float(image.attrib.get("height", 0))
        if "preserveAspectRatio" in image.attrib:
            LOGGER.warning(
                '"preserveAspectRatio" defined on <image> is currently not supported (contributions are welcome to add support for it)'
            )
        if "style" in image.attrib:
            LOGGER.warning(
                '"style" defined on <image> is currently not supported (contributions are welcome to add support for it)'
            )
        if "transform" in image.attrib:
            LOGGER.warning(
                '"transform" defined on <image> is currently not supported (contributions are welcome to add support for it)'
            )
        # Note: at this moment, self.image_cache is not set yet:
        svg_image = SVGImage(
            href=href,
            x=float(image.attrib.get("x", "0")),
            y=float(image.attrib.get("y", "0")),
            width=width,
            height=height,
            svg_obj=self,
        )
        self.update_xref(image.attrib.get("id"), svg_image)
        return svg_image

    @force_nodocument
    def build_text(self, text_tag, inherited_style=None):
        """
        Convert <text> (and simple <tspan>) into a PaintedPath with Text runs.
        - Uses Text baseline at (x,y)
        - Honors x/y and dx/dy on <text> and direct child <tspan>
        - Flattens nested tspans; advanced per-character positioning is not implemented
        """
        local_style = self._style_map_for(text_tag)
        effective_style = dict(inherited_style or {})
        effective_style.update(local_style)
        path = PaintedPath()
        apply_styles(path, text_tag, local_style)
        self.apply_clipping_path(path, text_tag, effective_style)

        preserve_parent = _preserve_ws(effective_style, text_tag)

        base_family, base_emph, base_size, base_anchor = _parse_font_attrs(
            text_tag, effective_style
        )
        if base_family is None:
            base_family = "sans-serif"
        default_font_size = (
            base_size if base_size is not None else resolve_length("16px")
        )
        base_x, base_y, base_dx, base_dy = _parse_xy_delta(
            text_tag, effective_style, font_size=default_font_size
        )
        anchor_x = base_x + base_dx
        anchor_y = base_y + base_dy

        text_runs: list[TextRun] = []
        pending_dx = 0.0
        pending_dy = 0.0

        def _style_for_run(tag, style_map_for_tag):
            if tag is None or style_map_for_tag is None:
                return None
            context = GraphicsContext()
            apply_styles(context, tag, style_map_for_tag)
            context.style.auto_close = GraphicsStyle.INHERIT
            overrides = any(
                getattr(context.style, prop) is not GraphicsStyle.INHERIT
                for prop in GraphicsStyle.MERGE_PROPERTIES
            )
            if not overrides:
                return None
            return deepcopy(context.style)

        def _add_run(
            raw_text: str,
            family: Optional[str],
            emphasis: Optional[str],
            size: Optional[float],
            preserve: bool,
            dx_extra: float = 0.0,
            dy_extra: float = 0.0,
            abs_x: Optional[float] = None,
            abs_y: Optional[float] = None,
            style_tag=None,
            style_map_for_tag=None,
        ):
            nonlocal pending_dx, pending_dy
            raw = raw_text or ""
            collapsed = _collapse_ws(raw, preserve=preserve)
            if preserve:
                content = collapsed
            else:
                trimmed = collapsed.strip()
                if trimmed:
                    content = trimmed
                    if raw[:1].isspace():
                        content = " " + content
                    if raw[-1:].isspace():
                        content = content + " "
                else:
                    if (raw[:1].isspace() or raw[-1:].isspace()) and text_runs:
                        content = " "
                    else:
                        content = ""
            if not content:
                pending_dx += dx_extra
                pending_dy += dy_extra
                return

            run_size = size if size is not None else default_font_size
            run_family = family or base_family or "sans-serif"
            run_emphasis = (emphasis if emphasis is not None else base_emph) or ""
            run_dx = pending_dx + dx_extra
            run_dy = pending_dy + dy_extra
            pending_dx = 0.0
            pending_dy = 0.0
            run_style = _style_for_run(style_tag, style_map_for_tag)

            text_runs.append(
                TextRun(
                    text=content,
                    family=run_family,
                    emphasis=run_emphasis,
                    size=run_size,
                    dx=run_dx,
                    dy=run_dy,
                    abs_x=abs_x,
                    abs_y=abs_y,
                    run_style=run_style,
                )
            )

        # Leading text (before child <tspan>)
        _add_run(
            text_tag.text or "",
            base_family,
            base_emph,
            base_size,
            preserve=preserve_parent,
            style_tag=None,
            style_map_for_tag=None,
        )

        for child in text_tag:
            if child.tag in xmlns_lookup("svg", "tspan"):
                child_local_style = self._style_map_for(child)
                child_effective_style = dict(effective_style)
                child_effective_style.update(child_local_style)
                fam, emph, size, _anchor = _parse_font_attrs(
                    child, child_effective_style
                )
                run_font_size = size if size is not None else default_font_size
                x, y, dx, dy = _parse_xy_delta(
                    child, child_effective_style, font_size=run_font_size
                )

                child_preserve = _preserve_ws(child_effective_style, child)
                raw_itertext = "".join(child.itertext())
                tail_text = child.tail or ""
                if tail_text and raw_itertext.endswith(tail_text):
                    run_text = raw_itertext[: -len(tail_text)]
                else:
                    run_text = raw_itertext
                abs_x = None
                abs_y = None
                if "x" in child.attrib or (
                    child_local_style is not None and "x" in child_local_style
                ):
                    abs_x = x
                if "y" in child.attrib or (
                    child_local_style is not None and "y" in child_local_style
                ):
                    abs_y = y

                _add_run(
                    run_text,
                    fam,
                    emph,
                    size,
                    preserve=child_preserve,
                    dx_extra=dx,
                    dy_extra=dy,
                    abs_x=abs_x,
                    abs_y=abs_y,
                    style_tag=child,
                    style_map_for_tag=child_local_style,
                )

                # Text between tspans inherits parent style
                _add_run(
                    child.tail or "",
                    base_family,
                    base_emph,
                    base_size,
                    preserve=preserve_parent,
                    style_tag=None,
                    style_map_for_tag=None,
                )
            else:
                # other child tags are ignored (already logged elsewhere)
                pass

        if text_runs:
            path.add_path_element(
                Text(
                    x=anchor_x,
                    y=anchor_y,
                    text_runs=tuple(text_runs),
                    text_anchor=base_anchor,
                ),
                _copy=False,
            )

        self.update_xref(text_tag.attrib.get("id"), path)
        return path


class SVGImage(NamedTuple):
    href: str
    x: Number
    y: Number
    width: Number
    height: Number
    svg_obj: SVGObject

    def __deepcopy__(self, _memo):
        # Defining this method is required to avoid the .svg_obj reference to be cloned:
        return SVGImage(
            href=self.href,
            x=self.x,
            y=self.y,
            width=self.width,
            height=self.height,
            svg_obj=self.svg_obj,
        )

    @force_nodocument
    def render(self, _resource_registry, _style, last_item, initial_point):
        image_cache = self.svg_obj and self.svg_obj.image_cache
        if not image_cache:
            raise AssertionError(
                "fpdf2 bug - Cannot render a raster image without a SVGObject.image_cache"
            )

        # We lazy-import this function to circumvent a circular import problem:
        # pylint: disable=cyclic-import,import-outside-toplevel
        from .image_parsing import preload_image

        _, _, info = preload_image(image_cache, self.href)
        if isinstance(info, VectorImageInfo):
            LOGGER.warning(
                "Inserting .svg vector graphics in <image> tags is currently not supported (contributions are welcome to add support for it)"
            )
            return "", last_item, initial_point
        w, h = info.size_in_document_units(self.width, self.height)
        stream_content = stream_content_for_raster_image(
            info=info,
            x=self.x,
            y=self.y,
            w=w,
            h=h,
            keep_aspect_ratio=True,
        )
        return stream_content, last_item, initial_point

    @force_nodocument
    def render_debug(
        self, resource_registry, style, last_item, initial_point, debug_stream, _pfx
    ):
        stream_content, last_item, initial_point = self.render(
            resource_registry, style, last_item, initial_point
        )
        debug_stream.write(f"{self.href} rendered as: {stream_content}\n")
        return stream_content, last_item, initial_point
