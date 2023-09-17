# Text Flow Regions #

**Notice:** As of fpdf2 release 2.7.6, this is an experimental feature. Both the API and the functionality may change before it is finalized, without prior notice.

Text regions are a hierarchy of classes that enable to flow text within a given outline. In the simplest case, it is just the running text column of a page. But it can also be a sequence of outlines, such as several parallel columns or the cells of a table. Other outlines may be combined by addition or subtraction to create more complex shapes.

There are two general categories of regions. One defines boundaries for running text that will just continue in the same manner one the next page. Those include columns and tables. The second category are distinct shapes. Examples would be a circle, a rectangle, a polygon of individual shape or even an image. They may be used individually, in combination, or to modify the outline of a multipage column. Shape regions will typically not cause a page break when they are full. In the future, a possibility to chain them may be implemented, so that a new shape will continue with the text that didn't fit into the previous one.

## General Operation ##

Using the different region types and combination always follows the same pattern. The main difference to the normal `FPDF.write()` method is that all added text will first be buffered, and you need to explicitly trigger its rendering on the page. This is necessary so that text can be aligned within the given boundaries even if its font, style, or size are arbitrarily varied along the way.

* Create the region instance
* If desired, add or subtract other shapes from it
* Use the `.write()` method to feed text into its buffer
* You can use the region instance as a context manager for filling, but you don't have to
  * When used as a context manager, you can change all text styling parameters within that context, and they will be used by the added text, but won't leak to the surroundings
  * For adding text with the already existing settings, just use the region instance as is.
* Within a region, paragraphs can be inserted. The primary purpose of a paragraph is to apply a different horizontal alignment than the surrounding text.
* Once all the desired text is collected to fill a shape or a set of columns, you can call its `.render()` method to actually do so. 


### Text Start Position ###

When rendering, the vertical start position of the text will be at the lowest one out of the current y position, the top of the region (if it has a defined top), or the top margin of the page. The horizontal start position will either at the current x position or at the left edge of the region, whichever is further to the right. In both horizontal and vertical positioning, regions with multiple columns may follow additional rules and restrictions.


### Interaction between Regions ###

Several region instances can exist at the same time. But only one of them can act as context manager at any given time. It is not currently possible to operate them recursively.
But it is possible to use them intermittingly. This will probably most often make sense between a columnar region and a table. You may have some running text ending at a given height, then insert a table with data, and finally continue the running text at the new height below the table within the existing column.

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
    cols = pdf.text_columns(align="J", ncols=3, gutter=5)
    with cols:
        cols.write(txt=LOREM_IPSUM)
        pdf.set_font("Times", "", 8)
        cols.write(txt=LOREM_IPSUM)
        pdf.set_font("Courier", "", 10)
        cols.write(txt=LOREM_IPSUM)
        pdf.set_font("Helvetica", "", 12)
```

#### Balanced Columns

Normally the columns will be filled left to right, and if the text ends before the page is full, the rightmost column will end up shorter than the others.
If you prefer that all columns on a page end on the same height, you can use the `balanced=True` argument. In that case a simple algorithm will be applied that attempts to approximately balance their bottoms.

```python
    with pdf.text_columns(align="J", ncols=3, gutter=5, balanced=True) as cols:
        pdf.set_font("Times", "", 14)
        cols.write(txt=LOREM_IPSUM[:300])
```
Note that this only works reliably when the font size (specifically the line height) doesn't change. If parts of the text use a larger or smaller font than the rest, then the balancing will usually be out of whack. Contributions for a more refined balancing algorithm are welcome.

### Possible future extensions

Those features are currently not supported, but Pull Requests are welcome to implement them:

* Columns with differing widths (no balancing possible in this case).


## Paragraphs ##

The primary purpose of paragraphs is to enable variations in horizontal text alignment, while the horizontal extents of the text are managed by the text region.

Other than text regions, paragraphs should alway be used as context managers and never be reused. Violating those rules may result in the entered text turning up on the page out of sequence.

### Possible future extensions

Those features are currently not supported, but Pull Requests are welcome to implement them:

* Setting the spacing between paragraphs
* first-line indent
