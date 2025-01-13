# fpdf2 internals

## FPDF.pages
`FPDF` is designed to add content progressively to the document generated, page by page.

Each page is an entry in the `.pages` attribute of `FPDF` instances.
Indices start at 1 (the first page) and values are [`PDFPage`](https://py-pdf.github.io/fpdf2/fpdf/output.html#fpdf.output.PDFPage) instances.

`PDFPage` instances have a `.contents` attribute that is a [`bytearray`](https://docs.python.org/3/library/stdtypes.html#bytearray) and contains the **Content Stream** for this page
(`bytearray` makes things [a lot faster](https://github.com/reingart/pyfpdf/pull/164)).


## GraphicsStateMixin
[fpdf/graphics_state.py](https://github.com/py-pdf/fpdf2/blob/master/fpdf/graphics_state.py)

`emphasis`


## OutputProducer


## syntax.py & objects serialization

