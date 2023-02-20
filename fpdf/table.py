from numbers import Number


class Table:
    def __init__(self, fpdf, line_height=None, width=None):
        self.fpdf = fpdf
        self.line_height = line_height or 2 * self.fpdf.font_size
        self.width = width or fpdf.epw
        self.col_widths = None
        self.rows = []

    def __enter__(self):
        return self

    def row(self):
        row = Row(self)
        self.rows.append(row)
        return row

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        for i, row in enumerate(self.rows):
            lines_count_per_cell = self._get_lines_count_per_cell(i)
            row_height = max(lines_count_per_cell) * self.line_height
            for j in range(len(row.cells)):
                cell_line_height = row_height / lines_count_per_cell[j]
                self._render_table_cell(
                    i, j, h=row_height, max_line_height=cell_line_height
                )
            self.fpdf.ln(row_height)

    def _render_table_cell(self, i, j, h, **kwargs):
        row = self.rows[i]
        col_width = self._get_col_width(i, j)
        return self.fpdf.multi_cell(
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
            cols_count = len(self.rows[i].cells)
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
        row = self.rows[i]
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
    def __init__(self, table):
        self.table = table
        self.cells = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        pass

    def cell(self, text):
        self.cells.append(text)
