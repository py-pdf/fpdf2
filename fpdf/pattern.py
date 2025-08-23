"""
Handles the creation of patterns and gradients

Usage documentation at: <https://py-pdf.github.io/fpdf2/Patterns.html>
"""

from abc import ABC
from typing import List, Optional, Tuple, Union

from .drawing_primitives import (
    DeviceCMYK,
    DeviceGray,
    DeviceRGB,
    Transform,
    convert_to_device_color,
)
from .syntax import Name, PDFArray, PDFObject

Color = Union[DeviceRGB, DeviceGray, DeviceCMYK]


def format_number(x: float, digits: int = 8) -> str:
    # snap tiny values to zero to avoid "-0" and scientific notation
    if abs(x) < 1e-12:
        x = 0.0
    s = f"{x:.{digits}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if s == "-0":
        s = "0"
    if s.startswith("."):
        s = "0" + s
    if s.startswith("-."):
        s = s.replace("-.", "-0.", 1)
    return s


class Pattern(PDFObject):
    """
    Represents a PDF Pattern object.

    Currently, this class supports only "shading patterns" (pattern_type 2),
    using either a linear or radial gradient. Tiling patterns (pattern_type 1)
    are not yet implemented.
    """

    def __init__(self, shading: "Gradient"):
        super().__init__()
        self.type = Name("Pattern")
        # 1 for a tiling pattern or type 2 for a shading pattern:
        self.pattern_type = 2
        self._shading = shading
        self._matrix = Transform.identity()
        # If True (default), OutputProducer will bake the page CTM into this pattern.
        # For patterns used inside Form XObjects (e.g., soft masks), set to False.
        self._apply_page_ctm = True

    @property
    def shading(self) -> str:
        return f"{self._shading.get_shading_object().id} 0 R"

    @property
    def matrix(self) -> str:
        return (
            f"[{format_number(self._matrix.a)} {format_number(self._matrix.b)} "
            f"{format_number(self._matrix.c)} {format_number(self._matrix.d)} "
            f"{format_number(self._matrix.e)} {format_number(self._matrix.f)}]"
        )

    def set_matrix(self, matrix) -> "Pattern":
        self._matrix = matrix
        return self

    def get_matrix(self) -> Transform:
        return self._matrix

    def set_apply_page_ctm(self, apply: bool) -> None:
        self._apply_page_ctm = apply

    def get_apply_page_ctm(self) -> bool:
        return self._apply_page_ctm


class Type2Function(PDFObject):
    """Transition between 2 colors"""

    def __init__(self, color_1, color_2):
        super().__init__()
        # 0: Sampled function; 2: Exponential interpolation function; 3: Stitching function; 4: PostScript calculator function
        self.function_type = 2
        self.domain = "[0 1]"
        c1 = self._get_color_components(color_1)
        c2 = self._get_color_components(color_2)
        if len(c1) != len(c2):
            raise ValueError("Type2Function endpoints must have same component count")
        self.c0 = f'[{" ".join(format_number(c) for c in c1)}]'
        self.c1 = f'[{" ".join(format_number(c) for c in c2)}]'
        self.n = 1

    @classmethod
    def _get_color_components(cls, color):
        if isinstance(color, DeviceGray):
            return [color.g]
        return color.colors


class Type2FunctionGray(PDFObject):
    """1‑channel exponential interpolation for alpha/luminance ramps."""

    def __init__(self, g0: float, g1: float):
        super().__init__()
        self.function_type = 2
        self.domain = "[0 1]"
        self.c0 = f"[{format_number(g0)}]"
        self.c1 = f"[{format_number(g1)}]"
        self.n = 1


class Type3Function(PDFObject):
    """When multiple colors are used, a type 3 function is necessary to stitch type 2 functions together
    and define the bounds between each color transition"""

    def __init__(self, functions, bounds):
        super().__init__()
        # 0: Sampled function; 2: Exponential interpolation function; 3: Stitching function; 4: PostScript calculator function
        self.function_type = 3
        self.domain = "[0 1]"
        self._functions = functions
        self.bounds = f"[{' '.join(format_number(bound) for bound in bounds)}]"
        self.encode = f"[{' '.join('0 1' for _ in functions)}]"

    @property
    def functions(self):
        return f"[{' '.join(f'{f.id} 0 R' for f in self._functions)}]"


class Shading(PDFObject):
    def __init__(
        self,
        shading_type: int,  # 2 for axial shading, 3 for radial shading
        background: Optional[Color],
        color_space: str,
        coords: List[float],
        functions: List[Union[Type2Function, Type3Function]],
        extend_before: bool,
        extend_after: bool,
    ):
        super().__init__()
        self.shading_type = shading_type
        self.background = (
            f'[{" ".join(format_number(c) for c in background.colors)}]'
            if background
            else None
        )
        self.color_space = Name(color_space)
        self.coords = coords
        self._functions = functions
        self.extend = f'[{"true" if extend_before else "false"} {"true" if extend_after else "false"}]'
        self.anti_alias = True

    @property
    def function(self) -> str:
        """Reference to the *top-level* function object for the shading dictionary."""
        return f"{self._functions[-1].id} 0 R"

    def get_functions(self):
        """All function objects used by this shading (Type2 segments + final Type3)."""
        return self._functions

    def get_shading_object(self) -> "Shading":
        """Return self, as this is already a shading object."""
        return self


class Gradient(ABC):
    def __init__(self, colors, background, extend_before, extend_after, bounds):
        self.color_space, self.colors, self._alphas = self._convert_colors(colors)
        self.background = None
        if background:
            bg = (
                convert_to_device_color(background)
                if isinstance(background, (str, DeviceGray, DeviceRGB, DeviceCMYK))
                else convert_to_device_color(*background)
            )
            # Re-map background to the chosen palette colorspace
            if self.color_space == "DeviceGray":
                if isinstance(bg, DeviceRGB):
                    bg = bg.to_gray()
                elif isinstance(bg, DeviceCMYK):
                    raise ValueError("Can't mix CMYK background with non-CMYK gradient")
            elif self.color_space == "DeviceRGB":
                if isinstance(bg, DeviceGray):
                    bg = DeviceRGB(bg.g, bg.g, bg.g)
                elif isinstance(bg, DeviceCMYK):
                    raise ValueError("Can't mix CMYK background with non-CMYK gradient")
            self.background = bg
        self.extend_before = extend_before
        self.extend_after = extend_after
        self.bounds = (
            bounds
            if bounds
            else [(i + 1) / (len(self.colors) - 1) for i in range(len(self.colors) - 2)]
        )
        if len(self.bounds) != len(self.colors) - 2:
            raise ValueError(
                "Bounds array length must be two less than the number of colors"
            )
        self.functions = self._generate_functions()
        self.pattern = Pattern(self)
        self._shading_object = None
        self._alpha_shading_object = None
        self.coords = None
        self.shading_type = 0

    @classmethod
    def _convert_colors(cls, colors) -> Tuple[str, List, List[float]]:
        """Normalize colors to a single device colorspace and capture per-stop alpha (default 1.0)."""
        if len(colors) < 2:
            raise ValueError("A gradient must have at least two colors")

        # 1) Convert everything to Device* instances
        palette = []
        spaces = set()
        alphas = []
        for color in colors:
            dc = (
                convert_to_device_color(color)
                if isinstance(color, (str, DeviceGray, DeviceRGB, DeviceCMYK))
                else convert_to_device_color(*color)
            )
            palette.append(dc)
            spaces.add(type(dc).__name__)
            a = getattr(dc, "a", None)
            alphas.append(float(a) if a is not None else 1.0)

        # 2) Disallow any CMYK mixture with others
        if "DeviceCMYK" in spaces and len(spaces) > 1:
            raise ValueError("Can't mix CMYK with other color spaces.")

        # 3) If we ended up with plain CMYK, we're done
        if spaces == {"DeviceCMYK"}:
            return "DeviceCMYK", palette, alphas

        # 4) Promote mix of Gray+RGB to RGB
        if spaces == {"DeviceGray", "DeviceRGB"}:
            promoted = []
            for c in palette:
                if isinstance(c, DeviceGray):
                    promoted.append(DeviceRGB(c.g, c.g, c.g))
                else:
                    promoted.append(c)
            return "DeviceRGB", promoted, alphas

        # 5) All Gray: stay Gray
        if spaces == {"DeviceGray"}:
            return "DeviceGray", palette, alphas

        # 6) All RGB: optionally downcast to Gray if all are achromatic
        if spaces == {"DeviceRGB"}:
            if all(c.is_achromatic() for c in palette):
                return "DeviceGray", [c.to_gray() for c in palette], alphas
            return "DeviceRGB", palette, alphas

        # Fallback: default to RGB
        return "DeviceRGB", palette, alphas

    def _generate_functions(self):
        if len(self.colors) < 2:
            raise ValueError("A gradient must have at least two colors")
        if len(self.colors) == 2:
            return [Type2Function(self.colors[0], self.colors[1])]
        number_of_colors = len(self.colors)
        functions = []
        for i in range(number_of_colors - 1):
            functions.append(Type2Function(self.colors[i], self.colors[i + 1]))
        functions.append(Type3Function(functions[:], self.bounds))
        return functions

    def get_functions(self):
        return self.functions

    def get_shading_object(self):
        if not self._shading_object:
            self._shading_object = Shading(
                shading_type=self.shading_type,
                background=self.background,
                color_space=self.color_space,
                coords=PDFArray(self.coords),
                functions=self.functions,
                extend_before=self.extend_before,
                extend_after=self.extend_after,
            )
        return self._shading_object

    def get_pattern(self):
        return self.pattern

    def has_alpha(self) -> bool:
        """True if any stop carries alpha != 1.0."""
        return any(abs(a - 1.0) > 1e-9 for a in self._alphas)

    def _generate_alpha_functions(self):
        """Stitched Type2 gray functions mirroring the color ramp bounds."""
        if len(self._alphas) < 2:
            raise ValueError("Alpha ramp requires at least two stops")
        if len(self._alphas) == 2:
            return [Type2FunctionGray(self._alphas[0], self._alphas[1])]
        functions = []
        for i in range(len(self._alphas) - 1):
            functions.append(Type2FunctionGray(self._alphas[i], self._alphas[i + 1]))
        functions.append(Type3Function(functions[:], self.bounds))
        return functions

    def get_alpha_shading_object(self):
        """Grayscale Shading object representing the alpha ramp (for a soft mask)."""
        if not self.has_alpha():
            return None
        if not self._alpha_shading_object:
            self._alpha_shading_object = Shading(
                shading_type=self.shading_type,
                background=None,  # mask content should be pure coverage, no bg
                color_space="DeviceGray",
                coords=PDFArray(self.coords),
                functions=self._generate_alpha_functions(),
                extend_before=False,
                extend_after=False,
            )
        return self._alpha_shading_object


class LinearGradient(Gradient):
    def __init__(
        self,
        from_x: float,
        from_y: float,
        to_x: float,
        to_y: float,
        colors: List,
        background=None,
        extend_before: bool = False,
        extend_after: bool = False,
        bounds: Optional[List[float]] = None,
    ):
        """
        A shading pattern that creates a linear (axial) gradient in a PDF.

        The gradient is defined by two points: (from_x, from_y) and (to_x, to_y),
        along which the specified colors are interpolated. Optionally, you can set
        a background color, extend the gradient beyond its start or end, and
        specify custom color stop positions via `bounds`.

        Args:
            fpdf (FPDF): The FPDF instance used for PDF generation.
            from_x (int or float): The x-coordinate of the starting point of the gradient,
                in user space units.
            from_y (int or float): The y-coordinate of the starting point of the gradient,
                in user space units.
            to_x (int or float): The x-coordinate of the ending point of the gradient,
                in user space units.
            to_y (int or float): The y-coordinate of the ending point of the gradient,
                in user space units.
            colors (List[str or Tuple[int, int, int]]): A list of colors along which the gradient
                will be interpolated. Colors may be given as hex strings (e.g., "#FF0000") or
                (R, G, B) tuples.
            background (str or Tuple[int, int, int], optional): A background color to use
                if the gradient does not fully cover the region it is applied to.
                Defaults to None (no background).
            extend_before (bool, optional): Whether to extend the first color beyond the
                starting point (from_x, from_y). Defaults to False.
            extend_after (bool, optional): Whether to extend the last color beyond the
                ending point (to_x, to_y). Defaults to False.
            bounds (List[float], optional): An optional list of floats in the range (0, 1)
                that represent gradient stops for color transitions. The number of bounds
                should be two less than the number of colors (for multi-color gradients).
                Defaults to None, which evenly distributes color stops.
        """
        super().__init__(colors, background, extend_before, extend_after, bounds)
        self.coords = [from_x, from_y, to_x, to_y]
        self.shading_type = 2


class RadialGradient(Gradient):
    def __init__(
        self,
        start_circle_x: float,
        start_circle_y: float,
        start_circle_radius: float,
        end_circle_x: float,
        end_circle_y: float,
        end_circle_radius: float,
        colors: List,
        background=None,
        extend_before: bool = False,
        extend_after: bool = False,
        bounds: Optional[List[float]] = None,
    ):
        """
        A shading pattern that creates a radial (or circular/elliptical) gradient in a PDF.

        The gradient is defined by two circles (start and end). Colors are blended from the
        start circle to the end circle, forming a radial gradient. You can optionally set a
        background color, extend the gradient beyond its circles, and provide custom color
        stop positions via `bounds`.

        Args:
            fpdf (FPDF): The FPDF instance used for PDF generation.
            start_circle_x (int or float): The x-coordinate of the inner circle's center,
                in user space units.
            start_circle_y (int or float): The y-coordinate of the inner circle's center,
                in user space units.
            start_circle_radius (int or float): The radius of the inner circle, in user space units.
            end_circle_x (int or float): The x-coordinate of the outer circle's center,
                in user space units.
            end_circle_y (int or float): The y-coordinate of the outer circle's center,
                in user space units.
            end_circle_radius (int or float): The radius of the outer circle, in user space units.
            colors (List[str or Tuple[int, int, int]]): A list of colors along which the gradient
                will be interpolated. Colors may be given as hex strings (e.g., "#FF0000") or
                (R, G, B) tuples.
            background (str or Tuple[int, int, int], optional): A background color to display
                if the gradient does not fully cover the region it's applied to. Defaults to None
                (no background).
            extend_before (bool, optional): Whether to extend the gradient beyond the start circle.
                Defaults to False.
            extend_after (bool, optional): Whether to extend the gradient beyond the end circle.
                Defaults to False.
            bounds (List[float], optional): An optional list of floats in the range (0, 1) that
                represent gradient stops for color transitions. The number of bounds should be one
                less than the number of colors (for multi-color gradients). Defaults to None,
                which evenly distributes color stops.
        """
        super().__init__(colors, background, extend_before, extend_after, bounds)
        self.coords = [
            start_circle_x,
            start_circle_y,
            start_circle_radius,
            end_circle_x,
            end_circle_y,
            end_circle_radius,
        ]
        self.shading_type = 3


def shape_linear_gradient(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    stops: List[Tuple[float, Union[Color, str]]],
) -> LinearGradient:
    """Create a linear gradient for a shape with SVG-like stops (offset in [0,1])."""
    if not stops:
        raise ValueError("At least one stop is required")

    TOLERANCE = 1e-9

    # 1) Normalize offsets, clamp, sort
    normalized = []
    for off, color in stops:
        offset = 0.0 if off < 0.0 else 1.0 if off > 1.0 else float(off)
        normalized.append((offset, color))
    normalized.sort(key=lambda t: t[0])

    # 2) Merge duplicates (or near-duplicates): keep the *last* color for same offset
    merged = []
    for o, c in normalized:
        if merged and abs(merged[-1][0] - o) <= TOLERANCE:
            merged[-1] = (o, c)
        else:
            merged.append((o, c))

    # 3) Single-stop: synthesize flat gradient
    if len(merged) == 1:
        o, c = merged[0]
        merged = [(0.0, c), (1.0, c)]

    # 4) Ensure first at 0 and last at 1 (with tolerance)
    if abs(merged[0][0] - 0.0) > TOLERANCE:
        merged.insert(0, (0.0, merged[0][1]))

    if abs(merged[-1][0] - 1.0) > TOLERANCE:
        merged.append((1.0, merged[-1][1]))

    colors = [color for _, color in merged]
    bounds = [offset for offset, _ in merged[1:-1]]

    return LinearGradient(
        from_x=x1,
        from_y=y1,
        to_x=x2,
        to_y=y2,
        colors=colors,
        bounds=bounds,
        extend_before=True,
        extend_after=True,
    )


def shape_radial_gradient(
    cx: float,
    cy: float,
    r: float,
    stops: List[Tuple[float, Union[Color, str]]],
    fx: Optional[float] = None,
    fy: Optional[float] = None,
    fr: float = 0.0,
) -> RadialGradient:
    """
    Create a radial gradient for a shape with SVG-like stops (offset in [0,1]).
    - (cx, cy, r): outer circle
    - (fx, fy, fr): focal/inner circle (defaults to center with radius 0)
    """
    if not stops:
        raise ValueError("At least one stop is required")

    TOLERANCE = 1e-9

    # 1) Normalize, clamp, sort
    normalized = []
    for off, color in stops:
        offset = 0.0 if off < 0.0 else 1.0 if off > 1.0 else float(off)
        normalized.append((offset, color))
    normalized.sort(key=lambda t: t[0])

    # 2) Merge duplicate/near-duplicate offsets (last wins)
    merged = []
    for offset, color in normalized:
        if merged and abs(merged[-1][0] - offset) <= TOLERANCE:
            merged[-1] = (offset, color)
        else:
            merged.append((offset, color))

    # 3) Single-stop: flat gradient
    if len(merged) == 1:
        _, c = merged[0]
        merged = [(0.0, c), (1.0, c)]

    # 4) Ensure first at 0 and last at 1 (with tolerance)
    if abs(merged[0][0] - 0.0) > TOLERANCE:
        merged.insert(0, (0.0, merged[0][1]))

    if abs(merged[-1][0] - 1.0) > TOLERANCE:
        merged.append((1.0, merged[-1][1]))

    colors = [color for _, color in merged]
    bounds = [offset for offset, _ in merged[1:-1]]

    if r < 0:
        raise ValueError("Outer radius r must be >= 0")
    if fr < 0:
        fr = 0.0
    if fx is None:
        fx = cx
    if fy is None:
        fy = cy
    # If inner radius exceeds outer, clamp
    if fr > r:
        fr = r

    return RadialGradient(
        start_circle_x=fx,
        start_circle_y=fy,
        start_circle_radius=fr,
        end_circle_x=cx,
        end_circle_y=cy,
        end_circle_radius=r,
        colors=colors,
        bounds=bounds,
        extend_before=True,
        extend_after=True,
    )
