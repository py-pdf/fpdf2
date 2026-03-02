# pylint: disable=protected-access
from fpdf import FPDF
from fpdf.line_break import Fragment

PDF = FPDF()
GSTATE = PDF._get_current_graphics_state()
GSTATE_B = GSTATE.copy()
GSTATE_B.font_style = "B"
GSTATE_I = GSTATE.copy()
GSTATE_I.font_style = "I"
GSTATE_S = GSTATE.copy()
GSTATE_S.strikethrough = True
GSTATE_U = GSTATE.copy()
GSTATE_U.underline = True
GSTATE_BI = GSTATE.copy()
GSTATE_BI.font_style = "BI"


def merge_fragments(fragments):
    """
    Helper function for testing the escaping characters
    Will merge fragments that have different characters but same fragment.graphics_state
    and same fragment.k and same fragment.link.
    Example Input:
    (
    Fragment(characters=['a'], graphics_state={000}, k=1, link=None),
    Fragment(characters=['b'], graphics_state={000}, k=1, link=None)
    )
    Example Output:
    (Fragment(characters=['a', 'b'], graphics_state={000}, k=1, link=None))
    """
    if not fragments:
        return []

    merged_fragments = []
    current_fragment = fragments[0]

    for fragment in fragments[1:]:
        if (
            fragment.graphics_state == current_fragment.graphics_state
            and fragment.k == current_fragment.k
            and fragment.link == current_fragment.link
        ):
            current_fragment.characters.extend(fragment.characters)
        else:
            merged_fragments.append(current_fragment)
            current_fragment = fragment

    merged_fragments.append(current_fragment)

    return tuple(merged_fragments)


def test_markdown_parse_simple_ok():
    frags = tuple(
        FPDF()._parse_chars(
            "**bold**, __italics__, ~~strikethrough~~ and --underlined--", True
        )
    )
    expected = (
        Fragment("bold", GSTATE_B, k=PDF.k),
        Fragment(", ", GSTATE, k=PDF.k),
        Fragment("italics", GSTATE_I, k=PDF.k),
        Fragment(", ", GSTATE, k=PDF.k),
        Fragment("strikethrough", GSTATE_S, k=PDF.k),
        Fragment(" and ", GSTATE, k=PDF.k),
        Fragment("underlined", GSTATE_U, k=PDF.k),
    )
    assert frags == expected


def test_markdown_parse_simple_ok_escaped():
    frags = merge_fragments(
        tuple(
            FPDF()._parse_chars(
                "\\**bold\\**, \\__italics\\__ and \\--underlined\\-- escaped", True
            )
        )
    )
    expected = (
        Fragment("**bold**, __italics__ and --underlined-- escaped", GSTATE, k=PDF.k),
    )
    assert frags == expected
    frags = merge_fragments(
        tuple(
            FPDF()._parse_chars(
                r"raw \**bold\**, \__italics\__ and \--underlined\-- escaped", True
            )
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
    assert frags == expected


def test_markdown_parse_strikethrough_escaped():
    frags = merge_fragments(tuple(FPDF()._parse_chars("\\~~strike\\~~", True)))
    expected = (Fragment("~~strike~~", GSTATE, k=PDF.k),)
    assert frags == expected


def test_markdown_unrelated_escape():
    frags = merge_fragments(
        tuple(FPDF()._parse_chars("unrelated \\ escape \\**bold\\**", True))
    )
    expected = (Fragment("unrelated \\ escape **bold**", GSTATE, k=PDF.k),)
    assert frags == expected
    frags = merge_fragments(
        tuple(FPDF()._parse_chars("unrelated \\\\ double escape \\**bold\\**", True))
    )
    expected = (Fragment("unrelated \\\\ double escape **bold**", GSTATE, k=PDF.k),)
    assert frags == expected


def test_markdown_parse_multiple_escape():
    frags = merge_fragments(
        tuple(FPDF()._parse_chars("\\\\**bold\\\\** double escaped", True))
    )
    expected = (
        Fragment("\\\\", GSTATE, k=PDF.k),
        Fragment("bold\\\\", GSTATE_B, k=PDF.k),
        Fragment(" double escaped", GSTATE, k=PDF.k),
    )

    assert frags == expected
    frags = merge_fragments(
        tuple(FPDF()._parse_chars("\\\\\\**triple bold\\\\\\** escaped", True))
    )
    expected = (Fragment("\\\\**triple bold\\\\** escaped", GSTATE, k=PDF.k),)
    assert frags == expected


def test_markdown_parse_overlapping():
    frags = tuple(FPDF()._parse_chars("**bold __italics__**", True))
    expected = (
        Fragment("bold ", GSTATE_B, k=PDF.k),
        Fragment("italics", GSTATE_BI, k=PDF.k),
    )
    assert frags == expected


def test_markdown_parse_overlapping_escaped():
    frags = merge_fragments(
        tuple(FPDF()._parse_chars("**bold \\__italics\\__**", True))
    )
    expected = (Fragment("bold __italics__", GSTATE_B, k=PDF.k),)
    assert frags == expected


def test_markdown_parse_crossing_markers():
    frags = merge_fragments(
        tuple(FPDF()._parse_chars("**bold __and** italics__", True))
    )
    expected = (
        Fragment("bold ", GSTATE_B, k=PDF.k),
        Fragment("and", GSTATE_BI, k=PDF.k),
        Fragment(" italics", GSTATE_I, k=PDF.k),
    )
    assert frags == expected


def test_markdown_parse_crossing_markers_escaped():
    frags = merge_fragments(
        tuple(FPDF()._parse_chars("**bold __and\\** italics__", True))
    )
    expected = (
        Fragment("bold ", GSTATE_B, k=PDF.k),
        Fragment("and** italics", GSTATE_BI, k=PDF.k),
    )
    assert frags == expected


def test_markdown_parse_unterminated():
    frags = merge_fragments(tuple(FPDF()._parse_chars("**bold __italics__", True)))
    expected = (
        Fragment("bold ", GSTATE_B, k=PDF.k),
        Fragment("italics", GSTATE_BI, k=PDF.k),
    )
    assert frags == expected


def test_markdown_parse_unterminated_escaped():
    frags = merge_fragments(tuple(FPDF()._parse_chars("**bold\\** __italics__", True)))
    expected = (
        Fragment("bold** ", GSTATE_B, k=PDF.k),
        Fragment("italics", GSTATE_BI, k=PDF.k),
    )
    assert frags == expected


def test_markdown_parse_line_of_markers():
    frags = merge_fragments(tuple(FPDF()._parse_chars("*** woops", True)))
    expected = (Fragment("*** woops", GSTATE, k=PDF.k),)
    assert frags == expected
    frags = merge_fragments(tuple(FPDF()._parse_chars("----------", True)))
    expected = (Fragment("----------", GSTATE, k=PDF.k),)
    assert frags == expected
    frags = tuple(FPDF()._parse_chars("****BOLD**", True))
    expected = (Fragment("****BOLD", GSTATE, k=PDF.k),)
    assert frags == expected
    frags = merge_fragments(tuple(FPDF()._parse_chars("\\****BOLD**\\**", True)))
    expected = (
        Fragment("**", GSTATE, k=PDF.k),
        Fragment("BOLD", GSTATE_B, k=PDF.k),
        Fragment("**", GSTATE, k=PDF.k),
    )
    assert frags == expected
    frags = merge_fragments(tuple(FPDF()._parse_chars("* **BOLD**", True)))
    expected = (
        Fragment("* ", GSTATE, k=PDF.k),
        Fragment("BOLD", GSTATE_B, k=PDF.k),
    )
    assert frags == expected


def test_markdown_parse_line_of_markers_escaped():
    frags = merge_fragments(tuple(FPDF()._parse_chars("\\****BOLD**", True)))
    expected = (
        Fragment("**", GSTATE, k=PDF.k),
        Fragment("BOLD", GSTATE_B, k=PDF.k),
    )
    assert frags == expected
    frags = merge_fragments(tuple(FPDF()._parse_chars("*\\***BOLD**", True)))
    expected = (Fragment("****BOLD", GSTATE, k=PDF.k),)
    assert frags == expected


def test_markdown_parse_newline_after_markdown_link():  # issue 916
    text = "[fpdf2](https://py-pdf.github.io/fpdf2/)\nGo visit it!"
    frags = merge_fragments(tuple(FPDF()._parse_chars(text, True)))
    gstate_link = GSTATE.copy()
    gstate_link.underline = True
    expected = (
        Fragment(
            "fpdf2",
            gstate_link,
            k=PDF.k,
            link="https://py-pdf.github.io/fpdf2/",
        ),
        Fragment("\nGo visit it!", GSTATE, k=PDF.k),
    )
    assert frags == expected


def test_markdown_parse_trailing_escape():
    frags = merge_fragments(tuple(FPDF()._parse_chars("trailing \\\\", True)))
    expected = (Fragment("trailing \\\\", GSTATE, k=PDF.k),)
    assert frags == expected


def test_markdown_parse_escape_non_marker():
    frags = merge_fragments(tuple(FPDF()._parse_chars(r"\a", True)))
    expected = (Fragment(r"\a", GSTATE, k=PDF.k),)
    assert frags == expected


def test_markdown_parse_escape_before_marker_odd_even():
    frags = tuple(FPDF()._parse_chars("\\\\**bold**", True))
    expected = (
        Fragment("\\\\", GSTATE, k=PDF.k),
        Fragment("bold", GSTATE_B, k=PDF.k),
    )
    assert frags == expected

    frags = tuple(FPDF()._parse_chars("\\**bold**", True))
    expected = (
        Fragment("**", GSTATE, k=PDF.k),
        Fragment("bold", GSTATE, k=PDF.k),
    )
    assert frags == expected


def test_markdown_parse_marker_adjacency():
    frags = merge_fragments(tuple(FPDF()._parse_chars("a***b", True)))
    expected = (Fragment("a***b", GSTATE, k=PDF.k),)
    assert frags == expected

    frags = tuple(FPDF()._parse_chars("**bold***", True))
    expected = (Fragment("bold***", GSTATE_B, k=PDF.k),)
    assert frags == expected


def test_markdown_parse_across_newline():
    frags = tuple(FPDF()._parse_chars("**bold\nstill**", True))
    expected = (Fragment("bold\nstill", GSTATE_B, k=PDF.k),)
    assert frags == expected


def test_markdown_parse_nested_combinations():
    frags = tuple(FPDF()._parse_chars("**bold --under--**", True))
    gstate_bu = GSTATE.copy()
    gstate_bu.font_style = "B"
    gstate_bu.underline = True
    expected = (
        Fragment("bold ", GSTATE_B, k=PDF.k),
        Fragment("under", gstate_bu, k=PDF.k),
    )
    assert frags == expected

    frags = tuple(FPDF()._parse_chars("~~strike __ital__~~", True))
    gstate_si = GSTATE_S.copy()
    gstate_si.font_style = "I"
    expected = (
        Fragment("strike ", GSTATE_S, k=PDF.k),
        Fragment("ital", gstate_si, k=PDF.k),
    )
    assert frags == expected


def test_markdown_parse_link_variations():
    frags = tuple(FPDF()._parse_chars("[go](2)", True))
    assert len(frags) == 1
    assert "".join(frags[0].characters) == "go"
    assert isinstance(frags[0].link, int)
    assert frags[0].graphics_state.underline is True

    frags = tuple(FPDF()._parse_chars("[**bold**](https://example.com)", True))
    assert len(frags) == 1
    assert "".join(frags[0].characters) == "**bold**"
    assert frags[0].graphics_state.underline is True
    assert frags[0].graphics_state.font_style == ""
    assert frags[0].link == "https://example.com"

    frags = tuple(FPDF()._parse_chars("[x](url)**y**", True))
    assert len(frags) == 2
    assert "".join(frags[0].characters) == "x"
    assert frags[0].graphics_state.underline is True
    assert frags[0].link == "url"
    assert "".join(frags[1].characters) == "y"
    assert frags[1].graphics_state.font_style == "B"

    frags = tuple(FPDF()._parse_chars("\\[x](url)", True))
    expected = (
        Fragment("\\", GSTATE, k=PDF.k),
        Fragment("x", GSTATE_U, k=PDF.k, link="url"),
    )
    assert frags == expected
    assert frags[1].link == "url"
