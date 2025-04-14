_New in [:octicons-tag-24: 2.7.6](https://github.com/py-pdf/fpdf2/blob/master/CHANGELOG.md)_

## Text Columns
The [`FPDF.text_columns()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.text_columns) method allows to create columnar layouts, with one or several columns.
Columns will always be of equal width.

Text columns support all the standard [text region](TextRegion.md) methods, and some extra ones:

* [`.paragraph()`](https://py-pdf.github.io/fpdf2/fpdf/text_region.html#fpdf.text_region.TextColumns.paragraph)
* [`.write()`](https://py-pdf.github.io/fpdf2/fpdf/text_region.html#fpdf.text_region.TextColumns.write)
* [`.ln()`](https://py-pdf.github.io/fpdf2/fpdf/text_region.html#fpdf.text_region.TextColumns.ln)
* [`.new_column()`](https://py-pdf.github.io/fpdf2/fpdf/text_region.html#fpdf.text_region.TextColumns.new_column)

A **form feed** character (`\u000c`) in the text will have the same effect as an explicit call to `.new_column()`,

Note that when used within [balanced columns](#balanced-columns), switching to a new column manually will result in incorrect balancing.

### Single-Column Example
In this example an inserted paragraph is used in order to format its content with justified alignment, while the rest of the text uses the default left alignment.

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Times", size=12)
with pdf.text_columns() as cols:
    cols.write(text=LOREM_IPSUM[:400])
    with cols.paragraph(
        text_align="J",
        top_margin=pdf.font_size,
        bottom_margin=pdf.font_size
    ) as paragraph:
        paragraph.write(text=LOREM_IPSUM[:400])
    cols.write(text=LOREM_IPSUM[:400])
pdf.output("text_columns.pdf")
```
![Single Text Column](tcols-single.png)

_New in [:octicons-tag-24: 2.8.3](https://github.com/py-pdf/fpdf2/blob/master/CHANGELOG.md)_

**Indentation** can be set on the first line of paragraphs
by passing a `first_line_indent` value to [`.paragraph()`](https://py-pdf.github.io/fpdf2/fpdf/text_region.html#fpdf.text_region.TextColumns.paragraph).

### Multi-Column Example
Here we have a layout with three columns. Note that font type and text size can be varied within a text region, while still maintaining the justified (in this case) horizontal alignment.

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Helvetica", size=16)
with pdf.text_columns(text_align="J", ncols=3, gutter=5) as cols:
    cols.write(text=LOREM_IPSUM[:600])
    pdf.set_font("Times", size=18)
    cols.write(text=LOREM_IPSUM[:500])
    pdf.set_font("Courier", size=20)
    cols.write(text=LOREM_IPSUM[:500])
pdf.output("multi_columns.pdf")
```
![Three Text Columns](tcols-three.png)

### Balanced Columns
Normally the columns will be filled left to right, and if the text ends before the page is full, the rightmost column will be shorter than the others.
If you prefer that all columns on a page end on the same height, you can use the `balance=True` argument. In that case a simple algorithm will be applied that attempts to approximately balance their bottoms.

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Times", size=12)

cols = pdf.text_columns(text_align="J", ncols=3, gutter=5, balance=True)
# fill columns with balanced text
with cols:
    pdf.set_font("Times", size=14)
    cols.write(text=LOREM_IPSUM[:300])
# add an image below
img_info = pdf.image(".../fpdf2/docs/regular_polygon.png",
                     x=pdf.l_margin, w=pdf.epw)
# continue multi-column text
with cols:
    cols.write(text=LOREM_IPSUM[300:600])
pdf.output("balanced_columns.pdf")
```
![Balanced Columns](tcols-balanced.png)

Note that column balancing only works reliably when the font size (specifically the line height) doesn't change, and if there are no images included. If parts of the text use a larger or smaller font than the rest, then the balancing will usually be out of whack. Contributions for a more refined balancing algorithm are welcome.

### Possible future extensions
Those features are currently not supported, but Pull Requests are welcome to implement them:

* Columns with differing widths (no balancing possible in this case).
