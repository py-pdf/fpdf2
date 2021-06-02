import itertools
from pathlib import Path

import pytest

from fpdf import FPDF
from fpdf.errors import FPDFException
from fpdf.fonts import fpdf_charwidths
from test.conftest import assert_pdf_equal

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
        str(e.value) == "Unknown style provided (only B/I/U letters are allowed): BDLO"
    )


def test_set_builtin_font(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    builtin_fonts = sorted(
        f for f in pdf.core_fonts if not f.endswith(("B", "I", "BI"))
    )
    for i, font_name in enumerate(builtin_fonts):
        styles = (
            ("",) if font_name in ("symbol", "zapfdingbats") else ("", "B", "I", "BI")
        )
        for j, style in enumerate(styles):
            pdf.set_font(font_name.capitalize(), style, 36)
            pdf.set_font(font_name.lower(), style, 36)
            pdf.text(0, 10 + 40 * i + 10 * j, "Hello World!")
    assert_pdf_equal(pdf, HERE / "fonts_set_builtin_font.pdf", tmp_path)


def test_issue_66(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", "B", 14)
    pdf.cell(txt="ABC")
    pdf.set_font("Times", size=10)
    pdf.cell(txt="DEF")
    # Setting the font to an already used one used to remove the text!
    pdf.set_font("Times", "B", 14)
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
            UserWarning,
            match=f"Substituting font {alias.lower()} by core font {alternative}",
        ):
            pdf.set_font(alias)

        # Test if font family is set correctly
        assert pdf.font_family == alternative
    # Test if the fonts were added in this order and without duplicats:
    # helvetica, courier, times
    assert [*pdf.fonts] == ["helvetica", "courier", "times"]


def test_set_font_core_font_attributes():
    """Test if the attributes of added core fonts are correct"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("courier")
    pdf.set_font("times")

    # Test for the font attributes
    assert pdf.fonts["courier"] == {
        "i": 1,
        "type": "core",
        "name": "Courier",
        "up": -100,
        "ut": 50,
        "cw": fpdf_charwidths["courier"],
        "fontkey": "courier",
    }
    assert pdf.fonts["times"] == {
        "i": 2,
        "type": "core",
        "name": "Times-Roman",
        "up": -100,
        "ut": 50,
        "cw": fpdf_charwidths["times"],
        "fontkey": "times",
    }


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
                ):
                    pdf.set_font(family, style=style)

                    # Test if style is set correctly (== no style)
                    assert pdf.font_style == ""

                # Test if underline is set correctly
                assert pdf.underline == int("U" in style)
