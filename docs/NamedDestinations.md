# Named Destinations

_New in [:octicons-tag-24: 2.8.5](https://github.com/py-pdf/fpdf2/blob/master/CHANGELOG.md)_

Named destinations allow you to create semantic bookmarks within PDF documents. Unlike simple page references,
named destinations remain valid even if page numbers change during document generation.

## Overview

Named destinations are defined in section 12.3.2.4 of the PDF 2.0 specification. They provide a way to
create stable references to specific locations within a PDF document, which can be used in:

- Internal links
- Bookmarks (outlines)
- Actions
- External documents referencing the PDF

## Basic Usage

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("helvetica", size=16)
pdf.cell(0, 10, "Section 1")

# Add a named destination for this section
pdf.add_link(name="section1")

pdf.add_page()
pdf.set_font("helvetica", size=16)
pdf.cell(0, 10, "Section 2")
pdf.add_link(name="section2")

pdf.output("document_with_destinations.pdf")
```

## Parameters

- `name`: A non-empty string that identifies the destination. This name can be used to create links to this location in the PDF document.

## Notes

- Named destinations are added to the current page at the time of calling `add_link(name="...")`.
- The name must be a non-empty string and cannot consist only of whitespace.
- Each named destination is unique; calling `add_link()` with the same name will overwrite any previous destination with that name.
- You can reference a named destination in a link by prefixing it with `#` (e.g., `link="#section1"`).

## Advanced Usage: Reserving Named Destinations

Sometimes you need to reference a destination before it exists in the document. You can reserve a named destination with `set_link()` and bind it later:

```python
pdf = FPDF()

# Reserve named destinations
pdf.set_link(name="section1")
pdf.set_link(name="section2")

# Create table of contents page
pdf.add_page()
pdf.set_font("helvetica", size=16)
pdf.cell(0, 10, "Table of Contents")
pdf.ln(20)

# Add links to sections using the # prefix
pdf.set_font("helvetica", size=12)
pdf.cell(0, 10, "Section 1", link="#section1")
pdf.ln(10)
pdf.cell(0, 10, "Section 2", link="#section2")

# Create content pages with destinations
pdf.add_page()
pdf.set_font("helvetica", size=16)
pdf.cell(0, 10, "Section 1")
pdf.add_link(name="section1")  # Binds "section1" destination to this position

pdf.add_page()
pdf.set_font("helvetica", size=16)
pdf.cell(0, 10, "Section 2")
pdf.add_link(name="section2")  # Binds "section2" destination to this position

pdf.output("document_with_toc.pdf")
```

## Technical Details

In the PDF structure, named destinations are stored in the catalog under:
`/Names -> /Dests -> /Names` array as name/destination pairs.

Each destination contains:
- A page reference
- A destination type (typically `/XYZ`)
- Position coordinates (left, top)
- An optional zoom factor

This implementation follows the PDF specification and ensures compatibility with all PDF readers.
