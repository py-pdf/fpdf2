import locale


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


def get_scale_factor(unit: str) -> float:
    """
    Get how many pts are in a unit. (k)

    Args:
        unit (str): Any of "pt", "mm", "cm", or "in".
    Returns:
        float: The number of points in that unit (assuming 72dpi)
    Raises:
        ValueError
    """
    if unit == "pt":
        return 1
    if unit == "mm":
        return 72 / 25.4
    if unit == "cm":
        return 72 / 2.54
    if unit == "in":
        return 72.0
    raise ValueError(f"Incorrect unit: {unit}")


def dochecks():
    # Check for locale-related bug
    # if (1.1==1):
    #     raise FPDFException("Don\'t alter the locale before including class file")
    # Check for decimal separator
    if f"{1.0:.1f}" != "1.0":
        locale.setlocale(locale.LC_NUMERIC, "C")


# Moved here from FPDF#__init__
dochecks()
