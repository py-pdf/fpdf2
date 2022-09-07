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
from fontTools import ttLib
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


@pytest.mark.parametrize(
    "font_filename",
    ["DejaVuSans.ttf", "DroidSansFallback.ttf", "Roboto-Regular.ttf", "cmss12.ttf"],
)
def test_first_999_chars(font_filename, tmp_path):
    font_path = HERE / ".." / ".." / "fonts" / font_filename
    font_name = font_path.stem

    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.add_font(font_name, fname=font_path)
    pdf.set_font(font_name, size=10)

    font = ttLib.TTFont(font_path)
    cmap = font.getBestCmap()

    # Create a PDF with the first 999 charters defined in the font:
    for counter, character in enumerate(cmap, 0):
        pdf.write(8, f"{counter:03}) {character:03x} - {character:c}", print_sh=True)
        pdf.ln()
        if counter >= 999:
            break

    assert_pdf_equal(pdf, HERE / f"charmap_first_999_chars-{font_name}.pdf", tmp_path)
