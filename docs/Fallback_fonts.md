# Font fallback #

FPDF allows you to specify a list of fonts to be used if one character is not available on the font currently used. Common scenarios are use of special characters like emojis within your text or mixing different languages.

The method set_fallback_font() will receive a list of fonts. When a character doesn’t exist on the current font, FPDF will look if it’s available on the fallback fonts, on the same order the list was provided.

## Example ##
```python
pdf = FPDF()
pdf.add_page()
pdf.add_font(family="Roboto", fname="Roboto-Regular.ttf")
# twitter emoji font: https://github.com/13rac1/twemoji-color-font/releases
pdf.add_font(family="TwitterEmoji", fname="TwitterColorEmoji-SVGinOT.ttf")
pdf.set_font("Roboto", size=15)
pdf.set_fallback_fonts(["TwitterEmoji"])
pdf.write(txt="text with an emoji 🌭")
pdf.output("text_with_emoji.pdf")
```
