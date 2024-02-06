"""
Vector drawing: managing colors, graphics states, paths, transforms...

The contents of this module are internal to fpdf2, and not part of the public API.
They may change at any time without prior warning or any deprecation period,
in non-backward-compatible ways.
"""

import copy, decimal, math, re
from collections import OrderedDict
from collections.abc import Sequence
from contextlib import contextmanager
from typing import Optional, NamedTuple, Union

from .enums import (
    BlendMode,
    ClippingPathIntersectionRule,
    IntersectionRule,
    PathPaintRule,
    StrokeCapStyle,
    StrokeJoinStyle,
    PDFStyleKeys,
)
from .syntax import Name, Raw
from .util import escape_parens

__pdoc__ = {"force_nodocument": False}


def force_nodocument(item):
    """A decorator that forces pdoc not to document the decorated item (class or method)"""
    __pdoc__[item.__qualname__] = False
    return item


@force_nodocument
def force_document(item):
    """A decorator that forces pdoc to document the decorated item (class or method)"""
    __pdoc__[item.__qualname__] = True
    return item


# type alias:
Number = Union[int, float, decimal.Decimal]
NumberClass = (int, float, decimal.Decimal)


WHITESPACE = frozenset("\0\t\n\f\r ")
"""Characters PDF considers to be whitespace."""
EOL_CHARS = frozenset("\n\r")
"""Characters PDF considers to mark the end of a line."""
DELIMITERS = frozenset("()<>[]{}/%")
"""Special delimiter characters"""


STR_ESC = re.compile(r"[\n\r\t\b\f()\\]")
STR_ESC_MAP = {
    "\n": r"\n",
    "\r": r"\r",
    "\t": r"\t",
    "\b": r"\b",
    "\f": r"\f",
    "(": r"\(",
    ")": r"\)",
    "\\": r"\\",
}


class GraphicsStateDictRegistry(OrderedDict):
    """
    A container providing deduplication of graphics state dictionaries across a PDF.
    """

    def register_style(self, style: "GraphicsStyle"):
        sdict = style.serialize()

        # empty style does not need a dictionary
        if not sdict:
            return None

        try:
            return self[sdict]
        except KeyError:
            pass

        name = Name(f"GS{len(self)}")
        self[sdict] = name

        return name


def _check_range(value, minimum=0.0, maximum=1.0):
    if not minimum <= value <= maximum:
        raise ValueError(f"{value} not in range [{minimum}, {maximum}]")

    return value


def number_to_str(number):
    """
    Convert a decimal number to a minimal string representation (no trailing 0 or .).

    Args:
        number (Number): the number to be converted to a string.

    Returns:
        The number's string representation.
    """
    # this approach tries to produce minimal representations of floating point numbers
    # but can also produce "-0".
    return f"{number:.4f}".rstrip("0").rstrip(".")


# this maybe should live in fpdf.syntax
def render_pdf_primitive(primitive):
    """
    Render a Python value as a PDF primitive type.

    Container types (tuples/lists and dicts) are rendered recursively. This supports
    values of the type Name, str, bytes, numbers, booleans, list/tuple, and dict.

    Any custom type can be passed in as long as it provides a `serialize` method that
    takes no arguments and returns a string. The primitive object is returned directly
    if it is an instance of the `Raw` class. Otherwise, The existence of the `serialize`
    method is checked before any other type checking is performed, so, for example, a
    `dict` subclass with a `serialize` method would be converted using its `pdf_repr`
    method rather than the built-in `dict` conversion process.

    Args:
        primitive: the primitive value to convert to its PDF representation.

    Returns:
        Raw-wrapped str of the PDF representation.

    Raises:
        ValueError: if a dictionary key is not a Name.
        TypeError: if `primitive` does not have a known conversion to a PDF
            representation.
    """

    if isinstance(primitive, Raw):
        return primitive

    if callable(getattr(primitive, "serialize", None)):
        output = primitive.serialize()
    elif primitive is None:
        output = "null"
    elif isinstance(primitive, str):
        output = f"({escape_parens(primitive)})"
    elif isinstance(primitive, bytes):
        output = f"<{primitive.hex()}>"
    elif isinstance(primitive, bool):  # has to come before number check
        output = ["false", "true"][primitive]
    elif isinstance(primitive, NumberClass):
        output = number_to_str(primitive)
    elif isinstance(primitive, (list, tuple)):
        output = "[" + " ".join(render_pdf_primitive(val) for val in primitive) + "]"
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


# We allow passing alpha in as None instead of a numeric quantity, which signals to the
# rendering procedure not to emit an explicit alpha field for this graphics state,
# causing it to be inherited from the parent.


# this weird inheritance is used because for some reason normal NamedTuple usage doesn't
# allow overriding __new__, even though it works just as expected this way.
class DeviceRGB(
    NamedTuple(
        "DeviceRGB",
        [("r", Number), ("g", Number), ("b", Number), ("a", Optional[Number])],
    )
):
    """A class representing a PDF DeviceRGB color."""

    # This follows a common PDF drawing operator convention where the operand is upcased
    # to apply to stroke and downcased to apply to fill.

    # This could be more manually specified by  `CS`/`cs` to set the color space(e.g. to
    # `/DeviceRGB`) and `SC`/`sc` to set the color parameters. The documentation isn't
    # perfectly clear on this front, but it appears that these cannot be set in the
    # current graphics state dictionary and instead is set in the current page resource
    # dictionary. fpdf appears to only generate a single resource dictionary for the
    # entire document, and even if it created one per page, it would still be a lot
    # clunkier to try to use that.

    # Because PDF hates me, personally, the opacity of the drawing HAS to be specified
    # in the current graphics state dictionary and does not exist as a standalone
    # directive.
    OPERATOR = "rg"
    """The PDF drawing operator used to specify this type of color."""

    def __new__(cls, r, g, b, a=None):
        if a is not None:
            _check_range(a)

        return super().__new__(
            cls, _check_range(r), _check_range(g), _check_range(b), a
        )

    @property
    def colors(self):
        """The color components as a tuple in order `(r, g, b)` with alpha omitted."""
        return self[:-1]

    def serialize(self) -> str:
        return " ".join(number_to_str(val) for val in self.colors) + f" {self.OPERATOR}"


__pdoc__["DeviceRGB.OPERATOR"] = False
__pdoc__["DeviceRGB.r"] = "The red color component. Must be in the interval [0, 1]."
__pdoc__["DeviceRGB.g"] = "The green color component. Must be in the interval [0, 1]."
__pdoc__["DeviceRGB.b"] = "The blue color component. Must be in the interval [0, 1]."
__pdoc__[
    "DeviceRGB.a"
] = """
The alpha color component (i.e. opacity). Must be `None` or in the interval [0, 1].

An alpha value of 0 makes the color fully transparent, and a value of 1 makes it fully
opaque. If `None`, the color will be interpreted as not specifying a particular
transparency rather than specifying fully transparent or fully opaque.
"""


# this weird inheritance is used because for some reason normal NamedTuple usage doesn't
# allow overriding __new__, even though it works just as expected this way.
class DeviceGray(
    NamedTuple(
        "DeviceGray",
        [("g", Number), ("a", Optional[Number])],
    )
):
    """A class representing a PDF DeviceGray color."""

    OPERATOR = "g"
    """The PDF drawing operator used to specify this type of color."""

    def __new__(cls, g, a=None):
        if a is not None:
            _check_range(a)

        return super().__new__(cls, _check_range(g), a)

    @property
    def colors(self):
        """The color components as a tuple in order (g,) with alpha omitted."""
        return self[:-1]

    def serialize(self) -> str:
        return " ".join(number_to_str(val) for val in self.colors) + f" {self.OPERATOR}"


__pdoc__["DeviceGray.OPERATOR"] = False
__pdoc__[
    "DeviceGray.g"
] = """
The gray color component. Must be in the interval [0, 1].

A value of 0 represents black and a value of 1 represents white.
"""
__pdoc__[
    "DeviceGray.a"
] = """
The alpha color component (i.e. opacity). Must be `None` or in the interval [0, 1].

An alpha value of 0 makes the color fully transparent, and a value of 1 makes it fully
opaque. If `None`, the color will be interpreted as not specifying a particular
transparency rather than specifying fully transparent or fully opaque.
"""


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
    """A class representing a PDF DeviceCMYK color."""

    OPERATOR = "k"
    """The PDF drawing operator used to specify this type of color."""

    def __new__(cls, c, m, y, k, a=None):
        if a is not None:
            _check_range(a)

        return super().__new__(
            cls, _check_range(c), _check_range(m), _check_range(y), _check_range(k), a
        )

    @property
    def colors(self):
        """The color components as a tuple in order (c, m, y, k) with alpha omitted."""

        return self[:-1]

    def serialize(self) -> str:
        return " ".join(number_to_str(val) for val in self.colors) + f" {self.OPERATOR}"


__pdoc__["DeviceCMYK.OPERATOR"] = False
__pdoc__["DeviceCMYK.c"] = "The cyan color component. Must be in the interval [0, 1]."
__pdoc__["DeviceCMYK.m"] = (
    "The magenta color component. Must be in the interval [0, 1]."
)
__pdoc__["DeviceCMYK.y"] = "The yellow color component. Must be in the interval [0, 1]."
__pdoc__["DeviceCMYK.k"] = "The black color component. Must be in the interval [0, 1]."
__pdoc__[
    "DeviceCMYK.a"
] = """
The alpha color component (i.e. opacity). Must be `None` or in the interval [0, 1].

An alpha value of 0 makes the color fully transparent, and a value of 1 makes it fully
opaque. If `None`, the color will be interpreted as not specifying a particular
transparency rather than specifying fully transparent or fully opaque.
"""


def rgb8(r, g, b, a=None):
    """
    Produce a DeviceRGB color from the given 8-bit RGB values.

    Args:
        r (Number): red color component. Must be in the interval [0, 255].
        g (Number): green color component. Must be in the interval [0, 255].
        b (Number): blue color component. Must be in the interval [0, 255].
        a (Optional[Number]): alpha component. Must be `None` or in the interval
            [0, 255]. 0 is fully transparent, 255 is fully opaque

    Returns:
        DeviceRGB color representation.

    Raises:
        ValueError: if any components are not in their valid interval.
    """
    if a is not None:
        a /= 255.0

    return DeviceRGB(r / 255.0, g / 255.0, b / 255.0, a)


def gray8(g, a=None):
    """
    Produce a DeviceGray color from the given 8-bit gray value.

    Args:
        g (Number): gray color component. Must be in the interval [0, 255]. 0 is black,
            255 is white.
        a (Optional[Number]): alpha component. Must be `None` or in the interval
            [0, 255]. 0 is fully transparent, 255 is fully opaque

    Returns:
        DeviceGray color representation.

    Raises:
        ValueError: if any components are not in their valid interval.
    """
    if a is not None:
        a /= 255.0

    return DeviceGray(g / 255.0, a)


def convert_to_device_color(r, g=-1, b=-1):
    if isinstance(r, (DeviceGray, DeviceRGB)):
        # Note: in this case, r is also a Sequence
        return r
    if isinstance(r, str) and r.startswith("#"):
        return color_from_hex_string(r)
    if isinstance(r, Sequence):
        r, g, b = r
    if (r, g, b) == (0, 0, 0) or g == -1:
        return DeviceGray(r / 255)
    return DeviceRGB(r / 255, g / 255, b / 255)


def cmyk8(c, m, y, k, a=None):
    """
    Produce a DeviceCMYK color from the given 8-bit CMYK values.

    Args:
        c (Number): red color component. Must be in the interval [0, 255].
        m (Number): green color component. Must be in the interval [0, 255].
        y (Number): blue color component. Must be in the interval [0, 255].
        k (Number): blue color component. Must be in the interval [0, 255].
        a (Optional[Number]): alpha component. Must be `None` or in the interval
            [0, 255]. 0 is fully transparent, 255 is fully opaque

    Returns:
        DeviceCMYK color representation.

    Raises:
        ValueError: if any components are not in their valid interval.
    """
    if a is not None:
        a /= 255.0

    return DeviceCMYK(c / 255.0, m / 255.0, y / 255.0, k / 255.0, a)


def color_from_hex_string(hexstr):
    """
    Parse an RGB color from a css-style 8-bit hexadecimal color string.

    Args:
        hexstr (str): of the form `#RGB`, `#RGBA`, `#RRGGBB`, or `#RRGGBBAA`. Must
            include the leading octothorp. Forms omitting the alpha field are
            interpreted as not specifying the opacity, so it will not be explicitly set.

            An alpha value of `00` is fully transparent and `FF` is fully opaque.

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


def color_from_rgb_string(rgbstr):
    """
    Parse an RGB color from a css-style rgb(R, G, B, A) color string.

    Args:
        rgbstr (str): of the form `rgb(R, G, B)` or `rgb(R, G, B, A)`.

    Returns:
        DeviceRGB representation of the color.
    """
    if not isinstance(rgbstr, str):
        raise TypeError(f"{rgbstr} is not of type str")

    rgbstr = rgbstr.replace(" ", "")

    if not rgbstr.startswith("rgb(") or not rgbstr.endswith(")"):
        raise ValueError(f"{rgbstr} does not follow the expected rgb(...) format")

    rgbstr = rgbstr[4:-1]
    colors = rgbstr.split(",")

    if len(colors) == 3:
        return rgb8(*[int(c) for c in colors], a=None)

    if len(colors) == 4:
        return rgb8(*[int(c) for c in colors])

    raise ValueError(f"{rgbstr} could not be interpreted as a rgb(R, G, B[, A]) color")


class Point(NamedTuple):
    """
    An x-y coordinate pair within the two-dimensional coordinate frame.
    """

    x: Number
    """The abscissa of the point."""

    y: Number
    """The ordinate of the point."""

    def render(self):
        """Render the point to the string `"x y"` for emitting to a PDF."""

        return f"{number_to_str(self.x)} {number_to_str(self.y)}"

    def dot(self, other):
        """
        Compute the dot product of two points.

        Args:
            other (Point): the point with which to compute the dot product.

        Returns:
            The scalar result of the dot product computation.

        Raises:
            TypeError: if `other` is not a `Point`.
        """
        if not isinstance(other, Point):
            raise TypeError(f"cannot dot with {other!r}")

        return self.x * other.x + self.y * other.y

    def angle(self, other):
        """
        Compute the angle between two points (interpreted as vectors from the origin).

        The return value is in the interval (-pi, pi]. Sign is dependent on ordering,
        with clockwise angle travel considered to be positive due to the orientation of
        the coordinate frame basis vectors (i.e. the angle between `(1, 0)` and `(0, 1)`
        is `+pi/2`, the angle between `(1, 0)` and `(0, -1)` is `-pi/2`, and the angle
        between `(0, -1)` and `(1, 0)` is `+pi/2`).

        Args:
            other (Point): the point to compute the angle sweep toward.

        Returns:
            The scalar angle between the two points **in radians**.

        Raises:
            TypeError: if `other` is not a `Point`.
        """

        if not isinstance(other, Point):
            raise TypeError(f"cannot compute angle with {other!r}")

        signifier = (self.x * other.y) - (self.y * other.x)
        sign = (signifier >= 0) - (signifier < 0)
        return sign * math.acos(round(self.dot(other) / (self.mag() * other.mag()), 8))

    def mag(self):
        """
        Compute the Cartesian distance from this point to the origin

        This is the same as computing the magnitude of the vector represented by this
        point.

        Returns:
            The scalar result of the distance computation.
        """

        return (self.x**2 + self.y**2) ** 0.5

    @force_document
    def __add__(self, other):
        """
        Produce the sum of two points.

        Adding two points is the same as translating the source point by interpreting
        the other point's x and y coordinates as distances.

        Args:
            other (Point): right-hand side of the infix addition operation

        Returns:
            A Point which is the sum of the two source points.
        """
        if isinstance(other, Point):
            return Point(x=self.x + other.x, y=self.y + other.y)

        return NotImplemented

    @force_document
    def __sub__(self, other):
        """
        Produce the difference between two points.

        Unlike addition, this is not a commutative operation!

        Args:
            other (Point): right-hand side of the infix subtraction operation

        Returns:
            A Point which is the difference of the two source points.
        """
        if isinstance(other, Point):
            return Point(x=self.x - other.x, y=self.y - other.y)

        return NotImplemented

    @force_document
    def __neg__(self):
        """
        Produce a point by negating this point's coordinates.

        Returns:
            A Point whose coordinates are this points coordinates negated.
        """
        return Point(x=-self.x, y=-self.y)

    @force_document
    def __mul__(self, other):
        """
        Multiply a point by a scalar value.

        Args:
            other (Number): the scalar value by which to multiply the point's
                coordinates.

        Returns:
            A Point whose coordinates are the result of the multiplication.
        """
        if isinstance(other, NumberClass):
            return Point(self.x * other, self.y * other)

        return NotImplemented

    __rmul__ = __mul__

    @force_document
    def __truediv__(self, other):
        """
        Divide a point by a scalar value.

        .. note::

            Because division is not commutative, `Point / scalar` is implemented, but
            `scalar / Point` is nonsensical and not implemented.

        Args:
            other (Number): the scalar value by which to divide the point's coordinates.

        Returns:
            A Point whose coordinates are the result of the division.
        """
        if isinstance(other, NumberClass):
            return Point(self.x / other, self.y / other)

        return NotImplemented

    @force_document
    def __floordiv__(self, other):
        """
        Divide a point by a scalar value using integer division.

        .. note::

            Because division is not commutative, `Point // scalar` is implemented, but
            `scalar // Point` is nonsensical and not implemented.

        Args:
            other (Number): the scalar value by which to divide the point's coordinates.

        Returns:
            A Point whose coordinates are the result of the division.
        """
        if isinstance(other, NumberClass):
            return Point(self.x // other, self.y // other)

        return NotImplemented

    # no __r(true|floor)div__ because division is not commutative!

    @force_document
    def __matmul__(self, other):
        """
        Transform a point with the given transform matrix.

        .. note::
            This operator is only implemented for Transforms. This transform is not
            commutative, so `Point @ Transform` is implemented, but `Transform @ Point`
            is not implemented (technically speaking, the current implementation is
            commutative because of the way points and transforms are represented, but
            if that representation were to change this operation could stop being
            commutative)

        Args:
            other (Transform): the transform to apply to the point

        Returns:
            A Point whose coordinates are the result of applying the transform.
        """
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

    ```
                        [ a b 0 ]
    [x' y' 1] = [x y 1] [ c d 0 ]
                        [ e f 1 ]
    ```

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

    For example, to rotate the square `(1,1) (1,3) (3,3) (3,1)` 45 degrees clockwise
    about its center point (which is `(2,2)`) , the translate-rotate-translate
    process described above may be applied:

    ```python
    rotate_centered = (
        Transform.translation(-2, -2)
        @ Transform.rotation_d(45)
        @ Transform.translation(2, 2)
    )
    ```

    Instances of this class provide a chaining API, so the above transform could also be
    constructed as follows:

    ```python
    rotate_centered = Transform.translation(-2, -2).rotate_d(45).translate(2, 2)
    ```

    Or, because the particular operation of performing some transformations about a
    specific point is pretty common,

    ```python
    rotate_centered = Transform.rotation_d(45).about(2, 2)
    ```

    By convention, this class provides class method constructors following noun-ish
    naming (`translation`, `scaling`, `rotation`, `shearing`) and instance method
    manipulations following verb-ish naming (`translate`, `scale`, `rotate`, `shear`).
    """

    a: Number
    b: Number
    c: Number
    d: Number
    e: Number
    f: Number

    # compact representation of an affine transformation matrix for 2D shapes.
    # The actual matrix is:
    #                     [ A B 0 ]
    # [x' y' 1] = [x y 1] [ C D 0 ]
    #                     [ E F 1 ]
    # The identity transform is 1 0 0 1 0 0

    @classmethod
    def identity(cls):
        """
        Create a transform representing the identity transform.

        The identity transform is a no-op.
        """
        return cls(1, 0, 0, 1, 0, 0)

    @classmethod
    def translation(cls, x, y):
        """
        Create a transform that performs translation.

        Args:
            x (Number): distance to translate points along the x (horizontal) axis.
            y (Number): distance to translate points along the y (vertical) axis.

        Returns:
            A Transform representing the specified translation.
        """

        return cls(1, 0, 0, 1, x, y)

    @classmethod
    def scaling(cls, x, y=None):
        """
        Create a transform that performs scaling.

        Args:
            x (Number): scaling ratio in the x (horizontal) axis. A value of 1
                results in no scale change in the x axis.
            y (Number): optional scaling ratio in the y (vertical) axis. A value of 1
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
        Create a transform that performs rotation.

        Args:
            theta (Number): the angle **in radians** by which to rotate. Positive
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
        Create a transform that performs rotation **in degrees**.

        Args:
            theta_d (Number): the angle **in degrees** by which to rotate. Positive
                values represent clockwise rotations.

        Returns:
            A Transform representing the specified rotation.

        """
        return cls.rotation(math.radians(theta_d))

    @classmethod
    def shearing(cls, x, y=None):
        """
        Create a transform that performs shearing (not of sheep).

        Args:
            x (Number): The amount to shear along the x (horizontal) axis.
            y (Number): Optional amount to shear along the y (vertical) axis. If omitted,
                this defaults to the value provided to the `x` argument.

        Returns:
            A Transform representing the specified shearing.

        """
        if y is None:
            y = x
        return cls(1, y, x, 1, 0, 0)

    def translate(self, x, y):
        """
        Produce a transform by composing the current transform with a translation.

        .. note::
            Transforms are immutable, so this returns a new transform rather than
            mutating self.

        Args:
            x (Number): distance to translate points along the x (horizontal) axis.
            y (Number): distance to translate points along the y (vertical) axis.

        Returns:
            A Transform representing the composed transform.
        """
        return self @ Transform.translation(x, y)

    def scale(self, x, y=None):
        """
        Produce a transform by composing the current transform with a scaling.

        .. note::
            Transforms are immutable, so this returns a new transform rather than
            mutating self.

        Args:
            x (Number): scaling ratio in the x (horizontal) axis. A value of 1
                results in no scale change in the x axis.
            y (Number): optional scaling ratio in the y (vertical) axis. A value of 1
                results in no scale change in the y axis. If this value is omitted, it
                defaults to the value provided to the `x` argument.

        Returns:
            A Transform representing the composed transform.
        """
        return self @ Transform.scaling(x, y)

    def rotate(self, theta):
        """
        Produce a transform by composing the current transform with a rotation.

        .. note::
            Transforms are immutable, so this returns a new transform rather than
            mutating self.

        Args:
            theta (Number): the angle **in radians** by which to rotate. Positive
                values represent clockwise rotations.

        Returns:
            A Transform representing the composed transform.
        """
        return self @ Transform.rotation(theta)

    def rotate_d(self, theta_d):
        """
        Produce a transform by composing the current transform with a rotation
        **in degrees**.

        .. note::
            Transforms are immutable, so this returns a new transform rather than
            mutating self.

        Args:
            theta_d (Number): the angle **in degrees** by which to rotate. Positive
                values represent clockwise rotations.

        Returns:
            A Transform representing the composed transform.
        """
        return self @ Transform.rotation_d(theta_d)

    def shear(self, x, y=None):
        """
        Produce a transform by composing the current transform with a shearing.

        .. note::
            Transforms are immutable, so this returns a new transform rather than
            mutating self.

        Args:
            x (Number): The amount to shear along the x (horizontal) axis.
            y (Number): Optional amount to shear along the y (vertical) axis. If omitted,
                this defaults to the value provided to the `x` argument.

        Returns:
            A Transform representing the composed transform.
        """
        return self @ Transform.shearing(x, y)

    def about(self, x, y):
        """
        Bracket the given transform in a pair of translations to make it appear about a
        point that isn't the origin.

        This is a useful shorthand for performing a transform like a rotation around the
        center point of an object that isn't centered at the origin.

        .. note::
            Transforms are immutable, so this returns a new transform rather than
            mutating self.

        Args:
            x (Number): the point along the x (horizontal) axis about which to transform.
            y (Number): the point along the y (vertical) axis about which to transform.

        Returns:
            A Transform representing the composed transform.
        """
        return Transform.translation(-x, -y) @ self @ Transform.translation(x, y)

    @force_document
    def __mul__(self, other):
        """
        Multiply the individual transform parameters by a scalar value.

        Args:
            other (Number): the scalar value by which to multiply the parameters

        Returns:
            A Transform with the modified parameters.
        """
        if isinstance(other, NumberClass):
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

    @force_document
    def __matmul__(self, other):
        """
        Compose two transforms into a single transform.

        Args:
            other (Transform): the right-hand side transform of the infix operator.

        Returns:
            A Transform representing the composed transform.
        """
        if isinstance(other, Transform):
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
        """
        Render the transform to its PDF output representation.

        Args:
            last_item: the last path element this transform applies to

        Returns:
            A tuple of `(str, last_item)`. `last_item` is returned unchanged.
        """
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


__pdoc__["Transform.a"] = False
__pdoc__["Transform.b"] = False
__pdoc__["Transform.c"] = False
__pdoc__["Transform.d"] = False
__pdoc__["Transform.e"] = False
__pdoc__["Transform.f"] = False


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
    """Singleton specifying a style parameter should be inherited from the parent context."""

    # order is be important here because some of these properties are entangled, e.g.
    # fill_color and fill_opacity
    MERGE_PROPERTIES = (
        "paint_rule",
        "allow_transparency",
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
    """An ordered collection of properties to use when merging two GraphicsStyles."""

    TRANSPARENCY_KEYS = (
        PDFStyleKeys.FILL_ALPHA.value,
        PDFStyleKeys.STROKE_ALPHA.value,
        PDFStyleKeys.BLEND_MODE.value,
    )
    """An ordered collection of attributes not to emit in no transparency mode."""

    PDF_STYLE_KEYS = (
        *(k.value for k in PDFStyleKeys if k is not PDFStyleKeys.STROKE_DASH_PATTERN),
    )
    """An ordered collection of keys to directly emit when serializing the style."""

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

    @classmethod
    def merge(cls, parent, child):
        """
        Merge parent and child into a single GraphicsStyle.

        The result contains the properties of the parent as overridden by any properties
        explicitly set on the child. If both the parent and the child specify to
        inherit a given property, that property will preserve the inherit value.
        """
        new = cls()
        for prop in cls.MERGE_PROPERTIES:
            cval = getattr(child, prop)
            if cval is cls.INHERIT:
                setattr(new, prop, getattr(parent, prop))
            else:
                setattr(new, prop, cval)

        return new

    def __init__(self):
        self.allow_transparency = self.INHERIT
        self.paint_rule = self.INHERIT
        self.auto_close = self.INHERIT
        self.intersection_rule = self.INHERIT
        self.fill_color = self.INHERIT
        self.fill_opacity = self.INHERIT
        self.stroke_color = self.INHERIT
        self.stroke_opacity = self.INHERIT
        self.blend_mode = self.INHERIT
        self.stroke_width = self.INHERIT
        self.stroke_cap_style = self.INHERIT
        self.stroke_join_style = self.INHERIT
        self.stroke_miter_limit = self.INHERIT
        self.stroke_dash_pattern = self.INHERIT
        self.stroke_dash_phase = self.INHERIT

    def __deepcopy__(self, memo):
        copied = self.__class__()
        for prop in self.MERGE_PROPERTIES:
            setattr(copied, prop, getattr(self, prop))

        return copied

    def __setattr__(self, name, value):
        if not hasattr(self.__class__, name):
            raise AttributeError(
                f'{self.__class__} does not have style "{name}" (a typo?)'
            )

        super().__setattr__(name, value)

    # at some point it probably makes sense to turn this into a general compliance
    # property, but for now this is the simple approach.
    @property
    def allow_transparency(self):
        return self._allow_transparency  # pylint: disable=no-member

    @allow_transparency.setter
    def allow_transparency(self, new):
        return super().__setattr__("_allow_transparency", new)

    # If these are used in a nested graphics context inside of a painting path
    # operation, they are no-ops. However, they can be used for outer GraphicsContexts
    # that painting paths inherit from.
    @property
    def paint_rule(self):
        """The paint rule to use for this path/group."""
        return self._paint_rule  # pylint: disable=no-member

    @paint_rule.setter
    def paint_rule(self, new):
        if new is None:
            super().__setattr__("_paint_rule", PathPaintRule.DONT_PAINT)
        elif new is self.INHERIT:
            super().__setattr__("_paint_rule", new)
        else:
            super().__setattr__("_paint_rule", PathPaintRule.coerce(new))

    @property
    def auto_close(self):
        """If True, unclosed paths will be automatically closed before stroking."""
        return self._auto_close  # pylint: disable=no-member

    @auto_close.setter
    def auto_close(self, new):
        if new not in {True, False, self.INHERIT}:
            raise TypeError(f"auto_close must be a bool or self.INHERIT, not {new}")

        super().__setattr__("_auto_close", new)

    @property
    def intersection_rule(self):
        """The desired intersection rule for this path/group."""
        return self._intersection_rule  # pylint: disable=no-member

    @intersection_rule.setter
    def intersection_rule(self, new):
        # don't allow None for this one.
        if new is self.INHERIT:
            super().__setattr__("_intersection_rule", new)
        else:
            super().__setattr__("_intersection_rule", IntersectionRule.coerce(new))

    @property
    def fill_color(self):
        """
        The desired fill color for this path/group.

        When setting this property, if the color specifies an opacity value, that will
        be used to set the fill_opacity property as well.
        """
        return self._fill_color  # pylint: disable=no-member

    @fill_color.setter
    def fill_color(self, color):
        if isinstance(color, str):
            color = color_from_hex_string(color)

        if isinstance(color, (DeviceRGB, DeviceGray, DeviceCMYK)):
            super().__setattr__("_fill_color", color)
            if color.a is not None:
                self.fill_opacity = color.a

        elif (color is None) or (color is self.INHERIT):
            super().__setattr__("_fill_color", color)

        else:
            raise TypeError(f"{color} doesn't look like a drawing color")

    @property
    def fill_opacity(self):
        """The desired fill opacity for this path/group."""
        return getattr(self, PDFStyleKeys.FILL_ALPHA.value)

    @fill_opacity.setter
    def fill_opacity(self, new):
        if new not in {None, self.INHERIT}:
            _check_range(new)

        super().__setattr__(PDFStyleKeys.FILL_ALPHA.value, new)

    @property
    def stroke_color(self):
        """
        The desired stroke color for this path/group.

        When setting this property, if the color specifies an opacity value, that will
        be used to set the fill_opacity property as well.
        """
        return self._stroke_color  # pylint: disable=no-member

    @stroke_color.setter
    def stroke_color(self, color):
        if isinstance(color, str):
            color = color_from_hex_string(color)

        if isinstance(color, (DeviceRGB, DeviceGray, DeviceCMYK)):
            super().__setattr__("_stroke_color", color)
            if color.a is not None:
                self.stroke_opacity = color.a
            if self.stroke_width is self.INHERIT:
                self.stroke_width = 1

        elif (color is None) or (color is self.INHERIT):
            super().__setattr__("_stroke_color", color)

        else:
            raise TypeError(f"{color} doesn't look like a drawing color")

    @property
    def stroke_opacity(self):
        """The desired stroke opacity for this path/group."""
        return getattr(self, PDFStyleKeys.STROKE_ALPHA.value)

    @stroke_opacity.setter
    def stroke_opacity(self, new):
        if new not in {None, self.INHERIT}:
            _check_range(new)

        super().__setattr__(PDFStyleKeys.STROKE_ALPHA.value, new)

    @property
    def blend_mode(self):
        """The desired blend mode for this path/group."""
        return getattr(self, PDFStyleKeys.BLEND_MODE.value)

    @blend_mode.setter
    def blend_mode(self, value):
        if value is self.INHERIT:
            super().__setattr__(PDFStyleKeys.BLEND_MODE.value, value)
        else:
            super().__setattr__(
                PDFStyleKeys.BLEND_MODE.value, BlendMode.coerce(value).value
            )

    @property
    def stroke_width(self):
        """The desired stroke width for this path/group."""
        return getattr(self, PDFStyleKeys.STROKE_WIDTH.value)

    @stroke_width.setter
    def stroke_width(self, width):
        if not isinstance(
            width,
            (int, float, decimal.Decimal, type(None), type(self.INHERIT)),
        ):
            raise TypeError(f"stroke_width must be a number, not {type(width)}")

        super().__setattr__(PDFStyleKeys.STROKE_WIDTH.value, width)

    @property
    def stroke_cap_style(self):
        """The desired stroke cap style for this path/group."""
        return getattr(self, PDFStyleKeys.STROKE_CAP_STYLE.value)

    @stroke_cap_style.setter
    def stroke_cap_style(self, value):
        if value is self.INHERIT:
            super().__setattr__(PDFStyleKeys.STROKE_CAP_STYLE.value, value)
        else:
            super().__setattr__(
                PDFStyleKeys.STROKE_CAP_STYLE.value, StrokeCapStyle.coerce(value)
            )

    @property
    def stroke_join_style(self):
        """The desired stroke join style for this path/group."""
        return getattr(self, PDFStyleKeys.STROKE_JOIN_STYLE.value)

    @stroke_join_style.setter
    def stroke_join_style(self, value):
        if value is self.INHERIT:
            super().__setattr__(PDFStyleKeys.STROKE_JOIN_STYLE.value, value)
        else:
            super().__setattr__(
                PDFStyleKeys.STROKE_JOIN_STYLE.value,
                StrokeJoinStyle.coerce(value),
            )

    @property
    def stroke_miter_limit(self):
        """The desired stroke miter limit for this path/group."""
        return getattr(self, PDFStyleKeys.STROKE_MITER_LIMIT.value)

    @stroke_miter_limit.setter
    def stroke_miter_limit(self, value):
        if (value is self.INHERIT) or isinstance(value, NumberClass):
            super().__setattr__(PDFStyleKeys.STROKE_MITER_LIMIT.value, value)
        else:
            raise TypeError(f"{value} is not a number")

    @property
    def stroke_dash_pattern(self):
        """The desired stroke dash pattern for this path/group."""
        return self._stroke_dash_pattern  # pylint: disable=no-member

    @stroke_dash_pattern.setter
    def stroke_dash_pattern(self, value):
        if value is None:
            result = ()
        elif value is self.INHERIT:
            result = value
        elif isinstance(value, NumberClass):
            result = (value,)
        else:
            try:
                accum = []
                for item in value:
                    if not isinstance(item, NumberClass):
                        raise TypeError(
                            f"stroke_dash_pattern {value} sequence has non-numeric value"
                        )
                    accum.append(item)
            except TypeError:
                raise TypeError(
                    f"stroke_dash_pattern {value} must be a number or sequence of numbers"
                ) from None
            result = (*accum,)

        super().__setattr__("_stroke_dash_pattern", result)

    @property
    def stroke_dash_phase(self):
        """The desired stroke dash pattern phase offset for this path/group."""
        return self._stroke_dash_phase  # pylint: disable=no-member

    @stroke_dash_phase.setter
    def stroke_dash_phase(self, value):
        if value is self.INHERIT or isinstance(value, NumberClass):
            return super().__setattr__("_stroke_dash_phase", value)

        raise TypeError(f"{value} isn't a number or GraphicsStyle.INHERIT")

    def serialize(self):
        """
        Convert this style object to a PDF dictionary with appropriate style keys.

        Only explicitly specified values are emitted.
        """
        result = OrderedDict()

        for key in self.PDF_STYLE_KEYS:
            value = getattr(self, key, self.INHERIT)

            if (value is not self.INHERIT) and (value is not None):
                # None is used for out-of-band signaling on these, e.g. a stroke_width
                # of None doesn't need to land here because it signals the
                # PathPaintRule auto resolution only.
                result[key] = value

        # There is additional logic in GraphicsContext to ensure that this will work
        if (self.stroke_dash_pattern is not self.INHERIT) and (
            self.stroke_dash_pattern is not None
        ):
            result[PDFStyleKeys.STROKE_DASH_PATTERN.value] = [
                self.stroke_dash_pattern,
                self.stroke_dash_phase,
            ]

        if self.allow_transparency is False:
            for key in self.TRANSPARENCY_KEYS:
                if key in result:
                    del result[key]

        if result:
            # Only insert this key if there is at least one other item in the result so
            # that we don't junk up the output PDF with empty ExtGState dictionaries.
            type_name = Name("Type")
            result[type_name] = Name("ExtGState")
            result.move_to_end(type_name, last=False)

            return render_pdf_primitive(result)

        # this signals to the GraphicsStateDictRegistry that there is nothing to
        # register. This is a success case.
        return None

    @force_nodocument
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

        elif self.paint_rule is self.INHERIT:
            # this shouldn't happen under normal usage, but certain API (ab)use can end
            # up in this state. We can't resolve anything meaningful, so fall back to a
            # sane(?) default.
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
    """
    A path move element.

    If a path has been created but not yet painted, this will create a new subpath.

    See: `PaintedPath.move_to`
    """

    pt: Point
    """The point to which to move."""

    @property
    def end_point(self):
        """The end point of this path element."""
        return self.pt

    @force_nodocument
    def render(self, gsd_registry, style, last_item, initial_point):
        """
        Render this path element to its PDF representation.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command

        Returns:
            a tuple of `(str, new_last_item)`, where `new_last_item` is `self`
        """
        # pylint: disable=unused-argument
        return _render_move(self.pt), self, self.pt

    @force_nodocument
    def render_debug(
        self, gsd_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command
            debug_stream (io.TextIO): the stream to which the debug output should be
                written. This is not guaranteed to be seekable (e.g. it may be stdout or
                stderr).
            pfx (str): the current debug output prefix string (only needed if emitting
                more than one line).

        Returns:
            The same tuple as `Move.render`.
        """
        # pylint: disable=unused-argument
        rendered, resolved, initial_point = self.render(
            gsd_registry, style, last_item, initial_point
        )
        debug_stream.write(str(self) + "\n")

        return rendered, resolved, initial_point


class RelativeMove(NamedTuple):
    """
    A path move element with an end point relative to the end of the previous path
    element.

    If a path has been created but not yet painted, this will create a new subpath.

    See: `PaintedPath.move_relative`
    """

    pt: Point
    """The offset by which to move."""

    @force_nodocument
    def render(self, gsd_registry, style, last_item, initial_point):
        """
        Render this path element to its PDF representation.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command

        Returns:
            a tuple of `(str, new_last_item)`, where `new_last_item` is the resolved
            `Move`
        """
        # pylint: disable=unused-argument
        point = last_item.end_point + self.pt
        return _render_move(point), Move(point), point

    @force_nodocument
    def render_debug(
        self, gsd_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command
            debug_stream (io.TextIO): the stream to which the debug output should be
                written. This is not guaranteed to be seekable (e.g. it may be stdout or
                stderr).
            pfx (str): the current debug output prefix string (only needed if emitting
                more than one line).

        Returns:
            The same tuple as `RelativeMove.render`.
        """
        # pylint: disable=unused-argument
        rendered, resolved, initial_point = self.render(
            gsd_registry, style, last_item, initial_point
        )
        debug_stream.write(f"{self} resolved to {resolved}\n")

        return rendered, resolved, initial_point


class Line(NamedTuple):
    """
    A path line element.

    This draws a straight line from the end point of the previous path element to the
    point specified by `pt`.

    See: `PaintedPath.line_to`
    """

    pt: Point
    """The point to which the line is drawn."""

    @property
    def end_point(self):
        """The end point of this path element."""
        return self.pt

    @force_nodocument
    def render(self, gsd_registry, style, last_item, initial_point):
        """
        Render this path element to its PDF representation.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command

        Returns:
            a tuple of `(str, new_last_item)`, where `new_last_item` is `self`
        """
        # pylint: disable=unused-argument
        return _render_line(self.pt), self, initial_point

    @force_nodocument
    def render_debug(
        self, gsd_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command
            debug_stream (io.TextIO): the stream to which the debug output should be
                written. This is not guaranteed to be seekable (e.g. it may be stdout or
                stderr).
            pfx (str): the current debug output prefix string (only needed if emitting
                more than one line).

        Returns:
            The same tuple as `Line.render`.
        """
        # pylint: disable=unused-argument
        rendered, resolved, initial_point = self.render(
            gsd_registry, style, last_item, initial_point
        )
        debug_stream.write(str(self) + "\n")

        return rendered, resolved, initial_point


class RelativeLine(NamedTuple):
    """
    A path line element with an endpoint relative to the end of the previous element.

    This draws a straight line from the end point of the previous path element to the
    point specified by `last_item.end_point + pt`. The absolute coordinates of the end
    point are resolved during the rendering process.

    See: `PaintedPath.line_relative`
    """

    pt: Point
    """The endpoint of the line relative to the previous path element."""

    @force_nodocument
    def render(self, gsd_registry, style, last_item, initial_point):
        """
        Render this path element to its PDF representation.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command

        Returns:
            a tuple of `(str, new_last_item)`, where `new_last_item` is the resolved
            `Line`.
        """
        # pylint: disable=unused-argument
        point = last_item.end_point + self.pt
        return _render_line(point), Line(point), initial_point

    @force_nodocument
    def render_debug(
        self, gsd_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command
            debug_stream (io.TextIO): the stream to which the debug output should be
                written. This is not guaranteed to be seekable (e.g. it may be stdout or
                stderr).
            pfx (str): the current debug output prefix string (only needed if emitting
                more than one line).

        Returns:
            The same tuple as `RelativeLine.render`.
        """
        # pylint: disable=unused-argument
        rendered, resolved, initial_point = self.render(
            gsd_registry, style, last_item, initial_point
        )
        debug_stream.write(f"{self} resolved to {resolved}\n")

        return rendered, resolved, initial_point


class HorizontalLine(NamedTuple):
    """
    A path line element that takes its ordinate from the end of the previous element.

    See: `PaintedPath.horizontal_line_to`
    """

    x: Number
    """The abscissa of the horizontal line's end point."""

    @force_nodocument
    def render(self, gsd_registry, style, last_item, initial_point):
        """
        Render this path element to its PDF representation.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command

        Returns:
            a tuple of `(str, new_last_item)`, where `new_last_item` is the resolved
            `Line`.
        """
        # pylint: disable=unused-argument
        end_point = Point(x=self.x, y=last_item.end_point.y)
        return _render_line(end_point), Line(end_point), initial_point

    @force_nodocument
    def render_debug(
        self, gsd_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command
            debug_stream (io.TextIO): the stream to which the debug output should be
                written. This is not guaranteed to be seekable (e.g. it may be stdout or
                stderr).
            pfx (str): the current debug output prefix string (only needed if emitting
                more than one line).

        Returns:
            The same tuple as `HorizontalLine.render`.
        """
        # pylint: disable=unused-argument
        rendered, resolved, initial_point = self.render(
            gsd_registry, style, last_item, initial_point
        )
        debug_stream.write(f"{self} resolved to {resolved}\n")

        return rendered, resolved, initial_point


class RelativeHorizontalLine(NamedTuple):
    """
    A path line element that takes its ordinate from the end of the previous element and
    computes its abscissa offset from the end of that element.

    See: `PaintedPath.horizontal_line_relative`
    """

    x: Number
    """
    The abscissa of the horizontal line's end point relative to the abscissa of the
    previous path element.
    """

    @force_nodocument
    def render(self, gsd_registry, style, last_item, initial_point):
        """
        Render this path element to its PDF representation.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command

        Returns:
            a tuple of `(str, new_last_item)`, where `new_last_item` is the resolved
            `Line`.
        """
        # pylint: disable=unused-argument
        end_point = Point(x=last_item.end_point.x + self.x, y=last_item.end_point.y)
        return _render_line(end_point), Line(end_point), initial_point

    @force_nodocument
    def render_debug(
        self, gsd_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command
            debug_stream (io.TextIO): the stream to which the debug output should be
                written. This is not guaranteed to be seekable (e.g. it may be stdout or
                stderr).
            pfx (str): the current debug output prefix string (only needed if emitting
                more than one line).

        Returns:
            The same tuple as `RelativeHorizontalLine.render`.
        """
        # pylint: disable=unused-argument
        rendered, resolved, initial_point = self.render(
            gsd_registry, style, last_item, initial_point
        )
        debug_stream.write(f"{self} resolved to {resolved}\n")

        return rendered, resolved, initial_point


class VerticalLine(NamedTuple):
    """
    A path line element that takes its abscissa from the end of the previous element.

    See: `PaintedPath.vertical_line_to`
    """

    y: Number
    """The ordinate of the vertical line's end point."""

    @force_nodocument
    def render(self, gsd_registry, style, last_item, initial_point):
        """
        Render this path element to its PDF representation.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command

        Returns:
            a tuple of `(str, new_last_item)`, where `new_last_item` is the resolved
            `Line`.
        """
        # pylint: disable=unused-argument
        end_point = Point(x=last_item.end_point.x, y=self.y)
        return _render_line(end_point), Line(end_point), initial_point

    @force_nodocument
    def render_debug(
        self, gsd_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command
            debug_stream (io.TextIO): the stream to which the debug output should be
                written. This is not guaranteed to be seekable (e.g. it may be stdout or
                stderr).
            pfx (str): the current debug output prefix string (only needed if emitting
                more than one line).

        Returns:
            The same tuple as `VerticalLine.render`.
        """
        # pylint: disable=unused-argument
        rendered, resolved, initial_point = self.render(
            gsd_registry, style, last_item, initial_point
        )
        debug_stream.write(f"{self} resolved to {resolved}\n")

        return rendered, resolved, initial_point


class RelativeVerticalLine(NamedTuple):
    """
    A path line element that takes its abscissa from the end of the previous element and
    computes its ordinate offset from the end of that element.

    See: `PaintedPath.vertical_line_relative`
    """

    y: Number
    """
    The ordinate of the vertical line's end point relative to the ordinate of the
    previous path element.
    """

    @force_nodocument
    def render(self, gsd_registry, style, last_item, initial_point):
        """
        Render this path element to its PDF representation.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command

        Returns:
            a tuple of `(str, new_last_item)`, where `new_last_item` is the resolved
            `Line`.
        """
        # pylint: disable=unused-argument
        end_point = Point(x=last_item.end_point.x, y=last_item.end_point.y + self.y)
        return _render_line(end_point), Line(end_point), initial_point

    @force_nodocument
    def render_debug(
        self, gsd_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command
            debug_stream (io.TextIO): the stream to which the debug output should be
                written. This is not guaranteed to be seekable (e.g. it may be stdout or
                stderr).
            pfx (str): the current debug output prefix string (only needed if emitting
                more than one line).

        Returns:
            The same tuple as `RelativeVerticalLine.render`.
        """
        # pylint: disable=unused-argument
        rendered, resolved, initial_point = self.render(
            gsd_registry, style, last_item, initial_point
        )
        debug_stream.write(f"{self} resolved to {resolved}\n")

        return rendered, resolved, initial_point


class BezierCurve(NamedTuple):
    """
    A cubic Bézier curve path element.

    This draws a Bézier curve parameterized by the end point of the previous path
    element, two off-curve control points, and an end point.

    See: `PaintedPath.curve_to`
    """

    c1: Point
    """The curve's first control point."""
    c2: Point
    """The curve's second control point."""
    end: Point
    """The curve's end point."""

    @property
    def end_point(self):
        """The end point of this path element."""
        return self.end

    @force_nodocument
    def render(self, gsd_registry, style, last_item, initial_point):
        """
        Render this path element to its PDF representation.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command

        Returns:
            a tuple of `(str, new_last_item)`, where `new_last_item` is `self`
        """
        # pylint: disable=unused-argument
        return _render_curve(self.c1, self.c2, self.end), self, initial_point

    @force_nodocument
    def render_debug(
        self, gsd_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command
            debug_stream (io.TextIO): the stream to which the debug output should be
                written. This is not guaranteed to be seekable (e.g. it may be stdout or
                stderr).
            pfx (str): the current debug output prefix string (only needed if emitting
                more than one line).

        Returns:
            The same tuple as `BezierCurve.render`.
        """
        # pylint: disable=unused-argument
        rendered, resolved, initial_point = self.render(
            gsd_registry, style, last_item, initial_point
        )
        debug_stream.write(str(self) + "\n")

        return rendered, resolved, initial_point


class RelativeBezierCurve(NamedTuple):
    """
    A cubic Bézier curve path element whose points are specified relative to the end
    point of the previous path element.

    See: `PaintedPath.curve_relative`
    """

    c1: Point
    """
    The curve's first control point relative to the end of the previous path element.
    """
    c2: Point
    """
    The curve's second control point relative to the end of the previous path element.
    """
    end: Point
    """The curve's end point relative to the end of the previous path element."""

    @force_nodocument
    def render(self, gsd_registry, style, last_item, initial_point):
        """
        Render this path element to its PDF representation.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command

        Returns:
            a tuple of `(str, new_last_item)`, where `new_last_item` is the resolved
            `BezierCurve`.
        """
        # pylint: disable=unused-argument
        last_point = last_item.end_point

        c1 = last_point + self.c1
        c2 = last_point + self.c2
        end = last_point + self.end

        return (
            _render_curve(c1, c2, end),
            BezierCurve(c1=c1, c2=c2, end=end),
            initial_point,
        )

    @force_nodocument
    def render_debug(
        self, gsd_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command
            debug_stream (io.TextIO): the stream to which the debug output should be
                written. This is not guaranteed to be seekable (e.g. it may be stdout or
                stderr).
            pfx (str): the current debug output prefix string (only needed if emitting
                more than one line).

        Returns:
            The same tuple as `RelativeBezierCurve.render`.
        """
        # pylint: disable=unused-argument
        rendered, resolved, initial_point = self.render(
            gsd_registry, style, last_item, initial_point
        )
        debug_stream.write(f"{self} resolved to {resolved}\n")

        return rendered, resolved, initial_point


class QuadraticBezierCurve(NamedTuple):
    """
    A quadratic Bézier curve path element.

    This draws a Bézier curve parameterized by the end point of the previous path
    element, one off-curve control point, and an end point.

    See: `PaintedPath.quadratic_curve_to`
    """

    ctrl: Point
    """The curve's control point."""
    end: Point
    """The curve's end point."""

    @property
    def end_point(self):
        """The end point of this path element."""
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

    @force_nodocument
    def render(self, gsd_registry, style, last_item, initial_point):
        """
        Render this path element to its PDF representation.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command

        Returns:
            a tuple of `(str, new_last_item)`, where `new_last_item` is `self`.
        """
        return (
            self.to_cubic_curve(last_item.end_point).render(
                gsd_registry, style, last_item, initial_point
            )[0],
            self,
            initial_point,
        )

    @force_nodocument
    def render_debug(
        self, gsd_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command
            debug_stream (io.TextIO): the stream to which the debug output should be
                written. This is not guaranteed to be seekable (e.g. it may be stdout or
                stderr).
            pfx (str): the current debug output prefix string (only needed if emitting
                more than one line).

        Returns:
            The same tuple as `QuadraticBezierCurve.render`.
        """
        # pylint: disable=unused-argument
        rendered, resolved, initial_point = self.render(
            gsd_registry, style, last_item, initial_point
        )
        debug_stream.write(
            f"{self} resolved to {self.to_cubic_curve(last_item.end_point)}\n"
        )

        return rendered, resolved, initial_point


class RelativeQuadraticBezierCurve(NamedTuple):
    """
    A quadratic Bézier curve path element whose points are specified relative to the end
    point of the previous path element.

    See: `PaintedPath.quadratic_curve_relative`
    """

    ctrl: Point
    """The curve's control point relative to the end of the previous path element."""
    end: Point
    """The curve's end point relative to the end of the previous path element."""

    @force_nodocument
    def render(self, gsd_registry, style, last_item, initial_point):
        """
        Render this path element to its PDF representation.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command

        Returns:
            a tuple of `(str, new_last_item)`, where `new_last_item` is the resolved
            `QuadraticBezierCurve`.
        """
        last_point = last_item.end_point

        ctrl = last_point + self.ctrl
        end = last_point + self.end

        absolute = QuadraticBezierCurve(ctrl=ctrl, end=end)
        return absolute.render(gsd_registry, style, last_item, initial_point)

    @force_nodocument
    def render_debug(
        self, gsd_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command
            debug_stream (io.TextIO): the stream to which the debug output should be
                written. This is not guaranteed to be seekable (e.g. it may be stdout or
                stderr).
            pfx (str): the current debug output prefix string (only needed if emitting
                more than one line).

        Returns:
            The same tuple as `RelativeQuadraticBezierCurve.render`.
        """
        # pylint: disable=unused-argument
        rendered, resolved, initial_point = self.render(
            gsd_registry, style, last_item, initial_point
        )
        debug_stream.write(
            f"{self} resolved to {resolved} "
            f"then to {resolved.to_cubic_curve(last_item.end_point)}\n"
        )

        return rendered, resolved, initial_point


class Arc(NamedTuple):
    """
    An elliptical arc path element.

    The arc is drawn from the end of the current path element to its specified end point
    using a number of parameters to determine how it is constructed.

    See: `PaintedPath.arc_to`
    """

    radii: Point
    """
    The x- and y-radii of the arc. If `radii.x == radii.y` the arc will be circular.
    """
    rotation: Number
    """The rotation of the arc's major/minor axes relative to the coordinate frame."""
    large: bool
    """If True, sweep the arc over an angle greater than or equal to 180 degrees."""
    sweep: bool
    """If True, the arc is swept in the positive angular direction."""
    end: Point
    """The end point of the arc."""

    @staticmethod
    @force_nodocument
    def subdivde_sweep(sweep_angle):
        """
        A generator that subdivides a swept angle into segments no larger than a quarter
        turn.

        Any sweep that is larger than a quarter turn is subdivided into as many equally
        sized segments as necessary to prevent any individual segment from being larger
        than a quarter turn.

        This is used for approximating a circular curve segment using cubic Bézier
        curves. This computes the parameters used for the Bézier approximation up
        front, as well as the transform necessary to place the segment in the correct
        position.

        Args:
            sweep_angle (Number): the angle to subdivide.

        Yields:
            A tuple of (ctrl1, ctrl2, end) representing the control and end points of
            the cubic Bézier curve approximating the segment as a unit circle centered
            at the origin.
        """
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
        """
        Approximate this arc with a sequence of `BezierCurve`.

        Args:
            last_item: the previous path element (used for its end point)

        Returns:
            a list of `BezierCurve`.
        """
        radii = self.radii

        reverse = Transform.rotation(-self.rotation)
        forward = Transform.rotation(self.rotation)

        prime = ((last_item.end_point - self.end) * 0.5) @ reverse

        lam_da = (prime.x / radii.x) ** 2 + (prime.y / radii.y) ** 2

        if lam_da > 1:
            radii = Point(x=(lam_da**0.5) * radii.x, y=(lam_da**0.5) * radii.y)

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

    @force_nodocument
    def render(self, gsd_registry, style, last_item, initial_point):
        """
        Render this path element to its PDF representation.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command

        Returns:
            a tuple of `(str, new_last_item)`, where `new_last_item` is a resolved
            `BezierCurve`.
        """
        curves = self._approximate_arc(last_item)

        if not curves:
            return "", last_item

        return (
            " ".join(
                curve.render(gsd_registry, style, prev, initial_point)[0]
                for prev, curve in zip([last_item, *curves[:-1]], curves)
            ),
            curves[-1],
            initial_point,
        )

    @force_nodocument
    def render_debug(
        self, gsd_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command
            debug_stream (io.TextIO): the stream to which the debug output should be
                written. This is not guaranteed to be seekable (e.g. it may be stdout or
                stderr).
            pfx (str): the current debug output prefix string (only needed if emitting
                more than one line).

        Returns:
            The same tuple as `Arc.render`.
        """
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
                curve.render(gsd_registry, style, prev, initial_point)[0]
                for prev, curve in zip(previous, curves)
            ),
            curves[-1],
            initial_point,
        )


class RelativeArc(NamedTuple):
    """
    An elliptical arc path element.

    The arc is drawn from the end of the current path element to its specified end point
    using a number of parameters to determine how it is constructed.

    See: `PaintedPath.arc_relative`
    """

    radii: Point
    """
    The x- and y-radii of the arc. If `radii.x == radii.y` the arc will be circular.
    """
    rotation: Number
    """The rotation of the arc's major/minor axes relative to the coordinate frame."""
    large: bool
    """If True, sweep the arc over an angle greater than or equal to 180 degrees."""
    sweep: bool
    """If True, the arc is swept in the positive angular direction."""
    end: Point
    """The end point of the arc relative to the end of the previous path element."""

    @force_nodocument
    def render(self, gsd_registry, style, last_item, initial_point):
        """
        Render this path element to its PDF representation.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command

        Returns:
            a tuple of `(str, new_last_item)`, where `new_last_item` is a resolved
            `BezierCurve`.
        """
        return Arc(
            self.radii,
            self.rotation,
            self.large,
            self.sweep,
            last_item.end_point + self.end,
        ).render(gsd_registry, style, last_item, initial_point)

    @force_nodocument
    def render_debug(
        self, gsd_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command
            debug_stream (io.TextIO): the stream to which the debug output should be
                written. This is not guaranteed to be seekable (e.g. it may be stdout or
                stderr).
            pfx (str): the current debug output prefix string (only needed if emitting
                more than one line).

        Returns:
            The same tuple as `RelativeArc.render`.
        """
        # newline is intentionally missing here
        debug_stream.write(f"{self} resolved to ")

        return Arc(
            self.radii,
            self.rotation,
            self.large,
            self.sweep,
            last_item.end_point + self.end,
        ).render_debug(gsd_registry, style, last_item, initial_point, debug_stream, pfx)


class Rectangle(NamedTuple):
    """A pdf primitive rectangle."""

    org: Point
    """The top-left corner of the rectangle."""
    size: Point
    """The width and height of the rectangle."""

    @force_nodocument
    def render(self, gsd_registry, style, last_item, initial_point):
        """
        Render this path element to its PDF representation.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command

        Returns:
            a tuple of `(str, new_last_item)`, where `new_last_item` is a `Line` back to
            the rectangle's origin.
        """
        # pylint: disable=unused-argument

        return (
            f"{self.org.render()} {self.size.render()} re",
            Line(self.org),
            initial_point,
        )

    @force_nodocument
    def render_debug(
        self, gsd_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command
            debug_stream (io.TextIO): the stream to which the debug output should be
                written. This is not guaranteed to be seekable (e.g. it may be stdout or
                stderr).
            pfx (str): the current debug output prefix string (only needed if emitting
                more than one line).

        Returns:
            The same tuple as `Rectangle.render`.
        """
        # pylint: disable=unused-argument
        rendered, resolved, initial_point = self.render(
            gsd_registry, style, last_item, initial_point
        )
        debug_stream.write(f"{self} resolved to {rendered}\n")

        return rendered, resolved, initial_point


class RoundedRectangle(NamedTuple):
    """
    A rectangle with rounded corners.

    See: `PaintedPath.rectangle`
    """

    org: Point
    """The top-left corner of the rectangle."""
    size: Point
    """The width and height of the rectangle."""
    corner_radii: Point
    """The x- and y-radius of the corners."""

    def _decompose(self):
        items = []

        if (self.size.x == 0) and (self.size.y == 0):
            pass
        elif (self.size.x == 0) or (self.size.y == 0):
            items.append(Move(self.org))
            items.append(Line(self.org + self.size))
            items.append(Close())
        elif (self.corner_radii.x == 0) or (self.corner_radii.y == 0):
            items.append(Rectangle(self.org, self.size))
        else:
            x, y = self.org
            w, h = self.size
            rx, ry = self.corner_radii
            sign_width = (self.size.x >= 0) - (self.size.x < 0)
            sign_height = (self.size.y >= 0) - (self.size.y < 0)

            if abs(rx) > abs(w):
                rx = self.size.x

            if abs(ry) > abs(h):
                ry = self.size.y

            rx = sign_width * abs(rx)
            ry = sign_height * abs(ry)
            arc_rad = Point(rx, ry)

            items.append(Move(Point(x + rx, y)))
            items.append(Line(Point(x + w - rx, y)))
            items.append(Arc(arc_rad, 0, False, True, Point(x + w, y + ry)))
            items.append(Line(Point(x + w, y + h - ry)))
            items.append(Arc(arc_rad, 0, False, True, Point(x + w - rx, y + h)))
            items.append(Line(Point(x + rx, y + h)))
            items.append(Arc(arc_rad, 0, False, True, Point(x, y + h - ry)))
            items.append(Line(Point(x, y + ry)))
            items.append(Arc(arc_rad, 0, False, True, Point(x + rx, y)))
            items.append(Close())

        return items

    @force_nodocument
    def render(self, gsd_registry, style, last_item, initial_point):
        """
        Render this path element to its PDF representation.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command

        Returns:
            a tuple of `(str, new_last_item)`, where `new_last_item` is a resolved
            `Line`.
        """
        components = self._decompose()

        if not components:
            return "", last_item

        render_list = []
        for item in components:
            rendered, last_item, initial_point = item.render(
                gsd_registry, style, last_item, initial_point
            )
            render_list.append(rendered)

        return " ".join(render_list), Line(self.org), initial_point

    @force_nodocument
    def render_debug(
        self, gsd_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command
            debug_stream (io.TextIO): the stream to which the debug output should be
                written. This is not guaranteed to be seekable (e.g. it may be stdout or
                stderr).
            pfx (str): the current debug output prefix string (only needed if emitting
                more than one line).

        Returns:
            The same tuple as `RoundedRectangle.render`.
        """
        components = self._decompose()

        debug_stream.write(f"{self} resolved to:\n")
        if not components:
            debug_stream.write(pfx + " └─ nothing\n")
            return "", last_item

        render_list = []
        for item in components[:-1]:
            rendered, last_item, initial_point = item.render(
                gsd_registry, style, last_item, initial_point
            )
            debug_stream.write(pfx + f" ├─ {item}\n")
            render_list.append(rendered)

        rendered, last_item, initial_point = components[-1].render(
            gsd_registry, style, last_item, initial_point
        )
        debug_stream.write(pfx + f" └─ {components[-1]}\n")
        render_list.append(rendered)

        return " ".join(render_list), Line(self.org), initial_point


class Ellipse(NamedTuple):
    """
    An ellipse.

    See: `PaintedPath.ellipse`
    """

    radii: Point
    """The x- and y-radii of the ellipse"""
    center: Point
    """The abscissa and ordinate of the center of the ellipse"""

    def _decompose(self):
        items = []

        rx = abs(self.radii.x)
        ry = abs(self.radii.y)
        cx, cy = self.center

        arc_rad = Point(rx, ry)

        # this isn't the most efficient way to do this, computationally, but it's
        # internally consistent.
        if (rx != 0) and (ry != 0):
            items.append(Move(Point(cx + rx, cy)))
            items.append(Arc(arc_rad, 0, False, True, Point(cx, cy + ry)))
            items.append(Arc(arc_rad, 0, False, True, Point(cx - rx, cy)))
            items.append(Arc(arc_rad, 0, False, True, Point(cx, cy - ry)))
            items.append(Arc(arc_rad, 0, False, True, Point(cx + rx, cy)))
            items.append(Close())

        return items

    @force_nodocument
    def render(self, gsd_registry, style, last_item, initial_point):
        """
        Render this path element to its PDF representation.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command

        Returns:
            a tuple of `(str, new_last_item)`, where `new_last_item` is a resolved
            `Move` to the center of the ellipse.
        """
        components = self._decompose()

        if not components:
            return "", last_item

        render_list = []
        for item in components:
            rendered, last_item, initial_point = item.render(
                gsd_registry, style, last_item, initial_point
            )
            render_list.append(rendered)

        return " ".join(render_list), Move(self.center), initial_point

    @force_nodocument
    def render_debug(
        self, gsd_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command
            debug_stream (io.TextIO): the stream to which the debug output should be
                written. This is not guaranteed to be seekable (e.g. it may be stdout or
                stderr).
            pfx (str): the current debug output prefix string (only needed if emitting
                more than one line).

        Returns:
            The same tuple as `Ellipse.render`.
        """
        components = self._decompose()

        debug_stream.write(f"{self} resolved to:\n")
        if not components:
            debug_stream.write(pfx + " └─ nothing\n")
            return "", last_item

        render_list = []
        for item in components[:-1]:
            rendered, last_item, initial_point = item.render(
                gsd_registry, style, last_item, initial_point
            )
            debug_stream.write(pfx + f" ├─ {item}\n")
            render_list.append(rendered)

        rendered, last_item, initial_point = components[-1].render(
            gsd_registry, style, last_item, initial_point
        )
        debug_stream.write(pfx + f" └─ {components[-1]}\n")
        render_list.append(rendered)

        return " ".join(render_list), Move(self.center), initial_point


class ImplicitClose(NamedTuple):
    """
    A path close element that is conditionally rendered depending on the value of
    `GraphicsStyle.auto_close`.
    """

    # pylint: disable=no-self-use
    @force_nodocument
    def render(self, gsd_registry, style, last_item, initial_point):
        """
        Render this path element to its PDF representation.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command

        Returns:
            a tuple of `(str, new_last_item)`, where `new_last_item` is whatever the old
            last_item was.
        """
        # pylint: disable=unused-argument
        if style.auto_close:
            return "h", last_item, initial_point

        return "", last_item, initial_point

    @force_nodocument
    def render_debug(
        self, gsd_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command
            debug_stream (io.TextIO): the stream to which the debug output should be
                written. This is not guaranteed to be seekable (e.g. it may be stdout or
                stderr).
            pfx (str): the current debug output prefix string (only needed if emitting
                more than one line).

        Returns:
            The same tuple as `ImplicitClose.render`.
        """
        # pylint: disable=unused-argument
        rendered, resolved, initial_point = self.render(
            gsd_registry, style, last_item, initial_point
        )
        debug_stream.write(f"{self} resolved to {rendered}\n")

        return rendered, resolved, initial_point


class Close(NamedTuple):
    """
    A path close element.

    Instructs the renderer to draw a straight line from the end of the last path element
    to the start of the current path.

    See: `PaintedPath.close`
    """

    # pylint: disable=no-self-use
    @force_nodocument
    def render(self, gsd_registry, style, last_item, initial_point):
        """
        Render this path element to its PDF representation.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command

        Returns:
            a tuple of `(str, new_last_item)`, where `new_last_item` is whatever the old
            last_item was.
        """
        # pylint: disable=unused-argument
        return "h", Move(initial_point), initial_point

    @force_nodocument
    def render_debug(
        self, gsd_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command
            debug_stream (io.TextIO): the stream to which the debug output should be
                written. This is not guaranteed to be seekable (e.g. it may be stdout or
                stderr).
            pfx (str): the current debug output prefix string (only needed if emitting
                more than one line).

        Returns:
            The same tuple as `Close.render`.
        """
        # pylint: disable=unused-argument
        rendered, resolved, initial_point = self.render(
            gsd_registry, style, last_item, initial_point
        )
        debug_stream.write(str(self) + "\n")

        return rendered, resolved, initial_point


class DrawingContext:
    """
    Base context for a drawing in a PDF

    This context is not stylable and is mainly responsible for transforming path
    drawing coordinates into user coordinates (i.e. it ensures that the output drawing
    is correctly scaled).
    """

    def __init__(self):
        self._subitems = []

    def add_item(self, item, _copy=True):
        """
        Append an item to this drawing context

        Args:
            item (GraphicsContext, PaintedPath): the item to be appended.
            _copy (bool): if true (the default), the item will be copied before being
                appended. This prevents modifications to a referenced object from
                "retroactively" altering its style/shape and should be disabled with
                caution.
        """

        if not isinstance(item, (GraphicsContext, PaintedPath)):
            raise TypeError(f"{item} doesn't belong in a DrawingContext")

        if _copy:
            item = copy.deepcopy(item)

        self._subitems.append(item)

    @staticmethod
    def _setup_render_prereqs(style, first_point, scale, height):
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

        render_list = ["q", scale]

        return render_list, style, last_item

    def render(self, gsd_registry, first_point, scale, height, starting_style):
        """
        Render the drawing context to PDF format.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the parent document's graphics
                state registry.
            first_point (Point): the starting point to use if the first path element is
                a relative element.
            scale (Number): the scale factor to convert from PDF pt units into the
                document's semantic units (e.g. mm or in).
            height (Number): the page height. This is used to remap the coordinates to
                be from the top-left corner of the page (matching fpdf's behavior)
                instead of the PDF native behavior of bottom-left.
            starting_style (GraphicsStyle): the base style for this drawing context,
                derived from the document's current style defaults.

        Returns:
            A string composed of the PDF representation of all the paths and groups in
            this context (an empty string is returned if there are no paths or groups)
        """
        if not self._subitems:
            return ""

        render_list, style, last_item = self._setup_render_prereqs(
            starting_style, first_point, scale, height
        )

        for item in self._subitems:
            rendered, last_item, first_point = item.render(
                gsd_registry, style, last_item, first_point
            )
            if rendered:
                render_list.append(rendered)

        # there was nothing to render: the only items are the start group and scale
        # transform.
        if len(render_list) == 2:
            return ""

        style_dict_name = gsd_registry.register_style(style)
        if style_dict_name is not None:
            render_list.insert(2, f"{render_pdf_primitive(style_dict_name)} gs")
            render_list.insert(
                3,
                render_pdf_primitive(style.stroke_dash_pattern)
                + f" {number_to_str(style.stroke_dash_phase)} d",
            )

        render_list.append("Q")

        return " ".join(render_list)

    def render_debug(
        self, gsd_registry, first_point, scale, height, starting_style, debug_stream
    ):
        """
        Render the drawing context to PDF format.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the parent document's graphics
                state registry.
            first_point (Point): the starting point to use if the first path element is
                a relative element.
            scale (Number): the scale factor to convert from PDF pt units into the
                document's semantic units (e.g. mm or in).
            height (Number): the page height. This is used to remap the coordinates to
                be from the top-left corner of the page (matching fpdf's behavior)
                instead of the PDF native behavior of bottom-left.
            starting_style (GraphicsStyle): the base style for this drawing context,
                derived from the document's current style defaults.
            debug_stream (TextIO): a text stream to which a debug representation of the
                drawing structure will be written.

        Returns:
            A string composed of the PDF representation of all the paths and groups in
            this context (an empty string is returned if there are no paths or groups)
        """
        render_list, style, last_item = self._setup_render_prereqs(
            starting_style, first_point, scale, height
        )

        debug_stream.write("ROOT\n")
        for child in self._subitems[:-1]:
            debug_stream.write(" ├─ ")
            rendered, last_item = child.render_debug(
                gsd_registry, style, last_item, debug_stream, " │  "
            )
            if rendered:
                render_list.append(rendered)

        if self._subitems:
            debug_stream.write(" └─ ")
            rendered, last_item, first_point = self._subitems[-1].render_debug(
                gsd_registry, style, last_item, first_point, debug_stream, "    "
            )
            if rendered:
                render_list.append(rendered)

            # there was nothing to render: the only items are the start group and scale
            # transform.
            if len(render_list) == 2:
                return ""

            style_dict_name = gsd_registry.register_style(style)
            if style_dict_name is not None:
                render_list.insert(2, f"{render_pdf_primitive(style_dict_name)} gs")
                render_list.insert(
                    3,
                    render_pdf_primitive(style.stroke_dash_pattern)
                    + f" {number_to_str(style.stroke_dash_phase)} d",
                )

            render_list.append("Q")

            return " ".join(render_list)

        return ""


class PaintedPath:
    """
    A path to be drawn by the PDF renderer.

    A painted path is defined by a style and an arbitrary sequence of path elements,
    which include the primitive path elements (`Move`, `Line`, `BezierCurve`, ...) as
    well as arbitrarily nested `GraphicsContext` containing their own sequence of
    primitive path elements and `GraphicsContext`.
    """

    def __init__(self, x=0, y=0):
        self._root_graphics_context = GraphicsContext()
        self._graphics_context = self._root_graphics_context

        self._closed = True
        self._close_context = self._graphics_context

        self._starter_move = Move(Point(x, y))

    def __deepcopy__(self, memo):
        # there's no real way to recover the matching current _graphics_context after
        # copying the root context, but that's ok because we can just disallow copying
        # of paths under modification as that is almost certainly wrong usage.
        if self._graphics_context is not self._root_graphics_context:
            raise RuntimeError(f"cannot copy path {self} while it is being modified")

        copied = self.__class__()
        copied._root_graphics_context = copy.deepcopy(self._root_graphics_context, memo)
        copied._graphics_context = copied._root_graphics_context
        copied._closed = self._closed
        copied._close_context = copied._graphics_context

        return copied

    @property
    def style(self):
        """The `GraphicsStyle` applied to all elements of this path."""
        return self._root_graphics_context.style

    @property
    def transform(self):
        """The `Transform` that applies to all of the elements of this path."""
        return self._root_graphics_context.transform

    @transform.setter
    def transform(self, tf):
        self._root_graphics_context.transform = tf

    @property
    def auto_close(self):
        """If true, the path should automatically close itself before painting."""
        return self.style.auto_close

    @auto_close.setter
    def auto_close(self, should):
        self.style.auto_close = should

    @property
    def paint_rule(self):
        """Manually specify the `PathPaintRule` to use for rendering the path."""
        return self.style.paint_rule

    @paint_rule.setter
    def paint_rule(self, style):
        self.style.paint_rule = style

    @property
    def clipping_path(self):
        """Set the clipping path for this path."""
        return self._root_graphics_context.clipping_path

    @clipping_path.setter
    def clipping_path(self, new_clipath):
        self._root_graphics_context.clipping_path = new_clipath

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
        Apply the provided `Transform` to all points added within this context.
        """
        with self._new_graphics_context() as ctxt:
            ctxt.transform = transform
            yield self

    def add_path_element(self, item, _copy=True):
        """
        Add the given element as a path item of this path.

        Args:
            item: the item to add to this path.
            _copy (bool): if true (the default), the item will be copied before being
                appended. This prevents modifications to a referenced object from
                "retroactively" altering its style/shape and should be disabled with
                caution.
        """
        if self._starter_move is not None:
            self._closed = False
            self._graphics_context.add_item(self._starter_move, _copy=False)
            self._close_context = self._graphics_context
            self._starter_move = None

        self._graphics_context.add_item(item, _copy=_copy)

    def remove_last_path_element(self):
        self._graphics_context.remove_last_item()

    def rectangle(self, x, y, w, h, rx=0, ry=0):
        """
        Append a rectangle as a closed subpath to the current path.

        If the width or the height are 0, the rectangle will be collapsed to a line
        (unless they're both 0, in which case it's collapsed to nothing).

        Args:
            x (Number): the abscissa of the starting corner of the rectangle.
            y (Number): the ordinate of the starting corner of the rectangle.
            w (Number): the width of the rectangle (if 0, the rectangle will be
                rendered as a vertical line).
            h (Number): the height of the rectangle (if 0, the rectangle will be
                rendered as a horizontal line).
            rx (Number): the x-radius of the rectangle rounded corner (if 0 the corners
                will not be rounded).
            ry (Number): the y-radius of the rectangle rounded corner (if 0 the corners
                will not be rounded).

        Returns:
            The path, to allow chaining method calls.
        """

        self._insert_implicit_close_if_open()
        self.add_path_element(
            RoundedRectangle(Point(x, y), Point(w, h), Point(rx, ry)), _copy=False
        )
        self._closed = True
        self.move_to(x, y)

        return self

    def circle(self, cx, cy, r):
        """
        Append a circle as a closed subpath to the current path.

        Args:
            cx (Number): the abscissa of the circle's center point.
            cy (Number): the ordinate of the circle's center point.
            r (Number): the radius of the circle.

        Returns:
            The path, to allow chaining method calls.
        """
        return self.ellipse(cx, cy, r, r)

    def ellipse(self, cx, cy, rx, ry):
        """
        Append an ellipse as a closed subpath to the current path.

        Args:
            cx (Number): the abscissa of the ellipse's center point.
            cy (Number): the ordinate of the ellipse's center point.
            rx (Number): the x-radius of the ellipse.
            ry (Number): the y-radius of the ellipse.

        Returns:
            The path, to allow chaining method calls.
        """
        self._insert_implicit_close_if_open()
        self.add_path_element(Ellipse(Point(rx, ry), Point(cx, cy)), _copy=False)
        self._closed = True
        self.move_to(cx, cy)

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
        if self._starter_move is not None:
            self._closed = False
            self._graphics_context.add_item(self._starter_move, _copy=False)
            self._close_context = self._graphics_context
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
        self.add_path_element(Line(Point(x, y)), _copy=False)
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
        self.add_path_element(RelativeLine(Point(dx, dy)), _copy=False)
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
        self.add_path_element(HorizontalLine(x), _copy=False)
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
        self.add_path_element(RelativeHorizontalLine(dx), _copy=False)
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
        self.add_path_element(VerticalLine(y), _copy=False)
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
        self.add_path_element(RelativeVerticalLine(dy), _copy=False)
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

        self.add_path_element(BezierCurve(ctrl1, ctrl2, end), _copy=False)
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
                end point of the previous path element
            dy2 (Number): ordinate offset of the second control point relative to the
                end point of the previous path element
            dx3 (Number): abscissa offset of the end point relative to the end point of
                the previous path element
            dy3 (Number): ordinate offset of the end point relative to the end point of
                the previous path element

        Returns:
            The path, to allow chaining method calls.
        """
        c1d = Point(dx1, dy1)
        c2d = Point(dx2, dy2)
        end = Point(dx3, dy3)

        self.add_path_element(RelativeBezierCurve(c1d, c2d, end), _copy=False)
        return self

    def quadratic_curve_to(self, x1, y1, x2, y2):
        """
        Append a cubic Bézier curve mimicking the specified quadratic Bézier curve.

        Args:
            x1 (Number): abscissa of the control point
            y1 (Number): ordinate of the control point
            x2 (Number): abscissa of the end point
            y2 (Number): ordinate of the end point

        Returns:
            The path, to allow chaining method calls.
        """
        ctrl = Point(x1, y1)
        end = Point(x2, y2)
        self.add_path_element(QuadraticBezierCurve(ctrl, end), _copy=False)
        return self

    def quadratic_curve_relative(self, dx1, dy1, dx2, dy2):
        """
        Append a cubic Bézier curve mimicking the specified quadratic Bézier curve.

        Args:
            dx1 (Number): abscissa of the control point relative to the end point of
                the previous path element
            dy1 (Number): ordinate of the control point relative to the end point of
                the previous path element
            dx2 (Number): abscissa offset of the end point relative to the end point of
                the previous path element
            dy2 (Number): ordinate offset of the end point relative to the end point of
                the previous path element

        Returns:
            The path, to allow chaining method calls.
        """
        ctrl = Point(dx1, dy1)
        end = Point(dx2, dy2)
        self.add_path_element(RelativeQuadraticBezierCurve(ctrl, end), _copy=False)
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
            x (Number): abscissa of the arc's end point.
            y (Number): ordinate of the arc's end point.
        """

        if rx == 0 or ry == 0:
            return self.line_to(x, y)

        radii = Point(abs(rx), abs(ry))
        large_arc = bool(large_arc)
        rotation = math.radians(rotation)
        positive_sweep = bool(positive_sweep)
        end = Point(x, y)

        self.add_path_element(
            Arc(radii, rotation, large_arc, positive_sweep, end), _copy=False
        )
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
            dx (Number): abscissa of the arc's end point relative to the end point of
                the previous path element.
            dy (Number): ordinate of the arc's end point relative to the end point of
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
            RelativeArc(radii, rotation, large_arc, positive_sweep, end), _copy=False
        )
        return self

    def close(self):
        """
        Explicitly close the current (sub)path.
        """
        self.add_path_element(Close(), _copy=False)
        self._closed = True
        self.move_relative(0, 0)

    def _insert_implicit_close_if_open(self):
        if not self._closed:
            self._close_context.add_item(ImplicitClose(), _copy=False)
            self._close_context = self._graphics_context
            self._closed = True

    def render(
        self, gsd_registry, style, last_item, initial_point, debug_stream=None, pfx=None
    ):
        self._insert_implicit_close_if_open()

        (
            render_list,
            last_item,
            initial_point,
        ) = self._root_graphics_context.build_render_list(
            gsd_registry, style, last_item, initial_point, debug_stream, pfx
        )

        paint_rule = GraphicsStyle.merge(style, self.style).resolve_paint_rule()

        render_list.insert(-1, paint_rule.value)

        return " ".join(render_list), last_item, initial_point

    def render_debug(
        self, gsd_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command
            debug_stream (io.TextIO): the stream to which the debug output should be
                written. This is not guaranteed to be seekable (e.g. it may be stdout or
                stderr).
            pfx (str): the current debug output prefix string (only needed if emitting
                more than one line).

        Returns:
            The same tuple as `PaintedPath.render`.
        """
        return self.render(
            gsd_registry, style, last_item, initial_point, debug_stream, pfx
        )


class ClippingPath(PaintedPath):
    """
    The PaintedPath API but to be used to create clipping paths.

    .. warning::
        Unless you really know what you're doing, changing attributes of the clipping
        path style is likely to produce unexpected results. This is because the
        clipping path styles override implicit style inheritance of the `PaintedPath`
        it applies to.

        For example, `clippath.style.stroke_width = 2` can unexpectedly override
        `paintpath.style.stroke_width = GraphicsStyle.INHERIT` and cause the painted
        path to be rendered with a stroke of 2 instead of what it would have normally
        inherited. Because a `ClippingPath` can be painted like a normal `PaintedPath`,
        it would be overly restrictive to remove the ability to style it, so instead
        this warning is here.
    """

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

    def render(
        self, gsd_registry, style, last_item, initial_point, debug_stream=None, pfx=None
    ):
        # painting the clipping path outside of its root graphics context allows it to
        # be transformed without affecting the transform of the graphics context of the
        # path it is being used to clip. This is because, unlike all of the other style
        # settings, transformations immediately affect the points following them,
        # rather than only affecting them at painting time. stroke settings and color
        # settings are applied only at paint time.

        if debug_stream:
            debug_stream.write("<ClippingPath> ")

        (
            render_list,
            last_item,
            initial_point,
        ) = self._root_graphics_context.build_render_list(
            gsd_registry,
            style,
            last_item,
            initial_point,
            debug_stream,
            pfx,
            _push_stack=False,
        )

        merged_style = GraphicsStyle.merge(style, self.style)
        # we should never get a collision error here
        intersection_rule = merged_style.intersection_rule
        if intersection_rule is merged_style.INHERIT:
            intersection_rule = ClippingPathIntersectionRule.NONZERO
        else:
            intersection_rule = ClippingPathIntersectionRule[
                intersection_rule.name  # pylint: disable=no-member, useless-suppression
            ]

        paint_rule = merged_style.resolve_paint_rule()

        render_list.append(intersection_rule.value)
        render_list.append(paint_rule.value)

        return " ".join(render_list), last_item, initial_point

    def render_debug(
        self, gsd_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            debug_stream (io.TextIO): the stream to which the debug output should be
                written. This is not guaranteed to be seekable (e.g. it may be stdout or
                stderr).
            pfx (str): the current debug output prefix string (only needed if emitting
                more than one line).

        Returns:
            The same tuple as `ClippingPath.render`.
        """
        return self.render(
            gsd_registry, style, last_item, initial_point, debug_stream, pfx
        )


class GraphicsContext:
    def __init__(self):
        self.style = GraphicsStyle()
        self.path_items = []

        self._transform = None
        self._clipping_path = None

    def __deepcopy__(self, memo):
        copied = self.__class__()
        copied.style = copy.deepcopy(self.style, memo)
        copied.path_items = copy.deepcopy(self.path_items, memo)

        copied._transform = copy.deepcopy(self.transform, memo)
        copied._clipping_path = copy.deepcopy(self.clipping_path, memo)

        return copied

    @property
    def transform(self):
        return self._transform

    @transform.setter
    def transform(self, tf):
        self._transform = tf

    @property
    def clipping_path(self):
        """The `ClippingPath` for this graphics context."""
        return self._clipping_path

    @clipping_path.setter
    def clipping_path(self, new_clipath):
        self._clipping_path = new_clipath

    def add_item(self, item, _copy=True):
        """
        Add a path element to this graphics context.

        Args:
            item: the path element to add. May be a primitive element or another
                `GraphicsContext` or a `PaintedPath`.
            _copy (bool): if true (the default), the item will be copied before being
                appended. This prevents modifications to a referenced object from
                "retroactively" altering its style/shape and should be disabled with
                caution.
        """
        if _copy:
            item = copy.deepcopy(item)

        self.path_items.append(item)

    def remove_last_item(self):
        del self.path_items[-1]

    def merge(self, other_context):
        """Copy another `GraphicsContext`'s path items into this one."""
        self.path_items.extend(other_context.path_items)

    @force_nodocument
    def build_render_list(
        self,
        gsd_registry,
        style,
        last_item,
        initial_point,
        debug_stream=None,
        pfx=None,
        _push_stack=True,
    ):
        """
        Build a list composed of all all the individual elements rendered.

        This is used by `PaintedPath` and `ClippingPath` to reuse the `GraphicsContext`
        rendering process while still being able to inject some path specific items
        (e.g. the painting directive) before the render is collapsed into a single
        string.

        Args:
            gsd_registry (GraphicsStateDictRegistry): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command
            debug_stream (io.TextIO): the stream to which the debug output should be
                written. This is not guaranteed to be seekable (e.g. it may be stdout or
                stderr).
            pfx (str): the current debug output prefix string (only needed if emitting
                more than one line).
            _push_stack (bool): if True, wrap the resulting render list in a push/pop
                graphics stack directive pair.

        Returns:
            `tuple[list[str], last_item]` where `last_item` is the past path element in
            this `GraphicsContext`
        """
        render_list = []

        if self.path_items:
            if debug_stream is not None:
                debug_stream.write(f"{self.__class__.__name__}")

            merged_style = style.__class__.merge(style, self.style)

            if debug_stream is not None:
                if self._transform:
                    debug_stream.write(f"({self._transform})")

                styles_dbg = []
                for attr in merged_style.MERGE_PROPERTIES:
                    val = getattr(merged_style, attr)
                    if val is not merged_style.INHERIT:
                        if getattr(self.style, attr) is merged_style.INHERIT:
                            inh = " (inherited)"
                        else:
                            inh = ""

                        styles_dbg.append(f"{attr}: {val}{inh}")

                if styles_dbg:
                    debug_stream.write(" {\n")
                    for style_dbg_line in styles_dbg:
                        debug_stream.write(pfx + "    ")
                        debug_stream.write(style_dbg_line)
                        debug_stream.write("\n")

                    debug_stream.write(pfx + "}┐\n")
                else:
                    debug_stream.write("\n")

            NO_EMIT_SET = {None, merged_style.INHERIT}

            emit_style = self.style
            if merged_style.allow_transparency != self.style.allow_transparency:
                emit_style = copy.deepcopy(self.style)
                emit_style.allow_transparency = merged_style.allow_transparency

            # in order to decouple the dash pattern and the dash phase at the API layer,
            # we have to perform additional logic here to recombine them. We can rely
            # on these being serializable because we always get a sane style on the
            # drawing context.
            dash_pattern = merged_style.stroke_dash_pattern
            dash_phase = merged_style.stroke_dash_phase
            if (dash_pattern != style.stroke_dash_pattern) or (
                dash_phase != style.stroke_dash_phase
            ):
                if emit_style is self.style:
                    emit_style = copy.deepcopy(emit_style)
                emit_style.stroke_dash_pattern = dash_pattern
                emit_style.stroke_dash_phase = dash_phase

                emit_dash = (dash_pattern, dash_phase)
            else:
                emit_dash = None

            style_dict_name = gsd_registry.register_style(emit_style)

            if style_dict_name is not None:
                render_list.append(f"{render_pdf_primitive(style_dict_name)} gs")

            # we can't set color in the graphics state context dictionary, so we have to
            # manually inherit it and emit it here.
            fill_color = self.style.fill_color
            stroke_color = self.style.stroke_color

            if fill_color not in NO_EMIT_SET:
                render_list.append(fill_color.serialize().lower())

            if stroke_color not in NO_EMIT_SET:
                render_list.append(stroke_color.serialize().upper())

            if emit_dash is not None:
                render_list.append(
                    render_pdf_primitive(emit_dash[0])
                    + f" {number_to_str(emit_dash[1])} d"
                )

            if debug_stream:
                if self.clipping_path is not None:
                    debug_stream.write(pfx + " ├─ ")
                    rendered_cpath, _, __ = self.clipping_path.render_debug(
                        gsd_registry,
                        merged_style,
                        last_item,
                        initial_point,
                        debug_stream,
                        pfx + " │  ",
                    )
                    if rendered_cpath:
                        render_list.append(rendered_cpath)

                for item in self.path_items[:-1]:
                    debug_stream.write(pfx + " ├─ ")
                    rendered, last_item, initial_point = item.render_debug(
                        gsd_registry,
                        merged_style,
                        last_item,
                        initial_point,
                        debug_stream,
                        pfx + " │  ",
                    )

                    if rendered:
                        render_list.append(rendered)

                debug_stream.write(pfx + " └─ ")
                rendered, last_item, initial_point = self.path_items[-1].render_debug(
                    gsd_registry,
                    merged_style,
                    last_item,
                    initial_point,
                    debug_stream,
                    pfx + "    ",
                )

                if rendered:
                    render_list.append(rendered)

            else:
                if self.clipping_path is not None:
                    rendered_cpath, _, __ = self.clipping_path.render(
                        gsd_registry, merged_style, last_item, initial_point
                    )
                    if rendered_cpath:
                        render_list.append(rendered_cpath)

                for item in self.path_items:
                    rendered, last_item, initial_point = item.render(
                        gsd_registry, merged_style, last_item, initial_point
                    )

                    if rendered:
                        render_list.append(rendered)

            # insert transform before points
            if self.transform is not None:
                render_list.insert(0, self.transform.render(last_item)[0])

            if _push_stack:
                render_list.insert(0, "q")
                render_list.append("Q")

        return render_list, last_item, initial_point

    def render(
        self,
        gsd_registry,
        style: DrawingContext,
        last_item,
        initial_point,
        debug_stream=None,
        pfx=None,
        _push_stack=True,
    ):
        render_list, last_item, initial_point = self.build_render_list(
            gsd_registry,
            style,
            last_item,
            initial_point,
            debug_stream,
            pfx,
            _push_stack=_push_stack,
        )

        return " ".join(render_list), last_item, initial_point

    def render_debug(
        self,
        gsd_registry,
        style: DrawingContext,
        last_item,
        initial_point,
        debug_stream,
        pfx,
        _push_stack=True,
    ):
        return self.render(
            gsd_registry,
            style,
            last_item,
            initial_point,
            debug_stream,
            pfx,
            _push_stack=_push_stack,
        )
