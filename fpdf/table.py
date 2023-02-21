from contextlib import contextmanager
from numbers import Number

from .fonts import FontStyle


DEFAULT_HEADINGS_STYLE = FontStyle(emphasis="BOLD")


class Table:
    def __init__(self, fpdf):
        self._fpdf = fpdf
        self._rows = []
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
            self._render_table_row_styled(i)

    def _render_table_row_styled(self, i):
        if i == 0 and self.first_row_as_headings:
            with self._fpdf.use_font_style(self.headings_style):
                self._render_table_row(i, fill=bool(self.headings_style.fill_color))
        else:
            self._render_table_row(i)

    def _render_table_row(self, i, **kwargs):
        row = self._rows[i]
        lines_count_per_cell = self._get_lines_count_per_cell(i)
        row_height = max(lines_count_per_cell) * self.line_height
        for j in range(len(row.cells)):
            cell_line_height = row_height / lines_count_per_cell[j]
            self._render_table_cell(
                i, j, h=row_height, max_line_height=cell_line_height, **kwargs
            )
        self._fpdf.ln(row_height)

    def _render_table_cell(self, i, j, h, **kwargs):
        row = self._rows[i]
        col_width = self._get_col_width(i, j)
        return self._fpdf.multi_cell(
            w=col_width,
            h=h,
            txt=row.cells[j],
            border=1,
            new_x="RIGHT",
            new_y="TOP",
            **kwargs,
        )

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

    def _get_lines_count_per_cell(self, i):
        row = self._rows[i]
        lines_count = []
        for j in range(len(row.cells)):
            lines_count.append(
                len(
                    self._render_table_cell(
                        i,
                        j,
                        h=self.line_height,
                        max_line_height=self.line_height,
                        split_only=True,
                    )
                )
            )
        return lines_count


class Row:
    def __init__(self):
        self.cells = []

    def cell(self, text):
        self.cells.append(text)
