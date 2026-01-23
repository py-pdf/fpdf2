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


def test_radio_button_unselected(tmp_path):
    """Test unselected radio button creation."""
    pdf = FPDF()
    pdf.add_page()
    pdf.radio_button(
        name="choice_group",
        x=10, y=10,
        size=10,
        selected=False,
        export_value="Option1",
    )
    assert_pdf_equal(pdf, HERE / "radio_button_unselected.pdf", tmp_path)


def test_radio_button_selected(tmp_path):
    """Test pre-selected radio button creation."""
    pdf = FPDF()
    pdf.add_page()
    pdf.radio_button(
        name="choice_group",
        x=10, y=10,
        size=10,
        selected=True,
        export_value="Option1",
    )
    assert_pdf_equal(pdf, HERE / "radio_button_selected.pdf", tmp_path)


def test_radio_button_group(tmp_path):
    """Test radio button group (multiple options with same name)."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)

    pdf.text(25, 15, "Option A")
    pdf.radio_button(
        name="radio_group",
        x=10, y=10,
        size=8,
        selected=True,
        export_value="OptionA",
    )

    pdf.text(25, 30, "Option B")
    pdf.radio_button(
        name="radio_group",
        x=10, y=25,
        size=8,
        selected=False,
        export_value="OptionB",
    )

    pdf.text(25, 45, "Option C")
    pdf.radio_button(
        name="radio_group",
        x=10, y=40,
        size=8,
        selected=False,
        export_value="OptionC",
    )

    assert_pdf_equal(pdf, HERE / "radio_button_group.pdf", tmp_path)


def test_push_button_basic(tmp_path):
    """Test basic push button creation."""
    pdf = FPDF()
    pdf.add_page()
    pdf.push_button(
        name="submit_btn",
        x=10, y=10,
        w=60, h=20,
        label="Submit",
    )
    assert_pdf_equal(pdf, HERE / "push_button_basic.pdf", tmp_path)


def test_push_button_styled(tmp_path):
    """Test styled push button creation."""
    pdf = FPDF()
    pdf.add_page()
    pdf.push_button(
        name="styled_btn",
        x=10, y=10,
        w=80, h=25,
        label="Click Me",
        font_size=14,
        background_color=(0.2, 0.4, 0.8),
        border_color=(0, 0, 0.5),
    )
    assert_pdf_equal(pdf, HERE / "push_button_styled.pdf", tmp_path)


def test_combo_box_basic(tmp_path):
    """Test basic combo box (dropdown) creation."""
    pdf = FPDF()
    pdf.add_page()
    pdf.combo_box(
        name="country",
        x=10, y=10,
        w=80, h=10,
        options=["United States", "Canada", "Mexico", "Other"],
        value="United States",
    )
    assert_pdf_equal(pdf, HERE / "combo_box_basic.pdf", tmp_path)


def test_combo_box_editable(tmp_path):
    """Test editable combo box creation."""
    pdf = FPDF()
    pdf.add_page()
    pdf.combo_box(
        name="custom_option",
        x=10, y=10,
        w=80, h=10,
        options=["Red", "Green", "Blue"],
        value="",
        editable=True,
    )
    assert_pdf_equal(pdf, HERE / "combo_box_editable.pdf", tmp_path)


def test_list_box_basic(tmp_path):
    """Test basic list box creation."""
    pdf = FPDF()
    pdf.add_page()
    pdf.list_box(
        name="fruits",
        x=10, y=10,
        w=80, h=50,
        options=["Apple", "Banana", "Cherry", "Date", "Elderberry"],
        value="Apple",
    )
    assert_pdf_equal(pdf, HERE / "list_box_basic.pdf", tmp_path)


def test_list_box_multi_select(tmp_path):
    """Test multi-select list box creation."""
    pdf = FPDF()
    pdf.add_page()
    pdf.list_box(
        name="colors",
        x=10, y=10,
        w=80, h=60,
        options=["Red", "Orange", "Yellow", "Green", "Blue", "Purple"],
        value="Green",
        multi_select=True,
    )
    assert_pdf_equal(pdf, HERE / "list_box_multi_select.pdf", tmp_path)


def test_complete_form_with_all_field_types(tmp_path):
    """Test form with all field types together."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)

    # Text field
    pdf.text(10, 20, "Name:")
    pdf.text_field(
        name="name",
        x=40, y=15,
        w=80, h=8,
        value="",
        border_color=(0, 0, 0),
    )

    # Checkbox
    pdf.checkbox(
        name="newsletter",
        x=10, y=35,
        size=5,
        checked=False,
    )
    pdf.text(18, 38, "Subscribe to newsletter")

    # Radio buttons
    pdf.text(10, 55, "Preferred Contact:")
    pdf.text(35, 55, "Email")
    pdf.radio_button(
        name="contact_method",
        x=25, y=50,
        size=6,
        selected=True,
        export_value="email",
    )
    pdf.text(70, 55, "Phone")
    pdf.radio_button(
        name="contact_method",
        x=60, y=50,
        size=6,
        selected=False,
        export_value="phone",
    )

    # Combo box
    pdf.text(10, 75, "Country:")
    pdf.combo_box(
        name="country",
        x=40, y=70,
        w=60, h=8,
        options=["USA", "Canada", "UK", "Other"],
        value="USA",
    )

    # List box
    pdf.text(10, 95, "Interests:")
    pdf.list_box(
        name="interests",
        x=40, y=90,
        w=60, h=30,
        options=["Sports", "Music", "Travel", "Technology", "Art"],
        value="",
        multi_select=True,
    )

    # Push button
    pdf.push_button(
        name="submit",
        x=60, y=130,
        w=50, h=15,
        label="Submit",
    )

    assert_pdf_equal(pdf, HERE / "complete_form.pdf", tmp_path)
