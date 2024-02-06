# Combine with pdfrw

`fpdf2` cannot **parse** existing PDF files.

However, other Python libraries can be combined with `fpdf2`
in order to add new content to existing PDF files.

This page provides several examples of using `fpdf2` with [`pdfrw`](https://github.com/pmaupin/pdfrw),
a great zero-dependency pure Python library dedicated to reading & writing PDFs,
with numerous examples and a very clean set of classes modelling the PDF internal syntax.

Sadly, this library is not maintained anymore, _cf._ [pmaupin/pdfrw issue #232](https://github.com/pmaupin/pdfrw/issues/232) & [sarnold/pdfrw issue #15](https://github.com/sarnold/pdfrw/issues/15).

## Adding content onto an existing PDF page

```python
{% include "../tutorial/add_on_page_with_pdfrw.py" %}
```

## Adding a page to an existing PDF

```python
{% include "../tutorial/add_new_page_with_pdfrw.py" %}
```

This example relies on [pdfrw _Pull Request_ #216](https://github.com/pmaupin/pdfrw/pull/216).
Until it is merged, you can install a forked version of `pdfrw` including the required patch:

    pip install git+https://github.com/PyFPDF/pdfrw.git@addpage_at_index

## Altering with pdfrw a document generated with fpdf2
A document created with `fpdf2` can the be edited with `pdfrw`
by passing its `.output()` to a `pdfrw.PdfReader`:
```python
import io
from fpdf import FPDF
from pdfrw import PdfReader

pdf = FPDF()
pdf.add_page()
pdf.set_font('times', 'B', 19)
pdf.text(50, 10, 'Hello World!')

reader = PdfReader(io.BytesIO(pdf.output()))
```
