"""Charmap Test Case

This module contains the test case for the Charmap Test. It prints the first
999 characters of the unicode character set with a unicode ttf font, and
verifies the result against a known good result.

This test will complain that some of the values in this font file are out of
the range of the C 'short' data type (2 bytes, 0 - 65535):
  fpdf/ttfonts.py:671: UserWarning: cmap value too big/small:
and this seems to be okay.
"""
from pathlib import Path

import pytest

import fpdf
from fpdf.ttfonts import TTFontFile
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


class MyTTFontFile(TTFontFile):
    """MyTTFontFile docstring

    I clearly have no idea what this does. It'd be great if this class were
    even a little bit better documented, so that it would be clearer what this
    test is testing, otherwise this test isn't clearly testing one class or the
    other.
    """

    def getCMAP4(self, unicode_cmap_offset, glyphToChar, charToGlyph):
        TTFontFile.getCMAP4(self, unicode_cmap_offset, glyphToChar, charToGlyph)
        self.saveChar = charToGlyph

    def getCMAP12(self, unicode_cmap_offset, glyphToChar, charToGlyph):
        TTFontFile.getCMAP12(self, unicode_cmap_offset, glyphToChar, charToGlyph)
        self.saveChar = charToGlyph


@pytest.mark.parametrize(
    "fontpath",
    ["DejaVuSans.ttf", "DroidSansFallback.ttf", "Roboto-Regular.ttf", "cmss12.ttf"],
)
def test_first_999_chars(fontpath, tmp_path):
    fontpath = HERE / fontpath
    fontname = fontpath.stem

    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.add_font(fontname, fname=fontpath, uni=True)
    pdf.set_font(fontname, size=10)

    ttf = MyTTFontFile()
    ttf.getMetrics(fontpath)

    # Create a PDF with the first 999 charters defined in the font:
    for counter, character in enumerate(ttf.saveChar, 0):
        pdf.write(8, f"{counter:03}) {character:03x} - {character:c}")
        pdf.ln()
        if counter >= 999:
            break

    assert_pdf_equal(pdf, HERE / f"charmap_first_999_chars-{fontname}.pdf", tmp_path)

    for pkl_path in HERE.glob("*.pkl"):
        pkl_path.unlink()
