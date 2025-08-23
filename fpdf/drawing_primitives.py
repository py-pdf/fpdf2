"""
Core drawing primitives for fpdf2.

This module defines the fundamental data structures used throughout the
drawing API, including:

- Color models: ``DeviceRGB``, ``DeviceGray``, ``DeviceCMYK``
- Geometric primitives: ``Point``
- Transformation matrices: ``Transform``

These classes are intentionally lightweight and self-contained so they can be
safely imported from any other drawing-related module without creating circular
dependencies.

All higher-level drawing features (paths, patterns, gradients, etc.) build on
top of these primitives.
"""

import decimal
import math

# type alias:
from collections.abc import Sequence
from typing import NamedTuple, Optional, Union

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


Number = Union[int, float, decimal.Decimal]
NumberClass = (int, float, decimal.Decimal)


def check_range(value, minimum=0.0, maximum=1.0):
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
            check_range(a)

        return super().__new__(cls, check_range(r), check_range(g), check_range(b), a)

    @property
    def colors(self):
        "The color components as a tuple in order `(r, g, b)` with alpha omitted, in range 0-1."
        return self[:-1]

    @property
    def colors255(self):
        "The color components as a tuple in order `(r, g, b)` with alpha omitted, in range 0-255."
        return tuple(255 * v for v in self.colors)

    def serialize(self) -> str:
        return " ".join(number_to_str(val) for val in self.colors) + f" {self.OPERATOR}"

    def is_achromatic(self) -> bool:
        # Treat tiny diffs as equal to avoid float noise
        return abs(self.r - self.g) < 1e-9 and abs(self.g - self.b) < 1e-9

    def to_gray(self) -> "DeviceGray":
        # sRGB luminance
        return DeviceGray(0.2126 * self.r + 0.7152 * self.g + 0.0722 * self.b)


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
            check_range(a)

        return super().__new__(cls, check_range(g), a)

    @property
    def colors(self):
        "The color components as a tuple in order (r, g, b) with alpha omitted, in range 0-1."
        return self.g, self.g, self.g

    @property
    def colors255(self):
        "The color components as a tuple in order `(r, g, b)` with alpha omitted, in range 0-255."
        return tuple(255 * v for v in self.colors)

    def serialize(self) -> str:
        return f"{number_to_str(self.g)} {self.OPERATOR}"


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
            check_range(a)

        return super().__new__(
            cls, check_range(c), check_range(m), check_range(y), check_range(k), a
        )

    @property
    def colors(self):
        "The color components as a tuple in order (c, m, y, k) with alpha omitted, in range 0-1."
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
    if a is None:
        if r == g == b:
            return DeviceGray(r / 255.0)
    else:
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
    if isinstance(r, (DeviceCMYK, DeviceGray, DeviceRGB)):
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
        hexstr (str): of the form `#RGB`, `#RGBA`, `#RRGGBB`, or `#RRGGBBAA` (case
            insensitive). Must include the leading octothorp. Forms omitting the alpha
            field are interpreted as not specifying the opacity, so it will not be
            explicitly set.

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

    x: float
    """The abscissa of the point."""

    y: float
    """The ordinate of the point."""

    def render(self) -> str:
        """Render the point to the string `"x y"` for emitting to a PDF."""

        return f"{number_to_str(self.x)} {number_to_str(self.y)}"

    def dot(self, other: "Point") -> float:
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

    def angle(self, other: "Point") -> float:
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
        if self.mag() * other.mag() == 0:  # Prevent division by 0
            return 0.0
        return sign * math.acos(round(self.dot(other) / (self.mag() * other.mag()), 8))

    def mag(self) -> float:
        """
        Compute the Cartesian distance from this point to the origin

        This is the same as computing the magnitude of the vector represented by this
        point.

        Returns:
            The scalar result of the distance computation.
        """

        return (self.x**2 + self.y**2) ** 0.5

    @force_document
    def __add__(self, other: "Point") -> "Point":
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
    def __sub__(self, other: "Point") -> "Point":
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
    def __neg__(self) -> "Point":
        """
        Produce a point by negating this point's coordinates.

        Returns:
            A Point whose coordinates are this points coordinates negated.
        """
        return Point(x=-self.x, y=-self.y)

    @force_document
    def __mul__(self, other: "Point") -> "Point":
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
    def __truediv__(self, other: Number) -> "Point":
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
            return Point(self.x / float(other), self.y / float(other))

        return NotImplemented

    @force_document
    def __floordiv__(self, other: Number) -> "Point":
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
            return Point(self.x // float(other), self.y // float(other))

        return NotImplemented

    # no __r(true|floor)div__ because division is not commutative!

    @force_document
    def __matmul__(self, other: "Transform") -> "Point":
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

    def __str__(self) -> str:
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
    def identity(cls) -> "Transform":
        """
        Create a transform representing the identity transform.

        The identity transform is a no-op.
        """
        return cls(1, 0, 0, 1, 0, 0)

    @classmethod
    def translation(cls, x: Number, y: Number) -> "Transform":
        """
        Create a transform that performs translation.

        Args:
            x (Number): distance to translate points along the x (horizontal) axis.
            y (Number): distance to translate points along the y (vertical) axis.

        Returns:
            A Transform representing the specified translation.
        """

        return cls(1, 0, 0, 1, float(x), float(y))

    @classmethod
    def scaling(cls, x: Number, y: Optional[Number] = None) -> "Transform":
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

        return cls(float(x), 0, 0, float(y), 0, 0)

    @classmethod
    def rotation(cls, theta: Number) -> "Transform":
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
    def rotation_d(cls, theta_d: Number) -> "Transform":
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
    def shearing(cls, x: Number, y: Optional[Number] = None) -> "Transform":
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
        return cls(1, float(y), float(x), 1, 0, 0)

    @classmethod
    def skewing(cls, ax: Number = 0, ay: Optional[Number] = None) -> "Transform":
        """
        Create a skew (shear) transform using angles **in radians**.

        Args:
            ax (Number): skew angle along the X axis (radians).
                Positive ax produces x' = x + tan(ax) * y
            ay (Number): optional skew angle along the Y axis (radians).
                Positive ay produces y' = y + tan(ay) * x
                If omitted, defaults to the value of `ax`.

        Returns:
            A Transform representing the specified skew.
        """
        if ay is None:
            ay = ax
        return cls(1, math.tan(float(ay)), math.tan(float(ax)), 1, 0, 0)

    @classmethod
    def skewing_d(cls, ax_d: Number = 0, ay_d: Optional[Number] = None) -> "Transform":
        """
        Create a skew (shear) transform using angles **in degrees**.

        Args:
            ax_d (Number): skew angle along X in degrees.
            ay_d (Number): optional skew angle along Y in degrees. If omitted, defaults to ax_d.

        Returns:
            A Transform representing the specified skew.

        Raises:
            ValueError: if an angle is too close to 90° + k·180° (infinite shear).
        """
        if ay_d is None:
            ay_d = ax_d
        ax = math.radians(float(ax_d))
        ay = math.radians(float(ay_d))
        # Guard against tan() blow-ups near ±90° (+ k·180°)
        eps = 1e-12
        if abs(math.cos(ax)) < eps or abs(math.cos(ay)) < eps:
            raise ValueError("Skew angle produces infinite shear (near 90° + k·180°).")
        return cls.skewing(ax, ay)

    def translate(self, x: Number, y: Number) -> "Transform":
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

    def scale(self, x: Number, y: Optional[Number] = None) -> "Transform":
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

    def rotate(self, theta: Number) -> "Transform":
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

    def rotate_d(self, theta_d: Number) -> "Transform":
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

    def shear(self, x: Number, y: Optional[Number] = None) -> "Transform":
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

    def skew(self, ax: Number = 0, ay: Optional[Number] = None) -> "Transform":
        """Compose with a skew (radians)."""
        return self @ Transform.skewing(ax, ay)

    def skew_d(self, ax_d: Number = 0, ay_d: Optional[Number] = None) -> "Transform":
        """Compose with a skew (degrees)."""
        return self @ Transform.skewing_d(ax_d, ay_d)

    def about(self, x: Number, y: Number) -> "Transform":
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

    def inverse(self) -> "Transform":
        """
        Produce a transform that is the inverse of this transform.

        Returns:
            A Transform representing the inverse of this transform.

        Raises:
            ValueError: if the transform is not invertible.
        """
        det = self.a * self.d - self.b * self.c
        if det == 0:
            raise ValueError("Transform is not invertible")

        return Transform(
            a=self.d / det,
            b=-self.b / det,
            c=-self.c / det,
            d=self.a / det,
            e=(self.c * self.f - self.d * self.e) / det,
            f=(self.b * self.e - self.a * self.f) / det,
        )

    @force_document
    def __mul__(self, other: Number) -> "Transform":
        """
        Multiply the individual transform parameters by a scalar value.

        Args:
            other (Number): the scalar value by which to multiply the parameters

        Returns:
            A Transform with the modified parameters.
        """
        if isinstance(other, NumberClass):
            other = float(other)
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
    def __matmul__(self, other: "Transform") -> "Transform":
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

    def render(self, last_item: "Renderable") -> tuple[str, "Renderable"]:
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

    def __str__(self) -> str:
        return (
            f"transform: ["
            f"{number_to_str(self.a)} {number_to_str(self.b)} 0; "
            f"{number_to_str(self.c)} {number_to_str(self.d)} 0; "
            f"{number_to_str(self.e)} {number_to_str(self.f)} 1]"
        )

    def row_norms(self) -> tuple[float, float]:
        """
        Returns (sqrt(a² + c²), sqrt(b² + d²)), i.e. the Euclidean norms of
        those rows. These values bound how much the transform can stretch geometry along the
        device X and Y axes, respectively, and are useful for inflating axis-aligned
        bounding boxes to account for stroke width under the CTM.
        """
        return (math.hypot(self.a, self.c), math.hypot(self.b, self.d))


__pdoc__["Transform.a"] = False
__pdoc__["Transform.b"] = False
__pdoc__["Transform.c"] = False
__pdoc__["Transform.d"] = False
__pdoc__["Transform.e"] = False
__pdoc__["Transform.f"] = False
