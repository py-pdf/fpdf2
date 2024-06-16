from dataclasses import dataclass, replace
from numbers import Number
from typing import Optional, Union

from .enums import (
    Align,
    MethodReturnValue,
    TableBordersLayout,
    TableCellFillMode,
    TableHeadingsDisplay,
    WrapMode,
    VAlign,
    TableSpan,
)
from .errors import FPDFException
from .fonts import CORE_FONTS, FontFace
from .text_region import TextColumns, Extents
from .util import Padding

DEFAULT_HEADINGS_STYLE = FontFace(emphasis="BOLD")


class Table:
    """
    Object that `fpdf.FPDF.table()` yields, used to build a table in the document.
    Detailed usage documentation: https://py-pdf.github.io/fpdf2/Tables.html
    """

    def __init__(
        self,
        fpdf,
        rows=(),
        *,
        align="CENTER",
        v_align="MIDDLE",
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
        num_heading_rows=1,
        repeat_headings=1,
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
            text_align (str, fpdf.enums.Align, tuple): optional, default to JUSTIFY. Control text alignment inside cells.
            v_align (str, fpdf.enums.AlignV): optional, default to CENTER. Control vertical alignment of cells content
            width (number): optional. Sets the table width
            wrapmode (fpdf.enums.WrapMode): "WORD" for word based line wrapping (default),
                "CHAR" for character based line wrapping.
            padding (number, tuple, Padding): optional. Sets the cell padding. Can be a single number or a sequence of numbers, default:0
                If padding for left and right ends up being non-zero then c_margin is ignored.
            outer_border_width (number): optional. Sets the width of the outer borders of the table.
                Only relevant when borders_layout is ALL or NO_HORIZONTAL_LINES. Otherwise, the border widths are controlled by FPDF.set_line_width()
            num_heading_rows (number): optional. Sets the number of heading rows, default value is 1. If this value is not 1,
                first_row_as_headings needs to be True if num_heading_rows>1 and False if num_heading_rows=0. For backwards compatibility,
                first_row_as_headings is used in case num_heading_rows is 1.
            repeat_headings (fpdf.enums.TableHeadingsDisplay): optional, indicates whether to print table headings on every page, default to 1.
        """
        self._fpdf = fpdf
        self.align = Align.coerce(align)
        if self.align not in (Align.L, Align.C, Align.R):
            raise ValueError(
                "FPDF.table() 'align' parameter must be 'LEFT', 'CENTER', or 'RIGHT', not '{self.align.value}'"
            )
        self.v_align = VAlign.coerce(v_align)
        self._borders_layout = TableBordersLayout.coerce(borders_layout)
        self._outer_border_width = outer_border_width
        self._cell_fill_color = cell_fill_color
        self._cell_fill_mode = TableCellFillMode.coerce(cell_fill_mode)
        self._col_widths = col_widths
        self._first_row_as_headings = first_row_as_headings
        self._gutter_height = gutter_height
        self._gutter_width = gutter_width
        self._headings_style = headings_style
        abs_line_height = 2 * fpdf.font_size if line_height is None else line_height
        self.line_height = abs_line_height / fpdf.font_size
        self._markdown = markdown
        self.text_align = text_align
        self._width = fpdf.epw if width is None else width
        self._wrapmode = wrapmode
        self._num_heading_rows = num_heading_rows
        self._repeat_headings = TableHeadingsDisplay.coerce(repeat_headings)
        self._initial_style = None
        self.rows = []

        if padding is None:
            self.padding = Padding.new(0)
        else:
            self.padding = Padding.new(padding)

        # check table_border_layout and outer_border_width
        if self._borders_layout not in (
            TableBordersLayout.ALL,
            TableBordersLayout.NO_HORIZONTAL_LINES,
        ):
            if outer_border_width is not None:
                raise ValueError(
                    "outer_border_width is only allowed when borders_layout is ALL or NO_HORIZONTAL_LINES"
                )
            self._outer_border_width = 0
        if self._outer_border_width:
            self._outer_border_margin = (
                (gutter_width + outer_border_width / 2),
                (gutter_height + outer_border_width / 2),
            )
        else:
            self._outer_border_margin = (0, 0)

        # check first_row_as_headings for non-default case num_heading_rows != 1
        if self._num_heading_rows != 1:
            if self._num_heading_rows == 0 and self._first_row_as_headings:
                raise ValueError(
                    "first_row_as_headings needs to be False if num_heading_rows == 0"
                )
            if self._num_heading_rows > 1 and not self._first_row_as_headings:
                raise ValueError(
                    "first_row_as_headings needs to be True if num_heading_rows > 0"
                )
        # for backwards compatibility, we respect the value of first_row_as_headings when num_heading_rows==1
        else:
            if not self._first_row_as_headings:
                self._num_heading_rows = 0

        for row in rows:
            self.row(row)

    def row(self, cells=(), style=None):
        "Adds a row to the table. Returns a `Row` object."
        if self._initial_style is None:
            self._initial_style = self._fpdf.font_face()
        cur_row_no = len(self.rows)
        if cur_row_no < self._num_heading_rows:
            style = self._headings_style
        else:
            style = self._fpdf.font_face()
        row = TableRow(self, self._fpdf, cur_row_no, style=style)
        self.rows.append(row)
        for cell in cells:
            if isinstance(cell, dict):
                row.cell(**cell)
            else:
                row.cell(cell)
        return row

    def _data_sanity_checks(self):
        if not self.rows:
            return False
        if self._width > self._fpdf.epw:
            raise ValueError(
                f"Invalid value provided width={self._width}: effective page width is {self._fpdf.epw}"
            )
        if self._num_heading_rows > 0:
            if not self._headings_style:
                raise ValueError(
                    "headings_style must be provided to FPDF.table() if num_heading_rows>1 or first_row_as_headings=True"
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
        cols_count = self.rows[0].cols_count
        if cols_count < 1:
            return False
        for i, row in enumerate(self.rows[1:], start=2):
            if row.cols_count != cols_count:
                raise FPDFException(
                    f"Inconsistent column count detected on row {i}:"
                    f" it has {row.cols_count} columns,"
                    f" whereas the top row has {cols_count}."
                )
        if (self._num_heading_rows > 0) and not self._headings_style:
            raise ValueError(
                "headings_style must be provided to FPDF.table() if num_heading_rows>1 or first_row_as_headings=True"
            )
        return True

    def render(self):
        "This is an internal method called by `fpdf.FPDF.table()` once the table is finished"
        # Starting with some sanity checks:
        if not self._data_sanity_checks():
            return
        if self._num_heading_rows > 0:
            emphasis = self._headings_style.emphasis
            if emphasis is not None:
                family = self._headings_style.family or self._fpdf.font_family
                font_key = family.lower() + emphasis.style
                if font_key not in CORE_FONTS and font_key not in self._fpdf.fonts:
                    # Raising a more explicit error than the one from set_font():
                    raise FPDFException(
                        f"Using font '{family}' with emphasis '{emphasis.style}'"
                        " in table headings require the corresponding font style"
                        " to be added using add_font()"
                    )

        # Defining table global horizontal position:
        if self.align == Align.C:
            self._left = (self._fpdf.w - self._width) / 2
        elif self.align == Align.R:
            self._left = self._fpdf.w - self._fpdf.r_margin - self._width
        elif self._fpdf.x != self._fpdf.l_margin:
            self._left = self._fpdf.x

        # Define horozontal position of all columns.
        self._determine_col_extents()

        # Render the actual cells.
        for i, row in enumerate(self.rows):
            col_n = 0
            row_height = 0
            for j, cell in enumerate(row.cells):
                if j >= len(self.col_extents):
                    raise ValueError(
                        f"Invalid .col_widths specified: missing width for table() column {j + 1} on row {i + 1}"
                    )
                # Preprocess the collected data and determine the required height for each cell.
                if i < self._num_heading_rows:
                    style = self._headings_style
                else:
                    style = cell.style or row.style
                left = self.col_extents[col_n].left
                right = self.col_extents[col_n + cell.colspan - 1].right
                cell.set_cell_extents(Extents(left, right))
                cell_height = cell.collect_cell_lines()
                if cell_height > row_height:
                    row_height = cell_height
                col_n += cell.colspan

            # YYY - handle page breaks

            top = self._fpdf.y
            bottom = self._fpdf.y + row_height

            for j, cell in enumerate(row.cells):

                fill = False
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

                cell.render_cell(top, bottom, fill)
            self._fpdf.y = bottom + self._gutter_height

        self._fpdf.x = self._fpdf.l_margin
        self._fpdf.y = bottom


    def get_cell_borders(self, i, j, cell):
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

        is_rightmost_column = j + cell.colspan == len(self.rows[i].cells)
        rows_count = len(self.rows)
        is_bottom_row = i + cell.rowspan == rows_count
        border = list("LRTB")
        if self._borders_layout == TableBordersLayout.INTERNAL:
            if i == 0:
                border.remove("T")
            if is_bottom_row:
                border.remove("B")
            if j == 0:
                border.remove("L")
            if is_rightmost_column:
                border.remove("R")
        if self._borders_layout == TableBordersLayout.MINIMAL:
            if i == 0 or i > self._num_heading_rows or rows_count == 1:
                border.remove("T")
            if i > self._num_heading_rows - 1:
                border.remove("B")
            if j == 0:
                border.remove("L")
            if is_rightmost_column:
                border.remove("R")
        if self._borders_layout == TableBordersLayout.NO_HORIZONTAL_LINES:
            if i > self._num_heading_rows:
                border.remove("T")
            if not is_bottom_row:
                border.remove("B")
        if self._borders_layout == TableBordersLayout.HORIZONTAL_LINES:
            if rows_count == 1:
                return 0
            border = list("TB")
            if i == 0 and "T" in border:
                border.remove("T")
            elif is_bottom_row:
                border.remove("B")
        if self._borders_layout == TableBordersLayout.SINGLE_TOP_LINE:
            if rows_count == 1:
                return 0
            return "B" if i < self._num_heading_rows else 0
        return "".join(border)


    def _determine_col_extents(self):
        "Precalculate the horizontal extents of each column, including border and margins, excluding gutters."
        cols_count = self.rows[0].cols_count
        if not self._col_widths:
            widths = ((self._width - (cols_count - 1) * self._gutter_width) / cols_count,) * cols_count
        elif isinstance(self._col_widths, Number):
            widths =  (self._col_widths,) * cols_count
        else:
            sum_width = sum(self._col_widths)
            w_mult = self._width / sum_width
            widths = [w * w_mult for w in self._col_widths]
        x = self._left
        self.col_extents = []
        for w in widths:
            self.col_extents.append(Extents(left=x, right=x + w))
            x += w + self._gutter_width


class TableRow:
    "Object that `Table.row()` yields, used to build a row in a table"

    def __init__(self, table: Table, fpdf, row_no, style=None):
        self._table = table
        self._fpdf = fpdf
        self.row_no = row_no
        self.style = style
        self.cells = []

    @property
    def cols_count(self):
        return sum(getattr(cell, "colspan", cell is not None) for cell in self.cells)

    @property
    def column_indices(self):
        columns_count = len(self.cells)
        colidx = 0
        indices = [colidx]
        for jj in range(columns_count - 1):
            colidx += self.cells[jj].colspan
            indices.append(colidx)
        return indices

    @property
    def max_rowspan(self):
        spans = {cell.rowspan for cell in self.cells if cell is not None}
        return max(spans) if len(spans) else 1

    def convert_spans(self, active_rowspans):
        # convert colspans
        prev_col = 0
        cells = []
        for i, cell in enumerate(self.cells):
            if cell is None:
                continue
            if cell == TableSpan.COL:
                prev_cell = cells[prev_col]
                if not isinstance(prev_cell, Cell):
                    raise FPDFException(
                        "Invalid location for TableSpan.COL placeholder entry"
                    )
                cells[prev_col] = replace(prev_cell, colspan=prev_cell.colspan + 1)
                cells.append(None)  # processed
            else:
                cells.append(cell)
                prev_col = i
                if isinstance(cell, Cell) and cell.colspan > 1:  # expand any colspans
                    cells.extend([None] * (cell.colspan - 1))
        # now we can correctly interpret active_rowspans
        remaining_rowspans = {}
        for k, v in active_rowspans.items():
            cells.insert(k, None)
            if v > 1:
                remaining_rowspans[k] = v - 1
        # accumulate any rowspans
        reverse_rowspans = []
        for i, cell in enumerate(cells):
            if isinstance(cell, Cell) and cell.rowspan > 1:
                for k in range(i, i + cell.colspan):
                    remaining_rowspans[k] = cell.rowspan - 1
            elif cell == TableSpan.ROW:
                reverse_rowspans.append(i)
                cells[i] = None  # processed
        self.cells = cells
        return remaining_rowspans, reverse_rowspans

    def cell(
        self,
        text="",
        align=None,
        v_align=None,
        line_height=None,
        style=None,
        img=None,
        img_fill_width=False,
        link=None,
        colspan=1,
        rowspan=1,
        padding=None,
        print_sh: bool = False,
        wrapmode: WrapMode = WrapMode.WORD,
        skip_leading_spaces: bool = False,
    ):
        """
        Adds a cell to the row.

        Args:
            text (str; optional): string content, can contain several lines. Text with varying formatting can be added
                with the `.write()` method of the instance.
            align (str, fpdf.enums.Align; optional): Text alignment within the cell.
            v_align (str, fpdf.enums.AlignV; optional): Vertical text alignment within the cell.
            style (fpdf.fonts.FontFace; optional): Default text style for the cell. Any properties defined in the
                supplied FontFace will override those defined for the whole row.
            img (str, bytes, io.BytesIO, PIL.Image.Image; optional):
                a path-like object or a the actual data of the image to be inserted into the cell.
                If both `text` and `img` arguments are given, the text will be inserted first.
                Images can also be added with the `.image()` method of the instance.
            img_fill_width (bool; optional): Indicates to render the image using the full width of the current
                table cell. (Default: False)
            colspan (int; optional): Number of columns this cell should span. (Default: 1)
            rowspan (int; optional): Number of rows this cell should span. (Default: 1)
            padding (tuple; optional): padding (left, top, right, bottom) for the cell.
            link (str, int): optional link, either an URL or an integer returned by `FPDF.add_link`, defining
               an internal link to a page. This link will apply only to any `text` or `img` arguments supplied,
               and not to content added with `.write()` or `.image()`.
            print_sh (bool; optional): Treat a soft-hyphen (\\u00ad) as a printable character,
                instead of a line breaking opportunity. (Default: False)
            wrapmode (fpdf.enums.WrapMode; optional): "WORD" for word based line wrapping,
                "CHAR" for character based line wrapping. (Default: "WORD")
            skip_leading_spaces (bool; optional): On each line, any space characters at the
                beginning will be skipped if True. (Default: False)
        """

        if isinstance(text, TableSpan):
            # Special placeholder object, converted to colspan/rowspan during processing
            self.cells.append(text)
            return text

        if not style:
            # pylint: disable=protected-access
            # We capture the current font settings:
            font_face = self._table._fpdf.font_face()
            if font_face not in (self.style, self._table._initial_style):
                style = font_face
        else:
            borders = None

        cell = TableCell(
            self,
            self._table,
            len(self.cells),
            self._fpdf,
            text=text,
            text_align=align if  align else self._table.text_align,
            v_align=v_align if v_align else self._table.v_align,
            line_height=line_height if line_height else self._table.line_height,
            style=style or self.style,
            img=img,
            img_fill_width=img_fill_width,
            link=link,
            colspan=colspan,
            rowspan=rowspan,
            padding=padding,
            print_sh=print_sh,
            wrapmode=wrapmode,
            skip_leading_spaces=skip_leading_spaces,
        )
        self.cells.append(cell)
        return cell

class TableCell(TextColumns):
    "Internal representation of a table cell"
    """
    text: str
    align: Optional[Union[str, Align]]
    v_align: Optional[Union[str, VAlign]]
    style: Optional[FontFace]
    img: Optional[str]
    img_fill_width: bool
    colspan: int
    padding: Optional[Union[int, tuple, type(None)]]
    link: Optional[Union[str, int]]
    """
    def __init__(self,
            row,
            table,
            cell_no,
            *args,
            text=None,
            v_align=None,
            style=None,
            link=None,
            colspan=None,
            rowspan=None,
            padding=None,
            **kwargs):
        self._row = row
        self._table = table
        self.cell_no = cell_no
        self.v_align = v_align
        self.style = style
        self.colspan = colspan
        self.rowspan = rowspan
        self.borders = self._table.get_cell_borders(row.row_no, cell_no, self)
        if padding:
            self.padding = padding
        else:
            self.padding = table.padding
        kwargs["ncols"] = 1
        super().__init__(*args, **kwargs)
        if text:
            cur_page = self.pdf.page
            self.pdf.page = 0
            with self.pdf.use_font_face(row.style if row.style else style):
                self.write(text, link=link)
            self.pdf.page = cur_page

    def set_cell_extents(self, extents):
        self._cols = [extents]

    def get_margins(self):
        left = self.padding.left
        right = self.padding.right
        if not left:
            left = self.pdf.c_margin
        if not right:
            right = self.pdf.c_margin
        return left, right

    def collect_cell_lines(self):
        self._text_lines = self.collect_lines()
        self.text_height = sum(l.line.height for l in self._text_lines)
        tb_border_w = 0
        for c in "TB":
            if self.borders and (self.borders == 1 or c in self.borders):
                tb_border_w += self.pdf.line_width
        return self.text_height + self.padding.top + self.padding.bottom + tb_border_w / 2

    def render_cell(self, cell_top, cell_bottom, fill):
        top = cell_top + self.padding.top
        bottom = cell_bottom - self.padding.bottom
        extents = self._cols[0]
        #print(self.style.fill_color, fill)
        draw_box_borders(
            self.pdf,
            extents.left,
            top,
            extents.right,
            bottom,
            border=self.borders,
            fill_color=self.style.fill_color if fill else None,
        )
        fillable_height = bottom - top
        if fillable_height > self.text_height:
            if self.v_align == VAlign.B:
                top += fillable_height - self.text_height
            elif self.v_align == VAlign.M:
                top += (fillable_height - self.text_height) / 2.0
        # YYY - Images tend to slightly overlap with the border lines.
        # YYY   It looks like images are not placed quite exactly where we expect them to be.
        # YYY   Are we taking the size of the image pixels into account correctly?
        #if self.borders and self.borders == 1 or "T" in self.borders:
        #    top += self.pdf.line_width / 2
        self._render_column_lines(self._text_lines, top, bottom)


@dataclass(frozen=True)
class RowLayoutInfo:
    height: float
    # accumulated rowspans to take in account when considering page breaks:
    pagebreak_height: float
    # heights of every cell in the row:
    rendered_heights: dict
    merged_heights: list


@dataclass(frozen=True)
class RowSpanLayoutInfo:
    column: int
    start: int
    length: int
    contents_height: float

    def row_range(self):
        return range(self.start, self.start + self.length)


def draw_box_borders(pdf, x1, y1, x2, y2, border, fill_color=None):
    """Draws a box using the provided style - private helper used by table for drawing the cell and table borders.
    Difference between this and rect() is that border can be defined as "L,R,T,B" to draw only some of the four borders;
    compatible with get_border(i,k)

    See Also: rect()"""

    if fill_color:
        prev_fill_color = pdf.fill_color
        pdf.set_fill_color(fill_color)

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

    if isinstance(border, str) and set(border).issuperset("LTRB"):
        border = 1

    if fill_color:
        op = "B" if border == 1 else "f"
        sl.append(f"{x1:.2f} {y2:.2f} " f"{x2 - x1:.2f} {y1 - y2:.2f} re {op}")
    elif border == 1:
        sl.append(f"{x1:.2f} {y2:.2f} " f"{x2 - x1:.2f} {y1 - y2:.2f} re S")

    if isinstance(border, str):
        if "L" in border:
            sl.append(f"{x1:.2f} {y2:.2f} m " f"{x1:.2f} {y1:.2f} l S")
        if "B" in border:
            sl.append(f"{x1:.2f} {y2:.2f} m " f"{x2:.2f} {y2:.2f} l S")
        if "R" in border:
            sl.append(f"{x2:.2f} {y2:.2f} m " f"{x2:.2f} {y1:.2f} l S")
        if "T" in border:
            sl.append(f"{x1:.2f} {y1:.2f} m " f"{x2:.2f} {y1:.2f} l S")

    s = " ".join(sl)
    pdf._out(s)  # pylint: disable=protected-access

    if fill_color:
        pdf.set_fill_color(prev_fill_color)
