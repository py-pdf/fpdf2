# pylint: disable=protected-access
from fpdf import FPDF
from fpdf.line_break import Fragment


def test_markdown_parse_simple_ok():
    assert tuple(
        FPDF()._markdown_parse("**bold**, __italics__ and --underlined--")
    ) == (
        Fragment("bold", "B", False),
        Fragment(", ", "", False),
        Fragment("italics", "I", False),
        Fragment(" and ", "", False),
        Fragment("underlined", "", True),
    )


def test_markdown_parse_overlapping():
    assert tuple(FPDF()._markdown_parse("**bold __italics__**")) == (
        Fragment("bold ", "B", False),
        Fragment("italics", "BI", False),
    )


def test_markdown_parse_crossing_markers():
    assert tuple(FPDF()._markdown_parse("**bold __and** italics__")) == (
        Fragment("bold ", "B", False),
        Fragment("and", "BI", False),
        Fragment(" italics", "I", False),
    )


def test_markdown_parse_unterminated():
    assert tuple(FPDF()._markdown_parse("**bold __italics__")) == (
        Fragment("bold ", "B", False),
        Fragment("italics", "BI", False),
    )


def test_markdown_parse_line_of_markers():
    assert tuple(FPDF()._markdown_parse("*** woops")) == (
        Fragment("*** woops", "", False),
    )
    assert tuple(FPDF()._markdown_parse("----------")) == (
        Fragment("----------", "", False),
    )
