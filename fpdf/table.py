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
    CellBordersLayout,
)
from .errors import FPDFException
from .fonts import CORE_FONTS, FontFace
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
        min_row_height=None,
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
            col_widths (float, tuple): optional. Sets column width. Can be a single number or a sequence of numbers.
                 When `col_widths` is a single number, it is interpreted as a fixed column width in document units.
                 When `col_widths` is provided as an array, the values are considered to be fractions of the full effective page width,
                 meaning that `col_widths=(1, 1, 2)` is strictly equivalent to `col_widths=(25, 25, 50)`.
            first_row_as_headings (bool): optional, default to True. If False, the first row of the table
                is not styled differently from the others
            gutter_height (float): optional vertical space between rows
            gutter_width (float): optional horizontal space between columns
            headings_style (fpdf.fonts.FontFace): optional, default to bold.
                Defines the visual style of the top headings row: size, color, emphasis...
            line_height (number): optional. Defines how much vertical space a line of text will occupy
            markdown (bool): optional, default to False. Enable markdown interpretation of cells textual content
            text_align (str, fpdf.enums.Align, tuple): optional, default to JUSTIFY. Control text alignment inside cells.
            v_align (str, fpdf.enums.VAlign): optional, default to CENTER. Control vertical alignment of cells content
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
        self._table_align = Align.coerce(align)
        self._v_align = VAlign.coerce(v_align)
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
        self._width = width
        self._wrapmode = wrapmode
        self._num_heading_rows = num_heading_rows
        self._repeat_headings = TableHeadingsDisplay.coerce(repeat_headings)
        self._min_row_height = min_row_height
        self._initial_style = None
        self.rows = []

        if padding is None:
            self._padding = Padding.new(0)
        else:
            self._padding = Padding.new(padding)

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
        # _outer_border_margin : vertical spacing around table
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

    def row(self, cells=(), style=None, v_align=None, min_height=None):
        "Adds a row to the table. Returns a `Row` object."
        if self._initial_style is None:
            self._initial_style = self._fpdf.font_face()
        row = Row(self, style=style, v_align=v_align, min_height=min_height)
        self.rows.append(row)
        for cell in cells:
            if isinstance(cell, dict):
                row.cell(**cell)
            else:
                row.cell(cell)
        return row

    def render(self):
        "This is an internal method called by `fpdf.FPDF.table()` once the table is finished"
        # Starting with some sanity checks:
        self._cols_count = max(row.cols_count for row in self.rows) if self.rows else 0
        if self._width is None:
            if self._col_widths and isinstance(self._col_widths, Number):
                self._width = self._cols_count * self._col_widths
            else:
                self._width = self._fpdf.epw
        elif self._col_widths and isinstance(self._col_widths, Number):
            if self._cols_count * self._col_widths != self._width:
                raise ValueError(
                    f"Invalid value provided width={self._width} should be a multiple of col_widths={self._col_widths}"
                )
        if self._width > self._fpdf.epw:
            raise ValueError(
                f"Invalid value provided width={self._width}: effective page width is {self._fpdf.epw}"
            )
        if self._table_align == Align.J:
            raise ValueError(
                "JUSTIFY is an invalid value for FPDF.table() 'align' parameter"
            )
        if self._num_heading_rows > 0:
            if not self._headings_style:
                raise ValueError(
                    "headings_style must be provided to FPDF.table() if num_heading_rows>1 or first_row_as_headings=True"
                )
            emphasis = self._headings_style.emphasis
            if emphasis is not None:
                family = self._headings_style.family or self._fpdf.font_family
                font_key = family.lower() + emphasis.style.replace("U", "")
                if font_key not in CORE_FONTS and font_key not in self._fpdf.fonts:
                    # Raising a more explicit error than the one from set_font():
                    raise FPDFException(
                        f"Using font '{family}' with emphasis '{emphasis.style}'"
                        " in table headings require the corresponding font style"
                        " to be added using add_font()"
                    )

        # Defining table global horizontal position:
        prev_x, prev_y, prev_l_margin = self._fpdf.x, self._fpdf.y, self._fpdf.l_margin
        if self._table_align == Align.C:
            self._fpdf.l_margin = (self._fpdf.w - self._width) / 2
            self._fpdf.x = self._fpdf.l_margin
        elif self._table_align == Align.R:
            self._fpdf.l_margin = self._fpdf.w - self._fpdf.r_margin - self._width
            self._fpdf.x = self._fpdf.l_margin
        elif self._fpdf.x != self._fpdf.l_margin:
            self._fpdf.l_margin = self._fpdf.x

        # Pre-Compute the relative x-positions of the individual columns:
        xx = self._fpdf.l_margin + self._outer_border_margin[0]
        cell_x_positions = [xx]
        if self.rows:
            for i in range(self._cols_count):
                xx += self._get_col_width(0, i)
                xx += self._gutter_width
                cell_x_positions.append(xx)

        # Process any rowspans
        rows_info = list(self._compute_rows_info())

        # actually render the cells
        repeat_headings = (
            self._repeat_headings is TableHeadingsDisplay.ON_TOP_OF_EVERY_PAGE
        )
        self._fpdf.y += self._outer_border_margin[1]
        if len(self.rows) > self._num_heading_rows > 0:
            # We avoid having the heading rows alone on a page - issue #1391
            # pylint: disable=protected-access
            self._fpdf._perform_page_break_if_need_be(
                sum(
                    rows_info[i].pagebreak_height
                    for i in range(self._num_heading_rows + 1)
                )
            )
        for i in range(len(self.rows)):
            pagebreak_height = rows_info[i].pagebreak_height
            # pylint: disable=protected-access
            page_break = self._fpdf._perform_page_break_if_need_be(pagebreak_height)
            if (
                page_break
                and self._fpdf.y + pagebreak_height > self._fpdf.page_break_trigger
            ):
                # Restoring original position on page:
                self._fpdf.x = prev_x
                self._fpdf.y = prev_y
                self._fpdf.l_margin = prev_l_margin
                raise ValueError(
                    f"The row with index {i} is too high and cannot be rendered on a single page"
                )
            if page_break and repeat_headings and i >= self._num_heading_rows:
                # repeat headings on top:
                self._fpdf.y += self._outer_border_margin[1]
                for row_idx in range(self._num_heading_rows):
                    self._render_table_row(
                        row_idx,
                        rows_info[row_idx],
                        cell_x_positions=cell_x_positions,
                    )
            if i > 0:
                self._fpdf.y += self._gutter_height
            self._render_table_row(i, rows_info[i], cell_x_positions)

        # Restoring altered FPDF settings:
        self._fpdf.l_margin = prev_l_margin
        self._fpdf.x = self._fpdf.l_margin

    # pylint: disable=too-many-return-statements
    def get_cell_border(self, i, j, cell):
        """
        Defines which cell borders should be drawn.
        Returns a string containing some or all of the letters L/R/T/B,
        to be passed to `fpdf.FPDF.multi_cell()`.
        Can be overridden to customize this logic
        """

        if cell.border != CellBordersLayout.INHERIT:
            return str(cell.border)

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

    def _render_table_row(self, i, row_layout_info, cell_x_positions, **kwargs):
        row = self.rows[i]
        y = self._fpdf.y  # remember current y position, reset after each cell

        for j, cell in enumerate(row.cells):
            if cell is None:
                continue
            self._render_table_cell(
                i,
                j,
                cell,
                row_height=self._line_height,
                cell_height_info=row_layout_info,
                cell_x_positions=cell_x_positions,
                **kwargs,
            )
            self._fpdf.set_y(y)  # restore y position after each cell

        self._fpdf.ln(row_layout_info.height)

    def _render_table_cell(
        self,
        i,
        j,
        cell,
        row_height,  # height of a row of text including line spacing
        cell_height_info=None,  # full height of a cell, including padding, used to render borders and images
        cell_x_positions=None,  # x-positions of the individual columns, pre-calculated for speed. Only relevant when rendering
        **kwargs,
    ):
        # If cell_height_info is provided then we are rendering a cell
        # If cell_height_info is not provided then we are only here to figure out the height of the cell
        #
        # So this function is first called without cell_height_info to figure out the heights of all cells in a row
        # and then called again with cell_height to actually render the cells

        if cell_height_info is None:
            cell_height = None
            height_query_only = True
        elif cell.rowspan > 1:
            cell_height = cell_height_info.merged_heights[cell.rowspan]
            height_query_only = False
        else:
            cell_height = cell_height_info.height
            height_query_only = False

        page_break_text = False
        page_break_image = False

        # Get style and cell content:

        row = self.rows[i]
        col_width = self._get_col_width(i, j, cell.colspan)
        img_height = 0

        text_align = cell.align or self._text_align
        if not isinstance(text_align, (Align, str)):
            text_align = text_align[j]

        style = self._initial_style
        cell_mode_fill = self._cell_fill_mode.should_fill_cell(i, j)
        if cell_mode_fill and self._cell_fill_color:
            style = style.replace(fill_color=self._cell_fill_color)
        if i < self._num_heading_rows:
            style = FontFace.combine(style, self._headings_style)
        style = FontFace.combine(style, row.style)
        style = FontFace.combine(style, cell.style)

        padding = Padding.new(cell.padding) if cell.padding else self._padding

        v_align = cell.v_align
        if not v_align:
            v_align = row.v_align
        if not v_align:
            v_align = self._v_align

        # We can not rely on the actual x position of the cell. Notably in case of
        # empty cells or cells with an image only the actual x position is incorrect.
        # Instead, we calculate the x position based on the column widths of the previous columns

        # place cursor (required for images after images)

        # not rendering, cell_x_positions is not relevant (and probably not provided):
        if height_query_only:
            cell_x = 0
        else:
            cell_x = cell_x_positions[j]
        self._fpdf.set_x(cell_x)

        # render cell border and background
        # if cell_height is defined, that means that we already know the size at which the cell will be rendered
        # so we can draw the borders now
        #
        # If cell_height is None then we're still in the phase of calculating the height of the cell meaning that
        # we do not need to set fonts & draw borders yet.
        if not height_query_only:
            x1 = self._fpdf.x
            y1 = self._fpdf.y
            x2 = (
                x1 + col_width
            )  # already includes gutter for cells spanning multiple columns
            y2 = y1 + cell_height

            draw_box_borders(
                self._fpdf,
                x1,
                y1,
                x2,
                y2,
                border=self.get_cell_border(i, j, cell),
                fill_color=style.fill_color if style else None,
            )

            # draw outer box if needed:
            if self._outer_border_width:
                _remember_linewidth = self._fpdf.line_width
                self._fpdf.set_line_width(self._outer_border_width)

                # draw the outer box separated by the gutter dimensions
                # the top and bottom borders are one continuous line
                # whereas the left and right borders are segments because of possible pagebreaks
                x1 = self._fpdf.l_margin
                x2 = x1 + self._width
                y1 = y1 - self._outer_border_margin[1]
                y2 = y2 + self._outer_border_margin[1]

                if j == 0:
                    # lhs border
                    self._fpdf.line(x1, y1, x1, y2)
                if j + cell.colspan == self._cols_count:
                    # rhs border
                    self._fpdf.line(x2, y1, x2, y2)
                    # continuous top line border
                    if i == 0:
                        self._fpdf.line(x1, y1, x2, y1)
                    # continuous bottom line border
                    if i + cell.rowspan == len(self.rows):
                        self._fpdf.line(x1, y2, x2, y2)

                self._fpdf.set_line_width(_remember_linewidth)

        # render image:
        if cell.img:
            x, y = self._fpdf.x, self._fpdf.y

            # if cell_height is None or width is given then call image with h=0
            # calling with h=0 means that the image will be rendered with an auto determined height
            auto_height = cell.img_fill_width or cell_height is None
            cell_border_line_width = self._fpdf.line_width

            # apply padding
            self._fpdf.x += padding.left + cell_border_line_width / 2
            self._fpdf.y += padding.top + cell_border_line_width / 2

            image = self._fpdf.image(
                cell.img,
                w=col_width - padding.left - padding.right - cell_border_line_width,
                h=(
                    0
                    if auto_height
                    else cell_height
                    - padding.top
                    - padding.bottom
                    - cell_border_line_width
                ),
                keep_aspect_ratio=True,
                link=cell.link,
            )

            img_height = (
                image.rendered_height
                + padding.top
                + padding.bottom
                + cell_border_line_width
            )

            if img_height + y > self._fpdf.page_break_trigger:
                page_break_image = True

            self._fpdf.set_xy(x, y)

        # render text

        if cell.text:
            dy = 0

            if cell_height is not None:
                actual_text_height = cell_height_info.rendered_heights[j]

                if v_align == VAlign.M:
                    dy = (cell_height - actual_text_height) / 2
                elif v_align == VAlign.B:
                    dy = cell_height - actual_text_height

            self._fpdf.y += dy

            with self._fpdf.use_font_face(style):
                page_break_text, cell_height = self._fpdf.multi_cell(
                    w=col_width,
                    h=row_height,
                    text=cell.text,
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
                    link=cell.link,
                    **kwargs,
                )

            self._fpdf.y -= dy
        else:
            cell_height = 0

        do_pagebreak = page_break_text or page_break_image

        return do_pagebreak, img_height, cell_height

    def _get_col_width(self, i, j, colspan=1):
        """Gets width of a column in a table, this excludes the outer gutter (outside the table) but includes the inner gutter
        between columns if the cell spans multiple columns."""

        cols_count = self._cols_count
        width = (
            self._width
            - (cols_count - 1) * self._gutter_width
            - 2 * self._outer_border_margin[0]
        )
        gutter_within_cell = max((colspan - 1) * self._gutter_width, 0)

        if not self._col_widths:
            return colspan * (width / cols_count) + gutter_within_cell
        if isinstance(self._col_widths, Number):
            return colspan * self._col_widths + gutter_within_cell
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

    def _compute_rows_info(self):
        # First pass: Regularise the table by processing the rowspan and colspan entries
        active_rowspans = {}
        prev_row_in_col = {}
        for i, row in enumerate(self.rows):
            # Link up rowspans
            active_rowspans, prior_rowspans = row.convert_spans(active_rowspans)
            for col_idx in prior_rowspans:
                # This cell is TableSpan.ROW, so accumulate to the previous row
                prev_row = prev_row_in_col[col_idx]
                if prev_row is not None:
                    # Since Cell objects are frozen, we need to recreate them to update the rowspan
                    cell = prev_row.cells[col_idx]
                    prev_row.cells[col_idx] = replace(cell, rowspan=cell.rowspan + 1)
            for j, cell in enumerate(row.cells):
                if isinstance(cell, Cell):
                    # Keep track of the non-span cells
                    prev_row_in_col[j] = row
                    for k in range(j + 1, j + cell.colspan):
                        prev_row_in_col[k] = None
        if len(active_rowspans) != 0:
            raise FPDFException("Rowspan extends beyond end of table")

        # Second pass: Estimate the cell sizes
        rowspan_list = []
        row_min_heights = []
        row_span_max = []
        rendered_heights = []
        # pylint: disable=protected-access
        with self._fpdf._disable_writing():
            for i, row in enumerate(self.rows):
                dictated_heights = []
                img_heights = []
                rendered_heights.append({})

                for j, cell in enumerate(row.cells):
                    if cell is None:  # placeholder cell
                        continue

                    # NB: ignore page_break since we might need to assign rowspan padding
                    _, img_height, text_height = self._render_table_cell(
                        i,
                        j,
                        cell,
                        row_height=self._line_height,
                    )
                    if cell.img_fill_width:
                        dictated_height = img_height
                    else:
                        dictated_height = text_height

                    # Store the dictated heights in a dict (not list) because of span elements
                    rendered_heights[i][j] = dictated_height

                    if cell.rowspan > 1:
                        # For spanned rows, use img_height if dictated_height is zero
                        rowspan_list.append(
                            RowSpanLayoutInfo(
                                j, i, cell.rowspan, dictated_height or img_height
                            )
                        )
                        # Often we want rowspans in headings, but issues arise if the span crosses outside the heading
                        is_heading = i < self._num_heading_rows
                        span_outside_heading = i + cell.rowspan > self._num_heading_rows
                        if is_heading and span_outside_heading:
                            raise FPDFException(
                                "Heading includes rowspan beyond the number of heading rows"
                            )
                    else:
                        dictated_heights.append(dictated_height)
                        img_heights.append(img_height)

                # The height of the rows is chosen as follows:
                # The "dictated height" is the space required for text/image, so pick the largest in the row
                # If this is zero, we will fill the space with images, so pick the largest image height
                # If this is still zero (e.g. empty/fully spanned row), use a sensible default
                min_height = 0
                if dictated_heights:
                    min_height = max(dictated_heights)
                    if min_height == 0:
                        min_height = max(img_heights)
                if min_height == 0:
                    min_height = self._line_height
                if row.min_height:
                    if min_height < row.min_height:
                        min_height = row.min_height
                elif self._min_row_height:
                    if min_height < self._min_row_height:
                        min_height = self._min_row_height

                row_min_heights.append(min_height)
                row_span_max.append(row.max_rowspan)

        # Sort the spans so we allocate padding to the smallest spans first
        rowspan_list = sorted(rowspan_list, key=lambda span: span.length)

        # Third pass: allocate space required for the rowspans
        row_span_padding = [0 for row in self.rows]
        for span in rowspan_list:
            # accumulate already assigned properties
            max_padding = 0
            assigned_height = self._gutter_height * (span.length - 1)
            assigned_padding = 0
            for i in span.row_range():
                max_padding = max(max_padding, row_span_padding[i])
                assigned_height += row_min_heights[i]
                assigned_padding += row_span_padding[i]

            # does additional padding need to be distributed?
            if assigned_height + assigned_padding < span.contents_height:
                # when there are overlapping rowspans, can we stretch the cells to be evenly padded?
                if span.contents_height > assigned_height + span.length * max_padding:
                    # stretch all cells to have the same padding, for aesthetic reasons
                    padding = (span.contents_height - assigned_height) / span.length
                    for i in span.row_range():
                        row_span_padding[i] = padding
                else:
                    # add proportional padding to the rows
                    extra = span.contents_height - assigned_height - assigned_padding
                    for i in span.row_range():
                        row_span_padding[i] += extra / span.length

        # Fourth pass: compute the final element sizes
        for i, row in enumerate(self.rows):
            row_height = row_min_heights[i] + row_span_padding[i]
            # Compute the size of merged cells
            merged_sizes = [0, row_height]
            for j in range(i + 1, i + row_span_max[i]):
                merged_sizes.append(
                    merged_sizes[-1]
                    + self._gutter_height
                    + row_min_heights[j]
                    + row_span_padding[j]
                )
            # Pagebreak should not occur within ANY rowspan, so validate ACCUMULATED rowspans
            # This gets complicated because of overlapping rowspans (see `test_table_with_rowspan_and_pgbreak()`)
            # Eventually, this should be refactored to rearrange cells to permit breaks within spans
            pagebreak_height = row_height
            pagebreak_row = i + row_span_max[i]
            j = i + 1
            while j < pagebreak_row:
                # NB: this can't be a for loop because the upper limit might keep changing
                pagebreak_row = max(pagebreak_row, j + row_span_max[j])
                pagebreak_height += (
                    self._gutter_height + row_min_heights[j] + row_span_padding[j]
                )
                j += 1

            yield RowLayoutInfo(
                merged_sizes[1], pagebreak_height, rendered_heights[i], merged_sizes
            )


class Row:
    "Object that `Table.row()` yields, used to build a row in a table"

    def __init__(self, table, style=None, v_align=None, min_height=None):
        self._table = table
        self.cells = []
        self.style = style
        self.v_align = VAlign.coerce(v_align) if v_align else v_align
        self.min_height = min_height

    @property
    def cols_count(self):
        return sum(getattr(cell, "colspan", cell is not None) for cell in self.cells)

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
        style=None,
        img=None,
        img_fill_width=False,
        colspan=1,
        rowspan=1,
        padding=None,
        link=None,
        border=CellBordersLayout.INHERIT,
    ):
        """
        Adds a cell to the row.

        Args:
            text (str): string content, can contain several lines.
                In that case, the row height will grow proportionally.
            align (str, fpdf.enums.Align): optional text alignment.
            v_align (str, fpdf.enums.VAlign): optional vertical text alignment.
            style (fpdf.fonts.FontFace): optional text style.
            img: optional. Either a string representing a file path to an image,
                an URL to an image, an io.BytesIO, or a instance of `PIL.Image.Image`.
            img_fill_width (bool): optional, defaults to False. Indicates to render the image
                using the full width of the current table column.
            colspan (int): optional number of columns this cell should span.
            rowspan (int): optional number of rows this cell should span.
            padding (tuple): optional padding (left, top, right, bottom) for the cell.
            link (str, int): optional link, either an URL or an integer returned by `FPDF.add_link`, defining an internal link to a page
            border (fpdf.enums.CellBordersLayout): optional cell borders, defaults to `CellBordersLayout.INHERIT`

        """
        if text and img:
            raise NotImplementedError(
                "fpdf2 currently does not support inserting text with an image in the same table cell."
                " Pull Requests are welcome to implement this 😊"
            )

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

        cell = Cell(
            text,
            align,
            VAlign.coerce(v_align) if v_align else v_align,
            style,
            img,
            img_fill_width,
            colspan,
            rowspan,
            padding,
            link,
            CellBordersLayout.coerce(border),
        )
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
        "rowspan",
        "padding",
        "link",
        "border",
    )
    text: str
    align: Optional[Union[str, Align]]
    v_align: Optional[Union[str, VAlign]]
    style: Optional[FontFace]
    img: Optional[str]
    img_fill_width: bool
    colspan: int
    rowspan: int
    padding: Optional[Union[int, tuple, type(None)]]
    link: Optional[Union[str, int]]
    border: Optional[CellBordersLayout]

    def write(self, text, align=None):
        raise NotImplementedError("Not implemented yet")


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
