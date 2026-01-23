# Interactive Forms (AcroForms)

`fpdf2` supports creating interactive PDF forms that users can fill out directly in their PDF viewer. This is implemented using the AcroForm standard.

Currently supported field types:
* **Text Fields**: Single-line, multi-line, and password inputs.
* **Checkboxes**: Toggleable buttons.
* **Radio Buttons**: Groups of mutually exclusive options.
* **Push Buttons**: Clickable buttons (typically used for form submission or actions).
* **Combo Boxes**: Dropdown selection lists.
* **List Boxes**: Scrollable selection lists with optional multi-select.

## Basic Usage

To add form fields, use the corresponding methods for each field type.

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Helvetica", size=12)

# Add a label and a text field
pdf.text(10, 20, "First Name:")
pdf.text_field(name="first_name", x=40, y=15, w=50, h=10, value="John")

# Add a checkbox
pdf.checkbox(name="subscribe", x=10, y=30, size=5, checked=True)
pdf.text(17, 34, "Subscribe to newsletter")

# Add radio buttons
pdf.text(10, 50, "Preferred contact:")
pdf.text(30, 50, "Email")
pdf.radio_button(name="contact", x=20, y=46, size=6, selected=True, export_value="email")
pdf.text(60, 50, "Phone")
pdf.radio_button(name="contact", x=50, y=46, size=6, selected=False, export_value="phone")

# Add a dropdown (combo box)
pdf.text(10, 65, "Country:")
pdf.combo_box(name="country", x=35, y=60, w=60, h=10, 
              options=["USA", "Canada", "UK", "Other"], value="USA")

# Add a submit button
pdf.push_button(name="submit", x=40, y=80, w=40, h=15, label="Submit")

pdf.output("form.pdf")
```

## Text Fields

The `text_field()` method supports several customization options:

| Parameter | Description |
| --- | --- |
| `name` | Unique identifier for the field. |
| `value` | Initial text content. |
| `multiline` | If `True`, the field allows multiple lines of text. |
| `password` | If `True`, characters are masked (e.g., with bullets). |
| `max_length` | Maximum number of characters allowed. |
| `font_size` | Size of the text in the field. |
| `font_color_gray` | Gray level (0-1) for the text. |
| `background_color` | RGB tuple (0-1) for the field background. |
| `border_color` | RGB tuple (0-1) for the field border. |

### Example: Multiline Text Area

```python
pdf.text_field(
    name="comments",
    x=10,
    y=50,
    w=100,
    h=30,
    multiline=True,
    value="Enter your comments here..."
)
```

## Checkboxes

The `checkbox()` method creates a toggleable button.

| Parameter | Description |
| --- | --- |
| `name` | Unique identifier for the checkbox. |
| `checked` | Initial state of the checkbox. |
| `size` | Width and height of the checkbox. |
| `check_color_gray` | Gray level (0-1) for the checkmark. |

## Radio Buttons

The `radio_button()` method creates radio buttons. Radio buttons with the same `name` form a group where only one can be selected at a time.

| Parameter | Description |
| --- | --- |
| `name` | Name for the radio button group. Buttons with the same name are mutually exclusive. |
| `selected` | Initial selected state of this button. |
| `export_value` | Value exported when this button is selected. |
| `size` | Diameter of the radio button. |
| `mark_color_gray` | Gray level (0-1) for the selection mark. |
| `no_toggle_to_off` | If `True`, clicking the selected button doesn't deselect it. |

### Example: Radio Button Group

```python
pdf.text(10, 20, "Size:")
pdf.radio_button(name="size", x=35, y=16, size=8, selected=True, export_value="Small")
pdf.text(47, 20, "Small")

pdf.radio_button(name="size", x=70, y=16, size=8, selected=False, export_value="Medium")
pdf.text(82, 20, "Medium")

pdf.radio_button(name="size", x=110, y=16, size=8, selected=False, export_value="Large")
pdf.text(122, 20, "Large")
```

## Push Buttons

The `push_button()` method creates a clickable button. Push buttons are typically used with JavaScript actions for form submission or other interactions.

| Parameter | Description |
| --- | --- |
| `name` | Unique identifier for the button. |
| `label` | Text displayed on the button. |
| `w` | Width of the button. |
| `h` | Height of the button. |
| `font_size` | Size of the label text. |
| `font_color_gray` | Gray level (0-1) for the label text. |
| `background_color` | RGB tuple (0-1) for the button background. |
| `border_color` | RGB tuple (0-1) for the button border. |

### Example: Styled Button

```python
pdf.push_button(
    name="submit",
    x=50, y=100,
    w=60, h=20,
    label="Submit Form",
    font_size=14,
    background_color=(0.2, 0.4, 0.8),
    border_color=(0, 0, 0.5)
)
```

## Combo Boxes (Dropdowns)

The `combo_box()` method creates a dropdown selection list.

| Parameter | Description |
| --- | --- |
| `name` | Unique identifier for the field. |
| `options` | List of option strings. |
| `value` | Initially selected value. |
| `editable` | If `True`, the user can type a custom value. |
| `w` | Width of the combo box. |
| `h` | Height of the combo box. |

### Example: Editable Combo Box

```python
pdf.combo_box(
    name="color",
    x=10, y=30,
    w=80, h=10,
    options=["Red", "Green", "Blue", "Custom"],
    value="",
    editable=True  # User can type a custom color
)
```

## List Boxes

The `list_box()` method creates a scrollable list where users can select one or more options.

| Parameter | Description |
| --- | --- |
| `name` | Unique identifier for the field. |
| `options` | List of option strings. |
| `value` | Initially selected value. |
| `multi_select` | If `True`, multiple options can be selected. |
| `w` | Width of the list box. |
| `h` | Height of the list box. |

### Example: Multi-Select List Box

```python
pdf.list_box(
    name="interests",
    x=10, y=50,
    w=80, h=50,
    options=["Sports", "Music", "Travel", "Technology", "Art", "Food"],
    value="",
    multi_select=True
)
```

## Field Properties

All field types support common properties:

* `read_only`: If `True`, the user cannot modify the field value.
* `required`: If `True`, the field must be filled before the form can be submitted.

## Compatibility

`fpdf2` generates **Appearance Streams** for all form fields. This ensures that the fields are visible and rendered correctly across almost all PDF readers, including:
* Adobe Acrobat Reader
* Chrome / Firefox / Edge built-in viewers
* Sumatra PDF
* Mobile PDF viewers

Note: Form fields require PDF version 1.4 or higher. `fpdf2` will automatically set the document version to 1.4 if any form fields are added.
