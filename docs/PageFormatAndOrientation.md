# Page format and orientation #

By default, a `FPDF` document has a [`A4`](https://en.wikipedia.org/wiki/ISO_216#A_series) format with `portrait` orientation.

Other formats & orientation can be specified to `FPDF` constructor:

```python
pdf = fpdf.FPDF(orientation="landscape", format="A5")
```

Currently supported formats are `a3`, `a4`, `a5`, `letter`, `legal` or a tuple `(width, height)`.
Additional standard formats are welcome and can be suggested through pull requests.

## Per-page format and orientation

The following code snippet illustrate how to configure different page formats for specific pages:

```python
from fpdf import FPDF

pdf = FPDF()
pdf.set_font("Helvetica")
for i in range(9):
    pdf.add_page(format=(210 * (1 - i/10), 297 * (1 - i/10)))
    pdf.cell(txt=str(i))
pdf.add_page(same=True)
pdf.cell(txt="9")
pdf.output("varying_format.pdf")
```

Similarly, an `orientation` parameter can be provided to the [`add_page`](fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page) method.

## Page display duration in presentation mode

In **presentation mode** (usually enabled with the `CTRL + L` shortcut),
page can be associated with a "display duration"
until when the viewer application automatically advances to the next page:

```python
from fpdf import FPDF

pdf = fpdf.FPDF()
pdf.set_font("Helvetica", size=120)
pdf.add_page(duration=3)
pdf.cell(txt="Page 1")
pdf.page_duration = .5
pdf.add_page()
pdf.cell(txt="Page 2")
pdf.add_page()
pdf.cell(txt="Page 3")
pdf.output("presentation.pdf")
```

As of june 2021, this configuration entry is onored by Adobe Acrobat reader,
but ignored by Sumatra PDF reader.
