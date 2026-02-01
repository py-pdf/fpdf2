"""
Various utilities that could not be gathered logically in a specific module.

The contents of this module are internal to fpdf2, and not part of the public API.
They may change at any time without prior warning or any deprecation period,
in non-backward-compatible ways.
"""

import decimal

# nosemgrep: python.lang.compatibility.python37.python37-compatibility-importlib2 (min Python is 3.9)
from importlib import resources
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    BinaryIO,
    Iterable,
    NamedTuple,
    Sequence,
    TypeVar,
    Union,
    overload,
)

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage

    from .svg import SVGObject

ImageType = Union[str, bytes, BinaryIO, "PILImage", Path, None]
ImageClass = (str, bytes, BinaryIO, "PILImage", Path)
ImageData = Union["SVGObject", "PILImage", bytes, BinaryIO, Path, None]
SVGObjectType = TypeVar("SVGObjectType", bound="SVGObject")
Number = Union[int, float, decimal.Decimal]
NumberClass = (int, float, decimal.Decimal)
_StrBytes = TypeVar("_StrBytes", str, bytes)


class Padding(NamedTuple):
    top: float = 0
    right: float = 0
    bottom: float = 0
    left: float = 0

    @classmethod
    def new(cls, padding: Union[Number, Sequence[Number], "Padding"]) -> "Padding":
        """Return a 4-tuple of padding values from a single value or a 2, 3 or 4-tuple according to CSS rules"""
        if isinstance(padding, NumberClass):
            return Padding(
                float(padding), float(padding), float(padding), float(padding)
            )
        if len(padding) == 2:
            return Padding(
                float(padding[0]),
                float(padding[1]),
                float(padding[0]),
                float(padding[1]),
            )
        if len(padding) == 3:
            return Padding(
                float(padding[0]),
                float(padding[1]),
                float(padding[2]),
                float(padding[1]),
            )
        if len(padding) == 4:
            return Padding(
                float(padding[0]),
                float(padding[1]),
                float(padding[2]),
                float(padding[3]),
            )

        raise ValueError(
            f"padding shall be a number or a sequence of 2, 3 or 4 numbers, got {str(padding)}"
        )


def buffer_subst(buffer: bytearray, placeholder: str, value: str) -> bytearray:
    buffer_size = len(buffer)
    assert len(placeholder) == len(value), f"placeholder={placeholder} value={value}"
    buffer = buffer.replace(placeholder.encode(), value.encode(), 1)
    assert len(buffer) == buffer_size
    return buffer


@overload
def escape_parens(s: str) -> str: ...


@overload
def escape_parens(s: bytes) -> bytes: ...


def escape_parens(s: _StrBytes) -> _StrBytes:
    """Add a backslash character before , ( and )"""
    if isinstance(s, str):
        return (
            s.replace("\\", "\\\\")
            .replace(")", "\\)")
            .replace("(", "\\(")
            .replace("\r", "\\r")
        )
    return (
        s.replace(b"\\", b"\\\\")
        .replace(b")", b"\\)")
        .replace(b"(", b"\\(")
        .replace(b"\r", b"\\r")
    )


def get_scale_factor(unit: Union[str, Number]) -> float:
    """
    Get how many pts are in a unit. (k)

    Args:
        unit (str, float, int): Any of "pt", "mm", "cm", "in", or a number.
    Returns:
        float: The number of points in that unit (assuming 72dpi)
    Raises:
        ValueError
    """
    if isinstance(unit, NumberClass):
        return float(unit)

    if unit == "pt":
        return 1
    if unit == "mm":
        return 72 / 25.4
    if unit == "cm":
        return 72 / 2.54
    if unit == "in":
        return 72.0
    raise ValueError(f"Incorrect unit: {unit}")


def convert_unit(
    to_convert: Number | Iterable[Any],
    old_unit: Union[str, Number],
    new_unit: Union[str, Number],
) -> Union[float, tuple[Any, ...]]:
    """
     Convert a number or sequence of numbers from one unit to another.

     If either unit is a number it will be treated as the number of points per unit.  So 72 would mean 1 inch.

     Args:
        to_convert (float, int, Iterable): The number / list of numbers, or points, to convert
        old_unit (str, float, int): A unit accepted by `fpdf.fpdf.FPDF` or a number
        new_unit (str, float, int): A unit accepted by `fpdf.fpdf.FPDF` or a number
    Returns:
        (float, tuple): to_convert converted from old_unit to new_unit or a tuple of the same
    """
    unit_conversion_factor = get_scale_factor(new_unit) / get_scale_factor(old_unit)
    if isinstance(to_convert, Iterable):
        return tuple(convert_unit(i, 1, unit_conversion_factor) for i in to_convert)
    return float(to_convert) / unit_conversion_factor


def number_to_str(number: Number) -> str:
    """
    Convert a decimal number to a minimal string representation (no trailing 0 or .).

    Args:
        number (Number): the number to be converted to a string.

    Returns:
        The number's string representation.
    """
    # this approach tries to produce minimal representations of floating point numbers
    # but can also produce "-0".
    return f"{number:.4f}".rstrip("0").rstrip(".")


ROMAN_NUMERAL_MAP = (
    ("M", 1000),
    ("CM", 900),
    ("D", 500),
    ("CD", 400),
    ("C", 100),
    ("XC", 90),
    ("L", 50),
    ("XL", 40),
    ("X", 10),
    ("IX", 9),
    ("V", 5),
    ("IV", 4),
    ("I", 1),
)


def int2roman(n: int) -> str:
    "Convert an integer to Roman numeral"
    result = ""
    if n is None:
        return result
    for numeral, integer in ROMAN_NUMERAL_MAP:
        while n >= integer:
            result += numeral
            n -= integer
    return result


def int_to_letters(n: int) -> str:
    "Convert an integer to a letter value (A to Z for the first 26, then AA to ZZ, and so on)"
    if n > 25:
        return int_to_letters(int((n / 26) - 1)) + int_to_letters(n % 26)
    return chr(n + ord("A"))


def builtin_srgb2014_bytes() -> bytes:
    pkg = "fpdf.data.color_profiles"
    return (resources.files(pkg) / "sRGB2014.icc").read_bytes()


def format_number(x: float, digits: int = 8) -> str:
    # snap tiny values to zero to avoid "-0" and scientific notation
    if abs(x) < 1e-12:
        x = 0.0
    s = f"{x:.{digits}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if s == "-0":
        s = "0"
    if s.startswith("."):
        s = "0" + s
    if s.startswith("-."):
        s = s.replace("-.", "-0.", 1)
    return s


def get_parsed_unicode_range(
    unicode_range: str | Sequence[str | int | tuple[int, int]],
) -> set[int]:
    """
    Parse unicode_range parameter into a set of codepoints.

    Supports CSS-style formats:

    - String with comma-separated ranges: "U+1F600-1F64F, U+2600-26FF, U+2615"
    - List of strings: ["U+1F600-1F64F", "U+2600", "U+26FF"]
    - List of tuples: [(0x1F600, 0x1F64F), (0x2600, 0x26FF)]
    - List of integers: [0x1F600, 0x2600, 128512]
    - Mixed formats: [(0x1F600, 0x1F64F), "U+2600", 128512]

    Returns a set of integer codepoints.
    """
    if unicode_range is not None and len(unicode_range) == 0:
        raise ValueError("unicode_range cannot be empty")

    codepoints: set[int] = set()

    if isinstance(unicode_range, str):
        unicode_range = [item.strip() for item in unicode_range.split(",")]

    for item in unicode_range:
        if isinstance(item, tuple):
            if len(item) != 2:
                raise ValueError(f"Tuple must have exactly 2 elements: {item}")
            start, end = item

            if isinstance(start, str):
                start = int(start.replace("U+", "").replace("u+", ""), 16)
            if isinstance(end, str):
                end = int(end.replace("U+", "").replace("u+", ""), 16)

            if start > end:
                raise ValueError(f"Invalid range: start ({start}) > end ({end})")

            codepoints.update(range(start, end + 1))

        elif isinstance(item, str):
            item_stripped = item.strip().replace("u+", "U+")

            if "-" in item_stripped and not item_stripped.startswith("-"):
                parts = item_stripped.split("-")
                if len(parts) != 2:
                    raise ValueError(f"Invalid range format: {item_stripped}")

                start = int(parts[0].replace("U+", ""), 16)
                end = int(parts[1].replace("U+", ""), 16)

                if start > end:
                    raise ValueError(
                        f"Invalid range: start ({hex(start)}) > end ({hex(end)})"
                    )

                codepoints.update(range(start, end + 1))
            else:
                codepoint = int(item_stripped.replace("U+", ""), 16)
                codepoints.add(codepoint)

        elif isinstance(item, int):
            if item < 0:
                raise ValueError(f"Invalid codepoint: {item} (must be non-negative)")
            codepoints.add(item)

        else:
            raise ValueError(
                f"Unsupported unicode_range item type: {type(item).__name__}"
            )

    return codepoints


class FloatTolerance:
    """Utility class for floating point math with a defined tolerance."""

    TOLERANCE = 1e-9

    @classmethod
    def equal(cls, a: float, b: float) -> bool:
        """Check if two floats are almost equal within the defined tolerance."""
        return abs(a - b) <= cls.TOLERANCE

    @classmethod
    def not_equal(cls, a: float, b: float) -> bool:
        """Check if two floats are not almost equal within the defined tolerance."""
        return not cls.equal(a, b)

    @classmethod
    def is_zero(cls, a: float) -> bool:
        """Check if a float is almost zero within the defined tolerance."""
        return abs(a) <= cls.TOLERANCE

    @classmethod
    def less_than(cls, a: float, b: float) -> bool:
        """Check if a is less than b considering the defined tolerance."""
        return (b - a) > cls.TOLERANCE

    @classmethod
    def greater_than(cls, a: float, b: float) -> bool:
        """Check if a is greater than b considering the defined tolerance."""
        return (a - b) > cls.TOLERANCE

    @classmethod
    def less_equal(cls, a: float, b: float) -> bool:
        """Check if a is less than or almost equal to b considering the defined tolerance."""
        return cls.less_than(a, b) or cls.equal(a, b)

    @classmethod
    def greater_equal(cls, a: float, b: float) -> bool:
        """Check if a is greater than or almost equal to b considering the defined tolerance."""
        return cls.greater_than(a, b) or cls.equal(a, b)
