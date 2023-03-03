# Tables

_New in [:octicons-tag-24: 2.7.0](https://github.com/PyFPDF/fpdf2/blob/master/CHANGELOG.md)_

Tables can be built using the `table()` method.
Here is a simple example:

```python
from fpdf import FPDF

TABLE_DATA = (
    ("First name", "Last name", "Age", "City"),
    ("Jules", "Smith", "34", "San Juan"),
    ("Mary", "Ramos", "45", "Orlando"),
    ("Carlson", "Banks", "19", "Los Angeles"),
    ("Lucas", "Cimon", "31", "Saint-Mahturin-sur-Loire"),
)
pdf = FPDF()
pdf.add_page()
pdf.set_font("Times", size=16)
with pdf.table() as table:
    for data_row in TABLE_DATA:
        row = table.row()
        for datum in data_row:
            row.cell(datum)
pdf.output('table.pdf')
```
Result:

![](table-simple.jpg)

## Features
* support cells with content wrapping over several lines
* control over column & row sizes (automatically computed by default)
* allow to style table headings (top row), or disable them
* control over borders: color, width & where they are drawn
* handle splitting a table over page breaks, with headings repeated
* control over cell background color
* control table width & position
* control over text alignment in cells, globally or per row
* allow to embed images in cells

## Setting table & column widths
```python
...
with pdf.table(width=150, col_widths=(30, 30, 10, 30)) as table:
    ...
```
Result:

![](table-with-fixed-column-widths.jpg)

`align` can be passed to `table()` to set the table horizontal position relative to the page,
when it's not using the full page width. It's centered by default.

## Setting text alignment
This can be set globally, or on a per-column basis:
```python
...
with pdf.table(text_align="CENTER") as table:
    ...
pdf.ln()
with pdf.table(text_align=("CENTER", "CENTER", "RIGHT", "LEFT")) as table:
    ...
```
Result:

![](table_align.jpg)

## Setting row height
```python
...
with pdf.table(line_height=2.5 * pdf.font_size) as table:
    ...
```

## Disable table headings
```python
...
with pdf.table(first_row_as_headings=False) as table:y
    ...
```

## Style table headings
```python
...
blue = (0, 0, 255)
grey = (128, 128, 128)
headings_style = FontStyle(emphasis="ITALICS", color=blue, fill_color=grey)
with pdf.table(headings_styleheadings_style=headings_style) as table:
    ...
```
Result:

![](table-styled.jpg)

## Set cells background
```python
...
greyscale = 200
with pdf.table(cell_fill_color=greyscale, cell_fill_mode="ROWS") as table:
    ...
```
Result:

![](table-with-cells-filled.jpg)

```python
...
lightblue = (173, 216, 230)
with pdf.table(cell_fill_color=lightblue, cell_fill_mode="COLUMNS") as table:
    ...
```
Result:

![](table-with-cells-filled2.jpg)

## Set borders layout
```python
...
with pdf.table(borders_layout="INTERNAL") as table:
    ...
```
Result:

![](table_with_internal_layout.jpg)

```python
...
with pdf.table(borders_layout="MINIMAL") as table:
    ...
```
Result:

![](table_with_minimal_layout.jpg)

```python
...
pdf.set_draw_color(50)  # very dark grey
pdf.set_line_width(.5)
with pdf.table(borders_layout="SINGLE_TOP_LINE") as table:
    ...
```
Result:

![](table_with_single_top_line_layout.jpg)

All the possible layout values are described there: [`TableBordersLayout`](https://pyfpdf.github.io/fpdf2/fpdf/enums.html#fpdf.enums.TableBordersLayout).

## Insert images
```python
TABLE_DATA = (
    ("First name", "Last name", "Image", "City"),
    ("Jules", "Smith", "shirt.png", "San Juan"),
    ("Mary", "Ramos", "joker.png", "Orlando"),
    ("Carlson", "Banks", "socialist.png", "Los Angeles"),
    ("Lucas", "Cimon", "circle.bmp", "Angers"),
)
pdf = FPDF()
pdf.add_page()
pdf.set_font("Times", size=16)
with pdf.table() as table:
    for i, data_row in enumerate(TABLE_DATA):
        row = table.row()
        for j, datum in enumerate(data_row):
            if j == 2 and i > 0:
                row.cell(img=datum)
            else:
                row.cell(datum)
pdf.output('table_with_images.pdf')
```
Result:

![](table_with_images.jpg)

By default, images height & width are constrained by the row height (based on text content)
and the column width. To render bigger images, you can set the `line_height` to increase the row height, or pass `img_fill_width=True` to `.cell()`:

```python
                    row.cell(img=datum, img_fill_width=True)
```
Result:

![](table_with_images_and_img_fill_width.jpg)

## Syntactic sugar

To simplify `table()` usage, shorter, alternative usage forms are allowed.

This sample code:
```python
with pdf.table() as table:
    for data_row in TABLE_DATA:
        row = table.row()
        for datum in data_row:
            row.cell(datum)
```

Can be shortened to the followng code,
by passing lists of strings as the `cells` optional argument of `.row()`:
```python
with pdf.table() as table:
    for data_row in TABLE_DATA:
        table.row(data_row)
```

And even shortened further to a single line,
by passing lists of lists of strings as the `rows` optional argument of `.table()`:
```python
with pdf.table(TABLE_DATA):
    pass
```

## Table from pandas DataFrame

_cf._ https://pyfpdf.github.io/fpdf2/Maths.html#using-pandas

## Using write_html

Tables can also be defined in HTML using [`FPDF.write_html`](HTML.md).
With the same `data` as above, and column widths defined as percent of the effective width:

```python
from fpdf import FPDF

pdf = FPDF()
pdf.set_font_size(16)
pdf.add_page()
pdf.write_html(
    f"""<table border="1"><thead><tr>
    <th width="25%">{TABLE_DATA[0][0]}</th>
    <th width="25%">{TABLE_DATA[0][1]}</th>
    <th width="15%">{TABLE_DATA[0][2]}</th>
    <th width="35%">{TABLE_DATA[0][3]}</th>
</tr></thead><tbody><tr>
    <td>{'</td><td>'.join(TABLE_DATA[1])}</td>
</tr><tr>
    <td>{'</td><td>'.join(TABLE_DATA[2])}</td>
</tr><tr>
    <td>{'</td><td>'.join(TABLE_DATA[3])}</td>
</tr><tr>
    <td>{'</td><td>'.join(TABLE_DATA[4])}</td>
</tr></tbody></table>""",
    table_line_separators=True,
)
pdf.output('table_html.pdf')
```

Note that `write_html` has [some limitations, notably regarding multi-lines cells](HTML.html#supported-html-features).
