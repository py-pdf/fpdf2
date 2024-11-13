import pytest

from fpdf.errors import FPDFPageFormatException
from fpdf.fpdf import get_page_format


def test_page_format_ok():
    assert get_page_format("a4") == (595.28, 841.89)
    assert get_page_format("letter") == (612, 792)
    assert get_page_format((297, 210), k=2) == (594, 420)


def test_page_format_error():
    with pytest.raises(FPDFPageFormatException) as error:
        get_page_format("letter1")

    assert "FPDFPageFormatException" in str(error.value)
    assert "Unknown page format" in str(error.value)
    assert "letter1" in str(error.value)

    with pytest.raises(FPDFPageFormatException) as error:
        get_page_format(3)

    assert "FPDFPageFormatException" in str(error.value)
    assert "Only one argument given" in str(error.value)

    with pytest.raises(FPDFPageFormatException) as error:
        get_page_format(4, "a")

    assert "FPDFPageFormatException" in str(error.value)
    assert "Arguments must be numbers: " in str(error.value)
