from dataclasses import dataclass
from numbers import Number
from typing import Optional, Union

from .enums import Align, TableBordersLayout, TableCellFillMode, WrapMode
from .enums import MethodReturnValue
from .errors import FPDFException
from .fonts import CORE_FONTS, FontFace


DEFAULT_HEADINGS_STYLE = FontFace(emphasis="BOLD")


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
            width (number): optional. Sets the table width
            wrapmode (fpdf.enums.WrapMode): "WORD" for word based line wrapping (default),
                "CHAR" for character based line wrapping.
        """
        self._fpdf = fpdf
        self._align = align
        self._borders_layout = TableBordersLayout.coerce(borders_layout)
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
                font_key = family.lower() + emphasis.style
                if font_key not in CORE_FONTS and font_key not in self._fpdf.fonts:
                    # Raising a more explicit error than the one from set_font():
                    raise FPDFException(
                        f"Using font emphasis '{emphasis.style}' in table headings require the corresponding font style to be added using add_font()"
                    )
        if self.rows:
            cols_count = self.rows[0].cols_count
            for i, row in enumerate(self.rows[1:], start=2):
                if row.cols_count != cols_count:
                    raise FPDFException(
                        f"Inconsistent column count detected on row {i}:"
                        f" it has {row.cols_count} columns,"
                        f" whereas the top row has {cols_count}."
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
                    self._render_table_row(0, self._get_row_layout_info(0))
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

    def _render_table_row(self, i, row_layout_info, fill=False, **kwargs):
        row = self.rows[i]
        j = 0
        for cell in row.cells:
            self._render_table_cell(
                i,
                j,
                cell,
                row_height=row_layout_info.height,
                fill=fill,
                **kwargs,
            )
            j += cell.colspan
        self._fpdf.ln(row_layout_info.height)

    def _render_table_cell(
        self,
        i,
        j,
        cell,
        row_height,
        fill=False,
        **kwargs,
    ):
        row = self.rows[i]
        col_width = self._get_col_width(i, j, cell.colspan)
        if j and self._gutter_width:
            self._fpdf.x += self._gutter_width
        img_height = 0
        if cell.img:
            x, y = self._fpdf.x, self._fpdf.y
            img_height = self._fpdf.image(
                cell.img,
                w=col_width,
                h=0 if cell.img_fill_width else row_height,
                keep_aspect_ratio=True,
                link=cell.link,
            ).rendered_height
            self._fpdf.set_xy(x, y)
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
        with self._fpdf.use_font_face(style):
            page_break, cell_height = self._fpdf.multi_cell(
                w=col_width,
                h=row_height,
                txt=cell.text,
                max_line_height=self._line_height,
                border=self.get_cell_border(i, j),
                link=cell.link,
                align=text_align,
                new_x="RIGHT",
                new_y="TOP",
                fill=fill,
                markdown=self._markdown,
                output=MethodReturnValue.PAGE_BREAK | MethodReturnValue.HEIGHT,
                wrapmode=self._wrapmode,
                **kwargs,
            )
        return page_break, max(img_height, cell_height)

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
            if k != j:
                col_width += self._gutter_width
        return col_width

    def _get_row_layout_info(self, i):
        """
        Compute the cells heights & detect page jumps,
        but disable actual rendering by using FPDF._disable_writing()
        """
        row = self.rows[i]
        heights_per_cell = []
        any_page_break = False
        # pylint: disable=protected-access
        with self._fpdf._disable_writing():
            j = 0
            for cell in row.cells:
                page_break, height = self._render_table_cell(
                    i,
                    j,
                    cell,
                    row_height=self._line_height,
                )
                j += cell.colspan
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
        style=None,
        img=None,
        img_fill_width=False,
        colspan=1,
        link=None,
    ):
        """
        Adds a cell to the row.

        Args:
            text (str): string content, can contain several lines.
                In that case, the row height will grow proportionally.
            align (str, fpdf.enums.Align): optional text alignment.
            style (fpdf.fonts.FontFace): optional text style.
            img: optional. Either a string representing a file path to an image,
                an URL to an image, an io.BytesIO, or a instance of `PIL.Image.Image`.
            img_fill_width (bool): optional, defaults to False. Indicates to render the image
                using the full width of the current table column.
            colspan (int): optional number of columns this cell should span.
            link (str, int): optional link, either an URL or an integer returned by `FPDF.add_link`, defining an internal link to a page

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
        cell = Cell(text, align, style, img, img_fill_width, colspan, link)
        self.cells.append(cell)
        return cell


@dataclass(frozen=True)
class Cell:
    "Internal representation of a table cell"
    __slots__ = (  # RAM usage optimization
        "text",
        "align",
        "style",
        "img",
        "img_fill_width",
        "colspan",
        "link",
    )
    text: str
    align: Optional[Union[str, Align]]
    style: Optional[FontFace]
    img: Optional[str]
    img_fill_width: bool
    colspan: int
    link: Optional[Union[str, int]]

    def write(self, text, align=None):
        raise NotImplementedError("Not implemented yet")
