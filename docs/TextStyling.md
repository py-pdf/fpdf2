# Text styling #

`fpdf2` supports setting _emphasis_ on text : **bold**, __italics__ or <u>underlined</u>.

Bold & italics require using dedicated fonts for each style.

For the standard fonts (Courier, Helvetica & Times), those dedicated fonts are configured by default.
Using other fonts means that their variants (bold, italics)
must be registered using `add_font` (with `style="B"` and `style="I"`).


## set_font ##

Setting emphasis on text can be controlled by using `set_font(style=...)`

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


## write_html ##

[`write_html`](HTML.md) allows to set emphasis on text through the `<b>`, `<i>` and `<u>` tags:

```python
pdf.write_html("""<B>bold</B>
                  <I>italic</I>
                  <U>underlined</U>
                  <B><I><U>all at once!</U></I></B>"""
)
```


## markdown=True ##

An optional `markdown=True` parameter can be passed to the [`cell`](fpdf/fpdf.html#fpdf.fpdf.FPDF.cell) method
in order to enable basic Markdown-like styling: `**bold**, __italics__, --underlined--`

```python
from fpdf import FPDF

pdf = fpdf.FPDF()
pdf.add_page()
pdf.set_font("Times", size=60)
pdf.cell(txt="**Lorem** __Ipsum__ --dolor--", markdown=True)
pdf.output("markdown-styled.pdf")
```
