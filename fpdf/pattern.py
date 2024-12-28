"""
Handles the creation of patterns and gradients
"""

from abc import ABC
from typing import List, Optional, TYPE_CHECKING, Tuple, Union

from .drawing import DeviceCMYK, DeviceGray, DeviceRGB, convert_to_device_color
from .syntax import Name, PDFArray, PDFObject

if TYPE_CHECKING:
    from .fpdf import FPDF


class Pattern(PDFObject):
    """
    Represents a PDF Pattern object.

    Currently, this class supports only "shading patterns" (pattern_type 2),
    using either a linear or radial gradient. Tiling patterns (pattern_type 1)
    are not yet implemented.
    """

    def __init__(self, shading: Union["LinearGradient", "RadialGradient"]):
        super().__init__()
        self.type = Name("Pattern")
        # 1 for a tiling pattern or type 2 for a shading pattern:
        self.pattern_type = 2
        self._shading = shading

    @property
    def shading(self):
        return f"{self._shading.get_shading_object().id} 0 R"


class Type2Function(PDFObject):
    """Transition between 2 colors"""

    def __init__(self, color_1, color_2):
        super().__init__()
        # 0: Sampled function; 2: Exponential interpolation function; 3: Stitching function; 4: PostScript calculator function
        self.function_type = 2
        self.domain = "[0 1]"
        self.c0 = f'[{" ".join(f"{c:.2f}" for c in color_1.colors)}]'
        self.c1 = f'[{" ".join(f"{c:.2f}" for c in color_2.colors)}]'
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
        self.bounds = f"[{' '.join(f'{bound:.2f}' for bound in bounds)}]"
        self.encode = f"[{' '.join('0 1' for _ in functions)}]"
        self.n = 1

    @property
    def functions(self):
        return f"[{' '.join(f'{f.id} 0 R' for f in self._functions)}]"


class Shading(PDFObject):
    def __init__(
        self,
        shading_type: int,  # 2 for axial shading, 3 for radial shading
        background: Optional[Union[DeviceRGB, DeviceGray, DeviceCMYK]],
        color_space: str,
        coords: List[int],
        function: Union[Type2Function, Type3Function],
        extend_before: bool,
        extend_after: bool,
    ):
        super().__init__()
        self.shading_type = shading_type
        self.background = (
            f'[{" ".join(f"{c:.2f}" for c in background.colors)}]' if background else None
        )
        self.color_space = Name(color_space)
        self.coords = coords
        self.function = f"{function.id} 0 R"
        self.extend = f'[{"true" if extend_before else "false"} {"true" if extend_after else "false"}]'


class Gradient(ABC):
    def __init__(self, colors, background, extend_before, extend_after):
        self.color_space, self.colors = self._convert_colors(colors)
        self.background = None
        if background:
            self.background = (
                convert_to_device_color(background)
                if isinstance(background, (str, DeviceGray, DeviceRGB, DeviceCMYK))
                else convert_to_device_color(*background)
            )
        if self.background and self.background.__class__.__name__ != self.color_space:
            raise ValueError(
                "The background color must be of the same color space as the gradient"
            )
        self.extend_before = extend_before
        self.extend_after = extend_after
        self.functions = self._generate_functions()
        self.pattern = Pattern(self)
        self._shading_object = None
        self.coords = None
        self.shading_type = 0

    @classmethod
    def _convert_colors(cls, colors) -> Tuple[str, List]:
        color_list = []
        if len(colors) < 2:
            raise ValueError("A gradient must have at least two colors")
        color_spaces = set()
        for color in colors:
            current_color = (
                convert_to_device_color(color)
                if isinstance(color, (str, DeviceGray, DeviceRGB, DeviceCMYK))
                else convert_to_device_color(*color)
            )
            color_list.append(current_color)
            color_spaces.add(type(current_color).__name__)
        if len(color_spaces) == 1:
            return color_spaces.pop(), color_list
        if "DeviceCMYK" in color_spaces:
            raise ValueError("Can't mix CMYK with other color spaces.")
        # mix of DeviceGray and DeviceRGB
        converted = []
        for color in color_list:
            if isinstance(color, DeviceGray):
                converted.append(DeviceRGB(color.g, color.g, color.g))
            else:
                converted.append(color)
        return "DeviceRGB", converted

    def _generate_functions(self):
        if len(self.colors) < 2:
            raise ValueError("A gradient must have at least two colors")
        if len(self.colors) == 2:
            return [Type2Function(self.colors[0], self.colors[1])]
        number_of_colors = len(self.colors)
        functions = []
        for i in range(number_of_colors - 1):
            functions.append(Type2Function(self.colors[i], self.colors[i + 1]))
        functions.append(
            Type3Function(
                functions[:],
                [(i + 1) / (number_of_colors - 1) for i in range(number_of_colors - 2)],
            )
        )
        return functions

    def get_shading_object(self):
        if not self._shading_object:
            self._shading_object = Shading(
                shading_type=self.shading_type,
                background=self.background,
                color_space=self.color_space,
                coords=PDFArray(self.coords),
                function=self.functions[-1],
                extend_before=self.extend_before,
                extend_after=self.extend_after,
            )
        return self._shading_object

    def get_pattern(self):
        return self.pattern


class LinearGradient(Gradient):
    def __init__(
        self,
        fpdf: "FPDF",
        from_x: int,
        from_y: int,
        to_x: int,
        to_y: int,
        colors: List,
        background=None,
        extend_before: bool = False,
        extend_after: bool = False,
    ):
        super().__init__(colors, background, extend_before, extend_after)
        coords = [from_x, fpdf.h - from_y, to_x, fpdf.h - to_y]
        self.coords = [f"{fpdf.k * c:.2f}" for c in coords]
        self.shading_type = 2


class RadialGradient(Gradient):
    def __init__(
        self,
        fpdf: "FPDF",
        start_circle_x: int,
        start_circle_y: int,
        start_circle_radius: int,
        end_circle_x: int,
        end_circle_y: int,
        end_circle_radius: int,
        colors: List,
        background=None,
        extend_before: bool = False,
        extend_after: bool = False,
    ):
        super().__init__(colors, background, extend_before, extend_after)
        coords = [
            start_circle_x,
            fpdf.h - start_circle_y,
            start_circle_radius,
            end_circle_x,
            fpdf.h - end_circle_y,
            end_circle_radius,
        ]
        self.coords = [f"{fpdf.k * c:.2f}" for c in coords]
        self.shading_type = 3
