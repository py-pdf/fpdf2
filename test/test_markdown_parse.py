# pylint: disable=protected-access
from fpdf import FPDF


def test_markdown_parse_simple_ok():
    assert tuple(
        FPDF()._markdown_parse("**bold**, __italics__ and --underlined--")
    ) == (
        ("bold", "B", False),
        (", ", "", False),
        ("italics", "I", False),
        (" and ", "", False),
        ("underlined", "", True),
    )


def test_markdown_parse_overlapping():
    assert tuple(FPDF()._markdown_parse("**bold __italics__**")) == (
        ("bold ", "B", False),
        ("italics", "BI", False),
    )


def test_markdown_parse_crossing_markers():
    assert tuple(FPDF()._markdown_parse("**bold __and** italics__")) == (
        ("bold ", "B", False),
        ("and", "BI", False),
        (" italics", "I", False),
    )


def test_markdown_parse_unterminated():
    assert tuple(FPDF()._markdown_parse("**bold __italics__")) == (
        ("bold ", "B", False),
        ("italics", "BI", False),
    )


def test_markdown_parse_line_of_markers():
    assert tuple(FPDF()._markdown_parse("*** woops")) == (("*** woops", "", False),)
    assert tuple(FPDF()._markdown_parse("----------")) == (("----------", "", False),)
