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
    frags = tuple(FPDF()._parse_chars("**bold**, __italics__ and --underlined--", True))
    expected = (
        Fragment("bold", GSTATE_B, k=PDF.k),
        Fragment(", ", GSTATE, k=PDF.k),
        Fragment("italics", GSTATE_I, k=PDF.k),
        Fragment(" and ", GSTATE, k=PDF.k),
        Fragment("underlined", GSTATE_U, k=PDF.k),
    )
    assert frags == expected


def test_markdown_parse_simple_ok_escaped():
    frags = tuple(
        FPDF()._parse_chars(
            "\\**bold\\**, \\__italics\\__ and \\--underlined\\-- escaped", True
        )
    )
    expected = (
        Fragment("**bold**, __italics__ and --underlined-- escaped", GSTATE, k=PDF.k),
    )
    assert frags == expected
    frags = tuple(
        FPDF()._parse_chars(
            r"raw \**bold\**, \__italics\__ and \--underlined\-- escaped", True
        )
    )
    expected = (
        Fragment(
            "raw **bold**, __italics__ and --underlined-- escaped", GSTATE, k=PDF.k
        ),
    )
    assert frags == expected
    frags = tuple(FPDF()._parse_chars("escape *\\*between marker*\\*", True))
    expected = (Fragment("escape *\\*between marker*\\*", GSTATE, k=PDF.k),)
    assert frags == expected
    frags = tuple(FPDF()._parse_chars("escape **\\after marker**\\", True))
    expected = (
        Fragment("escape ", GSTATE, k=PDF.k),
        Fragment("\\after marker", GSTATE_B, k=PDF.k),
        Fragment("\\", GSTATE, k=PDF.k),
    )


def test_markdown_unrelated_escape():
    frags = tuple(FPDF()._parse_chars("unrelated \\ escape \\**bold\\**", True))
    expected = (Fragment("unrelated \\ escape **bold**", GSTATE, k=PDF.k),)
    assert frags == expected
    frags = tuple(
        FPDF()._parse_chars("unrelated \\\\ double escape \\**bold\\**", True)
    )
    expected = (Fragment("unrelated \\\\ double escape **bold**", GSTATE, k=PDF.k),)
    assert frags == expected


def test_markdown_parse_multiple_escape():
    frags = tuple(FPDF()._parse_chars("\\\\**bold\\\\** double escaped", True))
    expected = (
        Fragment("\\", GSTATE, k=PDF.k),
        Fragment("bold\\", GSTATE_B, k=PDF.k),
        Fragment(" double escaped", GSTATE, k=PDF.k),
    )
    assert frags == expected
    frags = tuple(FPDF()._parse_chars("\\\\\\**triple bold\\\\\\** escaped", True))
    expected = (Fragment("\\**triple bold\\** escaped", GSTATE, k=PDF.k),)
    assert frags == expected


def test_markdown_parse_overlapping():
    frags = tuple(FPDF()._parse_chars("**bold __italics__**", True))
    expected = (
        Fragment("bold ", GSTATE_B, k=PDF.k),
        Fragment("italics", GSTATE_BI, k=PDF.k),
    )
    assert frags == expected


def test_markdown_parse_overlapping_escaped():
    frags = tuple(FPDF()._parse_chars("**bold \\__italics\\__**", True))
    expected = (Fragment("bold __italics__", GSTATE_B, k=PDF.k),)
    assert frags == expected


def test_markdown_parse_crossing_markers():
    frags = tuple(FPDF()._parse_chars("**bold __and** italics__", True))
    expected = (
        Fragment("bold ", GSTATE_B, k=PDF.k),
        Fragment("and", GSTATE_BI, k=PDF.k),
        Fragment(" italics", GSTATE_I, k=PDF.k),
    )
    assert frags == expected


def test_markdown_parse_crossing_markers_escaped():
    frags = tuple(FPDF()._parse_chars("**bold __and\\** italics__", True))
    expected = (
        Fragment("bold ", GSTATE_B, k=PDF.k),
        Fragment("and** italics", GSTATE_BI, k=PDF.k),
    )
    assert frags == expected


def test_markdown_parse_unterminated():
    frags = tuple(FPDF()._parse_chars("**bold __italics__", True))
    expected = (
        Fragment("bold ", GSTATE_B, k=PDF.k),
        Fragment("italics", GSTATE_BI, k=PDF.k),
    )
    assert frags == expected


def test_markdown_parse_unterminated_escaped():
    frags = tuple(FPDF()._parse_chars("**bold\\** __italics__", True))
    expected = (
        Fragment("bold** ", GSTATE_B, k=PDF.k),
        Fragment("italics", GSTATE_BI, k=PDF.k),
    )
    assert frags == expected


def test_markdown_parse_line_of_markers():
    frags = tuple(FPDF()._parse_chars("*** woops", True))
    expected = (Fragment("*** woops", GSTATE, k=PDF.k),)
    assert frags == expected
    frags = tuple(FPDF()._parse_chars("----------", True))
    expected = (Fragment("----------", GSTATE, k=PDF.k),)
    assert frags == expected
    frags = tuple(FPDF()._parse_chars("****BOLD**", True))
    expected = (Fragment("****BOLD", GSTATE, k=PDF.k),)
    assert frags == expected
    frags = tuple(FPDF()._parse_chars("* **BOLD**", True))
    expected = (
        Fragment("* ", GSTATE, k=PDF.k),
        Fragment("BOLD", GSTATE_B, k=PDF.k),
    )
    assert frags == expected


def test_markdown_parse_line_of_markers_escaped():
    frags = tuple(FPDF()._parse_chars("\\****BOLD**", True))
    expected = (Fragment("\\****BOLD", GSTATE, k=PDF.k),)
    assert frags == expected
    frags = tuple(FPDF()._parse_chars("*\\***BOLD**", True))
    expected = (Fragment("*\\***BOLD", GSTATE, k=PDF.k),)
    assert frags == expected


def test_markdown_parse_newline_after_markdown_link():  # issue 916
    text = "[fpdf2](https://py-pdf.github.io/fpdf2/)\nGo visit it!"
    frags = tuple(FPDF()._parse_chars(text, True))
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
