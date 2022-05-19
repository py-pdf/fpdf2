from fpdf.util import b
import pytest


def test_string_to_bytes():
    expected = "foo".encode("latin1")
    assert b("foo") == expected


def test_bytes_conversion_error():
    with pytest.raises(ValueError) as error:
        b([1, 2, 3])
    assert "Invalid input:" in str(error.value)
