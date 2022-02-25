# pylint: disable=protected-access
from fpdf import FPDF
from fpdf.line_break import Fragment


def test_markdown_parse_simple_ok():
    assert tuple(
        FPDF()._markdown_parse("**bold**, __italics__ and --underlined--")
    ) == (
        Fragment.from_string("bold", "B", False),
        Fragment.from_string(", ", "", False),
        Fragment.from_string("italics", "I", False),
        Fragment.from_string(" and ", "", False),
        Fragment.from_string("underlined", "", True),
    )


def test_markdown_parse_overlapping():
    assert tuple(FPDF()._markdown_parse("**bold __italics__**")) == (
        Fragment.from_string("bold ", "B", False),
        Fragment.from_string("italics", "BI", False),
    )


def test_markdown_parse_crossing_markers():
    assert tuple(FPDF()._markdown_parse("**bold __and** italics__")) == (
        Fragment.from_string("bold ", "B", False),
        Fragment.from_string("and", "BI", False),
        Fragment.from_string(" italics", "I", False),
    )


def test_markdown_parse_unterminated():
    assert tuple(FPDF()._markdown_parse("**bold __italics__")) == (
        Fragment.from_string("bold ", "B", False),
        Fragment.from_string("italics", "BI", False),
    )


def test_markdown_parse_line_of_markers():
    assert tuple(FPDF()._markdown_parse("*** woops")) == (
        Fragment.from_string("*** woops", "", False),
    )
    assert tuple(FPDF()._markdown_parse("----------")) == (
        Fragment.from_string("----------", "", False),
    )
