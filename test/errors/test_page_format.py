import pytest

import fpdf


def test_page_format_error_class():
    with pytest.raises(TypeError) as e:
        fpdf.errors.FPDFPageFormatException(None, unknown=True, one=True)

    expected = "FPDF Page Format Exception cannot be both"
    assert expected in str(e.value)


def test_page_format_error():
    with pytest.raises(fpdf.errors.FPDFPageFormatException) as e:
        fpdf.fpdf.get_page_format("letter1")

    assert "FPDFPageFormatException" in str(e.value)
    assert "Unknown page format" in str(e.value)
    assert "letter1" in str(e.value)

    with pytest.raises(fpdf.errors.FPDFPageFormatException) as e:
        fpdf.fpdf.get_page_format(3)

    assert "FPDFPageFormatException" in str(e.value)
    assert "Only one argument given" in str(e.value)

    with pytest.raises(fpdf.errors.FPDFPageFormatException) as e:
        fpdf.fpdf.get_page_format(4, "a")

        assert "FPDFPageFormatException" in str(e.value)
        assert "Arguments must be numbers: " in str(e.value)
