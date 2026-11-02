import itertools
from pathlib import Path

import pytest

from fpdf import FPDF
from fpdf.enums import TextEmphasis
from fpdf.errors import FPDFException
from fpdf.fonts import CORE_FONTS, CORE_FONTS_CHARWIDTHS
from test.conftest import assert_pdf_equal, assert_same_file

HERE = Path(__file__).resolve().parent


def test_no_set_font():
    pdf = FPDF()
    pdf.add_page()
    with pytest.raises(FPDFException) as error:
        pdf.text(10, 10, "Hello World!")
    expected_msg = "No font set, you need to call set_font() beforehand"
    assert str(error.value) == expected_msg


def test_set_unknown_font():
    pdf = FPDF()
    pdf.add_page()
    with pytest.raises(FPDFException) as e:
        pdf.set_font("Dummy")
    assert (
        str(e.value)
        == "Undefined font: dummy - Use built-in fonts or FPDF.add_font() beforehand"
    )


def test_set_unknown_style():
    pdf = FPDF()
    pdf.add_page()
    with pytest.raises(ValueError) as e:
        pdf.set_font("Times", style="bold")
    assert (
        str(e.value)
        == "Unknown style provided (only B/I/S/U letters are allowed): BDLO"
    )


def test_set_font_repeated_style_letters():
    "A style letter given twice is the same style: 'BB' is bold, not an unknown font."
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", style="BB")
    assert pdf.font_style == "B"
    pdf.set_font("Times", style="ibIu")
    assert pdf.font_style == "BI"
    assert pdf.underline


@pytest.mark.parametrize("size", [-0.5, -12])
def test_set_font_negative_size(size):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=12)
    with pytest.raises(ValueError, match="Font size must be zero or a positive number"):
        pdf.set_font("Times", size=size)
    with pytest.raises(ValueError, match="Font size must be zero or a positive number"):
        pdf.set_font_size(size)
    assert pdf.font_size_pt == 12


def test_set_builtin_font(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    builtin_fonts = sorted(f for f in CORE_FONTS if not f.endswith(("B", "I", "BI")))
    for i, font_name in enumerate(builtin_fonts):
        styles = (
            ("",) if font_name in ("symbol", "zapfdingbats") else ("", "B", "I", "BI")
        )
        for j, style in enumerate(styles):
            pdf.set_font(font_name.capitalize(), style, size=36)
            pdf.set_font(font_name.lower(), style, size=36)
            pdf.text(0, 10 + 40 * i + 10 * j, "Hello World!")
    assert_pdf_equal(pdf, HERE / "fonts_set_builtin_font.pdf", tmp_path)


def test_issue_66(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", style="B", size=14)
    pdf.cell(text="ABC")
    pdf.set_font("Times", size=10)
    pdf.cell(text="DEF")
    # Setting the font to an already used one used to remove the text!
    pdf.set_font("Times", style="B", size=14)
    assert_pdf_equal(pdf, HERE / "fonts_issue_66.pdf", tmp_path)


def test_set_font_aliases_as_font():
    """Test if font aliases are being converted to their alternatives."""
    pdf = FPDF()
    pdf.add_page()
    aliases = ["ARIAL", "Arial", "arial", "couriernew", "timesnewroman"]
    alternatives = ["helvetica", "helvetica", "helvetica", "courier", "times"]
    for alias, alternative in zip(aliases, alternatives):
        # Test if warning get's emitted
        with pytest.warns(
            DeprecationWarning,
            match=f"Substituting font {alias.lower()} by core font {alternative} - This is deprecated since v2.7.8, and will soon be removed",
        ) as record:
            pdf.set_font(alias)

        assert len(record) == 1
        assert_same_file(record[0].filename, __file__)

        # Test if font family is set correctly
        assert pdf.font_family == alternative
    # Test if the fonts were added in this order and without duplicates:
    # helvetica, courier, times
    assert [*pdf.fonts] == ["helvetica", "courier", "times"]


def test_set_font_core_font_attributes():
    """Test if the attributes of added core fonts are correct"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("courier")
    pdf.set_font("times")

    # Test for the font attributes
    assert pdf.fonts["courier"].i == 1
    assert pdf.fonts["courier"].type == "core"
    assert pdf.fonts["courier"].name == "Courier"
    assert pdf.fonts["courier"].up == -100
    assert pdf.fonts["courier"].ut == 50
    assert pdf.fonts["courier"].cw == CORE_FONTS_CHARWIDTHS["courier"]
    assert pdf.fonts["courier"].fontkey == "courier"
    assert pdf.fonts["courier"].emphasis == 0

    assert pdf.fonts["times"].i == 2
    assert pdf.fonts["times"].type == "core"
    assert pdf.fonts["times"].name == "Times-Roman"
    assert pdf.fonts["times"].up == -100
    assert pdf.fonts["times"].ut == 50
    assert pdf.fonts["times"].cw == CORE_FONTS_CHARWIDTHS["times"]
    assert pdf.fonts["times"].fontkey == "times"
    assert pdf.fonts["times"].emphasis == 0


def test_set_font_styles():
    """Test the different font styles "B", "I" and "U" and combinations."""
    pdf = FPDF()
    pdf.add_page()

    # Generate all possible combinations of "B", "I" and "U" -> "B", "BI", "BUI" ...
    # including "" (no style)
    styles = [
        "".join(style) for i in range(4) for style in itertools.permutations("BUI", i)
    ]

    for style in styles:
        pdf.set_font("Times", style=style)

        # Test if underline is set correctly
        assert pdf.underline == int("U" in style)

        # pylint: disable=redefined-loop-name
        # Test if style is set correctly
        style = style.replace("U", "")
        if style == "IB":
            style = "BI"
        assert pdf.font_style == style


def test_set_font_zapfdingbats_symbol_with_style():
    """Test the fonts zapfdingbats and symbol with a style. This should emit a
    warning, as these fonts don't have a style."""
    pdf = FPDF()
    pdf.add_page()

    # Generate all possible combinations of "B", "I" and "U" -> "B", "BI", "BUI" ...
    # excluding "" (no style)
    styles = [
        "".join(style)
        for i in range(1, 4)
        for style in itertools.permutations("BUI", i)
    ]
    for family in ("zapfdingbats", "symbol"):
        for style in styles:
            if "B" in style or "I" in style:
                with pytest.warns(
                    UserWarning,
                    match=f"Built-in font {family} only has a single 'style' and "
                    f"can't be bold or italic",
                ) as record:
                    pdf.set_font(family, style=style)

                    # Test if style is set correctly (== no style)
                    assert pdf.font_style == ""

                assert len(record) == 1
                assert_same_file(record[0].filename, __file__)

                # Test if underline is set correctly
                assert pdf.underline == int("U" in style)


def test_set_font_restores_current_font_after_state_divergence():
    """
    Regression test for gh-1488: set_font() must not early-return when font_family
    matches the requested family but current_font has diverged (e.g. after fallback
    font rendering sets self.current_font to the fallback font object while leaving
    self.font_family pointing to the primary font).
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    # Register Times so it can be used below.
    pdf.set_font("Times", size=12)
    times_font = pdf.current_font

    # Simulate the divergent state: font_family says 'helvetica' but
    # current_font is the Times object (as happens when a fallback font
    # was the last font written to the page content stream).
    pdf.font_family = "helvetica"
    pdf.font_style = ""
    pdf.font_size_pt = 12
    pdf.current_font = times_font

    assert pdf.font_family == "helvetica"
    assert pdf.current_font.fontkey == "times"

    # set_font("Helvetica") must restore current_font to helvetica, not return early.
    pdf.set_font("Helvetica", size=12)
    assert pdf.current_font.fontkey == "helvetica", (
        f"set_font() returned early due to matching font_family, "
        f"but current_font was not restored (got {pdf.current_font.fontkey!r})"
    )


@pytest.mark.parametrize(
    "style_input,expected_fontkey,expected_style,expected_emphasis",
    [
        ("", "helvetica", "", TextEmphasis.coerce("")),
        ("B", "helveticaB", "B", TextEmphasis.B),
        ("I", "helveticaI", "I", TextEmphasis.I),
        ("BI", "helveticaBI", "BI", TextEmphasis.B | TextEmphasis.I),
        ("IB", "helveticaBI", "BI", TextEmphasis.B | TextEmphasis.I),
    ],
)
def test_font_style_setter_synchronizes_font(
    style_input, expected_fontkey, expected_style, expected_emphasis
):
    """Setting pdf.font_style must select the corresponding font and update emphasis (#1223)."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.font_style = style_input
    assert pdf.font_style == expected_style
    assert pdf.current_font.fontkey == expected_fontkey
    assert pdf.emphasis == expected_emphasis


@pytest.mark.parametrize(
    "emphasis_input,expected_fontkey,expected_style,expected_underline,expected_strikethrough",
    [
        ("BOLD", "helveticaB", "B", False, False),
        ("B", "helveticaB", "B", False, False),
        ("I", "helveticaI", "I", False, False),
        ("italics", "helveticaI", "I", False, False),
        ("U", "helvetica", "", True, False),
        ("Underline", "helvetica", "", True, False),
        ("S", "helvetica", "", False, True),
        (TextEmphasis.B, "helveticaB", "B", False, False),
        (TextEmphasis.I, "helveticaI", "I", False, False),
        (TextEmphasis.B | TextEmphasis.U, "helveticaB", "B", True, False),
        (
            TextEmphasis.B | TextEmphasis.I | TextEmphasis.U | TextEmphasis.S,
            "helveticaBI",
            "BI",
            True,
            True,
        ),
        ("", "helvetica", "", False, False),
    ],
)
def test_emphasis_setter_synchronizes_font(
    emphasis_input,
    expected_fontkey,
    expected_style,
    expected_underline,
    expected_strikethrough,
):
    """Setting pdf.emphasis must update font style, underline, strikethrough, and font selection (#1223)."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.emphasis = emphasis_input
    assert pdf.font_style == expected_style
    assert pdf.current_font.fontkey == expected_fontkey
    assert pdf.underline is expected_underline
    assert pdf.strikethrough is expected_strikethrough


def test_font_style_and_emphasis_setters_before_set_font():
    """Setting pdf.font_style or pdf.emphasis before font_family is configured updates internal state without crashing (#1223)."""
    pdf = FPDF()
    pdf.font_style = "B"
    assert pdf.font_style == "B"

    pdf2 = FPDF()
    pdf2.emphasis = TextEmphasis.B | TextEmphasis.U
    assert pdf2.font_style == "B"
    assert pdf2.underline is True
    assert pdf2.strikethrough is False
    assert pdf2.emphasis == TextEmphasis.B | TextEmphasis.U


def test_font_style_setter_sequence_issue_1223():
    """Verify consecutive font_style updates properly change current_font (#1223)."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.font_style = ""
    pdf.cell(text="Eins.")
    assert pdf.current_font.fontkey == "helvetica"
    pdf.font_style = "B"
    pdf.cell(text="Zwei.")
    assert pdf.current_font.fontkey == "helveticaB"
    pdf.font_style = "I"
    pdf.cell(text="Drei.")
    assert pdf.current_font.fontkey == "helveticaI"


def test_font_style_setter_preserves_underline_and_strikethrough():
    """Setting pdf.font_style must preserve existing underline and strikethrough flags (#1223)."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", style="US", size=12)

    with pdf.text_columns() as columns:
        columns.write("Hello")

    assert pdf.underline is True
    assert pdf.strikethrough is True

    # Direct setter update must also preserve flags
    pdf.font_style = "B"
    assert pdf.font_style == "B"
    assert pdf.underline is True
    assert pdf.strikethrough is True
    assert pdf.current_font.fontkey == "helveticaB"
