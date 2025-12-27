"""
Interactive PDF form fields (AcroForms).

The contents of this module are internal to fpdf2, and not part of the public API.
They may change at any time without prior warning or any deprecation period,
in non-backward-compatible ways.
"""

from .annotations import PDFAnnotation, DEFAULT_ANNOT_FLAGS
from .enums import AnnotationFlag, FieldFlag
from .syntax import Name, PDFArray, PDFContentStream, PDFObject, PDFString


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
        self.d_a = f"/Helv {font_size:.2f} Tf {font_color_gray:.2f} g"

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
        resources = "<</ProcSet [/PDF /Text] /Font <</Helv 2 0 R>>>>"

        self._appearance_normal = PDFFormXObject(content, width, height, resources)
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
        self.d_a = f"/ZaDb {size * 0.8:.2f} Tf {check_color_gray:.2f} g"
        self.a_s = Name("Yes") if checked else Name("Off")

    def _generate_appearance(self, font_name: str = "ZaDb", font_size: float = None):
        """Generate appearance streams for checked and unchecked states."""
        size = self._size
        if font_size is None:
            font_size = size * 0.8

        off_commands = self._generate_box_appearance(size, show_check=False)
        off_xobj = PDFFormXObject(off_commands, size, size)

        yes_commands = self._generate_box_appearance(size, show_check=True, font_size=font_size)
        yes_xobj = PDFFormXObject(yes_commands, size, size)

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
            if font_size is None:
                font_size = size * 0.8
            commands.append("BT")
            commands.append(f"/ZaDb {font_size:.2f} Tf")
            commands.append(f"{self._check_color_gray:.2f} g")
            x_offset = (size - font_size) / 2
            y_offset = (size - font_size) / 2 + 1
            commands.append(f"{x_offset:.2f} {y_offset:.2f} Td")
            commands.append(f"({self.CHECK_CHAR}) Tj")
            commands.append("ET")

        commands.append("Q")
        return "\n".join(commands)

    @property
    def a_p(self):
        """Return the appearance dictionary for checkbox."""
        if self._appearance_off and self._appearance_yes:
            return f"<</N <</Off {self._appearance_off.ref} /Yes {self._appearance_yes.ref}>>>>"
        return None
