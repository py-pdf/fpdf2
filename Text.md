# Adding Text

There are several ways in fpdf to add text to a PDF document, each of which comes with its own special features and its own set of advantages and disadvantages. You will need to pick the right one for your specific task.

| method | lines | markdown | HTML | positioning | details |
| -- | :--: | :--: | :--: | :--: | -- |
| [`.text()`](#text)  | one | no | no | fixed | Inserts a single-line text string with a precise location on the base line of the font.|
| [`.cell()`](#cell)  | one | yes | no | yes | Inserts a single-line text string within the boundaries of a given box, optionally with background and border. |
| [`.multi_cell()`](#multi_cell) | several | yes | no | yes | Inserts a multi-line text string within the boundaries of a given box, optionally with background and border. |
| [`.write()`](#write) | several | no | no | auto | Inserts a multi-line text string within the boundaries of the page margins, starting at the current x/y location (typically the end of the last inserted text). |
| [`.write_html()`](#write_html) | several | no | yes | auto | From [html.py](HTML.html). An extension to `.write()`, with additional parsing of basic HTML tags.

## Text Formatting
For all text insertion methods, the relevant font related properties (eg. font/style and foreground/background color) must be set before invoking them. This includes using:
* [`.set_font()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font)
* [`.set_text_color()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color)
* [`.set_draw_color()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color) - for cell borders
* [`.set_fill_color()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color) - for the background

In addition, some of the methods can optionally use [markdown](TextStyling.html#markdowntrue) or [HTML](HTML.html) markup in the supplied text in order to change the font style (bold/italic/underline) of parts of the output.

## Change in current position
`.cell()` and `.multi_cell()` let you specify where the current position (`.x`/`.y`) should go after the call. This is handled by the parameters `new_x` and `new_y`. Their values are one out of the Enums `.XPos` and `.YPos` respectively, which offer the following options:

#### .XPos
* XPos.LEFT    - left end of the cell
* XPos.RIGHT   - right end of the cell
* XPos.START   - start of actual text
* XPos.END     - end of actual text
* XPos.WCONT   - for write() to continue next (slightly left of END)
* XPos.CENTER  - center of actual text
* XPos.LMARGIN - left page margin (start of printable area)
* XPos.RMARGIN - right page margin (end of printable area)

#### .YPos
* YPos.TOP     - top of the first line
* YPos.LAST    - top of the last line (same as TOP for single-line text)
* YPos.NEXT    - top of next line (bottom of current text)
* YPos.TMARGIN - top page margin (start of printable area)
* YPos.BMARGIN - bottom page margin (end of printable area)


## .text()
Prints a single-line character string. In contrast to the other text methods,
the position is given explicitly, and not taken from `.x`/`.y`. The origin is
on the left of the first character, on the baseline. This method allows placing
a string with typographical precision on the page, but it is usually easier to
use the `.cell()`, `.multi_cell()` or `.write()` methods.

#### text(x, y, txt='')
* __x__ (float) - The horizontal component origin position
* __y__ (float) - The vertical component origin position
* __txt__ (str) - the text string to print


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

#### cell(w=None, h=None, txt='', border=0, new_x=XPos.RIGHT, new_y=YPos.TOP, align='', fill=False, link='', center=False, markdown=False)

* __w__ (float) - Cell width. If `None`, fit text width. If 0, the cell extends up to the right margin.
* __h__ (float) - Cell height. If `None`, use the the current font size.
* __txt__ (str) - String to print.
* __border__ - Indicates if borders must be drawn around the cell. The value can be either a number
	* 0: no border
	* 1: full frame

	or a string containing some or all of the following characters (in any order):
	* "L": left
	* "T": top
	* "R": right
	* "B": bottom

* __new_x__ (Enum XPos): New current position in x after the call.
* __new_y__ (Enum YPos): New current position in y after the call.
* align (str) - Allows to center or align the text inside the cell. Possible values are:
	* "L" or empty string: left align
	* "C": center 
	* "R": right align
* __fill__ (bool) - Indicates if the cell background must be painted (True) or transparent (False).
* __link__ (str) - optional link to add on the cell, internal (identifier returned by `.add_link()`) or external URL.
* __markdown__ (bool) - enable minimal markdown-like markup.


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


#### multi_cell(w, h=None, txt="", border=0, align="J", fill=False, split_only=False, link="", new_x=XPos.RIGHT, new_y=YPos.NEXT, max_line_height=None, markdown=False, print_sh=False) -> Bool or List

* __w__ (float): cell width. If 0, the cell extends to the right margin of the page.
* __h__ (float): cell height. If None, use the current font size.
* __txt__ (str): string to print.
* __border__: Indicates if borders must be drawn around the cell. The value can be either a number
	* 0: no border
	* 1: full frame

	or a string containing some or all of the following characters (in any order):
	* "L": left
	* "T": top
	* "R": right
	* "B": bottom
* __align__ (str): Allows to center or align the text inside the cell. Possible values are:
	* "L" or empty string: left align
	* "C": center 
	* "R": right align
	* "J": justify
* __fill__ (bool): Indicates if the cell background must be painted (`True`)
	or transparent (`False`).
* __split_only__ (bool): if `True`, don't output anything, only perform
	word-wrapping and return the resulting multi-lines array of strings.
* __link__ (str): optional link to add on the cell, internal
	(identifier returned by `add_link`) or external URL.
* __new_x__ (Enum XPos): New current position in x after the call.
* __new_y__ (Enum YPos): New current position in y after the call.
* __max_line_height__ (float): optional maximum height of each sub-cell generated
* __markdown__ (bool): enable minimal markdown-like markup to render part
	of text as bold / italics / underlined.
* __print_sh__ (bool): Treat a soft-hyphen (\\u00ad) as a normal printable
	character, instead of a line breaking opportunity.


## .write()
Prints multi-line text between the page margins, starting from the current position.
When the right margin is reached, a line break occurs at the most recent
space or soft-hyphen character, and text continues from the left margin.
A manual break happens any time the \\n character is met,
Upon method exit, the current position is left near the end of the text, ready for the next call to continue without a gap, potentially with a different font or size set. Returns a boolean indicating if page break was triggered.

The primary purpose of this method is to print continuously wrapping text, where different parts may be rendered in different fonts or font sizes. This contrasts eg. with `.multi_cell()`, where a change in font family or size can only become effective on a new line.


#### write(h: float = None, txt: str = "", link: str = "", print_sh: bool = False) -> bool

* __h__ (float): line height. If None, use the current font size.
* __txt__ (str): text content
* __link__ (str): optional link to add on the text, internal
	(identifier returned by `add_link`) or external URL.
* __print_sh__ (bool): Treat a soft-hyphen (\\u00ad) as a normal printable
	character, instead of a line breaking opportunity.


## .write_html()
This method can be accessed by using the class `HTMLMixin` from "[html.py](HTML.html)". It is very similar to `.write()`, but accepts basic HTML formatted text as input. See [html.py](HTML.html) for more details and the supported HTML tags.

Note that when using data from actual web pages, the result may not look exactly as expected, because `.write_html()` prints all whitespace unchanged as it finds them, while webbrowsers rather collapse each run of consequitive whitespace into a single space character.

#### write_html(text, image_map=None, li_tag_indent=5, table_line_separators=False, ul_bullet_char=BULLET_WIN1252, heading_sizes=None)

* __text__ (str): the HTML text to be processed.
* __image_map__ (function): an optional one-argument function that maps
	img tag "src" property to new image URLs.
* __li_tag_indent__ (float): Indentation of \<li\> elements in document units.
* __table_line_separators__ (bool): if True, enable horizontal line separators between table rows.
* __ul_bullet_char__ (str): bullet character for \<ul\> elements.
* __heading_sizes__ (dict): a dictionary of heading types ("h1" to "h#") as keys and the respective font sizes in points as values. If None, use the builtin defaults.


