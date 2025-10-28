"""
Vector drawing: managing colors, graphics states, paths, transforms...

The contents of this module are internal to fpdf2, and not part of the public API.
They may change at any time without prior warning or any deprecation period,
in non-backward-compatible ways.

Usage documentation at: <https://py-pdf.github.io/fpdf2/Drawing.html>
"""

import decimal
import math
from collections import OrderedDict
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Generator,
    NamedTuple,
    Optional,
    Protocol,
    Union,
    runtime_checkable,
)

from fpdf.drawing_primitives import (
    DeviceCMYK,
    DeviceGray,
    DeviceRGB,
    Number,
    NumberClass,
    Point,
    Transform,
    check_range,
    color_from_hex_string,
    force_nodocument,
    number_to_str,
)

from .enums import (
    BlendMode,
    ClippingPathIntersectionRule,
    CompositingOperation,
    GradientSpreadMethod,
    GradientUnits,
    IntersectionRule,
    PathPaintRule,
    PDFResourceType,
    PDFStyleKeys,
    StrokeCapStyle,
    StrokeJoinStyle,
)
from .pattern import (
    Gradient,
    Pattern,
    LinearGradient,
    RadialGradient,
    SweepGradient,
    shape_linear_gradient,
    shape_radial_gradient,
)
from .syntax import Name, Raw
from .util import escape_parens

from fontTools.pens.basePen import BasePen

if TYPE_CHECKING:
    from .output import ResourceCatalog


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


class GradientPaint:
    """Fill/stroke paint using a gradient"""

    __slots__ = (
        "gradient",
        "units",
        "gradient_transform",
        "apply_page_ctm",
        "skip_alpha",
        "spread_method",
    )

    def __init__(
        self,
        gradient: "Gradient",
        units: Union[GradientUnits, str] = GradientUnits.USER_SPACE_ON_USE,
        gradient_transform: Optional["Transform"] = None,
        apply_page_ctm: bool = True,
        spread_method: Optional[Union[str, GradientSpreadMethod]] = None,
    ):
        self.gradient = gradient
        self.units = GradientUnits.coerce(units)
        self.gradient_transform = gradient_transform or Transform.identity()
        self.apply_page_ctm = apply_page_ctm
        self.skip_alpha = False
        self.spread_method = (
            GradientSpreadMethod.coerce(spread_method)
            if spread_method is not None
            else GradientSpreadMethod.PAD
        )

    def _matrix_for(self, bbox: Optional["BoundingBox"]) -> "Transform":
        """Return the final /Matrix for this gradient, given an optional bbox."""
        if self.units == GradientUnits.OBJECT_BOUNDING_BOX:
            if bbox is None:
                raise RuntimeError(
                    "GradientPaint requires bbox for objectBoundingBox units"
                )
            # Map [0,1]x[0,1] object space, then apply gradient_transform
            matrix_bbox = Transform(
                a=bbox.width, b=0, c=0, d=bbox.height, e=bbox.x0, f=bbox.y0
            )
            return self.gradient_transform @ matrix_bbox
        # userSpaceOnUse: only the provided gradient_transform
        return self.gradient_transform

    def _register_pattern(self, resource_catalog, gradient, matrix: "Transform") -> str:
        """Create a Pattern with the given matrix, register shading+pattern, return pattern name."""
        resource_catalog.add(PDFResourceType.SHADING, gradient, None)
        pattern = Pattern(gradient).set_matrix(matrix)
        pattern.set_apply_page_ctm(self.apply_page_ctm)
        return resource_catalog.add(PDFResourceType.PATTERN, pattern, None)

    def emit_fill(self, resource_catalog, bbox: Optional["BoundingBox"]) -> str:
        domain_bbox = (
            BoundingBox(0.0, 0.0, 1.0, 1.0)
            if self.units == GradientUnits.OBJECT_BOUNDING_BOX
            else bbox
        )
        gradient = self._get_gradient_with_spread_method(domain_bbox)
        matrix = self._matrix_for(bbox)
        pattern_name = self._register_pattern(resource_catalog, gradient, matrix)
        return f"/Pattern cs /{pattern_name} scn"

    def emit_stroke(self, resource_catalog, bbox: Optional["BoundingBox"]) -> str:
        domain_bbox = (
            BoundingBox(0.0, 0.0, 1.0, 1.0)
            if self.units == GradientUnits.OBJECT_BOUNDING_BOX
            else bbox
        )
        gradient = self._get_gradient_with_spread_method(domain_bbox)
        matrix = self._matrix_for(bbox)
        pattern_name = self._register_pattern(resource_catalog, gradient, matrix)
        return f"/Pattern CS /{pattern_name} SCN"

    def has_alpha(self) -> bool:
        return self.gradient and self.gradient.has_alpha() and not self.skip_alpha

    def _register_alpha_pattern(
        self, resource_catalog, matrix: "Transform", bbox: "BoundingBox"
    ) -> str:
        alpha_shading = self.gradient.get_alpha_shading_object(bbox)
        if alpha_shading is None:
            raise RuntimeError("Alpha gradient requested but no alpha ramp found")
        # Register the shading and wrap it into a Pattern using the same matrix
        resource_catalog.add(PDFResourceType.SHADING, alpha_shading, None)
        alpha_pattern = Pattern(alpha_shading).set_matrix(matrix)
        alpha_pattern.set_apply_page_ctm(False)
        return resource_catalog.add(PDFResourceType.PATTERN, alpha_pattern, None)

    def _get_gradient_with_spread_method(self, bbox: "BoundingBox") -> Gradient:
        """
        Now that the bbox is known, we can construct a new gradient stop line to apply
        the spread method reflect or repeat.
        """

        if isinstance(self.gradient, SweepGradient):
            self.gradient.spread_method = self.spread_method
            return self.gradient.get_shading_object(bbox)

        if self.spread_method == GradientSpreadMethod.PAD:
            return self.gradient  # nothing to do

        if isinstance(self.gradient, LinearGradient):
            x1, y1, x2, y2 = self.gradient.coords
            raw_stops = getattr(self.gradient, "raw_stops", None)
            if raw_stops is None:
                colors = self.gradient.colors
                bounds = self.gradient.bounds
                stops = (
                    [(0.0, colors[0])]
                    + list(zip(bounds, colors[1:-1]))
                    + [(1.0, colors[-1])]
                )
            else:
                stops = raw_stops

            spread_bbox = bbox
            if (
                bbox is not None
                and self.units == GradientUnits.USER_SPACE_ON_USE
                and self.gradient_transform is not None
            ):
                try:
                    spread_bbox = bbox.transformed(self.gradient_transform.inverse())
                except ValueError:
                    spread_bbox = bbox

            return shape_linear_gradient(
                x1,
                y1,
                x2,
                y2,
                stops,
                spread_method=self.spread_method,
                bbox=spread_bbox,
            )

        if isinstance(self.gradient, RadialGradient):
            (fx, fy, fr, cx, cy, r) = self.gradient.coords
            raw_stops = getattr(self.gradient, "raw_stops", None)
            if raw_stops is None:
                colors = self.gradient.colors
                bounds = self.gradient.bounds
                stops = (
                    [(0.0, colors[0])]
                    + list(zip(bounds, colors[1:-1]))
                    + [(1.0, colors[-1])]
                )
            else:
                stops = raw_stops
            spread_bbox = bbox
            if (
                bbox is not None
                and self.units == GradientUnits.USER_SPACE_ON_USE
                and self.gradient_transform is not None
            ):
                try:
                    spread_bbox = bbox.transformed(self.gradient_transform.inverse())
                except ValueError:
                    spread_bbox = bbox

            return shape_radial_gradient(
                cx,
                cy,
                r,
                stops,
                fx=fx,
                fy=fy,
                fr=fr,
                spread_method=self.spread_method,
                bbox=spread_bbox,
            )

        return self.gradient  # unknown gradient type, return as is


class _AlphaGradientPaint(GradientPaint):

    def emit_fill(self, resource_catalog, bbox: "BoundingBox") -> str:
        domain_bbox = (
            BoundingBox(0.0, 0.0, 1.0, 1.0)
            if self.units == GradientUnits.OBJECT_BOUNDING_BOX
            else bbox
        )
        matrix = self._matrix_for(bbox)
        pattern_name = self._register_alpha_pattern(
            resource_catalog, matrix, domain_bbox
        )
        return f"/Pattern cs /{pattern_name} scn"

    def emit_stroke(self, resource_catalog, bbox: "BoundingBox") -> str:
        domain_bbox = (
            BoundingBox(0.0, 0.0, 1.0, 1.0)
            if self.units == GradientUnits.OBJECT_BOUNDING_BOX
            else bbox
        )
        matrix = self._matrix_for(bbox)
        pattern_name = self._register_alpha_pattern(
            resource_catalog, matrix, domain_bbox
        )
        return f"/Pattern CS /{pattern_name} SCN"

    def has_alpha(self) -> bool:
        return False  # already on the alpha gradient, can't alpha the alpha


class BoundingBox(NamedTuple):
    """Represents a bounding box, with utility methods for creating and manipulating them."""

    x0: float
    y0: float
    x1: float
    y1: float

    @classmethod
    def empty(cls) -> "BoundingBox":
        """
        Return an 'empty' bounding box with extreme values that collapse on merge.
        """
        return cls(float("inf"), float("inf"), float("-inf"), float("-inf"))

    def is_valid(self) -> bool:
        """Return True if the bounding box is not empty."""
        return self.x0 <= self.x1 and self.y0 <= self.y1

    @classmethod
    def from_points(cls, points: list[Point]) -> "BoundingBox":
        """Given a list of points, create a bounding box that encloses them all."""
        xs = [float(p.x) for p in points]
        ys = [float(p.y) for p in points]
        return cls(min(xs), min(ys), max(xs), max(ys))

    def merge(self, other: "BoundingBox") -> "BoundingBox":
        """Expand this bounding box to include another one."""
        if not self.is_valid():
            return other
        if not other.is_valid():
            return self
        return BoundingBox(
            min(self.x0, other.x0),
            min(self.y0, other.y0),
            max(self.x1, other.x1),
            max(self.y1, other.y1),
        )

    def transformed(self, tf: Transform) -> "BoundingBox":
        """
        Return a new bounding box resulting from applying a transform to this one.
        """
        corners = [
            Point(self.x0, self.y0),
            Point(self.x1, self.y0),
            Point(self.x0, self.y1),
            Point(self.x1, self.y1),
        ]
        transformed_points = [pt @ tf for pt in corners]
        return BoundingBox.from_points(transformed_points)

    def expanded(self, dx: float, dy: Optional[float] = None) -> "BoundingBox":
        """Return a new bounding box expanded by the given amounts in each direction."""
        if dy is None:
            dy = dx
        return BoundingBox(self.x0 - dx, self.y0 - dy, self.x1 + dx, self.y1 + dy)

    def expanded_to_stroke(
        self, style: "GraphicsStyle", row_norms: tuple[float, float] = (1.0, 1.0)
    ) -> "BoundingBox":
        """Expand this bbox to include stroke coverage, given a graphics style."""

        # 1) Is there any stroke to consider?
        if not style.resolve_paint_rule() in (
            PathPaintRule.STROKE,
            PathPaintRule.STROKE_FILL_NONZERO,
            PathPaintRule.STROKE_FILL_EVENODD,
        ):
            return self

        # If stroke opacity resolves to 0, no visible stroke => no expansion
        so = getattr(style, "stroke_opacity", GraphicsStyle.INHERIT)
        if (so is not GraphicsStyle.INHERIT) and (so is not None):
            try:
                if float(so) <= 0.0:
                    return self  # no visible stroke, don't expand
            except (TypeError, ValueError):
                pass

        # 2) Effective stroke width (PDF default is 1 if unset/inherit)
        w = (
            1.00
            if style.stroke_width is None or style.stroke_width is GraphicsStyle.INHERIT
            else style.stroke_width
        )
        w = float(w)
        if w == 0.0:
            return self
        r = 0.5 * w

        # 3) Row norms from CTM to scale the half-stroke in X/Y
        nx, ny = row_norms
        return self.expanded(r * nx, r * ny)

    def to_tuple(self) -> tuple[float, float, float, float]:
        """Convert bounding box to a 4-tuple."""
        return (self.x0, self.y0, self.x1, self.y1)

    def to_pdf_array(self) -> str:
        """Convert bounding box to a PDF array string."""
        return f"[{number_to_str(self.x0)} {number_to_str(self.y0)} {number_to_str(self.x1)} {number_to_str(self.y1)}]"

    def corners(
        self,
    ) -> tuple[
        tuple[float, float],
        tuple[float, float],
        tuple[float, float],
        tuple[float, float],
    ]:
        """Clockwise corners (x,y): (x0,y0),(x1,y0),(x1,y1),(x0,y1)."""
        return (
            (self.x0, self.y0),
            (self.x1, self.y0),
            (self.x1, self.y1),
            (self.x0, self.y1),
        )

    def project_interval_on_axis(
        self, x1: float, y1: float, x2: float, y2: float
    ) -> tuple[float, float, float]:
        """
        Project bbox corners onto the axis from (x1,y1) to (x2,y2).
        Returns (tmin, tmax, L) where:
          - L is the axis length
          - t are distances along the axis with t=0 at (x1,y1)
        """
        vx, vy = (x2 - x1), (y2 - y1)
        L = math.hypot(vx, vy)
        if L == 0.0:
            return 0.0, 0.0, 0.0
        ux, uy = vx / L, vy / L
        ts = []
        for X, Y in self.corners():
            dx, dy = (X - x1), (Y - y1)
            ts.append(dx * ux + dy * uy)  # dot with unit axis
        return min(ts), max(ts), L

    def max_distance_to_point(self, cx: float, cy: float) -> float:
        """Max Euclidean distance from (cx,cy) to any bbox corner."""
        return max(math.hypot(X - cx, Y - cy) for (X, Y) in self.corners())

    @property
    def width(self) -> float:
        """Return the width of the bounding box."""
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        """Return the height of the bounding box."""
        return self.y1 - self.y0

    def __str__(self) -> str:
        return f"BoundingBox({self.x0}, {self.y0}, {self.x1}, {self.y1})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BoundingBox):
            return False
        tolerance = 1e-6
        return (
            abs(self.x0 - other.x0) < tolerance
            and abs(self.y0 - other.y0) < tolerance
            and abs(self.x1 - other.x1) < tolerance
            and abs(self.y1 - other.y1) < tolerance
        )

    def __hash__(self) -> int:
        # Round to match the tolerance used in __eq__
        return hash(
            (
                round(self.x0, 6),
                round(self.y0, 6),
                round(self.x1, 6),
                round(self.y1, 6),
            )
        )


class GraphicsStyle:
    """
    A class representing various style attributes that determine drawing appearance.

    This class uses the convention that the global Python singleton ellipsis (`...`) is
    exclusively used to represent values that are inherited from the parent style. This
    is to disambiguate the value None which is used for several values to signal an
    explicitly disabled style. An example of this is the fill/stroke color styles,
    which use None as hints to the auto paint style detection code.
    """

    _PRIVATE_SLOTS = (
        "_allow_transparency",
        "_auto_close",
        "_fill_color",
        "_intersection_rule",
        "_paint_rule",
        "_stroke_color",
        "_stroke_dash_pattern",
        "_stroke_dash_phase",
    )

    __slots__ = _PRIVATE_SLOTS + tuple(
        k.value
        for k in PDFStyleKeys
        # we do not store STROKE_DASH_PATTERN under its PDF key; it's in _stroke_dash_pattern
        if k is not PDFStyleKeys.STROKE_DASH_PATTERN
    )

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
        "soft_mask",
    )
    """An ordered collection of properties to use when merging two GraphicsStyles."""

    TRANSPARENCY_KEYS = (
        PDFStyleKeys.FILL_ALPHA.value,
        PDFStyleKeys.STROKE_ALPHA.value,
        PDFStyleKeys.BLEND_MODE.value,
        PDFStyleKeys.SOFT_MASK.value,
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
    def merge(cls, parent: "GraphicsStyle", child: "GraphicsStyle") -> "GraphicsStyle":
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
        self.soft_mask = self.INHERIT

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)  # bypass __init__
        # copy private slots directly
        for s in cls._PRIVATE_SLOTS:
            object.__setattr__(new, s, getattr(self, s, cls.INHERIT))
        # copy PDF-exposed slots (BM, ca, CA, etc.)
        for key in cls.PDF_STYLE_KEYS:
            object.__setattr__(new, key, getattr(self, key, cls.INHERIT))
        return new

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

        if isinstance(color, (DeviceRGB, DeviceGray, DeviceCMYK, GradientPaint)):
            super().__setattr__("_fill_color", color)
            if getattr(color, "a", None) is not None:
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
            check_range(new)

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

        if isinstance(color, (DeviceRGB, DeviceGray, DeviceCMYK, GradientPaint)):
            super().__setattr__("_stroke_color", color)
            if getattr(color, "a", None) is not None:
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
            check_range(new)

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

    @property
    def soft_mask(self):
        return getattr(self, PDFStyleKeys.SOFT_MASK.value)

    @soft_mask.setter
    def soft_mask(self, value):
        if value is self.INHERIT or isinstance(value, PaintSoftMask):
            return super().__setattr__(PDFStyleKeys.SOFT_MASK.value, value)
        raise TypeError(f"{value} isn't a PaintSoftMask or GraphicsStyle.INHERIT")

    def serialize(self) -> Optional[Raw]:
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
        if self.stroke_dash_pattern and self.stroke_dash_pattern is not self.INHERIT:
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

        # this signals to the graphics state registry that there is nothing to
        # register. This is a success case.
        return None

    @force_nodocument
    def resolve_paint_rule(self) -> PathPaintRule:
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


@runtime_checkable
class Renderable(Protocol):
    """
    Structural type for things that can render themselves into PDF operators
    and report a geometric bounding box.
    """

    def render(
        self,
        resource_registry: "ResourceCatalog",
        style: GraphicsStyle,
        last_item: "Renderable",
        initial_point: Point,
    ) -> tuple[str, "Renderable", Point]: ...

    def bounding_box(self, start: Point) -> tuple[BoundingBox, Point]: ...


def _render_move(pt: Point) -> str:
    return f"{pt.render()} m"


def _render_line(pt: Point) -> str:
    return f"{pt.render()} l"


def _render_curve(ctrl1: Point, ctrl2: Point, end: Point) -> str:
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
    def end_point(self) -> Point:
        """The end point of this path element."""
        return self.pt

    # pylint: disable=unused-argument
    def bounding_box(self, start) -> tuple[BoundingBox, Point]:
        bbox = BoundingBox.empty()
        return bbox, self.pt

    @force_nodocument
    def render(
        self,
        resource_registry: "ResourceCatalog",
        style: GraphicsStyle,
        last_item: Renderable,
        initial_point: Point,
    ) -> tuple[str, Renderable, Point]:
        """
        Render this path element to its PDF representation.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command

        Returns:
            a tuple of `(str, new_last_item)`, where `new_last_item` is `self`
        """
        return _render_move(self.pt), self, self.pt

    # pylint: disable=unused-argument
    @force_nodocument
    def render_debug(
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
        rendered, resolved, initial_point = self.render(
            resource_registry, style, last_item, initial_point
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

    def bounding_box(self, start: Point) -> tuple[BoundingBox, Point]:
        """RelativeMove doesn't draw anything, so it has no bounding box."""
        return BoundingBox.empty(), start + self.pt

    @force_nodocument
    def render(
        self,
        resource_registry: "ResourceCatalog",
        style: GraphicsStyle,
        last_item: Renderable,
        initial_point: Point,
    ) -> tuple[str, Renderable, Point]:
        """
        Render this path element to its PDF representation.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
            resource_registry, style, last_item, initial_point
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
    def end_point(self) -> Point:
        """The end point of this path element."""
        return self.pt

    def bounding_box(self, start: Point) -> tuple[BoundingBox, Point]:
        """Compute the bounding box of a line from the start point to the end point."""
        return BoundingBox.from_points([start, self.pt]), self.pt

    @force_nodocument
    def render(
        self,
        resource_registry: "ResourceCatalog",
        style: GraphicsStyle,
        last_item: Renderable,
        initial_point: Point,
    ) -> tuple[str, Renderable, Point]:
        """
        Render this path element to its PDF representation.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
            resource_registry, style, last_item, initial_point
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

    def bounding_box(self, start: Point) -> tuple[BoundingBox, Point]:
        """Compute the bounding box of a relative line from the start point to the new end point."""
        return BoundingBox.from_points([start, start + self.pt]), start + self.pt

    @force_nodocument
    def render(
        self,
        resource_registry: "ResourceCatalog",
        style: GraphicsStyle,
        last_item: Renderable,
        initial_point: Point,
    ) -> tuple[str, Renderable, Point]:
        """
        Render this path element to its PDF representation.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
            resource_registry, style, last_item, initial_point
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

    def bounding_box(self, start: Point) -> tuple[BoundingBox, Point]:
        """Compute the bounding box of a horizontal line from the start point to the new x."""
        end = Point(float(self.x), start.y)
        return BoundingBox.from_points([start, end]), end

    @force_nodocument
    def render(
        self,
        resource_registry: "ResourceCatalog",
        style: GraphicsStyle,
        last_item: Renderable,
        initial_point: Point,
    ) -> tuple[str, Renderable, Point]:
        """
        Render this path element to its PDF representation.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
            resource_registry, style, last_item, initial_point
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

    def bounding_box(self, start: Point) -> tuple[BoundingBox, Point]:
        """Compute the bounding box of a relative horizontal line."""
        end = Point(float(start.x) + float(self.x), start.y)
        bbox = BoundingBox.from_points([start, end])
        return bbox, end

    @force_nodocument
    def render(
        self,
        resource_registry: "ResourceCatalog",
        style: GraphicsStyle,
        last_item: Renderable,
        initial_point: Point,
    ) -> tuple[str, Renderable, Point]:
        """
        Render this path element to its PDF representation.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
            resource_registry, style, last_item, initial_point
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

    def bounding_box(self, start: Point) -> tuple[BoundingBox, Point]:
        """Compute the bounding box of this vertical line."""
        end = Point(start.x, float(self.y))
        bbox = BoundingBox.from_points([start, end])
        return bbox, end

    @force_nodocument
    def render(
        self,
        resource_registry: "ResourceCatalog",
        style: GraphicsStyle,
        last_item: Renderable,
        initial_point: Point,
    ) -> tuple[str, Renderable, Point]:
        """
        Render this path element to its PDF representation.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command

        Returns:
            a tuple of `(str, new_last_item)`, where `new_last_item` is the resolved
            `Line`.
        """
        # pylint: disable=unused-argument
        end_point = Point(x=last_item.end_point.x, y=float(self.y))
        return _render_line(end_point), Line(end_point), initial_point

    @force_nodocument
    def render_debug(
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
            resource_registry, style, last_item, initial_point
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

    def bounding_box(self, start: Point) -> tuple[BoundingBox, Point]:
        """Compute the bounding box of this relative vertical line."""
        end = Point(start.x, float(start.y) + float(self.y))
        bbox = BoundingBox.from_points([start, end])
        return bbox, end

    @force_nodocument
    def render(
        self,
        resource_registry: "ResourceCatalog",
        style: GraphicsStyle,
        last_item: Renderable,
        initial_point: Point,
    ) -> tuple[str, Renderable, Point]:
        """
        Render this path element to its PDF representation.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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

    # pylint: disable=unused-argument
    @force_nodocument
    def render_debug(
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
        rendered, resolved, initial_point = self.render(
            resource_registry, style, last_item, initial_point
        )
        debug_stream.write(f"{self} resolved to {resolved}\n")

        return rendered, resolved, initial_point


def _eval_cubic_bezier_1d(
    t: float, p0: float, p1: float, p2: float, p3: float
) -> float:
    """Cubic Bézier scalar evaluation at t ∈ [0,1]."""
    u = 1 - t
    return (
        (u * u * u) * p0
        + 3 * (u * u) * t * p1
        + 3 * u * (t * t) * p2
        + (t * t * t) * p3
    )


def _cubic_bezier_critical_ts_1d(
    p0: float, p1: float, p2: float, p3: float, eps: float = 1e-12
) -> list[float]:
    """t ∈ (0,1) where d/dt of the cubic Bézier equals 0 (possible extrema)."""
    a = -3 * p0 + 9 * p1 - 9 * p2 + 3 * p3
    b = 6 * p0 - 12 * p1 + 6 * p2
    c = -3 * p0 + 3 * p1
    ts = []
    if abs(a) < eps:
        if abs(b) > eps:
            t = -c / b
            if 0 < t < 1:
                ts.append(t)
    else:
        disc = b * b - 4 * a * c
        if disc >= 0:
            r = disc**0.5
            for t in ((-b + r) / (2 * a), (-b - r) / (2 * a)):
                if 0 < t < 1:
                    ts.append(t)
    return ts


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
    def end_point(self) -> Point:
        """The end point of this path element."""
        return self.end

    def bounding_box(self, start: Point) -> tuple[BoundingBox, Point]:
        """Compute the bounding box of this cubic Bézier curve."""

        # Evaluate all candidate t values (endpoints + extrema) for both axes
        px = [start.x, self.c1.x, self.c2.x, self.end.x]
        py = [start.y, self.c1.y, self.c2.y, self.end.y]

        tx = [0, 1] + _cubic_bezier_critical_ts_1d(*px)
        ty = [0, 1] + _cubic_bezier_critical_ts_1d(*py)

        xs = [_eval_cubic_bezier_1d(t, *px) for t in tx]
        ys = [_eval_cubic_bezier_1d(t, *py) for t in ty]

        bbox = BoundingBox(min(xs), min(ys), max(xs), max(ys))
        return bbox, self.end

    @force_nodocument
    def render(
        self,
        resource_registry: "ResourceCatalog",
        style: GraphicsStyle,
        last_item: Renderable,
        initial_point: Point,
    ) -> tuple[str, Renderable, Point]:
        """
        Render this path element to its PDF representation.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
            resource_registry, style, last_item, initial_point
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

    def bounding_box(self, start: Point) -> tuple[BoundingBox, Point]:
        """
        Compute the bounding box of this relative cubic Bézier curve.

        Args:
            start (Point): The starting point of the curve (i.e., the end of the previous path element).

        Returns:
            A tuple containing:
                - BoundingBox: the axis-aligned bounding box containing the entire curve.
                - Point: the end point of the curve.
        """
        # Resolve absolute coordinates
        p0 = start
        p1 = start + self.c1
        p2 = start + self.c2
        p3 = start + self.end

        tx = [0, 1] + _cubic_bezier_critical_ts_1d(p0.x, p1.x, p2.x, p3.x)
        ty = [0, 1] + _cubic_bezier_critical_ts_1d(p0.y, p1.y, p2.y, p3.y)

        xs = [
            _eval_cubic_bezier_1d(t, float(p0.x), float(p1.x), float(p2.x), float(p3.x))
            for t in tx
        ]
        ys = [
            _eval_cubic_bezier_1d(t, float(p0.y), float(p1.y), float(p2.y), float(p3.y))
            for t in ty
        ]

        bbox = BoundingBox(min(xs), min(ys), max(xs), max(ys))
        return bbox, p3

    @force_nodocument
    def render(
        self,
        resource_registry: "ResourceCatalog",
        style: GraphicsStyle,
        last_item: Renderable,
        initial_point: Point,
    ) -> tuple[str, Renderable, Point]:
        """
        Render this path element to its PDF representation.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
            resource_registry, style, last_item, initial_point
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
    def end_point(self) -> Point:
        """The end point of this path element."""
        return self.end

    def to_cubic_curve(self, start_point: Point) -> BezierCurve:
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

    def bounding_box(self, start: Point) -> tuple[BoundingBox, Point]:
        """Compute the bounding box of this quadratic Bézier curve by converting it to a cubic Bézier."""
        cubic = self.to_cubic_curve(start)
        return cubic.bounding_box(start)

    @force_nodocument
    def render(
        self,
        resource_registry: "ResourceCatalog",
        style: GraphicsStyle,
        last_item: Renderable,
        initial_point: Point,
    ) -> tuple[str, Renderable, Point]:
        """
        Render this path element to its PDF representation.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command

        Returns:
            a tuple of `(str, new_last_item)`, where `new_last_item` is `self`.
        """
        return (
            self.to_cubic_curve(last_item.end_point).render(
                resource_registry, style, last_item, initial_point
            )[0],
            self,
            initial_point,
        )

    @force_nodocument
    def render_debug(
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
            resource_registry, style, last_item, initial_point
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

    def bounding_box(self, start: Point) -> tuple[BoundingBox, Point]:
        """Compute the bounding box of this relative quadratic Bézier curve."""
        ctrl = start + self.ctrl
        end = start + self.end
        return QuadraticBezierCurve(ctrl=ctrl, end=end).bounding_box(start)

    @force_nodocument
    def render(
        self,
        resource_registry: "ResourceCatalog",
        style: GraphicsStyle,
        last_item: Renderable,
        initial_point: Point,
    ) -> tuple[str, Renderable, Point]:
        """
        Render this path element to its PDF representation.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
        return absolute.render(resource_registry, style, last_item, initial_point)

    @force_nodocument
    def render_debug(
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
            resource_registry, style, last_item, initial_point
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
    def subdivide_sweep(
        sweep_angle: float,
    ) -> Generator[tuple[Point, Point, Point], None, None]:
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
            sweep_angle (float): the angle to subdivide.

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

    def _approximate_arc(self, last_item: Renderable) -> list[BezierCurve]:
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

        for ctrl1, ctrl2, end in self.subdivide_sweep(deltatheta):
            curves.append(
                BezierCurve(ctrl1 @ final_tf, ctrl2 @ final_tf, end @ final_tf)
            )

        return curves

    def bounding_box(self, start: Point) -> tuple[BoundingBox, Point]:
        """
        Compute the bounding box of this arc by approximating it with a series of
        Bezier curves and aggregating their bounding boxes.
        """
        bbox = BoundingBox.empty()
        prev = Move(start)

        for curve in self._approximate_arc(prev):
            segment_bbox, _ = curve.bounding_box(prev.end_point)
            bbox = bbox.merge(segment_bbox)
            prev = curve

        return bbox, self.end

    @force_nodocument
    def render(
        self,
        resource_registry: "ResourceCatalog",
        style: GraphicsStyle,
        last_item: Renderable,
        initial_point: Point,
    ) -> tuple[str, Renderable, Point]:
        """
        Render this path element to its PDF representation.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
            return "", last_item, initial_point

        return (
            " ".join(
                curve.render(resource_registry, style, prev, initial_point)[0]
                for prev, curve in zip([last_item, *curves[:-1]], curves)
            ),
            curves[-1],
            initial_point,
        )

    @force_nodocument
    def render_debug(
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
            return "", last_item, initial_point

        previous = [last_item]
        for curve in curves[:-1]:
            previous.append(curve)
            debug_stream.write(pfx + f" ├─ {curve}\n")
        debug_stream.write(pfx + f" └─ {curves[-1]}\n")

        return (
            " ".join(
                curve.render(resource_registry, style, prev, initial_point)[0]
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

    def bounding_box(self, start: Point) -> tuple[BoundingBox, Point]:
        """Compute the bounding box of the resolved arc from the given start point."""
        end_point = start + self.end
        arc = Arc(
            radii=self.radii,
            rotation=self.rotation,
            large=self.large,
            sweep=self.sweep,
            end=end_point,
        )
        return arc.bounding_box(start)

    @force_nodocument
    def render(
        self,
        resource_registry: "ResourceCatalog",
        style: GraphicsStyle,
        last_item: Renderable,
        initial_point: Point,
    ) -> tuple[str, Renderable, Point]:
        """
        Render this path element to its PDF representation.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
        ).render(resource_registry, style, last_item, initial_point)

    @force_nodocument
    def render_debug(
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
        ).render_debug(
            resource_registry, style, last_item, initial_point, debug_stream, pfx
        )


class Rectangle(NamedTuple):
    """A pdf primitive rectangle."""

    org: Point
    """The top-left corner of the rectangle."""
    size: Point
    """The width and height of the rectangle."""

    # pylint: disable=unused-argument
    def bounding_box(self, start=None) -> tuple[BoundingBox, Point]:
        """Compute the bounding box of this rectangle."""
        x0, y0 = self.org.x, self.org.y
        x1 = float(x0) + float(self.size.x)
        y1 = float(y0) + float(self.size.y)

        bbox = BoundingBox.from_points(
            [
                Point(x0, y0),
                Point(x1, y0),
                Point(x0, y1),
                Point(x1, y1),
            ]
        )
        return bbox, self.org

    @force_nodocument
    def render(
        self,
        resource_registry: "ResourceCatalog",
        style: GraphicsStyle,
        last_item: Renderable,
        initial_point: Point,
    ) -> tuple[str, Renderable, Point]:
        """
        Render this path element to its PDF representation.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
                dictionary registry.
            style (GraphicsStyle): the current resolved graphics style
            last_item: the previous path element.
            initial_point: last position set by a "M" or "m" command

        Returns:
            a tuple of `(str, new_last_item)`, where `new_last_item` is a `Line` back to
            the rectangle's origin.
        """

        return (
            f"{self.org.render()} {self.size.render()} re",
            Line(self.org),
            initial_point,
        )

    @force_nodocument
    def render_debug(
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
        rendered, resolved, initial_point = self.render(
            resource_registry, style, last_item, initial_point
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

    def _decompose(self) -> list[Renderable]:
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

    def bounding_box(self, start: Point) -> tuple[BoundingBox, Point]:
        """
        Compute the bounding box of this rounded rectangle by decomposing into primitives
        and merging their individual bounding boxes.
        """
        bbox = BoundingBox.empty()
        current_point = start

        for item in self._decompose():
            b, current_point = item.bounding_box(current_point)
            bbox = bbox.merge(b)

        return bbox, self.org

    @force_nodocument
    def render(
        self,
        resource_registry: "ResourceCatalog",
        style: GraphicsStyle,
        last_item: Renderable,
        initial_point: Point,
    ) -> tuple[str, Renderable, Point]:
        """
        Render this path element to its PDF representation.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
            return "", last_item, initial_point

        render_list = []
        for item in components:
            rendered, last_item, initial_point = item.render(
                resource_registry, style, last_item, initial_point
            )
            render_list.append(rendered)

        return " ".join(render_list), Line(self.org), initial_point

    @force_nodocument
    def render_debug(
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
            return "", last_item, initial_point

        render_list = []
        for item in components[:-1]:
            rendered, last_item, initial_point = item.render(
                resource_registry, style, last_item, initial_point
            )
            debug_stream.write(pfx + f" ├─ {item}\n")
            render_list.append(rendered)

        rendered, last_item, initial_point = components[-1].render(
            resource_registry, style, last_item, initial_point
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

    def _decompose(self) -> list[Renderable]:
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

    def bounding_box(self, start: Point) -> tuple[BoundingBox, Point]:
        """
        Compute the bounding box of this ellipse by decomposing it and merging the bounding boxes
        of its components.
        """
        bbox = BoundingBox.empty()
        current_point = start

        for item in self._decompose():
            b, current_point = item.bounding_box(current_point)
            bbox = bbox.merge(b)

        return bbox, self.center

    @force_nodocument
    def render(
        self,
        resource_registry: "ResourceCatalog",
        style: GraphicsStyle,
        last_item: Renderable,
        initial_point: Point,
    ) -> tuple[str, Renderable, Point]:
        """
        Render this path element to its PDF representation.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
            return "", last_item, initial_point

        render_list = []
        for item in components:
            rendered, last_item, initial_point = item.render(
                resource_registry, style, last_item, initial_point
            )
            render_list.append(rendered)

        return " ".join(render_list), Move(self.center), initial_point

    @force_nodocument
    def render_debug(
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
            return "", last_item, initial_point

        render_list = []
        for item in components[:-1]:
            rendered, last_item, initial_point = item.render(
                resource_registry, style, last_item, initial_point
            )
            debug_stream.write(pfx + f" ├─ {item}\n")
            render_list.append(rendered)

        rendered, last_item, initial_point = components[-1].render(
            resource_registry, style, last_item, initial_point
        )
        debug_stream.write(pfx + f" └─ {components[-1]}\n")
        render_list.append(rendered)

        return " ".join(render_list), Move(self.center), initial_point


class TextRun(NamedTuple):
    text: str
    family: str
    emphasis: str
    size: float
    dx: float = 0.0
    dy: float = 0.0
    abs_x: Optional[float] = None
    abs_y: Optional[float] = None
    transform: Optional[Transform] = None
    run_style: Optional[GraphicsStyle] = None


class Text(NamedTuple):
    """
    SVG-like text renderable.
    Stores the anchor position (x, y) and one or more TextRuns that include
    relative positioning offsets. Accurate glyph positioning is resolved
    during rendering once font metrics are available.
    """

    x: float
    y: float
    text_runs: tuple[TextRun, ...]
    text_anchor: str = "start"  # "start" | "middle" | "end"

    def _approximate_layout(self) -> tuple[list[tuple[float, float, float]], float]:
        """
        Produce an approximate layout for bounding-box estimation.

        Returns:
            A tuple of (per-run layout list, total width estimate).  Each layout
            entry is (x, y, width) in user space.
        """
        positions: list[tuple[float, float, float]] = []
        pen_x = self.x
        pen_y = self.y
        max_right = pen_x
        min_left = pen_x

        for run in self.text_runs:
            if run.abs_x is not None:
                pen_x = run.abs_x
            if run.abs_y is not None:
                pen_y = run.abs_y
            pen_x += run.dx
            pen_y += run.dy
            # Fallback width estimation: ~0.5em per glyph
            approx_width = 0.5 * run.size * max(0, len(run.text))
            positions.append((pen_x, pen_y, approx_width))
            min_left = min(min_left, pen_x)
            max_right = max(max_right, pen_x + approx_width)
            pen_x += approx_width

        total_width = max_right - min_left
        return positions, total_width

    def _anchor_offset(self, positions: list[tuple[float, float, float]]) -> float:
        """Compute anchor offset for the provided approximate layout."""
        if not positions:
            return 0.0

        if any(run.abs_x is not None for run in self.text_runs):
            return 0.0

        min_x = min(pos[0] for pos in positions)
        max_x = max(pos[0] + pos[2] for pos in positions)

        if self.text_anchor == "middle":
            return self.x - (min_x + max_x) / 2.0
        if self.text_anchor == "end":
            return self.x - max_x
        return self.x - min_x

    def bounding_box(self, start: Point) -> tuple["BoundingBox", Point]:
        """
        Compute a conservative bbox for the text.

        Font metrics are not available at this stage so the layout relies on
        approximate glyph widths proportional to the run font size. The actual
        layout is computed precisely in render().
        """
        if not self.text_runs:
            return BoundingBox.empty(), start

        positions, _ = self._approximate_layout()
        anchor_offset = self._anchor_offset(positions)

        min_x = float("inf")
        max_x = float("-inf")
        min_y = float("inf")
        max_y = float("-inf")

        for (run_x, run_y, run_width), run in zip(positions, self.text_runs):
            adj_x = run_x + anchor_offset
            asc = 0.8 * run.size
            desc = 0.2 * run.size
            min_x = min(min_x, adj_x)
            max_x = max(max_x, adj_x + run_width)
            min_y = min(min_y, run_y - asc)
            max_y = max(max_y, run_y + desc)

        if min_x == float("inf"):
            return BoundingBox.empty(), start

        x0 = min_x
        x1 = max_x
        y0 = min_y
        y1 = max_y

        return BoundingBox.from_points([Point(x0, y0), Point(x1, y1)]), start

    @force_nodocument
    def render(
        self,
        resource_registry: "ResourceCatalog",
        style: "GraphicsStyle",
        last_item: "Renderable",
        initial_point: Point,
    ) -> tuple[str, "Renderable", Point]:
        """
        Emit PDF text operators:

          BT
            <font_id> <font_size> Tf
            Tr <mode>               (map from GraphicsStyle->PathPaintRule)
            1 0 0 1 x y Tm
            (escaped-text) Tj
          ET
        """
        if not self.text_runs:
            return "", last_item, initial_point

        # Precise layout resolution with actual font metrics
        layout: list[tuple[float, float, float, TextRun, object]] = []
        pen_x = self.x
        pen_y = self.y
        min_x = pen_x
        max_x = pen_x

        for run in self.text_runs:
            font = resource_registry.get_font_from_family(run.family, run.emphasis)
            _, width = font.get_text_width(run.text, run.size, None)
            if run.abs_x is not None:
                pen_x = run.abs_x
            if run.abs_y is not None:
                pen_y = run.abs_y
            pen_x += run.dx
            pen_y += run.dy
            min_x = min(min_x, pen_x)
            max_x = max(max_x, pen_x + width)
            layout.append((pen_x, pen_y, width, run, font))
            pen_x += width

        has_absolute = any(run.abs_x is not None for _, _, _, run, _ in layout)

        if layout and not has_absolute:
            if self.text_anchor == "middle":
                anchor_offset = self.x - (min_x + max_x) / 2.0
            elif self.text_anchor == "end":
                anchor_offset = self.x - max_x
            else:
                anchor_offset = self.x - min_x
        else:
            anchor_offset = 0.0

        ops: list[str] = []
        NO_EMIT_SET = (None, GraphicsStyle.INHERIT)

        for run_x, run_y, width, run, font in layout:
            effective_style = (
                GraphicsStyle.merge(style, run.run_style)
                if run.run_style is not None
                else style
            )

            # Determine text rendering mode
            rule = effective_style.resolve_paint_rule()
            if rule in (PathPaintRule.FILL_NONZERO, PathPaintRule.FILL_EVENODD):
                tr = 0
            elif rule is PathPaintRule.STROKE:
                tr = 1
            elif rule in (
                PathPaintRule.STROKE_FILL_NONZERO,
                PathPaintRule.STROKE_FILL_EVENODD,
            ):
                tr = 2
            else:  # PathPaintRule.DONT_PAINT:
                tr = 3

            run_ops: list[str] = []

            if run.run_style is not None:
                merged_style = effective_style
                style_dict_name = resource_registry.register_graphics_style(
                    merged_style
                )

                if style_dict_name is not None:
                    run_ops.append(f"{render_pdf_primitive(style_dict_name)} gs")

                fill_color = merged_style.fill_color
                stroke_color = merged_style.stroke_color

                run_bbox = BoundingBox.from_points(
                    [
                        Point(run_x + anchor_offset, run_y - 0.8 * run.size),
                        Point(run_x + anchor_offset + width, run_y + 0.2 * run.size),
                    ]
                )

                if fill_color not in NO_EMIT_SET:
                    if isinstance(fill_color, GradientPaint):
                        run_ops.append(
                            fill_color.emit_fill(resource_registry, run_bbox)
                        )
                    else:
                        run_ops.append(fill_color.serialize().lower())
                if stroke_color not in NO_EMIT_SET:
                    if isinstance(stroke_color, GradientPaint):
                        run_ops.append(
                            stroke_color.emit_stroke(resource_registry, run_bbox)
                        )
                    else:
                        run_ops.append(stroke_color.serialize().upper())

                dash_pattern = merged_style.stroke_dash_pattern
                dash_phase = merged_style.stroke_dash_phase
                if dash_pattern not in NO_EMIT_SET:
                    run_ops.append(
                        render_pdf_primitive(dash_pattern)
                        + f" {number_to_str(dash_phase)} d"
                    )

            run_ops.extend(
                [
                    "BT",
                    f"/F{font.i} {number_to_str(run.size)} Tf",
                    f"{number_to_str(tr)} Tr",
                    f"1 0 0 -1 {number_to_str(run_x + anchor_offset)} {number_to_str(run_y)} Tm",
                    font.encode_text(run.text),
                    "ET",
                ]
            )

            if run.run_style is not None:
                run_ops = ["q"] + run_ops + ["Q"]

            ops.extend(run_ops)

        return " ".join(ops), last_item, initial_point

    # pylint: disable=unused-argument
    @force_nodocument
    def render_debug(
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        rendered, resolved, initial_point = self.render(
            resource_registry, style, last_item, initial_point
        )
        debug_stream.write(str(self) + "\n")
        return rendered, resolved, initial_point


class ImplicitClose(NamedTuple):
    """
    A path close element that is conditionally rendered depending on the value of
    `GraphicsStyle.auto_close`.
    """

    # pylint: disable=no-self-use
    def bounding_box(self, start: Point) -> tuple[BoundingBox, Point]:
        """Return an empty bounding box; Close does not affect the geometry."""
        return BoundingBox.empty(), start

    # pylint: disable=no-self-use
    @force_nodocument
    def render(
        self,
        resource_registry: "ResourceCatalog",
        style: GraphicsStyle,
        last_item: Renderable,
        initial_point: Point,
    ) -> tuple[str, Renderable, Point]:
        """
        Render this path element to its PDF representation.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
            resource_registry, style, last_item, initial_point
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
    def bounding_box(self, start: Point) -> tuple[BoundingBox, Point]:
        """Return an empty bounding box; Close does not affect the geometry."""
        return BoundingBox.empty(), start

    # pylint: disable=no-self-use
    @force_nodocument
    def render(
        self,
        resource_registry: "ResourceCatalog",
        style: GraphicsStyle,
        last_item: Renderable,
        initial_point: Point,
    ) -> tuple[str, Renderable, Point]:
        """
        Render this path element to its PDF representation.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
            resource_registry, style, last_item, initial_point
        )
        debug_stream.write(str(self) + "\n")

        return rendered, resolved, initial_point


if TYPE_CHECKING:
    # Validate all path items conform to the Renderable protocol
    move: Renderable = Move(pt=Point(0, 0))
    relative_move: Renderable = RelativeMove(pt=Point(0, 0))
    line: Renderable = Line(pt=Point(0, 0))
    relative_line: Renderable = RelativeLine(pt=Point(0, 0))
    horizontal_line: Renderable = HorizontalLine(x=0)
    relative_horizontal_line: Renderable = RelativeHorizontalLine(x=0)
    vertical_line: Renderable = VerticalLine(y=0)
    relative_vertical_line: Renderable = RelativeVerticalLine(y=0)
    bezier_curve: Renderable = BezierCurve(
        c1=Point(0, 0), c2=Point(0, 0), end=Point(0, 0)
    )
    relative_bezier_curve: Renderable = RelativeBezierCurve(
        c1=Point(0, 0), c2=Point(0, 0), end=Point(0, 0)
    )
    quadratic_bezier_curve: Renderable = QuadraticBezierCurve(
        ctrl=Point(0, 0), end=Point(0, 0)
    )
    relative_quadratic_bezier_curve: Renderable = RelativeQuadraticBezierCurve(
        ctrl=Point(0, 0), end=Point(0, 0)
    )
    arc: Renderable = Arc(
        radii=Point(0, 0), rotation=0, large=False, sweep=False, end=Point(0, 0)
    )
    relative_arc: Renderable = RelativeArc(
        radii=Point(0, 0), rotation=0, large=False, sweep=False, end=Point(0, 0)
    )
    rectangle: Renderable = Rectangle(org=Point(0, 0), size=Point(0, 0))
    rounded_rectangle: Renderable = RoundedRectangle(
        org=Point(0, 0), size=Point(0, 0), corner_radii=Point(0, 0)
    )
    ellipse: Renderable = Ellipse(radii=Point(0, 0), center=Point(0, 0))
    text: Renderable = Text(
        x=0,
        y=0,
        text_runs=(TextRun(text="", family="Sans serif", emphasis="", size=12.0),),
    )
    implicit_close: Renderable = ImplicitClose()
    close: Renderable = Close()


class DrawingContext:
    """
    Base context for a drawing in a PDF

    This context is not stylable and is mainly responsible for transforming path
    drawing coordinates into user coordinates (i.e. it ensures that the output drawing
    is correctly scaled).
    """

    __slots__ = ("_subitems",)

    def __init__(self):
        self._subitems: list[Union[GraphicsContext, PaintedPath, PaintComposite]] = []

    def add_item(
        self,
        item: Union["GraphicsContext", "PaintedPath", "PaintComposite"],
        _copy: bool = True,
    ) -> None:
        """
        Append an item to this drawing context

        Args:
            item (GraphicsContext, PaintedPath): the item to be appended.
            _copy (bool): if true (the default), the item will be copied before being
                appended. This prevents modifications to a referenced object from
                "retroactively" altering its style/shape and should be disabled with
                caution.
        """

        if not isinstance(item, (GraphicsContext, PaintedPath, PaintComposite)):
            raise TypeError(f"{item} doesn't belong in a DrawingContext")

        if _copy:
            item = deepcopy(item)

        self._subitems.append(item)

    @staticmethod
    def _setup_render_prereqs(
        style, first_point: Point, scale: float, height: float
    ) -> tuple[list[str], GraphicsStyle, Renderable]:
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

    def render(
        self,
        resource_registry: "ResourceCatalog",
        first_point: Point,
        scale: float,
        height: float,
        starting_style: GraphicsStyle,
    ) -> str:
        """
        Render the drawing context to PDF format.

        Args:
            resource_registry (ResourceCatalog): the parent document's graphics
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
                resource_registry, style, last_item, first_point
            )
            if rendered:
                render_list.append(rendered)

        # there was nothing to render: the only items are the start group and scale
        # transform.
        if len(render_list) == 2:
            return ""

        if (
            style.soft_mask
            and style.soft_mask is not GraphicsStyle.INHERIT
            and style.soft_mask.object_id == 0
        ):
            style.soft_mask.object_id = resource_registry.register_soft_mask(
                style.soft_mask
            )
        style_dict_name = resource_registry.register_graphics_style(style)
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
        self,
        resource_registry,
        first_point,
        scale,
        height,
        starting_style,
        debug_stream,
    ):
        """
        Render the drawing context to PDF format.

        Args:
            resource_registry (ResourceCatalog): the parent document's graphics
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
                resource_registry, style, last_item, debug_stream, " │  "
            )
            if rendered:
                render_list.append(rendered)

        if self._subitems:
            debug_stream.write(" └─ ")
            rendered, last_item, first_point = self._subitems[-1].render_debug(
                resource_registry, style, last_item, first_point, debug_stream, "    "
            )
            if rendered:
                render_list.append(rendered)

            # there was nothing to render: the only items are the start group and scale
            # transform.
            if len(render_list) == 2:
                return ""

            if (
                style.soft_mask
                and style.soft_mask is not GraphicsStyle.INHERIT
                and style.soft_mask.object_id == 0
            ):
                style.soft_mask.object_id = resource_registry.register_soft_mask(
                    style.soft_mask
                )
            style_dict_name = resource_registry.register_graphics_style(style)
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

    __slots__ = (
        "_root_graphics_context",
        "_graphics_context",
        "_closed",
        "_close_context",
        "_starter_move",
    )

    def __init__(self, x: float = 0, y: float = 0) -> None:
        self._root_graphics_context: GraphicsContext = GraphicsContext()
        self._graphics_context: GraphicsContext = self._root_graphics_context

        self._closed: bool = True
        self._close_context: GraphicsContext = self._graphics_context

        self._starter_move: Renderable = Move(Point(x, y))

    def __deepcopy__(self, memo):
        # there's no real way to recover the matching current _graphics_context after
        # copying the root context, but that's ok because we can just disallow copying
        # of paths under modification as that is almost certainly wrong usage.
        if self._graphics_context is not self._root_graphics_context:
            raise RuntimeError(f"cannot copy path {self} while it is being modified")

        copied = self.__class__()
        copied._root_graphics_context = deepcopy(self._root_graphics_context, memo)
        copied._graphics_context = copied._root_graphics_context
        copied._closed = self._closed
        copied._close_context = copied._graphics_context

        return copied

    @property
    def style(self) -> GraphicsStyle:
        """The `GraphicsStyle` applied to all elements of this path."""
        return self._root_graphics_context.style

    @property
    def transform(self) -> Optional[Transform]:
        """The `Transform` that applies to all of the elements of this path."""
        return self._root_graphics_context.transform

    @transform.setter
    def transform(self, tf: Transform) -> None:
        self._root_graphics_context.transform = tf

    @property
    def auto_close(self) -> bool:
        """If true, the path should automatically close itself before painting."""
        return self.style.auto_close

    @auto_close.setter
    def auto_close(self, should: bool) -> None:
        self.style.auto_close = should

    @property
    def paint_rule(self) -> PathPaintRule:
        """Manually specify the `PathPaintRule` to use for rendering the path."""
        return self.style.paint_rule

    @paint_rule.setter
    def paint_rule(self, style: PathPaintRule) -> None:
        self.style.paint_rule = style

    @property
    def clipping_path(self):
        """Set the clipping path for this path."""
        return self._root_graphics_context.clipping_path

    @clipping_path.setter
    def clipping_path(self, new_clipath):
        self._root_graphics_context.clipping_path = new_clipath

    def get_graphics_context(self):
        return self._graphics_context

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
            x (Number): abscissa of the (sub)path starting point relative to the previous point.
            y (Number): ordinate of the (sub)path starting point relative to the previous point.
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

    def text(
        self,
        x: float,
        y: float,
        content: str,
        *,
        font_family: str = "helvetica",
        font_style: str = "",  # "", "B", "I", "BI"
        font_size: float = 12.0,
        text_anchor: str = "start",  # "start" | "middle" | "end"
    ):
        """
        Append a text run at (x, y) to this path.

        The baseline is at (x, y). `text_anchor` controls alignment about x.
        `font_style` accepts "", "B", "I", or "BI". `font_family` can be a single
        name or a comma-separated fallback list (handled at render-time).

        Returns:
            self (to allow chaining)
        """
        # Normalize style just in case e.g. "ib" -> "BI"
        s = "".join(sorted(font_style.upper()))

        self.add_path_element(
            Text(
                x=x,
                y=y,
                text_runs=(
                    TextRun(
                        text=content,
                        family=font_family,
                        emphasis=s,
                        size=font_size,
                    ),
                ),
                text_anchor=text_anchor,
            ),
            _copy=False,
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

    def bounding_box(
        self, start: Point, expand_for_stroke=True
    ) -> tuple[BoundingBox, Point]:
        """Compute the bounding box of this painted path, including nested contexts and transformations."""
        return self._root_graphics_context.bounding_box(
            start, self.style, expand_for_stroke=expand_for_stroke
        )

    def render(
        self,
        resource_registry,
        style,
        last_item,
        initial_point,
        debug_stream=None,
        pfx=None,
    ):
        self._insert_implicit_close_if_open()

        (
            render_list,
            last_item,
            initial_point,
        ) = self._root_graphics_context.build_render_list(
            resource_registry, style, last_item, initial_point, debug_stream, pfx
        )

        paint_rule = GraphicsStyle.merge(style, self.style).resolve_paint_rule()
        render_list.insert(-1, paint_rule.value)
        return " ".join(render_list), last_item, initial_point

    def render_debug(
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
            resource_registry, style, last_item, initial_point, debug_stream, pfx
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

    __slots__ = ()  # no new attributes; preserve slotted layout from PaintedPath

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
        self,
        resource_registry,
        style,
        last_item,
        initial_point,
        debug_stream=None,
        pfx=None,
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
            resource_registry,
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
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        """
        Render this path element to its PDF representation and produce debug
        information.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
            resource_registry, style, last_item, initial_point, debug_stream, pfx
        )


class GraphicsContext:
    """
    Page-level container that collects drawable items and renders them into a PDF
    content stream.

    Converts model coordinates to PDF user space by applying the provided
    `scale` and a vertical flip so (0, 0) is the top-left of the page.

    Wraps output in a saved graphics state (`q … Q`) and registers any
    required resources (graphics state dictionaries, soft masks, dash pattern).

    Child items are typically `GraphicsContext`, `PaintedPath`, or `PaintComposite`
    objects added via `add_item()`. By default, items are deep-copied on insert to
    avoid later mutations affecting the emitted stream.
    """

    __slots__ = ("style", "path_items", "_transform", "_clipping_path")

    def __init__(self):
        self.style: GraphicsStyle = GraphicsStyle()
        self.path_items: list[Renderable] = []

        self._transform: Optional[Transform] = None
        self._clipping_path: Optional[ClippingPath] = None

    def __deepcopy__(self, memo):
        copied = self.__class__()
        copied.style = deepcopy(self.style, memo)
        copied.path_items = deepcopy(self.path_items, memo)
        copied._transform = deepcopy(self.transform, memo)
        copied._clipping_path = deepcopy(self.clipping_path, memo)
        return copied

    @property
    def transform(self) -> Optional[Transform]:
        return self._transform

    @transform.setter
    def transform(self, tf: Transform) -> None:
        self._transform = tf

    @property
    def clipping_path(self) -> Optional[ClippingPath]:
        """The `ClippingPath` for this graphics context."""
        return self._clipping_path

    @clipping_path.setter
    def clipping_path(self, new_clipath: ClippingPath) -> None:
        self._clipping_path = new_clipath

    def add_item(self, item: Renderable, _copy: bool = True) -> None:
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
            item = deepcopy(item)

        self.path_items.append(item)

    def remove_last_item(self) -> None:
        del self.path_items[-1]

    def merge(self, other_context: "GraphicsContext") -> None:
        """Copy another `GraphicsContext`'s path items into this one."""
        self.path_items.extend(other_context.path_items)

    @force_nodocument
    def build_render_list(
        self,
        resource_registry: "ResourceCatalog",
        style: GraphicsStyle,
        last_item: Renderable,
        initial_point: Point,
        debug_stream=None,
        pfx: Optional[str] = None,
        _push_stack: bool = True,
    ):
        """
        Build a list composed of all all the individual elements rendered.

        This is used by `PaintedPath` and `ClippingPath` to reuse the `GraphicsContext`
        rendering process while still being able to inject some path specific items
        (e.g. the painting directive) before the render is collapsed into a single
        string.

        Args:
            resource_registry (ResourceCatalog): the owner's graphics state
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
                            inherited = " (inherited)"
                        else:
                            inherited = ""
                        styles_dbg.append(f"{attr}: {val}{inherited}")

                if styles_dbg:
                    debug_stream.write(" {\n")
                    for style_dbg_line in styles_dbg:
                        debug_stream.write(pfx + "    ")
                        debug_stream.write(style_dbg_line)
                        debug_stream.write("\n")

                    debug_stream.write(pfx + "}┐\n")
                else:
                    debug_stream.write("\n")

            NO_EMIT_SET = (None, merged_style.INHERIT)

            emit_style = self.style
            if merged_style.allow_transparency != self.style.allow_transparency:
                emit_style = deepcopy(self.style)
                emit_style.allow_transparency = merged_style.allow_transparency

            # in order to decouple the dash pattern and the dash phase at the API layer,
            # we have to perform additional logic here to recombine them. We can rely
            # on these being serializable because we always get a sane style on the
            # drawing context.
            dash_pattern = merged_style.stroke_dash_pattern
            dash_phase = merged_style.stroke_dash_phase
            emit_dash = None
            if (
                dash_pattern != style.stroke_dash_pattern
                or dash_phase != style.stroke_dash_phase
            ):
                if emit_style is self.style:
                    emit_style = deepcopy(emit_style)
                emit_style.stroke_dash_pattern = dash_pattern
                emit_style.stroke_dash_phase = dash_phase
                emit_dash = (dash_pattern, dash_phase)

            if (
                emit_style.soft_mask
                and emit_style.soft_mask is not GraphicsStyle.INHERIT
                and emit_style.soft_mask.object_id == 0
            ):
                emit_style.soft_mask.object_id = resource_registry.register_soft_mask(
                    emit_style.soft_mask
                )
            # ---- If fill/stroke use a GradientPaint with alpha, synthesize a soft mask now
            # Compute bbox once so mask and color share the same mapping
            bbox_for_units = self.bounding_box(
                initial_point, style=self.style, expand_for_stroke=False
            )[0]

            def _attach_alpha_mask_if_needed(paint_obj: GradientPaint):
                if not isinstance(paint_obj, GradientPaint):
                    return
                if not paint_obj.has_alpha():
                    return
                # bbox in content space (shared by color & mask)
                bbox_for_units = self.bounding_box(
                    initial_point,
                    style=self.style,
                    expand_for_stroke=False,
                    transformed=False,
                )[0]
                # rectangular mask covering the painted area
                mask_rect = PaintedPath()
                mask_rect.rectangle(
                    bbox_for_units.x0,
                    bbox_for_units.y0,
                    bbox_for_units.width,
                    bbox_for_units.height,
                )
                # paint that rectangle with the grayscale alpha gradient
                alpha_paint = _AlphaGradientPaint(
                    paint_obj.gradient,
                    paint_obj.units,
                    gradient_transform=paint_obj.gradient_transform,
                )
                alpha_paint.apply_page_ctm = paint_obj.apply_page_ctm
                mask_rect.style.fill_color = alpha_paint
                mask_rect.style.stroke_color = None
                mask_rect.style.stroke_width = 0
                mask_rect.style.paint_rule = PathPaintRule.FILL_NONZERO

                mask_gc = GraphicsContext()
                mask_gc.add_item(mask_rect, _copy=False)

                # use luminosity so gray intensity drives coverage
                sm = PaintSoftMask(
                    mask_gc,
                    invert=False,
                    use_luminosity=True,
                    matrix=paint_obj.gradient_transform,
                )

                nonlocal emit_style
                if emit_style.allow_transparency is False:
                    return
                if emit_style is self.style:
                    emit_style = deepcopy(self.style)
                emit_style.soft_mask = sm
                emit_style.soft_mask.object_id = resource_registry.register_soft_mask(
                    emit_style.soft_mask
                )

            # Decide whether to attach a soft mask from fill or stroke gradient alpha.
            # Priority: fill first (most common), otherwise stroke.
            if isinstance(emit_style.fill_color, GradientPaint) and (
                emit_style.soft_mask in (None, GraphicsStyle.INHERIT)
            ):
                _attach_alpha_mask_if_needed(self.style.fill_color)
            elif isinstance(emit_style.stroke_color, GradientPaint) and (
                emit_style.soft_mask in (None, GraphicsStyle.INHERIT)
            ):
                _attach_alpha_mask_if_needed(self.style.stroke_color)

            style_dict_name = resource_registry.register_graphics_style(emit_style)

            if style_dict_name is not None:
                render_list.append(f"{render_pdf_primitive(style_dict_name)} gs")

            # we can't set color in the graphics state context dictionary, so we have to
            # manually inherit it and emit it here.
            fill_color = self.style.fill_color
            stroke_color = self.style.stroke_color

            if fill_color not in NO_EMIT_SET:
                if isinstance(fill_color, GradientPaint):
                    render_list.append(
                        fill_color.emit_fill(resource_registry, bbox_for_units)
                    )
                else:
                    render_list.append(fill_color.serialize().lower())

            if stroke_color not in NO_EMIT_SET:
                if isinstance(stroke_color, GradientPaint):
                    render_list.append(
                        stroke_color.emit_stroke(resource_registry, bbox_for_units)
                    )
                else:
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
                        resource_registry,
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
                        resource_registry,
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
                    resource_registry,
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
                        resource_registry, merged_style, last_item, initial_point
                    )
                    if rendered_cpath:
                        render_list.append(rendered_cpath)

                for item in self.path_items:
                    rendered, last_item, initial_point = item.render(
                        resource_registry, merged_style, last_item, initial_point
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

    def bounding_box(
        self,
        start: Point,
        style: Optional[GraphicsStyle] = None,
        expand_for_stroke: bool = True,
        transformed: bool = True,
    ) -> tuple[BoundingBox, Point]:
        """
        Compute bbox of all path items. We:
        1) recurse with accumulated CTM,
        2) merge child bboxes already transformed to this level,
        3) at the end, expand once for stroke using the worst-case CTM row norms.
        """
        identity = Transform.identity()

        def walk(
            ctx: "GraphicsContext",
            current_point: Point,
            ambient_style: Optional[GraphicsStyle],
            accum_tf: Transform,
        ) -> tuple[BoundingBox, Point, float, float]:
            bbox = BoundingBox.empty()
            tf = accum_tf @ (ctx.transform or identity)
            if not transformed:
                tf = identity

            merged_style = (
                ambient_style.__class__.merge(ambient_style, ctx.style)
                if ambient_style
                else ctx.style
            )

            max_nx, max_ny = tf.row_norms()

            for item in ctx.path_items:
                if isinstance(item, GraphicsContext):
                    child_bbox, end_point, cnx, cny = walk(
                        item, current_point, merged_style, tf
                    )
                    bbox = bbox.merge(child_bbox)  # child bbox already in this space
                    current_point = end_point
                    max_nx = max(max_nx, cnx)
                    max_ny = max(max_ny, cny)
                elif hasattr(item, "bounding_box"):
                    item_bbox, end_point = item.bounding_box(current_point)
                    bbox = bbox.merge(item_bbox.transformed(tf))
                    current_point = end_point

            return bbox, current_point, max_nx, max_ny

        # 1) geometric + collect CTM scales
        geom_bbox, end_pt, nx, ny = walk(self, start, style, identity)

        final_bbox = geom_bbox

        if expand_for_stroke:
            # 2) expand once for stroke with the effective style at *this* level
            effective_style = (
                style.__class__.merge(style, self.style) if style else self.style
            )
            final_bbox = geom_bbox.expanded_to_stroke(
                effective_style, row_norms=(nx, ny)
            )
        return final_bbox, end_pt

    def render(
        self,
        resource_registry: "ResourceCatalog",
        style: GraphicsStyle,
        last_item: Renderable,
        initial_point: Point,
        debug_stream=None,
        pfx=None,
        _push_stack=True,
    ) -> tuple[str, Renderable, Point]:
        render_list, last_item, initial_point = self.build_render_list(
            resource_registry,
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
        resource_registry,
        style,
        last_item,
        initial_point,
        debug_stream,
        pfx,
        _push_stack=True,
    ):
        return self.render(
            resource_registry,
            style,
            last_item,
            initial_point,
            debug_stream,
            pfx,
            _push_stack=_push_stack,
        )


class PaintSoftMask:
    """
    Wraps a vector path as a PDF soft mask (SMask) that can be attached to a
    graphics state.

    The provided `mask_path` is deep-copied and forced to render as an opaque
    grayscale fill (white, alpha=1, nonzero rule, transparency disabled). During
    rendering, the mask’s content stream is generated and its resource
    dictionary is collected so it can be embedded as a Form XObject and
    referenced from an ExtGState.
    """

    __slots__ = (
        "mask_path",
        "invert",
        "resources",
        "use_luminosity",
        "object_id",
        "matrix",
    )

    def __init__(
        self,
        mask_path: Union[PaintedPath, GraphicsContext],
        invert: bool = False,
        use_luminosity=False,
        matrix=Transform.identity(),
    ):
        self.mask_path = deepcopy(mask_path)
        self.invert = invert
        self.use_luminosity = use_luminosity
        self.resources = set()
        self.object_id = 0
        self.matrix = matrix

        if not self.use_luminosity:
            # Pure alpha mask -> force opaque white so shape defines coverage
            self.mask_path.style.paint_rule = PathPaintRule.FILL_NONZERO
            self.mask_path.style.fill_opacity = 1
            self.mask_path.style.fill_color = "#ffffff"

    def serialize(self):
        tr = (
            " /TR <</FunctionType 2 /Domain [0 1] /Range [0 1] /C0 [1] /C1 [0] /N 1>>"
            if self.invert
            else ""
        )
        mask_type = "/Luminosity" if self.use_luminosity else "/Alpha"
        return f"<</S {mask_type} /G {self.object_id} 0 R{tr}>>"

    def get_bounding_box(self) -> tuple[float, float, float, float]:
        bounding_box, _ = self.mask_path.bounding_box(Point(0, 0))
        return bounding_box.to_tuple()

    def get_resource_dictionary(self, gfxstate_objs_per_name, pattern_objs_per_name):
        """Build the resource dictionary for this soft mask, resolving GS & Pattern ids."""
        resources_registered: dict[str, list] = {}
        for resource_type, resource_id in self.resources:
            resources_registered.setdefault(resource_type.value, set()).add(resource_id)

        parts: list[str] = []

        # ExtGState
        if "ExtGState" in resources_registered and resources_registered["ExtGState"]:
            parts.append(
                Name("ExtGState").serialize()
                + "<<"
                + "".join(
                    f"{Name(gs_name).serialize()} {gfxstate_objs_per_name[gs_name].id} 0 R"
                    for gs_name in sorted(resources_registered["ExtGState"])
                )
                + ">>"
            )

        # Pattern
        if "Pattern" in resources_registered and resources_registered["Pattern"]:
            parts.append(
                Name("Pattern").serialize()
                + "<<"
                + "".join(
                    f"{Name(pat_name).serialize()} {pattern_objs_per_name[pat_name].id} 0 R"
                    for pat_name in sorted(resources_registered["Pattern"])
                )
                + ">>"
            )
        return "<<" + "".join(parts) + ">>"

    def render(self, resource_registry):
        stream, _, _ = self.mask_path.render(
            resource_registry,
            style=GraphicsStyle(),
            last_item=None,
            initial_point=Point(0, 0),
        )
        self.resources = resource_registry.scan_stream(stream)
        return stream

    @staticmethod
    def coverage_white(
        node: Union[PaintedPath, GraphicsContext],
    ) -> Union[PaintedPath, GraphicsContext]:
        """
        Return a deep-copied version of *node* whose appearance encodes only its
        geometric coverage: every shape is converted to an **opaque white fill**
        (nonzero rule), with **no stroke**, no soft mask, and inherited blend mode.

        The transform/clipping/structure of the original node is preserved; only
        paint-related attributes are normalized. This is intended for building the
        “B” term of soft-mask expressions (coverage), where inside = 1 and
        outside = 0.
        """

        def _force_white(gc: GraphicsContext):
            # normalize the GC's own style
            gc.style.paint_rule = PathPaintRule.FILL_NONZERO
            gc.style.fill_color = "#ffffff"
            gc.style.fill_opacity = 1
            gc.style.stroke_color = None
            gc.style.blend_mode = GraphicsStyle.INHERIT
            gc.style.soft_mask = GraphicsStyle.INHERIT

            # recurse into children
            for child in gc.path_items:
                if isinstance(child, GraphicsContext):
                    _force_white(child)
                elif isinstance(child, PaintedPath):
                    child.style.paint_rule = PathPaintRule.FILL_NONZERO
                    child.style.fill_color = "#ffffff"
                    child.style.fill_opacity = 1
                    child.style.stroke_color = None
                    child.style.blend_mode = GraphicsStyle.INHERIT
                    child.style.soft_mask = GraphicsStyle.INHERIT

        new_node = clone_structure(node)
        gc = (
            new_node
            if isinstance(new_node, GraphicsContext)
            else new_node.get_graphics_context()
        )
        _force_white(gc)
        return new_node

    @staticmethod
    def alpha_layers_from(node) -> Optional[GraphicsContext]:
        """
        Build a GraphicsContext that encodes the *alpha ramps* contributed by any
        `GradientPaint` used by *node*. Each contributing PaintedPath yields one
        rectangle covering its content-space bounding box; that rectangle is filled
        with an `_AlphaGradientPaint` (the gradient’s *alpha channel only*).
        Rectangles are stacked with `BM=Multiply` so multiple alpha sources
        combine multiplicatively.
        """
        layers = []
        for n in _iter_nodes(node):
            if isinstance(n, PaintedPath):
                for paint in (n.style.fill_color, n.style.stroke_color):
                    if (
                        isinstance(paint, GradientPaint)
                        and paint.gradient
                        and paint.gradient.has_alpha()
                    ):
                        bb = n.bounding_box(Point(0, 0), expand_for_stroke=False)[0]
                        if bb.width <= 0 or bb.height <= 0:
                            continue
                        rect = PaintedPath()
                        rect.rectangle(bb.x0, bb.y0, bb.width, bb.height)
                        alpha_paint = _AlphaGradientPaint(
                            gradient=paint.gradient,
                            units=paint.units,
                            gradient_transform=paint.gradient_transform,
                            apply_page_ctm=paint.apply_page_ctm,
                        )
                        rect.style.fill_color = alpha_paint
                        rect.style.stroke_color = None
                        rect.style.stroke_width = 0
                        rect.style.paint_rule = PathPaintRule.FILL_NONZERO

                        layer_gc = GraphicsContext()
                        layer_gc.add_item(rect, _copy=False)
                        # multiply multiple alpha contributors together
                        layer_gc.style.blend_mode = BlendMode.MULTIPLY
                        layers.append(layer_gc)

        if not layers:
            return None

        A = GraphicsContext()
        for layer in layers:
            A.add_item(layer)
        return A

    @classmethod
    def from_AB(
        cls,
        A: Optional[GraphicsContext],
        B: Union[PaintedPath, GraphicsContext],
        invert: bool,
        registry,
        region_bbox: Optional["BoundingBox"] = None,
    ) -> "PaintSoftMask":
        """
        Construct a **luminosity soft mask** from two ingredients:

        - **A**: Optional GraphicsContext encoding alpha ramps (e.g., the result of
        :meth:`alpha_layers_from`). If ``None``, the effective alpha is 1.
        - **B**: Coverage term (e.g., the result of :meth:`coverage_white`).

        The mask luminance is:
            - ``A × B``        when ``invert = False``
            - ``A × (1 − B)``  when ``invert = True``

        Implementation outline:
        1. Compute the union bbox of A and B (no stroke expansion).
        2. Paint a background rectangle: **black** for ``A×B`` or **white** for
        ``A×(1−B)``.
        3. Paint **B**; when ``invert=True``, set ``BM=Difference`` to obtain
        ``1−B`` from the white background.
        4. If A is present, paint it with ``BM=Multiply`` to apply the alpha ramp.
        5. Wrap the result as a Form XObject and attach it as ``/SMask`` with
        ``/S /Luminosity``.
        """

        # Decide the canvas/BBox for the soft mask
        if region_bbox is not None:
            union = region_bbox
        else:
            bb_A = (
                A.bounding_box(Point(0, 0), expand_for_stroke=False)[0] if A else None
            )
            bb_B = B.bounding_box(Point(0, 0), expand_for_stroke=False)[0]
            union = bb_B if bb_A is None else bb_A.merge(bb_B)

        canvas = GraphicsContext()

        # Background: black for A×B, white for A×(1−B)
        bg = PaintedPath()
        bg.rectangle(union.x0, union.y0, union.width, union.height)
        bg.style.fill_color = "#000000" if not invert else "#ffffff"
        bg.style.fill_opacity = 1
        bg.style.stroke_color = None
        canvas.add_item(bg)

        # Paint B (optionally build 1−B using Difference on white bg)
        if invert:
            B.style.blend_mode = BlendMode.DIFFERENCE
        canvas.add_item(B)

        # Multiply by A if present
        if A is not None:
            A.style.blend_mode = BlendMode.MULTIPLY
            canvas.add_item(A)

        sm = cls(canvas, invert=False, use_luminosity=True)
        _ = sm.render(registry)
        sm.object_id = registry.register_soft_mask(sm)
        return sm


def _iter_nodes(node):
    # Yields all GraphicsContext/PaintedPath nodes recursively
    if isinstance(node, PaintedPath):
        yield node
        root_gc = node.get_graphics_context()
        for ch in root_gc.path_items:
            if isinstance(ch, (GraphicsContext, PaintedPath)):
                yield from _iter_nodes(ch)
    elif isinstance(node, GraphicsContext):
        yield node
        for ch in node.path_items:
            if isinstance(ch, (GraphicsContext, PaintedPath)):
                yield from _iter_nodes(ch)


def _disable_auto_alpha(node: Union[PaintedPath, GraphicsContext]) -> None:
    for n in _iter_nodes(node):
        if isinstance(n, PaintedPath):
            for attr in ("fill_color", "stroke_color"):
                col = getattr(n.style, attr)
                if isinstance(col, GradientPaint):
                    # decide from the gradient, not col.has_alpha() (which checks skip_alpha)
                    if col.gradient and col.gradient.has_alpha():
                        col.skip_alpha = True


# pylint: disable=protected-access
def clone_structure(node):
    if isinstance(node, GraphicsContext):
        new = GraphicsContext()
        new.style = deepcopy(node.style)
        new.transform = node.transform
        new.clipping_path = node.clipping_path
        new.path_items = [
            (
                clone_structure(ch)
                if isinstance(ch, (GraphicsContext, PaintedPath))
                else ch
            )
            for ch in node.path_items
        ]
        return new
    if isinstance(node, PaintedPath):
        new = PaintedPath.__new__(PaintedPath)
        root = clone_structure(node.get_graphics_context())
        object.__setattr__(new, "_root_graphics_context", root)
        object.__setattr__(new, "_graphics_context", root)
        object.__setattr__(new, "_closed", node._closed)
        object.__setattr__(new, "_close_context", root)
        object.__setattr__(new, "_starter_move", node._starter_move)
        return new
    return node


class PaintComposite:

    @dataclass(frozen=True)
    class _Step:
        draw: str  # "source" or "backdrop"
        mask_from: Optional[str]  # "source" | "backdrop" | None
        invert: bool = False

    _MODES = {
        CompositingOperation.SOURCE: (_Step("source", None),),
        CompositingOperation.DESTINATION: (_Step("backdrop", None),),
        CompositingOperation.SOURCE_OVER: (
            _Step("backdrop", None),
            _Step("source", None),
        ),
        CompositingOperation.DESTINATION_OVER: (
            _Step("source", None),
            _Step("backdrop", None),
        ),
        CompositingOperation.SOURCE_IN: (_Step("source", "backdrop"),),
        CompositingOperation.DESTINATION_IN: (_Step("backdrop", "source"),),
        CompositingOperation.SOURCE_OUT: (_Step("source", "backdrop", True),),
        CompositingOperation.DESTINATION_OUT: (_Step("backdrop", "source", True),),
        CompositingOperation.SOURCE_ATOP: (
            _Step("backdrop", "source", True),
            _Step("source", "backdrop"),
        ),
        CompositingOperation.DESTINATION_ATOP: (
            _Step("source", "backdrop", True),
            _Step("backdrop", "source"),
        ),
        CompositingOperation.XOR: (
            _Step("source", "backdrop", True),
            _Step("backdrop", "source", True),
        ),
        CompositingOperation.CLEAR: tuple(),
    }

    def __init__(self, backdrop, source, operation: CompositingOperation):
        if not isinstance(backdrop, (PaintedPath, GraphicsContext)) or not isinstance(
            source, (PaintedPath, GraphicsContext)
        ):
            raise TypeError("PaintComposite requires two PaintedPath instances.")
        self.backdrop = backdrop
        self.source = source
        self.mode = operation

        if self.mode not in self._MODES:
            raise NotImplementedError(
                f"Compositing mode '{self.mode.value}' is not yet supported."
            )

    @classmethod
    def _with_mask(
        cls,
        path: Union[PaintedPath, GraphicsContext],
        mask_from: Union[PaintedPath, GraphicsContext],
        invert: bool,
        resource_registry,
    ) -> Union[PaintedPath, GraphicsContext]:
        p = deepcopy(path)

        A = PaintSoftMask.alpha_layers_from(p)
        B = PaintSoftMask.coverage_white(mask_from)

        bb_p = p.bounding_box(Point(0, 0), expand_for_stroke=False)[0]
        bb_B = B.bounding_box(Point(0, 0), expand_for_stroke=False)[0]
        region_bbox = bb_p.merge(bb_B)

        sm = PaintSoftMask.from_AB(
            A, B, invert, resource_registry, region_bbox=region_bbox
        )
        p.style.soft_mask = sm
        _disable_auto_alpha(p)
        return p

    def _pick(self, which: str) -> Union[PaintedPath, GraphicsContext]:
        return self.source if which == "source" else self.backdrop

    def render(
        self,
        resource_registry,
        style,
        last_item,
        initial_point,
        debug_stream=None,
        pfx=None,
    ):
        steps = self._MODES[self.mode]
        if not steps:  # CLEAR
            return "", last_item, initial_point

        parts = []
        for st in steps:
            node = self._pick(st.draw)
            if st.mask_from is not None:
                node = self._with_mask(
                    node, self._pick(st.mask_from), st.invert, resource_registry
                )
            s, last_item, initial_point = node.render(
                resource_registry, style, last_item, initial_point, debug_stream, pfx
            )
            parts.append(s)
        return " ".join(parts), last_item, initial_point

    def render_debug(
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        debug_stream.write(f"{pfx}<PaintComposite mode={self.mode}>\n")
        return self.render(
            resource_registry, style, last_item, initial_point, debug_stream, pfx
        )


class _BlendGroup:
    __slots__ = ("context", "base_style", "resources")

    def __init__(self, context: GraphicsContext, base_style: GraphicsStyle):
        self.context = context
        self.base_style = deepcopy(base_style)
        self.resources = set()

    def render(self, resource_registry):
        stream, _, _ = self.context.render(
            resource_registry,
            style=self.base_style,
            last_item=None,
            initial_point=Point(0, 0),
        )
        self.resources = resource_registry.scan_stream(stream)
        return stream

    def get_bounding_box(self) -> tuple[float, float, float, float]:
        bbox, _ = self.context.bounding_box(
            Point(0, 0), style=self.base_style, expand_for_stroke=True
        )
        if not bbox.is_valid():
            return (0.0, 0.0, 0.0, 0.0)
        return bbox.to_tuple()

    def get_resource_dictionary(
        self,
        gfxstate_objs_per_name,
        pattern_objs_per_name,
        shading_objs_per_name,
        font_objs_per_index,
        img_objs_per_index,
    ):
        resources_registered: dict[PDFResourceType, set] = {}
        for rtype, resource_id in self.resources:
            resources_registered.setdefault(rtype, set()).add(resource_id)

        parts: list[str] = []

        ext_g_states = resources_registered.get(PDFResourceType.EXT_G_STATE)
        if ext_g_states:
            serialized = "".join(
                f"{Name(name).serialize()} {gfxstate_objs_per_name[name].id} 0 R"
                for name in sorted(ext_g_states)
                if name in gfxstate_objs_per_name
            )
            if serialized:
                parts.append(f"{Name('ExtGState').serialize()}<<{serialized}>>")

        patterns = resources_registered.get(PDFResourceType.PATTERN)
        if patterns:
            serialized = "".join(
                f"{Name(name).serialize()} {pattern_objs_per_name[name].id} 0 R"
                for name in sorted(patterns)
                if name in pattern_objs_per_name
            )
            if serialized:
                parts.append(f"{Name('Pattern').serialize()}<<{serialized}>>")

        shadings = resources_registered.get(PDFResourceType.SHADING)
        if shadings:
            serialized = "".join(
                f"{Name(name).serialize()} {shading_objs_per_name[name].id} 0 R"
                for name in sorted(shadings)
                if name in shading_objs_per_name
            )
            if serialized:
                parts.append(f"{Name('Shading').serialize()}<<{serialized}>>")

        fonts = resources_registered.get(PDFResourceType.FONT)
        if fonts:
            serialized = "".join(
                f"{Name(f'F{idx}').serialize()} {font_objs_per_index[idx].id} 0 R"
                for idx in sorted(fonts)
                if idx in font_objs_per_index
            )
            if serialized:
                parts.append(f"{Name('Font').serialize()}<<{serialized}>>")

        xobjects = resources_registered.get(PDFResourceType.X_OBJECT)
        if xobjects:
            serialized = "".join(
                f"{Name(f'I{idx}').serialize()} {img_objs_per_index[idx].id} 0 R"
                for idx in sorted(xobjects)
                if idx in img_objs_per_index
            )
            if serialized:
                parts.append(f"{Name('XObject').serialize()}<<{serialized}>>")

        return "<<" + "".join(parts) + ">>" if parts else "<<>>"


class PaintBlendComposite:
    __slots__ = ("backdrop", "source", "blend_mode", "_form_index")

    def __init__(
        self,
        backdrop: Union[GraphicsContext, PaintedPath],
        source: Union[GraphicsContext, PaintedPath],
        blend_mode: BlendMode,
    ):
        if not isinstance(backdrop, (PaintedPath, GraphicsContext)) or not isinstance(
            source, (PaintedPath, GraphicsContext)
        ):
            raise TypeError(
                "PaintBlendComposite requires PaintedPath or GraphicsContext operands."
            )
        self.backdrop = backdrop
        self.source = source
        self.blend_mode = blend_mode
        self._form_index: Optional[int] = None

    def _ensure_form_index(self, resource_registry, base_style: GraphicsStyle) -> int:
        if self._form_index is not None:
            return self._form_index

        group = GraphicsContext()
        backdrop_node = self.backdrop
        source_node = self.source

        if hasattr(source_node, "style"):
            source_node.style.blend_mode = self.blend_mode
            if source_node.style.allow_transparency is False:
                source_node.style.allow_transparency = GraphicsStyle.INHERIT

        group.add_item(backdrop_node, _copy=False)
        group.add_item(source_node, _copy=False)

        effective_style = (
            base_style if isinstance(base_style, GraphicsStyle) else GraphicsStyle()
        )
        blend_group = _BlendGroup(group, effective_style)
        self._form_index = resource_registry.register_blend_form(blend_group)
        self.backdrop = None
        self.source = None
        return self._form_index

    # pylint: disable=unused-argument
    def render(
        self,
        resource_registry,
        style,
        last_item,
        initial_point,
        debug_stream=None,
        pfx=None,
    ):
        form_index = self._ensure_form_index(resource_registry, style)
        rendered = f"q /I{form_index} Do Q"
        return rendered, last_item, initial_point

    def render_debug(
        self, resource_registry, style, last_item, initial_point, debug_stream, pfx
    ):
        debug_stream.write(f"{pfx}<PaintBlendComposite mode={self.blend_mode}>\n")
        return self.render(
            resource_registry, style, last_item, initial_point, debug_stream, pfx
        )


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


class GlyphPathPen(PathPen):
    """A pen that can be used to draw glyphs into a `PaintedPath`."""

    def _closePath(self):
        """
        The difference between GlyphPathPen and PathPen is that GlyphPathPen does not
        remove the last path element before closing the path.
        This last line back to start point is necessary for correctly rendering glyphs.
        """
        self.pdf_path.close()
