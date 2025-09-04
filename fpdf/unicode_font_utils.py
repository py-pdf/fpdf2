"""
Unicode font utilities for fpdf2.

This module provides utilities for automatic Unicode font detection and management,
helping users work with non-Latin scripts like Cyrillic, Arabic, Chinese, etc.

The contents of this module are internal to fpdf2, and not part of the public API.
They may change at any time without prior warning or any deprecation period,
in non-backward-compatible ways.
"""

import os
import platform
from pathlib import Path
from typing import List, Optional, Tuple, Dict
import logging

from .unicode_script import get_unicode_script, UnicodeScript

LOGGER = logging.getLogger(__name__)


class UnicodeFontManager:
    """
    Manages Unicode font detection and provides recommendations for different scripts.
    """
    
    def __init__(self):
        self.system = platform.system().lower()
        self.font_paths = self._get_system_font_paths()
        self.available_fonts = self._scan_available_fonts()
    
    def _get_system_font_paths(self) -> List[Path]:
        """Get common font paths for the current system."""
        paths = []
        
        if self.system == "darwin":  # macOS
            paths.extend([
                Path("/System/Library/Fonts"),
                Path("/Library/Fonts"),
                Path.home() / "Library/Fonts",
            ])
        elif self.system == "linux":
            paths.extend([
                Path("/usr/share/fonts"),
                Path("/usr/local/share/fonts"),
                Path.home() / ".fonts",
                Path.home() / ".local/share/fonts",
            ])
        elif self.system == "windows":
            paths.extend([
                Path("C:/Windows/Fonts"),
                Path.home() / "AppData/Local/Microsoft/Windows/Fonts",
            ])
        
        return [p for p in paths if p.exists()]
    
    def _scan_available_fonts(self) -> Dict[str, Path]:
        """Scan for available TrueType/OpenType fonts."""
        fonts = {}
        
        for font_dir in self.font_paths:
            for font_file in font_dir.rglob("*.ttf"):
                font_name = font_file.stem.lower()
                if font_name not in fonts:  # Prefer first found
                    fonts[font_name] = font_file
            for font_file in font_dir.rglob("*.otf"):
                font_name = font_file.stem.lower()
                if font_name not in fonts:  # Prefer first found
                    fonts[font_name] = font_file
            for font_file in font_dir.rglob("*.ttc"):
                font_name = font_file.stem.lower()
                if font_name not in fonts:  # Prefer first found
                    fonts[font_name] = font_file
        
        return fonts
    
    def get_recommended_fonts_for_script(self, script: UnicodeScript) -> List[Tuple[str, str]]:
        """
        Get recommended font names and their file paths for a specific Unicode script.
        
        Returns:
            List of (font_name, file_path) tuples, ordered by preference.
        """
        recommendations = []
        
        # Define font recommendations by script
        script_fonts = {
            UnicodeScript.CYRILLIC: [
                "dejavusans", "dejavuserif", "dejavusanscondensed",
                "arial", "helvetica", "liberationsans", "liberationserif",
                "notosans", "notoserif", "roboto", "opensans"
            ],
            UnicodeScript.ARABIC: [
                "dejavusans", "dejavuserif", "notosansarabic", "notoserifarabic",
                "amiri", "scheherazade", "lateef"
            ],
            UnicodeScript.HAN: [
                "dejavusans", "dejavuserif", "notosanscjk", "notoserifcjk",
                "sourcehansans", "sourcehanserif", "fireflysung"
            ],
            UnicodeScript.HANGUL: [
                "dejavusans", "dejavuserif", "notosanskr", "notoserifkr",
                "nanumgothic", "nanummyeongjo"
            ],
            UnicodeScript.HIRAGANA: [
                "dejavusans", "dejavuserif", "notosansjp", "notoserifjp",
                "sourcehansans", "sourcehanserif"
            ],
            UnicodeScript.KATAKANA: [
                "dejavusans", "dejavuserif", "notosansjp", "notoserifjp",
                "sourcehansans", "sourcehanserif"
            ],
            UnicodeScript.DEVANAGARI: [
                "dejavusans", "dejavuserif", "notosansdevanagari", "notoserifdevanagari",
                "gargi", "lohitdevanagari"
            ],
            UnicodeScript.THAI: [
                "dejavusans", "dejavuserif", "notosansthai", "notoserifthai",
                "waree", "garuda"
            ],
            UnicodeScript.HEBREW: [
                "dejavusans", "dejavuserif", "notosanshebrew", "notoserifhebrew",
                "frankruehl", "david"
            ],
        }
        
        # Get fonts for the specific script
        preferred_fonts = script_fonts.get(script, ["dejavusans", "dejavuserif"])
        
        # Find available fonts from the preferred list
        for font_name in preferred_fonts:
            if font_name in self.available_fonts:
                recommendations.append((font_name, str(self.available_fonts[font_name])))
        
        # If no specific fonts found, recommend DejaVu fonts (most comprehensive Unicode support)
        if not recommendations:
            for fallback in ["dejavusans", "dejavuserif", "arial", "helvetica"]:
                if fallback in self.available_fonts:
                    recommendations.append((fallback, str(self.available_fonts[fallback])))
                    break
        
        return recommendations
    
    def detect_script_in_text(self, text: str) -> Optional[UnicodeScript]:
        """
        Detect the primary Unicode script in the given text.
        
        Returns:
            The most common Unicode script in the text, or None if no non-Common script is found.
        """
        script_counts = {}
        
        for char in text:
            script = get_unicode_script(char)
            if script != UnicodeScript.COMMON:
                script_counts[script] = script_counts.get(script, 0) + 1
        
        if not script_counts:
            return None
        
        return max(script_counts.items(), key=lambda x: x[1])[0]
    
    def get_font_recommendation_for_text(self, text: str) -> Optional[Tuple[str, str]]:
        """
        Get a font recommendation for the given text based on its Unicode script.
        
        Returns:
            (font_name, file_path) tuple for the recommended font, or None if no recommendation.
        """
        script = self.detect_script_in_text(text)
        if not script:
            return None
        
        recommendations = self.get_recommended_fonts_for_script(script)
        return recommendations[0] if recommendations else None
    
    def list_available_unicode_fonts(self) -> Dict[str, str]:
        """
        List all available Unicode-capable fonts.
        
        Returns:
            Dictionary mapping font names to file paths.
        """
        return {name: str(path) for name, path in self.available_fonts.items()}


def get_unicode_font_recommendation(text: str) -> Optional[Tuple[str, str]]:
    """
    Convenience function to get a Unicode font recommendation for text.
    
    Args:
        text: The text to analyze for Unicode script detection.
        
    Returns:
        (font_name, file_path) tuple for the recommended font, or None if no recommendation.
    """
    manager = UnicodeFontManager()
    return manager.get_font_recommendation_for_text(text)


def suggest_unicode_font_for_error(error_text: str, font_name: str) -> str:
    """
    Generate a helpful error message suggesting Unicode fonts when encoding errors occur.
    
    Args:
        error_text: The text that caused the encoding error.
        font_name: The name of the font that failed.
        
    Returns:
        A helpful error message with font suggestions.
    """
    manager = UnicodeFontManager()
    script = manager.detect_script_in_text(error_text)
    
    if not script:
        return (
            f"The text contains characters that cannot be encoded with the '{font_name}' font. "
            "Consider using a Unicode font like DejaVu Sans or Arial."
        )
    
    script_name = script.name.replace('_', ' ').title()
    recommendations = manager.get_recommended_fonts_for_script(script)
    
    if recommendations:
        font_name_rec, font_path = recommendations[0]
        message = (
            f"The text contains {script_name} characters that cannot be encoded with the '{font_name}' font. "
            f"Consider using a Unicode font like '{font_name_rec}' instead.\n"
            f"To use it, add the font with: pdf.add_font('{font_name_rec}', '', '{font_path}')"
        )
    else:
        message = (
            f"The text contains {script_name} characters that cannot be encoded with the '{font_name}' font. "
            "Consider using a Unicode font like DejaVu Sans or Arial."
        )
    
    return message
