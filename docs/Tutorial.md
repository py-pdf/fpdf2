# Tutorial #

Español: [Tutorial-es](Tutorial-es.md)

[TOC]

## Tuto 1 - Minimal Example ##

Let's start with the classic example:

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font('helvetica', 'B', 16)
pdf.cell(40, 10, 'Hello World!')
pdf.output('tuto1.pdf')
```

[Demo](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto1.pdf)

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
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        # Logo
        self.image('logo_pb.png', 10, 8, 33)
        # helvetica bold 15
        self.set_font('helvetica', 'B', 15)
        # Move to the right
        self.cell(80)
        # Title
        self.cell(30, 10, 'Title', 1, 0, 'C')
        # Line break
        self.ln(20)

    # Page footer
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # helvetica italic 8
        self.set_font('helvetica', 'I', 8)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

# Instantiation of inherited class
pdf = PDF()
pdf.alias_nb_pages()
pdf.add_page()
pdf.set_font('Times', '', 12)
for i in range(1, 41):
    pdf.cell(0, 10, 'Printing line number ' + str(i), 0, 1)
pdf.output('tuto2.pdf')
```

[Demo](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto2.pdf)

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
from fpdf import FPDF

title = '20000 Leagues Under the Seas'

class PDF(FPDF):
    def header(self):
        # helvetica bold 15
        self.set_font('helvetica', 'B', 15)
        # Calculate width of title and position
        w = self.get_string_width(title) + 6
        self.set_x((210 - w) / 2)
        # Colors of frame, background and text
        self.set_draw_color(0, 80, 180)
        self.set_fill_color(230, 230, 0)
        self.set_text_color(220, 50, 50)
        # Thickness of frame (1 mm)
        self.set_line_width(1)
        # Title
        self.cell(w, 9, title, 1, 1, 'C', True)
        # Line break
        self.ln(10)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # helvetica italic 8
        self.set_font('helvetica', 'I', 8)
        # Text color in gray
        self.set_text_color(128)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()), 0, 0, 'C')

    def chapter_title(self, num, label):
        # helvetica 12
        self.set_font('helvetica', '', 12)
        # Background color
        self.set_fill_color(200, 220, 255)
        # Title
        self.cell(0, 6, f'Chapter {num} : {label}', 0, 1, 'L', True)
        # Line break
        self.ln(4)

    def chapter_body(self, name):
        # Read text file
        with open(name, 'rb') as fh:
            txt = fh.read().decode('latin-1')
        # Times 12
        self.set_font('Times', '', 12)
        # Output justified text
        self.multi_cell(0, 5, txt)
        # Line break
        self.ln()
        # Mention in italics
        self.set_font('', 'I')
        self.cell(0, 5, '(end of excerpt)')

    def print_chapter(self, num, title, name):
        self.add_page()
        self.chapter_title(num, title)
        self.chapter_body(name)

pdf = PDF()
pdf.set_title(title)
pdf.set_author('Jules Verne')
pdf.print_chapter(1, 'A RUNAWAY REEF', '20k_c1.txt')
pdf.print_chapter(2, 'THE PROS AND CONS', '20k_c2.txt')
pdf.output('tuto3.pdf')
```

[Demo](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto3.pdf)

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

The method used to print the paragraphs is [multi_cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell).
Each time a line reaches the right extremity of the cell or a carriage return
character is met, a line break is issued and a new cell automatically created
under the current one. Text is justified by default.

Two document properties are defined: the title 
([set_title](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_title)) and the author 
([set_author](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_author)). Properties can be viewed by two means.
First is to open the document directly with Acrobat Reader, go to the File menu
and choose the Document Properties option. The second, also available from the
plug-in, is to right-click and select Document Properties.

## Tuto 4 - Multi Columns ##

 This example is a variant of the previous one, showing how to lay the text across multiple columns.

```python
 from fpdf import FPDF


class PDF(FPDF):
    # Current column
    col = 0
    # Ordinate of column start
    y0 = 0

    def header(self):
        # Page header
        self.set_font("helvetica", "B", 15)
        w = self.get_string_width(title) + 6
        self.set_x((210 - w) / 2)
        self.set_draw_color(0, 80, 180)
        self.set_fill_color(230, 230, 0)
        self.set_text_color(220, 50, 50)
        self.set_line_width(1)
        self.cell(w, 9, title, 1, 1, "C", True)
        self.ln(10)
        # Save ordinate
        self.y0 = self.get_y()

    def footer(self):
        # Page footer
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

    def set_col(self, col):
        # Set position at a given column
        self.col = col
        x = 10 + col * 65
        self.set_left_margin(x)
        self.set_x(x)

    @property
    def accept_page_break(self):
        if self.col < 2:
            # Go to next column:
            self.set_col(self.col + 1)
            # Set ordinate to top:
            self.set_y(self.y0)
            # Stay on the same page:
            return False
        # Go back to first column:
        self.set_col(0)
        # Trigger a page break:
        return True

    def chapter_title(self, num, label):
        # Title
        self.set_font("helvetica", "", 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 6, f"Chapter {num} : {label}", 0, 1, "L", True)
        self.ln(4)
        # Save ordinate
        self.y0 = self.get_y()

    def chapter_body(self, name):
        # Read text file
        with open(name, "rb") as fh:
            txt = fh.read().decode("latin-1")
        # Font
        self.set_font("Times", size=12)
        # Output text in a 6 cm width column
        self.multi_cell(60, 5, txt)
        self.ln()
        # Mention
        self.set_font(style="I")
        self.cell(0, 5, "(end of excerpt)")
        # Go back to first column
        self.set_col(0)

    def print_chapter(self, num, title, name):
        # Add chapter
        self.add_page()
        self.chapter_title(num, title)
        self.chapter_body(name)


pdf = PDF()
title = "20000 Leagues Under the Seas"
pdf.set_title(title)
pdf.set_author("Jules Verne")
pdf.print_chapter(1, "A RUNAWAY REEF", "20k_c1.txt")
pdf.print_chapter(2, "THE PROS AND CONS", "20k_c1.txt")
pdf.output("tuto4.pdf")
```

[Demo](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto4.pdf)

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
