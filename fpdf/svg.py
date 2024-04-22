"""
Utilities to parse SVG graphics into fpdf.drawing objects.

The contents of this module are internal to fpdf2, and not part of the public API.
They may change at any time without prior warning or any deprecation period,
in non-backward-compatible ways.
"""

import logging, math, re, warnings
from numbers import Number
from typing import NamedTuple

from fontTools.svgLib.path import parse_path
from fontTools.pens.basePen import BasePen

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
from .drawing import (
    color_from_hex_string,
    color_from_rgb_string,
    GraphicsContext,
    GraphicsStyle,
    PaintedPath,
    ClippingPath,
    Transform,
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
    r"(matrix|rotate|scale|scaleX|scaleY|skew|skewX|skewY|translate|translateX|translateY)"
    r"\(((?:\s*(?:[-+]?[\d\.]+,?)+\s*)+)\)"
)


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
    if value == "inherit":
        return GraphicsStyle.INHERIT

    return converter(value)


@force_nodocument
def optional(value, converter=lambda noop: noop):
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
            dasharray, lambda da: [float(item) for item in NUMBER_SPLIT.split(da)]
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
def apply_styles(stylable, svg_element):
    """Apply the known styles from `svg_element` to the pdf path/group `stylable`."""
    html.parse_style(svg_element.attrib)

    stylable.style.auto_close = False

    for attr_name, converter in svg_attr_map.items():
        value = svg_element.attrib.get(attr_name)
        if value:
            setattr(stylable.style, *converter(value))

    # handle this separately for now
    opacity = svg_element.attrib.get("opacity")
    if opacity:
        opacity = float(opacity)
        stylable.style.fill_opacity = opacity
        stylable.style.stroke_opacity = opacity

    tfstr = svg_element.attrib.get("transform")
    if tfstr:
        stylable.transform = convert_transforms(tfstr)


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


class PathPen(BasePen):
    def __init__(self, pdf_path, *args, **kwargs):
        self.pdf_path = pdf_path
        self.last_was_line_to = False
        self.first_is_move = None
        super().__init__(*args, **kwargs)

    def _moveTo(self, pt):
        self.pdf_path.move_to(*pt)
        self.last_was_line_to = False
        if self.first_is_move is None:
            self.first_is_move = True

    def _lineTo(self, pt):
        self.pdf_path.line_to(*pt)
        self.last_was_line_to = True
        if self.first_is_move is None:
            self.first_is_move = False

    def _curveToOne(self, pt1, pt2, pt3):
        self.pdf_path.curve_to(
            x1=pt1[0], y1=pt1[1], x2=pt2[0], y2=pt2[1], x3=pt3[0], y3=pt3[1]
        )
        self.last_was_line_to = False
        if self.first_is_move is None:
            self.first_is_move = False

    def _qCurveToOne(self, pt1, pt2):
        self.pdf_path.quadratic_curve_to(x1=pt1[0], y1=pt1[1], x2=pt2[0], y2=pt2[1])
        self.last_was_line_to = False
        if self.first_is_move is None:
            self.first_is_move = False

    def arcTo(self, rx, ry, rotation, arc, sweep, end):
        self.pdf_path.arc_to(
            rx=rx,
            ry=ry,
            rotation=rotation,
            large_arc=arc,
            positive_sweep=sweep,
            x=end[0],
            y=end[1],
        )
        self.last_was_line_to = False
        if self.first_is_move is None:
            self.first_is_move = False

    def _closePath(self):
        # The fonttools parser inserts an unnecessary explicit line back to the start
        # point of the path before actually closing it. Let's get rid of that again.
        if self.last_was_line_to:
            self.pdf_path.remove_last_path_element()
        self.pdf_path.close()


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

        # disabling bandit rule as we use defusedxml:
        svg_tree = parse_xml_str(svg_text)  # nosec B314

        if svg_tree.tag not in xmlns_lookup("svg", "svg"):
            raise ValueError(f"root tag must be svg, not {svg_tree.tag}")

        self.extract_shape_info(svg_tree)
        self.convert_graphics(svg_tree)

    @force_nodocument
    def update_xref(self, key, referenced):
        if key:
            key = "#" + key if not key.startswith("#") else key
            self.cross_references[key] = referenced

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
            viewbox.strip()
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
            pdf (fpdf.FPDF): the pdf to use the page size of.
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
            pdf (fpdf.FPDF): the document to which the converted SVG is rendered.
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
        pdf_group = GraphicsContext()
        apply_styles(pdf_group, xref)

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
    def build_group(self, group, pdf_group=None):
        """Handle nested items within a group <g> tag."""
        if pdf_group is None:
            pdf_group = GraphicsContext()
            apply_styles(pdf_group, group)

        # handle defs before anything else
        for child in [
            child for child in group if child.tag in xmlns_lookup("svg", "defs")
        ]:
            self.handle_defs(child)

        for child in group:
            if child.tag in xmlns_lookup("svg", "defs"):
                self.handle_defs(child)
            elif child.tag in xmlns_lookup("svg", "g"):
                pdf_group.add_item(self.build_group(child))
            elif child.tag in xmlns_lookup("svg", "path"):
                pdf_group.add_item(self.build_path(child))
            elif child.tag in shape_tags:
                pdf_group.add_item(self.build_shape(child))
            elif child.tag in xmlns_lookup("svg", "use"):
                pdf_group.add_item(self.build_xref(child))
            elif child.tag in xmlns_lookup("svg", "image"):
                pdf_group.add_item(self.build_image(child))
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
        pdf_path = PaintedPath()
        apply_styles(pdf_path, path)
        self.apply_clipping_path(pdf_path, path)
        svg_path = path.attrib.get("d")
        if svg_path is not None:
            svg_path_converter(pdf_path, svg_path)
        self.update_xref(path.attrib.get("id"), pdf_path)
        return pdf_path

    @force_nodocument
    def build_shape(self, shape):
        """Convert an SVG shape tag into a PDF path object. Necessary to make xref (because ShapeBuilder doesn't have access to this object.)"""
        shape_builder = getattr(ShapeBuilder, shape_tags[shape.tag])
        shape_path = shape_builder(shape)
        self.apply_clipping_path(shape_path, shape)
        self.update_xref(shape.attrib.get("id"), shape_path)
        return shape_path

    @force_nodocument
    def build_clipping_path(self, shape, clip_id):
        if shape.tag in shape_tags:
            shape_builder = getattr(ShapeBuilder, shape_tags[shape.tag])
            clipping_path_shape = shape_builder(shape, True)
        elif shape.tag in xmlns_lookup("svg", "path"):
            clipping_path_shape = PaintedPath()
            apply_styles(clipping_path_shape, shape)
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
    def apply_clipping_path(self, stylable, svg_element):
        clipping_path = svg_element.attrib.get("clip-path")
        if clipping_path:
            clipping_path_id = re.search(r"url\((\#\w+)\)", clipping_path)
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
    def render(self, _gsd_registry, _style, last_item, initial_point):
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
        self, gsd_registry, style, last_item, initial_point, debug_stream, _pfx
    ):
        stream_content, last_item, initial_point = self.render(
            gsd_registry, style, last_item, initial_point
        )
        debug_stream.write(f"{self.href} rendered as: {stream_content}\n")
        return stream_content, last_item, initial_point
