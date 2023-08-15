# Combine with pypdf

`fpdf2` cannot **parse** existing PDF files.

However, other Python libraries can be combined with `fpdf2`
in order to add new content to existing PDF files.

This page provides several examples of doing so using [`pypdf`](https://github.com/py-pdf/pypdf), an actively-maintained library formerly known as `PyPDF2`.

## Adding content onto an existing PDF page
In this code snippet, new content will be added on top of existing content:
```python
{% include "../tutorial/add_on_page_with_pypdf.py" %}
```

## Adding a page to an existing PDF

```python
{% include "../tutorial/add_new_page_with_pypdf.py" %}
```

## Altering with pypdf a document generated with fpdf2
A document created with `fpdf2` can the be edited with `pypdf`
by passing its `.output()` to a `pypdf.PdfReader`:
```python
import io
from fpdf import FPDF
from pypdf import PdfReader

pdf = FPDF()
pdf.add_page()
pdf.set_font('times', 'B', 19)
pdf.text(50, 10, 'Hello World!')

reader = PdfReader(io.BytesIO(pdf.output()))
```
