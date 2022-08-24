# pylint: disable=protected-access
from fpdf import FPDF
from fpdf.line_break import Fragment

PDF = FPDF()
GSTATE = PDF.get_current_graphics_state()
GSTATE_B = GSTATE.copy()
GSTATE_B["font_style"] = "B"
GSTATE_I = GSTATE.copy()
GSTATE_I["font_style"] = "I"
GSTATE_U = GSTATE.copy()
GSTATE_U["underline"] = True
GSTATE_BI = GSTATE.copy()
GSTATE_BI["font_style"] = "BI"


def test_markdown_parse_simple_ok():
    res = tuple(FPDF()._markdown_parse("**bold**, __italics__ and --underlined--"))
    exp = (
        Fragment("bold", GSTATE_B, k=PDF.k),
        Fragment(", ", GSTATE, k=PDF.k),
        Fragment("italics", GSTATE_I, k=PDF.k),
        Fragment(" and ", GSTATE, k=PDF.k),
        Fragment("underlined", GSTATE_U, k=PDF.k),
    )
    assert res == exp


def test_markdown_parse_overlapping():
    res = tuple(FPDF()._markdown_parse("**bold __italics__**"))
    exp = (
        Fragment("bold ", GSTATE_B, k=PDF.k),
        Fragment("italics", GSTATE_BI, k=PDF.k),
    )
    assert res == exp


def test_markdown_parse_crossing_markers():
    res = tuple(FPDF()._markdown_parse("**bold __and** italics__"))
    exp = (
        Fragment("bold ", GSTATE_B, k=PDF.k),
        Fragment("and", GSTATE_BI, k=PDF.k),
        Fragment(" italics", GSTATE_I, k=PDF.k),
    )
    assert res == exp


def test_markdown_parse_unterminated():
    res = tuple(FPDF()._markdown_parse("**bold __italics__"))
    exp = (
        Fragment("bold ", GSTATE_B, k=PDF.k),
        Fragment("italics", GSTATE_BI, k=PDF.k),
    )
    assert res == exp


def test_markdown_parse_line_of_markers():
    res = tuple(FPDF()._markdown_parse("*** woops"))
    exp = (Fragment("*** woops", GSTATE, k=PDF.k),)
    res = tuple(FPDF()._markdown_parse("----------"))
    exp = (Fragment("----------", GSTATE, k=PDF.k),)
    assert res == exp
