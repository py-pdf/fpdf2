"""
Tests for Unicode font utilities.
"""

from pathlib import Path

from fpdf.unicode_font_utils import (
    UnicodeFontManager,
    font_file_covers,
    get_unicode_font_recommendation,
    suggest_unicode_font_for_error,
)
from fpdf.unicode_script import UnicodeScript


def test_init():
    """Test UnicodeFontManager initialization."""
    manager = UnicodeFontManager()
    assert isinstance(manager.system, str)
    assert isinstance(manager.font_paths, list)
    assert isinstance(manager.available_fonts, dict)


def test_detect_script_in_text_cyrillic():
    """Test Cyrillic script detection."""
    manager = UnicodeFontManager()

    # Test Cyrillic text
    cyrillic_text = "Привет, мир!"
    script = manager.detect_script_in_text(cyrillic_text)
    assert script == UnicodeScript.CYRILLIC

    # Test mixed text
    mixed_text = "Hello Привет World"
    script = manager.detect_script_in_text(mixed_text)
    assert (
        script == UnicodeScript.CYRILLIC
    )  # Should detect the most common non-Common script


def test_detect_script_in_text_arabic():
    """Test Arabic script detection."""
    manager = UnicodeFontManager()

    arabic_text = "مرحبا بالعالم"
    script = manager.detect_script_in_text(arabic_text)
    assert script == UnicodeScript.ARABIC


def test_detect_script_in_text_latin_only():
    """Test Latin-only text detection."""
    manager = UnicodeFontManager()

    latin_text = "Hello World"
    script = manager.detect_script_in_text(latin_text)
    assert script is None  # Should return None for Latin-only text


def test_get_recommended_fonts_for_script_cyrillic():
    """Test font recommendations for Cyrillic script."""
    manager = UnicodeFontManager()

    recommendations = manager.get_recommended_fonts_for_script(UnicodeScript.CYRILLIC)
    assert isinstance(recommendations, list)

    # Should return tuples of (font_name, file_path)
    for font_name, file_path in recommendations:
        assert isinstance(font_name, str)
        assert isinstance(file_path, str)


def test_get_font_recommendation_for_text():
    """Test getting font recommendations for text."""
    manager = UnicodeFontManager()

    # Test with Cyrillic text
    cyrillic_text = "Привет, мир!"
    recommendation = manager.get_font_recommendation_for_text(cyrillic_text)

    if recommendation:  # Only test if fonts are available
        font_name, file_path = recommendation
        assert isinstance(font_name, str)
        assert isinstance(file_path, str)
        assert Path(file_path).exists()


def test_list_available_unicode_fonts():
    """Test listing available Unicode fonts."""
    manager = UnicodeFontManager()

    fonts = manager.list_available_unicode_fonts()
    assert isinstance(fonts, dict)

    # Check that all values are valid file paths
    for font_name, file_path in fonts.items():
        assert isinstance(font_name, str)
        assert isinstance(file_path, str)
        assert Path(file_path).exists()


def test_get_unicode_font_recommendation():
    """Test the get_unicode_font_recommendation convenience function."""
    cyrillic_text = "Привет, мир!"
    recommendation = get_unicode_font_recommendation(cyrillic_text)

    if recommendation:  # Only test if fonts are available
        font_name, file_path = recommendation
        assert isinstance(font_name, str)
        assert isinstance(file_path, str)


def test_suggest_unicode_font_for_error_cyrillic():
    """A suggestion, when returned, names the script, the failing font and a replacement."""
    suggestion = suggest_unicode_font_for_error("Привет, мир!", "helvetica")
    # A suggestion is only returned when an installed font is verified to cover
    # the characters, so None is valid on a host without such a font.
    if suggestion is not None:
        assert "Cyrillic" in suggestion
        assert "helvetica" in suggestion
        assert "Unicode font" in suggestion
        assert "pdf.add_font(" in suggestion


def test_suggest_unicode_font_for_error_arabic():
    """A suggestion for Arabic text, when returned, is well-formed."""
    suggestion = suggest_unicode_font_for_error("مرحبا بالعالم", "times")
    if suggestion is not None:
        assert "Arabic" in suggestion
        assert "times" in suggestion
        assert "Unicode font" in suggestion


def test_suggest_unicode_font_for_error_no_script():
    """Latin-only / no-script text yields no font suggestion (caller uses the generic message)."""
    assert suggest_unicode_font_for_error("Hello World 123", "courier") is None


def test_font_file_covers_verifies_glyph_coverage():
    """font_file_covers inspects the actual character map, not just that a font exists."""
    dejavu = Path(__file__).parent / "DejaVuSans.ttf"
    assert dejavu.exists()
    # DejaVu Sans covers Latin and Cyrillic...
    assert font_file_covers(dejavu, {"A", "П"}) is True
    # ...but not Han ideographs.
    assert font_file_covers(dejavu, {"你"}) is False
    # An empty requirement is never treated as covered.
    assert font_file_covers(dejavu, set()) is False


def test_font_file_covers_unreadable_file_is_safe():
    """A path that cannot be read is treated as not covering, so it is never recommended."""
    assert font_file_covers(Path("/no/such/font.ttf"), {"A"}) is False


def test_unicode_font_manager_with_real_fonts():
    """Test UnicodeFontManager with real system fonts."""
    manager = UnicodeFontManager()

    # This test will pass even if no fonts are found
    # It just ensures the manager doesn't crash
    fonts = manager.list_available_unicode_fonts()
    assert isinstance(fonts, dict)

    # Test recommendations for different scripts
    for script in [UnicodeScript.CYRILLIC, UnicodeScript.ARABIC, UnicodeScript.HAN]:
        recommendations = manager.get_recommended_fonts_for_script(script)
        assert isinstance(recommendations, list)


def test_script_detection_accuracy():
    """Test script detection accuracy with various texts."""
    manager = UnicodeFontManager()

    test_cases = [
        ("Привет, мир!", UnicodeScript.CYRILLIC),
        ("مرحبا بالعالم", UnicodeScript.ARABIC),
        ("你好世界", UnicodeScript.HAN),
        ("안녕하세요", UnicodeScript.HANGUL),
        ("こんにちは世界", UnicodeScript.HIRAGANA),
        ("नमस्ते दुनिया", UnicodeScript.DEVANAGARI),
        ("สวัสดีชาวโลก", UnicodeScript.THAI),
        ("שלום עולם", UnicodeScript.HEBREW),
    ]

    for text, expected_script in test_cases:
        detected_script = manager.detect_script_in_text(text)
        assert detected_script == expected_script, f"Failed for text: {text}"
