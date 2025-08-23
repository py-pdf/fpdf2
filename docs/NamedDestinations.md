# Named Destinations

Named destinations allow you to create bookmarks in your PDF document that point to specific pages. This feature is useful for creating navigation within your PDF documents.

## Basic Usage

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("helvetica", size=16)
pdf.cell(0, 10, "Section 1")

# Add a named destination for this section
pdf.add_named_dest("section1")

pdf.add_page()
pdf.set_font("helvetica", size=16)
pdf.cell(0, 10, "Section 2")
pdf.add_named_dest("section2")

pdf.output("document_with_destinations.pdf")
```

## Parameters

- `name`: A non-empty string that identifies the destination. This name can be used to create links to this location in the PDF document.

## Notes

- Named destinations are added to the current page at the time of calling `add_named_dest()`.
- The name must be a non-empty string and cannot consist only of whitespace.
- Each named destination is unique; calling `add_named_dest()` with the same name will overwrite any previous destination with that name.

## Example: Creating Links to Named Destinations

```python
from fpdf import FPDF

pdf = FPDF()

# Create table of contents page
pdf.add_page()
pdf.set_font("helvetica", size=16)
pdf.cell(0, 10, "Table of Contents")
pdf.ln(20)

# Add links to sections
pdf.set_font("helvetica", size=12)
pdf.cell(0, 10, "Section 1", link="section1")
pdf.ln(10)
pdf.cell(0, 10, "Section 2", link="section2")

# Create content pages with destinations
pdf.add_page()
pdf.set_font("helvetica", size=16)
pdf.cell(0, 10, "Section 1")
pdf.add_named_dest("section1")

pdf.add_page()
pdf.set_font("helvetica", size=16)
pdf.cell(0, 10, "Section 2")
pdf.add_named_dest("section2")

pdf.output("document_with_toc.pdf")
```
