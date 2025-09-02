from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from test.conftest import assert_pdf_equal

import pytest

HERE = Path(__file__).resolve().parent


def test_named_destinations(tmp_path):
    """Test PDF generation with named destinations and links.

    This test demonstrates how to create a hierarchical structure of named destinations
    by reserving names first and then binding them to pages later.
    """
    # Create PDF
    pdf = FPDF()

    # Create the first page first
    pdf.add_page()

    # Then create all named destinations
    # We need to specify the page number for each destination
    main_toc_link = pdf.add_link(name="dests/main", page=1)
    sub1_link = pdf.add_link(name="dests/subsection1", page=2)
    sub2_link = pdf.add_link(name="dests/subsection2", page=3)
    sub3_link = pdf.add_link(name="dests/subsection3", page=4)

    # First page is already created
    pdf.set_font("Helvetica", size=16)
    # Bind the main TOC destination to this location
    pdf.set_link(main_toc_link)
    pdf.cell(0, 10, "Table of Contents", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)
    pdf.set_font("Helvetica", size=12)

    # Add links to subsections in the TOC
    pdf.cell(
        0,
        10,
        "Subsection 1: Concepts",
        link=sub1_link,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    # You can also reference the destination by name
    pdf.cell(
        0,
        10,
        "Subsection 2: Implementation",
        link="#dests/subsection2",  # Using the '#' prefix to reference the named destination
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    # Or retrieve it through get_named_destination
    sub3_ref = pdf.get_named_destination("dests/subsection3")
    pdf.cell(
        0,
        10,
        "Subsection 3: Advanced Usage",
        link=sub3_ref,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    # Subsection 1 page
    pdf.add_page()
    pdf.set_font("Helvetica", size=16)
    # Bind subsection1 destination to this location
    pdf.set_link(sub1_link)
    pdf.cell(0, 10, "Subsection 1: Concepts", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(
        0,
        10,
        (
            "This page demonstrates binding a previously created named destination. "
            "The destination 'dests/subsection1' was created before this page existed "
            "and is now bound to this location.\n\n"
            "Click on the table of contents link to return."
        ),
    )
    # Add a link back to TOC
    pdf.cell(
        0,
        10,
        "Return to Table of Contents",
        link=main_toc_link,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    # Subsection 2 page
    pdf.add_page()
    pdf.set_font("Helvetica", size=16)
    # Bind subsection2 destination to this location
    pdf.set_link(sub2_link)
    pdf.cell(0, 10, "Subsection 2: Implementation", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(
        0,
        10,
        (
            "This page shows how named destinations maintain stability when page numbers "
            "change. Even if pages are added or removed, the named destination 'dests/subsection2' "
            "will always point to this content.\n\n"
            "Click on the table of contents link to return."
        ),
    )
    # Add a link back to TOC
    pdf.cell(
        0,
        10,
        "Return to Table of Contents",
        link="#dests/main",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    # Subsection 3 page
    pdf.add_page()
    pdf.set_font("Helvetica", size=16)
    # Bind subsection3 destination to this location
    pdf.set_link(sub3_link)
    pdf.cell(0, 10, "Subsection 3: Advanced Usage", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(
        0,
        10,
        (
            "Named destinations can be referenced anywhere in the document, including in "
            "bookmarks, outlines, and from external documents. The hierarchical naming scheme "
            "'dests/subsection3' allows for organized structure.\n\n"
            "Click on the table of contents link to return."
        ),
    )
    # Add a link back to TOC using get_named_destination
    toc_ref = pdf.get_named_destination("dests/main")
    pdf.cell(
        0,
        10,
        "Return to Table of Contents",
        link=toc_ref,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    # Compare with reference PDF
    assert_pdf_equal(
        pdf,
        HERE / "test_named_destinations.pdf",
        tmp_path,
    )


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


def test_set_link_with_name():
    """Test setting a named destination using set_link with name parameter."""
    pdf = FPDF()
    pdf.add_page()

    # Create a named destination with set_link
    name = pdf.set_link(name="direct_destination")

    # Verify the name was returned
    assert name == "direct_destination"

    # Verify the destination exists
    assert "direct_destination" in pdf.named_destinations

    # Create another page and reference the destination
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, "Link to first page", link="#direct_destination")

    # This should not raise an error
    dest_link = pdf.get_named_destination("direct_destination")
    assert dest_link is not None
