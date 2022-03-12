# Tutorial #

Methods full documentation: [`fpdf.FPDF` API doc](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF)

[TOC]

## Tuto 1 - Minimal Example ##

Let's start with the classic example:

```python
{% include "../tutorial/tuto1.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto1.pdf)

After including the library file, we create an `FPDF` object. The 
[FPDF](fpdf/fpdf.html#fpdf.fpdf.FPDF) constructor is used here with the default values: 
pages are in A4 portrait and the measure unit is millimeter.
It could have been specified explicitly with:

```python
pdf = FPDF(orientation="P", unit="mm", format="A4")
```

It is possible to set the PDF in landscape mode (`L`) or to use other page formats
(such as `Letter` and `Legal`) and measure units (`pt`, `cm`, `in`).

There is no page for the moment, so we have to add one with 
[add_page](fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page). The origin is at the upper-left corner and the
current position is by default placed at 1 cm from the borders; the margins can
be changed with [set_margins](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_margins).

Before we can print text, it is mandatory to select a font with 
[set_font](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font), otherwise the document would be invalid.
We choose Helvetica bold 16:

```python
pdf.set_font('helvetica', 'B', 16)
```

We could have specified italics with `I`, underlined with `U` or a regular font
with an empty string (or any combination). Note that the font size is given in
points, not millimeters (or another user unit); it is the only exception.
The other built-in fonts are `Times`, `Courier`, `Symbol` and `ZapfDingbats`.

We can now print a cell with [cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.cell). A cell is a rectangular
area, possibly framed, which contains some text. It is rendered at the current
position. We specify its dimensions, its text (centered or aligned), if borders
should be drawn, and where the current position moves after it (to the right,
below or to the beginning of the next line). To add a frame, we would do this:

```python
pdf.cell(40, 10, 'Hello World!', 1)
```

To add a new cell next to it with centered text and go to the next line, we
would do:

```python
pdf.cell(60, 10, 'Powered by FPDF.', ln=1, align='C')
```

**Remark**: the line break can also be done with [ln](fpdf/fpdf.html#fpdf.fpdf.FPDF.ln). This
method allows to specify in addition the height of the break.

Finally, the document is closed and saved under the provided file path using
[output](fpdf/fpdf.html#fpdf.fpdf.FPDF.output). Without any parameter provided, `output()`
returns the PDF `bytearray` buffer.

## Tuto 2 - Header, footer, page break and image ##

Here is a two page example with header, footer and logo:

```python
{% include "../tutorial/tuto2.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto2.pdf)

This example makes use of the [header](fpdf/fpdf.html#fpdf.fpdf.FPDF.header) and 
[footer](fpdf/fpdf.html#fpdf.fpdf.FPDF.footer) methods to process page headers and footers. They
are called automatically. They already exist in the FPDF class but do nothing,
therefore we have to extend the class and override them.

The logo is printed with the [image](fpdf/fpdf.html#fpdf.fpdf.FPDF.image) method by specifying
its upper-left corner and its width. The height is calculated automatically to
respect the image proportions.

To print the page number, a null value is passed as the cell width. It means
that the cell should extend up to the right margin of the page; it is handy to
center text. The current page number is returned by
the [page_no](fpdf/fpdf.html#fpdf.fpdf.FPDF.page_no) method; as for
the total number of pages, it is obtained by means of the special value `{nb}`
which will be substituted on document closure (provided you first called 
[alias_nb_pages](fpdf/fpdf.html#fpdf.fpdf.FPDF.alias_nb_pages)).
Note the use of the [set_y](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_y) method which allows to set
position at an absolute location in the page, starting from the top or the
bottom.

Another interesting feature is used here: the automatic page breaking. As soon
as a cell would cross a limit in the page (at 2 centimeters from the bottom by
default), a break is performed and the font restored. Although the header and
footer select their own font (`helvetica`), the body continues with `Times`.
This mechanism of automatic restoration also applies to colors and line width.
The limit which triggers page breaks can be set with 
[set_auto_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break).


## Tuto 3 - Line breaks and colors ##

Let's continue with an example which prints justified paragraphs. It also
illustrates the use of colors.

```python
{% include "../tutorial/tuto3.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto3.pdf)

[Jules Verne text](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/20k_c1.txt)

The [get_string_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.get_string_width) method allows determining
the length of a string in the current font, which is used here to calculate the
position and the width of the frame surrounding the title. Then colors are set
(via [set_draw_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color),
[set_fill_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color) and 
[set_text_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color)) and the thickness of the line is set
to 1 mm (against 0.2 by default) with
[set_line_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_line_width). Finally, we output the cell (the
last parameter to true indicates that the background must be filled).

The method used to print the paragraphs is [multi_cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell). Text is justified by default.
Each time a line reaches the right extremity of the cell or a carriage return character (`\n`) is met,
a line break is issued and a new cell automatically created under the current one.
An automatic break is performed at the location of the nearest space or soft-hyphen (`\u00ad`) character before the right limit.
A soft-hyphen will be replaced by a normal hyphen when triggering a line break, and ignored otherwise.

Two document properties are defined: the title 
([set_title](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_title)) and the author 
([set_author](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_author)). Properties can be viewed by two means.
First is to open the document directly with Acrobat Reader, go to the File menu
and choose the Document Properties option. The second, also available from the
plug-in, is to right-click and select Document Properties.

## Tuto 4 - Multi Columns ##

 This example is a variant of the previous one, showing how to lay the text across multiple columns.

```python
{% include "../tutorial/tuto4.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto4.pdf)

[Jules Verne text](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/20k_c1.txt)

The key difference from the previous tutorial is the use of the 
[accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) and the set_col methods.

Using the [accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) method, once 
the cell crosses the bottom limit of the page, it will check the current column number. If it 
is less than 2 (we chose to divide the page in three columns) it will call the set_col method, 
increasing the column number and altering the position of the next column so the text may continue there.

Once the bottom limit of the third column is reached, the 
[accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) method will reset and go 
back to the first column and trigger a page break.

## Tuto 5 - Creating Tables ##

This tutorial will explain how to create tables easily.

The code will create three different tables to explain what
 can be achieved with some simple adjustments.

```python
{% include "../tutorial/tuto5.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto5.pdf) -
[Countries text](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/countries.txt)

Since a table is just a collection of cells, it is natural to build one
 from them.

The first example is achieved in the most basic way possible: simple framed
 cells, all of the same size and left aligned. The result is rudimentary but
 very quick to obtain.

The second table brings some improvements: each column has its own width,
 titles are centered and figures right aligned. Moreover, horizontal lines have
 been removed. This is done by means of the border parameter of the Cell()
 method, which specifies which sides of the cell must be drawn. Here we want
 the left (L) and right (R) ones. Now only the problem of the horizontal line
 to finish the table remains. There are two possibilities to solv it: check
 for the last line in the loop, in which case we use LRB for the border
 parameter; or, as done here, add the line once the loop is over.

The third table is similar to the second one but uses colors. Fill, text and
 line colors are simply specified. Alternate coloring for rows is obtained by
 using alternatively transparent and filled cells.

## Tuto 6 - Creating links and mixing text styles ##

This tutorial will explain several ways to insert links inside a pdf document,
 as well as adding links to external sources.

 It will also show several ways we can use different text styles,
 (bold, italic, underline) within the same text.

```python
{% include "../tutorial/tuto6.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto6.pdf) -
[fpdf2-logo](https://raw.githubusercontent.com/PyFPDF/fpdf2/master/docs/fpdf2-logo.png)

The new method shown here to print text is
 [write()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write)
. It is very similar to
 [multi_cell()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell)
 , the key differences being:

- The end of line is at the right margin and the next line begins at the left
 margin.
- The current position moves to the end of the text.

The method therefore allows us to write a chunk of text, alter the font style,
 and continue from the exact place we left off.
On the other hand, its main drawback is that we cannot justify the text like
 we do with the
 [multi_cell()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell)
 method.

In the first page of the example, we used
 [write()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write)
 for this purpose. The beginning of the sentence is written in regular style
 text, then using the
 [set_font()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font)
 method, we switched to underline and finished the sentence.

To add an internal link pointing to the second page, we used the
 [add_link()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_link)
 method, which creates a clickable area which we named "link" that directs to
 another place within the document. On the second page, we used
 [set_link()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_link)
 to define the destination area for the link we just created.

To create the external link using an image, we used
 [image()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image)
. The method has the
 option to pass a link as one of its arguments. The link can be both internal
 or external.

As an alternative, another option to change the font style and add links is to
 use the `write_html()` method. It is an html parser, which allows adding text,
 changing font style and adding links using html.
