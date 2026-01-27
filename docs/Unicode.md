# Fonts and Unicode #

Besides the limited set of latin fonts built into the PDF format, `fpdf2` offers full support for using and embedding Unicode (TrueType "ttf" and OpenType "otf") fonts. To keep the output file size small, it only embeds the subset of each font that is actually used in the document. This part of the code has been completely rewritten since the fork from PyFPDF. It uses the [fonttools](https://fonttools.readthedocs.io/en/latest/) library for parsing the font data, and [harfbuzz](https://harfbuzz.github.io/) (via [uharfbuzz](https://github.com/harfbuzz/uharfbuzz)) for [text shaping](TextShaping.md).

To make use of that functionality, you have to install at least one Unicode font, either in the system font folder or in some other location accessible to your program.
For professional work, many designers prefer commercial fonts, suitable to their specific needs. There are also many sources of free TTF fonts that can be downloaded online and used free of cost (some of them may have restrictions on commercial redistribution, such as server installations or including them in a software project).

  * [Font Library](https://fontlibrary.org/) - A collection of fonts for many languages with an open source type license.

  * [Google Fonts](https://fonts.google.com/) - A collection of free to use fonts for many languages.

  * [Microsoft Font Library](https://learn.microsoft.com/en-gb/typography/font-list/) - A large collection of fonts that are free to use.

  * [GitHub: Fonts](https://github.com/topics/fonts) - Links to public repositories of open source font projects as well as font related software projects.

  * [GNU FreeFont](http://www.gnu.org/software/freefont/) family: FreeSans,
FreeSerif, FreeMono

To use a Unicode font in your program, use the [`add_font()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_font), and then the  [`set_font()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font) method calls.

### Web fonts (WOFF and WOFF2) ###

WOFF and WOFF2 are web-optimized, compressed containers for TrueType and OpenType fonts, designed to reduce download size for browsers. `fpdf2` supports these formats by decompressing them before embedding the resulting font data into the generated PDF.


### Built-in Fonts vs. Unicode Fonts ###

The PDF file format knows a small number of "standard" fonts, namely **Courier**, **Helvetica**, **Times**, **Symbol**, and **ZapfDingbats**.
The first three are available in regular, bold, italic, and bold-italic versions.
This gives us a set of fonts known as "14 Standard PDF fonts".
Any PDF processor (eg. a viewer) must provide those fonts for display.
To use them, you don't need to call `.add_font()`, but only `.set_font()`.

![PDF builtin fonts](core_fonts.png)

( script used to generate this: [tutorial/core_fonts.py](https://github.com/py-pdf/fpdf2/blob/master/tutorial/core_fonts.py) )

While that may seem convenient, there's a big drawback. Those fonts only support latin characters, or a set of special characters for the last two. If you try to render any Unicode character outside of those ranges, then you'll get an error like: "`Character "θ" at index 13 in text is outside the range of characters supported by the font used: "courier". Please consider using a Unicode font.`".
So if you want to create documents with any characters other than those common in English and a small number of european languages, then you need to add a Unicode font containing the respective glyph as described in this document.

Note that even if you have a font eg. named "Courier" installed as a system font on your computer, by default this will not be used. You'll have to explicitly call eg. `.add_font("Courier2", fname=r"C:\Windows\Fonts\cour.ttf")` to make it available. If the name is really the same (ignoring case), then you'll have to use a suitable variation, since trying to overwrite one of the "standard" names with `.add_font()` will result in an error.


### Adding and Using Fonts ###

Before using a Unicode font, you need to load it from a font file. Usually you'll have call `add_font()` for each style of the same font family you want to use. The styles that fpdf2 understands are:

* Regular: ""
* Bold: "b"
* Italic/Oblique: "i"
* Bold-Italic: "bi"

Note that we use the same family name for each of them, but load them from different files. Only when a font has variants (eg. "narrow"), or there are more styles than the four standard ones (eg. "black" or "extra light"), you'll have to add those with a different family name. If the font files are not located in the current directory, you'll have to provide a file name with a relative or absolute path. If the font is not found elsewhere, then fpdf2 will look for it in a subdirectory named "font".

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
# Different styles of the same font family.
pdf.add_font("dejavu-sans", style="", fname="DejaVuSans.ttf")
pdf.add_font("dejavu-sans", style="b", fname="DejaVuSans-Bold.ttf")
pdf.add_font("dejavu-sans", style="i", fname="DejaVuSans-Oblique.ttf")
pdf.add_font("dejavu-sans", style="bi", fname="DejaVuSans-BoldOblique.ttf")
# Different type of the same font design.
pdf.add_font("dejavu-sans-narrow", style="", fname="DejaVuSansCondensed.ttf")
pdf.add_font("dejavu-sans-narrow", style="i", fname="DejaVuSansCondensed-Oblique.ttf")
```

To actually use the loaded font, or to use one of the standard built-in fonts, you'll have to set the current font before calling any text generating method.
`.set_font()` uses the same combinations of family name and style as arguments, plus the font size in typographic points.
In addition to the previously mentioned styles, the letter `u` may be included for creating underlined text,
and `s` for creating strikethrough text.
If the family or size are omitted, the already set values will be retained.
If the style is omitted, it defaults to regular.

```python
# Set and use first family in regular style.
pdf.set_font(family="dejavu-sans", style="", size=12)
pdf.cell(text="Hello")
# Set and use the same family in bold style.
pdf.set_font(style="b", size=18)  # still uses the same dejavu-sans font family.
pdf.cell(text="Fat World")
# Set and use a variant in italic and underlined.
pdf.set_font(family="dejavu-sans-narrow", style="iu", size=12)
pdf.cell(text="lean on me")
```

![add-unicode-font](add-unicode-font.png)


### Note on non-latin languages ###

Many non-latin writing systems have complex ways to combine characters, ligatures, and possibly multiple diacritic symbols together, change the shape of characters depending on its location in a word, or use a different writing direction. A small number of examples are:

* Hebrew - right-to-left, placement of diacritics
* Arabic - right-to-left, contextual shapes
* Thai - stacked diacritics
* Devanagari (and other indic scripts) - multi-character ligatures, reordering

To make sure those scripts to be rendered correctly, [text shaping](TextShaping.md) must be enabled with `.set_text_shaping(True)`.


### Right-to-Left scripts ###

When [text shaping](TextShaping.md) is enabled, `fpdf2` will apply the [Unicode Bidirectional Algorithm](https://www.unicode.org/reports/tr9/) to render correctly any text, including bidirectional (mix of right-to-left and left-to-right scripts).

## Example ##

This example uses several free fonts to display some Unicode strings. Be sure to
install the fonts in the `font` directory first.

```python
#!/usr/bin/env python
# -*- coding: utf8 -*-

from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_text_shaping(True)

# Add a DejaVu Unicode font (uses UTF-8)
# Supports more than 200 languages. For a coverage status see:
# http://dejavu.svn.sourceforge.net/viewvc/dejavu/trunk/dejavu-fonts/langcover.txt
pdf.add_font(fname='DejaVuSansCondensed.ttf')
pdf.set_font('DejaVuSansCondensed', size=14)

text = u"""
English: Hello World
Greek: Γειά σου κόσμος
Polish: Witaj świecie
Portuguese: Olá mundo
Russian: Здравствуй, Мир
Vietnamese: Xin chào thế giới
Arabic: مرحبا العالم
Hebrew: שלום עולם
"""

for txt in text.split('\n'):
    pdf.write(8, txt)
    pdf.ln(8)

# Add a Indic Unicode font (uses UTF-8)
# Supports: Bengali, Devanagari, Gujarati, 
#           Gurmukhi (including the variants for Punjabi) 
#           Kannada, Malayalam, Oriya, Tamil, Telugu, Tibetan
pdf.add_font(fname='gargi.ttf')
pdf.set_font('gargi', size=14)
pdf.write(8, u'Hindi: नमस्ते दुनिया')
pdf.ln(20)

# Add a AR PL New Sung Unicode font (uses UTF-8)
# The Open Source Chinese Font (also supports other east Asian languages)
pdf.add_font(fname='fireflysung.ttf')
pdf.set_font('fireflysung', size=14)
pdf.write(8, u'Chinese: 你好世界\n')
pdf.write(8, u'Japanese: こんにちは世界\n')
pdf.ln(10)

# Add a Alee Unicode font (uses UTF-8)
# General purpose Hangul truetype fonts that contain Korean syllable 
# and Latin9 (iso8859-15) characters.
pdf.add_font(fname='Eunjin.ttf')
pdf.set_font('Eunjin', size=14)
pdf.write(8, u'Korean: 안녕하세요')
pdf.ln(20)

# Add a Fonts-TLWG (formerly ThaiFonts-Scalable) (uses UTF-8)
pdf.add_font(fname='Waree.ttf')
pdf.set_font('Waree', size=14)
pdf.write(8, u'Thai: สวัสดีชาวโลก')
pdf.ln(20)

# Select a standard font (uses windows-1252)
pdf.set_font('helvetica', size=14)
pdf.ln(10)
pdf.write(5, 'This is standard built-in font')

pdf.output("unicode.pdf")
```


View the result here: 
[unicode.pdf](https://github.com/py-pdf/fpdf2/raw/master/tutorial/unicode.pdf)

## Free Font Pack ##

For your convenience, the author of the original PyFPDF has collected 96 TTF files in an optional 
["Free Unicode TrueType Font Pack for FPDF"](https://github.com/reingart/pyfpdf/releases/download/binary/fpdf_unicode_font_pack.zip), with useful fonts commonly distributed with GNU/Linux operating systems. Note that this collection is from 2015, so it will not contain any newer fonts or possible updates.


## Fallback fonts ##

_New in [:octicons-tag-24: 2.7.0](https://github.com/py-pdf/fpdf2/blob/master/CHANGELOG.md)_

The method [`set_fallback_fonts()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fallback_fonts) allows you to specify a list of fonts to be used if any character is not available on the font currently set. When a character doesn’t exist on the current font, `fpdf2` will look if it’s available on the fallback fonts, on the same order the list was provided.

Common scenarios are use of special characters like emojis within your text, greek characters in formulas or citations mixing different languages.

Example:
```python
import fpdf

pdf = fpdf.FPDF()
pdf.add_page()
pdf.add_font(fname="Roboto.ttf")
# twitter emoji font: https://github.com/13rac1/twemoji-color-font/releases
pdf.add_font(fname="TwitterEmoji.ttf")
pdf.set_font("Roboto", size=15)
pdf.set_fallback_fonts(["TwitterEmoji"])
pdf.write(text="text with an emoji 🌭")
pdf.output("text_with_emoji.pdf")
```

When a glyph cannot be rendered uing the current font,
`fpdf2` will look for a fallback font matching the current character emphasis (bold/italics).
By default, if it does not find such matching font, the character will not be rendered using any fallback font. This behaviour can be relaxed by passing `exact_match=False` to [`set_fallback_fonts()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fallback_fonts).

Moreover, for more control over font fallback election logic,
the [`get_fallback_font()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.get_fallback_font) can be overridden.
An example of this can be found in [test/fonts/test_font_fallback.py](https://github.com/py-pdf/fpdf2/blob/master/test/fonts/test_font_fallback.py).


## Unicode range limits ##

_New in [:octicons-tag-24: 2.8.5](https://github.com/py-pdf/fpdf2/blob/master/CHANGELOG.md)_

The `unicode_range` parameter in [`add_font()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_font) allows you to restrict which Unicode characters a font will handle, similar to CSS `@font-face` unicode-range rules. This gives you fine-grained control over font priority on a per-character basis.

This is particularly useful when you want fallback fonts to take priority for specific character ranges, even when the main font technically supports those characters. A common scenario is preferring colorful emoji fonts over monochrome glyphs that exist in regular fonts.

Example:

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()

# Main font for text
pdf.add_font(family="DejaVu", fname="DejaVuSans.ttf", unicode_range="U+0020-007E")

# Emoji font restricted to emoticons range only
pdf.add_font(
    family="NotoEmoji",
    fname="colrv1-NotoColorEmoji.ttf",
    unicode_range="U+1F600-1F64F",  # Emoticons
)

pdf.set_font("DejaVu", size=24)
pdf.set_fallback_fonts(["NotoEmoji"])

# Emojis in the specified range render from NotoEmoji (colorful)
pdf.write(text="Hello World! 😀 😊 😎")
pdf.output("emoji_with_unicode_range.pdf")
```

![unicode_range_color_emojis](unicode_range_color_emojis.png)

Supported Formats for `unicode_range` param

```python
# CSS-style string with comma-separated ranges
pdf.add_font(fname="font.ttf", unicode_range="U+1F600-1F64F, U+2600-26FF, U+2615")

# List of strings
pdf.add_font(fname="font.ttf", unicode_range=["U+1F600-1F64F", "U+2600", "U+26FF"])

# List of tuples (start, end)
pdf.add_font(fname="font.ttf", unicode_range=[(0x1F600, 0x1F64F), (0x2600, 0x26FF)])

# List of integers (individual codepoints)
pdf.add_font(fname="font.ttf", unicode_range=[0x1F600, 0x2600, 128512])
```

When you specify a unicode_range, the font's internal character map (cmap) is trimmed to only include codepoints within the specified ranges. This ensures that:

- The font will only be used for characters in its allowed ranges
- Fallback fonts can take priority for characters outside those ranges
- You avoid unwanted "fallback pollution" from fonts with poor-quality glyphs

For more information on fallback fonts, see the [Fallback fonts](#fallback-fonts) section.


## Variable Fonts ##

_New in [:octicons-tag-24: 2.8.5](https://github.com/py-pdf/fpdf2/blob/master/CHANGELOG.md)_

A variable font allows users to use a single font file containing many
variations of a typeface, such as weight, width, optical size, and slant. Each such variable which modifies the typeface is called an axis.
These variables have specific tags which are used to specify their values, such as `"wdth"` for modifying width,
and `"wght"` for modifying weight. For a full list
of tags, please check the documentation of your variable font.

The `variations` parameter in [add_font](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_font) allows you to specify the value
of one or more axes, thus creating a static font from the variable font.

The following examples assume that the provided font is a variable font.

```python
# Specify width and weight in regular style.
pdf.add_font(
    "Roboto Variable", "", "Roboto-Variable.ttf", variations={"wdth": 75, "wght": 300}
)

# Specify weight for bold style.
pdf.add_font("Roboto Variable", "B", "Roboto-Variable.ttf", variations={"wght": 600})

```

The above examples provide the axes dictionary to specify
the styles. If an axis is not mentioned, the default width will be used, and the axis will be dropped as shown below.

```python
# Creating an italic version of the variable font.
# If an axis is set to None, or if the axis is unspecified,
# it will not be variable in the created font.
pdf.add_font(
    "Roboto Variable",
    "B",
    "Roboto-Variable.ttf",
    variations={"wght": 800, "wdth": None},
)
```

It is also possible to specify more than 1 style in the `variations` dictionary.
If a separate axes dictionary is specified for each style, then the `style` parameter
is ignored as shown below.

```python
pdf.add_font(
    "Roboto Variable",
    style="", # ignored
    fname="Roboto-Variable.ttf",
    variations={"": {"wght": 300}, "B": {"wght": 700}},
)
```
A `TypeError` will be raised if `variations` is not a dictionary, and
an `AttributeError` will be raised if `variations` is used but the font is **not** a variable font.


## Color Font Palette Selection ##

_New in [:octicons-tag-24: 2.8.5](https://github.com/py-pdf/fpdf2/blob/master/CHANGELOG.md)_

Some color fonts (COLRv0, COLRv1, CBDT, SBIX, SVG) contain multiple predefined color palettes.
The `palette` parameter in [`add_font()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_font) allows you to select which palette to use when rendering the font.

This is useful when you want to use different color schemes from the same font file without having to embed the font multiple times.

Example:

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()

# Add the same color font with different palettes using different family names
pdf.add_font(
    family="Nabla-Default",
    fname="Nabla-Regular-COLRv1.ttf",
    palette=0  # Use palette 0 (default)
)

pdf.add_font(
    family="Nabla-Blue",
    fname="Nabla-Regular-COLRv1.ttf",
    palette=1  # Use palette 1
)

pdf.add_font(
    family="Nabla-Grey",
    fname="Nabla-Regular-COLRv1.ttf",
    palette=2  # Use palette 2
)

# Use the fonts with different palettes
pdf.set_font("Nabla-Default", size=24)
pdf.cell(text="Text with Palette 0", new_x="lmargin", new_y="next")

pdf.set_font("Nabla-Blue", size=24)
pdf.cell(text="Text with Palette 1", new_x="lmargin", new_y="next")

pdf.set_font("Nabla-Grey", size=24)
pdf.cell(text="Text with Palette 2", new_x="lmargin", new_y="next")

pdf.output("color_font_palettes.pdf")
```

If you specify a palette index that is out of range, `fpdf2` will log a warning and fall back to palette 0.
You can check the number of available palettes in your color font's documentation or by inspecting the font file.
