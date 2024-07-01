# HTML

`fpdf2` supports basic rendering from HTML.

This is implemented by using `html.parser.HTMLParser` from the Python standard library.
The whole HTML 5 specification is **not** supported, and neither is CSS,
but bug reports & contributions are very welcome to improve this.
_cf._ [Supported HTML features](#supported-html-features) below for details on its current limitations.

For a more robust & feature-full HTML-to-PDF converter in Python,
you may want to check [Reportlab](https://www.reportlab.com) (or [xhtml2pdf](https://pypi.org/project/xhtml2pdf/) based on it), [WeasyPrint](https://weasyprint.org)
or [borb](https://github.com/jorisschellekens/borb-examples/#76-exporting-html-as-pdf).


## write_html usage example

HTML rendering requires the use of [`FPDF.write_html()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write_html):

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
    <p><a href="https://github.com/py-pdf/fpdf2">py-pdf/fpdf2 GitHub repo</a></p>
    <p align="right">right aligned text</p>
    <p>i am a paragraph <br>in two parts.</p>
    <font color="#00ff00"><p>hello in green</p></font>
    <font size="7"><p>hello small</p></font>
    <font face="helvetica"><p>hello helvetica</p></font>
    <font face="times"><p>hello times</p></font>
  </section>
  <section>
    <h2>Other section title</h2>
    <ul type="circle">
      <li>unordered</li>
      <li>list</li>
      <li>items</li>
    </ul>
    <ol start="3" type="i">
      <li>ordered</li>
      <li>list</li>
      <li>items</li>
    </ol>
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

### Styling HTML tags globally

_New in [:octicons-tag-24: 2.7.9](https://github.com/py-pdf/fpdf2/blob/master/CHANGELOG.md)_

The style of several HTML tags (`<a>`, `<blockquote>`, `<code>`, `<pre>`, `<h1>`, `<h2>`, `<h3>`...) can be set globally, for the whole HTML document, by passing `tag_styles` to `FPDF.write_html()`:

```python
from fpdf import FPDF, FontFace

pdf = FPDF()
pdf.add_page()
pdf.write_html("""
  <h1>Big title</h1>
  <section>
    <h2>Section title</h2>
    <p>Hello world!</p>
  </section>
""", tag_styles={
    "h1": FontFace(color="#948b8b", size_pt=32),
    "h2": FontFace(color="#948b8b", size_pt=24),
})
pdf.output("html_styled.pdf")
```

Similarly, the indentation of several HTML tags (`<blockquote>`, `<dd>`, `<li>`) can be set globally, for the whole HTML document, by passing `tag_styles` to `FPDF.write_html()`:

```python
from fpdf import FPDF, TextStyle

pdf = FPDF()
pdf.add_page()
pdf.write_html("""
  <dl>
      <dt>Term</dt>
      <dd>Definition</dd>
  </dl>
  <blockquote>
  Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed non risus.
  Suspendisse lectus tortor, dignissim sit amet, adipiscing nec, ultricies sed, dolor.
  Cras elementum ultrices diam.
  </blockquote>
""", tag_styles={
    "dd": TextStyle(l_margin=5),
    "blockquote": TextStyle(color="#ccc", font_style="I",
                            t_margin=5, b_margin=5, l_margin=10),
  })
pdf.output("html_dd_indented.pdf")
```

⚠️ Note that this styling is currently only supported for a subset of all HTML tags,
and that some [`FontFace`](https://py-pdf.github.io/fpdf2/fpdf/fonts.html#fpdf.fonts.FontFace) or [`TextStyle`](https://py-pdf.github.io/fpdf2/fpdf/fonts.html#fpdf.fonts.TextStyle) properties may not be honored.
However, **Pull Request are welcome** to implement missing features!


## Supported HTML features

* `<h1>` to `<h6>`: headings (and `align` attribute)
* `<p>`: paragraphs (and `align`, `line-height` attributes)
* `<br>` & `<hr>` tags
* `<b>`, `<i>`, `<u>`: bold, italic, underline
* `<font>`: (and `face`, `size`, `color` attributes)
* `<center>` for aligning
* `<a>`: links (and `href` attribute) to a file, URL, or page number.
* `<pre>` & `<code>` tags
* `<img>`: images (and `src`, `width`, `height` attributes)
* `<ol>`, `<ul>`, `<li>`: ordered, unordered and list items (can be nested)
* `<dl>`, `<dt>`, `<dd>`: description list, title, details (can be nested)
* `<sup>`, `<sub>`: superscript and subscript text
* `<table>`: (with `align`, `border`, `width`, `cellpadding`, `cellspacing` attributes)
    + `<thead>`: optional tag, wraps the table header row
    + `<tfoot>`: optional tag, wraps the table footer row
    + `<tbody>`: optional tag, wraps the table rows with actual content
    + `<tr>`: rows (with `align`, `bgcolor` attributes)
    + `<th>`: heading cells (with `align`, `bgcolor`, `width` attributes)
    * `<td>`: cells (with `align`, `bgcolor`, `width`, `rowspan`, `colspan` attributes)

### Page breaks

_New in [:octicons-tag-24: 2.7.10](https://github.com/py-pdf/fpdf2/blob/master/CHANGELOG.md)_

Page breaks can be triggered explicitly using the [break-before](https://developer.mozilla.org/en-US/docs/Web/CSS/break-before) or [break-after](https://developer.mozilla.org/en-US/docs/Web/CSS/break-after) CSS properties.
For exemple you can use:
```html
<br style="break-after: page">
```
or:
```html
<p style="break-before: page">
Top of a new page.
</p>
```

## Known limitations

`fpdf2` HTML renderer does not support some configurations of nested tags.
For example:

* `<table>` cells can contain `<td><b><em>nested tags forming a single text block</em></b></td>`, but **not** `<td><b>arbitrarily</b> nested <em>tags</em></td>` - _cf._ [issue #845](https://github.com/py-pdf/fpdf2/issues/845)

You can also check the currently open GitHub issues with the tag `html`:
[label:html is:open](https://github.com/py-pdf/fpdf2/issues?q=is%3Aopen+label%3Ahtml)


## Using Markdown

Check [Combine with mistletoe to use Markdown](CombineWithMistletoeoToUseMarkdown.md)
