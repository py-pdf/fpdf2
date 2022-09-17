# Links #

`fpdf2` can generate both **internal** links (to other pages in the document)
& **hyperlinks** (links to external URLs that will be opened in a browser).


## Hyperlink with FPDF.cell ##

This method makes the whole cell clickable (not only the text):

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("helvetica", size=24)
pdf.cell(w=40, h=10, txt="Cell link", border=1, align="C", link="https://github.com/PyFPDF/fpdf2")
pdf.output("hyperlink.pdf")
```


## Hyperlink with FPDF.link ##

The `FPDF.link` is a low-level method that defines a rectangular clickable area.

There is an example showing how to place such rectangular link over some text:

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("helvetica", size=36)
line_height = 10
text = "Text link"
pdf.text(x=0, y=line_height, txt=text)
width = pdf.get_string_width(text)
pdf.link(x=0, y=0, w=width, h=line_height, link="https://github.com/PyFPDF/fpdf2")
pdf.output("hyperlink.pdf")
```


## Hyperlink with write_html ##

An alternative method using [`FPDF.write_html`](HTML.md):

```python
from fpdf import FPDF

pdf = FPDF()
pdf.set_font_size(16)
pdf.add_page()
pdf.write_html('<a href="https://github.com/PyFPDF/fpdf2">Link defined as HTML</a>')
pdf.output("hyperlink.pdf")
```

The hyperlinks defined this way will be rendered in blue with underline.


## Internal links ##

Using `FPDF.cell`:

```python
from fpdf import FPDF

pdf = FPDF()
pdf.set_font("helvetica", size=24)
pdf.add_page()
# Displaying a full-width cell with centered text:
pdf.cell(w=pdf.epw, txt="Welcome on first page!", align="C")
pdf.add_page()
link = pdf.add_link()
pdf.set_link(link, page=1)
pdf.cell(txt="Internal link to first page", border=1, link=link)
pdf.output("internal_link.pdf")
```

Similarly, `FPDF.link` can be used instead of `FPDF.cell`,
however `write_html` does not allow to define internal links.


## Alternative description ##

An optional textual description of the link can be provided, for accessibility purposes:

```python
pdf.link(x=0, y=0, w=width, h=line_height, link="https://github.com/PyFPDF/fpdf2",
         alt_text="GitHub page for fpdf2")
```