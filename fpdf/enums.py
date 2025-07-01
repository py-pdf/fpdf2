import abc
from dataclasses import dataclass
from enum import Enum, Flag, IntEnum, IntFlag
from sys import intern
from typing import Optional, Tuple, Union

from .syntax import Name, wrap_in_local_context


class SignatureFlag(IntEnum):
    SIGNATURES_EXIST = 1
    "If set, the document contains at least one signature field."
    APPEND_ONLY = 2
    """
    If set, the document contains signatures that may be invalidated
    if the file is saved (written) in a way that alters its previous contents,
    as opposed to an incremental update.
    """


class CoerciveEnum(Enum):
    "An enumeration that provides a helper to coerce strings into enumeration members."

    @classmethod
    def coerce(cls, value, case_sensitive=False):
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
                return cls[value] if case_sensitive else cls[value.upper()]
            except KeyError:
                pass

            raise ValueError(f"{value} is not a valid {cls.__name__}")

        raise TypeError(f"{value} cannot be converted to a {cls.__name__}")


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


class CoerciveIntFlag(IntFlag):
    """
    Enumerated constants that can be combined using the bitwise operators,
    with a helper to coerce strings and integers into enumeration members.
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
                pass
            try:
                flags = cls[value[0].upper()]
                for char in value[1:]:
                    flags = flags | cls[char.upper()]
                return flags
            except KeyError:
                raise ValueError(f"{value} is not a valid {cls.__name__}") from None

        if isinstance(value, int):
            return cls(value)

        raise TypeError(f"{value} cannot convert to a {cls.__name__}")


class WrapMode(CoerciveEnum):
    "Defines how to break and wrap lines in multi-line text."

    WORD = intern("WORD")
    "Wrap by word"

    CHAR = intern("CHAR")
    "Wrap by character"


class CharVPos(CoerciveEnum):
    "Defines the vertical position of text relative to the line."

    SUP = intern("SUP")
    "Superscript"

    SUB = intern("SUB")
    "Subscript"

    NOM = intern("NOM")
    "Nominator of a fraction"

    DENOM = intern("DENOM")
    "Denominator of a fraction"

    LINE = intern("LINE")
    "Default line position"


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

    # pylint: disable=arguments-differ
    @classmethod
    def coerce(cls, value):
        if value == "":
            return cls.L
        if isinstance(value, str):
            value = value.upper()
        return super(cls, cls).coerce(value)


class VAlign(CoerciveEnum):
    """Defines how to vertically render text in a cell.
    Default value is MIDDLE"""

    M = intern("MIDDLE")
    "Center text vertically"

    T = intern("TOP")
    "Place text at the top of the cell, but obey the cells padding"

    B = intern("BOTTOM")
    "Place text at the bottom of the cell, but obey the cells padding"

    # pylint: disable=arguments-differ
    @classmethod
    def coerce(cls, value):
        if value == "":
            return cls.M
        return super(cls, cls).coerce(value)


class TextEmphasis(CoerciveIntFlag):
    """
    Indicates use of bold / italics / underline.

    This enum values can be combined with & and | operators:
        style = B | I
    """

    NONE = 0
    "No emphasis"

    B = 1
    "Bold"

    I = 2
    "Italics"

    U = 4
    "Underline"

    S = 8
    "Strikethrough"

    @property
    def style(self):
        return "".join(
            name for name, value in self.__class__.__members__.items() if value & self
        )

    def add(self, value: "TextEmphasis"):
        return self | value

    def remove(self, value: "TextEmphasis"):
        return TextEmphasis.coerce(
            "".join(s for s in self.style if s not in value.style)
        )

    @classmethod
    def coerce(cls, value):
        if isinstance(value, str):
            if value == "":
                return cls.NONE
            if value.upper() == "BOLD":
                return cls.B
            if value.upper() == "ITALICS":
                return cls.I
            if value.upper() == "UNDERLINE":
                return cls.U
            if value.upper() == "STRIKETHROUGH":
                return cls.S
        return super(cls, cls).coerce(value)


class MethodReturnValue(CoerciveIntFlag):
    """
    Defines the return value(s) of a FPDF content-rendering method.

    This enum values can be combined with & and | operators:
        PAGE_BREAK | LINES
    """

    PAGE_BREAK = 1
    "The method will return a boolean indicating if a page break occurred"

    LINES = 2
    "The method will return a multi-lines array of strings, after performing word-wrapping"

    HEIGHT = 4
    "The method will return how much vertical space was used"


class CellBordersLayout(CoerciveIntFlag):
    """Defines how to render cell borders in table

    The integer value of `border` determines which borders are applied. Below are some common examples:

    - border=1 (LEFT): Only the left border is enabled.
    - border=3 (LEFT | RIGHT): Both the left and right borders are enabled.
    - border=5 (LEFT | TOP): The left and top borders are enabled.
    - border=12 (TOP | BOTTOM): The top and bottom borders are enabled.
    - border=15 (ALL): All borders (left, right, top, bottom) are enabled.
    - border=16 (INHERIT): Inherit the border settings from the parent element.

    Using `border=3` will combine LEFT and RIGHT borders, as it represents the
    bitwise OR of `LEFT (1)` and `RIGHT (2)`.
    """

    NONE = 0
    "Draw no border on any side of cell"

    LEFT = 1
    "Draw border on the left side of the cell"

    RIGHT = 2
    "Draw border on the right side of the cell"

    TOP = 4
    "Draw border on the top side of the cell"

    BOTTOM = 8
    "Draw border on the bottom side of the cell"

    ALL = LEFT | RIGHT | TOP | BOTTOM
    "Draw border on all side of the cell"

    INHERIT = 16
    "Inherits the border layout from the table borders layout"

    @classmethod
    def coerce(cls, value):
        if isinstance(value, int) and value > 16:
            raise ValueError("INHERIT cannot be combined with other values")
        return super().coerce(value)

    def __and__(self, value):
        value = super().__and__(value)
        if value > 16:
            raise ValueError("INHERIT cannot be combined with other values")
        return value

    def __or__(self, value):
        value = super().__or__(value)
        if value > 16:
            raise ValueError("INHERIT cannot be combined with other values")
        return value

    def __str__(self):
        border_str = []
        if self & CellBordersLayout.LEFT:
            border_str.append("L")
        if self & CellBordersLayout.RIGHT:
            border_str.append("R")
        if self & CellBordersLayout.TOP:
            border_str.append("T")
        if self & CellBordersLayout.BOTTOM:
            border_str.append("B")
        return "".join(border_str) if border_str else "NONE"


@dataclass
class TableBorderStyle:
    """A helper class for drawing one border of a table

    Attributes:
        thickness: The thickness of the border. If None use default. If <= 0 don't draw the border.
        color: The color of the border. If None use default.
    """

    thickness: Optional[float] = None
    color: Union[int, Tuple[int, int, int]] = None
    dash: Optional[float] = None
    gap: float = 0.0
    phase: float = 0.0

    @staticmethod
    def from_bool(should_draw):
        """
        From boolean or TableBorderStyle input, convert to definite TableBorderStyle class object
        """
        if isinstance(should_draw, TableBorderStyle):
            return should_draw  # don't change specified TableBorderStyle
        if should_draw:
            return TableBorderStyle()  # keep default stroke
        return TableBorderStyle(thickness=0.0)  # don't draw the border

    def _changes_thickness(self, pdf):
        """Return True if this style changes the thickness of the draw command, False otherwise"""
        return (
            self.thickness is not None
            and self.thickness > 0.0
            and self.thickness != pdf.line_width
        )

    def _changes_color(self, pdf):
        """Return True if this style changes the color of the draw command, False otherwise"""
        return self.color is not None and self.color != pdf.draw_color

    @property
    def dash_dict(self):
        """Return dict object specifying dash in the same format as the pdf object"""
        return {"dash": self.dash, "gap": self.gap, "phase": self.phase}

    def _changes_dash(self, pdf):
        """Return True if this style changes the dash of the draw command, False otherwise"""
        return self.dash is not None and self.dash_dict != pdf.dash_pattern

    def changes_stroke(self, pdf):
        """Return True if this style changes the any aspect of the draw command, False otherwise"""
        return self.should_render() and (
            self._changes_color(pdf)
            or self._changes_thickness(pdf)
            or self._changes_dash(pdf)
        )

    def should_render(self):
        """Return True if this style produces a visible stroke, False otherwise"""
        return self.thickness is None or self.thickness > 0.0

    def _get_change_thickness_command(self, scale, pdf=None):
        """Return list with string for the draw command to change thickness (empty if no change)"""
        thickness = self.thickness if pdf is None else pdf.line_width
        return [] if thickness is None else [f"{thickness * scale:.2f} w"]

    def _get_change_line_color_command(self, pdf=None):
        """Return list with string for the draw command to change color (empty if no change)"""
        # pylint: disable=import-outside-toplevel,cyclic-import
        from .drawing import convert_to_device_color

        if pdf is None:
            color = self.color
        else:
            color = pdf.draw_color
        return (
            []
            if color is None
            else [convert_to_device_color(color).serialize().upper()]
        )

    def _get_change_dash_command(self, scale, pdf=None):
        """Return list with string for the draw command to change dash (empty if no change)"""
        dash_dict = self.dash_dict if pdf is None else pdf.dash_pattern
        dash, gap, phase = dash_dict["dash"], dash_dict["gap"], dash_dict["phase"]
        if dash is None:
            return []
        if dash <= 0:
            return ["[] 0 d"]
        if gap <= 0:
            return [f"[{dash * scale:.3f}] {phase * scale:.3f} d"]
        return [f"[{dash * scale:.3f} {gap * scale:.3f}] {phase * scale:.3f} d"]

    def get_change_stroke_commands(self, scale):
        """Return list of strings for the draw command to change stroke (empty if no change)"""
        return (
            self._get_change_dash_command(scale)
            + self._get_change_line_color_command()
            + self._get_change_thickness_command(scale)
        )

    @staticmethod
    def get_line_command(x1, y1, x2, y2):
        """Return list with string for the command to draw a line at the specified endpoints"""
        return [f"{x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S"]

    def get_draw_commands(self, pdf, x1, y1, x2, y2):
        """
        Get draw commands for this section of a cell border. x and y are presumed to be already
        shifted and scaled.
        """
        if not self.should_render():
            return []

        if self.changes_stroke(pdf):
            draw_commands = self.get_change_stroke_commands(
                scale=pdf.k
            ) + self.get_line_command(x1, y1, x2, y2)
            # wrap in local context to prevent stroke changes from affecting later rendering
            return wrap_in_local_context(draw_commands)
        return self.get_line_command(x1, y1, x2, y2)


@dataclass
class TableCellStyle:
    """A helper class for drawing all the borders of one cell in a table

    Attributes:
        left: bool or TableBorderStyle specifying the style of the cell's left border
        bottom: bool or TableBorderStyle specifying the style of the cell's bottom border
        right: bool or TableBorderStyle specifying the style of the cell's right border
        top: bool or TableBorderStyle specifying the style of the cell's top border
    """

    left: Union[bool, TableBorderStyle] = False
    bottom: Union[bool, TableBorderStyle] = False
    right: Union[bool, TableBorderStyle] = False
    top: Union[bool, TableBorderStyle] = False

    def _get_common_border_style(self):
        """Return bool or TableBorderStyle if all borders have the same style, otherwise None"""
        if all(
            isinstance(border, bool)
            for border in [self.left, self.bottom, self.right, self.top]
        ):
            if all(border for border in [self.left, self.bottom, self.right, self.top]):
                return True
            if all(
                not border for border in [self.left, self.bottom, self.right, self.top]
            ):
                return False
        elif all(
            isinstance(border, TableBorderStyle)
            for border in [self.left, self.bottom, self.right, self.top]
        ):
            common = self.left
            if all(border == common for border in [self.bottom, self.right, self.top]):
                return common
        return None

    @staticmethod
    def get_change_fill_color_command(color):
        """Return list with string for command to change device color (empty list if no color)"""
        # pylint: disable=import-outside-toplevel,cyclic-import
        from .drawing import convert_to_device_color

        return (
            []
            if color is None
            else [convert_to_device_color(color).serialize().lower()]
        )

    def get_draw_commands(self, pdf, x1, y1, x2, y2, fill_color=None):
        """
        Get list of primitive commands to draw the cell border for this cell, and fill it with the
        given fill color.
        """
        # y top to bottom instead of bottom to top
        y1 = pdf.h - y1
        y2 = pdf.h - y2
        # scale coordinates and thickness
        scale = pdf.k
        x1 *= scale
        y1 *= scale
        x2 *= scale
        y2 *= scale

        common_border_style = self._get_common_border_style()
        draw_commands, needs_wrap = (
            self._draw_when_no_common_style(x1, y1, x2, y2, pdf, fill_color)
            if common_border_style is None
            else (
                self._draw_with_no_border(x1, y1, x2, y2, pdf, fill_color)
                if common_border_style is False
                else self._draw_all_borders_the_same(
                    x1, y1, x2, y2, pdf, fill_color, scale, common_border_style
                )
            )
        )

        if needs_wrap:
            draw_commands = wrap_in_local_context(draw_commands)

        return draw_commands

    def _draw_when_no_common_style(self, x1, y1, x2, y2, pdf, fill_color):
        """Get draw commands for case when some of the borders have different styles"""
        needs_wrap = False
        draw_commands = []
        if fill_color is not None:
            # draw fill with no box
            if fill_color != pdf.fill_color:
                needs_wrap = True
                draw_commands.extend(self.get_change_fill_color_command(fill_color))
            draw_commands.append(f"{x1:.2f} {y2:.2f} {x2 - x1:.2f} {y1 - y2:.2f} re f")
        # draw the individual borders
        draw_commands.extend(
            TableBorderStyle.from_bool(self.left).get_draw_commands(pdf, x1, y2, x1, y1)
            + TableBorderStyle.from_bool(self.bottom).get_draw_commands(
                pdf, x1, y2, x2, y2
            )
            + TableBorderStyle.from_bool(self.right).get_draw_commands(
                pdf, x2, y2, x2, y1
            )
            + TableBorderStyle.from_bool(self.top).get_draw_commands(
                pdf, x1, y1, x2, y1
            )
        )
        return draw_commands, needs_wrap

    def _draw_with_no_border(self, x1, y1, x2, y2, pdf, fill_color):
        """Get draw commands for case when all of the borders are off / not drawn"""
        needs_wrap = False
        draw_commands = []
        if fill_color is not None:
            # draw fill with no box
            if fill_color != pdf.fill_color:
                needs_wrap = True
                draw_commands.extend(self.get_change_fill_color_command(fill_color))
            draw_commands.append(f"{x1:.2f} {y2:.2f} {x2 - x1:.2f} {y1 - y2:.2f} re f")
        return draw_commands, needs_wrap

    def _draw_all_borders_the_same(
        self, x1, y1, x2, y2, pdf, fill_color, scale, common_border_style
    ):
        """Get draw commands for case when all the borders have the same style"""
        needs_wrap = False
        draw_commands = []
        # all borders are the same
        if isinstance(
            common_border_style, TableBorderStyle
        ) and common_border_style.changes_stroke(pdf):
            # the border styles aren't default, so
            draw_commands.extend(common_border_style.get_change_stroke_commands(scale))
            needs_wrap = True
        if fill_color is not None:
            # draw filled rectangle
            if fill_color != pdf.fill_color:
                needs_wrap = True
                draw_commands.extend(self.get_change_fill_color_command(fill_color))
            draw_commands.append(f"{x1:.2f} {y2:.2f} {x2 - x1:.2f} {y1 - y2:.2f} re B")
        else:
            # draw empty rectangle
            draw_commands.append(f"{x1:.2f} {y2:.2f} {x2 - x1:.2f} {y1 - y2:.2f} re S")
        return draw_commands, needs_wrap

    def override_cell_border(self, cell_border: CellBordersLayout):
        """Allow override by CellBordersLayout mechanism"""
        return (
            self
            if cell_border == CellBordersLayout.INHERIT
            else TableCellStyle(  # translate cell_border into equivalent TableCellStyle
                left=bool(cell_border & CellBordersLayout.LEFT),
                bottom=bool(cell_border & CellBordersLayout.BOTTOM),
                right=bool(cell_border & CellBordersLayout.RIGHT),
                top=bool(cell_border & CellBordersLayout.TOP),
            )
        )

    def draw_cell_border(self, pdf, x1, y1, x2, y2, fill_color=None):
        """
        Draw the cell border for this cell, and fill it with the given fill color.
        """
        pdf._out(  # pylint: disable=protected-access
            " ".join(self.get_draw_commands(pdf, x1, y1, x2, y2, fill_color=fill_color))
        )


class TableBordersLayout(abc.ABC):
    """
    Customizable class for setting the drawing style of cell borders for the whole table.
    cell_style_getter is an abstract method that derived classes must implement. All current classes
    do not use self, but it is available in case a very complicated derived class needs to refer to
    stored internal data.

    Standard TableBordersLayouts are available as static members of this class

    Attributes:
        cell_style_getter: a callable that takes row_num, column_num,
            num_heading_rows, num_rows, num_columns; and returns the drawing style of
            the cell border (as a TableCellStyle object)
        ALL: static TableBordersLayout that draws all table cells borders
        NONE: static TableBordersLayout that draws no table cells borders
        INTERNAL: static TableBordersLayout that draws only internal horizontal & vertical borders
        MINIMAL: static TableBordersLayout that draws only the top horizontal border, below the
            headings, and internal vertical borders
        HORIZONTAL_LINES: static TableBordersLayout that draws only horizontal lines
        NO_HORIZONTAL_LINES: static TableBordersLayout that draws all cells border except interior
            horizontal lines after the headings
        SINGLE_TOP_LINE: static TableBordersLayout that draws only the top horizontal border, below
            the headings
    """

    @abc.abstractmethod
    def cell_style_getter(
        self,
        row_idx,
        col_idx,
        col_pos,
        num_heading_rows,
        num_rows,
        num_col_idx,
        num_col_pos,
    ) -> TableCellStyle:
        """Specify the desired TableCellStyle for the given position in the table

        Args:
            row_idx: the 0-based index of the row in the table
            col_idx: the 0-based logical index of the cell in the row. If colspan > 1, this indexes
                into non-null cells. e.g. if there are two cells with colspan = 3, then col_idx will
                be 0 or 1
            col_pos: the 0-based physical position of the cell in the row. If colspan > 1, this
                indexes into all cells including null ones. e.g. e.g. if there are two cells with
                colspan = 3, then col_pos will be 0 or 3
            num_heading_rows: the number of rows in the table heading
            num_rows: the total number of rows in the table
            num_col_idx: the number of non-null cells. e.g. if there are two cells with colspan = 3,
                then num_col_idx = 2
            num_col_pos: the full width of the table in physical cells. e.g. if there are two cells
                with colspan = 3, then num_col_pos = 6
        Returns:
            TableCellStyle for the given position in the table
        """
        raise NotImplementedError

    @classmethod
    def coerce(cls, value):
        """
        Attempt to coerce `value` into a member of this class.

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
                coerced_value = getattr(cls, value.upper())
                if isinstance(coerced_value, cls):
                    return coerced_value
            except ValueError:
                pass

        raise ValueError(f"{value} is not a valid {cls.__name__}")


class TableBordersLayoutAll(TableBordersLayout):
    """Class for drawing all cell borders"""

    def cell_style_getter(
        self,
        row_idx,
        col_idx,
        col_pos,
        num_heading_rows,
        num_rows,
        num_col_idx,
        num_col_pos,
    ):
        return TableCellStyle(left=True, bottom=True, right=True, top=True)


# add as static member of base TableBordersLayout class
TableBordersLayout.ALL = TableBordersLayoutAll()


class TableBordersLayoutNone(TableBordersLayout):
    """Class for drawing zero cell borders"""

    def cell_style_getter(
        self,
        row_idx,
        col_idx,
        col_pos,
        num_heading_rows,
        num_rows,
        num_col_idx,
        num_col_pos,
    ):
        return TableCellStyle(left=False, bottom=False, right=False, top=False)


# add as static member of base TableBordersLayout class
TableBordersLayout.NONE = TableBordersLayoutNone()


class TableBordersLayoutInternal(TableBordersLayout):
    """Class to draw only internal horizontal & vertical borders"""

    def cell_style_getter(
        self,
        row_idx,
        col_idx,
        col_pos,
        num_heading_rows,
        num_rows,
        num_col_idx,
        num_col_pos,
    ):
        return TableCellStyle(
            left=col_idx > 0,
            bottom=row_idx < num_rows - 1,
            right=col_idx < num_col_idx - 1,
            top=row_idx > 0,
        )


# add as static member of base TableBordersLayout class
TableBordersLayout.INTERNAL = TableBordersLayoutInternal()


class TableBordersLayoutMinimal(TableBordersLayout):
    """
    Class to draw only the top horizontal border, below the headings, and internal vertical borders
    """

    def cell_style_getter(
        self,
        row_idx,
        col_idx,
        col_pos,
        num_heading_rows,
        num_rows,
        num_col_idx,
        num_col_pos,
    ):
        return TableCellStyle(
            left=col_idx > 0,
            bottom=row_idx < num_heading_rows,
            right=col_idx < num_col_idx - 1,
            top=0 < row_idx <= num_heading_rows,
        )


# add as static member of base TableBordersLayout class
TableBordersLayout.MINIMAL = TableBordersLayoutMinimal()


class TableBordersLayoutHorizontalLines(TableBordersLayout):
    """Class to draw only horizontal lines"""

    def cell_style_getter(
        self,
        row_idx,
        col_idx,
        col_pos,
        num_heading_rows,
        num_rows,
        num_col_idx,
        num_col_pos,
    ):
        return TableCellStyle(
            left=False,
            bottom=row_idx < num_rows - 1,
            right=False,
            top=row_idx > 0,
        )


# add as static member of base TableBordersLayout class
TableBordersLayout.HORIZONTAL_LINES = TableBordersLayoutHorizontalLines()


class TableBordersLayoutNoHorizontalLines(TableBordersLayout):
    """Class to draw all cells border except interior horizontal lines after the headings"""

    def cell_style_getter(
        self,
        row_idx,
        col_idx,
        col_pos,
        num_heading_rows,
        num_rows,
        num_col_idx,
        num_col_pos,
    ):
        return TableCellStyle(
            left=True,
            bottom=row_idx == num_rows - 1,
            right=True,
            top=row_idx <= num_heading_rows,
        )


# add as static member of base TableBordersLayout class
TableBordersLayout.NO_HORIZONTAL_LINES = TableBordersLayoutNoHorizontalLines()


class TableBordersLayoutSingleTopLine(TableBordersLayout):
    """Class to draw a single top line"""

    def cell_style_getter(
        self,
        row_idx,
        col_idx,
        col_pos,
        num_heading_rows,
        num_rows,
        num_col_idx,
        num_col_pos,
    ):
        return TableCellStyle(
            left=False, bottom=row_idx <= num_heading_rows - 1, right=False, top=False
        )


# add as static member of base TableBordersLayout class
TableBordersLayout.SINGLE_TOP_LINE = TableBordersLayoutSingleTopLine()


class TableCellFillMode(CoerciveEnum):
    "Defines which table cells to fill"

    NONE = intern("NONE")
    "Fill zero table cell"

    ALL = intern("ALL")
    "Fill all table cells"

    ROWS = intern("ROWS")
    "Fill only table cells in odd rows"

    COLUMNS = intern("COLUMNS")
    "Fill only table cells in odd columns"

    EVEN_ROWS = intern("EVEN_ROWS")
    "Fill only table cells in even rows"

    EVEN_COLUMNS = intern("EVEN_COLUMNS")
    "Fill only table cells in even columns"

    # pylint: disable=arguments-differ
    @classmethod
    def coerce(cls, value):
        "Any class that has a .should_fill_cell() method is considered a valid 'TableCellFillMode' (duck-typing)"
        if callable(getattr(value, "should_fill_cell", None)):
            return value
        return super().coerce(value)

    def should_fill_cell(self, i, j):
        if self is self.NONE:
            return False
        if self is self.ALL:
            return True
        if self is self.ROWS:
            return i % 2 == 1
        if self is self.COLUMNS:
            return j % 2 == 1
        if self is self.EVEN_ROWS:
            return i % 2 == 0
        if self is self.EVEN_COLUMNS:
            return j % 2 == 0
        raise NotImplementedError


class TableSpan(CoerciveEnum):
    ROW = intern("ROW")
    "Mark this cell as a continuation of the previous row"

    COL = intern("COL")
    "Mark this cell as a continuation of the previous column"


class TableHeadingsDisplay(CoerciveIntEnum):
    "Defines how the table headings should be displayed"

    NONE = 0
    "0: Only render the table headings at the beginning of the table"

    ON_TOP_OF_EVERY_PAGE = 1
    "1: When a page break occurs, repeat the table headings at the top of every table fragment"


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

    # pylint: disable=arguments-differ
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


class Angle(CoerciveIntEnum):
    "Direction values used for mirror transformations specifying the angle of mirror line"

    NORTH = 90
    EAST = 0
    SOUTH = 270
    WEST = 180
    NORTHEAST = 45
    SOUTHEAST = 315
    SOUTHWEST = 225
    NORTHWEST = 135


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
    "An enumeration of the named standard named blend functions supported by PDF."

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


class FileAttachmentAnnotationName(CoerciveEnum):
    "The name of an icon that shall be used in displaying the annotation"

    PUSH_PIN = Name("PushPin")
    GRAPH_PUSH_PIN = Name("GraphPushPin")
    PAPERCLIP_TAG = Name("PaperclipTag")


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
    "An enumeration of the PDF drawing directives that define a path as a clipping path."

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
    "An enumeration of the graphics state parameter dictionary keys."

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


class FontDescriptorFlags(Flag):
    """An enumeration of the flags for the unsigned 32-bit integer entry in the font descriptor specifying various
    characteristics of the font. Bit positions are numbered from 1 (low-order) to 32 (high-order).
    """

    FIXED_PITCH = 0x0000001
    """
    "All glyphs have the same width (as opposed to proportional or
    variable-pitch fonts, which have different widths."
    """

    SYMBOLIC = 0x0000004
    """
    "Font contains glyphs outside the Adobe standard Latin character set.
    This flag and the Nonsymbolic flag shall not both be set or both be clear."
    """

    ITALIC = 0x0000040
    """
    "Glyphs have dominant vertical strokes that are slanted."
    """

    FORCE_BOLD = 0x0040000
    """
    "The flag shall determine whether bold glyphs shall be painted with extra pixels even at very
    small text sizes by a conforming reader. If set, features of bold glyphs may be thickened at
    small text sizes."
    """


class AccessPermission(IntFlag):
    "Permission flags will translate as an integer on the encryption dictionary"

    PRINT_LOW_RES = 0b000000000100
    "Print the document"

    MODIFY = 0b000000001000
    "Modify the contents of the document"

    COPY = 0b000000010000
    "Copy or extract text and graphics from the document"

    ANNOTATION = 0b000000100000
    "Add or modify text annotations"

    FILL_FORMS = 0b000100000000
    "Fill in existing interactive form fields"

    COPY_FOR_ACCESSIBILITY = 0b001000000000
    "Extract text and graphics in support of accessibility to users with disabilities"

    ASSEMBLE = 0b010000000000
    "Insert, rotate or delete pages and create bookmarks or thumbnail images"

    PRINT_HIGH_RES = 0b100000000000
    "Print document at the highest resolution"

    @classmethod
    def all(cls):
        "All flags enabled"
        result = 0
        for permission in list(AccessPermission):
            result = result | permission
        return result

    @classmethod
    def none(cls):
        "All flags disabled"
        return 0


class EncryptionMethod(Enum):
    "Algorithm to be used to encrypt the document"

    NO_ENCRYPTION = 0
    RC4 = 1
    AES_128 = 2
    AES_256 = 3


class TextDirection(CoerciveEnum):
    "Text rendering direction for text shaping"

    LTR = intern("LTR")
    "left to right"

    RTL = intern("RTL")
    "right to left"

    TTB = intern("TTB")
    "top to bottom"

    BTT = intern("BTT")
    "bottom to top"


class OutputIntentSubType(CoerciveEnum):
    "Definition for Output Intent Subtypes"

    PDFX = Name("GTS_PDFX")
    "PDF/X-1a which is based upon CMYK processing"

    PDFA = Name("GTS_PDFA1")
    "PDF/A (ISO 19005) standard to produce RGB output"

    ISOPDF = Name("ISO_PDFE1")
    "ISO_PDFE1 PDF/E standards (ISO 24517, all parts)"


class PageLabelStyle(CoerciveEnum):
    "Style of the page label"

    NUMBER = intern("D")
    "decimal arabic numerals"

    UPPER_ROMAN = intern("R")
    "uppercase roman numerals"

    LOWER_ROMAN = intern("r")
    "lowercase roman numerals"

    UPPER_LETTER = intern("A")
    "uppercase letters A to Z, AA to ZZ, AAA to ZZZ and so on"

    LOWER_LETTER = intern("a")
    "uppercase letters a to z, aa to zz, aaa to zzz and so on"

    NONE = None
    "no label"


class Duplex(CoerciveEnum):
    "The paper handling option that shall be used when printing the file from the print dialog."

    SIMPLEX = Name("Simplex")
    "Print single-sided"

    DUPLEX_FLIP_SHORT_EDGE = Name("DuplexFlipShortEdge")
    "Duplex and flip on the short edge of the sheet"

    DUPLEX_FLIP_LONG_EDGE = Name("DuplexFlipLongEdge")
    "Duplex and flip on the long edge of the sheet"


class PageBoundaries(CoerciveEnum):
    ART_BOX = Name("ArtBox")
    BLEED_BOX = Name("BleedBox")
    CROP_BOX = Name("CropBox")
    MEDIA_BOX = Name("MediaBox")
    TRIM_BOX = Name("TrimBox")


class PageOrientation(CoerciveEnum):
    PORTRAIT = intern("P")
    LANDSCAPE = intern("L")

    # pylint: disable=arguments-differ
    @classmethod
    def coerce(cls, value):
        if isinstance(value, str):
            value = value.upper()
        return super(cls, cls).coerce(value)


class PDFResourceType(Enum):
    EXT_G_STATE = intern("ExtGState")
    COLOR_SPACE = intern("ColorSpace")
    PATTERN = intern("Pattern")
    SHADDING = intern("Shading")
    X_OBJECT = intern("XObject")
    FONT = intern("Font")
    PROC_SET = intern("ProcSet")
    PROPERTIES = intern("Properties")
