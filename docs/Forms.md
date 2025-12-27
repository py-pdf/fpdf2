# Interactive Forms (AcroForms)

`fpdf2` supports creating interactive PDF forms that users can fill out directly in their PDF viewer. This is implemented using the AcroForm standard.

Currently supported field types:
* **Text Fields**: Single-line, multi-line, and password inputs.
* **Checkboxes**: Toggleable buttons.

## Basic Usage

To add form fields, use the `text_field()` and `checkbox()` methods.

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

## Field Properties

Both field types support common properties:

* `read_only`: If `True`, the user cannot modify the field value.
* `required`: If `True`, the field must be filled before the form can be submitted.

## Compatibility

`fpdf2` generates **Appearance Streams** for all form fields. This ensures that the fields are visible and rendered correctly across almost all PDF readers, including:
* Adobe Acrobat Reader
* Chrome / Firefox / Edge built-in viewers
* Sumatra PDF
* Mobile PDF viewers

Note: Form fields require PDF version 1.4 or higher. `fpdf2` will automatically set the document version to 1.4 if any form fields are added.
