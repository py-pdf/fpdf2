# Adding Text

There are several ways in fpdf to add text to a PDF document, each of which comes with its own special features and its own set of advantages and disadvantages. You will need to pick the right one for your specific task.

| method | lines | markdown support | HTML support | accepts new current position | details |
| -- | :--: | :--: | :--: | :--: | -- |
| [`.text()`](#text)  | one | no | no | fixed | Inserts a single-line text string with a precise location on the base line of the font.|
| [`.cell()`](#cell)  | one | yes | no | yes | Inserts a single-line text string within the boundaries of a given box, optionally with background and border. |
| [`.multi_cell()`](#multi_cell) | several | yes | no | yes | Inserts a multi-line text string within the boundaries of a given box, optionally with background and border. |
| [`.write()`](#write) | several | no | no | auto | Inserts a multi-line text string within the boundaries of the page margins, starting at the current x/y location (typically the end of the last inserted text). |
| [`.write_html()`](#write_html) | several | no | yes | auto | From [html.py](HTML.html). An extension to `.write()`, with additional parsing of basic HTML tags.

## Typographical Limitations

There are a few advanced typesetting features that fpdf doesn't currently support.

* Automatic ligatures - Some writing systems (eg. most hindic scripts such as Devaganari, Hangul) frequently combine a number of written characters into a single glyph. This would require advanced font analysis capabilities, which aren't currently implemented.
* Contextual forms - In some writing systems (eg. Arabic, Hebrew, Mongolian, etc.), characters may take a different shape, depending on whether they appear at the beginning, in the middle, or at the end of a word, or isolated. Fpdf will always use the same standard shape in those cases.
* Vertical writing - Some writing systems are meant to be written vertically. Doing so is not directly supported. In cases where this just means to stack characters on top of each other (eg. Chinese, Japanese, etc.), client software can implement this by placing each character individuall at the correct location. In cases where the characters are connected with each other (eg. Mongolian), this may be more difficult, if possible at all.

## Text Formatting
For all text insertion methods, the relevant font related properties (eg. font/style and foreground/background color) must be set before invoking them. This includes using:

* [`.set_font()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font)
* [`.set_text_color()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color)
* [`.set_draw_color()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color) - for cell borders
* [`.set_fill_color()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color) - for the background

In addition, some of the methods can optionally use [markdown](TextStyling.html#markdowntrue) or [HTML](HTML.html) markup in the supplied text in order to change the font style (bold/italic/underline) of parts of the output.

## Change in current position
`.cell()` and `.multi_cell()` let you specify where the current position (`.x`/`.y`) should go after the call. This is handled by the parameters `new_x` and `new_y`. Their values are one out of the Enums `fpdf.XPos` and `fpdf.YPos` respectively, which offer the following options:

#### XPos

* `XPos.LEFT`    - left end of the cell
* `XPos.RIGHT`   - right end of the cell
* `XPos.START`   - start of actual text
* `XPos.END`     - end of actual text
* `XPos.WCONT`   - for write() to continue next (slightly left of END)
* `XPos.CENTER`  - center of actual text
* `XPos.LMARGIN` - left page margin (start of printable area)
* `XPos.RMARGIN` - right page margin (end of printable area)

#### YPos

* `YPos.TOP`     - top of the first line
* `YPos.LAST`    - top of the last line (same as TOP for single-line text)
* `YPos.NEXT`    - top of next line (bottom of current text)
* `YPos.TMARGIN` - top page margin (start of printable area)
* `YPos.BMARGIN` - bottom page margin (end of printable area)

## .text()
Prints a single-line character string. In contrast to the other text methods,
the position is given explicitly, and not taken from `.x`/`.y`. The origin is
on the left of the first character, on the baseline. This method allows placing
a string with typographical precision on the page, but it is usually easier to
use the `.cell()`, `.multi_cell()` or `.write()` methods.

[Signature and parameters for .text()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.text)

## .cell()
Prints a cell (rectangular area) with optional borders, background color and
character string. The upper-left corner of the cell corresponds to the current
position. The text can be aligned or centered. After the call, the current
position moves to the selected `new_x`/`new_y` position. It is possible to put a link on the text.
If `markdown=True`, then minimal [markdown](TextStyling.html#markdowntrue)
styling is enabled, to render parts of the text in bold, italics, and/or
underlined.

If automatic page breaking is enabled and the cell goes beyond the limit, a
page break is performed before outputting.

[Signature and parameters for.cell()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.cell)

## .multi_cell()
Allows printing text with line breaks. Those can be automatic (breaking at the
most recent space or soft-hyphen character) as soon as the text reaches the
right border of the cell, or explicit (via the `\\n` character).
As many cells as necessary are stacked, one below the other.
Text can be aligned, centered or justified. The cell block can be framed and
the background painted.

Using `new_x=XPos.RIGHT, new_y=XPos.TOP, maximum height=pdf.font_size` can be
useful to build tables with multiline text in cells.

In normal operation, returns a boolean indicating if page break was triggered.
When `split_only == True`, returns `txt` split into lines in an array (with any markdown markup removed).

[Signature and parameters for.multi_cell()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell)

## .write()
Prints multi-line text between the page margins, starting from the current position.
When the right margin is reached, a line break occurs at the most recent
space or soft-hyphen character, and text continues from the left margin.
A manual break happens any time the \\n character is met,
Upon method exit, the current position is left near the end of the text, ready for the next call to continue without a gap, potentially with a different font or size set. Returns a boolean indicating if page break was triggered.

The primary purpose of this method is to print continuously wrapping text, where different parts may be rendered in different fonts or font sizes. This contrasts eg. with `.multi_cell()`, where a change in font family or size can only become effective on a new line.

[Signature and parameters for.write()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write)


## .write_html()
This method can be accessed by using the class `HTMLMixin` from "[html.py](HTML.html)". It is very similar to `.write()`, but accepts basic HTML formatted text as input. See [html.py](HTML.html) for more details and the supported HTML tags.

Note that when using data from actual web pages, the result may not look exactly as expected, because `.write_html()` prints all whitespace unchanged as it finds them, while webbrowsers rather collapse each run of consequitive whitespace into a single space character.

[Signature and parameters for.write_html()](https://pyfpdf.github.io/fpdf2/fpdf/html.html#fpdf.html.HTMLMixin.write_html)

