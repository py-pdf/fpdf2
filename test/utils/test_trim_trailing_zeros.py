import pytest

from fpdf.util import trim_trailing_zeros


@pytest.mark.parametrize(
    "value,expected",
    [
        ("100", "100"),
        ("100.00", "100"),
        ("1.1000", "1.1"),
        ("1.123456789012345", "1.123456789012345"),
        ("-0.00", "-0"),
        ("1e+20", "1e+20"),
        ("1.00e-20", "1e-20"),
        ("1.00E+20", "1E+20"),
    ],
)
def test_trim_trailing_zeros(value, expected):
    assert trim_trailing_zeros(value) == expected
