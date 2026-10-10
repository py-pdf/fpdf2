"""
Comprehensive test suite for unicode_range feature
Tests both the parser and the emoji fallback functionality
"""

from pathlib import Path

import pytest

from fpdf import FPDF
from fpdf.util import get_parsed_unicode_range
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent

# Unit tests for get_parsed_unicode_range method


def test_single_u_plus_codepoint():
    """Test parsing single U+ format codepoint"""

    result = get_parsed_unicode_range("U+1F600")
    assert result == {0x1F600}


def test_u_plus_range():
    """Test parsing U+ format range"""

    result = get_parsed_unicode_range("U+1F600-1F603")
    assert result == {0x1F600, 0x1F601, 0x1F602, 0x1F603}


def test_comma_separated_u_plus_ranges():
    """Test parsing comma-separated U+ ranges in single string"""

    result = get_parsed_unicode_range("U+0041-0043, U+0061-0063")
    expected = {0x41, 0x42, 0x43, 0x61, 0x62, 0x63}  # A-C, a-c
    assert result == expected


def test_list_of_u_plus_strings():
    """Test parsing list of U+ format strings"""

    result = get_parsed_unicode_range(["U+1F600-1F602", "U+2600", "U+2615"])
    expected = {0x1F600, 0x1F601, 0x1F602, 0x2600, 0x2615}
    assert result == expected


def test_integer_tuple_range():
    """Test parsing tuple with integer range"""

    result = get_parsed_unicode_range([(0x1F600, 0x1F603)])
    assert result == {0x1F600, 0x1F601, 0x1F602, 0x1F603}


def test_list_of_integer_tuples():
    """Test parsing multiple tuple ranges"""

    result = get_parsed_unicode_range([(0x41, 0x43), (0x61, 0x63)])
    expected = {0x41, 0x42, 0x43, 0x61, 0x62, 0x63}
    assert result == expected


def test_list_of_single_integers():
    """Test parsing list of individual integer codepoints"""

    result = get_parsed_unicode_range([0x1F600, 0x2600, 128515])
    assert result == {0x1F600, 0x2600, 128515}


def test_mixed_formats():
    """Test parsing mixed format input"""

    result = get_parsed_unicode_range(
        ["U+1F600-1F602", (0x2600, 0x2601), 0x2615, "U+0041"]
    )
    expected = {0x1F600, 0x1F601, 0x1F602, 0x2600, 0x2601, 0x2615, 0x41}
    assert result == expected


def test_case_insensitive_u_plus():
    """Test that u+ (lowercase) works same as U+"""

    result = get_parsed_unicode_range("u+1f600-1f602")
    expected = {0x1F600, 0x1F601, 0x1F602}
    assert result == expected


def test_whitespace_handling():
    """Test that whitespace is properly handled"""

    result = get_parsed_unicode_range("  U+1F600  ,  U+2600-2602  ")
    expected = {0x1F600, 0x2600, 0x2601, 0x2602}
    assert result == expected


def test_empty_input():
    """Test empty unicode_range returns empty set"""

    with pytest.raises(ValueError, match="unicode_range cannot be empty"):
        get_parsed_unicode_range([])


def test_single_character_range():
    """Test range where start == end"""

    result = get_parsed_unicode_range([(0x41, 0x41)])
    assert result == {0x41}


def test_large_range():
    """Test handling of very large unicode ranges"""

    result = get_parsed_unicode_range("U+4E00-9FFF")
    # Full CJK Unified Ideographs block (20,000+ characters)
    assert len(result) == 0x9FFF - 0x4E00 + 1
    assert 0x4E00 in result
    assert 0x9FFF in result


def test_supplementary_plane():
    """Test ranges in supplementary Unicode planes"""

    result = get_parsed_unicode_range("U+1F600-1F650")
    assert 0x1F600 in result
    assert 0x1F650 in result
    assert len(result) == 0x1F650 - 0x1F600 + 1


# Test error handling in get_parsed_unicode_range


def test_invalid_range_start_greater_than_end():
    """Test error when start > end in range"""

    with pytest.raises(ValueError) as error:
        get_parsed_unicode_range("U+1F603-1F600")
    assert "Invalid range" in str(error.value)


def test_invalid_tuple_length():
    """Test error for tuple with wrong number of elements"""

    with pytest.raises(ValueError) as error:
        get_parsed_unicode_range([(0x1F600, 0x1F602, 0x1F603)])
    assert "exactly 2 elements" in str(error.value)


def test_negative_codepoint():
    """Test error for negative codepoint"""

    with pytest.raises(ValueError) as error:
        get_parsed_unicode_range([-1])
    assert "must be non-negative" in str(error.value)


def test_invalid_hex_format():
    """Test error for invalid hex string"""

    with pytest.raises(ValueError):
        get_parsed_unicode_range("U+GHIJ")


def test_unsupported_type():
    """Test error for unsupported input type"""

    with pytest.raises(ValueError) as error:
        get_parsed_unicode_range([3.14])
    assert "Unsupported unicode_range item type" in str(error.value)


def test_invalid_range_format():
    """Test error for malformed range string"""

    with pytest.raises(ValueError):
        get_parsed_unicode_range("U+1F600-1F602-1F604")


# Test that unicode_range correctly filters font character maps


def test_filters_basic_latin():
    """Test filtering to basic Latin characters only"""

    pdf = FPDF()
    pdf.add_font(
        family="DejaVu",
        fname=HERE / "DejaVuSans.ttf",
        unicode_range="U+0041-005A",  # A-Z only
    )
    font = pdf.fonts["dejavu"]

    # Should have A-Z
    assert 0x0041 in font.cmap  # A
    assert 0x005A in font.cmap  # Z

    # Should NOT have a-z or other chars
    assert 0x0061 not in font.cmap  # a
    assert 0x007A not in font.cmap  # z


def test_filters_multiple_ranges():
    """Test filtering with multiple ranges"""

    pdf = FPDF()
    pdf.add_font(
        family="DejaVu",
        fname=HERE / "DejaVuSans.ttf",
        unicode_range=[(0x0041, 0x005A), (0x0061, 0x007A)],  # A-Z and a-z
    )
    font = pdf.fonts["dejavu"]

    assert 0x0041 in font.cmap  # A
    assert 0x0061 in font.cmap  # a
    assert 0x0030 not in font.cmap  # 0 (digit)


def test_empty_range_raises_value_error():
    """Test that an empty unicode_range raises a ValueError"""

    pdf = FPDF()
    with pytest.raises(ValueError, match="unicode_range cannot be empty"):
        pdf.add_font(family="DejaVu", fname=HERE / "DejaVuSans.ttf", unicode_range=[])


def test_none_range_keeps_full_cmap():
    """Test that None unicode_range keeps full font cmap"""

    pdf = FPDF()
    pdf.add_font(family="DejaVu", fname=HERE / "DejaVuSans.ttf", unicode_range=None)
    font = pdf.fonts["dejavu"]
    # DejaVu has thousands of glyphs
    assert len(font.cmap) > 2000


def test_preserves_font_style():
    """Test that unicode_range works with font styles"""

    pdf = FPDF()
    pdf.add_font(
        family="DejaVu",
        style="B",
        fname=HERE / "DejaVuSans-Bold.ttf",
        unicode_range="U+0041-005A",
    )
    assert "dejavuB" in pdf.fonts
    font = pdf.fonts["dejavuB"]
    assert 0x0041 in font.cmap


def test_emoji_fallback_with_unicode_range(tmp_path):
    """Test that emoji falls back to color font when main font filtered"""
    pdf = FPDF()

    pdf.add_font(
        family="DejaVu",
        fname=HERE / "DejaVuSans.ttf",
        unicode_range="U+0000-007F",  # Basic Latin only, no emoji
    )

    # Fallback: Noto Emoji renders all emojis in color
    pdf.add_font(
        family="NotoEmoji",
        fname=HERE.parent / "color_font" / "colrv1-NotoColorEmoji.ttf",
    )

    pdf.set_font("DejaVu", size=24)
    pdf.set_fallback_fonts(["NotoEmoji"])
    pdf.add_page()

    # Text with emoji that DejaVu has (monochrome) but we want from NotoEmoji
    pdf.cell(w=0, text="Hello 😀 🚀 ☀ ☕")

    assert_pdf_equal(
        pdf,
        HERE / "emoji_fallback_with_unicode_range.pdf",
        tmp_path,
    )


def test_emoji_without_unicode_range_shows_monochrome(tmp_path):
    """Test baseline: without unicode_range, DejaVu's monochrome emoji is used"""

    pdf = FPDF()

    # Main font: DejaVu without unicode_range restriction
    pdf.add_font(family="DejaVu", fname=HERE / "DejaVuSans.ttf")

    # Fallback: Noto Emoji (won't be used for chars DejaVu has)
    pdf.add_font(
        family="NotoEmoji",
        fname=HERE.parent / "color_font" / "colrv1-NotoColorEmoji.ttf",
    )

    pdf.set_font("DejaVu", size=24)
    pdf.set_fallback_fonts(["NotoEmoji"])
    pdf.add_page()

    # Some emoji will render as monochrome from DejaVu
    pdf.cell(w=0, text="Hello 😀 🚀 ☀ ☕")

    assert_pdf_equal(
        pdf,
        HERE / "emoji_without_unicode_range.pdf",
        tmp_path,
    )


def test_restrict_emoji_font_to_specific_ranges(tmp_path):
    """Test restricting emoji font to only handle specific emoji ranges"""

    pdf = FPDF()

    pdf.add_font(
        family="DejaVu",
        fname=HERE / "DejaVuSans.ttf",
        unicode_range="U+0020-007E",
    )

    pdf.add_font(
        family="NotoEmoji",
        fname=HERE.parent / "color_font" / "colrv1-NotoColorEmoji.ttf",
        unicode_range="U+1F600-1F64F",  # Emoticons only
    )

    pdf.set_font("DejaVu", size=24)
    pdf.set_fallback_fonts(["NotoEmoji"])
    pdf.add_page()

    # 😀 is in emoticons range (will use NotoEmoji)
    # ☀ is in misc symbols (not in NotoEmoji's restricted range as well as not in DejaVu)
    pdf.cell(w=0, text="Hello 😀 World ☀")

    assert_pdf_equal(pdf, HERE / "emoji_restricted_range.pdf", tmp_path)


def test_multiple_emoji_fonts_different_ranges(tmp_path):
    """Test using multiple emoji fonts with different unicode ranges"""

    pdf = FPDF()

    pdf.add_font(
        family="DejaVu",
        fname=HERE / "DejaVuSans.ttf",
        unicode_range="U+0020-007E, U+2600-26FF",
    )

    pdf.add_font(
        family="NotoEmoji",
        fname=HERE.parent / "color_font" / "colrv1-NotoColorEmoji.ttf",
        unicode_range="U+1F600-1F64F, U+1F680-1F6FF",
    )

    pdf.set_font("DejaVu", size=24)
    pdf.set_fallback_fonts(["NotoEmoji"])
    pdf.add_page()

    # Misc Symbols (DejaVu - monochrome)
    pdf.cell(w=0, text="Symbols: ☀ ☁ ☂ ☃ ⚡ ☕ ♠ ♥ ♦")
    pdf.ln()
    # Emoticons (NotoEmoji - colorful)
    pdf.cell(w=0, text="Faces: 😀 😁 😂 😃 😄 😅 😆 😊 😍 😎")
    pdf.ln()
    # Transport (NotoEmoji - colorful)
    pdf.cell(w=0, text="Transport: 🚀 🚁 🚂 🚃 🚄 🚅 🚗 🚙")
    pdf.ln()
    # Mixed: showing contrast
    pdf.cell(w=0, text="Mixed: ☀ 😀 ☕ 😊 ☂ 🚀 ♦ 😎 ♥")

    assert_pdf_equal(pdf, HERE / "multiple_emoji_fonts.pdf", tmp_path)


def test_mixed_text_with_multiple_scripts(tmp_path):
    """Test document with Latin, symbols, and emoji"""

    pdf = FPDF()

    # Main font: Basic Latin + Latin Extended
    pdf.add_font(
        family="DejaVu",
        fname=HERE / "DejaVuSans.ttf",
        unicode_range="U+0020-007F, U+00A0-00FF, U+0100-017F",
    )

    # Emoji font
    pdf.add_font(
        family="NotoEmoji",
        fname=HERE.parent / "color_font" / "colrv1-NotoColorEmoji.ttf",
        unicode_range="U+1F300-1F9FF, U+2600-27BF",
    )

    pdf.set_font("DejaVu", size=16)
    pdf.set_fallback_fonts(["NotoEmoji"])
    pdf.add_page()

    pdf.cell(w=0, text="Regular text")
    pdf.ln()
    pdf.cell(w=0, text="Accented: café, naïve, résumé")
    pdf.ln()
    pdf.cell(w=0, text="Emoji: 😀 🎉 ☀ 🚀 ⭐")
    pdf.ln()
    pdf.cell(w=0, text="Mixed: Hello 😀 café ☕")

    assert_pdf_equal(
        pdf,
        HERE / "mixed_text_multiple_scripts.pdf",
        tmp_path,
    )


def test_prefer_specialized_font_for_punctuation(tmp_path):
    """Test preferring a specialized font for smart quotes"""

    pdf = FPDF()

    pdf.add_font(
        family="DejaVu",
        fname=HERE / "DejaVuSans.ttf",
        unicode_range="U+0020-2017, U+201A-10FFFF",  # Skip U+2018-2019
    )

    pdf.add_font(
        family="DejaVuQuotes",
        fname=HERE / "DejaVuSans-Bold.ttf",
        unicode_range="U+2018-201F",  # Smart quotes
    )

    pdf.set_font("DejaVu", size=24)
    pdf.set_fallback_fonts(["DejaVuQuotes"])
    pdf.add_page()
    pdf.cell(w=0, text="Regular text with 'smart' and \"fancy\" quotes")

    assert_pdf_equal(
        pdf,
        HERE / "specialized_punctuation.pdf",
        tmp_path,
    )


def test_multi_cell_with_unicode_range(tmp_path):
    """Test unicode_range works with multi_cell and text wrapping"""

    pdf = FPDF()

    pdf.add_font(
        family="DejaVu", fname=HERE / "DejaVuSans.ttf", unicode_range="U+0020-007E"
    )

    pdf.add_font(
        family="NotoEmoji",
        fname=HERE.parent / "color_font" / "colrv1-NotoColorEmoji.ttf",
        unicode_range="U+1F600-1F64F, U+2600-26FF",
    )

    pdf.set_font("DejaVu", size=16)
    pdf.set_fallback_fonts(["NotoEmoji"])
    pdf.add_page()

    long_text = (
        "This is a long text with emoji 😀 that should wrap "
        "across multiple lines ☀ and still render correctly 🚀 "
        "even when using unicode_range to control font fallback. "
        "More emoji: 😊 ⭐ 🎉"
    )

    pdf.multi_cell(w=0, text=long_text)

    assert_pdf_equal(
        pdf,
        HERE / "multi_cell_unicode_range.pdf",
        tmp_path,
    )


def test_markdown_with_unicode_range(tmp_path):
    """Test unicode_range works with markdown formatting"""

    pdf = FPDF()

    pdf.add_font(
        family="DejaVu", fname=HERE / "DejaVuSans.ttf", unicode_range="U+0020-007E"
    )
    pdf.add_font(
        family="DejaVu",
        style="B",
        fname=HERE / "DejaVuSans-Bold.ttf",
        unicode_range="U+0020-007E",
    )
    pdf.add_font(
        family="DejaVu",
        style="I",
        fname=HERE / "DejaVuSans-Oblique.ttf",
        unicode_range="U+0020-007E",
    )

    pdf.add_font(
        family="NotoEmoji",
        fname=HERE.parent / "color_font" / "colrv1-NotoColorEmoji.ttf",
    )

    pdf.set_font("DejaVu", size=16)
    pdf.set_fallback_fonts(["NotoEmoji"])
    pdf.add_page()

    text = "**Bold text** with emoji 😀 and __italic text__ with ☀ symbols"
    pdf.multi_cell(w=0, text=text, markdown=True)

    assert_pdf_equal(
        pdf,
        HERE / "markdown_unicode_range.pdf",
        tmp_path,
    )


def test_unicode_range_with_zero_width_characters(tmp_path):
    """Test unicode_range with zero-width and combining characters"""

    pdf = FPDF()

    pdf.add_font(
        family="DejaVu",
        fname=HERE / "DejaVuSans.ttf",
        unicode_range="U+0020-007F, U+0300-036F",  # Include combining diacritics
    )

    pdf.set_font("DejaVu", size=24)
    pdf.add_page()

    pdf.cell(w=0, text="e\u0301")

    assert_pdf_equal(
        pdf,
        HERE / "unicode_range_combining.pdf",
        tmp_path,
    )


def test_unicode_range_bmp_boundary(tmp_path):
    """Test unicode_range at BMP/supplementary plane boundary"""

    pdf = FPDF()

    pdf.add_font(
        family="DejaVu",
        fname=HERE / "DejaVuSans.ttf",
        unicode_range="U+FFF0-FFFF, U+10000-1000F",  # Cross plane boundary
    )

    pdf.set_font("DejaVu", size=24)
    pdf.add_page()

    # This mainly tests that parsing works across planes
    pdf.cell(w=0, text="Test")

    assert_pdf_equal(
        pdf,
        HERE / "unicode_range_bmp_boundary.pdf",
        tmp_path,
    )
