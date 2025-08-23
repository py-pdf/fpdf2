"""Unit tests for named destinations in links for FPDF2."""

import os
import pytest
from fpdf import FPDF


def test_add_link_with_named_destination():
    """Test adding a link with a named destination."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=16)

    # Create Table of Contents
    pdf.cell(0, 10, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("helvetica", size=12)

    # Create link with named destination for Section 1
    link1 = pdf.add_link(name="section1")
    pdf.cell(0, 10, "1. Introduction", link=link1, new_x="LMARGIN", new_y="NEXT")

    # Create link with named destination for Section 2
    link2 = pdf.add_link(name="section2")
    pdf.cell(0, 10, "2. Named Destinations", link=link2, new_x="LMARGIN", new_y="NEXT")

    # Add content pages with destinations
    pdf.add_page()
    pdf.set_font("helvetica", size=16)
    pdf.cell(0, 10, "1. Introduction", new_x="LMARGIN", new_y="NEXT")
    pdf.set_link(link1)  # Set Section 1 destination

    pdf.set_font("helvetica", size=12)
    pdf.multi_cell(
        0,
        10,
        "This is the introduction section. Click on the Table of Contents to navigate.",
    )

    pdf.add_page()
    pdf.set_font("helvetica", size=16)
    pdf.cell(0, 10, "2. Named Destinations", new_x="LMARGIN", new_y="NEXT")
    pdf.set_link(link2)  # Set Section 2 destination

    pdf.set_font("helvetica", size=12)
    pdf.multi_cell(
        0,
        10,
        "This section explains named destinations. They allow you to create bookmarks in your PDF document.",
    )

    # Verify the named destinations were created
    assert "section1" in pdf.named_destinations
    assert "section2" in pdf.named_destinations
    assert pdf.named_destinations["section1"].page_number == 2  # First content page
    assert pdf.named_destinations["section2"].page_number == 3  # Second content page

    # Save the PDF to verify the output
    pdf.output("D:/tech entre/contribuition/fdpdf/test/named_dest.pdf")

    # Assert the generated PDF matches expected output
    assert os.path.exists(
        "D:/tech entre/contribuition/fdpdf/test/named_dest.pdf"
    ), "PDF file was not created"

    # Clean up the test file


def test_add_link_with_invalid_named_destination():
    """Test adding a link with invalid named destination."""
    pdf = FPDF()
    pdf.add_page()

    with pytest.raises(ValueError):
        pdf.add_link(name="")  # Empty name

    with pytest.raises(ValueError):
        pdf.add_link(name=" ")  # Only whitespace
