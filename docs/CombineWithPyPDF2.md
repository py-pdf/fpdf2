# Combine with PyPDF2

`fpdf2` cannot **parse** existing PDF files.

However, other Python libraries can be combined with `fpdf2`
in order to add new content to existing PDF files.

This page provides several examples of doing so using [`PyPDF2`](https://github.com/py-pdf/PyPDF2).

## Modifying content in an existing PDF

```python
import sys
import io

from fpdf import FPDF
from PyPDF2 import PdfReader, PdfWriter

IN_FILEPATH = sys.argv[1]
OUT_FILEPATH = sys.argv[2]


def new_page(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('times', 'B', 30)
    pdf.text(50, 150, text)

    return pdf.output()


output = PdfWriter()

page_mod = PdfReader(io.BytesIO(new_page('Hello World!'))).getPage(0)
existing_page = PdfReader(IN_FILEPATH).getPage(0)
existing_page.merge_page(page2=page_mod, expand=True)
#The new content is added on top of the existing content. To adjust the position of the added content, use the in-built x,y parameters in fpdf.text

output.add_page(existing_page)
output.write(OUT_FILEPATH)
```

## Adding a page to an existing PDF

```python
import sys
import io

from fpdf import FPDF
from PyPDF2 import PdfReader, PdfWriter

IN_FILEPATH = sys.argv[1]
OUT_FILEPATH = sys.argv[2]


def new_page(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('times', 'B', 30)
    pdf.text(50, 150, text)

    # The fpdf output will have to be converted to a 'file-like' object using BytesIO.
    return io.BytesIO(pdf.output())


output = PdfWriter()
input_pdf = PdfReader(IN_FILEPATH)
output.append_pages_from_reader(input_pdf)
output.append_pages_from_reader(PdfReader(new_page('Hello World!')))

output.write(OUT_FILEPATH)
```

To add a page at an index of your choice, use `PDFMerger.merge` instead.

```python
import sys
import io

from fpdf import FPDF
from PyPDF2 import PdfMerger

IN_FILEPATH = sys.argv[1]
OUT_FILEPATH = sys.argv[2]


def new_page(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('times', 'B', 19)
    pdf.text(50, 10, text)

    return pdf.output()


merger = PdfMerger()

merger.merge(position=0, fileobj=IN_FILEPATH)
merger.merge(position=1, fileobj=io.BytesIO(new_page('Hello World!')))

merger.write(OUT_FILEPATH)
```
