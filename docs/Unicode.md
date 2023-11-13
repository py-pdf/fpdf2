# Fonts and Unicode #

Besides the limited set of latin fonts built into the PDF format, Fpdf2 offers full support for using and embedding Unicode (TrueType "ttf" and OpenType "otf") fonts. To keep the output file size small, it only embeds the subset of each font that is actually used in the document. This part of the code has been completely rewritten since the fork from PyFPDF. It uses the [fonttools](https://fonttools.readthedocs.io/en/latest/) library for parsing the font data, and [harfbuzz](https://harfbuzz.github.io/) (via [uharfbuzz](https://github.com/harfbuzz/uharfbuzz)) for [text shaping](TextShaping.html).

To make use of that functionality, you have to install at least one Unicode font, either in the system font folder or in some other location accessible to your program.
For professional work, many designers prefer commercial fonts, suitable to their specific needs. There are also many sources of free TTF fonts that can be downloaded online and used free of cost (some of them may have restrictions on commercial redistribution, such as server installations or including them in a software project).

  * [Font Library](https://fontlibrary.org/) - A collection of fonts for many languates with an open source type license.

  * [Google Fonts](https://fonts.google.com/) - A collection of free to use fonts for many languages.

  * [Microsoft Font Library](https://learn.microsoft.com/en-gb/typography/font-list/) - A large collection of fonts that are free to use.

  * [GitHub: Fonts](https://github.com/topics/fonts) - Links to public repositories of open source font projects as well as font related software projects.

  * [GNU FreeFont](http://www.gnu.org/software/freefont/) family: FreeSans,
FreeSerif, FreeMono

To use a Unicode font in your program, use the [`add_font()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.add_font), and then the  [`set_font()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font) method calls.


### Built-in Fonts vs. Unicode Fonts ###

The PDF file format knows a small number of "standard" fonts, namely "courier", "helvetica", "times", "symbol", and "zapfdingbats". The first three are available in regular, bold, italic, and bold-italic versions. Any PDF processor (eg. a viewer) must provide those fonts for display. To use them, you don't need to call `.add_font()`, but only `.set_font()`.

While that may seem convenient, there's a big drawback. Those fonts only support latin characters, or a set of special characters for the last two. If you try to render any Unicode character outside of those ranges, then you'll get an error like: "`Character "θ" at index 13 in text is outside the range of characters supported by the font used: "courier". Please consider using a Unicode font.`".
So if you want to create documents with any characters other than those common in English and a small number of european languages, then you need to add a Unicode font containing the respective glyph as described in this document.

Note that even if you have a font eg. named "Courier" installed as a system font on your computer, by default this will not be used. You'll have to explicitly call eg. `.add_font("courier2", "", r"C:\Windows\Fonts\cour.ttf")` to make it available. If the name is really the same (ignoring case), then you'll have to use a suitable variation, since trying to overwrite one of the "standard" names with `.add_font()` will result in an error.


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

To actually use the loaded font, or to use one of the standard built-in fonts, you'll have to set the current font before calling any text generating method. `.set_font()` uses the same combinations of family name and style as arguments, plus the font size in typographic points. In addition to the previously mentioned styles, the letter "u" may be included for creating underlined text. If the family or size are omitted, the already set values will be retained. If the style is omitted, it defaults to regular.

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

To make sure those scripts to be rendered correctly, [text shaping](TextShaping.html) must be enabled with `.set_text_shaping(True)`. 


### Right-to-Left & Arabic Script workaround ###

Arabic, Hebrew and other scripts written right-to-left (RTL) should work correctly when text is added that only contains one script at a time. As of release 2.7.6, more complete support for mixing RTL and LTR text is being worked on.
In the mean time, there is a temporary solution for Arabic and other RTL scripts using two additional libraries `python-bidi` and `arabic-reshaper`. It works for most languages; only a few (rare) Arabic characters aren't supported. Using it on other scripts (eg. when the input is unknown or mixed scripts) does not affect them:
```python
from arabic_reshaper import reshape
from bidi.algorithm import get_display

some_text = 'اَلْعَرَبِيَّةُכַּף סוֹפִית'
fixed_text = get_display(reshape(some_text))
```

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

The method [`set_fallback_fonts()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fallback_fonts) allows you to specify a list of fonts to be used if any character is not available on the font currently set. When a character doesn’t exist on the current font, `fpdf2` will look if it’s available on the fallback fonts, on the same order the list was provided.

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
By default, if it does not find such matching font, the character will not be rendered using any fallback font. This behaviour can be relaxed by passing `exact_match=False` to [`set_fallback_fonts()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fallback_fonts).

Moreover, for more control over font fallback election logic,
the [`get_fallback_font()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.get_fallback_font) can be overriden.
An example of this can be found in [test/fonts/test_font_fallback.py](https://github.com/py-pdf/fpdf2/blob/master/test/fonts/test_font_fallback.py).
