_cf._ https://squidfunk.github.io/mkdocs-material/customization/#overriding-blocks
## Example: Using `clone()`

You can duplicate an existing object using the `clone()` method.  
This is useful to reuse the same element multiple times without redefining it.

```python
from fpdf import FPDF

# Create a PDF instance
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=16)

# Original cell
pdf.cell(40, 10, "Original Cell")

# Clone the cell and place it below
cloned = pdf.clone(pdf.cell(40, 10, "Cloned Cell"))

# Save the PDF
pdf.output("clone_example.pdf")
