# HTML #

`fpdf2` supports basic rendering from HTML.

This is implemented by using `html.parser.HTMLParser` from the Python standard library.
The whole HTML 5 specification is **not** supported, and neither is CSS,
but bug reports & contributions are very welcome to improve this.
_cf._ [Supported HTML features](#supported-html-features) below for details on its current limitations.

For a more robust & feature-full HTML-to-PDF converter in Python,
you may want to check [Reportlab](https://www.reportlab.com) (or [xhtml2pdf](https://pypi.org/project/xhtml2pdf/) based on it), [WeasyPrint](https://weasyprint.org)
or [borb](https://github.com/jorisschellekens/borb-examples/#76-exporting-html-as-pdf).


## write_html usage example ##

HTML rendering require the use of `write_html` method:

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.write_html("""
  <dl>
      <dt>Description title</dt>
      <dd>Description Detail</dd>
  </dl>
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


## Supported HTML features

* `<h1>` to `<h8>`: headings (and `align` attribute)
* `<p>`: paragraphs (and `align`, `line-height` attributes)
* `<b>`, `<i>`, `<u>`: bold, italic, underline
* `<font>`: (and `face`, `size`, `color` attributes)
* `<center>` for aligning
* `<a>`: links (and `href` attribute)
* `<pre>` & `<code>` tags
* `<img>`: images (and `src`, `width`, `height` attributes)
* `<ol>`, `<ul>`, `<li>`: ordered, unordered and list items (can be nested)
* `<dl>`, `<dt>`, `<dd>`: description list, title, details (can be nested)
* `<sup>`, `<sub>`: superscript and subscript text
* `<table>`: (with `align`, `border`, `width` attributes)
    + `<thead>`: optional tag, wraps the table header row
    + `<tfoot>`: optional tag, wraps the table footer row
    + `<tbody>`: optional tag, wraps the table rows with actual content
    + `<tr>`: rows (with `align`, `bgcolor` attributes)
    + `<th>`: heading cells (with `align`, `bgcolor`, `width` attributes)
    * `<td>`: cells (with `align`, `bgcolor`, `width` attributes)
