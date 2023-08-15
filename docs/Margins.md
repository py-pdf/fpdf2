# Margins #

By default a `FPDF` document has a 2cm margin at the bottom,
and 1cm margin on the other sides.

Those margins control the initial current X & Y position to render elements on a page,
and also define the height limit that triggers automatic page breaks when they are enabled.

Margins can be completely removed:

```python
pdf.set_margin(0)
```

Several methods can be used to set margins:

* [set_margin](https://py-pdf.github.io/fpdf2/fpdf/#fpdf.FPDF.set_margin)
* [set_left_margin](https://py-pdf.github.io/fpdf2/fpdf/#fpdf.FPDF.set_left_margin)
* [set_right_margin](https://py-pdf.github.io/fpdf2/fpdf/#fpdf.FPDF.set_right_margin)
* [set_top_margin](https://py-pdf.github.io/fpdf2/fpdf/#fpdf.FPDF.set_top_margin)
* [set_margins](https://py-pdf.github.io/fpdf2/fpdf/#fpdf.FPDF.set_margins)
* [set_auto_page_break](https://py-pdf.github.io/fpdf2/fpdf/#fpdf.FPDF.set_auto_page_break)
