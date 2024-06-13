# Adding Text

There are several ways in fpdf to add text to a PDF document, each of which comes with its own special features and its own set of advantages and disadvantages. You will need to pick the right one for your specific task.

## Simple Text Methods

| method | lines | markdown support | HTML support | accepts new current position | details                                                                                                                                                         |
| -- | :--: | :--: | :--: | :--: |-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`.text()`](#text)  | one | no | no | fixed | Inserts a single-line text string with a precise location on the base line of the font.                                                                         |
| [`.cell()`](#cell)  | one | yes | no | yes | Inserts a single-line text string within the boundaries of a given box, optionally with background and border.                                                  |
| [`.multi_cell()`](#multi_cell) | several | yes | no | yes | Inserts a multi-line text string within the boundaries of a given box, optionally with background, border and padding.                                          |
| [`.write()`](#write) | several | no | no | auto | Inserts a multi-line text string within the boundaries of the page margins, starting at the current x/y location (typically the end of the last inserted text). |
| [`.write_html()`](#write_html) | several | no | yes | auto | An extension to `.write()`, with additional parsing of basic HTML tags.                                                                                         

## Flowable Text Regions

Text regions allow to insert flowing text into a predefined region on the page. It is possible to change the formatting and even the font within paragraphs, which will still be aligned as one text block. 
The currently implemented type of text regions is [text_columns()](TextColumns.html), which defines one or several columns that can be filled sequentially or height-balanced.

## Typography and Language Specific Concepts 
### Supported Features
With supporting Unicode fonts, fpdf2 should handle the following text shaping features correctly. More details can be found in [TextShaping](TextShaping.html).
* Automatic ligatures / glyph substitution - Some writing systems (eg. most Indic scripts such as Devaganari, Tamil, Kannada) frequently combine a number of written characters into a single glyph. In latin script, "ff", "fi", "ft", "st" and others are often combined. In programming fonts "<=", "++" "!=" etc. may be combined into more compact representations.
* Special diacritics that use separate code points (eg. in Diné Bizaad, Hebrew) will be placed in the correct location relative to their base character.
* Kerning, where the spacing between characters varies depending on their combination (eg. moving the succeeding lowercase character closer to an uppercase "T".
* Left-to-right and right-to-left text formatting (the latter most prominently in Arabic and Hebrew).

### Limitations
There are a few advanced typesetting features that fpdf doesn't currently support.
* Contextual forms - In some writing systems (eg. Arabic, Mongolian, etc.), characters may take a different shape, depending on whether they appear at the beginning, in the middle, or at the end of a word, or isolated. Fpdf will always use the same standard shape in those cases.
* Vertical writing - Some writing systems are meant to be written vertically. Doing so is not directly supported. In cases where this just means to stack characters on top of each other (eg. Chinese, Japanese, etc.), client software can implement this by placing each character individuall at the correct location. In cases where the characters are connected with each other (eg. Mongolian), this may be more difficult, if possible at all.

### Character or Word Based Line Wrapping
By default, `multi_cell()` and `write()` will wrap lines based on words, using space characters and soft hyphens as separators.
Non-breaking spaces (\U00a0) do not trigger a word wrap, but are otherwise treated exactly as a normal space character.
For languages like Chinese and Japanese, that don't usually separate their words, character based wrapping is more appropriate.
In such a case, the argument `wrapmode="CHAR"` can be used (the default is "WORD"), and each line will get broken right before the
character that doesn't fit anymore.


## Text Formatting
For all text insertion methods, the relevant font related properties (eg. font/style and foreground/background color) must be set before invoking them. This includes using:

* [`.set_font()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font)
* [`.set_text_color()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color)
* [`.set_draw_color()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color) - for cell borders
* [`.set_fill_color()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color) - for the background

All three `set_*_colors()` methods accept either a single greyscale value, 3 valeurs as RGB components, a single `#abc` or `#abcdef` hexadecimal color string, or an instance of [`fpdf.drawing.DeviceCMYK`](https://py-pdf.github.io/fpdf2/fpdf/drawing.html#fpdf.drawing.DeviceCMYK), [`fpdf.drawing.DeviceRGB`](https://py-pdf.github.io/fpdf2/fpdf/drawing.html#fpdf.drawing.DeviceRGB) or [`fpdf.drawing.DeviceGray`](https://py-pdf.github.io/fpdf2/fpdf/drawing.html#fpdf.drawing.DeviceGray).
You can even use [named web colors](https://en.wikipedia.org/wiki/Web_colors#HTML_color_names) by using [`html.color_as_decimal()`](fpdf/html.html#fpdf.html.color_as_decimal).

In addition, some of the methods can optionally use [markdown](TextStyling.md#markdowntrue) or [HTML](HTML.md) markup in the supplied text in order to change the font style (bold/italic/underline) of parts of the output.

## Change in current position
`.cell()` and `.multi_cell()` let you specify where the current position (`.x`/`.y`) should go after the call.
This is handled by the parameters `new_x` and `new_y`.
Their values must one of the following enums values or an equivalent string:

* [`XPos`](fpdf/enums.html#fpdf.enums.XPos)
* [`YPos`](fpdf/enums.html#fpdf.enums.YPos)

## .text()
Prints a single-line character string. In contrast to the other text methods,
the position is given explicitly, and not taken from `.x`/`.y`. The origin is
on the left of the first character, on the baseline. This method allows placing
a string with typographical precision on the page, but it is usually easier to
use the `.cell()`, `.multi_cell()` or `.write()` methods.

[Signature and parameters for .text()](fpdf/fpdf.html#fpdf.fpdf.FPDF.text)

## .cell()
Prints a cell (rectangular area) with optional borders, background color and
character string. The upper-left corner of the cell corresponds to the current
position. The text can be aligned or centered. After the call, the current
position moves to the selected `new_x`/`new_y` position. It is possible to put a link on the text.
If `markdown=True`, then minimal [markdown](TextStyling.md#markdowntrue)
styling is enabled, to render parts of the text in bold, italics, and/or
underlined.

If automatic page breaking is enabled and the cell goes beyond the limit, a
page break is performed before outputting.

[Signature and parameters for.cell()](fpdf/fpdf.html#fpdf.fpdf.FPDF.cell)

## .multi_cell()
Allows printing text with word or character based line breaks. Those can be automatic
(breaking at the most recent space or soft-hyphen character) as soon as the text
reaches the right border of the cell, or explicit (via the `\\n` character).
As many cells as necessary are stacked, one below the other.
Text can be aligned, centered or justified. The cell block can be framed and
the background painted. Padding between text and the cell edge can be specified in the same way as for tables.

Using `new_x="RIGHT", new_y="TOP", maximum height=pdf.font_size` can be
useful to build tables with multiline text in cells.

In normal operation, returns a boolean indicating if page break was triggered. The return value can be altered by specifying the `output` parameter.

[Signature and parameters for.multi_cell()](fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell)

## .write()
Prints multi-line text between the page margins, starting from the current position.
When the right margin is reached, a line break occurs at the most recent
space or soft-hyphen character (in word wrap mode) or at the current position (in
character break mode), and text continues from the left margin.
A manual break happens any time the \\n character is met.
Upon method exit, the current position is left near the end of the text, ready for
the next call to continue without a gap, potentially with a different font or size set.
Returns a boolean indicating if page break was triggered.

The primary purpose of this method is to print continuously wrapping text, where different parts may be rendered in different fonts or font sizes. This contrasts eg. with `.multi_cell()`, where a change in font family or size can only become effective on a new line.

[Signature and parameters for.write()](fpdf/fpdf.html#fpdf.fpdf.FPDF.write)


## .write_html()
This method is very similar to `.write()`, but accepts basic HTML formatted text as input. See [html.py](HTML.md) for more details and the supported HTML tags.

Note that when using data from actual web pages, the result may not look exactly as expected, because `.write_html()` prints all whitespace unchanged as it finds them, while webbrowsers rather collapse each run of consequitive whitespace into a single space character.

[Signature and parameters for .write_html()](fpdf/fpdf.html#fpdf.fpdf.FPDF.write_html)
