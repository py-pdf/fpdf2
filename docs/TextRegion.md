_New in [:octicons-tag-24: 2.7.7](https://github.com/py-pdf/fpdf2/blob/master/CHANGELOG.md)_
# Text Flow Regions #

**Notice:** As of fpdf2 release 2.7.7, this is an experimental feature. Both the API and the functionality may change before it is finalized, without prior notice.

Text regions are a hierarchy of classes that enable to flow text within a given outline. In the simplest case, it is just the running text column of a page. But it can also be a sequence of outlines, such as several parallel columns or the cells of a table. Other outlines may be combined by addition or subtraction to create more complex shapes. 

There are two general categories of regions. One defines boundaries for running text that will just continue in the same manner one the next page. Those include columns and tables. The second category are distinct shapes. Examples would be a circle, a rectangle, a polygon of individual shape or even an image. They may be used individually, in combination, or to modify the outline of a multipage column. Shape regions will typically not cause a page break when they are full. In the future, a possibility to chain them may be implemented, so that a new shape will continue with the text that didn't fit into the previous one.

**The current implementation only supports columns.** Shaped regions and combinations are still in the design phase.

## General Operation ##

Using the different region types and combination always follows the same pattern. The main difference to the normal `FPDF.write()` method is that all added text will first be buffered, and you need to explicitly trigger its rendering on the page. This is necessary so that text can be aligned within the given boundaries even if its font, style, or size are arbitrarily varied along the way.

* Create the region instance with an `FPDF` method.
* future: (_If desired, add or subtract other shapes from it (with geometric regions)_).
* Use the `.write()` method to feed text into its buffer.
* Best practise is to use the region instance as a context manager for filling.
	* Text will be rendered automatically after closing the context.
	* When used as a context manager, you can change all text styling parameters within that context, and they will be used by the added text, but won't leak to the surroundings
* Alternatively, eg. for filling a single column of text with the already existing settings, just use the region instance as is. In that case, you'll have to explicitly use the `render()` method after adding the text.
* Within a region, paragraphs can be inserted. The primary purpose of a paragraph is to apply a different horizontal alignment than the surrounding text.

### Text Start Position ###

When rendering, the vertical start position of the text will be at the lowest one out of the current y position, the top of the region (if it has a defined top), or the top margin of the page. The horizontal start position will be either at the current x position if that lies within the boundaries of the region/column or at the left edge of the region. In both horizontal and vertical positioning, regions with multiple columns may follow additional rules and restrictions.


### Interaction between Regions ###

Several region instances can exist at the same time. But only one of them can act as context manager at any given time. It is not currently possible to use them recursively.
But it is possible to use them intermittingly. This will probably most often make sense between a columnar region and a table. You may have some running text ending at a given height, then insert a table with data, and finally continue the running text at the new height below the table within the existing column(s).


## Columns ##

The `FPDF.text_column() and ``FPDF.text_columns()` methods allow to create columnar layouts, with one or several columns respectively. Columns will always be of equal width.

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


## Paragraphs ##

The primary purpose of paragraphs is to enable variations in horizontal text alignment, while the horizontal extents of the text are managed by the text region. To set the alignment, you can use the `align` argument when creating the paragraph, with the same `Align` values as elsewhere in the library. Note that the `write()` methods of paragraphs and text regions in general don't accept this argument, they only accept text.

For more typographical control, you can also use the following arguments:
* line_height (default: 1.0) - This is a factor by which the line spacing will be different from the font height. It works similar to the attribute of the same name in HTML/CSS.
* top_margin (default: 0.0) 
* bottom_margin (default: 0.0) - Those two values determine how much spacing is added above and below the paragraph. No spacing will be added at the top if the paragraph if the current y position is at (or above) the top margin of the page. Similarly, none will be added at the bottom if it would result in overstepping the bottom margin of the page.
* skip_leading_spaces (default: False) - This flag is primarily used by `write_html()`, but may also have other uses. It removes all space characters at the beginning of each line.

Other than text regions, paragraphs should alway be used as context managers and never be reused. Violating those rules may result in the entered text turning up on the page out of sequence.

### Possible future extensions

Those features are currently not supported, but Pull Requests are welcome to implement them:

* per-paragraph indentation
* first-line indentation
