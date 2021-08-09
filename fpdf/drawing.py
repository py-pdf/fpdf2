from collections import OrderedDict
from contextlib import contextmanager
import enum
import decimal
import math
from typing import Optional, NamedTuple, Union


# type alias:
Number = Union[int, float, decimal.Decimal]

_global_style_registry = {}
# this is just a reverse mapping of the above
_global_style_name_lookup = {}


# this maybe should live in fpdf.syntax
class Raw(str):
    """raw data to be directly emitted to the pdf"""


class Name(str):
    """a pdf name, which is distinct from strings"""


WHITESPACE = frozenset({"\0", "\t", "\n", "\f", "\r", " "})
EOL_CHARS = frozenset({"\n", "\r"})


def get_style_dict_by_name(name):
    return _global_style_name_lookup[name]


def _new_global_style_name():
    return Name(f"GS{len(_global_style_registry)}")


def _get_or_set_style_dict(style):
    sdict = style.to_pdf_dict()

    try:
        return _global_style_registry[sdict]
    except KeyError:
        pass

    name = _new_global_style_name()
    _global_style_registry[sdict] = name
    _global_style_name_lookup[name] = sdict

    return name


def _check_range(value, minimum=0.0, maximum=1.0):
    if not minimum <= value <= maximum:
        raise ValueError(f"{value} not in range [{minimum}, {maximum}]")

    return value


def number_to_str(number):
    # this approach tries to produce minimal representations of floating point numbers
    # but can also produce "-0".
    return f"{number:.4f}".rstrip("0").rstrip(".")


# this maybe should live in fpdf.syntax
def render_pdf_primitive(primitive):
    if isinstance(primitive, Raw):
        output = primitive
    elif callable(getattr(primitive, "pdf_repr", None)):
        output = primitive.pdf_repr()
    elif isinstance(primitive, Name):
        # this should handle escape sequences, to be proper (#XX)
        output = f"/{primitive}"
    elif isinstance(primitive, str):
        # this should handle escape sequences, to be proper (\n \r \t \b \f \( \) \\)
        output = f"({str})"
    elif isinstance(primitive, bytes):
        output = f"<{primitive.hex()}>"
    elif isinstance(primitive, (int, float, decimal.Decimal)):
        output = number_to_str(primitive)
    elif isinstance(primitive, bool):
        output = ["false", "true"][primitive]
    elif isinstance(primitive, (list, tuple)):
        output = "[" + " ".join(render_pdf_primitive(val) for val in primitive) + "]"
    elif primitive is None:
        output = "null"
    elif isinstance(primitive, dict):
        item_list = []
        for key, val in primitive.items():
            if not isinstance(key, Name):
                raise ValueError("dict keys must be Names")

            item_list.append(
                render_pdf_primitive(key) + " " + render_pdf_primitive(val)
            )

        output = "<< " + "\n".join(item_list) + " >>"
    else:
        raise TypeError(f"cannot produce PDF representation for value {primitive!r}")

    return Raw(output)


_global_style_registry[render_pdf_primitive({Name("Type"): Name("ExtGState")})] = None


# We allow passing alpha in as None instead of a numeric quantity, which signals to the
# rendering procedure not to omit an explicit alpha field for this graphics state,
# causing it to be inherited from the parent.

# this weird inheritance is used because for some reason normal NamedTuple usage doesn't
# allow overriding __new__, even though it works just as expected this way.
class DeviceRGB(
    NamedTuple(
        "DeviceRGB",
        [("r", Number), ("g", Number), ("b", Number), ("a", Optional[Number])],
    )
):
    """Emit a DeviceRGB color"""

    # This follows a common PDF drawing operator convention where the operand is upcased
    # to apply to stroke and downcased to apply to fill.

    # This could be more manually specified by  `CS`/`cs` to set the color space
    # (e.g. to /DeviceRGB) and `SC`/`sc` to set the color parameters. The documentation
    # isn't perfectly clear on this front, but it appears that these cannot be set in
    # the current graphics state dictionary and instead is set in the current page
    # resource dictionary. fpdf appears to only generate a single resource dictionary
    # for the entire document, and even if it created one per page, it would still be a
    # lot clunkier to try to use that.

    # Because PDF hates me, personally, the opacity of the drawing HAS to be specified
    # in the current graphics state dictionary and does not exist as a standalone
    # directive.
    OPERATOR = "rg"

    def __new__(cls, r, g, b, a=None):
        if a is not None:
            _check_range(a)

        return super().__new__(
            cls, _check_range(r), _check_range(g), _check_range(b), a
        )

    @property
    def colors(self):
        return self[:-1]


# this weird inheritance is used because for some reason normal NamedTuple usage doesn't
# allow overriding __new__, even though it works just as expected this way.
class DeviceGray(
    NamedTuple(
        "DeviceGray",
        [("g", Number), ("a", Optional[Number])],
    )
):
    """Emit a DeviceGray color"""

    OPERATOR = "g"

    def __new__(cls, g, a=None):
        if a is not None:
            _check_range(a)

        return super().__new__(cls, _check_range(g), a)

    @property
    def colors(self):
        return self[:-1]


# this weird inheritance is used because for some reason normal NamedTuple usage doesn't
# allow overriding __new__, even though it works just as expected this way.
class DeviceCMYK(
    NamedTuple(
        "DeviceCMYK",
        [
            ("c", Number),
            ("m", Number),
            ("y", Number),
            ("k", Number),
            ("a", Optional[Number]),
        ],
    )
):
    """Emit a DeviceCMYK color"""

    OPERATOR = "k"

    def __new__(cls, c, m, y, k, a=None):
        if a is not None:
            _check_range(a)

        return super().__new__(
            cls, _check_range(c), _check_range(m), _check_range(y), _check_range(k), a
        )

    @property
    def colors(self):
        return self[:-1]


def rgb8(r, g, b, a=None):
    if a is not None:
        a /= 255.0

    return DeviceRGB(r / 255.0, g / 255.0, b / 255.0, a)


def gray8(g, a=None):
    if a is not None:
        a /= 255.0

    return DeviceGray(g / 255.0, a)


def cmyk8(c, m, y, k, a=None):
    if a is not None:
        a /= 255.0

    return DeviceCMYK(c / 255.0, m / 255.0, y / 255.0, k / 255.0, a)


def color_from_hex_string(hexstr):
    """
    Parse an RGB color from a css-style 8-bit hexadecimal color string.

    Arg:
        hexstr (str): of the form #RGB, #RGBA, #RRGGBB, or #RRGGBBAA. Must include the
            leading octothorpe. Forms omitting the alpha field are interpreted as
            not specifying the opacity, so it will not be explicitly set.

            An alpha value of 00 is fully transparent and FF is fully opaque.

    Returns:
        DeviceRGB representation of the color.
    """
    if not isinstance(hexstr, str):
        raise TypeError(f"{hexstr} is not of type str")

    if not hexstr.startswith("#"):
        raise ValueError(f"{hexstr} does not start with #")

    hlen = len(hexstr)

    if hlen == 4:
        return rgb8(*[int(char * 2, base=16) for char in hexstr[1:]], a=None)

    if hlen == 5:
        return rgb8(*[int(char * 2, base=16) for char in hexstr[1:]])

    if hlen == 7:
        return rgb8(
            *[int(hexstr[idx : idx + 2], base=16) for idx in range(1, hlen, 2)], a=None
        )

    if hlen == 9:
        return rgb8(*[int(hexstr[idx : idx + 2], base=16) for idx in range(1, hlen, 2)])

    raise ValueError(f"{hexstr} could not be interpreted as a RGB(A) hex string")


class Point(NamedTuple):
    x: Number
    y: Number

    def render(self):
        return f"{number_to_str(self.x)} {number_to_str(self.y)}"

    def dot(self, other):
        """
        Compute the dot product of two points.
        """
        if not isinstance(other, Point):
            raise TypeError(f"cannot dot with {other!r}")

        return self.x * other.x + self.y * other.y

    def angle(self, other):
        """
        Compute the angle between two points (interpreted as vectors from the origin).

        The return value is in the interval (-pi, pi]. Sign is dependent on ordering,
        with clockwise angle travel considered to be positive (i.e. the angle between
        (1, 0) and (0, 1) is +pi/2, the angle between (1, 0) and(0, -1) is -pi/2, and
        the angle between (0, -1) and (1, 0) is +pi/2).
        """

        if not isinstance(other, Point):
            raise TypeError(f"cannot compute angle with {other!r}")

        signifier = (self.x * other.y) - (self.y * other.x)
        sign = (signifier >= 0) - (signifier < 0)
        return sign * math.acos(round(self.dot(other) / (self.mag() * other.mag()), 8))

    def mag(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5

    def __add__(self, other):
        """
        Produce the sum of two points.

        Adding two points is the same as translating the source point by interpreting
        the other point's x and y coordinates as distances.

        Args:
            other (Point): right-hand side of the infix addition operation

        Returns:
            A Point which is the the sum of the two source points.
        """
        if isinstance(other, Point):
            return Point(x=self.x + other.x, y=self.y + other.y)

        return NotImplemented

    def __sub__(self, other):
        """Produce the difference between two points"""
        if isinstance(other, Point):
            return Point(x=self.x - other.x, y=self.y - other.y)

        return NotImplemented

    def __neg__(self):
        """Negate a point"""
        return Point(x=-self.x, y=-self.y)

    def __mul__(self, other):
        """Multiply a point by a scalar value"""
        if isinstance(other, (int, float, decimal.Decimal)):
            return Point(self.x * other, self.y * other)

        return NotImplemented

    __rmul__ = __mul__

    def __div__(self, other):
        if isinstance(other, (int, float, decimal.Decimal)):
            return Point(self.x / other, self.y / other)

        return NotImplemented

    # division is not commutative!

    def __matmul__(self, other):
        if isinstance(other, Transform):
            return Point(
                x=other.a * self.x + other.c * self.y + other.e,
                y=other.b * self.x + other.d * self.y + other.f,
            )

        return NotImplemented

    def __str__(self):
        return f"(x={number_to_str(self.x)}, y={number_to_str(self.y)})"


class Transform(NamedTuple):
    """
    A representation of an affine transformation matrix for 2D shapes.

    The actual matrix is:

                            [ a b 0 ]
        [x' y' 1] = [x y 1] [ c d 0 ]
                            [ e f 1 ]

    Complex transformation operations can be composed via a sequence of simple
    transformations by performing successive matrix multiplication of the simple
    transformations.

    For example, scaling a set of points around a specific center point can be
    represented by a translation-scale-translation sequence, where the first
    translation translates the center to the origin, the scale transform scales the
    points relative to the origin, and the second translation translates the points
    back to the specified center point. Transform multiplication is performed using
    python's dedicated matrix multiplication operator, `@`

    The semantics of this representation mean composed transformations are specified
    left-to-right in order of application (some other systems provide transposed
    representations, in which case the application order is right-to-left).

    For example, to rotate the square (1,1) (1,3) (3,3) (3,1) about its center point
    (which is (2,2)) 45 degrees clockwise, the translate-rotate-translate
    process described above may be applied:

    ```
    rotate_centered = (
        Transform.translation(-2, -2)
        @ Transform.rotation_d(45)
        @ Transform.translation(2, 2)
    )
    ```

    Instance of this class provide a chaining API, so the above transform could also be
    constructed as follows:

    ```
    rotate_centered = Transform.translation(-2, -2).rotate_d(45).translate(2, 2)
    ```

    Or, because the particular operation of performing some transformations about a
    specific point is pretty common,

    ```
    rotate_centered = Transform.rotation_d(45).about(2, 2)
    ```

    By convention, this class provides class method constructors following noun-ish
    naming (translation, scaling, rotation, shearing) and instance method manipulations
    following verb-ish naming (translate, scale, rotate, shear).
    """

    a: float
    b: float
    c: float
    d: float
    e: float
    f: float

    # compact representation of an affine transformation matrix for 2D shapes.
    # The actual matrix is:
    #                     [ A B 0 ]
    # [x' y' 1] = [x y 1] [ C D 0 ]
    #                     [ E F 1 ]
    # The identity transform is 1 0 0 1 0 0

    @classmethod
    def identity(cls):
        """
        Create a transformation matrix representing the identity transform.

        The identity transform is a no-op.
        """
        return cls(1, 0, 0, 1, 0, 0)

    @classmethod
    def translation(cls, x, y):
        """
        Create a transformation matrix that performs translation.

        Args:
            x (float): distance to translate points along the x (horizontal) axis.
            y (float): distance to translate points along the y (vertical) axis.

        Returns:
            A Transform representing the specified translation.
        """

        return cls(1, 0, 0, 1, x, y)

    @classmethod
    def scaling(cls, x, y=None):
        """
        Create a transformation matrix that performs scaling.

        Args:
            x (float): scaling ratio in the x (horizontal) axis. A value of 1
                results in no scale change in the x axis.
            y (float): optional scaling ratio in the y (vertical) axis. A value of 1
                results in no scale change in the y axis. If this value is omitted, it
                defaults to the value provided to the `x` argument.

        Returns:
            A Transform representing the specified scaling.
        """
        if y is None:
            y = x

        return cls(x, 0, 0, y, 0, 0)

    @classmethod
    def rotation(cls, theta):
        """
        Create a transformation matrix that performs rotation.

        Args:
            theta (float): the angle **in radians** by which to rotate. Positive
                values represent clockwise rotations.

        Returns:
            A Transform representing the specified rotation.

        """
        return cls(
            math.cos(theta), math.sin(theta), -math.sin(theta), math.cos(theta), 0, 0
        )

    @classmethod
    def rotation_d(cls, theta_d):
        """
        Create a transformation matrix that performs rotation.

        Args:
            theta (float): the angle **in degrees** by which to rotate. Positive
                values represent clockwise rotations.

        Returns:
            A Transform representing the specified rotation.

        """
        return cls.rotation(math.radians(theta_d))

    @classmethod
    def shearing(cls, x, y=None):
        """
        Create a transformation matrix that performs shearing (not of sheep).

        Args:
            x (float): The amount to shear along the x (horizontal) axis.
            y (float): Optional amount to shear along the y (vertical) axis. If omitted,
                this defaults to the value provided to the `x` argument.

        Returns:
            A Transform representing the specified shearing.

        """
        if y is None:
            y = x
        return cls(1, y, x, 1, 0, 0)

    def translate(self, x, y):
        return self @ Transform.translation(x, y)

    def scale(self, x, y=None):
        return self @ Transform.scaling(x, y)

    def rotate(self, theta):
        return self @ Transform.rotation(theta)

    def rotate_d(self, theta_d):
        return self @ Transform.rotation_d(theta_d)

    def shear(self, x, y=None):
        return self @ Transform.shearing(x, y)

    def about(self, x, y):
        return Transform.translation(-x, -y) @ self @ Transform.translation(x, y)

    def __mul__(self, other):
        if isinstance(other, (int, float, decimal.Decimal)):
            return Transform(
                a=self.a * other,
                b=self.b * other,
                c=self.c * other,
                d=self.d * other,
                e=self.e * other,
                f=self.f * other,
            )

        return NotImplemented

    # scalar multiplication is commutative
    __rmul__ = __mul__

    def __matmul__(self, other):
        if isinstance(other, Transform):
            # in this multiplication, self is the lhs and other is the rhs
            return self.__class__(
                a=self.a * other.a + self.b * other.c,
                b=self.a * other.b + self.b * other.d,
                c=self.c * other.a + self.d * other.c,
                d=self.c * other.b + self.d * other.d,
                e=self.e * other.a + self.f * other.c + other.e,
                f=self.e * other.b + self.f * other.d + other.f,
            )

        return NotImplemented

    def render(self, last_item):
        return (
            f"{number_to_str(self.a)} {number_to_str(self.b)} "
            f"{number_to_str(self.c)} {number_to_str(self.d)} "
            f"{number_to_str(self.e)} {number_to_str(self.f)} cm",
            last_item,
        )

    def __str__(self):
        return (
            f"transform: ["
            f"{number_to_str(self.a)} {number_to_str(self.b)} 0; "
            f"{number_to_str(self.c)} {number_to_str(self.d)} 0; "
            f"{number_to_str(self.e)} {number_to_str(self.f)} 1]"
        )


class CoerciveEnum(enum.Enum):
    @classmethod
    def coerce(cls, value):
        if isinstance(value, cls):
            return value

        if isinstance(value, str):
            try:
                return cls(value)
            except ValueError:
                pass
            try:
                return cls[value.upper()]
            except KeyError:
                pass

            raise ValueError(f"{value} is not a valid {cls.__name__}")

        raise TypeError(f"{value} cannot convert to a {cls.__name__}")


class IntersectionRule(CoerciveEnum):
    NONZERO = "nonzero"
    EVENODD = "evenodd"


class PathPaintRule(CoerciveEnum):
    # the auto-close paint rules are omitted here because it's easier to just emit
    # close operators when appropriate, programmatically
    STROKE = "S"
    FILL_NONZERO = "f"
    FILL_EVENODD = "f*"
    STROKE_FILL_NONZERO = "B"
    STROKE_FILL_EVENODD = "B*"
    DONT_PAINT = "n"

    AUTO = "auto"


class ClippingPathIntersectionRule(CoerciveEnum):
    NONZERO = "W"
    EVENODD = "W*"


class CoerciveIntEnum(enum.IntEnum):
    @classmethod
    def coerce(cls, value):
        if isinstance(value, cls):
            return value

        if isinstance(value, str):
            try:
                return cls[value.upper()]
            except KeyError:
                raise ValueError(f"{value} is not a valid {cls.__name__}") from None

        if isinstance(value, int):
            return cls(value)

        raise TypeError(f"{value} cannot convert to a {cls.__name__}")


class StrokeCapStyle(CoerciveIntEnum):
    BUTT = 0
    ROUND = 1
    SQUARE = 2


class StrokeJoinStyle(CoerciveIntEnum):
    MITER = 0
    ROUND = 1
    BEVEL = 2


class BlendMode(CoerciveEnum):
    NORMAL = Name("Normal")
    MULTIPLY = Name("Multiply")
    SCREEN = Name("Screen")
    OVERLAY = Name("Overlay")
    DARKEN = Name("Darken")
    LIGHTEN = Name("Lighten")
    COLOR_DODGE = Name("ColorDodge")
    COLOR_BURN = Name("ColorBurn")
    HARD_LIGHT = Name("HardLight")
    SOFT_LIGHT = Name("SoftLight")
    DIFFERENCE = Name("Difference")
    EXCLUSION = Name("Exclusion")
    # nonseparable, but I believe that only affects rendering
    HUE = Name("Hue")
    SATURATION = Name("Saturation")
    COLOR = Name("Color")
    LUMINOSITY = Name("Luminosity")


class PDFStyleKeys(enum.Enum):
    FILL_ALPHA = Name("ca")
    BLEND_MODE = Name("BM")  # shared between stroke and fill
    STROKE_ALPHA = Name("CA")
    STROKE_ADJUSTMENT = Name("SA")
    STROKE_WIDTH = Name("LW")
    STROKE_CAP_STYLE = Name("LC")
    STROKE_JOIN_STYLE = Name("LJ")
    STROKE_MITER_LIMIT = Name("ML")
    STROKE_DASH_PATTERN = Name("D")  # array of array, number, e.g. [[1 1] 0]


class GraphicsStyle:
    """
    A class representing various style attributes that determine drawing appearance.

    This class uses the convention that the global Python singleton ellipsis (`...`) is
    exclusively used to represent values that are inherited from the parent style. This
    is to disambiguate the value None which is used for several values to signal an
    explicitly disabled style. An example of this is the fill/stroke color styles,
    which use None as hints to the auto paint style detection code.
    """

    INHERIT = ...
    # order is be important here because some of these properties are entangled, e.g.
    # stroke_dash_pattern and stroke_dash_phase
    MERGE_PROPERTIES = (
        "paint_rule",
        "auto_close",
        "intersection_rule",
        "fill_color",
        "fill_opacity",
        "stroke_color",
        "stroke_opacity",
        "blend_mode",
        "stroke_width",
        "stroke_cap_style",
        "stroke_join_style",
        "stroke_miter_limit",
        "stroke_dash_pattern",
        "stroke_dash_phase",
    )

    _PAINT_RULE_LOOKUP = {
        frozenset({}): PathPaintRule.DONT_PAINT,
        frozenset({"stroke"}): PathPaintRule.STROKE,
        frozenset({"fill", IntersectionRule.NONZERO}): PathPaintRule.FILL_NONZERO,
        frozenset({"fill", IntersectionRule.EVENODD}): PathPaintRule.FILL_EVENODD,
        frozenset(
            {"stroke", "fill", IntersectionRule.NONZERO}
        ): PathPaintRule.STROKE_FILL_NONZERO,
        frozenset(
            {"stroke", "fill", IntersectionRule.EVENODD}
        ): PathPaintRule.STROKE_FILL_EVENODD,
    }
    """A dictionary for resolving `PathPaintRule.AUTO`"""

    # If these are used in a nested graphics context inside of a painting path
    # operation, they are no-ops. However, they can be used for outer GraphicsContexts
    # that painting paths inherit from.

    @classmethod
    def merge(cls, parent, child):
        new = cls()
        for prop in cls.MERGE_PROPERTIES:
            cval = getattr(child, prop)
            if cval is not GraphicsStyle.INHERIT:
                setattr(new, prop, cval)
            else:
                setattr(new, prop, getattr(parent, prop))

        return new

    @property
    def paint_rule(self):
        return getattr(self, "_paint_rule", GraphicsStyle.INHERIT)

    @paint_rule.setter
    def paint_rule(self, new):
        if new is None:
            self._paint_rule = PathPaintRule.DONT_PAINT
        if new is GraphicsStyle.INHERIT:
            self._paint_rule = new
        else:
            self._paint_rule = PathPaintRule.coerce(new)

    @property
    def auto_close(self):
        return getattr(self, "_auto_close", GraphicsStyle.INHERIT)

    @auto_close.setter
    def auto_close(self, new):
        if new not in {True, False, GraphicsStyle.INHERIT}:
            raise ValueError(
                f"auto_close must be a bool or GraphicsStyle.INHERIT, not {new}"
            )

        self._auto_close = new

    @property
    def intersection_rule(self):
        return getattr(self, "_intersection_rule", GraphicsStyle.INHERIT)

    @intersection_rule.setter
    def intersection_rule(self, new):
        # don't allow None for this one.
        if new is GraphicsStyle.INHERIT:
            self._intersection_rule = new
        else:
            self._intersection_rule = IntersectionRule.coerce(new)

    @property
    def fill_color(self):
        return getattr(self, "_fill_color", GraphicsStyle.INHERIT)

    @fill_color.setter
    def fill_color(self, color):
        if isinstance(color, str):
            color = color_from_hex_string(color)

        if isinstance(color, (DeviceRGB, DeviceGray, DeviceCMYK)):
            self._fill_color = color
            # strip opacity
            # self._fill_color = color.__class__(*color.colors)
            if color.a is not None:
                self.fill_opacity = color.a

        elif (color is None) or (color is GraphicsStyle.INHERIT):
            self._fill_color = color

        else:
            raise TypeError(f"{color} doesn't look like a drawing color")

    @property
    def fill_opacity(self):
        return getattr(self, PDFStyleKeys.FILL_ALPHA.value, GraphicsStyle.INHERIT)

    @fill_opacity.setter
    def fill_opacity(self, new):
        if new not in {None, GraphicsStyle.INHERIT}:
            _check_range(new)

        setattr(self, PDFStyleKeys.FILL_ALPHA.value, new)

    @property
    def stroke_color(self):
        return getattr(self, "_stroke_color", GraphicsStyle.INHERIT)

    @stroke_color.setter
    def stroke_color(self, color):
        if isinstance(color, str):
            color = color_from_hex_string(color)

        if isinstance(color, (DeviceRGB, DeviceGray, DeviceCMYK)):
            self._stroke_color = color
            if color.a is not None:
                self.stroke_opacity = color.a

        elif (color is None) or (color is GraphicsStyle.INHERIT):
            self._stroke_color = color

        else:
            raise TypeError(f"{color} doesn't look like a drawing color")

    @property
    def stroke_opacity(self):
        return getattr(self, PDFStyleKeys.STROKE_ALPHA.value, GraphicsStyle.INHERIT)

    @stroke_opacity.setter
    def stroke_opacity(self, new):
        if new not in {None, GraphicsStyle.INHERIT}:
            _check_range(new)

        setattr(self, PDFStyleKeys.STROKE_ALPHA.value, new)

    @property
    def blend_mode(self):
        return getattr(self, PDFStyleKeys.BLEND_MODE.value, GraphicsStyle.INHERIT)

    @blend_mode.setter
    def blend_mode(self, value):
        if value is GraphicsStyle.INHERIT:
            setattr(self, PDFStyleKeys.BLEND_MODE.value, value)
        else:
            setattr(self, PDFStyleKeys.BLEND_MODE.value, BlendMode.coerce(value).value)

    @property
    def stroke_width(self):
        return getattr(self, PDFStyleKeys.STROKE_WIDTH.value, GraphicsStyle.INHERIT)

    @stroke_width.setter
    def stroke_width(self, width):
        if not isinstance(
            width,
            (int, float, decimal.Decimal, type(None), type(GraphicsStyle.INHERIT)),
        ):
            raise TypeError(f"stroke_width must be a number, not {type(width)}")

        setattr(self, PDFStyleKeys.STROKE_WIDTH.value, width)

    @property
    def stroke_cap_style(self):
        return getattr(self, PDFStyleKeys.STROKE_CAP_STYLE.value, GraphicsStyle.INHERIT)

    @stroke_cap_style.setter
    def stroke_cap_style(self, value):
        if value is GraphicsStyle.INHERIT:
            setattr(self, PDFStyleKeys.STROKE_CAP_STYLE.value, value)
        else:
            setattr(
                self, PDFStyleKeys.STROKE_CAP_STYLE.value, StrokeCapStyle.coerce(value)
            )

    @property
    def stroke_join_style(self):
        return getattr(
            self, PDFStyleKeys.STROKE_JOIN_STYLE.value, GraphicsStyle.INHERIT
        )

    @stroke_join_style.setter
    def stroke_join_style(self, value):
        if value is GraphicsStyle.INHERIT:
            setattr(self, PDFStyleKeys.STROKE_JOIN_STYLE.value, value)
        else:
            setattr(
                self,
                PDFStyleKeys.STROKE_JOIN_STYLE.value,
                StrokeJoinStyle.coerce(value),
            )

    @property
    def stroke_miter_limit(self):
        return getattr(
            self, PDFStyleKeys.STROKE_MITER_LIMIT.value, GraphicsStyle.INHERIT
        )

    @stroke_miter_limit.setter
    def stroke_miter_limit(self, value):
        if (value is GraphicsStyle.INHERIT) or isinstance(
            value, (int, float, decimal.Decimal)
        ):
            setattr(self, PDFStyleKeys.STROKE_MITER_LIMIT.value, value)
        else:
            raise TypeError(f"{value} is not a number")

    @property
    def stroke_dash_pattern(self):
        result = getattr(
            self, PDFStyleKeys.STROKE_DASH_PATTERN.value, GraphicsStyle.INHERIT
        )
        if isinstance(result, tuple):
            return result[0]
        return result

    @stroke_dash_pattern.setter
    def stroke_dash_pattern(self, value):
        if isinstance(value, (float, int)):
            value = (value,)

        if isinstance(value, (list, tuple)):
            result = getattr(
                self, PDFStyleKeys.STROKE_DASH_PATTERN.value, GraphicsStyle.INHERIT
            )
            if isinstance(result, tuple):
                new = (tuple(value), result[1])
            else:
                new = (tuple(value), 0)
            setattr(self, PDFStyleKeys.STROKE_DASH_PATTERN.value, new)
        elif value is None:
            setattr(self, PDFStyleKeys.STROKE_DASH_PATTERN.value, ((), 0))
        elif value is GraphicsStyle.INHERIT:
            setattr(self, PDFStyleKeys.STROKE_DASH_PATTERN.value, value)
        else:
            raise TypeError(f"{value} cannot be interpreted as a dash pattern")

    @property
    def stroke_dash_phase(self):
        result = getattr(
            self, PDFStyleKeys.STROKE_DASH_PATTERN.value, GraphicsStyle.INHERIT
        )
        if isinstance(result, tuple):
            return result[1]

        return result

    @stroke_dash_phase.setter
    def stroke_dash_phase(self, value):
        if isinstance(value, (float, int)):
            result = getattr(
                self, PDFStyleKeys.STROKE_DASH_PATTERN.value, GraphicsStyle.INHERIT
            )
            if isinstance(result, tuple):
                setattr(
                    self, PDFStyleKeys.STROKE_DASH_PATTERN.value, (result[0], value)
                )
            else:
                raise ValueError("no dash pattern to set the phase on")
        elif value is GraphicsStyle.INHERIT:
            pass
        else:
            raise TypeError(f"{value} isn't a number")

    def to_pdf_dict(self):
        result = OrderedDict()
        result[Name("Type")] = Name("ExtGState")

        for key in PDFStyleKeys:
            value = getattr(self, key.value, GraphicsStyle.INHERIT)

            if (value is not GraphicsStyle.INHERIT) and (value is not None):
                # None is used for out-of-band signaling on these, e.g. a stroke_width
                # of None doesn't need to land here because it signals the
                # PathPaintRule auto resolution only.
                result[key.value] = value

        return render_pdf_primitive(result)

    def resolve_paint_rule(self):
        """
        Resolve `PathPaintRule.AUTO` to a real paint rule based on this style.

        Returns:
            the resolved `PathPaintRule`.
        """
        if self.paint_rule is PathPaintRule.AUTO:
            want = set()
            if self.stroke_width is not None and self.stroke_color is not None:
                want.add("stroke")
            if self.fill_color is not None:
                want.add("fill")
                # we need to guarantee that this will not be None. The default will
                # be "nonzero".
                assert self.intersection_rule is not None
                want.add(self.intersection_rule)

            try:
                rule = self._PAINT_RULE_LOOKUP[frozenset(want)]
            except KeyError:
                # don't default to DONT_PAINT because that's almost certainly not a very
                # good default.
                rule = PathPaintRule.STROKE_FILL_NONZERO

        else:
            rule = self.paint_rule

        return rule


def _render_move(pt):
    return f"{pt.render()} m"


def _render_line(pt):
    return f"{pt.render()} l"


def _render_curve(ctrl1, ctrl2, end):
    return f"{ctrl1.render()} {ctrl2.render()} {end.render()} c"


class Move(NamedTuple):
    pt: Point

    @property
    def end_point(self):
        return self.pt

    def render(self, path_gsds, style, last_item):
        # pylint: disable=unused-argument
        return _render_move(self.pt), self

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        # pylint: disable=unused-argument
        rendered, resolved = self.render(path_gsds, style, last_item)
        debug_stream.write(str(self) + "\n")

        return rendered, resolved


class RelativeMove(NamedTuple):
    pt: Point

    def render(self, path_gsds, style, last_item):
        # pylint: disable=unused-argument
        point = last_item.end_point + self.pt
        return _render_move(point), Move(point)

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        # pylint: disable=unused-argument
        rendered, resolved = self.render(path_gsds, style, last_item)
        debug_stream.write(f"{self} resolved to {resolved}\n")

        return rendered, resolved


class Line(NamedTuple):
    pt: Point

    @property
    def end_point(self):
        return self.pt

    def render(self, path_gsds, style, last_item):
        # pylint: disable=unused-argument
        return _render_line(self.pt), self

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        # pylint: disable=unused-argument
        rendered, resolved = self.render(path_gsds, style, last_item)
        debug_stream.write(str(self) + "\n")

        return rendered, resolved


class RelativeLine(NamedTuple):
    pt: Point

    def render(self, path_gsds, style, last_item):
        # pylint: disable=unused-argument
        point = last_item.end_point + self.pt
        return _render_line(point), Line(point)

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        # pylint: disable=unused-argument
        rendered, resolved = self.render(path_gsds, style, last_item)
        debug_stream.write(f"{self} resolved to {resolved}\n")

        return rendered, resolved


class HorizontalLine(NamedTuple):
    x: Number

    def render(self, path_gsds, style, last_item):
        # pylint: disable=unused-argument
        end_point = Point(x=self.x, y=last_item.end_point.y)
        return _render_line(end_point), Line(end_point)

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        # pylint: disable=unused-argument
        rendered, resolved = self.render(path_gsds, style, last_item)
        debug_stream.write(f"{self} resolved to {resolved}\n")

        return rendered, resolved


class RelativeHorizontalLine(NamedTuple):
    x: Number

    def render(self, path_gsds, style, last_item):
        # pylint: disable=unused-argument
        end_point = Point(x=last_item.end_point.x + self.x, y=last_item.end_point.y)
        return _render_line(end_point), Line(end_point)

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        # pylint: disable=unused-argument
        rendered, resolved = self.render(path_gsds, style, last_item)
        debug_stream.write(f"{self} resolved to {resolved}\n")

        return rendered, resolved


class VerticalLine(NamedTuple):
    y: Number

    def render(self, path_gsds, style, last_item):
        # pylint: disable=unused-argument
        end_point = Point(x=last_item.end_point.x, y=self.y)
        return _render_line(end_point), Line(end_point)

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        # pylint: disable=unused-argument
        rendered, resolved = self.render(path_gsds, style, last_item)
        debug_stream.write(f"{self} resolved to {resolved}\n")

        return rendered, resolved


class RelativeVerticalLine(NamedTuple):
    y: Number

    def render(self, path_gsds, style, last_item):
        # pylint: disable=unused-argument
        end_point = Point(x=last_item.end_point.x, y=last_item.end_point.y + self.y)
        return _render_line(end_point), Line(end_point)

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        # pylint: disable=unused-argument
        rendered, resolved = self.render(path_gsds, style, last_item)
        debug_stream.write(f"{self} resolved to {resolved}\n")

        return rendered, resolved


class BezierCurve(NamedTuple):
    c1: Point
    c2: Point
    end: Point

    @property
    def end_point(self):
        return self.end

    def render(self, path_gsds, style, last_item):
        # pylint: disable=unused-argument
        return (_render_curve(self.c1, self.c2, self.end), self)

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        # pylint: disable=unused-argument
        rendered, resolved = self.render(path_gsds, style, last_item)
        debug_stream.write(str(self) + "\n")

        return rendered, resolved


class RelativeBezierCurve(NamedTuple):
    c1: Point
    c2: Point
    end: Point

    def render(self, path_gsds, style, last_item):
        # pylint: disable=unused-argument
        last_point = last_item.end_point

        c1 = last_point + self.c1
        c2 = last_point + self.c2
        end = last_point + self.end

        return (
            _render_curve(c1, c2, end),
            BezierCurve(c1=c1, c2=c2, end=end),
        )

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        # pylint: disable=unused-argument
        rendered, resolved = self.render(path_gsds, style, last_item)
        debug_stream.write(f"{self} resolved to {resolved}\n")

        return rendered, resolved


class QuadraticBezierCurve(NamedTuple):
    ctrl: Point
    end: Point

    @property
    def end_point(self):
        return self.end

    def to_cubic_curve(self, start_point):
        ctrl = self.ctrl
        end = self.end

        ctrl1 = Point(
            x=start_point.x + 2 * (ctrl.x - start_point.x) / 3,
            y=start_point.y + 2 * (ctrl.y - start_point.y) / 3,
        )
        ctrl2 = Point(
            x=end.x + 2 * (ctrl.x - end.x) / 3,
            y=end.y + 2 * (ctrl.y - end.y) / 3,
        )

        return BezierCurve(ctrl1, ctrl2, end)

    def render(self, path_gsds, style, last_item):
        # pylint: disable=unused-argument
        return (
            self.to_cubic_curve(last_item.end_point).render(
                path_gsds, style, last_item
            )[0],
            self,
        )

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        # pylint: disable=unused-argument
        rendered, resolved = self.render(path_gsds, style, last_item)
        debug_stream.write(
            f"{self} resolved to {self.to_cubic_curve(last_item.end_point)}\n"
        )

        return rendered, resolved


class RelativeQuadraticBezierCurve(NamedTuple):
    ctrl: Point
    end: Point

    def render(self, path_gsds, style, last_item):
        # pylint: disable=unused-argument
        last_point = last_item.end_point

        ctrl = last_point + self.ctrl
        end = last_point + self.end

        absolute = QuadraticBezierCurve(ctrl=ctrl, end=end)
        return absolute.render(path_gsds, style, last_item)

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        # pylint: disable=unused-argument
        rendered, resolved = self.render(path_gsds, style, last_item)
        debug_stream.write(
            f"{self} resolved to {resolved} "
            f"then to {resolved.to_cubic_curve(last_item.end_point)}\n"
        )

        return rendered, resolved


class Arc(NamedTuple):
    radii: Point
    rotation: Number
    large: bool
    sweep: bool
    end: Point

    @staticmethod
    def subdivde_sweep(sweep_angle):
        sweep_angle = abs(sweep_angle)
        sweep_left = sweep_angle

        quarterturn = math.pi / 2
        chunks = math.ceil(sweep_angle / quarterturn)

        sweep_segment = sweep_angle / chunks
        cos_t = math.cos(sweep_segment)
        sin_t = math.sin(sweep_segment)
        kappa = 4 / 3 * math.tan(sweep_segment / 4)

        ctrl1 = Point(1, kappa)
        ctrl2 = Point(cos_t + kappa * sin_t, sin_t - kappa * cos_t)
        end = Point(cos_t, sin_t)

        for _ in range(chunks):
            offset = sweep_angle - sweep_left

            transform = Transform.rotation(offset)
            yield ctrl1 @ transform, ctrl2 @ transform, end @ transform

            sweep_left -= sweep_segment

    def _approximate_arc(self, last_item):
        radii = self.radii

        reverse = Transform.rotation(-self.rotation)
        forward = Transform.rotation(self.rotation)

        prime = ((last_item.end_point - self.end) * 0.5) @ reverse

        lam_da = (prime.x / radii.x) ** 2 + (prime.y / radii.y) ** 2

        if lam_da > 1:
            radii = Point(x=(lam_da ** 0.5) * radii.x, y=(lam_da ** 0.5) * radii.y)

        sign = (self.large != self.sweep) - (self.large == self.sweep)
        rxry2 = (radii.x * radii.y) ** 2
        rxpy2 = (radii.x * prime.y) ** 2
        rypx2 = (radii.y * prime.x) ** 2

        centerprime = (
            sign
            * math.sqrt(round(rxry2 - rxpy2 - rypx2, 8) / (rxpy2 + rypx2))
            * Point(
                x=radii.x * prime.y / radii.y,
                y=-radii.y * prime.x / radii.x,
            )
        )

        center = (centerprime @ forward) + ((last_item.end_point + self.end) * 0.5)

        arcstart = Point(
            x=(prime.x - centerprime.x) / radii.x,
            y=(prime.y - centerprime.y) / radii.y,
        )
        arcend = Point(
            x=(-prime.x - centerprime.x) / radii.x,
            y=(-prime.y - centerprime.y) / radii.y,
        )

        theta = Point(1, 0).angle(arcstart)
        deltatheta = arcstart.angle(arcend)

        if (self.sweep is False) and (deltatheta > 0):
            deltatheta -= math.tau
        elif (self.sweep is True) and (deltatheta < 0):
            deltatheta += math.tau

        sweep_sign = (deltatheta >= 0) - (deltatheta < 0)
        final_tf = (
            Transform.scaling(x=1, y=sweep_sign)  # flip negative sweeps
            .rotate(theta)  # rotate start of arc to correct position
            .scale(radii.x, radii.y)  # scale unit circle into the final ellipse shape
            .rotate(self.rotation)  # rotate the ellipse the specified angle
            .translate(center.x, center.y)  # translate to the final coordinates
        )

        curves = []

        for ctrl1, ctrl2, end in self.subdivde_sweep(deltatheta):
            curves.append(
                BezierCurve(ctrl1 @ final_tf, ctrl2 @ final_tf, end @ final_tf)
            )

        return curves

    def render(self, path_gsds, style, last_item):
        # pylint: disable=unused-argument
        curves = self._approximate_arc(last_item)

        if not curves:
            return "", last_item

        return (
            " ".join(
                curve.render(path_gsds, style, prev)[0]
                for prev, curve in zip([last_item, *curves[:-1]], curves)
            ),
            curves[-1],
        )

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        # pylint: disable=unused-argument
        curves = self._approximate_arc(last_item)

        debug_stream.write(f"{self} resolved to:\n")
        if not curves:
            debug_stream.write(pfx + " └─ nothing\n")
            return "", last_item

        previous = [last_item]
        for curve in curves[:-1]:
            previous.append(curve)
            debug_stream.write(pfx + f" ├─ {curve}\n")
        debug_stream.write(pfx + f" └─ {curves[-1]}\n")

        return (
            " ".join(
                curve.render(path_gsds, style, prev)[0]
                for prev, curve in zip(previous, curves)
            ),
            curves[-1],
        )


class RelativeArc(NamedTuple):
    radii: Point
    rotation: Number
    large: bool
    sweep: bool
    end: Point

    def render(self, path_gsds, style, last_item):
        # pylint: disable=unused-argument
        return Arc(
            self.radii,
            self.rotation,
            self.large,
            self.sweep,
            last_item.end_point + self.end,
        ).render(path_gsds, style, last_item)

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        # pylint: disable=unused-argument
        # newline is intentionally missing here
        debug_stream.write(f"{self} resolved to ")

        return Arc(
            self.radii,
            self.rotation,
            self.large,
            self.sweep,
            last_item.end_point + self.end,
        ).render_debug(path_gsds, style, last_item, debug_stream, pfx)


class Rectangle(NamedTuple):
    org: Point
    size: Point

    def render(self, path_gsds, style, last_item):
        # pylint: disable=unused-argument
        return (f"{self.org.render()} {self.size.render()} re", Line(self.org))

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        # pylint: disable=unused-argument
        rendered, resolved = self.render(path_gsds, style, last_item)
        debug_stream.write(f"{self} resolved to {rendered}\n")

        return rendered, resolved


class ImplicitClose(NamedTuple):
    def render(self, path_gsds, style, last_item):
        # pylint: disable=unused-argument,no-self-use
        if style.auto_close:
            return "h", last_item

        return "", last_item

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        # pylint: disable=unused-argument
        rendered, resolved = self.render(path_gsds, style, last_item)
        debug_stream.write(f"{self} resolved to {rendered}\n")

        return rendered, resolved


class Close(NamedTuple):
    def render(self, path_gsds, style, last_item):
        # pylint: disable=unused-argument,no-self-use
        return "h", last_item

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        # pylint: disable=unused-argument
        rendered, resolved = self.render(path_gsds, style, last_item)
        debug_stream.write(str(self) + "\n")

        return rendered, resolved


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

    @staticmethod
    def _setup_render_prereqs(first_point, scale, height):
        style = GraphicsStyle()
        style.auto_close = True
        style.paint_rule = PathPaintRule.AUTO
        style.intersection_rule = IntersectionRule.NONZERO

        last_item = Move(first_point)
        scale, last_item = (
            Transform.scaling(x=1, y=-1)
            .about(x=0, y=height / 2)
            .scale(scale)
            .render(last_item)
        )

        # we use an OrderedDict here so that the path_gsds output ordering is
        # deterministic for a given input and also inherently deduplicated.
        path_gsds = OrderedDict()
        render_list = ["q", scale]

        return render_list, path_gsds, style, last_item

    def render(self, first_point, scale, height):
        if not self._subitems:
            return "", OrderedDict()

        render_list, path_gsds, style, last_item = self._setup_render_prereqs(
            first_point, scale, height
        )

        for item in self._subitems:
            rendered, last_item = item.render(path_gsds, style, last_item)
            if rendered:
                render_list.append(rendered)

        render_list.append("Q")

        return " ".join(render_list), path_gsds

    def render_debug(self, first_point, scale, height, debug_stream):
        render_list, path_gsds, style, last_item = self._setup_render_prereqs(
            first_point, scale, height
        )

        debug_stream.write("ROOT\n")
        for child in self._subitems[:-1]:
            debug_stream.write(" ├─ ")
            rendered = child.render_debug(
                path_gsds, style, last_item, debug_stream, " │  "
            )
            if rendered:
                render_list.append(rendered)

        if self._subitems:
            debug_stream.write(" └─ ")
            rendered, last_item = self._subitems[-1].render_debug(
                path_gsds, style, last_item, debug_stream, "    "
            )
            if rendered:
                render_list.append(rendered)

            render_list.append("Q")

            # print(render_list)
            return " ".join(render_list), path_gsds

        return "", OrderedDict()


class PaintedPath:
    def __init__(self, x=0, y=0):
        self._root_graphics_context = GraphicsContext()
        self._graphics_context = self._root_graphics_context

        self._closed = True
        self._close_context = self._graphics_context

        self.move_to(x, y)

    @property
    def style(self):
        """The `GraphicsStyle` applied to all elements of this path."""
        return self._root_graphics_context.style

    @property
    def transform(self):
        return self._root_graphics_context.transform

    @transform.setter
    def transform(self, tf):
        self._root_graphics_context.transform = tf

    @property
    def auto_close(self):
        return self.style.auto_close

    @auto_close.setter
    def auto_close(self, should):
        self.style.auto_close = should

    @property
    def paint_rule(self):
        return self.style.paint_rule

    @paint_rule.setter
    def paint_rule(self, style):
        self.style.paint_rule = style

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

    def add_path_element(self, item):
        if self._starter_move is not None:
            self._closed = False

            self._graphics_context.add_item(self._starter_move)
            self._close_context = self._graphics_context
            self._starter_move = None

        self._graphics_context.add_item(item)

    def rectangle(self, x, y, w, h, rx=0, ry=0):
        """
        Append a rectangle as a closed subpath to the current path.
        """

        if (rx == 0) or (ry == 0):
            self._insert_implicit_close_if_open()
            self.add_path_element(Rectangle(Point(x, y), Point(w, h)))
        else:
            rx = abs(rx)
            ry = abs(ry)
            self.move_to(x + rx, y)
            self.line_to(x + w - rx, y)
            self.arc_to(rx, ry, 0, False, True, x + w, y + ry)
            self.line_to(x + w, y + h - ry)
            self.arc_to(rx, ry, 0, False, True, x + w - rx, y + h)
            self.line_to(x + rx, y + h)
            self.arc_to(rx, ry, 0, False, True, x, y + h - ry)
            self.line_to(x, y + ry)
            self.arc_to(rx, ry, 0, False, True, x + rx, y)
            self.close()

        return self

    def circle(self, cx, cy, r):
        """
        Append a circle as a closed subpath to the current path.
        """
        return self.ellipse(cx, cy, r, r)

    def ellipse(self, cx, cy, rx, ry):
        """
        Append an ellipse as a closed subpath to the current path.
        """
        rx = abs(rx)
        ry = abs(ry)

        # this isn't the most efficient way to do this, computationally, but it's
        # internally consistent.
        self.move_to(cx + rx, cy)
        self.arc_to(rx, ry, 0, False, True, cx, cy + ry)
        self.arc_to(rx, ry, 0, False, True, cx - rx, cy)
        self.arc_to(rx, ry, 0, False, True, cx, cy - ry)
        self.arc_to(rx, ry, 0, False, True, cx + rx, cy)
        self.close()

        return self

    def move_to(self, x, y):
        """
        Start a new subpath or move the path starting point.

        If no path elements have been added yet, this will change the path starting
        point. If path elements have been added, this will insert an implicit close in
        order to start a new subpath.

        Args:
            x (Number): abscissa of the (sub)path starting point.
            y (Number): ordinate of the (sub)path starting point.

        Returns:
            The path, to allow chaining method calls.

        """
        self._insert_implicit_close_if_open()
        self._starter_move = Move(Point(x, y))
        return self

    def move_relative(self, x, y):
        """
        Start a new subpath or move the path start point relative to the previous point.

        If no path elements have been added yet, this will change the path starting
        point. If path elements have been added, this will insert an implicit close in
        order to start a new subpath.

        This will overwrite an absolute move_to as long as no non-move path items have
        been appended. The relative position is resolved from the previous item when
        the path is being rendered, or from 0, 0 if it is the first item.

        Args:
            x (Number): abscissa of the (sub)path starting point relative to the.
            y (Number): ordinate of the (sub)path starting point relative to the.
        """

        self._insert_implicit_close_if_open()
        self._starter_move = RelativeMove(Point(x, y))
        return self

    def line_to(self, x, y):
        """
        Append a straight line to this path.

        Args:
            x (Number): abscissa the line's end point.
            y (Number): ordinate of the line's end point.

        Returns:
            The path, to allow chaining method calls.
        """
        self.add_path_element(Line(Point(x, y)))
        return self

    def line_relative(self, dx, dy):
        """
        Append a straight line whose end is computed as an offset from the end of the
        previous path element.

        Args:
            x (Number): abscissa the line's end point relative to the end point of the
                previous path element.
            y (Number): ordinate of the line's end point relative to the end point of
                the previous path element.

        Returns:
            The path, to allow chaining method calls.
        """
        self.add_path_element(RelativeLine(Point(dx, dy)))
        return self

    def horizontal_line_to(self, x):
        """
        Append a straight horizontal line to the given abscissa. The ordinate is
        retrieved from the end point of the previous path element.

        Args:
            x (Number): abscissa of the line's end point.

        Returns:
            The path, to allow chaining method calls.
        """
        self.add_path_element(HorizontalLine(x))
        return self

    def horizontal_line_relative(self, dx):
        """
        Append a straight horizontal line to the given offset from the previous path
        element. The ordinate is retrieved from the end point of the previous path
        element.

        Args:
            x (Number): abscissa of the line's end point relative to the end point of
                the previous path element.

        Returns:
            The path, to allow chaining method calls.
        """
        self.add_path_element(RelativeHorizontalLine(dx))
        return self

    def vertical_line_to(self, y):
        """
        Append a straight vertical line to the given ordinate. The abscissa is
        retrieved from the end point of the previous path element.

        Args:
            y (Number): ordinate of the line's end point.

        Returns:
            The path, to allow chaining method calls.
        """
        self.add_path_element(VerticalLine(y))
        return self

    def vertical_line_relative(self, dy):
        """
        Append a straight vertical line to the given offset from the previous path
        element. The abscissa is retrieved from the end point of the previous path
        element.

        Args:
            y (Number): ordinate of the line's end point relative to the end point of
                the previous path element.

        Returns:
            The path, to allow chaining method calls.
        """
        self.add_path_element(RelativeVerticalLine(dy))
        return self

    def curve_to(self, x1, y1, x2, y2, x3, y3):
        """
        Append a cubic Bézier curve to this path.

        Args:
            x1 (Number): abscissa of the first control point
            y1 (Number): ordinate of the first control point
            x2 (Number): abscissa of the second control point
            y2 (Number): ordinate of the second control point
            x3 (Number): abscissa of the end point
            y3 (Number): ordinate of the end point

        Returns:
            The path, to allow chaining method calls.
        """
        ctrl1 = Point(x1, y1)
        ctrl2 = Point(x2, y2)
        end = Point(x3, y3)

        self.add_path_element(BezierCurve(ctrl1, ctrl2, end))
        return self

    def curve_relative(self, dx1, dy1, dx2, dy2, dx3, dy3):
        """
        Append a cubic Bézier curve whose points are expressed relative to the
        end point of the previous path element.

        E.g. with a start point of (0, 0), given (1, 1), (2, 2), (3, 3), the output
        curve would have the points:

        (0, 0) c1 (1, 1) c2 (3, 3) e (6, 6)

        Args:
            dx1 (Number): abscissa of the first control point relative to the end point
                of the previous path element
            dy1 (Number): ordinate of the first control point relative to the end point
                of the previous path element
            dx2 (Number): abscissa offset of the second control point relative to the
                first control point
            dy2 (Number): ordinate offset of the second control point relative to the
                first control point
            dx3 (Number): abscissa offset of the end point relative to the second
                control point
            dy3 (Number): ordinate offset of the end point relative to the second
                control point

        Returns:
            The path, to allow chaining method calls.
        """
        c1d = Point(dx1, dy1)
        c2d = Point(dx2, dy2)
        end = Point(dx3, dy3)

        self.add_path_element(RelativeBezierCurve(c1d, c2d, end))
        return self

    def quadratic_bezier_to(self, x1, y1, x2, y2):
        """
        Append a cubic Bézier curve mimicking the specified quadratic Bézier curve.
        """
        ctrl = Point(x1, y1)
        end = Point(x2, y2)
        self.add_path_element(QuadraticBezierCurve(ctrl, end))
        return self

    def quadratic_bezier_relative(self, x1, y1, x2, y2):
        """
        Append a cubic Bézier curve mimicking the specified quadratic Bézier curve.
        """
        ctrl = Point(x1, y1)
        end = Point(x2, y2)
        self.add_path_element(RelativeQuadraticBezierCurve(ctrl, end))
        return self

    def arc_to(self, rx, ry, rotation, large_arc, positive_sweep, x, y):
        """
        Append an elliptical arc from the end of the previous path point to the
        specified end point.

        The arc is approximated using Bézier curves, so it is not perfectly accurate.
        However, the error is small enough to not be noticeable at any reasonable
        (and even most unreasonable) scales, with a worst-case deviation of around 3‱.

        Notes:
            - The signs of the radii arguments (`rx` and `ry`) are ignored (i.e. their
              absolute values are used instead).
            - If either radius is 0, then a straight line will be emitted instead of an
              arc.
            - If the radii are too small for the arc to reach from the current point to
              the specified end point (`x` and `y`), then they will be proportionally
              scaled up until they are big enough, which will always result in a
              half-ellipse arc (i.e. an 180 degree sweep)

        Args:
            rx (Number): radius in the x-direction.
            ry (Number): radius in the y-direction.
            rotation (Number): angle (in degrees) that the arc should be rotated
                clockwise from the principle axes. This parameter does not have
                a visual effect in the case that `rx == ry`.
            large_arc (bool): if True, the arc will cover a sweep angle of at least 180
                degrees. Otherwise, the sweep angle will be at most 180 degrees.
            positive_sweep (bool): if True, the arc will be swept over a positive angle,
                i.e. clockwise. Otherwise, the arc will be swept over a negative
                angle.
            x (Number): ordinate of the arc's end point.
            y (Number): abscissa of the arc's end point.
        """

        if rx == 0 or ry == 0:
            return self.line_to(x, y)

        radii = Point(abs(rx), abs(ry))
        large_arc = bool(large_arc)
        rotation = math.radians(rotation)
        positive_sweep = bool(positive_sweep)
        end = Point(x, y)

        self.add_path_element(Arc(radii, rotation, large_arc, positive_sweep, end))
        return self

    def arc_relative(self, rx, ry, rotation, large_arc, positive_sweep, dx, dy):
        """
        Append an elliptical arc from the end of the previous path point to an offset
        point.

        The arc is approximated using Bézier curves, so it is not perfectly accurate.
        However, the error is small enough to not be noticeable at any reasonable
        (and even most unreasonable) scales, with a worst-case deviation of around 3‱.

        Notes:
            - The signs of the radii arguments (`rx` and `ry`) are ignored (i.e. their
              absolute values are used instead).
            - If either radius is 0, then a straight line will be emitted instead of an
              arc.
            - If the radii are too small for the arc to reach from the current point to
              the specified end point (`x` and `y`), then they will be proportionally
              scaled up until they are big enough, which will always result in a
              half-ellipse arc (i.e. an 180 degree sweep)

        Args:
            rx (Number): radius in the x-direction.
            ry (Number): radius in the y-direction.
            rotation (Number): angle (in degrees) that the arc should be rotated
                clockwise from the principle axes. This parameter does not have
                a visual effect in the case that `rx == ry`.
            large_arc (bool): if True, the arc will cover a sweep angle of at least 180
                degrees. Otherwise, the sweep angle will be at most 180 degrees.
            positive_sweep (bool): if True, the arc will be swept over a positive angle,
                i.e. clockwise. Otherwise, the arc will be swept over a negative
                angle.
            dx (Number): ordinate of the arc's end point relative to the end point of
                the previous path element.
            dy (Number): abscissa of the arc's end point relative to the end point of
                the previous path element.
        """
        if rx == 0 or ry == 0:
            return self.line_relative(dx, dy)

        radii = Point(abs(rx), abs(ry))
        large_arc = bool(large_arc)
        rotation = math.radians(rotation)
        positive_sweep = bool(positive_sweep)
        end = Point(dx, dy)

        self.add_path_element(
            RelativeArc(radii, rotation, large_arc, positive_sweep, end)
        )
        return self

    def close(self):
        self.add_path_element(Close())
        self._closed = True
        self.move_relative(0, 0)

    def _insert_implicit_close_if_open(self):
        if not self._closed:
            self._close_context.add_item(ImplicitClose())
            self._close_context = self._graphics_context
            self._closed = True

    def render(self, path_gsds, style, last_item, debug_stream=None, pfx=None):
        self._insert_implicit_close_if_open()

        render_list, last_item = self._root_graphics_context.build_render_list(
            path_gsds, style, last_item, debug_stream, pfx
        )

        paint_rule = GraphicsStyle.merge(style, self.style).resolve_paint_rule()

        render_list.insert(-1, paint_rule.value)

        return " ".join(render_list), last_item

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        return self.render(path_gsds, style, last_item, debug_stream, pfx)


class ClippingPath(PaintedPath):
    # because clipping paths can be painted, we inherit from PaintedPath. However, when
    # setting the styling on the clipping path, those values will also be applied to
    # the PaintedPath the ClippingPath is applied to unless they are explicitly set for
    # that painted path. This is not ideal, but there's no way to really fix it from
    # the PDF rendering model, and trying to track the appropriate state/defaults seems
    # similarly error prone.

    # In general, the expectation is that painted clipping paths are likely to be very
    # uncommon, so it's an edge case that isn't worth worrying too much about.

    def __init__(self, x=0, y=0):
        super().__init__(x=x, y=y)
        self.paint_rule = PathPaintRule.DONT_PAINT

    # def __deepcopy__(self, memo):
    #     copied = ClippingPath(self._intersection_rule, self._paint_style)
    #     copied._root_graphics_context = copy.deepcopy(self._root_graphics_context, memo)
    #     copied._graphics_context = copied._root_graphics_context
    #     copied._closed = self._closed
    #     return copied

    def render(self, path_gsds, style, last_item, debug_stream=None, pfx=None):
        # painting the clipping path outside of its root graphics context allows it to
        # be transformed without affecting the transform of the graphics context of the
        # path it is being used to clip. This is because, unlike all of the other style
        # settings, transformations immediately affect the points following them,
        # rather than only affecting them at painting time. stroke settings and color
        # settings are applied only at paint time.

        render_list, last_item = self._root_graphics_context.build_render_list(
            path_gsds, style, last_item, _push_stack=False
        )

        style = GraphicsStyle.merge(style, self.style)
        # we should never get a collision error here
        intersection_rule = style.intersection_rule
        if style.intersection_rule == GraphicsStyle.INHERIT:
            intersection_rule = ClippingPathIntersectionRule.NONZERO
        else:
            intersection_rule = ClippingPathIntersectionRule[intersection_rule.name]

        paint_rule = style.resolve_paint_rule()

        if debug_stream:
            ...

        render_list.append(intersection_rule.value)
        render_list.append(paint_rule.value)

        return " ".join(render_list), last_item

    def render_debug(self, path_gsds, style, last_item, debug_stream, pfx):
        return self.render(path_gsds, style, last_item, debug_stream, pfx)


class GraphicsContext:
    def __init__(self):
        self.style = GraphicsStyle()
        self.path_items = []

        self.transform = None

    @property
    def transform(self):
        return self._transform

    @transform.setter
    def transform(self, tf):
        self._transform = tf

    # def __deepcopy__(self, memo):
    #     copied = GraphicsContext()
    #     copied._style_items = copy.deepcopy(self._style_items, memo)
    #     copied.path_items = copy.deepcopy(self.path_items, memo)
    #     return copied

    def add_item(self, item):
        self.path_items.append(item)

    def merge(self, other_context):
        # TODO: merge styles?
        self.path_items.extend(other_context.path_items)

    def build_render_list(
        self, path_gsds, style, last_item, debug_stream=None, pfx=None, _push_stack=True
    ):
        render_list = []

        if self.path_items:
            if debug_stream is not None:
                debug_stream.write(f"{self.__class__.__name__}")

            style = GraphicsStyle.merge(style, self.style)

            if debug_stream is not None:
                styles_dbg = []
                for attr in GraphicsStyle.MERGE_PROPERTIES:
                    val = getattr(style, attr)
                    if val is not GraphicsStyle.INHERIT:
                        styles_dbg.append(f"{attr}: {val}")

                if styles_dbg:
                    debug_stream.write(" {\n")
                    for style_dbg_line in styles_dbg:
                        debug_stream.write(pfx + "    ")
                        debug_stream.write(style_dbg_line)
                        debug_stream.write("\n")

                    debug_stream.write(pfx + "}┐\n")
                else:
                    debug_stream.write("\n")

            sdict = _get_or_set_style_dict(style)
            if sdict is not None:
                path_gsds[sdict] = None
                render_list.append(f"{render_pdf_primitive(sdict)} gs")

            if debug_stream:
                for item in self.path_items[:-1]:
                    debug_stream.write(pfx + " ├─ ")
                    rendered, last_item = item.render_debug(
                        path_gsds, style, last_item, debug_stream, pfx + " │  "
                    )

                    if rendered:
                        render_list.append(rendered)

                debug_stream.write(pfx + " └─ ")
                rendered, last_item = self.path_items[-1].render_debug(
                    path_gsds, style, last_item, debug_stream, pfx + "    "
                )

                if rendered:
                    render_list.append(rendered)
            else:
                for item in self.path_items:
                    rendered, last_item = item.render(path_gsds, style, last_item)

                    if rendered:
                        render_list.append(rendered)

            NO_EMIT_SET = {None, GraphicsStyle.INHERIT}
            # we can't set color in the graphics state context dictionary, so we have to
            # manually inherit it and emit it here.
            fill_color = style.fill_color
            stroke_color = style.stroke_color
            dash_pattern = style.stroke_dash_pattern

            if fill_color not in NO_EMIT_SET:
                render_list.append(
                    " ".join(number_to_str(val) for val in fill_color.colors)
                    + f" {fill_color.OPERATOR.lower()}"
                )

            if stroke_color not in NO_EMIT_SET:
                render_list.append(
                    " ".join(number_to_str(val) for val in stroke_color.colors)
                    + f" {stroke_color.OPERATOR.upper()}"
                )

            # We perform this redundant drawing operation here (the dash pattern is also
            # emitted to the graphics state parameter dictionary for this path) because
            # macOS preview.app does not appear to render dash patterns specified in
            # the graphics state parameter dictionary. This was cross-referenced
            # against mupdf and adobe acrobat reader DC, which both do render as
            # expected, giving some assurance that it isn't a problem with the PDF
            # generation itself.
            if dash_pattern not in NO_EMIT_SET:
                render_list.append(
                    render_pdf_primitive(dash_pattern)
                    + f" {number_to_str(self.style.stroke_dash_phase)} d"
                )

            # insert transform before points
            if self.transform is not None:
                render_list.insert(0, self.transform.render(last_item)[0])

            if _push_stack:
                render_list.insert(0, "q")
                render_list.append("Q")

        return render_list, last_item

    def render(
        self, path_gsds, style, last_item, debug_stream=None, pfx=None, _push_stack=True
    ):
        render_list, last_item = self.build_render_list(
            path_gsds, style, last_item, debug_stream, pfx, _push_stack=_push_stack
        )

        return " ".join(render_list), last_item

    def render_debug(
        self, path_gsds, style, last_item, debug_stream, pfx, _push_stack=True
    ):
        return self.render(
            path_gsds, style, last_item, debug_stream, pfx, _push_stack=_push_stack
        )
