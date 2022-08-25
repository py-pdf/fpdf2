# Page format and orientation #

By default, a `FPDF` document has a [`A4`](https://en.wikipedia.org/wiki/ISO_216#A_series) format with `portrait` orientation.

Other formats & orientation can be specified to `FPDF` constructor:

```python
pdf = fpdf.FPDF(orientation="landscape", format="A5")
```

Currently supported formats are `a3`, `a4`, `a5`, `letter`, `legal` or a tuple `(width, height)`.
Additional standard formats are welcome and can be suggested through pull requests.

## Per-page format, orientation and background
`.set_page_background()` lets you set a background for all pages following this call until the background is removed.
The value must be of type `str`, `io.BytesIO`, `PIL.Image.Image`, `drawing.DeviceRGB`, `tuple` or `None`

The following code snippet illustrates how to configure different page formats for specific pages as well as setting different backgrounds and then removing it:

```python
from fpdf import FPDF

pdf = FPDF()
pdf.set_font("Helvetica")
pdf.set_page_background((252,212,255))
for i in range(9):
    if i == 6:
        pdf.set_page_background('image_path.png')
    pdf.add_page(format=(210 * (1 - i/10), 297 * (1 - i/10)))
    pdf.cell(txt=str(i))
pdf.set_page_background(None)
pdf.add_page(same=True)
pdf.cell(txt="9")
pdf.output("varying_format.pdf")
```

Similarly, an `orientation` parameter can be provided to the [`add_page`](fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page) method.

## Page layout & zoom level ##

[`set_display_mode()`](fpdf/fpdf.html#fpdf.FPDF.set_display_mode) allows to set the **zoom level**:
pages can be displayed entirely on screen, occupy the full width of the window, use the real size,
be scaled by a specific zooming factor or use the viewer default (configured in its _Preferences_ menu).

The **page layout** can also be specified: single page at a time, continuous display, two columns or viewer default.

```python
from fpdf import FPDF

pdf = FPDF()
pdf.set_display_mode(zoom="default", layout="TWO_COLUMN_LEFT")
pdf.set_font("helvetica", size=30)
pdf.add_page()
pdf.cell(txt="page 1")
pdf.add_page()
pdf.cell(txt="page 2")
pdf.output("two-column.pdf")
```

## Viewer preferences ##

```python
from fpdf import FPDF, ViewerPreferences

pdf = FPDF()
pdf.viewer_preferences = ViewerPreferences(
    hide_toolbar=True,
    hide_menubar=True,
    hide_window_u_i=True,
    fit_window=True,
    center_window=True,
    display_doc_title=True,
    non_full_screen_page_mode="USE_OUTLINES",
)
pdf.set_font("helvetica", size=30)
pdf.add_page()
pdf.cell(txt="page 1")
pdf.add_page()
pdf.cell(txt="page 2")
pdf.output("viewer-prefs.pdf")
```

## Full screen ##

```python
from fpdf import FPDF

pdf = FPDF()
pdf.page_mode = "FULL_SCREEN"
pdf.output("full-screen.pdf")
```
