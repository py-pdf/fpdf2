_New in [:octicons-tag-24: 2.7.7](https://github.com/py-pdf/fpdf2/blob/master/CHANGELOG.md)_

**Notice:** As of fpdf2 release 2.7.7, this is an experimental feature. Both the API and the functionality may change before it is finalized, without prior notice.


## Text Columns ##

The `FPDF.text_column() and ``FPDF.text_columns()` methods allow to create columnar layouts, with one or several columns respectively. Columns will always be of equal width.

Beyond the parameters common to all text regions, the following are available for text columns:

* l_margin (float, optional) - override the current left page margin.
* r_margin (float, optional) - override the current right page margin.

Only for `FPDF.text_columns()`:

* ncols (float, optional) - the number of columns to generate (Default: 2).
* gutter (float, optional) - the space required between each two columns (Default 10).


#### Single-Column Example ####

In this example an inserted paragraph is used in order to format its content with justified alignment, while the rest of the text uses the default left alignment.

```python
    cols = pdf.text_column()
    with cols:
        cols.write(txt=LOREM_IPSUM)
        with cols.paragraph(align="J") as par:
            par.write(txt=LOREM_IPSUM[:100])
        cols.write(txt=LOREM_IPSUM)
```

#### Multi-Column Example

Here we have a layout with three columns. Note that font type and text size can be varied within a text region, while still maintaining the justified (in this case) horizontal alignment.

```python
    with pdf.text_columns(align="J", ncols=3, gutter=5) as cols
        cols.write(txt=LOREM_IPSUM)
        pdf.set_font("Times", "", 8)
        cols.write(txt=LOREM_IPSUM)
        pdf.set_font("Courier", "", 10)
        cols.write(txt=LOREM_IPSUM)
        pdf.set_font("Helvetica", "", 12)
```

#### Balanced Columns

Normally the columns will be filled left to right, and if the text ends before the page is full, the rightmost column will be shorter than the others.
If you prefer that all columns on a page end on the same height, you can use the `balance=True` argument. In that case a simple algorithm will be applied that attempts to approximately balance their bottoms.

```python
    cols = pdf.text_columns(align="J", ncols=3, gutter=5, balanced=True)
	# fill columns with balanced text
	with cols:
        pdf.set_font("Times", "", 14)
        cols.write(txt=LOREM_IPSUM[:300])
	pdf.ln()
	# add an image below
	img_info = pdf.image("image_spanning_the_page_width.png")
	# move vertical position to below the image
	pdf.ln(img_info.rendered_hight + pdf.font_size)
	# continue multi-column text
	with cols:
        cols.write(txt=LOREM_IPSUM[300:600])
```

Note that column balancing only works reliably when the font size (specifically the line height) doesn't change. If parts of the text use a larger or smaller font than the rest, then the balancing will usually be out of whack. Contributions for a more refined balancing algorithm are welcome.


### Possible future extensions

Those features are currently not supported, but Pull Requests are welcome to implement them:

* Columns with differing widths (no balancing possible in this case).

