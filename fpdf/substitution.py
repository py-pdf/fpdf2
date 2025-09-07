import enum
from uuid import uuid4
from typing import Any, Optional


class SubstitutionType(enum.Enum):
    GENERAL = enum.auto()
    TOTAL_PAGES_NUM = enum.auto()
    CURRENT_PAGE = enum.auto()
    DEFAULT_TOC_PAGE = enum.auto()


class SubstitutionAlign(enum.Enum):
    C = enum.auto()  # Center.
    L = enum.auto()  # Left.
    R = enum.auto()  # Right.


class Substitution:
    """
    This class binds a placeholder to a specific value.

    You're supposed to use the string representation (e.g. str(x) or f'{x}')
    to put a substitution object in text.

    You must assign a string to the property "value" before "outputting" the PDF,
    so the placeholder will be substituted with this string in the result file.

    Substitution types can be used to differentiate substitutions, e.g. to set values automatically.

    The mask defines the width of the result string.
    If the actual string is shorter, there will be empty space.
    If it is longer, part of it may be overlaid on other text.

    You might need to store some related data to compute the substitution value later.
    The "extra_data" property can be used for this.
    """

    PREFIX = ":sub:"
    STR_LENGTH = 37  # 5 chars of PREFIX + 32 chars of UUID.hex

    __slots__ = ("_id", "stype", "align", "mask", "value", "extra_data")

    def __init__(
        self,
        stype: SubstitutionType,
        align: SubstitutionAlign,
        mask: str,
        extra_data: Optional[Any] = None,
    ):
        assert mask, "Mask must be a non-empty string."
        self.value: Optional[str] = None
        self.stype = stype
        self.align = align
        self.mask = mask
        self.extra_data = extra_data
        self._id = uuid4()

    def __str__(self):
        return self.PREFIX + self._id.hex

    def __hash__(self):
        return self._id.int

    def __setattr__(self, name, value):
        if name == "value" and not (value is None or isinstance(value, str)):
            raise ValueError(
                f"Value must be a string, but it has the type {type(value)}."
            )

        return super().__setattr__(name, value)
