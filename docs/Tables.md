# Tables #

Tables can be built either using **cells**
or with [`write_html`](HTML.md).


## Using cells ##

There is a method to build tables allowing for multilines content in cells:

```python
from fpdf import FPDF

data = (
    ("First name", "Last name", "Age", "City"),
    ("Jules", "Smith", "34", "San Juan"),
    ("Mary", "Ramos", "45", "Orlando"),
    ("Carlson", "Banks", "19", "Los Angeles"),
    ("Lucas", "Cimon", "31", "Saint-Mahturin-sur-Loire"),
)

pdf = FPDF()
pdf.add_page()
pdf.set_font("Times", size=10)
line_height = pdf.font_size * 2.5
col_width = pdf.epw / 4  # distribute content evenly
for row in data:
    for datum in row:
        pdf.multi_cell(col_width, line_height, datum, border=1,
                new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
    pdf.ln(line_height)
pdf.output('table_with_cells.pdf')
```


## Using write_html ##

An alternative method using [`FPDF.write_html`](HTML.md),
with the same `data` as above, and column widths defined as percent of the effective width:

```python
from fpdf import FPDF

pdf = FPDF()
pdf.set_font_size(16)
pdf.add_page()
pdf.write_html(
    f"""<table border="1"><thead><tr>
    <th width="25%">{data[0][0]}</th>
    <th width="25%">{data[0][1]}</th>
    <th width="15%">{data[0][2]}</th>
    <th width="35%">{data[0][3]}</th>
</tr></thead><tbody><tr>
    <td>{'</td><td>'.join(data[1])}</td>
</tr><tr>
    <td>{'</td><td>'.join(data[2])}</td>
</tr><tr>
    <td>{'</td><td>'.join(data[3])}</td>
</tr><tr>
    <td>{'</td><td>'.join(data[4])}</td>
</tr></tbody></table>""",
    table_line_separators=True,
)
pdf.output('table_html.pdf')
```

Note that `write_html` has [some limitations, notably regarding multi-lines cells](HTML.html#supported-html-features).


## Recipes ##

- our 5th tutorial provides examples on how to build tables: [Tuto 5 - Creating Tables](Tutorial.md#tuto-5-creating-tables)
- `@bvalgard` wrote a custom `table()` method: [YouTube video](https://www.youtube.com/watch?v=euNvxWaRQMY) - [`create_table()` source code](https://github.com/bvalgard/create-pdf-with-python-fpdf2/blob/main/create_table_fpdf2.py)
- [code snippet by @RubendeBruin to adapt row height to the highest cell](https://github.com/PyFPDF/fpdf2/issues/91#issuecomment-813033012)
- detect if adding a table row will result in a page break: this can be done using [`.offset_rendering()`](https://pyfpdf.github.io/fpdf2/PageBreaks.html#unbreakable-sections)


## Repeat table header on each page ##

The following recipe demonstrates a solution to handle this requirement:

```python
from fpdf import FPDF

TABLE_COL_NAMES = ("First name", "Last name", "Age", "City")
TABLE_DATA = (
    ("Jules", "Smith", "34", "San Juan"),
    ("Mary", "Ramos", "45", "Orlando"),
    ("Carlson", "Banks", "19", "Los Angeles"),
    ("Lucas", "Cimon", "31", "Angers"),
)

pdf = FPDF()
pdf.add_page()
pdf.set_font("Times", size=16)
line_height = pdf.font_size * 2
col_width = pdf.epw / 4  # distribute content evenly

def render_table_header():
    pdf.set_font(style="B")  # enabling bold text
    for col_name in TABLE_COL_NAMES:
        pdf.cell(col_width, line_height, col_name, border=1)
    pdf.ln(line_height)
    pdf.set_font(style="")  # disabling bold text

render_table_header()
for _ in range(10):  # repeat data rows
    for row in TABLE_DATA:
        if pdf.will_page_break(line_height):
            render_table_header()
        for datum in row:
            pdf.cell(col_width, line_height, datum, border=1)
        pdf.ln(line_height)

pdf.output("table_with_headers_on_every_page.pdf")
```

Note that if you want to use [`multi_cell()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) method instead of `cell()`,
some extra code will be required: an initial call to `multi_cell` with `split_only=True`
will be needed in order to compute the number of lines in the cell.
