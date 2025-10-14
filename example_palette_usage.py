"""
Example demonstrating the palette parameter in add_font() for color fonts.
This matches the proposed feature from the issue.
"""

from fpdf import FPDF

# Create a PDF instance
pdf = FPDF()

# Example 1: Add font with palette 0 (default)
pdf.add_font(
    family="Nabla",
    fname="test/color_font/Nabla-Regular-COLRv1-VariableFont_EDPT,EHLT.ttf",
    palette=0
)

# Example 2: Add the same font with palette 2 using a different family name
pdf.add_font(
    family="Nabla-Blue",
    fname="test/color_font/Nabla-Regular-COLRv1-VariableFont_EDPT,EHLT.ttf",
    palette=2
)

# Example 3: Add the same font with palette 3 using another family name
pdf.add_font(
    family="Nabla-Grey",
    fname="test/color_font/Nabla-Regular-COLRv1-VariableFont_EDPT,EHLT.ttf",
    palette=3
)

# Create a page and use the fonts
pdf.add_page()

# Use palette 0
pdf.set_font("Nabla", size=24)
pdf.cell(text="Text with Palette 0", new_x="lmargin", new_y="next")
pdf.ln(5)

# Use palette 2
pdf.set_font("Nabla-Blue", size=24)
pdf.cell(text="Text with Palette 2", new_x="lmargin", new_y="next")
pdf.ln(5)

# Use palette 3
pdf.set_font("Nabla-Grey", size=24)
pdf.cell(text="Text with Palette 3", new_x="lmargin", new_y="next")

# Output the PDF
pdf.output("example_palette_output.pdf")
print("PDF created successfully: example_palette_output.pdf")
