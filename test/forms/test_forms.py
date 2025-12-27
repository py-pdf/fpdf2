"""
Test script for interactive PDF form fields.
Creates a sample PDF with text fields and checkboxes to verify cross-reader compatibility.
"""

import sys
sys.path.insert(0, r'g:\Stuff\Study\Open Source\fpdf2')

from fpdf import FPDF


def create_test_form():
    """Create a test PDF form with various form fields."""
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Interactive PDF Form Test", ln=True, align="C")
    pdf.ln(10)
    
    # Instructions
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, 
        "This form demonstrates fpdf2's interactive form field support. "
        "You should be able to fill in the text fields and check the checkboxes "
        "in any PDF reader that supports AcroForms (Adobe Acrobat, Sumatra, browsers, etc.)."
    )
    pdf.ln(10)
    
    # Form fields
    pdf.set_font("Helvetica", "", 12)
    
    # Text field - First Name
    pdf.text(10, 60, "First Name:")
    pdf.text_field(
        name="first_name",
        x=50, y=55,
        w=60, h=8,
        value="",
        border_color=(0, 0, 0),
        background_color=(1, 1, 1),
    )
    
    # Text field - Last Name
    pdf.text(10, 75, "Last Name:")
    pdf.text_field(
        name="last_name",
        x=50, y=70,
        w=60, h=8,
        value="",
        border_color=(0, 0, 0),
        background_color=(1, 1, 1),
    )
    
    # Text field - Email
    pdf.text(10, 90, "Email:")
    pdf.text_field(
        name="email",
        x=50, y=85,
        w=100, h=8,
        value="",
        border_color=(0, 0, 0),
        background_color=(0.95, 0.95, 1),  # Light blue background
    )
    
    # Text field - Comments (multiline)
    pdf.text(10, 110, "Comments:")
    pdf.text_field(
        name="comments",
        x=50, y=105,
        w=140, h=30,
        value="",
        multiline=True,
        border_color=(0, 0, 0),
        background_color=(1, 1, 1),
    )
    
    # Checkbox - Subscribe
    pdf.checkbox(
        name="subscribe",
        x=10, y=150,
        size=5,
        checked=False,
    )
    pdf.text(18, 153, "Subscribe to newsletter")
    
    # Checkbox - Terms (pre-checked)
    pdf.checkbox(
        name="agree_terms",
        x=10, y=162,
        size=5,
        checked=True,
    )
    pdf.text(18, 165, "I agree to the terms and conditions")
    
    # Checkbox - Read-only (to test that flag)
    pdf.checkbox(
        name="readonly_check",
        x=10, y=174,
        size=5,
        checked=True,
        read_only=True,
    )
    pdf.text(18, 177, "This checkbox is read-only (cannot be changed)")
    
    # Read-only text field
    pdf.text(10, 195, "Read-only:")
    pdf.text_field(
        name="readonly_field",
        x=50, y=190,
        w=60, h=8,
        value="Cannot edit",
        read_only=True,
        border_color=(0.5, 0.5, 0.5),
        background_color=(0.9, 0.9, 0.9),
    )
    
    # Save the PDF
    output_path = r"g:\Stuff\Study\Open Source\fpdf2\test_form_output.pdf"
    pdf.output(output_path)
    print(f"PDF form created: {output_path}")
    print("\nPlease test this PDF in:")
    print("  - Adobe Acrobat Reader")
    print("  - Sumatra PDF")
    print("  - Chrome/Firefox PDF viewer")
    print("  - Mobile PDF viewers")


if __name__ == "__main__":
    create_test_form()
