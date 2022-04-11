# Text styling #

## set_font ##

Setting emphasis on text can be controlled by using `set_font(style=...)`:

* `style="B"` indicates **bold**
* `style="I"` indicates _italics_
* `style="U"` indicates <u>underline</u>
* `style="BI"` indicates _**bold italics**_

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Times", size=36)
pdf.cell(txt="This")
pdf.set_font(style="B")
pdf.cell(txt="is")
pdf.set_font(style="I")
pdf.cell(txt="a")
pdf.set_font(style="U")
pdf.cell(txt="PDF")
pdf.output("style.pdf")
```


## Text mode ##

The PDF spec defines several text modes:
![](pdf-text-modes.jpg)

The text mode can be controlled with the `.text_mode` attribute.
With `STROKE` modes, the line width is induced by `.line_width`,
and its color can be configured with [`set_draw_color()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color).
With `FILL` modes, the filling color can be controlled by [`set_fill_color()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color)
of [`set_text_color()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color).

With any of the 4 `CLIP` modes, the letters will be filled by vector drawings made afterwards,
as can be seen in this example:

```python
from fpdf import FPDF, TextMode

pdf = FPDF(orientation="landscape")
pdf.add_page()
pdf.set_font("Helvetica", size=100)

with pdf.local_context(text_mode=TextMode.STROKE, line_width=2):
    pdf.cell(txt="Hello world")
# Outside the local context, text_mode & line_width are reverted
# back to their original default values
pdf.ln()

with pdf.local_context(text_mode=TextMode.CLIP):
    pdf.cell(txt="CLIP text mode")
    for r in range(0, 250, 2):  # drawing concentric circles
        pdf.circle(x=130-r/2, y=70-r/2, r=r)

pdf.output("text-modes.pdf")
```
![](text-modes.png)

More examples from [`test_text_mode.py`](https://github.com/PyFPDF/fpdf2/blob/master/test/text/test_text_mode.py):

* [text_modes.pdf](https://github.com/PyFPDF/fpdf2/blob/master/test/text/text_modes.pdf)
* [clip_text_modes.pdf](https://github.com/PyFPDF/fpdf2/blob/master/test/text/clip_text_modes.pdf)


## markdown=True ##

An optional `markdown=True` parameter can be passed to the [`cell()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.cell)
& [`multi_cell()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) methods
in order to enable basic Markdown-like styling: `**bold**, __italics__, --underlined--`

Bold & italics require using dedicated fonts for each style.

For the standard fonts (Courier, Helvetica & Times), those dedicated fonts are configured by default.
Using other fonts means that their variants (bold, italics)
must be registered using `add_font` (with `style="B"` and `style="I"`).

```python
from fpdf import FPDF

pdf = fpdf.FPDF()
pdf.add_page()
pdf.set_font("Times", size=60)
pdf.cell(txt="**Lorem** __Ipsum__ --dolor--", markdown=True)
pdf.output("markdown-styled.pdf")
```


## write_html ##

[`write_html`](HTML.md) allows to set emphasis on text through the `<b>`, `<i>` and `<u>` tags:

```python
pdf.write_html("""<B>bold</B>
                  <I>italic</I>
                  <U>underlined</U>
                  <B><I><U>all at once!</U></I></B>"""
)
```
