# borb #

![](https://raw.githubusercontent.com/jorisschellekens/borb/master/logo/borb_64.png)

Joris Schellekens made another excellent pure-Python library dedicated to reading & write PDF: [borb](https://github.com/jorisschellekens/borb/).
He even wrote a very detailed e-book about it, available publicly there: [borb-examples](https://github.com/jorisschellekens/borb-examples/).

The maintainer of `fpdf2` wrote an article comparing it with `borb`:
[borb vs fpdf2](https://chezsoi.org/lucas/blog/fpdf2-5-2-svg-support-and-borb.html).


## Creating a document with `fpdf2` and transforming it into a `borb.pdf.document.Document` ##

```python
from io import BytesIO
from borb.pdf.pdf import PDF
from fpdf import FPDF

pdf = FPDF()
pdf.set_title('Initiating a borb doc from a FPDF instance')
pdf.set_font('helvetica', size=12)
pdf.add_page()
pdf.cell(text="Hello world!")

doc = PDF.loads(BytesIO(pdf.output()))
print(doc.get_document_info().get_title())
```
