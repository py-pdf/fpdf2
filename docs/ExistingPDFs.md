# Existing PDFs #

`fpdf2` cannot **parse** existing PDF files.

However, other Python libraries can be combined with `fpdf2`
in order to add new content to existing PDF files.

This page provides several examples of doing so using [`pdfrw`](https://github.com/pmaupin/pdfrw),
a great zero-dependency pure Python library dedicated to reading & writing PDFs,
with numerous examples and a very clean set of classes modelling the PDF internal syntax.


## Adding content onto an existing PDF page ##

```python
import sys
from fpdf import FPDF
from pdfrw import PageMerge, PdfReader, PdfWriter

IN_FILEPATH = sys.argv[1]
OUT_FILEPATH = sys.argv[2]
ON_PAGE_INDEX = 1
UNDERNEATH = False  # if True, new content will be placed underneath page (painted first)

def new_content():
    fpdf = FPDF()
    fpdf.add_page()
    fpdf.set_font("helvetica", size=36)
    fpdf.text(50, 50, "Hello!")
    reader = PdfReader(fdata=bytes(fpdf.output()))
    return reader.pages[0]

writer = PdfWriter(trailer=PdfReader(IN_FILEPATH))
PageMerge(writer.pagearray[ON_PAGE_INDEX]).add(new_content(), prepend=UNDERNEATH).render()
writer.write(OUT_FILEPATH)
```


## Adding a page to an existing PDF ##

```python
import sys
from fpdf import FPDF
from pdfrw import PdfReader, PdfWriter

IN_FILEPATH = sys.argv[1]
OUT_FILEPATH = sys.argv[2]
NEW_PAGE_INDEX = 1  # set to None to append at the end

def new_page():
    fpdf = FPDF()
    fpdf.add_page()
    fpdf.set_font("helvetica", size=36)
    fpdf.text(50, 50, "Hello!")
    reader = PdfReader(fdata=bytes(fpdf.output()))
    return reader.pages[0]

writer = PdfWriter(trailer=PdfReader(IN_FILEPATH))
writer.addpage(new_page(), at_index=NEW_PAGE_INDEX)
writer.write(OUT_FILEPATH)
```

This example relies on [pdfrw _Pull Request_ #216](https://github.com/pmaupin/pdfrw/pull/216).Until it is merged, you can install a forked version of `pdfrw` including the required patch:

    pip install git+https://github.com/PyPDF/pdfrw.git@addpage_at_index


## borb ##

![](https://raw.githubusercontent.com/jorisschellekens/borb/master/logo/borb_64.png)

Joris Schellekens made another excellent pure-Python library dedicated to reading & write PDF: [borb](https://github.com/jorisschellekens/borb/).
He even wrote a book about it, available publicly there: [borb-examples](https://github.com/jorisschellekens/borb-examples/).


### Creating a document with `fpdf2` and transforming it into a `borb.pdf.document.Document` ###

```python
from io import BytesIO
from borb.pdf.pdf import PDF  
from fpdf import FPDF

pdf = FPDF()
pdf.set_title('Initiating a borb doc from a FPDF instance')
pdf.set_font('helvetica', size=12)
pdf.add_page()
pdf.cell(txt="Hello world!")

doc = PDF.loads(BytesIO(pdf.output()))
print(doc.get_document_info().get_title())
```
