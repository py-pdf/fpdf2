import functools
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


def handle_color(colorstr):
    if colorstr == "none":
        return None

    try:
        colorstr = html.COLOR_DICT[colorstr]
    except KeyError:
        pass

    if colorstr.startswith("#"):
        return drawing.color_from_hex_string(colorstr)

    raise ValueError(f"unsupported color specification {colorstr}")


cross_references = {}
svg_attr_map = {
    "fill": lambda colorstr: ("fill_color", handle_color(colorstr)),
    "stroke-width": lambda valuestr: ("stroke_width", float(valuestr)),
    "stroke": lambda colorstr: ("stroke_color", handle_color(colorstr)),
}

# defs paths are not drawn immediately but are added to xrefs and can be referenced
# later to be drawn.
def handle_defs(defs):
    for child in defs:
        if child.tag in xmlns_set("svg", "g"):
            build_group(child)
        if child.tag in xmlns_set("svg", "path"):
            build_path(path)


def apply_styles(stylable, svg_element):
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
        return
    else:
        stylable.transform = convert_transforms(tfstr)


def build_group(group):
    pdf_group = drawing.GraphicsContext()
    apply_styles(pdf_group, group)

    for child in group:
        if child.tag in xmlns_lookup("svg", "g"):
            pdf_group.add_item(build_group(child))
        if child.tag in xmlns_lookup("svg", "path"):
            pdf_group.add_item(build_path(child))
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


# this assumes xrefs only reference already-defined ids. I don't know if this is
# required by the svg spec.
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
        raise ValueError(f"use {xref} references nonexistent ref id {ref}")

    return pdf_group


alphabet = re.compile(r"([a-zA-Z])")
number_split = re.compile(r"[ ,]+")
# this doesn't support all transform types, sorry
transform_getter = re.compile(
    r"(scale|translate|rotate)\(((?:\s*(?:[-+]?[\d\.]+,?)+\s*)+)\)"
)


def convert_transforms(tfstr):
    parsed = transform_getter.findall(tfstr)

    transform = drawing.Transform.identity()
    for type, args in parsed:
        if type == "scale":
            arg = float(args)
            transform = drawing.Transform.scaling(x=arg, y=arg) @ transform
        elif type == "rotate":
            arg = float(args)
            transform = drawing.Transform.rotation_d(theta_d=arg) @ transform
        elif type == "translate":
            x, y = tuple(float(n) for n in number_split.split(args))
            transform = drawing.Transform.translation(x=x, y=y) @ transform

    return transform


class SVGSmoothCubicCurve(NamedTuple):
    c2: drawing.Point
    end: drawing.Point

    @classmethod
    def from_path_points(cls, path, c2x, c2y, ex, ey):
        return path.add_item(
            cls(c2=drawing.Point(x=c2x, y=c2y), end=drawing.Point(x=ex, y=ey))
        )

    def render(self, path_gsds, style, last_item):
        if isinstance(last_item, drawing.BezierCurve):
            c1 = drawing.Point((2 * last_item.end) - last_item.c2)
        else:
            c1 = last_item.end_point

        return drawing.BezierCurve(c1, self.c2, self.end).render(
            path_gsds, style, last_item
        )

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        rendered, resolved = self.render(path_gsds, style, last_item)
        debug_stream.write(f"{self} resolved to {resolved}\n")

        return rendered, resolved


class SVGSmoothCubicCurveRelative(NamedTuple):
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
            c1 = drawing.Point((2 * last_item.end) - last_item.c2)
        else:
            c1 = last_point

        c2 = last_point + self.c2
        end = last_point + self.end

        return drawing.BezierCurve(c1, c2, end).render(path_gsds, style, last_item)

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        rendered, resolved = self.render(path_gsds, style, last_item)
        debug_stream.write(f"{self} resolved to {resolved}\n")

        return rendered, resolved


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
        rendered, resolved = self.render(path_gsds, style, last_item)
        debug_stream.write(f"{self} resolved to {resolved}\n")

        return rendered, resolved


class SVGSmoothCubicCurveRelative(NamedTuple):
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
        rendered, resolved = self.render(path_gsds, style, last_item)
        debug_stream.write(f"{self} resolved to {resolved}\n")

        return rendered, resolved


class SVGSmoothQuadraticCurveRelative(NamedTuple):
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
    "s": (4, SVGSmoothCubicCurveRelative.from_path_points),
    "S": (4, SVGSmoothCubicCurve.from_path_points),
    "q": (4, drawing.PaintedPath.quadratic_bezier_relative),
    "Q": (4, drawing.PaintedPath.quadratic_bezier_to),
    "t": (2, SVGSmoothQuadraticCurveRelative.from_path_points),
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

        # we use read_idx as an indicator of whether the path directive was implicit or
        # not. SVG allows for purely implicit line directives to follow a move
        # directive, i.e. `M 0,0 1,1` is the same as `M 0,0 L 1,1`. Similarly,
        # `m 0,0 1,1` is the same as `m 0,0 l 1,1` (see:
        # https://www.w3.org/TR/SVG/paths.html#PathDataMovetoCommands)
        if last_directive in {"m", "M"} and read_idx == 0:
            read_count, last_directive = path_directive_mapping[
                {"m": "l", "M": "L"}[last_directive]
            ]

        numbers, svg_path = _read_n_numbers(svg_path[read_idx:], read_count)

        last_directive(pdf_path, *numbers)


def convert_svg_to_path(svg_text):
    svg_tree = xml.etree.ElementTree.fromstring(svg_text)

    # tag name includes the xml namespace if it is provided
    if svg_tree.tag not in xmlns_lookup("svg", "svg"):
        raise ValueError(f"root tag must be svg, not {svg_tree.tag}")

    try:
        viewbox = svg_tree.attrib["viewBox"]
    except KeyError:
        view_x = view_y = view_w = view_h = 0
    else:
        view_x, view_y, view_w, view_h = tuple(
            float(i) for i in svg_tree.attrib["viewBox"].split(" ")
        )

    # we currently render irrespective of the viewport (i.e. don't grab width/height
    # attributes from the svg)

    base_group = drawing.GraphicsContext()
    base_group.transform = drawing.Transform.scaling(x=1, y=-1).about(
        x=view_w / 2, y=view_h / 2
    ) @ drawing.Transform.translation(-view_x, -view_y)
    base_group.style.stroke_width = None
    base_group.style.auto_close = False

    for child in svg_tree:
        if child.tag in xmlns_lookup("svg", "defs"):
            handle_defs(child)
        if child.tag in xmlns_lookup("svg", "g"):
            base_group.add_item(build_group(child))
        elif child.tag in xmlns_lookup("svg", "path"):
            base_group.add_item(build_path(child))
        elif child.tag in xmlns_lookup("svg", "use"):
            base_group.add_item(build_xref(child))

    return base_group
