import math
import re
from typing import NamedTuple
import xml.etree.ElementTree

from . import drawing, html

# https://www.w3.org/TR/SVG/Overview.html

_handy_namespaces = {
    "svg": "http://www.w3.org/2000/svg",
    "xlink": "http://www.w3.org/1999/xlink",
}

alphabet = re.compile(r"([a-zA-Z])")
number_split = re.compile(r"[ ,]+")
transform_getter = re.compile(
    r"(matrix|rotate|scale|scaleX|scaleY|skew|skewX|skewY|translate|translateX|translateY)"
    r"\(((?:\s*(?:[-+]?[\d\.]+,?)+\s*)+)\)"
)


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
def resolve_length(length_str, default_unit="pt"):
    value, unit = unit_splitter.match(length_str).groups()
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


def resolve_angle(angle_str, default_unit="deg"):
    """Convert an angle value to our canonical unit, radians"""
    value, unit = unit_splitter.match(angle_str).groups()
    if not unit:
        unit = default_unit

    try:
        return float(value) * angle_units[unit]
    except KeyError:
        raise ValueError(f"angle {angle_str} has unknown unit {unit}") from None


def xmlns(space, name):
    try:
        space = _handy_namespaces[space]
    except KeyError:
        # probably we should not eat this KeyError actually
        space = ""

    return f"{{{space}}}{name}"


def xmlns_lookup(space, *names):
    result = {}
    for name in names:
        result[xmlns(space, name)] = name
        result[name] = name

    return result


shape_tags = xmlns_lookup(
    "svg", "rect", "circle", "ellipse", "line", "polyline", "polygon"
)


def svgcolor(colorstr):
    try:
        colorstr = html.COLOR_DICT[colorstr]
    except KeyError:
        pass

    if colorstr.startswith("#"):
        return drawing.color_from_hex_string(colorstr)

    raise ValueError(f"unsupported color specification {colorstr}")


def optional(value, converter=lambda noop: noop):
    if value == "none":
        return None
    if value == "auto":
        return drawing.GraphicsStyle.INHERIT

    return converter(value)


cross_references = {}
svg_attr_map = {
    "fill": lambda colorstr: ("fill_color", optional(colorstr, svgcolor)),
    "stroke-width": lambda valuestr: ("stroke_width", optional(valuestr, float)),
    "stroke": lambda colorstr: ("stroke_color", optional(colorstr, svgcolor)),
    "stroke-dasharray": lambda dasharray: (
        "stroke_dash_pattern",
        optional(
            dasharray, lambda da: [float(item) for item in number_split.split(da)]
        ),
    ),
    "stroke-linecap": lambda capstr: ("stroke_cap_style", optional(capstr)),
    "stroke-linejoin": lambda joinstr: ("stroke_join_style", optional(joinstr)),
    "stroke-miterlimit": lambda limstr: ("stroke_miter_limit", optional(limstr)),
    "stroke-opacity": lambda stropstr: ("stroke_opacity", optional(stropstr)),
    "fill-opacity": lambda filopstr: ("fill_opacity", optional(filopstr)),
}


# defs paths are not drawn immediately but are added to xrefs and can be referenced
# later to be drawn.
def handle_defs(defs):
    for child in defs:
        if child.tag in xmlns_lookup("svg", "g"):
            build_group(child)
        if child.tag in xmlns_lookup("svg", "path"):
            build_path(child)


def apply_styles(stylable, svg_element):
    stylable.style.auto_close = False

    for svg_attr, converter in svg_attr_map.items():
        try:
            attr, value = converter(svg_element.attrib[svg_attr])
        except KeyError:
            pass
        else:
            setattr(stylable.style, attr, value)

    # handle this separately for now
    try:
        opacity = float(svg_element.attrib["opacity"])
    except KeyError:
        pass
    else:
        stylable.style.fill_opacity = opacity
        stylable.style.stroke_opacity = opacity

    try:
        tfstr = svg_element.attrib["transform"]
    except KeyError:
        pass
    else:
        stylable.transform = convert_transforms(tfstr)


def build_group(group, pdf_group=None):
    if pdf_group is None:
        pdf_group = drawing.GraphicsContext()
        apply_styles(pdf_group, group)

    for child in group:
        if child.tag in xmlns_lookup("svg", "defs"):
            handle_defs(child)
        if child.tag in xmlns_lookup("svg", "g"):
            pdf_group.add_item(build_group(child))
        if child.tag in xmlns_lookup("svg", "path"):
            pdf_group.add_item(build_path(child))
        elif child.tag in shape_tags:
            pdf_group.add_item(getattr(ShapeBuilder, shape_tags[child.tag])(child))
        if child.tag in xmlns_lookup("svg", "use"):
            pdf_group.add_item(build_xref(child))

    try:
        cross_references["#" + group.attrib["id"]] = pdf_group
    except KeyError:
        pass

    return pdf_group


def build_path(path):
    pdf_path = drawing.PaintedPath()
    apply_styles(pdf_path, path)

    svg_path_converter(pdf_path, path.attrib["d"])

    try:
        cross_references["#" + path.attrib["id"]] = pdf_path
    except KeyError:
        pass

    return pdf_path


class ShapeBuilder:
    @staticmethod
    def new_path(tag):
        path = drawing.PaintedPath()
        apply_styles(path, tag)

        return path

    @classmethod
    def rect(cls, tag):
        # svg rect is wound clockwise
        x = float(tag.attrib.get("x", 0))
        y = float(tag.attrib.get("y", 0))
        width = float(tag.attrib.get("width", 0))
        height = float(tag.attrib.get("height", 0))
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
            rx = ry = float(rx)

        if (width < 0) or (height < 0) or (rx < 0) or (ry < 0):
            raise ValueError(f"bad rect {tag}")

        if (width == 0) or (height == 0):
            return drawing.PaintedPath()

        if rx > (width / 2):
            rx = width / 2
        if ry > (height / 2):
            ry = height / 2

        path = cls.new_path(tag)

        path.rectangle(x, y, width, height, rx, ry)
        return path

    @classmethod
    def circle(cls, tag):
        cx = float(tag.attrib.get("cx", 0))
        cy = float(tag.attrib.get("cy", 0))
        r = float(tag.attrib["r"])

        path = cls.new_path(tag)

        path.circle(cx, cy, r)
        return path

    @classmethod
    def ellipse(cls, tag):
        cx = float(tag.attrib.get("cx", 0))
        cy = float(tag.attrib.get("cy", 0))

        rx = tag.attrib.get("rx", "auto")
        ry = tag.attrib.get("ry", "auto")

        path = cls.new_path(tag)

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
        points = tag.attrib["points"]

        path = cls.new_path(tag)

        points = "M" + points
        svg_path_converter(path, points)

        return path

    @classmethod
    def polygon(cls, tag):
        points = tag.attrib["points"]

        path = cls.new_path(tag)

        points = "M" + points + "Z"
        svg_path_converter(path, points)

        return path


# this assumes xrefs only reference already-defined ids. I don't know if this is
# required by the SVG spec.
def build_xref(xref):
    pdf_group = drawing.GraphicsContext()
    apply_styles(pdf_group, xref)

    for candidate in xmlns_lookup("xlink", "href"):
        try:
            ref = xref.attrib[candidate]
            break
        except KeyError:
            pass
    else:
        raise ValueError(f"use {xref} doesn't contain known xref attribute")

    try:
        pdf_group.add_item(cross_references[ref])
    except KeyError:
        raise ValueError(f"use {xref} references nonexistent ref id {ref}") from None

    return pdf_group


def convert_transforms(tfstr):
    """
    Convert SVG/CSS transform functions into our own transformation mapping
    """

    # https://drafts.csswg.org/css-transforms/#two-d-transform-functions
    parsed = transform_getter.findall(tfstr)

    transform = drawing.Transform.identity()
    for tf_type, args in parsed:
        if tf_type == "matrix":
            a, b, c, d, e, f = tuple(float(n) for n in number_split.split(args))
            transform = drawing.Transform(a, b, c, d, e, f) @ transform

        elif tf_type == "rotate":
            theta = resolve_angle(args)
            transform = drawing.Transform.rotation(theta=theta) @ transform

        elif tf_type == "scale":
            # if sy is not provided, it takes a value equal to sx
            args = number_split.split(args)
            if len(args) == 2:
                sx = float(args[0])
                sy = float(args[1])
            elif len(args) == 1:
                sx = sy = float(args[0])
            else:
                raise ValueError(f"bad scale transform {tfstr}")

            transform = drawing.Transform.scaling(x=sx, y=sy) @ transform

        elif tf_type == "scaleX":
            transform = drawing.Transform.scaling(x=float(args), y=1) @ transform

        elif tf_type == "scaleY":
            transform = drawing.Transform.scaling(x=1, y=float(args)) @ transform

        elif tf_type == "skew":
            # if sy is not provided, it takes a value equal to 0
            args = number_split.split(args)
            if len(args) == 2:
                sx = resolve_angle(args[0])
                sy = resolve_angle(args[1])
            elif len(args) == 1:
                sx = resolve_angle(args[0])
                sy = 0
            else:
                raise ValueError(f"bad skew transform {tfstr}")

            transform = (
                drawing.Transform.shearing(x=math.tan(sx), y=math.tan(sy)) @ transform
            )

        elif tf_type == "skewX":
            transform = (
                drawing.Transform.shearing(x=math.tan(resolve_angle(args)), y=0)
                @ transform
            )

        elif tf_type == "skewY":
            transform = (
                drawing.Transform.shearing(x=0, y=math.tan(resolve_angle(args)))
                @ transform
            )

        elif tf_type == "translate":
            # if y is not provided, it takes a value equal to 0
            args = number_split.split(args)
            if len(args) == 2:
                x = resolve_length(args[0])
                y = resolve_length(args[1])
            elif len(args) == 1:
                x = resolve_length(args[0])
                y = 0
            else:
                raise ValueError(f"bad translation transform {tfstr}")

            transform = drawing.Transform.translation(x=x, y=y) @ transform

        elif tf_type == "translateX":
            transform = (
                drawing.Transform.translation(x=resolve_length(args), y=0) @ transform
            )

        elif tf_type == "translateY":
            transform = (
                drawing.Transform.translation(x=0, y=resolve_length(args)) @ transform
            )

    return transform


class SVGSmoothCubicCurve(NamedTuple):
    c2: drawing.Point
    end: drawing.Point

    @classmethod
    def from_path_points(cls, path, c2x, c2y, ex, ey):
        return path.add_path_element(
            cls(c2=drawing.Point(x=c2x, y=c2y), end=drawing.Point(x=ex, y=ey))
        )

    def render(self, path_gsds, style, last_item):
        # technically, it would also be possible to chain on from a quadratic Bézier,
        # since we can convert those to cubic curves and then retrieve the appropriate
        # control point. However, the SVG specification states in
        # https://www.w3.org/TR/SVG/paths.html#PathDataCubicBezierCommands
        # "if the previous command was not an C, c, S or s, assume the first control
        # point is coincident with the current point."
        if isinstance(last_item, drawing.BezierCurve):
            c1 = (2 * last_item.end) - last_item.c2
        else:
            c1 = last_item.end_point

        return drawing.BezierCurve(c1, self.c2, self.end).render(
            path_gsds, style, last_item
        )

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        # pylint: disable=unused-argument
        rendered, resolved = self.render(path_gsds, style, last_item)
        debug_stream.write(f"{self} resolved to {resolved}\n")

        return rendered, resolved


class SVGRelativeSmoothCubicCurve(NamedTuple):
    c2: drawing.Point
    end: drawing.Point

    @classmethod
    def from_path_points(cls, path, c2x, c2y, ex, ey):
        return path.add_path_element(
            cls(c2=drawing.Point(x=c2x, y=c2y), end=drawing.Point(x=ex, y=ey))
        )

    def render(self, path_gsds, style, last_item):
        last_point = last_item.end_point

        if isinstance(last_item, drawing.BezierCurve):
            c1 = (2 * last_item.end) - last_item.c2
        else:
            c1 = last_point

        c2 = last_point + self.c2
        end = last_point + self.end

        return drawing.BezierCurve(c1, c2, end).render(path_gsds, style, last_item)

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        # pylint: disable=unused-argument
        rendered, resolved = self.render(path_gsds, style, last_item)
        debug_stream.write(f"{self} resolved to {resolved}\n")

        return rendered, resolved


class SVGSmoothQuadraticCurve(NamedTuple):
    end: drawing.Point

    @classmethod
    def from_path_points(cls, path, ex, ey):
        return path.add_path_element(cls(end=drawing.Point(x=ex, y=ey)))

    def render(self, path_gsds, style, last_item):
        if isinstance(last_item, drawing.QuadraticBezierCurve):
            ctrl = (2 * last_item.end) - last_item.ctrl
        else:
            ctrl = last_item.end_point

        return drawing.QuadraticBezierCurve(ctrl, self.end).render(
            path_gsds, style, last_item
        )

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        # pylint: disable=unused-argument
        rendered, resolved = self.render(path_gsds, style, last_item)
        debug_stream.write(f"{self} resolved to {resolved}\n")

        return rendered, resolved


class SVGRelativeSmoothQuadraticCurve(NamedTuple):
    end: drawing.Point

    @classmethod
    def from_path_points(cls, path, ex, ey):
        return path.add_path_element(cls(end=drawing.Point(x=ex, y=ey)))

    def render(self, path_gsds, style, last_item):
        last_point = last_item.end_point

        if isinstance(last_item, drawing.QuadraticBezierCurve):
            ctrl = (2 * last_item.end) - last_item.ctrl
        else:
            ctrl = last_point

        end = last_point + self.end

        return drawing.QuadraticBezierCurve(ctrl, end).render(
            path_gsds, style, last_item
        )

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        # pylint: disable=unused-argument
        rendered, resolved = self.render(path_gsds, style, last_item)
        debug_stream.write(f"{self} resolved to {resolved}\n")

        return rendered, resolved


path_directive_mapping = {
    "m": (2, drawing.PaintedPath.move_relative),
    "M": (2, drawing.PaintedPath.move_to),
    "z": (0, drawing.PaintedPath.close),
    "Z": (0, drawing.PaintedPath.close),
    "l": (2, drawing.PaintedPath.line_relative),
    "L": (2, drawing.PaintedPath.line_to),
    "h": (1, drawing.PaintedPath.horizontal_line_relative),
    "H": (1, drawing.PaintedPath.horizontal_line_to),
    "v": (1, drawing.PaintedPath.vertical_line_relative),
    "V": (1, drawing.PaintedPath.vertical_line_to),
    "c": (6, drawing.PaintedPath.curve_relative),
    "C": (6, drawing.PaintedPath.curve_to),
    "s": (4, SVGRelativeSmoothCubicCurve.from_path_points),
    "S": (4, SVGSmoothCubicCurve.from_path_points),
    "q": (4, drawing.PaintedPath.quadratic_bezier_relative),
    "Q": (4, drawing.PaintedPath.quadratic_bezier_to),
    "t": (2, SVGRelativeSmoothQuadraticCurve.from_path_points),
    "T": (2, SVGSmoothQuadraticCurve.from_path_points),
    "a": (7, drawing.PaintedPath.arc_relative),
    "A": (7, drawing.PaintedPath.arc_to),
}

path_directives = {*path_directive_mapping}


def _read_n_numbers(path_str, n):
    path_str = path_str.lstrip()
    *numbers, leftover = number_split.split(path_str, maxsplit=n)
    if len(numbers) == n - 1:
        numbers.append(leftover)
        leftover = ""
    return tuple(float(num) for num in numbers), leftover.lstrip()


def svg_path_converter(pdf_path, svg_path):
    # - can be used as a numeric separator as well, irritatingly (e.g. "3-4" should be
    # parsed like "3, -4"), so we insert spaces before - to make sure these get split
    # apart correctly.

    svg_path = alphabet.sub(r" \1 ", svg_path).replace("-", " -").strip()
    while svg_path:
        read_idx = 0
        directive = svg_path[read_idx]

        if directive in path_directives:
            read_idx = 1
            read_count, last_directive = path_directive_mapping[directive]
            last_directive_name = directive

        # we use read_idx as an indicator of whether the path directive was implicit or
        # not. SVG allows for purely implicit line directives to follow a move
        # directive, i.e. `M 0,0 1,1` is the same as `M 0,0 L 1,1`. Similarly,
        # `m 0,0 1,1` is the same as `m 0,0 l 1,1` (see:
        # https://www.w3.org/TR/SVG/paths.html#PathDataMovetoCommands)
        if last_directive_name in {"m", "M"} and read_idx == 0:
            read_count, last_directive = path_directive_mapping[
                {"m": "l", "M": "L"}[last_directive_name]
            ]

        numbers, svg_path = _read_n_numbers(svg_path[read_idx:], read_count)

        last_directive(pdf_path, *numbers)


class SVGObject:
    @classmethod
    def from_file(cls, filename, *args, **kwargs):
        with open(filename, "r") as svgfile:
            return cls(svgfile.read(), *args, **kwargs)

    def __init__(self, svg_text):
        svg_tree = xml.etree.ElementTree.fromstring(svg_text)

        if svg_tree.tag not in xmlns_lookup("svg", "svg"):
            raise ValueError(f"root tag must be svg, not {svg_tree.tag}")

        self.extract_shape_info(svg_tree)
        self.convert_graphics(svg_tree)

    def extract_shape_info(self, root_tag):
        width = root_tag.get("width")
        height = root_tag.get("height")
        viewbox = root_tag.get("viewBox")
        # we don't fully support this, just check for its existence
        preserve_ar = root_tag.get("preserveAspectRatio", True)
        if preserve_ar == "none":
            self.preserve_ar = None
        else:
            self.preserve_ar = True

        if width is not None:
            width.strip()
            if width.endswith("%"):
                width = Percent(width[:-1])
            else:
                width = resolve_length(width)
        else:
            width = Percent(100)

        self.width = width

        if height is not None:
            height.strip()
            if height.endswith("%"):
                height = Percent(height[:-1])
            else:
                height = resolve_length(height)
        else:
            height = Percent(100)

        self.height = height

        if viewbox is not None:
            viewbox.strip()
            vx, vy, vw, vh = [float(num) for num in number_split.split(viewbox)]
            if (vw < 0) or (vh < 0):
                raise ValueError(f"invalid negative width/height in viewbox {viewbox}")

            self.viewbox = [vx, vy, vw, vh]
        else:
            self.viewbox = None

    def convert_graphics(self, root_tag):
        base_group = drawing.GraphicsContext()
        base_group.style.stroke_width = None
        base_group.style.auto_close = False

        build_group(root_tag, base_group)

        self.base_group = base_group

    def transform_to_page_viewport(self, pdf):
        return self.transform_to_rect_viewport(pdf.k, pdf.w, pdf.h)

    def transform_to_rect_viewport(self, scale, width, height):
        if isinstance(self.width, Percent):
            vp_width = self.width * width / 100
        else:
            vp_width = self.width

        if isinstance(self.height, Percent):
            vp_height = self.height * height / 100
        else:
            vp_height = self.height

        if scale != 1:
            transform = drawing.Transform.scaling(1 / scale)
        else:
            transform = drawing.Transform.identity()

        if self.viewbox:
            vx, vy, vw, vh = self.viewbox

            if (vw == 0) or (vh == 0):
                return 0, 0, drawing.GraphicsContext()

            w_ratio = vp_width / self.viewbox[2]
            h_ratio = vp_height / self.viewbox[3]

            if self.preserve_ar and (w_ratio != h_ratio):
                w_ratio = h_ratio = min(w_ratio, h_ratio)

            transform = (
                transform
                @ drawing.Transform.scaling(x=w_ratio, y=h_ratio)
                @ drawing.Transform.translation(x=-vx, y=-vy)
            )

        self.base_group.transform = transform

        return vp_width / scale, vp_height / scale, self.base_group

    def draw_to_page(self, pdf, x=None, y=None, debug_stream=None):
        _, _, path = self.transform_to_page_viewport(pdf)

        old_x, old_y = pdf.x, pdf.y
        try:
            if x is not None and y is not None:
                pdf.set_xy(0, 0)
                path.transform = path.transform @ drawing.Transform.translation(x, y)

            pdf.draw_path(path, debug_stream)

        finally:
            pdf.set_xy(old_x, old_y)
