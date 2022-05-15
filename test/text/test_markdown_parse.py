# pylint: disable=protected-access
from fpdf import FPDF
from fpdf.line_break import Fragment


def test_markdown_parse_simple_ok():
    pdf = FPDF()
    assert tuple(pdf._markdown_parse("**bold**, __italics__ and --underlined--")) == (
        Fragment(
            pdf.font_family,
            pdf.font_size_pt,
            "B",
            False,
            pdf.font_stretching,
            list("bold"),
        ),
        Fragment(
            pdf.font_family,
            pdf.font_size_pt,
            "",
            False,
            pdf.font_stretching,
            list(", "),
        ),
        Fragment(
            pdf.font_family,
            pdf.font_size_pt,
            "I",
            False,
            pdf.font_stretching,
            list("italics"),
        ),
        Fragment(
            pdf.font_family,
            pdf.font_size_pt,
            "",
            False,
            pdf.font_stretching,
            list(" and "),
        ),
        Fragment(
            pdf.font_family,
            pdf.font_size_pt,
            "",
            True,
            pdf.font_stretching,
            list("underlined"),
        ),
    )


def test_markdown_parse_overlapping():
    pdf = FPDF()
    assert tuple(pdf._markdown_parse("**bold __italics__**")) == (
        Fragment(
            pdf.font_family,
            pdf.font_size_pt,
            "B",
            False,
            pdf.font_stretching,
            list("bold "),
        ),
        Fragment(
            pdf.font_family,
            pdf.font_size_pt,
            "BI",
            False,
            pdf.font_stretching,
            list("italics"),
        ),
    )


def test_markdown_parse_crossing_markers():
    pdf = FPDF()
    assert tuple(pdf._markdown_parse("**bold __and** italics__")) == (
        Fragment(
            pdf.font_family,
            pdf.font_size_pt,
            "B",
            False,
            pdf.font_stretching,
            list("bold "),
        ),
        Fragment(
            pdf.font_family,
            pdf.font_size_pt,
            "BI",
            False,
            pdf.font_stretching,
            list("and"),
        ),
        Fragment(
            pdf.font_family,
            pdf.font_size_pt,
            "I",
            False,
            pdf.font_stretching,
            list(" italics"),
        ),
    )


def test_markdown_parse_unterminated():
    pdf = FPDF()
    assert tuple(pdf._markdown_parse("**bold __italics__")) == (
        Fragment(
            pdf.font_family,
            pdf.font_size_pt,
            "B",
            False,
            pdf.font_stretching,
            list("bold "),
        ),
        Fragment(
            pdf.font_family,
            pdf.font_size_pt,
            "BI",
            False,
            pdf.font_stretching,
            list("italics"),
        ),
    )


def test_markdown_parse_line_of_markers():
    pdf = FPDF()
    assert tuple(pdf._markdown_parse("*** woops")) == (
        Fragment(
            pdf.font_family,
            pdf.font_size_pt,
            "",
            False,
            pdf.font_stretching,
            list("*** woops"),
        ),
    )
    assert tuple(pdf._markdown_parse("----------")) == (
        Fragment(
            pdf.font_family,
            pdf.font_size_pt,
            "",
            False,
            pdf.font_stretching,
            list("----------"),
        ),
    )
