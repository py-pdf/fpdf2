"""
Mixin class for managing a stack of graphics state variables.

The contents of this module are internal to fpdf2, and not part of the public API.
They may change at any time without prior warning or any deprecation period,
in non-backward-compatible ways.

Usage documentation at: <https://py-pdf.github.io/fpdf2/Internals.html#graphicsstatemixin>
"""

from copy import copy
from typing import TYPE_CHECKING, Any, Optional, Sequence

from .drawing_primitives import DeviceCMYK, DeviceGray, DeviceRGB
from .enums import CharVPos, TextEmphasis, TextMode
from .fonts import CoreFont, FontFace, TTFFont
from .util import Number

StateStackType = dict[str, Any]


class GraphicsStateMixin:
    """Mixin class for managing a stack of graphics state variables.

    To the subclassing library and its users, the variables look like
    normal instance attributes. But by the magic of properties, we can
    push and pop levels as needed, and users will always see and modify
    just the current version.

    This class is mixed in by fpdf.FPDF(), and is not meant to be used
    directly by user code.
    """

    DEFAULT_DRAW_COLOR = DeviceGray(0)
    DEFAULT_FILL_COLOR = DeviceGray(0)
    DEFAULT_TEXT_COLOR = DeviceGray(0)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.__statestack: list[StateStackType] = [
            dict(
                draw_color=self.DEFAULT_DRAW_COLOR,
                fill_color=self.DEFAULT_FILL_COLOR,
                text_color=self.DEFAULT_TEXT_COLOR,
                underline=False,
                strikethrough=False,
                font_style="",
                font_stretching=100,
                char_spacing=0,
                font_family="",
                font_size_pt=0,
                current_font=None,
                current_font_is_set_on_page=False,
                dash_pattern=dict(dash=0, gap=0, phase=0),
                line_width=0,
                text_mode=TextMode.FILL,
                char_vpos=CharVPos.LINE,
                sub_scale=0.7,
                sup_scale=0.7,
                nom_scale=0.75,
                denom_scale=0.75,
                sub_lift=-0.15,
                sup_lift=0.4,
                nom_lift=0.2,
                denom_lift=0.0,
                text_shaping=None,
            )
        ]
        super().__init__(*args, **kwargs)

    def _push_local_stack(self, new: Optional[StateStackType] = None) -> StateStackType:
        "Push a graphics state on the stack"
        if not new:
            new = self._get_current_graphics_state()
        self.__statestack.append(new)
        return new

    def _pop_local_stack(self) -> StateStackType:
        "Pop the last graphics state on the stack"
        return self.__statestack.pop()

    def _get_current_graphics_state(self) -> StateStackType:
        "Retrieve the current graphics state"
        # "current_font" must be shallow copied
        # "text_shaping" must be deep copied (different fragments may have different languages/direction)
        # Doing a whole copy and then creating a copy of text_shaping to achieve this result
        gs = copy(self.__statestack[-1])
        gs["text_shaping"] = copy(gs["text_shaping"])
        return gs

    def _is_current_graphics_state_nested(self) -> bool:
        "Indicate if the stack contains items (else it is empty)"
        return len(self.__statestack) > 1

    @property
    def draw_color(self) -> Optional[DeviceRGB | DeviceCMYK | DeviceGray]:
        if TYPE_CHECKING:
            assert isinstance(
                self.__statestack[-1]["draw_color"],
                (DeviceRGB, DeviceGray, DeviceCMYK, type(None)),
            )
        return self.__statestack[-1]["draw_color"]

    @draw_color.setter
    def draw_color(
        self,
        v: Optional[
            DeviceGray | DeviceRGB | DeviceCMYK | str | Number | Sequence[Number]
        ],
    ) -> None:
        self.__statestack[-1]["draw_color"] = v

    @property
    def fill_color(self) -> Optional[DeviceRGB | DeviceCMYK | DeviceGray]:
        if TYPE_CHECKING:
            assert isinstance(
                self.__statestack[-1]["fill_color"],
                (DeviceRGB, DeviceGray, DeviceCMYK, type(None)),
            )
        return self.__statestack[-1]["fill_color"]

    @fill_color.setter
    def fill_color(
        self,
        v: Optional[
            DeviceGray | DeviceRGB | DeviceCMYK | str | Number | Sequence[Number]
        ],
    ) -> None:
        self.__statestack[-1]["fill_color"] = v

    @property
    def text_color(self) -> Optional[DeviceRGB | DeviceCMYK | DeviceGray]:
        if TYPE_CHECKING:
            assert isinstance(
                self.__statestack[-1]["text_color"],
                (DeviceRGB, DeviceGray, DeviceCMYK, type(None)),
            )
        return self.__statestack[-1]["text_color"]

    @text_color.setter
    def text_color(
        self,
        v: Optional[
            DeviceGray | DeviceRGB | DeviceCMYK | str | Number | Sequence[Number]
        ],
    ) -> None:
        self.__statestack[-1]["text_color"] = v

    @property
    def underline(self) -> bool:
        if TYPE_CHECKING:
            assert isinstance(self.__statestack[-1]["underline"], bool)
        return self.__statestack[-1]["underline"]

    @underline.setter
    def underline(self, v: bool) -> None:
        self.__statestack[-1]["underline"] = v

    @property
    def strikethrough(self) -> bool:
        if TYPE_CHECKING:
            assert isinstance(self.__statestack[-1]["strikethrough"], bool)
        return self.__statestack[-1]["strikethrough"]

    @strikethrough.setter
    def strikethrough(self, v: bool) -> None:
        self.__statestack[-1]["strikethrough"] = v

    @property
    def font_style(self) -> str:
        if TYPE_CHECKING:
            assert isinstance(self.__statestack[-1]["font_style"], str)
        return self.__statestack[-1]["font_style"]

    @font_style.setter
    def font_style(self, v: str) -> None:
        self.__statestack[-1]["font_style"] = v

    @property
    def font_stretching(self) -> float:
        if TYPE_CHECKING:
            assert isinstance(self.__statestack[-1]["font_stretching"], float)
        return self.__statestack[-1]["font_stretching"]

    @font_stretching.setter
    def font_stretching(self, v: float) -> None:
        self.__statestack[-1]["font_stretching"] = v

    @property
    def char_spacing(self) -> float:
        if TYPE_CHECKING:
            assert isinstance(self.__statestack[-1]["char_spacing"], float)
        return self.__statestack[-1]["char_spacing"]

    @char_spacing.setter
    def char_spacing(self, v: float) -> None:
        self.__statestack[-1]["char_spacing"] = v

    @property
    def font_family(self) -> str:
        if TYPE_CHECKING:
            assert isinstance(self.__statestack[-1]["font_family"], str)
        return self.__statestack[-1]["font_family"]

    @font_family.setter
    def font_family(self, v: str) -> None:
        self.__statestack[-1]["font_family"] = v

    @property
    def font_size_pt(self) -> float:
        if TYPE_CHECKING:
            assert isinstance(self.__statestack[-1]["font_size_pt"], float)
        return self.__statestack[-1]["font_size_pt"]

    @font_size_pt.setter
    def font_size_pt(self, v: float) -> None:
        self.__statestack[-1]["font_size_pt"] = v

    @property
    def font_size(self) -> float:
        if TYPE_CHECKING:
            assert isinstance(self.__statestack[-1]["font_size_pt"], float)
            assert isinstance(self.k, float)  # type: ignore[attr-defined]
        return self.__statestack[-1]["font_size_pt"] / self.k  # type: ignore[attr-defined]

    @font_size.setter
    def font_size(self, v: float) -> None:
        self.__statestack[-1]["font_size_pt"] = v * self.k  # type: ignore[attr-defined]

    @property
    def current_font(self) -> Optional[CoreFont | TTFFont]:
        if TYPE_CHECKING:
            assert isinstance(
                self.__statestack[-1]["current_font"], (CoreFont, TTFFont, type(None))
            )
        return self.__statestack[-1]["current_font"]

    @current_font.setter
    def current_font(self, v: CoreFont | TTFFont) -> None:
        self.__statestack[-1]["current_font"] = v

    @property
    def current_font_is_set_on_page(self) -> bool:
        if TYPE_CHECKING:
            assert isinstance(
                self.__statestack[-1]["current_font_is_set_on_page"], bool
            )
        return self.__statestack[-1]["current_font_is_set_on_page"]

    @current_font_is_set_on_page.setter
    def current_font_is_set_on_page(self, v: bool) -> None:
        self.__statestack[-1]["current_font_is_set_on_page"] = v

    @property
    def dash_pattern(self) -> dict[str, float]:
        if TYPE_CHECKING:
            assert isinstance(self.__statestack[-1]["dash_pattern"], dict)
        return self.__statestack[-1][
            "dash_pattern"
        ]  # pyright: ignore[reportUnknownVariableType]

    @dash_pattern.setter
    def dash_pattern(self, v: dict[str, float]) -> None:
        self.__statestack[-1]["dash_pattern"] = v

    @property
    def line_width(self) -> float:
        if TYPE_CHECKING:
            assert isinstance(self.__statestack[-1]["line_width"], float)
        return self.__statestack[-1]["line_width"]

    @line_width.setter
    def line_width(self, v: float) -> None:
        self.__statestack[-1]["line_width"] = v

    @property
    def text_mode(self) -> TextMode:
        if TYPE_CHECKING:
            assert isinstance(self.__statestack[-1]["text_mode"], TextMode)
        return self.__statestack[-1]["text_mode"]

    @text_mode.setter
    def text_mode(self, v: TextMode | str | int) -> None:
        self.__statestack[-1]["text_mode"] = TextMode.coerce(v)

    @property
    def char_vpos(self) -> CharVPos:
        """
        Return vertical character position relative to line.
        ([docs](../TextStyling.html#subscript-superscript-and-fractional-numbers))
        """
        if TYPE_CHECKING:
            assert isinstance(self.__statestack[-1]["char_vpos"], CharVPos)
        return self.__statestack[-1]["char_vpos"]

    @char_vpos.setter
    def char_vpos(self, v: CharVPos | str) -> None:
        """
        Set vertical character position relative to line.
        ([docs](../TextStyling.html#subscript-superscript-and-fractional-numbers))
        """
        self.__statestack[-1]["char_vpos"] = CharVPos.coerce(v)

    @property
    def sub_scale(self) -> float:
        """
        Return scale factor for subscript text.
        ([docs](../TextStyling.html#subscript-superscript-and-fractional-numbers))
        """
        if TYPE_CHECKING:
            assert isinstance(self.__statestack[-1]["sub_scale"], float)
        return self.__statestack[-1]["sub_scale"]

    @sub_scale.setter
    def sub_scale(self, v: float) -> None:
        """
        Set scale factor for subscript text.
        ([docs](../TextStyling.html#subscript-superscript-and-fractional-numbers))
        """
        self.__statestack[-1]["sub_scale"] = float(v)

    @property
    def sup_scale(self) -> float:
        """
        Return scale factor for superscript text.
        ([docs](../TextStyling.html#subscript-superscript-and-fractional-numbers))
        """
        if TYPE_CHECKING:
            assert isinstance(self.__statestack[-1]["sup_scale"], float)
        return self.__statestack[-1]["sup_scale"]

    @sup_scale.setter
    def sup_scale(self, v: float) -> None:
        """
        Set scale factor for superscript text.
        ([docs](../TextStyling.html#subscript-superscript-and-fractional-numbers))
        """
        self.__statestack[-1]["sup_scale"] = float(v)

    @property
    def nom_scale(self) -> float:
        """
        Return scale factor for nominator text.
        ([docs](../TextStyling.html#subscript-superscript-and-fractional-numbers))
        """
        if TYPE_CHECKING:
            assert isinstance(self.__statestack[-1]["nom_scale"], float)
        return self.__statestack[-1]["nom_scale"]

    @nom_scale.setter
    def nom_scale(self, v: float) -> None:
        """
        Set scale factor for nominator text.
        ([docs](../TextStyling.html#subscript-superscript-and-fractional-numbers))
        """
        self.__statestack[-1]["nom_scale"] = float(v)

    @property
    def denom_scale(self) -> float:
        """
        Return scale factor for denominator text.
        ([docs](../TextStyling.html#subscript-superscript-and-fractional-numbers))
        """
        if TYPE_CHECKING:
            assert isinstance(self.__statestack[-1]["denom_scale"], float)
        return self.__statestack[-1]["denom_scale"]

    @denom_scale.setter
    def denom_scale(self, v: float) -> None:
        """
        Set scale factor for denominator text.
        ([docs](../TextStyling.html#subscript-superscript-and-fractional-numbers))
        """
        self.__statestack[-1]["denom_scale"] = float(v)

    @property
    def sub_lift(self) -> float:
        """
        Return lift factor for subscript text.
        ([docs](../TextStyling.html#subscript-superscript-and-fractional-numbers))
        """
        if TYPE_CHECKING:
            assert isinstance(self.__statestack[-1]["sub_lift"], float)
        return self.__statestack[-1]["sub_lift"]

    @sub_lift.setter
    def sub_lift(self, v: float) -> None:
        """
        Set lift factor for subscript text.
        ([docs](../TextStyling.html#subscript-superscript-and-fractional-numbers))
        """
        self.__statestack[-1]["sub_lift"] = float(v)

    @property
    def sup_lift(self) -> float:
        """
        Return lift factor for superscript text.
        ([docs](../TextStyling.html#subscript-superscript-and-fractional-numbers))
        """
        if TYPE_CHECKING:
            assert isinstance(self.__statestack[-1]["sup_lift"], float)
        return self.__statestack[-1]["sup_lift"]

    @sup_lift.setter
    def sup_lift(self, v: float) -> None:
        """
        Set lift factor for superscript text.
        ([docs](../TextStyling.html#subscript-superscript-and-fractional-numbers))
        """
        self.__statestack[-1]["sup_lift"] = float(v)

    @property
    def nom_lift(self) -> float:
        """
        Return lift factor for nominator text.
        ([docs](../TextStyling.html#subscript-superscript-and-fractional-numbers))
        """
        if TYPE_CHECKING:
            assert isinstance(self.__statestack[-1]["nom_lift"], float)
        return self.__statestack[-1]["nom_lift"]

    @nom_lift.setter
    def nom_lift(self, v: float) -> None:
        """
        Set lift factor for nominator text.
        ([docs](../TextStyling.html#subscript-superscript-and-fractional-numbers))
        """
        self.__statestack[-1]["nom_lift"] = float(v)

    @property
    def denom_lift(self) -> float:
        """
        Return lift factor for denominator text.
        ([docs](../TextStyling.html#subscript-superscript-and-fractional-numbers))
        """
        if TYPE_CHECKING:
            assert isinstance(self.__statestack[-1]["denom_lift"], float)
        return self.__statestack[-1]["denom_lift"]

    @denom_lift.setter
    def denom_lift(self, v: float) -> None:
        """
        Set lift factor for denominator text.
        ([docs](../TextStyling.html#subscript-superscript-and-fractional-numbers))
        """
        self.__statestack[-1]["denom_lift"] = float(v)

    @property
    def text_shaping(self) -> Optional[dict[str, Any]]:
        if TYPE_CHECKING:
            assert isinstance(self.__statestack[-1]["text_shaping"], dict)
        return self.__statestack[-1][
            "text_shaping"
        ]  # pyright: ignore[reportUnknownVariableType]

    @text_shaping.setter
    def text_shaping(self, v: Optional[dict[str, Any]]) -> None:
        self.__statestack[-1]["text_shaping"] = v

    def font_face(self) -> FontFace:
        """
        Return a `fpdf.fonts.FontFace` instance
        representing a subset of properties of this GraphicsState.
        """
        return FontFace(
            family=self.font_family,
            emphasis=TextEmphasis.coerce(self.font_style),
            size_pt=self.font_size_pt,
            color=(
                self.text_color if self.text_color != self.DEFAULT_TEXT_COLOR else None
            ),
            fill_color=(
                self.fill_color if self.fill_color != self.DEFAULT_FILL_COLOR else None
            ),
        )


__pdoc__ = {
    "GraphicsStateMixin._push_local_stack": True,
    "GraphicsStateMixin._pop_local_stack": True,
    "GraphicsStateMixin._get_current_graphics_state": True,
    "GraphicsStateMixin._is_current_graphics_state_nested": True,
}
