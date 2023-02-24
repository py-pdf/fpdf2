from contextlib import contextmanager
from numbers import Number
from typing import List

from .enums import TableBordersLayout
from .fonts import FontStyle


DEFAULT_HEADINGS_STYLE = FontStyle(emphasis="BOLD")


class Table:
    def __init__(self, fpdf):
        self._fpdf = fpdf
        self._rows = []
        self.borders_layout = TableBordersLayout.ALL
        self.cell_fill_color = None
        self.cell_fill_logic = lambda i, j: True
        self.col_widths = None
        self.first_row_as_headings = True
        self.headings_style = DEFAULT_HEADINGS_STYLE
        self.line_height = 2 * fpdf.font_size
        self.width = fpdf.epw

    @contextmanager
    def row(self):
        row = Row()
        self._rows.append(row)
        yield row

    def render(self):
        for i in range(len(self._rows)):
            with self._fpdf.offset_rendering() as test:
                self._render_table_row_styled(i)
            if test.page_break_triggered:
                # pylint: disable=protected-access
                self._fpdf._perform_page_break()
                if self.first_row_as_headings:  # repeat headings on top:
                    self._render_table_row_styled(0)
            if self.cell_fill_color:
                prev_fill_color = self._fpdf.fill_color
                self._fpdf.set_fill_color(self.cell_fill_color)
            else:
                prev_fill_color = None
            self._render_table_row_styled(i)
            if prev_fill_color:
                self._fpdf.set_fill_color(prev_fill_color)

    def get_cell_border(self, i, j):
        "Can be overriden to customize this logic"
        if self.borders_layout == TableBordersLayout.ALL.value:
            return 1
        columns_count = max(len(row.cells) for row in self._rows)
        rows_count = len(self._rows)
        border = list("LRTB")
        if self.borders_layout == TableBordersLayout.INTERNAL.value:
            if i == 0 and "T" in border:
                border.remove("T")
            if i == rows_count - 1 and "B" in border:
                border.remove("B")
            if j == 0 and "L" in border:
                border.remove("L")
            if j == columns_count - 1 and "R" in border:
                border.remove("R")
        if self.borders_layout == TableBordersLayout.MINIMAL.value:
            if i != 0 and "B" in border:
                border.remove("B")
            if rows_count > 1 and i != 1 and "T" in border:
                border.remove("T")
            if j == 0 and "L" in border:
                border.remove("L")
            if j == columns_count - 1 and "R" in border:
                border.remove("R")
        if self.borders_layout == TableBordersLayout.SINGLE_TOP_LINE.value:
            border = list("TB")
            if i != 0 and "B" in border:
                border.remove("B")
            if rows_count > 1 and i != 1 and "T" in border:
                border.remove("T")
        return "".join(border)

    def _render_table_row_styled(self, i):
        if i == 0 and self.first_row_as_headings:
            with self._fpdf.use_font_style(self.headings_style):
                self._render_table_row(i, fill=bool(self.headings_style.fill_color))
        else:
            self._render_table_row(i)

    def _render_table_row(self, i, fill=False, **kwargs):
        row = self._rows[i]
        lines_heights_per_cell = self._get_lines_heights_per_cell(i)
        row_height = max(sum(lines_heights) for lines_heights in lines_heights_per_cell)
        for j in range(len(row.cells)):
            cell_line_height = row_height / len(lines_heights_per_cell[j])
            self._render_table_cell(
                i,
                j,
                cell_line_height=cell_line_height,
                row_height=row_height,
                fill=fill,
                **kwargs,
            )
        self._fpdf.ln(row_height)

    # pylint: disable=inconsistent-return-statements
    def _render_table_cell(
        self,
        i,
        j,
        cell_line_height,
        row_height,
        fill=False,
        lines_heights_only=False,
        **kwargs,
    ):
        """
        If `lines_heights_only` is True, returns a list of lines (subcells) heights.
        """
        row = self._rows[i]
        col_width = self._get_col_width(i, j)
        cell = row.cells[j]
        lines_heights = []
        if cell.img:
            if lines_heights_only:
                info = self._fpdf.preload_image(cell.img)[2]
                img_ratio = info.width / info.height
                if cell.img_fill_width or row_height * img_ratio > col_width:
                    img_height = col_width / img_ratio
                else:
                    img_height = row_height
                lines_heights += [img_height]
            else:
                x, y = self._fpdf.x, self._fpdf.y
                self._fpdf.image(
                    cell.img,
                    w=col_width,
                    h=0 if cell.img_fill_width else row_height,
                    keep_aspect_ratio=True,
                )
                self._fpdf.set_xy(x, y)
        if not fill:
            fill = self.cell_fill_color and self.cell_fill_logic(i, j)
        lines = self._fpdf.multi_cell(
            w=col_width,
            h=row_height,
            txt=cell.text or "",
            max_line_height=cell_line_height,
            border=self.get_cell_border(i, j),
            new_x="RIGHT",
            new_y="TOP",
            fill=fill,
            split_only=lines_heights_only,
            **kwargs,
        )
        if lines_heights_only and cell.text:
            lines_heights += len(lines) * [self.line_height]
        if lines_heights_only:
            return lines_heights

    def _get_col_width(self, i, j):
        if not self.col_widths:
            cols_count = len(self._rows[i].cells)
            return self.width / cols_count
        if isinstance(self.col_widths, Number):
            return self.col_widths
        if j >= len(self.col_widths):
            raise ValueError(
                f"Invalid .col_widths specified: missing width for table() column {j + 1} on row {i + 1}"
            )
        # pylint: disable=unsubscriptable-object
        col_ratio = self.col_widths[j] / sum(self.col_widths)
        return col_ratio * self.width

    def _get_lines_heights_per_cell(self, i) -> List[List[int]]:
        row = self._rows[i]
        lines_heights = []
        for j in range(len(row.cells)):
            lines_heights.append(
                self._render_table_cell(
                    i,
                    j,
                    cell_line_height=self.line_height,
                    row_height=self.line_height,
                    lines_heights_only=True,
                )
            )
        return lines_heights


class Row:
    def __init__(self):
        self.cells = []

    def cell(self, text=None, img=None, img_fill_width=False):
        self.cells.append(Cell(text, img, img_fill_width))


class Cell:
    def __init__(self, text, img, img_fill_width):
        self.text = text
        self.img = img
        self.img_fill_width = img_fill_width
