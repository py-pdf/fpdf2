from enum import Enum, IntEnum
from sys import intern

from .syntax import Name


class DocumentState(IntEnum):
    UNINITIALIZED = 0
    READY = 1  # page not started yet
    GENERATING_PAGE = 2
    CLOSED = 3  # EOF printed


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


class Align(CoerciveEnum):
    "Defines how to render text in a cell"

    C = intern("CENTER")
    "Center text horizontally"

    X = intern("X_CENTER")
    "Center text horizontally around current x position"

    L = intern("LEFT")
    "Left-align text"

    R = intern("RIGHT")
    "Right-align text"

    J = intern("JUSTIFY")
    "Justify text"

    @classmethod
    def coerce(cls, value):
        if value == "":
            return cls.L
        return super(cls, cls).coerce(value)


class RenderStyle(CoerciveEnum):
    "Defines how to render shapes"

    D = intern("DRAW")
    """
    Draw lines.
    Line color can be controlled with `fpdf.fpdf.FPDF.set_draw_color()`.
    Line thickness can be controlled with `fpdf.fpdf.FPDF.set_line_width()`.
    """

    F = intern("FILL")
    """
    Fill areas.
    Filling color can be controlled with `fpdf.fpdf.FPDF.set_fill_color()`.
    """

    DF = intern("DRAW_FILL")
    "Draw lines and fill areas"

    @property
    def operator(self):
        return {self.D: "S", self.F: "f", self.DF: "B"}[self]

    @property
    def is_draw(self):
        return self in (self.D, self.DF)

    @property
    def is_fill(self):
        return self in (self.F, self.DF)

    @classmethod
    def coerce(cls, value):
        if not value:
            return cls.D
        if value == "FD":
            value = "DF"
        return super(cls, cls).coerce(value)


class TextMode(CoerciveIntEnum):
    "Values described in PDF spec section 'Text Rendering Mode'"
    FILL = 0
    STROKE = 1
    FILL_STROKE = 2
    INVISIBLE = 3
    FILL_CLIP = 4
    STROKE_CLIP = 5
    FILL_STROKE_CLIP = 6
    CLIP = 7


class XPos(CoerciveEnum):
    "Positional values in horizontal direction for use after printing text."

    LEFT = intern("LEFT")  # self.x
    "left end of the cell"

    RIGHT = intern("RIGHT")  # self.x + w
    "right end of the cell (default)"

    START = intern("START")
    "left start of actual text"

    END = intern("END")
    "right end of actual text"

    WCONT = intern("WCONT")
    "for write() to continue next (slightly left of END)"

    CENTER = intern("CENTER")
    "center of actual text"

    LMARGIN = intern("LMARGIN")  # self.l_margin
    "left page margin (start of printable area)"

    RMARGIN = intern("RMARGIN")  # self.w - self.r_margin
    "right page margin (end of printable area)"


class YPos(CoerciveEnum):
    "Positional values in vertical direction for use after printing text"

    TOP = intern("TOP")  # self.y
    "top of the first line (default)"

    LAST = intern("LAST")
    "top of the last line (same as TOP for single-line text)"

    NEXT = intern("NEXT")  # LAST + h
    "top of next line (bottom of current text)"

    TMARGIN = intern("TMARGIN")  # self.t_margin
    "top page margin (start of printable area)"

    BMARGIN = intern("BMARGIN")  # self.h - self.b_margin
    "bottom page margin (end of printable area)"


class PageLayout(CoerciveEnum):
    "Specify the page layout shall be used when the document is opened"

    SINGLE_PAGE = Name("SinglePage")
    "Display one page at a time"

    ONE_COLUMN = Name("OneColumn")
    "Display the pages in one column"

    TWO_COLUMN_LEFT = Name("TwoColumnLeft")
    "Display the pages in two columns, with odd-numbered pages on the left"

    TWO_COLUMN_RIGHT = Name("TwoColumnRight")
    "Display the pages in two columns, with odd-numbered pages on the right"

    TWO_PAGE_LEFT = Name("TwoPageLeft")
    "Display the pages two at a time, with odd-numbered pages on the left"

    TWO_PAGE_RIGHT = Name("TwoPageRight")
    "Display the pages two at a time, with odd-numbered pages on the right"


class PageMode(CoerciveEnum):
    "Specifying how to display the document on exiting full-screen mode"

    USE_NONE = Name("UseNone")
    "Neither document outline nor thumbnail images visible"

    USE_OUTLINES = Name("UseOutlines")
    "Document outline visible"

    USE_THUMBS = Name("UseThumbs")
    "Thumbnail images visible"

    FULL_SCREEN = Name("FullScreen")
    "Full-screen mode, with no menu bar, window controls, or any other window visible"

    USE_OC = Name("UseOC")
    "Optional content group panel visible"

    USE_ATTACHMENTS = Name("UseAttachments")
    "Attachments panel visible"


class TextMarkupType(CoerciveEnum):
    "Subtype of a text markup annotation"

    HIGHLIGHT = Name("Highlight")

    UNDERLINE = Name("Underline")

    SQUIGGLY = Name("Squiggly")

    STRIKE_OUT = Name("StrikeOut")


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


class AnnotationFlag(CoerciveIntEnum):
    INVISIBLE = 1
    """
    If set, do not display the annotation if it does not belong to one of the
    standard annotation types and no annotation handler is available.
    """
    HIDDEN = 2
    "If set, do not display or print the annotation or allow it to interact with the user"
    PRINT = 4
    "If set, print the annotation when the page is printed."
    NO_ZOOM = 8
    "If set, do not scale the annotation’s appearance to match the magnification of the page."
    NO_ROTATE = 16
    "If set, do not rotate the annotation’s appearance to match the rotation of the page."
    NO_VIEW = 32
    "If set, do not display the annotation on the screen or allow it to interact with the user"
    READ_ONLY = 64
    """
    If set, do not allow the annotation to interact with the user.
    The annotation may be displayed or printed but should not respond to mouse clicks.
    """
    LOCKED = 128
    """
    If set, do not allow the annotation to be deleted or its properties
    (including position and size) to be modified by the user.
    """
    TOGGLE_NO_VIEW = 256
    "If set, invert the interpretation of the NoView flag for certain events."
    LOCKED_CONTENTS = 512
    "If set, do not allow the contents of the annotation to be modified by the user."


class AnnotationName(CoerciveEnum):
    "The name of an icon that shall be used in displaying the annotation"

    NOTE = Name("Note")
    COMMENT = Name("Comment")
    HELP = Name("Help")
    PARAGRAPH = Name("Paragraph")
    NEW_PARAGRAPH = Name("NewParagraph")
    INSERT = Name("Insert")


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


class Corner(CoerciveEnum):
    TOP_RIGHT = "TOP_RIGHT"
    TOP_LEFT = "TOP_LEFT"
    BOTTOM_RIGHT = "BOTTOM_RIGHT"
    BOTTOM_LEFT = "BOTTOM_LEFT"


# This enum is only used internally:
__pdoc__ = {"DocumentState": False}
