## write_html ##

```python
HTMLMixin.write_html(text: str, image_map = None)
```

### Description ###

`fpdf2` supports basic HTML, mainly intended to write reports from web frameworks.

It understands a limited subset of the HTML language, and it doesn't support advanced features nor CSS (look below).

HTMLMixin could be used along with FPDF class to implement this functionality (see the example).

### Parameters ###

test:
> string with HTML markup

image_map:
> dictionary with image map

### Details ###

HTML tags and attributes supported:

  * H1 to H8: headings (align attribute)
  * P: paragraphs (align attributes)
  * B, I, U: bold, italic, underline
  * FONT: (face, size, color attributes)
  * CENTER for aligning
  * A: links (href attribute)
  * IMG: images (src, width, height attributes)
  * OL, UL, LI: ordered, unordered and list items (can be nested)
  * TABLE: (border, width attributes)
    * THEAD: header (opens each page)
    * TFOOT: footer (closes each page)
    * TBODY: actual rows
      * TR: rows (bgcolor attribute)
        * TH: highlight cells (align, bgcolor, width attributes)
        * TD: rows (align, bgcolor, width attributes)

Note: Tables should have at least a first TH row with a width attribute.

### Example ###

```python
html = """
<H1 align="center">html2fpdf</H1>
<h2>Basic usage</h2>
<p>You can now easily print text mixing different
styles : <B>bold</B>, <I>italic</I>, <U>underlined</U>, or
<B><I><U>all at once</U></I></B>!<BR>You can also insert links
on text, such as <A HREF="https://pyfpdf.github.io/fpdf2/">pyfpdf.github.io/fpdf2/</A>,
or on an image: click on the logo.<br>
<center>
<A HREF="https://pyfpdf.github.io/fpdf2/"><img src="docs/fpdf2-logo.png" width="104" height="71"></A>
</center>
<h3>Sample List</h3>
<ul><li>option 1</li>
<ol><li>option 2</li></ol>
<li>option 3</li></ul>

<table border="0" align="center" width="50%">
<thead><tr><th width="30%">Header 1</th><th width="70%">header 2</th></tr></thead>
<tbody>
<tr><td>cell 1</td><td>cell 2</td></tr>
<tr><td>cell 2</td><td>cell 3</td></tr>
</tbody>
</table>
"""

from fpdf import FPDF, HTMLMixin

class MyFPDF(FPDF, HTMLMixin):
    pass
                    
pdf = MyFPDF()
#First page
pdf.add_page()
pdf.write_html(html)
pdf.output('html.pdf')
```
See html.py or [Web2Py] (../Web2Py.md) for a complete example. `# TODO fix links`

### See also ###
[write](write.md), [add_font](add_font.md), [image](image.md).

