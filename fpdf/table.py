from dataclasses import dataclass
from numbers import Number
from typing import Optional, Union, NamedTuple

try:
    from types import NoneType
except ImportError:
    NoneType = type(None)

from .enums import Align, TableBordersLayout, TableCellFillMode, WrapMode, AlignV
from .enums import MethodReturnValue
from .errors import FPDFException
from .fonts import FontFace

DEFAULT_HEADINGS_STYLE = FontFace(emphasis="BOLD")

class Padding(NamedTuple):
    top: Number = 0
    right: Number = 0
    bottom: Number = 0
    left: Number = 0

def get_padding_tuple(padding: Union[int, float, tuple, list]) -> Padding:
    """Return a 4-tuple of padding values from a single value or a 2, 3 or 4-tuple according to CSS rules"""
    if isinstance(padding, (int, float)):
        return Padding(padding, padding, padding, padding)
    elif len(padding) == 2:
        return Padding(padding[0], padding[1], padding[0], padding[1])
    elif len(padding) == 3:
        return Padding(padding[0], padding[1], padding[2], padding[1])
    elif len(padding) == 4:
        return Padding(*padding)

    raise ValueError(
        f"padding shall be a number or a sequence of 2, 3 or 4 numbers, got {str(padding)}"
    )

def draw_box(pdf, x1, y1, x2, y2, border, fill = None):
    """Draws a box using the provided style - private helper used by table for drawing the cell and table borders.
    Difference bewteen this and rect() is that border can be defined as "L,R,T,B" to draw only some of the four borders; compatible with get_border(i,k)

    See Also: rect()"""

    if fill:
        prev_fill_color = pdf.fill_color
        pdf.set_fill_color(*fill)

    sl = []

    k = pdf.k

    # y top to bottom instead of bottom to top
    y1 = pdf.h - y1
    y2 = pdf.h - y2

    # scale
    x1 *= k
    x2 *= k
    y2 *= k
    y1 *= k

    if fill:
        op = "B" if border == 1 else "f"
        sl.append(f"{x1:.2f} {y2:.2f} " f"{x2 - x1:.2f} {y1 - y2:.2f} re {op}")
    elif border == 1:
        sl.append(f"{x1:.2f} {y2:.2f} " f"{x2 - x1:.2f} {y1 - y2:.2f} re S")

    if isinstance(border, str):
        if "L" in border:
            sl.append(f"{x1:.2f} {y2:.2f} m " f"{x1:.2f} {y1:.2f} l S")
        if "T" in border:
            sl.append(f"{x1:.2f} {y2:.2f} m " f"{x2:.2f} {y2:.2f} l S")
        if "R" in border:
            sl.append(f"{x2:.2f} {y2:.2f} m " f"{x2:.2f} {y1:.2f} l S")
        if "B" in border:
            sl.append(f"{x1:.2f} {y1:.2f} m " f"{x2:.2f} {y1:.2f} l S")

    s = " ".join(sl)
    pdf._out(s)

    if fill:
        pdf.set_fill_color(prev_fill_color)

@dataclass(frozen=True)
class RowLayoutInfo:
    height: float
    triggers_page_jump: bool


class Table:
    """
    Object that `fpdf.FPDF.table()` yields, used to build a table in the document.
    Detailed usage documentation: https://pyfpdf.github.io/fpdf2/Tables.html
    """

    def __init__(
        self,
        fpdf,
        rows=(),
        *,
        align="CENTER",
        v_align="CENTER",
        borders_layout=TableBordersLayout.ALL,
        cell_fill_color=None,
        cell_fill_mode=TableCellFillMode.NONE,
        col_widths=None,
        first_row_as_headings=True,
        gutter_height=0,
        gutter_width=0,
        headings_style=DEFAULT_HEADINGS_STYLE,
        line_height=None,
        markdown=False,
        text_align="JUSTIFY",
        width=None,
        wrapmode=WrapMode.WORD,
        padding=None,
        outer_border_width=None,
    ):
        """
        Args:
            fpdf (fpdf.FPDF): FPDF current instance
            rows: optional. Sequence of rows (iterable) of str to initiate the table cells with text content
            align (str, fpdf.enums.Align): optional, default to CENTER. Sets the table horizontal position relative to the page,
                when it's not using the full page width
            borders_layout (str, fpdf.enums.TableBordersLayout): optional, default to ALL. Control what cell borders are drawn
            cell_fill_color (float, tuple, fpdf.drawing.DeviceGray, fpdf.drawing.DeviceRGB): optional.
                Defines the cells background color
            cell_fill_mode (str, fpdf.enums.TableCellFillMode): optional. Defines which cells are filled with color in the background
            col_widths (float, tuple): optional. Sets column width. Can be a single number or a sequence of numbers
            first_row_as_headings (bool): optional, default to True. If False, the first row of the table
                is not styled differently from the others
            gutter_height (float): optional vertical space between rows
            gutter_width (float): optional horizontal space between columns
            headings_style (fpdf.fonts.FontFace): optional, default to bold.
                Defines the visual style of the top headings row: size, color, emphasis...
            line_height (number): optional. Defines how much vertical space a line of text will occupy
            markdown (bool): optional, default to False. Enable markdown interpretation of cells textual content
            text_align (str, fpdf.enums.Align): optional, default to JUSTIFY. Control text alignment inside cells.
            v_align (str, fpdf.enums.AlignV): optional, default to CENTER. Control vertical alignment of cells content
            width (number): optional. Sets the table width
            wrapmode (fpdf.enums.WrapMode): "WORD" for word based line wrapping (default),
                "CHAR" for character based line wrapping.
            padding (number, tuple): optional. Sets the cell padding. Can be a single number or a sequence of numbers, default: half line height
            outer_border_width (number): optional. Sets the width of the outer borders of the table
        """
        self._fpdf = fpdf
        self._align = align
        self._v_align = AlignV.coerce(v_align)
        self._borders_layout = TableBordersLayout.coerce(borders_layout)
        self._outer_border_width = outer_border_width
        self._cell_fill_color = cell_fill_color
        self._cell_fill_mode = TableCellFillMode.coerce(cell_fill_mode)
        self._col_widths = col_widths
        self._first_row_as_headings = first_row_as_headings
        self._gutter_height = gutter_height
        self._gutter_width = gutter_width
        self._headings_style = headings_style
        self._line_height = 2 * fpdf.font_size if line_height is None else line_height
        self._markdown = markdown
        self._text_align = text_align
        self._width = fpdf.epw if width is None else width
        self._wrapmode = wrapmode
        self.rows = []


        if padding is None:
            self._padding = get_padding_tuple(0)
        else:
            self._padding = get_padding_tuple(padding)

        for row in rows:
            self.row(row)

    def row(self, cells=()):
        "Adds a row to the table. Yields a `Row` object."
        row = Row(self._fpdf)
        self.rows.append(row)
        for cell in cells:
            row.cell(cell)
        return row

    def render(self):
        "This is an internal method called by `fpdf.FPDF.table()` once the table is finished"
        # Starting with some sanity checks:
        if self._width > self._fpdf.epw:
            raise ValueError(
                f"Invalid value provided width={self._width}: effective page width is {self._fpdf.epw}"
            )
        table_align = Align.coerce(self._align)
        if table_align == Align.J:
            raise ValueError(
                "JUSTIFY is an invalid value for FPDF.table() 'align' parameter"
            )
        if self._first_row_as_headings:
            if not self._headings_style:
                raise ValueError(
                    "headings_style must be provided to FPDF.table() if first_row_as_headings=True"
                )
            emphasis = self._headings_style.emphasis
            if emphasis is not None:
                family = self._headings_style.family or self._fpdf.font_family
                font_key = family + emphasis.style
                if (
                    font_key not in self._fpdf.core_fonts
                    and font_key not in self._fpdf.fonts
                ):
                    # Raising a more explicit error than the one from set_font():
                    raise FPDFException(
                        f"Using font emphasis '{emphasis.style}' in table headings require the corresponding font style to be added using add_font()"
                    )
        # Defining table global horizontal position:
        prev_l_margin = self._fpdf.l_margin
        if table_align == Align.C:
            self._fpdf.l_margin = (self._fpdf.w - self._width) / 2
            self._fpdf.x = self._fpdf.l_margin
        elif table_align == Align.R:
            self._fpdf.l_margin = self._fpdf.w - self._fpdf.r_margin - self._width
            self._fpdf.x = self._fpdf.l_margin
        elif self._fpdf.x != self._fpdf.l_margin:
            self._fpdf.l_margin = self._fpdf.x
        # Starting the actual rows & cells rendering:
        for i in range(len(self.rows)):
            row_layout_info = self._get_row_layout_info(i)
            if row_layout_info.triggers_page_jump:
                # pylint: disable=protected-access
                self._fpdf._perform_page_break()
                if self._first_row_as_headings:  # repeat headings on top:
                    self._render_table_row(0)
            elif i and self._gutter_height:
                self._fpdf.y += self._gutter_height
            self._render_table_row(i, row_layout_info)
        # Restoring altered FPDF settings:
        self._fpdf.l_margin = prev_l_margin
        self._fpdf.x = self._fpdf.l_margin

    def get_cell_border(self, i, j):
        """
        Defines which cell borders should be drawn.
        Returns a string containing some or all of the letters L/R/T/B,
        to be passed to `fpdf.FPDF.multi_cell()`.
        Can be overriden to customize this logic
        """
        if self._borders_layout == TableBordersLayout.ALL:
            return 1
        if self._borders_layout == TableBordersLayout.NONE:
            return 0
        columns_count = max(row.cols_count for row in self.rows)
        rows_count = len(self.rows)
        border = list("LRTB")
        if self._borders_layout == TableBordersLayout.INTERNAL:
            if i == 0 and "T" in border:
                border.remove("T")
            if i == rows_count - 1 and "B" in border:
                border.remove("B")
            if j == 0 and "L" in border:
                border.remove("L")
            if j == columns_count - 1 and "R" in border:
                border.remove("R")
        if self._borders_layout == TableBordersLayout.MINIMAL:
            if (i != 1 or rows_count == 1) and "T" in border:
                border.remove("T")
            if i != 0 and "B" in border:
                border.remove("B")
            if j == 0 and "L" in border:
                border.remove("L")
            if j == columns_count - 1 and "R" in border:
                border.remove("R")
        if self._borders_layout == TableBordersLayout.NO_HORIZONTAL_LINES:
            if i not in (0, 1) and "T" in border:
                border.remove("T")
            if i not in (0, rows_count - 1) and "B" in border:
                border.remove("B")
        if self._borders_layout == TableBordersLayout.HORIZONTAL_LINES:
            if rows_count == 1:
                return 0
            border = list("TB")
            if i == 0 and "T" in border:
                border.remove("T")
            if i == rows_count - 1 and "B" in border:
                border.remove("B")
        if self._borders_layout == TableBordersLayout.SINGLE_TOP_LINE:
            if rows_count == 1:
                return 0
            border = list("TB")
            if i != 1 and "T" in border:
                border.remove("T")
            if i != 0 and "B" in border:
                border.remove("B")
        return "".join(border)

    def _render_table_row(self, i, row_layout_info=None, fill=False, **kwargs):
        if not row_layout_info:
            row_layout_info = self._get_row_layout_info(i)
        row = self.rows[i]
        j = 0
        while j < len(row.cells):
            self._render_table_cell(
                i,
                j,
                row_height=self._line_height,
                cell_height=row_layout_info.height,
                fill=fill,
                **kwargs,
            )
            j += row.cells[j].colspan
        self._fpdf.ln(row_layout_info.height)

    def _render_table_cell(
        self,
        i,
        j,
        row_height,        # height of a row of text including line spacing
        fill=False,
        cell_height=None,  # full height of a cell, including padding, used to render borders and images
        **kwargs,
    ):
        # If cell_height is provided then we are rendering a cell
        # If cell_height is not provided then we are only here to figure out the height of the cell
        #
        # So this function is first called without cell_height to figure out the heights of all cells in a row
        # and then called again with cell_height to actually render the cells

        # default values:

        page_break_text = False
        page_break_image = False

        # Get style and cell content:

        row = self.rows[i]
        cell = row.cells[j]
        col_width = self._get_col_width(i, j, cell.colspan)
        img_height = 0

        text_align = cell.align or self._text_align
        if not isinstance(text_align, (Align, str)):
            text_align = text_align[j]
        if i == 0 and self._first_row_as_headings:
            style = self._headings_style
        else:
            style = cell.style or row.style
        if style and style.fill_color:
            fill = True
        elif (
            not fill
            and self._cell_fill_color
            and self._cell_fill_mode != TableCellFillMode.NONE
        ):
            if self._cell_fill_mode == TableCellFillMode.ALL:
                fill = True
            elif self._cell_fill_mode == TableCellFillMode.ROWS:
                fill = bool(i % 2)
            elif self._cell_fill_mode == TableCellFillMode.COLUMNS:
                fill = bool(j % 2)
        if fill and self._cell_fill_color and not (style and style.fill_color):
            style = (
                style.replace(fill_color=self._cell_fill_color)
                if style
                else FontFace(fill_color=self._cell_fill_color)
            )

        padding = get_padding_tuple(cell.padding) if cell.padding else self._padding

        v_align = cell.v_align if cell.v_align else self._v_align

        # place cursor (required for images after images)
        cell_widths = [self._get_col_width(i, jj) for jj in range(j)]
        cell_x = sum(cell_widths)

        self._fpdf.set_x(self._fpdf.l_margin + cell_x + self._gutter_width * j)

        # render cell border and background

        # if cell_height is defined, that means that we already know the size at which the cell will be rendered
        # so we can draw the borders now
        #
        # If cell_height is None then we're still in the phase of calculating the height of the cell meaning that
        # we do not need to set fonts & draw borders yet.
        if cell_height is not None:
            x1 = self._fpdf.x
            y1 = self._fpdf.y
            x2 = x1 + col_width
            y2 = y1 + cell_height

            draw_box(
                self._fpdf,
                x1, y1, x2, y2, border=self.get_cell_border(i, j),
                fill=style.fill_color if fill else None
            )

            # draw outer box if needed
            if self._outer_border_width:

                _remember_linewidth = self._fpdf.line_width
                self._fpdf.set_line_width(self._outer_border_width)

                if i == 0:
                    self._fpdf.line(x1, y1, x2, y1)
                if i== len(self.rows) - 1:
                    self._fpdf.line(x1, y2, x2, y2)
                if j == 0:
                    self._fpdf.line(x1, y1, x1, y2)
                if j == len(row.cells) - 1:
                    self._fpdf.line(x2, y1, x2, y2)

                self._fpdf.set_line_width(_remember_linewidth)


        # render image

        if cell.img:
            x, y = self._fpdf.x, self._fpdf.y

            # if cell_height is None or width is given then call image with h=0
            # calling with h=0 means that the image will be rendered with an auto determined height
            auto_height = cell.img_fill_width or cell_height is None

            # apply padding
            self._fpdf.x += padding.left
            self._fpdf.y += padding.top

            image = self._fpdf.image(
                cell.img,
                w=col_width - padding.left - padding.right,
                h=0 if auto_height else cell_height - padding.top - padding.bottom,
                keep_aspect_ratio=True,
            )

            img_height = image.rendered_height

            if img_height + y > self._fpdf.page_break_trigger:
                page_break_image = True

            self._fpdf.set_xy(x, y)

        # render text

        if cell.text:
            dy = 0
            if cell_height is not None:
                if v_align != AlignV.T:  # For Top we don't need to calculate the dy

                    # TODO: Make this more efficient by not calling multi_cell twice

                    # first dry run to get the actual text height of the cell
                    _, actual_text_height = self._fpdf.multi_cell(
                        w=col_width,
                        h=row_height,
                        txt=cell.text,
                        max_line_height=self._line_height,
                        border=0,
                        align=text_align,
                        new_x="RIGHT",
                        new_y="TOP",
                        fill=False,  # fill is already done above
                        markdown=self._markdown,
                        output=MethodReturnValue.PAGE_BREAK | MethodReturnValue.HEIGHT,
                        wrapmode=self._wrapmode,
                        dry_run=True,
                        padding=padding,
                        **kwargs,
                    )
                    # then calculate the y offset of the text depending on the vertical alignment

                    if v_align == AlignV.C:
                        dy = (cell_height - actual_text_height) / 2
                    elif v_align == AlignV.B:
                        dy = cell_height - actual_text_height

            self._fpdf.y += dy

            with self._fpdf.use_font_face(style):
                page_break_text, cell_height = self._fpdf.multi_cell(
                    w=col_width,
                    h=row_height,
                    txt=cell.text,
                    max_line_height=self._line_height,
                    border=0,
                    align=text_align,
                    new_x="RIGHT",
                    new_y="TOP",
                    fill=False,  # fill is already done above
                    markdown=self._markdown,
                    output=MethodReturnValue.PAGE_BREAK | MethodReturnValue.HEIGHT,
                    wrapmode=self._wrapmode,
                    padding=padding,
                    **kwargs,
                )

            self._fpdf.y -= dy
        else:
            cell_height = 0
        return page_break_text or page_break_image, max(img_height, cell_height)

    def _get_col_width(self, i, j, colspan=1):
        cols_count = self.rows[i].cols_count
        width = self._width - (cols_count - 1) * self._gutter_width
        if not self._col_widths:
            return colspan * (width / cols_count)
        if isinstance(self._col_widths, Number):
            return colspan * self._col_widths
        if j >= len(self._col_widths):
            raise ValueError(
                f"Invalid .col_widths specified: missing width for table() column {j + 1} on row {i + 1}"
            )
        col_width = 0
        for k in range(j, j + colspan):
            col_ratio = self._col_widths[k] / sum(self._col_widths)
            col_width += col_ratio * width
        return col_width

    def _get_row_layout_info(self, i):
        """
        Uses FPDF.offset_rendering() to detect a potential page jump
        and compute the cells heights.
        """
        row = self.rows[i]
        heights_per_cell = []
        any_page_break = False
        # pylint: disable=protected-access
        with self._fpdf._disable_writing():
            for j in range(len(row.cells)):
                page_break, height = self._render_table_cell(
                    i,
                    j,
                    row_height=self._line_height,
                )
                any_page_break = any_page_break or page_break
                heights_per_cell.append(height)
        row_height = (
            max(height for height in heights_per_cell) if heights_per_cell else 0
        )
        return RowLayoutInfo(row_height, any_page_break)


class Row:
    "Object that `Table.row()` yields, used to build a row in a table"

    def __init__(self, fpdf):
        self._fpdf = fpdf
        self.cells = []
        self.style = fpdf.font_face()

    @property
    def cols_count(self):
        return sum(cell.colspan for cell in self.cells)

    def cell(
        self,
        text="",
        align=None,
        v_align=None,
        style=None,
        img=None,
        img_fill_width=False,
        colspan=1,
        padding=None,
    ):
        """
        Adds a cell to the row.

        Args:
            text (str): string content, can contain several lines.
                In that case, the row height will grow proportionally.
            align (str, fpdf.enums.Align): optional text alignment.
            v_align (str, fpdf.enums.AlignV): optional vertical text alignment.
            style (fpdf.fonts.FontFace): optional text style.
            img: optional. Either a string representing a file path to an image,
                an URL to an image, an io.BytesIO, or a instance of `PIL.Image.Image`.
            img_fill_width (bool): optional, defaults to False. Indicates to render the image
                using the full width of the current table column.
            colspan (int): optional number of columns this cell should span.
            padding (tuple): optional padding (left, top, right, bottom) for the cell.
        """
        if text and img:
            raise NotImplementedError(
                # pylint: disable=implicit-str-concat
                "fpdf2 currently does not support inserting text with an image in the same table cell."
                "Pull Requests are welcome to implement this 😊"
            )
        if not style:
            # We capture the current font settings:
            font_face = self._fpdf.font_face()
            if font_face != self.style:
                style = font_face
        cell = Cell(text, align, v_align, style, img, img_fill_width, colspan, padding)
        self.cells.append(cell)
        return cell


@dataclass(frozen=True)
class Cell:
    "Internal representation of a table cell"
    __slots__ = (  # RAM usage optimization
        "text",
        "align",
        "v_align",
        "style",
        "img",
        "img_fill_width",
        "colspan",
        "padding",
    )
    text: str
    align: Optional[Union[str, Align]]
    v_align: Optional[Union[str, AlignV]]
    style: Optional[FontFace]
    img: Optional[str]
    img_fill_width: bool
    colspan: int
    padding: Optional[Union[int, tuple, NoneType]]

    def write(self, text, align=None):
        raise NotImplementedError("Not implemented yet")
