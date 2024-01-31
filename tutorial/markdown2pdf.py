from mistletoe import markdown

html = markdown(
    """
# Top title (ATX)

Subtitle (setext)
-----------------

### An even lower heading (ATX)

**Text in bold**

_Text in italics_

[This is a link](https://github.com/PyFPDF/fpdf2)

<https://py-pdf.github.io/fpdf2/>

This is an unordered list:
* an item
* another item

This is an ordered list:
1. first item
2. second item
3. third item with an unordered sublist:
    * an item
    * another item

Inline `code span`

A table:

| Foo | Bar | Baz |
|:--- |:---:| ---:|
| Foo | Bar | Baz |

Some horizontal thematic breaks:

***
---
___

![Alternate description](https://py-pdf.github.io/fpdf2/fpdf2-logo.png)
"""
)

from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.write_html(html)
pdf.output("pdf-from-markdown.pdf")
