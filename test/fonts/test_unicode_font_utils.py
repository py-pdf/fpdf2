"""
Tests for Unicode font utilities.
"""

import pytest
from pathlib import Path

from fpdf.unicode_font_utils import (
    UnicodeFontManager,
    get_unicode_font_recommendation,
    suggest_unicode_font_for_error,
)
from fpdf.unicode_script import UnicodeScript


class TestUnicodeFontManager:
    """Test the UnicodeFontManager class."""
    
    def test_init(self):
        """Test UnicodeFontManager initialization."""
        manager = UnicodeFontManager()
        assert isinstance(manager.system, str)
        assert isinstance(manager.font_paths, list)
        assert isinstance(manager.available_fonts, dict)
    
    def test_detect_script_in_text_cyrillic(self):
        """Test Cyrillic script detection."""
        manager = UnicodeFontManager()
        
        # Test Cyrillic text
        cyrillic_text = "Привет, мир!"
        script = manager.detect_script_in_text(cyrillic_text)
        assert script == UnicodeScript.CYRILLIC
        
        # Test mixed text
        mixed_text = "Hello Привет World"
        script = manager.detect_script_in_text(mixed_text)
        assert script == UnicodeScript.CYRILLIC  # Should detect the most common non-Common script
    
    def test_detect_script_in_text_arabic(self):
        """Test Arabic script detection."""
        manager = UnicodeFontManager()
        
        arabic_text = "مرحبا بالعالم"
        script = manager.detect_script_in_text(arabic_text)
        assert script == UnicodeScript.ARABIC
    
    def test_detect_script_in_text_latin_only(self):
        """Test Latin-only text detection."""
        manager = UnicodeFontManager()
        
        latin_text = "Hello World"
        script = manager.detect_script_in_text(latin_text)
        assert script is None  # Should return None for Latin-only text
    
    def test_get_recommended_fonts_for_script_cyrillic(self):
        """Test font recommendations for Cyrillic script."""
        manager = UnicodeFontManager()
        
        recommendations = manager.get_recommended_fonts_for_script(UnicodeScript.CYRILLIC)
        assert isinstance(recommendations, list)
        
        # Should return tuples of (font_name, file_path)
        for font_name, file_path in recommendations:
            assert isinstance(font_name, str)
            assert isinstance(file_path, str)
    
    def test_get_font_recommendation_for_text(self):
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
    
    def test_list_available_unicode_fonts(self):
        """Test listing available Unicode fonts."""
        manager = UnicodeFontManager()
        
        fonts = manager.list_available_unicode_fonts()
        assert isinstance(fonts, dict)
        
        # Check that all values are valid file paths
        for font_name, file_path in fonts.items():
            assert isinstance(font_name, str)
            assert isinstance(file_path, str)
            assert Path(file_path).exists()


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_get_unicode_font_recommendation(self):
        """Test the get_unicode_font_recommendation convenience function."""
        cyrillic_text = "Привет, мир!"
        recommendation = get_unicode_font_recommendation(cyrillic_text)
        
        if recommendation:  # Only test if fonts are available
            font_name, file_path = recommendation
            assert isinstance(font_name, str)
            assert isinstance(file_path, str)
    
    def test_suggest_unicode_font_for_error_cyrillic(self):
        """Test error suggestion for Cyrillic text."""
        error_text = "Привет, мир!"
        font_name = "helvetica"
        
        suggestion = suggest_unicode_font_for_error(error_text, font_name)
        assert isinstance(suggestion, str)
        assert "Cyrillic" in suggestion
        assert "helvetica" in suggestion
        assert "Unicode font" in suggestion
    
    def test_suggest_unicode_font_for_error_arabic(self):
        """Test error suggestion for Arabic text."""
        error_text = "مرحبا بالعالم"
        font_name = "times"
        
        suggestion = suggest_unicode_font_for_error(error_text, font_name)
        assert isinstance(suggestion, str)
        assert "Arabic" in suggestion
        assert "times" in suggestion
        assert "Unicode font" in suggestion
    
    def test_suggest_unicode_font_for_error_no_script(self):
        """Test error suggestion for text with no specific script."""
        error_text = "Hello World 123"
        font_name = "courier"
        
        suggestion = suggest_unicode_font_for_error(error_text, font_name)
        assert isinstance(suggestion, str)
        assert "courier" in suggestion
        assert "Unicode font" in suggestion


class TestIntegration:
    """Integration tests with actual fpdf2 functionality."""
    
    def test_unicode_font_manager_with_real_fonts(self):
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
    
    def test_script_detection_accuracy(self):
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
