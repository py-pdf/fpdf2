from contextlib import contextmanager
import enum
import math


def _clamp8(value):
    return 0.0 if value < 0.0 else 255.0 if value > 255.0 else value


def _render_number(number):
    # this approach tries to produce minimal representations of floating point numbers
    # but can also produce "-0".
    return f"{number:.4f}".rstrip("0").rstrip(".")


class Color:
    def __init__(self, parameters):
        self._parameters = parameters

    def render(self):
        return " ".join(_render_number(param) for param in self._parameters)


class RGBColor(Color):
    operand = "rg"


class GrayColor(Color):
    operand = "g"


class CMYKColor(Color):
    operand = "k"


class RGB8(RGBColor):
    def __init__(self, r, g, b):
        super().__init__([_clamp8(r) / 255.0, _clamp8(g) / 255.0, _clamp8(b) / 255.0])

    def __str__(self):
        params = []
        for field, value in zip(("r", "g", "b"), self._parameters):
            params.append(f"{field}={round(value * 255)}")

        return f"RGB8: {' '.join(params)}"


class Gray8(GrayColor):
    def __init__(self, w):
        super().__init__([_clamp8(w) / 255.0])

    def __str__(self):
        return f"Gray8: {round(self._parameters[0] * 255)}"


class CMYK8(CMYKColor):
    def __init__(self, c, m, y, k):
        super().__init__(
            [
                _clamp8(c) / 255.0,
                _clamp8(m) / 255.0,
                _clamp8(y) / 255.0,
                _clamp8(k) / 255.0,
            ]
        )

    def __str__(self):
        params = []
        for field, value in zip(("c", "m", "y", "k"), self._parameters):
            params.append(f"{field}={round(value * 255)}")

        return f"CMYK8: {' '.join(params)}"


class DrawingContext:
    """
    Base context for a drawing in a PDF

    This context is not stylable and is mainly responsible for transforming path
    drawing coordinates into user coordinates (i.e. it ensures that the output drawing
    is correctly scaled).
    """

    def __init__(self):
        self._subitems = []

    def add_item(self, item):
        """
        Append an item to this drawing context

        Args:
            item (GraphicsContext, PaintedPath): the item to be appended.
        """

        if not isinstance(item, (GraphicsContext, PaintedPath)):
            raise TypeError(f"{item} doesn't belong in a DrawingContext")

        self._subitems.append(item)

    def render(self, first_point, scale):
        if not self._subitems:
            return ""

        start, last_point = PushGraphicsStack().render(first_point)
        scale, last_point = Transform.scale(x=scale, y=scale).render(last_point)

        render_list = [start, scale]

        for item in self._subitems:
            rendered, last_point = item.render(last_point)
            if rendered:
                render_list.append(rendered)

        render_list.append(PopGraphicsStack().render(last_point)[0])

        return " ".join(render_list)

    def dump_render_tree(self, outstream):
        outstream.write("ROOT\n")
        for child in self._subitems[:-1]:
            outstream.write(" ├─ ")
            child.dump_render_tree(outstream, " │  ")

        if self._subitems:
            outstream.write(" └─ ")
            self._subitems[-1].dump_render_tree(outstream, "    ")


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def translate(self, delta):
        return self.__class__(self.x + delta.x, self.y + delta.y)

    def render(self):
        return f"{_render_number(self.x)} {_render_number(self.y)}"

    def __eq__(self, other):
        if isinstance(other, Point):
            return self.x == other.x and self.y == other.y

        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return self.__class__(self.x * other, self.y * other)

        return NotImplemented

    def __str__(self):
        return f"(x={_render_number(self.x)}, y={_render_number(self.y)})"


class PushGraphicsStack:
    def render(self, last_point):
        return ("q", last_point)

    def __str__(self):
        return "push graphics stack"


class PopGraphicsStack:
    def render(self, last_point):
        return ("Q", last_point)

    def __str__(self):
        return "pop graphics stack"


class PaintStyle(enum.Enum):
    stroke = "S"
    close_stroke = "s"
    fill_nonzero = "f"
    fill_evenodd = "f*"
    stroke_fill_nonzero = "B"
    stroke_fill_evenodd = "B*"
    close_stroke_fill_nonzero = "b"
    close_stroke_fill_evenodd = "b*"
    dont_paint = "n"

    @classmethod
    def coerce(cls, value):
        if isinstance(value, cls):
            return value
        elif isinstance(value, str):
            try:
                return cls(value)
            except ValueError:
                pass
            try:
                return cls[value.lower()]
            except KeyError:
                pass

            raise ValueError(f"{value} is not a valid {cls.__name__}")
        else:
            raise TypeError(f"{value} cannot convert to a {cls.__name__}")

    def render(self, last_point):
        return (self.value, last_point)

    def __str__(self):
        return f"paint style: {self.name}"


class ClippingPathIntersection(enum.Enum):
    nonzero = "W"
    evenodd = "W*"

    @classmethod
    def coerce(cls, value):
        if isinstance(value, cls):
            return value
        elif isinstance(value, str):
            try:
                return cls(value)
            except ValueError:
                pass
            try:
                return cls[value.lower()]
            except KeyError:
                pass

            raise ValueError(f"{value} is not a valid {cls.__name__}")
        else:
            raise TypeError(f"{value} cannot convert to a {cls.__name__}")

    def render(self, last_point):
        return (self.value, last_point)

    def __str__(self):
        return f"clipping path intersection rule: {self.name}"


class Transform:
    # compact representation of an affine transformation matrix for 2D shapes.
    # The actual matrix is:
    #                     [ A B 0 ]
    # [x' y' 1] = [x y 1] [ C D 0 ]
    #                     [ E F 1 ]
    # The identity transform is 1 0 0 1 0 0

    @classmethod
    def identity(cls):
        return cls(1, 0, 0, 1, 0, 0)

    @classmethod
    def translation(cls, x, y):
        return cls(1, 0, 0, 1, x, y)

    @classmethod
    def scale(cls, x=1, y=1):
        return cls(x, 0, 0, y, 0, 0)

    @classmethod
    def rotation(cls, theta):
        return cls(
            math.cos(theta), -math.sin(theta), math.sin(theta), math.cos(theta), 0, 0
        )

    @classmethod
    def rotation_d(cls, theta_d):
        return cls.rotation(math.radians(theta_d))

    @classmethod
    def shear(cls, x, y):
        return cls(1, x, y, 1, 0, 0)

    def __init__(self, a, b, c, d, e, f):
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.f = f

    def _update(self, tf):
        self.a = tf.a
        self.b = tf.b
        self.c = tf.c
        self.d = tf.d
        self.e = tf.e
        self.f = tf.f
        return self

    def translate(self, x, y):
        return self._update(self.__class__.translation(x, y) * self)

    def rotate(self, theta):
        return self._update(self.__class__.rotation(theta) * self)

    def rotate_d(self, theta_d):
        return self._update(self.__class__.rotation_d(theta_d) * self)

    def about(self, x, y):
        return self._update(
            self.__class__.translation(-x, -y) * self * self.__class__.translation(x, y)
        )

    def __mul__(self, other):
        if isinstance(other, Transform):
            # in this multiplication, self is the left operand and other is the right
            return self.__class__(
                a=self.a * other.a + self.b * other.c,
                b=self.a * other.b + self.b * other.d,
                c=self.c * other.a + self.d * other.c,
                d=self.c * other.b + self.d * other.d,
                e=self.e * other.a + self.f * other.c + other.e,
                f=self.e * other.b + self.f * other.d + other.f,
            )
        elif isinstance(other, Point):
            return Point(
                x=self.a * other.x + self.c * other.y + self.e,
                y=self.b * other.x + self.d * other.y + self.f,
            )
        else:
            return NotImplemented

    def render(self, last_point):
        return (
            f"{_render_number(self.a)} {_render_number(self.b)} "
            f"{_render_number(self.c)} {_render_number(self.d)} "
            f"{_render_number(self.e)} {_render_number(self.f)} cm",
            last_point,
        )

    def __str__(self):
        return (
            f"transform: ["
            f"{_render_number(self.a)} {_render_number(self.b)} 0; "
            f"{_render_number(self.c)} {_render_number(self.d)} 0; "
            f"{_render_number(self.e)} {_render_number(self.f)} 1]"
        )


class StrokeWidth:
    def __init__(self, width):
        self.width = width

    def render(self, last_point):
        return (f"{_render_number(self.width)} w", last_point)

    def __str__(self):
        return f"stroke width: {_render_number(self.width)}"


class StrokeCapStyle(enum.IntEnum):
    butt = 0
    round = 1
    square = 2

    @classmethod
    def coerce(cls, value):
        if isinstance(value, cls):
            return value
        elif isinstance(value, str):
            return cls[value.lower()]
        elif isinstance(value, int):
            return cls(value)
        else:
            raise TypeError(f"{value} cannot convert to a {cls.__name__}")

    def render(self, last_point):
        return (f"{self.value} J", last_point)

    def __str__(self):
        return f"stroke cap style: {self.name}"


class StrokeJoinStyle(enum.IntEnum):
    miter = 0
    round = 1
    bevel = 2

    @classmethod
    def coerce(cls, value):
        if isinstance(value, cls):
            return value
        elif isinstance(value, str):
            return cls[value.lower()]
        elif isinstance(value, int):
            return cls(value)
        else:
            raise TypeError(f"{value} cannot convert to a {cls.__name__}")

    def render(self, last_point):
        return (f"{self.value} j", last_point)

    def __str__(self):
        return f"stroke join style: {self.name}"


class StrokeMiterLimit:
    def __init__(self, limit):
        self.limit = limit

    def render(self, last_point):
        # limit is a ratio so it does not need to be scaled
        return (f"{_render_number(self.limit)} M", last_point)

    def __str__(self):
        return f"stroke miter limit: {_render_number(self.limit)}"


class StrokeDashPattern:
    def __init__(self, pattern, phase):
        if isinstance(pattern, (int, float)):
            pattern = (pattern,)

        if len(pattern) > 2:
            raise ValueError(f"dash pattern must have 2 or fewer entries")
        self.pattern = pattern
        self.phase = phase

    def render(self, last_point):
        return (
            f"[{' '.join(_render_number(pat) for pat in self.pattern)}] {_render_number(self.phase)} d",
            last_point,
        )

    def __str__(self):
        return f"stroke dash: pattern={self.pattern} phase={self.phase}"


class FillColor:
    def __init__(self, color):
        self.color = color

    def render(self, last_point):
        return (f"{self.color.render()} {self.color.operand}", last_point)

    def __str__(self):
        return f"fill color: {self.color}"


class StrokeColor:
    def __init__(self, color):
        self.color = color

    def render(self, last_point):
        return (f"{self.color.render()} {self.color.operand.upper()}", last_point)

    def __str__(self):
        return f"stroke color: {self.color}"


def _render_move(pt):
    return f"{pt.render()} m"


def _render_line(pt):
    return f"{pt.render()} l"


def _render_curve(start, ctrl1, ctrl2, end):
    if start == ctrl1:
        return f"{ctrl2.render()} {end.render()} v"
    elif ctrl2 == end:
        return f"{ctrl1.render()} {end.render()} y"
    else:
        return f"{ctrl1.render()} {ctrl2.render()} {end.render()} c"


class Move:
    def __init__(self, pt):
        self.pt = pt

    def render(self, last_point):
        return (_render_move(self.pt), self.pt)

    def __str__(self):
        return f"move to: {self.pt}"


class RelativeMove:
    def __init__(self, d):
        self.d = d

    def render(self, last_point):
        point = last_point.translate(self.d)
        return (_render_move(point), point)

    def __str__(self):
        return f"move to (offset): {self.d}"


class Line:
    def __init__(self, pt):
        self.pt = pt

    def render(self, last_point):
        return (_render_line(self.pt), self.pt)

    def __str__(self):
        return f"line to: {self.pt}"


class RelativeLine:
    def __init__(self, d):
        self.d = d

    def render(self, last_point):
        point = last_point.translate(self.d)
        return (_render_line(point), point)

    def __str__(self):
        return f"line to (offset): {self.d}"


class BezierCurve:
    def __init__(self, ctrl1, ctrl2, end):
        self.ctrl1 = ctrl1
        self.ctrl2 = ctrl2
        self.end = end

    def render(self, last_point):
        return (
            _render_curve(last_point, self.ctrl1, self.ctrl2, self.end),
            self.end,
        )

    def __str__(self):
        return f"curve to: ctrl1={self.ctrl1}, ctrl2={self.ctrl2}, end={self.end}"


class RelativeBezierCurve:
    def __init__(self, c1d, c2d, end):
        self.c1d = c1d
        self.c2d = c2d
        self.end = end

    def render(self, last_point):
        ctrl1 = last_point.translate(self.c1d)
        ctrl2 = ctrl1.translate(self.c2d)
        end = ctrl2.translate(self.end)

        return (_render_curve(last_point, ctrl1, ctrl2, end), end)

    def __str__(self):
        return f"curve to (offset): ctrl1={self.c1d}, ctrl2={self.c2d}, end={self.end}"


class QuadraticBezierCurve:
    def __init__(self, ctrl, end):
        self.ctrl = ctrl
        self.end = end

    def render(self, last_point):
        ctrl = self.ctrl
        end = self.end
        ctrl1 = Point(
            last_point.x + 2 * (ctrl.x - last_point.x) / 3,
            last_point.y + 2 * (ctrl.y - last_point.y) / 3,
        )
        ctrl2 = Point(
            end.x + 2 * (ctrl.x - end.x) / 3, end.y + 2 * (ctrl.y - end.y) / 3
        )

        return (_render_curve(last_point, ctrl1, ctrl2, end), end)

    def __str__(self):
        return f"quadratic curve to (offset): ctrl={self.ctrl}, end={self.end}"


class RelativeQuadraticBezierCurve:
    def __init__(self, ctrl, end):
        self.ctrl = ctrl
        self.end = end

    def render(self, last_point):
        ctrl = last_point.translate(self.ctrl)
        end = last_point.translate(self.end)

        ctrl1 = Point(
            last_point.x + 2 * (ctrl.x - last_point.x) / 3,
            last_point.y + 2 * (ctrl.y - last_point.y) / 3,
        )
        ctrl2 = Point(
            end.x + 2 * (ctrl.x - end.x) / 3, end.y + 2 * (ctrl.y - end.y) / 3
        )

        return (_render_curve(last_point, ctrl1, ctrl2, end), end)

    def __str__(self):
        return f"quadratic curve to (offset): ctrl={self.ctrl}, end={self.end}"


class Rectangle:
    def __init__(self, org, size):
        self.org = org
        self.size = size

    def render(self, last_point):
        return (f"{self.org.render()} {self.size.render()} re", last_point)

    def __str__(self):
        return (
            f"Rect: x={_render_number(self.org.x)}, y={_render_number(self.org.y)}, "
            f"w={_render_number(self.size.x)}, h={_render_number(self.size.y)}"
        )


class Close:
    def render(self, last_point):
        return "h", last_point

    def __str__(self):
        return "close path"


class Stylable:
    def _get_style(self, style_class):
        raise NotImplementedError()

    def _set_style(self, style):
        raise NotImplementedError()

    @property
    def fill_color(self):
        try:
            return self._get_style(FillColor).color
        except KeyError:
            return None

    @fill_color.setter
    def fill_color(self, color):
        self._set_style(FillColor(color))

    @property
    def stroke_color(self):
        try:
            return self._get_style(StrokeColor).color
        except KeyError:
            return None

    @stroke_color.setter
    def stroke_color(self, color):
        self._set_style(StrokeColor(color))

    @property
    def stroke_width(self):
        try:
            return self._get_style(StrokeWidth).width
        except KeyError:
            return None

    @stroke_width.setter
    def stroke_width(self, width):
        self._set_style(StrokeWidth(width))

    @property
    def stroke_dash_pattern(self):
        try:
            pattern = self._get_style(StrokeDashPattern)
            return pattern.pattern, pattern.phase
        except KeyError:
            return None

    @stroke_dash_pattern.setter
    def stroke_dash_pattern(self, value):
        self._set_style(StrokeDashPattern(value[0], value[1]))

    @property
    def stroke_cap_style(self):
        try:
            return self._get_style(StrokeCapStyle)
        except KeyError:
            return None

    @stroke_cap_style.setter
    def stroke_cap_style(self, style):
        self._set_style(StrokeCapStyle.coerce(style))

    @property
    def stroke_join_style(self):
        try:
            return self._get_style(StrokeJoinStyle)
        except KeyError:
            return None

    @stroke_join_style.setter
    def stroke_join_style(self, style):
        self._set_style(StrokeJoinStyle.coerce(style))

    @property
    def stroke_miter_limit(self):
        try:
            return self._get_style(StrokeMiterLimit).limit
        except KeyError:
            return None

    @stroke_miter_limit.setter
    def stroke_miter_limit(self, limit):
        self._set_style(StrokeMiterLimit(limit))

    @property
    def transform(self):
        try:
            return self._get_style(Transform)
        except KeyError:
            return None

    @transform.setter
    def transform(self, tf):
        self._set_style(tf)

    @property
    def clipping_path(self):
        try:
            return self._get_style(ClippingPath)
        except KeyError:
            return None

    @clipping_path.setter
    def clipping_path(self, path):
        self._set_style(path)


class PaintedPath(Stylable):
    def __init__(self, paint_style, x=0, y=0):
        self._root_graphics_context = GraphicsContext()
        self._graphics_context = self._root_graphics_context

        self._paint_style = PaintStyle.coerce(paint_style)
        self._auto_close = self._paint_style in {
            PaintStyle.close_stroke,
            PaintStyle.close_stroke_fill_nonzero,
            PaintStyle.close_stroke_fill_evenodd,
        }

        # self._auto_close = False

        self._closed = True
        self._close_context = self._graphics_context
        self.move_to(x, y)

    @contextmanager
    def _new_graphics_context(self, _attach=True):
        old_graphics_context = self._graphics_context
        new_graphics_context = GraphicsContext()
        self._graphics_context = new_graphics_context
        try:
            yield new_graphics_context
            if _attach:
                old_graphics_context.add_item(new_graphics_context)
        finally:
            self._graphics_context = old_graphics_context

    @contextmanager
    def transform_group(self, transform):
        """
        Apply the provided transforms to all points added within this context.
        """
        with self._new_graphics_context() as ctxt:
            ctxt.transform = transform
            yield self

    def _push_drawing_sequence(self, item):
        if self._starter_move is not None:
            self._closed = False

            self._graphics_context.add_item(self._starter_move)
            self._close_context = self._graphics_context
            self._starter_move = None

        self._graphics_context.add_item(item)

    def rectangle(self, x, y, w, h):
        """
        Append a rectangle as a closed subpath to the current path.

        The rectangle has all of the same constraints that regular subpaths do.
        """
        self._close()
        self._push_drawing_sequence(Rectangle(Point(x, y), Point(w, h)))

        return self

    def move_to(self, x, y):
        self._close()
        self._starter_move = Move(Point(x, y))

    def move_relative(self, x, y):
        self._close()
        self._starter_move = RelativeMove(Point(x, y))

    def line_to(self, x, y):
        point = Point(x, y)
        self._push_drawing_sequence(Line(point))
        return self

    def line_relative(self, dx, dy):
        offset = Point(dx, dy)
        self._push_drawing_sequence(RelativeLine(offset))
        return self

    def curve_to(self, x1, y1, x2, y2, x3, y3):
        ctrl1 = Point(x1, y1)
        ctrl2 = Point(x2, y2)
        end = Point(x3, y3)

        self._push_drawing_sequence(BezierCurve(ctrl1, ctrl2, end))
        return self

    def curve_relative(self, dx1, dy1, dx2, dy2, dx3, dy3):
        """
        Append a cubic Bézier curve whose points are each expressed relative to the
        preceding point.

        E.g. with a start point of (0, 0), given (1, 1), (2, 2), (3, 3), the output
        curve would have the points:

        (0, 0) c1 (1, 1) c2 (3, 3) e (6, 6)
        """
        c1d = Point(dx1, dy1)
        c2d = Point(dx2, dy2)
        end = Point(dx3, dy3)

        self._push_drawing_sequence(RelativeBezierCurve(c1d, c2d, end))
        return self

    def quadratic_bezier_to(self, x1, y1, x2, y2):
        """
        Append a cubic Bézier curve mimicking the specified quadratic Bézier curve.
        """
        ctrl = Point(x1, y1)
        end = Point(x2, y2)
        self._push_drawing_sequence(QuadraticBezierCurve(ctrl, end))
        return self

    def quadratic_bezier_relative(self, x1, y1, x2, y2):
        """
        Append a cubic Bézier curve mimicking the specified quadratic Bézier curve.
        """
        ctrl = Point(x1, y1)
        end = Point(x2, y2)
        self._push_drawing_sequence(RelativeQuadraticBezierCurve(ctrl, end))
        return self

    def close(self):
        self.closed = True
        self._push_drawing_sequence(Close())

    def _close(self):
        if not self._closed:
            if self._auto_close:
                self._close_context.add_item(Close())
                self._close_context = self._graphics_context

            self._closed = True

    def _get_style(self, style_class):
        self._root_graphics_context._get_style(style_class)

    def _set_style(self, style):
        self._root_graphics_context._set_style(style)

    def render(self, last_point):
        self._root_graphics_context.add_item(self._paint_style)

        return self._root_graphics_context.render(last_point)


    def dump_render_tree(self, outstream, prefix):
        outstream.write(f"{self.__class__.__name__} ({self._paint_style}) > ")
        self._root_graphics_context.dump_render_tree(outstream, prefix)


class ClippingPath(PaintedPath):
    # because clipping paths can be painted, we inherit from PaintedPath. However, when
    # setting the styling on the clipping path, those values will also be applied to
    # the PaintedPath the ClippingPath is applied to unless they are explicitly set for
    # that painted path. This is not ideal, but there's no way to really fix it from
    # the PDF rendering model, and trying to track the appropriate state/defaults seems
    # similarly error prone.

    # In general, the expectation is that painted clipping paths are likely to be very
    # uncommon, so it's an edge case that isn't worth worrying too much about.

    def __init__(self, intersection_rule, paint_style=PaintStyle.dont_paint, x=0, y=0):
        super().__init__(paint_style=paint_style, x=x, y=y)
        self._intersection_rule = ClippingPathIntersection.coerce(intersection_rule)
        self._paint_style = PaintStyle.coerce(paint_style)

    def render(self, last_point):
        # painting the clipping path outside of its root graphics context allows it to
        # be transformed without affecting the transform of the graphics context of the
        # path it is being used to clip. This is because, unlike all of the other style
        # settings, transformations immediately affect the points following them,
        # rather than only affecting them at painting time. stroke settings and color
        # settings are applied only at paint time.

        render_list, last_point = self._root_graphics_context._build_render_list(
            last_point, _push_stack=False
        )
        render_list.append(self._intersection_rule.render(None)[0])
        render_list.append(self._paint_style.render(None)[0])

        return " ".join(render_list), last_point



class GraphicsContext(Stylable):
    style_order = (
        Transform,
        FillColor,
        StrokeColor,
        StrokeWidth,
        StrokeDashPattern,
        StrokeCapStyle,
        StrokeJoinStyle,
        StrokeMiterLimit,
        ClippingPath,
    )
    style_set = {*style_order}

    def __init__(self):
        self._style_items = {}
        self._path_items = []

    def _set_style(self, style):
        if style.__class__ not in self.style_set:
            raise TypeError(f"{style} is not a style item.")

        self._style_items[style.__class__] = style

    def _get_style(self, style_class):
        if style_class not in self.style_set:
            raise TypeError(f"{style_class} is not a style item.")

        return self._style_items[style_class]


    def add_item(self, item):
        self._path_items.append(item)

    def merge(self, other_context):
        self._path_items.extend(other_context._path_items)

    def _build_render_list(self, last_point, _push_stack=True):
        if not self._path_items:
            return ([], last_point)
        else:
            render_list = []

            # add the clipping path first so that it can preserve all of its style
            # settings for being drawn without needing to push the graphics stack
            try:
                render_list.append(
                    self._style_items[ClippingPath].render(last_point)[0]
                )
            except KeyError:
                pass

            # we loop over the tuple instead of the style dict to make the PDF
            # generation deterministic
            for style_class in self.style_order:
                if style_class is ClippingPath:
                    continue

                try:
                    rendered, last_point = self._get_style(style_class).render(
                        last_point
                    )
                    if rendered:
                        render_list.append(rendered)
                except KeyError:
                    pass

            for item in self._path_items:
                rendered, last_point = item.render(last_point)

                if rendered:
                    render_list.append(rendered)

            if _push_stack:
                render_list.insert(0, PushGraphicsStack().render(None)[0])
                render_list.append(PopGraphicsStack().render(None)[0])

            # TODO: hmmmmmm, is this even close to being correct behavior?
            try:
                last_point = self._style_items[Transform] * last_point
            except KeyError:
                pass

            return render_list, last_point

    def render(self, last_point, _push_stack=True):
        render_list, last_point = self._build_render_list(last_point, _push_stack=True)
        return (" ".join(render_list), last_point)

    def dump_render_tree(self, outstream, prefix):
        outstream.write(f"{self.__class__.__name__}")

        styles = []
        for item in self._style_items.values():
            if not isinstance(item, ClippingPath):
                styles.append(str(item))

        if styles:
            outstream.write(" (" + ", ".join(styles) + ")")
        outstream.write("\n")

        if ClippingPath in self._style_items:
            outstream.write(prefix + " ├─ ")
            self._style_items[ClippingPath].dump_render_tree(outstream, prefix + " │  ")

        for item in self._path_items[:-1]:
            outstream.write(prefix + " ├─ ")
            if isinstance(item, (GraphicsContext, PaintedPath)):
                item.dump_render_tree(outstream, prefix + " │  ")
            else:
                outstream.write(f"{item}\n")

        if self._path_items:
            item = self._path_items[-1]
            outstream.write(prefix + " └─ ")
            if isinstance(item, (GraphicsContext, PaintedPath)):
                item.dump_render_tree(outstream, prefix + "    ")
            else:
                outstream.write(f"{item}\n")
