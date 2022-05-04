# Metadata #

The PDF specification contain two types of metadata, the newer XMP
(Extensible Metadata Platform, XML-based) and older `DocumentInformation` dictionary.
The PDF 2.0 specification removes the `DocumentInformation` dictionary.

Currently, the following methods on `fpdf.FPDF` allow to set metadata information
in the `DocumentInformation` dictionary:

- `set_title`
- `set_lang`
- `set_subject`
- `set_author`
- `set_keywords`
- `set_producer`
- `set_creator`
- `set_creation_date`
- `set_xmp_metadata`, that requires you to craft the necessary XML string

For a more user-friendly API to set metadata,
we recommend using [`pikepdf`](https://github.com/pikepdf/pikepdf/) that will set both XMP & `DocumentInformation` metadata:

```python
import sys
from datetime import datetime

import pikepdf
from fpdf import FPDF_VERSION

with pikepdf.open(sys.argv[1], allow_overwriting_input=True) as pdf:
    with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
        meta["dc:title"] = "Title"
        meta["dc:description"] = "Description"
        meta["dc:creator"] = ["Author1", "Author2"]
        meta["pdf:Keywords"] = "keyword1 keyword2 keyword3"
        meta["pdf:Producer"] = f"PyFPDF/fpdf{FPDF_VERSION}"
        meta["xmp:CreatorTool"] = __file__
        meta["xmp:MetadataDate"] = datetime.now(datetime.utcnow().astimezone().tzinfo).isoformat()
    pdf.save()
```

## Full screen ##

```python
from fpdf import FPDF

pdf = FPDF()
pdf.page_mode = "FULL_SCREEN"
pdf.output("full-screen.pdf")
```

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
from fpdf import FPDF

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
