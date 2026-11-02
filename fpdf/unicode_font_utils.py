"""
Unicode font utilities for fpdf2.

This module provides utilities for automatic Unicode font detection and management,
helping users work with non-Latin scripts like Cyrillic, Arabic, Chinese, etc.

The contents of this module are internal to fpdf2, and not part of the public API.
They may change at any time without prior warning or any deprecation period,
in non-backward-compatible ways.
"""

import platform
from contextlib import suppress
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import logging

from fontTools import ttLib

from .unicode_script import get_unicode_script, UnicodeScript

LOGGER = logging.getLogger(__name__)


class UnicodeFontManager:
    """
    Manages Unicode font detection and provides recommendations for different scripts.
    """

    def __init__(self) -> None:
        self.system = platform.system().lower()
        self.font_paths = self._get_system_font_paths()
        # The filesystem scan is deferred: it is potentially expensive (it walks
        # every system font directory) and is only needed when a recommendation
        # is actually requested. See the `available_fonts` property below.
        self._available_fonts: Optional[Dict[str, Path]] = None
        self._available_fonts_loaded = False

    @property
    def available_fonts(self) -> Dict[str, Path]:
        """Mapping of font name to file path, scanned lazily on first access."""
        if not self._available_fonts_loaded:
            self._available_fonts = self._scan_available_fonts()
            self._available_fonts_loaded = True
        assert self._available_fonts is not None
        return self._available_fonts

    def _get_system_font_paths(self) -> List[Path]:
        """Get common font paths for the current system."""
        paths: List[Path] = []

        if self.system == "darwin":  # macOS
            paths.extend(
                [
                    Path("/System/Library/Fonts"),
                    Path("/Library/Fonts"),
                    Path.home() / "Library/Fonts",
                ]
            )
        elif self.system == "linux":
            paths.extend(
                [
                    Path("/usr/share/fonts"),
                    Path("/usr/local/share/fonts"),
                    Path.home() / ".fonts",
                    Path.home() / ".local/share/fonts",
                ]
            )
        elif self.system == "windows":
            paths.extend(
                [
                    Path("C:/Windows/Fonts"),
                    Path.home() / "AppData/Local/Microsoft/Windows/Fonts",
                ]
            )

        return [p for p in paths if p.exists()]

    def _scan_available_fonts(self) -> Dict[str, Path]:
        """Scan for available TrueType/OpenType fonts."""
        fonts: Dict[str, Path] = {}

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

    def get_recommended_fonts_for_script(
        self, script: UnicodeScript
    ) -> List[Tuple[str, str]]:
        """
        Get recommended font names and their file paths for a specific Unicode script.

        Returns:
            List of (font_name, file_path) tuples, ordered by preference.
        """
        recommendations: List[Tuple[str, str]] = []

        # Define font recommendations by script
        script_fonts: Dict[UnicodeScript, List[str]] = {
            UnicodeScript.CYRILLIC: [
                "dejavusans",
                "dejavuserif",
                "dejavusanscondensed",
                "arial",
                "helvetica",
                "liberationsans",
                "liberationserif",
                "notosans",
                "notoserif",
                "roboto",
                "opensans",
            ],
            UnicodeScript.ARABIC: [
                "dejavusans",
                "dejavuserif",
                "notosansarabic",
                "notoserifarabic",
                "amiri",
                "scheherazade",
                "lateef",
            ],
            UnicodeScript.HAN: [
                "dejavusans",
                "dejavuserif",
                "notosanscjk",
                "notoserifcjk",
                "sourcehansans",
                "sourcehanserif",
                "fireflysung",
            ],
            UnicodeScript.HANGUL: [
                "dejavusans",
                "dejavuserif",
                "notosanskr",
                "notoserifkr",
                "nanumgothic",
                "nanummyeongjo",
            ],
            UnicodeScript.HIRAGANA: [
                "dejavusans",
                "dejavuserif",
                "notosansjp",
                "notoserifjp",
                "sourcehansans",
                "sourcehanserif",
            ],
            UnicodeScript.KATAKANA: [
                "dejavusans",
                "dejavuserif",
                "notosansjp",
                "notoserifjp",
                "sourcehansans",
                "sourcehanserif",
            ],
            UnicodeScript.DEVANAGARI: [
                "dejavusans",
                "dejavuserif",
                "notosansdevanagari",
                "notoserifdevanagari",
                "gargi",
                "lohitdevanagari",
            ],
            UnicodeScript.THAI: [
                "dejavusans",
                "dejavuserif",
                "notosansthai",
                "notoserifthai",
                "waree",
                "garuda",
            ],
            UnicodeScript.HEBREW: [
                "dejavusans",
                "dejavuserif",
                "notosanshebrew",
                "notoserifhebrew",
                "frankruehl",
                "david",
            ],
        }

        # Get fonts for the specific script
        preferred_fonts = script_fonts.get(script, ["dejavusans", "dejavuserif"])

        # Find available fonts from the preferred list. No generic fallback is
        # added: a font is only worth recommending once we have verified that it
        # actually contains the glyphs the text needs (see font_file_covers and
        # get_font_recommendation_for_text). Recommending a font merely because
        # it is installed could send the user back to the same encoding error.
        for font_name in preferred_fonts:
            if font_name in self.available_fonts:
                recommendations.append(
                    (font_name, str(self.available_fonts[font_name]))
                )

        return recommendations

    @staticmethod
    def detect_script_in_text(text: str) -> Optional[UnicodeScript]:
        """
        Detect the primary Unicode script in the given text.

        Returns:
            The most common non-Latin Unicode script in the text, or None if only Latin/Common scripts are found.
        """
        script_counts: Dict[UnicodeScript, int] = {}

        for char in text:
            script = get_unicode_script(char)
            if script not in (UnicodeScript.COMMON, UnicodeScript.LATIN):
                script_counts[script] = script_counts.get(script, 0) + 1

        if not script_counts:
            return None

        return max(script_counts.items(), key=lambda x: x[1])[0]

    def get_font_recommendation_for_text(self, text: str) -> Optional[Tuple[str, str]]:
        """
        Get a font recommendation for the given text based on its Unicode script.

        A candidate font is only returned once its character map has been
        verified to contain every character of the detected script present in
        the text. If no installed candidate covers those characters, None is
        returned rather than a guess that might fail the same way.

        Returns:
            (font_name, file_path) tuple for the recommended font, or None if no recommendation.
        """
        script = self.detect_script_in_text(text)
        if not script:
            return None

        # The characters that actually drove the recommendation and that the
        # suggested font must be able to render.
        required = {ch for ch in text if get_unicode_script(ch) == script}

        for font_name, file_path in self.get_recommended_fonts_for_script(script):
            if font_file_covers(Path(file_path), required):
                return (font_name, file_path)

        return None

    def list_available_unicode_fonts(self) -> Dict[str, str]:
        """
        List all available Unicode-capable fonts.

        Returns:
            Dictionary mapping font names to file paths.
        """
        return {name: str(path) for name, path in self.available_fonts.items()}


def font_file_covers(font_path: Path, characters: Set[str]) -> bool:
    """
    Return True if the font file has a glyph for every character in `characters`.

    The font's character map is inspected with fontTools. Collection files
    (.ttc/.otc) count as covering the characters if any of their member fonts do.
    Any failure to open or parse the font, or a font without a usable character
    map, is treated as "not covered" so that an unreadable or unsuitable font is
    never recommended.
    """
    if not characters:
        return False

    codepoints = {ord(ch) for ch in characters}
    fonts: List[ttLib.TTFont] = []
    try:
        if font_path.suffix.lower() in (".ttc", ".otc"):
            collection = ttLib.TTCollection(str(font_path), lazy=True)
            members = collection.fonts  # pyright: ignore[reportUnknownMemberType]
            fonts = list(members)  # pyright: ignore[reportUnknownArgumentType]
        else:
            fonts = [ttLib.TTFont(str(font_path), fontNumber=0, lazy=True)]
        for font in fonts:
            cmap: Optional[Dict[int, str]] = font.getBestCmap()
            if cmap and codepoints.issubset(cmap.keys()):
                return True
    except Exception:  # pylint: disable=broad-exception-caught
        # Unreadable / corrupt / cmap-less fonts must never be recommended.
        return False
    finally:
        for font in fonts:
            with suppress(Exception):
                font.close()

    return False


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


def suggest_unicode_font_for_error(error_text: str, font_name: str) -> Optional[str]:
    """
    Generate a helpful error message suggesting a Unicode font when encoding errors occur.

    A font is only suggested when one is installed whose character map is verified
    to cover the offending characters. When no such font is found, None is returned
    so the caller can fall back to the generic "Please consider using a Unicode
    font." message instead of naming a font that might not work.

    Args:
        error_text: The text that caused the encoding error.
        font_name: The name of the font that failed.

    Returns:
        A helpful error message naming a verified font, or None if none was found.
    """
    manager = UnicodeFontManager()
    script = manager.detect_script_in_text(error_text)
    if not script:
        return None

    recommendation = manager.get_font_recommendation_for_text(error_text)
    if recommendation is None:
        return None

    font_name_rec, font_path = recommendation
    script_name = script.name.replace("_", " ").title()
    return (
        f"The text contains {script_name} characters that cannot be encoded with the '{font_name}' font. "
        f"Consider using a Unicode font like '{font_name_rec}' instead.\n"
        f"To use it, add the font with: pdf.add_font('{font_name_rec}', '', {font_path!r})"
    )
