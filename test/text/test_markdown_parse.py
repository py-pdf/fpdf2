# pylint: disable=protected-access
from fpdf import FPDF
from fpdf.line_break import Fragment

PDF = FPDF()
GSTATE = PDF._get_current_graphics_state()
GSTATE_B = GSTATE.copy()
GSTATE_B["font_style"] = "B"
GSTATE_I = GSTATE.copy()
GSTATE_I["font_style"] = "I"
GSTATE_U = GSTATE.copy()
GSTATE_U["underline"] = True
GSTATE_BI = GSTATE.copy()
GSTATE_BI["font_style"] = "BI"


def test_markdown_parse_simple_ok():
    frags = tuple(FPDF()._markdown_parse("**bold**, __italics__ and --underlined--"))
    expected = (
        Fragment("bold", GSTATE_B, k=PDF.k),
        Fragment(", ", GSTATE, k=PDF.k),
        Fragment("italics", GSTATE_I, k=PDF.k),
        Fragment(" and ", GSTATE, k=PDF.k),
        Fragment("underlined", GSTATE_U, k=PDF.k),
    )
    assert frags == expected


def test_markdown_parse_overlapping():
    frags = tuple(FPDF()._markdown_parse("**bold __italics__**"))
    expected = (
        Fragment("bold ", GSTATE_B, k=PDF.k),
        Fragment("italics", GSTATE_BI, k=PDF.k),
    )
    assert frags == expected


def test_markdown_parse_crossing_markers():
    frags = tuple(FPDF()._markdown_parse("**bold __and** italics__"))
    expected = (
        Fragment("bold ", GSTATE_B, k=PDF.k),
        Fragment("and", GSTATE_BI, k=PDF.k),
        Fragment(" italics", GSTATE_I, k=PDF.k),
    )
    assert frags == expected


def test_markdown_parse_unterminated():
    frags = tuple(FPDF()._markdown_parse("**bold __italics__"))
    expected = (
        Fragment("bold ", GSTATE_B, k=PDF.k),
        Fragment("italics", GSTATE_BI, k=PDF.k),
    )
    assert frags == expected


def test_markdown_parse_line_of_markers():
    frags = tuple(FPDF()._markdown_parse("*** woops"))
    expected = (Fragment("*** woops", GSTATE, k=PDF.k),)
    assert frags == expected
    frags = tuple(FPDF()._markdown_parse("----------"))
    expected = (Fragment("----------", GSTATE, k=PDF.k),)
    assert frags == expected


def test_markdown_parse_newline_after_markdown_link():  # issue 916
    text = "[fpdf2](https://py-pdf.github.io/fpdf2/)\nGo visit it!"
    frags = tuple(FPDF()._markdown_parse(text))
    expected = (
        Fragment(
            "fpdf2",
            {**GSTATE, "underline": True},
            k=PDF.k,
            link="https://py-pdf.github.io/fpdf2/",
        ),
        Fragment("\nGo visit it!", GSTATE, k=PDF.k),
    )
    assert frags == expected
