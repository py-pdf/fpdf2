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
pdf.cell(text="Cell link", border=1, center=True,
         link="https://github.com/py-pdf/fpdf2")
pdf.output("hyperlink.pdf")
```


## Hyperlink with FPDF.multi_cell ##

```python
from fpdf import FPDF

pdf = FPDF()
pdf.set_font("helvetica", size=24)
pdf.add_page()
pdf.multi_cell(
    pdf.epw,
    text="**Website:** [fpdf2](https://py-pdf.github.io/fpdf2/) __Go visit it!__",
    markdown=True,
)
pdf.output("hyperlink.pdf")
```

Links defined this way in Markdown can be styled by setting `FPDF` class attributes `MARKDOWN_LINK_COLOR` (default: `None`) & `MARKDOWN_LINK_UNDERLINE` (default: `True`).

`link="https://...your-url"` can also be used to make the whole cell clickable.


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
pdf.text(x=0, y=line_height, text=text)
width = pdf.get_string_width(text)
pdf.link(x=0, y=0, w=width, h=line_height, link="https://github.com/py-pdf/fpdf2")
pdf.output("hyperlink.pdf")
```


## Hyperlink with write_html ##

An alternative method using [`FPDF.write_html`](HTML.md):

```python
from fpdf import FPDF

pdf = FPDF()
pdf.set_font_size(16)
pdf.add_page()
pdf.write_html('<a href="https://github.com/py-pdf/fpdf2">Link defined as HTML</a>')
pdf.output("hyperlink.pdf")
```

The hyperlinks defined this way will be rendered in blue with underline.


## Internal links ##

Internal links are links redirecting to other pages in the document.

Using `FPDF.cell`:

```python
from fpdf import FPDF

pdf = FPDF()
pdf.set_font("helvetica", size=24)
pdf.add_page()
pdf.cell(text="Welcome on first page!", align="C", center=True)
pdf.add_page()
link = pdf.add_link(page=1)
pdf.cell(text="Internal link to first page", border=1, link=link)
pdf.output("internal_link.pdf")
```

There are some situations where a user wants to create
an internal link to another page in the PDF document, but
the page number is not known at the time of link creation.
In this case, the link can be created using `pdf.add_link()`
as before, and then later re-reference to a specific page using 
`pdf.set_link()`. In this example our goal is to link to a
page that occurs after a section with a variable
amount of text, potentially occupying multiple pages:

```python
from fpdf import FPDF
import random

pdf = FPDF()
pdf.set_font("helvetica", size=24)
pdf.add_page()

# create a link to a page that will be created later
link_to_summary_page = pdf.add_link()
pdf.cell(text="Link to summary after elements", border=1, link=link_to_summary_page)
pdf.ln(20)

pdf.cell(text="List of elements", align="C", center=True)
pdf.ln(20)

# this num_elements variable can vary across runs
# resulting in a different number of pages
num_elements = random.randint(10,30)
for i in range(num_elements):
    pdf.cell(text=f"Element {i+1}", align="C", center=True)
    pdf.ln(20)

# `set_link` to change page referenced by the link
pdf.add_page()
pdf.set_link(link_to_summary_page)
pdf.cell(text=f"Summary: there are {num_elements} elements", align="C", center=True)
pdf.ln(20)

# link back to the first page
link = pdf.add_link(page=1)
pdf.cell(text="Internal link to first page", border=1, link=link)

pdf.output("internal_link_unknown_pages.pdf")
```
Other methods can also insert internal links:

* [FPDF.multi_cell](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) using `link=` **or** `markdown=True` and this syntax: `[link text](page number)`
* [FPDF.link](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.link)
* [FPDF.write_html](HTML.md) using anchor tags: `<a href="page number">link text</a>`

The unit tests `test_internal_links()` in [test_links.py](https://github.com/py-pdf/fpdf2/blob/master/test/test_links.py) provides examples for all of those methods.


## Links to other documents on the filesystem ##

Using `FPDF.cell`:

```python
from fpdf import FPDF

pdf = FPDF()
pdf.set_font("helvetica", size=24)
pdf.add_page()
pdf.cell(text="Link to other_doc.pdf", border=1, link="other_doc.pdf")
pdf.output("link_to_other_doc.pdf")
```

Other methods can also insert internal links:

* [FPDF.multi_cell](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) using `link=` **or** `markdown=True` and this syntax: `[link text](other_doc.pdf)`
* [FPDF.link](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.link)
* [FPDF.write_html](HTML.md) using anchor tags: `<a href="other_doc.pdf">link text</a>`

The unit test `test_link_to_other_document()` in [test_links.py](https://github.com/py-pdf/fpdf2/blob/master/test/test_links.py) provides examples for all of those methods.



## Alternative description ##

An optional textual description of the link can be provided, for accessibility purposes:

```python
pdf.link(x=0, y=0, w=width, h=line_height, link="https://github.com/py-pdf/fpdf2",
         alt_text="GitHub page for fpdf2")
```