from enum import Enum, IntEnum

from .syntax import Name


class DocumentState(IntEnum):
    UNINITIALIZED = 0
    READY = 1  # page not started yet
    GENERATING_PAGE = 2
    CLOSED = 3  # EOF printed


class TextMode(IntEnum):
    "Values described in PDF spec section 'Text Rendering Mode'"
    FILL = 0
    STROKE = 1
    FILL_STROKE = 2
    INVISIBLE = 3
    FILL_CLIP = 4
    STROKE_CLIP = 5
    FILL_STROKE_CLIP = 6
    CLIP = 7


class XPos(IntEnum):
    """
    Positional values in horizontal direction for use after printing text.
        LEFT    - left end of the cell
        RIGHT   - right end of the cell (default)
        START   - start of actual text
        END     - end of actual text
        WCONT   - for write() to continue next (slightly left of END)
        CENTER  - center of actual text
        LMARGIN - left page margin (start of printable area)
        RMARGIN - right page margin (end of printable area)
    """

    LEFT = 1  # self.x
    RIGHT = 2  # self.x + w
    START = 3  # left end of actual text
    END = 4  # right end of actual text
    WCONT = 5  # continuation point for write()
    CENTER = 6  # center of actual text
    LMARGIN = 7  # self.l_margin
    RMARGIN = 8  # self.w - self.r_margin


class YPos(IntEnum):
    """
    Positional values in vertical direction for use after printing text.
        TOP     - top of the first line (default)
        LAST    - top of the last line (same as TOP for single-line text)
        NEXT    - top of next line (bottom of current text)
        TMARGIN - top page margin (start of printable area)
        BMARGIN - bottom page margin (end of printable area)
    """

    TOP = 1  # self.y
    LAST = 2  # top of last line (TOP for single lines)
    NEXT = 3  # LAST + h
    TMARGIN = 4  # self.t_margin
    BMARGIN = 5  # self.h - self.b_margin


class CoerciveEnum(Enum):
    """
    An enumeration that provides a helper to coerce strings into enumeration members.
    """

    @classmethod
    def coerce(cls, value):
        """
        Attempt to coerce `value` into a member of this enumeration.

        If value is already a member of this enumeration it is returned unchanged.
        Otherwise, if it is a string, attempt to convert it as an enumeration value. If
        that fails, attempt to convert it (case insensitively, by upcasing) as an
        enumeration name.

        If all different conversion attempts fail, an exception is raised.

        Args:
            value (Enum, str): the value to be coerced.

        Raises:
            ValueError: if `value` is a string but neither a member by name nor value.
            TypeError: if `value`'s type is neither a member of the enumeration nor a
                string.
        """

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


class CoerciveIntEnum(IntEnum):
    """
    An enumeration that provides a helper to coerce strings and integers into
    enumeration members.
    """

    @classmethod
    def coerce(cls, value):
        """
        Attempt to coerce `value` into a member of this enumeration.

        If value is already a member of this enumeration it is returned unchanged.
        Otherwise, if it is a string, attempt to convert it (case insensitively, by
        upcasing) as an enumeration name. Otherwise, if it is an int, attempt to
        convert it as an enumeration value.

        Otherwise, an exception is raised.

        Args:
            value (IntEnum, str, int): the value to be coerced.

        Raises:
            ValueError: if `value` is an int but not a member of this enumeration.
            ValueError: if `value` is a string but not a member by name.
            TypeError: if `value`'s type is neither a member of the enumeration nor an
                int or a string.
        """
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


class BlendMode(CoerciveEnum):
    """
    An enumeration of the named standard named blend functions supported by PDF.
    """

    NORMAL = Name("Normal")
    '''"Selects the source color, ignoring the backdrop."'''
    MULTIPLY = Name("Multiply")
    '''"Multiplies the backdrop and source color values."'''
    SCREEN = Name("Screen")
    """
    "Multiplies the complements of the backdrop and source color values, then
    complements the result."
    """
    OVERLAY = Name("Overlay")
    """
    "Multiplies or screens the colors, depending on the backdrop color value. Source
    colors overlay the backdrop while preserving its highlights and shadows. The
    backdrop color is not replaced but is mixed with the source color to reflect the
    lightness or darkness of the backdrop."
    """
    DARKEN = Name("Darken")
    '''"Selects the darker of the backdrop and source colors."'''
    LIGHTEN = Name("Lighten")
    '''"Selects the lighter of the backdrop and source colors."'''
    COLOR_DODGE = Name("ColorDodge")
    """
    "Brightens the backdrop color to reflect the source color. Painting with black
     produces no changes."
    """
    COLOR_BURN = Name("ColorBurn")
    """
    "Darkens the backdrop color to reflect the source color. Painting with white
     produces no change."
    """
    HARD_LIGHT = Name("HardLight")
    """
    "Multiplies or screens the colors, depending on the source color value. The effect
    is similar to shining a harsh spotlight on the backdrop."
    """
    SOFT_LIGHT = Name("SoftLight")
    """
    "Darkens or lightens the colors, depending on the source color value. The effect is
    similar to shining a diffused spotlight on the backdrop."
    """
    DIFFERENCE = Name("Difference")
    '''"Subtracts the darker of the two constituent colors from the lighter color."'''
    EXCLUSION = Name("Exclusion")
    """
    "Produces an effect similar to that of the Difference mode but lower in contrast.
    Painting with white inverts the backdrop color; painting with black produces no
    change."
    """
    HUE = Name("Hue")
    """
    "Creates a color with the hue of the source color and the saturation and luminosity
    of the backdrop color."
    """
    SATURATION = Name("Saturation")
    """
    "Creates a color with the saturation of the source color and the hue and luminosity
    of the backdrop color. Painting with this mode in an area of the backdrop that is
    a pure gray (no saturation) produces no change."
    """
    COLOR = Name("Color")
    """
    "Creates a color with the hue and saturation of the source color and the luminosity
    of the backdrop color. This preserves the gray levels of the backdrop and is
    useful for coloring monochrome images or tinting color images."
    """
    LUMINOSITY = Name("Luminosity")
    """
    "Creates a color with the luminosity of the source color and the hue and saturation
    of the backdrop color. This produces an inverse effect to that of the Color mode."
    """


class IntersectionRule(CoerciveEnum):
    """
    An enumeration representing the two possible PDF intersection rules.

    The intersection rule is used by the renderer to determine which points are
    considered to be inside the path and which points are outside the path. This
    primarily affects fill rendering and clipping paths.
    """

    NONZERO = "nonzero"
    """
    "The nonzero winding number rule determines whether a given point is inside a path
    by conceptually drawing a ray from that point to infinity in any direction and
    then examining the places where a segment of the path crosses the ray. Starting
    with a count of 0, the rule adds 1 each time a path segment crosses the ray from
    left to right and subtracts 1 each time a segment crosses from right to left.
    After counting all the crossings, if the result is 0, the point is outside the
    path; otherwise, it is inside."
    """
    EVENODD = "evenodd"
    """
    "An alternative to the nonzero winding number rule is the even-odd rule. This rule
    determines whether a point is inside a path by drawing a ray from that point in
    any direction and simply counting the number of path segments that cross the ray,
    regardless of direction. If this number is odd, the point is inside; if even, the
    point is outside. This yields the same results as the nonzero winding number rule
    for paths with simple shapes, but produces different results for more complex
    shapes."
    """


class PathPaintRule(CoerciveEnum):
    """
    An enumeration of the PDF drawing directives that determine how the renderer should
    paint a given path.
    """

    # the auto-close paint rules are omitted here because it's easier to just emit
    # close operators when appropriate, programmatically
    STROKE = "S"
    '''"Stroke the path."'''

    FILL_NONZERO = "f"
    """
    "Fill the path, using the nonzero winding number rule to determine the region to
    fill. Any subpaths that are open are implicitly closed before being filled."
    """

    FILL_EVENODD = "f*"
    """
    "Fill the path, using the even-odd rule to determine the region to fill. Any
    subpaths that are open are implicitly closed before being filled."
    """

    STROKE_FILL_NONZERO = "B"
    """
    "Fill and then stroke the path, using the nonzero winding number rule to determine
    the region to fill. This operator produces the same result as constructing two
    identical path objects, painting the first with `FILL_NONZERO` and the second with
    `STROKE`."
    """

    STROKE_FILL_EVENODD = "B*"
    """
    "Fill and then stroke the path, using the even-odd rule to determine the region to
    fill. This operator produces the same result as `STROKE_FILL_NONZERO`, except that
    the path is filled as if with `FILL_EVENODD` instead of `FILL_NONZERO`."
    """

    DONT_PAINT = "n"
    """
    "End the path object without filling or stroking it. This operator is a
    path-painting no-op, used primarily for the side effect of changing the current
    clipping path."
    """

    AUTO = "auto"
    """
    Automatically determine which `PathPaintRule` should be used.

    PaintedPath will select one of the above `PathPaintRule`s based on the resolved
    set/inherited values of its style property.
    """


class ClippingPathIntersectionRule(CoerciveEnum):
    """
    An enumeration of the PDF drawing directives that define a path as a clipping path.
    """

    NONZERO = "W"
    """
    "The nonzero winding number rule determines whether a given point is inside a path
    by conceptually drawing a ray from that point to infinity in any direction and
    then examining the places where a segment of the path crosses the ray. Starting
    with a count of 0, the rule adds 1 each time a path segment crosses the ray from
    left to right and subtracts 1 each time a segment crosses from right to left.
    After counting all the crossings, if the result is 0, the point is outside the
    path; otherwise, it is inside."
    """
    EVENODD = "W*"
    """
    "An alternative to the nonzero winding number rule is the even-odd rule. This rule
    determines whether a point is inside a path by drawing a ray from that point in
    any direction and simply counting the number of path segments that cross the ray,
    regardless of direction. If this number is odd, the point is inside; if even, the
    point is outside. This yields the same results as the nonzero winding number rule
    for paths with simple shapes, but produces different results for more complex
    shapes."""


class StrokeCapStyle(CoerciveIntEnum):
    """
    An enumeration of values defining how the end of a stroke should be rendered.

    This affects the ends of the segments of dashed strokes, as well.
    """

    BUTT = 0
    """
    "The stroke is squared off at the endpoint of the path. There is no projection
    beyond the end of the path."
    """
    ROUND = 1
    """
    "A semicircular arc with a diameter equal to the line width is drawn around the
    endpoint and filled in."
    """
    SQUARE = 2
    """
    "The stroke continues beyond the endpoint of the path for a distance equal to half
    the line width and is squared off."
    """


class StrokeJoinStyle(CoerciveIntEnum):
    """
    An enumeration of values defining how the corner joining two path components should
    be rendered.
    """

    MITER = 0
    """
    "The outer edges of the strokes for the two segments are extended until they meet at
    an angle, as in a picture frame. If the segments meet at too sharp an angle
    (as defined by the miter limit parameter), a bevel join is used instead."
    """
    ROUND = 1
    """
    "An arc of a circle with a diameter equal to the line width is drawn around the
    point where the two segments meet, connecting the outer edges of the strokes for
    the two segments. This pieslice-shaped figure is filled in, pro- ducing a rounded
    corner."
    """
    BEVEL = 2
    """
    "The two segments are finished with butt caps and the resulting notch beyond the
    ends of the segments is filled with a triangle."
    """


class PDFStyleKeys(Enum):
    """
    An enumeration of the graphics state parameter dictionary keys.
    """

    FILL_ALPHA = Name("ca")
    BLEND_MODE = Name("BM")  # shared between stroke and fill
    STROKE_ALPHA = Name("CA")
    STROKE_ADJUSTMENT = Name("SA")
    STROKE_WIDTH = Name("LW")
    STROKE_CAP_STYLE = Name("LC")
    STROKE_JOIN_STYLE = Name("LJ")
    STROKE_MITER_LIMIT = Name("ML")
    STROKE_DASH_PATTERN = Name("D")  # array of array, number, e.g. [[1 1] 0]
