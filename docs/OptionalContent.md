# Optional content (layers)

_New in [:octicons-tag-24: 2.8.8](https://github.com/py-pdf/fpdf2/blob/master/CHANGELOG.md)_

## Overview

PDF supports **optional content groups** (often called *layers*): portions of a
document whose visibility can be toggled. A common use case is content that
should be visible on screen but not printed, such as a watermark or a background
image, or the other way around.

`fpdf2` exposes this through the [`FPDF.optional_content()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.optional_content)
context manager. Anything drawn inside the `with` block (text, images, shapes)
is placed in an optional content group whose visibility on screen and in print
is controlled by the `on_view` and `on_print` arguments:

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("helvetica", size=24)

# Shown on screen but not printed:
with pdf.optional_content(on_print=False):
    pdf.image("background.png", x=0, y=0, w=pdf.epw)

# Printed but not shown on screen:
with pdf.optional_content(on_view=False):
    pdf.text(20, 50, "Printed copy only")

pdf.text(20, 70, "Always visible")
pdf.output("optional_content.pdf")
```

The `label` argument sets the name shown for the group in the layers panel of
PDF viewers that expose one (for example Adobe Acrobat).

Groups that share the same `on_view` / `on_print` visibility are reused, so
calling `optional_content()` repeatedly with the same arguments does not create
redundant groups.

Using optional content sets the minimum PDF version of the document to 1.5.

!!! warning "Viewer support"
    Not all PDF viewers honor optional content. Many browser-based viewers
    ignore it and display every group. The screen-versus-print distinction in
    particular is respected by viewers such as Adobe Acrobat, but not by all.
