# Combine with mistletoe to use Markdown

Several `fpdf2` methods allow Markdown syntax elements:

* [`FPDF.cell()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.cell) has an optional `markdown=True` parameter that makes it possible to use `**bold**`, `__italics__` or `--underlined--` Markdown markers
* [`FPDF.multi_cell()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) & [`FPDF.table()`](Tables.md) methods have a similar feature

But `fpdf2` also allows for basic conversion **from HTML to PDF** (_cf._ [HTML](HTML.md)).
This can be combined with the [mistletoe](https://pypi.org/project/kaleido/) library,
that follows the [CommonMark specification](https://spec.commonmark.org),
in order to generate **PDF documents from Markdown**:

```python
{% include "../tutorial/markdown2pdf.py" %}
```

<!-- Code blocks can also be rendered, but currently break mkdocs-include-markdown-plugin:

```python
msg = "This is some Python code in a fenced code block"
print(msg)
```

    msg = "This is some code in an indented code block"
    print(msg)
-->

## Rendering unicode characters

```python
{% include "../tutorial/markdown2pdf_unicode.py" %}
```

Result:

![](docs/markdown2pdf_unicode.png)
