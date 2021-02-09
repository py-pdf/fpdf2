# HTML #

`fpdf2` can perform rendering from HTML.

This is implemented by using `html.parser.HTMLParser` from the Python standard library.
The whole HTML 5 specification is very likely **not** supported,
but bug reports & contributions are very welcome to improve this.


## write_html usage example ##

HTML rendering require the use of `fpdf.HTMLMixin`,
that provides a new `write_html` method:

```python
from fpdf import FPDF, HTMLMixin

class PDF(FPDF, HTMLMixin):
    pass

pdf = PDF()
pdf.add_page()
pdf.write_html("""
  <h1>Big title</h1>
  <section>
    <h2>Section title</h2>
    <p><b>Hello</b> world. <u>I am</u> <i>tired</i>.</p>
    <p><a href="https://github.com/PyFPDF/fpdf2">PyFPDF/fpdf2 GitHub repo</a></p>
    <p align="right">right aligned text</p>
    <p>i am a paragraph <br />in two parts.</p>
    <font color="#00ff00"><p>hello in green</p></font>
    <font size="7"><p>hello small</p></font>
    <font face="helvetica"><p>hello helvetica</p></font>
    <font face="times"><p>hello times</p></font>
  </section>
  <section>
    <h2>Other section title</h2>
    <ul><li>unordered</li><li>list</li><li>items</li></ul>
    <ol><li>ordered</li><li>list</li><li>items</li></ol>
    <br>
    <br>
    <pre>i am preformatted text.</pre>
    <br>
    <blockquote>hello blockquote</blockquote>
    <table width="50%">
      <thead>
        <tr>
          <th width="30%">ID</th>
          <th width="70%">Name</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>1</td>
          <td>Alice</td>
        </tr>
        <tr>
          <td>2</td>
          <td>Bob</td>
        </tr>
      </tbody>
    </table>
  </section>
""")
pdf.output("html.pdf")
```
