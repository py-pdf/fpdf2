import locale
from typing import Union, Iterable
from enum import IntEnum


# Those two need to be here to avoid circular imports.
class XPos(IntEnum):
    """
    Positional values in horizontal direction for use after printing text.
        LEFT    - left end of the cell
        RIGHT   - right end of the cell (default)
        START   - start of actual text
        END     - end of actual text
        WCONT   - for write() to continue next (slightly left of END)
        CENTER  - center of actual text
        LMARGIN - left page margin (start of printable area)
        RMARGIN - right page margin (end of printable area)
    """

    LEFT = 1  # self.x
    RIGHT = 2  # self.x + w
    START = 3  # left end of actual text
    END = 4  # right end of actual text
    WCONT = 5  # continuation point for write()
    CENTER = 6  # center of actual text
    LMARGIN = 7  # self.l_margin
    RMARGIN = 8  # self.w - self.r_margin


class YPos(IntEnum):
    """
    Positional values in vertical direction for use after printing text.
        TOP     - top of the first line (default)
        LAST    - top of the last line (same as TOP for single-line text)
        NEXT    - top of next line (bottom of current text)
        TMARGIN - top page margin (start of printable area)
        BMARGIN - bottom page margin (end of printable area)
    """

    TOP = 1  # self.y
    LAST = 2  # top of last line (TOP for single lines)
    NEXT = 3  # LAST + h
    TMARGIN = 4  # self.t_margin
    BMARGIN = 5  # self.h - self.b_margin


def substr(s, start, length=-1):
    if length < 0:
        length = len(s) - start
    return s[start : start + length]


def enclose_in_parens(s):
    """Format a text string"""
    if s:
        assert isinstance(s, str)
        return f"({escape_parens(s)})"
    return ""


def escape_parens(s):
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


# shortcut to bytes conversion (b prefix)
def b(s):
    if isinstance(s, str):
        return s.encode("latin1")
    if isinstance(s, int):
        return bytes([s])  # http://bugs.python.org/issue4588
    raise ValueError(f"Invalid input: {s}")


def get_scale_factor(unit: Union[str, float, int]) -> float:
    """
    Get how many pts are in a unit. (k)

    Args:
        unit (str, float, int): Any of "pt", "mm", "cm", "in", or a number.
    Returns:
        float: The number of points in that unit (assuming 72dpi)
    Raises:
        ValueError
    """
    if isinstance(unit, (int, float)):
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
    to_convert: Union[float, int, Iterable[Union[float, int, Iterable]]],
    old_unit: Union[str, float, int],
    new_unit: Union[str, float, int],
) -> Union[float, tuple]:
    """
     Convert a number or sequence of numbers from one unit to another.

     If either unit is a number it will be treated as the number of points per unit.  So 72 would mean 1 inch.

     Args:
        to_convert (float, int, Iterable): The number / list of numbers, or points, to convert
        old_unit (str, float, int): A unit accepted by fpdf.FPDF or a number
        new_unit (str, float, int): A unit accepted by fpdf.FPDF or a number
    Returns:
        (float, tuple): to_convert converted from old_unit to new_unit or a tuple of the same
    """
    unit_conversion_factor = get_scale_factor(new_unit) / get_scale_factor(old_unit)
    if isinstance(to_convert, Iterable):
        return tuple(
            map(lambda i: convert_unit(i, 1, unit_conversion_factor), to_convert)
        )
    return to_convert / unit_conversion_factor


def dochecks():
    # Check for locale-related bug
    # if (1.1==1):
    #     raise FPDFException("Don\'t alter the locale before including class file")
    # Check for decimal separator
    if f"{1.0:.1f}" != "1.0":
        locale.setlocale(locale.LC_NUMERIC, "C")


# Moved here from FPDF#__init__
dochecks()
