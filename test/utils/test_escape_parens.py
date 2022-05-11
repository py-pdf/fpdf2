from fpdf.util import escape_parens


def test_escape_parens_string():
    expected = "\\\\ \\) \\( \\r"
    assert expected == escape_parens("\\ ) ( \r")


def test_escape_parens_bytes():
    expected = "\\\\ \\) \\( \\r".encode()
    assert expected == escape_parens("\\ ) ( \r".encode())
