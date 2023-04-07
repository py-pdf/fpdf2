# Combine with PyPDF2

`fpdf2` cannot **parse** existing PDF files.

However, other Python libraries can be combined with `fpdf2`
in order to add new content to existing PDF files.

This page provides several examples of doing so using [`PyPDF2`](https://github.com/py-pdf/PyPDF2).

## Adding content onto an existing PDF page
In this code snippet, new content will be added on top of existing content:
```python
import io, sys

from fpdf import FPDF
from PyPDF2 import PdfReader, PdfWriter

IN_FILEPATH = sys.argv[1]
OUT_FILEPATH = sys.argv[2]
ON_PAGE_INDEX = 0  # Index of the target page (starts at zero)

def new_content():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('times', 'B', 30)
    pdf.text(50, 150, 'Hello World!')
    return pdf.output()

reader = PdfReader(IN_FILEPATH)
page_overlay = PdfReader(io.BytesIO(new_content())).getPage(0)
reader.getPage(ON_PAGE_INDEX).merge_page(page2=page_overlay)

writer = PdfWriter()
writer.append_pages_from_reader(reader)
writer.write(OUT_FILEPATH)
```

## Adding a page to an existing PDF

```python
import io, sys

from fpdf import FPDF
from PyPDF2 import PdfMerger

IN_FILEPATH = sys.argv[1]
OUT_FILEPATH = sys.argv[2]
ON_PAGE_INDEX = 2  # Index at which the page will be inserted (starts at zero)

def new_page():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('times', 'B', 19)
    pdf.text(50, 10, 'Hello World!')
    return io.BytesIO(pdf.output())

merger = PdfMerger()
merger.merge(position=0, fileobj=IN_FILEPATH)
merger.merge(position=ON_PAGE_INDEX, fileobj=new_page())
merger.write(OUT_FILEPATH)
```

## Altering with PyPDF2 a document generated with fpdf2
A document created with `fpdf2` can the be edited with `PyPDF2`
by passing its `.output()` to a `PyPDF2.PdfReader`:
```python
import io
from fpdf import FPDF
from PyPDF2 import PdfReader

pdf = FPDF()
pdf.add_page()
pdf.set_font('times', 'B', 19)
pdf.text(50, 10, 'Hello World!')

reader = PdfReader(io.BytesIO(pdf.output()))
```
