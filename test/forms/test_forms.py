"""
Tests for interactive PDF form fields (AcroForms).
"""

from pathlib import Path

from fpdf import FPDF

from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def test_text_field_basic(tmp_path):
    """Test basic text field creation."""
    pdf = FPDF()
    pdf.add_page()
    pdf.text_field(
        name="test_field",
        x=10, y=10,
        w=60, h=8,
        value="initial",
        border_color=(0, 0, 0),
        background_color=(1, 1, 1),
    )
    assert_pdf_equal(pdf, HERE / "text_field_basic.pdf", tmp_path)


def test_text_field_multiline(tmp_path):
    """Test multiline text field creation."""
    pdf = FPDF()
    pdf.add_page()
    pdf.text_field(
        name="multiline_field",
        x=10, y=10,
        w=100, h=30,
        value="line1",
        multiline=True,
        border_color=(0, 0, 0),
        background_color=(1, 1, 1),
    )
    assert_pdf_equal(pdf, HERE / "text_field_multiline.pdf", tmp_path)


def test_text_field_readonly(tmp_path):
    """Test read-only text field."""
    pdf = FPDF()
    pdf.add_page()
    pdf.text_field(
        name="readonly_field",
        x=10, y=10,
        w=60, h=8,
        value="Cannot edit",
        read_only=True,
    )
    assert_pdf_equal(pdf, HERE / "text_field_readonly.pdf", tmp_path)


def test_checkbox_unchecked(tmp_path):
    """Test unchecked checkbox creation."""
    pdf = FPDF()
    pdf.add_page()
    pdf.checkbox(
        name="unchecked_box",
        x=10, y=10,
        size=10,
        checked=False,
    )
    assert_pdf_equal(pdf, HERE / "checkbox_unchecked.pdf", tmp_path)


def test_checkbox_checked(tmp_path):
    """Test pre-checked checkbox creation."""
    pdf = FPDF()
    pdf.add_page()
    pdf.checkbox(
        name="checked_box",
        x=10, y=10,
        size=10,
        checked=True,
    )
    assert_pdf_equal(pdf, HERE / "checkbox_checked.pdf", tmp_path)


def test_checkbox_readonly(tmp_path):
    """Test read-only checkbox."""
    pdf = FPDF()
    pdf.add_page()
    pdf.checkbox(
        name="readonly_box",
        x=10, y=10,
        size=10,
        checked=True,
        read_only=True,
    )
    assert_pdf_equal(pdf, HERE / "checkbox_readonly.pdf", tmp_path)


def test_form_with_multiple_fields(tmp_path):
    """Test form with multiple fields of different types."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 12)

    # Add text fields
    pdf.text(10, 20, "First Name:")
    pdf.text_field(
        name="first_name",
        x=50, y=15,
        w=60, h=8,
        value="",
        border_color=(0, 0, 0),
        background_color=(1, 1, 1),
    )

    pdf.text(10, 35, "Last Name:")
    pdf.text_field(
        name="last_name",
        x=50, y=30,
        w=60, h=8,
        value="",
        border_color=(0, 0, 0),
        background_color=(1, 1, 1),
    )

    # Add checkboxes
    pdf.checkbox(
        name="subscribe",
        x=10, y=50,
        size=5,
        checked=False,
    )
    pdf.text(18, 53, "Subscribe to newsletter")

    pdf.checkbox(
        name="agree_terms",
        x=10, y=62,
        size=5,
        checked=True,
    )
    pdf.text(18, 65, "I agree to the terms")

    assert_pdf_equal(pdf, HERE / "form_multiple_fields.pdf", tmp_path)
