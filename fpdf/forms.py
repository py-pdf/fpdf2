"""
Interactive PDF form fields (AcroForms).

The contents of this module are internal to fpdf2, and not part of the public API.
They may change at any time without prior warning or any deprecation period,
in non-backward-compatible ways.
"""

from .annotations import PDFAnnotation
from .enums import FieldFlag
from .syntax import Name, PDFArray, PDFContentStream, PDFString


# Standard font resource dictionaries for appearance streams.
# These MUST be included in each appearance XObject's /Resources for Adobe Acrobat compatibility.
# Browser PDF viewers are more lenient and may use AcroForm's /DR, but Acrobat requires local resources.
# /ProcSet is required by Adobe Acrobat to properly interpret the content stream operators.
HELV_FONT_RESOURCE = "<</ProcSet [/PDF /Text] /Font <</Helv <</Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding>>>>>>"
ZADB_FONT_RESOURCE = "<</ProcSet [/PDF /Text] /Font <</ZaDb <</Type /Font /Subtype /Type1 /BaseFont /ZapfDingbats>>>>>>"
HELV_ZADB_FONT_RESOURCE = "<</ProcSet [/PDF /Text] /Font <</Helv <</Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding>> /ZaDb <</Type /Font /Subtype /Type1 /BaseFont /ZapfDingbats>>>>>>"
# Graphics-only resources dictionary - for appearance streams that use only path operators (no text)
# /ProcSet [/PDF] tells the viewer this stream uses PDF graphics operators
GRAPHICS_ONLY_RESOURCES = "<</ProcSet [/PDF]>>"


class PDFFormXObject(PDFContentStream):
    """A Form XObject used for appearance streams of form fields."""

    def __init__(self, commands: str, width: float, height: float, resources: str = None):
        if isinstance(commands, str):
            commands = commands.encode("latin-1")
        super().__init__(contents=commands, compress=False)
        self.type = Name("XObject")
        self.subtype = Name("Form")
        self.b_box = PDFArray([0, 0, round(width, 2), round(height, 2)])
        self.form_type = 1
        self._resources_str = resources

    @property
    def resources(self):
        return self._resources_str


class FormField(PDFAnnotation):
    """Base class for interactive form fields."""

    def __init__(
        self,
        field_type: str,
        field_name: str,
        x: float,
        y: float,
        width: float,
        height: float,
        value=None,
        default_value=None,
        field_flags: int = 0,
        **kwargs,
    ):
        super().__init__(
            subtype="Widget",
            x=x,
            y=y,
            width=width,
            height=height,
            field_type=field_type,
            value=value,
            **kwargs,
        )
        self.t = PDFString(field_name, encrypt=True)
        self.d_v = default_value
        self.f_f = field_flags if field_flags else None
        self._width = width
        self._height = height
        self._appearance_normal = None
        self._appearance_dict = None

    def _generate_appearance(self, font_name: str = "Helv", font_size: float = 12):
        """Generate the appearance stream for this field. Must be overridden by subclasses."""
        raise NotImplementedError("Subclasses must implement _generate_appearance")

    @property
    def a_p(self):
        """Return the appearance dictionary (/AP) for serialization."""
        if self._appearance_dict:
            return self._appearance_dict
        if self._appearance_normal:
            return f"<</N {self._appearance_normal.ref}>>"
        return None


class TextField(FormField):
    """An interactive text input field."""

    def __init__(
        self,
        field_name: str,
        x: float,
        y: float,
        width: float,
        height: float,
        value: str = "",
        font_size: float = 12,
        font_color_gray: float = 0,
        background_color: tuple = None,
        border_color: tuple = None,
        border_width: float = 1,
        max_length: int = None,
        multiline: bool = False,
        password: bool = False,
        read_only: bool = False,
        required: bool = False,
        **kwargs,
    ):
        field_flags = 0
        if multiline:
            field_flags |= FieldFlag.MULTILINE
        if password:
            field_flags |= FieldFlag.PASSWORD
        if read_only:
            field_flags |= FieldFlag.READ_ONLY
        if required:
            field_flags |= FieldFlag.REQUIRED

        super().__init__(
            field_type="Tx",
            field_name=field_name,
            x=x,
            y=y,
            width=width,
            height=height,
            value=PDFString(value, encrypt=True) if value else None,
            default_value=PDFString(value, encrypt=True) if value else None,
            field_flags=field_flags,
            border_width=border_width,
            **kwargs,
        )

        self._font_size = font_size
        self._font_color_gray = font_color_gray
        self._background_color = background_color
        self._border_color = border_color
        self._multiline = multiline
        self._value_str = value or ""
        self.max_len = max_length
        # Default Appearance (/DA): PDF content stream fragment specifying font and color.
        # Format: "/FontName FontSize Tf GrayLevel g" (e.g., "/Helv 12 Tf 0 g" = Helvetica 12pt black)
        # Must be a PDFString so it serializes with parentheses as required by PDF spec.
        self.d_a = PDFString(f"/Helv {font_size:.2f} Tf {font_color_gray:.2f} g")

    def _generate_appearance(self, font_name: str = "Helv", font_size: float = None):
        """Generate the appearance stream XObject for this text field."""
        if font_size is None:
            font_size = self._font_size

        width = self._width
        height = self._height
        value = self._value_str

        commands = []
        commands.append("/Tx BMC")
        commands.append("q")

        if self._background_color:
            r, g, b = self._background_color
            commands.append(f"{r:.3f} {g:.3f} {b:.3f} rg")
            commands.append(f"0 0 {width:.2f} {height:.2f} re")
            commands.append("f")

        if self._border_color:
            r, g, b = self._border_color
            commands.append(f"{r:.3f} {g:.3f} {b:.3f} RG")
            commands.append("1 w")
            commands.append(f"0.5 0.5 {width - 1:.2f} {height - 1:.2f} re")
            commands.append("S")

        if value:
            commands.append(f"2 2 {width - 4:.2f} {height - 4:.2f} re W n")
            commands.append("BT")
            commands.append(f"/{font_name} {font_size:.2f} Tf")
            commands.append(f"{self._font_color_gray:.2f} g")
            
            text_y = (height - font_size) / 2 + 2
            if self._multiline:
                text_y = height - font_size - 2
            commands.append(f"2 {text_y:.2f} Td")
            
            escaped_value = value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            commands.append(f"({escaped_value}) Tj")
            commands.append("ET")

        commands.append("Q")
        commands.append("EMC")

        content = "\n".join(commands)

        # Include font resources in the appearance XObject for Adobe Acrobat compatibility
        self._appearance_normal = PDFFormXObject(content, width, height, resources=HELV_FONT_RESOURCE)
        return self._appearance_normal


class Checkbox(FormField):
    """An interactive checkbox field."""

    CHECK_CHAR = "4"

    def __init__(
        self,
        field_name: str,
        x: float,
        y: float,
        size: float = 12,
        checked: bool = False,
        background_color: tuple = (1, 1, 1),
        border_color: tuple = (0, 0, 0),
        check_color_gray: float = 0,
        border_width: float = 1,
        read_only: bool = False,
        required: bool = False,
        **kwargs,
    ):
        field_flags = 0
        if read_only:
            field_flags |= FieldFlag.READ_ONLY
        if required:
            field_flags |= FieldFlag.REQUIRED

        value = Name("Yes") if checked else Name("Off")

        super().__init__(
            field_type="Btn",
            field_name=field_name,
            x=x,
            y=y,
            width=size,
            height=size,
            value=value,
            default_value=value,
            field_flags=field_flags,
            border_width=border_width,
            **kwargs,
        )

        self._size = size
        self._checked = checked
        self._background_color = background_color
        self._border_color = border_color
        self._check_color_gray = check_color_gray
        # Default Appearance (/DA): PDF content stream fragment for the checkmark.
        # Uses ZapfDingbats font (/ZaDb) which contains the checkmark character.
        # Must be a PDFString so it serializes with parentheses as required by PDF spec.
        self.d_a = PDFString(f"/ZaDb {size * 0.8:.2f} Tf {check_color_gray:.2f} g")
        self.a_s = Name("Yes") if checked else Name("Off")

    def _generate_appearance(self, font_name: str = "ZaDb", font_size: float = None):
        """Generate appearance streams for checked and unchecked states."""
        size = self._size
        if font_size is None:
            font_size = size * 0.8

        off_commands = self._generate_box_appearance(size, show_check=False)
        # Use graphics-only resources since checkmark is drawn with path operators (no font)
        off_xobj = PDFFormXObject(off_commands, size, size, resources=GRAPHICS_ONLY_RESOURCES)

        yes_commands = self._generate_box_appearance(size, show_check=True, font_size=font_size)
        yes_xobj = PDFFormXObject(yes_commands, size, size, resources=GRAPHICS_ONLY_RESOURCES)

        self._appearance_off = off_xobj
        self._appearance_yes = yes_xobj

        return off_xobj, yes_xobj

    def _generate_box_appearance(self, size: float, show_check: bool, font_size: float = None) -> str:
        """Generate the appearance commands for a checkbox box."""
        commands = []
        commands.append("q")

        if self._background_color:
            r, g, b = self._background_color
            commands.append(f"{r:.3f} {g:.3f} {b:.3f} rg")
            commands.append(f"0 0 {size:.2f} {size:.2f} re")
            commands.append("f")

        if self._border_color:
            r, g, b = self._border_color
            commands.append(f"{r:.3f} {g:.3f} {b:.3f} RG")
            commands.append("1 w")
            commands.append(f"0.5 0.5 {size - 1:.2f} {size - 1:.2f} re")
            commands.append("S")

        if show_check:
            # Draw graphical checkmark using path operators (no font dependency)
            # This ensures compatibility with Adobe Acrobat without font resolution issues
            commands.append(f"{self._check_color_gray:.2f} G")  # Stroke color (gray)
            line_width = max(1.5, size * 0.12)  # Scale line width with checkbox size
            commands.append(f"{line_width:.2f} w")
            commands.append("1 J")  # Round line caps
            commands.append("1 j")  # Round line joins
            # Checkmark path: starts from left, goes down to bottom-center, then up to top-right
            x1 = size * 0.20  # Start point (left side)
            y1 = size * 0.55
            x2 = size * 0.40  # Bottom point (center-left)
            y2 = size * 0.25
            x3 = size * 0.80  # End point (top-right)
            y3 = size * 0.80
            commands.append(f"{x1:.2f} {y1:.2f} m")  # Move to start
            commands.append(f"{x2:.2f} {y2:.2f} l")  # Line to bottom
            commands.append(f"{x3:.2f} {y3:.2f} l")  # Line to top-right
            commands.append("S")  # Stroke the path

        commands.append("Q")
        return "\n".join(commands)

    @property
    def a_p(self):
        """Return the appearance dictionary for checkbox."""
        if self._appearance_off and self._appearance_yes:
            return f"<</N <</Off {self._appearance_off.ref} /Yes {self._appearance_yes.ref}>>>>"
        return None


class RadioButton(FormField):
    """
    An interactive radio button field.
    
    Radio buttons work in groups - buttons with the same name are part of a group,
    and selecting one deselects the others.
    """

    # ZapfDingbats bullet character for radio button
    BULLET_CHAR = "l"  # Filled circle in ZapfDingbats

    def __init__(
        self,
        field_name: str,
        x: float,
        y: float,
        size: float = 12,
        selected: bool = False,
        export_value: str = "Choice1",
        background_color: tuple = (1, 1, 1),
        border_color: tuple = (0, 0, 0),
        mark_color_gray: float = 0,
        border_width: float = 1,
        read_only: bool = False,
        required: bool = False,
        no_toggle_to_off: bool = True,
        **kwargs,
    ):
        field_flags = FieldFlag.RADIO
        if read_only:
            field_flags |= FieldFlag.READ_ONLY
        if required:
            field_flags |= FieldFlag.REQUIRED
        if no_toggle_to_off:
            field_flags |= FieldFlag.NO_TOGGLE_TO_OFF

        value = Name(export_value) if selected else Name("Off")

        super().__init__(
            field_type="Btn",
            field_name=field_name,
            x=x,
            y=y,
            width=size,
            height=size,
            value=value,
            default_value=value,
            field_flags=field_flags,
            border_width=border_width,
            **kwargs,
        )

        self._size = size
        self._selected = selected
        self._export_value = export_value
        self._background_color = background_color
        self._border_color = border_color
        self._mark_color_gray = mark_color_gray
        self.d_a = PDFString(f"/ZaDb {size * 0.6:.2f} Tf {mark_color_gray:.2f} g")
        self.a_s = Name(export_value) if selected else Name("Off")

    def _generate_appearance(self, font_name: str = "ZaDb", font_size: float = None):
        """Generate appearance streams for selected and unselected states."""
        size = self._size

        off_commands = self._generate_circle_appearance(size, show_mark=False)
        # Use graphics-only resources since circles are drawn with path operators (no font)
        off_xobj = PDFFormXObject(off_commands, size, size, resources=GRAPHICS_ONLY_RESOURCES)

        on_commands = self._generate_circle_appearance(size, show_mark=True)
        # Use graphics-only resources since circles are drawn with path operators (no font)
        on_xobj = PDFFormXObject(on_commands, size, size, resources=GRAPHICS_ONLY_RESOURCES)

        self._appearance_off = off_xobj
        self._appearance_on = on_xobj

        return off_xobj, on_xobj

    def _generate_circle_appearance(self, size: float, show_mark: bool, font_size: float = None) -> str:
        """Generate the appearance commands for a radio button circle."""
        commands = []
        commands.append("q")

        # Draw circle using Bezier curves (approximation)
        cx, cy = size / 2, size / 2
        r = size / 2 - 1  # radius with margin for border

        # Bezier control point offset for circle approximation
        k = 0.5523  # (4/3) * (sqrt(2) - 1)
        kr = k * r

        if self._background_color:
            r_col, g_col, b_col = self._background_color
            commands.append(f"{r_col:.3f} {g_col:.3f} {b_col:.3f} rg")
            # Draw filled circle
            commands.append(f"{cx + r:.2f} {cy:.2f} m")
            commands.append(f"{cx + r:.2f} {cy + kr:.2f} {cx + kr:.2f} {cy + r:.2f} {cx:.2f} {cy + r:.2f} c")
            commands.append(f"{cx - kr:.2f} {cy + r:.2f} {cx - r:.2f} {cy + kr:.2f} {cx - r:.2f} {cy:.2f} c")
            commands.append(f"{cx - r:.2f} {cy - kr:.2f} {cx - kr:.2f} {cy - r:.2f} {cx:.2f} {cy - r:.2f} c")
            commands.append(f"{cx + kr:.2f} {cy - r:.2f} {cx + r:.2f} {cy - kr:.2f} {cx + r:.2f} {cy:.2f} c")
            commands.append("f")

        if self._border_color:
            r_col, g_col, b_col = self._border_color
            commands.append(f"{r_col:.3f} {g_col:.3f} {b_col:.3f} RG")
            commands.append("1 w")
            # Draw circle outline
            commands.append(f"{cx + r:.2f} {cy:.2f} m")
            commands.append(f"{cx + r:.2f} {cy + kr:.2f} {cx + kr:.2f} {cy + r:.2f} {cx:.2f} {cy + r:.2f} c")
            commands.append(f"{cx - kr:.2f} {cy + r:.2f} {cx - r:.2f} {cy + kr:.2f} {cx - r:.2f} {cy:.2f} c")
            commands.append(f"{cx - r:.2f} {cy - kr:.2f} {cx - kr:.2f} {cy - r:.2f} {cx:.2f} {cy - r:.2f} c")
            commands.append(f"{cx + kr:.2f} {cy - r:.2f} {cx + r:.2f} {cy - kr:.2f} {cx + r:.2f} {cy:.2f} c")
            commands.append("s")

        if show_mark:
            # Draw a smaller filled circle as the selection mark (graphical, no font needed)
            mark_r = r * 0.5  # Inner mark is 50% of the outer radius
            mark_kr = k * mark_r
            commands.append(f"{self._mark_color_gray:.3f} g")
            commands.append(f"{cx + mark_r:.2f} {cy:.2f} m")
            commands.append(f"{cx + mark_r:.2f} {cy + mark_kr:.2f} {cx + mark_kr:.2f} {cy + mark_r:.2f} {cx:.2f} {cy + mark_r:.2f} c")
            commands.append(f"{cx - mark_kr:.2f} {cy + mark_r:.2f} {cx - mark_r:.2f} {cy + mark_kr:.2f} {cx - mark_r:.2f} {cy:.2f} c")
            commands.append(f"{cx - mark_r:.2f} {cy - mark_kr:.2f} {cx - mark_kr:.2f} {cy - mark_r:.2f} {cx:.2f} {cy - mark_r:.2f} c")
            commands.append(f"{cx + mark_kr:.2f} {cy - mark_r:.2f} {cx + mark_r:.2f} {cy - mark_kr:.2f} {cx + mark_r:.2f} {cy:.2f} c")
            commands.append("f")

        commands.append("Q")
        return "\n".join(commands)

    @property
    def a_p(self):
        """Return the appearance dictionary for radio button."""
        if self._appearance_off and self._appearance_on:
            # Use the export value directly (it's already a string)
            return f"<</N <</Off {self._appearance_off.ref} /{self._export_value} {self._appearance_on.ref}>>>>"
        return None


class PushButton(FormField):
    """
    An interactive push button field.
    
    Push buttons do not retain a permanent value and are typically used
    to trigger actions like form submission or reset.
    """

    def __init__(
        self,
        field_name: str,
        x: float,
        y: float,
        width: float,
        height: float,
        label: str = "",
        font_size: float = 12,
        font_color_gray: float = 0,
        background_color: tuple = (0.9, 0.9, 0.9),
        border_color: tuple = (0, 0, 0),
        border_width: float = 1,
        read_only: bool = False,
        **kwargs,
    ):
        field_flags = FieldFlag.PUSH_BUTTON
        if read_only:
            field_flags |= FieldFlag.READ_ONLY

        super().__init__(
            field_type="Btn",
            field_name=field_name,
            x=x,
            y=y,
            width=width,
            height=height,
            value=None,
            default_value=None,
            field_flags=field_flags,
            border_width=border_width,
            **kwargs,
        )

        self._width = width
        self._height = height
        self._label = label
        self._font_size = font_size
        self._font_color_gray = font_color_gray
        self._background_color = background_color
        self._border_color = border_color
        self.d_a = PDFString(f"/Helv {font_size:.2f} Tf {font_color_gray:.2f} g")

    def _generate_appearance(self, font_name: str = "Helv", font_size: float = None):
        """Generate the appearance stream XObject for this push button."""
        if font_size is None:
            font_size = self._font_size

        width = self._width
        height = self._height
        label = self._label

        commands = []
        commands.append("q")

        # Background
        if self._background_color:
            r, g, b = self._background_color
            commands.append(f"{r:.3f} {g:.3f} {b:.3f} rg")
            commands.append(f"0 0 {width:.2f} {height:.2f} re")
            commands.append("f")

        # Border with 3D effect
        if self._border_color:
            # Light edge (top and left)
            commands.append("1 1 1 RG")
            commands.append("1 w")
            commands.append(f"0 0 m {width:.2f} 0 l S")
            commands.append(f"0 0 m 0 {height:.2f} l S")
            # Dark edge (bottom and right)
            commands.append("0.5 0.5 0.5 RG")
            commands.append(f"{width:.2f} 0 m {width:.2f} {height:.2f} l S")
            commands.append(f"0 {height:.2f} m {width:.2f} {height:.2f} l S")

        # Label text centered
        if label:
            commands.append("BT")
            commands.append(f"/{font_name} {font_size:.2f} Tf")
            commands.append(f"{self._font_color_gray:.2f} g")
            # Approximate centering
            text_width = len(label) * font_size * 0.5
            x_pos = (width - text_width) / 2
            y_pos = (height - font_size) / 2 + 2
            commands.append(f"{x_pos:.2f} {y_pos:.2f} Td")
            escaped_label = label.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            commands.append(f"({escaped_label}) Tj")
            commands.append("ET")

        commands.append("Q")

        content = "\n".join(commands)
        # Include Helvetica font resource for the button label
        self._appearance_normal = PDFFormXObject(content, width, height, resources=HELV_FONT_RESOURCE)
        return self._appearance_normal


class ChoiceField(FormField):
    """
    Base class for choice fields (list boxes and combo boxes).
    """

    def __init__(
        self,
        field_name: str,
        x: float,
        y: float,
        width: float,
        height: float,
        options: list,
        value: str = None,
        font_size: float = 12,
        font_color_gray: float = 0,
        background_color: tuple = (1, 1, 1),
        border_color: tuple = (0, 0, 0),
        border_width: float = 1,
        is_combo: bool = False,
        editable: bool = False,
        multi_select: bool = False,
        read_only: bool = False,
        required: bool = False,
        sort: bool = False,
        **kwargs,
    ):
        field_flags = 0
        if is_combo:
            field_flags |= FieldFlag.COMBO
        if editable:
            field_flags |= FieldFlag.EDIT
        if multi_select:
            field_flags |= FieldFlag.MULTI_SELECT
        if read_only:
            field_flags |= FieldFlag.READ_ONLY
        if required:
            field_flags |= FieldFlag.REQUIRED
        if sort:
            field_flags |= FieldFlag.SORT

        super().__init__(
            field_type="Ch",
            field_name=field_name,
            x=x,
            y=y,
            width=width,
            height=height,
            value=PDFString(value, encrypt=True) if value else None,
            default_value=PDFString(value, encrypt=True) if value else None,
            field_flags=field_flags,
            border_width=border_width,
            **kwargs,
        )

        self._width = width
        self._height = height
        self._options = options
        self._value_str = value or ""
        self._font_size = font_size
        self._font_color_gray = font_color_gray
        self._background_color = background_color
        self._border_color = border_color
        self._is_combo = is_combo
        self.d_a = PDFString(f"/Helv {font_size:.2f} Tf {font_color_gray:.2f} g")
        # Options array - can be simple strings or [export_value, display_value] pairs
        self.opt = PDFArray([PDFString(opt, encrypt=True) for opt in options])

    def _generate_appearance(self, font_name: str = "Helv", font_size: float = None):
        """Generate the appearance stream XObject for this choice field."""
        if font_size is None:
            font_size = self._font_size

        width = self._width
        height = self._height
        value = self._value_str

        commands = []
        commands.append("q")

        # Background
        if self._background_color:
            r, g, b = self._background_color
            commands.append(f"{r:.3f} {g:.3f} {b:.3f} rg")
            commands.append(f"0 0 {width:.2f} {height:.2f} re")
            commands.append("f")

        # Border
        if self._border_color:
            r, g, b = self._border_color
            commands.append(f"{r:.3f} {g:.3f} {b:.3f} RG")
            commands.append("1 w")
            commands.append(f"0.5 0.5 {width - 1:.2f} {height - 1:.2f} re")
            commands.append("S")

        # For combo boxes, draw dropdown arrow
        if self._is_combo:
            arrow_size = min(height - 4, 10)
            arrow_x = width - arrow_size - 2
            arrow_y = (height - arrow_size) / 2
            commands.append("0.5 0.5 0.5 rg")
            # Simple triangle
            commands.append(f"{arrow_x:.2f} {arrow_y + arrow_size:.2f} m")
            commands.append(f"{arrow_x + arrow_size:.2f} {arrow_y + arrow_size:.2f} l")
            commands.append(f"{arrow_x + arrow_size / 2:.2f} {arrow_y:.2f} l")
            commands.append("f")

        # Display current value
        if value:
            commands.append("BT")
            commands.append(f"/{font_name} {font_size:.2f} Tf")
            commands.append(f"{self._font_color_gray:.2f} g")
            y_pos = (height - font_size) / 2 + 2
            commands.append(f"2 {y_pos:.2f} Td")
            escaped_value = value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            commands.append(f"({escaped_value}) Tj")
            commands.append("ET")

        commands.append("Q")

        content = "\n".join(commands)
        # Include Helvetica font resource for Adobe Acrobat compatibility
        self._appearance_normal = PDFFormXObject(content, width, height, resources=HELV_FONT_RESOURCE)
        return self._appearance_normal


class ComboBox(ChoiceField):
    """An interactive combo box (dropdown list) field."""

    def __init__(
        self,
        field_name: str,
        x: float,
        y: float,
        width: float,
        height: float,
        options: list,
        value: str = None,
        editable: bool = False,
        **kwargs,
    ):
        super().__init__(
            field_name=field_name,
            x=x,
            y=y,
            width=width,
            height=height,
            options=options,
            value=value,
            is_combo=True,
            editable=editable,
            **kwargs,
        )


class ListBox(ChoiceField):
    """An interactive list box field."""

    def __init__(
        self,
        field_name: str,
        x: float,
        y: float,
        width: float,
        height: float,
        options: list,
        value: str = None,
        multi_select: bool = False,
        **kwargs,
    ):
        super().__init__(
            field_name=field_name,
            x=x,
            y=y,
            width=width,
            height=height,
            options=options,
            value=value,
            is_combo=False,
            multi_select=multi_select,
            **kwargs,
        )

    def _generate_appearance(self, font_name: str = "Helv", font_size: float = None):
        """Generate the appearance stream for list box showing options."""
        if font_size is None:
            font_size = self._font_size

        width = self._width
        height = self._height

        commands = []
        commands.append("q")

        # Background
        if self._background_color:
            r, g, b = self._background_color
            commands.append(f"{r:.3f} {g:.3f} {b:.3f} rg")
            commands.append(f"0 0 {width:.2f} {height:.2f} re")
            commands.append("f")

        # Border
        if self._border_color:
            r, g, b = self._border_color
            commands.append(f"{r:.3f} {g:.3f} {b:.3f} RG")
            commands.append("1 w")
            commands.append(f"0.5 0.5 {width - 1:.2f} {height - 1:.2f} re")
            commands.append("S")

        # Establish clipping path for content area (prevents text overflow)
        commands.append(f"2 2 {width - 4:.2f} {height - 4:.2f} re W n")

        # Draw options
        line_height = font_size + 2
        max_lines = int((height - 4) / line_height)
        y_pos = height - font_size - 2

        # First, draw highlight rectangles for selected items (outside of BT/ET)
        for i, option in enumerate(self._options[:max_lines]):
            option_y = y_pos - i * line_height
            if option_y < 2:
                break
            if option == self._value_str:
                commands.append("0.8 0.8 1 rg")
                commands.append(f"2 {option_y - 2:.2f} {width - 4:.2f} {line_height:.2f} re f")

        # Now draw all option texts
        commands.append("BT")
        commands.append(f"/{font_name} {font_size:.2f} Tf")
        commands.append(f"{self._font_color_gray:.2f} g")

        first_line = True
        for i, option in enumerate(self._options[:max_lines]):
            option_y = y_pos - i * line_height
            if option_y < 2:
                break
            
            if first_line:
                # First Td uses absolute position from origin
                commands.append(f"2 {option_y:.2f} Td")
                first_line = False
            else:
                # Subsequent Td moves relative to previous position (just move down by line_height)
                commands.append(f"0 {-line_height:.2f} Td")
            
            escaped_option = str(option).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            commands.append(f"({escaped_option}) Tj")

        commands.append("ET")
        commands.append("Q")

        content = "\n".join(commands)
        # Include Helvetica font resource for Adobe Acrobat compatibility
        self._appearance_normal = PDFFormXObject(content, width, height, resources=HELV_FONT_RESOURCE)
        return self._appearance_normal
