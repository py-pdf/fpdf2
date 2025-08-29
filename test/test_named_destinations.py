from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from test.conftest import assert_pdf_equal

import pytest

HERE = Path(__file__).resolve().parent


def test_named_destinations(tmp_path):
    """Test PDF generation with named destinations and links."""
    # Create PDF
    pdf = FPDF()

    # First page with table of contents
    pdf.add_page()
    pdf.set_font("Helvetica", size=16)
    pdf.cell(0, 10, "Table of Contents", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)
    pdf.set_font("Helvetica", size=12)

    # Create named destinations and add links in table of contents
    intro_link = pdf.add_link(name="introduction")
    pdf.cell(
        0, 10, "Introduction", link=intro_link, new_x=XPos.LMARGIN, new_y=YPos.NEXT
    )
    chapter1_link = pdf.add_link(name="chapter1")
    pdf.cell(
        0,
        10,
        "Chapter 1: Getting Started",
        link=chapter1_link,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    chapter2_link = pdf.add_link(name="chapter2")
    pdf.cell(
        0,
        10,
        "Chapter 2: Advanced Topics",
        link=chapter2_link,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    # Introduction page
    pdf.add_page()
    pdf.set_font("Helvetica", size=16)
    pdf.set_link(intro_link)
    pdf.cell(0, 10, "Introduction", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(
        0,
        10,
        (
            "This is the introduction section. It explains the basics of the "
            "document.\nClick on the links in the table of contents to navigate."
        ),
    )

    # Chapter 1
    pdf.add_page()
    pdf.set_font("Helvetica", size=16)
    pdf.set_link(chapter1_link)
    pdf.cell(0, 10, "Chapter 1: Getting Started", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(
        0,
        10,
        (
            "This is Chapter 1. It covers the basic concepts.\nYou can return "
            "to the table of contents to navigate to other sections."
        ),
    )

    # Chapter 2
    pdf.add_page()
    pdf.set_font("Helvetica", size=16)
    pdf.set_link(chapter2_link)
    pdf.cell(0, 10, "Chapter 2: Advanced Topics", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(
        0,
        10,
        (
            "This is Chapter 2. It covers more advanced topics.\nTry clicking "
            "different links in the table of contents to test navigation."
        ),
    )

    # Compare with reference PDF
    assert_pdf_equal(pdf, HERE / "test_named_destinations.pdf", tmp_path)


def test_invalid_destination():
    """Test that using non-existent named destinations raises a KeyError."""
    pdf = FPDF()
    pdf.add_page()
    with pytest.raises(KeyError):
        pdf.set_link(99999)


def test_duplicate_destinations():
    """Test that creating multiple destinations with the same name works."""
    pdf = FPDF()
    pdf.add_page()
    link1 = pdf.add_link(name="test")
    link2 = pdf.add_link(name="test")
    # Should not raise any error when setting either link
    pdf.set_link(link1)
    pdf.set_link(link2)
